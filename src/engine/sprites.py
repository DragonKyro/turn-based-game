"""Procedural sprites for units and buildings.

Each draw_* function composes arcade primitives (polygons, circles, arcs, rectangles) into
a recognizable silhouette for one kind. Team color tints the primary body; accents and details
are fixed per kind. All drawn centered at (cx, cy) within a bounding circle of `size`.

No external image assets — everything is vector. This keeps the repo self-contained and lets
colors / team tints live in src/config.py's palette.
"""
from __future__ import annotations

import math

import arcade

from src.config import COLORS, TILE_SIZE
from src.entities.building import Building
from src.entities.hero import Hero
from src.entities.unit import Unit

# -----------------------------------------------------------------------------
# Colour helpers
# -----------------------------------------------------------------------------

_STEEL = (200, 205, 215)
_DARK_STEEL = (70, 80, 95)
_GOLD = COLORS["hero_accent"]
_SHADOW = (30, 25, 35)
_FLAME = (255, 140, 60)
_ICE = (180, 220, 245)
_WOOD = (120, 85, 50)
_STONE = (140, 140, 150)
_BRICK = (160, 90, 75)
_ROOF = (90, 55, 55)
_SEA_DARK = (30, 65, 120)


def _team_color(owner_id: int | None) -> tuple[int, int, int]:
    if owner_id == 1:
        return COLORS["player1"]
    if owner_id == 2:
        return COLORS["player2"]
    return (140, 140, 150)


