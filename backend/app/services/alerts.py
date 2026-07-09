from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Driver, LegalDocument, OdometerLog, PlanItem, Vehicle
from app.schemas import AlertOut
from app.services.peru_rules import brevete_status, citv_status, impuesto_vehicular_status, soat_status
from app.services.plan_progress import compute_progress
from app.services.reminders import odometer_reminder_status

PLAN_ALERT_STATUSES = {"warn", "overdue"}
DOC_ALERT_STATUSES = {"warn", "critical", "overdue"}

ODOMETER_TITLES = {
    "notice": "Actualiza tu kilometraje",
    "reminder": "Sigues sin actualizar tu kilometraje",
}


def _current_km(vehicle_id: int, db: Session) -> tuple[int, date | None]:
    row = db.execute(
        select(func.max(OdometerLog.km), func.max(OdometerLog.recorded_on)).where(
            OdometerLog.vehicle_id == vehicle_id
        )
    ).one()
    return row[0] or 0, row[1]


def get_alerts(user_id: int, db: Session) -> list[AlertOut]:
    alerts: list[AlertOut] = []
    vehicles = db.scalars(select(Vehicle).where(Vehicle.user_id == user_id)).all()

    for vehicle in vehicles:
        label = f"{vehicle.brand} {vehicle.model}"
        current_km, last_odometer_date = _current_km(vehicle.id, db)

        # Plan de mantenimiento
        items = db.scalars(select(PlanItem).where(PlanItem.vehicle_id == vehicle.id)).all()
        for item in items:
            progress = compute_progress(item, current_km)
            if progress.status in PLAN_ALERT_STATUSES:
                if progress.km_remaining is not None and progress.km_remaining >= 0:
                    due = f"en {progress.km_remaining:,} km"
                elif progress.km_remaining is not None:
                    due = f"vencido hace {-progress.km_remaining:,} km"
                else:
                    due = _days_message(progress.days_remaining)
                alerts.append(
                    AlertOut(
                        kind="plan",
                        status=progress.status,
                        title=f"{item.name} · {label}",
                        message=due,
                        vehicle_id=vehicle.id,
                        days_remaining=progress.days_remaining,
                    )
                )

        # SOAT / CITV
        soat_doc = db.scalar(
            select(LegalDocument).where(
                LegalDocument.vehicle_id == vehicle.id, LegalDocument.doc_type == "soat"
            )
        )
        soat = soat_status(soat_doc.expiry_date if soat_doc else None)
        if soat.get("status") in DOC_ALERT_STATUSES:
            alerts.append(
                AlertOut(
                    kind="document",
                    status=soat["status"],
                    title=f"SOAT · {label}",
                    message=_days_message(soat.get("days_remaining")),
                    vehicle_id=vehicle.id,
                    days_remaining=soat.get("days_remaining"),
                )
            )

        citv_doc = db.scalar(
            select(LegalDocument).where(
                LegalDocument.vehicle_id == vehicle.id, LegalDocument.doc_type == "citv"
            )
        )
        citv = citv_status(vehicle.year, citv_doc.expiry_date if citv_doc else None)
        if citv.get("status") in DOC_ALERT_STATUSES:
            alerts.append(
                AlertOut(
                    kind="document",
                    status=citv["status"],
                    title=f"Revisión técnica · {label}",
                    message=citv.get("message") or _days_message(citv.get("days_remaining")),
                    vehicle_id=vehicle.id,
                    days_remaining=citv.get("days_remaining"),
                )
            )

        # Impuesto vehicular
        impuesto = impuesto_vehicular_status(vehicle.first_registration_year)
        if impuesto.get("applicable") and impuesto.get("status") in DOC_ALERT_STATUSES:
            alerts.append(
                AlertOut(
                    kind="document",
                    status=impuesto["status"],
                    title=f"Impuesto vehicular · {label}",
                    message=impuesto.get("message") or _days_message(impuesto.get("days_remaining")),
                    vehicle_id=vehicle.id,
                    days_remaining=impuesto.get("days_remaining"),
                )
            )

        # Recordatorio de kilometraje
        odo = odometer_reminder_status(last_odometer_date)
        if odo["show"]:
            alerts.append(
                AlertOut(
                    kind="odometer",
                    status=odo["stage"],
                    title=ODOMETER_TITLES[odo["stage"]],
                    message=f"{label} · sin actualizar hace {odo['days_since_update']} días",
                    vehicle_id=vehicle.id,
                    days_remaining=None,
                )
            )

    # Brevetes
    drivers = db.scalars(select(Driver).where(Driver.user_id == user_id)).all()
    for driver in drivers:
        b = brevete_status(driver.license_expiry, driver.birth_date)
        if b.get("has_data") and b.get("status") in DOC_ALERT_STATUSES:
            alerts.append(
                AlertOut(
                    kind="driver",
                    status=b["status"],
                    title=f"Brevete · {driver.name}",
                    message=_days_message(b.get("days_remaining")),
                    driver_id=driver.id,
                    days_remaining=b.get("days_remaining"),
                )
            )

    severity = {"overdue": 0, "critical": 1, "reminder": 2, "warn": 3, "notice": 4}
    alerts.sort(key=lambda a: severity.get(a.status, 9))
    return alerts


def _days_message(days: int | None) -> str:
    if days is None:
        return ""
    if days < 0:
        return f"vencido hace {-days} días"
    if days == 0:
        return "vence hoy"
    return f"en {days} días"
