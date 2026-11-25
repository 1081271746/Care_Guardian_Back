from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.database.base import Base


class SymptomRecord(Base):
    __tablename__ = "symptom_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    caregiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    calidad_sueno: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    estado_animo: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    apetito: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    nivel_dolor: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    temperatura: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    nivel_gravedad: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="bajo"
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )