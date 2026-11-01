"""Explicit same-state tail domains, not a substitute for active producers.

The constructor starts these vectors empty. The composition retains their
state and refuses unknown producers; it never supplies empty vectors to an
original program. Full component functions own their separate verified slices.
"""
from dataclasses import dataclass
from .frame_systems135 import UnresolvedFrameSystem135


@dataclass(frozen=True)
class TailDomains135:
    active84_storage: tuple = ()
    active84_count: int = 0
    deadline32_storage: tuple = ()
    deadline32_count: int = 0
    secondary112_storage: tuple = ()
    secondary112_count: int = 0
    claims88_storage: tuple = ()
    claims88_count: int = 0
    special40_storage: tuple = ()
    special40_count: int = 0
    field400: int = 0
    flag2568: int = 0
    gate2579: int = 0

    def __post_init__(self):
        for name, size in (('active84', 84), ('deadline32', 32), ('secondary112', 112),
                ('claims88', 88), ('special40', 40)):
            storage, count = getattr(self, name + '_storage'), getattr(self, name + '_count')
            if type(storage) is not tuple or type(count) is not int or not 0 <= count <= len(storage) <= 512:
                raise ValueError('Explicit full tail backing and active count required')
            if any(len(bytes.fromhex(raw)) != size for raw in storage):
                raise ValueError('Tail record stride differs')
        if type(self.field400) is not int or not 0 <= self.field400 < 1 << 32:
            raise ValueError('Explicit field400 word required')
        for value in (self.flag2568, self.gate2579):
            if type(value) is not int or not 0 <= value <= 255:
                raise ValueError('Explicit tail byte flags required')


def guard_extra916(timed_records, active_count):
    """916 checks timed12 expiry before active84; both must be truly empty.

    These are the actual vectors, not a class-based absence guess. Nonempty
    source scheduling requires the original producer and explicit continuation.
    """
    if type(timed_records) is not tuple or type(active_count) is not int or active_count < 0:
        raise ValueError('Explicit timed and active source counts required')
    if timed_records or active_count:
        raise UnresolvedFrameSystem135('Active916 timed/extra sources need a composition continuation')


def guard_special2376(count, flag2576):
    """Full2376 outer block exits if flag2576!=0 orG1924==0.

    Both event creation and subsequent target selection are inside that block.
    Nonempty unprotected40B events remain an explicit unresolved producer.
    """
    if type(count) is not int or count < 0 or type(flag2576) is not int or not 0 <= flag2576 <= 255:
        raise ValueError('Explicit event count and phase byte required')
    if count and not flag2576:
        raise UnresolvedFrameSystem135('Active2376 event production and target selection require continuation')


def projection(state):
    result = {}
    for name in ('active84', 'deadline32', 'secondary112', 'claims88', 'special40'):
        storage, count = getattr(state, name + '_storage'), getattr(state, name + '_count')
        result[name] = dict(capacity=len(storage), records_hex=list(storage[:count]))
    result.update(field400=state.field400, flag2568=state.flag2568, gate2579=state.gate2579)
    return result
