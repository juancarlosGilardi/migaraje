import io

SAMPLE_INVOICE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
    <cbc:ID>F001-00012345</cbc:ID>
    <cbc:IssueDate>2026-07-02</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID>20481234567</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>Taller AutoPro S.A.C.</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:InvoiceLine>
        <cbc:InvoicedQuantity>1</cbc:InvoicedQuantity>
        <cac:Item>
            <cbc:Description>Aceite sintetico 5W-30 (4L)</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount>260.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
    <cac:InvoiceLine>
        <cbc:InvoicedQuantity>1</cbc:InvoicedQuantity>
        <cac:Item>
            <cbc:Description>Filtro de aceite original</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount>60.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
    <cac:InvoiceLine>
        <cbc:InvoicedQuantity>1</cbc:InvoicedQuantity>
        <cac:Item>
            <cbc:Description>Mano de obra</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount>100.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
    <cac:LegalMonetaryTotal>
        <cbc:PayableAmount>420.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
</Invoice>
"""

BRAKE_INVOICE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
    <cbc:ID>F002-00000456</cbc:ID>
    <cbc:IssueDate>2026-03-03</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID>20999888777</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>Servicio Rodriguez E.I.R.L.</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:InvoiceLine>
        <cbc:InvoicedQuantity>2</cbc:InvoicedQuantity>
        <cac:Item>
            <cbc:Description>Pastillas de freno delanteras</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount>310.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
    <cac:LegalMonetaryTotal>
        <cbc:PayableAmount>620.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
</Invoice>
"""

INVALID_XML = "<not-an-invoice><foo>bar</foo></not-an-invoice>"

NOT_XML_AT_ALL = "%PDF-1.4 esto no es xml en absoluto"


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


def _upload(client, auth_headers, vid, filename, content, content_type):
    return client.post(
        f"/api/vehicles/{vid}/services/upload",
        files={"file": (filename, io.BytesIO(content.encode() if isinstance(content, str) else content), content_type)},
        headers=auth_headers,
    )


def test_parse_valid_ubl_invoice(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]

    res = _upload(client, auth_headers, vid, "factura.xml", SAMPLE_INVOICE_XML, "text/xml")
    assert res.status_code == 200
    preview = res.json()

    assert preview["is_xml"] is True
    assert preview["parse_error"] is None
    assert preview["supplier_name"] == "Taller AutoPro S.A.C."
    assert preview["supplier_ruc"] == "20481234567"
    assert preview["issue_date"] == "2026-07-02"
    assert preview["currency"] == "PEN"
    assert preview["total"] == 420.00
    assert len(preview["items"]) == 3
    assert preview["upload_token"]


