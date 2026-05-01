"""Global game constants. No arcade import here so core modules can safely read from this file."""
from __future__ import annotations

from pathlib import Path

# --- Window ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
WINDOW_TITLE = "Embercrown"

# --- Map rendering ---
TILE_SIZE = 48

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
LEVELS_DIR = PROJECT_ROOT / "src" / "data" / "levels"

# --- Gameplay ---
DEFAULT_LEVEL = "01_first_clash"

# Palette (RGB). Kept as tuples so pure-logic modules can reference them too.
COLORS = {
    "background":    (18, 18, 22),
    "text":          (235, 235, 235),
    "text_dim":      (140, 140, 150),
    "ui_panel":      (30, 30, 38),
    "ui_border":     (70, 70, 90),

    # Terrain fills
    "plains":        (128, 180, 95),
    "forest":        (48, 110, 58),
    "mountain":      (120, 100, 80),
    "road":          (190, 170, 120),
    "sea":           (48, 94, 160),
    "grid_line":     (55, 55, 62),

    # Players
    "player1":       (205, 70, 55),   # Emberdyne red-orange
    "player2":       (80, 140, 220),  # Frostmoor blue

    # Overlays
    "move_range":    (80, 160, 255, 90),
    "attack_range":  (230, 70, 70, 100),
    "selection":     (255, 230, 120, 180),
    "hero_accent":   (255, 210, 60),

    # Fog
    "fog_hidden":    (0, 0, 0, 255),
    "fog_explored":  (0, 0, 0, 130),
}
