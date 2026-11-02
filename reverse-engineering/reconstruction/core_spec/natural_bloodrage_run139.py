"""Natural single-cleave139 opening→2123→925→2890→first choice adapter.

All XP comes from actual death-pickup consumption. Spawn952 and other884
stages remain separate until their proper owner interfaces are composed.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .opening139 import DefaultOpeningInput139,initialize_default_opening139
from .opening_profile139 import EmptyAccountSources139
from .growth139 import from_constructor139
from .player_update139 import PlayerUpdateState139,LiveVector139
from .player_effects139 import AuraSnapshot139
from .bloodrage_autocast139 import NaturalBloodrageAutocastState139 as NaturalAutocastState139,update_natural_bloodrage_autocast139 as update_natural_autocast139
from .bloodrage_damage139 import BloodrageLedger139 as NaturalOutgoingLedger139
from .natural_demo_growth_v2_139 import PlayerGrowthContext139,gain_xp_player139,select_first_new_player139
from .natural_collection139 import NaturalCollectionState139,ForwardQueue139,constructor_empty_claims139,collect_natural_pickups139
from .enemy_ai139 import EnemyAIState139
from .enemy_ai_dead139_v2 import PhysicalNPCVector139
from .demo_family_ai139 import update_demo_family139
from .incoming139 import IncomingState139,Buff139,word
from .incoming_history139 import IncomingHistory139
from .death139 import OrdinaryDamageState139,DefaultDeathSources139
from .bloodrage139 import attach_bloodrage_state139,update_owned_effects983_139,BloodrageDeathSources139,scan_bloodrage_sources139
from .healing139 import DefaultHealingSources139
from .death_pickups139 import PickupVector139
from .hit_events139 import produce_default_cleave_hit_sources139,prove_owned_execution11_absent139
from .candidates139_data import DEFINITIONS139


class PendingNaturalRun139(NotImplementedError):pass


@dataclass(frozen=True)
class NaturalRunState139:
    actor:NaturalAutocastState139
    units:PhysicalNPCVector139
    incoming:IncomingState139
    history:IncomingHistory139
    distance_map:object
    distance_clock2372_bits:int
    claims:object
    xp_queue:ForwardQueue139
    coin_queue:ForwardQueue139
    gold1456:int=0
    earned1100:int=0

    def __post_init__(self):
        if self.actor.damage.records432!=self.units.active or self.actor.player.growth.units432_cells!=self.units.active:raise ValueError('Complete physical/logical count-domain NPC source')


def _incoming(state,player,units):
    g=player.growth
    return replace(state,phase2587=g.phase2587,now_bits=g.now_bits,hp1440_bits=g.current_hp_bits,
        maximum1536_bits=g.derived_bits[1536],armor1568_bits=g.derived_bits[1568],armor_cap1572_bits=g.derived_bits[1572],
        nearby1624_bits=g.derived_bits[1624],last_hit1652_bits=player.last_hit1652_bits,player_xy=player.player_xyz[:2],records432=units.active,
        live32=tuple(Buff139(word(r,8),None if word(r,8)==12 else word(r,12),word(r,20),word(r,24))for r in player.live.active))


def _adopt_player(actor,player,units,*,pickups=None,sequence=None,ledger=None):
    g=player.growth;d=actor.damage
    d=replace(d,records432=units.active,rng_words=g.rng_words,now_bits=g.now_bits,phase2587=g.phase2587,
        player_hp1440_bits=g.current_hp_bits,maximum1536_bits=g.derived_bits[1536],
        pickups=d.pickups if pickups is None else pickups,
        movement_sequence2412=d.movement_sequence2412 if sequence is None else sequence)
    return replace(actor,player=player,damage=d,ledger=actor.ledger if ledger is None else ledger)


def prepare_natural_bloodrage_run139(app_seed,world):
    opening=initialize_default_opening139(DefaultOpeningInput139(app_seed,EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
    records=tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells'])
    g=replace(from_constructor139(opening.constructor,phase2587=1),rng_words=opening.rng_words,units432_cells=records)
    p=PlayerUpdateState139(g,LiveVector139((),0),opening.constructor.player_xyz,((),(),()),0,AuraSnapshot139.empty_constructor139())
    profile=[None]*376
    for offset in(160,*range(260,336,4)):profile[offset:offset+4]=bytes(4)
    profile[344]=profile[345]=1
    declarations=((DEFINITIONS139['cleave'][0],bytes.fromhex(DEFINITIONS139['cleave'][1])),)
    hit=produce_default_cleave_hit_sources139(tuple(profile),g.owned_records80,g.racial_record80)
    hit=replace(hit,owned_execution_scan=prove_owned_execution11_absent139(g.owned_records80,declarations))
    d=OrdinaryDamageState139(records,g.rng_words,0,1,0,(),0,0,opening.counter,1,0,g.current_hp_bits,g.derived_bits[1536],
        PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),DefaultDeathSources139(hit,(),(),(),(),()))
    actor=NaturalAutocastState139(p,attach_bloodrage_state139(d,p),NaturalOutgoingLedger139(0,0,()),0,0)
    incoming=IncomingState139(1,0,0,0,g.current_hp_bits,g.derived_bits[1536],g.derived_bits[1568],g.derived_bits[1572],
        last_hit1652_bits=p.last_hit1652_bits,player_xy=p.player_xyz[:2],records432=records,items8=())
    return opening,NaturalRunState139(actor,PhysicalNPCVector139(records,len(records)),incoming,
        IncomingHistory139(0,0,0,(),(),()),None,0,constructor_empty_claims139(),ForwardQueue139(0),ForwardQueue139(0))


@dataclass(frozen=True)
class NaturalRunResult139:
    state:NaturalRunState139
    player_result:object
    ai_result:object
    collection_result:object
    packets:tuple
    heal_events:tuple
    owned_effects_result:object=None


def advance_natural_bloodrage_run139(state,now,dt,world,*,pause_world):
    if state.actor.player.growth.phase2587!=1:raise PendingNaturalRun139('Phase2 UI decision required; no clock/timer skipping')
    player=update_natural_autocast139(state.actor,now,dt,world);actor=player.state
    owned_effects=update_owned_effects983_139(actor,dt,world,healing_sources=DefaultHealingSources139(1,actor.player.growth.source_counts));actor=owned_effects.state
    units=PhysicalNPCVector139(tuple(actor.damage.records432)+state.units.storage[state.units.count:],state.units.count)
    incoming=_incoming(state.incoming,actor.player,units)
    ai=update_demo_family139(EnemyAIState139(units.active,now,dt,actor.player.player_xyz,incoming,state.history,
        tuple(actor.player.growth.player_fields.items()),actor.damage.movement_sequence2412,state.distance_map,state.distance_clock2372_bits),
        units,world)
    units=ai.units;p=actor.player
    p=replace(p,growth=replace(p.growth,units432_cells=units.active,current_hp_bits=ai.ai.incoming.hp1440_bits,
        player_fields=dict(ai.ai.player_fields)),last_hit1652_bits=ai.ai.incoming.last_hit1652_bits)
    actor=_adopt_player(actor,p,units,sequence=ai.ai.movement_sequence2412)
    context=PlayerGrowthContext139(p,actor.ledger,units,actor.damage.movement_sequence2412)
    def gain(growth,award,sequence):
        nonlocal context
        context=replace(context,player=replace(context.player,growth=growth),movement_sequence2412=sequence)
        value=gain_xp_player139(context,award,world,pause_world=pause_world);context=value.context
        return value
    collection=NaturalCollectionState139(p.growth,actor.damage.pickups,state.claims,p.player_xyz,actor.damage.movement_sequence2412,
        state.gold1456,state.earned1100,0,0,1,0,state.xp_queue,state.coin_queue)
    collected=collect_natural_pickups139(collection,now,gain_xp139=gain)
    p=replace(context.player,growth=collected.state.growth)
    actor=_adopt_player(actor,p,units,pickups=collected.state.pickups,sequence=collected.state.movement_sequence2412,ledger=context.ledger)
    incoming=_incoming(ai.ai.incoming,p,units)
    result=replace(state,actor=actor,units=units,incoming=incoming,history=ai.ai.history,distance_map=ai.ai.distance_map,
        distance_clock2372_bits=ai.ai.distance_clock2372_bits,gold1456=collected.state.gold1456,earned1100=collected.state.earned1100,
        xp_queue=collected.state.xp_queue2144,coin_queue=collected.state.coin_queue2156)
    extra_heals=tuple(event for growth_result in collected.growth_results for event in growth_result.heal_events)
    return NaturalRunResult139(result,player,ai,collected,player.packets+owned_effects.packets+ai.packets+collected.packets,player.heal_events+owned_effects.heal_events+extra_heals,owned_effects)


def choose_natural_bloodrage_card139(state,index,world,*,resume_world):
    from .bloodrage_choice139 import select_bloodrage_choice139
    if state.incoming.mode2582 or state.xp_queue.entries:raise PendingNaturalRun139('Default local first4603 selection only')
    context=PlayerGrowthContext139(state.actor.player,state.actor.ledger,state.units,state.actor.damage.movement_sequence2412)
    choice=select_bloodrage_choice139(context,state.actor.damage.pickups,index,world,pause_world=resume_world,resume_world=resume_world)
    if not choice.accepted:return state,choice
    value=choice.growth_result
    actor=_adopt_player(state.actor,value.context.player,state.units,pickups=choice.pickups,sequence=value.context.movement_sequence2412,ledger=value.context.ledger)
    pointers=tuple(word(tuple(r),0)for r in actor.player.growth.owned_records80)
    declarations=tuple((pointer,bytes.fromhex(raw))for pointer,raw,kinds in DEFINITIONS139.values()if pointer in pointers)
    # Preserve actual owned order; dictionary order need not equal selected order.
    declarations=tuple(next(row for row in declarations if row[0]==p)for p in pointers)
    if len(pointers)==3:
        hit=replace(actor.damage.sources.hit_sources,owned_execution_scan=scan_bloodrage_sources139(actor.player.growth.owned_records80))
        sources=BloodrageDeathSources139(hit,(),(),(),(),())
    else:
        hit=replace(actor.damage.sources.hit_sources,owned_execution_scan=prove_owned_execution11_absent139(actor.player.growth.owned_records80,declarations))
        sources=replace(actor.damage.sources,hit_sources=hit)
    actor=replace(actor,damage=attach_bloodrage_state139(replace(actor.damage,sources=sources),actor.player))
    return replace(state,actor=actor,incoming=_incoming(state.incoming,actor.player,state.units)),choice
