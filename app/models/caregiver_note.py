from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CaregiverNote(Base):
    __tablename__ = "caregiver_notes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    caregiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    contenido: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    