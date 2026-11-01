"""Independent fixed135 special40 target update and exact quiet continuation.

The full original2376 also creates due NPCs and localized announcements. Those
branches remain explicit boundaries here, rather than dropping their objects.
Complete40B backing and scalar words are caller inputs; no original snapshot,
function, executable or IO is consulted by this production module.
"""
from dataclasses import dataclass, replace
import struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .record_cells135 import cells135,encode_row,u32,u64


class UnknownSpecial2376_135(NotImplementedError):
    pass


def _word(value, bits=32):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('Explicit unsigned scalar required')
    return value


def _total_key(word):
    # Original signed i32 comparison after total-order sign transformation.
    word ^= 0x7fffffff if word & 0x80000000 else 0
    return word - (1 << 32) if word & 0x80000000 else word


@dataclass(frozen=True)
class SpecialState2376_135:
    storage: tuple
    count: int
    now_bits: int
    player_xy_bits: tuple
    protection2576: int
    navigation2564: int
    announced2565: int
    selected392: int
    target396: int
    announcement_time2392_bits: int

    def __post_init__(self):
        if type(self.storage) is not tuple or type(self.count) is not int or not 0 <= self.count <= len(self.storage) <= 512:
            raise ValueError('Explicit active prefix and complete40B capacity required')
        for row in self.storage:
            cells135(row,40)
        if type(self.player_xy_bits) is not tuple or len(self.player_xy_bits) != 2:
            raise ValueError('Explicit player XY binary32 words required')
        for value in (self.now_bits, *self.player_xy_bits, self.selected392, self.target396, self.announcement_time2392_bits):
            _word(value)
        for value in (self.protection2576, self.navigation2564, self.announced2565):
            _word(value, 8)


@dataclass(frozen=True)
class SpecialResult2376_135:
    state: SpecialState2376_135
    packets: tuple
    status: str


def _target(state):
    active = [i for i, row in enumerate(state.storage[:state.count]) if u64(row,0,'special2376.marker') != 0]
    if not active:
        # Strict comparison retains the first equal total-order deadline.
        return min(range(state.count), key=lambda i: _total_key(u32(state.storage[i],32,'special2376.deadline')))
    def distance(index):
        x,y=u32(state.storage[index],16,'special2376.x'),u32(state.storage[index],20,'special2376.y')
        if any(v & 0x7fffffff >= f.INF for v in (x, y, *state.player_xy_bits)):
            raise UnknownSpecial2376_135('Active target nonfinite coordinate distance ordering remains unverified')
        dx, dy = f.sub(x, state.player_xy_bits[0]), f.sub(y, state.player_xy_bits[1])
        return _total_key(sqrt_bits(f.add(f.mul(dx, dx), f.mul(dy, dy))))
    return min(active, key=distance)


def tick_special2376_135(state):
    """Complete2376 for undued/all-active records and quiet navigation paths.

    Due zero-marker records and text-emitting paths are rejected explicitly.
    Existing40B objects and inactive capacity bytes remain exactly preserved.
    The disabled-navigation clear548 path is fully produced, including payload.
    """
    if not isinstance(state, SpecialState2376_135):
        raise TypeError('Explicit SpecialState2376_135 required')
    if state.protection2576 or not state.count:
        return SpecialResult2376_135(state, (), 'special_outer_gate_complete')
    for index, row in enumerate(state.storage[:state.count]):
        if u64(row,0,'special2376.marker') == 0 and f.to_float(state.now_bits) >= f.to_float(u32(row,32,'special2376.deadline')):
            raise UnknownSpecial2376_135(f'Due inactive special{index} requires NPC production and complete1525 continuation')
    target = _target(state)
    if state.navigation2564 == 0:
        final = replace(state, selected392=1, target396=target, announced2565=0)
        if not state.announced2565:
            return SpecialResult2376_135(final, (), 'special_selection_quiet_complete')
        payload = struct.pack('<5I', 99, *state.player_xy_bits, 6, 0) + b'\0'
        return SpecialResult2376_135(final, ((548, 32, payload.hex()),), 'special_navigation_clear_complete')
    elapsed = f.sub(state.now_bits, state.announcement_time2392_bits)
    if state.selected392 and state.target396 == target and state.announced2565 & 1 and not f.to_float(elapsed) > 300:
        return SpecialResult2376_135(state, (), 'special_announcement_suppressed_complete')
    raise UnknownSpecial2376_135('Selected-target localized548 announcement producer remains explicit pending')


def projection_special2376_135(result):
    s = result.state
    return dict(storage=[encode_row(cells135(row,40)) for row in s.storage], count=s.count,
                selected392=s.selected392, target396=s.target396, announced2565=s.announced2565,
                announcement_time2392_bits=s.announcement_time2392_bits,
                packets=[list(value) for value in result.packets], status=result.status)
