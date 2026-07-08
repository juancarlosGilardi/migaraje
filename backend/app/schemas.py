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
