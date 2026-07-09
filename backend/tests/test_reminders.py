from datetime import date, timedelta

from app.services.reminders import odometer_reminder_status


def _status(days_ago: int):
    today = date(2026, 7, 8)
    last_update = today - timedelta(days=days_ago)
    return odometer_reminder_status(last_update, today=today)


def test_sin_registro_previo():
    r = odometer_reminder_status(None, today=date(2026, 7, 8))
    assert r["show"] is False
    assert r["stage"] == "ok"


def test_dentro_del_mes_de_gracia():
    r = _status(0)
    assert r["show"] is False
    r = _status(29)
    assert r["show"] is False


def test_al_dia_30_muestra_aviso():
    r = _status(30)
    assert r["stage"] == "notice"
    assert r["show"] is True


def test_aviso_dura_una_semana():
    r = _status(36)
    assert r["stage"] == "notice"


def test_dia_37_pasa_a_recordatorio():
    r = _status(37)
    assert r["stage"] == "reminder"
    assert r["show"] is True


def test_recordatorio_dura_una_semana():
    r = _status(43)
    assert r["stage"] == "reminder"


def test_dia_44_entra_en_silencio():
    r = _status(44)
    assert r["stage"] == "silent"
    assert r["show"] is False


def test_silencio_dura_30_dias():
    r = _status(73)
    assert r["stage"] == "silent"


def test_dia_74_reinicia_el_ciclo_con_aviso():
    r = _status(74)
    assert r["stage"] == "notice"
    assert r["show"] is True


def test_el_ciclo_se_repite_indefinidamente():
    # segundo ciclo: aviso en el dia 74, recordatorio en el dia 81, silencio en el 88
    assert _status(74)["stage"] == "notice"
    assert _status(81)["stage"] == "reminder"
    assert _status(88)["stage"] == "silent"
    # tercer ciclo empieza en 74 + 44 = 118
    assert _status(118)["stage"] == "notice"
