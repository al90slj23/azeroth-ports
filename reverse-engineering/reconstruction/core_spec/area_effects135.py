"""Independent135 normal persistent-area producer922 and consumer3757.

Caller supplies full88B records, unused append-slot bytes and flat-world height.
No binary, oracle result, save, packet or asset is read. Unknown record variants,
frost-trap stun, following-area modifier36 and effect-override49 remain pending.
"""
from dataclasses import dataclass, fields, replace
import struct

from . import binary32 as f
from .ability_state import AbilityRecord
from .cast135 import (CastDefinition, CastState, UnresolvedCast, base_damage,
    query_targets, position, distance_squared, _critical, _updated_combat)
from .cast_events135 import apply_hit
from .progression134 import round_85718_bits, trunc_sat_u32
from .radius import radius_bits
from .record_cells135 import cells135,u32,u64,put_u32,put_u64,encode_row

AREAS = {
    b'consecration': (5468396, 0, 26573), b'volley': (5469716, 0, 1510),
    b'immolation_trap': (5470068, 0, 13797), b'blizzard': (5473764, 1, 10),
    b'flamestrike': (5473852, 0, 2120), b'rain_of_fire': (5474820, 0, 5740),
    b'hurricane': (5475788, 1, 16914),
}


def _u(value):
    if type(value) is not int or not 0 <= value <= f.MASK:
        raise ValueError('Explicit u32 required')
    return value


def _finite(value):
    _u(value)
    if value & 0x7fffffff >= f.INF:
        raise UnresolvedCast('Nonfinite area arithmetic remains outside this bounded slice')
    return value


def _raw(hexdata):
    return cells135(hexdata,88)


@dataclass(frozen=True)
class AreaDefinition135:
    pointer: int
    ability_id: bytes
    raw88_hex: str

    def words(self):
        raw = _raw(self.raw88_hex)
        w = tuple(u32(raw,o,'135 area definition')for o in range(0,88,4))
        if self.ability_id not in AREAS or (self.pointer, w[0], w[11]) != AREAS[self.ability_id] or raw[84] != 3:
            raise UnresolvedCast('Unrestored area definition/execution/effect')
        return w

    def common(self):
        w = self.words(); raw = _raw(self.raw88_hex)
        return CastDefinition(self.pointer, self.ability_id, 3, w[0], w[11], raw[85],
            w[12], w[13], w[14], w[15], w[16])


@dataclass(frozen=True)
class AreaState135:
    records: tuple = ()
    spawn_counter: int = 0

    def __post_init__(self):
        _u(self.spawn_counter)
        if type(self.records) is not tuple or len(self.records) > 4096:
            raise ValueError('Bounded ordered area vector required')
        for row in self.records:
            raw = _raw(row)
            if u64(raw,0,'135 area tag') != 0 or u32(raw,32,'135 area effect tag') not in (0, 1):
                raise UnresolvedCast('Hostile/alternate area variants and other status effects remain pending')
            spell = u32(raw,60,'135 area spell')
            if spell not in {v[2] for v in AREAS.values()}:
                raise UnresolvedCast('Unknown area spell/follow behavior remains pending')
            for offset in (36, 40, 44, 48, 52, 56, 64, 68, 76, 80):
                _finite(u32(raw,offset,'135 active area scalar'))


@dataclass(frozen=True)
class AreaCastResult135:
    cast: CastState
    areas: AreaState135
    success: int
    center_xyz: tuple
    attempted_spell_sets: tuple
    pending: tuple = ('Physical cast/visual packets and allocator capacity are pending',)


@dataclass(frozen=True)
class AreaTickResult135:
    cast: CastState
    areas: AreaState135
    hits: tuple
    expired_visual_guids: tuple
    effect_writes: tuple
    pending: tuple = ('Physical visual despawn packets and full frame scheduler are pending',)


