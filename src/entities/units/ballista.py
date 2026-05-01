"""Ballista: slow vehicle with long-range, high-damage siege attack. Cannot counter up close."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import hp_above
from src.entities.unit import CritPredicate, Unit


class Ballista(Unit):
    kind: ClassVar[str] = "ballista"
    unit_class: ClassVar[UnitClass] = UnitClass.VEHICLE
    max_hp: ClassVar[int] = 9
    attack: ClassVar[int] = 9
    defense: ClassVar[int] = 1
    move: ClassVar[int] = 3
    cost: ClassVar[int] = 400
    vision_range: ClassVar[int] = 2
    attack_range: ClassVar[tuple[int, int]] = (2, 4)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"knight", "ballista"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        hp_above(0.75),
    )
    display_letter: ClassVar[str] = "b"
