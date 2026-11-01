"""Independent fixed135 nav-grid -> distance-map producer at the start of921.

The navigation grid is an explicit input, including independently produced
world.nav. No snapshot, original binary, host or original result is read here.
Distances count eight-neighbor steps; diagonals cannot cut occupied corners.
"""
from collections import deque
from dataclasses import dataclass
import math

from . import binary32 as f
from .world_position135 import DistanceMap135
from resource_spec.world_query135 import NavGrid135, QueryBoundsTrap135

UNREACHABLE = 65535
NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1),
             (1, 1), (1, -1), (-1, 1), (-1, -1))


class UnknownDistanceMap135(NotImplementedError):
    pass


@dataclass(frozen=True)
class ProducedDistanceMap135(DistanceMap135):
    """Actual Rc payload fields: Vec values, reachable count24, seed index20."""
    start_index: int

    def __post_init__(self):
        super().__post_init__()
        if type(self.start_index) is not int or not 0 <= self.start_index < len(self.values_u16):
            raise ValueError('Explicit valid distance-map seed index required')


@dataclass(frozen=True)
class DistanceMapUpdate135:
    distance_map: ProducedDistanceMap135 | None
    updated_at_bits: int
    recomputed: bool
    reason: str


def _word(value):
    if type(value) is not int or not 0 <= value <= f.MASK:
        raise ValueError('Explicit u32/binary32 word required')
    return value


def _cell_index(nav, player_xy_bits):
    if not isinstance(nav, NavGrid135) or len(player_xy_bits) != 2:
        raise ValueError('Explicit navigation grid and player XY required')
    for word in player_xy_bits:
        _word(word)
        if f.is_nan(word) or f.is_inf(word):
            raise UnknownDistanceMap135('Finite player coordinate domain required')
    dx, dy = (f.sub(word, origin) for word, origin in zip(player_xy_bits, nav.origin_xy_bits))
    if f.to_float(dx) < 0 or f.to_float(dy) < 0:
        return None
    # Finite subtraction may overflow; saturating conversion then fails bounds.
    def trunc_sat(word):
        value = f.to_float(word)
        if not value > 0:
            return 0
        return f.MASK if value >= f.MASK else math.trunc(value)
    x, y = trunc_sat(dx), trunc_sat(dy)
    return None if x >= nav.width or y >= nav.width else x + nav.width * y


def produce_distance_map135(nav, player_xy_bits):
    """Build exact u16 costs and reachable count for an in-bounds source cell.

    A blocked source still starts at zero. Every later visited cell and both
    orthogonal cells of a diagonal must have navigation byte0. Out-of-bounds
    player coordinates produce no map. Short physical navigation backing traps
    only when a candidate actually reads it, matching the original read order.
    """
    start = _cell_index(nav, player_xy_bits)
    if start is None:
        return None
    width = nav.width
    count = width * width
    if count > 1048576:
        raise UnknownDistanceMap135('Independent distance-map allocation watchdog')
    values = [UNREACHABLE] * count
    values[start] = 0
    queue = deque((start,))
    visited = 1

    def blocked(index):
        if index >= len(nav.values):
            raise QueryBoundsTrap135(index, len(nav.values), 'distance-map921')
        return nav.values[index] != 0

    while queue:
        current = queue.popleft()
        y, x = divmod(current, width)
        distance = values[current] + 1
        for dx, dy in NEIGHBORS:
            xx, yy = x + dx, y + dy
            if not 0 <= xx < width or not 0 <= yy < width:
                continue
            index = xx + width * yy
            if blocked(index) or values[index] != UNREACHABLE:
                continue
            if dx and dy and (blocked(xx + width * y) or blocked(x + width * yy)):
                continue
            if distance >= UNREACHABLE:
                raise UnknownDistanceMap135('u16 sentinel-collision path continuation is unresolved')
            values[index] = distance
            visited += 1
            queue.append(index)
    return ProducedDistanceMap135(tuple(values), visited, start)


def update_distance_map135(nav, player_xy_bits, now_bits, *, previous=None, updated_at_bits=0):
    """921 refresh gate: same-cell reuse, then strict >=binary32(0.2) age.

    Missing nav preserves the old map and update clock. An absent old map is
    rebuilt immediately. A due outside-player rebuild clears the old map and
    writes now, just like a successful rebuild. No Rc addresses are synthesized.
    """
    _word(now_bits); _word(updated_at_bits)
    if previous is not None and not isinstance(previous, ProducedDistanceMap135):
        raise ValueError('Explicit old produced payload including seed index20 required')
    if nav is None:
        return DistanceMapUpdate135(previous, updated_at_bits, False, 'navigation_absent')
    if previous is not None:
        current = _cell_index(nav, player_xy_bits)
        if current is not None and current == previous.start_index:
            return DistanceMapUpdate135(previous, updated_at_bits, False, 'same_cell')
        if not f.to_float(f.sub(now_bits, updated_at_bits)) >= f.to_float(0x3e4ccccd):
            return DistanceMapUpdate135(previous, updated_at_bits, False, 'refresh_not_due')
    produced = produce_distance_map135(nav, player_xy_bits)
    return DistanceMapUpdate135(produced, now_bits, True,
        'rebuilt' if produced is not None else 'outside_cleared')
