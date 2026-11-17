import os
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.access import require_patient
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.evolution_analysis import EvolutionAnalysis
from app.models.user import User
from app.schemas.evolution import Period, AnalysisRequest, CONSENT_VERSION
from app.services.evolution import evolution
from app.services.groq_analysis import generate_analysis

router = APIRouter(prefix="/evolution", tags=["Evolution"])


def period_query(desde: date | None = None, hasta: date | None = None):
    if desde and hasta and desde > hasta:
        raise HTTPException(422, "La fecha inicial debe ser anterior a la final")
    return Period(desde=desde, hasta=hasta)


@router.get("/patients/{patient_id}")
def get_evolution(patient_id: int, period: Period = Depends(period_query),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_patient(db, user, patient_id)
    return evolution(db, patient_id, period)


@router.get("/patients/{patient_id}/analyses")
def list_analyses(patient_id: int, limit: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_patient(db, user, patient_id)
    records = db.query(EvolutionAnalysis).filter_by(
        patient_id=patient_id, status="completed"
    ).order_by(EvolutionAnalysis.created_at.desc(), EvolutionAnalysis.id.desc()).limit(limit).all()
    return [{"id": r.id, "fecha": r.created_at, "modelo": r.model, "resultado": r.result}
            for r in records]


@router.post("/patients/{patient_id}/analyses", status_code=201)
def create_analysis(patient_id: int, body: AnalysisRequest,
                    db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_patient(db, user, patient_id, active=True)
    data = evolution(db, patient_id, body)
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
    )
    db.add(attempt)
    db.commit()
    try:
        result = generate_analysis(data)
    except HTTPException:
        attempt.status = "failed"
        db.commit()
        raise
    attempt.status = "completed"
    attempt.result = result
    db.commit()
    return {"id": attempt.id, "fecha": attempt.created_at, "modelo": model, "resultado": result}