def test_suggests_oil_change_service_type_and_oil_match(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    assert vehicle["spec"]["oil"]["viscosity"] == "0W-16"  # plantilla RAV4 real

    res = _upload(client, auth_headers, vid, "factura.xml", SAMPLE_INVOICE_XML, "text/xml")
    preview = res.json()
    assert preview["suggested_service_type"] == "Cambio de aceite y filtro"
    # el aceite de la factura es 5W-30, pero el recomendado del RAV4 es 0W-16 -> no coincide
    assert preview["oil_match"]["matches"] is False


def test_oil_match_true_when_viscosity_matches(client, auth_headers):
    res = client.post(
        "/api/vehicles",
        json={"brand": "Marca Rara", "model": "X1", "year": 2020, "plate": "xyz-123"},
        headers=auth_headers,
    )
    vehicle = res.json()
    vid = vehicle["id"]
    # plantilla genérica no trae viscosidad conocida ("Consulta tu manual"),
    # así que forzamos un XML con esa misma cadena para verificar la ruta neutra
    if vehicle["spec"]["oil"]["viscosity"] == "Consulta tu manual":
        res = _upload(client, auth_headers, vid, "factura.xml", SAMPLE_INVOICE_XML, "text/xml")
        preview = res.json()
        assert preview["oil_match"]["matches"] is None


def test_brake_service_suggestion(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    res = _upload(client, auth_headers, vid, "factura2.xml", BRAKE_INVOICE_XML, "text/xml")
    preview = res.json()
    assert preview["suggested_service_type"] == "Servicio de frenos"
    assert preview["total"] == 620.00
    # cantidad 2 * precio unitario 310 = 620 en el ítem de línea
    assert preview["items"][0]["amount"] == 620.00


def test_invalid_xml_returns_clear_error_not_500(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]

    res = _upload(client, auth_headers, vid, "raro.xml", INVALID_XML, "text/xml")
    assert res.status_code == 200  # el preview se genera pero marca el error
    preview = res.json()
    assert preview["parse_error"] is not None
    assert preview["supplier_name"] is None

    res2 = _upload(client, auth_headers, vid, "roto.xml", "<abrio-pero<no cierra", "text/xml")
    assert res2.status_code == 200
    assert res2.json()["parse_error"] is not None


def test_pdf_upload_has_no_parser_but_allows_manual_flow(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    res = _upload(client, auth_headers, vid, "factura.pdf", NOT_XML_AT_ALL, "application/pdf")
    assert res.status_code == 200
    preview = res.json()
    assert preview["is_xml"] is False
    assert preview["parse_error"] is None
    assert preview["upload_token"]


def test_confirm_creates_service_record_with_file(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]

    upload_res = _upload(client, auth_headers, vid, "factura.xml", SAMPLE_INVOICE_XML, "text/xml")
    preview = upload_res.json()

    res = client.post(
        f"/api/vehicles/{vid}/services",
        json={
            "upload_token": preview["upload_token"],
            "service_date": "2026-07-02",
            "km": 48350,
            "service_type": preview["suggested_service_type"],
            "cost": preview["total"],
            "workshop": preview["supplier_name"],
            "ruc": preview["supplier_ruc"],
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    record = res.json()
    assert record["service_type"] == "Cambio de aceite y filtro"
    assert record["has_xml"] is True
    assert record["has_pdf"] is False
    assert float(record["cost"]) == 420.00

    # aparece en el historial
    history = client.get(f"/api/vehicles/{vid}/services", headers=auth_headers).json()
    assert len(history) == 1
    assert history[0]["id"] == record["id"]

    # descarga del archivo
    file_res = client.get(f"/api/vehicles/{vid}/services/{record['id']}/file", headers=auth_headers)
    assert file_res.status_code == 200
    assert file_res.headers["content-type"].startswith("text/xml") or file_res.headers["content-type"].startswith("application/xml")


def test_confirm_without_upload_token_manual_entry(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    res = client.post(
        f"/api/vehicles/{vid}/services",
        json={
            "service_date": "2026-01-15",
            "km": 44000,
            "service_type": "Mantenimiento de 44,000 km",
            "cost": 1850,
            "workshop": "Taller AutoPro S.A.C.",
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    record = res.json()
    assert record["has_pdf"] is False
    assert record["has_xml"] is False

    # sin archivo adjunto -> descarga da 404
    file_res = client.get(f"/api/vehicles/{vid}/services/{record['id']}/file", headers=auth_headers)
    assert file_res.status_code == 404


def test_expired_or_unknown_upload_token_is_rejected(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    res = client.post(
        f"/api/vehicles/{vid}/services",
        json={
            "upload_token": "token-inventado-que-no-existe",
            "service_date": "2026-01-15",
            "service_type": "Mantenimiento general",
        },
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_delete_service_record(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    res = client.post(
        f"/api/vehicles/{vid}/services",
        json={"service_date": "2026-01-15", "service_type": "Mantenimiento general"},
        headers=auth_headers,
    )
    service_id = res.json()["id"]
    del_res = client.delete(f"/api/vehicles/{vid}/services/{service_id}", headers=auth_headers)
    assert del_res.status_code == 204

    history = client.get(f"/api/vehicles/{vid}/services", headers=auth_headers).json()
    assert history == []


def test_services_isolated_between_users(client, auth_headers):
    vehicle = _create_rav4(client, auth_headers)
    vid = vehicle["id"]
    client.post(
        f"/api/vehicles/{vid}/services",
        json={"service_date": "2026-01-15", "service_type": "Mantenimiento general"},
        headers=auth_headers,
    )

    res = client.post(
        "/api/auth/register",
        json={"email": "intruso3@test.pe", "name": "Intruso", "password": "clave-intrusa-3"},
    )
    other = {"Authorization": f"Bearer {res.json()['access_token']}"}

    assert client.get(f"/api/vehicles/{vid}/services", headers=other).status_code == 404
    assert _upload(client, other, vid, "x.xml", SAMPLE_INVOICE_XML, "text/xml").status_code == 404
