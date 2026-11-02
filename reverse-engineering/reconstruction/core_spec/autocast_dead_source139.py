"""Pure typed producer for the cold/moving current139 death-prefix fixture.

Replays the source procedure of frozen autocast formal case2 through2123 step6.
No original/output files or bytes are read. Future oracle users must perform a
new source-bound native prefix; this helper itself adds no runtime evidence.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .thunder_clap_world139 import prepare_thunder_world139
from .player_autocast139 import PlayerAutocastState139,update_player_autocast139
from .default_damage139 import DefaultOutgoingLedger139
from .enemy_ai139 import EnemyAIState139,update_enemy_ai139,position_xyz139
from .incoming139 import IncomingState139,Buff139
from .incoming_history139 import IncomingHistory139
from .death139 import OrdinaryDamageState139,DefaultDeathSources139,word139
from .death_pickups139 import PickupVector139
from .hit_events139 import produce_default_cleave_hit_sources139,prove_owned_execution11_absent139
from .candidates139_data import DEFINITIONS139


@dataclass(frozen=True)
class AutocastDeadSource139:
    actor:PlayerAutocastState139
    ai:EnemyAIState139
    setup_ai_result:object
    steps:tuple
    controlled_player_xyz:tuple
    input_app_seed:int=11


def prepare_autocast_dead_source139(world):
    opening,gain,selected,p=prepare_thunder_world139(11,world)
    g=p.growth
    history=IncomingHistory139(0,0,0,(),(),())
    incoming=IncomingState139(1,0,0,0,g.current_hp_bits,g.derived_bits[1536],
        g.derived_bits[1568],g.derived_bits[1572],last_hit1652_bits=p.last_hit1652_bits,
        player_xy=p.player_xyz[:2],records432=g.units432_cells,
        live32=tuple(Buff139(word139(r,8),None if word139(r,8)==12 else word139(r,12),
            word139(r,20),word139(r,24))for r in p.live.active),items8=())
    setup=update_enemy_ai139(EnemyAIState139(g.units432_cells,0,0x3dcccccd,p.player_xyz,
        incoming,history,tuple(g.player_fields.items()),1),world,
        english_names={5830904:'Kobold Vermin'})
    assert not setup.attacks
    pos=position_xyz139(setup.state.records432[0],0x3dcccccd)
    xy=(f.add(pos[0],0x41000000),pos[1]);height=world.height(*xy)
    if not height.found:raise ValueError('Actual controlled map height required')
    player=(*xy,height.value_bits)
    p=replace(p,player_xyz=player,growth=replace(g,units432_cells=setup.state.records432))
    profile=[None]*376
    for offset in(160,*range(260,336,4)):profile[offset:offset+4]=bytes(4)
    profile[344]=profile[345]=1
    declarations=tuple((DEFINITIONS139[k][0],bytes.fromhex(DEFINITIONS139[k][1]))for k in('cleave','thunder_clap'))
    hit=produce_default_cleave_hit_sources139(tuple(profile),(g.owned_records80[0],),g.racial_record80)
    hit=replace(hit,owned_execution_scan=prove_owned_execution11_absent139(g.owned_records80,declarations))
    d=OrdinaryDamageState139(p.growth.units432_cells,g.rng_words,0,1,0,(),0,0,
        opening.counter,setup.state.movement_sequence2412,0,g.current_hp_bits,g.derived_bits[1536],
        PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),
        DefaultDeathSources139(hit,(),(),(),(),()))
    actor=PlayerAutocastState139(p,d,DefaultOutgoingLedger139(0,0,()),0,0)
    steps=[]
    for _ in range(6):
        now=f.add(actor.player.growth.now_bits,0x3dcccccd)
        value=update_player_autocast139(actor,now,0x3dcccccd,world)
        actor=value.state;steps.append(value)
    p=actor.player;g=p.growth
    incoming=replace(incoming,now_bits=g.now_bits,records432=g.units432_cells,
        hp1440_bits=g.current_hp_bits,maximum1536_bits=g.derived_bits[1536],
        armor1568_bits=g.derived_bits[1568],armor_cap1572_bits=g.derived_bits[1572],
        nearby1624_bits=g.derived_bits[1624],player_xy=p.player_xyz[:2],
        last_hit1652_bits=p.last_hit1652_bits,
        live32=tuple(Buff139(word139(r,8),None if word139(r,8)==12 else word139(r,12),
            word139(r,20),word139(r,24))for r in p.live.active))
    ai=replace(setup.state,records432=g.units432_cells,now_bits=g.now_bits,
        player_xyz=player,incoming=incoming,history=history,
        player_fields=tuple(g.player_fields.items()),movement_sequence2412=actor.damage.movement_sequence2412)
    return AutocastDeadSource139(actor,ai,setup,tuple(steps),player)
