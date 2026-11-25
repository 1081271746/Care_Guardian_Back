from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.access import require_patient, require_record
from app.core.dependencies import get_current_user
from app.core.time import utc_now
from app.database.connection import get_db
from app.models.symptom_record import SymptomRecord
from app.models.user import User
from app.schemas.symptom_record import SymptomRecordCreate, SymptomRecordResponse, SymptomRecordUpdate
from app.services.alert_generator import generate_alert_from_symptom

router = APIRouter(
    prefix="/symptoms",
    tags=["Symptoms"]
)

NOT_FOUND = "Registro de síntomas no encontrado"
MEASUREMENTS = ("calidad_sueno", "estado_animo", "apetito", "nivel_dolor", "temperatura", "observaciones")


@router.post(
    "/patients/{patient_id}",
    response_model=SymptomRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar síntomas"
)
def create_symptom_record(
    patient_id: int,
    symptom_data: SymptomRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id, active=True)

    data = symptom_data.model_dump()
    if all(data[field] is None for field in MEASUREMENTS):
        raise HTTPException(
            status_code=422,
            detail="Registra al menos una medición u observación",
        )

    data["fecha_registro"] = data["fecha_registro"] or utc_now()
    new_record = SymptomRecord(patient_id=patient_id, caregiver_id=current_user.id, **data)

    db.add(new_record)
    db.flush()

    # Analizar automáticamente el nivel de riesgo (misma transacción)
    generate_alert_from_symptom(new_record, db)

    db.commit()
    db.refresh(new_record)

    return new_record


@router.get(
    "/patients/{patient_id}",
    response_model=list[SymptomRecordResponse],
    summary="Historial de síntomas"
)
def get_patient_symptoms(
    patient_id: int,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id)

    return db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo.is_(True)
    ).order_by(
        SymptomRecord.fecha_registro.desc(), SymptomRecord.id.desc()
    ).offset(offset).limit(limit).all()


@router.get(
    "/{symptom_id}",
    response_model=SymptomRecordResponse,
    summary="Consultar registro"
)
def get_symptom_record(
    symptom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return require_record(db, current_user, SymptomRecord, symptom_id, not_found=NOT_FOUND)


@router.put(
    "/{symptom_id}",
    response_model=SymptomRecordResponse,
    summary="Corregir registro"
)
def update_symptom_record(
    symptom_id: int,
    symptom_data: SymptomRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = require_record(db, current_user, SymptomRecord, symptom_id, not_found=NOT_FOUND, active=True)
    changes = symptom_data.model_dump(exclude_unset=True)

    for required in ("nivel_gravedad", "activo"):
        if required in changes and changes[required] is None:
            raise HTTPException(status_code=422, detail=f"El campo {required} no puede quedar vacío")

    for field, value in changes.items():
        setattr(record, field, value)

    if record.activo:
        # A corrected measurement can reveal a risk that the original did not.
        generate_alert_from_symptom(record, db)

    db.commit()
    db.refresh(record)

    return record


@router.delete("/{symptom_id}",
    summary="Desactivar registro"
)
def delete_symptom_record(
    symptom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = require_record(db, current_user, SymptomRecord, symptom_id, not_found=NOT_FOUND)

    record.activo = False

    db.commit()

    return {
        "mensaje": "Registro de síntomas desactivado correctamente"
    }
