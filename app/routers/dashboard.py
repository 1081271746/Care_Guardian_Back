
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db

from app.models.user import User
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord
from app.models.medication import Medication
from app.models.appointment import Appointment
from app.models.caregiver_note import CaregiverNote
from app.models.alert import Alert

from app.services.historical_analysis import analyze_patient_history


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


def _to_iso(value):
    """Convert dates and datetimes to ISO strings."""
    return value.isoformat() if value is not None else None


def _register_latest_activity(activity_map, patient_id, timestamp):
    """Keep the latest activity timestamp for each patient."""
    if timestamp is None:
        return

    current = activity_map.get(patient_id)

    if current is None or timestamp > current:
        activity_map[patient_id] = timestamp


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    today = now.date()

    # Dashboard time windows
    citas_dias = 30
    recientes_dias = 14

    recent_start = today - timedelta(days=recientes_dias - 1)
    appointment_end = today + timedelta(days=citas_dias)

    recent_datetime = datetime.combine(
        recent_start,
        datetime.min.time(),
        tzinfo=timezone.utc
    )

    # Only patients assigned to the authenticated caregiver
    patient_ids = [
        row[0]
        for row in db.query(PatientCaregiver.patient_id)
        .filter(PatientCaregiver.user_id == current_user.id)
        .all()
    ]

    patients = []

    if patient_ids:
        patients = (
            db.query(Patient)
            .filter(Patient.id.in_(patient_ids))
            .order_by(Patient.id.asc())
            .all()
        )

    ids = [patient.id for patient in patients]

    # Empty collections for caregivers without assigned patients
    symptoms = []
    medications = []
    recent_medications = []
    appointments = []
    recent_appointments = []
    notes = []
    alerts = []

    if ids:
        symptoms = (
            db.query(SymptomRecord)
            .filter(
                SymptomRecord.patient_id.in_(ids),
                SymptomRecord.activo.is_(True),
                SymptomRecord.fecha_registro >= recent_datetime
            )
            .order_by(SymptomRecord.fecha_registro.desc())
            .all()
        )

        medications = (
            db.query(Medication)
            .filter(Medication.patient_id.in_(ids))
            .all()
        )

        recent_medications = (
    db.query(Medication)
    .filter(
        Medication.patient_id.in_(ids),
        Medication.fecha_registro >= recent_datetime
    )
    .all()
)

        appointments = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id.in_(ids),
                Appointment.fecha >= today,
                Appointment.fecha <= appointment_end,
                Appointment.estado != "cancelada"
            )
            .order_by(
                Appointment.fecha.asc(),
                Appointment.hora.asc()
            )
            .all()
        )

        recent_appointments = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id.in_(ids),
                Appointment.fecha_registro >= recent_datetime
            )
            .order_by(Appointment.fecha_registro.desc())
            .all()
        )

        notes = (
            db.query(CaregiverNote)
            .filter(
                CaregiverNote.patient_id.in_(ids),
                CaregiverNote.activo.is_(True),
                CaregiverNote.fecha_registro >= recent_datetime
            )
            .order_by(CaregiverNote.fecha_registro.desc())
            .all()
        )

        alerts = (
            db.query(Alert)
            .filter(
                Alert.patient_id.in_(ids),
                Alert.activa.is_(True)
            )
            .order_by(Alert.fecha_registro.desc())
            .all()
        )

    # Patient names
    patient_names = {
        patient.id: f"{patient.nombres} {patient.apellidos}".strip()
        for patient in patients
    }

    # Pending alerts
    pending_alerts = [
        alert for alert in alerts
        if alert.estado == "pendiente"
    ]

    # Active alerts grouped by severity
    alert_levels = {
        "bajo": 0,
        "medio": 0,
        "alto": 0
    }

    for alert in alerts:
        if alert.nivel in alert_levels:
            alert_levels[alert.nivel] += 1

    # Symptoms grouped by day, including days without records
    daily_counts = {}

    for day_offset in range(recientes_dias):
        day = recent_start + timedelta(days=day_offset)
        daily_counts[day.isoformat()] = 0

    for symptom in symptoms:
        day = symptom.fecha_registro.date().isoformat()

        if day in daily_counts:
            daily_counts[day] += 1

    # Latest activity and active alerts per patient
    patient_alert_counts = {
        patient_id: 0 for patient_id in ids
    }

    patient_last_activity = {
        patient_id: None for patient_id in ids
    }

    for alert in alerts:
        patient_alert_counts[alert.patient_id] += 1

        _register_latest_activity(
            patient_last_activity,
            alert.patient_id,
            alert.fecha_registro
        )

    for symptom in symptoms:
        _register_latest_activity(
            patient_last_activity,
            symptom.patient_id,
            symptom.fecha_registro
        )

    for note in notes:
        _register_latest_activity(
            patient_last_activity,
            note.patient_id,
            note.fecha_registro
        )

    for medication in medications:
        _register_latest_activity(
            patient_last_activity,
            medication.patient_id,
            medication.fecha_registro
        )

    for appointment in recent_appointments:
        _register_latest_activity(
            patient_last_activity,
            appointment.patient_id,
            appointment.fecha_registro
        )

    # Patient summary
    patient_summary = [
        {
            "id": patient.id,
            "nombre": patient_names[patient.id],
            "activo": patient.activo,
            "alertas_activas": patient_alert_counts[patient.id],
            "ultimo_registro": _to_iso(
                patient_last_activity[patient.id]
            )
        }
        for patient in patients
    ]

    # Upcoming appointments
    upcoming_summary = [
        {
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "titulo": appointment.titulo,
            "especialidad": appointment.especialidad,
            "profesional": appointment.profesional,
            "fecha": _to_iso(appointment.fecha),
            "hora": _to_iso(appointment.hora),
            "lugar": appointment.lugar,
            "estado": appointment.estado,
            "paciente": patient_names.get(
                appointment.patient_id, ""
            )
        }
        for appointment in appointments[:5]
    ]

    # Recent activity
    activity = []

    for symptom in symptoms:
        activity.append({
            "id": f"sintoma-{symptom.id}",
            "tipo": "sintoma",
            "patient_id": symptom.patient_id,
            "paciente": patient_names.get(symptom.patient_id, ""),
            "descripcion": "Nuevo registro de síntomas",
            "fecha": _to_iso(symptom.fecha_registro)
        })

    for note in notes:
        activity.append({
            "id": f"nota-{note.id}",
            "tipo": "nota",
            "patient_id": note.patient_id,
            "paciente": patient_names.get(note.patient_id, ""),
            "descripcion": "Nueva nota de seguimiento",
            "fecha": _to_iso(note.fecha_registro)
        })

    for alert in alerts:
        activity.append({
            "id": f"alerta-{alert.id}",
            "tipo": "alerta",
            "patient_id": alert.patient_id,
            "paciente": patient_names.get(alert.patient_id, ""),
            "descripcion": alert.titulo,
            "fecha": _to_iso(alert.fecha_registro)
        })

    for medication in recent_medications:
        activity.append({
            "id": f"medicamento-{medication.id}",
            "tipo": "medicamento",
            "patient_id": medication.patient_id,
            "paciente": patient_names.get(medication.patient_id, ""),
            "descripcion": f"Medicamento registrado: {medication.nombre}",
            "fecha": _to_iso(medication.fecha_registro)
        })

    for appointment in recent_appointments:
        activity.append({
            "id": f"cita-{appointment.id}",
            "tipo": "cita",
            "patient_id": appointment.patient_id,
            "paciente": patient_names.get(appointment.patient_id, ""),
            "descripcion": f"Cita programada: {appointment.titulo}",
            "fecha": _to_iso(appointment.fecha_registro)
        })

    activity.sort(
        key=lambda item: item["fecha"] or "",
        reverse=True
    )

    # Final response
    return {
        "generado": now.isoformat(),
        "zona_horaria": "UTC",

        "totales": {
            "pacientes": len(patients),
            "pacientes_activos": sum(
                1 for patient in patients if patient.activo
            ),
            "medicamentos_activos": sum(
                1 for medication in medications if medication.activo
            ),
            "medicamentos_registrados": len(medications),
            "citas_proximas": len(appointments),
            "sintomas_recientes": len(symptoms),
            "notas_recientes": len(notes),
            "alertas_pendientes": len(pending_alerts)
        },

        "ventanas": {
            "citas_dias": citas_dias,
            "recientes_dias": recientes_dias
        },

        "alertas_por_nivel": alert_levels,

        "sintomas_por_dia": [
            {
                "fecha": day,
                "cantidad": count
            }
            for day, count in daily_counts.items()
        ],

        "proximas_citas": upcoming_summary,

        "pacientes": patient_summary,

        "actividad_reciente": activity[:10]
    }


