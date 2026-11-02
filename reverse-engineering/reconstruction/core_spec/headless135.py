"""Independent same-state135 ordered-entry gameplay composition.

Constructor, casts/racial/areas, hits, ordinary AI, drops/XP and selection share one
canonical player/source/RNG state. This is not a replacement for880 or full915,
asset boot or their still-unrecovered side effects. World inputs come from an
explicit independent producer; unsupported effects/events return boundaries.
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
from .cleave135 import cast_cleave135
from .thunder_clap135 import cast_thunder_clap135
from .battle_shout135 import BattleShoutDefinition135,cast_battle_shout135
from .demo_shout135 import DemoDebuff135,cast_demo_shout135
from .cast_catalogue135 import definition, RAW_BY_POINTER
from .combat135 import CombatState, encoded_hp
from .currency134 import CurrencyState
from .death_loot134 import OrdinaryDefinition
from .death_pickup135 import (DeathContext135, CollectionState135, OrdinaryDeathBinding135,
    consume_ordinary_death, collect_pickups, apply_damage_lifesteal)
from .effect_system135 import EffectSystemState135, step_effect_system
from .frame_systems135 import (guard_owned_execution975, tick_scheduled_spells38007,
    tick_secondary_areas2602, guard_claim_tick2573, guard_terminal_tick49037)
from .headless_tail135 import TailDomains135, guard_extra916, guard_special2376, projection as tail_projection
from .incoming135 import IncomingState135, BuffRecord, ModifierRecord
from .initial_state135 import InitialState135
from .initial_state135_data import ZONE_ENTRIES
from .level_cycle135 import projection as level_projection
from .ordinary_placement135 import project_from_record
from .owned_cast135 import OwnedEntry135, OwnedSources135, tick_owned
from .movement_pause135 import moving_sequence_delta
from .player_update135 import prepare_player_update
from .resource_player_update135 import prepare_resource_player_update135
from .headless_player135 import PlayerSources135
from .headless_motion135 import HeadlessMotionOwner135
from .run_ledger135 import (RunLedger135, record_ordinary_death135,
    record_ordinary_selection135, run_ledger_projection135)
from .player_motion135 import MotionWorld135, MotionMap135, consume_motion_payload135
from .live_owner135 import retain_live135, resume_live1020_135, append_live135, ScratchAuxiliaryWord135
from .pickups134 import encode_record56
from .racial_cast135 import RacialDefinition135, RACIALS, cast_self_buff
from .selection_cycle135 import SelectionCycleState, select_card
from .spawn135 import NORMALS, definition as normal_definition
from .spawn_frame_motion135 import step_ordinary_frame
from .spawn_schedule135 import FrameInput
from .unit_records135 import decode_spatial, patch_units
from .record_cells135 import cells135,u32,u64,put_u32,encode_row,known_bytes
from .pickup_record_cells135 import pickup_words135,encode_pickup_cells135
from .opaque_pickup135 import PickupAmountAddress135,pickup_semantics_with_origins135
from .event_wave135 import CONSTRUCTOR_LAST_EVENT2586,EventWaveInput135,step_event_wave135
from .spawn_boss135_data import BOSSES


class PendingHeadless135(NotImplementedError): pass


def _aux_admission135(state,event,selected_kind=None):
    """Bind every admitted source count to this same independent state."""
    from .motion_aux_owner135 import MotionAuxAdmission135,EMPTY_SOURCE_COUNTS135
    level=state.collection.level;sources=state.run_ledger.callback_sources;tail=state.tail
    counts={604:len(level.sources.timed_records),652:tail.active84_count,
        2032:sources.items8.count,2056:sources.modifiers36.count,
        1804:len(state.areas),1852:len(state.queued_hits),
        1816:len(state.effect_records120),1828:len(state.delayed_records56),
        1840:tail.deadline32_count,1864:tail.secondary112_count,2116:tail.claims88_count}
    pointers=tuple(x.record.definition_pointer for x in level.choice_inputs.owned)+(state.racial.definition_pointer,)
    return MotionAuxAdmission135(event,level.phase2587,state.special_mode2582,level.flags2576,
        level.stats.class_byte,level.stats.race_byte,tuple((p,RAW_BY_POINTER[p])for p in pointers),
        tuple((o,counts[o])for o in EMPTY_SOURCE_COUNTS135),selected_kind)


def _inherit_aux135(before,after,event,selected_kind=None):
    if before.run_ledger is None:return after
    from .motion_aux_owner135 import inherit_motion_aux135
    owner=inherit_motion_aux135(before.run_ledger.auxiliary_motion,
        _aux_admission135(before,event,selected_kind),_aux_admission135(after,event,selected_kind))
    return replace(after,run_ledger=replace(after.run_ledger,auxiliary_motion=owner))


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
    effect_clock2364_bits: int = 0
    effect_counter2356: int = 0
    action_sequence1644: int = 1
    player_action_tag416: int = 0
    delayed_records56: tuple = ()
    delayed_storage56: tuple = ()
    effect_records120: tuple = ()
    effect_capacity120: int = 0
    tail: TailDomains135 = TailDomains135()
    frames: int = 0
    selections: int = 0
    opening_handoff: object|None = None
    world: object|None = None
    distance_map: object|None = None
    distance_map_updated_at_bits: int = 0
    allow_unknown_storage_growth: bool = False
    pickup_storage56: tuple = ()
    pickup_active_count: int = 0
    window_storage8: tuple = ()
    window_count: int = 0
    boundary_storage8: tuple = ()
    boundary_count: int = 0
    special_locale: object|None = None
    produced_packets: tuple = ()
    guardian_cooldowns: tuple = ()
    #Empty-profile1560 writes the packed1092 counter to0;404 is unwritten.
    #The current gameplay domain has no producer that changes1092. Its raw
    #value is compared at every stage rather than inferred from player level.
    special_field1092: int = 0
    special_endless_start404_bits: int|None = None
    special_mode2582: int = 0
    special_members2540: int|None = None
    next_resource2444_bits: int|None = None
    next_event2424_bits: int|None = None
    last_event2586: int = CONSTRUCTOR_LAST_EVENT2586
    next_supply2448_bits: int|None = None
    event_locale: object|None = None
    opaque_pickup_amount_origins: tuple = ()
    banner_locale: str|None = None
    pending_banner_events: tuple = ()
    player_sources: PlayerSources135|None = None
    rune_notifications: tuple = ()
    player_motion_owner: HeadlessMotionOwner135|None = None
    run_ledger: RunLedger135|None = None
    terminal_notifications: tuple = ()
    paused408: int|None = None
    paused412_bits: int|None = None
    fatal_stop_packets: tuple = ()
    physical_output_pending: tuple = ()

    def __post_init__(self):
        #G2408 is owned only by collection.death. AreaState135 is constructed
        #transiently at each consumer/producer boundary with that same counter.
        AreaState135(self.areas, self.collection.death.spawn_counter)
        def valid_row(raw,size):
            if isinstance(raw,str):return len(bytes.fromhex(raw))==size
            if isinstance(raw,bytes):return len(raw)==size
            return len(cells135(raw,size))==size
        if len(self.area_storage)>4096 or any(not valid_row(raw,88)for raw in self.area_storage):
            raise PendingHeadless135('Explicit real88B area backing required')
        if len(self.areas) > len(self.area_storage) or self.area_storage[:len(self.areas)] != self.areas:
            raise ValueError('Active area records and backing prefix disagree')
        if self.player_sources is not None:
            self.player_sources.validate_view(self.live_records, self.unspecified_live_words)
            self.player_sources.context(self.collection.level, self.source_id, self.action_sequence1644)
            if self.collection.resource_context is not None:
                raise ValueError('Resource context must not persist between frame phases')
        if self.run_ledger is not None:
            if not isinstance(self.run_ledger,RunLedger135):raise TypeError('Explicit run ledger owner required')
            if self.special_field1092!=self.run_ledger.counters.guardians1092:
                raise ValueError('Special and run-summary guardian counter owners disagree')


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
        initial.source_id, initial.initial_scalar_words, initial.game_tag,
        action_sequence1644=2 if abs(f.to_float(f.sub(initial.level.stats.previous_speed_bits, 0x40e00000))) > f.to_float(0x3c23d70a) else 1,
        next_resource2444_bits=words[2444],next_event2424_bits=words[2424],next_supply2448_bits=words[2448])


def resolve_controlled_entry(state, *, phase1_entry_explicitly_resolved=False):
    """Research fixture boundary, NEVER a claim1089/world-entry is implemented."""
    if phase1_entry_explicitly_resolved is not True:
        raise PendingHeadless135('Actual movement/1089/resource phase entry is unresolved')
    if state.collection.level.phase2587 != 0: raise ValueError('Expected constructor phase0')
    return replace(state, collection=replace(state.collection,
        level=replace(state.collection.level, phase2587=1)))


def from_opening_handoff(handoff, *, navigation_enabled,special_locale=None,event_locale=None,banner_locale=None,
        app_notification_next_id=None,resource_locale=None,motion_enabled=False,run_ledger=None):
    """Consume the real independent opening; retain all physical owners.

    This installs neither a synthetic phase nor an original memory image.
    Remaining consumer boundaries apply to the actual nonempty owners.
    """
    from .opening_handoff135 import OpeningHandoff135
    if not isinstance(handoff,OpeningHandoff135):raise TypeError('Independent opening handoff required')
    if type(navigation_enabled)is not bool:raise ValueError('Explicit navigation preference required')
    initial=handoff.initial;words=dict(initial.initial_scalar_words);o=handoff.opening
    if initial.level.phase2587!=1:raise ValueError('Preserve actual opening phase')
    def storage(vector):return tuple(encode_row(row)for row in vector.storage)
    tail=TailDomains135(claims88_storage=storage(o.companions),claims88_count=o.companions.count,
        special40_storage=storage(o.special),special40_count=o.special.count,
        special_navigation2564=int(navigation_enabled))
    collection=replace(handoff.collection,claims_empty=o.companions.count==0)
    state = HeadlessState135(collection,tuple(encode_row(row)for row in handoff.records),
        storage(o.units),(),(),initial.racial,initial.timer1628_bits,(),0.0,
        IncomingState135(phase_2579=0,last_hit_1648_bits=words[1652],
            absorbed_740_bits=words[740],maximum_shield_744_bits=words[744]),(),(),(),words[2416],(0,0),
        tuple(words[v]for v in(2428,2432,2436)),initial.region_index,handoff.world.fallback_height_bits,
        initial.source_id,initial.initial_scalar_words,initial.game_tag,
        action_sequence1644=2 if abs(f.to_float(f.sub(initial.level.stats.previous_speed_bits,0x40e00000)))>f.to_float(0x3c23d70a)else 1,
        tail=tail,opening_handoff=handoff,world=handoff.world,allow_unknown_storage_growth=True,
        pickup_storage56=storage(o.pickups),pickup_active_count=o.pickups.count,
        window_storage8=storage(o.windows),window_count=o.windows.count,
        boundary_storage8=storage(o.boundaries),boundary_count=o.boundaries.count,
        special_locale=special_locale,produced_packets=o.packets,next_resource2444_bits=words[2444],
        next_event2424_bits=words[2424],next_supply2448_bits=words[2448],event_locale=event_locale,banner_locale=banner_locale,
        run_ledger=run_ledger)
    if run_ledger is not None:
        from .run_summary135 import empty_constructor_counters135
        from .motion_aux_owner135 import (from_empty_profile1560_aux135,
            MotionAuxAdmission135,EMPTY_SOURCE_COUNTS135,inherit_motion_aux135)
        if run_ledger.counters!=empty_constructor_counters135()or run_ledger.history.capacity or run_ledger.history.head or run_ledger.history.count:
            raise ValueError('Opening requires a constructor-produced empty run ledger')
        constructor=o.constructor_initial
        if not isinstance(constructor,InitialState135)or constructor.level.phase2587!=0:
            raise PendingHeadless135('Actual retained phase0 constructor producer required')
        aux=from_empty_profile1560_aux135(constructor)
        if run_ledger.auxiliary_motion is not None and run_ledger.auxiliary_motion!=aux:
            raise ValueError('Supplied auxiliary owner differs from this constructor')
        state=replace(state,run_ledger=replace(run_ledger,auxiliary_motion=aux))
        pointers=tuple(r.definition_pointer for r in constructor.owned)+(constructor.racial.definition_pointer,)
        # These are1560's empty queue/header writes, retained at the actual
        # producer boundary. Subsequent events bind actual canonical owners.
        pre=MotionAuxAdmission135('opening1089',constructor.level.phase2587,0,
            constructor.level.flags2576,constructor.level.stats.class_byte,constructor.level.stats.race_byte,
            tuple((p,RAW_BY_POINTER[p])for p in pointers),tuple((o,0)for o in EMPTY_SOURCE_COUNTS135))
        inherit_motion_aux135(aux,pre,_aux_admission135(state,'opening1089'))
    if app_notification_next_id is not None or resource_locale is not None:
        if app_notification_next_id is None or resource_locale is None:
            raise ValueError('Both explicit App notification counter and resource locale required')
        if collection.level.sources.live_effects:
            raise PendingHeadless135('Empty-profile opening live producer required by this entry')
        if banner_locale != resource_locale:
            raise ValueError('Growth and rune presentation must use one explicit locale')
        sources = PlayerSources135.empty(notification_next_id14340336=app_notification_next_id,
            locale_code=resource_locale)
        state = replace(state,player_sources=sources)
    if type(motion_enabled)is not bool:raise ValueError('Explicit motion preference required')
    if motion_enabled:
        state=replace(state,player_motion_owner=HeadlessMotionOwner135.from_empty_constructor(state.zone))
    return state


def move_player135(state,opcode,payload24):
    """Canonical24→local968 core segment→2328 on the canonical Game state.

    This is not full968/App routing,17726 registration or rebroadcast. The
    default no-primary world is independently produced; other primary/aux
    sources need their actual producer. Unrestored correction queue storage
    remains unknown rather than receiving a made-up capacity.
    """
    owner=state.player_motion_owner
    if owner is None or state.opening_handoff is None or state.world is None:
        raise PendingHeadless135('Independent opening and explicit motion owner required')
    if state.collection.level.phase2587!=1:
        raise PendingHeadless135('Movement outside the admitted running phase requires its input policy')
    if state.special_mode2582 or state.collection.currency.mode or state.collection.currency.local_peer:
        raise PendingHeadless135('Remote/multiplayer movement routing remains separate')
    if state.world.primary is not None:
        raise PendingHeadless135('Primary-present movement requires independently produced auxiliary raster')
    level=state.collection.level
    cells=owner.bind(player_xyz=state.collection.player_xyz,now_bits=level.stats.now_bits,
        source_id=state.source_id,action_sequence1644=state.action_sequence1644,
        player_action_tag416=state.player_action_tag416,phase2587=level.phase2587,
        local_peer2528=state.collection.currency.local_peer,
        flags2583=dict(state.opening_handoff.initial.initial_byte_flags)[2583])
    result=consume_motion_payload135(cells,opcode,payload24,MotionWorld135(state.world,None),
        MotionMap135.fixed_zone(state.zone))
    if result is None:return state,'motion_payload_rejected'
    if not result.complete2328 or result.begin_run_required:
        raise PendingHeadless135('Actual phase0 begin1089 continuation is not supplied here')
    owner=owner.adopt(result.game_bytes)
    xyz=tuple(u32(result.game_bytes,o,'2328 resulting position')for o in(1416,1420,1424))
    updated=replace(state,player_motion_owner=owner,
        collection=replace(state.collection,player_xyz=xyz),
        action_sequence1644=u32(result.game_bytes,1644,'2328 action sequence'),
        player_action_tag416=u32(result.game_bytes,416,'2328 correction state'),
        produced_packets=state.produced_packets+result.packets)
    return _inherit_aux135(state,updated,'motion2328'),'motion_core_projection'


def _adopt_player_context135(state, context, collection, *, packets=(),notifications=(),live_owner=None):
    """Commit one consumer's level and physical owners in the same replacement."""
    if state.player_sources is None:
        raise PendingHeadless135('Physical player-source owner was not installed at entry')
    if context.player_guid != state.source_id:
        raise ValueError('Resource consumer changed the player GUID owner')
    sources=state.player_sources.adopt(context,live_owner=live_owner)
    live,unknown=sources.active_view()
    collection=replace(collection,resource_context=None)
    return replace(state,collection=collection,player_sources=sources,
        live_records=live,unspecified_live_words=unknown,
        action_sequence1644=context.action_sequence1644,
        produced_packets=state.produced_packets+tuple(packets),
        rune_notifications=state.rune_notifications+tuple(notifications))


