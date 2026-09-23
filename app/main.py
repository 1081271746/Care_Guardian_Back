from app.routers.patient import router as patient_router
from fastapi import FastAPI
from app.models.patient_caregiver import PatientCaregiver
from app.routers.medication import router as medication_router

from app.database.base import Base
from app.database.connection import engine
from app.models.user import User
from app.models.patient import Patient
from app.models.medication import Medication
from app.routers.user import router as user_router
from app.routers.auth import router as auth_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CareGuardian API",
    description="Sistema de acompañamiento para cuidadores de adultos mayores",
    version="1.0.0"
)


app.include_router(user_router)
app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(medication_router)

@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a CareGuardian API",
        "estado": "Backend funcionando"
    }