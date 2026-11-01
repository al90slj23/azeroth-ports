"""Recovered 0.126.0 owned-ability mutation, independently implemented.

This module never loads the original WASM. It models the 80-byte owned record,
1065's existing-ability upgrade loop, and explicit selection control boundaries.
The full 1065 postprocessing, talent calculation26840 and rarity helper26457
are not silently replaced: callers must supply their results or handle pending
effects. All floating fields are raw binary32 words; integer fields are u32.
"""
from dataclasses import dataclass, replace
import struct

from . import binary32 as f
from .upgrade_values import UpgradeState, upgrade_value_bits

ONE = 0x3f800000


class UnresolvedAbilityEffect(NotImplementedError):
    """An original helper result is required to proceed faithfully."""


@dataclass(frozen=True)
class AbilityDefinition:
    pointer: int
    ability_id: bytes
    execution_kind: int


@dataclass(frozen=True)
class AbilityRecord:
    definition_pointer: int
    level: int = 1
    remaining_cooldown_bits: int = 0x3f000000
    damage_bits: int = ONE
    cooldown_bits: int = ONE
    extra_targets: int = 0
    area_bits: int = ONE
    duration_bits: int = ONE
    counts: tuple = (0, 0, 0, 0, 0)
    additional_damage_bits: int = ONE
    additional_cooldown_bits: int = ONE
    additional_targets: int = 0
    additional_area_bits: int = ONE
    additional_duration_bits: int = ONE
    life_damage_bits: int = 0
    field76_bits: int = ONE

    def words(self):
        if len(self.counts) != 5:
            raise ValueError('The owned record has five upgrade counters')
        return (self.definition_pointer, self.level, self.remaining_cooldown_bits,
                self.damage_bits, self.cooldown_bits, self.extra_targets,
                self.area_bits, self.duration_bits, *self.counts,
                self.additional_damage_bits, self.additional_cooldown_bits,
                self.additional_targets, self.additional_area_bits,
                self.additional_duration_bits, self.life_damage_bits, self.field76_bits)

    def to_bytes(self):
        return struct.pack('<20I', *(word & f.MASK for word in self.words()))

    @classmethod
    def from_bytes(cls, raw):
        if len(raw) != 80:
            raise ValueError('An owned ability record is exactly 80 bytes')
        words = struct.unpack('<20I', raw)
        return cls(*words[:8], tuple(words[8:13]), *words[13:])


@dataclass(frozen=True)
class UpgradeCard:
    owned_index: int
    kinds: tuple
    tier: int

    @classmethod
    def from_candidate_bytes(cls, raw, read_memory):
        """Decode the existing-ability variant of an original 80B candidate.

        read_memory(address, length) must return bytes from a caller-owned
        memory snapshot. Candidate+60 is a niche discriminant, NOT ability ID.
        Nonnegative tags and0x80000001 select the existing-ability branch;
        the latter is a reserved/niche encoding, not a normal Vec capacity.
        """
        if len(raw) != 80:
            raise ValueError('A candidate record is exactly 80 bytes')
        tag, kinds_pointer, count, owned_index, tier = struct.unpack_from('<5I', raw, 60)
        if tag & 0x80000000 and tag != 0x80000001:
            raise ValueError('Candidate is not the existing-ability variant')
        if count & 0x80000000:
            raise ValueError('Original vector allocation rejects this signed length')
        kinds = bytes(read_memory(kinds_pointer, count))
        if len(kinds) != count:
            raise ValueError('Candidate kinds snapshot is truncated')
        return cls(owned_index, tuple(kinds), tier)


@dataclass(frozen=True)
class NewAbilityCard:
    ability_id: bytes
    tier: int

    @classmethod
    def from_candidate_bytes(cls, raw, read_memory):
        """Decode the canonical new-ability niche tag0x80000000."""
        if len(raw) != 80:
            raise ValueError('A candidate record is exactly80 bytes')
        tag, pointer, length, _, tier = struct.unpack_from('<5I', raw, 60)
        if tag != 0x80000000:
            raise ValueError('Candidate is not the canonical new-ability variant')
        identifier = bytes(read_memory(pointer, length))
        if len(identifier) != length:
            raise ValueError('Candidate identifier snapshot is truncated')
        return cls(identifier, tier)


