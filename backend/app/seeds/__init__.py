import json
from functools import lru_cache
from pathlib import Path
from typing import Any

TEMPLATES_PATH = Path(__file__).parent / "templates.json"


@lru_cache
def _load_templates() -> list[dict[str, Any]]:
    return json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))


def find_template(brand: str, model: str) -> dict[str, Any]:
    """Busca la plantilla por marca/modelo (coincidencia flexible); si no hay match usa la genérica."""
    brand_norm = brand.strip().lower()
    model_norm = model.strip().lower()
    templates = _load_templates()

    for tpl in templates:
        if tpl["match_brand"] == "*":
            continue
        if tpl["match_brand"] == brand_norm and tpl["match_model"] in model_norm:
            return tpl

    return next(tpl for tpl in templates if tpl["match_brand"] == "*")
