"""Terrain value object. Data-only; behavior (combat/vision rules) lives in core modules."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.types import IMPASSABLE, UnitClass


@dataclass(frozen=True)
class Terrain:
    name: str
    defense_bonus: int
    move_cost: dict[UnitClass, int]
    blocks_vision: bool = False

    def cost_for(self, unit_class: UnitClass) -> int:
        return self.move_cost.get(unit_class, IMPASSABLE)

    def passable_for(self, unit_class: UnitClass) -> bool:
        return self.cost_for(unit_class) < IMPASSABLE
