"""Hero: a Unit subclass with an ultimate that charges up over play."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from src.entities.unit import Unit

if TYPE_CHECKING:
    from src.core.game_state import GameState


@dataclass
class Hero(Unit):
    # Adds one per-instance field on top of Unit:
    ultimate_charge: int = 0

    ultimate_charge_max: ClassVar[int] = 10
    is_hero: ClassVar[bool] = True

    def add_charge(self, amount: int = 1) -> None:
        self.ultimate_charge = min(self.ultimate_charge + amount, self.ultimate_charge_max)

    def can_activate_ultimate(self) -> bool:
        return self.ultimate_charge >= self.ultimate_charge_max

    # Subclasses override and return a list of effect descriptors for the UI.
    def activate_ultimate(self, state: "GameState") -> list[dict]:
        raise NotImplementedError
