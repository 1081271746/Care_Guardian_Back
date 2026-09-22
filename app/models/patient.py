from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    nombres: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    apellidos: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    fecha_nacimiento: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    documento: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    telefono: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    direccion: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    contacto_emergencia: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    telefono_emergencia: Mapped[str | None] = mapped_column(
        String(20),
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