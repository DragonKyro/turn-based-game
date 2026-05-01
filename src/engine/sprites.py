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
from src.core.factions import get_faction
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


def _team_color(owner_id: int | None, faction_key: str | None = None) -> tuple[int, int, int]:
    """Primary color for the owner. If a faction is provided its palette wins; otherwise
    fall back to a stable per-owner-id color."""
    if faction_key:
        return get_faction(faction_key).primary
    if owner_id == 1:
        return COLORS["player1"]
    if owner_id == 2:
        return COLORS["player2"]
    return (140, 140, 150)


def _team_accent(faction_key: str | None) -> tuple[int, int, int]:
    if faction_key:
        return get_faction(faction_key).accent
    return _GOLD


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

def draw_building(b: Building, cx: float, cy: float, faction_key: str | None = None) -> None:
    color = _team_color(b.owner_id, faction_key)
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
    """Mine: a mountain with an entry arch and a pickaxe sign. Owner-agnostic visual.

    The two-peak silhouette is rendered as two overlapping convex triangles rather than a
    single non-convex polygon — arcade's triangle-fan fill misdraws concave shapes.
    """
    half = s / 2
    dark = _darken(_STONE, 0.55)
    base_y = cy - half + 3
    # Left peak (triangle): spans from left base to center, apex up-left
    left_peak = [
        (cx - s * 0.45, base_y),
        (cx + s * 0.05, base_y),
        (cx - s * 0.2,  cy + half - s * 0.1),
    ]
    # Right peak (triangle): spans from center to right base, apex up-right (taller)
    right_peak = [
        (cx - s * 0.05, base_y),
        (cx + s * 0.45, base_y),
        (cx + s * 0.15, cy + half - s * 0.05),
    ]
    arcade.draw_polygon_filled(left_peak, _STONE)
    arcade.draw_polygon_outline(left_peak, dark, 1)
    arcade.draw_polygon_filled(right_peak, _STONE)
    arcade.draw_polygon_outline(right_peak, dark, 1)
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

def draw_unit(u: Unit, cx: float, cy: float, dimmed: bool,
              anim_time: float = 0.0, faction: str = "emberdyne") -> None:
    """Draw a unit. `faction` is a key from src.core.factions; its palette + emblem motif
    are used for banner color and emblem decoration so same-kind units on different factions
    still read as distinct."""
    team = _team_color(u.owner_id, faction)
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
        _draw_infantry(cx, cy + dy, size, team, faction=faction)
    elif kind == "archer":
        _draw_archer(cx, cy + dy, size, team, faction=faction, anim_time=anim_time, phase=phase)
    elif kind == "spearman":
        _draw_spearman(cx, cy + dy, size, team, faction=faction)
    elif kind == "knight":
        _draw_knight(cx, cy + dy, size, team, faction=faction)
    elif kind == "scout":
        _draw_scout(cx, cy + dy, size, team, faction=faction)
    elif kind == "ballista":
        _draw_ballista(cx, cy + dy, size, team, faction=faction)
    elif kind == "wyvern":
        _draw_wyvern(cx, cy + dy, size, team, wing_scale=wing_scale, faction=faction)
    elif kind == "griffon":
        _draw_griffon(cx, cy + dy, size, team, wing_scale=wing_scale, faction=faction)
    elif kind == "longship":
        _draw_longship(cx, cy + dy, size, team, rock_deg=rock_deg, faction=faction)
    elif kind == "warship":
        _draw_warship(cx, cy + dy, size, team, faction=faction)
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