def supported(pointer):
    d = definition(pointer)
    return (d.effect_tag == 0 and d.execution_kind in (0, 2) or d.ability_id==b'cleave' and d.effect_tag==0 and d.execution_kind==5
        or d.ability_id==b'thunder_clap' and d.effect_tag==1 and d.execution_kind==2
        or d.ability_id==b'demo_shout' and d.effect_tag==11 and d.execution_kind==2
        or d.ability_id==b'battle_shout' and d.effect_tag==8 and d.execution_kind==9 or d.ability_id in RACIALS
        or d.execution_kind == 3 and d.ability_id in AREAS)


def _demo_owner135(raw):
    """Bind a typed effect/Aura owner to known bytes of this physical unit."""
    return DemoDebuff135(u64(raw,112,'Demo physical GUID'),u32(raw,0,'Demo physical marker'),
        tuple(u32(raw,o,'Demo physical weakness')for o in(128,132,136,140)),
        u32(raw,360,'Demo physical spell'),u32(raw,364,'Demo physical duration'),
        tuple(u32(raw,o,'Demo physical Aura slot')for o in range(168,232,4)),
        u32(raw,240,'Demo physical ability count'))


def _store_prefix(storage, records, *, stride=None,allow_growth=False):
    if len(records) > len(storage):
        if not allow_growth or stride is None:raise PendingHeadless135('Unresolved destination storage growth')
        grown=list(storage)
        while len(grown)<len(records):grown.extend([(None,)*stride]*(max(4,2*len(grown))-len(grown)))
        storage=tuple(grown)
    return tuple(records) + storage[len(records):]


