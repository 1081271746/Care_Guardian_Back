import app.models

from app.database.connection import SessionLocal
from app.models.symptom_record import SymptomRecord
from app.services.alert_generator import generate_alert_from_symptom


db = SessionLocal()

try:
    # Usamos el síntoma nuevo que acabamos de crear
    symptom = db.query(SymptomRecord).filter(
        SymptomRecord.id == 3
    ).first()

    if symptom is None:
        print("❌ No se encontró el síntoma con ID 3.")
    else:
        print("🩺 Síntoma encontrado")
        print("ID:", symptom.id)
        print("Paciente:", symptom.patient_id)

        alert = generate_alert_from_symptom(symptom, db)

        if alert is None:
            print("ℹ️ No se generó alerta porque el riesgo es bajo.")
        else:
            print("\n🚨 RESULTADO")
            print("ID alerta:", alert.id)
            print("Paciente:", alert.patient_id)
            print("Síntoma origen:", alert.symptom_id)
            print("Nivel:", alert.nivel)
            print("Tipo:", alert.tipo)
            print("Estado:", alert.estado)
            print("Activa:", alert.activa)

finally:
    db.close()