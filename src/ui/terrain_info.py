"""Bottom-left panel showing terrain details for the hovered tile.

Follows AW/Wargroove convention: always visible while hovering over the map, so the
player can check cover/movement without a separate click.
"""
from __future__ import annotations

import arcade

from src.config import COLORS
from src.core.types import IMPASSABLE, UnitClass
from src.world.terrain import Terrain


_CLASS_LABEL = {
    UnitClass.LAND:    "Land",
    UnitClass.VEHICLE: "Vehicle",
    UnitClass.AIR:     "Air",
    UnitClass.WATER:   "Water",
}


class TerrainInfo:
    def __init__(self, window_height: int) -> None:
        self.window_height = window_height
        self.panel_w = 260
        self.panel_h = 170
        self.x = 12
        self.y = 40   # sits above the bottom banner

        self._title = arcade.Text("", self.x + 12, self.y + self.panel_h - 24,
                                  COLORS["text"], font_size=15, bold=True)
        self._defense = arcade.Text("", self.x + 12, self.y + self.panel_h - 50,
                                    COLORS["text"], font_size=12)
        self._vision = arcade.Text("", self.x + 12, self.y + self.panel_h - 70,
                                   COLORS["text_dim"], font_size=11)
        self._move_label = arcade.Text("Movement cost:", self.x + 12, self.y + 80,
                                       COLORS["text_dim"], font_size=11)
        self._move_rows = [
            arcade.Text("", self.x + 20, self.y + 62 - i * 16,
                        COLORS["text"], font_size=11)
            for i in range(4)
        ]

    def draw(self, terrain: Terrain | None) -> None:
        if terrain is None:
            return
        arcade.draw_lbwh_rectangle_filled(self.x, self.y, self.panel_w, self.panel_h,
                                           COLORS["ui_panel"])
        arcade.draw_lbwh_rectangle_outline(self.x, self.y, self.panel_w, self.panel_h,
                                            COLORS["ui_border"], 2)

        self._title.text = terrain.name.capitalize()
        self._title.draw()

        self._defense.text = f"Defense bonus: +{terrain.defense_bonus}"
        self._defense.draw()

        self._vision.text = (
            "Blocks line of sight beyond adjacent tiles." if terrain.blocks_vision
            else "Does not block vision."
        )
        self._vision.draw()

        self._move_label.draw()
        for i, uclass in enumerate((UnitClass.LAND, UnitClass.VEHICLE,
                                     UnitClass.AIR, UnitClass.WATER)):
            cost = terrain.cost_for(uclass)
            label = _CLASS_LABEL[uclass]
            row = self._move_rows[i]
            if cost >= IMPASSABLE:
                row.text = f"  {label:<8}  impassable"
                row.color = COLORS["text_dim"]
            else:
                row.text = f"  {label:<8}  {cost} mp/tile"
                row.color = COLORS["text"]
            row.draw()
