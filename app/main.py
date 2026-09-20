from fastapi import FastAPI

from app.database.base import Base
from app.database.connection import engine
from app.models.user import User


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CareGuardian API",
    description="Sistema de acompañamiento para cuidadores de adultos mayores",
    version="1.0.0"
)


@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a CareGuardian API",
        "estado": "Backend funcionando"
    }