def _draw_infantry(cx: float, cy: float, s: float, team: tuple[int, int, int],
                   faction: str = "Emberdyne") -> None:
    """A soldier: rounded helmet + visor + breastplate + shield + spear.

    Faction affects the emblem on the shield (flame = Emberdyne, snowflake = Frostmoor)."""
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
    # Shield on left arm (faction emblem in the center)
    sx = cx - s * 0.3
    arcade.draw_ellipse_filled(sx, cy + s * 0.04, s * 0.14, s * 0.22, _darken(team, 0.6))
    arcade.draw_ellipse_outline(sx, cy + s * 0.04, s * 0.14, s * 0.22, _DARK_STEEL, 1)
    _draw_faction_emblem(sx, cy + s * 0.04, s * 0.12, faction)
    # Spear (right side, diagonal)
    spear_bottom = (cx + s * 0.28, cy - s * 0.32)
    spear_top = (cx + s * 0.42, cy + s * 0.4)
    arcade.draw_line(*spear_bottom, *spear_top, _WOOD, 2)
    # Spearhead
    arcade.draw_polygon_filled(
        [spear_top, (spear_top[0] - 2, spear_top[1] - 6), (spear_top[0] + 4, spear_top[1] - 3)],
        _STEEL,
    )


def _draw_knight(cx: float, cy: float, s: float, team: tuple[int, int, int],
                 faction: str = "Emberdyne") -> None:
    """Mounted knight: horse silhouette beneath a lance-wielding rider.
    Faction adds a flame or snowflake accent above the lance pennant."""
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
    # Lance pennant (team) + faction emblem just above the lance tip
    arcade.draw_polygon_filled(
        [lance_start, (lance_start[0] + s * 0.12, lance_start[1] + 4),
         (lance_start[0] + s * 0.12, lance_start[1] - 4)],
        team,
    )
    _draw_faction_emblem(lance_tip[0] + 4, lance_tip[1] + 4, s * 0.08, faction)


def _draw_wyvern(cx: float, cy: float, s: float, team: tuple[int, int, int],
                 wing_scale: float = 1.0, faction: str = "Emberdyne") -> None:
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
    # Eye (flame glow for Emberdyne, ice glow for Frostmoor)
    eye_color = _ICE if faction == "Frostmoor" else _FLAME
    arcade.draw_circle_filled(cx - s * 0.02, cy + s * 0.26, 1.8, eye_color)
    # Wing bone ridges (team lighten)
    arcade.draw_line(cx - s * 0.05, cy + s * 0.05, cx - s * 0.38, cy + s * 0.3, _lighten(team, 0.3), 2)
    arcade.draw_line(cx + s * 0.05, cy + s * 0.05, cx + s * 0.38, cy + s * 0.3, _lighten(team, 0.3), 2)


def _draw_longship(cx: float, cy: float, s: float, team: tuple[int, int, int],
                    rock_deg: float = 0.0, faction: str = "Emberdyne") -> None:
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
    # Faction emblem centered on the sail
    _draw_faction_emblem((sail_left + sail_right) / 2,
                         (sail_top + sail_bot) / 2,
                         s * 0.16, faction)
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


