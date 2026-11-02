"""Independent fixed135 ordinary melee planning with real nav/path/height input.

The caller updates the distance map once before this phase. Logical entity Z
and movement-message projected Z are separate outputs. This module reads no
original code, snapshots, resource files or differential evidence.
"""
from dataclasses import dataclass, replace
import math

from . import binary32 as f
from .ai135 import (AiFrame135, AiResult135, position, unit_position,
    _validate, _get, _put, _float, _speed, _attack, _maximum, _distance)
from .ai_trig135 import sin_bits, cos_bits
from .distance_map135 import ProducedDistanceMap135, NEIGHBORS
from .incoming135 import IncomingState135, resolve_incoming_prefix
from .record_cells135 import cells135, u64, encode_row
from .demo_ai135 import demo_bindings135,begin_demo_expiry135,finish_demo_expiry135
from resource_spec.world_query135 import WorldQueries135, probe_nav, QueryBoundsTrap135


@dataclass(frozen=True)
class MovementGeometry135:
    target_id: int
    start_xyz_bits: tuple
    end_xyz_bits: tuple
    duration_bits: int
    milliseconds: int
    stop_flag: int


@dataclass(frozen=True)
class WorldAiResult135(AiResult135):
    movement_geometry: tuple = ()
    routing: tuple = ()


@dataclass(frozen=True)
class WorldAiPlan135:
    """921 ordinary planning output before any queued incoming is consumed.

    records contains every planning write, including early360 expiry. The
    separate demo bindings/removals remain pending until the late4543 drain.
    incoming binds the original clock/playerXY and these planned unit motions;
    HP/shields/totals are still the input values. No1073 prefix has run.
    """
    records: tuple
    incoming: IncomingState135
    attacks: tuple
    movements: tuple
    movement_geometry: tuple
    routing: tuple
    demo_bindings: tuple
    demo_expirations: tuple


def segment_fraction135(nav, start_xy, end_xy):
    """29894: ceil(distance/0.3) samples and the last traversable f32 fraction.

    Only bit0 blocks entry. An initial blocked run can be left; once a sampled
    cell clears its bit0, later occupied cells block. Outside grid samples are0.
    """
    length = _distance(start_xy, end_xy)
    if f.to_float(length) < f.to_float(0x3a83126f):
        return 0x3f800000
    first = probe_nav(nav, *start_xy)
    occupied = first.value if first.in_bounds else 0
    count = math.ceil(f.to_float(f.div(length, 0x3e99999a)))
    if count > 1000000:
        raise ValueError('Independent nav segment sample watchdog')
    if count <= 0:
        return 0x3f800000
    dx, dy = (f.sub(b, a) for a, b in zip(start_xy, end_xy))
    last = 0
    divisor = f.from_u32(count)
    for index in range(1, count + 1):
        ratio = f.div(f.from_u32(index), divisor)
        xy = (f.add(start_xy[0], f.mul(dx, ratio)), f.add(start_xy[1], f.mul(dy, ratio)))
        sample = probe_nav(nav, *xy)
        value = sample.value if sample.in_bounds else 0
        if not ((occupied | ~value) & 1):
            return last
        occupied &= value
        last = ratio
    return 0x3f800000


def descend_distance_map135(path, width, current):
    """28963: first minimum finite eight-neighbor; require strict descent."""
    if not width:
        raise ValueError('Original28963 nonzero-width domain required')
    y, x = divmod(current, width)
    best = None
    for dx, dy in NEIGHBORS:
        xx, yy = x + dx, y + dy
        if not 0 <= xx < width or not 0 <= yy < width:
            continue
        index = xx + width * yy
        if index >= len(path.values_u16):
            raise QueryBoundsTrap135(index, len(path.values_u16), 'distance-descent28963')
        cost = path.values_u16[index]
        if cost != 65535 and (best is None or cost < best[0]):
            best = cost, index
    if best is None:
        return None
    if current >= len(path.values_u16):
        raise QueryBoundsTrap135(current, len(path.values_u16), 'distance-descent28963')
    cost = path.values_u16[current]
    return best[1] if cost == 65535 or best[0] < cost else None


def route_destination135(nav, path, current_xyz, planned_xyz):
    """921 inline: when blocked, use cell centres with at most40 lookahead steps."""
    if nav is None or path is None:
        return planned_xyz, 'navigation_or_map_absent'
    if f.to_float(segment_fraction135(nav, current_xyz[:2], planned_xyz[:2])) >= 1:
        return planned_xyz, 'direct_clear'
    point = probe_nav(nav, *current_xyz[:2])
    if not point.in_bounds:
        return planned_xyz, 'source_outside_navigation'
    index = point.index
    if index >= len(path.values_u16):
        raise QueryBoundsTrap135(index, len(path.values_u16), 'distance-route921')
    if path.values_u16[index] == 65535:
        candidate = descend_distance_map135(path, nav.width, index)
        if candidate is None:
            return planned_xyz, 'no_reachable_neighbor'
        index = candidate

    def centre(cell):
        yy, xx = divmod(cell, nav.width)
        return (f.add(nav.origin_xy_bits[0], f.add(f.from_u32(xx), 0x3f000000)),
                f.add(nav.origin_xy_bits[1], f.add(f.from_u32(yy), 0x3f000000)))
    selected = centre(index)
    if index != path.start_index:
        candidate = descend_distance_map135(path, nav.width, index)
        for _ in range(40):
            if candidate is None:
                break
            xy = centre(candidate)
            if f.to_float(_distance(current_xyz[:2], xy)) > 14:
                break
            if f.to_float(segment_fraction135(nav, current_xyz[:2], xy)) < 1:
                break
            selected = xy
            if candidate == path.start_index:
                break
            candidate = descend_distance_map135(path, nav.width, candidate)
    return (*selected, current_xyz[2]), 'flow_cell_centre'


