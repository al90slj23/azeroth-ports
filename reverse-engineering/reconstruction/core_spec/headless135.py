"""Independent same-state135 ordered-entry gameplay composition.

Constructor, casts/racial/areas, hits, ordinary AI, drops/XP and selection share one
canonical player/source/RNG state. This is not a replacement for880/915,
asset boot, phase-entry or their still-unrecovered side effects. Terrain is an
explicit flat-world domain, and unsupported effects/events return boundaries.
Production code reads no original program, index, output, save or network.
"""
from dataclasses import asdict, dataclass, replace
import struct
import hashlib

from . import binary32 as f
from .ability_state import AbilityRecord
from .ai135 import AiFrame135
from .ai_motion135 import update_ordinary_units
from .ai_lifecycle135 import cleanup_ordinary_corpses
from .area_effects135 import AREAS, AreaDefinition135, AreaState135, produce_area, tick_areas
from .cast135 import CastState, CastResult, UnresolvedCast
from .cast_events135 import cast_ability, process_hits
from .cast_catalogue135 import definition, RAW_BY_POINTER
from .combat135 import CombatState, encoded_hp
from .currency134 import CurrencyState
from .death_loot134 import OrdinaryDefinition
from .death_pickup135 import (DeathContext135, CollectionState135, OrdinaryDeathBinding135,
    consume_ordinary_death, collect_pickups, apply_damage_lifesteal)
from .incoming135 import IncomingState135, BuffRecord
from .initial_state135 import InitialState135
from .initial_state135_data import ZONE_ENTRIES
from .level_cycle135 import projection as level_projection
from .ordinary_placement135 import project_from_record
from .owned_cast135 import OwnedEntry135, OwnedSources135, tick_owned
from .movement_pause135 import moving_sequence_delta
from .player_update135 import prepare_player_update
from .pickups134 import encode_record56
from .racial_cast135 import RacialDefinition135, RACIALS, cast_self_buff
from .selection_cycle135 import SelectionCycleState, select_card
from .spawn135 import NORMALS, definition as normal_definition
from .spawn_frame_motion135 import step_ordinary_frame
from .spawn_schedule135 import FrameInput
from .unit_records135 import decode_spatial, patch_units


class PendingHeadless135(NotImplementedError): pass


@dataclass(frozen=True)
class DispatchEntry135(OwnedEntry135):
    """A fixed declaration; dispatch must independently prove its behavior."""
    def __post_init__(self):
        if definition(self.record.definition_pointer) != self.definition:
            raise ValueError('Fixed135 declaration identity differs')


@dataclass(frozen=True)
class HeadlessState135:
    collection: CollectionState135
    records: tuple
    unit_storage: tuple
    areas: tuple
    area_storage: tuple
    racial: AbilityRecord
    melee_timer_bits: int
    queued_hits: tuple
    outgoing_total: float
    incoming: IncomingState135
    attempted_spells: tuple
    live_records: tuple
    unspecified_live_words: tuple
    budget_bits: int
    velocity_xy: tuple
    previous_player_xyz: tuple
    zone: int
    flat_height_bits: int
    source_id: int
    initial_scalars: tuple
    game_tag: int
    frames: int = 0
    selections: int = 0

    def __post_init__(self):
        #G2408 is owned only by collection.death. AreaState135 is constructed
        #transiently at each consumer/producer boundary with that same counter.
        AreaState135(self.areas, self.collection.death.spawn_counter)
        if len(self.area_storage) != 128 or any(len(bytes.fromhex(raw)) != 88 for raw in self.area_storage):
            raise PendingHeadless135('Explicit128-slot88B area backing required')
        if len(self.areas) > len(self.area_storage) or self.area_storage[:len(self.areas)] != self.areas:
            raise ValueError('Active area records and backing prefix disagree')


