from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, func
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
    # Ficha técnica (aceite, llantas, batería, combustible) copiada de la plantilla al crear
    spec_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="vehicles")
    odometer_logs: Mapped[list["OdometerLog"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    plan_items: Mapped[list["PlanItem"]] = relationship(
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


class PlanItem(Base):
    __tablename__ = "plan_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    interval_km: Mapped[int | None]
    interval_months: Mapped[int | None]
    last_service_km: Mapped[int | None]
    last_service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    vehicle: Mapped[Vehicle] = relationship(back_populates="plan_items")
