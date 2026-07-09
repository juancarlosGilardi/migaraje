from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# --- Auth ---
class RegisterIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Vehículos ---
class VehicleIn(BaseModel):
    brand: str = Field(min_length=2, max_length=60)
    model: str = Field(min_length=1, max_length=60)
    year: int = Field(ge=1950, le=2035)
    plate: str = Field(min_length=6, max_length=10)
    fuel: str = "gasolina"
    first_registration_year: int | None = Field(default=None, ge=1950, le=2035)
    initial_km: int = Field(default=0, ge=0)


class VehicleUpdate(BaseModel):
    brand: str | None = Field(default=None, min_length=2, max_length=60)
    model: str | None = Field(default=None, min_length=1, max_length=60)
    year: int | None = Field(default=None, ge=1950, le=2035)
    plate: str | None = Field(default=None, min_length=6, max_length=10)
    fuel: str | None = None
    first_registration_year: int | None = Field(default=None, ge=1950, le=2035)


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    year: int
    plate: str
    fuel: str
    first_registration_year: int | None
    current_km: int = 0
    spec: dict[str, Any] | None = None


# --- Kilometraje ---
class OdometerIn(BaseModel):
    km: int = Field(ge=0)
    recorded_on: date | None = None
    source: str = "manual"


class OdometerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    km: int
    recorded_on: date
    source: str


# --- Plan de mantenimiento ---
class PlanItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    interval_km: int | None = Field(default=None, ge=1)
    interval_months: int | None = Field(default=None, ge=1)
    last_service_km: int | None = Field(default=None, ge=0)
    last_service_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _at_least_one_interval(self):
        if self.interval_km is None and self.interval_months is None:
            raise ValueError("Indica un intervalo por kilometraje o por meses")
        return self


class PlanItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    interval_km: int | None = Field(default=None, ge=1)
    interval_months: int | None = Field(default=None, ge=1)
    last_service_km: int | None = Field(default=None, ge=0)
    last_service_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class PlanItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    interval_km: int | None
    interval_months: int | None
    last_service_km: int | None
    last_service_date: date | None
    notes: str | None
    due_km: int | None = None
    km_remaining: int | None = None
    due_date: date | None = None
    days_remaining: int | None = None
    percent: float = 0
    status: str = "ok"


# --- Historial de servicios / facturas ---
class InvoiceItemOut(BaseModel):
    description: str
    amount: float


class OilMatchOut(BaseModel):
    matches: bool | None = None
    message: str | None = None


class InvoicePreviewOut(BaseModel):
    """Vista previa de un XML SUNAT parseado, aún no guardado."""

    upload_token: str
    filename: str
    is_xml: bool
    invoice_number: str | None = None
    issue_date: str | None = None
    currency: str | None = None
    supplier_name: str | None = None
    supplier_ruc: str | None = None
    items: list[InvoiceItemOut] = []
    total: float | None = None
    suggested_service_type: str | None = None
    oil_match: OilMatchOut = OilMatchOut()
    parse_error: str | None = None


class ServiceRecordIn(BaseModel):
    upload_token: str | None = None
    service_date: date
    km: int | None = Field(default=None, ge=0)
    service_type: str = Field(min_length=2, max_length=120)
    cost: float | None = Field(default=None, ge=0)
    workshop: str | None = Field(default=None, max_length=160)
    ruc: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=2000)


class ServiceFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    is_xml: bool = False


class ServiceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_date: date
    km: int | None
    service_type: str
    cost: float | None
    workshop: str | None
    ruc: str | None
    notes: str | None
    has_pdf: bool = False
    has_xml: bool = False
    files: list[ServiceFileOut] = []


# --- Papeles: conductores (brevete) ---
class DriverIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    license_class: str = Field(default="A-I", max_length=20)
    license_expiry: date | None = None
    birth_date: date | None = None


class DriverUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    license_class: str | None = Field(default=None, max_length=20)
    license_expiry: date | None = None
    birth_date: date | None = None


class DriverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    license_class: str
    license_expiry: date | None
    birth_date: date | None
    has_data: bool = False
    days_remaining: int | None = None
    status: str = "unknown"
    age: int | None = None
    renewal_period_years: int | None = None


# --- Papeles: SOAT / revisión técnica / impuesto vehicular ---
class LegalDocumentIn(BaseModel):
    reference_number: str | None = Field(default=None, max_length=60)
    expiry_date: date


class LegalDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_type: str
    reference_number: str | None = None
    expiry_date: date | None = None
    has_data: bool = False
    has_history: bool | None = None
    days_remaining: int | None = None
    status: str = "unknown"
    message: str | None = None
    first_due_year: int | None = None


class ImpuestoVehicularOut(BaseModel):
    applicable: bool | None
    reason: str | None = None
    year_index: int | None = None
    quota_number: int | None = None
    next_due_date: date | None = None
    days_remaining: int | None = None
    status: str = "unknown"
    message: str | None = None


class VehicleDocumentsOut(BaseModel):
    soat: LegalDocumentOut
    citv: LegalDocumentOut
    impuesto_vehicular: ImpuestoVehicularOut
