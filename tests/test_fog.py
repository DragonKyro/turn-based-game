"""Tests for fog of war visibility."""
from __future__ import annotations

from src.core.fog import recompute_visibility
from src.core.game_state import GameState
from src.core.player import Player
from src.core.types import VisState
from src.entities.units.infantry import Infantry
from src.world.map import Map
from src.world.terrain_types import FOREST, PLAINS
from src.world.tile import Tile


def _blank_state(terrain_grid) -> GameState:
    height = len(terrain_grid)
    width = len(terrain_grid[0])
    m = Map(width=width, height=height)
    for visual_row, row in enumerate(terrain_grid):
        grid_row = height - 1 - visual_row
        for col, t in enumerate(row):
            m.tiles[(col, grid_row)] = Tile(terrain=t)
    p1 = Player(id=1, name="P1", faction="R", gold=0)
    p1.init_visibility(width, height)
    return GameState(map=m, players={1: p1}, units={}, buildings={}, current_player_id=1)


def test_vision_marks_tiles_within_range():
    state = _blank_state([[PLAINS] * 5] * 5)
    u = Infantry(id=1, owner_id=1, coord=(2, 2), hp=Infantry.max_hp)
    state.units[1] = u
    state.map.tiles[(2, 2)].unit_id = 1
    recompute_visibility(state, 1)
    vis = state.players[1].visibility
    # Infantry vision_range=2 (diamond).
    assert vis[2][2] == VisState.VISIBLE
    assert vis[0][2] == VisState.VISIBLE
    assert vis[4][2] == VisState.VISIBLE
    # Corner (0,0) is manhattan 4 away — outside range.
    assert vis[0][0] == VisState.HIDDEN


def test_forest_blocks_vision_unless_adjacent():
    # A forest tile two away should be hidden; a forest tile one away should still be VISIBLE.
    state = _blank_state([
        [PLAINS, PLAINS, PLAINS, PLAINS, PLAINS],
        [PLAINS, FOREST, PLAINS, FOREST, PLAINS],
        [PLAINS, PLAINS, PLAINS, PLAINS, PLAINS],
    ])
    u = Infantry(id=1, owner_id=1, coord=(2, 0), hp=Infantry.max_hp)
    state.units[1] = u
    state.map.tiles[(2, 0)].unit_id = 1
    recompute_visibility(state, 1)
    vis = state.players[1].visibility
    # Adjacent forest at (1, 1) visible-adjacent, distance 2 so not "adjacent" in our rule.
    # Our rule: forest visible only when manhattan <= 1. So (1,1) at distance 2 is HIDDEN.
    # (Adjust if the rule is relaxed later.)
    assert vis[1][1] == VisState.HIDDEN
    assert vis[3][1] == VisState.HIDDEN


def test_visible_demotes_to_explored_on_recompute():
    # 9-wide map so moving from col 0 to col 8 takes (2,1) out of vision range 2.
    state = _blank_state([[PLAINS] * 9] * 3)
    u = Infantry(id=1, owner_id=1, coord=(0, 1), hp=Infantry.max_hp)
    state.units[1] = u
    state.map.tiles[(0, 1)].unit_id = 1
    recompute_visibility(state, 1)
    assert state.players[1].visibility[2][1] == VisState.VISIBLE

    # Move the unit far away
    state.map.tiles[(0, 1)].unit_id = None
    u.coord = (8, 1)
    state.map.tiles[(8, 1)].unit_id = 1
    recompute_visibility(state, 1)
    # (2,1) is now manhattan 6 away — way outside vision 2.
    # Should have been demoted to EXPLORED (not back to HIDDEN).
    assert state.players[1].visibility[2][1] == VisState.EXPLORED
