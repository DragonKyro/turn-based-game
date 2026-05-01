"""Registry of concrete unit kinds. Level loader looks up classes by `kind` string here."""
from __future__ import annotations

from src.entities.units.archer import Archer
from src.entities.units.ballista import Ballista
from src.entities.units.griffon import Griffon
from src.entities.units.infantry import Infantry
from src.entities.units.knight import Knight
from src.entities.units.longship import Longship
from src.entities.units.scout import Scout
from src.entities.units.spearman import Spearman
from src.entities.units.warship import Warship
from src.entities.units.wyvern import Wyvern

UNIT_REGISTRY: dict[str, type] = {
    Infantry.kind: Infantry,
    Archer.kind: Archer,
    Spearman.kind: Spearman,
    Knight.kind: Knight,
    Scout.kind: Scout,
    Ballista.kind: Ballista,
    Wyvern.kind: Wyvern,
    Griffon.kind: Griffon,
    Longship.kind: Longship,
    Warship.kind: Warship,
}

__all__ = [
    "UNIT_REGISTRY",
    "Infantry", "Archer", "Spearman",
    "Knight", "Scout", "Ballista",
    "Wyvern", "Griffon",
    "Longship", "Warship",
]