def _trunc_sat_u32(bits):
    value = f.to_float(bits)
    if not value > 0:  # NaN and negative values, including -Inf.
        return 0
    if value >= 4294967295:
        return f.MASK
    return int(value)


def apply_upgrade_card(record, card, definition):
    """Return the mutated owned record; apply every kind in its listed order.

    This is the numeric loop in1065, excluding candidate cleanup/postprocessing.
    level and counts wrap modulo2**32, as do original i32.add operations. Tier
    and kind validation cover the supported 25242 domain; invalid input raises.
    An empty kinds vector does not inspect tier and leaves the record unchanged.
    """
    if record.definition_pointer != definition.pointer:
        raise ValueError('Owned record and supplied definition differ')
    result = record
    for kind in card.kinds:
        if kind not in range(5):
            raise ValueError('Recovered upgrade kinds are 0..4')
        level = (result.level + 1) & f.MASK
        result = replace(result, level=level)
        state = UpgradeState(result.counts, result.cooldown_bits,
                             result.extra_targets, result.area_bits,
                             result.duration_bits, definition.execution_kind,
                             definition.ability_id)
        value = upgrade_value_bits(kind, card.tier, state)
        if kind == 0:
            result = replace(result, damage_bits=f.mul(f.add(value, ONE), result.damage_bits))
        elif kind == 1:
            result = replace(result, cooldown_bits=f.sub(result.cooldown_bits, value))
        elif kind == 2:
            result = replace(result, extra_targets=(result.extra_targets + _trunc_sat_u32(value)) & f.MASK)
        elif kind == 3:
            result = replace(result, area_bits=f.add(value, result.area_bits))
        else:
            result = replace(result, duration_bits=f.add(value, result.duration_bits))
        counts = list(result.counts)
        counts[kind] = (counts[kind] + 1) & f.MASK
        denominator = f.add(f.mul(f.from_u32(max(0, level - 2)), 0x3e000000), ONE)
        factor = f.add(f.div(0x3d23d70a, denominator), ONE)
        result = replace(result, counts=tuple(counts), damage_bits=f.mul(factor, result.damage_bits))
    return result


def initialize_ability(definition, *, tier=0, additional=None):
    """Build1065's new 80B record from an explicit 26840 result.

    additional is exactly28B (fields52..79) returned by the recovered talent
    calculation. Pass neutral_additional_bytes() only when the caller has
    established an empty modifier vector. Nonzero tier requires26457 and raises.
    Initialization starts cooldown at0.5, unlike a generic all-zero record.
    """
    if additional is None:
        raise UnresolvedAbilityEffect('Need explicit28B talent/helper26840 result')
    if len(additional) != 28:
        raise ValueError('Additional fields52..79 are exactly28 bytes')
    if tier != 0:
        raise UnresolvedAbilityEffect('Nonzero new-ability tier requires helper26457')
    base = AbilityRecord(definition.pointer).to_bytes()
    return AbilityRecord.from_bytes(base[:52] + additional)


def neutral_additional_bytes():
    """26840's result when its modifier vector is empty (not a default claim)."""
    return struct.pack('<7I', ONE, ONE, 0, ONE, ONE, 0, ONE)


@dataclass(frozen=True)
class SelectionState:
    owned: tuple = ()
    candidates: tuple = ()
    phase2299: int = 2
    selection_kind2297: int = 0


@dataclass(frozen=True)
class SelectionResult:
    state: SelectionState
    accepted: bool
    owned_index: int | None = None
    pending_effects: tuple = ()


POSTPROCESS_EFFECTS = ('1065 shared talent/notification/equipment postprocessing',
                       '1573 derived-stat rebuild', '4595 selection completion')


