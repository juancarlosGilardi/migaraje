from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
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
    drivers: Mapped[list["Driver"]] = relationship(
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
    service_records: Mapped[list["ServiceRecord"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    legal_documents: Mapped[list["LegalDocument"]] = relationship(
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


class ServiceRecord(Base):
    __tablename__ = "service_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    service_date: Mapped[date] = mapped_column(Date, default=date.today)
    km: Mapped[int | None]
    service_type: Mapped[str] = mapped_column(String(120))
    cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    workshop: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ruc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    vehicle: Mapped[Vehicle] = relationship(back_populates="service_records")
    files: Mapped[list["ServiceFile"]] = relationship(
        back_populates="service_record", cascade="all, delete-orphan"
    )


class ServiceFile(Base):
    __tablename__ = "service_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_record_id: Mapped[int] = mapped_column(ForeignKey("service_records.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    service_record: Mapped[ServiceRecord] = relationship(back_populates="files")


class Driver(Base):
    """Conductor (no necesariamente el dueño de la cuenta) — para el brevete."""

    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    license_class: Mapped[str] = mapped_column(String(20), default="A-I")
    license_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="drivers")


class LegalDocument(Base):
    """SOAT o revisión técnica (CITV) de un vehículo. El impuesto vehicular no
    se guarda aquí: se calcula al vuelo desde Vehicle.first_registration_year."""

    __tablename__ = "legal_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    doc_type: Mapped[str] = mapped_column(String(20))  # 'soat' | 'citv'
    reference_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    expiry_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    vehicle: Mapped[Vehicle] = relationship(back_populates="legal_documents")

    __table_args__ = (
        UniqueConstraint("vehicle_id", "doc_type", name="uq_legal_document_vehicle_type"),
    )


class MaintenanceComponent(Base):
    """Catálogo de componentes mantenibles (motor, frenos, transmisión...) con
    su intervalo típico. Sirve para el selector al agregar un ítem al plan de
    cualquier vehículo — no depende de marca/modelo."""

    __tablename__ = "maintenance_components"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    category: Mapped[str] = mapped_column(String(40))
    default_interval_km: Mapped[int | None]
    default_interval_months: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CatalogMake(Base):
    """Marca de vehículo del catálogo propio (importado de NHTSA + agregados curados para Perú)."""

    __tablename__ = "catalog_makes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    # 'nhtsa' (importado del proxy NHTSA) | 'custom' (agregado a mano para el mercado peruano)
    source: Mapped[str] = mapped_column(String(20), default="nhtsa")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    models: Mapped[list["CatalogModel"]] = relationship(
        back_populates="make", cascade="all, delete-orphan"
    )


class CatalogModel(Base):
    """Modelo de vehículo asociado a una marca del catálogo propio."""

    __tablename__ = "catalog_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    make_id: Mapped[int] = mapped_column(ForeignKey("catalog_makes.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    source: Mapped[str] = mapped_column(String(20), default="nhtsa")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    make: Mapped[CatalogMake] = relationship(back_populates="models")

    __table_args__ = (
        # Evita duplicar el mismo modelo dentro de una marca (permite idempotencia en el import).
        UniqueConstraint("make_id", "name", name="uq_catalog_model_make_name"),
    )