def _sync_pickup_owner(state, *, pre_compaction_records=None,removal_order='reverse'):
    """Keep the physical active prefix alongside canonical pickup semantics.

    Removals compact in descending-index order; append preserves the actual
    destination's unconsumed arrival word. No new allocator bytes are invented.
    """
    if state.opening_handoff is None:return state
    records=state.collection.death.records;backing=list(state.pickup_storage56)
    if state.collection.death.capacity<len(backing):raise PendingHeadless135('Pickup allocation shrink needs continuation')
    backing.extend([(None,)*56]*(state.collection.death.capacity-len(backing)))
    wanted={p.guid for p in records}
    if len(wanted)!=len(records):raise PendingHeadless135('Duplicate pickup GUID ownership unresolved')
    count=state.pickup_active_count
    if pre_compaction_records is not None:
        if len(pre_compaction_records)!=count:raise PendingHeadless135('Pickup pre-compaction count differs')
        for i,pickup in enumerate(pre_compaction_records):
            if u64(backing[i],16,'Pickup pre-compaction GUID')!=pickup.guid:
                raise PendingHeadless135('Pickup pre-compaction ownership differs')
            backing[i]=encode_pickup_cells135(pickup,prior=backing[i])
    remove=[i for i in range(count)if u64(backing[i],16,'Pickup owner removal GUID')not in wanted]
    if removal_order not in('reverse','forward'):raise ValueError('Explicit pickup removal order required')
    ordered=reversed(remove)if removal_order=='reverse'else (index-shift for shift,index in enumerate(remove))
    for i in ordered:
        for j in range(i,count-1):backing[j]=backing[j+1]
        count-=1
    for i,pickup in enumerate(records):
        if i<count and u64(backing[i],16,'Pickup owner prefix GUID')!=pickup.guid:
            raise PendingHeadless135('Pickup reorder requires a physical owner continuation')
        backing[i]=encode_pickup_cells135(pickup,prior=backing[i])
    return replace(state,pickup_storage56=tuple(backing),pickup_active_count=len(records))


def _cast_state(state):
    level = state.collection.level; d = dict(level.derived_bits)
    spatial = tuple(decode_spatial(raw) for raw in state.records)
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
        expiry = u32(backing[index],80,'3757 area expiry compaction')
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
    original = {u64(raw,112,'Headless pre-hit GUID'): raw for raw in state.records}
    death_positions = {}
    effect_writes = ()
    demo_owners = None
    indexed_effect_writes = ()
    aura_packets = ()
    player_sources = state.player_sources
    action_sequence = state.action_sequence1644
    run_ledger = state.run_ledger

    def accept_self_buff(result, previous_speed_bits):
        nonlocal collection, live, unknown, player_sources, aura_packets, action_sequence
        level=result.level
        if player_sources is not None:
            if result.physical_live is None:
                raise PendingHeadless135('Self-buff lost the full physical live owner')
            if result.physical_scratch_write is not None:
                index,offset,source=result.physical_scratch_write
                spell=u32(result.physical_live.storage[index],20,'922 auxiliary destination spell')
                player_sources=player_sources.retain(lambda row:
                    u32(row,20,'922 retain spell')!=spell or u64(row,0,'922 retain owner')!=0)
                origin=('922.effect8or9.caller_frame+48',state.frames,spell,
                    level.stats.now_bits,len(result.cast.attempted_spell_ids))
                player_sources=player_sources.replace_live(result.physical_live,
                    scratch_write=result.physical_scratch_write,origin=origin)
            elif result.physical_live!=player_sources.live:
                raise PendingHeadless135('Self-buff physical mutation lacks a declared producer')
            if '1512' in result.callbacks and abs(f.to_float(f.sub(
                    level.stats.previous_speed_bits,previous_speed_bits)))>f.to_float(0x3c23d70a):
                from .opening_entities135 import packed_guid
                aura_packets+=((226,(packed_guid(state.source_id)+struct.pack('<II',
                    action_sequence,level.stats.previous_speed_bits)).hex()),)
                action_sequence=(action_sequence+1)&f.MASK
            if '1202' in result.callbacks:
                level,player_sources=player_sources.refresh_aura(level)
        collection=replace(collection,level=level)
        live,unknown=result.live_records,result.unspecified_live_words
        return CastResult(result.cast,result.success,(),0,0,())

    def on_hit(cast, damage):
        nonlocal collection
        level = replace(collection.level, stats=replace(collection.level.stats, now_bits=cast.combat.now_bits))
        collection = replace(collection, level=apply_damage_lifesteal(level, damage.damage_bits))
        return cast

    def on_death(cast, damage):
        nonlocal collection,run_ledger
        guid = damage.target.target_id
        placed = project_from_record(state.zone, cast.combat.now_bits, original[guid], state.flat_height_bits,
            terrain_grid_absent=state.world is None, navigation_absent=state.world is None,world=state.world)
        pointer = u32(original[guid],284,'Headless ordinary death definition')
        index = next((i for i, row in enumerate(NORMALS[state.zone]) if row[1] == pointer), None)
        if index is None: raise PendingHeadless135('Ordinary definition source not restored')
        row = normal_definition(state.zone, index)
        binding = OrdinaryDeathBinding135(OrdinaryDefinition(row['xp'], row['cost_bits'], row['elite']),
            pointer, placed.xp_placement, placed.currency_placement, placed.death_xyz, placed.movement_message)
        result = consume_ordinary_death(cast, damage, collection.death, binding)
        if run_ledger is not None:run_ledger=record_ordinary_death135(run_ledger,damage)
        collection = replace(collection, death=result.context); death_positions[guid] = result.death_xyz
        return result.cast

    def dispatch(cast, d, owned, **callbacks):
        nonlocal collection, live, unknown, areas, area_storage, effect_writes
        nonlocal demo_owners, indexed_effect_writes, aura_packets
        if d.ability_id in AREAS:
            if state.world is not None:raise PendingHeadless135('Real-world area height producer requires continuation')
            if len(areas) >= len(area_storage):
                if not state.allow_unknown_storage_growth:raise PendingHeadless135('Area backing growth requires explicit unknown slots')
                area_storage=_store_prefix(area_storage,areas+((None,)*88,),stride=88,allow_growth=True)
            result = produce_area(cast, AreaState135(areas, collection.death.spawn_counter),
                AreaDefinition135(d.pointer, d.ability_id, RAW_BY_POINTER[d.pointer]), owned,
                state.flat_height_bits, append_slot_hex=area_storage[len(areas)],
                terrain_grid_absent=True, navigation_absent=True, area_modifiers_absent=True, busy488=0)
            areas = result.areas.records
            area_storage = _store_prefix(area_storage, areas,stride=88,allow_growth=state.allow_unknown_storage_growth)
            #No damage/death callbacks run inside the area producer; this is
            #the freshly consumed canonical counter, including earlier hits.
            collection = replace(collection, death=replace(collection.death,
                spawn_counter=result.areas.spawn_counter))
            return CastResult(result.cast, result.success, (), 0, 0, ())
        if d.ability_id==b'cleave':return cast_cleave135(cast,d,owned,**callbacks)
        if d.ability_id==b'thunder_clap':
            result=cast_thunder_clap135(cast,d,owned,**callbacks)
            effect_writes+=result.effect_writes
            return result
        if d.ability_id==b'demo_shout':
            if demo_owners is None:
                demo_owners=tuple(_demo_owner135(row)for row in state.records)
            if len(demo_owners)!=len(cast.combat.units)or any(
                    row.guid!=unit.target_id for row,unit in zip(demo_owners,cast.combat.units)):
                raise PendingHeadless135('Demo indexed physical/semantic owners disagree')
            # Earlier hits in this same owned phase may already have killed a
            # target. The2244 scan observes that latest marker, never its entry
            # snapshot; the raw debuff/Aura owner remains attached to its slot.
            demo_owners=tuple(replace(row,marker=unit.marker)
                for row,unit in zip(demo_owners,cast.combat.units))
            result=cast_demo_shout135(cast,d,owned,debuffs=demo_owners,**callbacks)
            demo_owners=result.debuffs
            indexed_effect_writes+=result.effect_writes
            aura_packets+=result.aura_packets
            return result
        if d.ability_id==b'battle_shout':
            level=replace(collection.level,rng_words=cast.rng_words,
                stats=replace(collection.level.stats,now_bits=cast.combat.now_bits))
            result=cast_battle_shout135(cast,level,BattleShoutDefinition135(),owned,
                live_records=live,unspecified_live_words=unknown,busy488=0,explicit_other_sources_absent=True,
                physical_live=None if player_sources is None else player_sources.live,
                scratch_word16_source=None if player_sources is None else ScratchAuxiliaryWord135(None))
            return accept_self_buff(result,level.stats.previous_speed_bits)
        if d.ability_id not in RACIALS:
            return cast_ability(cast, d, owned, **callbacks)
        level = replace(collection.level, rng_words=cast.rng_words,
            stats=replace(collection.level.stats, now_bits=cast.combat.now_bits))
        result = cast_self_buff(cast, level, RacialDefinition135(d.pointer, d.ability_id, RAW_BY_POINTER[d.pointer]),
            owned, live_records=live, unspecified_live_words=unknown, busy488=0,
            physical_live=None if player_sources is None else player_sources.live,
            scratch_word16_source=None if player_sources is None else ScratchAuxiliaryWord135(None))
        return accept_self_buff(result,level.stats.previous_speed_bits)

    cast = _cast_state(state)
    if phase == 'area':
        area_storage = _area_expire_storage(area_storage, areas, collection.level.stats.now_bits)
        result = tick_areas(cast, AreaState135(areas, collection.death.spawn_counter),
            collection.level.stats.now_bits, after_hit=on_hit, after_death=on_death,
            area_modifiers_absent=True)
        cast, areas, effect_writes = result.cast, result.areas.records, result.effect_writes
        area_storage = _store_prefix(area_storage, areas,stride=88,allow_growth=state.allow_unknown_storage_growth)
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
    records = list(patch_units(state.records, cast.combat.units))
    for j, raw in enumerate(records):
        guid = u64(raw,112,'Headless post-hit GUID')
        if guid in death_positions:
            raw = cells135(raw,424)
            for offset in (316, 328):
                for k,value in enumerate(death_positions[guid]):put_u32(raw,offset+4*k,value)
            records[j] = raw
    #The generic combat adapter owns modeled124, but intentionally not U120.
    #Apply both returned writes after the generic patch to retain canonical
    #full424B records for the next AI stage and future phase readback.
    if effect_writes:
        indices = {u64(raw,112,'Headless effect GUID'): j for j, raw in enumerate(records)}
        for guid, offset, value in effect_writes:
            if offset not in (120, 124) or guid not in indices:
                raise PendingHeadless135('Unrestored area status-write destination')
            j = indices[guid]; raw = cells135(records[j],424);put_u32(raw,offset,value)
            records[j] = raw
    for index,guid,offset,value in indexed_effect_writes:
        if (not 0<=index<len(records)or u64(records[index],112,'Demo write GUID')!=guid
                or offset not in(128,132,136,140,360,364)and offset not in range(168,232,4)):
            raise PendingHeadless135('Demo indexed write has no proven physical owner')
        raw=cells135(records[index],424);put_u32(raw,offset,value);records[index]=raw
    collection = replace(collection, level=replace(collection.level, rng_words=cast.rng_words))
    serialized = tuple(encode_row(raw)for raw in records)
    return _sync_pickup_owner(replace(state, collection=collection, records=serialized,
        unit_storage=_store_prefix(state.unit_storage, serialized,stride=424,allow_growth=state.allow_unknown_storage_growth),
        areas=areas, area_storage=area_storage,
        racial=racial, melee_timer_bits=timer, queued_hits=cast.queued,
        outgoing_total=cast.combat.accounted_total, attempted_spells=cast.attempted_spell_ids,
        live_records=live, unspecified_live_words=unknown,
        player_sources=player_sources,action_sequence1644=action_sequence,
        produced_packets=state.produced_packets+aura_packets,run_ledger=run_ledger))


