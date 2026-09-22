from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PatientCaregiver(Base):
    __tablename__ = "patient_caregivers"

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
        default=datetime.utcnow
    )

    patient = relationship(
        "Patient",
        back_populates="relaciones_cuidadores"
    )

    user = relationship(
        "User",
        back_populates="relaciones_pacientes"
    )