def _draw_archer(cx: float, cy: float, s: float, team: tuple[int, int, int],
                 faction: str, anim_time: float, phase: float) -> None:
    """Archer: hooded figure with a drawn bow. Bow string twitches slightly."""
    # Tabard
    arcade.draw_polygon_filled(
        [(cx - s * 0.16, cy - s * 0.32),
         (cx + s * 0.16, cy - s * 0.32),
         (cx + s * 0.18, cy + s * 0.02),
         (cx - s * 0.18, cy + s * 0.02)],
        team,
    )
    # Hood (pointed triangle over the head)
    head_y = cy + s * 0.22
    arcade.draw_polygon_filled(
        [(cx - s * 0.13, head_y - s * 0.02),
         (cx + s * 0.13, head_y - s * 0.02),
         (cx + s * 0.07, head_y + s * 0.2),
         (cx - s * 0.07, head_y + s * 0.2)],
        _darken(team, 0.6),
    )
    # Face strip peeking from the hood
    arcade.draw_lbwh_rectangle_filled(
        cx - s * 0.06, head_y - s * 0.02, s * 0.12, s * 0.06, (230, 200, 170)
    )
    # Bow (curved via 3 line segments) and twitching string
    bow_x = cx - s * 0.28
    arcade.draw_line(bow_x, cy + s * 0.22, bow_x + s * 0.04, cy + s * 0.05, _WOOD, 2)
    arcade.draw_line(bow_x + s * 0.04, cy + s * 0.05, bow_x + s * 0.04, cy - s * 0.05, _WOOD, 2)
    arcade.draw_line(bow_x + s * 0.04, cy - s * 0.05, bow_x, cy - s * 0.22, _WOOD, 2)
    string_offset = 2 * math.sin(anim_time * 10 + phase)
    arcade.draw_line(bow_x, cy + s * 0.22,
                     bow_x + s * 0.14 + string_offset, cy + s * 0.0,
                     _STEEL, 1)
    arcade.draw_line(bow_x + s * 0.14 + string_offset, cy + s * 0.0,
                     bow_x, cy - s * 0.22, _STEEL, 1)
    # Arrow on the string (shaft + triangular head — 3-point triangle, proper winding)
    arcade.draw_line(bow_x + s * 0.14 + string_offset, cy,
                     cx + s * 0.2, cy, _darken(_WOOD, 0.5), 2)
    arcade.draw_polygon_filled(
        [(cx + s * 0.3, cy), (cx + s * 0.2, cy + 3), (cx + s * 0.2, cy - 3)],
        _STEEL,
    )
    # Faction emblem on the tabard belt
    _draw_faction_emblem(cx, cy - s * 0.14, s * 0.1, faction)


def _draw_spearman(cx: float, cy: float, s: float, team: tuple[int, int, int],
                   faction: str) -> None:
    """Spearman: kite shield, straight spear, polished helm."""
    # Body / tabard
    arcade.draw_polygon_filled(
        [(cx - s * 0.18, cy - s * 0.32),
         (cx + s * 0.18, cy - s * 0.32),
         (cx + s * 0.22, cy + s * 0.02),
         (cx - s * 0.22, cy + s * 0.02)],
        team,
    )
    # Breastplate
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.14, cy, s * 0.28, s * 0.2, _STEEL)
    arcade.draw_lbwh_rectangle_outline(cx - s * 0.14, cy, s * 0.28, s * 0.2, _DARK_STEEL, 1)
    # Kite shield (left)
    sx = cx - s * 0.3
    shield_points = [
        (sx, cy + s * 0.24),
        (sx + s * 0.1, cy + s * 0.08),
        (sx + s * 0.1, cy - s * 0.18),
        (sx, cy - s * 0.28),
        (sx - s * 0.1, cy - s * 0.18),
        (sx - s * 0.1, cy + s * 0.08),
    ]
    arcade.draw_polygon_filled(shield_points, _darken(team, 0.6))
    arcade.draw_polygon_outline(shield_points, _DARK_STEEL, 1)
    _draw_faction_emblem(sx, cy - s * 0.06, s * 0.14, faction)
    # Helm (round + cheek plates)
    head_y = cy + s * 0.28
    arcade.draw_circle_filled(cx + s * 0.03, head_y, s * 0.12, _STEEL)
    arcade.draw_arc_filled(cx + s * 0.03, head_y, s * 0.22, s * 0.2, _DARK_STEEL, 180, 360)
    # Spear (vertical, long)
    arcade.draw_line(cx + s * 0.26, cy - s * 0.34, cx + s * 0.26, cy + s * 0.45, _WOOD, 2)
    arcade.draw_polygon_filled(
        [(cx + s * 0.26, cy + s * 0.45), (cx + s * 0.22, cy + s * 0.38),
         (cx + s * 0.3, cy + s * 0.38)], _STEEL,
    )


