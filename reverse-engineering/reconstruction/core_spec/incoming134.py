"""Independent scalar-prefix rules for official 0.134.0 function 1063.

No original module or subprocess is called. The complete original function has
statistics, events, retaliation and revival effects; they are deliberately not
silently treated as no-ops here. Results say which original stage is represented
and list pending consumers. All *_bits values are IEEE binary32 uint32 words.
NaN payload/sign equality is outside this specification.
"""
from dataclasses import dataclass, fields, replace
from . import binary32 as f

ZERO = 0
ONE = 0x3f800000


def _u(value, bits=32):
    if not isinstance(value, int) or not 0 <= value < 1 << bits:
        raise ValueError('Expected uint' + str(bits))
    return value


def _positive(value):
    # Original two selects: NaN -> +0, then only strictly-positive survives.
    return value if f.to_float(value) > 0 else ZERO


def _minnum(a, b):
    # Original selects; ties select a, including signed-zero bits.
    left = a if f.is_nan(b) else b
    right = left if f.is_nan(a) else a
    return left if f.to_float(left) < f.to_float(right) else right


def _maxnum(a, b):
    left = a if f.is_nan(b) else b
    right = left if f.is_nan(a) else a
    return left if f.to_float(left) > f.to_float(right) else right


def classify_38322(id_bytes):
    """Recovered exact-byte lookup; unrecognized IDs return raw index 0."""
    if not isinstance(id_bytes, bytes):
        raise ValueError('Map ID must be bytes')
    return {b'elwynn': 0, b'duskwood': 1, b'wsg': 2, b'ungoro': 3,
            b'ab': 4, b'feralas': 5, b'arena': 6, b'sm': 7,
            b'av': 8, b'brm': 9, b'aq': 10, b'naxx': 11}.get(id_bytes, 0)


@dataclass(frozen=True)
class UnitPosition:
    marker: int = 0
    target_id: int = 1                # U112; scalar fixture excludes source match
    start_x_bits: int = ZERO           # U316
    start_y_bits: int = ZERO           # U320
    end_x_bits: int = ZERO             # U328
    end_y_bits: int = ZERO             # U332
    movement_time_bits: int = ZERO     # U340
    movement_duration_bits: int = ZERO # U344

    def __post_init__(self):
        _u(self.marker)
        _u(self.target_id, 64)
        for field in fields(self):
            if field.name.endswith('_bits'):
                _u(getattr(self, field.name))


@dataclass(frozen=True)
class BuffRecord:
    tag: int                         # 32B buff +8; no inferred enum name
    spell_id: int = 0                # +20
    value12_bits: int = ZERO
    expires24_bits: int = ZERO

    def __post_init__(self):
        for value in (self.tag, self.spell_id, self.value12_bits, self.expires24_bits):
            _u(value)


@dataclass(frozen=True)
class ModifierRecord:
    tag: int                        # 36B record +0
    byte4: int = 0
    byte5: int = 0

    def __post_init__(self):
        _u(self.tag)
        _u(self.byte4, 8)
        _u(self.byte5, 8)


@dataclass(frozen=True)
class IncomingState:
    phase_2579: int = 1
    protection_2568: int = 0
    mode_2574: int = 0
    map_id: bytes = b''
    wave_2532: int = 1
    now_bits: int = ZERO
    armor_1392_bits: int = ZERO
    nearby_reduction_1444_bits: int = ZERO
    player_x_1504_bits: int = ZERO
    player_y_1508_bits: int = ZERO
    hp_1528_bits: int = ZERO
    shield_1532_bits: int = ZERO
    barrier_1536_bits: int = ZERO
    shield_source_1344: int = 0
    shield_source_remaining_1348_bits: int = ZERO
    reserve_768_bits: int = ZERO
    absorbed_740_bits: int = ZERO
    maximum_shield_744_bits: int = ZERO
    incoming_total_992: float = 0.0
    last_hit_1648_bits: int = ZERO
    units: tuple = ()
    buffs: tuple = ()
    modifiers: tuple = ()

    def __post_init__(self):
        for name, cls in (('units', UnitPosition), ('buffs', BuffRecord),
                          ('modifiers', ModifierRecord)):
            values = tuple(getattr(self, name))
            if not all(isinstance(x, cls) for x in values):
                raise ValueError('Unexpected ' + name + ' record')
            object.__setattr__(self, name, values)
        for field in fields(self):
            if field.name.endswith('_bits'):
                _u(getattr(self, field.name))
        for value in (self.phase_2579, self.protection_2568, self.mode_2574):
            _u(value, 8)
        _u(self.wave_2532)
        _u(self.shield_source_1344)
        if not isinstance(self.map_id, bytes):
            raise ValueError('Map ID must be bytes')


