"""Typed expected-first prefix for two current925 emission-order probes.

Replays from independent fullopening/XP5/firstThunder, not captured output.
Uses v1 ordinaryAI/lifetime models only to compute preceding owner state;
their known combined-message order defect is not asserted as passing evidence.
The target AI925 step is deliberately not executed here.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .thunder_clap_world139 import prepare_thunder_world139
from .player_autocast139 import PlayerAutocastState139,update_player_autocast139
from .default_damage139 import DefaultOutgoingLedger139
from .player_enemy139 import PlayerEnemyState139,update_player_enemy139,_incoming_after_player
from .enemy_ai139 import EnemyAIState139,position_xyz139
from .enemy_ai_dead139 import PhysicalNPCVector139
from .incoming139 import IncomingState139,Buff139,word
from .incoming_history139 import IncomingHistory139
from .death139 import OrdinaryDamageState139,DefaultDeathSources139
from .death_pickups139 import PickupVector139
from .hit_events139 import produce_default_cleave_hit_sources139,prove_owned_execution11_absent139
from .candidates139_data import DEFINITIONS139
from .frame_clock139 import FrameClock139,sample_frame_clock139,bits64,advance_game_clock139


@dataclass(frozen=True)
class PlayerEnemyProbeSource139:
    before_target_player:PlayerEnemyState139
    after_target_player:PlayerEnemyState139
    target_ai:EnemyAIState139
    units:PhysicalNPCVector139
    previous_steps:tuple
    target_player_result:object
    clock:FrameClock139
    target_now_bits:int
    target_dt_bits:int
    target_step_index:int
    timestamps64:tuple
    placement:dict|None


def prepare_player_enemy_probe_source139(world,case_id):
    if case_id not in(0,1):raise ValueError('Two exact source-frozen ordering probes')
    opening,gain,selected,p=prepare_thunder_world139(11,world)
    placement=None
    if case_id==1:
        xyz=position_xyz139(p.growth.units432_cells[0],0);height=world.height(*xyz[:2])
        if not height.found:raise ValueError('Canonical actual map height required')
        p=replace(p,player_xyz=(*xyz[:2],height.value_bits))
        placement=dict(anchor_index=0,height_bits=height.value_bits)
    g=p.growth;profile=[None]*376
    for offset in(160,*range(260,336,4)):profile[offset:offset+4]=bytes(4)
    profile[344]=profile[345]=1
    declarations=tuple((DEFINITIONS139[k][0],bytes.fromhex(DEFINITIONS139[k][1]))for k in('cleave','thunder_clap'))
    hit=produce_default_cleave_hit_sources139(tuple(profile),(g.owned_records80[0],),g.racial_record80)
    hit=replace(hit,owned_execution_scan=prove_owned_execution11_absent139(g.owned_records80,declarations))
    d=OrdinaryDamageState139(g.units432_cells,g.rng_words,0,1,0,(),0,0,opening.counter,1,0,
        g.current_hp_bits,g.derived_bits[1536],PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),
        DefaultDeathSources139(hit,(),(),(),(),()))
    actor=PlayerAutocastState139(p,d,DefaultOutgoingLedger139(0,0,()),0,0)
    incoming=IncomingState139(1,0,0,0,g.current_hp_bits,g.derived_bits[1536],g.derived_bits[1568],g.derived_bits[1572],
        last_hit1652_bits=p.last_hit1652_bits,player_xy=p.player_xyz[:2],records432=g.units432_cells,
        live32=tuple(Buff139(word(r,8),None if word(r,8)==12 else word(r,12),word(r,20),word(r,24))for r in p.live.active),items8=())
    state=PlayerEnemyState139(actor,PhysicalNPCVector139(d.records432,len(d.records432)),incoming,
        IncomingHistory139(0,0,0,(),(),()),None,0)
    target=81 if case_id==0 else 39
    clock=FrameClock139(1,bits64(0.));steps=[];stamps=[]
    for index in range(target+1):
        stamp=bits64((index+1)*.125);stamps.append(stamp)
        sampled=sample_frame_clock139(clock,stamp);clock=sampled.state
        now=advance_game_clock139(state.actor.player.growth.now_bits,sampled.dt_bits,phase2587=1)
        if index<target:
            value=update_player_enemy139(state,now,sampled.dt_bits,world)
            state=value.state;steps.append(value)
        else:
            before=state;player=update_player_autocast139(state.actor,now,sampled.dt_bits,world)
            units=PhysicalNPCVector139(tuple(player.state.damage.records432)+state.units.storage[state.units.count:],state.units.count)
            state=replace(state,actor=player.state,units=units)
            incoming=_incoming_after_player(state)
            ai=EnemyAIState139(units.active,now,sampled.dt_bits,player.state.player.player_xyz,incoming,state.history,
                tuple(player.state.player.growth.player_fields.items()),player.state.damage.movement_sequence2412,
                state.distance_map,state.distance_clock2372_bits)
            return PlayerEnemyProbeSource139(before,state,ai,units,tuple(steps),player,clock,
                now,sampled.dt_bits,target,tuple(stamps),placement)
