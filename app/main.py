import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.access import enforce_patient_scope

from app.routers.patient import router as patient_router
from app.routers.evolution import router as evolution_router
from app.routers.medication import router as medication_router
from app.routers.appointment import router as appointment_router
from app.routers.symptom_record import router as symptom_router
from app.routers.caregiver_note import router as caregiver_note_router
from app.routers.alert import router as alert_router
from app.routers.analysis import router as analysis_router
from app.routers.dashboard import router as dashboard_router
from app.routers.user import router as user_router
from app.routers.auth import router as auth_router

import app.models  # noqa: F401  (registers every table in Base.metadata)

from app.database.connection import engine


@asynccontextmanager
async def lifespan(app):
    if not os.getenv("SECRET_KEY") or len(os.environ["SECRET_KEY"]) < 32:
        raise RuntimeError(
            "Configura SECRET_KEY con al menos 32 caracteres"
        )

    try:
        timeout = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30"))
        rpm = int(os.getenv("GROQ_REQUESTS_PER_MINUTE", "10"))

        if not 1 <= timeout <= 120 or rpm < 1:
            raise ValueError()

    except ValueError:
        raise RuntimeError(
            "Revisa GROQ_TIMEOUT_SECONDS (1–120) "
            "y GROQ_REQUESTS_PER_MINUTE (entero positivo)"
        )

    yield
    engine.dispose()


app = FastAPI(
    title="CareGuardian API",
    description="Sistema de acompañamiento para cuidadores de adultos mayores",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:4200,http://127.0.0.1:4200"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(user_router)
app.include_router(auth_router)

for scoped_router in (
    patient_router,
    medication_router,
    appointment_router,
    symptom_router,
    caregiver_note_router,
    alert_router,
    analysis_router,
    dashboard_router,
    evolution_router,
):
    app.include_router(
        scoped_router,
        dependencies=[Depends(enforce_patient_scope)]
    )


@app.middleware("http")
async def private_responses(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "ok"}

    except Exception:
        return JSONResponse(
            {"status": "unavailable"},
            status_code=503
        )


@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a CareGuardian API",
        "estado": "Backend funcionando"
    }