"""Fixed139 incoming48 history ring; not complete incoming1076.

Source data are explicit current139 inputs. The48B layout and pruning/writes
are re-bound to1076; old runtime acceptance is not inherited.

Each backing byte is either known or explicitly uninitialized. Resource pointer
words written by an append remain unknown addresses, while their byte strings
are independently supplied and compared. Existing unwritten padding is kept.
No target/runtime/assets or IO are used by this module.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f

STRIDE = 48
FALLBACK = {
    0: ('Melee', 'INV_Sword_04'),
    1: ('Spell', 'Spell_Shadow_ShadowBolt'),
    2: ('Boss mechanic', 'Spell_Fire_SelfDestruct'),
}


@dataclass(frozen=True)
class IncomingHistory139:
    capacity: int
    head: int
    count: int
    storage: tuple
    strings: tuple
    # Per-byte provenance: fixture / resource_pointer / allocator_unwritten.
    provenance: tuple

    def __post_init__(self):
        if not (0 <= self.capacity <= 4096 and 0 <= self.count <= self.capacity):
            raise ValueError('Invalid history capacity/count')
        if self.head < 0 or (self.capacity and self.head >= self.capacity) or (not self.capacity and self.head):
            raise ValueError('Invalid history head')
        if len(self.storage) != self.capacity or len(self.strings) != self.capacity or len(self.provenance) != self.capacity:
            raise ValueError('Full physical history backing required')
        for raw, origin in zip(self.storage, self.provenance):
            if len(raw) != 48 or len(origin) != 48:
                raise ValueError('History record size differs')
            if any(x is not None and (type(x) is not int or not 0 <= x <= 255) for x in raw):
                raise ValueError('Invalid physical byte')
            if any(x is None and why not in ('resource_pointer', 'allocator_unwritten') for x, why in zip(raw, origin)):
                raise ValueError('Unknown byte needs exact provenance')


def from_raw_storage(storage, head, count):
    raw = tuple(tuple(bytes.fromhex(x)) for x in storage)
    # Controlled fixture strings must be valid empty borrowed slices.
    for row in raw:
        if any(struct.unpack_from('<I', bytes(row), x)[0] for x in (4, 12, 20)):
            raise ValueError('Fixture strings require explicit resolved content')
    return IncomingHistory139(len(raw), head, count, raw, (('', '', ''),) * len(raw),
                              (('fixture',) * 48,) * len(raw))


def _grow(state):
    old_cap, head, length = state.capacity, state.head, state.count
    new_cap = max(old_cap * 2, 4)
    if new_cap > 4096:
        raise ValueError('History research capacity budget')
    storage = list(state.storage) + [(None,) * 48] * (new_cap - old_cap)
    strings = list(state.strings) + [None] * (new_cap - old_cap)
    origin = list(state.provenance) + [('allocator_unwritten',) * 48] * (new_cap - old_cap)
    # Original deque growth branch: strict prefix > suffix; ties move the tail.
    if head > old_cap - length:
        prefix = old_cap - head
        suffix = length - prefix
        if prefix > suffix and new_cap - old_cap >= suffix:
            storage[old_cap:old_cap + suffix] = storage[:suffix]
            strings[old_cap:old_cap + suffix] = strings[:suffix]
            origin[old_cap:old_cap + suffix] = origin[:suffix]
        else:
            new_head = new_cap - prefix
            storage[new_head:new_cap] = storage[head:old_cap]
            strings[new_head:new_cap] = strings[head:old_cap]
            origin[new_head:new_cap] = origin[head:old_cap]
            head = new_head
    return IncomingHistory139(new_cap, head, length, tuple(storage), tuple(strings), tuple(origin))


def append_incoming_history(state, *, now_bits, damage_bits, absorbed_bits,
                            hp_after_prefix_bits, maximum_hp_bits, category=0,
                            source_label='', source_classification=4,
                            resolved_spell=None):
    """Prune and append exactly one already-resolved incoming record.

    Caller owns entry guards, armor/shields, source lookup and real resource
    loading. `resolved_spell=None` explicitly chooses the actual fallback path;
    it does not mean an unresolved nonzero spell may be silently omitted.
    """
    for x in (now_bits, damage_bits, absorbed_bits, hp_after_prefix_bits, maximum_hp_bits, category):
        if type(x) is not int or not 0 <= x <= 0xffffffff:
            raise ValueError('Expected exact binary32/u32 words')
    if type(source_classification) is not int or not 0 <= source_classification <= 255:
        raise ValueError('Source classification byte')
    if not isinstance(source_label, str):
        raise ValueError('Resolved source label required')
    if resolved_spell is None:
        name, icon = FALLBACK.get(category, FALLBACK[0])
    else:
        if not isinstance(resolved_spell, tuple) or len(resolved_spell) != 2 or not all(isinstance(x, str) for x in resolved_spell):
            raise ValueError('Resolved spell name/icon pair required')
        name, icon = resolved_spell
    metadata = (source_label, name, icon)
    for text in metadata:
        if len(text.encode('utf-8')) > 1048576:
            raise ValueError('Metadata budget')
    head, count = state.head, state.count
    cutoff = f.add(now_bits, 0xc1200000)  # now + (-10.0), one f32 operation
    while count:
        row = state.storage[head]
        if any(x is None for x in row[24:28]):
            raise ValueError('Oldest timestamp must be resolved')
        stamp = struct.unpack('<I', bytes(row[24:28]))[0]
        if not (count > 399 or f.to_float(stamp) < f.to_float(cutoff)):
            break
        count -= 1
        head += 1
        if head >= state.capacity:
            head -= state.capacity
    state = IncomingHistory139(state.capacity, head, count, state.storage, state.strings, state.provenance)
    if count == state.capacity:
        state = _grow(state)
    slot = state.head + state.count
    if slot >= state.capacity:
        slot -= state.capacity
    raw = list(state.storage[slot])
    origin = list(state.provenance[slot])
    # Actual pointer bytes are retained by the oracle; content is compared
    # separately. A new pointer is never asserted to equal numeric zero.
    for offset, value in zip((0, 8, 16), metadata):
        raw[offset:offset + 4] = [None] * 4
        origin[offset:offset + 4] = ['resource_pointer'] * 4
        raw[offset + 4:offset + 8] = struct.pack('<I', len(value.encode('utf-8')))
        origin[offset + 4:offset + 8] = ['semantic'] * 4
    raw[24:44] = struct.pack('<5I', now_bits, damage_bits, absorbed_bits, hp_after_prefix_bits, maximum_hp_bits)
    origin[24:44] = ['semantic'] * 20
    raw[44:46] = [source_classification, int(category == 2)]
    origin[44:46] = ['semantic'] * 2
    # +46..47 really are not written: preserve known prior bytes or their
    # allocator-unwritten provenance. Do not call all padding unspecified.
    storage = list(state.storage); storage[slot] = tuple(raw)
    strings = list(state.strings); strings[slot] = metadata
    provenance = list(state.provenance); provenance[slot] = tuple(origin)
    return IncomingHistory139(state.capacity, state.head, state.count + 1,
                              tuple(storage), tuple(strings), tuple(provenance))


def projection(state):
    active = []
    for logical in range(state.count):
        slot = (state.head + logical) % state.capacity
        active.append(dict(slot=slot, strings=list(state.strings[slot])))
    return dict(header=dict(capacity=state.capacity, head=state.head, count=state.count),
                storage=[list(x) for x in state.storage], provenance=[list(x) for x in state.provenance],
                active=active)
