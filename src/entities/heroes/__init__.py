"""Registry of hero kinds."""
from __future__ import annotations

from src.entities.heroes.emberlord import Emberlord
from src.entities.heroes.frostqueen import Frostqueen

HERO_REGISTRY: dict[str, type] = {
    Emberlord.kind: Emberlord,
    Frostqueen.kind: Frostqueen,
}

__all__ = ["HERO_REGISTRY", "Emberlord", "Frostqueen"]
