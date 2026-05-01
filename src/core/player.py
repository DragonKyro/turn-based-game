"""Player: a side in the match. Holds resources, fog state, and a reference to their hero."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.core.types import VisState


@dataclass
class Player:
    id: int
    name: str
    faction: str
    gold: int = 0
    hero_id: int | None = None
    is_ai: bool = False
    # visibility[col][row] -> VisState. Sized to the map at init.
    visibility: list[list[VisState]] = field(default_factory=list)

    def init_visibility(self, width: int, height: int) -> None:
        self.visibility = [[VisState.HIDDEN for _ in range(height)] for _ in range(width)]
