from datetime import date

from app.services.peru_rules import (
    brevete_status,
    citv_status,
    impuesto_vehicular_status,
    renewal_period_years,
    soat_status,
    status_from_days,
)


# --- status_from_days ---
def test_status_from_days():
    assert status_from_days(None) == "unknown"
    assert status_from_days(-1) == "overdue"
    assert status_from_days(0) == "critical"
    assert status_from_days(20) == "critical"
    assert status_from_days(21) == "warn"
    assert status_from_days(60) == "warn"
    assert status_from_days(61) == "ok"


# --- Impuesto vehicular ---
def test_impuesto_vehicular_sin_anio():
    r = impuesto_vehicular_status(None)
    assert r["applicable"] is None


def test_impuesto_vehicular_antes_de_aplicar():
    # inscrito en 2026, hoy sigue siendo 2026 -> aplica recién en 2027
    r = impuesto_vehicular_status(2026, today=date(2026, 6, 1))
    assert r["applicable"] is False
    assert r["reason"] == "not_yet"


def test_impuesto_vehicular_ya_no_aplica():
    # inscrito en 2020 -> afecto 2021-2023, en 2026 ya no aplica
    r = impuesto_vehicular_status(2020, today=date(2026, 6, 1))
    assert r["applicable"] is False
    assert r["reason"] == "expired"


def test_impuesto_vehicular_dentro_del_rango_calcula_cuota():
    # inscrito en 2023 -> afecto 2024, 2025, 2026 (año 3 de 3)
    r = impuesto_vehicular_status(2023, today=date(2026, 7, 1))
    assert r["applicable"] is True
    assert r["year_index"] == 3
    # la cuota 3 vence el ultimo dia habil de agosto 2026
    assert r["quota_number"] == 3
    assert r["next_due_date"].month == 8
    assert r["days_remaining"] is not None
    assert r["status"] in ("ok", "warn", "critical", "overdue")


def test_impuesto_vehicular_cuota_vence_ultimo_dia_habil():
    # 31 de agosto de 2026 cae domingo -> debe retroceder a un dia habil
    r = impuesto_vehicular_status(2023, today=date(2026, 8, 1))
    due = r["next_due_date"]
    assert due.weekday() < 5  # lunes=0 ... viernes=4


def test_impuesto_vehicular_cuotas_del_anio_completadas():
    # inscrito en 2023, ya pasó noviembre 2026 -> no queda cuota pendiente este año
    r = impuesto_vehicular_status(2023, today=date(2026, 12, 15))
    assert r["applicable"] is True
    assert r["next_due_date"] is None


# --- CITV ---
def test_citv_sin_historial_aun_no_toca():
    r = citv_status(vehicle_year=2022, expiry_date=None, today=date(2026, 1, 1))
    assert r["has_history"] is False
    assert r["first_due_year"] == 2026
    assert r["status"] == "warn"  # justo el año que le toca


def test_citv_sin_historial_falta_tiempo():
    r = citv_status(vehicle_year=2024, expiry_date=None, today=date(2026, 1, 1))
    assert r["status"] == "ok"
    assert r["first_due_year"] == 2028


def test_citv_sin_historial_vencido():
    r = citv_status(vehicle_year=2018, expiry_date=None, today=date(2026, 1, 1))
    assert r["status"] == "overdue"


def test_citv_con_certificado_rastrea_su_propio_vencimiento():
    # el certificado ya trae impresa su fecha de vencimiento (igual que el SOAT)
    r = citv_status(vehicle_year=2022, expiry_date=date(2026, 8, 1), today=date(2026, 7, 1))
    assert r["has_history"] is True
    assert r["expiry_date"] == date(2026, 8, 1)
    assert r["days_remaining"] == 31
    assert r["status"] == "warn"


def test_citv_con_certificado_vencido():
    r = citv_status(vehicle_year=2022, expiry_date=date(2026, 1, 1), today=date(2026, 7, 1))
    assert r["status"] == "overdue"


def test_citv_comercial_primera_revision_es_al_tercer_anio():
    r = citv_status(
        vehicle_year=2022, expiry_date=None, today=date(2025, 1, 1), is_commercial=True
    )
    assert r["first_due_year"] == 2025  # comercial: 3er año (vs 4to en particular)


# --- SOAT ---
def test_soat_sin_datos():
    assert soat_status(None)["has_data"] is False


def test_soat_con_fecha():
    r = soat_status(date(2026, 8, 15), today=date(2026, 7, 8))
    assert r["has_data"] is True
    assert r["days_remaining"] == 38
    assert r["status"] == "warn"


def test_soat_vencido():
    r = soat_status(date(2026, 1, 1), today=date(2026, 7, 8))
    assert r["status"] == "overdue"
    assert r["days_remaining"] < 0


# --- Brevete ---
def test_renewal_period_years():
    assert renewal_period_years(30) == 10
    assert renewal_period_years(69) == 10
    assert renewal_period_years(70) == 5
    assert renewal_period_years(74) == 5
    assert renewal_period_years(75) == 3
    assert renewal_period_years(80) == 3
    assert renewal_period_years(81) == 2
    assert renewal_period_years(95) == 2


def test_brevete_sin_datos():
    assert brevete_status(None)["has_data"] is False


def test_brevete_con_fecha_sin_nacimiento():
    r = brevete_status(date(2026, 8, 1), today=date(2026, 7, 8))
    assert r["has_data"] is True
    assert "age" not in r or r.get("age") is None


def test_brevete_calcula_edad_y_periodo_renovacion():
    # nacido en 1950 -> 76 años en jul 2026 -> renovacion de 3 años
    r = brevete_status(date(2026, 8, 1), birth_date=date(1950, 3, 1), today=date(2026, 7, 8))
    assert r["age"] == 76
    assert r["renewal_period_years"] == 3


def test_brevete_vencido_pronto():
    r = brevete_status(date(2026, 7, 20), today=date(2026, 7, 8))
    assert r["status"] == "critical"
