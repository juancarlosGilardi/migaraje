import re
import time

import httpx

NHTSA_BASE = "https://vpic.nhtsa.dot.gov/api/vehicles"
CACHE_TTL_SECONDS = 24 * 60 * 60
VEHICLE_TYPES = ("car", "truck", "multipurpose passenger vehicle (mpv)")

_JUNK_PATTERN = re.compile(
    r"\b(CUSTOM|KUSTOM|COACHWORKS|IRONWORKS|FABRICATION|CONVERSIONS?|REPLICA|"
    r"STAGEWAY|KIT CAR|CONCEPTS?|CLASSICS?|RACING|MOTORSPORTS?|SPECIALTIES|"
    r"ENTERPRISES?|TRANSPORTS?|WORKS,? INC|CORPORATION$|CUSTOMS$)\b",
    re.IGNORECASE,
)

# Marcas más vendidas en Perú: aparecen primero en el buscador, con su forma de escritura habitual.
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
_PRIORITY_DISPLAY = {m.upper(): m for m in PRIORITY_MAKES}

_ACRONYMS = {"BMW", "MG", "JAC", "DFSK", "GMC", "SEAT", "RAM"}

_cache: dict[str, tuple[float, list[str]]] = {}


def _display_name(raw: str) -> str:
    key = raw.strip().upper()
    if key in _PRIORITY_DISPLAY:
        return _PRIORITY_DISPLAY[key]
    if key in _ACRONYMS:
        return key
    return raw.strip().title()


def _fetch_makes_for_type(vehicle_type: str) -> list[str]:
    with httpx.Client(timeout=10) as client:
        res = client.get(
            f"{NHTSA_BASE}/getmakesforvehicletype/{vehicle_type}", params={"format": "json"}
        )
        res.raise_for_status()
        return [r["MakeName"] for r in res.json()["Results"]]


def get_makes() -> list[str]:
    cached = _cache.get("makes")
    if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    raw_names: set[str] = set()
    for vtype in VEHICLE_TYPES:
        try:
            raw_names.update(_fetch_makes_for_type(vtype))
        except httpx.HTTPError:
            continue

    seen: dict[str, str] = {}  # upper -> display name, dedup por marca
    for raw in raw_names:
        if _JUNK_PATTERN.search(raw):
            continue
        key = raw.strip().upper()
        seen.setdefault(key, _display_name(raw))

    def sort_key(item: tuple[str, str]):
        key, display = item
        priority = _PRIORITY_UPPER.get(key, len(PRIORITY_MAKES) + 1)
        return (priority, display.lower())

    ordered = sorted(seen.items(), key=sort_key)
    result = [display for _, display in ordered]

    if result:
        _cache["makes"] = (time.time(), result)
    return result


def get_models(make: str) -> list[str]:
    cache_key = f"models:{make.lower()}"
    cached = _cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    with httpx.Client(timeout=10) as client:
        res = client.get(f"{NHTSA_BASE}/getmodelsformake/{make}", params={"format": "json"})
        res.raise_for_status()
        names = sorted({r["Model_Name"].strip() for r in res.json()["Results"]})

    if names:
        _cache[cache_key] = (time.time(), names)
    return names
