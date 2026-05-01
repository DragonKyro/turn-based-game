"""Fight-scene overlay shown after a combat resolves.

Timeline (t in [0, 1] over `duration` seconds):
  0.00 – 0.25   approach: both sprites lunge toward the center
  0.25 – 0.45   attacker swing + flash + particle burst + defender HP bar depletes
  0.35 – 0.55   counter-attack (if any) swings back, particles, attacker HP bar depletes
  0.55 – 1.00   retreat / hold, damage numbers settle on screen

The game state was already mutated by apply_action; this is a replay for the player.
Screen shake kicks in on hit.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import arcade

from src.config import COLORS, TILE_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH
from src.core.combat import CombatResult
from src.engine import sprites


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]


@dataclass
class FightScene:
    attacker_kind: str
    attacker_faction: str
    attacker_owner: int
    attacker_hp_before: int
    attacker_hp_after: int
    attacker_hp_max: int
    defender_kind: str
    defender_faction: str
    defender_owner: int
    defender_hp_before: int
    defender_hp_after: int
    defender_hp_max: int
    result: CombatResult
    duration: float = 2.2
    elapsed: float = 0.0
    _particles: list[Particle] = field(default_factory=list)
    _atk_particles_spawned: bool = False
    _def_particles_spawned: bool = False

    # Cached Text objects — populated in __post_init__
    _title_text: arcade.Text | None = None
    _atk_label: arcade.Text | None = None
    _def_label: arcade.Text | None = None
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
        self._atk_label = arcade.Text(
            self.attacker_kind.capitalize(),
            cx - 180, cy - 130, COLORS["text"], font_size=14, anchor_x="center", bold=True,
        )
        self._def_label = arcade.Text(
            self.defender_kind.capitalize(),
            cx + 180, cy - 130, COLORS["text"], font_size=14, anchor_x="center", bold=True,
        )
        self._atk_dmg_text = arcade.Text(
            "", cx - 180, cy + 90, (230, 90, 90),
            font_size=28, anchor_x="center", bold=True,
        )
        self._def_dmg_text = arcade.Text(
            "", cx + 180, cy + 90, (230, 90, 90),
            font_size=28, anchor_x="center", bold=True,
        )
        self._break_text = arcade.Text(
            "", cx, cy - 170, COLORS["text_dim"], font_size=12, anchor_x="center",
        )

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration

    def tick(self, dt: float) -> None:
        self.elapsed += dt
        # Update particles
        alive: list[Particle] = []
        for p in self._particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy -= 120 * dt  # mild gravity on dust/spark
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self._particles = alive

    def _t(self) -> float:
        return self.elapsed / max(self.duration, 0.1)

    def _spawn_particles(self, cx: float, cy: float, n: int = 22) -> None:
        for _ in range(n):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 220)
            life = random.uniform(0.25, 0.55)
            color = random.choice([(255, 230, 90), (255, 150, 60), (240, 240, 240)])
            self._particles.append(Particle(
                x=cx, y=cy,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=life, color=color,
            ))

    def _screen_shake_offset(self) -> tuple[float, float]:
        """Small offset during impact windows so the panel wobbles."""
        t = self._t()
        if 0.26 < t < 0.36 or (self.result.counter and 0.42 < t < 0.52):
            mag = 6
            return (random.uniform(-mag, mag), random.uniform(-mag, mag))
        return (0.0, 0.0)

    def draw(self) -> None:
        cx = WINDOW_WIDTH / 2
        cy = WINDOW_HEIGHT / 2
        shake_x, shake_y = self._screen_shake_offset()
        t = self._t()

        # Dim backdrop (no shake — the battle is the foreground)
        arcade.draw_lbwh_rectangle_filled(
            0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, (0, 0, 0, 180)
        )

        panel_w, panel_h = 680, 320
        px = cx - panel_w / 2 + shake_x
        py = cy - panel_h / 2 + shake_y
        arcade.draw_lbwh_rectangle_filled(px, py, panel_w, panel_h, COLORS["ui_panel"])
        arcade.draw_lbwh_rectangle_outline(px, py, panel_w, panel_h, COLORS["hero_accent"], 3)

        self._title_text.draw()

        # Lunge: attacker from left, defender from right. Both retreat near the end.
        lunge = 0.0
        if t < 0.25:
            lunge = t / 0.25
        elif t > 0.75:
            lunge = max(0.0, 1.0 - (t - 0.75) / 0.25)
        else:
            lunge = 1.0
        approach = 50 * lunge

        scale = 1.9
        ax = cx - 180 + approach + shake_x * 0.3
        ay = cy + 15 + shake_y * 0.3
        dx = cx + 180 - approach + shake_x * 0.3
        dy = cy + 15 + shake_y * 0.3

        # Draw sprites
        _draw_staged(ax, ay, scale, self.attacker_kind,
                      self.attacker_faction, self.attacker_owner)
        _draw_staged(dx, dy, scale, self.defender_kind,
                      self.defender_faction, self.defender_owner)

        # Weapon swing: a yellow-white slash arc that crosses the defender on attack impact.
        if 0.25 <= t <= 0.45:
            local = (t - 0.25) / 0.2
            self._draw_slash(ax, ay, dx, dy, local, attacker_side=True)
            if not self._def_particles_spawned and local > 0.4:
                self._spawn_particles(dx, dy, n=28)
                self._def_particles_spawned = True

        # Counter swing (if any): defender slashes back.
        if self.result.counter and 0.42 <= t <= 0.60:
            local = (t - 0.42) / 0.18
            self._draw_slash(dx, dy, ax, ay, local, attacker_side=False)
            if not self._atk_particles_spawned and local > 0.4:
                self._spawn_particles(ax, ay, n=22)
                self._atk_particles_spawned = True

        # Particles on top of sprites
        for p in self._particles:
            arcade.draw_circle_filled(p.x, p.y, 2.2, p.color)

        # HP bars (large) beneath each combatant. Animates from pre → post over the damage window.
        self._draw_big_hp_bar(
            cx - 240, cy - 90, 160, 14,
            self.attacker_hp_before, self.attacker_hp_after, self.attacker_hp_max,
            window=(0.42, 0.55) if self.result.counter else (0.0, 0.0),
            t=t,
        )
        self._draw_big_hp_bar(
            cx + 80, cy - 90, 160, 14,
            self.defender_hp_before, self.defender_hp_after, self.defender_hp_max,
            window=(0.28, 0.42),
            t=t,
        )
        self._atk_label.draw()
        self._def_label.draw()

        # Floating damage numbers
        atk_final = self.result.attack.final
        ctr_final = self.result.counter.final if self.result.counter else None
        if t > 0.3:
            # Rise + fade
            rise = (t - 0.3) * 30
            self._def_dmg_text.text = f"-{atk_final}"
            self._def_dmg_text.x = cx + 180 + shake_x * 0.3
            self._def_dmg_text.y = cy + 90 + rise
            self._def_dmg_text.draw()
            if ctr_final:
                if t > 0.45:
                    self._atk_dmg_text.text = f"-{ctr_final}"
                    self._atk_dmg_text.x = cx - 180 + shake_x * 0.3
                    self._atk_dmg_text.y = cy + 90 + (t - 0.45) * 30
                    self._atk_dmg_text.draw()

        # Breakdown line at the bottom of the panel
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

    # --- helpers ---

    def _draw_slash(self, fx: float, fy: float, tx: float, ty: float,
                    local_t: float, attacker_side: bool) -> None:
        """Draw a sweeping slash arc between the attacker and defender during `local_t` in [0, 1]."""
        # Sweep angle: -60° → +60° from the midline.
        angle = math.radians(-60 + 120 * local_t)
        midx = (fx + tx) / 2
        midy = (fy + ty) / 2
        length = TILE_SIZE * 1.2
        # Direction from attacker to defender
        dxn = tx - fx
        dyn = ty - fy
        norm = max(math.hypot(dxn, dyn), 1e-6)
        ux = dxn / norm
        uy = dyn / norm
        # Rotate (ux, uy) by `angle` to get the slash direction
        sx = ux * math.cos(angle) - uy * math.sin(angle)
        sy = ux * math.sin(angle) + uy * math.cos(angle)
        alpha = int(255 * (1.0 - abs(local_t - 0.5) * 2))
        alpha = max(60, min(alpha, 255))
        color_core = (255, 240, 180, alpha)
        color_edge = (255, 160, 40, alpha)
        # Draw a thick + thin slash for a nicer gleam
        arcade.draw_line(midx - sx * length / 2, midy - sy * length / 2,
                          midx + sx * length / 2, midy + sy * length / 2, color_edge, 6)
        arcade.draw_line(midx - sx * length / 2, midy - sy * length / 2,
                          midx + sx * length / 2, midy + sy * length / 2, color_core, 2)
        _ = attacker_side

    def _draw_big_hp_bar(self, left: float, bottom: float, w: float, h: float,
                         hp_before: int, hp_after: int, hp_max: int,
                         window: tuple[float, float], t: float) -> None:
        # Background
        arcade.draw_lbwh_rectangle_filled(left, bottom, w, h, (20, 20, 28))
        arcade.draw_lbwh_rectangle_outline(left, bottom, w, h, (80, 80, 90), 1)
        # Interpolate displayed HP across the damage window
        w_start, w_end = window
        if t <= w_start:
            displayed = hp_before
        elif t >= w_end or w_end <= w_start:
            displayed = hp_after
        else:
            k = (t - w_start) / (w_end - w_start)
            displayed = hp_before + (hp_after - hp_before) * k
        ratio = max(0.0, displayed / max(hp_max, 1))
        if ratio > 0.66:
            fill = (120, 210, 95)
        elif ratio > 0.33:
            fill = (230, 200, 70)
        else:
            fill = (220, 80, 70)
        arcade.draw_lbwh_rectangle_filled(left + 1, bottom + 1,
                                           (w - 2) * ratio, h - 2, fill)


def _draw_staged(cx: float, cy: float, scale: float, kind: str,
                 faction: str, owner_id: int) -> None:
    """Draw a unit-like sprite at the given position with a manual size override."""
    team = sprites._team_color(owner_id, faction)  # type: ignore[attr-defined]
    size = TILE_SIZE * scale
    if kind == "infantry":
        sprites._draw_infantry(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "archer":
        sprites._draw_archer(cx, cy, size, team, faction=faction, anim_time=0.0, phase=0.0)  # type: ignore[attr-defined]
    elif kind == "spearman":
        sprites._draw_spearman(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "knight":
        sprites._draw_knight(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "scout":
        sprites._draw_scout(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "ballista":
        sprites._draw_ballista(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "wyvern":
        sprites._draw_wyvern(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "griffon":
        sprites._draw_griffon(cx, cy, size, team, wing_scale=1.0, faction=faction)  # type: ignore[attr-defined]
    elif kind == "longship":
        sprites._draw_longship(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "warship":
        sprites._draw_warship(cx, cy, size, team, faction=faction)  # type: ignore[attr-defined]
    elif kind == "emberlord":
        sprites._draw_emberlord(cx, cy, size, team, dimmed=False)  # type: ignore[attr-defined]
    elif kind == "frostqueen":
        sprites._draw_frostqueen(cx, cy, size, team, dimmed=False)  # type: ignore[attr-defined]
    else:
        sprites._draw_generic_unit(cx, cy, size, team)  # type: ignore[attr-defined]
