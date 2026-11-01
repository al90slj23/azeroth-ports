"""Independent official0.134.0 kind0 pickup record/arithmetic projection.

Source SHA256:2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52.
Evidence:reports/2026-11-01-death-xp0134-chain.json (full1417/2862).
This module never calls original WASM. World placement is an explicit already
resolved input; physical heap addresses, visual/message serialization, other
pickup kinds, claims, multiplayer and4630 side effects are reported pending.
Floating inputs/outputs are IEEE754 u32 words. Codec preserves all raw words;
arithmetic uses binary32 and canonicalizes NaNs as documented by binary32.py.
"""
from dataclasses import dataclass, fields, replace
import struct

from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .progression134 import round_85718_bits, trunc_sat_u32

STRIDE = 56
XP_KIND = 0
XP_VISUAL_ID = 9001
XP_GUID_PREFIX = 0xf130002329000000
ONE = 0x3f800000
MIN_DELAY = 0x3df5c28f           # exact f32 literal0.12 from2862
AGE_SIX = 0x40c00000
SPEED_24 = 0x41c00000
SPEED_32 = 0x42000000
MILLISECONDS = 0x447a0000
_RECORD = struct.Struct('<IIIIQIIIIIIII')


def _u(value, width=32):
    if type(value) is not int or not 0 <= value < 1 << width:
        raise ValueError('Expected uint' + str(width))
    return value


@dataclass(frozen=True)
class Placement:
    """The result of1417's region clamp/height query, supplied explicitly."""
    x_bits: int
    y_bits: int
    height_bits: int

    def __post_init__(self):
        for field in fields(self):
            _u(getattr(self, field.name))


@dataclass(frozen=True)
class PickupRecord:
    """All56 bytes; arrival=None means append has not written that word.

    Newly appended kind0 record+4 is uninitialized in the original. Encoding
    such a record therefore requires either its prior56B slot or an explicit
    raw word. A decoded record always carries the actual raw arrival bits.
    """
    marker: int = 0
    arrival_bits: int | None = None
    kind: int = XP_KIND
    amount: int = 0
    guid: int = 0
    aux_capacity: int = 0
    aux_pointer: int = 8
    aux_count: int = 0
    visual_id: int = XP_VISUAL_ID
    x_bits: int = 0
    y_bits: int = 0
    height_bits: int = 0
    spawn_time_bits: int = 0

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name == 'arrival_bits' and value is None:
                continue
            _u(value, 64 if field.name == 'guid' else 32)


def decode_record56(raw):
    """Decode exactly one complete record, preserving NaNs and stale words."""
    if not isinstance(raw, bytes) or len(raw) != STRIDE:
        raise ValueError('Expected exactly56 bytes')
    return PickupRecord(*_RECORD.unpack(raw))


def encode_record56(record, *, prior_slot=None, uninitialized_arrival_bits=None):
    """Encode all words; never silently invent append's unwritten+4 field."""
    if not isinstance(record, PickupRecord):
        raise TypeError('Expected a PickupRecord')
    arrival = record.arrival_bits
    if prior_slot is not None and (not isinstance(prior_slot, bytes) or len(prior_slot) != STRIDE):
        raise ValueError('Prior slot must be exactly56 bytes')
    if uninitialized_arrival_bits is not None:
        _u(uninitialized_arrival_bits)
    if arrival is None:
        if prior_slot is not None and uninitialized_arrival_bits is not None:
            raise ValueError('Use either prior slot or explicit unwritten word')
        if prior_slot is not None:
            arrival = struct.unpack_from('<I', prior_slot, 4)[0]
        elif uninitialized_arrival_bits is not None:
            arrival = uninitialized_arrival_bits
        else:
            raise ValueError('Original append leaves arrival unwritten; supply its raw word')
    return _RECORD.pack(record.marker, arrival, record.kind, record.amount, record.guid,
        record.aux_capacity, record.aux_pointer, record.aux_count, record.visual_id,
        record.x_bits, record.y_bits, record.height_bits, record.spawn_time_bits)


