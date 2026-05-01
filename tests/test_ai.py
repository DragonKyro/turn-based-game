"""Sanity tests for the dumb AI: it moves toward the enemy, attacks when in range, ends the turn."""
from __future__ import annotations

from src.core.ai import take_turn
from src.core.coord import manhattan
from src.core.game_state import GameState
from src.core.player import Player
from src.entities.buildings.barracks import Barracks
from src.entities.units.infantry import Infantry
from src.world.map import Map
from src.world.terrain_types import PLAINS
from src.world.tile import Tile


def _state(ai_starts_at, enemy_at, extras=()) -> GameState:
    m = Map(width=8, height=3)
    for col in range(8):
        for row in range(3):
            m.tiles[(col, row)] = Tile(terrain=PLAINS)

    p1 = Player(id=1, name="P1", faction="R", gold=0)
    p1.init_visibility(8, 3)
    p2 = Player(id=2, name="AI", faction="B", gold=0, is_ai=True)
    p2.init_visibility(8, 3)

    enemy = Infantry(id=1, owner_id=1, coord=enemy_at, hp=Infantry.max_hp)
    ai_unit = Infantry(id=2, owner_id=2, coord=ai_starts_at, hp=Infantry.max_hp)
    m.tiles[enemy_at].unit_id = 1
    m.tiles[ai_starts_at].unit_id = 2

    state = GameState(
        map=m,
        players={1: p1, 2: p2},
        units={1: enemy, 2: ai_unit},
        buildings={},
        current_player_id=2,
    )
    for b in extras:
        state.buildings[b.id] = b
        state.map.tiles[b.coord].building_id = b.id
    return state


def test_ai_moves_toward_nearest_enemy():
    state = _state(ai_starts_at=(0, 1), enemy_at=(7, 1))
    before = state.units[2].coord
    take_turn(state)
    after = state.units[2].coord
    # Should have moved closer to the enemy.
    assert manhattan(after, (7, 1)) < manhattan(before, (7, 1))


def test_ai_attacks_when_in_range():
    state = _state(ai_starts_at=(5, 1), enemy_at=(6, 1))
    enemy_hp_before = state.units[1].hp
    take_turn(state)
    # Enemy should have taken damage.
    assert state.units[1].hp < enemy_hp_before


def test_ai_ends_the_turn():
    state = _state(ai_starts_at=(0, 1), enemy_at=(7, 1))
    assert state.current_player_id == 2
    take_turn(state)
    assert state.current_player_id == 1


def test_ai_produces_units_when_affordable():
    barracks = Barracks(id=99, coord=(4, 1), owner_id=2)  # adjacent tiles free
    state = _state(ai_starts_at=(1, 1), enemy_at=(7, 1), extras=(barracks,))
    state.players[2].gold = 500  # enough for infantry (cost 100)
    unit_count_before = len(state.units)
    take_turn(state)
    assert len(state.units) > unit_count_before
    # New unit must belong to P2 and be adjacent to the barracks (adjacent-spawn rule).
    bx, by = barracks.coord
    new_units = [
        u for u in state.units.values()
        if u.owner_id == 2 and abs(u.coord[0] - bx) + abs(u.coord[1] - by) == 1
    ]
    assert len(new_units) >= 1