def _message_xyz(world, xyz):
    height = world.height(xyz[0], xyz[1])
    if height.found:
        return xyz[0], xyz[1], height.value_bits
    nearest = world.nearest_primary(xyz[0], xyz[1])
    return (xyz[0], xyz[1], nearest.xyz_bits[2]) if nearest.found else xyz


def _geometry(world, guid, start, end, duration):
    if not f.to_float(duration) > 0:
        return MovementGeometry135(guid, start, start, duration, 1, 3)
    value = f.to_float(f.mul(duration, 0x447a0000))
    milliseconds = 0 if not value > 0 else f.MASK if value >= f.MASK else math.trunc(value)
    return MovementGeometry135(guid, _message_xyz(world, start), _message_xyz(world, end),
        duration, max(1, milliseconds), 0)


def plan_world_ordinary_units135(state: AiFrame135, world, *, distance_map=None):
    """Plan every admitted ordinary unit without consuming incoming attacks.

    All existing ordinary/local/finite source restrictions stay explicit. Nav
    changes logical XY; terrain/nearest-height queries change only message XYZ.
    Unknown physical padding remains None through record_cells135. The caller
    can now plan guardian owners before draining921's ordered incoming queue.
    """
    if not isinstance(world, WorldQueries135):
        raise TypeError('Explicit independently resolved WorldQueries135 required')
    if distance_map is not None and not isinstance(distance_map, ProducedDistanceMap135):
        raise TypeError('Distance map requires explicit seed20 and reachable count24')
    if len(state.records) > 512 or len(state.player_xyz_bits) != 3:
        raise ValueError('Frame budget/input shape')
    if state.other_incoming_sources_absent is not True or state.incoming_item_effects:
        raise ValueError('Explicit absent unmodeled incoming/item sources required')
    if any(x.tag not in (7, 12) for x in state.incoming.buffs):
        raise ValueError('Only known shield7/protection12 incoming buffs accepted')
    if any(x.tag != 54 or x.byte4 != 1 for x in state.incoming.modifiers):
        raise ValueError('Only known effective-armor54 variant1 accepted')
    if state.incoming.mode_2574 not in (0, 1) or (state.incoming.mode_2574 and state.incoming.phase_2579 == 2):
        raise ValueError('Remote party interpolation remains unresolved')
    if any(not -1e20 < f.to_float(x) < 1e20 for x in (state.now_bits, state.dt_bits, *state.player_xyz_bits)):
        raise ValueError('Finite bounded frame inputs required')
    raws = [cells135(row) for row in state.records]
    demo_bindings=demo_bindings135(raws,state.known_demo_statuses)
    if demo_bindings and state.incoming.mode_2574:
        raise ValueError('Demo AI remote-party target/owner selection remains unresolved')
    for raw in raws:
        _validate(raw, state.now_bits,known_demo=demo_bindings.get(u64(raw,112))if demo_bindings else None)
    if state.incoming.mode_2574 and any(_get(row, 280) != 0 for row in raws):
        raise ValueError('Only local owner0 routing is restored')
    now, attacks, movements, geometries, routing = state.now_bits, [], [], [], []
    demo_removals=[]
    now_value = f.to_float(now)
    for raw in raws:
        removal=begin_demo_expiry135(raw,demo_bindings.get(u64(raw,112))if demo_bindings else None,now)
        if removal is not None:demo_removals.append(removal)
        if _float(raw, 400) > now_value:
            continue
        pos = position(raw, now)
        timer = f.sub(_get(raw, 352), state.dt_bits); _put(raw, 352, timer)
        guid = u64(raw, 112, consumer='ai_world135.guid')
        distance = _distance(pos, state.player_xyz_bits)
        if f.to_float(distance) <= _float(raw, 308):
            if _float(raw, 344) > 0 and now_value < f.to_float(f.add(_get(raw, 340), _get(raw, 344))):
                for index in range(3):
                    _put(raw, 316 + 4 * index, pos[index]); _put(raw, 328 + 4 * index, pos[index])
                _put(raw, 340, now); _put(raw, 344, 0)
                movements.append((guid, pos, pos, 0)); geometries.append(_geometry(world, guid, pos, pos, 0))
            if f.to_float(timer) <= 0 and _float(raw, 404) <= now_value:
                _put(raw, 352, _get(raw, 304)); attacks.append((guid, _attack(raw, now)))
            continue
        if _float(raw, 348) > now_value:
            continue
        angle = f.add(_get(raw, 396), 0x3e19999a); _put(raw, 396, angle)
        radius = _maximum(f.mul(_get(raw, 308), 0x3f4ccccd), 0x3fc00000)
        dest = (f.add(state.player_xyz_bits[0], f.mul(radius, cos_bits(angle))),
                f.add(state.player_xyz_bits[1], f.mul(radius, sin_bits(angle))), state.player_xyz_bits[2])
        length = _distance(pos, dest)
        if f.to_float(length) > 14:
            factor = f.div(0x41600000, length)
            dest = (f.add(pos[0], f.mul(f.sub(dest[0], pos[0]), factor)),
                    f.add(pos[1], f.mul(f.sub(dest[1], pos[1]), factor)), pos[2])
        dest, branch = route_destination135(world.nav, distance_map, pos, dest)
        routing.append((guid, branch))
        duration = f.div(_distance(pos, dest), _maximum(_speed(raw, now), 0x3f000000))
        for index in range(3):
            _put(raw, 316 + 4 * index, pos[index]); _put(raw, 328 + 4 * index, dest[index])
        _put(raw, 340, now); _put(raw, 344, duration)
        deadline = _maximum(duration, 0x3e800000)
        deadline = 0x3f333333 if f.to_float(deadline) > .7 else deadline
        _put(raw, 348, f.add(now, deadline))
        movements.append((guid, pos, dest, duration)); geometries.append(_geometry(world, guid, pos, dest, duration))
    incoming = replace(state.incoming, now_bits=now, player_x_1504_bits=state.player_xyz_bits[0],
        player_y_1508_bits=state.player_xyz_bits[1], units=tuple(unit_position(raw) for raw in raws))
    return WorldAiPlan135(tuple(encode_row(raw) for raw in raws), incoming,
        tuple(attacks), tuple(movements), tuple(geometries), tuple(routing),
        tuple(demo_bindings.values()), tuple(demo_removals))


