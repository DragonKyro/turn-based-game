"""Reified player actions. The UI, AI, and tests all construct these and hand them to game_rules."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.types import Coord


@dataclass(frozen=True)
class MoveAction:
    unit_id: int
    destination: Coord


@dataclass(frozen=True)
class AttackAction:
    unit_id: int
    target_unit_id: int


@dataclass(frozen=True)
class BuildAction:
    building_id: int
    unit_kind: str


@dataclass(frozen=True)
class CaptureAction:
    unit_id: int       # the capturing unit (must be an infantry-class unit on a capturable building)
    building_id: int


@dataclass(frozen=True)
class ActivateUltimateAction:
    hero_id: int


@dataclass(frozen=True)
class EndTurnAction:
    pass


Action = MoveAction | AttackAction | BuildAction | CaptureAction | ActivateUltimateAction | EndTurnAction
