"""Independent1398740/13563 consumers of an explicitly resolved real world.

Geometry is a pure input implementing height/nav_probe/nearest_primary. It is
never obtained by this module from an original snapshot, file or host callback.
World production and all entity/packet append operations are separate systems.
"""
from dataclasses import dataclass

from . import binary32 as f
from .rng import next_u32_words, uniform_range_bits
from .position_math139 import sin_bits, cos_bits, hypot_bits
from .npc_heading139 import atan2_bits
from .world_position139_data import ZONE_GEOMETRY139 as ZONE_GEOMETRY


def _finite(word):
    if type(word) is not int or not 0 <= word <= f.MASK or (word & ~f.SIGN) >= f.INF:
        raise ValueError('Explicit finite binary32 position input required')
    return word


@dataclass(frozen=True)
class DistanceMap139:
    values_u16: tuple|None
    field24: int

    def __post_init__(self):
        if type(self.field24) is not int or not 0 <= self.field24 <= f.MASK:
            raise ValueError('Actual2368-payload field24 required')
        if self.values_u16 is not None and (type(self.values_u16)is not tuple or any(type(x) is not int or not 0 <= x <= 65535 for x in self.values_u16)):
            raise ValueError('Explicit u16 path values required')


@dataclass(frozen=True)
class WorldPositionInput139:
    zone: int
    player_xyz: tuple
    velocity_xy: tuple
    low_radius_bits: int
    high_radius_bits: int
    bias_probability_bits: int
    rng_words: tuple
    distance_map: DistanceMap139 | None = None

    def __post_init__(self):
        if type(self.zone) is not int or self.zone != 0:
            raise ValueError('Currentmatched139Elwynn zone0 required')
        if len(self.player_xyz) != 3 or len(self.velocity_xy) != 2:
            raise ValueError('Explicit player XYZ and velocity XY required')
        for value in (*self.player_xyz, *self.velocity_xy, self.low_radius_bits,
                      self.high_radius_bits, self.bias_probability_bits):
            _finite(value)
        if not 0<=f.to_float(self.low_radius_bits)<f.to_float(self.high_radius_bits)<=8192:raise ValueError('Explicit0<=low<high<=8192 radius domain')
        if len(self.rng_words) != 4 or any(type(x) is not int or not 0 <= x <= f.MASK for x in self.rng_words):
            raise ValueError('Four actual RNG words required')
        if self.distance_map is not None and not isinstance(self.distance_map, DistanceMap139):
            raise ValueError('Explicit distance map or absent2368 required')


@dataclass(frozen=True)
class WorldPositionResult139:
    position_bits: tuple
    rng_words: tuple
    draws: int
    attempts: int
    radius_shrinks: int = 0
    fallback_attempts: int = 0
    branch: str = 'sampled'


def _uniform(words, low, high):
    value = uniform_range_bits(words, low, high)
    return value.bits, value.state, value.draws


def _candidate(player_xy, angle, radius):
    return (f.add(player_xy[0], f.mul(cos_bits(angle), radius)),
            f.add(player_xy[1], f.mul(sin_bits(angle), radius)))


def sample_random_position(state, world):
    """13563:12 clamped trials, then one unconditional un-clamped trial.

    The final nearest-primary query contributes only Z; its returned cell
    centre does not replace the random XY. First-trial height tolerance is
    strictly less than25, unlike8740's inclusive height threshold.
    """
    words = state.rng_words
    draws = 0
    cx, cy, limit = ZONE_GEOMETRY[state.zone]
    px, py, pz = state.player_xyz
    for attempt in range(1, 13):
        angle, words, n = _uniform(words, 0, 0x40c90fdb)
        draws += n
        radius, words, n = _uniform(words, state.low_radius_bits, state.high_radius_bits)
        draws += n
        angle = f.add(angle, 0)
        x, y = _candidate((px, py), angle, radius)
        dx, dy = f.sub(x, cx), f.sub(y, cy)
        distance = hypot_bits(dx, dy)
        if f.to_float(distance) > f.to_float(limit):
            # Original13563 uses limit*(delta/distance), not
            # (limit/distance)*delta; both f32 roundings are observable.
            y = f.add(cy, f.mul(limit, f.div(dy, distance)))
            x = f.add(cx, f.mul(limit, f.div(dx, distance)))
        nav = world.nav_probe(x, y)
        if nav.present and nav.in_bounds and nav.value:
            continue
        height = world.height(x, y)
        if height.found and f.to_float(f.sub(height.value_bits, pz) & ~f.SIGN) < 25:
            return WorldPositionResult139((x, y, height.value_bits), words, draws, attempt)
    angle, words, n = _uniform(words, 0, 0x40c90fdb)
    draws += n
    radius, words, n = _uniform(words, state.low_radius_bits, state.high_radius_bits)
    draws += n
    x, y = _candidate((px, py), f.add(angle, 0), radius)
    height = world.height(x, y)
    if height.found:
        z, branch = height.value_bits, 'unclamped_height'
    else:
        nearest = world.nearest_primary(x, y)
        if nearest.found:
            z, branch = nearest.xyz_bits[2], 'unclamped_nearest_primary_z'
        else:
            z, branch = world.fallback_height_bits, 'unclamped_world_fallback_z'
    return WorldPositionResult139((x, y, z), words, draws, 13, fallback_attempts=13, branch=branch)


