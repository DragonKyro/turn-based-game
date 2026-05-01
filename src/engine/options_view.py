"""Options screen reachable from the main menu."""
from __future__ import annotations

import arcade

from src.config import COLORS, WINDOW_HEIGHT, WINDOW_WIDTH
from src.core.options import Options
from src.ui.button import Button


class OptionsView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        self.options = Options.load()

        self._title = arcade.Text(
            "OPTIONS",
            WINDOW_WIDTH // 2, WINDOW_HEIGHT - 120,
            COLORS["hero_accent"], font_size=48, anchor_x="center", bold=True,
        )

        btn_w, btn_h = 360, 50
        btn_x = WINDOW_WIDTH // 2 - btn_w // 2
        y0 = WINDOW_HEIGHT // 2 + 110

        self._buttons: list[Button] = []
        self._fight_btn = self._make_toggle_btn(
            btn_x, y0, btn_w, btn_h,
            lambda: self._fmt("Fight scene", self.options.show_fight_scene),
            self._toggle_fight_scene,
        )
        self._music_btn = self._make_toggle_btn(
            btn_x, y0 - 70, btn_w, btn_h,
            lambda: self._fmt("Music", self.options.music_enabled),
            self._toggle_music,
        )
        self._sfx_btn = self._make_toggle_btn(
            btn_x, y0 - 140, btn_w, btn_h,
            lambda: self._fmt("Sound effects", self.options.sfx_enabled),
            self._toggle_sfx,
        )
        self._back_btn = Button(
            label="Back to menu",
            left=btn_x, bottom=y0 - 230, width=btn_w, height=btn_h,
            on_click=self._back,
        )
        self._buttons = [self._fight_btn, self._music_btn, self._sfx_btn, self._back_btn]

    def _fmt(self, label: str, enabled: bool) -> str:
        return f"{label}:  {'ON' if enabled else 'OFF'}"

    def _make_toggle_btn(self, x: float, y: float, w: float, h: float,
                          label_fn, on_click) -> Button:
        return Button(label=label_fn(), left=x, bottom=y, width=w, height=h,
                       on_click=on_click)

    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]

    def on_draw(self) -> None:
        self.clear()
        self._title.draw()
        for b in self._buttons:
            b.draw()

    def on_mouse_motion(self, x: int, y: int, _dx: int, _dy: int) -> None:
        for b in self._buttons:
            b.set_hovered(b.contains(x, y))

    def on_mouse_press(self, x: int, y: int, _button: int, _mods: int) -> None:
        for b in self._buttons:
            if b.on_click_if_inside(x, y):
                from src.engine.audio import Audio
                Audio.get().play_sfx("click")
                return

    def on_key_press(self, symbol: int, _modifiers: int) -> None:
        if symbol == arcade.key.ESCAPE:
            self._back()

    # --- toggles ---

    def _rebuild_buttons(self) -> None:
        """Rebuild the three toggle buttons so their cached labels refresh."""
        self._fight_btn = self._make_toggle_btn(
            self._fight_btn.left, self._fight_btn.bottom,
            self._fight_btn.width, self._fight_btn.height,
            lambda: self._fmt("Fight scene", self.options.show_fight_scene),
            self._toggle_fight_scene,
        )
        self._music_btn = self._make_toggle_btn(
            self._music_btn.left, self._music_btn.bottom,
            self._music_btn.width, self._music_btn.height,
            lambda: self._fmt("Music", self.options.music_enabled),
            self._toggle_music,
        )
        self._sfx_btn = self._make_toggle_btn(
            self._sfx_btn.left, self._sfx_btn.bottom,
            self._sfx_btn.width, self._sfx_btn.height,
            lambda: self._fmt("Sound effects", self.options.sfx_enabled),
            self._toggle_sfx,
        )
        self._buttons = [self._fight_btn, self._music_btn, self._sfx_btn, self._back_btn]

    def _toggle_fight_scene(self) -> None:
        self.options.show_fight_scene = not self.options.show_fight_scene
        self.options.save()
        self._rebuild_buttons()

    def _toggle_music(self) -> None:
        self.options.music_enabled = not self.options.music_enabled
        self.options.save()
        from src.engine.audio import Audio
        if self.options.music_enabled:
            Audio.get().play_music("title")
        else:
            Audio.get().stop_music()
        self._rebuild_buttons()

    def _toggle_sfx(self) -> None:
        self.options.sfx_enabled = not self.options.sfx_enabled
        self.options.save()
        self._rebuild_buttons()

    def _back(self) -> None:
        from src.engine.menu_view import MenuView
        self.window.show_view(MenuView())
