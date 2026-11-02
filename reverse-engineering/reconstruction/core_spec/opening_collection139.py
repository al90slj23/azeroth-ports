"""Current139 full default opening→controlled cleave→XP collection.

This composes real independent opening objects, preserving both Rune rows,
windows, special40 and boundary GUIDs. Player placement and direct entry
schedule are controlled inputs, not a recovered input/AI/mainloop scheduler.
Initial combat accounting counters remain an explicit source contract.
"""
from dataclasses import dataclass,replace
from .opening139 import DefaultOpeningInput139,initialize_default_opening139,opening_projection139,opening_known_game139
from .opening_profile139 import EmptyAccountSources139
from .death139 import OrdinaryDamageState139,DefaultDeathSources139,cast_cleave_with_ordinary_death139
from .death_pickups139 import PickupVector139,word139
from .hit_events139 import produce_default_cleave_hit_sources139,prove_owned_execution11_absent139
from .candidates139_data import DEFINITIONS139
from .growth139 import from_constructor139,gain_xp139
from .initial_state139 import canonical_game_cells139
from .collection139 import CollectionState139,ForwardQueue139,constructor_empty_claims139,collect_pickups139
from .growth139 import projection139 as growth_projection139
from .growth_world139 import gain_xp_world139,select_card_world139
from . import binary32 as f


@dataclass(frozen=True)
class OpeningCombatCounters139:
    accounted_total_bits:int
    spell_totals64:tuple
    kills1084:int
    elites1088:int
    movement_sequence2412:int
    killcost2420_bits:int
    gold1456:int
    earned1100:int

    def __post_init__(self):
        values=(self.accounted_total_bits,self.kills1084,self.elites1088,
                self.movement_sequence2412,self.killcost2420_bits,self.gold1456,self.earned1100)
        if any(type(v)is not int or v<0 for v in values):raise ValueError('Explicit unsigned initial counters')
        if self.spell_totals64:raise NotImplementedError('Only explicit empty initial spell totals')


@dataclass(frozen=True)
class OpeningCollectionInput139:
    app_seed_u64:int
    counters:OpeningCombatCounters139
    action:str
    collect_times:tuple

    def __post_init__(self):
        if not isinstance(self.counters,OpeningCombatCounters139):raise TypeError('Explicit counter-source contract')
        if self.action not in('near_first','near_second'):raise ValueError('Controlled player placement')
        if type(self.collect_times)is not tuple or not 1<=len(self.collect_times)<=8:raise ValueError('Bounded controlled entry times')


def collection_projection139(state):
    g=state.growth
    return dict(pickup_capacity=state.pickups.capacity,pickup_count=state.pickups.count,
        pickups56_cells=[list(r)for r in state.pickups.storage],movement_sequence2412=state.movement_sequence2412,
        gold1456=state.gold1456,earned1100=state.earned1100,level1432=g.level,xp1436=g.xp,
        pending2376=g.pending,phase2587=g.phase2587,selection_kind2585=g.selection_kind2585,
        generation2400=g.generation_counter2400,rng_words=list(g.rng_words),hp1440_bits=g.current_hp_bits,
        derived_bits={str(k):v for k,v in g.derived_bits.items()},known_player_fields={str(k):v for k,v in g.player_fields.items()},
        xp_queue2144=dict(capacity=state.xp_queue2144.capacity,entries=[list(v)for v in state.xp_queue2144.entries]),
        coin_queue2156=dict(capacity=state.coin_queue2156.capacity,entries=[list(v)for v in state.coin_queue2156.entries]))


