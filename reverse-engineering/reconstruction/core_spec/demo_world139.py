"""WIP current139 genuine fullopening/XP5 first-newDemo selection source."""
from dataclasses import dataclass,replace
from .opening139 import DefaultOpeningInput139,initialize_default_opening139
from .opening_profile139 import EmptyAccountSources139
from .growth139 import from_constructor139
from .growth_world139 import gain_xp_world139,select_card_world139
from .player_update139 import PlayerUpdateState139,LiveVector139
from .player_effects139 import AuraSnapshot139,sync_aura139
from .hit_events139 import produce_default_cleave_hit_sources139,prove_owned_execution11_absent139
from .candidates139_data import DEFINITIONS139
from .death139 import OrdinaryDamageState139,DefaultDeathSources139,word139
from .death_pickups139 import PickupVector139
from .demo_damage139 import NaturalOutgoingLedger139
from .healing139 import HealingLedger139

@dataclass(frozen=True)
class DemoActor139:
 player:object
 damage:OrdinaryDamageState139
 ledger:HealingLedger139
 player_guid:int=0
 inherited_context908:int=0
 def __post_init__(self):
  g=self.player.growth;d=self.damage
  if tuple(word139(r,0)for r in g.owned_records80)!=(5882740,5883180):raise ValueError('Actualselectedcleave/Demoownersrequired')
  if d.records432!=g.units432_cells or d.rng_words!=g.rng_words or d.player_hp1440_bits!=g.current_hp_bits:raise ValueError('Actualsharedownerprojection')
  if self.player_guid or self.inherited_context908:raise ValueError('DefaultGUID0/context0')


def demo_gain139(app_seed,world):
 opening=initialize_default_opening139(DefaultOpeningInput139(app_seed,EmptyAccountSources139(0,0,0,0),tuple([165]*40)),world);g=replace(from_constructor139(opening.constructor,phase2587=1),rng_words=opening.rng_words,units432_cells=tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells']));return opening,gain_xp_world139(g,5)


def prepare_demo_world139(app_seed,index,world):
 opening,gain=demo_gain139(app_seed,world);card=gain.state.candidates[index]
 if card.variant!='new'or card.ability_id!='demo_shout':raise ValueError('SelectactualnewDemo cardonly')
 selected=select_card_world139(gain.state,index)
 if not selected.accepted:raise ValueError('ActualnewDemo selectionmustaccept')
 g=selected.state;live=g.live32_cells;p=PlayerUpdateState139(g,LiveVector139(live+tuple((None,)*32 for _ in range(4-len(live))),len(live)),tuple(opening.constructor.player_xyz),((),(),()),0,AuraSnapshot139.empty_constructor139());p=sync_aura139(dict(player_state=p,growth=g,live=p.live,spell_sets=p.spell_sets,aura=p.aura_state,racial80=g.racial_record80,player_xyz=p.player_xyz))['player_state']
 profile=[None]*376
 for off in(160,*range(260,336,4)):profile[off:off+4]=bytes(4)
 profile[344]=profile[345]=1
 hit=produce_default_cleave_hit_sources139(tuple(profile),(g.owned_records80[0],),g.racial_record80);decl=tuple((DEFINITIONS139[n][0],bytes.fromhex(DEFINITIONS139[n][1]))for n in('cleave','demo_shout'));hit=replace(hit,owned_execution_scan=prove_owned_execution11_absent139(g.owned_records80,decl));d=OrdinaryDamageState139(g.units432_cells,g.rng_words,0,1,0,(),0,0,opening.counter,1,0,g.current_hp_bits,g.derived_bits[1536],PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),DefaultDeathSources139(hit,(),(),(),(),()))
 return opening,gain,selected,DemoActor139(p,d,NaturalOutgoingLedger139(0,0,()))
