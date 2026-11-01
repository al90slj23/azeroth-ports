"""Independent ordered-f32 projection of official0.134.0 damage function914.

This module has its own current-version state schema:424B units and the extra
36B spell-modifier records. It does not call the original module. Raw tags50/51
retain their numeric names; their gameplay names/production are not assumed.
Full procs, healing, per-spell statistics, packets, loot and death RNG remain
outside this core-field projection. Inputs ending in _bits are IEEE754 u32s.
"""
from dataclasses import dataclass, fields, replace
import math
from . import binary32 as f

ONE = 0x3f800000
ZERO = 0


def _bits(value):
    if not isinstance(value, int) or not 0 <= value <= f.MASK:
        raise ValueError('Expected uint32 float bits')
    return value


@dataclass(frozen=True)
class ItemModifier:
    tag: int
    value_bits: int

    def __post_init__(self):
        if not isinstance(self.tag, int) or not 0 <= self.tag <= 255:
            raise ValueError('Item tag must be uint8')
        _bits(self.value_bits)


@dataclass(frozen=True)
class AbilityReference:
    id_bytes: bytes
    spell_id: int

    def __post_init__(self):
        if not isinstance(self.id_bytes, bytes) or not self.id_bytes:
            raise ValueError('Ability ID must be a nonempty byte string')
        if not isinstance(self.spell_id, int) or not 0 <= self.spell_id <= f.MASK:
            raise ValueError('Spell ID must be uint32')


@dataclass(frozen=True)
class SpellModifier:
    tag: int
    ability_id: bytes
    value12_bits: int = ZERO
    value16_bits: int = ZERO

    def __post_init__(self):
        if not isinstance(self.tag, int) or not 0 <= self.tag <= f.MASK:
            raise ValueError('36B record tag must be uint32')
        if not isinstance(self.ability_id, bytes):
            raise ValueError('Ability ID must be bytes')
        _bits(self.value12_bits)
        _bits(self.value16_bits)


class AbilityLookupPanic(ValueError):
    """A gated tag50/51 ID missing from the declaration table traps in914."""


@dataclass(frozen=True)
class UnitState:
    target_id: int
    hp_bits: int
    max_hp_bits: int
    marker: int = 0
    kind_40: int = -1
    linked_id_32: int = 0
    kind_64: int = -1
    elite_244: int = -1
    elite_416: int = 0
    afflicted_240: int = 0
    control_until_124_bits: int = ZERO
    control_until_380_bits: int = ZERO
    control_until_388_bits: int = ZERO
    modifier_until_356_bits: int = ZERO
    additive_144_bits: int = ZERO
    additive_until_148_bits: int = ZERO
    additive_152_bits: int = ZERO
    additive_until_156_bits: int = ZERO
    additive_160_bits: int = ZERO
    additive_until_164_bits: int = ZERO
    additive_368_bits: int = ZERO
    phase_until_408_bits: int = ZERO
    phase_until_412_bits: int = ZERO
    movement_duration_344_bits: int = ZERO
    movement_time_340_bits: int = ZERO
    death_time_4_bits: int = ZERO

    def __post_init__(self):
        for field in fields(self):
            if field.name.endswith('_bits'):
                _bits(getattr(self, field.name))
        for value in (self.target_id, self.linked_id_32):
            if not isinstance(value, int) or not 0 <= value <= 0xffffffffffffffff:
                raise ValueError('GUID must be uint64')


@dataclass(frozen=True)
class CombatState:
    units: tuple = ()
    items: tuple = ()
    spell_modifiers: tuple = ()
    abilities: tuple = ()
    now_bits: int = ZERO
    shield_bits: int = ZERO
    phase_2579: int = 1
    accounted_total: float = 0.0          # f64 G+984

    def __post_init__(self):
        for name, cls in (('units', UnitState), ('items', ItemModifier),
                          ('spell_modifiers', SpellModifier), ('abilities', AbilityReference)):
            value = tuple(getattr(self, name))
            object.__setattr__(self, name, value)
            if not all(isinstance(x, cls) for x in value):
                raise ValueError('Unexpected record in '+name)
        ids = [x.id_bytes for x in self.abilities]
        if len(ids) != len(set(ids)):
            raise ValueError('Projection requires unique ability IDs')
        _bits(self.now_bits)
        _bits(self.shield_bits)


def _tag_sum(items, tag):
    result = 0x80000000                  # item accumulator starts -0
    for item in items:
        if item.tag == tag:
            result = f.add(result, item.value_bits)
    return result