def from_initial(initial: InitialState135, *, flat_height_bits, zeroed_unit_storage_resolved=False,
        zeroed_area_storage_resolved=False):
    if not isinstance(initial, InitialState135): raise TypeError('Real constructor result required')
    if zeroed_unit_storage_resolved is not True:
        raise PendingHeadless135('Explicit zeroed destination storage is required by this composition')
    if zeroed_area_storage_resolved is not True:
        raise PendingHeadless135('Explicit128 zeroed88B area destination slots are required by this composition')
    words = dict(initial.initial_scalar_words)
    if initial.level.phase2587 != 0: raise ValueError('Constructor phase must be preserved')
    death = DeathContext135((), 0, initial.spawn_counter, initial.message_sequence, initial.kill_cost_bits)
    currency = CurrencyState(0, 0, dict(initial.level.derived_bits)[1588],
        initial.level.stats.flag2574, 0, initial.member_count, initial.region_index, (), 0, initial.level.player_fields)
    collection = CollectionState135(initial.level, death, currency, initial.player_xyz, (), 0, True)
    return HeadlessState135(collection, (), (bytes(424).hex(),) * 128, (), (bytes(88).hex(),) * 128,
        initial.racial, initial.timer1628_bits, (), 0.0,
        IncomingState135(phase_2579=0, last_hit_1648_bits=words[1652],
            absorbed_740_bits=words[740], maximum_shield_744_bits=words[744]), (), (), (), words[2416], (0, 0),
        tuple(words[o] for o in (2428, 2432, 2436)), initial.region_index, flat_height_bits,
        initial.source_id, initial.initial_scalar_words, initial.game_tag)


def resolve_controlled_entry(state, *, phase1_entry_explicitly_resolved=False):
    """Research fixture boundary, NEVER a claim1089/world-entry is implemented."""
    if phase1_entry_explicitly_resolved is not True:
        raise PendingHeadless135('Actual movement/1089/resource phase entry is unresolved')
    if state.collection.level.phase2587 != 0: raise ValueError('Expected constructor phase0')
    return replace(state, collection=replace(state.collection,
        level=replace(state.collection.level, phase2587=1)))


def supported(pointer):
    d = definition(pointer)
    return (d.effect_tag == 0 and d.execution_kind in (0, 2) or d.ability_id in RACIALS
        or d.execution_kind == 3 and d.ability_id in AREAS)


def _store_prefix(storage, records):
    if len(records) > len(storage): raise PendingHeadless135('Unresolved destination storage growth')
    return tuple(records) + storage[len(records):]


def _cast_state(state):
    level = state.collection.level; d = dict(level.derived_bits)
    spatial = tuple(decode_spatial(bytes.fromhex(raw)) for raw in state.records)
    combat = CombatState(tuple(s.unit for s in spatial), now_bits=level.stats.now_bits,
        phase_2579=level.phase2587, accounted_total=state.outgoing_total)
    return CastState(combat, spatial, state.collection.player_xyz[:2], level.rng_words,
        d[1540], d[1536], d[1548], d[1552], d[1580], d[1544], d[1592],
        state.source_id, 0, 0, (), state.queued_hits, state.attempted_spells)


def _area_expire_storage(storage, records, now_bits):
    """3757 memory.copy compaction, retaining all inactive tail-slot bytes.

    Replacing only the final prefix loses intermediate shifted tail bytes when
    several entries expire. Compaction is ordered; subsequent normal tick
    writes are applied to the active prefix after this storage transformation.
    """
    if tuple(storage[:len(records)]) != tuple(records):
        raise ValueError('Area backing prefix differs before expiration')
    backing = list(storage); count = len(records); index = 0
    while index < count:
        expiry = struct.unpack_from('<I', bytes.fromhex(backing[index]), 80)[0]
        if f.to_float(now_bits) >= f.to_float(expiry):
            for j in range(index, count - 1): backing[j] = backing[j + 1]
            count -= 1
        else:
            index += 1
    return tuple(backing)


