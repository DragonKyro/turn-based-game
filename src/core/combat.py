"""Damage resolution. Returns an itemised result so UI can show "base + RPS + crit - terrain",
and exposes a predicted damage range so the hover preview can show "X–Y dmg" instead of a point."""
from __future__ import annotations

import random
from dataclasses import dataclass

from src.core.coord import manhattan
from src.core.game_state import GameState
from src.entities.hero import Hero
from src.entities.unit import Unit


@dataclass
class SideDamage:
    attacker_id: int
    defender_id: int
    base: int
    rps_bonus: int
    crit_bonus: int
    terrain_reduction: int
    damage_min: int
    damage_max: int
    final: int


@dataclass
class CombatResult:
    attack: SideDamage
    counter: SideDamage | None  # None if defender couldn't counter (died or out of range)
    attacker_died: bool
    defender_died: bool


_RPS_MULT = 1.5
_CRIT_MULT = 1.5
_VARIANCE = 0.10  # ±10%


def _compute_side_damage(
    attacker: Unit, defender: Unit, state: GameState, rng: random.Random | None = None
) -> SideDamage:
    # HP-scaled base damage (AW-style).
    base = type(attacker).attack * attacker.hp_ratio

    rps_mult = _RPS_MULT if defender.kind in type(attacker).rps_strong_vs else 1.0
    crit_firing = any(
        p(attacker, state) for p in type(attacker).positional_crit_conditions
    )
    crit_mult = _CRIT_MULT if crit_firing else 1.0

    damage_before_terrain = base * rps_mult * crit_mult

    defender_tile = state.map.tile(defender.coord)
    terrain_reduction = int(round(defender_tile.terrain.defense_bonus * defender.hp_ratio))

    mid_damage = max(0, int(round(damage_before_terrain)) - terrain_reduction)

    # Range for preview + roll for resolution. Min/max stay tight (±10%, but always ±1
    # at minimum so there's visible variance on low-damage attacks).
    spread = max(1, int(round(mid_damage * _VARIANCE)))
    damage_min = max(0, mid_damage - spread)
    damage_max = max(damage_min, mid_damage + spread)
    if rng is None:
        final = mid_damage  # preview/no-roll path
    else:
        final = rng.randint(damage_min, damage_max)

    return SideDamage(
        attacker_id=attacker.id,
        defender_id=defender.id,
        base=int(round(base)),
        rps_bonus=int(round(base * (rps_mult - 1.0))),
        crit_bonus=int(round(base * rps_mult * (crit_mult - 1.0))),
        terrain_reduction=terrain_reduction,
        damage_min=damage_min,
        damage_max=damage_max,
        final=final,
    )


def _can_counter(attacker: Unit, defender: Unit) -> bool:
    """Defender counters if the attacker is within the defender's own attack range."""
    lo, hi = type(defender).attack_range
    d = manhattan(attacker.coord, defender.coord)
    return lo <= d <= hi


def _award_hero_charge(u: Unit, amount: int) -> None:
    if isinstance(u, Hero) and amount > 0:
        u.add_charge(1)


def resolve_attack(
    state: GameState, attacker_id: int, defender_id: int,
    rng: random.Random | None = None,
) -> CombatResult:
    """Resolve an attack with damage rolled from the computed range.

    Pass a pre-seeded `rng` for determinism in tests; otherwise a fresh Random() is used.
    """
    if rng is None:
        rng = random.Random()
    attacker = state.units[attacker_id]
    defender = state.units[defender_id]

    attack_dmg = _compute_side_damage(attacker, defender, state, rng=rng)
    defender.hp = max(0, defender.hp - attack_dmg.final)
    _award_hero_charge(attacker, attack_dmg.final)
    _award_hero_charge(defender, attack_dmg.final)

    counter: SideDamage | None = None
    if defender.is_alive and _can_counter(attacker, defender):
        counter = _compute_side_damage(defender, attacker, state, rng=rng)
        attacker.hp = max(0, attacker.hp - counter.final)
        _award_hero_charge(defender, counter.final)
        _award_hero_charge(attacker, counter.final)

    return CombatResult(
        attack=attack_dmg,
        counter=counter,
        attacker_died=not attacker.is_alive,
        defender_died=not defender.is_alive,
    )


def predict_attack(state: GameState, attacker_id: int, defender_id: int) -> CombatResult:
    """Non-mutating prediction: show the RANGE on a state snapshot so UI can preview damage.

    Caller is expected to pass a state snapshot (e.g., via copy.deepcopy) if they want to
    avoid touching live state. The prediction path doesn't roll — `final` equals the midpoint.
    """
    attacker = state.units[attacker_id]
    defender = state.units[defender_id]
    attack_dmg = _compute_side_damage(attacker, defender, state, rng=None)
    counter: SideDamage | None = None
    if _can_counter(attacker, defender):
        counter = _compute_side_damage(defender, attacker, state, rng=None)
    return CombatResult(
        attack=attack_dmg,
        counter=counter,
        attacker_died=False,
        defender_died=False,
    )
