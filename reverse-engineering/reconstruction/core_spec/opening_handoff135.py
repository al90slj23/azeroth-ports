"""Lossless independent opening -> gameplay ownership boundary for fixed135.

The input is the actual result of opening135, never an original memory image
or a constructor with its phase overwritten. All six physical vectors and the
explicit world stay owned by the result, including inactive slots and None
allocator bytes. Collection gets a semantic view of the existing pickups; the
physical pickup owner remains authoritative for unwritten/partly-known bytes.
This adapter performs no IO and does not claim that pending consumers ran.
"""
from dataclasses import asdict, dataclass

from .currency134 import CurrencyState
from .death_pickup135 import CollectionState135, DeathContext135
from .opening135 import (EmptyOpeningInput135, OpeningState135, initialize_empty_opening,
    initialize_absent_companion_opening)
from .opening_entities135 import PhysicalVector135
from .opening_npc_pickups135 import OpeningVector135
from .pickups134 import PickupRecord


VECTOR_STRIDES = (('companions', 88), ('units', 424), ('pickups', 56),
                  ('special', 40), ('windows', 8), ('boundaries', 8))


class PendingOpeningHandoff135(NotImplementedError):
    """An actual consumer read, rather than unused backing, is unknown."""


@dataclass(frozen=True)
class PendingConsumer135:
    owner: str
    consumer: str
    requirement: str


# These are ownership/composition obligations. They are not substitutes for
# executing the components, and a component can be implemented independently
# before its continuation is wired into the same gameplay state.
PENDING_CONSUMERS = (
    PendingConsumer135('units424', 'headless135 ordered combat/AI/spawn',
        'Consume None-aware records using real capacity and explicit world queries.'),
    PendingConsumer135('pickups56', '2862 kind2 collection and physical backing writes',
        'Keep kind2 records idle until their real guard dispatches; retain +4 and inactive slots.'),
    PendingConsumer135('companions88', 'companion movement/lifecycle',
        'Consume existing companion records without reconstructing equipment from captures.'),
    PendingConsumer135('special40', '2376 same-state continuation',
        'Thread event records and their canonical RNG/counter back to this owner.'),
    PendingConsumer135('windows8', 'event-window schedule continuation',
        'Retain the produced count, times and full backing through the main loop.'),
    PendingConsumer135('boundaries8', 'boundary-object lifetime/transport',
        'Retain existing GUIDs, backing and corresponding logical creates.'),
    PendingConsumer135('world', 'all placement/movement consumers',
        'Use this exact query provider; a scalar flat-height replacement is not equivalent.'),
    PendingConsumer135('opening outputs', 'transport and object keyed-tree ownership',
        'Retain creates/packets/start notification; App/heap/transport layout is separate.'),
)


def _word(row, offset, width=4, *, optional=False):
    cells = row[offset:offset + width]
    if any(value is None for value in cells):
        if optional:
            return None
        raise PendingOpeningHandoff135('Pickup consumer requires known bytes at +' + str(offset))
    return int.from_bytes(bytes(cells), 'little')


def pickup_semantics135(row):
    """Read written56B fields without supplying concrete scratch/zero bytes.

    The opening's idle kind2 +4 is unwritten and unconsumed. An optional word
    with any unknown byte remains semantically unknown; its exact byte mask
    and any known byte values still live in the physical vector. Moving
    records require +4 because the collection consumer can read their arrival.
    """
    if type(row) is not tuple or len(row) != 56:
        raise TypeError('Explicit tuple of56 physical bytes required')
    if any(value is not None and (type(value) is not int or not 0 <= value <= 255)
           for value in row):
        raise ValueError('Exact bytes or None required')
    marker = _word(row, 0)
    arrival = _word(row, 4, optional=marker == 0)
    return PickupRecord(marker, arrival, _word(row, 8), _word(row, 12),
        _word(row, 16, 8), *(_word(row, offset) for offset in range(24, 56, 4)))


def _collection(opening):
    initial = opening.initial
    pickups = tuple(pickup_semantics135(row) for row in opening.pickups.storage[:opening.pickups.count])
    death = DeathContext135(pickups, opening.pickups.capacity, initial.spawn_counter,
        initial.message_sequence, initial.kill_cost_bits)
    # This adapter accepts only the declared empty-profile mode0 opening.
    # The constructor/default opening owns these empty queues and zero run
    # currency; neither current account state nor a running capture is input.
    currency = CurrencyState(0, 0, dict(initial.level.derived_bits)[1588],
        initial.level.stats.flag2574, 0, initial.member_count, initial.region_index,
        (), 0, initial.level.player_fields)
    return CollectionState135(initial.level, death, currency, initial.player_xyz, (), 0, opening.companions.count==0)


