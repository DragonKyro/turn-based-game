"""Stable: produces Vehicle units."""
from __future__ import annotations

from typing import ClassVar

from src.core.types import UnitClass
from src.entities.building import Building


class Stable(Building):
    kind: ClassVar[str] = "stable"
    display_letter: ClassVar[str] = "S"
    produces_class: ClassVar[UnitClass | None] = UnitClass.VEHICLE
    produces_kinds: ClassVar[tuple[str, ...]] = ("knight", "scout", "ballista")
