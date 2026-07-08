"""Cache temporal en memoria para archivos subidos en preview, antes de confirmar.

Diseño elegido (prioriza simplicidad, ver plan de F4): el endpoint POST /upload
no persiste nada en la BD todavía. Guarda el archivo original (bytes + nombre +
content_type) en un dict de proceso, indexado por un `upload_token` (uuid4) con
expiración corta. El endpoint POST / (confirmar) recibe ese mismo token y solo
entonces crea el ServiceRecord + ServiceFile en la base de datos.

No es apto para múltiples workers/procesos (un cache in-memory no se comparte
entre procesos uvicorn), pero el despliegue actual corre un solo proceso
systemd — suficiente para el MVP. Si se escala a múltiples workers, migrar a
Redis o similar.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

_TTL_SECONDS = 15 * 60  # 15 minutos es de sobra para revisar el preview y confirmar


@dataclass
class CachedUpload:
    filename: str
    content_type: str
    content: bytes
    vehicle_id: int
    expires_at: float


_cache: dict[str, CachedUpload] = {}


def _purge_expired() -> None:
    now = time.time()
    expired = [token for token, item in _cache.items() if item.expires_at < now]
    for token in expired:
        _cache.pop(token, None)


def store(vehicle_id: int, filename: str, content_type: str, content: bytes) -> str:
    _purge_expired()
    token = uuid.uuid4().hex
    _cache[token] = CachedUpload(
        filename=filename,
        content_type=content_type,
        content=content,
        vehicle_id=vehicle_id,
        expires_at=time.time() + _TTL_SECONDS,
    )
    return token


def pop(token: str, vehicle_id: int) -> CachedUpload | None:
    """Recupera y elimina el archivo cacheado. None si no existe, expiró, o es de otro vehículo."""
    _purge_expired()
    item = _cache.pop(token, None)
    if item is None or item.vehicle_id != vehicle_id:
        return None
    return item
