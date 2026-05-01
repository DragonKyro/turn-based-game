"""Right-side info panel showing full stats of the selected unit."""
from __future__ import annotations

import arcade

from src.config import COLORS
from src.entities.hero import Hero
from src.entities.unit import Unit


class UnitPanel:
    def __init__(self, window_width: int, window_height: int) -> None:
        self.panel_w = 240
        self.panel_h = 260
        self.x = window_width - self.panel_w - 12
        self.y = window_height - self.panel_h - 40
        self.title = arcade.Text("", self.x + 12, self.y + self.panel_h - 24,
                                 COLORS["text"], font_size=15, bold=True)
        self.subtitle = arcade.Text("", self.x + 12, self.y + self.panel_h - 44,
                                    COLORS["text_dim"], font_size=11)
        self.lines = [
            arcade.Text("", self.x + 12, self.y + self.panel_h - 70 - i * 18,
                        COLORS["text"], font_size=12)
            for i in range(8)
        ]

    def draw(self, unit: Unit) -> None:
        arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.panel_w, self.panel_h, COLORS["ui_panel"])
        arcade.draw_lbwh_rectangle_outline(self.x, self.y, self.panel_w, self.panel_h, COLORS["ui_border"], 2)
        cls = type(unit)
        self.title.text = cls.__name__
        self.title.color = COLORS["player1"] if unit.owner_id == 1 else COLORS["player2"]
        self.title.draw()
        self.subtitle.text = f"{cls.unit_class.name.capitalize()} unit — owner P{unit.owner_id}"
        self.subtitle.draw()

        flag_str = []
        if unit.has_moved: flag_str.append("moved")
        if unit.has_acted: flag_str.append("acted")
        flags = ", ".join(flag_str) or "ready"

        texts = [
            f"HP: {unit.hp} / {cls.max_hp}",
            f"Attack: {cls.attack}",
            f"Defense: {cls.defense}",
            f"Move: {cls.move}    Vision: {cls.vision_range}",
            f"Attack range: {cls.attack_range[0]}-{cls.attack_range[1]}",
            f"Strong vs: {', '.join(sorted(cls.rps_strong_vs)) or '—'}",
            f"Status: {flags}",
        ]
        if isinstance(unit, Hero):
            texts.append(f"Ultimate: {unit.ultimate_charge} / {cls.ultimate_charge_max}")

        for i, text in enumerate(texts):
            self.lines[i].text = text
            self.lines[i].draw()
