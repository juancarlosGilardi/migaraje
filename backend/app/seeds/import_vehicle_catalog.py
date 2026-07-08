"""Importa el catálogo de marcas/modelos de vehículos a la base de datos propia.

Reutiliza la lógica de filtrado ya existente en app.services.nhtsa_client (marcas
car+truck+mpv, sin nombres de talleres/customs) y para cada marca descarga sus
modelos desde NHTSA vPIC (GetModelsForMake) con concurrencia moderada. Al final
mezcla el archivo curado catalog_additions.json con modelos importantes para el
mercado peruano que NHTSA no tiene (ej. Toyota Hilux).

Idempotente: puede volver a ejecutarse sin duplicar filas (verifica existencia
antes de insertar / hace upsert por nombre).

IMPORTANTE: este script hace llamadas HTTPS reales a NHTSA. Desde la laptop de
desarrollo (Windows) esas llamadas fallan por inspección TLS de la red local
(CERTIFICATE_VERIFY_FAILED). Debe ejecutarse en el VPS de producción, donde sí
hay conectividad:

    ssh vps-facturape
    cd /opt/migaraje/backend
    source venv/bin/activate  # o venv/bin/python directamente
    python -m app.seeds.import_vehicle_catalog

Uso recomendado en el VPS para procesos largos (varios minutos):

    nohup venv/bin/python -m app.seeds.import_vehicle_catalog > /tmp/import_catalog.log 2>&1 &
    tail -f /tmp/import_catalog.log
"""

import asyncio
import json
import re
import sys
import time
from pathlib import Path

import httpx

from app.db import SessionLocal
from app.models import CatalogMake, CatalogModel

NHTSA_BASE = "https://vpic.nhtsa.dot.gov/api/vehicles"
VEHICLE_TYPES = ("car", "truck", "multipurpose passenger vehicle (mpv)")
CONCURRENCY = 6
ADDITIONS_PATH = Path(__file__).parent / "catalog_additions.json"

# --- Mismo filtro/priorización que vehicle_catalog.py (mantenido en sync a mano;
#     si cambia uno, revisar el otro) ---

_JUNK_PATTERN = re.compile(
    r"\b(CUSTOM|KUSTOM|COACHWORKS|IRONWORKS|FABRICATION|CONVERSIONS?|REPLICA|"
    r"STAGEWAY|KIT CAR|CONCEPTS?|CLASSICS?|RACING|MOTORSPORTS?|SPECIALTIES|"
    r"ENTERPRISES?|TRANSPORTS?|WORKS,? INC|CORPORATION$|CUSTOMS$)\b",
    re.IGNORECASE,
)

PRIORITY_MAKES = [
    "Toyota", "Hyundai", "Kia", "Nissan", "Chevrolet", "Suzuki", "Mitsubishi",
    "Volkswagen", "Ford", "Honda", "Mazda", "Subaru", "Renault", "Peugeot",
    "BMW", "Mercedes-Benz", "Audi", "Jeep", "Fiat", "Great Wall", "Changan",
    "JAC", "Chery", "MG", "BYD", "Volvo", "Land Rover", "MINI", "Porsche",
    "Isuzu", "SsangYong", "Foton", "Dongfeng", "Geely", "DFSK", "SEAT",
    "Citroën", "Skoda", "Jaguar", "Lexus", "Acura", "Infiniti", "Tesla",
    "Mahindra", "Tata", "Daihatsu", "Opel", "Alfa Romeo",
]
_PRIORITY_DISPLAY = {m.upper(): m for m in PRIORITY_MAKES}
_ACRONYMS = {"BMW", "MG", "JAC", "DFSK", "GMC", "SEAT", "RAM"}


def _display_name(raw: str) -> str:
    key = raw.strip().upper()
    if key in _PRIORITY_DISPLAY:
        return _PRIORITY_DISPLAY[key]
    if key in _ACRONYMS:
        return key
    return raw.strip().title()


async def _fetch_makes_for_type(client: httpx.AsyncClient, vehicle_type: str) -> list[str]:
    res = await client.get(
        f"{NHTSA_BASE}/getmakesforvehicletype/{vehicle_type}", params={"format": "json"}
    )
    res.raise_for_status()
    return [r["MakeName"] for r in res.json()["Results"]]


async def fetch_all_makes() -> list[str]:
    """Devuelve las marcas filtradas (sin talleres/customs), en su forma de display."""
    async with httpx.AsyncClient(timeout=15) as client:
        raw_names: set[str] = set()
        for vtype in VEHICLE_TYPES:
            try:
                raw_names.update(await _fetch_makes_for_type(client, vtype))
            except httpx.HTTPError as exc:
                print(f"  [WARN] no se pudo obtener marcas de tipo {vtype!r}: {exc}")

    seen: dict[str, str] = {}
    for raw in raw_names:
        if _JUNK_PATTERN.search(raw):
            continue
        key = raw.strip().upper()
        seen.setdefault(key, _display_name(raw))

    return sorted(seen.values(), key=str.lower)


