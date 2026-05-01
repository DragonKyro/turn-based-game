"""Stronghold: player HQ. Generates gold and is the victory target. Does NOT produce units."""
from __future__ import annotations

from typing import ClassVar

from src.entities.building import Building


class Stronghold(Building):
    kind: ClassVar[str] = "stronghold"
    display_letter: ClassVar[str] = "H"
    is_hq: ClassVar[bool] = True
    gold_per_turn: ClassVar[int] = 200
    vision_range: ClassVar[int] = 3
    max_hp: ClassVar[int] = 25  # HQs are tougher than ordinary buildings
    # No production — produces_kinds inherited from Building default (empty).
