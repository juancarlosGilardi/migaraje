from datetime import date, timedelta


def _create_rav4(client, auth_headers, initial_km=48350):
    res = client.post(
        "/api/vehicles",
        json={
            "brand": "Toyota",
            "model": "RAV4",
            "year": 2022,
            "plate": "bgr-742",
            "initial_km": initial_km,
            "first_registration_year": 2023,
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_no_alerts_for_fresh_vehicle(client, auth_headers):
    _create_rav4(client, auth_headers)
    res = client.get("/api/alerts", headers=auth_headers)
    assert res.status_code == 200
    # recien creado: plan al 0%, sin SOAT/CITV registrados (unknown, no alerta),
    # impuesto puede o no estar en rango segun la fecha real, pero sin odometro
    # vencido ni plan vencido no debería haber alertas de plan/odometro
    kinds = {a["kind"] for a in res.json()}
    assert "plan" not in kinds
    assert "odometer" not in kinds


def test_plan_alert_when_oil_change_close(client, auth_headers):
    vid = _create_rav4(client, auth_headers)
    # acercar el km al limite del intervalo de aceite (10,000 km, umbral warn=80%)
    client.post(f"/api/vehicles/{vid}/odometer", json={"km": 48350 + 8500}, headers=auth_headers)
    res = client.get("/api/alerts", headers=auth_headers)
    alerts = res.json()
    plan_alerts = [a for a in alerts if a["kind"] == "plan"]
    assert any("Aceite" in a["title"] for a in plan_alerts)


def test_document_alert_for_soat_expiring(client, auth_headers):
    vid = _create_rav4(client, auth_headers)
    soon = (date.today() + timedelta(days=10)).isoformat()
    client.put(
        f"/api/vehicles/{vid}/documents/soat",
        json={"expiry_date": soon},
        headers=auth_headers,
    )
    res = client.get("/api/alerts", headers=auth_headers)
    soat_alerts = [a for a in res.json() if a["kind"] == "document" and "SOAT" in a["title"]]
    assert len(soat_alerts) == 1
    assert soat_alerts[0]["status"] == "critical"


def test_driver_alert_for_expiring_license(client, auth_headers):
    soon = (date.today() + timedelta(days=5)).isoformat()
    client.post("/api/drivers", json={"name": "Juan", "license_expiry": soon}, headers=auth_headers)
    res = client.get("/api/alerts", headers=auth_headers)
    driver_alerts = [a for a in res.json() if a["kind"] == "driver"]
    assert len(driver_alerts) == 1
    assert driver_alerts[0]["status"] == "critical"


def test_odometer_alert_when_stale(client, auth_headers):
    # sin km inicial (initial_km=0 no crea registro) para poder controlar la
    # unica fecha de odometro y simular que hace 31 dias que no se actualiza
    vid = _create_rav4(client, auth_headers, initial_km=0)
    old_date = (date.today() - timedelta(days=31)).isoformat()
    res = client.post(
        f"/api/vehicles/{vid}/odometer",
        json={"km": 48400, "recorded_on": old_date},
        headers=auth_headers,
    )
    assert res.status_code == 200
    res = client.get("/api/alerts", headers=auth_headers)
    odo_alerts = [a for a in res.json() if a["kind"] == "odometer"]
    assert len(odo_alerts) == 1
    assert odo_alerts[0]["status"] == "notice"


def test_alerts_sorted_by_severity(client, auth_headers):
    vid = _create_rav4(client, auth_headers)
    past = (date.today() - timedelta(days=10)).isoformat()
    soon = (date.today() + timedelta(days=10)).isoformat()
    client.put(f"/api/vehicles/{vid}/documents/soat", json={"expiry_date": past}, headers=auth_headers)
    client.put(f"/api/vehicles/{vid}/documents/citv", json={"expiry_date": soon}, headers=auth_headers)

    res = client.get("/api/alerts", headers=auth_headers)
    alerts = res.json()
    statuses = [a["status"] for a in alerts]
    severity = {"overdue": 0, "critical": 1, "reminder": 2, "warn": 3, "notice": 4}
    assert statuses == sorted(statuses, key=lambda s: severity.get(s, 9))


def test_alerts_isolated_between_users(client, auth_headers):
    vid = _create_rav4(client, auth_headers)
    past = (date.today() - timedelta(days=10)).isoformat()
    client.put(f"/api/vehicles/{vid}/documents/soat", json={"expiry_date": past}, headers=auth_headers)

    res = client.post(
        "/api/auth/register",
        json={"email": "otro-alertas@test.pe", "name": "Otro", "password": "clave-otra-789"},
    )
    other = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert client.get("/api/alerts", headers=other).json() == []
