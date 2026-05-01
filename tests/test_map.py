"""Tests for src.world.map."""
from __future__ import annotations

from src.world.map import Map
from src.world.terrain_types import PLAINS
from src.world.tile import Tile


def test_in_bounds():
    m = Map(width=4, height=3)
    assert m.in_bounds((0, 0))
    assert m.in_bounds((3, 2))
    assert not m.in_bounds((4, 2))
    assert not m.in_bounds((0, 3))
    assert not m.in_bounds((-1, 0))


def test_iter_coords_bottom_left_origin():
    m = Map(width=2, height=2)
    coords = list(m.iter_coords())
    # row 0 first (bottom), then row 1 (top)
    assert coords == [(0, 0), (1, 0), (0, 1), (1, 1)]


def test_tile_lookup():
    m = Map(width=2, height=2)
    m.tiles[(0, 0)] = Tile(terrain=PLAINS)
    assert m.tile((0, 0)).terrain is PLAINS
