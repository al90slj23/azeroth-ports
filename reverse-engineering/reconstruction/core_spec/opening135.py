"""Independent default empty-profile opening over an explicit resolved world.

The same constructor/state/RNG feeds companions, four enemies, two kind2
pickups, special declarations, event windows and boundary objects. No original
program, snapshot, asset, save or host is accessed. World/profile production,
other entry modes and the subsequent full main loop remain separate work.
"""
from dataclasses import dataclass, replace

from .initial_state135 import ConstructorInput135, initialize_empty_profile
from .initial_state135_data import ZONE_ENTRIES
from .opening_entities135 import (CompanionSlot135, create_companions,
    create_opening_windows, create_special_records, create_boundaries, start_banner150)
from .opening_npc_pickups135 import create_opening_npcs, create_initial_kind2
from .opening_entities135_data import ZONE_OPENING

MASK64 = (1 << 64) - 1


@dataclass(frozen=True)
class EmptyOpeningInput135:
    class_byte: int
    race_byte: int
    region_index: int
    app_lcg_seed_u64: int
    object_id_u64: int


@dataclass(frozen=True)
class OpeningState135:
    initial: object
    constructor_seed_u64: int
    companions: object
    units: object
    pickups: object
    special: object
    windows: object
    boundaries: object
    creates: tuple
    packets: tuple
    notifications_utf8: tuple
    position_draws: int
    actor_draws: int
    window_draws: int
    pending: tuple
    # Preserve the actual phase0 producer for later ownership certificates.
    # It is never reconstructed by overwriting the completed opening phase.
    constructor_initial: object|None = None

    @property
    def rng_words(self): return self.initial.level.rng_words

    @property
    def counter(self): return self.initial.spawn_counter

    @property
    def phase2587(self): return self.initial.level.phase2587


def initialize_empty_opening(value, world, *, title_utf8, subtitle_utf8, companion_slots=None):
    """Complete default1089 logical opening within an explicit empty profile.

    Mode0, protection0 and rank273=0 are declared here. The historical default
    retains its two explicitly zero selected equipment slots. A different
    profile must supply its independently produced companion_slots; this never
    infers absence from a missing account/profile. Locale/world are inputs.
    """
    if not isinstance(value, EmptyOpeningInput135):
        raise TypeError('Explicit empty-profile opening input required')
    if type(value.app_lcg_seed_u64) is not int or not 0 <= value.app_lcg_seed_u64 <= MASK64:
        raise ValueError('Explicit uint64 App LCG input required')
    seed = (value.app_lcg_seed_u64 * 6364136223846793005 + 1442695040888963407) & MASK64
    if type(value.region_index) is not int or not 0 <= value.region_index < len(ZONE_ENTRIES):
        raise ValueError('Fixed135 region required')
    zone = ZONE_ENTRIES[value.region_index]
    height = world.height(zone[1], zone[2])
    if not height.found:
        raise NotImplementedError('Constructor centre miss/nearest placement requires separate recovery')
    initial = initialize_empty_profile(ConstructorInput135(value.class_byte, value.race_byte,
        value.region_index, seed, value.object_id_u64, height.value_bits))
    xyz = initial.player_xyz
    #1560 reads zone152+116 to local33 and temp+1516, copied toGame1428.
    heading = ZONE_OPENING[value.region_index][1]
    slots = (CompanionSlot135(0,0,0,0,0),) * 2 if companion_slots is None else companion_slots
    companions = create_companions(slots, xyz, heading, 0,
        dict(initial.level.derived_bits)[1556], 0, initial.spawn_counter, world)
    npcs = create_opening_npcs(value.region_index, xyz, world, initial.level.rng_words,
        companions.counter, player_guid=initial.source_id, level1432=1, now_bits=0,
        zone_multiplier_bits=dict(initial.initial_scalar_words)[2516], difficulty=0)
    pickups = create_initial_kind2(value.region_index, xyz, world, npcs.rng_words,
        npcs.counter, now_bits=0)
    windows = create_opening_windows(value.region_index, pickups.rng_words)
    special = create_special_records(value.region_index, world)
    boundaries = create_boundaries(value.region_index, world, pickups.counter, windows.rng_words)
    creates = companions.creates + npcs.creates + pickups.creates + boundaries.creates
    packets = ((150, start_banner150(title_utf8, subtitle_utf8).hex()),) + tuple(
        (169, x.payload169_hex) for x in creates)
    final_initial = replace(initial, level=replace(initial.level, phase2587=1,
        rng_words=boundaries.rng_words), spawn_counter=boundaries.counter)
    return OpeningState135(final_initial, seed, companions.vector, npcs.vector, pickups.vector,
        special, windows.vector, boundaries.vector, creates, packets, (b'{"type":"start"}',),
        npcs.position_draws + pickups.position_draws,
        npcs.entity_draws + pickups.actor_draws + boundaries.draws,
        windows.count_draws + windows.window_draws,
        ('World/VFS/M2/WMO/cache production is an explicit input, not implemented by this opening.',
         'Menu/profile assembly, nonempty equipment/talents, other entry modes and all locales remain separate.',
         'CompleteGame2592/pointer ownership/player keyed tree are not all independently projected.',
         'Subsequent full880, all abilities/AI, saves/UI/multiplayer and complete game remain unfinished.'),
        constructor_initial=initial)


def initialize_absent_companion_opening(value, world, *, companion_profile, title_utf8, subtitle_utf8):
    """Distinct empty-account path, preserving the historical zero-slot API."""
    from .profile_companions135 import produce_companion_slots
    return initialize_empty_opening(value, world, title_utf8=title_utf8, subtitle_utf8=subtitle_utf8,
        companion_slots=produce_companion_slots(companion_profile))


def projection(state):
    def vector(value):
        return dict(capacity=value.capacity, count=value.count,
            storage=[list(row) for row in value.storage])
    return dict(phase2587=state.phase2587, counter2408=state.counter,
        rng_words=list(state.rng_words), player_xyz=list(state.initial.player_xyz),
        companions=vector(state.companions), units=vector(state.units), pickups=vector(state.pickups),
        special=vector(state.special), windows=vector(state.windows), boundaries=vector(state.boundaries),
        packets=[dict(opcode=opcode,payload_hex=payload) for opcode,payload in state.packets],
        notifications_utf8_hex=[x.hex() for x in state.notifications_utf8])
