import calendar
from datetime import date, timedelta


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def last_business_day(year: int, month: int) -> date:
    """Último día hábil del mes (solo excluye sábados/domingos; no considera feriados)."""
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    while d.weekday() >= 5:  # 5=sábado, 6=domingo
        d -= timedelta(days=1)
    return d


def age_at(birth_date: date, at_date: date) -> int:
    years = at_date.year - birth_date.year
    if (at_date.month, at_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years