@dataclass(frozen=True)
class OpeningHandoff135:
    opening: OpeningState135
    world: object
    collection: CollectionState135
    pending_consumers: tuple = PENDING_CONSUMERS

    def __post_init__(self):
        if not isinstance(self.opening, OpeningState135):
            raise TypeError('Independent OpeningState135 required; memory import is not this API')
        if self.opening.phase2587 != 1:
            raise ValueError('Real opening phase1 required; constructor phase must not be overwritten')
        if self.opening.initial.level.stats.flag2574 != 0:
            raise PendingOpeningHandoff135('Only the declared empty-profile mode0 opening is resolved')
        for name, stride in VECTOR_STRIDES:
            vector = getattr(self.opening, name)
            expected_type = OpeningVector135 if stride in (56, 424) else PhysicalVector135
            if not isinstance(vector, expected_type) or vector.stride != stride:
                raise TypeError('Actual opening physical vector required: ' + name)
        if not all(callable(getattr(self.world, name, None))
                   for name in ('height', 'nearest_primary', 'nav_probe')):
            raise TypeError('Explicit world query provider required')
        if not isinstance(self.collection, CollectionState135):
            raise TypeError('CollectionState135 required')
        if self.collection != _collection(self.opening):
            raise ValueError('Collection view differs from its opening owner')
        if self.pending_consumers != PENDING_CONSUMERS:
            raise ValueError('This producer cannot silently mark a consumer completed')

    @property
    def initial(self): return self.opening.initial

    @property
    def records(self): return self.opening.units.storage[:self.opening.units.count]

    @property
    def unit_storage(self): return self.opening.units.storage

    @property
    def pickup_storage(self): return self.opening.pickups.storage

    @property
    def phase2587(self): return self.collection.level.phase2587

    @property
    def rng_words(self): return self.collection.level.rng_words

    @property
    def counter(self): return self.collection.death.spawn_counter


def from_opening(opening, world):
    """Own an independently produced complete opening without changing it."""
    if not isinstance(opening, OpeningState135):
        raise TypeError('Independent opening required')
    return OpeningHandoff135(opening, world, _collection(opening))


def initialize_empty_handoff(value, world, *, title_utf8, subtitle_utf8):
    """Legacy explicitly zero-slot opening -> lossless handoff, unchanged."""
    if not isinstance(value, EmptyOpeningInput135):
        raise TypeError('Explicit empty-profile input required')
    opening = initialize_empty_opening(value, world, title_utf8=title_utf8, subtitle_utf8=subtitle_utf8)
    return from_opening(opening, world)


def initialize_absent_companion_handoff(value, world, *, companion_profile, title_utf8, subtitle_utf8):
    """Explicit empty account flags -> absent slots -> opening -> handoff."""
    opening = initialize_absent_companion_opening(value, world, companion_profile=companion_profile,
        title_utf8=title_utf8, subtitle_utf8=subtitle_utf8)
    return from_opening(opening, world)


def projection(state):
    """Lossless byte-aware owner projection, not an emulated original heap."""
    if not isinstance(state, OpeningHandoff135):
        raise TypeError('OpeningHandoff135 required')
    opening = state.opening
    return dict(kind='independent_opening_gameplay_handoff', phase2587=state.phase2587,
        counter2408=state.counter, rng_words=list(state.rng_words),
        initial=asdict(state.initial), constructor_seed_u64=str(opening.constructor_seed_u64),
        vectors={name: dict(stride=stride, capacity=getattr(opening, name).capacity,
            count=getattr(opening, name).count,
            storage=[list(row) for row in getattr(opening, name).storage]) for name, stride in VECTOR_STRIDES},
        creates=[dict(guid=str(row.guid), kind=row.kind, position_bits=list(row.position_bits),
            heading_bits=row.heading_bits, fields=[list(pair) for pair in row.fields],
            payload169_hex=row.payload169_hex) for row in opening.creates],
        packets=[dict(opcode=opcode, payload_hex=payload) for opcode, payload in opening.packets],
        notifications_utf8_hex=[value.hex() for value in opening.notifications_utf8],
        draws=dict(position=opening.position_draws, actor=opening.actor_draws, window=opening.window_draws),
        opening_pending=list(opening.pending),
        pending_consumers=[dict(owner=row.owner, consumer=row.consumer, requirement=row.requirement)
                           for row in state.pending_consumers],
        world_retained_by_reference=True, original_memory_input=False,
        mainloop_frames=0, whole_game_complete=False)