def _cast_phase(state, dt, *, phase='owned'):
    if phase not in ('owned', 'hits', 'area'):
        raise ValueError('Explicit owned/hits/area entry phase required')
    collection = state.collection; live = state.live_records; unknown = state.unspecified_live_words
    areas, area_storage = state.areas, state.area_storage
    original = {struct.unpack_from('<Q', bytes.fromhex(raw), 112)[0]: raw for raw in state.records}
    death_positions = {}
    effect_writes = ()

    def on_hit(cast, damage):
        nonlocal collection
        level = replace(collection.level, stats=replace(collection.level.stats, now_bits=cast.combat.now_bits))
        collection = replace(collection, level=apply_damage_lifesteal(level, damage.damage_bits))
        return cast

    def on_death(cast, damage):
        nonlocal collection
        guid = damage.target.target_id
        placed = project_from_record(state.zone, cast.combat.now_bits, original[guid], state.flat_height_bits,
            terrain_grid_absent=True, navigation_absent=True)
        pointer = struct.unpack_from('<I', bytes.fromhex(original[guid]), 284)[0]
        index = next((i for i, row in enumerate(NORMALS[state.zone]) if row[1] == pointer), None)
        if index is None: raise PendingHeadless135('Ordinary definition source not restored')
        row = normal_definition(state.zone, index)
        binding = OrdinaryDeathBinding135(OrdinaryDefinition(row['xp'], row['cost_bits'], row['elite']),
            pointer, placed.xp_placement, placed.currency_placement, placed.death_xyz, placed.movement_message)
        result = consume_ordinary_death(cast, damage, collection.death, binding)
        collection = replace(collection, death=result.context); death_positions[guid] = result.death_xyz
        return result.cast

    def dispatch(cast, d, owned, **callbacks):
        nonlocal collection, live, unknown, areas, area_storage
        if d.ability_id in AREAS:
            if len(areas) >= len(area_storage):
                raise PendingHeadless135('Area backing growth beyond128 slots is unresolved')
            result = produce_area(cast, AreaState135(areas, collection.death.spawn_counter),
                AreaDefinition135(d.pointer, d.ability_id, RAW_BY_POINTER[d.pointer]), owned,
                state.flat_height_bits, append_slot_hex=area_storage[len(areas)],
                terrain_grid_absent=True, navigation_absent=True, area_modifiers_absent=True, busy488=0)
            areas = result.areas.records
            area_storage = _store_prefix(area_storage, areas)
            #No damage/death callbacks run inside the area producer; this is
            #the freshly consumed canonical counter, including earlier hits.
            collection = replace(collection, death=replace(collection.death,
                spawn_counter=result.areas.spawn_counter))
            return CastResult(result.cast, result.success, (), 0, 0, ())
        if d.ability_id not in RACIALS:
            return cast_ability(cast, d, owned, **callbacks)
        level = replace(collection.level, rng_words=cast.rng_words,
            stats=replace(collection.level.stats, now_bits=cast.combat.now_bits))
        result = cast_self_buff(cast, level, RacialDefinition135(d.pointer, d.ability_id, RAW_BY_POINTER[d.pointer]),
            owned, live_records=live, unspecified_live_words=unknown, busy488=0)
        collection = replace(collection, level=result.level)
        live, unknown = result.live_records, result.unspecified_live_words
        return CastResult(result.cast, result.success, (), 0, 0, ())

    cast = _cast_state(state)
    if phase == 'area':
        area_storage = _area_expire_storage(area_storage, areas, collection.level.stats.now_bits)
        result = tick_areas(cast, AreaState135(areas, collection.death.spawn_counter),
            collection.level.stats.now_bits, after_hit=on_hit, after_death=on_death,
            area_modifiers_absent=True)
        cast, areas, effect_writes = result.cast, result.areas.records, result.effect_writes
        area_storage = _store_prefix(area_storage, areas)
        #result.areas.spawn_counter is its entry snapshot. Death callbacks may
        #have spawned XP/coins since then: retain collection.death's final word.
        racial, timer = state.racial, state.melee_timer_bits
    elif phase == 'hits':
        cast, _ = process_hits(cast, collection.level.stats.now_bits, after_hit=on_hit, after_death=on_death)
        racial, timer = state.racial, state.melee_timer_bits
    else:
        entries = tuple(DispatchEntry135(definition(x.record.definition_pointer), x.record)
            for x in collection.level.choice_inputs.owned)
        racial_entry = DispatchEntry135(definition(state.racial.definition_pointer), state.racial)
        result = tick_owned(cast, entries, racial_entry, dt, sources=OwnedSources135((), (), True),
            class_byte=collection.level.stats.class_byte, timer1628_bits=state.melee_timer_bits,
            after_hit=on_hit, after_death=on_death, cast_dispatch=dispatch)
        cast, racial, timer = result.state, result.basic.record, result.prelude.timer1628_bits
        owned = tuple(replace(old, record=new.record)
            for old, new in zip(collection.level.choice_inputs.owned, result.entries))
        collection = replace(collection, level=replace(collection.level,
            choice_inputs=replace(collection.level.choice_inputs, owned=owned)))
    records = list(patch_units(tuple(bytes.fromhex(raw) for raw in state.records), cast.combat.units))
    for j, raw in enumerate(records):
        guid = struct.unpack_from('<Q', raw, 112)[0]
        if guid in death_positions:
            raw = bytearray(raw)
            for offset in (316, 328): struct.pack_into('<3I', raw, offset, *death_positions[guid])
            records[j] = bytes(raw)
    #The generic combat adapter owns modeled124, but intentionally not U120.
    #Apply both returned writes after the generic patch to retain canonical
    #full424B records for the next AI stage and future phase readback.
    if effect_writes:
        indices = {struct.unpack_from('<Q', raw, 112)[0]: j for j, raw in enumerate(records)}
        for guid, offset, value in effect_writes:
            if offset not in (120, 124) or guid not in indices:
                raise PendingHeadless135('Unrestored area status-write destination')
            j = indices[guid]; raw = bytearray(records[j]); struct.pack_into('<I', raw, offset, value)
            records[j] = bytes(raw)
    collection = replace(collection, level=replace(collection.level, rng_words=cast.rng_words))
    serialized = tuple(raw.hex() for raw in records)
    return replace(state, collection=collection, records=serialized,
        unit_storage=_store_prefix(state.unit_storage, serialized),
        areas=areas, area_storage=area_storage,
        racial=racial, melee_timer_bits=timer, queued_hits=cast.queued,
        outgoing_total=cast.combat.accounted_total, attempted_spells=cast.attempted_spell_ids,
        live_records=live, unspecified_live_words=unknown)


