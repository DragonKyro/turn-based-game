"""Tests for terrain data and registry."""
from __future__ import annotations

from src.core.types import IMPASSABLE, UnitClass
from src.world.terrain_types import MOUNTAIN, PLAINS, SEA, TERRAIN_REGISTRY


def test_registry_has_known_terrains():
    assert set(TERRAIN_REGISTRY.keys()) >= {"plains", "forest", "mountain", "road", "sea"}


def test_plains_passable_to_land_but_not_water():
    assert PLAINS.passable_for(UnitClass.LAND)
    assert PLAINS.passable_for(UnitClass.VEHICLE)
    assert PLAINS.passable_for(UnitClass.AIR)
    assert not PLAINS.passable_for(UnitClass.WATER)


def test_sea_only_air_and_water():
    assert SEA.passable_for(UnitClass.WATER)
    assert SEA.passable_for(UnitClass.AIR)
    assert not SEA.passable_for(UnitClass.LAND)
    assert not SEA.passable_for(UnitClass.VEHICLE)


def test_mountain_blocks_vehicle_but_not_land():
    assert MOUNTAIN.passable_for(UnitClass.LAND)
    assert not MOUNTAIN.passable_for(UnitClass.VEHICLE)


def test_impassable_uses_sentinel():
    assert SEA.cost_for(UnitClass.LAND) == IMPASSABLE
