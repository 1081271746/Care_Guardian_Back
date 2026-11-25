from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.access import require_patient, require_record
from app.core.dependencies import get_current_user
from app.core.time import utc_now
from app.database.connection import get_db
from app.models.caregiver_note import CaregiverNote
from app.models.user import User
from app.schemas.caregiver_note import (
    CaregiverNoteCreate,
    CaregiverNoteUpdate,
    CaregiverNoteResponse
)
from app.services.alert_generator import generate_alert_from_note
from app.services.note_analysis import analyze_caregiver_note


router = APIRouter(
    prefix="/notes",
    tags=["Caregiver Notes"]
)

NOT_FOUND = "Nota no encontrada"


@router.post(
    "/patients/{patient_id}",
    response_model=CaregiverNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nota"
)
def create_note(
    patient_id: int,
    note_data: CaregiverNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id, active=True)

    new_note = CaregiverNote(
        patient_id=patient_id,
        caregiver_id=current_user.id,
        contenido=note_data.contenido,
        fecha_registro=note_data.fecha_registro or utc_now(),
    )

    db.add(new_note)
    db.flush()

    # Analizar automáticamente la nota y generar alerta si se detecta un riesgo
    generate_alert_from_note(new_note, analyze_caregiver_note(new_note.contenido), db)

    db.commit()
    db.refresh(new_note)

    return new_note


@router.get(
    "/patients/{patient_id}",
    response_model=list[CaregiverNoteResponse],
    summary="Historial de notas"
)
def get_patient_notes(
    patient_id: int,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id)

    return db.query(CaregiverNote).filter(
        CaregiverNote.patient_id == patient_id,
        CaregiverNote.activo.is_(True)
    ).order_by(
        CaregiverNote.fecha_registro.desc(), CaregiverNote.id.desc()
    ).offset(offset).limit(limit).all()


@router.get(
    "/{note_id}",
    response_model=CaregiverNoteResponse,
    summary="Consultar nota"
)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return require_record(db, current_user, CaregiverNote, note_id, not_found=NOT_FOUND)


@router.put(
    "/{note_id}",
    response_model=CaregiverNoteResponse,
    summary="Editar nota (solo autor)"
)
def update_note(
    note_id: int,
    note_data: CaregiverNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = require_record(db, current_user, CaregiverNote, note_id, not_found=NOT_FOUND, active=True)

    if note.caregiver_id != current_user.id:
        # Teammates can read each other's notes but only the author edits them.
        raise HTTPException(status_code=403, detail="Solo el autor puede modificar esta nota")

    if note_data.contenido is not None:
        note.contenido = note_data.contenido
        if note.activo:
            generate_alert_from_note(note, analyze_caregiver_note(note.contenido), db)

    if note_data.activo is not None:
        note.activo = note_data.activo

    db.commit()
    db.refresh(note)

    return note


@router.delete("/{note_id}",
    summary="Desactivar nota (solo autor)"
)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = require_record(db, current_user, CaregiverNote, note_id, not_found=NOT_FOUND)

    if note.caregiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el autor puede eliminar esta nota")

    note.activo = False

    db.commit()

    return {
        "mensaje": "Nota desactivada correctamente"
    }
