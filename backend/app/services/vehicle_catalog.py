"""Catálogo de marcas/modelos de vehículos.

Consulta la base de datos propia (tablas catalog_makes / catalog_models),
poblada por app/seeds/import_vehicle_catalog.py a partir de NHTSA vPIC más
agregados curados para el mercado peruano. Ya no se hace proxy en vivo a
NHTSA en cada request: es más rápido y no depende de un servicio externo
para el uso normal de la app.

Mantiene la misma firma que la versión anterior (get_makes() / get_models(make))
para no romper app/routers/catalog.py ni los tests existentes.
"""

from app.db import SessionLocal
from app.models import CatalogMake, CatalogModel

# Marcas más vendidas en Perú: aparecen primero en el buscador.
PRIORITY_MAKES = [
    "Toyota", "Hyundai", "Kia", "Nissan", "Chevrolet", "Suzuki", "Mitsubishi",
    "Volkswagen", "Ford", "Honda", "Mazda", "Subaru", "Renault", "Peugeot",
    "BMW", "Mercedes-Benz", "Audi", "Jeep", "Fiat", "Great Wall", "Changan",
    "JAC", "Chery", "MG", "BYD", "Volvo", "Land Rover", "MINI", "Porsche",
    "Isuzu", "SsangYong", "Foton", "Dongfeng", "Geely", "DFSK", "SEAT",
    "Citroën", "Skoda", "Jaguar", "Lexus", "Acura", "Infiniti", "Tesla",
    "Mahindra", "Tata", "Daihatsu", "Opel", "Alfa Romeo",
]
_PRIORITY_UPPER = {m.upper(): i for i, m in enumerate(PRIORITY_MAKES)}


def _sort_key(name: str):
    priority = _PRIORITY_UPPER.get(name.strip().upper(), len(PRIORITY_MAKES) + 1)
    return (priority, name.lower())


def get_makes() -> list[str]:
    """Todas las marcas del catálogo propio, con las populares en Perú primero."""
    db = SessionLocal()
    try:
        names = [m.name for m in db.query(CatalogMake).all()]
    finally:
        db.close()
    return sorted(names, key=_sort_key)


def get_models(make: str) -> list[str]:
    """Modelos de una marca (case-insensitive). Lista vacía si la marca no existe."""
    db = SessionLocal()
    try:
        make_row = (
            db.query(CatalogMake)
            .filter(CatalogMake.name.ilike(make.strip()))
            .one_or_none()
        )
        if make_row is None:
            return []
        names = [m.name for m in db.query(CatalogModel).filter(CatalogModel.make_id == make_row.id)]
    finally:
        db.close()
    return sorted(names)
