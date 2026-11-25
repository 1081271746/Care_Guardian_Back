from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.access import require_patient, require_record
from app.core.dependencies import get_current_user
from app.core.time import utc_now
from app.database.connection import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import (
    CLOSED_STATUSES,
    AlertCreate,
    AlertUpdate,
    AlertResponse
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)

NOT_FOUND = "Alerta no encontrada"
DUPLICATE_WINDOW = timedelta(hours=24)


@router.post(
    "/patients/{patient_id}",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_alert(
    patient_id: int,
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id, active=True)

    duplicate = db.query(Alert.id).filter(
        Alert.patient_id == patient_id,
        Alert.activa.is_(True),
        func.lower(Alert.titulo) == alert_data.titulo.lower(),
        Alert.fecha_registro >= utc_now() - DUPLICATE_WINDOW,
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una alerta activa con ese título en las últimas 24 horas",
        )

    new_alert = Alert(patient_id=patient_id, **alert_data.model_dump())
    new_alert.activa = alert_data.estado not in CLOSED_STATUSES

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
    incluir_cerradas: bool = Query(False, description="Incluir alertas atendidas o descartadas"),
    nivel: str | None = Query(None, pattern="^(bajo|medio|alto)$"),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id)

    query = db.query(Alert).filter(Alert.patient_id == patient_id)
    if not incluir_cerradas:
        query = query.filter(Alert.activa.is_(True))
    if nivel:
        query = query.filter(Alert.nivel == nivel)

    return query.order_by(Alert.fecha_registro.desc(), Alert.id.desc()).limit(limit).all()


@router.get(
    "/{alert_id}",
    response_model=AlertResponse
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return require_record(db, current_user, Alert, alert_id, not_found=NOT_FOUND)


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
    alert = require_record(db, current_user, Alert, alert_id, not_found=NOT_FOUND, active=True)
    changes = alert_data.model_dump(exclude_none=True)

    for field, value in changes.items():
        setattr(alert, field, value)

    # The status drives visibility unless the caller sets activa explicitly.
    if "estado" in changes and "activa" not in changes:
        alert.activa = alert.estado not in CLOSED_STATUSES

    db.commit()
    db.refresh(alert)

    return alert


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = require_record(db, current_user, Alert, alert_id, not_found=NOT_FOUND)

    alert.activa = False
    if alert.estado not in CLOSED_STATUSES:
        alert.estado = "descartada"

    db.commit()

    return {
        "mensaje": "Alerta desactivada correctamente"
    }
