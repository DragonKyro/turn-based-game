"""Griffon: balanced mid-cost flyer. Weaker than wyverns but with better vision."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import adjacent_to_commander, hp_above
from src.entities.unit import CritPredicate, Unit


class Griffon(Unit):
    kind: ClassVar[str] = "griffon"
    unit_class: ClassVar[UnitClass] = UnitClass.AIR
    max_hp: ClassVar[int] = 9
    attack: ClassVar[int] = 6
    defense: ClassVar[int] = 1
    move: ClassVar[int] = 5
    cost: ClassVar[int] = 350
    vision_range: ClassVar[int] = 5
    attack_range: ClassVar[tuple[int, int]] = (1, 1)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"archer"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        adjacent_to_commander,
        hp_above(0.7),
    )
    display_letter: ClassVar[str] = "g"
