"""Object-level authorization shared by old and new patient routes."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.caregiver_note import CaregiverNote
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord


def require_patient(db, user, patient_id, *, active=False):
    assignment = db.query(PatientCaregiver).filter_by(
        patient_id=patient_id, user_id=user.id
    ).first()
    # Do not disclose whether another caregiver's patient exists.
    if assignment is None:
        raise HTTPException(403, "No tienes acceso a este paciente")
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "Paciente no encontrado")
    if active and not patient.activo:
        raise HTTPException(400, "El paciente está inactivo")
    return patient


def assigned_patient_ids(db, user):
    """Subquery with the ids of every patient assigned to ``user``."""
    return db.query(PatientCaregiver.patient_id).filter(
        PatientCaregiver.user_id == user.id
    )


def require_record(db, user, model, record_id, *, not_found="Registro no encontrado", active=False):
    """Load a patient-owned record and verify the caller is assigned to its patient.

    ``active=True`` is used by write operations: an inactive patient's history
    is read-only until the patient is reactivated.
    """
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(404, not_found)
    require_patient(db, user, record.patient_id, active=active)
    return record


def enforce_patient_scope(
    request: Request, db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    params = request.path_params
    def identifier(key):
        try:
            return int(params[key])
        except (TypeError, ValueError):
            raise HTTPException(422, "El identificador debe ser un número entero") from None
    if "patient_id" in params:
        require_patient(db, user, identifier("patient_id"))
        return
    for key, model in (
        ("medication_id", Medication), ("appointment_id", Appointment),
        ("symptom_id", SymptomRecord), ("note_id", CaregiverNote),
        ("alert_id", Alert),
    ):
        if key in params:
            record = db.get(model, identifier(key))
            if record is None:
                raise HTTPException(404, "Registro no encontrado")
            require_patient(db, user, record.patient_id)
            return
