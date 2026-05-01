"""Per-tile terrain decorations.

Each function draws a terrain tile's texture (trees, rocks, waves, cobbles, grass tufts).
Variation is seeded on (col, row) so a tile is visually stable across frames but differs from
its neighbors. Detail stays within the inner 60-70% of the tile so units and buildings centered
on the tile remain unambiguous.
"""
from __future__ import annotations

import math
import random

import arcade

from src.config import COLORS, TILE_SIZE

# Colors
_DARK = (0, 0, 0)
_SHADOW = (30, 25, 35)


def _tile_rand(coord: tuple[int, int]) -> random.Random:
    """Deterministic per-tile RNG so the same tile always looks the same."""
    col, row = coord
    return random.Random(col * 73_856_093 ^ row * 19_349_663)


def draw_tile_decoration(coord: tuple[int, int], terrain_name: str,
                         fog_factor: float) -> None:
    """Draw per-terrain decorations on the given tile.

    fog_factor in [0, 1]: 1 = fully visible, <1 = darken decorations too so EXPLORED
    tiles look correctly dimmed.
    """
    col, row = coord
    cx = col * TILE_SIZE + TILE_SIZE / 2
    cy = row * TILE_SIZE + TILE_SIZE / 2
    rng = _tile_rand(coord)
    if terrain_name == "plains":
        _draw_plains(cx, cy, rng, fog_factor)
    elif terrain_name == "forest":
        _draw_forest(cx, cy, rng, fog_factor)
    elif terrain_name == "mountain":
        _draw_mountain(cx, cy, rng, fog_factor)
    elif terrain_name == "road":
        _draw_road(coord, cx, cy, rng, fog_factor)
    elif terrain_name == "sea":
        _draw_sea(cx, cy, rng, fog_factor)


def _apply_fog(color: tuple[int, int, int], fog_factor: float) -> tuple[int, int, int]:
    if fog_factor >= 1.0:
        return color
    return (int(color[0] * fog_factor), int(color[1] * fog_factor), int(color[2] * fog_factor))


# -----------------------------------------------------------------------------
# Plains: a couple of grass tufts, rare tiny flower.
# -----------------------------------------------------------------------------
def _draw_plains(cx: float, cy: float, rng: random.Random, fog: float) -> None:
    base = _apply_fog(COLORS["plains"], fog)
    grass_a = _apply_fog((90, 140, 70), fog)
    grass_b = _apply_fog((155, 195, 120), fog)
    flower = _apply_fog((245, 220, 90), fog)

    n_tufts = rng.randint(2, 4)
    for _ in range(n_tufts):
        ox = rng.uniform(-TILE_SIZE * 0.34, TILE_SIZE * 0.34)
        oy = rng.uniform(-TILE_SIZE * 0.34, TILE_SIZE * 0.34)
        # Skip tufts near the tile center (so units on top aren't cluttered)
        if abs(ox) < TILE_SIZE * 0.14 and abs(oy) < TILE_SIZE * 0.14:
            continue
        # Tiny V-shape blades
        arcade.draw_line(cx + ox, cy + oy, cx + ox - 2, cy + oy + 3, grass_a, 1)
        arcade.draw_line(cx + ox, cy + oy, cx + ox + 2, cy + oy + 3, grass_b, 1)
        arcade.draw_line(cx + ox, cy + oy, cx + ox, cy + oy + 4, grass_a, 1)

    # Rare flower
    if rng.random() < 0.12:
        fx = cx + rng.uniform(-TILE_SIZE * 0.3, TILE_SIZE * 0.3)
        fy = cy + rng.uniform(-TILE_SIZE * 0.3, TILE_SIZE * 0.3)
        if abs(fx - cx) > TILE_SIZE * 0.18 or abs(fy - cy) > TILE_SIZE * 0.18:
            arcade.draw_circle_filled(fx, fy, 1.5, flower)
    _ = base


# -----------------------------------------------------------------------------
# Forest: 2-3 small trees arranged around the edges of the tile.
# -----------------------------------------------------------------------------
def _draw_forest(cx: float, cy: float, rng: random.Random, fog: float) -> None:
    # Very dark background so the lighter trees read clearly
    arcade.draw_lbwh_rectangle_filled(
        cx - TILE_SIZE / 2, cy - TILE_SIZE / 2, TILE_SIZE, TILE_SIZE,
        _apply_fog((38, 85, 48), fog),
    )

    trunk = _apply_fog((70, 48, 30), fog)
    canopy_dark = _apply_fog((30, 75, 40), fog)
    canopy_light = _apply_fog((85, 140, 70), fog)

    # Tree positions around the edges so center stays mostly clear for units
    positions: list[tuple[float, float, float]] = []  # (x, y, radius)
    candidates = [
        (-0.28, 0.22, 0.17), (0.24, 0.26, 0.18), (-0.24, -0.28, 0.15), (0.28, -0.22, 0.17),
        (0.0, 0.30, 0.14), (0.0, -0.30, 0.14),
    ]
    rng.shuffle(candidates)
    for dx, dy, dr in candidates[: rng.randint(2, 3)]:
        positions.append((cx + dx * TILE_SIZE, cy + dy * TILE_SIZE, dr * TILE_SIZE))

    for (x, y, r) in positions:
        # Trunk (small)
        arcade.draw_lbwh_rectangle_filled(x - 1, y - r * 0.8, 2, r * 0.8, trunk)
        # Canopy (two overlapping circles for a bushy look)
        arcade.draw_circle_filled(x, y + r * 0.1, r, canopy_dark)
        arcade.draw_circle_filled(x - r * 0.3, y + r * 0.3, r * 0.55, canopy_light)


