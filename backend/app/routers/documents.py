from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import LegalDocument, User
from app.routers.vehicles import _get_owned_vehicle
from app.schemas import (
    ImpuestoVehicularOut,
    LegalDocumentIn,
    LegalDocumentOut,
    VehicleDocumentsOut,
)
from app.services.peru_rules import citv_status, impuesto_vehicular_status, soat_status

router = APIRouter(prefix="/api/vehicles/{vehicle_id}/documents", tags=["documents"])

VALID_DOC_TYPES = ("soat", "citv")


def _get_doc(vehicle_id: int, doc_type: str, db: Session) -> LegalDocument | None:
    return db.scalar(
        select(LegalDocument).where(
            LegalDocument.vehicle_id == vehicle_id, LegalDocument.doc_type == doc_type
        )
    )


def _soat_out(doc: LegalDocument | None) -> LegalDocumentOut:
    data = soat_status(doc.expiry_date if doc else None)
    return LegalDocumentOut(
        doc_type="soat",
        reference_number=doc.reference_number if doc else None,
        expiry_date=doc.expiry_date if doc else None,
        has_data=data.get("has_data", False),
        days_remaining=data.get("days_remaining"),
        status=data.get("status", "unknown"),
    )


def _citv_out(doc: LegalDocument | None, vehicle_year: int) -> LegalDocumentOut:
    data = citv_status(vehicle_year, expiry_date=doc.expiry_date if doc else None)
    return LegalDocumentOut(
        doc_type="citv",
        reference_number=doc.reference_number if doc else None,
        expiry_date=doc.expiry_date if doc else None,
        has_data=doc is not None,
        has_history=data.get("has_history"),
        days_remaining=data.get("days_remaining"),
        status=data.get("status", "unknown"),
        message=data.get("message"),
        first_due_year=data.get("first_due_year"),
    )


@router.get("", response_model=VehicleDocumentsOut)
def get_documents(
    vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    soat_doc = _get_doc(vehicle_id, "soat", db)
    citv_doc = _get_doc(vehicle_id, "citv", db)
    impuesto = impuesto_vehicular_status(vehicle.first_registration_year)
    return VehicleDocumentsOut(
        soat=_soat_out(soat_doc),
        citv=_citv_out(citv_doc, vehicle.year),
        impuesto_vehicular=ImpuestoVehicularOut(**impuesto),
    )


@router.put("/{doc_type}", response_model=LegalDocumentOut)
def upsert_document(
    vehicle_id: int,
    doc_type: str,
    data: LegalDocumentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if doc_type not in VALID_DOC_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tipo de documento inválido (usa soat o citv)")
    vehicle = _get_owned_vehicle(vehicle_id, user, db)

    doc = _get_doc(vehicle_id, doc_type, db)
    if doc is None:
        doc = LegalDocument(vehicle_id=vehicle.id, doc_type=doc_type)
        db.add(doc)
    doc.reference_number = data.reference_number
    doc.expiry_date = data.expiry_date
    db.commit()
    db.refresh(doc)

    if doc_type == "soat":
        return _soat_out(doc)
    return _citv_out(doc, vehicle.year)


@router.delete("/{doc_type}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    vehicle_id: int,
    doc_type: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_vehicle(vehicle_id, user, db)
    doc = _get_doc(vehicle_id, doc_type, db)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay documento registrado de ese tipo")
    db.delete(doc)
    db.commit()
