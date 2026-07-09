"""Reglas peruanas de vencimientos: impuesto vehicular, revisión técnica (CITV),
SOAT y brevete. Fuentes verificadas (ver memoria del proyecto):
- Impuesto vehicular: SAT Lima / MEF — 3 años desde el año siguiente a la
  1.ª inscripción, cuotas último día hábil de feb/may/ago/nov.
- CITV: MTC — particulares, 1.ª revisión al 4.º año de fabricación, luego anual.
- Brevete: MTC — clase A-I vigente 10 años; desde los 70: 5/3/2 años.
"""

from datetime import date

from app.services.date_utils import age_at, last_business_day

# Umbrales de alerta compartidos (días restantes -> estado)
CRITICAL_DAYS = 20
WARN_DAYS = 60


def status_from_days(days_remaining: int | None) -> str:
    if days_remaining is None:
        return "unknown"
    if days_remaining < 0:
        return "overdue"
    if days_remaining <= CRITICAL_DAYS:
        return "critical"
    if days_remaining <= WARN_DAYS:
        return "warn"
    return "ok"


def impuesto_vehicular_status(first_registration_year: int | None, today: date | None = None) -> dict:
    today = today or date.today()
    if first_registration_year is None:
        return {
            "applicable": None,
            "message": "Falta el año de 1.ª inscripción para calcular el impuesto vehicular",
        }

    first_year = first_registration_year + 1
    last_year = first_registration_year + 3
    current_year = today.year

    if current_year < first_year:
        return {
            "applicable": False,
            "reason": "not_yet",
            "message": f"El impuesto vehicular empezará a aplicar en {first_year}",
        }
    if current_year > last_year:
        return {
            "applicable": False,
            "reason": "expired",
            "message": "Ya no aplica: pasaron los 3 años en que se paga este impuesto",
        }

    year_index = current_year - first_registration_year  # 1, 2 o 3
    quotas = [last_business_day(current_year, m) for m in (2, 5, 8, 11)]
    next_quota = next((q for q in quotas if q >= today), None)

    if next_quota is None:
        return {
            "applicable": True,
            "year_index": year_index,
            "quota_number": None,
            "next_due_date": None,
            "days_remaining": None,
            "status": "ok",
            "message": f"Año {year_index} de 3 · cuotas de este año ya vencieron",
        }

    quota_number = quotas.index(next_quota) + 1
    days_remaining = (next_quota - today).days
    return {
        "applicable": True,
        "year_index": year_index,
        "quota_number": quota_number,
        "next_due_date": next_quota,
        "days_remaining": days_remaining,
        "status": status_from_days(days_remaining),
        "message": f"Año {year_index} de 3 · cuota {quota_number}/4",
    }


def citv_status(
    vehicle_year: int | None,
    expiry_date: date | None,
    today: date | None = None,
    is_commercial: bool = False,
) -> dict:
    """Si ya hay un certificado CITV, se rastrea su fecha de vencimiento tal cual
    figura impresa en él (igual que el SOAT) — es más preciso que recalcular desde
    la fecha en que se hizo, porque el centro de inspección ya aplicó el intervalo
    real al emitirlo. Sin certificado, se estima cuándo toca la primera revisión."""
    today = today or date.today()

    if expiry_date is not None:
        days_remaining = (expiry_date - today).days
        return {
            "has_history": True,
            "expiry_date": expiry_date,
            "days_remaining": days_remaining,
            "status": status_from_days(days_remaining),
        }

    if vehicle_year is None:
        return {"has_history": False, "message": "Falta el año del vehículo para estimar tu primera revisión"}

    # Sin historial: se estima cuándo toca la primera revisión (aproximado: no
    # tenemos la fecha exacta de matrícula, solo el año del vehículo).
    first_due_year = vehicle_year + (3 if is_commercial else 4)
    if today.year < first_due_year:
        status = "ok"
        message = f"Tu primera revisión técnica toca en {first_due_year} (aprox.)"
    elif today.year == first_due_year:
        status = "warn"
        message = f"Te toca la primera revisión técnica este año ({first_due_year}, aprox.)"
    else:
        status = "overdue"
        message = f"Debiste hacer tu primera revisión técnica en {first_due_year} (aprox.)"

    return {
        "has_history": False,
        "first_due_year": first_due_year,
        "status": status,
        "message": message,
    }


def soat_status(expiry_date: date | None, today: date | None = None) -> dict:
    today = today or date.today()
    if expiry_date is None:
        return {"has_data": False}
    days_remaining = (expiry_date - today).days
    return {
        "has_data": True,
        "expiry_date": expiry_date,
        "days_remaining": days_remaining,
        "status": status_from_days(days_remaining),
    }


def renewal_period_years(age: int) -> int:
    """Vigencia de la licencia A-I al renovar, según la edad (MTC)."""
    if age < 70:
        return 10
    if age < 75:
        return 5
    if age < 81:
        return 3
    return 2


def brevete_status(
    expiry_date: date | None, birth_date: date | None = None, today: date | None = None
) -> dict:
    today = today or date.today()
    if expiry_date is None:
        return {"has_data": False}

    days_remaining = (expiry_date - today).days
    result = {
        "has_data": True,
        "expiry_date": expiry_date,
        "days_remaining": days_remaining,
        "status": status_from_days(days_remaining),
    }
    if birth_date is not None:
        age_now = age_at(birth_date, today)
        result["age"] = age_now
        result["renewal_period_years"] = renewal_period_years(age_now)
    return result
