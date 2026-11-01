"""Independent947 G2444 and1417 kinds3..5 resource-object producers.

The caller supplies an independently resolved real world, actual shared RNG,
counter and the complete physical56B pickup vector. This is the resource slice
after ordinary947 work, not a whole-frame scheduler or resource collection.
No original memory, files or host callbacks are read by this module.
"""
from dataclasses import dataclass
import struct

from . import binary32 as f
from .rng import next_u32_words
from .spawn_geometry135 import hypot_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .world_position135 import WorldPositionInput135, sample_random_position
from .opening_entities135 import create_world_actor
from .opening_npc_pickups135 import OpeningVector135, _write_row


RESOURCE_DEFINITIONS135 = ((3, 9006, 5931), (4, 9007, 5995), (5, 9008, 5991))


class PendingResourceSpawn135(NotImplementedError):
    pass


def _word(value):
    if type(value) is not int or not 0 <= value <= f.MASK:
        raise ValueError('Exact unsigned32 word required')
    return value


def _finite(value):
    _word(value)
    if value & 0x7fffffff >= f.INF:
        raise ValueError('Finite binary32 resource time/position required')
    return value


def _common(zone, now_bits, rng_words, counter, pickups):
    if type(zone) is not int or not 0 <= zone < len(ZONE_GEOMETRY):
        raise ValueError('Explicit fixed135 zone required')
    _finite(now_bits); _word(counter)
    if len(rng_words) != 4:
        raise ValueError('Four actual shared RNG words required')
    for word in rng_words:
        _word(word)
    if not isinstance(pickups, OpeningVector135) or pickups.stride != 56:
        raise ValueError('Complete physical56B pickup vector required')


@dataclass(frozen=True)
class ResourcePickupInput135:
    zone: int
    kind: int
    amount: int
    position_bits: tuple
    now_bits: int
    rng_words: tuple
    counter: int
    pickups: OpeningVector135


@dataclass(frozen=True)
class ResourcePickupResult135:
    pickups: OpeningVector135
    rng_words: tuple
    counter: int
    position_bits: tuple
    creates: tuple
    draws: int


def _resource_xyz(zone, xyz, world):
    if world is None or not hasattr(world, 'primary'):
        raise PendingResourceSpawn135('Actual world query provider required')
    if len(xyz) != 3:
        raise ValueError('Explicit XYZ required')
    x, y, _ = tuple(_finite(word) for word in xyz)
    cx, cy, radius = ZONE_GEOMETRY[zone]
    dx, dy = f.sub(x, cx), f.sub(y, cy)
    distance = hypot_bits(dx, dy)
    limit = f.add(radius, 0xc0000000)
    limit = limit if not f.is_nan(limit) and f.to_float(limit) > 1 else 0x3f800000
    if not f.to_float(distance) <= f.to_float(limit):
        x = f.add(cx, f.mul(f.div(dx, distance), limit))
        y = f.add(cy, f.mul(f.div(dy, distance), limit))
        # Original1417 performs this first pure lookup on its clamp path,
        # then repeats the lookup in the kinds3..5 common object branch.
        first = world.height(x, y)
        if not first.found and world.primary is not None:
            world.nearest_primary(x, y)
    height = world.height(x, y)
    if height.found:
        return (x, y, height.value_bits)
    if world.primary is None:
        return (x, y, world.fallback_height_bits)
    nearest = world.nearest_primary(x, y)
    if nearest.found:
        return (x, y, nearest.xyz_bits[2])
    # The actual1417 primary-present nearest-miss branch loads+116
    # relative to the original kind argument. Do not invent a fallback
    # for that unrecovered low-address read. Real451 world has no primary.
    raise PendingResourceSpawn135('1417 primary-present nearest-miss low-address fallback unresolved')


