"""Integration tests for the action spine: chains of Move -> Attack -> Build -> EndTurn."""
from __future__ import annotations

import pytest

from src.core.actions import (
    ActivateUltimateAction,
    AttackAction,
    BuildAction,
    EndTurnAction,
    MoveAction,
)
from src.core.game_rules import IllegalAction, apply_action
from src.core.game_state import GameState
from src.core.player import Player
from src.entities.buildings.barracks import Barracks
from src.entities.buildings.stronghold import Stronghold
from src.entities.heroes.emberlord import Emberlord
from src.core.types import VisState
from src.entities.units.infantry import Infantry
from src.entities.units.wyvern import Wyvern
from src.world.map import Map
from src.world.terrain_types import PLAINS
from src.world.tile import Tile


def _state() -> GameState:
    m = Map(width=6, height=6)
    for col in range(6):
        for row in range(6):
            m.tiles[(col, row)] = Tile(terrain=PLAINS)

    p1 = Player(id=1, name="P1", faction="emberdyne", gold=500)
    p1.visibility = [[VisState.VISIBLE for _ in range(6)] for _ in range(6)]
    p2 = Player(id=2, name="P2", faction="frostmoor", gold=500)
    p2.visibility = [[VisState.VISIBLE for _ in range(6)] for _ in range(6)]

    hero = Emberlord(id=1, owner_id=1, coord=(0, 0), hp=Emberlord.max_hp)
    inf1 = Infantry(id=2, owner_id=1, coord=(1, 0), hp=Infantry.max_hp)
    wyv2 = Wyvern(id=3, owner_id=2, coord=(5, 0), hp=Wyvern.max_hp)
    p1.hero_id = 1

    m.tiles[(0, 0)].unit_id = 1
    m.tiles[(1, 0)].unit_id = 2
    m.tiles[(5, 0)].unit_id = 3

    hq = Stronghold(id=10, coord=(0, 1), owner_id=1)
    barracks = Barracks(id=11, coord=(0, 2), owner_id=1)
    enemy_hq = Stronghold(id=20, coord=(5, 5), owner_id=2)
    m.tiles[(0, 1)].building_id = 10
    m.tiles[(0, 2)].building_id = 11
    m.tiles[(5, 5)].building_id = 20

    return GameState(
        map=m,
        players={1: p1, 2: p2},
        units={1: hero, 2: inf1, 3: wyv2},
        buildings={10: hq, 11: barracks, 20: enemy_hq},
        current_player_id=1,
    )


def test_move_then_flag_set_and_second_move_rejected():
    state = _state()
    apply_action(state, MoveAction(unit_id=2, destination=(2, 0)))
    assert state.units[2].coord == (2, 0)
    assert state.units[2].has_moved is True
    with pytest.raises(IllegalAction, match="already moved"):
        apply_action(state, MoveAction(unit_id=2, destination=(3, 0)))


def test_cannot_move_opponent_unit():
    state = _state()
    with pytest.raises(IllegalAction, match="opponent"):
        apply_action(state, MoveAction(unit_id=3, destination=(4, 0)))


def test_attack_out_of_range_rejected():
    state = _state()
    # Infantry at (1,0), Wyvern at (5,0). Range too far.
    with pytest.raises(IllegalAction, match="attack range"):
        apply_action(state, AttackAction(unit_id=2, target_unit_id=3))


def test_move_then_attack_sequence():
    state = _state()
    # Move the hero up next to the infantry first, keeping charge check intact.
    apply_action(state, MoveAction(unit_id=2, destination=(4, 0)))  # infantry to (4,0) — adjacent to wyvern
    apply_action(state, AttackAction(unit_id=2, target_unit_id=3))
    # Attacker used its action this turn:
    assert state.units[2].has_acted is True


def test_build_spends_gold_and_creates_unit():
    state = _state()
    gold_before = state.players[1].gold
    events = apply_action(state, BuildAction(building_id=11, unit_kind="infantry"))
    ev = events[0]
    assert ev["type"] == "unit_built"
    # Wargroove-style adjacent spawn: unit appears on a tile next to the building, not on it.
    col, row = state.buildings[11].coord
    spawn_col, spawn_row = ev["coord"]
    assert abs(spawn_col - col) + abs(spawn_row - row) == 1
    new_id = ev["unit_id"]
    assert state.units[new_id].hp == Infantry.max_hp
    assert state.units[new_id].has_moved and state.units[new_id].has_acted
    assert state.players[1].gold == gold_before - Infantry.cost
    assert state.buildings[11].has_produced is True


def test_build_rejected_if_poor():
    state = _state()
    state.players[1].gold = 50
    with pytest.raises(IllegalAction, match="Not enough gold"):
        apply_action(state, BuildAction(building_id=11, unit_kind="infantry"))


def test_cannot_produce_wrong_class():
    state = _state()
    with pytest.raises(IllegalAction, match="cannot produce"):
        apply_action(state, BuildAction(building_id=11, unit_kind="wyvern"))  # barracks -> land only


def test_ultimate_requires_full_charge():
    state = _state()
    with pytest.raises(IllegalAction, match="not ready"):
        apply_action(state, ActivateUltimateAction(hero_id=1))


def test_attacking_building_reduces_hp_and_flips_ownership_at_zero():
    state = _state()
    # Park an infantry adjacent to the enemy stronghold (for deterministic adjacency).
    state.map.tiles[(1, 0)].unit_id = None
    state.units[2].coord = (5, 4)  # adjacent to stronghold at (5, 5)
    state.map.tiles[(5, 4)].unit_id = 2
    state.units[2].has_moved = False
    state.units[2].has_acted = False

    hq = state.buildings[20]
    start_hp = hq.hp
    events = apply_action(state, AttackAction(unit_id=2, target_building_id=20))

    # Exactly one "building_attacked" event; HP must drop.
    assert events[0]["type"] == "building_attacked"
    assert state.buildings[20].hp < start_hp
    assert state.buildings[20].owner_id == 2

    # Hammer it until it flips. Reset flags between attacks.
    for _ in range(50):
        if state.buildings[20].owner_id == 1:
            break
        state.units[2].has_moved = False
        state.units[2].has_acted = False
        events = apply_action(state, AttackAction(unit_id=2, target_building_id=20))
    assert state.buildings[20].owner_id == 1
    # HP resets to max after capture
    assert state.buildings[20].hp == type(state.buildings[20]).max_hp


def test_cannot_attack_own_building():
    state = _state()
    # P1 infantry attempting to attack P1's own HQ.
    state.map.tiles[(1, 0)].unit_id = None
    state.units[2].coord = (0, 2)  # adjacent to own stronghold at (0, 1)
    state.map.tiles[(0, 2)].unit_id = 2
    state.units[2].has_moved = False
    state.units[2].has_acted = False
    with pytest.raises(IllegalAction, match="own building"):
        apply_action(state, AttackAction(unit_id=2, target_building_id=10))


def test_end_turn_event_reports_current_player():
    state = _state()
    events = apply_action(state, EndTurnAction())
    assert events[0]["type"] == "end_turn"
    assert events[0]["current_player"] == 2