def _draw_scout(cx: float, cy: float, s: float, team: tuple[int, int, int],
                faction: str) -> None:
    """Scout: light rider on a tan horse, carrying a small pennant."""
    horse = _darken((180, 140, 100), 1.0)
    # Horse body (stretched, lower profile than knight's)
    arcade.draw_ellipse_filled(cx, cy - s * 0.18, s * 0.4, s * 0.12, horse)
    for dx in (-s * 0.24, -s * 0.1, s * 0.08, s * 0.22):
        arcade.draw_line(cx + dx, cy - s * 0.26, cx + dx, cy - s * 0.38, _darken(horse, 0.7), 2)
    # Horse neck + head
    arcade.draw_line(cx + s * 0.25, cy - s * 0.14, cx + s * 0.36, cy + s * 0.02, horse, 5)
    arcade.draw_ellipse_filled(cx + s * 0.38, cy + s * 0.04, s * 0.07, s * 0.05, horse)
    # Rider (hooded)
    arcade.draw_polygon_filled(
        [(cx - s * 0.12, cy - s * 0.04),
         (cx + s * 0.12, cy - s * 0.04),
         (cx + s * 0.14, cy + s * 0.2),
         (cx - s * 0.14, cy + s * 0.2)],
        team,
    )
    arcade.draw_polygon_filled(
        [(cx - s * 0.1, cy + s * 0.18),
         (cx + s * 0.1, cy + s * 0.18),
         (cx, cy + s * 0.36)],
        _darken(team, 0.55),
    )
    # Small pennant-topped lance behind rider
    arcade.draw_line(cx - s * 0.1, cy + s * 0.2, cx - s * 0.18, cy + s * 0.46, _WOOD, 2)
    arcade.draw_polygon_filled(
        [(cx - s * 0.18, cy + s * 0.46), (cx - s * 0.3, cy + s * 0.42),
         (cx - s * 0.18, cy + s * 0.38)], team,
    )
    _draw_faction_emblem(cx - s * 0.22, cy + s * 0.42, s * 0.08, faction)


def _draw_ballista(cx: float, cy: float, s: float, team: tuple[int, int, int],
                   faction: str) -> None:
    """Ballista: wheeled wooden siege weapon with a horizontal bow and loaded bolt."""
    # Wheeled carriage base
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.32, cy - s * 0.3, s * 0.64, s * 0.14, _WOOD)
    arcade.draw_lbwh_rectangle_outline(cx - s * 0.32, cy - s * 0.3, s * 0.64, s * 0.14,
                                        _darken(_WOOD, 0.5), 1)
    # Wheels
    arcade.draw_circle_filled(cx - s * 0.22, cy - s * 0.34, s * 0.08, _darken(_WOOD, 0.6))
    arcade.draw_circle_outline(cx - s * 0.22, cy - s * 0.34, s * 0.08, _DARK_STEEL, 1)
    arcade.draw_circle_filled(cx + s * 0.22, cy - s * 0.34, s * 0.08, _darken(_WOOD, 0.6))
    arcade.draw_circle_outline(cx + s * 0.22, cy - s * 0.34, s * 0.08, _DARK_STEEL, 1)
    # Frame posts
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.04, cy - s * 0.16, s * 0.08, s * 0.3, _WOOD)
    # Horizontal bow arms
    arcade.draw_line(cx - s * 0.3, cy + s * 0.04, cx - s * 0.04, cy + s * 0.16, _DARK_STEEL, 3)
    arcade.draw_line(cx + s * 0.04, cy + s * 0.16, cx + s * 0.3, cy + s * 0.04, _DARK_STEEL, 3)
    # Bowstring
    arcade.draw_line(cx - s * 0.3, cy + s * 0.04, cx + s * 0.3, cy + s * 0.04, _STEEL, 1)
    # Bolt loaded
    arcade.draw_line(cx, cy + s * 0.04, cx, cy + s * 0.38, _WOOD, 3)
    arcade.draw_polygon_filled(
        [(cx, cy + s * 0.38), (cx - 3, cy + s * 0.32), (cx + 3, cy + s * 0.32)], _STEEL,
    )
    # Team banner on the frame
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.03, cy - s * 0.02, s * 0.06, s * 0.14, team)
    _draw_faction_emblem(cx, cy + s * 0.04, s * 0.08, faction)


