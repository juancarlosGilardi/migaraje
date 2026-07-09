"""Recordatorio mensual de kilometraje, sin saturar al usuario.

Regla (pedida por el usuario): un aviso al mes, si lo ignora un solo
recordatorio más, y si sigue sin responder el sistema calla 30 días antes
de volver a preguntar. Se calcula de forma pura a partir de la fecha del
último registro de odómetro — no hace falta guardar estado en la BD: el
ciclo se repite solo con aritmética de fechas.
"""

from datetime import date

GRACE_DAYS = 30  # sin pedir nada durante el primer mes desde el último registro
NOTICE_DAYS = 7  # ventana del "aviso"
REMINDER_DAYS = 7  # ventana del "recordatorio" (tras ignorar el aviso)
SILENCE_DAYS = 30  # pausa antes de reiniciar el ciclo

CYCLE_DAYS = NOTICE_DAYS + REMINDER_DAYS + SILENCE_DAYS


def odometer_reminder_status(last_update: date | None, today: date | None = None) -> dict:
    today = today or date.today()
    if last_update is None:
        return {"stage": "ok", "show": False, "days_since_update": None}

    days = (today - last_update).days
    if days < GRACE_DAYS:
        return {"stage": "ok", "show": False, "days_since_update": days}

    offset = (days - GRACE_DAYS) % CYCLE_DAYS
    if offset < NOTICE_DAYS:
        stage = "notice"
    elif offset < NOTICE_DAYS + REMINDER_DAYS:
        stage = "reminder"
    else:
        stage = "silent"

    return {"stage": stage, "show": stage != "silent", "days_since_update": days}
