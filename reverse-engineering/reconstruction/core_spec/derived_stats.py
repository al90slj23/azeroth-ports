"""Independent ordered binary32 projection of original attribute recalculation1573.

The production model never reads the original WASM, WAT, SQLite index or saves.
All scalar floats are unsigned binary32 bit patterns, including modifier values.
The source domains deliberately retain separate tag spaces. Unknown identifiers
remain raw IDs; this does not invent equipment, talent or spell producers.
Object-field values and a movement-update decision are returned as data; actual
allocation, BTree insertion, queue serialization and networking are excluded.
"""
from dataclasses import dataclass, field
import math

from .binary32 import MASK, SIGN, add, sub, mul, div, from_u32, from_float, is_nan, to_float
from .progression import trunc_sat_u32

Z, ONE = 0, 0x3f800000
TWO, NINE = 0x40000000, 0x41100000

# Exact static record values, independently transcribed from immutable evidence.
CLASS_HP_ARMOR = {
    1: (0x43660000, 0x3e6147ae), 2: (0x43750000, 0x3e4ccccd),
    3: (0x43700000, 0x3e23d70a), 4: (0x433e0000, 0x3e3851ec),
    5: (0x432a0000, 0x3da3d70a), 7: (0x43430000, 0x3e2e147b),
    8: (0x43570000, 0x3da3d70a), 9: (0x43250000, 0x3d75c28f),
    11: (0x434d0000, 0x3df5c28f),
}
RACE_MODIFIERS = {
    1: ((8, 0x3dcccccd), (9, 0x3e4ccccd)), 2: ((0, 0x3dcccccd),),
    3: ((1, 0x3d75c28f), (7, 0x3e99999a)),
    4: ((3, 0x3da3d70a), (5, 0x3d4ccccd)),
    5: ((11, ONE), (5, 0x3d23d70a)), 6: ((0, 0x3e19999a),),
    7: ((2, 0x3da3d70a), (10, 0x3e4ccccd)),
    8: ((6, 0x3fc00000), (4, 0x3cf5c28f)),
}


def _u32(value):
    if type(value) is not int or not 0 <= value <= MASK:
        raise ValueError('Expected an unsigned 32-bit integer or binary32 bits')
    return value


def _lt(a, b): return to_float(a) < to_float(b)
def _gt(a, b): return to_float(a) > to_float(b)
def _le(a, b): return to_float(a) <= to_float(b)
def _eq(a, b): return to_float(a) == to_float(b)


def _min_select(a, b):
    """Original select sequence: NaN-aware min, choosing b on equal zeros."""
    x = b if is_nan(a) else a
    y = x if is_nan(b) else b
    return x if _lt(x, y) else y


def _max_select(a, b):
    """Original select sequence: NaN-aware max, choosing b on equal zeros."""
    x = b if is_nan(a) else a
    y = x if is_nan(b) else b
    return x if _gt(x, y) else y


def _ceil(bits):
    value = to_float(bits)
    if not math.isfinite(value) or value == 0:
        return bits
    rounded = math.ceil(value)
    return SIGN if rounded == 0 and bits & SIGN else from_float(rounded)


@dataclass(frozen=True)
class Modifier:
    tag: int
    value_bits: int


@dataclass(frozen=True)
class Adjustment:
    """16B entry: tag comes from definition+36, auxiliary from definition+32."""
    tag: int
    value_bits: int
    definition32_bits: int = Z


@dataclass(frozen=True)
class TimedRecord:
    definition_index: int
    stack_count: int
    expires_bits: int


@dataclass(frozen=True)
class TimedDefinition:
    kind: int
    value20_bits: int
    modifier_tag: int


@dataclass(frozen=True)
class LiveEffect:
    """32B entry: type+8, value+12, spellID+20, expiry+24."""
    kind: int
    value_bits: int
    spell_id: int
    expires_bits: int


@dataclass
class StatsInput:
    class_byte: int = 1
    race_byte: int = 1
    level: int = 1
    old_max_hp_bits: int = Z
    current_hp_bits: int = Z
    now_bits: int = Z
    previous_speed_bits: int = 0x40e00000
    conditional268_bits: int = Z
    flag2294: int = 0
    passives: list[Modifier] = field(default_factory=list)
    adjustments: list[Adjustment] = field(default_factory=list)
    item_modifiers: list[Modifier] = field(default_factory=list)
    # Exact 9-byte ID and u8 rank; caller owns the source definitions.
    owned_skills: list[tuple[str, int]] = field(default_factory=list)
    timed_records: list[TimedRecord] = field(default_factory=list)
    timed_definitions: list[TimedDefinition] = field(default_factory=list)
    live_effects: list[LiveEffect] = field(default_factory=list)


