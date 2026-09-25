from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    symptom_id: Mapped[int | None] = mapped_column(
    ForeignKey("symptom_records.id"),
    nullable=True
)

    note_id: Mapped[int | None] = mapped_column(
    ForeignKey("caregiver_notes.id"),
    nullable=True
)


    tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    nivel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medio"
    )

    titulo: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    mensaje: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pendiente"
    )

    origen: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="sistema"
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    activa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )