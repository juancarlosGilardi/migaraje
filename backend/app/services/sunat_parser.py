"""Parser de facturas electrónicas peruanas en formato UBL 2.1 (SUNAT).

No usamos storage externo ni OCR: solo XML UBL bien formado. Si el XML no
matchea la estructura esperada, lanzamos InvalidInvoiceError con un mensaje
claro para que el router devuelva un 400 en vez de un 500.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lxml import etree

NSMAP = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}

# Palabras clave -> tipo de servicio sugerido. Se evalúa en orden: la primera
# palabra clave que matchee en el texto combinado de los ítems gana.
KEYWORD_RULES: list[tuple[tuple[str, ...], str]] = [
    (("aceite",), "Cambio de aceite y filtro"),
    (("llanta", "neumático", "neumatico", "rotación", "rotacion"), "Rotación de llantas"),
    (("freno",), "Servicio de frenos"),
    (("batería", "bateria"), "Cambio de batería"),
    (("filtro de aire",), "Filtro de aire"),
]
FALLBACK_SERVICE_TYPE = "Mantenimiento general"


class InvalidInvoiceError(Exception):
    """El XML no pudo parsearse como una factura UBL 2.1 válida."""


@dataclass
class InvoiceItem:
    description: str
    amount: float


@dataclass
class ParsedInvoice:
    invoice_number: str | None
    issue_date: str | None
    currency: str | None
    supplier_name: str | None
    supplier_ruc: str | None
    items: list[InvoiceItem] = field(default_factory=list)
    total: float | None = None


def _text(node, xpath: str) -> str | None:
    result = node.xpath(xpath, namespaces=NSMAP)
    if not result:
        return None
    value = result[0].text
    return value.strip() if value else None


def parse_ubl_invoice(xml_bytes: bytes) -> ParsedInvoice:
    """Parsea bytes de un XML UBL 2.1 (factura SUNAT) y devuelve sus datos clave.

    Lanza InvalidInvoiceError si el XML no es válido o no tiene la
    estructura UBL/SUNAT esperada (namespaces, InvoiceLine, etc.).
    """
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(xml_bytes, parser=parser)
    except etree.XMLSyntaxError as exc:
        raise InvalidInvoiceError(f"El archivo no es un XML válido: {exc}") from exc

    if root.tag.split("}")[-1] != "Invoice":
        raise InvalidInvoiceError(
            "El XML no es una factura electrónica UBL (se esperaba el elemento raíz <Invoice>)"
        )

    invoice_number = _text(root, "cbc:ID")
    issue_date = _text(root, "cbc:IssueDate")
    currency = _text(root, "cbc:DocumentCurrencyCode")

    supplier_name = _text(
        root,
        "cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
    )
    supplier_ruc = _text(
        root,
        "cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID",
    )

    lines = root.xpath("cac:InvoiceLine", namespaces=NSMAP)
    if not lines:
        raise InvalidInvoiceError(
            "El XML no contiene ítems de factura (cac:InvoiceLine) — no parece una factura UBL válida"
        )

    items: list[InvoiceItem] = []
    for line in lines:
        description = _text(line, "cac:Item/cbc:Description") or "Ítem sin descripción"
        amount_text = _text(line, "cac:Price/cbc:PriceAmount")
        quantity_text = _text(line, "cbc:InvoicedQuantity")
        amount = _to_float(amount_text)
        if amount is not None and quantity_text:
            quantity = _to_float(quantity_text) or 1.0
            # cbc:Price/PriceAmount es el precio unitario; el monto de línea es qty * precio
            amount = round(amount * quantity, 2)
        items.append(InvoiceItem(description=description, amount=amount or 0.0))

    total_text = _text(root, "cac:LegalMonetaryTotal/cbc:PayableAmount")
    total = _to_float(total_text)

    if not supplier_name and not invoice_number:
        raise InvalidInvoiceError(
            "El XML no tiene los datos mínimos de una factura SUNAT (emisor, número)"
        )

    return ParsedInvoice(
        invoice_number=invoice_number,
        issue_date=issue_date,
        currency=currency,
        supplier_name=supplier_name,
        supplier_ruc=supplier_ruc,
        items=items,
        total=total,
    )


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def suggest_service_type(items: list[InvoiceItem]) -> str:
    """Sugiere el tipo de servicio según palabras clave en las descripciones de los ítems."""
    combined = " ".join(item.description for item in items).lower()
    for keywords, service_type in KEYWORD_RULES:
        if any(keyword in combined for keyword in keywords):
            return service_type
    return FALLBACK_SERVICE_TYPE


def check_oil_match(items: list[InvoiceItem], recommended_viscosity: str | None) -> dict:
    """Cruza el texto de los ítems contra la viscosidad de aceite recomendada del vehículo.

    Devuelve un dict con `matches` (bool | None si no aplica) y `message` para
    mostrar en el frontend, siguiendo el mockup ("✓ El aceite de la factura
    coincide con el recomendado").
    """
    if not recommended_viscosity or recommended_viscosity.strip().lower() in (
        "",
        "consulta tu manual",
    ):
        return {"matches": None, "message": None}

    combined = " ".join(item.description for item in items).lower()
    has_oil_item = "aceite" in combined
    if not has_oil_item:
        return {"matches": None, "message": None}

    viscosity_norm = recommended_viscosity.strip().lower()
    if viscosity_norm in combined:
        return {
            "matches": True,
            "message": f"El aceite de la factura coincide con el recomendado ({recommended_viscosity})",
        }
    return {
        "matches": False,
        "message": f"El aceite de la factura no coincide con el recomendado ({recommended_viscosity})",
    }