def recalculate(state: StatsInput):
    """Return the 22 derived stores, current HP, object fields and speed decision.

    The original's byte-selector and modulo-u32 behaviors are preserved. Every
    arithmetic instruction rounds through binary32.py. NaN payloads may differ
    from a particular WASM engine and must be compared by NaN classification.
    """
    for value in (state.level, state.old_max_hp_bits, state.current_hp_bits,
                  state.now_bits, state.previous_speed_bits, state.conditional268_bits):
        _u32(value)
    class_key = state.class_byte & 255
    hp, armor = CLASS_HP_ARMOR.get(class_key, CLASS_HP_ARMOR[1])
    race = RACE_MODIFIERS.get(state.race_byte & 255, RACE_MODIFIERS[1])
    n = add(from_u32(state.level), 0xbf800000)
    # Locals retain their original indices to make separate domains auditable.
    f = {i: Z for i in range(21, 52)}
    f.update({22: armor, 24: ONE, 25: ONE, 26: 0x3d4ccccd,
              27: ONE, 28: add(mul(n, 0x3cf5c28f), ONE), 29: NINE,
              31: add(mul(n, 0x3da3d70a), 0x3f4ccccd), 32: TWO,
              33: ONE, 35: ONE, 41: n, 49: hp})
    integer17 = 0
    def accum(local, value): f[local] = add(f[local], value)
    for tag, value in race:
        local = {0:25, 1:28, 2:30, 3:24, 4:26, 5:22, 6:31,
                 8:33, 9:27, 10:36, 11:38}.get(tag, 25)
        if tag == 7: f[29] = mul(f[29], add(value, ONE))
        else: accum(local, value)
    for entry in state.passives:
        tag, value = _u32(entry.tag), _u32(entry.value_bits)
        if tag == 8: f[29] = mul(f[29], add(value, ONE))
        elif tag == 11: integer17 = (integer17 + value) & MASK
        else:
            accum({0:28,1:30,2:42,3:26,4:32,5:24,6:22,7:31,
                   9:27,10:35,12:39,13:43,14:44}.get(tag, 28), value)
    for entry in state.adjustments:
        tag, value = _u32(entry.tag) & 255, _u32(entry.value_bits)
        if tag in (16, 18): continue
        if tag == 5:
            # Preserve old armor before the temporary local22 overwrite.
            f[22] = add(f[22], _min_select(value, mul(entry.definition32_bits, 0x40400000)))
            accum(25, mul(value, 0x40800000))
        elif tag == 6:
            f[22] = add(f[22], _min_select(mul(value, 0x3e23d70a), 0x3df5c28f))
            accum(25, value)
        elif tag == 11: f[29] = mul(f[29], add(value, ONE))
        else:
            accum({0:28,1:30,2:25,3:26,4:32,7:31,8:35,9:39,
                   10:24,12:33,13:27,14:36,15:38,17:40,19:23}.get(tag,28),value)
    f[50] = _min_select(f[23], 0x3ecccccd) if state.adjustments else Z
    f[23], f[37] = 0x3f19999a, Z
    temporary = list(state.item_modifiers)
    tag32_sum = SIGN  # Original reduction starts at negative zero.
    for entry in state.item_modifiers:
        if (_u32(entry.tag) & 255) == 32: tag32_sum = add(tag32_sum, _u32(entry.value_bits))
    if _gt(tag32_sum, Z):
        # The first matching soul_link determines whether a modifier is appended.
        for identifier, rank in state.owned_skills:
            if identifier == 'soul_link':
                if rank & 255: temporary.append(Modifier(5, mul(from_u32(rank & 255), 0x3c23d70a)))
                break
    for record in state.timed_records:
        if _le(record.expires_bits, state.now_bits): continue
        index = _u32(record.definition_index)
        if index >= len(state.timed_definitions): continue
        definition = state.timed_definitions[index]
        if definition.kind != 27: continue
        temporary.append(Modifier(definition.modifier_tag & 255,
                                  mul(definition.value20_bits, from_u32(_u32(record.stack_count)))))
    for entry in temporary:
        tag, value = _u32(entry.tag) & 255, _u32(entry.value_bits)
        if tag in (14,16,17,18,19,20,21,22,28,29,30,31,32): continue
        if tag == 9: f[29] = mul(f[29], add(value, ONE))
        else:
            accum({0:28,1:30,2:25,3:26,4:32,5:22,6:31,7:24,8:35,
                   10:33,11:27,12:36,13:39,15:38,23:40,24:45,
                   25:37,26:46,27:23}.get(tag,28), value)
    live_scale = add(f[40], ONE)
    accepted_live = []
    for i, entry in enumerate(state.live_effects):
        if _le(entry.expires_bits, state.now_bits): continue
        skip = False
        for j, other in enumerate(state.live_effects):
            if i == j or other.spell_id != entry.spell_id or other.spell_id == 774: continue
            if not _gt(other.expires_bits, state.now_bits): continue
            is_8_or_9 = (entry.kind & 0xfffffffe) == 8
            current = entry.value_bits if is_8_or_9 else Z
            if other.kind in (8, 9):
                competing = other.value_bits
                if _gt(competing, current): skip = True; break
            else:
                if is_8_or_9 and _lt(entry.value_bits, Z): skip = True; break
                competing = Z
            if j < i and _eq(competing, current): skip = True; break
        if skip: continue
        accepted_live.append(i)
        if entry.kind == 8: accum(28, mul(live_scale, entry.value_bits))
        elif entry.kind == 9: accum(30, mul(live_scale, entry.value_bits))
        if entry.spell_id == 23451: accum(24, 0x3f19999a)
        elif entry.spell_id == 23505: accum(28, 0x3f000000)
    critical_excess = _gt(f[26], ONE)
    base_hp = add(hp, mul(n, NINE))
    max_hp = mul(add(base_hp, f[42]), f[25])
    speed_multiplier = _min_select(f[24], 0x400ccccd)
    final_armor = _min_select(f[22], f[23])
    derived = {
        1260:f[44], 1256:f[43], 1248:f[50],
        1244:min(((trunc_sat_u32(n)+1)&MASK)//15, 3),
        1240:f[40],1236:f[38],1232:f[39],1228:integer17,1224:f[27],
        1220:add(f[36],state.conditional268_bits) if state.flag2294 & 255 else f[36],
        1216:f[35],1204:f[33],1200:f[29],1188:ONE if critical_excess else f[26],
        1184:div(ONE,add(f[30],ONE)),1176:max_hp,
        1192:add(f[32],add(f[26],0xbf800000)) if critical_excess else f[32],
        1212:add(mul(f[45],max_hp),f[31]),1196:speed_multiplier,1208:final_armor,
        1252:add(div(max_hp,_max_select(base_hp,ONE)),0xbf800000),
        1180:add(add(div(mul(f[37],final_armor),0x41200000),
                     mul(f[46],_max_select(sub(f[22],f[23]),Z))),f[28]),
    }
    delta = sub(max_hp,state.old_max_hp_bits)
    candidate = add(delta,state.current_hp_bits) if _gt(delta,Z) else state.current_hp_bits
    current_hp = _min_select(candidate,max_hp)
    speed = mul(speed_multiplier,0x40e00000)
    speed_changed = _gt(sub(speed,state.previous_speed_bits)&0x7fffffff,0x3c23d70a)
    return {'derived_bits': {str(k):v for k,v in sorted(derived.items())},
            'current_hp_bits':current_hp, 'speed_bits':speed if speed_changed else state.previous_speed_bits,
            'speed_changed':speed_changed, 'accepted_live_indices':accepted_live,
            'object_fields':{'22':trunc_sat_u32(_ceil(_max_select(current_hp,Z))),
                             '28':trunc_sat_u32(_ceil(max_hp)),
                             '1109':mul(derived[1188],0x42c80000)}}


def input_from_dict(raw):
    """Strict structural constructor used by executable fixtures and future ports."""
    values = dict(raw)
    for key, constructor in (('passives',Modifier),('adjustments',Adjustment),
                             ('item_modifiers',Modifier),('timed_records',TimedRecord),
                             ('timed_definitions',TimedDefinition),('live_effects',LiveEffect)):
        if key in values: values[key] = [constructor(**entry) for entry in values[key]]
    return StatsInput(**values)
