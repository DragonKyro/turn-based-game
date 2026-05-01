"""Coordinate math. Grid origin is bottom-left — column increases rightward, row increases upward.

Never mix pixel (x, y) and grid (col, row) in the same function signature. Use the helpers here.
"""
from __future__ import annotations

from src.core.types import Coord


def neighbors4(c: Coord) -> list[Coord]:
    col, row = c
    return [(col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)]


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def within_range(center: Coord, lo: int, hi: int) -> list[Coord]:
    """All coords whose manhattan distance from center is in [lo, hi]."""
    col, row = center
    out: list[Coord] = []
    for dc in range(-hi, hi + 1):
        for dr in range(-hi, hi + 1):
            d = abs(dc) + abs(dr)
            if lo <= d <= hi:
                out.append((col + dc, row + dr))
    return out


def grid_to_pixel(c: Coord, tile_size: int) -> tuple[float, float]:
    """Center of tile `c` in world pixel coordinates."""
    col, row = c
    return (col * tile_size + tile_size / 2, row * tile_size + tile_size / 2)


def pixel_to_grid(x: float, y: float, tile_size: int) -> Coord:
    return (int(x // tile_size), int(y // tile_size))
