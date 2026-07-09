from datetime import date

from app.models import PlanItem
from app.services.date_utils import add_months


class PlanProgress:
    def __init__(
        self,
        due_km: int | None,
        km_remaining: int | None,
        due_date: date | None,
        days_remaining: int | None,
        percent: float,
        status: str,
    ):
        self.due_km = due_km
        self.km_remaining = km_remaining
        self.due_date = due_date
        self.days_remaining = days_remaining
        self.percent = percent
        self.status = status


def compute_progress(item: PlanItem, current_km: int) -> PlanProgress:
    """Progreso por km y por tiempo; manda el que esté más avanzado (lo que ocurra primero)."""
    km_percent: float | None = None
    due_km: int | None = None
    km_remaining: int | None = None
    if item.interval_km:
        last_km = item.last_service_km or 0
        due_km = last_km + item.interval_km
        km_remaining = due_km - current_km
        km_percent = ((current_km - last_km) / item.interval_km) * 100

    time_percent: float | None = None
    due_date: date | None = None
    days_remaining: int | None = None
    if item.interval_months and item.last_service_date:
        due_date = add_months(item.last_service_date, item.interval_months)
        days_remaining = (due_date - date.today()).days
        total_days = (due_date - item.last_service_date).days
        if total_days > 0:
            elapsed_days = (date.today() - item.last_service_date).days
            time_percent = (elapsed_days / total_days) * 100

    candidates = [p for p in (km_percent, time_percent) if p is not None]
    percent = max(candidates) if candidates else 0.0
    percent = max(0.0, percent)

    if percent >= 100:
        status = "overdue"
    elif percent >= 80:
        status = "warn"
    else:
        status = "ok"

    return PlanProgress(due_km, km_remaining, due_date, days_remaining, round(percent, 1), status)
