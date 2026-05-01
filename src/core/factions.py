"""Faction definitions: palette + emblem motif.

Every faction fields the same unit roster — what differs is color scheme and banner motif
(flame, snowflake, leaf, lightning, wave, sun, moon, gear). Levels reference factions by
their lowercase key; the Player dataclass stores that key as `faction`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Faction:
    key: str
    display_name: str
    primary: tuple[int, int, int]   # main body/banner color
    accent: tuple[int, int, int]    # highlight / emblem color
    emblem: str                     # one of EMBLEMS
    tagline: str


EMBLEMS = ("flame", "snowflake", "leaf", "lightning", "wave", "sun", "moon", "gear")


FACTION_REGISTRY: dict[str, Faction] = {
    "emberdyne": Faction(
        key="emberdyne", display_name="Emberdyne",
        primary=(205, 70, 55), accent=(255, 210, 60),
        emblem="flame", tagline="Ashen crown of the southern lords",
    ),
    "frostmoor":  Faction(
        key="frostmoor",  display_name="Frostmoor",
        primary=(80, 140, 220), accent=(200, 230, 250),
        emblem="snowflake", tagline="Glaciers and the long silence",
    ),
    "verdania":   Faction(
        key="verdania",   display_name="Verdania",
        primary=(95, 170, 85), accent=(230, 245, 140),
        emblem="leaf", tagline="Green riders of the deep wood",
    ),
    "stormhold":  Faction(
        key="stormhold",  display_name="Stormhold",
        primary=(150, 105, 220), accent=(255, 235, 120),
        emblem="lightning", tagline="Thunder from the high peaks",
    ),
    "tidecaller": Faction(
        key="tidecaller", display_name="Tidecaller",
        primary=(55, 170, 195), accent=(170, 240, 235),
        emblem="wave", tagline="The sea-kings of the drowned coast",
    ),
    "sunspire":   Faction(
        key="sunspire",   display_name="Sunspire",
        primary=(240, 170, 55), accent=(255, 240, 165),
        emblem="sun", tagline="Dawn host of the desert reach",
    ),
    "nightvale":  Faction(
        key="nightvale",  display_name="Nightvale",
        primary=(115, 95, 165), accent=(210, 190, 235),
        emblem="moon", tagline="Moon-riders of the black valley",
    ),
    "ironclad":   Faction(
        key="ironclad",   display_name="Ironclad",
        primary=(150, 155, 165), accent=(225, 225, 230),
        emblem="gear", tagline="Clockwork legion of the grey citadel",
    ),
}


def get_faction(key: str) -> Faction:
    """Look up a faction by key (case-insensitive). Falls back to Emberdyne with a warning."""
    k = key.lower()
    if k in FACTION_REGISTRY:
        return FACTION_REGISTRY[k]
    # Legacy levels stored display names — tolerate that.
    for f in FACTION_REGISTRY.values():
        if f.display_name.lower() == k:
            return f
    return FACTION_REGISTRY["emberdyne"]
