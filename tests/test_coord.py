"""Tests for src.core.coord."""
from __future__ import annotations

from src.core.coord import grid_to_pixel, manhattan, neighbors4, pixel_to_grid, within_range


def test_neighbors4_returns_four_orthogonal():
    assert set(neighbors4((2, 2))) == {(3, 2), (1, 2), (2, 3), (2, 1)}


def test_manhattan_distance():
    assert manhattan((0, 0), (3, 4)) == 7
    assert manhattan((5, 5), (5, 5)) == 0


def test_within_range_excludes_center_when_lo_positive():
    result = set(within_range((0, 0), 1, 2))
    assert (0, 0) not in result
    assert (1, 0) in result
    assert (2, 0) in result
    assert (3, 0) not in result  # outside hi


def test_grid_pixel_round_trip():
    # Any grid coord -> center pixel -> back to the same grid coord.
    for col in range(-3, 10):
        for row in range(-3, 10):
            px, py = grid_to_pixel((col, row), 48)
            assert pixel_to_grid(px, py, 48) == (col, row)


def test_pixel_to_grid_floors_within_tile():
    # Clicks anywhere inside tile (0,0) resolve to (0,0).
    assert pixel_to_grid(0, 0, 48) == (0, 0)
    assert pixel_to_grid(47.9, 47.9, 48) == (0, 0)
    # One pixel into the next tile
    assert pixel_to_grid(48, 0, 48) == (1, 0)
