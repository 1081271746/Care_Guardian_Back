from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse
)
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


@router.post(
    "/patients/{patient_id}",
    response_model=AppointmentResponse
)
def create_appointment(
    patient_id: int,
    appointment_data: AppointmentCreate,
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

    new_appointment = Appointment(
        patient_id=patient_id,
        titulo=appointment_data.titulo,
        especialidad=appointment_data.especialidad,
        profesional=appointment_data.profesional,
        fecha=appointment_data.fecha,
        hora=appointment_data.hora,
        lugar=appointment_data.lugar,
        estado=appointment_data.estado,
        notas=appointment_data.notas
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return new_appointment


@router.get(
    "/patients/{patient_id}",
    response_model=list[AppointmentResponse]
)
def get_patient_appointments(
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

    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(
        Appointment.fecha,
        Appointment.hora
    ).all()

    return appointments


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )

    return appointment


@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )

    if appointment_data.titulo is not None:
        appointment.titulo = appointment_data.titulo

    if appointment_data.especialidad is not None:
        appointment.especialidad = appointment_data.especialidad

    if appointment_data.profesional is not None:
        appointment.profesional = appointment_data.profesional

    if appointment_data.fecha is not None:
        appointment.fecha = appointment_data.fecha

    if appointment_data.hora is not None:
        appointment.hora = appointment_data.hora

    if appointment_data.lugar is not None:
        appointment.lugar = appointment_data.lugar

    if appointment_data.estado is not None:
        appointment.estado = appointment_data.estado

    if appointment_data.notas is not None:
        appointment.notas = appointment_data.notas

    db.commit()
    db.refresh(appointment)

    return appointment


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )

    db.delete(appointment)
    db.commit()

    return {
        "mensaje": "Cita eliminada correctamente"
    }