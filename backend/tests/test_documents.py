from datetime import date, timedelta


def _create_vehicle(client, auth_headers, year=2022, first_registration_year=None):
    res = client.post(
        "/api/vehicles",
        json={
            "brand": "Toyota",
            "model": "RAV4",
            "year": year,
            "plate": "bgr-742",
            "first_registration_year": first_registration_year,
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_documents_empty_by_default(client, auth_headers):
    vid = _create_vehicle(client, auth_headers, first_registration_year=2023)
    res = client.get(f"/api/vehicles/{vid}/documents", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["soat"]["has_data"] is False
    assert data["citv"]["has_data"] is False
    assert data["impuesto_vehicular"]["applicable"] is True  # 2023 -> afecto hasta 2026


def test_upsert_soat(client, auth_headers):
    vid = _create_vehicle(client, auth_headers)
    future = (date.today() + timedelta(days=100)).isoformat()
    res = client.put(
        f"/api/vehicles/{vid}/documents/soat",
        json={"reference_number": "4501-9921", "expiry_date": future},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["has_data"] is True
    assert res.json()["reference_number"] == "4501-9921"

    # actualizar (upsert) no debe duplicar
    future2 = (date.today() + timedelta(days=200)).isoformat()
    res = client.put(
        f"/api/vehicles/{vid}/documents/soat",
        json={"expiry_date": future2},
        headers=auth_headers,
    )
    assert res.status_code == 200
    docs = client.get(f"/api/vehicles/{vid}/documents", headers=auth_headers).json()
    assert docs["soat"]["expiry_date"] == future2


def test_upsert_citv(client, auth_headers):
    vid = _create_vehicle(client, auth_headers, year=2022)
    past = (date.today() - timedelta(days=100)).isoformat()
    res = client.put(
        f"/api/vehicles/{vid}/documents/citv",
        json={"expiry_date": past},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "overdue"


def test_invalid_doc_type_rejected(client, auth_headers):
    vid = _create_vehicle(client, auth_headers)
    res = client.put(
        f"/api/vehicles/{vid}/documents/impuesto",
        json={"expiry_date": "2030-01-01"},
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_delete_document(client, auth_headers):
    vid = _create_vehicle(client, auth_headers)
    client.put(
        f"/api/vehicles/{vid}/documents/soat",
        json={"expiry_date": "2030-01-01"},
        headers=auth_headers,
    )
    assert client.delete(f"/api/vehicles/{vid}/documents/soat", headers=auth_headers).status_code == 204
    assert client.delete(f"/api/vehicles/{vid}/documents/soat", headers=auth_headers).status_code == 404


def test_documents_isolated_between_users(client, auth_headers):
    vid = _create_vehicle(client, auth_headers)
    res = client.post(
        "/api/auth/register",
        json={"email": "otro-docs@test.pe", "name": "Otro", "password": "clave-otra-456"},
    )
    other = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert client.get(f"/api/vehicles/{vid}/documents", headers=other).status_code == 404
