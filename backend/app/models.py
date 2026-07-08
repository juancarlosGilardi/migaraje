from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    brand: Mapped[str] = mapped_column(String(60))
    model: Mapped[str] = mapped_column(String(60))
    year: Mapped[int]
    plate: Mapped[str] = mapped_column(String(10))
    fuel: Mapped[str] = mapped_column(String(20), default="gasolina")
    # Año de 1.ª inscripción en Registros Públicos: base del impuesto vehicular (F5)
    first_registration_year: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="vehicles")
    odometer_logs: Mapped[list["OdometerLog"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class OdometerLog(Base):
    __tablename__ = "odometer_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    km: Mapped[int]
    recorded_on: Mapped[date] = mapped_column(Date, default=date.today)
    source: Mapped[str] = mapped_column(String(10), default="manual")  # manual | photo
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    vehicle: Mapped[Vehicle] = relationship(back_populates="odometer_logs")
