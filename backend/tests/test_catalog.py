def test_list_makes(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.services.vehicle_catalog.get_makes", lambda: ["Toyota", "Hyundai", "Zzz Motors"]
    )
    res = client.get("/api/catalog/makes", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == ["Toyota", "Hyundai", "Zzz Motors"]


def test_list_makes_unavailable(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.services.vehicle_catalog.get_makes", lambda: [])
    res = client.get("/api/catalog/makes", headers=auth_headers)
    assert res.status_code == 503


def test_list_models(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.services.vehicle_catalog.get_models", lambda make: ["RAV4", "Corolla", "Hilux"]
    )
    res = client.get("/api/catalog/models", params={"make": "Toyota"}, headers=auth_headers)
    assert res.status_code == 200
    assert "RAV4" in res.json()


def test_list_models_requires_make(client, auth_headers):
    res = client.get("/api/catalog/models", params={"make": "  "}, headers=auth_headers)
    assert res.status_code == 400


def test_catalog_requires_auth(client):
    assert client.get("/api/catalog/makes").status_code == 401