def select_area_center(cast, range_bits, radius):
    """13151: first24 range candidates; maximum all-live density, later ties."""
    ids = [s.unit.target_id for s in cast.spatial]
    if len(set(ids)) != len(ids):
        raise UnresolvedCast('Duplicate-GUID area selection is unresolved')
    if f.to_float(range_bits) <= 0:
        return cast.player_xy if query_targets(cast.spatial, cast.player_xy, radius, cast.combat.now_bits) else ()
    candidates = query_targets(cast.spatial, cast.player_xy, range_bits, cast.combat.now_bits)[:24]
    locations = {s.unit.target_id: position(s, cast.combat.now_bits) for s in cast.spatial if not s.unit.marker}
    best, score = (), -1
    limit = f.mul(radius, radius)
    for guid in candidates:
        xy = locations[guid]
        count = sum(f.to_float(distance_squared(xy, p)) <= f.to_float(limit) for p in locations.values())
        if count >= score:
            best, score = xy, count
    return best


def _cast_finite(cast):
    for value in (cast.combat.now_bits, cast.damage_multiplier_bits, cast.max_hp_bits,
            cast.critical_chance_bits, cast.critical_multiplier_bits, cast.area_multiplier_bits,
            *cast.player_xy):
        _finite(value)
    ids = [u.target_id for u in cast.combat.units]
    if len(ids) != len(set(ids)):
        raise UnresolvedCast('Duplicate-GUID area lookup remains pending')
    for entry in cast.spatial:
        for field in fields(entry.unit):
            #3757/922 do not consume an old death timestamp. Corpse cleanup
            #requires U4 only after marker1, not during an unrelated area pass.
            if field.name.endswith('_bits') and field.name!='death_time_4_bits':
                _finite(getattr(entry.unit, field.name))
        for value in (*entry.from_xy, *entry.to_xy):
            _finite(value)


def produce_area(cast, areas, definition, owned, flat_height_bits, *, append_slot_hex,
        terrain_grid_absent=False, navigation_absent=False, busy488=0,
        attempted_spell_sets=None, area_modifiers_absent=False):
    """Actual kind3 append; every unwritten byte retains explicit slot input.

    area_modifiers_absent explicitly excludes36 follow and49 effect overrides,
    plus other unmodeled producer globals. It must describe the actual sources.
    """
    if not isinstance(cast, CastState) or not isinstance(areas, AreaState135) or not isinstance(owned, AbilityRecord):
        raise TypeError('Resolved cast/area/owned snapshots required')
    if terrain_grid_absent is not True or navigation_absent is not True or area_modifiers_absent is not True:
        raise UnresolvedCast('Terrain/navigation or nonempty area modifier sources remain pending')
    _finite(flat_height_bits); _cast_finite(cast); _u(busy488)
    w = definition.words(); common = definition.common(); raw = _raw(append_slot_hex)
    if owned.definition_pointer != definition.pointer:
        raise ValueError('Owned pointer differs')
    for value in (cast.area_multiplier_bits, owned.area_bits, owned.additional_area_bits,
                  owned.duration_bits, owned.additional_duration_bits, owned.damage_bits,
                  owned.additional_damage_bits, owned.life_damage_bits, *cast.player_xy):
        _finite(value)
    if attempted_spell_sets is None:
        if busy488 or cast.context908 & 1:
            raise ValueError('Three explicit attempt ledgers required for gated third ledger')
        ledgers = (cast.attempted_spell_ids,) * 3
    else:
        ledgers = tuple(tuple(x) for x in attempted_spell_sets)
        if len(ledgers) != 3 or ledgers[0] != cast.attempted_spell_ids:
            raise ValueError('Three ledgers and CastState first ledger must agree')
        for row in ledgers:
            for value in row: _u(value)
    spell = w[11]
    ledgers = tuple((row if spell in row else row + (spell,)) if i < 2 or (not busy488 and not cast.context908 & 1) else row
        for i, row in enumerate(ledgers))
    cast = replace(cast, attempted_spell_ids=ledgers[0])
    radius = radius_bits(f.mul(cast.area_multiplier_bits, f.mul(w[15], f.mul(owned.area_bits, owned.additional_area_bits))))
    xy = select_area_center(cast, w[14], radius)
    if not xy:
        return AreaCastResult135(cast, areas, 0, (), ledgers)
    duration = f.mul(f.mul(f.mul(w[17], 0x3fb33333), owned.duration_bits), owned.additional_duration_bits)
    _finite(duration); _finite(radius)
    base_ticks = f.from_u32(max(1, w[18]))
    # Fixed definitions have positive finite base duration; use exact85719 leaf algorithm.
    denominator = w[17] if f.to_float(w[17]) > .01 else 0x3c23d70a
    actual = max(1, trunc_sat_u32(round_85718_bits(f.mul(f.div(duration, denominator), base_ticks))))
    if actual > 1000000:
        raise UnresolvedCast('Area tick-count watchdog')
    counter = (areas.spawn_counter + 1) & f.MASK
    put_u64(raw,0,0)
    put_u64(raw,24,0xf100000000000000 | counter)
    effect_aux = f.mul(owned.additional_duration_bits, w[2]) if w[0] == 1 else w[2]
    for offset, value in ((32, w[0]), (36, w[1]), (40, effect_aux), (44, xy[0]), (48, xy[1]), (52, flat_height_bits),
        (56, radius), (60, spell), (64, f.add(cast.combat.now_bits, 0x3e800000)),
        (68, f.div(duration, f.from_u32(actual))), (72, actual), (76, f.div(base_damage(cast, common, owned), base_ticks)),
        (80, f.add(f.add(duration, cast.combat.now_bits), 0x3e99999a))):
        put_u32(raw,offset,value)
    raw[84] = _raw(definition.raw88_hex)[85]
    return AreaCastResult135(cast, AreaState135(areas.records + (encode_row(raw),), counter), 1, xy + (flat_height_bits,), ledgers)


