"""Independent26364 gather and35988/25613 motion pause/resume consumers.

These consumers leave the underlying actor motion records unchanged. They
emit stop/resume221 messages; the caller owns phase and clock transitions.
No original program, snapshot, file or captured result is read here.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f


class PendingWorldPause139(NotImplementedError):
    pass


def _uint(value, bits=32):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('Explicit unsigned word required')
    return value


def _word(row, offset, size=4):
    part = row[offset:offset + size]
    if len(part) != size or None in part:
        raise PendingWorldPause139('Consumed Unknown actor field at ' + str(offset))
    return int.from_bytes(bytes(part), 'little')


def _finite(word):
    _uint(word)
    if f.is_nan(word) or f.is_inf(word):
        raise PendingWorldPause139('Processed motion requires finite binary32 fields')
    return word


def _storage(storage, count, stride):
    _uint(count)
    if type(storage) is not tuple or not 0 <= count <= len(storage) <= 512:
        raise ValueError('Explicit bounded complete physical backing required')
    for row in storage:
        if type(row) is not tuple or len(row) != stride:
            raise ValueError('Actor stride differs')
        if any(v is not None and (type(v) is not int or not 0 <= v <= 255) for v in row):
            raise ValueError('Known byte or Unknown cell required')


@dataclass(frozen=True)
class WorldMotionOwners139:
    units432_storage: tuple
    units_count: int
    auxiliary112_storage: tuple
    auxiliary_count: int
    companions88_storage: tuple
    companions_count: int

    def __post_init__(self):
        _storage(self.units432_storage, self.units_count, 432)
        _storage(self.auxiliary112_storage, self.auxiliary_count, 112)
        _storage(self.companions88_storage, self.companions_count, 88)


@dataclass(frozen=True)
class GatheredMotion139:
    guid: int
    current_xyz: tuple
    end_xyz: tuple
    remaining_bits: int
    source_family: str
    source_index: int

    @property
    def cells40(self):
        # Original writes0..35. Its four padding bytes remain unconsumed.
        return tuple(struct.pack('<Q7I', self.guid, *self.current_xyz,
                                 *self.end_xyz, self.remaining_bits)) + (None,) * 4


@dataclass(frozen=True)
class GatheredWorldMotion139:
    motions: tuple
    capacity: int

    @property
    def count(self):
        return len(self.motions)

    @property
    def storage40(self):
        return tuple(m.cells40 for m in self.motions) + ((None,) * 40,) * (self.capacity - self.count)


def gather_world_motion139(owners, now_bits):
    """26364 stable NPC→auxiliary→companion gather, including merge reserve."""
    if not isinstance(owners, WorldMotionOwners139):
        raise TypeError('Typed actor owners required')
    _finite(now_bits)
    motions = []
    capacity = 0
    families = (
        ('NPC', owners.units432_storage[:owners.units_count], 316, 328, 340, 344, 112),
        ('auxiliary', owners.auxiliary112_storage[:owners.auxiliary_count], 32, 44, 56, 60, 16),
        ('companion', owners.companions88_storage[:owners.companions_count], 44, 56, 68, 72, 24),
    )
    for family, rows, origin, end, start, duration, guid_offset in families:
        selected = []
        family_capacity = 0
        for index, row in enumerate(rows):
            if family == 'NPC' and _word(row, 0) != 0:
                continue
            d = _word(row, duration)
            if not f.to_float(d) > 0:
                continue
            s = _word(row, start)
            endtime = f.add(d, s)
            active = (not f.to_float(endtime) <= f.to_float(now_bits)) if family == 'companion' else f.to_float(endtime) > f.to_float(now_bits)
            if not active:
                continue
            _finite(d); _finite(s); _finite(endtime)
            a = tuple(_finite(_word(row, origin + j * 4)) for j in range(3))
            b = tuple(_finite(_word(row, end + j * 4)) for j in range(3))
            ratio = f.div(f.sub(now_bits, s), d)
            if f.to_float(ratio) < 0:
                ratio = 0
            if f.to_float(ratio) > 1:
                ratio = 0x3f800000
            current = tuple(f.add(x, f.mul(f.sub(y, x), ratio)) for x, y in zip(a, b))
            value = GatheredMotion139(_word(row, guid_offset, 8), current, b,
                                      f.sub(endtime, now_bits), family, index)
            if len(selected) == family_capacity:
                family_capacity = max(4, 2 * family_capacity)
            selected.append(value)
        if family == 'NPC':
            motions = selected
            capacity = family_capacity
        else:
            #26364 copies each donor vector into the first vector then frees it.
            required = len(motions) + len(selected)
            if required > capacity:
                capacity = max(4, capacity * 2, required)
            motions.extend(selected)
    return GatheredWorldMotion139(tuple(motions), capacity)


def _packed(guid):
    raw = guid.to_bytes(8, 'little')
    return bytes([sum(1 << j for j, value in enumerate(raw) if value)]) + bytes(value for value in raw if value)


def _height(world, xyz):
    result = world.height(*xyz[:2])
    if result.found:
        return (*xyz[:2], result.value_bits)
    if getattr(world, 'primary', None) is not None:
        nearest = world.nearest_primary(*xyz[:2])
        if nearest.found:
            return (*xyz[:2], nearest.xyz_bits[2])
    return xyz


def _sat_u32(bits):
    value = f.to_float(bits)
    return 0 if not value > 0 else f.MASK if value >= f.MASK else int(value)


@dataclass(frozen=True)
class WorldPauseResult139:
    owners: WorldMotionOwners139
    gathered: GatheredWorldMotion139
    movement_sequence2412: int
    packets: tuple
    mode: str


def update_world_pause139(owners, now_bits, sequence, world, *, resume=False):
    """35988 stop or25613 resume; no actor, phase, player or clock writes."""
    _uint(sequence)
    if type(resume) is not bool or world is None:
        raise ValueError('Explicit pause/resume mode and query world required')
    gathered = gather_world_motion139(owners, now_bits)
    packets = []
    for motion in gathered.motions:
        current = _height(world, motion.current_xyz)
        sequence = (sequence + 1) & f.MASK
        payload = _packed(motion.guid) + struct.pack('<4I', *current, sequence)
        if resume:
            end = _height(world, motion.end_xyz)
            milliseconds = max(1, _sat_u32(f.mul(motion.remaining_bits, 0x447a0000)))
            payload += b'\0' + struct.pack('<3I', 256, milliseconds, 1) + struct.pack('<3I', *end)
            capacity = 64
        else:
            payload += b'\1'
            capacity = 32
        packets.append((221, capacity, payload.hex()))
    return WorldPauseResult139(owners, gathered, sequence, tuple(packets), 'resume' if resume else 'pause')
