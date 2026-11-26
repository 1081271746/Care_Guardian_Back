from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.access import assigned_patient_ids, require_patient
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.user import User
from app.schemas.caregiver import CaregiverAssignmentCreate, CaregiverResponse
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate

router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


def document_taken(db: Session, documento: str, *, exclude_id: int | None = None) -> bool:
    query = db.query(Patient.id).filter(Patient.documento == documento)
    if exclude_id is not None:
        query = query.filter(Patient.id != exclude_id)
    return query.first() is not None


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar paciente (queda asignado a quien lo crea)",
)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if document_taken(db, patient_data.documento):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un paciente con ese documento"
        )

    new_patient = Patient(**patient_data.model_dump())

    db.add(new_patient)
    db.flush()

    # Asignar automáticamente el paciente al cuidador creador.
    new_assignment = PatientCaregiver(
        patient_id=new_patient.id,
        user_id=current_user.id,
        rol="cuidador"
    )

    db.add(new_assignment)
    db.commit()

    db.refresh(new_patient)

    return new_patient


@router.get("/", response_model=list[PatientResponse], summary="Pacientes asignados")
def get_patients(
    q: str | None = Query(None, max_length=100, description="Buscar por nombre o documento"),
    activos: bool | None = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Patient).filter(
        Patient.id.in_(assigned_patient_ids(db, current_user))
    )
    if activos is not None:
        query = query.filter(Patient.activo.is_(activos))
    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        query = query.filter(or_(
            func.lower(Patient.nombres).like(term),
            func.lower(Patient.apellidos).like(term),
            func.lower(Patient.documento).like(term),
        ))
    return query.order_by(Patient.apellidos.asc(), Patient.nombres.asc(), Patient.id.asc()).all()


@router.get("/{patient_id}", response_model=PatientResponse, summary="Consultar paciente")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Explicit check in addition to the router-level scope dependency.
    return require_patient(db, current_user, patient_id)


@router.put("/{patient_id}", response_model=PatientResponse, summary="Actualizar paciente")
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = require_patient(db, current_user, patient_id)
    changes = patient_data.model_dump(exclude_unset=True)

    for required in ("nombres", "apellidos", "fecha_nacimiento", "documento", "activo"):
        if required in changes and changes[required] is None:
            raise HTTPException(status_code=422, detail=f"El campo {required} no puede quedar vacío")

    if "documento" in changes and document_taken(db, changes["documento"], exclude_id=patient_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un paciente con ese documento"
        )

    # exclude_unset lets optional contact fields be cleared with null.
    for field, value in changes.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    return patient


@router.delete("/{patient_id}", summary="Desactivar paciente (conserva el historial)")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate instead of deleting: the clinical history must be preserved."""
    patient = require_patient(db, current_user, patient_id)
    patient.activo = False
    db.commit()

    return {
        "mensaje": "Paciente desactivado correctamente; su historial se conserva",
        "id": patient.id,
        "activo": False,
    }


@router.post(
    "/{patient_id}/caregivers",
    status_code=status.HTTP_201_CREATED,
    summary="Asignar cuidador por correo o id",
)
def assign_caregiver(
    patient_id: int,
    assignment: CaregiverAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id, active=True)

    if assignment.email is not None:
        user = db.query(User).filter(func.lower(User.email) == assignment.email).first()
    else:
        user = db.get(User, assignment.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un usuario con esos datos"
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario está inactivo"
        )

    existing_assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == patient_id,
        PatientCaregiver.user_id == user.id
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya está asignado a este paciente"
        )

    new_assignment = PatientCaregiver(
        patient_id=patient_id,
        user_id=user.id,
        rol=assignment.rol
    )

    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return {
        "mensaje": "Cuidador asignado correctamente",
        "asignacion": {
            "id": new_assignment.id,
            "patient_id": new_assignment.patient_id,
            "user_id": new_assignment.user_id,
            "rol": new_assignment.rol,
            "fecha_asignacion": new_assignment.fecha_asignacion
        }
    }


@router.get("/{patient_id}/caregivers", response_model=list[CaregiverResponse], summary="Equipo de cuidado")
def get_patient_caregivers(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_patient(db, current_user, patient_id)

    caregivers = (
        db.query(PatientCaregiver, User)
        .join(User, PatientCaregiver.user_id == User.id)
        .filter(PatientCaregiver.patient_id == patient_id)
        .order_by(PatientCaregiver.fecha_asignacion.asc(), PatientCaregiver.id.asc())
        .all()
    )

    return [
        CaregiverResponse(user_id=user.id, nombre=user.nombre, email=user.email, rol=assignment.rol)
        for assignment, user in caregivers
    ]


@router.delete("/{patient_id}/caregivers/{user_id}", summary="Desasignar cuidador")
def remove_caregiver(
    patient_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_patient(db, current_user, patient_id)
    assignments = db.query(PatientCaregiver).filter(PatientCaregiver.patient_id == patient_id).all()
    target = next((a for a in assignments if a.user_id == user_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="El usuario no está asignado a este paciente")
    if len(assignments) == 1:
        raise HTTPException(status_code=409, detail="El paciente debe conservar al menos un cuidador")
    db.delete(target)
    db.commit()
    return {"mensaje": "Cuidador desasignado correctamente"}
