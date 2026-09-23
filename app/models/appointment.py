from datetime import date, time, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    titulo: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    especialidad: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    profesional: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    fecha: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    hora: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    lugar: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pendiente"
    )

    notas: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )