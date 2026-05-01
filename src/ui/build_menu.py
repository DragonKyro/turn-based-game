"""Production popup with clickable rows + a details side-card on hover.

Rows are mouse-hoverable (highlight on hover) and mouse-clickable. Digit keys 1-9 still work
as a fallback. Hovering a row reveals a details panel with the unit's full stat block
(HP, attack, defense, move, vision, attack range, RPS target, cost) so the player knows
what they're buying before they click.
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

        # --- Layout ---
        self.row_h = 34
        self.panel_w = 240
        self.x = 20

        kinds = list(type(building).produces_kinds)
        self._kinds = kinds
        self.panel_h = 64 + self.row_h * max(1, len(kinds))
        self.y = WINDOW_HEIGHT - self.panel_h - 40

        # --- Rows ---
        self._row_texts: list[tuple[arcade.Text, arcade.Text]] = []  # (name, cost)
        for i, kind in enumerate(kinds):
            cls = UNIT_REGISTRY[kind]
            afford = gold >= cls.cost
            name_color = COLORS["text"] if afford else COLORS["text_dim"]
            row_y = self._row_y(i)
            self._row_texts.append((
                arcade.Text(
                    f"{i + 1}. {kind.capitalize()}",
                    self.x + 14, row_y + 10,
                    name_color, font_size=14, bold=True,
                ),
                arcade.Text(
                    f"{cls.cost}g",
                    self.x + self.panel_w - 58, row_y + 10,
                    name_color, font_size=13,
                ),
            ))

        self._title = arcade.Text(
            f"Build from {type(building).__name__}",
            self.x + 10, self.y + self.panel_h - 22,
            COLORS["text"], font_size=13, bold=True,
        )
        self._hint = arcade.Text(
            "Click a row (or press 1-9). Esc to close.",
            self.x + 10, self.y + 8,
            COLORS["text_dim"], font_size=11,
        )

        # --- Details side-card (shown when a row is hovered) ---
        self.detail_w = 240
        self.detail_h = 200
        self.detail_x = self.x + self.panel_w + 12
        self.detail_y = self.y + self.panel_h - self.detail_h

        self._detail_title = arcade.Text("", self.detail_x + 12,
                                         self.detail_y + self.detail_h - 24,
                                         COLORS["hero_accent"], font_size=16, bold=True)
        self._detail_subtitle = arcade.Text("", self.detail_x + 12,
                                            self.detail_y + self.detail_h - 44,
                                            COLORS["text_dim"], font_size=11)
        self._detail_rows = [
            arcade.Text("", self.detail_x + 14,
                        self.detail_y + self.detail_h - 72 - i * 18,
                        COLORS["text"], font_size=12)
            for i in range(7)
        ]

        # --- State ---
        self._hovered_index: int | None = None

    def _row_y(self, i: int) -> float:
        # Top-most row sits right under the title; index grows downward.
        top = self.y + self.panel_h - 44
        return top - (i + 1) * self.row_h

    def _row_rect(self, i: int) -> tuple[float, float, float, float]:
        # (left, bottom, w, h)
        return (self.x + 6, self._row_y(i) + 2, self.panel_w - 12, self.row_h - 4)

    # --- Introspection for GameView ---

    def option_kinds(self) -> list[str]:
        return list(self._kinds)

    def kind_at_index(self, i: int) -> str | None:
        return self._kinds[i] if 0 <= i < len(self._kinds) else None

    def can_afford(self, kind: str) -> bool:
        cls = UNIT_REGISTRY.get(kind)
        return cls is not None and self.gold >= cls.cost

    # --- Mouse ---

    def on_mouse_motion(self, x: int, y: int) -> None:
        self._hovered_index = None
        for i in range(len(self._kinds)):
            left, bottom, w, h = self._row_rect(i)
            if left <= x <= left + w and bottom <= y <= bottom + h:
                self._hovered_index = i
                return

    def on_mouse_press(self, x: int, y: int) -> str | None:
        """If the click landed on a row, return that kind; else None.

        Clicking outside both the menu AND the details card closes the menu — the caller
        decides, though; we just return None. Caller inspects contains_point.
        """
        for i in range(len(self._kinds)):
            left, bottom, w, h = self._row_rect(i)
            if left <= x <= left + w and bottom <= y <= bottom + h:
                return self._kinds[i]
        return None

    def contains_point(self, x: int, y: int) -> bool:
        """True if (x, y) falls inside the main panel OR the details card — so clicks inside
        the whole menu complex don't immediately close it."""
        if self.x <= x <= self.x + self.panel_w and self.y <= y <= self.y + self.panel_h:
            return True
        if self._hovered_index is not None:
            if (self.detail_x <= x <= self.detail_x + self.detail_w
                and self.detail_y <= y <= self.detail_y + self.detail_h):
                return True
        return False

    # --- Drawing ---

    def draw(self) -> None:
        arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.panel_w, self.panel_h,
                                           COLORS["ui_panel"])
        arcade.draw_lbwh_rectangle_outline(self.x, self.y, self.panel_w, self.panel_h,
                                            COLORS["ui_border"], 2)
        self._title.draw()

        for i, (name, cost) in enumerate(self._row_texts):
            left, bottom, w, h = self._row_rect(i)
            hovered = (self._hovered_index == i)
            if hovered:
                arcade.draw_lbwh_rectangle_filled(left, bottom, w, h, COLORS["hero_accent"])
                name.color = (30, 20, 10)
                cost.color = (30, 20, 10)
            else:
                afford = self.can_afford(self._kinds[i])
                c = COLORS["text"] if afford else COLORS["text_dim"]
                name.color = c
                cost.color = c
            name.draw()
            cost.draw()

        self._hint.draw()

        if self._hovered_index is not None:
            self._draw_details(self._kinds[self._hovered_index])

    def _draw_details(self, kind: str) -> None:
        cls = UNIT_REGISTRY.get(kind)
        if cls is None:
            return
        arcade.draw_lbwh_rectangle_filled(
            self.detail_x, self.detail_y, self.detail_w, self.detail_h, COLORS["ui_panel"]
        )
        arcade.draw_lbwh_rectangle_outline(
            self.detail_x, self.detail_y, self.detail_w, self.detail_h, COLORS["hero_accent"], 2
        )
        self._detail_title.text = kind.capitalize()
        self._detail_title.draw()
        self._detail_subtitle.text = f"{cls.unit_class.name.capitalize()} unit"
        self._detail_subtitle.draw()
        rps = ", ".join(sorted(cls.rps_strong_vs)) or "none"
        texts = [
            f"Cost: {cls.cost}g   {'(affordable)' if self.gold >= cls.cost else '(NOT affordable)'}",
            f"HP: {cls.max_hp}    Move: {cls.move}",
            f"Attack: {cls.attack}    Defense: {cls.defense}",
            f"Attack range: {cls.attack_range[0]}–{cls.attack_range[1]}",
            f"Vision range: {cls.vision_range}",
            f"Strong vs: {rps}",
            "Spawns on this building, cannot move this turn.",
        ]
        for i, t in enumerate(texts):
            r = self._detail_rows[i]
            r.text = t
            r.color = (COLORS["hero_accent"] if i == 0 and self.gold < cls.cost
                       else COLORS["text"])
            r.draw()
