from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import MaintenanceComponent, User
from app.schemas import MaintenanceComponentOut
from app.services import vehicle_catalog

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("/makes", response_model=list[str])
def list_makes(user: User = Depends(get_current_user)):
    makes = vehicle_catalog.get_makes()
    if not makes:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "No se pudo obtener el catálogo de marcas. Puedes escribir la marca manualmente.",
        )
    return makes


@router.get("/models", response_model=list[str])
def list_models(make: str, user: User = Depends(get_current_user)):
    if not make.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Falta indicar la marca")
    return vehicle_catalog.get_models(make.strip())


@router.get("/components", response_model=list[MaintenanceComponentOut])
def list_components(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(MaintenanceComponent).order_by(MaintenanceComponent.category, MaintenanceComponent.name)
    ).all()
