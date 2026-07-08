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
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    return res.json()


def test_vehicle_creation_seeds_spec_and_plan(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    assert vehicle["spec"]["oil"]["viscosity"] == "0W-16"
    assert vehicle["spec"]["tires"]["size"] == "225/60 R18"

    res = client.get(f"/api/vehicles/{vehicle['id']}/plan", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()
    names = {i["name"] for i in items}
    assert "Aceite y filtro de motor" in names
    assert len(items) == 5  # 5 items en la plantilla RAV4

    oil = next(i for i in items if i["name"] == "Aceite y filtro de motor")
    assert oil["last_service_km"] == 48350
    assert oil["due_km"] == 48350 + 10000
    assert oil["percent"] == 0  # recién "sembrado" = recién hecho
    assert oil["status"] == "ok"


def test_generic_template_for_unknown_brand(client, auth_headers):
    res = client.post(
        "/api/vehicles",
        json={"brand": "Marca Rara", "model": "X1", "year": 2020, "plate": "xyz-123"},
        headers=auth_headers,
    )
    vehicle = res.json()
    assert vehicle["spec"]["oil"]["viscosity"] == "Consulta tu manual"

    res = client.get(f"/api/vehicles/{vehicle['id']}/plan", headers=auth_headers)
    items = res.json()
    assert len(items) == 4  # plantilla genérica tiene 4 items


def test_progress_updates_with_odometer(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]

    # avanzar el odómetro casi al límite del intervalo (10,000 km)
    client.post(f"/api/vehicles/{vid}/odometer", json={"km": 48350 + 8500}, headers=auth_headers)

    items = client.get(f"/api/vehicles/{vid}/plan", headers=auth_headers).json()
    oil = next(i for i in items if i["name"] == "Aceite y filtro de motor")
    assert oil["percent"] == 85.0
    assert oil["status"] == "warn"
    assert oil["km_remaining"] == 1500

    # pasarse del intervalo -> overdue
    client.post(f"/api/vehicles/{vid}/odometer", json={"km": 48350 + 11000}, headers=auth_headers)
    items = client.get(f"/api/vehicles/{vid}/plan", headers=auth_headers).json()
    oil = next(i for i in items if i["name"] == "Aceite y filtro de motor")
    assert oil["status"] == "overdue"
    assert oil["km_remaining"] == -1000


def test_mark_done_resets_progress(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    client.post(f"/api/vehicles/{vid}/odometer", json={"km": 48350 + 9500}, headers=auth_headers)

    items = client.get(f"/api/vehicles/{vid}/plan", headers=auth_headers).json()
    oil = next(i for i in items if i["name"] == "Aceite y filtro de motor")
    assert oil["status"] == "warn"

    res = client.post(f"/api/vehicles/{vid}/plan/{oil['id']}/mark-done", headers=auth_headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["last_service_km"] == 48350 + 9500
    assert updated["last_service_date"] == date.today().isoformat()
    assert updated["percent"] == 0
    assert updated["status"] == "ok"


def test_edit_plan_item_interval(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    items = client.get(f"/api/vehicles/{vid}/plan", headers=auth_headers).json()
    oil = next(i for i in items if i["name"] == "Aceite y filtro de motor")

    res = client.patch(
        f"/api/vehicles/{vid}/plan/{oil['id']}",
        json={"interval_km": 5000},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["interval_km"] == 5000
    assert res.json()["due_km"] == 48350 + 5000


def test_add_and_delete_custom_plan_item(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]

    res = client.post(
        f"/api/vehicles/{vid}/plan",
        json={"name": "Filtro de cabina", "interval_km": 15000},
        headers=auth_headers,
    )
    assert res.status_code == 201
    item_id = res.json()["id"]

    # sin ningún intervalo -> rechazado
    res = client.post(
        f"/api/vehicles/{vid}/plan", json={"name": "Sin intervalo"}, headers=auth_headers
    )
    assert res.status_code == 422

    res = client.delete(f"/api/vehicles/{vid}/plan/{item_id}", headers=auth_headers)
    assert res.status_code == 204


def test_plan_isolated_between_users(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]

    res = client.post(
        "/api/auth/register",
        json={"email": "intruso2@test.pe", "name": "Intruso", "password": "clave-intrusa-2"},
    )
    other = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert client.get(f"/api/vehicles/{vid}/plan", headers=other).status_code == 404


def test_time_based_progress_when_more_urgent(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    items = client.get(f"/api/vehicles/{vid}/plan", headers=auth_headers).json()
    rotation = next(i for i in items if i["name"] == "Rotación de llantas")  # 10,000km / 6 meses

    # forzar last_service_date muy en el pasado sin mover el odómetro -> el tiempo manda
    old_date = (date.today() - timedelta(days=200)).isoformat()  # > 6 meses
    client.patch(
        f"/api/vehicles/{vid}/plan/{rotation['id']}",
        json={"last_service_date": old_date},
        headers=auth_headers,
    )
    items = client.get(f"/api/vehicles/{vid}/plan", headers=auth_headers).json()
    rotation = next(i for i in items if i["name"] == "Rotación de llantas")
    assert rotation["status"] == "overdue"
