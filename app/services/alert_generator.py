from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.symptom_record import SymptomRecord
from app.services.risk_analysis import analyze_symptoms

LEVEL_ORDER = {"bajo": 0, "medio": 1, "alto": 2}


def _escalate(existing: Alert, nivel: str, mensaje: str) -> Alert:
    """Reuse an open alert, raising its level when the new evaluation is worse."""
    if LEVEL_ORDER.get(nivel, 0) > LEVEL_ORDER.get(existing.nivel, 0):
        existing.nivel = nivel
        existing.mensaje = mensaje
    return existing


def generate_alert_from_symptom(
    symptom: SymptomRecord,
    db: Session
):
    result = analyze_symptoms(symptom)

    # Si el riesgo es bajo, no se genera alerta
    if result.nivel == "bajo":
        return None

    # Evitar alertas duplicadas para el mismo síntoma
    existing_alert = db.query(Alert).filter(
        Alert.symptom_id == symptom.id,
        Alert.activa.is_(True)
    ).first()

    factores = ", ".join(result.factores)
    mensaje = (
        f"Se identificaron los siguientes factores: {factores}. "
        f"Puntuación de riesgo: {result.score}. "
        f"{result.recomendacion}"
    )

    if existing_alert is not None:
        return _escalate(existing_alert, result.nivel, mensaje)

    alert = Alert(
        patient_id=symptom.patient_id,
        symptom_id=symptom.id,
        tipo="evaluacion_riesgo",
        nivel=result.nivel,
        titulo="Posible cambio en el estado del paciente",
        mensaje=mensaje,
        estado="pendiente",
        origen="sistema",
        activa=True
    )

    db.add(alert)
    # The caller commits, so the source record and its alert are saved atomically.
    db.flush()

    return alert

def generate_alert_from_history(patient_id: int, result, db: Session):
    """
    Genera una alerta a partir del análisis histórico de síntomas.
    Evita crear múltiples alertas activas para el mismo análisis.
    """

    if result.nivel == "bajo":
        return None

    existing_alert = db.query(Alert).filter(
        Alert.patient_id == patient_id,
        Alert.tipo == "evaluacion_historica",
        Alert.activa.is_(True)
    ).first()

    tendencias = ", ".join(result.tendencias)
    mensaje = (
        f"El análisis de los registros recientes detectó las siguientes "
        f"tendencias: {tendencias}. "
        f"Puntuación de riesgo: {result.score}. "
        f"{result.recomendacion}"
    )

    if existing_alert is not None:
        return _escalate(existing_alert, result.nivel, mensaje)

    alert = Alert(
        patient_id=patient_id,
        symptom_id=None,
        tipo="evaluacion_historica",
        nivel=result.nivel,
        titulo="Riesgo detectado en la evolución del paciente",
        mensaje=mensaje,
        estado="pendiente",
        origen="analisis_historico",
        activa=True
    )

    db.add(alert)
    # The caller commits, so the source record and its alert are saved atomically.
    db.flush()

    return alert


def generate_alert_from_note(note, result, db: Session):
    """
    Genera una alerta a partir del análisis de una nota del cuidador.
    Evita crear más de una alerta activa para la misma nota.
    """

    if result.nivel == "bajo":
        return None

    existing_alert = db.query(Alert).filter(
        Alert.note_id == note.id,
        Alert.activa.is_(True)
    ).first()

    factores = ", ".join(result.factores)
    mensaje = (
        f"Se identificaron los siguientes factores en la nota: "
        f"{factores}. "
        f"Puntuación de riesgo: {result.score}. "
        f"{result.recomendacion}"
    )

    if existing_alert is not None:
        return _escalate(existing_alert, result.nivel, mensaje)

    alert = Alert(
        patient_id=note.patient_id,
        symptom_id=None,
        note_id=note.id,
        tipo="evaluacion_nota",
        nivel=result.nivel,
        titulo="Posibles cambios detectados en una nota del cuidador",
        mensaje=mensaje,
        estado="pendiente",
        origen="analisis_nota",
        activa=True
    )

    db.add(alert)
    # The caller commits, so the source record and its alert are saved atomically.
    db.flush()

    return alert