# -----------------------------------------------------------------------------
# Mountain: 1-2 rocky peaks with a snow cap. Placed to not block tile center entirely.
# -----------------------------------------------------------------------------
def _draw_mountain(cx: float, cy: float, rng: random.Random, fog: float) -> None:
    arcade.draw_lbwh_rectangle_filled(
        cx - TILE_SIZE / 2, cy - TILE_SIZE / 2, TILE_SIZE, TILE_SIZE,
        _apply_fog((95, 78, 60), fog),
    )
    rock = _apply_fog((150, 130, 105), fog)
    rock_shadow = _apply_fog((85, 70, 55), fog)
    snow = _apply_fog((240, 240, 250), fog)

    # Pick one big peak and optionally a smaller second one.
    big_dx = rng.choice([-0.12, 0.0, 0.12])
    big_height = rng.uniform(0.30, 0.38)
    peak_x = cx + big_dx * TILE_SIZE
    base_y = cy - TILE_SIZE * 0.28
    peak_y = cy + TILE_SIZE * big_height

    arcade.draw_polygon_filled(
        [(peak_x - TILE_SIZE * 0.24, base_y),
         (peak_x + TILE_SIZE * 0.24, base_y),
         (peak_x, peak_y)],
        rock,
    )
    # Shadow face (right)
    arcade.draw_polygon_filled(
        [(peak_x, base_y), (peak_x + TILE_SIZE * 0.24, base_y), (peak_x, peak_y)],
        rock_shadow,
    )
    # Snow cap
    arcade.draw_polygon_filled(
        [(peak_x - TILE_SIZE * 0.08, cy + TILE_SIZE * 0.2),
         (peak_x + TILE_SIZE * 0.08, cy + TILE_SIZE * 0.2),
         (peak_x, peak_y)],
        snow,
    )
    # Optional small second peak
    if rng.random() < 0.5:
        side = -1 if big_dx >= 0 else 1
        px = cx + side * TILE_SIZE * 0.3
        ph = rng.uniform(0.15, 0.25)
        arcade.draw_polygon_filled(
            [(px - TILE_SIZE * 0.14, base_y),
             (px + TILE_SIZE * 0.14, base_y),
             (px, cy + TILE_SIZE * ph)],
            rock_shadow,
        )


# -----------------------------------------------------------------------------
# Road: cobblestone texture. Geometry is clipped inside the tile to avoid
# spill-over onto neighboring terrain that made the road look like rocks.
# -----------------------------------------------------------------------------
def _draw_road(coord: tuple[int, int], cx: float, cy: float,
                rng: random.Random, fog: float) -> None:
    light = _apply_fog((205, 185, 135), fog)
    dark = _apply_fog((160, 140, 95), fog)
    line = _apply_fog((120, 100, 70), fog)
    arcade.draw_lbwh_rectangle_filled(
        cx - TILE_SIZE / 2, cy - TILE_SIZE / 2, TILE_SIZE, TILE_SIZE, light
    )
    # 4x4 brick grid with a 2-px inset on all sides — bricks never touch the tile edge.
    col, row = coord
    inset = 2
    usable = TILE_SIZE - 2 * inset
    n = 4
    cell_w = usable / n
    cell_h = usable / n
    brick_gap = 1
    # Per-row horizontal shift alternates so rows "interlock" like brickwork.
    for gr in range(n):
        row_shift = (cell_w / 2) if (gr + row) % 2 else 0
        for gc in range(n):
            px = cx - TILE_SIZE / 2 + inset + gc * cell_w + row_shift
            py = cy - TILE_SIZE / 2 + inset + gr * cell_h
            # Clip any brick that would exceed the usable region.
            right = cx - TILE_SIZE / 2 + inset + usable
            if px >= right:
                continue
            w = min(cell_w - brick_gap, right - px - brick_gap)
            h = cell_h - brick_gap
            if w <= 0:
                continue
            color = dark if (gc + gr + col + row) % 2 else light
            arcade.draw_lbwh_rectangle_filled(px, py, w, h, color)
            arcade.draw_lbwh_rectangle_outline(px, py, w, h, line, 1)


# -----------------------------------------------------------------------------
# Sea: layered wave lines + occasional whitecap; deterministic phase per tile.
# -----------------------------------------------------------------------------
def _draw_sea(cx: float, cy: float, rng: random.Random, fog: float) -> None:
    base = _apply_fog((48, 94, 160), fog)
    mid = _apply_fog((70, 130, 200), fog)
    highlight = _apply_fog((170, 210, 240), fog)

    arcade.draw_lbwh_rectangle_filled(
        cx - TILE_SIZE / 2, cy - TILE_SIZE / 2, TILE_SIZE, TILE_SIZE, base
    )
    # 3 stacked horizontal wavelets with phase offsets
    for i in range(3):
        y = cy - TILE_SIZE * 0.28 + i * TILE_SIZE * 0.24
        phase = rng.uniform(0, math.tau)
        # Draw a wavy polyline
        pts = []
        for k in range(7):
            x = cx - TILE_SIZE * 0.4 + k * TILE_SIZE * 0.13
            pts.append((x, y + math.sin(phase + k * 0.7) * 1.6))
        for j in range(len(pts) - 1):
            arcade.draw_line(pts[j][0], pts[j][1], pts[j + 1][0], pts[j + 1][1], mid, 1)
    # Occasional whitecap
    if rng.random() < 0.55:
        wx = cx + rng.uniform(-TILE_SIZE * 0.2, TILE_SIZE * 0.2)
        wy = cy + rng.uniform(-TILE_SIZE * 0.2, TILE_SIZE * 0.2)
        arcade.draw_line(wx - 3, wy, wx + 3, wy, highlight, 1)
