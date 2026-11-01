"""Independent fixed1351202 live-only aura cache and logical-field projection.

This slice admits inert kind0, unique1020 kind12, positive kind8 lives, and no
other aura producers (kind7, timed definitions38, active shield/owned-kind12,
or negative/control sources). The caller must establish that source domain;
neither absent sources nor original allocation bytes are inferred here.
"""
from dataclasses import dataclass

from . import binary32 as f
from .record_cells135 import cells135, put_u32, u32


class PendingResourceAura135(NotImplementedError):
    pass


def _word(value, bits=32):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('Explicit unsigned aura word required')
    return value


@dataclass(frozen=True)
class ResourceAuraState135:
    storage: tuple
    initialized2569: int

    def __post_init__(self):
        if not isinstance(self.storage, tuple) or len(self.storage) not in (0, 48):
            raise ValueError('Explicit empty or full48-slot aura owner required')
        _word(self.initialized2569, 8)
        for row in self.storage:
            cells135(row, 16)

    @property
    def capacity(self):
        return len(self.storage)

    @property
    def count(self):
        return len(self.storage)


@dataclass(frozen=True)
class ResourceAuraResult135:
    aura: ResourceAuraState135
    player_fields: tuple
    events: tuple
    field_writes: tuple


def _buffs(live_storage32, live_count, now_bits):
    if not isinstance(live_storage32, tuple) or not 0 <= live_count <= len(live_storage32) <= 4096:
        raise ValueError('Explicit bounded physical32B live owner required')
    rows = [cells135(row, 32) for row in live_storage32]
    active = []
    protection_seen = False
    for index, row in enumerate(rows[:live_count]):
        expiry = u32(row, 24, '1202 live expiry')
        # Ordered greater-than: NaN and already-expired rows contribute no aura
        # and do not require their other physical words to be initialized.
        if not f.to_float(expiry) > f.to_float(now_bits):
            continue
        kind = u32(row, 8, '1202 live kind')
        spell = u32(row, 20, '1202 live spell')
        if kind == 8:
            value = u32(row, 12, '1202 kind8 magnitude')
            if value & 0x7fffffff >= f.INF or f.to_float(value) < 0:
                raise PendingResourceAura135('Only finite nonnegative kind8 aura source restored')
        elif kind == 12:
            if spell != 1020 or protection_seen:
                raise PendingResourceAura135('Only unique producer1020 kind12 aura source restored')
            protection_seen = True
        elif kind != 0:
            raise PendingResourceAura135('Only kind0, protection1020 and unique nonnegative kind8 aura restored')
        active.append((index, kind, spell, expiry))
    by_spell = {}
    for _, kind, spell, expiry in active:
        if spell in by_spell:
            old = by_spell[spell]
            if spell == 774:
                old[1] = old[1] if f.to_float(old[1]) > f.to_float(expiry) else expiry
                old[2] = (old[2] + 1) & f.MASK
                continue
            if kind not in (0, 12) or old[3] not in (0, 12):
                raise PendingResourceAura135('Duplicate kind8 dominance/priority requires its full1202 continuation')
            # Ordinary kind0 duplicate effective magnitudes are both0. The
            # earliest unexpired row wins before the aggregation loop, so a
            # later expiry must not replace the first expiry in this case.
            continue
        by_spell[spell] = [spell, expiry, 1, kind]
    return tuple(tuple(row[:3]) for row in by_spell.values())[:32]


def _present(row):
    marker = u32(row, 0, '1202 previous aura tag')
    if marker not in (0, 1):
        raise PendingResourceAura135('Canonical prior aura0/1 tag domain required')
    return marker == 1


def _spell(row):
    return u32(row, 4, '1202 prior aura spell') if _present(row) else 0


def _flags(rows, group):
    value = 0
    for index in range(group * 8, group * 8 + 8):
        if _present(rows[index]):
            value |= (9 if index < 32 else 8) << (4 * (index & 7))
    return value


def _applications(rows, group):
    value = 0
    for index in range(group * 4, group * 4 + 4):
        if _present(rows[index]):
            count = u32(rows[index], 12, '1202 prior aura applications')
            if count:
                value |= (min(count, 255) - 1) << (8 * (index & 3))
    return value


def rebuild_resource_aura135(live_storage32, live_count, now_bits,
        previous: ResourceAuraState135, player_fields):
    """Rebuild the original48-slot cache and ordered field writes in this slice.

    Slot0..31 receives the original ordered positive-buff aggregation. Slots
    32..47 remain absent because the separate negative/source vector is empty
    in the declared domain. New inactive slots contain only a known zero tag;
    their other12 bytes are unknown allocation storage, never zero-filled.
    """
    _word(now_bits)
    if now_bits & 0x7fffffff >= f.INF:
        raise PendingResourceAura135('Finite original aura now domain required')
    if not isinstance(previous, ResourceAuraState135):
        raise TypeError('Explicit prior aura owner required')
    if not isinstance(player_fields, tuple):
        raise ValueError('Explicit logical-field tuple required')
    fields = dict(player_fields)
    if len(fields) != len(player_fields):
        raise ValueError('Duplicate logical-field key')
    for key, value in fields.items():
        _word(key, 16); _word(value)
    buffs = _buffs(live_storage32, live_count, now_bits)
    rows = [[None] * 16 for _ in range(48)]
    for row in rows:
        put_u32(row, 0, 0)
    for row, (spell, expiry, count) in zip(rows, buffs):
        for offset, value in ((0, 1), (4, spell), (8, expiry), (12, count)):
            put_u32(row, offset, value)
    initialized = len(previous.storage) == 48 and bool(previous.initialized2569 & 1)
    old = previous.storage if initialized else ()
    writes = []
    for slot, row in enumerate(rows):
        spell = _spell(row)
        if not initialized or spell != _spell(old[slot]):
            writes.append((47 + slot, spell))
    for group in range(6):
        flags = _flags(rows, group)
        if not initialized or flags != _flags(old, group):
            writes.append((95 + group, flags))
    for group in range(12):
        applications = _applications(rows, group)
        if not initialized or applications != _applications(old, group):
            writes.append((113 + group, applications))
    fields.update(writes)
    aura = ResourceAuraState135(tuple(tuple(row) for row in rows), 1)
    # These are logical-write descriptors, not original queue events or packets.
    events = tuple(('aura_field_write', key, value) for key, value in writes)
    return ResourceAuraResult135(aura, tuple(sorted(fields.items())), events, tuple(writes))
