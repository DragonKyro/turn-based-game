"""Concrete terrain instances. Levels reference these by name via TERRAIN_REGISTRY."""
from __future__ import annotations

from src.core.types import IMPASSABLE, UnitClass
from src.world.terrain import Terrain

L, V, A, W = UnitClass.LAND, UnitClass.VEHICLE, UnitClass.AIR, UnitClass.WATER

PLAINS = Terrain(
    name="plains",
    defense_bonus=0,
    move_cost={L: 1, V: 1, A: 1, W: IMPASSABLE},
)

FOREST = Terrain(
    name="forest",
    defense_bonus=2,
    move_cost={L: 2, V: 3, A: 1, W: IMPASSABLE},
    blocks_vision=True,
)

MOUNTAIN = Terrain(
    name="mountain",
    defense_bonus=4,
    move_cost={L: 3, V: IMPASSABLE, A: 1, W: IMPASSABLE},
    blocks_vision=True,
)

ROAD = Terrain(
    name="road",
    defense_bonus=0,
    move_cost={L: 1, V: 1, A: 1, W: IMPASSABLE},
)

SEA = Terrain(
    name="sea",
    defense_bonus=0,
    move_cost={L: IMPASSABLE, V: IMPASSABLE, A: 1, W: 1},
)


TERRAIN_REGISTRY: dict[str, Terrain] = {
    "plains": PLAINS,
    "forest": FOREST,
    "mountain": MOUNTAIN,
    "road": ROAD,
    "sea": SEA,
}
