from datetime import date, datetime, time, timedelta, timezone
from statistics import mean
from fastapi import HTTPException
from app.models.symptom_record import SymptomRecord
from app.models.medication import Medication
from app.models.appointment import Appointment
from app.models.caregiver_note import CaregiverNote
from app.models.alert import Alert

MAX_RECORDS = 2000


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def evolution(db, patient_id, period):
    start = datetime.combine(period.desde, time.min, timezone.utc) if period.desde else None
    # date.max has no following day; no stored date can exceed it.
    next_day = period.hasta + timedelta(days=1) if period.hasta and period.hasta < date.max else None
    end = datetime.combine(next_day, time.min, timezone.utc) if next_day else None
    sources = (
        ("sintoma", SymptomRecord, "activo"),
        ("medicamento", Medication, None),
        ("cita", Appointment, None),
        ("nota", CaregiverNote, "activo"),
        ("alerta", Alert, "activa"),
    )
    rows = {}
    events = []
    for kind, model, active in sources:
        query = db.query(model).filter(model.patient_id == patient_id)
        if active:
            query = query.filter(getattr(model, active).is_(True))
        # The timeline uses the occurrence date of appointments and medication starts.
        column = model.fecha if kind == "cita" else model.fecha_inicio if kind == "medicamento" else model.fecha_registro
        if start:
            query = query.filter(column >= (period.desde if kind in ("cita", "medicamento") else start))
        if end:
            query = query.filter(column < (next_day if kind in ("cita", "medicamento") else end))
        records = query.order_by(column.asc(), model.id.asc()).limit(MAX_RECORDS + 1).all()
        if len(records) > MAX_RECORDS:
            raise HTTPException(422, "Demasiados registros; selecciona un período más corto")
        rows[kind] = records
        for record in records:
            timestamp = (
                datetime.combine(record.fecha, record.hora, timezone.utc) if kind == "cita"
                else datetime.combine(record.fecha_inicio, time.min, timezone.utc) if kind == "medicamento"
                else utc(record.fecha_registro)
            )
            description = (
                record.contenido if kind == "nota" else record.mensaje if kind == "alerta"
                else f"{record.nombre} · {record.dosis} · {record.frecuencia}" if kind == "medicamento"
                else f"{record.titulo} · {record.estado}" if kind == "cita"
                else record.observaciones or "Registro de síntomas"
            )
            events.append({"id": f"{kind}-{record.id}", "tipo": kind,
                           "fecha": timestamp.isoformat(), "descripcion": description})
    symptoms = rows["sintoma"]
    metrics = {}
    facts = {}
    for field, label, unit in (
        ("nivel_dolor", "Dolor", "/10"),
        ("calidad_sueno", "Calidad del sueño", "/10"),
        ("temperatura", "Temperatura", " °C"),
    ):
        values = [getattr(r, field) for r in symptoms if getattr(r, field) is not None]
        points = [{"fecha": utc(r.fecha_registro).isoformat(), "valor": getattr(r, field)}
                  for r in symptoms if getattr(r, field) is not None]
        metrics[field] = {
            "cantidad": len(values), "promedio": round(mean(values), 2) if values else None,
            "inicial": values[0] if values else None, "ultimo": values[-1] if values else None,
            "cambio": round(values[-1] - values[0], 2) if len(values) > 1 else None,
            "puntos": points,
        }
        if values:
            facts[field] = (
                f"{label}: {len(values)} mediciones; promedio {round(mean(values), 2)}{unit}."
                + (f" Primera {values[0]}{unit}, última {values[-1]}{unit}; "
                   f"cambio {round(values[-1] - values[0], 2):+}{unit}."
                   if len(values) > 1 else " No hay suficientes mediciones para comparar.")
            )
    # No free text (names, notes, observations, medication names, identifiers) goes to Groq.
    for kind, label in (("sintoma", "síntomas"), ("nota", "notas del cuidador"),
                        ("medicamento", "inicios de medicamentos"), ("cita", "citas"),
                        ("alerta", "alertas activas")):
        facts[f"total_{kind}"] = f"Hay {len(rows[kind])} registros de {label} en el período."
    return {
        "patient_id": patient_id, "periodo": period.model_dump(mode="json", include={"desde", "hasta"}),
        "totales": {kind: len(records) for kind, records in rows.items()},
        "metricas": metrics, "hechos": facts,
        "historial": sorted(events, key=lambda event: (event["fecha"], event["id"]), reverse=True),
        "datos_suficientes": any(m["cantidad"] >= 2 for m in metrics.values()),
        "nota": "Las diferencias comparan primera y última medición, no prueban una tendencia clínica. "
                "No se registra administración de dosis; no se puede calcular adherencia.",
    }
