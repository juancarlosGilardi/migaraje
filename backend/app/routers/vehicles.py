from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import OdometerLog, PlanItem, User, Vehicle
from app.schemas import OdometerIn, OdometerOut, VehicleIn, VehicleOut, VehicleUpdate
from app.seeds import find_template

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


def _get_owned_vehicle(vehicle_id: int, user: User, db: Session) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehículo no encontrado")
    return vehicle


def _current_km(vehicle_id: int, db: Session) -> int:
    return db.scalar(
        select(func.max(OdometerLog.km)).where(OdometerLog.vehicle_id == vehicle_id)
    ) or 0


def _to_out(vehicle: Vehicle, db: Session) -> VehicleOut:
    out = VehicleOut.model_validate(vehicle)
    out.current_km = _current_km(vehicle.id, db)
    out.spec = vehicle.spec_json
    return out


def _seed_plan_and_spec(vehicle: Vehicle, initial_km: int) -> None:
    """Copia la plantilla de marca/modelo como ficha técnica y plan de mantenimiento inicial."""
    template = find_template(vehicle.brand, vehicle.model)
    vehicle.spec_json = template["spec"]
    today = date.today()
    for item in template["plan_items"]:
        vehicle.plan_items.append(
            PlanItem(
                name=item["name"],
                interval_km=item["interval_km"],
                interval_months=item["interval_months"],
                last_service_km=initial_km,
                last_service_date=today,
                notes=item["notes"],
            )
        )


@router.get("", response_model=list[VehicleOut])
def list_vehicles(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicles = db.scalars(
        select(Vehicle).where(Vehicle.user_id == user.id).order_by(Vehicle.created_at)
    ).all()
    return [_to_out(v, db) for v in vehicles]


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    data: VehicleIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    vehicle = Vehicle(
        user_id=user.id,
        brand=data.brand.strip(),
        model=data.model.strip(),
        year=data.year,
        plate=data.plate.strip().upper(),
        fuel=data.fuel,
        first_registration_year=data.first_registration_year,
    )
    db.add(vehicle)
    db.flush()
    if data.initial_km > 0:
        db.add(OdometerLog(vehicle_id=vehicle.id, km=data.initial_km, recorded_on=date.today()))
    _seed_plan_and_spec(vehicle, data.initial_km)
    db.commit()
    db.refresh(vehicle)
    return _to_out(vehicle, db)


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(
    vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _to_out(_get_owned_vehicle(vehicle_id, user, db), db)


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    changes = data.model_dump(exclude_unset=True)
    if "plate" in changes and changes["plate"]:
        changes["plate"] = changes["plate"].strip().upper()
    for field, value in changes.items():
        setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return _to_out(vehicle, db)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    db.delete(vehicle)
    db.commit()


@router.post("/{vehicle_id}/odometer", response_model=VehicleOut)
def add_odometer(
    vehicle_id: int,
    data: OdometerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    current = _current_km(vehicle.id, db)
    if data.km < current:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"El kilometraje no puede ser menor al último registrado ({current:,} km)",
        )
    db.add(
        OdometerLog(
            vehicle_id=vehicle.id,
            km=data.km,
            recorded_on=data.recorded_on or date.today(),
            source=data.source,
        )
    )
    db.commit()
    return _to_out(vehicle, db)


@router.get("/{vehicle_id}/odometer", response_model=list[OdometerOut])
def list_odometer(
    vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    vehicle = _get_owned_vehicle(vehicle_id, user, db)
    return db.scalars(
        select(OdometerLog)
        .where(OdometerLog.vehicle_id == vehicle.id)
        .order_by(OdometerLog.km.desc())
        .limit(50)
    ).all()