def _ai_phase(state, dt):
    level = state.collection.level; d = dict(level.derived_bits); stats = level.stats
    allowed_live=(0,7,8,9,12) if state.player_sources is not None else (7,8,9,12)
    if any(e.kind not in allowed_live for e in level.sources.live_effects):
        raise PendingHeadless135('Unrestored incoming/retaliation source')
    #8/9 affect outgoing1512 only. Keep their canonical raw/semantic records;
    #the incoming scalar projection consumes the relevant7/12 subset.
    buffs = tuple(BuffRecord(e.kind, e.spell_id, e.value_bits, e.expires_bits)
        for e in level.sources.live_effects if e.kind in (7, 12))
    incoming_modifiers=()
    incoming_items=()
    if state.run_ledger is not None:
        sources=state.run_ledger.callback_sources
        #These are constructor/selection-maintained physical owners, not the
        #older numeric stat projection's placeholder empty source tuples.
        incoming_items=sources.items8.storage[:sources.items8.count]
        incoming_modifiers=tuple(ModifierRecord(u32(row,0,'Incoming modifier kind'),
            cells135(row,36)[4],cells135(row,36)[5])
            for row in sources.modifiers36.storage[:sources.modifiers36.count])
    incoming = replace(state.incoming, phase_2579=level.phase2587, protection_2568=level.flags2576,
        mode_2574=stats.flag2574, map_id=ZONE_ENTRIES[state.zone][0].encode('ascii'),
        wave_2532=state.collection.currency.member_count, now_bits=stats.now_bits,
        armor_1392_bits=d[1568], armor_cap_1572_bits=d[1572], nearby_reduction_1444_bits=d[1624],
        hp_1528_bits=stats.current_hp_bits, shield_1532_bits=stats.pool1532_bits,
        barrier_1536_bits=stats.pool1536_bits, shield_source_1344=stats.conditional1344_id,
        shield_source_remaining_1348_bits=stats.conditional1348_bits, reserve_768_bits=stats.pool768_bits,
        buffs=buffs, modifiers=incoming_modifiers)
    owners={owner.guid:owner for owner in state.guardian_cooldowns}
    if len(owners)!=len(state.guardian_cooldowns):raise PendingHeadless135('Duplicate guardian timer owners')
    guardian_indices=[];indices=[];seen=set()
    for j,raw in enumerate(state.records):
        guid=u64(raw,112,'Headless AI owner GUID')
        if guid in owners:
            guardian_indices.append(j);seen.add(guid)
        elif u32(raw,64,'Headless AI timer family')!=f.MASK:
            raise PendingHeadless135('Nonordinary AI family lacks an independent timer owner')
        elif u32(raw,0,'Headless AI live marker')==0:indices.append(j)
    if seen!=set(owners):raise PendingHeadless135('Guardian timer owner missing its physical unit')
    ai_input=AiFrame135(tuple(state.records[j]for j in indices),stats.now_bits,dt,
        state.collection.player_xyz,incoming,incoming_item_effects=incoming_items,other_incoming_sources_absent=True,
        known_demo_statuses=tuple(_demo_owner135(state.records[j])for j in indices
            if u32(state.records[j],360,'AI typed demo spell')==1160))
    world_plan=None
    if state.world is None:
        if state.run_ledger is not None:
            raise PendingHeadless135('Recorded incoming drain requires the actual independent world-query owner')
        result=update_ordinary_units(ai_input)
    else:
        from .distance_map135 import update_distance_map135
        from .ai_world135 import update_world_ordinary_units135,plan_world_ordinary_units135
        distances=update_distance_map135(state.world.nav,state.collection.player_xyz[:2],stats.now_bits,
            previous=state.distance_map,updated_at_bits=state.distance_map_updated_at_bits)
        state=replace(state,distance_map=distances.distance_map,distance_map_updated_at_bits=distances.updated_at_bits)
        if state.run_ledger is None:
            result=update_world_ordinary_units135(ai_input,state.world,distance_map=state.distance_map)
        else:
            world_plan=plan_world_ordinary_units135(ai_input,state.world,distance_map=state.distance_map)
            result=world_plan
    records = list(state.records)
    for j, raw in zip(indices, result.records): records[j] = raw
    guardian_owners=[];guardian_movements=[]
    if guardian_indices:
        from .guardian_ai135 import GuardianContext135,step_guardian_unit135,guardian_cleanup_admitted135
        context=GuardianContext135(stats.now_bits,dt,state.collection.player_xyz,
            state.tail.special40_storage,state.tail.special40_count,state.world,
            mode=state.special_mode2582,local_peer=state.collection.currency.local_peer,
            phase2587=level.phase2587,other_sources_absent=True)
        for j in guardian_indices:
            guid=u64(records[j],112,'Headless guardian owner GUID')
            planned=step_guardian_unit135(records[j],owners[guid],context,unit_index=j)
            if planned.attacks or planned.planned_actions or planned.pending:
                raise PendingHeadless135('Guardian actions require canonical ordered910/incoming drain')
            if not guardian_cleanup_admitted135(planned.record,planned.cooldowns,context):
                raise PendingHeadless135('Guardian lifecycle requires an explicit resource consumer')
            records[j]=planned.record;guardian_owners.append(planned.cooldowns)
            guardian_movements.extend(planned.movements)
    #921 drains the expired-corpse39635 queue before movement/incoming queues.
    #Compact the planned backing now: a later fatal stop writes only its active
    #prefix, leaving the retained inactive tail in its pre-stop planned state.
    ordinary_plan_guids=tuple(u64(raw,112,'Ordinary planned GUID')for raw in result.records)
    storage=_store_prefix(state.unit_storage,tuple(records),stride=424,
        allow_growth=state.allow_unknown_storage_growth)
    cleanup=cleanup_ordinary_corpses(tuple(raw for j,raw in enumerate(records)if j not in guardian_indices),
        stats.now_bits,mode=stats.flag2574,local_peer=state.collection.currency.local_peer,
        explicit_other_sources_absent=True)
    backing=list(storage);count=len(records)
    for guid in cleanup.removed_guids:
        index=0
        while index<count:
            if u64(backing[index],112,'39635 physical removal GUID')==guid:
                for j in range(index,count-1):backing[j]=backing[j+1]
                count-=1
            else:index+=1
    storage=tuple(backing);records=list(storage[:count])
    relocated={u64(raw,112,'Post-cleanup planned GUID'):j for j,raw in enumerate(records)}
    if len(relocated)!=len(records):
        raise PendingHeadless135('Post-cleanup unit GUID ownership is ambiguous')
    if any(guid not in relocated for guid in ordinary_plan_guids):
        raise PendingHeadless135('Corpse cleanup removed a planned live ordinary owner')
    indices=[relocated[guid]for guid in ordinary_plan_guids]
    guardian_owners=tuple(replace(owner,unit_index=relocated[owner.guid])for owner in guardian_owners)
    #All owners are planned before incoming. A fatal1073 freezes this compacted
    #canonical backing; no old plan may overwrite its stopped coordinates.
    movement_sequence=(state.collection.death.message_sequence+len(result.movements)+len(guardian_movements))&f.MASK
    if world_plan is not None:
        from .ai_world135 import finish_world_ordinary_plan135
        from .run_incoming135 import drain_run_incoming135
        drained=drain_run_incoming135(state,world_plan.incoming,world_plan.attacks,
            records=tuple(records),unit_storage=storage,
            movement_sequence2412=movement_sequence,
            auxiliary_owner=state.run_ledger.auxiliary_motion)
        records=list(drained.records)
        result=finish_world_ordinary_plan135(world_plan,drained.incoming,
            records=tuple(records[j]for j in indices))
        for j,raw in zip(indices,result.records):records[j]=raw
        #Late Aura writes apply on the stopped backing, including its retained
        #inactive tail. No queue-header values are inferred from packet subsets.
        state=replace(state,unit_storage=drained.unit_storage,
            run_ledger=drained.ledger,
            tail=replace(state.tail,claims88_storage=drained.claims_storage),
            produced_packets=state.produced_packets+tuple((op,payload)for op,cap,payload in drained.packets),
            fatal_stop_packets=state.fatal_stop_packets+drained.packets,
            terminal_notifications=state.terminal_notifications+drained.notifications,
            paused408=drained.paused408,paused412_bits=drained.paused412_bits,
            physical_output_pending=tuple(dict.fromkeys(state.physical_output_pending+drained.physical_queue_pending)))
        movement_sequence=drained.movement_sequence2412
        level=replace(level,phase2587=drained.incoming.phase_2579)
        storage=drained.unit_storage
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
    remaining = list(current.buffs); live = []; semantic = []; unknown = set(); keep_flags=[]
    for i, (raw, effect) in enumerate(zip(state.live_records, level.sources.live_effects)):
        if effect.kind in (7, 12):
            expected = BuffRecord(effect.kind, effect.spell_id, effect.value_bits, effect.expires_bits)
            if expected not in remaining:
                keep_flags.append(False)
                continue
            remaining.remove(expected)
        keep_flags.append(True)
        j = len(live); live.append(raw); semantic.append(effect)
        unknown.update((j, offset) for row, offset in state.unspecified_live_words if row == i)
    if remaining: raise PendingHeadless135('Incoming produced an unresolved new live source')
    level = replace(level, sources=replace(level.sources, live_effects=tuple(semantic)))
    player_sources=state.player_sources
    if player_sources is not None:
        flags=iter(keep_flags)
        player_sources=player_sources.retain(lambda row:next(flags))
        live,unknown=player_sources.active_view()
        if not all(keep_flags):
            level,player_sources=player_sources.refresh_aura(level)
    death = replace(state.collection.death,message_sequence=movement_sequence)
    return replace(state, records=tuple(records), incoming=current,
        unit_storage=_store_prefix(storage, tuple(records),stride=424,allow_growth=state.allow_unknown_storage_growth),
        guardian_cooldowns=guardian_owners,
        live_records=tuple(live), unspecified_live_words=tuple(sorted(unknown)),
        player_sources=player_sources,
        produced_packets=state.produced_packets+result.demo_aura_packets169,
        collection=replace(state.collection, level=level, death=death))


