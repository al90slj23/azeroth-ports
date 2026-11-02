"""Current139 execution2/effect1 Thunder Clap over actual known/None owners.

This is a direct922 component, not the1238 scheduler. Current922 applies913
then2189 synchronously per target; it does not enqueue1775 hits or3755 areas.
Ordinary damage/death is composed from its separately recovered139 rules.
"""
from dataclasses import dataclass, replace
import struct
from . import binary32 as f
from .death139 import (OrdinaryDamageState139, word139, guid139, position3_139,
                       resolve_ordinary_damage139)
from .rng import next_u32_words
from .radius import radius_bits


def thunder_launch306139(source_id, spell, targets):
    """10490 area variant2: ordered target list, targetmask0, no targetGUID."""
    raw = struct.pack('<Q', source_id)
    packed = bytes([sum((v != 0) << i for i, v in enumerate(raw))]) + bytes(v for v in raw if v)
    return (packed*2 + struct.pack('<IH', spell, 256) + bytes([len(targets)])
        + b''.join(struct.pack('<Q', v) for v in targets) + b'\x00\x00\x00').hex()


class PendingThunderClap139(NotImplementedError):
    pass


@dataclass(frozen=True)
class ThunderClapDefinition139:
    pointer: int
    raw88: bytes

    def __post_init__(self):
        r = self.raw88
        if (self.pointer != 5882916 or type(r) is not bytes or len(r) != 88
                or word139(r, 0) != 1 or r[84] != 2 or r[85] != 0
                or word139(r, 44) != 6343):
            raise PendingThunderClap139('Only current139 exec2/effect1/spell6343')


def _distance(a, b):
    x, y = f.sub(a[0], b[0]), f.sub(a[1], b[1])
    return f.add(f.mul(x, x), f.mul(y, y))


def _total_key(v):
    return ~v & f.MASK if v & f.SIGN else v | f.SIGN


def targets_thunder_clap139(records, player_xyz, now_bits, radius):
    """Actual27754 marker0/inclusive XY radius and stable distance order."""
    square = f.mul(radius, radius)
    rows = []
    for row in records:
        if word139(row, 0) == 0:
            distance = _distance(position3_139(row, now_bits), player_xyz)
            if f.to_float(distance) <= f.to_float(square):
                rows.append((distance, guid139(row)))
    rows.sort(key=lambda v: _total_key(v[0]))
    return tuple(v[1] for v in rows)


def _slow139(state, target, strength, duration):
    #2189 checks the real36B source owner, then scans first marker!=1 GUID.
    if state.sources.hit_sources.event_definitions36.count != 0:
        raise PendingThunderClap139('Nonempty effect49 source pending')
    for index, row in enumerate(state.records432):
        if guid139(row) == target and word139(row, 0) != 1:
            if word139(row, 376) != 0:
                raise PendingThunderClap139('Existing slow spell376 removal4593 pending')
            expiry = f.add(state.now_bits, duration)
            updated = list(row)
            for offset, value in ((124, expiry), (120, strength), (376, 0)):
                updated[offset:offset+4] = struct.pack('<I', value)
            records = list(state.records432)
            records[index] = tuple(updated)
            return replace(state, records432=tuple(records)), (
                (target, 124, expiry), (target, 120, strength), (target, 376, 0))
    return state, ()


@dataclass(frozen=True)
class ThunderClapResult139:
    state: OrdinaryDamageState139
    spell_sets: tuple
    success: int
    selected_ids: tuple
    base_damage_bits: int
    radius_bits: int
    owned80: bytes
    hits: tuple
    effect_writes: tuple
    known_packets: tuple
    enqueued_pending_hits: tuple = ()
    enqueued_areas: tuple = ()
    physical_packet_stream_complete: bool = False


def cast_thunder_clap139(state, player_xyz, derived, definition, owned80,
                        spell_sets, world, *, source_id=0,
                        suppress_primary_attempt=False, context908=0):
    """Full known922 area2 damage/effect branch with real ordinary death.

    The caller must provide actual inherited source owners. Unsupported slow
    spell removal, proc sources and target kinds stop explicitly. No NPC or
    live record is removed to make the source contract fit.
    """
    if not isinstance(state, OrdinaryDamageState139):
        raise TypeError('Actual ordinary139 damage/source/pickup owner required')
    if not isinstance(definition, ThunderClapDefinition139):
        raise TypeError('Bound current139 Thunder Clap declaration required')
    if (type(owned80) is not bytes or len(owned80) != 80
            or word139(owned80, 0) != definition.pointer):
        raise ValueError('Actual complete selected80B owned record required')
    if context908:
        raise PendingThunderClap139('Inherited proc context pending')
    if len(player_xyz) != 3 or any(f.is_nan(v) or f.is_inf(v) for v in player_xyz):
        raise PendingThunderClap139('Finite actual playerXYZ required')
    scan = state.sources.hit_sources.owned_execution_scan
    if (scan.definition_pointers != (5882740, 5882916)
            or scan.execution_bytes84 != (5, 2)
            or not scan.execution11_arm_skipped):
        raise PendingThunderClap139('Actual cleave+selected thunder owned source required')
    raw = definition.raw88
    value = f.mul(word139(raw, 48), 0x3fb33333)
    value = f.mul(value, word139(owned80, 12))
    value = f.mul(value, word139(owned80, 52))
    value = f.mul(value, 0x3f000000)  #current table1601276, execution2 coefficient
    life = f.mul(derived['1536'], word139(owned80, 72)) if f.to_float(word139(raw, 48)) > 0 else 0
    base = f.mul(derived['1540'], f.add(value, life))
    radius = f.mul(word139(owned80, 24), word139(owned80, 64))
    radius = f.mul(word139(raw, 60), radius)
    radius = radius_bits(f.mul(derived['1580'], radius))
    selected = targets_thunder_clap139(state.records432, player_xyz, state.now_bits, radius)
    spell = word139(raw, 44)
    sets = [tuple(v) for v in spell_sets]
    if len(sets) != 3 or any(len(v) != len(set(v)) for v in sets):
        raise ValueError('Three actual ordered unique spell sets required')
    for index in range(3):
        if not (index == 2 and suppress_primary_attempt) and spell not in sets[index]:
            sets[index] += (spell,)
    hits, writes, packets = [], [], []
    #Area variant2 is mask0; cleave's variant0 instead has mask2/firstGUID.
    if selected:
        packets.append((306, thunder_launch306139(source_id, spell, selected)))
    duration = f.mul(word139(raw, 8), word139(owned80, 68))
    for target in selected:
        sample, words = next_u32_words(state.rng_words)
        roll = f.mul(f.from_u32(sample >> 8), 0x33800000)
        critical = int(f.to_float(derived['1548']) > f.to_float(roll))
        amount = f.mul(base, derived['1552']) if critical else base
        result = resolve_ordinary_damage139(replace(state, rng_words=words), target,
            amount, world, spell_id=spell, school=raw[85], critical=critical)
        state = result.state
        packets.extend(result.known_packets)
        state, effect = _slow139(state, target, word139(raw, 4), duration)
        writes.extend(effect)
        hits.append((target, amount, critical, result))
    return ThunderClapResult139(state, tuple(sets), int(bool(selected)), selected,
        base, radius, owned80, tuple(hits), tuple(writes), tuple(packets))