def compose_opening_collection139(value,world,definition):
    if not isinstance(value,OpeningCollectionInput139):raise TypeError('OpeningCollectionInput139')
    opening=initialize_default_opening139(DefaultOpeningInput139(value.app_seed_u64,
        EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
    initial=opening.constructor;owned=bytes.fromhex(initial.owned_records_hex[0]);derived=initial.stats_result['derived_bits']
    records=tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells'])
    profile=[None]*376
    for o in(160,*range(260,336,4)):profile[o:o+4]=bytes(4)
    profile[344]=profile[345]=1
    hit=produce_default_cleave_hit_sources139(tuple(profile),(owned,),bytes.fromhex(initial.racial_record_hex))
    source=DefaultDeathSources139(hit,(),(),(),(),());c=value.counters
    state=OrdinaryDamageState139(records,opening.rng_words,0,1,c.accounted_total_bits,c.spell_totals64,
        c.kills1084,c.elites1088,opening.counter,c.movement_sequence2412,c.killcost2420_bits,
        derived['1536'],derived['1536'],PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),source)
    row=records[0 if value.action=='near_first'else 1];player=tuple(word139(row,o)for o in(316,320,324));sets=((),(),());casts=[]
    for _ in range(2):
        result=cast_cleave_with_ordinary_death139(state,player,derived,definition,owned,sets,world)
        state,sets=result.state,result.spell_sets
        casts.append(dict(success=result.success,records432_cells=[list(r)for r in state.records432],
            rng_words=list(state.rng_words),accounted_total_bits=str(state.accounted_total_bits),
            spell_sets=[list(s)for s in sets],owned80_hex=owned.hex(),player_xyz=list(player),phase2587=state.phase2587,
            spell_totals64=[[spell,str(bits)]for spell,bits in state.spell_totals64],kills1084=state.kills1084,
            elites1088=state.elites1088,counter2408=state.counter2408,movement_sequence2412=state.movement_sequence2412,
            killcost2420_bits=state.killcost2420_bits,player_hp1440_bits=state.player_hp1440_bits,
            maximum1536_bits=state.maximum1536_bits,xp1436=0,pickup_capacity=state.pickups.capacity,
            pickup_count=state.pickups.count,pickups56_cells=[list(r)for r in state.pickups.storage],
            known_packets=[list(p)for p in result.known_packets]))
    claims=constructor_empty_claims139();growth=replace(from_constructor139(initial,phase2587=1),
        rng_words=state.rng_words,current_hp_bits=state.player_hp1440_bits,units432_cells=state.records432,
        claims88_cells=claims.storage88)
    collection=CollectionState139(growth,state.pickups,claims,player,state.movement_sequence2412,
        c.gold1456,c.earned1100,0,0,1,0,ForwardQueue139(0),ForwardQueue139(0))
    stages=[];diagnostics=[]
    for now in value.collect_times:
        result=collect_pickups139(collection,now,gain_xp139=gain_xp139);collection=result.state
        projection=collection_projection139(collection);projection['now_bits']=now;projection['new_packets']=[list(p)for p in result.packets]
        stages.append(projection);diagnostics.append(dict(attractions=result.attraction_events,
            consumption=result.consumption_events,growth=[r.events for r in result.growth_results]))
    component=dict(projection=opening_projection139(opening),known_Game2592=list(opening_known_game139(opening)),
        constructor_cells=list(canonical_game_cells139(initial)),constructor_seed_u64=str(opening.constructor_seed_u64),
        selected40_cells=list(opening.selected40_cells))
    return dict(opening_expected=component,cast_stages=casts,collection_stages=stages,
        diagnostics=diagnostics,source_counters=c,controlled_player_xyz=player,
        background=dict(windows=opening.windows.vector,special=opening.special,boundaries=opening.boundaries.vector),
        full_mainloop_frames=0,complete_games=0)


def compose_firstlevel_opening_collection139(value,world,definition):
    """Actual default drops reach first level; no direct XP award is inserted.

    Each round relocates to the first remaining living normal, calls cleave
    twice, attracts pickups, then advances the controlled clock by .5. The
    bounded schedule ends only after a genuine first choice, or raises at an
    unrecovered domain. It does not clear owners or synthesize XP to finish.
    """
    if not isinstance(value,OpeningCollectionInput139):raise TypeError('OpeningCollectionInput139')
    opening=initialize_default_opening139(DefaultOpeningInput139(value.app_seed_u64,
        EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
    initial=opening.constructor;owned=bytes.fromhex(initial.owned_records_hex[0]);derived=initial.stats_result['derived_bits']
    profile=[None]*376
    for o in(160,*range(260,336,4)):profile[o:o+4]=bytes(4)
    profile[344]=profile[345]=1
    hit=produce_default_cleave_hit_sources139(tuple(profile),(owned,),bytes.fromhex(initial.racial_record_hex))
    sources=DefaultDeathSources139(hit,(),(),(),(),());c=value.counters
    death=OrdinaryDamageState139(tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells']),
        opening.rng_words,0,1,c.accounted_total_bits,c.spell_totals64,c.kills1084,c.elites1088,opening.counter,
        c.movement_sequence2412,c.killcost2420_bits,derived['1536'],derived['1536'],
        PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),sources)
    claims=constructor_empty_claims139();growth=from_constructor139(initial,phase2587=1)
    sets=((),(),());gold,earned=c.gold1456,c.earned1100;clock=0;rounds=[];selection=None
    for round_index in range(4):
        target=next((i for i,row in enumerate(death.records432)if word139(row,0)==0),None)
        if target is None:raise NotImplementedError('Initial normals exhausted before first level;spawn scheduler required')
        row=death.records432[target];player=tuple(word139(row,o)for o in(316,320,324));death=replace(death,now_bits=clock);casts=[]
        for _ in range(2):
            cast=cast_cleave_with_ordinary_death139(death,player,derived,definition,owned,sets,world)
            death,sets=cast.state,cast.spell_sets
            casts.append(dict(success=cast.success,records432_cells=[list(r)for r in death.records432],
                rng_words=list(death.rng_words),accounted_total_bits=str(death.accounted_total_bits),
                spell_sets=[list(s)for s in sets],owned80_hex=owned.hex(),player_xyz=list(player),phase2587=1,
                spell_totals64=[[spell,str(bits)]for spell,bits in death.spell_totals64],kills1084=death.kills1084,
                elites1088=death.elites1088,counter2408=death.counter2408,movement_sequence2412=death.movement_sequence2412,
                killcost2420_bits=death.killcost2420_bits,player_hp1440_bits=death.player_hp1440_bits,
                maximum1536_bits=death.maximum1536_bits,xp1436=growth.xp,pickup_capacity=death.pickups.capacity,
                pickup_count=death.pickups.count,pickups56_cells=[list(r)for r in death.pickups.storage],
                known_packets=[list(p)for p in cast.known_packets]))
        growth=replace(growth,rng_words=death.rng_words,current_hp_bits=death.player_hp1440_bits,
            units432_cells=death.records432,claims88_cells=claims.storage88,now_bits=clock)
        state=CollectionState139(growth,death.pickups,claims,player,death.movement_sequence2412,
            gold,earned,0,0,1,0,ForwardQueue139(0),ForwardQueue139(0));collects=[];diagnostics=[]
        times=(clock,f.add(clock,0x3f000000))
        for now in times:
            result=collect_pickups139(state,now,gain_xp139=gain_xp_world139);state=result.state
            projection=collection_projection139(state);projection.update(now_bits=now,new_packets=[list(p)for p in result.packets],
                growth_projection=growth_projection139(state.growth))
            collects.append(projection);diagnostics.append(dict(attractions=result.attraction_events,
                consumption=result.consumption_events,growth=[r.events for r in result.growth_results]))
        growth=state.growth;gold,earned=state.gold1456,state.earned1100
        rounds.append(dict(target_index=target,now_bits=clock,collect_times=list(times),player_xyz=list(player),
            cast_stages=casts,collection_stages=collects,diagnostics=diagnostics))
        death=replace(death,pickups=state.pickups,movement_sequence2412=state.movement_sequence2412,
            rng_words=growth.rng_words,player_hp1440_bits=growth.current_hp_bits,maximum1536_bits=growth.derived_bits[1536])
        clock=times[-1]
        if growth.phase2587==2:
            card_index=next((i for i,card in enumerate(growth.candidates)if card.variant=='new'),None)
            if card_index is None:raise NotImplementedError('First ordinary choice has no restored new-card route')
            selected=select_card_world139(growth,card_index)
            if not selected.accepted:raise AssertionError('First new-card choice rejected')
            selection=dict(index=card_index,projection=growth_projection139(selected.state),
                live32_cells=[list(r)for r in selected.state.live32_cells])
            break
    if selection is None:raise NotImplementedError('No first choice reached in initial four-normal schedule')
    # The selected state actually owns two records. Re-scan those records;
    # retaining the constructor's one-owned proof would be invalid here.
    selected_state=selected.state
    if selected_state.source_counts!=(0,)*7:raise NotImplementedError('Postselection nonempty source owners')
    declarations=tuple((p,bytes.fromhex(raw))for p,raw,_ in DEFINITIONS139.values())
    scan=prove_owned_execution11_absent139(selected_state.owned_records80,declarations)
    post_sources=replace(sources,hit_sources=replace(sources.hit_sources,owned_execution_scan=scan))
    follow_index=next((i for i,row in enumerate(death.records432)if word139(row,0)==0),None)
    continuation=None
    if follow_index is not None:
        row=death.records432[follow_index];player=tuple(word139(row,o)for o in(316,320,324))
        death=replace(death,phase2587=1,now_bits=clock,rng_words=selected_state.rng_words,
            player_hp1440_bits=selected_state.current_hp_bits,maximum1536_bits=selected_state.derived_bits[1536],sources=post_sources)
        cast=cast_cleave_with_ordinary_death139(death,player,
            {str(k):v for k,v in selected_state.derived_bits.items()},definition,selected_state.owned_records80[0],sets,world)
        follow=cast.state
        continuation=dict(target_index=follow_index,player_xyz=list(player),now_bits=clock,
            actual_owned_scan=dict(pointers=list(scan.definition_pointers),execution_bytes=list(scan.execution_bytes84)),
            state=dict(success=cast.success,records432_cells=[list(r)for r in follow.records432],
                rng_words=list(follow.rng_words),accounted_total_bits=str(follow.accounted_total_bits),
                spell_sets=[list(s)for s in cast.spell_sets],owned80_hex=selected_state.owned_records80[0].hex(),player_xyz=list(player),phase2587=1,
                spell_totals64=[[spell,str(bits)]for spell,bits in follow.spell_totals64],kills1084=follow.kills1084,
                elites1088=follow.elites1088,counter2408=follow.counter2408,movement_sequence2412=follow.movement_sequence2412,
                killcost2420_bits=follow.killcost2420_bits,player_hp1440_bits=follow.player_hp1440_bits,
                maximum1536_bits=follow.maximum1536_bits,xp1436=selected_state.xp,pickup_capacity=follow.pickups.capacity,
                pickup_count=follow.pickups.count,pickups56_cells=[list(r)for r in follow.pickups.storage],
                known_packets=[list(p)for p in cast.known_packets]),
            live32_cells_preserved=[list(r)for r in selected_state.live32_cells])
    component=dict(projection=opening_projection139(opening),known_Game2592=list(opening_known_game139(opening)),
        constructor_cells=list(canonical_game_cells139(initial)),constructor_seed_u64=str(opening.constructor_seed_u64),
        selected40_cells=list(opening.selected40_cells))
    post_hit_sources=dict(pointers=list(scan.definition_pointers),execution_bytes=list(scan.execution_bytes84),
        event_definitions_count=post_sources.hit_sources.event_definitions36.count,initial_mode770=post_sources.hit_sources.initial_mode770)
    return dict(opening_expected=component,rounds=rounds,selection=selection,continuation=continuation,
        postselection_hit_sources=post_hit_sources,source_counters=c,
        next_boundary='Directcleave continuation only;owned2/live12 scheduler and new enemy production not yet integrated',
        full_mainloop_frames=0,complete_games=0)