def _effects_phase(state, dt):
    """915's actually observed idle-queue domain, using the independent model.

    1560 writes scratch+2444/2452=0 and i64(1<<32) at1728, then copies
    scratch+88 toG: 2356/2364 start0 and1644 starts1. Its416 action tag
    starts0. Inactive payload words420..436 are not modeled or compared;
    representative zeros below are never read in this guarded domain and
    never written to the original. Actual payload bytes remain observations.
    """
    if state.delayed_records56 or state.effect_records120 or state.player_action_tag416:
        raise PendingHeadless135('Active915 queues/player action need a headless continuation')
    level = state.collection.level
    snapshot = EffectSystemState135(now_bits=level.stats.now_bits,
        delayed_records=state.delayed_records56, delayed_storage=state.delayed_storage56,
        effect_records120=state.effect_records120, units=state.records,
        clock2364_bits=state.effect_clock2364_bits, action_sequence1644=state.action_sequence1644,
        movement_sequence2412=state.collection.death.message_sequence,
        player_xyz_bits=state.collection.player_xyz, player_action_words=(0, 0, 0, 0, 0, 0),
        source_id=state.source_id, phase2587=level.phase2587, mode2582=0,
        local_peer2528=state.collection.currency.local_peer, zone=state.zone,
        flat_height_bits=state.flat_height_bits, flat_height_enabled=state.world is None,
        terrain_grid_absent=state.world is None, collision_grid_absent=state.world is None, navigation_absent=state.world is None,
        rng_words=level.rng_words, spawn_counter2408=state.collection.death.spawn_counter)
    result = step_effect_system(snapshot, dt)
    if result.status != 'delayed_prefix_projection':
        raise PendingHeadless135('Unresolved915 continuation: ' + result.status)
    updated = result.state
    collection = replace(state.collection, player_xyz=updated.player_xyz_bits,
        level=replace(level, rng_words=updated.rng_words),
        death=replace(state.collection.death, spawn_counter=updated.spawn_counter2408,
            message_sequence=updated.movement_sequence2412))
    return replace(state, collection=collection, records=updated.units,
        unit_storage=_store_prefix(state.unit_storage, updated.units,stride=424,allow_growth=state.allow_unknown_storage_growth),
        effect_clock2364_bits=updated.clock2364_bits,
        action_sequence1644=updated.action_sequence1644,
        delayed_records56=updated.delayed_records, delayed_storage56=updated.delayed_storage)


