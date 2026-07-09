def test_list_components(client, auth_headers):
    res = client.get("/api/catalog/components", headers=auth_headers)
    assert res.status_code == 200
    components = res.json()
    assert len(components) == 23
    names = {c["name"] for c in components}
    assert "Pastillas de freno delanteras" in names
    assert "Bujías" in names
    assert "Batería" in names

    oil = next(c for c in components if c["name"] == "Aceite y filtro de motor")
    assert oil["category"] == "motor"
    assert oil["default_interval_km"] == 10000

    battery = next(c for c in components if c["name"] == "Batería")
    assert battery["default_interval_km"] is None
    assert battery["default_interval_months"] == 36


def test_components_requires_auth(client):
    assert client.get("/api/catalog/components").status_code == 401


def test_components_sorted_by_category(client, auth_headers):
    res = client.get("/api/catalog/components", headers=auth_headers)
    categories = [c["category"] for c in res.json()]
    assert categories == sorted(categories)


def test_add_custom_plan_item_from_component(client, auth_headers):
    res = client.post(
        "/api/vehicles",
        json={"brand": "Toyota", "model": "RAV4", "year": 2022, "plate": "bgr-742"},
        headers=auth_headers,
    )
    vid = res.json()["id"]

    res = client.post(
        f"/api/vehicles/{vid}/plan",
        json={"name": "Rótulas y terminales de dirección", "interval_km": 60000, "notes": "Revisión de juego y desgaste"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    assert res.json()["name"] == "Rótulas y terminales de dirección"
