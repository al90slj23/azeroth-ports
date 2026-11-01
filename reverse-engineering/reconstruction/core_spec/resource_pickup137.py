"""Independent0.137.0 full1420 resource kinds3..5 producer.

This module owns the new source's producer contract, not its caller947 or
collection2862. Pure numeric/actor-encoding/vector primitives are shared with
the135 specification; new137 original calls must validate their use here.
The zone geometry bits are statically rechecked against137's relocated table.
No original program, memory snapshot, files or host calls are model inputs.
"""
from dataclasses import dataclass
import struct

from . import binary32 as f
from .spawn_geometry135 import hypot_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .opening_entities135 import create_world_actor
from .opening_npc_pickups135 import OpeningVector135, _write_row


RESOURCE_DEFINITIONS137 = ((3, 9006, 5931), (4, 9007, 5995), (5, 9008, 5991))


class PendingResourcePickup137(NotImplementedError):
    pass


def _word(value):
    if type(value) is not int or not 0 <= value <= f.MASK:
        raise ValueError('Exact unsigned32 word required')
    return value


def _finite(value):
    _word(value)
    if value & 0x7fffffff >= f.INF:
        raise ValueError('Finite binary32 resource time/coordinate required')
    return value


@dataclass(frozen=True)
class ResourcePickupInput137:
    zone: int
    kind: int
    amount: int
    position_bits: tuple
    now_bits: int
    rng_words: tuple
    counter: int
    pickups: OpeningVector135


@dataclass(frozen=True)
class ResourcePickupResult137:
    pickups: OpeningVector135
    rng_words: tuple
    counter: int
    position_bits: tuple
    creates: tuple
    draws: int
    clamped: bool


def produce_resource_pickup137(value: ResourcePickupInput137, world):
    """1420 append/1827 actor/169 payload; unconsumed+4 stays untouched."""
    if type(value.zone) is not int or not 0 <= value.zone < len(ZONE_GEOMETRY):
        raise ValueError('Explicit fixed137 zone required')
    _finite(value.now_bits); _word(value.counter); _word(value.amount)
    if len(value.rng_words) != 4:
        raise ValueError('Four actual shared RNG words required')
    for word in value.rng_words:
        _word(word)
    if not isinstance(value.pickups, OpeningVector135) or value.pickups.stride != 56:
        raise ValueError('Complete physical56B pickup vector required')
    if value.kind not in (3, 4, 5):
        raise PendingResourcePickup137('Only1420 resource kinds3..5 restored')
    if world is None or not hasattr(world, 'primary'):
        raise PendingResourcePickup137('Explicit query-world provider required')
    if len(value.position_bits) != 3:
        raise ValueError('Explicit XYZ required')
    x, y, _ = tuple(_finite(word) for word in value.position_bits)
    cx, cy, radius = ZONE_GEOMETRY[value.zone]
    dx, dy = f.sub(x, cx), f.sub(y, cy)
    distance = hypot_bits(dx, dy)
    limit = f.add(radius, 0xc0000000)
    limit = limit if not f.is_nan(limit) and f.to_float(limit) > 1 else 0x3f800000
    clamped = not f.to_float(distance) <= f.to_float(limit)
    if clamped:
        x = f.add(cx, f.mul(f.div(dx, distance), limit))
        y = f.add(cy, f.mul(f.div(dy, distance), limit))
        first = world.height(x, y)
        if not first.found and world.primary is not None:
            world.nearest_primary(x, y)
    height = world.height(x, y)
    if height.found:
        xyz = x, y, height.value_bits
    elif world.primary is None:
        xyz = x, y, world.fallback_height_bits
    else:
        nearest = world.nearest_primary(x, y)
        if not nearest.found:
            raise PendingResourcePickup137('1420 primary-present nearest-miss low-address read unresolved')
        xyz = x, y, nearest.xyz_bits[2]
    _, visual, display = RESOURCE_DEFINITIONS137[value.kind - 3]
    actor = create_world_actor(visual, display, 0x3f800000, xyz, 5, 0,
        value.counter, value.rng_words)
    pickups = _write_row(value.pickups, ((0, struct.pack('<I', 0)),
        (8, struct.pack('<IIQ', value.kind, value.amount, actor.create.guid)),
        (24, struct.pack('<III', 0, 8, 0)), (36, struct.pack('<I', visual)),
        (40, struct.pack('<4I', *xyz, value.now_bits))))
    return ResourcePickupResult137(pickups, actor.rng_words, actor.counter,
        xyz, (actor.create,), actor.draws, clamped)