def _tail_phase(state, kind, dt):
    tail, level = state.tail, state.collection.level
    if kind == 'extra':
        guard_extra916(level.sources.timed_records, tail.active84_count)
    elif kind == 'owned_effects':
        guard_owned_execution975(tuple(x.record.to_bytes().hex() for x in level.choice_inputs.owned), RAW_BY_POINTER, dt)
    elif kind == 'deadline':
        result = tick_scheduled_spells38007(tail.deadline32_storage, tail.deadline32_count, level.stats.now_bits)
        if result.status != 'scheduled_spells_complete': raise PendingHeadless135(result.status)
        #A nonempty producer is not yet connected to the canonical message
        #state. Keep it a boundary rather than losing its real packet stream.
        if result.packets: raise PendingHeadless135('Active38007 packet producer needs canonical continuation')
        tail = replace(tail, deadline32_storage=result.storage, deadline32_count=result.count)
    elif kind == 'secondary':
        result = tick_secondary_areas2602(tail.secondary112_storage, tail.secondary112_count, level.stats.now_bits)
        if result.status != 'secondary_expiry_idle_complete' or result.packets:
            raise PendingHeadless135('Active2602 continuation: ' + result.status)
        tail = replace(tail, secondary112_storage=result.storage, secondary112_count=result.count)
    elif kind == 'claims':
        result = guard_claim_tick2573(tail.claims88_storage, tail.claims88_count, level.phase2587)
        if result.status != 'claim_gate_complete': raise PendingHeadless135(result.status)
        tail = replace(tail, claims88_storage=result.storage, claims88_count=result.count)
    elif kind == 'special':
        if state.opening_handoff is None:guard_special2376(tail.special40_count,level.flags2576)
        else:
            from .special2376_135 import SpecialState2376_135,tick_special2376_135,UnknownSpecial2376_135
            from .special2376_notify135 import tick_special2376_notify135
            special=SpecialState2376_135(tail.special40_storage,tail.special40_count,
                level.stats.now_bits,state.collection.player_xyz[:2],level.flags2576,tail.special_navigation2564,
                tail.special_announced2565,tail.special_selected392,tail.special_target396,tail.special_clock2392_bits)
            try:result=tick_special2376_135(special)
            except UnknownSpecial2376_135 as error:
                if str(error).startswith('Due inactive special'):
                    from .special2376_spawn135 import SpecialSpawnInput135,tick_special_spawn135
                    from .opening_npc_pickups135 import OpeningVector135
                    spawned=tick_special_spawn135(SpecialSpawnInput135(special,
                        OpeningVector135(424,state.unit_storage,len(state.records)),level.rng_words,
                        state.collection.death.spawn_counter,state.collection.player_xyz,state.source_id,
                        level.progression.level,dict(state.initial_scalars)[2516],level.heal_gate387,
                        state.special_mode2582,state.special_members2540,
                        state.special_field1092,tail.field400,tail.flag2568,
                        state.special_endless_start404_bits,zone=state.zone),locale=state.special_locale)
                    updated=spawned.units
                    state=replace(state,records=tuple(encode_row(row)for row in updated.storage[:updated.count]),
                        unit_storage=tuple(encode_row(row)for row in updated.storage),
                        guardian_cooldowns=state.guardian_cooldowns+spawned.cooldowns,
                        collection=replace(state.collection,level=replace(level,rng_words=spawned.rng_words),
                            death=replace(state.collection.death,spawn_counter=spawned.counter)),
                        produced_packets=state.produced_packets+spawned.packets)
                    s=spawned.special
                    tail=replace(tail,special40_storage=s.storage,special_selected392=s.selected392,special_target396=s.target396,
                        special_navigation2564=s.navigation2564,special_announced2565=s.announced2565,special_clock2392_bits=s.announcement_time2392_bits)
                    return replace(state,tail=tail)
                if not str(error).startswith('Selected-target localized548'):raise
                if state.special_locale is None:raise PendingHeadless135('Explicit initialized special locale names required')
                result=tick_special2376_notify135(special,state.zone,state.special_locale)
            s=result.state
            tail=replace(tail,special40_storage=s.storage,special_selected392=s.selected392,special_target396=s.target396,
                special_navigation2564=s.navigation2564,special_announced2565=s.announced2565,special_clock2392_bits=s.announcement_time2392_bits)
            state=replace(state,produced_packets=state.produced_packets+tuple((opcode,payload)for opcode,cap,payload in result.packets))
    elif kind == 'terminal':
        guard_terminal_tick49037(tail.field400, level.phase2587, tail.flag2568)
    else:
        raise ValueError('Unknown main-tail stage')
    return replace(state, tail=tail)


def _event_phase(state):
    """947 G2424 after ordinary and the still-future G2440 branch."""
    if state.next_event2424_bits is None:
        raise PendingHeadless135('Event deadline has no explicit producer')
    level=state.collection.level
    if f.to_float(level.stats.now_bits)<f.to_float(state.next_event2424_bits):return state
    if state.opening_handoff is None:
        raise PendingHeadless135('Event wave requires actual opening unit/world ownership')
    from .opening_npc_pickups135 import OpeningVector135
    vector=OpeningVector135(424,tuple(tuple(cells135(row,424))for row in state.unit_storage),len(state.records))
    result=step_event_wave135(EventWaveInput135(state.zone,level.stats.now_bits,state.next_event2424_bits,
        state.last_event2586,state.collection.player_xyz,state.velocity_xy,level.rng_words,
        state.collection.death.spawn_counter,state.collection.death.message_sequence,vector,state.source_id,
        level.progression.level,dict(state.initial_scalars)[2516],level.heal_gate387,state.special_mode2582,
        state.special_members2540,state.tail.field400,state.tail.flag2568,state.special_endless_start404_bits,
        state.distance_map),state.world,locale=state.event_locale)
    collection=replace(state.collection,level=replace(level,rng_words=result.rng_words),
        death=replace(state.collection.death,spawn_counter=result.counter,message_sequence=result.message_sequence))
    return replace(state,collection=collection,records=tuple(encode_row(row)for row in result.units.storage[:result.units.count]),
        unit_storage=tuple(encode_row(row)for row in result.units.storage),next_event2424_bits=result.next_event2424_bits,
        last_event2586=result.last_event2586,produced_packets=state.produced_packets+result.packets)


def _resource_phase(state):
    """947 resource slice after ordinary work; other due branches are guarded.

    The current physical pickup owner, shared RNG/counter and real world are
    authoritative. Creation is after this frame's collection, even if that
    collection changed phase. No nearby-resource consumer is implied here.
    """
    from .resource_spawn135 import ResourceSpawnInput135,step_resource_spawn135
    from .opening_npc_pickups135 import OpeningVector135
    if state.next_resource2444_bits is None:
        raise PendingHeadless135('Resource deadline has no explicit producer')
    level=state.collection.level
    if f.to_float(level.stats.now_bits)<f.to_float(state.next_resource2444_bits):return state
    if state.opening_handoff is None:
        raise PendingHeadless135('Resource production requires actual opening pickup/world ownership')
    if (state.pickup_active_count!=len(state.collection.death.records)
            or len(state.pickup_storage56)!=state.collection.death.capacity):
        raise PendingHeadless135('Resource pickup physical/semantic ownership differs')
    vector=OpeningVector135(56,tuple(tuple(cells135(row,56))for row in state.pickup_storage56),state.pickup_active_count)
    result=step_resource_spawn135(ResourceSpawnInput135(state.zone,level.stats.now_bits,
        state.next_resource2444_bits,state.collection.player_xyz,state.velocity_xy,
        level.rng_words,state.collection.death.spawn_counter,vector),state.world)
    records=tuple(pickup_semantics_with_origins135(row,state.opaque_pickup_amount_origins)
        for row in result.pickups.storage[:result.pickups.count])
    collection=replace(state.collection,level=replace(level,rng_words=result.rng_words),
        death=replace(state.collection.death,records=records,capacity=result.pickups.capacity,spawn_counter=result.counter))
    return replace(state,collection=collection,pickup_storage56=tuple(encode_row(row)for row in result.pickups.storage),
        pickup_active_count=result.pickups.count,next_resource2444_bits=result.next_resource2444_bits,
        produced_packets=state.produced_packets+tuple((169,x.payload169_hex)for x in result.creates))


def _supply_phase(state):
    """947 G2448 after resource345; retain address provenance in kind2+12."""
    from .opening_npc_pickups135 import OpeningVector135
    from .supply_kind2_135 import SupplyTickInput135,step_supply_kind2_135
    if state.next_supply2448_bits is None:
        raise PendingHeadless135('Supply deadline has no explicit producer')
    level=state.collection.level
    if f.to_float(level.stats.now_bits)<f.to_float(state.next_supply2448_bits):return state
    if state.opening_handoff is None or state.special_mode2582!=0:
        raise PendingHeadless135('Supply composition currently requires actual local-mode opening ownership')
    vector=OpeningVector135(56,tuple(tuple(cells135(row,56))for row in state.pickup_storage56),state.pickup_active_count)
    if vector.count!=len(state.collection.death.records)or vector.capacity!=state.collection.death.capacity:
        raise PendingHeadless135('Supply pickup physical/semantic ownership differs')
    result=step_supply_kind2_135(SupplyTickInput135(state.zone,level.stats.now_bits,state.next_supply2448_bits,
        state.collection.player_xyz,state.velocity_xy,level.rng_words,state.collection.death.spawn_counter,vector,
        mode=0,party_count2140=0,excluded2548=0),state.world)
    origins={origin.guid:origin for origin in state.opaque_pickup_amount_origins}
    for item in result.opaque_word_provenance:
        if item['owner_symbol']!='pickup56_owner_before2448'or item['offset']!=12 or item['bytes']!=4:
            raise PendingHeadless135('Unrestored supply opaque-word producer')
        guid=int(item['guid']);origins[guid]=PickupAmountAddress135(guid,1872,item['byte_delta'])
    active={u64(row,16,'Supply active GUID')for row in result.pickups.storage[:result.pickups.count]}
    origins=tuple(origin for guid,origin in origins.items()if guid in active)
    records=tuple(pickup_semantics_with_origins135(row,origins)for row in result.pickups.storage[:result.pickups.count])
    collection=replace(state.collection,level=replace(level,rng_words=result.rng_words),
        death=replace(state.collection.death,records=records,capacity=result.pickups.capacity,spawn_counter=result.counter))
    return replace(state,collection=collection,pickup_storage56=tuple(encode_row(row)for row in result.pickups.storage),
        pickup_active_count=result.pickups.count,next_supply2448_bits=result.next_supply2448_bits,
        opaque_pickup_amount_origins=origins,produced_packets=state.produced_packets+result.packets)


