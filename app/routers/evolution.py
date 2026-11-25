import os
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.access import require_patient
from app.core.dependencies import get_current_user
from app.core.time import app_timezone
from app.database.connection import get_db
from app.models.evolution_analysis import EvolutionAnalysis
from app.models.user import User
from app.schemas.evolution import CONSENT_VERSION, AnalysisRequest, Period
from app.services.evolution import evolution
from app.services.groq_analysis import generate_analysis

router = APIRouter(prefix="/evolution", tags=["Evolution"])


def resolve_zone(name: str | None):
    try:
        return app_timezone(name)
    except ValueError:
        raise HTTPException(422, "Zona horaria no válida")


def period_query(desde: date | None = None, hasta: date | None = None):
    if desde and hasta and desde > hasta:
        raise HTTPException(422, "La fecha inicial debe ser anterior a la final")
    return Period(desde=desde, hasta=hasta)


@router.get("/ai-status", summary="Disponibilidad del análisis con Groq (sin secretos)")
def ai_status(user=Depends(get_current_user)):
    model = os.getenv("GROQ_MODEL", "")
    return {
        "configurado": bool(os.getenv("GROQ_API_KEY")) and bool(model),
        "proveedor": "Groq",
        "modelo": model or None,
        "limite_por_minuto": max(1, int(os.getenv("GROQ_REQUESTS_PER_MINUTE", "10"))),
        "version_consentimiento": CONSENT_VERSION,
    }


@router.get("/patients/{patient_id}", summary="Estadísticas, mediciones e historial del período")
def get_evolution(patient_id: int, period: Period = Depends(period_query),
                  zona: str | None = Query(None, max_length=64,
                                           description="Zona IANA del navegador; por defecto APP_TIMEZONE"),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_patient(db, user, patient_id)
    return evolution(db, patient_id, period, resolve_zone(zona))


def serialize_analysis(record):
    return {
        "id": record.id, "fecha": record.created_at, "modelo": record.model,
        "periodo": {"desde": record.period_start, "hasta": record.period_end},
        "autor_id": record.user_id, "resultado": record.result,
    }


@router.get("/patients/{patient_id}/analyses", summary="Resúmenes con IA guardados")
def list_analyses(patient_id: int, limit: int = Query(20, ge=1, le=100),
                  offset: int = Query(0, ge=0),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_patient(db, user, patient_id)
    records = db.query(EvolutionAnalysis).filter_by(
        patient_id=patient_id, status="completed"
    ).order_by(EvolutionAnalysis.created_at.desc(), EvolutionAnalysis.id.desc()
    ).offset(offset).limit(limit).all()
    return [serialize_analysis(r) for r in records]


@router.get("/patients/{patient_id}/analyses/{analysis_id}", summary="Un resumen guardado")
def get_analysis(patient_id: int, analysis_id: int,
                 db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_patient(db, user, patient_id)
    record = db.query(EvolutionAnalysis).filter_by(
        id=analysis_id, patient_id=patient_id, status="completed"
    ).first()
    if record is None:
        raise HTTPException(404, "Análisis no encontrado")
    return serialize_analysis(record)


@router.post("/patients/{patient_id}/analyses", status_code=201,
             summary="Generar resumen con Groq (requiere consentimiento)")
def create_analysis(patient_id: int, body: AnalysisRequest,
                    db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_patient(db, user, patient_id, active=True)
    data = evolution(db, patient_id, body, resolve_zone(body.zona))
    if not data["datos_suficientes"]:
        raise HTTPException(422, "Se necesitan al menos dos mediciones de un mismo indicador")
    model = os.getenv("GROQ_MODEL", "")
    if not os.getenv("GROQ_API_KEY") or not model:
        raise HTTPException(503, "El análisis IA no está configurado")
    # A PostgreSQL row lock serializes quota reservations across replicas/processes.
    db.query(User).filter_by(id=user.id).with_for_update().one()
    now = datetime.now(timezone.utc)
    attempts = db.query(EvolutionAnalysis).filter(
        EvolutionAnalysis.user_id == user.id,
        EvolutionAnalysis.created_at >= now - timedelta(minutes=1),
    ).count()
    limit = max(1, int(os.getenv("GROQ_REQUESTS_PER_MINUTE", "10")))
    if attempts >= limit:
        raise HTTPException(429, "Límite de análisis por minuto alcanzado", headers={"Retry-After": "60"})
    attempt = EvolutionAnalysis(
        patient_id=patient_id, user_id=user.id, consent_version=CONSENT_VERSION,
        model=model, status="pending", created_at=now,
        period_start=body.desde, period_end=body.hasta,
    )
    db.add(attempt)
    db.commit()
    try:
        result = generate_analysis(data)
    except HTTPException as error:
        attempt.status = "failed"
        attempt.error = str(error.detail)[:200]
        db.commit()
        raise
    except Exception:
        # Unexpected failures must not leave the attempt "pending" forever.
        attempt.status = "failed"
        attempt.error = "Error inesperado"
        db.commit()
        raise HTTPException(502, "No se pudo completar el análisis con Groq")
    attempt.status = "completed"
    attempt.result = result
    db.commit()
    db.refresh(attempt)
    return serialize_analysis(attempt)
