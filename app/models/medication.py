from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    dosis: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    frecuencia: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    hora: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    fecha_inicio: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    fecha_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    indicaciones: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )