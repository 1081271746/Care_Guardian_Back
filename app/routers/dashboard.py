from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.core.dependencies import get_current_user
from app.database.connection import get_db

from app.models.user import User
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord
from app.models.medication import Medication
from app.models.appointment import Appointment
from app.models.caregiver_note import CaregiverNote
from app.models.alert import Alert

from app.services.historical_analysis import analyze_patient_history


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/patients/{patient_id}")
def get_patient_dashboard(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verificar paciente

    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )

    if not patient.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El paciente está inactivo"
        )

    # 2. Verificar cuidador asignado

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    # 3. Últimos síntomas

    symptoms = db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo == True
    ).order_by(
        SymptomRecord.fecha_registro.desc()
    ).limit(5).all()

    # 4. Medicamentos activos

    medications = db.query(Medication).filter(
        Medication.patient_id == patient_id,
        Medication.activo == True
    ).all()

    # 5. Próximas citas

    appointments = db.query(Appointment).filter(
    Appointment.patient_id == patient_id,
    Appointment.fecha >= date.today(),
    Appointment.estado != "cancelada"
)    .order_by(
    Appointment.fecha.asc(),
    Appointment.hora.asc()
)    .limit(5).all()

    # 6. Notas recientes

    notes = db.query(CaregiverNote).filter(
        CaregiverNote.patient_id == patient_id,
        CaregiverNote.activo == True
    ).order_by(
        CaregiverNote.fecha_registro.desc()
    ).limit(5).all()

    # 7. Alertas activas

    alerts = db.query(Alert).filter(
        Alert.patient_id == patient_id,
        Alert.activa == True
    ).order_by(
        Alert.fecha_registro.desc()
    ).limit(10).all()

    # 8. Análisis histórico
    

    historical_symptoms = db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo == True
    ).order_by(
        SymptomRecord.fecha_registro.desc()
    ).limit(10).all()

    historical_result = analyze_patient_history(
        historical_symptoms
    )

    # 9. Nivel de riesgo actual

    risk_level = historical_result.nivel

    # 10. Construir respuesta

    return {
        "patient": {
    "id": patient.id,
    "nombres": patient.nombres,
    "apellidos": patient.apellidos,
    "fecha_nacimiento": patient.fecha_nacimiento,
    "documento": patient.documento,
    "telefono": patient.telefono,
    "direccion": patient.direccion,
    "contacto_emergencia": patient.contacto_emergencia,
    "telefono_emergencia": patient.telefono_emergencia
       },

        "symptoms": symptoms,

        "medications": medications,

        "upcoming_appointments": appointments,

        "recent_notes": notes,

        "active_alerts": alerts,

        "historical_analysis": {
            "registros_analizados": historical_result.registros_analizados,
            "score": historical_result.score,
            "nivel": historical_result.nivel,
            "tendencias": historical_result.tendencias,
            "recomendacion": historical_result.recomendacion
        },

        "current_risk_level": risk_level
    }