from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import Driver, User
from app.schemas import DriverIn, DriverOut, DriverUpdate
from app.services.peru_rules import brevete_status

router = APIRouter(prefix="/api/drivers", tags=["drivers"])


def _get_owned_driver(driver_id: int, user: User, db: Session) -> Driver:
    driver = db.get(Driver, driver_id)
    if driver is None or driver.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conductor no encontrado")
    return driver


def _to_out(driver: Driver) -> DriverOut:
    out = DriverOut.model_validate(driver)
    status_data = brevete_status(driver.license_expiry, driver.birth_date)
    out.has_data = status_data.get("has_data", False)
    out.days_remaining = status_data.get("days_remaining")
    out.status = status_data.get("status", "unknown")
    out.age = status_data.get("age")
    out.renewal_period_years = status_data.get("renewal_period_years")
    return out


@router.get("", response_model=list[DriverOut])
def list_drivers(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    drivers = db.scalars(
        select(Driver).where(Driver.user_id == user.id).order_by(Driver.created_at)
    ).all()
    return [_to_out(d) for d in drivers]


@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(
    data: DriverIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    driver = Driver(user_id=user.id, **data.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return _to_out(driver)


@router.patch("/{driver_id}", response_model=DriverOut)
def update_driver(
    driver_id: int,
    data: DriverUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    driver = _get_owned_driver(driver_id, user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return _to_out(driver)


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
    driver_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    driver = _get_owned_driver(driver_id, user, db)
    db.delete(driver)
    db.commit()