def _ai_phase(state, dt):
    level = state.collection.level; d = dict(level.derived_bits); stats = level.stats
    if any(e.kind not in (7, 8, 9, 12) for e in level.sources.live_effects):
        raise PendingHeadless135('Unrestored incoming/retaliation source')
    #8/9 affect outgoing1512 only. Keep their canonical raw/semantic records;
    #the incoming scalar projection consumes the relevant7/12 subset.
    buffs = tuple(BuffRecord(e.kind, e.spell_id, e.value_bits, e.expires_bits)
        for e in level.sources.live_effects if e.kind in (7, 12))
    incoming = replace(state.incoming, phase_2579=level.phase2587, protection_2568=level.flags2576,
        mode_2574=stats.flag2574, map_id=ZONE_ENTRIES[state.zone][0].encode('ascii'),
        wave_2532=state.collection.currency.member_count, now_bits=stats.now_bits,
        armor_1392_bits=d[1568], armor_cap_1572_bits=d[1572], nearby_reduction_1444_bits=d[1624],
        hp_1528_bits=stats.current_hp_bits, shield_1532_bits=stats.pool1532_bits,
        barrier_1536_bits=stats.pool1536_bits, shield_source_1344=stats.conditional1344_id,
        shield_source_remaining_1348_bits=stats.conditional1348_bits, reserve_768_bits=stats.pool768_bits,
        buffs=buffs, modifiers=())
    indices = [j for j, raw in enumerate(state.records) if struct.unpack_from('<I', bytes.fromhex(raw))[0] == 0]
    result = update_ordinary_units(AiFrame135(tuple(state.records[j] for j in indices), stats.now_bits, dt,
        state.collection.player_xyz, incoming, incoming_item_effects=(), other_incoming_sources_absent=True))
    records = list(state.records)
    for j, raw in zip(indices, result.records): records[j] = raw
    storage = _store_prefix(state.unit_storage, tuple(records))
    cleanup = cleanup_ordinary_corpses(tuple(records), stats.now_bits, mode=stats.flag2574,
        local_peer=state.collection.currency.local_peer, explicit_other_sources_absent=True)
    records = list(cleanup.records)
    current = result.incoming
    stats = replace(stats, current_hp_bits=current.hp_1528_bits, pool1532_bits=current.shield_1532_bits,
        pool1536_bits=current.barrier_1536_bits, conditional1344_id=current.shield_source_1344,
        conditional1348_bits=current.shield_source_remaining_1348_bits, pool768_bits=current.reserve_768_bits)
    fields = dict(level.player_fields)
    if result.attacks:
        fields[22], fields[28] = encoded_hp(stats.current_hp_bits), encoded_hp(d[1536])
    level = replace(level, stats=stats, player_fields=tuple(sorted(fields.items())))
    # Preserve outgoing8/9 records while reflecting the actually consumed7/12
    #records. Their physical owner/auxiliary words and unknown-word marks stay
    #attached to the surviving source, rather than being recreated from stats.
    remaining = list(current.buffs); live = []; semantic = []; unknown = set()
    for i, (raw, effect) in enumerate(zip(state.live_records, level.sources.live_effects)):
        if effect.kind in (7, 12):
            expected = BuffRecord(effect.kind, effect.spell_id, effect.value_bits, effect.expires_bits)
            if expected not in remaining: continue
            remaining.remove(expected)
        j = len(live); live.append(raw); semantic.append(effect)
        unknown.update((j, offset) for row, offset in state.unspecified_live_words if row == i)
    if remaining: raise PendingHeadless135('Incoming produced an unresolved new live source')
    level = replace(level, sources=replace(level.sources, live_effects=tuple(semantic)))
    death = replace(state.collection.death,
        message_sequence=(state.collection.death.message_sequence + len(result.movements)) & f.MASK)
    return replace(state, records=tuple(records), incoming=current,
        unit_storage=_store_prefix(storage, tuple(records)),
        live_records=tuple(live), unspecified_live_words=tuple(sorted(unknown)),
        collection=replace(state.collection, level=level, death=death))


