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