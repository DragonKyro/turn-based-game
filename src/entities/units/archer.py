"""Archer: ranged land unit. Soft but reaches 1-2 tiles; suffers no counter from melee adjacency."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.crit_rules import hp_above, on_terrain
from src.entities.unit import CritPredicate, Unit


class Archer(Unit):
    kind: ClassVar[str] = "archer"
    unit_class: ClassVar[UnitClass] = UnitClass.LAND
    max_hp: ClassVar[int] = 8
    attack: ClassVar[int] = 6
    defense: ClassVar[int] = 0
    move: ClassVar[int] = 3
    cost: ClassVar[int] = 200
    vision_range: ClassVar[int] = 3
    attack_range: ClassVar[tuple[int, int]] = (1, 2)
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset({"infantry", "spearman"})
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = (
        on_terrain("forest", "mountain"),  # high ground shooting
        hp_above(0.85),
    )
    display_letter: ClassVar[str] = "R"
