"""Deterministic, fictional fixtures matching the existing API schemas."""
from datetime import date, timedelta
import re
from hashlib import sha256

DEFAULT_COUNTS = {
    "patients": 10, "medications": 20, "appointments": 20,
    "symptoms": 30, "notes": 20, "alerts": 30,
}
IDENTITY_FIELDS = {
    "medications": "nombre", "appointments": "titulo",
    "symptoms": "observaciones", "notes": "contenido", "alerts": "titulo",
}


def validate_namespace(namespace):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,24}", namespace):
        raise ValueError("El espacio de prueba debe tener 1–24 letras, números, guiones o guiones bajos")
    return namespace


def marker(namespace, resource, index):
    validate_namespace(namespace)
    return f"CG-DEMO-{namespace}-{resource}-{index:04d}"


def patient_payload(namespace, index):
    return {
        "nombres": "Paciente ficticio", "apellidos": f"Demostración {index + 1}",
        "fecha_nacimiento": f"{1945 + index % 25}-06-15",
        # PostgreSQL patients.documento is VARCHAR(30).
        "documento": "CG-DEMO-" + sha256(marker(namespace, "patients", index).encode()).hexdigest()[:20],
    }


def resource_payload(namespace, resource, index, today=None):
    tag = marker(namespace, resource, index)
    day = today or date.today()
    if resource == "medications":
        return {"nombre": tag, "dosis": "Dosis de demostración, no administrar",
                "frecuencia": "diaria", "hora": "08:00",
                "fecha_inicio": (day - timedelta(days=index % 14)).isoformat(),
                "indicaciones": "Registro ficticio para pruebas, no es una prescripción."}
    if resource == "appointments":
        return {"titulo": tag, "especialidad": "Control de demostración",
                "profesional": "Profesional ficticio", "fecha": (day + timedelta(days=index % 14)).isoformat(),
                "hora": "09:00:00", "estado": "pendiente", "notas": "Cita ficticia, no asistir."}
    if resource == "symptoms":
        return {"observaciones": tag, "nivel_dolor": index % 5, "calidad_sueno": 6 + index % 4,
                "temperatura": 36.2 + (index % 5) / 10, "nivel_gravedad": "bajo",
                "estado_animo": "tranquilo", "apetito": "normal"}
    if resource == "notes":
        return {"contenido": tag + " · Acompañamiento ficticio de demostración, sin indicaciones clínicas."}
    if resource == "alerts":
        return {"titulo": tag, "tipo": "manual", "nivel": "bajo", "estado": "pendiente",
                "origen": "manual", "mensaje": "Alerta ficticia de demostración; no representa una urgencia."}
    raise ValueError("Recurso no admitido")
