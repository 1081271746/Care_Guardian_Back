from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.access import require_patient, require_record
from app.core.dependencies import get_current_user
from app.core.time import local_today
from app.database.connection import get_db
from app.models.appointment import Appointment
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse
)


router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)

NOT_FOUND = "Cita no encontrada"


@router.post(
    "/patients/{patient_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(
    patient_id: int,
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id, active=True)

    if appointment_data.estado == "pendiente" and appointment_data.fecha < local_today():
        raise HTTPException(
            status_code=422,
            detail="Una cita pendiente no puede programarse en una fecha pasada",
        )

    new_appointment = Appointment(patient_id=patient_id, **appointment_data.model_dump())

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
    proximas: bool = Query(False, description="Solo citas desde hoy (zona APP_TIMEZONE), no canceladas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id)

    query = db.query(Appointment).filter(Appointment.patient_id == patient_id)
    if proximas:
        query = query.filter(
            Appointment.fecha >= local_today(),
            Appointment.estado != "cancelada",
        )

    return query.order_by(Appointment.fecha, Appointment.hora, Appointment.id).all()


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return require_record(db, current_user, Appointment, appointment_id, not_found=NOT_FOUND)


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
    appointment = require_record(db, current_user, Appointment, appointment_id, not_found=NOT_FOUND, active=True)
    changes = appointment_data.model_dump(exclude_unset=True)

    for required in ("titulo", "especialidad", "profesional", "fecha", "hora", "estado"):
        if required in changes and changes[required] is None:
            raise HTTPException(status_code=422, detail=f"El campo {required} no puede quedar vacío")

    new_date = changes.get("fecha", appointment.fecha)
    new_status = changes.get("estado", appointment.estado)
    if ("fecha" in changes or "estado" in changes) and new_status == "pendiente" and new_date < local_today():
        raise HTTPException(
            status_code=422,
            detail="Una cita pendiente no puede quedar en una fecha pasada; márcala como completada o cancelada",
        )

    for field, value in changes.items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)

    return appointment


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = require_record(db, current_user, Appointment, appointment_id, not_found=NOT_FOUND)

    db.delete(appointment)
    db.commit()

    return {
        "mensaje": "Cita eliminada correctamente"
    }
