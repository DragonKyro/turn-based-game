"""Building base + flavours: Production (spawns units), Currency (gold), Stronghold (HQ, both).

Buildings have HP now. Instead of a separate "capture" action, they are attacked like units:
damage reduces HP; at 0 HP the building flips to the attacker's owner and HP restores to max.
Attackers never DESTROY buildings — they always flip ownership.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from src.core.types import Coord, UnitClass


@dataclass
class Building:
    id: int
    coord: Coord
    owner_id: int | None  # None = neutral / capturable
    hp: int = -1   # -1 sentinel: set to max_hp in __post_init__
    has_produced: bool = False

    kind: ClassVar[str] = ""
    display_letter: ClassVar[str] = "?"
    max_hp: ClassVar[int] = 15
    gold_per_turn: ClassVar[int] = 0
    is_hq: ClassVar[bool] = False
    vision_range: ClassVar[int] = 2

    produces_class: ClassVar[UnitClass | None] = None
    produces_kinds: ClassVar[tuple[str, ...]] = ()

    def __post_init__(self) -> None:
        if self.hp < 0:
            self.hp = type(self).max_hp

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def can_produce(self, unit_kind: str) -> bool:
        return unit_kind in self.produces_kinds
