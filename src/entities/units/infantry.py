"""Infantry: cheap line trooper. Strong vs Wyverns (pikes skyward). Can capture buildings."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import adjacent_to_commander, on_terrain
from src.entities.unit import CritPredicate, Unit


class Infantry(Unit):
    kind: ClassVar[str] = "infantry"
    unit_class: ClassVar[UnitClass] = UnitClass.LAND
    max_hp: ClassVar[int] = 10
    attack: ClassVar[int] = 5
    defense: ClassVar[int] = 1
    move: ClassVar[int] = 3
    cost: ClassVar[int] = 100
    vision_range: ClassVar[int] = 2
    attack_range: ClassVar[tuple[int, int]] = (1, 1)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"wyvern"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        adjacent_to_commander,
        on_terrain("forest"),
    )
    display_letter: ClassVar[str] = "I"
