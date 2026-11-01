"""Bounded original135 main-tail queues, independent of the original runtime.

Complete caller-supplied backing bytes are preserved. Class resource execution11
and active secondary-area effects remain explicit continuations, never dropped.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f


class UnresolvedFrameSystem135(NotImplementedError):
    def __init__(self, message, partial=None):
        super().__init__(message)
        self.partial = partial


def _u(value, bits=32):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('Explicit unsigned word required')
    return value


def _raw(value, size):
    if type(value) is not str: raise TypeError('Complete raw hexadecimal record required')
    raw = bytes.fromhex(value)
    if len(raw) != size: raise ValueError(f'Complete{size}B record required')
    return raw


def _rows(storage, count, size):
    if type(storage) is not tuple or len(storage) > 512:
        raise ValueError('Explicit bounded full backing tuple required')
    _u(count)
    if count > len(storage): raise ValueError('Active prefix exceeds backing')
    return [_raw(x, size) for x in storage]


def _word(raw, offset): return struct.unpack_from('<I', raw, offset)[0]
def _guid(raw, offset=0): return struct.unpack_from('<Q', raw, offset)[0]


def _packed_guid(guid):
    bs = guid.to_bytes(8, 'little')
    return bytes([sum(1 << j for j,b in enumerate(bs) if b)]) + bytes(b for b in bs if b)


@dataclass(frozen=True)
class FrameQueueResult135:
    storage: tuple
    count: int
    packets: tuple
    status: str
    pending_index: int | None = None


def guard_owned_execution975(owned80, definitions88, dt_bits):
    """Original975 first scans all real owned definitions at byte84.

    No execution11 means the entire function exits without reading resource
    queues784..904, NPCs, RNG or even dt/now. Definitions and owned records must
    be explicit, including the original pointer word; no class-name inference.
    Returns the exact full owned bytes unchanged in this proven gate domain.
    """
    _u(dt_bits)
    if type(owned80) is not tuple or len(owned80) > 512 or type(definitions88) is not dict:
        raise ValueError('Explicit full owned vector and definition map required')
    for item in owned80:
        raw = _raw(item, 80); pointer = _word(raw, 0)
        if pointer not in definitions88:
            raise UnresolvedFrameSystem135('Owned definition bytes are unknown')
        definition = _raw(definitions88[pointer], 88)
        if definition[84] == 11:
            raise UnresolvedFrameSystem135('Execution11 class resources and queues require full975 continuation')
    return owned80


def tick_scheduled_spells38007(storage32, count, now_bits):
    """Full38007: due<=now stable32B removal and full10529/306 wire payload.

    Row+0 GUID, +8 due, +12 spell, +16..24 raw XYZ. Word+28 is unexamined
    opaque physical storage and is retained through exact memmove/tail reuse.
    No NPC, phase, ownership, sequence or RNG guards exist in this function.
    """
    _u(now_bits); rows = _rows(storage32, count, 32); now = f.to_float(now_bits)
    packets = []; index = 0
    while index < count:
        row = rows[index]
        # Ordered <=: either NaN retains the row, as in original38007.
        if not f.to_float(_word(row, 8)) <= now:
            index += 1; continue
        for j in range(index, count - 1): rows[j] = rows[j + 1]
        count -= 1
        guid = _packed_guid(_guid(row))
        payload = guid + guid + row[12:16] + b'\x00\x01\x00\x00\x40\x00' + row[16:28]
        packets.append((306, max(32, 64 if len(payload) > 32 else 32), payload.hex()))
    return FrameQueueResult135(tuple(x.hex() for x in rows), count, tuple(packets), 'scheduled_spells_complete')


def tick_secondary_areas2602(storage112, count, now_bits):
    """Full2602 expiry prefix and exact idle rows; active due effects stop.

    Expiry100 is tested before periodic104. Due live rows mutate104+=108
    before dispatch, so an unresolved result carries that precise partial state.
    Caller must not treat a pending status as completed2602.
    """
    _u(now_bits); rows = _rows(storage112, count, 112); now = f.to_float(now_bits)
    packets = []; index = 0
    def result(status, pending=None):
        return FrameQueueResult135(tuple(x.hex() for x in rows), count, tuple(packets), status, pending)
    while index < count:
        row = rows[index]
        if now >= f.to_float(_word(row, 100)):
            guid = _guid(row, 80)
            for j in range(index, count - 1): rows[j] = rows[j + 1]
            count -= 1
            # The stack retains removed row+0 across the length store. Its
            # null check branches to80660 after compaction, independently oflen.
            if _word(row, 0) == 0:
                return result('trap_null_secondary_definition_after_pop', index)
            if guid: packets.append((170, 32, guid.to_bytes(8, 'little').hex()))
            if count <= index: return result('secondary_expiry_idle_complete')
            continue
        if f.to_float(_word(row, 104)) <= now:
            raw = bytearray(row)
            struct.pack_into('<I', raw, 104, f.add(_word(row, 104), _word(row, 108)))
            rows[index] = bytes(raw)
            return result('pending_secondary_due_effect', index)
        index += 1
    return result('secondary_expiry_idle_complete')


def guard_claim_tick2573(storage88, count, phase2587):
    """Original2573 exits before any other read ifphase!=1 orclaimlen==0.

    Nonempty running claims require attraction/expiry/XP/UI continuation; all
    caller-owned raw88B backing remains explicit and is never silently cleared.
    """
    _u(phase2587, 8); rows = _rows(storage88, count, 88)
    if phase2587 == 1 and count:
        raise UnresolvedFrameSystem135('Running nonempty claims require full2573 continuation')
    return FrameQueueResult135(tuple(x.hex() for x in rows), count, (), 'claim_gate_complete')


def guard_terminal_tick49037(field400, phase2587, endless2568):
    """Exact49037 early exits; a true terminal path is never called complete.

    Triggering17119 movementstop, auxiliary helpers and1938 notification still
    require their ordered full state. Exposed as a precise pending boundary.
    """
    _u(field400); _u(phase2587, 8); _u(endless2568, 8)
    if field400 != 0 and phase2587 == 1 and endless2568 & 1 == 0:
        raise UnresolvedFrameSystem135('Terminal phase5,17119 movement andmessage continuation required')
    return phase2587
