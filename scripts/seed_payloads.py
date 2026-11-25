"""Deterministic, fictional fixtures matching the API schemas.

Every record carries a ``CG-DEMO-<namespace>-<resource>-<index>`` marker in an
identity field so reruns reconcile instead of duplicating. Names and titles are
readable but always labelled "(demo)": none of this is clinical information.
"""
from datetime import date, datetime, time, timedelta, timezone
import re
from hashlib import sha256

DEFAULT_COUNTS = {
    "patients": 6, "medications": 18, "appointments": 12,
    "symptoms": 84, "notes": 24, "alerts": 6,
}
# Field that holds the marker and identifies the record on reruns.
IDENTITY_FIELDS = {
    "medications": "indicaciones", "appointments": "notas",
    "symptoms": "observaciones", "notes": "contenido", "alerts": "mensaje",
}

FIRST_NAMES = ["Elena", "Joaquín", "Rosa", "Ernesto", "Lucía", "Hernando", "Marta", "Alberto"]
MEDICATIONS = [
    ("Vitamina D (demo)", "1 cápsula", "diaria", "08:00"),
    ("Calcio (demo)", "1 tableta", "cada 12 horas", "09:00"),
    ("Suplemento B12 (demo)", "1 tableta", "diaria", "13:00"),
    ("Hidratante cutáneo (demo)", "aplicación local", "cada 8 horas", "20:00"),
]
APPOINTMENTS = [
    ("Control general (demo)", "Medicina general", "Dra. Ficticia Ramírez"),
    ("Revisión de visión (demo)", "Oftalmología", "Dr. Ficticio Torres"),
    ("Terapia física (demo)", "Fisioterapia", "Ft. Ficticia Gómez"),
    ("Control nutricional (demo)", "Nutrición", "Nut. Ficticio León"),
]
MOODS = ["tranquilo", "estable", "alegre", "tranquilo", "regular", "triste", "estable"]
APPETITES = ["normal", "bueno", "normal", "regular", "normal", "bajo", "normal"]
NOTES = [
    "Caminó 15 minutos por el patio y conversó con la familia.",
    "Participó en la actividad de lectura y almorzó completo.",
    "Se mostró atento durante la visita y pidió ver fotografías.",
    "Realizó los ejercicios de movilidad sugeridos sin molestias.",
    "Tarde tranquila; escuchó música y tomó suficiente agua.",
    "Durmió poco y amaneció más callado de lo habitual.",
]
ALERTS = [
    ("Revisar hidratación (demo)", "medio"),
    ("Confirmar cita de control (demo)", "bajo"),
    ("Observar calidad del sueño (demo)", "medio"),
]


def validate_namespace(namespace):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,24}", namespace):
        raise ValueError("El espacio de prueba debe tener 1–24 letras, números, guiones o guiones bajos")
    return namespace


def marker(namespace, resource, index):
    validate_namespace(namespace)
    return f"CG-DEMO-{namespace}-{resource}-{index:04d}"


def patient_payload(namespace, index):
    return {
        "nombres": f"{FIRST_NAMES[index % len(FIRST_NAMES)]} (demo)",
        "apellidos": f"Paciente ficticio {index + 1}",
        "fecha_nacimiento": f"{1938 + index % 22}-0{1 + index % 9}-15",
        # PostgreSQL patients.documento is VARCHAR(30).
        "documento": "CG-DEMO-" + sha256(marker(namespace, "patients", index).encode()).hexdigest()[:20],
        "telefono": f"+57 300 000 {index % 10000:04d}",
        "contacto_emergencia": "Contacto ficticio (demo)",
    }


def _observed_at(index, now):
    """Spread observations over the last weeks at plausible local hours (UTC-5)."""
    days_back = (index // 2) % 28 + 1
    hour_utc = 13 if index % 2 == 0 else 23  # 08:00 and 18:00 in Bogotá
    moment = datetime.combine((now - timedelta(days=days_back)).date(), time(hour_utc), timezone.utc)
    return min(moment, now - timedelta(minutes=5)).isoformat()


def resource_payload(namespace, resource, index, today=None, now=None):
    tag = marker(namespace, resource, index)
    day = today or date.today()
    now = now or datetime.now(timezone.utc)
    if resource == "medications":
        nombre, dosis, frecuencia, hora = MEDICATIONS[index % len(MEDICATIONS)]
        return {"nombre": nombre, "dosis": dosis, "frecuencia": frecuencia, "hora": hora,
                "fecha_inicio": (day - timedelta(days=7 + index % 21)).isoformat(),
                "indicaciones": f"{tag} · Registro ficticio de demostración, no es una prescripción."}
    if resource == "appointments":
        titulo, especialidad, profesional = APPOINTMENTS[index % len(APPOINTMENTS)]
        return {"titulo": titulo, "especialidad": especialidad, "profesional": profesional,
                "fecha": (day + timedelta(days=1 + index % 20)).isoformat(),
                "hora": f"{8 + index % 8:02d}:30", "estado": "pendiente",
                "lugar": "Sede ficticia de demostración",
                "notas": f"{tag} · Cita ficticia, no asistir."}
    if resource == "symptoms":
        wave = (index * 7) % 10
        return {"observaciones": f"{tag} · Observación ficticia de demostración.",
                "nivel_dolor": [1, 2, 2, 3, 2, 4, 3, 2, 1, 2][wave],
                "calidad_sueno": [7, 8, 6, 7, 5, 6, 7, 8, 6, 7][wave],
                # Varies across the indexes that land on the same patient (stride = patients).
                "temperatura": round(36.1 + ((index * 5 + index // 6) % 7) / 10, 1),
                "nivel_gravedad": "bajo",
                "estado_animo": MOODS[index % len(MOODS)],
                "apetito": APPETITES[index % len(APPETITES)],
                "fecha_registro": _observed_at(index, now)}
    if resource == "notes":
        return {"contenido": f"{tag} · (demo) {NOTES[index % len(NOTES)]}",
                "fecha_registro": _observed_at(index * 3 + 1, now)}
    if resource == "alerts":
        titulo, nivel = ALERTS[index % len(ALERTS)]
        return {"titulo": f"{titulo} #{index + 1}", "tipo": "manual", "nivel": nivel, "estado": "pendiente",
                "mensaje": f"{tag} · Alerta ficticia de demostración; no representa una urgencia."}
    raise ValueError("Recurso no admitido")
