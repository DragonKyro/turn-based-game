"""Damage resolution. Returns an itemised result so UI can show "base + RPS + crit - terrain"."""
from __future__ import annotations

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
    final: int


@dataclass
class CombatResult:
    attack: SideDamage
    counter: SideDamage | None  # None if defender couldn't counter (died or out of range)
    attacker_died: bool
    defender_died: bool


_RPS_MULT = 1.5
_CRIT_MULT = 1.5


def _compute_side_damage(
    attacker: Unit, defender: Unit, state: GameState
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

    final = max(0, int(round(damage_before_terrain)) - terrain_reduction)

    return SideDamage(
        attacker_id=attacker.id,
        defender_id=defender.id,
        base=int(round(base)),
        rps_bonus=int(round(base * (rps_mult - 1.0))),
        crit_bonus=int(round(base * rps_mult * (crit_mult - 1.0))),
        terrain_reduction=terrain_reduction,
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
    state: GameState, attacker_id: int, defender_id: int
) -> CombatResult:
    attacker = state.units[attacker_id]
    defender = state.units[defender_id]

    attack_dmg = _compute_side_damage(attacker, defender, state)
    defender.hp = max(0, defender.hp - attack_dmg.final)
    _award_hero_charge(attacker, attack_dmg.final)
    _award_hero_charge(defender, attack_dmg.final)

    counter: SideDamage | None = None
    if defender.is_alive and _can_counter(attacker, defender):
        counter = _compute_side_damage(defender, attacker, state)
        attacker.hp = max(0, attacker.hp - counter.final)
        _award_hero_charge(defender, counter.final)
        _award_hero_charge(attacker, counter.final)

    return CombatResult(
        attack=attack_dmg,
        counter=counter,
        attacker_died=not attacker.is_alive,
        defender_died=not defender.is_alive,
    )