def accept_upgrade_selection(state, index, definitions):
    """Apply1065's entry guards and owned-record update, exposing remaining work.

    definitions maps definition_pointer to AbilityDefinition. An out-of-range
    owned index is a no-op mutation, but1065 still runs shared postprocessing.
    Phase/pending queues remain unchanged until the explicit effects are handled.
    """
    if (state.phase2299 != 2 or not 0 <= index < len(state.candidates)
            or state.selection_kind2297 == 255):
        return SelectionResult(state, False)
    card = state.candidates[index]
    if not isinstance(card, UpgradeCard):
        raise UnresolvedAbilityEffect('This selection API covers existing-ability cards')
    owned = list(state.owned)
    if 0 <= card.owned_index < len(owned):
        record = owned[card.owned_index]
        owned[card.owned_index] = apply_upgrade_card(record, card, definitions[record.definition_pointer])
    return SelectionResult(replace(state, owned=tuple(owned)), True,
                           card.owned_index, POSTPROCESS_EFFECTS)


def accept_new_ability_selection(state, index, definitions, *, additional=None):
    """Append the tier0 new owned record, with explicit remaining1065 effects.

    definitions maps the string bytes ID to AbilityDefinition. The caller must
    resolve26840 and pass its28B result; nonzero rarity remains an explicit error.
    The original lookup scans all113 definitions by ID, rather than spellID.
    """
    if (state.phase2299 != 2 or not 0 <= index < len(state.candidates)
            or state.selection_kind2297 == 255):
        return SelectionResult(state, False)
    card = state.candidates[index]
    if not isinstance(card, NewAbilityCard):
        raise UnresolvedAbilityEffect('This selection API covers new-ability cards')
    definition = definitions[card.ability_id]
    if definition.ability_id != card.ability_id:
        raise ValueError('Definition lookup and selected string ID differ')
    record = initialize_ability(definition, tier=card.tier, additional=additional)
    return SelectionResult(replace(state, owned=state.owned + (record,)), True,
                           len(state.owned),
                           ('1065 new-ability spell notification',) + POSTPROCESS_EFFECTS)


@dataclass(frozen=True)
class CompletionDecision:
    pending2088: int
    pending2092: int
    pending2096: int
    flag2293: int
    next_selection_kind: int | None
    phase2299: int
    selection_kind2297: int
    candidates_cleared: bool = True
    pending_effects: tuple = ()


def selection_completion_control(*, entry_kind, pending2088, pending2092,
                                 pending2096, flag2293=0, flag2284=0,
                                 flag2285=0, loot_collection_complete=False):
    """4595 control subset, after explicitly completing its loot pass.

    4595 decrements first, clears candidate vector, collects nearby XP loot, and
    THEN chooses the next queue. XP collection can add queue entries: the caller
    must supply post-loot pending counts with entry decrement already reflected
    by setting entry_kind=None, or prove the loot pass made no changes and pass
    the original entry kind. No original helper execution is implied.
    """
    if not loot_collection_complete:
        raise UnresolvedAbilityEffect('4595 loot pass must be resolved before queue decision')
    counts = [pending2088 & f.MASK, pending2092 & f.MASK, pending2096 & f.MASK]
    if entry_kind is not None:
        kind = entry_kind & 255
        slot = kind if kind in (1, 2) else 0
        counts[slot] -= int(counts[slot] != 0)
        if slot == 0:
            flag2293 = 1
    next_kind = (1 if counts[1] else 2 if counts[2] else
                 0 if counts[0] and not (flag2284 == 1 and flag2285 & 1) else None)
    if next_kind is None:
        effects = ('4595 clear2285/2297, resume25345 in mode0, effect1020 and notifications',)
        return CompletionDecision(*counts, flag2293, None, 1, 255, pending_effects=effects)
    return CompletionDecision(*counts, flag2293, next_kind, 2, next_kind,
                              pending_effects=('2098 generate next candidates with enter_now=0',))
