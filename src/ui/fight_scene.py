"""Fight-scene overlay shown briefly after a combat resolves.

Draws the two combatants facing each other with a clash effect, HP deltas, and the itemised
damage breakdown. Animated across a fixed duration (set in Options), then the view clears
itself. A skippable cinematic, not a blocking modal — the game state is already updated
when this appears.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import arcade

from src.config import COLORS, TILE_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH
from src.core.combat import CombatResult
from src.engine import sprites


@dataclass
class FightScene:
    """One-shot fight cinematic. Caller advances `elapsed` each tick and calls `draw`."""
    attacker_kind: str
    attacker_faction: str
    attacker_owner: int
    defender_kind: str
    defender_faction: str
    defender_owner: int
    result: CombatResult
    duration: float = 2.2
    elapsed: float = 0.0

    _title_text: arcade.Text | None = None
    _atk_hp_text: arcade.Text | None = None
    _def_hp_text: arcade.Text | None = None
    _atk_dmg_text: arcade.Text | None = None
    _def_dmg_text: arcade.Text | None = None
    _break_text: arcade.Text | None = None

    def __post_init__(self) -> None:
        cx = WINDOW_WIDTH / 2
        cy = WINDOW_HEIGHT / 2
        self._title_text = arcade.Text(
            "BATTLE", cx, cy + 150, COLORS["hero_accent"],
            font_size=28, anchor_x="center", bold=True,
        )
        self._atk_hp_text = arcade.Text(
            "", cx - 180, cy - 110, COLORS["text"], font_size=14, anchor_x="center",
        )
        self._def_hp_text = arcade.Text(
            "", cx + 180, cy - 110, COLORS["text"], font_size=14, anchor_x="center",
        )
        self._atk_dmg_text = arcade.Text(
            "", cx - 180, cy + 90, (230, 90, 90),
            font_size=20, anchor_x="center", bold=True,
        )
        self._def_dmg_text = arcade.Text(
            "", cx + 180, cy + 90, (230, 90, 90),
            font_size=20, anchor_x="center", bold=True,
        )
        self._break_text = arcade.Text(
            "", cx, cy - 150, COLORS["text_dim"], font_size=12, anchor_x="center",
        )

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration

    def tick(self, dt: float) -> None:
        self.elapsed += dt

    def draw(self) -> None:
        cx = WINDOW_WIDTH / 2
        cy = WINDOW_HEIGHT / 2

        # Dim backdrop
        arcade.draw_lbwh_rectangle_filled(
            0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, (0, 0, 0, 180)
        )
        # Central stage panel
        panel_w, panel_h = 640, 280
        arcade.draw_lbwh_rectangle_filled(
            cx - panel_w / 2, cy - panel_h / 2, panel_w, panel_h,
            COLORS["ui_panel"],
        )
        arcade.draw_lbwh_rectangle_outline(
            cx - panel_w / 2, cy - panel_h / 2, panel_w, panel_h,
            COLORS["hero_accent"], 3,
        )

        self._title_text.draw()

        # Figure out an "approach" offset so combatants lunge toward each other in the first
        # third of the cinematic, then retreat in the final third.
        t = self.elapsed / max(self.duration, 0.1)
        lunge = 0.0
        if t < 0.4:
            lunge = min(t / 0.4, 1.0)
        elif t > 0.7:
            lunge = max(0.0, 1.0 - (t - 0.7) / 0.3)
        else:
            lunge = 1.0
        approach = 40 * lunge

        # Attacker on the left, defender on the right (both roughly tile-sized).
        scale = 1.7  # bigger than on the map
        ax = cx - 180 + approach
        ay = cy + 10
        dx = cx + 180 - approach
        dy = cy + 10

        # Draw each as a giant sprite by leveraging the existing unit-draw helpers.
        _draw_staged(ax, ay, scale, self.attacker_kind, self.attacker_faction,
                      self.attacker_owner)
        _draw_staged(dx, dy, scale, self.defender_kind, self.defender_faction,
                      self.defender_owner)

        # Clash flash at the meeting point during the lunge peak
        if 0.35 < t < 0.6:
            flash = 0.5 + 0.5 * math.sin((t - 0.35) / 0.25 * math.pi)
            radius = 24 + 16 * flash
            arcade.draw_circle_filled(cx, cy + 10, radius, (255, 230, 100, int(180 * flash)))
            arcade.draw_circle_outline(cx, cy + 10, radius, (255, 200, 60), 2)

        # HP labels, damage floaties
        atk_final = self.result.attack.final
        ctr_final = self.result.counter.final if self.result.counter else None

        self._atk_hp_text.text = (
            f"{self.attacker_kind.capitalize()}"
            + (f"  -{ctr_final}" if ctr_final else "")
        )
        self._def_hp_text.text = f"{self.defender_kind.capitalize()}  -{atk_final}"
        self._atk_hp_text.draw()
        self._def_hp_text.draw()

        # Big floating damage numbers above each combatant — fade in during lunge, stay to end
        if t > 0.35:
            self._def_dmg_text.text = f"-{atk_final}"
            self._def_dmg_text.draw()
            if ctr_final:
                self._atk_dmg_text.text = f"-{ctr_final}"
                self._atk_dmg_text.draw()

        # Itemised breakdown below
        a = self.result.attack
        parts = [f"Base {a.base}"]
        if a.rps_bonus > 0:
            parts.append(f"RPS +{a.rps_bonus}")
        if a.crit_bonus > 0:
            parts.append(f"Crit +{a.crit_bonus}")
        if a.terrain_reduction > 0:
            parts.append(f"Cover -{a.terrain_reduction}")
        parts.append(f"= {atk_final}")
        self._break_text.text = "   ".join(parts)
        self._break_text.draw()


def _draw_staged(cx: float, cy: float, scale: float, kind: str,
                 faction: str, owner_id: int) -> None:
    """Draw a unit-like sprite at the given position with a manual scaling hack:
    overload sprites.draw_unit by temporarily swapping TILE_SIZE — not ideal but
    keeps a single source of truth for the sprite art.
    """
    # Rather than actually swap a global, we call the per-kind drawers directly
    # with an explicit size argument for crisp scaling.
    team = sprites._team_color(owner_id)  # type: ignore[attr-defined]
    size = TILE_SIZE * scale
    if kind == "infantry":
        sprites._draw_infantry(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "knight":
        sprites._draw_knight(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "wyvern":
        sprites._draw_wyvern(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "longship":
        sprites._draw_longship(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "emberlord":
        sprites._draw_emberlord(cx, cy, size, team, dimmed=False)  # type: ignore[attr-defined]
    elif kind == "frostqueen":
        sprites._draw_frostqueen(cx, cy, size, team, dimmed=False)  # type: ignore[attr-defined]
    else:
        sprites._draw_generic_unit(cx, cy, size, team)  # type: ignore[attr-defined]