def tick_areas(cast, areas, now_bits, *, after_hit=None, after_death=None, area_modifiers_absent=False):
    """3757 ordered vector; remove expired first, at most one due tick per entry.

    The per-hit callback runs for every accepted914 hit, and an explicit death
    continuation completes914 before2244. Status120 writes are returned for raw
    unit adapters; modeled124 deadlines are already synchronized in CastState.
    """
    if area_modifiers_absent is not True:
        raise UnresolvedCast('Following/effect-override sources must be explicitly absent')
    _finite(now_bits); _cast_finite(cast)
    cast = replace(cast, combat=replace(cast.combat, now_bits=now_bits))
    rows, expired, hits, writes = [], [], [], []
    for hexdata in areas.records:
        raw = _raw(hexdata)
        w = {i:u32(raw,i*4,'3757 active area field')for i in(8,9,10,11,12,14,15,16,17,18,19,20)}
        if f.to_float(now_bits) >= f.to_float(w[20]):
            guid = u64(raw,24,'3757 expired area GUID')
            if guid: expired.append(guid)
            continue
        if w[18] and f.to_float(w[16]) <= f.to_float(now_bits):
            put_u32(raw,72,w[18]-1)
            put_u32(raw,64,f.add(w[16],w[17]))
            targets = query_targets(cast.spatial, (w[11], w[12]), w[14], now_bits)
            for guid in targets:
                cast, damage, critical = _critical(cast, w[19])
                cast, result = apply_hit(cast, guid, damage, w[15], after_hit=after_hit, after_death=after_death)
                hits.append((guid, damage, critical, result.applied, result.dead, result.new_hp_bits))
                if w[8] == 1:
                    units = list(cast.combat.units)
                    for i, unit in enumerate(units):
                        if unit.target_id == guid and unit.marker != 1:
                            expiry = f.add(now_bits, w[10])
                            units[i] = replace(unit, control_until_124_bits=expiry)
                            writes.extend(((guid, 120, w[9]), (guid, 124, expiry)))
                            break
                    cast = _updated_combat(cast, replace(cast.combat, units=tuple(units)))
        rows.append(encode_row(raw))
    return AreaTickResult135(cast, AreaState135(tuple(rows), areas.spawn_counter), tuple(hits), tuple(expired), tuple(writes))
