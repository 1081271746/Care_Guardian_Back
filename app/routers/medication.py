from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.user import User
from app.schemas.medication import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse
)
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/medications",
    tags=["Medications"]
)


@router.post(
    "/patients/{patient_id}",
    response_model=MedicationResponse
)
def create_medication(
    patient_id: int,
    medication_data: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

    new_medication = Medication(
        patient_id=patient_id,
        nombre=medication_data.nombre,
        dosis=medication_data.dosis,
        frecuencia=medication_data.frecuencia,
        hora=medication_data.hora,
        fecha_inicio=medication_data.fecha_inicio,
        fecha_fin=medication_data.fecha_fin,
        indicaciones=medication_data.indicaciones
    )

    db.add(new_medication)
    db.commit()
    db.refresh(new_medication)

    return new_medication


@router.get(
    "/patients/{patient_id}",
    response_model=list[MedicationResponse]
)
def get_patient_medications(
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

    medications = db.query(Medication).filter(
        Medication.patient_id == patient_id
    ).all()

    return medications


@router.get(
    "/{medication_id}",
    response_model=MedicationResponse
)
def get_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    medication = db.get(Medication, medication_id)

    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicamento no encontrado"
        )

    return medication


@router.put(
    "/{medication_id}",
    response_model=MedicationResponse
)
def update_medication(
    medication_id: int,
    medication_data: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    medication = db.get(Medication, medication_id)

    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicamento no encontrado"
        )

    if medication_data.nombre is not None:
        medication.nombre = medication_data.nombre

    if medication_data.dosis is not None:
        medication.dosis = medication_data.dosis

    if medication_data.frecuencia is not None:
        medication.frecuencia = medication_data.frecuencia

    if medication_data.hora is not None:
        medication.hora = medication_data.hora

    if medication_data.fecha_inicio is not None:
        medication.fecha_inicio = medication_data.fecha_inicio

    if medication_data.fecha_fin is not None:
        medication.fecha_fin = medication_data.fecha_fin

    if medication_data.indicaciones is not None:
        medication.indicaciones = medication_data.indicaciones

    if medication_data.activo is not None:
        medication.activo = medication_data.activo

    db.commit()
    db.refresh(medication)

    return medication


@router.delete("/{medication_id}")
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    medication = db.get(Medication, medication_id)

    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicamento no encontrado"
        )

    db.delete(medication)
    db.commit()

    return {
        "mensaje": "Medicamento eliminado correctamente"
    }