def _growth_banners(state, events):
    """Emit each4630 iteration's presentation from its actual old/new stats.

    Numeric-only callers without a selected locale retain semantic events;
    the complete banner-comparison lane must provide that context explicitly.
    """
    if not events:return state
    if state.banner_locale is None:
        return replace(state,pending_banner_events=state.pending_banner_events+tuple(events))
    from .level_banner135 import LevelBannerInput135,level_banners135
    kinds=tuple(definition(entry.record.definition_pointer).execution_kind
        for entry in state.collection.level.choice_inputs.owned)
    packets=[]
    for event in events:
        result=level_banners135(LevelBannerInput135(event['level_before'],event['level_after'],
            event['derived_before'],event['derived_after'],kinds,state.banner_locale))
        packets.extend(result.packets)
    return replace(state,produced_packets=state.produced_packets+tuple(packets))


def _resource_live_origins135(sources,effects,now_bits):
    """Carry written scratch origins through10298's exact retain/partial append.

    No source word is reconstructed from the returned original or a guessed
    zero. Every modeled byte is cross-checked against the consumer's returned
    physical owner when the context is adopted.
    """
    for effect in effects:
        if effect.stage!='resource' or effect.pickup_kind==5:continue
        if effect.pickup_kind not in(3,4):raise PendingHeadless135('Unknown resource live producer')
        spell,duration=(23451,0x41200000)if effect.pickup_kind==3 else(23505,0x41700000)
        sources=sources.retain(lambda row:u32(row,20,'10298 sameSpell retain')!=spell)
        physical=append_live135(sources.live,((0,0),(4,0),(8,0),(20,spell),
            (24,f.add(now_bits,duration)),(28,0)))
        sources=sources.replace_live(physical)
    return sources


def _collect_phase135(state, now_bits):
    """Bind the current live view only for2862, then commit all returned owners."""
    collection=state.collection
    if state.player_sources is not None:
        context=state.player_sources.context(collection.level,state.source_id,state.action_sequence1644)
        collection=replace(collection,resource_context=context)
    result=collect_pickups(collection,now_bits)
    if result.status!='core_projection':raise PendingHeadless135(result.status)
    if (collection.level.stats.flag2574==0 and collection.level.phase2587==1
            and result.state.level.phase2587==2):
        motion=moving_sequence_delta(state.records,now_bits,auxiliary_motions=(),claims=())
        result=replace(result,state=replace(result.state,death=replace(result.state.death,
            message_sequence=(result.state.death.message_sequence+motion.count)&f.MASK)))
    if state.player_sources is None:
        state=_sync_pickup_owner(replace(state,collection=result.state),
            pre_compaction_records=result.pre_compaction_records)
        return _growth_banners(state,result.growth_events)
    from .mixed_resource135 import project_mixed_pickup_storage135
    from .opening_npc_pickups135 import OpeningVector135
    vector=OpeningVector135(56,tuple(tuple(cells135(row,56))for row in state.pickup_storage56),
        state.pickup_active_count)
    physical=project_mixed_pickup_storage135(vector,collection.death.records,result)
    packets=[];notifications=[]
    for effect in result.ordered_effects:
        if effect.stage=='despawn':
            packets.append((170,struct.pack('<Q',effect.guid).hex()))
        packets.extend(effect.packets)
        notifications.extend(effect.notifications)
    #Growth packets are already attached to each XP award in reverse
    #consumption order. Appending growth_events again would duplicate150 and
    #move it after a later rune/coin instead of preserving the original order.
    state=_adopt_player_context135(state,result.state.resource_context,result.state,
        packets=packets,notifications=notifications,
        live_owner=_resource_live_origins135(state.player_sources,result.ordered_effects,now_bits))
    return replace(state,pickup_storage56=tuple(encode_row(row)for row in physical.storage),
        pickup_active_count=physical.count)


def step_frame(state, dt_bits):
    """Controlled full single-state tail, not880front/party/transport orboot.

    Omitted880 phases and active915 continuation remain explicit boundaries.
    Unknown due timers or a selected unsupported ability stop before the frame.
    """
    if not 0 <= f.to_float(dt_bits) <= .1000000015: raise ValueError('Finite clamped frame delta required')
    level = state.collection.level
    if level.phase2587 != 1: return state, (), 'not_running'
    if any(not supported(x.record.definition_pointer) for x in level.choice_inputs.owned) or not supported(state.racial.definition_pointer):
        return state, (), 'pending_selected_ability'
    now = f.add(level.stats.now_bits, dt_bits)
    words = dict(state.initial_scalars)
    if f.to_float(now)>=f.to_float(words[2440]):
        return state, (), 'pending_due_event'
    next_boss=words[2456]
    if next_boss<5 and f.to_float(f.div(now,0x42700000))>=f.to_float(BOSSES[state.zone][next_boss][5]):
        return state, (), 'pending_scheduled_boss'
    if next_boss>=5 and state.tail.flag2568 and f.to_float(now)>=f.to_float(words[2460]):
        return state, (), 'pending_endless_boss'
    player_before=state
    state = replace(state, collection=replace(state.collection,
        level=replace(level, stats=replace(level.stats, now_bits=now))), frames=state.frames + 1)
    if state.player_sources is None:
        prepared = prepare_player_update(state.collection.level, state.live_records, state.unspecified_live_words,
            now, dt_bits, state.incoming.last_hit_1648_bits, explicit_other_sources_absent=True, periodic_input=())
        state = replace(state, collection=replace(state.collection, level=prepared.level),
            live_records=prepared.live_records, unspecified_live_words=prepared.unspecified_live_words)
    else:
        context=state.player_sources.context(state.collection.level,state.source_id,state.action_sequence1644)
        prepared=prepare_resource_player_update135(state.collection.level,context,now,dt_bits,
            state.incoming.last_hit_1648_bits,explicit_other_sources_absent=True,periodic_input=())
        sources=state.player_sources
        if prepared.recalculated:
            sources=sources.retain(lambda row:f.to_float(now)<f.to_float(u32(row,24,'2088 retain expiry')))
        state=_adopt_player_context135(state,prepared.context,
            replace(state.collection,level=prepared.level),packets=prepared.packets,live_owner=sources)
    stages = []
    def stage(kind,previous,current):
        current=_inherit_aux135(previous,current,kind)
        stages.append((kind,current))
        return current
    state=stage('player',player_before,_cast_phase(state,dt_bits))
    state=stage('extra',state,_tail_phase(state,'extra',dt_bits))
    state=stage('owned_effects',state,_tail_phase(state,'owned_effects',dt_bits))
    state=stage('hits',state,_cast_phase(state,dt_bits,phase='hits'))
    state=stage('area',state,_cast_phase(state,dt_bits,phase='area'))
    state=stage('effects',state,_effects_phase(state,dt_bits))
    state=stage('deadline',state,_tail_phase(state,'deadline',dt_bits))
    state=stage('secondary',state,_tail_phase(state,'secondary',dt_bits))
    state=stage('ai',state,_ai_phase(state,dt_bits))
    state=stage('collect',state,_collect_phase135(state,now))
    state=stage('claims',state,_tail_phase(state,'claims',dt_bits))
    if state.tail.gate2579:
        raise PendingHeadless135('Alternate2579 spawn/special gate requires continuation')
    spawn_before=state
    level = state.collection.level
    frame = FrameInput(state.zone, now, dt_bits, state.budget_bits, state.collection.death.kill_cost_bits,
        level.stats.flag2574, state.collection.currency.member_count, level.heal_gate387, words[2516],
        0, 0, 0, state.collection.player_xyz, state.previous_player_xyz, state.velocity_xy,
        state.flat_height_bits, level.rng_words, state.collection.death.spawn_counter, state.records, True)
    spawned = step_ordinary_frame(frame, destination_slots=state.unit_storage,world=state.world,
        distance_map=state.distance_map,allow_unknown_storage_growth=state.allow_unknown_storage_growth)
    if spawned.status != 'ordinary_projection': raise PendingHeadless135(spawned.status)
    collection = replace(state.collection, level=replace(level, rng_words=spawned.rng_words),
        death=replace(state.collection.death, spawn_counter=spawned.counter, kill_cost_bits=spawned.kill_cost_bits))
    state = replace(state, collection=collection, records=spawned.unit_records,
        unit_storage=_store_prefix(state.unit_storage, spawned.unit_records,stride=424,allow_growth=state.allow_unknown_storage_growth),
        budget_bits=spawned.budget_bits, velocity_xy=spawned.velocity_xy,
        previous_player_xyz=state.collection.player_xyz if level.stats.flag2574==0 else state.previous_player_xyz)
    state=_event_phase(state)
    state=_resource_phase(state)
    state=_supply_phase(state)
    state=stage('spawn',spawn_before,state)
    state=stage('special',state,_tail_phase(state,'special',dt_bits))
    state=stage('terminal',state,_tail_phase(state,'terminal',dt_bits))
    return state, tuple(stages), 'ordered_frame_projection'


