"""Title screen with mouse-clickable buttons + hover highlight."""
from __future__ import annotations

import arcade

from src.config import COLORS, DEFAULT_LEVEL, WINDOW_HEIGHT, WINDOW_WIDTH
from src.ui.button import Button


class MenuView(arcade.View):
    def __init__(self) -> None:
        super().__init__()
        # Cached text
        self._title_text = arcade.Text(
            "EMBERCROWN",
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 120,
            COLORS["hero_accent"], font_size=64, anchor_x="center", bold=True,
        )
        self._subtitle_text = arcade.Text(
            "A turn-based tactics skirmish",
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70,
            COLORS["text_dim"], font_size=18, anchor_x="center",
        )
        self._hint_text = arcade.Text(
            "Click a button below, or use Enter / Esc.",
            WINDOW_WIDTH // 2, 40,
            COLORS["text_dim"], font_size=13, anchor_x="center",
        )

        btn_w = 260
        btn_h = 56
        btn_x = WINDOW_WIDTH // 2 - btn_w // 2
        gap = 14
        y = WINDOW_HEIGHT // 2 - 10

        self._play_btn = Button(
            label="Play — First Clash",
            left=btn_x, bottom=y, width=btn_w, height=btn_h,
            on_click=self._start_game,
        )
        self._options_btn = Button(
            label="Options",
            left=btn_x, bottom=y - btn_h - gap, width=btn_w, height=btn_h,
            on_click=self._open_options,
        )
        self._quit_btn = Button(
            label="Quit",
            left=btn_x, bottom=y - 2 * (btn_h + gap), width=btn_w, height=btn_h,
            on_click=self._quit,
        )
        self._buttons = [self._play_btn, self._options_btn, self._quit_btn]

    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]
        from src.engine.audio import Audio
        from src.core.options import Options
        opts = Options.load()
        audio = Audio.get()
        if opts.music_enabled:
            audio.play_music("title")
        else:
            audio.stop_music()

    def on_draw(self) -> None:
        self.clear()
        # Decorative banner behind the buttons
        arcade.draw_lbwh_rectangle_filled(
            0, WINDOW_HEIGHT // 2 + 60, WINDOW_WIDTH, 2, COLORS["hero_accent"]
        )
        self._title_text.draw()
        self._subtitle_text.draw()
        for b in self._buttons:
            b.draw()
        self._hint_text.draw()

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
        if symbol == arcade.key.ENTER:
            self._start_game()
        elif symbol == arcade.key.ESCAPE:
            self._quit()

    # --- actions ---

    def _start_game(self) -> None:
        from src.engine.faction_select_view import FactionSelectView
        self.window.show_view(FactionSelectView(DEFAULT_LEVEL))

    def _open_options(self) -> None:
        from src.engine.options_view import OptionsView
        self.window.show_view(OptionsView())

    def _quit(self) -> None:
        self.window.close()
