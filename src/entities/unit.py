"""Unit base dataclass. Concrete units subclass and override ClassVar stats."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from src.core.types import Coord, UnitClass

if TYPE_CHECKING:
    from src.core.game_state import GameState

# Given (attacker, state) return True when a positional crit condition is met.
CritPredicate = Callable[["Unit", "GameState"], bool]


@dataclass
class Unit:
    # Per-instance state. `@dataclass` makes these __init__ parameters.
    id: int
    owner_id: int
    coord: Coord
    hp: int
    has_moved: bool = False
    has_acted: bool = False

    # Class-level stats (ClassVar annotations are ignored by @dataclass).
    # Subclasses override by re-assigning without the annotation.
    kind: ClassVar[str] = ""
    unit_class: ClassVar[UnitClass] = UnitClass.LAND
    max_hp: ClassVar[int] = 10
    attack: ClassVar[int] = 1
    defense: ClassVar[int] = 0
    move: ClassVar[int] = 3
    cost: ClassVar[int] = 100
    vision_range: ClassVar[int] = 2
    attack_range: ClassVar[tuple[int, int]] = (1, 1)  # (min, max) manhattan
    rps_strong_vs: ClassVar[frozenset[str]] = frozenset()
    positional_crit_conditions: ClassVar[tuple[CritPredicate, ...]] = ()
    display_letter: ClassVar[str] = "?"
    is_hero: ClassVar[bool] = False

    @property
    def hp_ratio(self) -> float:
        return max(0.0, self.hp / self.max_hp)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0