def sample_spawn_position(state, world):
    """8740: heading bias,16 trials with2-unit shrinking, then full13563.

    Absent distance-map2368 rejects only nav byte1. Present distance-map
    rejects every nonzero byte. An absent/outside grid is not an obstacle;
    the full distance-map branch additionally requires an in-bounds cell.
    """
    vx, vy = state.velocity_xy
    moving = f.to_float(f.add(f.mul(vx, vx), f.mul(vy, vy))) > 4
    heading = atan2_bits(vy, vx) if moving else 0
    words = state.rng_words
    draws = shrinks = 0
    cx, cy, limit = ZONE_GEOMETRY[state.zone]
    px, py, pz = state.player_xyz
    for attempt in range(1, 17):
        biased = False
        if moving:
            output, words = next_u32_words(words)
            draws += 1
            chance = f.mul(f.from_u32(output >> 8), 0x33800000)
            biased = f.to_float(chance) < f.to_float(state.bias_probability_bits)
        if biased:
            angle, words, n = _uniform(words, 0xbf99999a, 0x3f99999a)
            angle = f.add(heading, angle)
        else:
            angle, words, n = _uniform(words, 0, 0x40c90fdb)
            angle = f.add(angle, 0)
        draws += n
        radius, words, n = _uniform(words, state.low_radius_bits, state.high_radius_bits)
        draws += n
        sine, cosine = sin_bits(angle), cos_bits(angle)
        while f.to_float(radius) >= 12:
            x = f.add(px, f.mul(cosine, radius))
            y = f.add(py, f.mul(sine, radius))
            distance = hypot_bits(f.sub(x, cx), f.sub(y, cy))
            if not f.to_float(distance) > f.to_float(f.add(limit, 0x41900000)):
                height = world.height(x, y)
                if height.found:
                    threshold = 8 if f.to_float(limit) < f.to_float(distance) else 25
                    if not f.to_float(f.sub(height.value_bits, pz) & ~f.SIGN) > threshold:
                        nav = world.nav_probe(x, y)
                        path = state.distance_map
                        if not nav.present:
                            allowed = True
                        elif path is None:
                            allowed = not nav.in_bounds or nav.value != 1
                        elif nav.in_bounds and nav.value:
                            allowed = False
                        elif path.field24 < 401:
                            allowed = True
                        elif not nav.in_bounds:
                            allowed = False
                        else:
                            if path.values_u16 is None:raise NotImplementedError('DistanceMap valuebacking isunknown onactuallyread branch')
                            if nav.index >= len(path.values_u16):
                                raise ValueError('Original8740 distance-map bounds trap domain')
                            cost = path.values_u16[nav.index]
                            direct = hypot_bits(f.sub(x, px), f.sub(y, py))
                            maximum = f.add(f.mul(direct, 0x3fc00000), 0x41400000)
                            allowed = cost != 65535 and f.to_float(f.from_u32(cost)) <= f.to_float(maximum)
                        if allowed:
                            return WorldPositionResult139((x, y, height.value_bits), words, draws, attempt, shrinks)
            radius = f.add(radius, 0xc0000000)
            shrinks += 1
    fallback = sample_random_position(WorldPositionInput139(state.zone, state.player_xyz,
        state.velocity_xy, state.low_radius_bits, state.high_radius_bits,
        state.bias_probability_bits, words), world)
    return WorldPositionResult139(fallback.position_bits, fallback.rng_words,
        draws + fallback.draws, 16, shrinks, fallback.attempts, 'fallback13563_' + fallback.branch)