@router.get("/patients/{patient_id}")
def get_patient_dashboard(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify patient
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

    # 2. Verify caregiver assignment
    assignment = db.query(PatientCaregiver).filter(
        PatientCaregiver.patient_id == patient_id,
        PatientCaregiver.user_id == current_user.id
    ).first()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no está asignado a este paciente"
        )

    # 3. Latest symptoms
    symptoms = db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo.is_(True)
    ).order_by(
        SymptomRecord.fecha_registro.desc()
    ).limit(5).all()

    # 4. Active medications
    medications = db.query(Medication).filter(
        Medication.patient_id == patient_id,
        Medication.activo.is_(True)
    ).all()

    # 5. Upcoming appointments
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.fecha >= date.today(),
        Appointment.estado != "cancelada"
    ).order_by(
        Appointment.fecha.asc(),
        Appointment.hora.asc()
    ).limit(5).all()

    # 6. Recent notes
    notes = db.query(CaregiverNote).filter(
        CaregiverNote.patient_id == patient_id,
        CaregiverNote.activo.is_(True)
    ).order_by(
        CaregiverNote.fecha_registro.desc()
    ).limit(5).all()

    # 7. Active alerts
    alerts = db.query(Alert).filter(
        Alert.patient_id == patient_id,
        Alert.activa.is_(True)
    ).order_by(
        Alert.fecha_registro.desc()
    ).limit(10).all()

    # 8. Historical analysis
    historical_symptoms = db.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.activo.is_(True)
    ).order_by(
        SymptomRecord.fecha_registro.desc()
    ).limit(10).all()

    historical_result = analyze_patient_history(
        historical_symptoms
    )

    # 9. Current risk level
    risk_level = historical_result.nivel

    # 10. Build response
    return {
        "patient": {
            "id": patient.id,
            "nombres": patient.nombres,
            "apellidos": patient.apellidos,
            "fecha_nacimiento": patient.fecha_nacimiento,
            "documento": patient.documento,
            "telefono": patient.telefono,
            "direccion": patient.direccion,
            "contacto_emergencia": patient.contacto_emergencia,
            "telefono_emergencia": patient.telefono_emergencia
        },

        "symptoms": symptoms,
        "medications": medications,
        "upcoming_appointments": appointments,
        "recent_notes": notes,
        "active_alerts": alerts,

        "historical_analysis": {
            "registros_analizados": historical_result.registros_analizados,
            "score": historical_result.score,
            "nivel": historical_result.nivel,
            "tendencias": historical_result.tendencias,
            "recomendacion": historical_result.recomendacion
        },

        "current_risk_level": risk_level
    }
