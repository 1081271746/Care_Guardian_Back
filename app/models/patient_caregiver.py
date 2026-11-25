from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.database.base import Base


class PatientCaregiver(Base):
    __tablename__ = "patient_caregivers"
    __table_args__ = (
        Index("uq_patient_caregivers_patient_user", "patient_id", "user_id", unique=True),
        Index("ix_patient_caregivers_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    rol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="cuidador"
    )

    fecha_asignacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    patient = relationship(
        "Patient",
        back_populates="relaciones_cuidadores"
    )

    user = relationship(
        "User",
        back_populates="relaciones_pacientes"
    )