def select(state, index):
    """Use actual generated candidates; never replace them to force a result."""
    before_selection=state
    collection = state.collection
    value = SelectionCycleState(collection.level, 0, 0, collection.death.records, collection.player_xyz[0],
        collection.player_xyz[1], collection.currency, state.game_tag, collection.xp_queue, collection.xp_queue_capacity)
    result = select_card(value, index, additional_modifiers=())
    if not result.accepted: return state, result.status
    run_ledger=state.run_ledger
    if run_ledger is not None:
        run_ledger=record_ordinary_selection135(run_ledger,collection.level.candidates[index],
            phase2587=collection.level.phase2587,selection_kind2585=collection.level.selection_kind2585)
    selected = result.state
    records = selected.pickups
    player_sources=state.player_sources
    if player_sources is None:
        live = []; unknown = set()
        for i, raw in enumerate(state.live_records):
            if result.status == 'running' and struct.unpack_from('<I', bytes.fromhex(raw), 20)[0] == 1020: continue
            j = len(live); live.append(raw)
            unknown.update((j, offset) for row, offset in state.unspecified_live_words if row == i)
        if result.status == 'running':
            index = len(live); expiry = selected.level.sources.live_effects[-1].expires_bits
            live.append(struct.pack('<8I', 0, 0, 12, 0, 0, 1020, expiry, 0).hex())
            unknown.update(((index, 12), (index, 16)))
    else:
        if result.status=='running':
            player_sources=player_sources.retain(lambda row:u32(row,20,'4600 retain1020')!=1020)
            physical=resume_live1020_135(player_sources.live,selected.level.stats.now_bits,
                resumption_explicit=True)
            player_sources=player_sources.replace_live(physical)
            level,player_sources=player_sources.refresh_aura(selected.level)
            selected=replace(selected,level=level)
        live,unknown=player_sources.active_view()
    collection = replace(collection, level=selected.level, currency=selected.currency,
        death=replace(collection.death, records=records), xp_queue=selected.xp_queue,
        xp_queue_capacity=selected.xp_queue_capacity)
    if collection.level.stats.flag2574 == 0 and result.status in ('running', 'choice_regenerated'):
        motion = moving_sequence_delta(state.records, collection.level.stats.now_bits,
            auxiliary_motions=(), claims=())
        collection = replace(collection, death=replace(collection.death,
            message_sequence=(collection.death.message_sequence + motion.count) & f.MASK))
    state = _sync_pickup_owner(replace(state, collection=collection, game_tag=selected.game_tag,
        live_records=tuple(live), unspecified_live_words=tuple(sorted(unknown)),
        player_sources=player_sources,selections=state.selections + 1,run_ledger=run_ledger),removal_order='forward')
    state=_growth_banners(state,result.growth_events)
    return _inherit_aux135(before_selection,state,'selection1072',before_selection.collection.level.selection_kind2585),result.status


def projection(state):
    result = level_projection(state.collection.level)
    if state.player_sources is None:
        result['player_fields'] = {k: v for k, v in result['player_fields'].items() if int(k) in (22, 28, 34, 716, 717, 1109, 1176)}
    live=[]
    for raw in state.live_records:
        row=cells135(raw,32)
        live.append([None if None in row[o:o+4]else u32(row,o,'Player live projection')for o in range(0,32,4)])
    for index, offset in state.unspecified_live_words: live[index][offset // 4] = None
    pickups = [list(pickup_words135(p))for p in state.collection.death.records]
    def storage_sha(storage):
        if any(not isinstance(row,(str,bytes))and None in row for row in storage):return None
        return hashlib.sha256(b''.join(bytes.fromhex(row)if isinstance(row,str)else known_bytes(row)for row in storage)).hexdigest()
    result.update(records=list(state.records), racial_record_hex=state.racial.to_bytes().hex(),
        owned_records_hex=[x.record.to_bytes().hex() for x in state.collection.level.choice_inputs.owned],
        timer1628_bits=state.melee_timer_bits, budget_bits=state.budget_bits,next_resource2444_bits=state.next_resource2444_bits,
        next_event2424_bits=state.next_event2424_bits,last_event2586=state.last_event2586,next_supply2448_bits=state.next_supply2448_bits,
        velocity_xy=list(state.velocity_xy), previous_player_xyz=list(state.previous_player_xyz), now_bits=state.collection.level.stats.now_bits,
        unit_storage_sha256=storage_sha(state.unit_storage),
        area_records=list(state.areas), area_capacity=len(state.area_storage),
        area_storage_sha256=storage_sha(state.area_storage),
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
        game_tag=str(state.game_tag), auxiliary_motion_count=0, claim_count=0,
        tail_state=tail_projection(state.tail), timed916_count=len(state.collection.level.sources.timed_records),
        effect_state=dict(clock2364_bits=state.effect_clock2364_bits,
            effect_counter2356=state.effect_counter2356, action_sequence1644=state.action_sequence1644,
            player_action_tag416=state.player_action_tag416, player_xyz=list(state.collection.player_xyz),
            delayed56=dict(capacity=len(state.delayed_storage56), records_hex=list(state.delayed_records56)),
            effects120=dict(capacity=state.effect_capacity120, records_hex=list(state.effect_records120))))
    if state.run_ledger is not None:
        result['run_ledger']=run_ledger_projection135(state.run_ledger,state.collection.level,state.collection.currency)
        result['terminal_notifications']=list(state.terminal_notifications)
        result['paused408']=state.paused408
        result['paused412_bits']=state.paused412_bits
        result['fatal_stop_packets']=list(state.fatal_stop_packets)
        result['physical_output_pending']=list(state.physical_output_pending)
    if state.player_sources is not None:
        sources=state.player_sources
        result['player_source_owner']={
            'live_capacity':sources.live.capacity,'live_count':sources.live.count,
            'live_backing_cells':[list(row)for row in sources.live.storage],
            'aura_capacity':sources.aura.capacity,'aura_initialized2569':sources.aura.initialized2569,
            'aura_backing_cells':[list(row)for row in sources.aura.storage],
            'notification_next_id14340336':sources.notification_next_id14340336,
            'rune_notifications':list(state.rune_notifications)}
    if state.opening_handoff is not None:
        path=state.distance_map
        result['independent_opening_owner']={
            'unit_capacity':len(state.unit_storage),'unit_backing_cells':[cells135(row,424)for row in state.unit_storage],
            'area_backing_cells':[cells135(row,88)for row in state.area_storage],
            'pickup_active_count':state.pickup_active_count,'pickup_backing_cells':[cells135(row,56)for row in state.pickup_storage56],
            'window_count':state.window_count,'window_backing_cells':[cells135(row,8)for row in state.window_storage8],
            'boundary_count':state.boundary_count,'boundary_backing_cells':[cells135(row,8)for row in state.boundary_storage8],
            'special_selected392':state.tail.special_selected392,'special_target396':state.tail.special_target396,
            'special_announced2565':state.tail.special_announced2565,'special_clock2392_bits':state.tail.special_clock2392_bits,
            'distance_map':None if path is None else dict(start_index=path.start_index,reachable=path.field24,
                values_sha256=hashlib.sha256(b''.join(struct.pack('<H',v)for v in path.values_u16)).hexdigest()),
            'distance_map_updated_at_bits':state.distance_map_updated_at_bits,
            'guardian_cooldowns':[dict(unit_index=x.unit_index,guid=str(x.guid),capacity=x.capacity,
                timers_bits=list(x.timers_bits),ability_pointer=x.ability_pointer,header_pointer=x.header_pointer,
                ability_records44_hex=list(x.ability_records44_hex),header28_hex=x.header28_hex)for x in state.guardian_cooldowns],
            'produced_packets':[list(x)for x in state.produced_packets],
            'new_mainloop_is_full880':False}
    return result
