from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import PlanItem, User
from app.routers.vehicles import _current_km, _get_owned_vehicle
from app.schemas import PlanItemCreate, PlanItemOut, PlanItemUpdate
from app.services.plan_progress import compute_progress

router = APIRouter(prefix="/api/vehicles/{vehicle_id}/plan", tags=["plan"])


def _get_owned_item(vehicle_id: int, item_id: int, user: User, db: Session) -> PlanItem:
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    item = db.get(PlanItem, item_id)
    if item is None or item.vehicle_id != vehicle.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ítem del plan no encontrado")
    return item


def _to_out(item: PlanItem, current_km: int) -> PlanItemOut:
    out = PlanItemOut.model_validate(item)
    progress = compute_progress(item, current_km)
    out.due_km = progress.due_km
    out.km_remaining = progress.km_remaining
    out.due_date = progress.due_date
    out.days_remaining = progress.days_remaining
    out.percent = progress.percent
    out.status = progress.status
    return out


@router.get("", response_model=list[PlanItemOut])
def list_plan(
    vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    current_km = _current_km(vehicle.id, db)
    items = db.scalars(
        select(PlanItem).where(PlanItem.vehicle_id == vehicle.id).order_by(PlanItem.id)
    ).all()
    return [_to_out(item, current_km) for item in items]


@router.post("", response_model=PlanItemOut, status_code=status.HTTP_201_CREATED)
def create_plan_item(
    vehicle_id: int,
    data: PlanItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    current_km = _current_km(vehicle.id, db)
    item = PlanItem(vehicle_id=vehicle.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_out(item, current_km)


@router.patch("/{item_id}", response_model=PlanItemOut)
def update_plan_item(
    vehicle_id: int,
    item_id: int,
    data: PlanItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _get_owned_item(vehicle_id, item_id, user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    current_km = _current_km(item.vehicle_id, db)
    return _to_out(item, current_km)


@router.post("/{item_id}/mark-done", response_model=PlanItemOut)
def mark_done(
    vehicle_id: int,
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marca el servicio como hecho hoy, al kilometraje actual del vehículo."""
    item = _get_owned_item(vehicle_id, item_id, user, db)
    current_km = _current_km(item.vehicle_id, db)
    item.last_service_km = current_km
    item.last_service_date = date.today()
    db.commit()
    db.refresh(item)
    return _to_out(item, current_km)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan_item(
    vehicle_id: int,
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _get_owned_item(vehicle_id, item_id, user, db)
    db.delete(item)
    db.commit()