def damage_modifier_bits(state, target):
    now = f.to_float(state.now_bits)
    result = ONE
    if any(f.to_float(x) > now for x in (target.control_until_380_bits,
                                        target.control_until_124_bits,
                                        target.control_until_388_bits)):
        result = f.add(_tag_sum(state.items, 18), ONE)
    if target.elite_244 != -1 or target.elite_416 == 1:
        result = f.add(result, _tag_sum(state.items, 19))
    if f.to_float(target.hp_bits) < f.to_float(f.mul(target.max_hp_bits, 0x3e99999a)):
        result = f.add(result, _tag_sum(state.items, 20))
    if target.afflicted_240 != 0:
        result = f.add(result, _tag_sum(state.items, 21))
    if now < f.to_float(target.additive_until_148_bits):
        result = f.add(result, target.additive_144_bits)
    term = ZERO
    if now < f.to_float(target.additive_until_156_bits):
        term = target.additive_152_bits
    elif f.to_float(target.additive_until_164_bits) > now:
        term = target.additive_160_bits
    result = f.add(result, term)
    if f.to_float(state.shield_bits) > 0:
        result = f.add(result, _tag_sum(state.items, 28))
    return f.add(result, target.additive_368_bits)


def spell_modifier_bits(state, target, spell_id):
    """New914 T: ordered rawtag50/51 gates, ID lookup and f32 sum from+0."""
    total = ZERO
    if not spell_id:
        return total
    for modifier in state.spell_modifiers:
        if modifier.tag == 50:
            gate = f.to_float(target.modifier_until_356_bits) > f.to_float(state.now_bits)
            term = modifier.value12_bits
        elif modifier.tag == 51:
            gate = f.to_float(target.hp_bits) < f.to_float(f.mul(target.max_hp_bits, modifier.value12_bits))
            term = modifier.value16_bits
        else:
            continue
        if not gate:
            continue
        definition = next((a for a in state.abilities if a.id_bytes == modifier.ability_id), None)
        if definition is None:
            raise AbilityLookupPanic('Gated modifier ability ID is absent')
        if definition.spell_id == spell_id:
            total = f.add(total, term)
    return total


def damage_phase_bits(state, target):
    if target.elite_244 != -1 or target.kind_64 != -1:
        now = f.to_float(state.now_bits)
        if f.to_float(target.phase_until_412_bits) > now:
            return 0x3fc00000
        if f.to_float(target.phase_until_408_bits) > now:
            return 0x3e800000
        if any(u.marker == 0 and u.kind_40 == 2 and u.linked_id_32 == target.target_id
               for u in state.units):
            return 0x3e800000
    return ONE


def cap_damage_bits(amount_bits, max_hp_bits):
    cap = f.div(max_hp_bits, 0x40a00000)
    a = cap if f.is_nan(amount_bits) else amount_bits
    b = a if f.is_nan(cap) else cap
    return a if f.to_float(a) < f.to_float(b) else b


def encoded_hp(hp_bits):
    value = f.to_float(hp_bits)
    if not value > 0:
        return 0
    return 0xffffffff if value >= 0xffffffff else math.ceil(value)


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
    """Apply914 core-field projection; table category is supplied for kind3."""
    _bits(amount_bits)
    if not isinstance(spell_id, int) or not 0 <= spell_id <= f.MASK:
        raise ValueError('Spell ID must be uint32')
    ids = [u.target_id for u in state.units]
    if len(ids) != len(set(ids)):
        raise ValueError('Projection requires unique target GUIDs')
    target = next((u for u in state.units if u.target_id == target_id), None)

    def skip(reason):
        hp = target.hp_bits if target else ZERO
        return DamageResult(state, target, False, reason, ZERO, hp, hp, ZERO,
                            encoded_hp(hp), bool(target and target.marker == 1))
    if state.phase_2579 != 1:
        return skip('not_running')
    if target is None:
        return skip('target_absent')
    multiplier = f.add(damage_modifier_bits(state, target), spell_modifier_bits(state, target, spell_id))
    amount = f.mul(f.mul(amount_bits, multiplier), damage_phase_bits(state, target))
    if target.kind_40 == 3 and target.linked_id_32 == 0:
        if spell_id:
            if not isinstance(spell_category, int) or not 0 <= spell_category <= 255:
                raise ValueError('Special target requires resolved original u8 spell category')
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
    after = replace(target, hp_bits=hp)
    if dead:
        after = replace(after, marker=1, movement_duration_344_bits=ZERO, afflicted_240=0,
                        death_time_4_bits=state.now_bits, movement_time_340_bits=state.now_bits)
    updated = replace(state, units=tuple(after if u.target_id == target_id else u for u in state.units),
                      accounted_total=state.accounted_total + f.to_float(accounted))
    return DamageResult(updated, after, True, 'applied', damage, target.hp_bits, hp,
                        accounted, encoded_hp(hp), dead)
