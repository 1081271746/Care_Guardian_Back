from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.alert_generator import generate_alert_from_symptom
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord
from app.models.user import User
from app.schemas.symptom_record import (
    SymptomRecordCreate,
    SymptomRecordUpdate,
    SymptomRecordResponse
)


router = APIRouter(
    prefix="/symptoms",
    tags=["Symptoms"]
)


@router.post(
    "/patients/{patient_id}",
    response_model=SymptomRecordResponse
)
def create_symptom_record(
    patient_id: int,
    symptom_data: SymptomRecordCreate,
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

    new_record = SymptomRecord(
        patient_id=patient_id,
        caregiver_id=current_user.id,
        calidad_sueno=symptom_data.calidad_sueno,
        estado_animo=symptom_data.estado_animo,
        apetito=symptom_data.apetito,
        nivel_dolor=symptom_data.nivel_dolor,
        temperatura=symptom_data.temperatura,
        observaciones=symptom_data.observaciones,
        nivel_gravedad=symptom_data.nivel_gravedad
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    # Analizar automáticamente el nivel de riesgo
    generate_alert_from_symptom(new_record, db)

    return new_record



@router.get(
    "/patients/{patient_id}",
    response_model=list[SymptomRecordResponse]
)
def get_patient_symptoms(
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

    records = db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo == True
    ).order_by(
        SymptomRecord.fecha_registro.desc()
    ).all()

    return records


@router.get(
    "/{symptom_id}",
    response_model=SymptomRecordResponse
)
def get_symptom_record(
    symptom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.get(SymptomRecord, symptom_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de síntomas no encontrado"
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == record.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    return record


@router.put(
    "/{symptom_id}",
    response_model=SymptomRecordResponse
)
def update_symptom_record(
    symptom_id: int,
    symptom_data: SymptomRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.get(SymptomRecord, symptom_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de síntomas no encontrado"
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == record.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    if symptom_data.calidad_sueno is not None:
        record.calidad_sueno = symptom_data.calidad_sueno

    if symptom_data.estado_animo is not None:
        record.estado_animo = symptom_data.estado_animo

    if symptom_data.apetito is not None:
        record.apetito = symptom_data.apetito

    if symptom_data.nivel_dolor is not None:
        record.nivel_dolor = symptom_data.nivel_dolor

    if symptom_data.temperatura is not None:
        record.temperatura = symptom_data.temperatura

    if symptom_data.observaciones is not None:
        record.observaciones = symptom_data.observaciones

    if symptom_data.nivel_gravedad is not None:
        record.nivel_gravedad = symptom_data.nivel_gravedad

    if symptom_data.activo is not None:
        record.activo = symptom_data.activo

    db.commit()
    db.refresh(record)

    return record


@router.delete("/{symptom_id}")
def delete_symptom_record(
    symptom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.get(SymptomRecord, symptom_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == record.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    record.activo = False

    db.commit()

    return {
        "mensaje": "Registro de síntomas desactivado correctamente"
    }