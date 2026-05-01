"""GameState: the root container. All game logic reads from here; only a small set of modules write."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from src.core.player import Player
from src.core.types import Coord
from src.entities.building import Building
from src.entities.unit import Unit
from src.world.map import Map


@dataclass
class VictoryResult:
    winner_id: int
    reason: str


@dataclass
class GameState:
    map: Map
    players: dict[int, Player]
    units: dict[int, Unit]
    buildings: dict[int, Building]
    current_player_id: int
    turn_number: int = 1
    victory: VictoryResult | None = None
    next_entity_id: int = 1_000  # ids beyond those baked in by the level loader

    # --- queries ---
    def unit_at(self, c: Coord) -> Unit | None:
        t = self.map.tiles.get(c)
        if t is None or t.unit_id is None:
            return None
        return self.units.get(t.unit_id)

    def building_at(self, c: Coord) -> Building | None:
        t = self.map.tiles.get(c)
        if t is None or t.building_id is None:
            return None
        return self.buildings.get(t.building_id)

    def units_of(self, player_id: int) -> Iterator[Unit]:
        for u in self.units.values():
            if u.owner_id == player_id and u.is_alive:
                yield u

    def buildings_of(self, player_id: int) -> Iterator[Building]:
        for b in self.buildings.values():
            if b.owner_id == player_id:
                yield b

    def allocate_id(self) -> int:
        self.next_entity_id += 1
        return self.next_entity_id
