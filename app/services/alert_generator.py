from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.symptom_record import SymptomRecord
from app.services.risk_analysis import analyze_symptoms


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
        Alert.activa == True
    ).first()

    if existing_alert is not None:
        return existing_alert

    factores = ", ".join(result.factores)

    alert = Alert(
        patient_id=symptom.patient_id,
        symptom_id=symptom.id,
        tipo="evaluacion_riesgo",
        nivel=result.nivel,
        titulo="Posible cambio en el estado del paciente",
        mensaje=(
            f"Se identificaron los siguientes factores: {factores}. "
            f"Puntuación de riesgo: {result.score}. "
            f"{result.recomendacion}"
        ),
        estado="pendiente",
        origen="sistema",
        activa=True
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

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
        Alert.activa == True
    ).first()

    if existing_alert is not None:
        return existing_alert

    tendencias = ", ".join(result.tendencias)

    alert = Alert(
        patient_id=patient_id,
        symptom_id=None,
        tipo="evaluacion_historica",
        nivel=result.nivel,
        titulo="Riesgo detectado en la evolución del paciente",
        mensaje=(
            f"El análisis de los registros recientes detectó las siguientes "
            f"tendencias: {tendencias}. "
            f"Puntuación de riesgo: {result.score}. "
            f"{result.recomendacion}"
        ),
        estado="pendiente",
        origen="analisis_historico",
        activa=True
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

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
        Alert.activa == True
    ).first()

    if existing_alert is not None:
        return existing_alert

    factores = ", ".join(result.factores)

    alert = Alert(
        patient_id=note.patient_id,
        symptom_id=None,
        note_id=note.id,
        tipo="evaluacion_nota",
        nivel=result.nivel,
        titulo="Posibles cambios detectados en una nota del cuidador",
        mensaje=(
            f"Se identificaron los siguientes factores en la nota: "
            f"{factores}. "
            f"Puntuación de riesgo: {result.score}. "
            f"{result.recomendacion}"
        ),
        estado="pendiente",
        origen="analisis_nota",
        activa=True
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert