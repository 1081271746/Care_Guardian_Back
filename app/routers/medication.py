from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.access import require_patient, require_record
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.medication import Medication
from app.models.user import User
from app.schemas.medication import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse
)


router = APIRouter(
    prefix="/medications",
    tags=["Medications"]
)

NOT_FOUND = "Medicamento no encontrado"


@router.post(
    "/patients/{patient_id}",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_medication(
    patient_id: int,
    medication_data: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id, active=True)

    new_medication = Medication(patient_id=patient_id, **medication_data.model_dump())

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
    activos: bool | None = Query(None, description="true: solo activos; false: solo suspendidos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id)

    query = db.query(Medication).filter(Medication.patient_id == patient_id)
    if activos is not None:
        query = query.filter(Medication.activo.is_(activos))

    return query.order_by(
        Medication.activo.desc(), Medication.hora.asc(), Medication.nombre.asc(), Medication.id.asc()
    ).all()


@router.get(
    "/{medication_id}",
    response_model=MedicationResponse
)
def get_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return require_record(db, current_user, Medication, medication_id, not_found=NOT_FOUND)


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
    medication = require_record(db, current_user, Medication, medication_id, not_found=NOT_FOUND, active=True)
    changes = medication_data.model_dump(exclude_unset=True)

    for required in ("nombre", "dosis", "frecuencia", "hora", "fecha_inicio", "activo"):
        if required in changes and changes[required] is None:
            raise HTTPException(status_code=422, detail=f"El campo {required} no puede quedar vacío")

    start = changes.get("fecha_inicio", medication.fecha_inicio)
    end = changes.get("fecha_fin", medication.fecha_fin)
    if end is not None and end < start:
        raise HTTPException(
            status_code=422,
            detail="La fecha de finalización no puede ser anterior a la de inicio",
        )

    for field, value in changes.items():
        setattr(medication, field, value)

    db.commit()
    db.refresh(medication)

    return medication


@router.delete("/{medication_id}")
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suspend the medication; the record stays in the patient's history."""
    medication = require_record(db, current_user, Medication, medication_id, not_found=NOT_FOUND)
    medication.activo = False
    db.commit()

    return {
        "mensaje": "Medicamento suspendido correctamente",
        "id": medication.id,
        "activo": False,
    }
