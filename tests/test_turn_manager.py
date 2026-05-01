"""Tests for turn rotation + income."""
from __future__ import annotations

from src.core.game_state import GameState
from src.core.player import Player
from src.core.turn_manager import end_turn
from src.entities.buildings.mine import Mine
from src.entities.buildings.stronghold import Stronghold
from src.entities.units.infantry import Infantry
from src.world.map import Map
from src.world.terrain_types import PLAINS
from src.world.tile import Tile


def _two_player_state_with_income() -> GameState:
    m = Map(width=4, height=4)
    for col in range(4):
        for row in range(4):
            m.tiles[(col, row)] = Tile(terrain=PLAINS)

    p1 = Player(id=1, name="P1", faction="R", gold=0)
    p1.init_visibility(4, 4)
    p2 = Player(id=2, name="P2", faction="B", gold=0)
    p2.init_visibility(4, 4)

    u1 = Infantry(id=1, owner_id=1, coord=(0, 0), hp=Infantry.max_hp, has_moved=True, has_acted=True)
    u2 = Infantry(id=2, owner_id=2, coord=(3, 3), hp=Infantry.max_hp)
    m.tiles[(0, 0)].unit_id = 1
    m.tiles[(3, 3)].unit_id = 2

    hq1 = Stronghold(id=10, coord=(0, 1), owner_id=1)
    mine1 = Mine(id=11, coord=(1, 0), owner_id=1)
    hq2 = Stronghold(id=20, coord=(3, 2), owner_id=2)
    m.tiles[(0, 1)].building_id = 10
    m.tiles[(1, 0)].building_id = 11
    m.tiles[(3, 2)].building_id = 20

    return GameState(
        map=m,
        players={1: p1, 2: p2},
        units={1: u1, 2: u2},
        buildings={10: hq1, 11: mine1, 20: hq2},
        current_player_id=1,
    )


def test_end_turn_resets_flags_of_previous_player():
    state = _two_player_state_with_income()
    assert state.units[1].has_moved is True
    end_turn(state)
    # Flags for the previous player (1) are reset.
    assert state.units[1].has_moved is False
    assert state.units[1].has_acted is False


def test_end_turn_rotates_current_player():
    state = _two_player_state_with_income()
    assert state.current_player_id == 1
    end_turn(state)
    assert state.current_player_id == 2
    end_turn(state)
    assert state.current_player_id == 1


def test_end_turn_increments_turn_number_on_wrap():
    state = _two_player_state_with_income()
    assert state.turn_number == 1
    end_turn(state)  # 1 -> 2; no wrap yet
    assert state.turn_number == 1
    end_turn(state)  # 2 -> 1; wrap
    assert state.turn_number == 2


def test_end_turn_awards_income_from_owned_income_buildings():
    state = _two_player_state_with_income()
    # End player 1's turn -> player 2 gets income.
    end_turn(state)
    # Player 2 owns 1 stronghold (200 gold) and no mines.
    assert state.players[2].gold == Stronghold.gold_per_turn

    # End player 2's turn -> player 1 gets income.
    end_turn(state)
    # Player 1 owns 1 stronghold (200) + 1 mine (150) = 350.
    assert state.players[1].gold == Stronghold.gold_per_turn + Mine.gold_per_turn