def _draw_griffon(cx: float, cy: float, s: float, team: tuple[int, int, int],
                  wing_scale: float, faction: str) -> None:
    """Griffon: feathered wings + lion-like body + eagle head."""
    # Wings (feathered — lighter than wyvern)
    wing_color = _lighten(team, 0.2)
    edge = _darken(team, 0.5)
    left_wing = [
        (cx - s * 0.05, cy + s * 0.06 * wing_scale),
        (cx - s * 0.34, cy + s * 0.26 * wing_scale),
        (cx - s * 0.42, cy + s * 0.12 * wing_scale),
        (cx - s * 0.38, cy - s * 0.02),
        (cx - s * 0.18, cy + s * 0.02),
    ]
    right_wing = [
        (cx + s * 0.05, cy + s * 0.06 * wing_scale),
        (cx + s * 0.34, cy + s * 0.26 * wing_scale),
        (cx + s * 0.42, cy + s * 0.12 * wing_scale),
        (cx + s * 0.38, cy - s * 0.02),
        (cx + s * 0.18, cy + s * 0.02),
    ]
    arcade.draw_polygon_filled(left_wing, wing_color)
    arcade.draw_polygon_outline(left_wing, edge, 1)
    arcade.draw_polygon_filled(right_wing, wing_color)
    arcade.draw_polygon_outline(right_wing, edge, 1)
    # Feather lines
    for base, tip in ((left_wing[0], left_wing[1]), (right_wing[0], right_wing[1])):
        arcade.draw_line(base[0], base[1], tip[0], tip[1], _lighten(team, 0.4), 1)
    # Body (tawny)
    body_color = (210, 180, 130)
    arcade.draw_ellipse_filled(cx, cy - s * 0.06, s * 0.13, s * 0.24, body_color)
    arcade.draw_ellipse_outline(cx, cy - s * 0.06, s * 0.13, s * 0.24, _DARK_STEEL, 1)
    # Eagle head with beak
    head_y = cy + s * 0.22
    arcade.draw_circle_filled(cx, head_y, s * 0.1, _lighten(body_color, 0.2))
    arcade.draw_circle_outline(cx, head_y, s * 0.1, _DARK_STEEL, 1)
    arcade.draw_polygon_filled(
        [(cx + s * 0.04, head_y), (cx + s * 0.14, head_y - s * 0.02),
         (cx + s * 0.04, head_y - s * 0.04)], (230, 180, 60),
    )
    # Eye
    arcade.draw_circle_filled(cx - s * 0.02, head_y + s * 0.02, 1.3, (40, 40, 40))
    # Tail tuft
    arcade.draw_line(cx, cy - s * 0.3, cx + s * 0.08, cy - s * 0.42, body_color, 3)
    # Small team-tinted collar
    arcade.draw_lbwh_rectangle_filled(cx - s * 0.08, cy + s * 0.08, s * 0.16, 3, team)
    _draw_faction_emblem(cx, cy - s * 0.12, s * 0.1, faction)


