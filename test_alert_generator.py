from app.database.connection import SessionLocal
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord
from app.models.patient import Patient  
from app.services.alert_generator import generate_alert_from_symptom
from app.models.user import User


db = SessionLocal()

try:
    symptom = db.query(SymptomRecord).filter(
        SymptomRecord.id == 1
    ).first()

    if symptom is None:
        print("No se encontró el síntoma con ID 1.")
    else:
        alert = generate_alert_from_symptom(
            symptom,
            db
        )

        if alert is None:
            print("No se generó alerta porque el nivel de riesgo es bajo.")
        else:
            print("🚨 ALERTA GENERADA")
            print("ID:", alert.id)
            print("Paciente:", alert.patient_id)
            print("Nivel:", alert.nivel)
            print("Tipo:", alert.tipo)
            print("Título:", alert.titulo)
            print("Mensaje:", alert.mensaje)
            print("Origen:", alert.origen)
            print("Activa:", alert.activa)

finally:
    db.close()