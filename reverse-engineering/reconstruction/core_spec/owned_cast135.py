"""Independent135 learned80B auto-cast1076, distinct from extra84B system916.

The common effect-tag0/execution0/2 domain is executable. The basic80B record
at G1256 is explicit input, never synthesized from a null definition pointer.
Source vectors and the outer player's decision to run this phase are explicit.
This module reads no original binary, index, runtime output or evidence file.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .ability_state import AbilityRecord
from .cast135 import CastDefinition, UnresolvedCast
from .cast_events135 import cast_ability
from .owned_prelude135 import tick_class_prelude


@dataclass(frozen=True)
class OwnedEntry135:
    definition: CastDefinition
    record: AbilityRecord

    def __post_init__(self):
        if self.record.definition_pointer != self.definition.pointer or not self.definition.pointer:
            raise ValueError('Resolved nonnull ability definition required')
        if self.definition.effect_tag != 0 or self.definition.execution_kind not in (0, 2):
            raise UnresolvedCast('Learned dispatcher effect/execution branch remains unresolved')


@dataclass(frozen=True)
class OwnedSources135:
    item_effects: tuple
    definitions: tuple
    other_sources_absent: bool
    extra_casts1596: int = 0

    def __post_init__(self):
        if type(self.item_effects) is not tuple or type(self.definitions) is not tuple:
            raise TypeError('Explicit ordered source snapshots required')
        if self.item_effects or self.definitions or self.other_sources_absent is not True or self.extra_casts1596 != 0:
            raise UnresolvedCast('Item/prelude/proc source continuation remains unresolved')


@dataclass(frozen=True)
class OwnedTickResult135:
    state: object
    entries: tuple
    basic: OwnedEntry135
    cast_results: tuple
    basic_result: object
    cooldown_events: tuple
    refresh_flag772: int
    prelude: object


def _floor_cooldown(state, entry):
    definition, owned = entry.definition, entry.record
    floor = 0x3f000000 if definition.ability_id == b'hellfire' else 0x3e800000
    value = f.mul(definition.cooldown_bits, 0x3fb33333)
    value = f.mul(value, owned.cooldown_bits)
    value = f.mul(value, owned.additional_cooldown_bits)
    value = f.mul(value, state.cooldown_multiplier_bits)
    # Original ordered selects implement numeric max, with NaN replaced by
    # the finite floor. Keep the first argument on equality, including zeros.
    value = floor if f.is_nan(value) else value
    return value if f.to_float(value) > f.to_float(floor) else floor


def _milliseconds(bits):
    value = f.to_float(f.mul(bits, 0x447a0000))
    if not value > 0:
        return 0
    return f.MASK if value >= 4294967295 else int(value)


def tick_owned(state, entries, basic, dt_bits, *, sources,
               class_byte, timer1628_bits, refresh_flag772=0,
               after_hit=None, after_death=None):
    """Forward learned entries, then basic attack; preserve HP/RNG hit order.

    Owned countdown uses ``not >0``; basic countdown uses ``<=0``. Consequently
    NaN attempts an owned cast but does not attempt a basic cast. Failures retry
    after0.2 and0.5 respectively. Successful common casts have a0.25 floor
    (hellfire0.5), and create two original cooldown/activation packets. The
    physical packet encoding is not projected by this result.
    """
    if not isinstance(sources, OwnedSources135):
        raise TypeError('Explicit resolved prelude/proc sources required')
    if refresh_flag772 != 0:
        raise UnresolvedCast('Requested26366 cooldown-refresh packet projection is unresolved')
    if state.context908 != 0:
        raise UnresolvedCast('Inherited proc-cast context remains unresolved')
    entries = tuple(entries)
    if any(not isinstance(entry, OwnedEntry135) for entry in entries) or not isinstance(basic, OwnedEntry135):
        raise TypeError('Ordered learned entries and a real basic entry required')
    prelude = tick_class_prelude(state, class_byte, timer1628_bits, dt_bits,
        after_hit=after_hit, after_death=after_death)
    state = prelude.state
    updated, results, events = [], [], []
    for entry in entries:
        remaining = f.sub(entry.record.remaining_cooldown_bits, dt_bits)
        result = None
        if not f.to_float(remaining) > 0:
            #1076 writes infinity before copying the80B record into922.
            casting = replace(entry.record, remaining_cooldown_bits=f.INF)
            result = cast_ability(state, entry.definition, casting,
                after_hit=after_hit, after_death=after_death)
            state = result.state
            remaining = _floor_cooldown(state, entry) if result.success else 0x3e4ccccd
            if result.success:
                events.append((entry.definition.spell_id, remaining, _milliseconds(remaining)))
        updated.append(replace(entry, record=replace(entry.record, remaining_cooldown_bits=remaining)))
        results.append(result)
    remaining = f.sub(basic.record.remaining_cooldown_bits, dt_bits)
    basic_result = None
    if f.to_float(remaining) <= 0:
        basic_result = cast_ability(state, basic.definition,
            replace(basic.record, remaining_cooldown_bits=remaining),
            after_hit=after_hit, after_death=after_death)
        state = basic_result.state
        remaining = _floor_cooldown(state, basic) if basic_result.success else 0x3f000000
        if basic_result.success:
            events.append((basic.definition.spell_id, remaining, _milliseconds(remaining)))
    basic = replace(basic, record=replace(basic.record, remaining_cooldown_bits=remaining))
    return OwnedTickResult135(state, tuple(updated), basic, tuple(results), basic_result,
        tuple(events), 0, prelude)
