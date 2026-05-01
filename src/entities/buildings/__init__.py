"""Registry of building kinds."""
from __future__ import annotations

from src.entities.buildings.aerie import Aerie
from src.entities.buildings.barracks import Barracks
from src.entities.buildings.harbor import Harbor
from src.entities.buildings.mine import Mine
from src.entities.buildings.stable import Stable
from src.entities.buildings.stronghold import Stronghold

BUILDING_REGISTRY: dict[str, type] = {
    Stronghold.kind: Stronghold,
    Barracks.kind: Barracks,
    Stable.kind: Stable,
    Aerie.kind: Aerie,
    Harbor.kind: Harbor,
    Mine.kind: Mine,
}

__all__ = [
    "BUILDING_REGISTRY",
    "Stronghold", "Barracks", "Stable", "Aerie", "Harbor", "Mine",
]
