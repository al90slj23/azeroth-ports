"""Independent ordered-binary32 projection of recovered933/934 combat slices.

All floating inputs/outputs except the f64 total are uint32 IEEE754 bits. This
models actual HP writes and core death fields, not complete933: procs, healing,
loot/XP and their RNG continuation, animation/position interpolation, packet queues and per-spell statistics
are excluded. Immutable records make the selected projection reviewable.
"""
from dataclasses import dataclass, fields, replace
import math
from . import binary32 as f
from .rng import next_u32_words

ONE = 0x3f800000
ZERO = 0


def _bits(value):
    if not isinstance(value, int) or not 0 <= value <= f.MASK:
        raise ValueError('Expected a uint32 binary32 bit pattern')
    return value


def base_hit_bits(definition_damage_bits, ability_damage_bits, ability_additional_bits,
                  category, player_hp_bits, ability_hp_component_bits, player_damage_bits):
    """934:L440..510 base; ability offsets12/52 and category84, ordered f32."""
    for value in (definition_damage_bits, ability_damage_bits, ability_additional_bits,
                  player_hp_bits, ability_hp_component_bits, player_damage_bits):
        _bits(value)
    if not isinstance(category, int) or not 0 <= category <= 255:
        raise ValueError('category is an original u8')
    scale = (0x3f000000, 0x3f000000, ONE, ONE, ONE, ONE, 0x3f000000)
    category_scale = scale[category - 2] if 2 <= category <= 8 else ONE
    spell = f.mul(definition_damage_bits, 0x3fb33333)
    spell = f.mul(spell, ability_damage_bits)
    spell = f.mul(spell, ability_additional_bits)
    spell = f.mul(spell, category_scale)
    hp = f.mul(player_hp_bits, ability_hp_component_bits)
    hp = hp if f.to_float(definition_damage_bits) > 0 else ZERO
    return f.mul(player_damage_bits, f.add(spell, hp))


@dataclass(frozen=True)
class CriticalHit:
    amount_bits: int
    critical: bool
    uniform_bits: int
    rng_state: tuple


def critical_hit_bits(base_bits, crit_probability_bits, crit_multiplier_bits, rng_state):
    """One934 draw; high24 bits, strict probability>U, no clamp/rejection."""
    for value in (base_bits, crit_probability_bits, crit_multiplier_bits):
        _bits(value)
    output, updated = next_u32_words(rng_state)
    uniform = f.mul(f.from_u32(output >> 8), 0x33800000)
    critical = f.to_float(crit_probability_bits) > f.to_float(uniform)
    return CriticalHit(f.mul(base_bits, crit_multiplier_bits) if critical else base_bits,
                       critical, uniform, updated)


@dataclass(frozen=True)
class ItemModifier:
    tag: int
    value_bits: int

    def __post_init__(self):
        if not isinstance(self.tag, int) or not 0 <= self.tag <= 255:
            raise ValueError('Item tag must be uint8')
        _bits(self.value_bits)


@dataclass(frozen=True)
class UnitState:
    target_id: int
    hp_bits: int
    max_hp_bits: int
    marker: int = 0                         # +0; 1 means dead
    kind_40: int = -1
    linked_id_32: int = 0
    kind_64: int = -1
    elite_244: int = -1
    elite_412: int = 0
    afflicted_240: int = 0
    control_until_124_bits: int = ZERO
    control_until_376_bits: int = ZERO
    control_until_384_bits: int = ZERO
    additive_144_bits: int = ZERO
    additive_until_148_bits: int = ZERO
    additive_152_bits: int = ZERO
    additive_until_156_bits: int = ZERO
    additive_160_bits: int = ZERO
    additive_until_164_bits: int = ZERO
    additive_364_bits: int = ZERO
    phase_until_404_bits: int = ZERO
    phase_until_408_bits: int = ZERO
    movement_duration_344_bits: int = ZERO
    movement_time_340_bits: int = ZERO
    death_time_4_bits: int = ZERO

    def __post_init__(self):
        for field in fields(self):
            if field.name.endswith('_bits'):
                _bits(getattr(self, field.name))
        for name in ('target_id', 'linked_id_32'):
            value = getattr(self, name)
            if not isinstance(value, int) or not 0 <= value <= 0xffffffffffffffff:
                raise ValueError('GUID must be uint64')


@dataclass(frozen=True)
class CombatState:
    units: tuple = ()
    items: tuple = ()
    now_bits: int = ZERO
    shield_bits: int = ZERO
    running_2299: int = 1
    accounted_total: float = 0.0           # original f64 +824

    def __post_init__(self):
        object.__setattr__(self, 'units', tuple(self.units))
        object.__setattr__(self, 'items', tuple(self.items))
        if not all(isinstance(u, UnitState) for u in self.units):
            raise ValueError('units must contain UnitState records')
        if not all(isinstance(i, ItemModifier) for i in self.items):
            raise ValueError('items must contain ItemModifier records')
        _bits(self.now_bits)
        _bits(self.shield_bits)


def _tag_sum(items, tag):
    value = 0x80000000                    # original accumulator starts -0
    for item in items:
        if item.tag == tag:
            value = f.add(value, item.value_bits)
    return value


