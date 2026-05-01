"""Minimal production popup: list the unit kinds a building can produce, with cost and affordability.

The menu is a value object. GameView owns positioning/visibility and dispatches the chosen kind.
"""
from __future__ import annotations

from dataclasses import dataclass

import arcade

from src.config import COLORS, WINDOW_HEIGHT
from src.entities.building import Building
from src.entities.units import UNIT_REGISTRY


@dataclass
class BuildMenu:
    building: Building
    gold: int

    def option_kinds(self) -> list[str]:
        return list(type(self.building).produces_kinds)

    def kind_at_index(self, i: int) -> str | None:
        kinds = self.option_kinds()
        return kinds[i] if 0 <= i < len(kinds) else None

    def can_afford(self, kind: str) -> bool:
        cls = UNIT_REGISTRY.get(kind)
        return cls is not None and self.gold >= cls.cost

    def draw(self) -> None:
        panel_w = 220
        row_h = 28
        x = 20
        rows = self.option_kinds()
        panel_h = 44 + row_h * max(1, len(rows))
        y = WINDOW_HEIGHT - panel_h - 40

        arcade.draw_lbwh_rectangle_filled(x, y, panel_w, panel_h, COLORS["ui_panel"])
        arcade.draw_lbwh_rectangle_outline(x, y, panel_w, panel_h, COLORS["ui_border"], 2)
        arcade.draw_text(
            f"Build from {type(self.building).__name__}",
            x + 10, y + panel_h - 22, COLORS["text"], font_size=13, bold=True,
        )
        for i, kind in enumerate(rows):
            row_y = y + panel_h - 44 - i * row_h
            cls = UNIT_REGISTRY[kind]
            afford = self.can_afford(kind)
            color = COLORS["text"] if afford else COLORS["text_dim"]
            arcade.draw_text(
                f"{i + 1}. {kind.capitalize()}   ({cls.cost}g)",
                x + 14, row_y, color, font_size=13,
            )
        arcade.draw_text(
            "Press 1-9 to build, Esc to close",
            x + 10, y + 8, COLORS["text_dim"], font_size=11,
        )
