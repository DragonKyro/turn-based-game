"""Tile occupies one grid cell: terrain + optional IDs for unit/building currently on it."""
from __future__ import annotations

from dataclasses import dataclass

from src.world.terrain import Terrain


@dataclass
class Tile:
    terrain: Terrain
    unit_id: int | None = None
    building_id: int | None = None
