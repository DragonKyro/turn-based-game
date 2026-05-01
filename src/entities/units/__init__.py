"""Registry of concrete unit kinds. Level loader looks up classes by `kind` string here."""
from __future__ import annotations

from src.entities.units.infantry import Infantry
from src.entities.units.knight import Knight
from src.entities.units.longship import Longship
from src.entities.units.wyvern import Wyvern

UNIT_REGISTRY: dict[str, type] = {
    Infantry.kind: Infantry,
    Knight.kind: Knight,
    Wyvern.kind: Wyvern,
    Longship.kind: Longship,
}

__all__ = ["UNIT_REGISTRY", "Infantry", "Knight", "Wyvern", "Longship"]
