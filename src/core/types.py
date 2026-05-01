"""Shared type aliases and enums referenced across core, world, and entity modules."""
from __future__ import annotations

from enum import Enum, auto

Coord = tuple[int, int]  # (col, row), origin bottom-left


class UnitClass(Enum):
    LAND = auto()
    VEHICLE = auto()
    AIR = auto()
    WATER = auto()


class VisState(Enum):
    HIDDEN = auto()
    EXPLORED = auto()
    VISIBLE = auto()


IMPASSABLE = 99  # sentinel used in Terrain.move_cost to mean "this class cannot enter"
