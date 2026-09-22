from datetime import datetime
from sqlalchemy.orm import relationship

from sqlalchemy import Boolean, DateTime, String, null
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    rol: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="cuidador"
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    relaciones_pacientes = relationship(
        "PatientCaregiver",
        back_populates="user",
        cascade="all, delete-orphan"
    )



    
