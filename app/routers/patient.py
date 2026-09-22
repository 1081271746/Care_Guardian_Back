from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.patient_caregiver import PatientCaregiver
from app.schemas.caregiver import CaregiverAssignmentCreate

from app.database.connection import get_db
from app.models.patient import Patient
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse
)
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


@router.post("/", response_model=PatientResponse)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_patient = db.query(Patient).filter(
        Patient.documento == patient_data.documento
    ).first()

    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un paciente con ese documento"
        )

    new_patient = Patient(
        nombres=patient_data.nombres,
        apellidos=patient_data.apellidos,
        fecha_nacimiento=patient_data.fecha_nacimiento,
        documento=patient_data.documento,
        telefono=patient_data.telefono,
        direccion=patient_data.direccion,
        contacto_emergencia=patient_data.contacto_emergencia,
        telefono_emergencia=patient_data.telefono_emergencia
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return new_patient


@router.get("/", response_model=list[PatientResponse])
def get_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patients = db.query(Patient).all()

    return patients


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )

    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )

    if patient_data.nombres is not None:
        patient.nombres = patient_data.nombres

    if patient_data.apellidos is not None:
        patient.apellidos = patient_data.apellidos

    if patient_data.fecha_nacimiento is not None:
        patient.fecha_nacimiento = patient_data.fecha_nacimiento

    if patient_data.documento is not None:
        patient.documento = patient_data.documento

    if patient_data.telefono is not None:
        patient.telefono = patient_data.telefono

    if patient_data.direccion is not None:
        patient.direccion = patient_data.direccion

    if patient_data.contacto_emergencia is not None:
        patient.contacto_emergencia = patient_data.contacto_emergencia

    if patient_data.telefono_emergencia is not None:
        patient.telefono_emergencia = patient_data.telefono_emergencia

    if patient_data.activo is not None:
        patient.activo = patient_data.activo

    db.commit()
    db.refresh(patient)

    return patient


@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )

    db.delete(patient)
    db.commit()

    return {
        "mensaje": "Paciente eliminado correctamente"
    }

@router.post("/{patient_id}/caregivers")
def assign_caregiver(
    patient_id: int,
    assignment: CaregiverAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )

    user = db.get(User, assignment.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario está inactivo"
        )

    existing_assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == patient_id,
        PatientCaregiver.user_id == assignment.user_id
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya está asignado a este paciente"
        )

    new_assignment = PatientCaregiver(
        patient_id=patient_id,
        user_id=assignment.user_id,
        rol=assignment.rol
    )

    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return {
        "mensaje": "Cuidador asignado correctamente",
        "asignacion": {
            "id": new_assignment.id,
            "patient_id": new_assignment.patient_id,
            "user_id": new_assignment.user_id,
            "rol": new_assignment.rol,
            "fecha_asignacion": new_assignment.fecha_asignacion
        }
    }