def position_bits(unit, now_bits):
    duration = unit.movement_duration_bits
    # The original uses !(duration <= 0), so NaN enters interpolation.
    if not (f.to_float(duration) <= 0):
        t = f.div(f.sub(now_bits, unit.movement_time_bits), duration)
        t = ZERO if f.to_float(t) < 0 else t
        t = ONE if f.to_float(t) > 1 else t
        return (f.add(unit.start_x_bits, f.mul(f.sub(unit.end_x_bits, unit.start_x_bits), t)),
                f.add(unit.start_y_bits, f.mul(f.sub(unit.end_y_bits, unit.start_y_bits), t)))
    return unit.end_x_bits, unit.end_y_bits


def _near_count(state, radius_squared_bits):
    count = 0
    for unit in state.units:
        if unit.marker != 0:
            continue
        x, y = position_bits(unit, state.now_bits)
        dx = f.sub(x, state.player_x_1504_bits)
        dy = f.sub(y, state.player_y_1508_bits)
        squared = f.add(f.mul(dx, dx), f.mul(dy, dy))
        if f.to_float(squared) <= f.to_float(radius_squared_bits):
            count += 1
    return count


@dataclass(frozen=True)
class Reduction:
    amount_bits: int
    mode_amount_bits: int
    reason: str


def reduce_incoming_bits(state, amount_bits):
    """Entry guards and arithmetic through1063 L781; never consumes a shield."""
    _u(amount_bits)
    if state.phase_2579 != 1:
        return Reduction(amount_bits, amount_bits, 'phase_guard')
    if state.protection_2568 & 1:
        return Reduction(amount_bits, amount_bits, 'protection_guard')
    mode_amount = amount_bits
    if state.mode_2574 == 1:
        b = f.from_float(.7) if classify_38322(state.map_id) < 3 else ONE
        scale = f.mul(b, f.from_u32((state.wave_2532 - 1) & f.MASK))
        scale = f.mul(scale, f.from_float(.064))
        scale = f.add(scale, ONE)
        scale = f.mul(scale, f.from_float(.8))
        mode_amount = f.mul(mode_amount, scale)
    now = f.to_float(state.now_bits)
    if any(b.tag == 12 and f.to_float(b.expires24_bits) > now for b in state.buffs):
        return Reduction(mode_amount, mode_amount, 'active_raw_buff12_guard')
    amount = f.mul(mode_amount, f.sub(ONE, state.armor_1392_bits))
    if (f.to_float(state.nearby_reduction_1444_bits) > 0
            and _near_count(state, f.from_float(64)) >= 5):
        amount = f.mul(amount, f.sub(ONE, state.nearby_reduction_1444_bits))
    # The first matching54/byte4==1 is selected, not the last or sum.
    record = next((x for x in state.modifiers if x.tag == 54 and x.byte4 == 1), None)
    if record is not None and _near_count(state, f.from_float(49)):
        factor = f.add(f.div(f.from_u32(record.byte5), f.from_float(-100)), ONE)
        amount = f.mul(amount, factor)
    return Reduction(amount, mode_amount, 'reduced')


@dataclass(frozen=True)
class IncomingResult:
    state: IncomingState
    status: str
    stage: str
    amount_bits: int
    absorbed_bits: int = ZERO
    pending: tuple = ()