def damage_modifier_bits(state, target):
    """933 additive item/debuff M, with original grouping and priority."""
    now = f.to_float(state.now_bits)
    m = ONE
    if any(f.to_float(x) > now for x in (target.control_until_376_bits,
                                         target.control_until_124_bits,
                                         target.control_until_384_bits)):
        m = f.add(_tag_sum(state.items, 18), ONE)
    if target.elite_244 != -1 or target.elite_412 == 1:
        m = f.add(m, _tag_sum(state.items, 19))
    if f.to_float(target.hp_bits) < f.to_float(f.mul(target.max_hp_bits, 0x3e99999a)):
        m = f.add(m, _tag_sum(state.items, 20))
    if target.afflicted_240 != 0:
        m = f.add(m, _tag_sum(state.items, 21))
    if now < f.to_float(target.additive_until_148_bits):
        m = f.add(m, target.additive_144_bits)
    term = ZERO
    if now < f.to_float(target.additive_until_156_bits):
        term = target.additive_152_bits
    elif f.to_float(target.additive_until_164_bits) > now:
        term = target.additive_160_bits
    m = f.add(m, term)
    if f.to_float(state.shield_bits) > 0:
        m = f.add(m, _tag_sum(state.items, 28))
    return f.add(m, target.additive_364_bits)


def damage_phase_bits(state, target):
    if target.elite_244 != -1 or target.kind_64 != -1:
        now = f.to_float(state.now_bits)
        if f.to_float(target.phase_until_408_bits) > now:
            return 0x3fc00000
        if f.to_float(target.phase_until_404_bits) > now:
            return 0x3e800000
        if any(u.marker == 0 and u.kind_40 == 2 and u.linked_id_32 == target.target_id
               for u in state.units):
            return 0x3e800000
    return ONE


def cap_damage_bits(amount_bits, max_hp_bits):
    """933 select-based minNum-like cap, preserving the original tie order."""
    cap = f.div(max_hp_bits, 0x40a00000)
    a = cap if f.is_nan(amount_bits) else amount_bits
    b = a if f.is_nan(cap) else cap
    return a if f.to_float(a) < f.to_float(b) else b


def encoded_hp(hp_bits):
    """933 HP field22: nonnegative/nonNaN -> f32.ceil -> trunc_sat_u32."""
    value = f.to_float(hp_bits)
    if not value > 0:
        return 0
    if value >= 0xffffffff:
        return 0xffffffff
    return math.ceil(value)


@dataclass(frozen=True)
class DamageResult:
    state: CombatState
    target: UnitState | None
    applied: bool
    reason: str
    damage_bits: int
    old_hp_bits: int
    new_hp_bits: int
    accounted_bits: int
    encoded_hp: int
    dead: bool
    unknown_sideeffects: tuple = ('per_spell_statistics', 'procs', 'healing', 'loot',
                                 'position_animation', 'packet_queue', 'death_xp_and_rng_continuation')


def resolve_damage(state, target_id, amount_bits, spell_id=0, spell_category=None):
    """Apply recovered933 core projection to a unique-GUID immutable unit set.

    For the special kind3/link0 target and a nonzero spell ID, callers supply the
    already resolved original u8 category; unknown categories raise, not guess.
    """
    _bits(amount_bits)
    ids = [u.target_id for u in state.units]
    if len(ids) != len(set(ids)):
        raise ValueError('Projection requires unique target GUIDs')
    target = next((u for u in state.units if u.target_id == target_id), None)
    def skip(reason):
        hp = target.hp_bits if target else ZERO
        return DamageResult(state, target, False, reason, ZERO, hp, hp, ZERO,
                            encoded_hp(hp), bool(target and target.marker == 1))
    if state.running_2299 != 1:
        return skip('not_running')
    if target is None:
        return skip('target_absent')
    amount = f.mul(amount_bits, damage_modifier_bits(state, target))
    amount = f.mul(amount, damage_phase_bits(state, target))
    if target.kind_40 == 3 and target.linked_id_32 == 0:
        if spell_id:
            if spell_category is None:
                raise ValueError('Special target requires resolved spell_category')
            if not isinstance(spell_category, int) or not 0 <= spell_category <= 255:
                raise ValueError('spell_category must be original u8')
            if spell_category <= 11 and (3340 >> spell_category) & 1:
                return skip('special_category_rejected')
        amount = cap_damage_bits(amount, target.max_hp_bits)
        if f.to_float(amount) == 0:
            return skip('special_zero_cap')
    if target.marker == 1:
        return skip('target_dead')
    amount = ONE if f.is_nan(amount) else amount
    damage = amount if f.to_float(amount) > 1 else ONE
    hp = f.sub(target.hp_bits, damage)
    old_nonnegative = target.hp_bits if f.to_float(target.hp_bits) > 0 else ZERO
    accounted = old_nonnegative if f.to_float(old_nonnegative) < f.to_float(damage) else damage
    dead = f.to_float(hp) <= 0
    target_after = replace(target, hp_bits=hp)
    if dead:
        target_after = replace(target_after, marker=1, movement_duration_344_bits=ZERO,
                               afflicted_240=0, death_time_4_bits=state.now_bits,
                               movement_time_340_bits=state.now_bits)
    updated = replace(state, units=tuple(target_after if u.target_id == target_id else u
                                         for u in state.units),
                      accounted_total=state.accounted_total + f.to_float(accounted))
    return DamageResult(updated, target_after, True, 'applied', damage, target.hp_bits,
                        hp, accounted, encoded_hp(hp), dead)