@dataclass(frozen=True)
class PickupState:
    records: tuple = ()
    capacity: int = 0                 # G1860; heap pointer is outside projection
    spawn_counter: int = 0            # G2400
    message_sequence: int = 0         # G2404 (attraction messages only)
    now_bits: int = 0                 # G2344 entry snapshot
    player_x_bits: int = 0            # G1504
    player_y_bits: int = 0            # G1508
    player_z_bits: int = 0            # G1512 raw word
    radius_bits: int = 0              # G1384
    xp_multiplier_bits: int = ONE     # G1388
    mode: int = 0                     # G2574; nonzero modes remain pending
    claims_empty: bool = True         # G2108 must be0 for controlled domain

    def __post_init__(self):
        values = tuple(self.records)
        if not all(isinstance(record, PickupRecord) for record in values):
            raise ValueError('Expected PickupRecord vector')
        object.__setattr__(self, 'records', values)
        for field in fields(self):
            if field.name.endswith('_bits'):
                _u(getattr(self, field.name))
        for value in (self.capacity, self.spawn_counter, self.message_sequence):
            _u(value)
        if len(values) > self.capacity:
            raise ValueError('Record count exceeds vector capacity')
        _u(self.mode, 8)
        if type(self.claims_empty) is not bool:
            raise ValueError('claims_empty must be bool')


@dataclass(frozen=True)
class MessageProjection:
    """Semantic message inputs, not the serialized original wire payload."""
    operation: str
    guid: int
    sequence: int | None = None
    position_bits: tuple = ()
    destination_bits: tuple = ()
    duration_bits: int | None = None
    duration_milliseconds: int | None = None
    amount: int | None = None


@dataclass(frozen=True)
class PickupResult:
    state: PickupState
    status: str
    messages: tuple = ()
    xp_awards: tuple = ()
    merged_index: int | None = None
    capacity_growth: tuple | None = None
    pending: tuple = ()


def _pending(state, reason):
    return PickupResult(state, 'pending_domain', pending=(reason,))


def _squared_distance(x, y, other_x, other_y):
    dx = f.sub(x, other_x)
    dy = f.sub(y, other_y)
    return f.add(f.mul(dx, dx), f.mul(dy, dy))


def _minimum_nan_safe(value_bits, minimum_bits):
    value = minimum_bits if f.is_nan(value_bits) else value_bits
    return value if f.to_float(value) > f.to_float(minimum_bits) else minimum_bits


def append_xp(state, amount, placement=None):
    """Project1417 kind0 append/45-idle merge with resolved world placement.

    Normal markers0/1 and finite merge coordinates are the specified domain.
    No region clamp or height is guessed. No original code or RNG is called.
    amount0 is legal for direct1417 callers even though914 normally skips it.
    """
    if not isinstance(state, PickupState):
        raise TypeError('Expected a PickupState')
    _u(amount)
    if not isinstance(placement, Placement):
        return _pending(state, '1417 region clamp/terrain placement must be supplied explicitly')
    xp = [(i, record) for i, record in enumerate(state.records) if record.kind == XP_KIND]
    if any(record.marker not in (0, 1) for _, record in xp):
        return _pending(state, '1417 noncanonical marker XOR1 cap arithmetic is not specified')
    idle = [(i, record) for i, record in xp if record.marker == 0]
    if len(idle) >= 45:
        coords = (placement.x_bits, placement.y_bits) + tuple(
            word for _, record in idle for word in (record.x_bits, record.y_bits))
        if any(f.is_inf(word) or f.is_nan(word) for word in coords):
            return _pending(state, '1417 nonfinite nearest-record bit-order comparison is pending')
        # Original uses strict greater-than to replace the selected record.
        # Finite coordinates may produce +inf squared distance; ties retain first.
        selected_index, selected = idle[0]
        distance = _squared_distance(selected.x_bits, selected.y_bits,
                                     placement.x_bits, placement.y_bits)
        for index, record in idle[1:]:
            candidate = _squared_distance(record.x_bits, record.y_bits,
                                         placement.x_bits, placement.y_bits)
            if f.to_float(distance) > f.to_float(candidate):
                selected_index, selected, distance = index, record, candidate
        records = list(state.records)
        records[selected_index] = replace(selected, amount=(selected.amount + amount) & f.MASK)
        return PickupResult(replace(state, records=tuple(records)), 'core_projection',
                            merged_index=selected_index)
    counter = (state.spawn_counter + 1) & f.MASK
    record = PickupRecord(amount=amount, guid=XP_GUID_PREFIX | (counter & 0xffffff),
        x_bits=placement.x_bits, y_bits=placement.y_bits, height_bits=placement.height_bits,
        spawn_time_bits=state.now_bits)
    capacity, growth = state.capacity, None
    if len(state.records) == capacity:
        capacity = max(4, (capacity * 2) & f.MASK)
        if capacity <= len(state.records) or capacity * STRIDE > 0x7fffffff:
            return _pending(state, '1417 allocation-size failure/overflow is pending')
        growth = (state.capacity, capacity)
    output = replace(state, records=state.records + (record,), capacity=capacity,
                     spawn_counter=counter)
    message = MessageProjection('xp_spawn', record.guid,
        position_bits=(record.x_bits, record.y_bits, record.height_bits), amount=amount)
    pending = ('10823/50797 XP visual serialization and keyed state',)
    if growth is not None:
        pending += ('65336/56191 physical allocation address and copied heap bytes',)
    return PickupResult(output, 'core_projection', (message,), capacity_growth=growth,
                        pending=pending)


