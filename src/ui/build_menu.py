"""Minimal production popup: list the unit kinds a building can produce, with cost and affordability.

Cached `arcade.Text` objects avoid the per-frame draw_text perf cost. Text objects are
constructed once per BuildMenu instance (= once per menu opening).
"""
from __future__ import annotations

import arcade

from src.config import COLORS, WINDOW_HEIGHT
from src.entities.building import Building
from src.entities.units import UNIT_REGISTRY


class BuildMenu:
    def __init__(self, building: Building, gold: int) -> None:
        self.building = building
        self.gold = gold
        self.panel_w = 220
        self.row_h = 28
        self.x = 20

        kinds = list(type(building).produces_kinds)
        self.panel_h = 44 + self.row_h * max(1, len(kinds))
        self.y = WINDOW_HEIGHT - self.panel_h - 40

        # Cached Text objects — built once per menu open.
        self._title = arcade.Text(
            f"Build from {type(building).__name__}",
            self.x + 10, self.y + self.panel_h - 22,
            COLORS["text"], font_size=13, bold=True,
        )
        self._kinds = kinds
        self._rows: list[arcade.Text] = []
        for i, kind in enumerate(kinds):
            cls = UNIT_REGISTRY[kind]
            afford = gold >= cls.cost
            color = COLORS["text"] if afford else COLORS["text_dim"]
            row_y = self.y + self.panel_h - 44 - i * self.row_h
            self._rows.append(
                arcade.Text(
                    f"{i + 1}. {kind.capitalize()}   ({cls.cost}g)",
                    self.x + 14, row_y, color, font_size=13,
                )
            )
        self._hint = arcade.Text(
            "Press 1-9 to build, Esc to close",
            self.x + 10, self.y + 8,
            COLORS["text_dim"], font_size=11,
        )

    def option_kinds(self) -> list[str]:
        return list(self._kinds)

    def kind_at_index(self, i: int) -> str | None:
        return self._kinds[i] if 0 <= i < len(self._kinds) else None

    def can_afford(self, kind: str) -> bool:
        cls = UNIT_REGISTRY.get(kind)
        return cls is not None and self.gold >= cls.cost

    def draw(self) -> None:
        arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.panel_w, self.panel_h, COLORS["ui_panel"])
        arcade.draw_lbwh_rectangle_outline(self.x, self.y, self.panel_w, self.panel_h, COLORS["ui_border"], 2)
        self._title.draw()
        for row in self._rows:
            row.draw()
        self._hint.draw()