def _darken(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def _lighten(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return (
        min(255, int(color[0] + (255 - color[0]) * factor)),
        min(255, int(color[1] + (255 - color[1]) * factor)),
        min(255, int(color[2] + (255 - color[2]) * factor)),
    )


# -----------------------------------------------------------------------------
# Building sprites
# -----------------------------------------------------------------------------

def draw_building(b: Building, cx: float, cy: float) -> None:
    color = _team_color(b.owner_id)
    s = TILE_SIZE * 0.9
    kind = b.kind
    if kind == "stronghold":
        _draw_stronghold(cx, cy, s, color)
    elif kind == "barracks":
        _draw_barracks(cx, cy, s, color)
    elif kind == "stable":
        _draw_stable(cx, cy, s, color)
    elif kind == "aerie":
        _draw_aerie(cx, cy, s, color)
    elif kind == "harbor":
        _draw_harbor(cx, cy, s, color)
    elif kind == "mine":
        _draw_mine(cx, cy, s, color)
    else:
        _draw_generic_building(cx, cy, s, color)

    # Capture progress pip
    threshold = type(b).capture_threshold
    if b.capture_progress > 0 and threshold:
        ratio = min(1.0, b.capture_progress / threshold)
        bar_w = s * 0.8
        arcade.draw_lbwh_rectangle_filled(
            cx - bar_w / 2, cy - s / 2 - 6, bar_w * ratio, 3, _GOLD
        )


def _draw_stronghold(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    """Castle keep: two crenellated towers flanking a tall center tower, team-colored banner."""
    half = s / 2
    base_bottom = cy - half + 2
    # Outer wall
    wall_h = s * 0.55
    wall_w = s * 0.95
    arcade.draw_lbwh_rectangle_filled(cx - wall_w / 2, base_bottom, wall_w, wall_h, _STONE)
    arcade.draw_lbwh_rectangle_outline(cx - wall_w / 2, base_bottom, wall_w, wall_h, _DARK_STEEL, 1)
    # Crenellations on outer wall
    cren_w = wall_w / 6
    cren_h = 4
    for i in range(6):
        if i % 2 == 0:
            lx = cx - wall_w / 2 + i * cren_w
            arcade.draw_lbwh_rectangle_filled(lx, base_bottom + wall_h, cren_w, cren_h, _STONE)
    # Central tower (tall)
    tower_w = s * 0.32
    tower_h = s * 0.78
    tx = cx - tower_w / 2
    ty = base_bottom + 4
    arcade.draw_lbwh_rectangle_filled(tx, ty, tower_w, tower_h, _lighten(_STONE, 0.08))
    arcade.draw_lbwh_rectangle_outline(tx, ty, tower_w, tower_h, _DARK_STEEL, 1)
    # Battlements on tower
    for i in range(3):
        if i % 2 == 0:
            lx = tx + i * (tower_w / 3)
            arcade.draw_lbwh_rectangle_filled(lx, ty + tower_h, tower_w / 3, cren_h, _lighten(_STONE, 0.1))
    # Banner on tower
    banner_w = tower_w * 0.6
    banner_h = tower_h * 0.45
    bx = cx - banner_w / 2
    by = ty + tower_h * 0.22
    arcade.draw_lbwh_rectangle_filled(bx, by, banner_w, banner_h, team)
    arcade.draw_lbwh_rectangle_outline(bx, by, banner_w, banner_h, _darken(team, 0.6), 1)
    # Gold cross/emblem on banner
    emblem_size = banner_w * 0.35
    arcade.draw_lbwh_rectangle_filled(cx - 1, by + banner_h * 0.3, 2, emblem_size, _GOLD)
    arcade.draw_lbwh_rectangle_filled(cx - emblem_size / 2, by + banner_h * 0.3 + emblem_size / 2 - 1,
                                       emblem_size, 2, _GOLD)
    # Arched gate at wall base
    gate_w = wall_w * 0.18
    gate_h = wall_h * 0.6
    arcade.draw_lbwh_rectangle_filled(cx - gate_w / 2, base_bottom, gate_w, gate_h, _SHADOW)


def _draw_barracks(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    """Long hall with pitched roof, a door, and two crossed swords above the door."""
    half = s / 2
    body_h = s * 0.5
    body_w = s * 0.85
    bx = cx - body_w / 2
    by = cy - half + 3
    arcade.draw_lbwh_rectangle_filled(bx, by, body_w, body_h, _BRICK)
    arcade.draw_lbwh_rectangle_outline(bx, by, body_w, body_h, _darken(_BRICK, 0.6), 1)
    # Pitched roof
    roof_top = by + body_h + s * 0.22
    arcade.draw_polygon_filled(
        [(bx - 2, by + body_h), (bx + body_w + 2, by + body_h), (cx, roof_top)], _ROOF
    )
    arcade.draw_polygon_outline(
        [(bx - 2, by + body_h), (bx + body_w + 2, by + body_h), (cx, roof_top)], _darken(_ROOF, 0.6), 1
    )
    # Team-colored flag on the peak
    arcade.draw_lbwh_rectangle_filled(cx - 1, roof_top - 1, 2, s * 0.18, _DARK_STEEL)
    arcade.draw_polygon_filled([(cx + 1, roof_top + s * 0.16), (cx + s * 0.14, roof_top + s * 0.12),
                                 (cx + 1, roof_top + s * 0.08)], team)
    # Door
    door_w = body_w * 0.18
    door_h = body_h * 0.7
    arcade.draw_lbwh_rectangle_filled(cx - door_w / 2, by, door_w, door_h, _SHADOW)
    # Crossed swords above door
    _draw_sword(cx - 3, by + door_h + 2, 14, angle_deg=45, color=_STEEL)
    _draw_sword(cx + 3, by + door_h + 2, 14, angle_deg=-45, color=_STEEL)
    # Window with team color
    win_size = body_w * 0.1
    arcade.draw_lbwh_rectangle_filled(bx + body_w * 0.15, by + body_h * 0.45, win_size, win_size, team)
    arcade.draw_lbwh_rectangle_filled(bx + body_w * 0.75, by + body_h * 0.45, win_size, win_size, team)


def _draw_stable(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    """Stable: barn with a horseshoe over a wide doorway."""
    half = s / 2
    body_h = s * 0.55
    body_w = s * 0.88
    bx = cx - body_w / 2
    by = cy - half + 3
    arcade.draw_lbwh_rectangle_filled(bx, by, body_w, body_h, _WOOD)
    arcade.draw_lbwh_rectangle_outline(bx, by, body_w, body_h, _darken(_WOOD, 0.6), 1)
    # Angled roof (gambrel-ish, just a triangle for silhouette)
    roof_top = by + body_h + s * 0.18
    arcade.draw_polygon_filled(
        [(bx - 2, by + body_h), (bx + body_w + 2, by + body_h), (cx, roof_top)], _darken(_ROOF, 0.9)
    )
    # Big double-door
    door_w = body_w * 0.45
    door_h = body_h * 0.78
    arcade.draw_lbwh_rectangle_filled(cx - door_w / 2, by, door_w, door_h, _SHADOW)
    arcade.draw_line(cx, by, cx, by + door_h, _darken(_WOOD, 0.3), 1)
    # Horseshoe above the door (gold arc)
    arcade.draw_arc_outline(cx, by + door_h + 5, 10, 10, _GOLD, 0, 180, num_segments=16, border_width=2)
    # Team banner stripe
    arcade.draw_lbwh_rectangle_filled(bx, by + body_h - 3, body_w, 3, team)


def _draw_aerie(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    """Tall spire with a perch for the wyvern (team-colored egg on the ring)."""
    half = s / 2
    # Rocky base
    base_h = s * 0.3
    base_w = s * 0.7
    bx = cx - base_w / 2
    by = cy - half + 3
    arcade.draw_polygon_filled(
        [(bx, by), (bx + base_w, by), (bx + base_w * 0.78, by + base_h),
         (bx + base_w * 0.22, by + base_h)], _STONE
    )
    # Tower
    tower_w = s * 0.3
    tower_h = s * 0.55
    tx = cx - tower_w / 2
    ty = by + base_h - 2
    arcade.draw_lbwh_rectangle_filled(tx, ty, tower_w, tower_h, _lighten(_STONE, 0.05))
    arcade.draw_lbwh_rectangle_outline(tx, ty, tower_w, tower_h, _DARK_STEEL, 1)
    # Spire cap (triangle)
    spire_top = ty + tower_h + s * 0.18
    arcade.draw_polygon_filled(
        [(tx - 2, ty + tower_h), (tx + tower_w + 2, ty + tower_h), (cx, spire_top)], _darken(_ROOF, 0.8)
    )
    # Perch ring near the top of the tower + egg in team color
    arcade.draw_circle_outline(cx, ty + tower_h * 0.7, tower_w * 0.7, _DARK_STEEL, 2)
    arcade.draw_ellipse_filled(cx, ty + tower_h * 0.7, tower_w * 0.55, tower_w * 0.7, team)
    arcade.draw_ellipse_outline(cx, ty + tower_h * 0.7, tower_w * 0.55, tower_w * 0.7, _darken(team, 0.6), 1)


def _draw_harbor(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    """Dock building on stilts with a pier and a tiny moored boat."""
    half = s / 2
    # Water under the harbor (subtle)
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.48, cy - half + 2, s * 0.96, s * 0.12,
                                       _lighten(_SEA_DARK, 0.12))
    # Stilts
    stilts_y = cy - half + 6
    for dx in (-s * 0.28, 0.0, s * 0.28):
        arcade.draw_lbwh_rectangle_filled(cx + dx - 1.5, stilts_y, 3, s * 0.18, _WOOD)
    # Dock building
    body_h = s * 0.38
    body_w = s * 0.8
    bx = cx - body_w / 2
    by = stilts_y + s * 0.18
    arcade.draw_lbwh_rectangle_filled(bx, by, body_w, body_h, _WOOD)
    arcade.draw_lbwh_rectangle_outline(bx, by, body_w, body_h, _darken(_WOOD, 0.6), 1)
    # Roof slanted
    arcade.draw_polygon_filled(
        [(bx - 2, by + body_h), (bx + body_w + 2, by + body_h),
         (bx + body_w - 4, by + body_h + s * 0.12), (bx + 4, by + body_h + s * 0.12)],
        _darken(_ROOF, 0.85),
    )
    # Team pennant
    arcade.draw_lbwh_rectangle_filled(bx + body_w * 0.4, by + body_h + s * 0.12,
                                       body_w * 0.2, s * 0.08, team)
    # Moored boat peeking out the right
    boat_x = cx + s * 0.32
    boat_y = stilts_y + 2
    arcade.draw_polygon_filled(
        [(boat_x, boat_y), (boat_x + s * 0.14, boat_y), (boat_x + s * 0.11, boat_y - 3),
         (boat_x + 3, boat_y - 3)], _darken(_WOOD, 0.5)
    )
    # Mast
    arcade.draw_line(boat_x + s * 0.06, boat_y, boat_x + s * 0.06, boat_y + s * 0.12, _WOOD, 1)


def _draw_mine(cx: float, cy: float, s: float, _team: tuple[int, int, int]) -> None:
    """Mine: a mountain with an entry arch and a pickaxe sign. Owner-agnostic visual."""
    half = s / 2
    # Mountain silhouette (two peaks)
    arcade.draw_polygon_filled(
        [(cx - s * 0.45, cy - half + 3),
         (cx + s * 0.45, cy - half + 3),
         (cx + s * 0.15, cy + half - s * 0.05),
         (cx,              cy + s * 0.15),
         (cx - s * 0.2,    cy + half - s * 0.1)],
        _STONE,
    )
    arcade.draw_polygon_outline(
        [(cx - s * 0.45, cy - half + 3),
         (cx + s * 0.45, cy - half + 3),
         (cx + s * 0.15, cy + half - s * 0.05),
         (cx,              cy + s * 0.15),
         (cx - s * 0.2,    cy + half - s * 0.1)],
        _darken(_STONE, 0.55), 1,
    )
    # Mine entrance arch
    ent_w = s * 0.22
    ent_h = s * 0.3
    arcade.draw_lbwh_rectangle_filled(cx - ent_w / 2, cy - half + 3, ent_w, ent_h, _SHADOW)
    arcade.draw_arc_filled(cx, cy - half + 3 + ent_h, ent_w, ent_w * 0.7, _SHADOW, 0, 180)
    # Rail track
    arcade.draw_line(cx, cy - half + 3, cx - s * 0.1, cy - half - 2, _DARK_STEEL, 1)
    arcade.draw_line(cx, cy - half + 3, cx + s * 0.1, cy - half - 2, _DARK_STEEL, 1)
    # Gold nugget accent glowing inside the mouth
    arcade.draw_circle_filled(cx, cy - half + 10, 3, _GOLD)


def _draw_generic_building(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    arcade.draw_lbwh_rectangle_filled(cx - s / 2 + 4, cy - s / 2 + 4, s - 8, s - 8, team)
    arcade.draw_lbwh_rectangle_outline(cx - s / 2 + 4, cy - s / 2 + 4, s - 8, s - 8, _DARK_STEEL, 2)


# -----------------------------------------------------------------------------
# Unit sprites
# -----------------------------------------------------------------------------

def draw_unit(u: Unit, cx: float, cy: float, dimmed: bool, anim_time: float = 0.0) -> None:
    team = _team_color(u.owner_id)
    if dimmed:
        team = _darken(team, 0.55)

    size = TILE_SIZE * 0.88
    kind = u.kind

    # Per-unit phase so same-kind units don't all bob in sync.
    phase = (u.id * 0.73) % math.tau
    # Ground shadow (static; stays put while sprite bobs).
    arcade.draw_ellipse_filled(cx, cy - size * 0.42, size * 0.38, size * 0.08, _SHADOW)

    # Compute per-kind idle offset / extras. Dimmed (spent) units still animate —
    # the color alone signals "acted" while the bob confirms the sprite is alive.
    bob = 0.0
    wing_scale = 1.0
    rock_deg = 0.0
    if kind == "wyvern":
        wing_scale = 1.0 + 0.15 * math.sin(anim_time * 6.0 + phase)
        bob = math.sin(anim_time * 3.0 + phase) * 1.5
    elif kind == "longship":
        rock_deg = math.sin(anim_time * 1.5 + phase) * 3.0
        bob = math.sin(anim_time * 1.5 + phase) * 1.5
    elif kind in ("emberlord", "frostqueen"):
        bob = math.sin(anim_time * 1.8 + phase) * 1.2
    else:
        bob = math.sin(anim_time * 2.0 + phase) * 1.0

    dy = bob
    if kind == "infantry":
        _draw_infantry(cx, cy + dy, size, team)
    elif kind == "knight":
        _draw_knight(cx, cy + dy, size, team)
    elif kind == "wyvern":
        _draw_wyvern(cx, cy + dy, size, team, wing_scale=wing_scale)
    elif kind == "longship":
        _draw_longship(cx, cy + dy, size, team, rock_deg=rock_deg)
    elif kind == "emberlord":
        _draw_emberlord(cx, cy + dy, size, team, dimmed=dimmed, anim_time=anim_time, phase=phase)
    elif kind == "frostqueen":
        _draw_frostqueen(cx, cy + dy, size, team, dimmed=dimmed, anim_time=anim_time, phase=phase)
    else:
        _draw_generic_unit(cx, cy + dy, size, team)

    # HP bar below the sprite (fixed position, no bob, so HP is easy to read).
    _draw_hp_bar(cx, cy - size / 2 - 4, u.hp, u.max_hp)

    # Hero ultimate-ready pulse ring: animated radius so it "breathes".
    if isinstance(u, Hero) and u.ultimate_charge >= type(u).ultimate_charge_max:
        pulse = 4 + 2 * math.sin(anim_time * 3.0)
        arcade.draw_circle_outline(cx, cy + dy, size / 2 + pulse, _GOLD, 2)

    # "Used" indicator: small dot in the corner when acted
    if u.has_acted:
        arcade.draw_circle_filled(cx + size / 2 - 4, cy - size / 2 + 4, 3, _DARK_STEEL)


def _draw_hp_bar(cx: float, cy: float, hp: int, max_hp: int) -> None:
    w = TILE_SIZE * 0.7
    h = 4
    left = cx - w / 2
    ratio = max(0.0, min(1.0, hp / max_hp))
    arcade.draw_lbwh_rectangle_filled(left, cy, w, h, COLORS["ui_panel"])
    # Color shades red as HP drops
    if ratio > 0.66:
        fill = (120, 210, 95)
    elif ratio > 0.33:
        fill = (230, 200, 70)
    else:
        fill = (220, 80, 70)
    arcade.draw_lbwh_rectangle_filled(left, cy, w * ratio, h, fill)
    arcade.draw_lbwh_rectangle_outline(left, cy, w, h, _DARK_STEEL, 1)


def _draw_infantry(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    """A soldier: rounded helmet + visor + breastplate + shield + spear."""
    # (Shadow drawn in draw_unit at static y.)
    # Body (tabard — team color, wide at waist)
    arcade.draw_polygon_filled(
        [(cx - s * 0.18, cy - s * 0.32),
         (cx + s * 0.18, cy - s * 0.32),
         (cx + s * 0.22, cy + s * 0.0),
         (cx - s * 0.22, cy + s * 0.0)],
        team,
    )
    # Breastplate
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.16, cy, s * 0.32, s * 0.2, _STEEL)
    arcade.draw_lbwh_rectangle_outline(cx - s * 0.16, cy, s * 0.32, s * 0.2, _DARK_STEEL, 1)
    # Helmet (skull cap) + visor slit
    head_y = cy + s * 0.28
    arcade.draw_circle_filled(cx, head_y, s * 0.12, _STEEL)
    arcade.draw_arc_filled(cx, head_y, s * 0.2, s * 0.2, _DARK_STEEL, 180, 360)
    arcade.draw_line(cx - s * 0.08, head_y - s * 0.02, cx + s * 0.08, head_y - s * 0.02, _SHADOW, 2)
    # Helmet plume in team color
    arcade.draw_polygon_filled(
        [(cx - s * 0.02, head_y + s * 0.1),
         (cx + s * 0.02, head_y + s * 0.1),
         (cx, head_y + s * 0.22)],
        team,
    )
    # Shield on left arm (gold emblem)
    sx = cx - s * 0.3
    arcade.draw_ellipse_filled(sx, cy + s * 0.04, s * 0.14, s * 0.22, _darken(team, 0.6))
    arcade.draw_ellipse_outline(sx, cy + s * 0.04, s * 0.14, s * 0.22, _DARK_STEEL, 1)
    arcade.draw_circle_filled(sx, cy + s * 0.04, s * 0.035, _GOLD)
    # Spear (right side, diagonal)
    spear_bottom = (cx + s * 0.28, cy - s * 0.32)
    spear_top = (cx + s * 0.42, cy + s * 0.4)
    arcade.draw_line(*spear_bottom, *spear_top, _WOOD, 2)
    # Spearhead
    arcade.draw_polygon_filled(
        [spear_top, (spear_top[0] - 2, spear_top[1] - 6), (spear_top[0] + 4, spear_top[1] - 3)],
        _STEEL,
    )


def _draw_knight(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    """Mounted knight: horse silhouette beneath a lance-wielding rider."""
    # Horse body
    body_left = cx - s * 0.36
    body_bottom = cy - s * 0.3
    body_w = s * 0.7
    body_h = s * 0.22
    arcade.draw_ellipse_filled(cx, body_bottom + body_h / 2, body_w / 2, body_h / 2, _darken(_WOOD, 0.9))
    # Legs (simple lines)
    for dx in (-s * 0.22, -s * 0.08, s * 0.08, s * 0.22):
        arcade.draw_line(cx + dx, body_bottom, cx + dx, body_bottom - s * 0.1, _darken(_WOOD, 0.7), 3)
    # Horse neck + head
    neck_start = (cx + s * 0.3, body_bottom + body_h * 0.7)
    head_pos = (cx + s * 0.42, body_bottom + body_h * 1.4)
    arcade.draw_line(*neck_start, *head_pos, _darken(_WOOD, 0.9), 6)
    arcade.draw_ellipse_filled(head_pos[0], head_pos[1], s * 0.08, s * 0.05, _darken(_WOOD, 0.9))
    # Horse mane (team tint)
    arcade.draw_polygon_filled(
        [neck_start, (neck_start[0] - 4, neck_start[1] + 10), (head_pos[0] - 5, head_pos[1])],
        team,
    )
    # Rider torso (armor + team tabard)
    rider_x = cx - s * 0.04
    rider_y = body_bottom + body_h + s * 0.08
    arcade.draw_polygon_filled(
        [(rider_x - s * 0.14, rider_y - s * 0.08),
         (rider_x + s * 0.14, rider_y - s * 0.08),
         (rider_x + s * 0.16, rider_y + s * 0.16),
         (rider_x - s * 0.16, rider_y + s * 0.16)],
        team,
    )
    # Rider helmet with visor
    head_y = rider_y + s * 0.26
    arcade.draw_circle_filled(rider_x, head_y, s * 0.1, _STEEL)
    arcade.draw_arc_filled(rider_x, head_y, s * 0.18, s * 0.18, _DARK_STEEL, 180, 360)
    arcade.draw_line(rider_x - s * 0.06, head_y - 2, rider_x + s * 0.06, head_y - 2, _SHADOW, 2)
    # Lance (diagonal right)
    lance_start = (rider_x + s * 0.1, rider_y + s * 0.04)
    lance_tip = (rider_x + s * 0.48, rider_y + s * 0.38)
    arcade.draw_line(*lance_start, *lance_tip, _WOOD, 3)
    arcade.draw_polygon_filled(
        [lance_tip, (lance_tip[0] - 3, lance_tip[1] - 7), (lance_tip[0] + 5, lance_tip[1] - 3)],
        _STEEL,
    )
    # Lance pennant (team)
    arcade.draw_polygon_filled(
        [lance_start, (lance_start[0] + s * 0.12, lance_start[1] + 4),
         (lance_start[0] + s * 0.12, lance_start[1] - 4)],
        team,
    )


def _draw_wyvern(cx: float, cy: float, s: float, team: tuple[int, int, int],
                 wing_scale: float = 1.0) -> None:
    """Dragon-like flyer: wide spread wings with team-colored membranes.

    `wing_scale` stretches the wings vertically — drive it with a sine wave for a flap effect.
    """
    wing_color = team
    wing_edge = _darken(team, 0.6)
    # Left wing — the y-offsets are scaled so the tips rise/fall with wing_scale
    left_wing = [
        (cx - s * 0.05, cy + s * 0.05 * wing_scale),
        (cx - s * 0.38, cy + s * 0.3 * wing_scale),
        (cx - s * 0.46, cy + s * 0.1 * wing_scale),
        (cx - s * 0.42, cy - s * 0.05),
        (cx - s * 0.2, cy + s * 0.0),
    ]
    arcade.draw_polygon_filled(left_wing, wing_color)
    arcade.draw_polygon_outline(left_wing, wing_edge, 2)
    right_wing = [
        (cx + s * 0.05, cy + s * 0.05 * wing_scale),
        (cx + s * 0.38, cy + s * 0.3 * wing_scale),
        (cx + s * 0.46, cy + s * 0.1 * wing_scale),
        (cx + s * 0.42, cy - s * 0.05),
        (cx + s * 0.2, cy + s * 0.0),
    ]
    arcade.draw_polygon_filled(right_wing, wing_color)
    arcade.draw_polygon_outline(right_wing, wing_edge, 2)
    # Body (dark scales)
    body_color = _darken(team, 0.4)
    arcade.draw_ellipse_filled(cx, cy - s * 0.02, s * 0.14, s * 0.28, body_color)
    arcade.draw_ellipse_outline(cx, cy - s * 0.02, s * 0.14, s * 0.28, _DARK_STEEL, 1)
    # Tail
    arcade.draw_line(cx, cy - s * 0.26, cx + s * 0.08, cy - s * 0.4, body_color, 3)
    # Head (pointed snout)
    head_base = (cx, cy + s * 0.2)
    snout_tip = (cx + s * 0.03, cy + s * 0.38)
    arcade.draw_polygon_filled(
        [(cx - s * 0.08, cy + s * 0.22),
         (cx + s * 0.08, cy + s * 0.22),
         snout_tip],
        body_color,
    )
    _ = head_base  # silence unused
    # Eye
    arcade.draw_circle_filled(cx - s * 0.02, cy + s * 0.26, 1.5, _FLAME)
    # Wing bone ridges (team lighten)
    arcade.draw_line(cx - s * 0.05, cy + s * 0.05, cx - s * 0.38, cy + s * 0.3, _lighten(team, 0.3), 2)
    arcade.draw_line(cx + s * 0.05, cy + s * 0.05, cx + s * 0.38, cy + s * 0.3, _lighten(team, 0.3), 2)


def _draw_longship(cx: float, cy: float, s: float, team: tuple[int, int, int],
                    rock_deg: float = 0.0) -> None:
    """Viking-style longship with striped team-colored sail.

    `rock_deg` is provided for a future rocking transform; currently the wave
    animation comes from the per-frame vertical bob applied in draw_unit.
    """
    _ = rock_deg
    # Water ripples under hull
    arcade.draw_line(cx - s * 0.4, cy - s * 0.35, cx - s * 0.2, cy - s * 0.35, _ICE, 2)
    arcade.draw_line(cx + s * 0.15, cy - s * 0.33, cx + s * 0.4, cy - s * 0.33, _ICE, 2)
    # Hull (crescent shape)
    hull = [
        (cx - s * 0.4, cy - s * 0.2),
        (cx - s * 0.3, cy - s * 0.3),
        (cx + s * 0.3, cy - s * 0.3),
        (cx + s * 0.42, cy - s * 0.2),
        (cx + s * 0.38, cy - s * 0.1),
        (cx - s * 0.36, cy - s * 0.1),
    ]
    arcade.draw_polygon_filled(hull, _WOOD)
    arcade.draw_polygon_outline(hull, _darken(_WOOD, 0.5), 2)
    # Dragon prow
    arcade.draw_polygon_filled(
        [(cx - s * 0.4, cy - s * 0.2),
         (cx - s * 0.48, cy - s * 0.02),
         (cx - s * 0.35, cy - s * 0.05)],
        _darken(_WOOD, 0.4),
    )
    arcade.draw_circle_filled(cx - s * 0.44, cy - s * 0.06, 1.5, _FLAME)
    # Mast
    mast_x = cx - s * 0.02
    arcade.draw_line(mast_x, cy - s * 0.1, mast_x, cy + s * 0.38, _darken(_WOOD, 0.3), 2)
    # Sail
    sail_left = mast_x - s * 0.22
    sail_right = mast_x + s * 0.22
    sail_top = cy + s * 0.36
    sail_bot = cy + s * 0.02
    arcade.draw_polygon_filled(
        [(sail_left, sail_bot), (sail_right, sail_bot),
         (sail_right, sail_top), (sail_left, sail_top)],
        _lighten(team, 0.2),
    )
    # Sail vertical stripes
    for fr in (0.25, 0.5, 0.75):
        x = sail_left + (sail_right - sail_left) * fr
        arcade.draw_line(x, sail_bot, x, sail_top, team, 2)
    # Sail outline
    arcade.draw_polygon_outline(
        [(sail_left, sail_bot), (sail_right, sail_bot),
         (sail_right, sail_top), (sail_left, sail_top)],
        _darken(team, 0.6), 1,
    )
    # Shield row on hull (alternating team color / steel)
    for i in range(5):
        px = cx - s * 0.3 + i * (s * 0.12)
        color = team if i % 2 == 0 else _STEEL
        arcade.draw_circle_filled(px, cy - s * 0.2, s * 0.045, color)
        arcade.draw_circle_outline(px, cy - s * 0.2, s * 0.045, _DARK_STEEL, 1)


def _draw_emberlord(cx: float, cy: float, s: float, team: tuple[int, int, int],
                    dimmed: bool, anim_time: float = 0.0, phase: float = 0.0) -> None:
    """Emberlord: cloaked figure with a flame crown and a burning sword."""
    # Cloak (wide triangle with team color, darker)
    cloak_color = _darken(team, 0.75)
    cloak = [
        (cx - s * 0.3, cy - s * 0.4),
        (cx + s * 0.3, cy - s * 0.4),
        (cx + s * 0.24, cy + s * 0.1),
        (cx - s * 0.24, cy + s * 0.1),
    ]
    arcade.draw_polygon_filled(cloak, cloak_color)
    arcade.draw_polygon_outline(cloak, _darken(team, 0.4), 2)
    # Tabard / breastplate
    arcade.draw_polygon_filled(
        [(cx - s * 0.12, cy - s * 0.35),
         (cx + s * 0.12, cy - s * 0.35),
         (cx + s * 0.14, cy + s * 0.1),
         (cx - s * 0.14, cy + s * 0.1)],
        team,
    )
    # Gold belt
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.14, cy - s * 0.1, s * 0.28, 3, _GOLD)
    # Head
    head_y = cy + s * 0.22
    arcade.draw_circle_filled(cx, head_y, s * 0.12, (230, 200, 170))
    arcade.draw_circle_outline(cx, head_y, s * 0.12, _DARK_STEEL, 1)
    # Eyes (glowing red)
    arcade.draw_circle_filled(cx - s * 0.04, head_y, 1.2, _FLAME)
    arcade.draw_circle_filled(cx + s * 0.04, head_y, 1.2, _FLAME)
    # Flame crown: three flame tongues. Each flickers with an independent offset.
    for i, (dx, ht) in enumerate(((-s * 0.08, 0.12), (0, 0.18), (s * 0.08, 0.12))):
        flicker = 1.0 + 0.15 * math.sin(anim_time * 8.0 + phase + i * 1.3) if not dimmed else 1.0
        base_y = head_y + s * 0.1
        tip_y = base_y + s * ht * flicker
        arcade.draw_polygon_filled(
            [(cx + dx - 2, base_y), (cx + dx + 2, base_y), (cx + dx, tip_y)],
            _FLAME,
        )
        arcade.draw_polygon_filled(
            [(cx + dx - 1, base_y + 1), (cx + dx + 1, base_y + 1), (cx + dx, tip_y - 2)],
            (255, 220, 100),
        )
    # Burning sword (right side)
    hilt = (cx + s * 0.16, cy - s * 0.02)
    tip = (cx + s * 0.42, cy + s * 0.34)
    arcade.draw_line(*hilt, *tip, _STEEL, 3)
    # Fire trail along blade
    for fr in (0.3, 0.55, 0.8):
        bx = hilt[0] + (tip[0] - hilt[0]) * fr
        by = hilt[1] + (tip[1] - hilt[1]) * fr
        arcade.draw_circle_filled(bx, by, 3 if not dimmed else 2, _FLAME)
    # Guard
    arcade.draw_line(hilt[0] - 4, hilt[1] - 4, hilt[0] + 4, hilt[1] + 4, _GOLD, 2)


def _draw_frostqueen(cx: float, cy: float, s: float, team: tuple[int, int, int],
                     dimmed: bool, anim_time: float = 0.0, phase: float = 0.0) -> None:
    """Frostqueen: regal figure with an ice tiara and a glowing staff."""
    # Cloak (flowing, team color)
    cloak_color = _darken(team, 0.7)
    cloak = [
        (cx - s * 0.32, cy - s * 0.4),
        (cx + s * 0.32, cy - s * 0.4),
        (cx + s * 0.24, cy + s * 0.12),
        (cx - s * 0.24, cy + s * 0.12),
    ]
    arcade.draw_polygon_filled(cloak, cloak_color)
    arcade.draw_polygon_outline(cloak, _darken(team, 0.4), 2)
    # Gown (lighter team color, flared at hem)
    gown = [
        (cx - s * 0.14, cy - s * 0.38),
        (cx + s * 0.14, cy - s * 0.38),
        (cx + s * 0.16, cy + s * 0.1),
        (cx - s * 0.16, cy + s * 0.1),
    ]
    arcade.draw_polygon_filled(gown, _lighten(team, 0.25))
    # Silver sash
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.14, cy - s * 0.06, s * 0.28, 3, _STEEL)
    # Head
    head_y = cy + s * 0.24
    arcade.draw_circle_filled(cx, head_y, s * 0.11, (235, 215, 195))
    arcade.draw_circle_outline(cx, head_y, s * 0.11, _DARK_STEEL, 1)
    # Eyes (ice blue)
    arcade.draw_circle_filled(cx - s * 0.035, head_y, 1.3, _ICE)
    arcade.draw_circle_filled(cx + s * 0.035, head_y, 1.3, _ICE)
    # Hair — long, silver-white behind the head
    arcade.draw_polygon_filled(
        [(cx - s * 0.12, head_y + s * 0.02),
         (cx + s * 0.12, head_y + s * 0.02),
         (cx + s * 0.16, cy - s * 0.02),
         (cx - s * 0.16, cy - s * 0.02)],
        (220, 225, 240),
    )
    # Ice tiara: three spikes
    for dx, ht in ((-s * 0.07, 0.1), (0, 0.16), (s * 0.07, 0.1)):
        base_y = head_y + s * 0.09
        tip_y = base_y + s * ht
        arcade.draw_polygon_filled(
            [(cx + dx - 2, base_y), (cx + dx + 2, base_y), (cx + dx, tip_y)],
            _ICE,
        )
        arcade.draw_polygon_outline(
            [(cx + dx - 2, base_y), (cx + dx + 2, base_y), (cx + dx, tip_y)],
            (130, 160, 200), 1,
        )
    # Staff in left hand (long vertical line with glowing orb on top)
    staff_x = cx - s * 0.32
    staff_bot = (staff_x, cy - s * 0.3)
    staff_top = (staff_x, cy + s * 0.42)
    arcade.draw_line(*staff_bot, *staff_top, _darken(_STEEL, 0.7), 3)
    orb_r = 5 if not dimmed else 3
    arcade.draw_circle_filled(staff_top[0], staff_top[1], orb_r, _ICE)
    arcade.draw_circle_outline(staff_top[0], staff_top[1], orb_r, (130, 170, 210), 1)
    # Frost particles orbiting the orb (rotation tied to anim_time for a slow swirl)
    swirl = anim_time * 1.2 if not dimmed else 0.0
    for i, angle in enumerate((30, 90, 150, 210, 270, 330)):
        rad = math.radians(angle) + swirl + phase
        arcade.draw_circle_filled(
            staff_top[0] + math.cos(rad) * 8, staff_top[1] + math.sin(rad) * 8, 1, _ICE
        )
        _ = i


def _draw_generic_unit(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    arcade.draw_circle_filled(cx, cy, s * 0.35, team)
    arcade.draw_circle_outline(cx, cy, s * 0.35, _DARK_STEEL, 2)


# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------

def _draw_sword(cx: float, cy: float, length: float, angle_deg: float,
                color: tuple[int, int, int]) -> None:
    rad = math.radians(angle_deg)
    half = length / 2
    dx = math.cos(rad) * half
    dy = math.sin(rad) * half
    arcade.draw_line(cx - dx, cy - dy, cx + dx, cy + dy, color, 2)
    # Crossguard perpendicular
    perp_rad = rad + math.pi / 2
    pdx = math.cos(perp_rad) * 3
    pdy = math.sin(perp_rad) * 3
    # At the pommel end (near side) draw a crossguard
    arcade.draw_line(cx - dx - pdx, cy - dy - pdy, cx - dx + pdx, cy - dy + pdy, _GOLD, 2)
