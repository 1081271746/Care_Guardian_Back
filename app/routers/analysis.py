from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord
from app.models.user import User
from app.services.historical_analysis import analyze_patient_history


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)


@router.get("/patients/{patient_id}")
def analyze_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # -------------------------------------------------
    # Verificar que el paciente existe
    # -------------------------------------------------

    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )

    # -------------------------------------------------
    # Verificar que el paciente está activo
    # -------------------------------------------------

    if not patient.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El paciente está inactivo"
        )

    # -------------------------------------------------
    # Verificar relación cuidador-paciente
    # -------------------------------------------------

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    # -------------------------------------------------
    # Obtener registros activos del paciente
    # -------------------------------------------------

    symptoms = db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo == True
    ).order_by(
        SymptomRecord.fecha_registro.desc()
    ).limit(10).all()

    # -------------------------------------------------
    # Analizar historial
    # -------------------------------------------------

    result = analyze_patient_history(symptoms)

    return {
        "patient_id": patient_id,
        "registros_analizados": result.registros_analizados,
        "score": result.score,
        "nivel": result.nivel,
        "tendencias": result.tendencias,
        "recomendacion": result.recomendacion
    }