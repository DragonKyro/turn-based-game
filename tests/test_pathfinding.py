"""Tests for Dijkstra reachable-set and attackable_from."""
from __future__ import annotations

from src.core.game_state import GameState
from src.core.pathfinding import attackable_from, reachable
from src.core.player import Player
from src.core.types import VisState
from src.entities.units.infantry import Infantry
from src.entities.units.knight import Knight
from src.entities.units.longship import Longship
from src.entities.units.wyvern import Wyvern
from src.world.map import Map
from src.world.terrain_types import FOREST, MOUNTAIN, PLAINS, SEA
from src.world.tile import Tile


def _blank_state(terrain_grid) -> GameState:
    height = len(terrain_grid)
    width = len(terrain_grid[0])
    m = Map(width=width, height=height)
    for visual_row, row in enumerate(terrain_grid):
        grid_row = height - 1 - visual_row
        for col, t in enumerate(row):
            m.tiles[(col, grid_row)] = Tile(terrain=t)
    # Mark the whole map VISIBLE for both players so these tests exercise pathfinding,
    # not fog-of-war restrictions (which have their own test file).
    p1 = Player(id=1, name="P1", faction="emberdyne", gold=0)
    p1.visibility = [[VisState.VISIBLE for _ in range(height)] for _ in range(width)]
    p2 = Player(id=2, name="P2", faction="frostmoor", gold=0)
    p2.visibility = [[VisState.VISIBLE for _ in range(height)] for _ in range(width)]
    return GameState(map=m, players={1: p1, 2: p2}, units={}, buildings={}, current_player_id=1)


def test_infantry_plains_range():
    state = _blank_state([[PLAINS] * 7] * 7)
    u = Infantry(id=1, owner_id=1, coord=(3, 3), hp=Infantry.max_hp)
    state.units[1] = u
    state.map.tiles[(3, 3)].unit_id = 1
    r = reachable(state, u)
    # Infantry move=3 on plains (cost 1/tile). Reachable = diamond of radius 3 minus origin.
    assert (0, 3) in r
    assert (6, 3) in r
    assert (3, 0) in r
    assert (3, 6) in r
    assert (3, 3) not in r  # origin excluded
    # Corner just outside range
    assert (0, 0) not in r


def test_forest_slows_infantry():
    state = _blank_state([
        [PLAINS, PLAINS, PLAINS],
        [PLAINS, FOREST, PLAINS],
        [PLAINS, PLAINS, PLAINS],
    ])
    # Infantry with move=3 starts bottom-left. Going through forest costs 2.
    u = Infantry(id=1, owner_id=1, coord=(0, 0), hp=Infantry.max_hp)
    state.units[1] = u
    state.map.tiles[(0, 0)].unit_id = 1
    r = reachable(state, u)
    # Going around the forest (via plains) reaches (2, 2) with cost 4 — OUT of budget 3.
    # Stepping onto the forest tile itself costs 1+2 = 3 — reachable.
    assert (1, 1) in r
    assert r[(1, 1)] == 3


def test_sea_blocks_land_but_wyvern_flies():
    state = _blank_state([
        [PLAINS, SEA, PLAINS],
        [PLAINS, SEA, PLAINS],
        [PLAINS, SEA, PLAINS],
    ])
    inf = Infantry(id=1, owner_id=1, coord=(0, 1), hp=Infantry.max_hp)
    state.units[1] = inf
    state.map.tiles[(0, 1)].unit_id = 1
    # Infantry cannot cross sea
    r = reachable(state, inf)
    assert (2, 1) not in r

    state.units.pop(1)
    state.map.tiles[(0, 1)].unit_id = None
    # Wyvern flies over sea
    w = Wyvern(id=2, owner_id=1, coord=(0, 1), hp=Wyvern.max_hp)
    state.units[2] = w
    state.map.tiles[(0, 1)].unit_id = 2
    r2 = reachable(state, w)
    assert (2, 1) in r2


def test_knight_blocked_by_mountain():
    state = _blank_state([
        [PLAINS, MOUNTAIN, PLAINS],
        [PLAINS, MOUNTAIN, PLAINS],
        [PLAINS, MOUNTAIN, PLAINS],
    ])
    k = Knight(id=1, owner_id=1, coord=(0, 1), hp=Knight.max_hp)
    state.units[1] = k
    state.map.tiles[(0, 1)].unit_id = 1
    r = reachable(state, k)
    # Mountain is impassable for vehicles — can't cross to column 2.
    assert (2, 1) not in r
    assert (0, 0) in r


def test_longship_only_sea():
    state = _blank_state([
        [SEA, SEA, SEA],
        [SEA, PLAINS, SEA],
        [SEA, SEA, SEA],
    ])
    ls = Longship(id=1, owner_id=1, coord=(0, 0), hp=Longship.max_hp)
    state.units[1] = ls
    state.map.tiles[(0, 0)].unit_id = 1
    r = reachable(state, ls)
    # Can move around the plains island but not onto it.
    assert (1, 1) not in r
    assert (2, 0) in r  # around by sea


def test_enemy_blocks_allied_passes_through():
    state = _blank_state([[PLAINS] * 5] * 3)
    mover = Infantry(id=1, owner_id=1, coord=(0, 1), hp=Infantry.max_hp)
    ally = Infantry(id=2, owner_id=1, coord=(2, 1), hp=Infantry.max_hp)
    enemy = Infantry(id=3, owner_id=2, coord=(4, 1), hp=Infantry.max_hp)
    for u in (mover, ally, enemy):
        state.units[u.id] = u
        state.map.tiles[u.coord].unit_id = u.id
    r = reachable(state, mover)
    # (2,1) is occupied by ally — pass-through allowed but cannot stop there.
    assert (2, 1) not in r
    # (3,1) past ally is reachable.
    assert (3, 1) in r
    # (4,1) is enemy — blocked, cannot reach and cannot stop.
    assert (4, 1) not in r


def test_reachable_excludes_hidden_tiles():
    state = _blank_state([[PLAINS] * 5] * 5)
    u = Infantry(id=1, owner_id=1, coord=(2, 2), hp=Infantry.max_hp)
    state.units[1] = u
    state.map.tiles[(2, 2)].unit_id = 1
    # Blot out two specific tiles as HIDDEN on player 1's fog.
    state.players[1].visibility[4][2] = VisState.HIDDEN
    state.players[1].visibility[2][4] = VisState.HIDDEN
    r = reachable(state, u)
    assert (4, 2) not in r  # hidden -> can't path there
    assert (2, 4) not in r
    assert (3, 2) in r       # still reachable (visible)


def test_attackable_from_ranged_unit():
    state = _blank_state([[SEA] * 7] * 7)
    ls = Longship(id=1, owner_id=1, coord=(3, 3), hp=Longship.max_hp)
    tiles = attackable_from(state, ls, (3, 3))
    # attack_range (2, 3): ring between 2 and 3 manhattan. Adjacent (dist 1) is NOT attackable.
    assert (3, 4) not in tiles      # dist 1 — too close
    assert (3, 5) in tiles          # dist 2
    assert (3, 6) in tiles          # dist 3
    assert (6, 3) in tiles          # dist 3
    assert (7, 3) not in tiles      # off map