async def _fetch_models_for_make(
    client: httpx.AsyncClient, sem: asyncio.Semaphore, make: str
) -> tuple[str, list[str]]:
    async with sem:
        try:
            res = await client.get(
                f"{NHTSA_BASE}/getmodelsformake/{make}", params={"format": "json"}
            )
            res.raise_for_status()
            names = sorted({r["Model_Name"].strip() for r in res.json()["Results"] if r["Model_Name"]})
            return make, names
        except httpx.HTTPError as exc:
            print(f"  [WARN] modelos de {make!r} fallaron: {exc}")
            return make, []


def _get_or_create_make(db, name: str, source: str) -> CatalogMake:
    make = db.query(CatalogMake).filter(CatalogMake.name == name).one_or_none()
    if make is None:
        make = CatalogMake(name=name, source=source)
        db.add(make)
        db.flush()  # asigna id sin cerrar la transacción
    return make


def _upsert_models(db, make: CatalogMake, model_names: list[str], source: str) -> int:
    existing = {
        m.name for m in db.query(CatalogModel).filter(CatalogModel.make_id == make.id)
    }
    added = 0
    for name in model_names:
        if not name or name in existing:
            continue
        db.add(CatalogModel(make_id=make.id, name=name, source=source))
        existing.add(name)
        added += 1
    return added


async def import_from_nhtsa() -> None:
    print("Descargando lista de marcas desde NHTSA (car + truck + mpv)...")
    makes = await fetch_all_makes()
    total_makes = len(makes)
    print(f"  {total_makes} marcas encontradas tras filtrar talleres/customs.")

    print(f"Descargando modelos para cada marca (concurrencia={CONCURRENCY})...")
    sem = asyncio.Semaphore(CONCURRENCY)
    start = time.time()
    results: dict[str, list[str]] = {}

    async with httpx.AsyncClient(timeout=15) as client:
        tasks = [_fetch_models_for_make(client, sem, make) for make in makes]
        done = 0
        for coro in asyncio.as_completed(tasks):
            make, models = await coro
            results[make] = models
            done += 1
            if done % 25 == 0 or done == total_makes:
                elapsed = time.time() - start
                print(f"  [{done}/{total_makes}] marcas procesadas ({elapsed:.0f}s transcurridos)")

    print("Descarga completa. Escribiendo en la base de datos...")
    db = SessionLocal()
    try:
        makes_added = 0
        models_added = 0
        for make_name in makes:
            model_names = results.get(make_name, [])
            make_row = db.query(CatalogMake).filter(CatalogMake.name == make_name).one_or_none()
            is_new_make = make_row is None
            make_row = _get_or_create_make(db, make_name, source="nhtsa")
            if is_new_make:
                makes_added += 1
            models_added += _upsert_models(db, make_row, model_names, source="nhtsa")
        db.commit()
        print(
            f"NHTSA importado: {makes_added} marcas nuevas, {models_added} modelos nuevos "
            f"(de {total_makes} marcas procesadas)."
        )
    finally:
        db.close()


def import_curated_additions() -> None:
    if not ADDITIONS_PATH.exists():
        print(f"  [WARN] no existe {ADDITIONS_PATH}, se omite el paso de agregados curados.")
        return

    data = json.loads(ADDITIONS_PATH.read_text(encoding="utf-8"))
    entries = data.get("makes", [])
    print(f"Aplicando agregados curados para Perú/Latam ({len(entries)} marcas en el archivo)...")

    db = SessionLocal()
    try:
        makes_added = 0
        models_added = 0
        for entry in entries:
            name = entry["name"].strip()
            model_names = [m.strip() for m in entry.get("models", []) if m.strip()]

            make_row = db.query(CatalogMake).filter(CatalogMake.name == name).one_or_none()
            is_new_make = make_row is None
            # Si la marca ya vino de NHTSA, se mantiene source='nhtsa' (solo se agregan
            # los modelos faltantes); si es una marca 100% nueva, se marca 'custom'.
            make_row = _get_or_create_make(db, name, source="custom")
            if is_new_make:
                makes_added += 1
            models_added += _upsert_models(db, make_row, model_names, source="custom")
        db.commit()
        print(f"Agregados curados aplicados: {makes_added} marcas nuevas, {models_added} modelos nuevos.")
    finally:
        db.close()


def print_summary() -> None:
    db = SessionLocal()
    try:
        n_makes = db.query(CatalogMake).count()
        n_models = db.query(CatalogModel).count()
        print(f"Total en la base de datos ahora: {n_makes} marcas, {n_models} modelos.")
    finally:
        db.close()


async def main() -> None:
    start = time.time()
    await import_from_nhtsa()
    import_curated_additions()
    print_summary()
    print(f"Listo en {time.time() - start:.0f}s.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
        sys.exit(1)
