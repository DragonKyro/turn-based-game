"""Screen shown between the main menu and level load. Shows all 8 factions as
clickable panels; picking one overrides the player's faction before the level starts
and picks a distinct random opponent."""
from __future__ import annotations

import math
import random

import arcade

from src.config import COLORS, WINDOW_HEIGHT, WINDOW_WIDTH
from src.core.factions import FACTION_REGISTRY, Faction
from src.engine import sprites


_PANEL_W = 220
_PANEL_H = 180
_PANEL_GAP = 18
_COLS = 4


class FactionSelectView(arcade.View):
    def __init__(self, level_name: str) -> None:
        super().__init__()
        self.level_name = level_name
        self.factions: list[Faction] = list(FACTION_REGISTRY.values())
        # Layout centered
        total_w = _COLS * _PANEL_W + (_COLS - 1) * _PANEL_GAP
        top = WINDOW_HEIGHT - 120
        left0 = (WINDOW_WIDTH - total_w) // 2
        self._rects: list[tuple[Faction, float, float, float, float]] = []
        for i, f in enumerate(self.factions):
            col = i % _COLS
            row = i // _COLS
            x = left0 + col * (_PANEL_W + _PANEL_GAP)
            y = top - _PANEL_H - row * (_PANEL_H + _PANEL_GAP)
            self._rects.append((f, x, y, _PANEL_W, _PANEL_H))

        self._hovered_idx: int | None = None
        self._anim_time = 0.0

        # Cached labels
        self._title = arcade.Text(
            "CHOOSE YOUR FACTION",
            WINDOW_WIDTH // 2, WINDOW_HEIGHT - 60,
            COLORS["hero_accent"], font_size=32, anchor_x="center", bold=True,
        )
        self._hint = arcade.Text(
            "Click a banner to take the field. Esc to cancel.",
            WINDOW_WIDTH // 2, 30,
            COLORS["text_dim"], font_size=13, anchor_x="center",
        )
        self._name_texts: list[arcade.Text] = []
        self._tag_texts: list[arcade.Text] = []
        for f, x, y, w, h in self._rects:
            self._name_texts.append(arcade.Text(
                f.display_name, x + w / 2, y + 30, COLORS["text"],
                font_size=16, anchor_x="center", bold=True,
            ))
            self._tag_texts.append(arcade.Text(
                f.tagline, x + w / 2, y + 10, COLORS["text_dim"],
                font_size=10, anchor_x="center",
            ))

    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]

    def on_update(self, delta_time: float) -> None:
        self._anim_time += delta_time

    def on_draw(self) -> None:
        self.clear()
        self._title.draw()
        self._hint.draw()

        for i, (f, x, y, w, h) in enumerate(self._rects):
            hovered = (i == self._hovered_idx)
            fill = (25, 25, 32) if not hovered else (50, 50, 62)
            border = f.accent if hovered else (80, 80, 92)
            arcade.draw_lbwh_rectangle_filled(x, y, w, h, fill)
            arcade.draw_lbwh_rectangle_outline(x, y, w, h, border, 3)
            # Big primary-colored banner inside
            banner_w = w - 40
            banner_h = h - 80
            arcade.draw_lbwh_rectangle_filled(
                x + 20, y + 60, banner_w, banner_h, f.primary
            )
            arcade.draw_lbwh_rectangle_outline(
                x + 20, y + 60, banner_w, banner_h, _darken(f.primary, 0.5), 2
            )
            # Emblem centered on the banner, pulsing gently when hovered
            pulse = 1.0 + (0.08 * math.sin(self._anim_time * 3.5) if hovered else 0)
            emblem_size = banner_h * 0.55 * pulse
            sprites._draw_faction_emblem(  # type: ignore[attr-defined]
                x + w / 2, y + 60 + banner_h / 2, emblem_size, f.key,
            )
            self._name_texts[i].draw()
            self._tag_texts[i].draw()

    # --- input ---

    def on_mouse_motion(self, x: int, y: int, _dx: int, _dy: int) -> None:
        self._hovered_idx = None
        for i, (f, rx, ry, w, h) in enumerate(self._rects):
            if rx <= x <= rx + w and ry <= y <= ry + h:
                self._hovered_idx = i
                return

    def on_mouse_press(self, x: int, y: int, _button: int, _mods: int) -> None:
        for i, (f, rx, ry, w, h) in enumerate(self._rects):
            if rx <= x <= rx + w and ry <= y <= ry + h:
                self._start_game(f)
                return

    def on_key_press(self, symbol: int, _modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            from src.engine.menu_view import MenuView
            self.window.show_view(MenuView())

    # --- action ---

    def _start_game(self, chosen: Faction) -> None:
        from src.engine.game_view import GameView
        # Pick a distinct random faction for the opponent.
        others = [k for k in FACTION_REGISTRY if k != chosen.key]
        opponent_key = random.choice(others) if others else chosen.key
        view = GameView(self.level_name,
                        player_factions={1: chosen.key, 2: opponent_key})
        self.window.show_view(view)


def _darken(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))
