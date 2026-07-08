def test_register_login_me(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "ana@test.pe", "name": "Ana", "password": "otra-clave-456"},
    )
    assert res.status_code == 201
    assert res.json()["user"]["name"] == "Ana"

    # correo duplicado
    res = client.post(
        "/api/auth/register",
        json={"email": "ana@test.pe", "name": "Ana 2", "password": "otra-clave-456"},
    )
    assert res.status_code == 409

    res = client.post("/api/auth/login", json={"email": "ana@test.pe", "password": "otra-clave-456"})
    assert res.status_code == 200
    token = res.json()["access_token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "ana@test.pe"

    # contraseña incorrecta
    res = client.post("/api/auth/login", json={"email": "ana@test.pe", "password": "incorrecta-99"})
    assert res.status_code == 401

    # sin token
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_vehicle_crud_and_odometer(client, auth_headers):
    # crear con km inicial
    res = client.post(
        "/api/vehicles",
        json={
            "brand": "Toyota",
            "model": "RAV4",
            "year": 2022,
            "plate": "bgr-742",
            "initial_km": 48350,
            "first_registration_year": 2023,
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    vehicle = res.json()
    assert vehicle["plate"] == "BGR-742"  # normalizada a mayúsculas
    assert vehicle["current_km"] == 48350
    vid = vehicle["id"]

    # actualizar km hacia adelante
    res = client.post(f"/api/vehicles/{vid}/odometer", json={"km": 48512}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["current_km"] == 48512

    # km menor al último → rechazado
    res = client.post(f"/api/vehicles/{vid}/odometer", json={"km": 48000}, headers=auth_headers)
    assert res.status_code == 400
    assert "menor" in res.json()["detail"]

    # listar
    res = client.get("/api/vehicles", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # otro usuario no ve ni toca el vehículo
    res = client.post(
        "/api/auth/register",
        json={"email": "intruso@test.pe", "name": "Intruso", "password": "clave-intrusa-1"},
    )
    other = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert client.get(f"/api/vehicles/{vid}", headers=other).status_code == 404
    assert client.get("/api/vehicles", headers=other).json() == []

    # eliminar
    res = client.delete(f"/api/vehicles/{vid}", headers=auth_headers)
    assert res.status_code == 204
    assert client.get("/api/vehicles", headers=auth_headers).json() == []
