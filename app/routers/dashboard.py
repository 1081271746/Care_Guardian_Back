from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.access import require_patient
from app.core.dependencies import get_current_user
from app.core.time import local_today
from app.database.connection import get_db
from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.caregiver_note import CaregiverNote
from app.models.medication import Medication
from app.models.symptom_record import SymptomRecord
from app.models.user import User
from app.schemas.alert import AlertResponse
from app.schemas.appointment import AppointmentResponse
from app.schemas.caregiver_note import CaregiverNoteResponse
from app.schemas.medication import MedicationResponse
from app.schemas.patient import PatientResponse
from app.schemas.symptom_record import SymptomRecordResponse
from app.services.dashboard_summary import build_summary
from app.services.historical_analysis import analyze_patient_history

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

HISTORY_WINDOW = 10
RECENT_ITEMS = 5


def serialize(schema, rows):
    return [schema.model_validate(row).model_dump(mode="json") for row in rows]


@router.get("/summary", summary="Indicadores de todos los pacientes asignados")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_summary(db, current_user)


@router.get("/patients/{patient_id}", summary="Panel de un paciente")
def get_patient_dashboard(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = require_patient(db, current_user, patient_id)

    # One query feeds both the recent list and the rule-based history analysis.
    history = db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo.is_(True)
    ).order_by(
        SymptomRecord.fecha_registro.desc(), SymptomRecord.id.desc()
    ).limit(HISTORY_WINDOW).all()

    medications = db.query(Medication).filter(
        Medication.patient_id == patient_id,
        Medication.activo.is_(True)
    ).order_by(Medication.hora.asc(), Medication.nombre.asc()).all()

    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.fecha >= local_today(),
        Appointment.estado != "cancelada"
    ).order_by(
        Appointment.fecha.asc(), Appointment.hora.asc()
    ).limit(RECENT_ITEMS).all()

    notes = db.query(CaregiverNote).filter(
        CaregiverNote.patient_id == patient_id,
        CaregiverNote.activo.is_(True)
    ).order_by(
        CaregiverNote.fecha_registro.desc(), CaregiverNote.id.desc()
    ).limit(RECENT_ITEMS).all()

    alerts = db.query(Alert).filter(
        Alert.patient_id == patient_id,
        Alert.activa.is_(True)
    ).order_by(
        Alert.fecha_registro.desc(), Alert.id.desc()
    ).limit(10).all()

    historical_result = analyze_patient_history(history)

    return {
        "patient": PatientResponse.model_validate(patient).model_dump(mode="json"),
        "symptoms": serialize(SymptomRecordResponse, history[:RECENT_ITEMS]),
        "medications": serialize(MedicationResponse, medications),
        "upcoming_appointments": serialize(AppointmentResponse, appointments),
        "recent_notes": serialize(CaregiverNoteResponse, notes),
        "active_alerts": serialize(AlertResponse, alerts),
        "historical_analysis": {
            "registros_analizados": historical_result.registros_analizados,
            "score": historical_result.score,
            "nivel": historical_result.nivel,
            "tendencias": historical_result.tendencias,
            "recomendacion": historical_result.recomendacion
        },
        "current_risk_level": historical_result.nivel,
    }