def resolve_incoming_prefix(state, amount_bits, source_guid=0):
    """Apply known scalar prefix and stop at unimplemented original callbacks.

    A core_hp_write result is the state at L1793, before per-source statistics,
    history, retaliation, events, minimum-one protection or death handling.
    It must never be presented as the final state after full1063 returns.
    """
    _u(source_guid, 64)
    reduced = reduce_incoming_bits(state, amount_bits)
    if reduced.reason != 'reduced':
        return IncomingResult(state, 'returned', reduced.reason, reduced.amount_bits)
    amount = reduced.amount_bits
    absorbed = ZERO
    if f.to_float(state.shield_1532_bits) > 0:
        old_shield = state.shield_1532_bits
        absorbed = _minnum(old_shield, amount)
        shield = f.sub(old_shield, absorbed)
        barrier = _positive(f.sub(state.barrier_1536_bits, absorbed))
        source = state.shield_source_1344
        remaining = state.shield_source_remaining_1348_bits
        if source:
            spill = _positive(f.sub(absorbed, remaining))
            source_depleted = f.to_float(remaining) <= f.to_float(absorbed)
            remaining = ZERO if source_depleted else f.sub(remaining, absorbed)
            new_source = 0 if source_depleted else source
        else:
            spill = absorbed
            source_depleted = False
            remaining = f.sub(remaining, absorbed)
            new_source = 0
        state = replace(state, shield_1532_bits=shield, barrier_1536_bits=barrier,
                        shield_source_1344=new_source,
                        shield_source_remaining_1348_bits=remaining)
        used_reserve = _minnum(state.reserve_768_bits, spill)
        if f.to_float(used_reserve) > 0:
            state = replace(state, reserve_768_bits=f.sub(state.reserve_768_bits, used_reserve))
            return IncomingResult(state, 'pending', 'before27959_and1453', amount, absorbed,
                                  ('27959/1453 reserve-spill callbacks before HP write',))
        state = replace(state, reserve_768_bits=_minnum(shield, state.reserve_768_bits))
        exhausted = f.to_float(shield) <= 0
        if exhausted:
            state = replace(state, barrier_1536_bits=ZERO, shield_source_1344=0,
                            shield_source_remaining_1348_bits=ZERO,
                            buffs=tuple(x for x in state.buffs if x.tag != 7))
        elif source_depleted:
            state = replace(state, buffs=tuple(x for x in state.buffs if x.spell_id != source))
        if exhausted or source_depleted:
            return IncomingResult(state, 'pending', 'before1202', amount, absorbed,
                                  ('1202 after shield/source depletion, then possible984 shield-break event',))
        amount = f.sub(amount, absorbed)
        state = replace(state, absorbed_740_bits=f.add(absorbed, state.absorbed_740_bits),
                        maximum_shield_744_bits=_maxnum(old_shield, state.maximum_shield_744_bits))
    if source_guid != 0 or any(x.target_id == 0 for x in state.units):
        return IncomingResult(state, 'pending', 'before_source_registry_L1515', amount, absorbed,
                              ('source GUID match/definition registry before HP write',))
    state = replace(state, last_hit_1648_bits=state.now_bits,
                    hp_1528_bits=f.sub(state.hp_1528_bits, amount),
                    incoming_total_992=state.incoming_total_992 + f.to_float(amount))
    return IncomingResult(state, 'pending', 'core_hp_write_L1793', amount, absorbed,
                          ('source-unit registry/statistics and48B history',
                           'raw buff13 and item22 retaliation through914',
                           'event984 callbacks before final HP reread',
                           '2570 minimum-one guard, revival/death and field22/28 writes'))


@dataclass(frozen=True)
class BarrierReplacement:
    shield_bits: int
    barrier_bits: int
    granted_bits: int
    other_shield_bits: int
    status: str = 'pending_cast922_remainder'


def replace_barrier_candidate_bits(shield_bits, barrier_bits, source_spell_id,
                                   source_remaining_bits, max_hp_bits, candidate_bits):
    """Exact922 L5337-5415 stores, given already-computed candidate L5328.

    This is neither a complete cast nor a replacement for the original sqrt,
    trigger, packet, buff and source bookkeeping after these scalar stores.
    """
    for value in (shield_bits, barrier_bits, source_spell_id, source_remaining_bits,
                  max_hp_bits, candidate_bits):
        _u(value)
    other = _positive(f.sub(shield_bits, barrier_bits))
    replaced = ZERO if source_spell_id == 11426 else source_remaining_bits
    other = _positive(f.sub(other, replaced))
    # The original min(other,+0)/max(...,+0) is exactly +0 after sanitization.
    base = ZERO
    available = _positive(f.sub(max_hp_bits, base))
    candidate = ZERO if f.to_float(candidate_bits) < 0 else candidate_bits
    granted = available if f.to_float(available) < f.to_float(candidate) else candidate
    return BarrierReplacement(f.add(other, granted), f.add(base, granted), granted, other)
