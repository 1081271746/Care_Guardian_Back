from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.access import require_patient
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.symptom_record import SymptomRecord
from app.models.user import User
from app.services.alert_generator import generate_alert_from_history
from app.services.historical_analysis import analyze_patient_history

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)

RECENT_RECORDS = 10


@router.get("/patients/{patient_id}", summary="Análisis por reglas de los últimos síntomas")
def analyze_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deterministic rules (no AI). May create or escalate a historical alert."""
    require_patient(db, current_user, patient_id, active=True)

    symptoms = db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo.is_(True)
    ).order_by(
        SymptomRecord.fecha_registro.desc(), SymptomRecord.id.desc()
    ).limit(RECENT_RECORDS).all()

    result = analyze_patient_history(symptoms)
    alert = generate_alert_from_history(patient_id, result, db)
    db.commit()

    return {
        "patient_id": patient_id,
        "registros_analizados": result.registros_analizados,
        "score": result.score,
        "nivel": result.nivel,
        "tendencias": result.tendencias,
        "recomendacion": result.recomendacion,
        "alerta_generada": alert is not None,
        "alerta_id": alert.id if alert else None,
    }
