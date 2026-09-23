from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.caregiver_note import CaregiverNote
from app.models.user import User
from app.schemas.caregiver_note import (
    CaregiverNoteCreate,
    CaregiverNoteUpdate,
    CaregiverNoteResponse
)


router = APIRouter(
    prefix="/notes",
    tags=["Caregiver Notes"]
)


@router.post(
    "/patients/{patient_id}",
    response_model=CaregiverNoteResponse
)
def create_note(
    patient_id: int,
    note_data: CaregiverNoteCreate,
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

    new_note = CaregiverNote(
        patient_id=patient_id,
        caregiver_id=current_user.id,
        contenido=note_data.contenido
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note


@router.get(
    "/patients/{patient_id}",
    response_model=list[CaregiverNoteResponse]
)
def get_patient_notes(
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

    notes = db.query(CaregiverNote).filter(
        CaregiverNote.patient_id == patient_id,
        CaregiverNote.activo == True
    ).order_by(
        CaregiverNote.fecha_registro.desc()
    ).all()

    return notes


@router.get(
    "/{note_id}",
    response_model=CaregiverNoteResponse
)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.get(CaregiverNote, note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota no encontrada"
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == note.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    return note


@router.put(
    "/{note_id}",
    response_model=CaregiverNoteResponse
)
def update_note(
    note_id: int,
    note_data: CaregiverNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.get(CaregiverNote, note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota no encontrada"
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == note.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    if note_data.contenido is not None:
        note.contenido = note_data.contenido

    if note_data.activo is not None:
        note.activo = note_data.activo

    db.commit()
    db.refresh(note)

    return note


@router.delete("/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.get(CaregiverNote, note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota no encontrada"
        )

    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == note.patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    note.activo = False

    db.commit()

    return {
        "mensaje": "Nota desactivada correctamente"
    }