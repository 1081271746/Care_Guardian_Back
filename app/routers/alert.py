from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.alert import Alert
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.user import User
from app.schemas.alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.post(
    "/patients/{patient_id}",
    response_model=AlertResponse
)
def create_alert(
    patient_id: int,
    alert_data: AlertCreate,
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

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    new_alert = Alert(
        patient_id=patient_id,
        tipo=alert_data.tipo,
        nivel=alert_data.nivel,
        titulo=alert_data.titulo,
        mensaje=alert_data.mensaje,
        estado=alert_data.estado,
        origen=alert_data.origen
    )

    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    return new_alert


@router.get(
    "/patients/{patient_id}",
    response_model=list[AlertResponse]
)
def get_patient_alerts(
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

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    alerts = db.query(Alert).filter(
        Alert.patient_id == patient_id,
        Alert.activa == True
    ).order_by(
        Alert.fecha_registro.desc()
    ).all()

    return alerts


@router.get(
    "/{alert_id}",
    response_model=AlertResponse
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.get(Alert, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == alert.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    return alert


@router.put(
    "/{alert_id}",
    response_model=AlertResponse
)
def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.get(Alert, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == alert.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    if alert_data.nivel is not None:
        alert.nivel = alert_data.nivel

    if alert_data.titulo is not None:
        alert.titulo = alert_data.titulo

    if alert_data.mensaje is not None:
        alert.mensaje = alert_data.mensaje

    if alert_data.estado is not None:
        alert.estado = alert_data.estado

    if alert_data.activa is not None:
        alert.activa = alert_data.activa

    db.commit()
    db.refresh(alert)

    return alert


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.get(Alert, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == alert.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    alert.activa = False

    db.commit()

    return {
        "mensaje": "Alerta desactivada correctamente"
    }