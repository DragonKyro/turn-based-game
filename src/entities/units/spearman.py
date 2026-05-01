"""Spearman: land anti-cavalry. Slightly sturdier than infantry, deadly to Knights."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import adjacent_to_commander
from src.entities.unit import CritPredicate, Unit


class Spearman(Unit):
    kind: ClassVar[str] = "spearman"
    unit_class: ClassVar[UnitClass] = UnitClass.LAND
    max_hp: ClassVar[int] = 11
    attack: ClassVar[int] = 5
    defense: ClassVar[int] = 2
    move: ClassVar[int] = 3
    cost: ClassVar[int] = 150
    vision_range: ClassVar[int] = 2
    attack_range: ClassVar[tuple[int, int]] = (1, 1)
    # Anti-cavalry + anti-dragon — spears punch above their weight vs mounted & flying targets.
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"knight", "wyvern"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        adjacent_to_commander,
    )
    display_letter: ClassVar[str] = "P"