def _draw_warship(cx: float, cy: float, s: float, team: tuple[int, int, int],
                  faction: str) -> None:
    """Warship: bigger boat with a cannon-bearing deck and two tall masts."""
    # Water shimmer
    arcade.draw_line(cx - s * 0.4, cy - s * 0.36, cx + s * 0.4, cy - s * 0.36, _ICE, 1)
    # Hull (wider than longship)
    hull = [
        (cx - s * 0.44, cy - s * 0.18),
        (cx - s * 0.32, cy - s * 0.32),
        (cx + s * 0.32, cy - s * 0.32),
        (cx + s * 0.46, cy - s * 0.18),
        (cx + s * 0.42, cy - s * 0.08),
        (cx - s * 0.4, cy - s * 0.08),
    ]
    arcade.draw_polygon_filled(hull, _darken(_WOOD, 0.85))
    arcade.draw_polygon_outline(hull, _darken(_WOOD, 0.5), 2)
    # Cannon ports (dark square dots along the side)
    for dx in (-s * 0.22, -s * 0.08, s * 0.06, s * 0.2):
        arcade.draw_lbwh_rectangle_filled(cx + dx - 2, cy - s * 0.22, 4, 4, _SHADOW)
    # Two masts
    for mast_x in (cx - s * 0.14, cx + s * 0.14):
        arcade.draw_line(mast_x, cy - s * 0.08, mast_x, cy + s * 0.42, _darken(_WOOD, 0.3), 2)
    # Sails
    for mast_x in (cx - s * 0.14, cx + s * 0.14):
        sail_left = mast_x - s * 0.12
        sail_right = mast_x + s * 0.12
        sail_top = cy + s * 0.4
        sail_bot = cy + s * 0.04
        arcade.draw_polygon_filled(
            [(sail_left, sail_bot), (sail_right, sail_bot),
             (sail_right, sail_top), (sail_left, sail_top)],
            _lighten(team, 0.25),
        )
        arcade.draw_polygon_outline(
            [(sail_left, sail_bot), (sail_right, sail_bot),
             (sail_right, sail_top), (sail_left, sail_top)],
            _darken(team, 0.6), 1,
        )
    # Faction emblem centered between the sails
    _draw_faction_emblem(cx, cy + s * 0.22, s * 0.14, faction)


def _draw_generic_unit(cx: float, cy: float, s: float, team: tuple[int, int, int]) -> None:
    arcade.draw_circle_filled(cx, cy, s * 0.35, team)
    arcade.draw_circle_outline(cx, cy, s * 0.35, _DARK_STEEL, 2)


# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------

def _draw_faction_emblem(cx: float, cy: float, size: float, faction_key: str) -> None:
    """Dispatch to the right emblem drawer based on the faction's `emblem` field."""
    f = get_faction(faction_key)
    emblem = f.emblem
    color = f.accent
    if emblem == "flame":
        _draw_flame(cx, cy, size, _FLAME)
    elif emblem == "snowflake":
        _draw_snowflake(cx, cy, size, _ICE)
    elif emblem == "leaf":
        _draw_leaf(cx, cy, size, color)
    elif emblem == "lightning":
        _draw_lightning(cx, cy, size, color)
    elif emblem == "wave":
        _draw_wave(cx, cy, size, color)
    elif emblem == "sun":
        _draw_sun(cx, cy, size, color)
    elif emblem == "moon":
        _draw_moon(cx, cy, size, color)
    elif emblem == "gear":
        _draw_gear(cx, cy, size, color)
    else:
        arcade.draw_circle_filled(cx, cy, max(2, size * 0.35), _GOLD)


def _draw_flame(cx: float, cy: float, size: float,
                color: tuple[int, int, int]) -> None:
    """Upward-pointing flame teardrop with a hotter core."""
    tip_y = cy + size * 0.55
    base_y = cy - size * 0.35
    half_w = size * 0.32
    arcade.draw_polygon_filled(
        [(cx - half_w, base_y), (cx + half_w, base_y), (cx, tip_y)],
        color,
    )
    arcade.draw_polygon_filled(
        [(cx - half_w * 0.5, base_y + 1), (cx + half_w * 0.5, base_y + 1),
         (cx, cy + size * 0.38)],
        (255, 220, 100),
    )


def _draw_snowflake(cx: float, cy: float, size: float,
                    color: tuple[int, int, int]) -> None:
    """Six-armed snowflake (three crossed lines) with a small core dot."""
    r = size * 0.45
    for angle_deg in (0, 60, 120):
        rad = math.radians(angle_deg)
        dx = math.cos(rad) * r
        dy = math.sin(rad) * r
        arcade.draw_line(cx - dx, cy - dy, cx + dx, cy + dy, color, 2)
    arcade.draw_circle_filled(cx, cy, max(1.5, size * 0.12), _lighten(color, 0.4))