def produce_resource_pickup135(value: ResourcePickupInput135, world):
    """Complete1417 resource3/4/5 append and1821/169 actor creation."""
    _common(value.zone, value.now_bits, value.rng_words, value.counter, value.pickups)
    _word(value.amount)
    if value.kind not in (3, 4, 5):
        raise PendingResourceSpawn135('Only actual947 resource kinds3..5 admitted')
    _, visual, display = RESOURCE_DEFINITIONS135[value.kind - 3]
    xyz = _resource_xyz(value.zone, value.position_bits, world)
    actor = create_world_actor(visual, display, 0x3f800000, xyz, 5, 0,
        value.counter, value.rng_words)
    pickups = _write_row(value.pickups, ((0, struct.pack('<I', 0)),
        (8, struct.pack('<IIQ', value.kind, value.amount, actor.create.guid)),
        (24, struct.pack('<III', 0, 8, 0)), (36, struct.pack('<I', visual)),
        (40, struct.pack('<4I', *xyz, value.now_bits))))
    return ResourcePickupResult135(pickups, actor.rng_words, actor.counter,
        xyz, (actor.create,), actor.draws)


@dataclass(frozen=True)
class ResourceSpawnInput135:
    zone: int
    now_bits: int
    next_resource2444_bits: int
    player_xyz_bits: tuple
    velocity_xy: tuple
    rng_words: tuple
    counter: int
    pickups: OpeningVector135


@dataclass(frozen=True)
class ResourceSpawnResult135:
    status: str
    next_resource2444_bits: int
    pickups: OpeningVector135
    rng_words: tuple
    counter: int
    chosen_kind: int | None = None
    amount: int | None = None
    position: object | None = None
    final_position_bits: tuple | None = None
    creates: tuple = ()
    selection_draws: int = 0
    position_draws: int = 0
    actor_draws: int = 0
    counted_resources: int | None = None

    @property
    def draws(self):
        return self.selection_draws + self.position_draws + self.actor_draws


def step_resource_spawn135(value: ResourceSpawnInput135, world):
    """Complete G2444 slice; caller retains ordered surrounding947 work.

    Due writes now+45 before counting *all* active records whose kind+8 is
    3..5, regardless of marker+0. Cap2 consumes no RNG. Accepted kind draw
    uses the inlined multiply3/rejection mask; its post-draw state[0] is the
    actual1417 amount argument, before13516 advances the shared RNG again.
    """
    _common(value.zone, value.now_bits, value.rng_words, value.counter, value.pickups)
    _word(value.next_resource2444_bits)
    if not f.to_float(value.now_bits) >= f.to_float(value.next_resource2444_bits):
        return ResourceSpawnResult135('resource2444_future', value.next_resource2444_bits,
            value.pickups, value.rng_words, value.counter)
    deadline = f.add(value.now_bits, 0x42340000)  #45
    count = 0
    for row in value.pickups.storage[:value.pickups.count]:
        if any(byte is None for byte in row[8:12]):
            raise PendingResourceSpawn135('Active pickup kind+8 must be known for G2444 cap')
        count += 3 <= int.from_bytes(bytes(row[8:12]), 'little') <= 5
    if count >= 2:
        return ResourceSpawnResult135('resource2444_cap', deadline, value.pickups,
            value.rng_words, value.counter, counted_resources=count)
    if world is None or not hasattr(world, 'primary'):
        raise PendingResourceSpawn135('Actual world query provider required')
    words = value.rng_words
    for draws in range(1, 100001):
        output, words = next_u32_words(words)
        product = output * 3
        if product & 0xc0000000 != 0xc0000000:
            break
    else:
        raise RuntimeError('Independent resource kind RNG watchdog exceeded')
    kind, amount = 3 + (product >> 32), words[0]
    position = sample_random_position(WorldPositionInput135(value.zone,
        value.player_xyz_bits, value.velocity_xy, 0x41700000, 0x42200000,
        0, words), world)
    produced = produce_resource_pickup135(ResourcePickupInput135(value.zone,
        kind, amount, position.position_bits, value.now_bits, position.rng_words,
        value.counter, value.pickups), world)
    return ResourceSpawnResult135('resource2444_spawned', deadline, produced.pickups,
        produced.rng_words, produced.counter, kind, amount, position,
        produced.position_bits, produced.creates, draws, position.draws,
        produced.draws, count)