def pickup_xp_amount(base_amount, xp_multiplier_bits):
    """Mode0 2862 ordered multiply/85718/NaN->1/min1/trunc_sat_u32."""
    _u(base_amount)
    _u(xp_multiplier_bits)
    amount = f.mul(xp_multiplier_bits, f.from_u32(base_amount))
    amount = f.mul(amount, ONE)        # Original modeMultiplier operation retained.
    amount = round_85718_bits(amount)
    return trunc_sat_u32(_minimum_nan_safe(amount, ONE))


def step_pickups(state):
    """Project one full2862 kind0-only, empty-claim, mode0 invocation.

    First attract marker0 records; then collect marker!=0 records whose stored
    arrival<=the same entry now. Eligible indices are processed in descending
    order, preserving31731's ordered removal. Very large now may round
    now+.12 back to now and allow collection within this same invocation.
    Return xp_awards in real dispatch order; apply_xp can project4630 fields.
    """
    if not isinstance(state, PickupState):
        raise TypeError('Expected a PickupState')
    if state.mode != 0:
        return _pending(state, '2862 nonzero-mode queue and XP multiplier are pending')
    if not state.claims_empty:
        return _pending(state, '2862 claim-vector construction and GUID membership are pending')
    if any(record.kind != XP_KIND for record in state.records):
        return _pending(state, '2862 mixed pickup-kind callbacks are pending')
    if any(record.marker not in (0, 1) for record in state.records):
        return _pending(state, '2862/31731 noncanonical marker/despawn variants are pending')
    if any(record.aux_count or record.aux_capacity for record in state.records):
        return _pending(state, '31731 auxiliary visual GUID vector/destruction is pending')
    if any(record.marker and record.arrival_bits is None for record in state.records):
        return _pending(state, 'Attracting record requires its actual stored arrival word')
    records, messages = list(state.records), []
    now = f.to_float(state.now_bits)
    sequence = state.message_sequence
    for index, record in enumerate(records):
        if record.marker != 0:
            continue
        distance = sqrt_bits(_squared_distance(record.x_bits, record.y_bits,
                                              state.player_x_bits, state.player_y_bits))
        age_override = f.to_float(f.sub(state.now_bits, record.spawn_time_bits)) > 6
        in_radius = f.to_float(distance) <= f.to_float(state.radius_bits)
        if not in_radius and not age_override:
            continue
        delay = _minimum_nan_safe(f.div(distance, SPEED_32 if age_override else SPEED_24),
                                  MIN_DELAY)
        records[index] = replace(record, marker=1, arrival_bits=f.add(state.now_bits, delay))
        sequence = (sequence + 1) & f.MASK
        messages.append(MessageProjection('xp_attract', record.guid, sequence,
            (record.x_bits, record.y_bits, record.height_bits),
            (state.player_x_bits, state.player_y_bits, state.player_z_bits),
            delay, trunc_sat_u32(f.mul(delay, MILLISECONDS))))
    eligible = [i for i, record in enumerate(records)
                if record.marker != 0 and record.arrival_bits is not None
                and f.to_float(record.arrival_bits) <= now]
    awards = []
    for index in reversed(eligible):
        record = records.pop(index)
        messages.append(MessageProjection('xp_despawn', record.guid))
        awards.append(pickup_xp_amount(record.amount, state.xp_multiplier_bits))
    output = replace(state, records=tuple(records), message_sequence=sequence)
    pending = ()
    if messages:
        pending += ('27456/31731 binary messages, allocation pointers and serialization',)
    if awards:
        pending += ('4630 keyed state, stat rebuild/heal, messages and choice generation; use progression134 only for selected fields',)
    return PickupResult(output, 'core_projection', tuple(messages), tuple(awards), pending=pending)