def _draw_leaf(cx: float, cy: float, size: float,
               color: tuple[int, int, int]) -> None:
    """Pointed-oval leaf with a central vein."""
    arcade.draw_ellipse_filled(cx, cy, size * 0.32, size * 0.55, color)
    arcade.draw_ellipse_outline(cx, cy, size * 0.32, size * 0.55, _darken(color, 0.5), 1)
    arcade.draw_line(cx, cy - size * 0.45, cx, cy + size * 0.45, _darken(color, 0.5), 1)


def _draw_lightning(cx: float, cy: float, size: float,
                     color: tuple[int, int, int]) -> None:
    """Zigzag lightning bolt as thick line segments (polygon fill misbehaves on a
    self-intersecting lightning shape)."""
    pts = [
        (cx - size * 0.2, cy + size * 0.45),
        (cx + size * 0.05, cy + size * 0.1),
        (cx - size * 0.05, cy - size * 0.02),
        (cx + size * 0.2, cy - size * 0.45),
    ]
    for i in range(len(pts) - 1):
        arcade.draw_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], color, 3)
    # Small core highlight
    arcade.draw_line(pts[1][0], pts[1][1], pts[2][0], pts[2][1],
                     _lighten(color, 0.3), 1)


def _draw_wave(cx: float, cy: float, size: float,
                color: tuple[int, int, int]) -> None:
    """Three stacked curved wavelets."""
    for i, dy in enumerate((-size * 0.2, 0.0, size * 0.2)):
        prev = (cx - size * 0.4, cy + dy)
        for k in range(1, 9):
            x = cx - size * 0.4 + k * (size * 0.1)
            y = cy + dy + math.sin(k * 0.9 + i) * size * 0.06
            arcade.draw_line(prev[0], prev[1], x, y, color, 2)
            prev = (x, y)


def _draw_sun(cx: float, cy: float, size: float,
               color: tuple[int, int, int]) -> None:
    """Central disk with 8 rays."""
    r = size * 0.22
    arcade.draw_circle_filled(cx, cy, r, color)
    arcade.draw_circle_outline(cx, cy, r, _darken(color, 0.5), 1)
    for angle_deg in (0, 45, 90, 135, 180, 225, 270, 315):
        rad = math.radians(angle_deg)
        ix = math.cos(rad) * r * 1.3
        iy = math.sin(rad) * r * 1.3
        ox = math.cos(rad) * size * 0.45
        oy = math.sin(rad) * size * 0.45
        arcade.draw_line(cx + ix, cy + iy, cx + ox, cy + oy, color, 2)


def _draw_moon(cx: float, cy: float, size: float,
                color: tuple[int, int, int]) -> None:
    """Crescent: big disk minus a smaller overlapping disk in the background color."""
    r = size * 0.4
    arcade.draw_circle_filled(cx, cy, r, color)
    # Cut out a crescent with a disk in the panel/background color.
    arcade.draw_circle_filled(cx + size * 0.15, cy + size * 0.05, r * 0.85, COLORS["ui_panel"])


def _draw_gear(cx: float, cy: float, size: float,
                color: tuple[int, int, int]) -> None:
    """Gear: filled ring with 6 rectangular teeth."""
    outer = size * 0.42
    inner = size * 0.28
    arcade.draw_circle_filled(cx, cy, outer, color)
    # Background-colored core (hollow look)
    arcade.draw_circle_filled(cx, cy, inner * 0.55, COLORS["ui_panel"])
    for angle_deg in range(0, 360, 60):
        rad = math.radians(angle_deg)
        tx = cx + math.cos(rad) * outer
        ty = cy + math.sin(rad) * outer
        arcade.draw_circle_filled(tx, ty, size * 0.08, color)
    arcade.draw_circle_outline(cx, cy, outer, _darken(color, 0.5), 1)


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