def finish_world_ordinary_plan135(plan, incoming, *, records=None):
    """Finish921's late demo queue on the caller's current physical backing.

    records=None chooses the unchanged planning backing for the old nonfatal
    adapter. After a callback/stop writes entity positions, the caller must
    pass those actual records explicitly. GUID order/count must match the
    plan; collection changes require their own unresolved continuation. The
    plan records never overwrite coordinates in the supplied backing.
    """
    if not isinstance(plan, WorldAiPlan135) or not isinstance(incoming, IncomingState135):
        raise TypeError('Explicit ordinary plan and post-drain incoming owner required')
    if records is None:
        records = plan.records
    if type(records) is not tuple or len(records) != len(plan.records):
        raise ValueError('Post-drain ordinary vector count/order continuation is unresolved')
    raws = [cells135(row) for row in records]
    if tuple(u64(raw,112,consumer='ai_world135.finish_owner') for raw in raws) != tuple(
            u64(raw,112,consumer='ai_world135.planned_owner') for raw in plan.records):
        raise ValueError('Post-drain ordinary GUID order differs from its plan')
    bindings = {row.guid: row for row in plan.demo_bindings}
    declarations, packets, fields = finish_demo_expiry135(raws, bindings, plan.demo_expirations)
    return WorldAiResult135(tuple(encode_row(raw) for raw in raws), incoming,
        plan.attacks, plan.movements,
        ('encoded_movement_and_hit_packets', 'incoming_registry_history_aura_metadata'),
        movement_geometry=plan.movement_geometry, routing=plan.routing,
        demo_expirations=plan.demo_expirations, demo_aura_packets169=packets,
        demo_aura_fields=fields, demo_statuses=declarations)


def drain_world_ordinary_plan135(plan):
    """Existing restricted nonfatal scalar drain, retaining every queue item.

    This is not full1073 callbacks/history/fatal completion. A root controller
    with restored callbacks instead drains plan.attacks in order, then calls
    finish_world_ordinary_plan135 with its post-callback incoming and backing.
    """
    if not isinstance(plan, WorldAiPlan135):
        raise TypeError('Explicit ordinary planning result required')
    incoming = plan.incoming
    for guid, amount in plan.attacks:
        result = resolve_incoming_prefix(incoming, amount, guid)
        if result.stage not in ('scalar_nonfatal_projection', 'phase_guard', 'protection_guard', 'active_raw_buff12_guard'):
            raise ValueError('Incoming callback/death boundary: ' + result.stage)
        incoming = result.state
    return finish_world_ordinary_plan135(plan, incoming)


def update_world_ordinary_units135(state: AiFrame135, world, *, distance_map=None):
    """Compatible nonfatal plan→scalar drain→late demo finish adapter.

    This preserves the previous default return fields, guards and boundaries.
    It does not claim a complete921, guardian queue or fatal continuation.
    """
    return drain_world_ordinary_plan135(
        plan_world_ordinary_units135(state, world, distance_map=distance_map))
