from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import ServiceFile, ServiceRecord, User
from app.routers.vehicles import _get_owned_vehicle
from app.schemas import (
    InvoiceItemOut,
    InvoicePreviewOut,
    OilMatchOut,
    ServiceFileOut,
    ServiceRecordIn,
    ServiceRecordOut,
)
from app.services import upload_cache
from app.services.sunat_parser import InvalidInvoiceError, check_oil_match, parse_ubl_invoice, suggest_service_type

router = APIRouter(prefix="/api/vehicles/{vehicle_id}/services", tags=["services"])

XML_CONTENT_TYPES = {"text/xml", "application/xml"}


def _is_xml(filename: str, content_type: str | None) -> bool:
    if content_type in XML_CONTENT_TYPES:
        return True
    return filename.lower().endswith(".xml")


def _is_pdf(filename: str, content_type: str | None) -> bool:
    if content_type == "application/pdf":
        return True
    return filename.lower().endswith(".pdf")


def _get_owned_record(vehicle_id: int, record_id: int, user: User, db: Session) -> ServiceRecord:
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    record = db.get(ServiceRecord, record_id)
    if record is None or record.vehicle_id != vehicle.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado")
    return record


def _to_out(record: ServiceRecord) -> ServiceRecordOut:
    out = ServiceRecordOut.model_validate(record)
    out.has_pdf = any(_is_pdf(f.filename, f.content_type) for f in record.files)
    out.has_xml = any(_is_xml(f.filename, f.content_type) for f in record.files)
    out.files = [
        ServiceFileOut(
            id=f.id,
            filename=f.filename,
            content_type=f.content_type,
            is_xml=_is_xml(f.filename, f.content_type),
        )
        for f in record.files
    ]
    return out


@router.get("", response_model=list[ServiceRecordOut])
def list_services(
    vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    records = db.scalars(
        select(ServiceRecord)
        .where(ServiceRecord.vehicle_id == vehicle.id)
        .order_by(ServiceRecord.service_date.desc(), ServiceRecord.id.desc())
    ).all()
    return [_to_out(r) for r in records]


@router.post("/upload", response_model=InvoicePreviewOut)
async def upload_invoice(
    vehicle_id: int,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recibe un PDF o XML, lo guarda en un cache temporal y devuelve un preview.

    No persiste nada en la BD todavía — eso ocurre en POST / (confirmar), que
    recibe el `upload_token` devuelto aquí. Si el archivo es XML, se intenta
    parsear como factura SUNAT UBL 2.1: emisor, ítems, total, tipo de servicio
    sugerido y si el aceite facturado coincide con el recomendado.

    Si es PDF, no hay parser automático (limitación conocida — OCR de PDF
    escaneado queda para post-MVP); el usuario completa los datos a mano.
    """
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    content = await file.read()
    filename = file.filename or "comprobante"
    content_type = file.content_type or "application/octet-stream"

    is_xml = _is_xml(filename, content_type)
    is_pdf = _is_pdf(filename, content_type)
    if not is_xml and not is_pdf:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Solo se aceptan archivos PDF o XML"
        )

    token = upload_cache.store(vehicle.id, filename, content_type, content)

    if not is_xml:
        return InvoicePreviewOut(upload_token=token, filename=filename, is_xml=False)

    try:
        parsed = parse_ubl_invoice(content)
    except InvalidInvoiceError as exc:
        return InvoicePreviewOut(
            upload_token=token, filename=filename, is_xml=True, parse_error=str(exc)
        )

    suggested = suggest_service_type(parsed.items)
    recommended_viscosity = None
    if vehicle.spec_json:
        recommended_viscosity = (vehicle.spec_json.get("oil") or {}).get("viscosity")
    oil_match = check_oil_match(parsed.items, recommended_viscosity)

    return InvoicePreviewOut(
        upload_token=token,
        filename=filename,
        is_xml=True,
        invoice_number=parsed.invoice_number,
        issue_date=parsed.issue_date,
        currency=parsed.currency,
        supplier_name=parsed.supplier_name,
        supplier_ruc=parsed.supplier_ruc,
        items=[InvoiceItemOut(description=i.description, amount=i.amount) for i in parsed.items],
        total=parsed.total,
        suggested_service_type=suggested,
        oil_match=OilMatchOut(**oil_match),
    )


@router.post("", response_model=ServiceRecordOut, status_code=status.HTTP_201_CREATED)
def create_service(
    vehicle_id: int,
    data: ServiceRecordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    record = ServiceRecord(
        vehicle_id=vehicle.id,
        service_date=data.service_date,
        km=data.km,
        service_type=data.service_type,
        cost=data.cost,
        workshop=data.workshop,
        ruc=data.ruc,
        notes=data.notes,
    )
    db.add(record)
    db.flush()

    if data.upload_token:
        cached = upload_cache.pop(data.upload_token, vehicle.id)
        if cached is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "El archivo subido ya expiró o no existe — vuelve a subirlo",
            )
        db.add(
            ServiceFile(
                service_record_id=record.id,
                filename=cached.filename,
                content_type=cached.content_type,
                content=cached.content,
            )
        )

    db.commit()
    db.refresh(record)
    return _to_out(record)


@router.get("/{service_id}/file")
def download_file(
    vehicle_id: int,
    service_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_owned_record(vehicle_id, service_id, user, db)
    if not record.files:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este servicio no tiene archivo adjunto")
    file = record.files[0]
    return Response(
        content=file.content,
        media_type=file.content_type,
        headers={"Content-Disposition": f'inline; filename="{file.filename}"'},
    )


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    vehicle_id: int,
    service_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_owned_record(vehicle_id, service_id, user, db)
    db.delete(record)
    db.commit()
