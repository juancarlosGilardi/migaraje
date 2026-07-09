from datetime import date, timedelta


def test_create_and_list_drivers(client, auth_headers):
    res = client.post(
        "/api/drivers",
        json={"name": "Juan Carlos", "license_class": "A-I", "license_expiry": "2030-01-01"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    driver = res.json()
    assert driver["name"] == "Juan Carlos"
    assert driver["has_data"] is True
    assert driver["status"] == "ok"

    res = client.get("/api/drivers", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_driver_without_expiry_has_no_status(client, auth_headers):
    res = client.post("/api/drivers", json={"name": "Sin datos"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["has_data"] is False


def test_driver_critical_soon(client, auth_headers):
    soon = (date.today() + timedelta(days=5)).isoformat()
    res = client.post(
        "/api/drivers", json={"name": "Juan", "license_expiry": soon}, headers=auth_headers
    )
    assert res.json()["status"] == "critical"


def test_update_driver(client, auth_headers):
    res = client.post("/api/drivers", json={"name": "Juan"}, headers=auth_headers)
    driver_id = res.json()["id"]

    res = client.patch(
        f"/api/drivers/{driver_id}",
        json={"birth_date": "1950-01-01", "license_expiry": "2030-01-01"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["age"] is not None
    assert res.json()["renewal_period_years"] is not None


def test_delete_driver(client, auth_headers):
    res = client.post("/api/drivers", json={"name": "Juan"}, headers=auth_headers)
    driver_id = res.json()["id"]
    assert client.delete(f"/api/drivers/{driver_id}", headers=auth_headers).status_code == 204
    assert client.get("/api/drivers", headers=auth_headers).json() == []


def test_drivers_isolated_between_users(client, auth_headers):
    res = client.post("/api/drivers", json={"name": "Juan"}, headers=auth_headers)
    driver_id = res.json()["id"]

    res = client.post(
        "/api/auth/register",
        json={"email": "otro-driver@test.pe", "name": "Otro", "password": "clave-otra-123"},
    )
    other = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert client.get("/api/drivers", headers=other).json() == []
    assert client.patch(f"/api/drivers/{driver_id}", json={"name": "Hackeado"}, headers=other).status_code == 404
    assert client.delete(f"/api/drivers/{driver_id}", headers=other).status_code == 404
