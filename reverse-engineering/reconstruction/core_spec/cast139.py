"""Independent current139 normal-target cleave, full922 numeric projection.

Explicit432B units/80B owned records and resolved88B definition are inputs.
This module reads no program, assets, memory snapshot or validation outputs.
The cleave306 launch envelope is modeled. Damage/HP packet envelopes, physical
containers, nonempty proc sources, other execution kinds, accepted-hit effects
and death are not silently replaced.
"""
from dataclasses import dataclass, replace
import struct

from . import binary32 as f
from .combat139 import DamageState139, resolve_damage139, PendingDamage139
from .rng import next_u32_words


class PendingCast139(NotImplementedError):
    pass


def u32(row, offset):
    return struct.unpack_from('<I', row, offset)[0]


def guid139(row):
    return struct.unpack_from('<Q', row, 112)[0]


def _finite(word):
    return (word & 0x7fffffff) < 0x7f800000


@dataclass(frozen=True)
class CleaveDefinition139:
    pointer: int
    ability_id: bytes
    raw88: bytes

    def __post_init__(self):
        if (self.pointer <= 0 or self.ability_id != b'cleave'
                or type(self.raw88) is not bytes or len(self.raw88) != 88
                or u32(self.raw88, 0) != 0 or self.raw88[84] != 5
                or u32(self.raw88, 44) != 845):
            raise PendingCast139('Only actual139 cleave execution5/effect0/spell845')


@dataclass(frozen=True)
class CleaveState139:
    combat: DamageState139
    player_xyz: tuple
    max_hp_bits: int
    damage_multiplier_bits: int
    critical_chance_bits: int
    critical_multiplier_bits: int
    extra_targets: int
    spell_sets: tuple = ((), (), ())
    suppress_primary_attempt: bool = False
    source_id: int = 999

    def __post_init__(self):
        if not isinstance(self.combat, DamageState139):
            raise TypeError('Typed current139 damage source contract required')
        if len(self.player_xyz) != 3 or not all(_finite(v) for v in self.player_xyz):
            raise PendingCast139('Finite explicit player XYZ required')
        if any(not _finite(v) for v in (self.max_hp_bits,
                self.damage_multiplier_bits, self.critical_chance_bits,
                self.critical_multiplier_bits, self.combat.now_bits)):
            raise PendingCast139('Nonfinite cast parameters pending')
        if not 0 <= self.extra_targets <= f.MASK:
            raise ValueError('extra_targets is u32')
        if type(self.source_id) is not int or not 0 <= self.source_id < 1 << 64:
            raise ValueError('Explicit source GUID is u64')
        if (len(self.spell_sets) != 3 or any(type(x) is not tuple
                or len(x) != len(set(x)) or len(x) > 64
                or any(type(y) is not int or not 0 <= y <= f.MASK for y in x)
                for x in self.spell_sets)):
            raise ValueError('Three explicit ordered unique spell sets required')
        for row in self.combat.units432:
            if (any(u32(row, o) != f.MASK for o in (40, 64, 244))
                    or row[424] not in (0, 1)):
                raise PendingCast139('Only normal kind/header -1 and class424=0/1')
            if any(not _finite(u32(row, o)) for o in
                    (288, 316, 320, 328, 332, 340, 344, 380)):
                raise PendingCast139('Finite target geometry/HP required')


def position139(row, now_bits):
    """Ordered current20123 interpolation; only XY affects radius/near tests."""
    duration = u32(row, 344)
    if f.to_float(duration) <= 0:
        return u32(row, 328), u32(row, 332)
    t = f.div(f.sub(now_bits, u32(row, 340)), duration)
    if f.to_float(t) < 0:
        t = 0
    if f.to_float(t) > 1:
        t = 0x3f800000
    return tuple(f.add(u32(row, start),
        f.mul(f.sub(u32(row, stop), u32(row, start)), t))
        for start, stop in ((316, 328), (320, 332)))


def _distance(a, b):
    x, y = f.sub(a[0], b[0]), f.sub(a[1], b[1])
    return f.add(f.mul(x, x), f.mul(y, y))


def _total_key(word):
    return ~word & f.MASK if word & f.SIGN else word | f.SIGN