def step_frame(state, dt_bits):
    """Controlled ordered entries2088→1754→3757→921→2862→947 on shared state.

    It intentionally does not pretend the omitted880/915 phases ran.
    Unknown due timers or a selected unsupported ability stop before the frame.
    """
    if not 0 <= f.to_float(dt_bits) <= .1000000015: raise ValueError('Finite clamped frame delta required')
    level = state.collection.level
    if level.phase2587 != 1: return state, (), 'not_running'
    if any(not supported(x.record.definition_pointer) for x in level.choice_inputs.owned) or not supported(state.racial.definition_pointer):
        return state, (), 'pending_selected_ability'
    now = f.add(level.stats.now_bits, dt_bits)
    words = dict(state.initial_scalars)
    if any(f.to_float(now) >= f.to_float(words[o]) for o in (2424, 2440, 2444, 2448)):
        return state, (), 'pending_due_event'
    state = replace(state, collection=replace(state.collection,
        level=replace(level, stats=replace(level.stats, now_bits=now))), frames=state.frames + 1)
    prepared = prepare_player_update(state.collection.level, state.live_records, state.unspecified_live_words,
        now, dt_bits, state.incoming.last_hit_1648_bits, explicit_other_sources_absent=True, periodic_input=())
    state = replace(state, collection=replace(state.collection, level=prepared.level),
        live_records=prepared.live_records, unspecified_live_words=prepared.unspecified_live_words)
    stages = []
    state = _cast_phase(state, dt_bits); stages.append(('player', state))
    state = _cast_phase(state, dt_bits, phase='hits'); stages.append(('hits', state))
    state = _cast_phase(state, dt_bits, phase='area'); stages.append(('area', state))
    state = _ai_phase(state, dt_bits); stages.append(('ai', state))
    result = collect_pickups(state.collection, now)
    if result.status != 'core_projection': raise PendingHeadless135(result.status)
    if state.collection.level.stats.flag2574 == 0 and state.collection.level.phase2587 == 1 and result.state.level.phase2587 == 2:
        motion = moving_sequence_delta(state.records, now, auxiliary_motions=(), claims=())
        result = replace(result, state=replace(result.state, death=replace(result.state.death,
            message_sequence=(result.state.death.message_sequence + motion.count) & f.MASK)))
    state = replace(state, collection=result.state); stages.append(('collect', state))
    level = state.collection.level
    frame = FrameInput(state.zone, now, dt_bits, state.budget_bits, state.collection.death.kill_cost_bits,
        level.stats.flag2574, state.collection.currency.member_count, level.heal_gate387, words[2516],
        0, 0, 0, state.collection.player_xyz, state.previous_player_xyz, state.velocity_xy,
        state.flat_height_bits, level.rng_words, state.collection.death.spawn_counter, state.records, True)
    spawned = step_ordinary_frame(frame, destination_slots=state.unit_storage)
    if spawned.status != 'ordinary_projection': raise PendingHeadless135(spawned.status)
    collection = replace(state.collection, level=replace(level, rng_words=spawned.rng_words),
        death=replace(state.collection.death, spawn_counter=spawned.counter, kill_cost_bits=spawned.kill_cost_bits))
    state = replace(state, collection=collection, records=spawned.unit_records,
        unit_storage=_store_prefix(state.unit_storage, spawned.unit_records),
        budget_bits=spawned.budget_bits, velocity_xy=spawned.velocity_xy,
        previous_player_xyz=state.collection.player_xyz if level.stats.flag2574==0 else state.previous_player_xyz)
    stages.append(('spawn', state))
    return state, tuple(stages), 'ordered_frame_projection'


