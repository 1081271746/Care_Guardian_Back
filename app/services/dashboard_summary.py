"""Caregiver-wide indicators computed from PostgreSQL on every request.

Nothing here is cached or hard-coded: every number is a COUNT/aggregate over
the patients assigned to the authenticated caregiver.
"""
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func

from app.core.time import app_timezone, as_utc, local_today
from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.caregiver_note import CaregiverNote
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord

UPCOMING_DAYS = 30
RECENT_DAYS = 7
CHART_DAYS = 14
ACTIVITY_ITEMS = 12


def _local_midnight_utc(day):
    return datetime.combine(day, time.min, app_timezone()).astimezone(timezone.utc)


def build_summary(db, user):
    zone = app_timezone()
    today = local_today()
    patient_ids = [row[0] for row in db.query(PatientCaregiver.patient_id).filter(
        PatientCaregiver.user_id == user.id
    ).all()]
    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).order_by(
        Patient.apellidos, Patient.nombres
    ).all() if patient_ids else []
    names = {p.id: f"{p.nombres} {p.apellidos}" for p in patients}

    def scoped(model):
        return db.query(model).filter(model.patient_id.in_(patient_ids))

    def count(query):
        return query.order_by(None).count() if patient_ids else 0

    recent_from = _local_midnight_utc(today - timedelta(days=RECENT_DAYS - 1))
    chart_from = _local_midnight_utc(today - timedelta(days=CHART_DAYS - 1))
    active_symptoms = scoped(SymptomRecord).filter(SymptomRecord.activo.is_(True))
    open_alerts = scoped(Alert).filter(Alert.activa.is_(True))
    upcoming = scoped(Appointment).filter(
        Appointment.fecha >= today,
        Appointment.fecha <= today + timedelta(days=UPCOMING_DAYS),
        Appointment.estado != "cancelada",
    )

    alerts_by_level = {"alto": 0, "medio": 0, "bajo": 0}
    if patient_ids:
        for level, total in db.query(Alert.nivel, func.count(Alert.id)).filter(
            Alert.patient_id.in_(patient_ids), Alert.activa.is_(True)
        ).group_by(Alert.nivel).all():
            alerts_by_level[level] = total

    # Daily symptom counts in the caregiver's calendar; days without records stay 0.
    per_day = {today - timedelta(days=offset): 0 for offset in range(CHART_DAYS)}
    if patient_ids:
        for (registered,) in active_symptoms.filter(
            SymptomRecord.fecha_registro >= chart_from
        ).with_entities(SymptomRecord.fecha_registro).all():
            day = as_utc(registered).astimezone(zone).date()
            if day in per_day:
                per_day[day] += 1

    per_patient_alerts = dict(db.query(Alert.patient_id, func.count(Alert.id)).filter(
        Alert.patient_id.in_(patient_ids), Alert.activa.is_(True)
    ).group_by(Alert.patient_id).all()) if patient_ids else {}
    last_symptom = dict(db.query(SymptomRecord.patient_id, func.max(SymptomRecord.fecha_registro)).filter(
        SymptomRecord.patient_id.in_(patient_ids), SymptomRecord.activo.is_(True)
    ).group_by(SymptomRecord.patient_id).all()) if patient_ids else {}

    activity = []
    if patient_ids:
        sources = (
            ("sintoma", active_symptoms, SymptomRecord.fecha_registro,
             lambda r: f"Síntomas registrados · gravedad {r.nivel_gravedad}"),
            ("nota", scoped(CaregiverNote).filter(CaregiverNote.activo.is_(True)), CaregiverNote.fecha_registro,
             lambda r: "Nota del cuidador"),
            ("alerta", scoped(Alert), Alert.fecha_registro,
             lambda r: f"Alerta {r.nivel}: {r.titulo}"),
            ("medicamento", scoped(Medication), Medication.fecha_registro,
             lambda r: f"Medicamento registrado: {r.nombre}"),
            ("cita", scoped(Appointment), Appointment.fecha_registro,
             lambda r: f"Cita registrada: {r.titulo}"),
        )
        for kind, query, column, describe in sources:
            for record in query.order_by(column.desc()).limit(ACTIVITY_ITEMS).all():
                activity.append({
                    "id": f"{kind}-{record.id}",
                    "tipo": kind,
                    "patient_id": record.patient_id,
                    "paciente": names.get(record.patient_id, ""),
                    "descripcion": describe(record),
                    "fecha": as_utc(record.fecha_registro).isoformat(),
                })
    activity.sort(key=lambda item: (item["fecha"], item["id"]), reverse=True)

    next_visits = upcoming.order_by(Appointment.fecha, Appointment.hora).limit(5).all() if patient_ids else []

    return {
        "generado": datetime.now(zone).isoformat(),
        "zona_horaria": str(zone),
        "totales": {
            "pacientes": len(patients),
            "pacientes_activos": sum(1 for p in patients if p.activo),
            "medicamentos_activos": count(scoped(Medication).filter(Medication.activo.is_(True))),
            "medicamentos_registrados": count(scoped(Medication)),
            "citas_proximas": count(upcoming),
            "sintomas_recientes": count(active_symptoms.filter(SymptomRecord.fecha_registro >= recent_from)),
            "notas_recientes": count(scoped(CaregiverNote).filter(
                CaregiverNote.activo.is_(True), CaregiverNote.fecha_registro >= recent_from)),
            "alertas_pendientes": count(open_alerts),
        },
        "ventanas": {"citas_dias": UPCOMING_DAYS, "recientes_dias": RECENT_DAYS},
        "alertas_por_nivel": alerts_by_level,
        "sintomas_por_dia": [
            {"fecha": day.isoformat(), "cantidad": per_day[day]} for day in sorted(per_day)
        ],
        "proximas_citas": [{
            "id": visit.id, "patient_id": visit.patient_id, "paciente": names.get(visit.patient_id, ""),
            "titulo": visit.titulo, "especialidad": visit.especialidad, "profesional": visit.profesional,
            "fecha": visit.fecha.isoformat(), "hora": visit.hora.strftime("%H:%M"),
            "lugar": visit.lugar, "estado": visit.estado,
        } for visit in next_visits],
        "pacientes": [{
            "id": p.id, "nombre": names[p.id], "activo": p.activo,
            "alertas_activas": per_patient_alerts.get(p.id, 0),
            "ultimo_registro": as_utc(last_symptom[p.id]).isoformat() if p.id in last_symptom else None,
        } for p in patients],
        "actividad_reciente": activity[:ACTIVITY_ITEMS],
    }