def cleave_targets139(state, radius_bits):
    """27754 distance order,8673 priorities and ordinary near6/HP order.

    Normal targets only: classification424=1 precedes ordinary424=0;
    active priority380 defers either. Equal distance/priority/HP stay stable.
    """
    square = f.mul(radius_bits, radius_bits)
    rows = [row for row in state.combat.units432 if u32(row, 0) == 0
        and f.to_float(_distance(position139(row, state.combat.now_bits),
            state.player_xyz[:2])) <= f.to_float(square)]
    rows.sort(key=lambda row: _total_key(_distance(
        position139(row, state.combat.now_bits), state.player_xyz[:2])))
    def priority(row):
        return 3 if f.to_float(state.combat.now_bits) < f.to_float(u32(row, 380)) else 2-row[424]
    rows.sort(key=priority)
    prefix = [row for row in rows if priority(row) < 2]
    ordinary = [row for row in rows if priority(row) == 2]
    deferred = [row for row in rows if priority(row) == 3]
    if ordinary:
        anchor = position139(ordinary[0], state.combat.now_bits)
        near, far = [], []
        for row in ordinary:
            distance = _distance(position139(row, state.combat.now_bits), anchor)
            (near if f.to_float(distance) <= 36 else far).append(row)
        near.sort(key=lambda row: _total_key(u32(row, 288)))
        ordinary = near + far
    return tuple(guid139(row) for row in prefix + ordinary + deferred)


@dataclass(frozen=True)
class CleaveResult139:
    state: CleaveState139
    success: int
    selected_ids: tuple
    base_damage_bits: int
    hits: tuple
    owned80: bytes
    launch306_hex: str | None


def _packed_guid(value):
    raw = struct.pack('<Q', value)
    mask = sum((byte != 0) << index for index, byte in enumerate(raw))
    return bytes((mask,)) + bytes(byte for byte in raw if byte)


def cleave_launch306139(source_id, spell_id, targets):
    """10490's declared zero-extra/target-tag0 cleave launch packet.

    This is one packet envelope only; damage592 and HP169 remain separate.
    """
    if not targets or len(targets) > 64:
        raise ValueError('Nonempty bounded ordered target IDs required')
    return (_packed_guid(source_id) * 2 + struct.pack('<IH', spell_id, 256)
        + bytes((len(targets),)) + b''.join(struct.pack('<Q', x) for x in targets)
        + b'\x00' + struct.pack('<H', 2) + _packed_guid(targets[0])).hex()


def cast_cleave139(state, definition, owned80):
    if not isinstance(state, CleaveState139) or not isinstance(definition, CleaveDefinition139):
        raise TypeError('Explicit current139 cast state and definition required')
    if type(owned80) is not bytes or len(owned80) != 80 or u32(owned80, 0) != definition.pointer:
        raise ValueError('Matching explicit complete80B owned record required')
    if any(not _finite(u32(owned80, o)) for o in (12, 52, 72)):
        raise PendingCast139('Nonfinite owned multipliers pending')
    raw = definition.raw88
    # The current type5 coefficient in table1601276 is exactly1.
    value = f.mul(u32(raw, 48), 0x3fb33333)
    value = f.mul(value, u32(owned80, 12))
    value = f.mul(value, u32(owned80, 52))
    value = f.mul(value, 0x3f800000)
    life = f.mul(state.max_hp_bits, u32(owned80, 72)) if f.to_float(u32(raw, 48)) > 0 else 0
    base = f.mul(state.damage_multiplier_bits, f.add(value, life))
    spell = u32(raw, 44)
    updated = []
    for index, values in enumerate(state.spell_sets):
        updated.append(values if spell in values or index == 2 and state.suppress_primary_attempt
            else values + (spell,))
    state = replace(state, spell_sets=tuple(updated))
    count = 1 if u32(raw, 64) == 0 else max(1,
        (u32(raw, 64)+u32(owned80, 60)+u32(owned80, 20)+state.extra_targets) & f.MASK)
    selected = cleave_targets139(state, u32(raw, 56))[:count]
    hits = []
    for target in selected:
        word, words = next_u32_words(state.combat.rng_words)
        chance = f.add(0, state.critical_chance_bits)
        critical = int(f.to_float(chance) > f.to_float(f.mul(f.from_u32(word >> 8), 0x33800000)))
        damage = f.mul(base, state.critical_multiplier_bits) if critical else base
        combat = replace(state.combat, rng_words=words)
        result = resolve_damage139(combat, target, damage, spell_id=spell,
            school=raw[85], critical=critical, context=0)
        state = replace(state, combat=result.state)
        hits.append((target, damage, critical, result.new_hp_bits))
    return CleaveResult139(state, int(bool(selected)), selected, base,
        tuple(hits), owned80,
        cleave_launch306139(state.source_id, spell, selected) if selected else None)
