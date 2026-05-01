"""Wyvern: flying unit. Ignores most terrain costs. Strong vs Knights."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import adjacent_to_commander
from src.entities.unit import CritPredicate, Unit


class Wyvern(Unit):
    kind: ClassVar[str] = "wyvern"
    unit_class: ClassVar[UnitClass] = UnitClass.AIR
    max_hp: ClassVar[int] = 11
    attack: ClassVar[int] = 8
    defense: ClassVar[int] = 0
    move: ClassVar[int] = 6
    cost: ClassVar[int] = 500
    vision_range: ClassVar[int] = 4
    attack_range: ClassVar[tuple[int, int]] = (1, 1)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"knight"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        adjacent_to_commander,
    )
    display_letter: ClassVar[str] = "W"
