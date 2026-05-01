"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from src.core.game_state import GameState
from src.core.player import Player
from src.core.types import UnitClass
from src.entities.units.infantry import Infantry
from src.entities.units.wyvern import Wyvern
from src.world.map import Map
from src.world.terrain_types import PLAINS
from src.world.tile import Tile


@pytest.fixture
def tiny_map() -> Map:
    m = Map(width=5, height=5)
    for col in range(5):
        for row in range(5):
            m.tiles[(col, row)] = Tile(terrain=PLAINS)
    return m


@pytest.fixture
def two_player_state(tiny_map: Map) -> GameState:
    p1 = Player(id=1, name="P1", faction="Red", gold=500)
    p1.init_visibility(tiny_map.width, tiny_map.height)
    p2 = Player(id=2, name="P2", faction="Blue", gold=500, is_ai=True)
    p2.init_visibility(tiny_map.width, tiny_map.height)

    # one infantry per side, placed
    u1 = Infantry(id=1, owner_id=1, coord=(1, 1), hp=Infantry.max_hp)
    u2 = Infantry(id=2, owner_id=2, coord=(3, 3), hp=Infantry.max_hp)
    tiny_map.tiles[(1, 1)].unit_id = 1
    tiny_map.tiles[(3, 3)].unit_id = 2

    state = GameState(
        map=tiny_map,
        players={1: p1, 2: p2},
        units={1: u1, 2: u2},
        buildings={},
        current_player_id=1,
    )
    return state


@pytest.fixture
def combat_ready_state(tiny_map: Map) -> GameState:
    """Attacker (infantry) and defender (wyvern, weak to infantry) adjacent."""
    p1 = Player(id=1, name="P1", faction="Red", gold=0)
    p1.init_visibility(tiny_map.width, tiny_map.height)
    p2 = Player(id=2, name="P2", faction="Blue", gold=0)
    p2.init_visibility(tiny_map.width, tiny_map.height)

    attacker = Infantry(id=1, owner_id=1, coord=(2, 2), hp=Infantry.max_hp)
    defender = Wyvern(id=2, owner_id=2, coord=(3, 2), hp=Wyvern.max_hp)
    tiny_map.tiles[(2, 2)].unit_id = 1
    tiny_map.tiles[(3, 2)].unit_id = 2

    state = GameState(
        map=tiny_map,
        players={1: p1, 2: p2},
        units={1: attacker, 2: defender},
        buildings={},
        current_player_id=1,
    )
    # wire hero_id to attacker so adjacent_to_commander crit rule can be exercised
    p1.hero_id = 1  # treat attacker as its own "commander" for the test — overridable
    _ = UnitClass  # silence unused import when this fixture is reused
    return state