def select(state, index):
    """Use actual generated candidates; never replace them to force a result."""
    collection = state.collection
    unspecified = {p.guid for p in collection.death.records if p.arrival_bits is None}
    #The original inactive arrival word is unused by4600. The adapter's zero
    #is a semantic placeholder, restored as unspecified if that record survives.
    pickups = tuple(replace(p, arrival_bits=0) if p.arrival_bits is None else p for p in collection.death.records)
    value = SelectionCycleState(collection.level, 0, 0, pickups, collection.player_xyz[0],
        collection.player_xyz[1], collection.currency, state.game_tag, collection.xp_queue, collection.xp_queue_capacity)
    result = select_card(value, index, additional_modifiers=())
    if not result.accepted: return state, result.status
    selected = result.state
    records = tuple(replace(p, arrival_bits=None) if p.guid in unspecified else p for p in selected.pickups)
    live = []; unknown = set()
    for i, raw in enumerate(state.live_records):
        if result.status == 'running' and struct.unpack_from('<I', bytes.fromhex(raw), 20)[0] == 1020: continue
        j = len(live); live.append(raw)
        unknown.update((j, offset) for row, offset in state.unspecified_live_words if row == i)
    if result.status == 'running':
        index = len(live); expiry = selected.level.sources.live_effects[-1].expires_bits
        live.append(struct.pack('<8I', 0, 0, 12, 0, 0, 1020, expiry, 0).hex())
        unknown.update(((index, 12), (index, 16)))
    collection = replace(collection, level=selected.level, currency=selected.currency,
        death=replace(collection.death, records=records), xp_queue=selected.xp_queue,
        xp_queue_capacity=selected.xp_queue_capacity)
    if collection.level.stats.flag2574 == 0 and result.status in ('running', 'choice_regenerated'):
        motion = moving_sequence_delta(state.records, collection.level.stats.now_bits,
            auxiliary_motions=(), claims=())
        collection = replace(collection, death=replace(collection.death,
            message_sequence=(collection.death.message_sequence + motion.count) & f.MASK))
    return replace(state, collection=collection, game_tag=selected.game_tag,
        live_records=tuple(live), unspecified_live_words=tuple(sorted(unknown)), selections=state.selections + 1), result.status


def projection(state):
    result = level_projection(state.collection.level)
    result['player_fields'] = {k: v for k, v in result['player_fields'].items() if int(k) in (22, 28, 34, 716, 717, 1109, 1176)}
    live = [list(struct.unpack('<8I', bytes.fromhex(raw))) for raw in state.live_records]
    for index, offset in state.unspecified_live_words: live[index][offset // 4] = None
    pickups = []
    for p in state.collection.death.records:
        raw = encode_record56(p, uninitialized_arrival_bits=0) if p.arrival_bits is None else encode_record56(p)
        words = list(struct.unpack('<14I', raw))
        if p.arrival_bits is None: words[1] = None
        pickups.append(words)
    result.update(records=list(state.records), racial_record_hex=state.racial.to_bytes().hex(),
        owned_records_hex=[x.record.to_bytes().hex() for x in state.collection.level.choice_inputs.owned],
        timer1628_bits=state.melee_timer_bits, budget_bits=state.budget_bits,
        velocity_xy=list(state.velocity_xy), previous_player_xyz=list(state.previous_player_xyz), now_bits=state.collection.level.stats.now_bits,
        unit_storage_sha256=hashlib.sha256(b''.join(bytes.fromhex(raw) for raw in state.unit_storage)).hexdigest(),
        area_records=list(state.areas), area_capacity=len(state.area_storage),
        area_storage_sha256=hashlib.sha256(b''.join(bytes.fromhex(raw) for raw in state.area_storage)).hexdigest(),
        pickup_words=pickups, pickup_capacity=state.collection.death.capacity,
        spawn_counter=state.collection.death.spawn_counter, message_sequence=state.collection.death.message_sequence,
        kill_cost_bits=state.collection.death.kill_cost_bits, live_words=live,
        outgoing_total_hex=struct.pack('>d', state.outgoing_total).hex(), incoming_total_hex=struct.pack('>d', state.incoming.incoming_total_992).hex(),
        last_hit_bits=state.incoming.last_hit_1648_bits,
        absorbed740_bits=state.incoming.absorbed_740_bits, maximum_shield744_bits=state.incoming.maximum_shield_744_bits,
        queued=[dict(asdict(h), target_id=str(h.target_id), source_id=str(h.source_id)) for h in state.queued_hits],
        attempted_spell_sets=[list(state.attempted_spells)] * 3, gold=state.collection.currency.gold,
        earned=state.collection.currency.earned, xp_queue=[list(x) for x in state.collection.xp_queue],
        xp_queue_capacity=state.collection.xp_queue_capacity,
        currency_queue=[list(x) for x in state.collection.currency.queue], currency_queue_capacity=state.collection.currency.queue_capacity,
        game_tag=str(state.game_tag), auxiliary_motion_count=0, claim_count=0)
    return result
