"""Typed current139 actual-damage prefix for new combat→952 experiments.

Only independently specified fullopening/XP5/selection/AI/player/cleave models
run here. No original files, observations or expected captures are read.
"""
from dataclasses import dataclass,replace
from .autocast_dead_source139 import prepare_autocast_dead_source139
from .thunder_clap_world139 import prepare_thunder_world139
from .enemy_ai_dead139_v2 import PhysicalNPCVector139
from .enemy_ai139 import position_xyz139
from .default_damage139 import cast_cleave_default139
from .player_autocast139 import _adopt
from .healing139 import DefaultHealingSources139
from .cast139 import CleaveDefinition139
from .candidates139_data import DEFINITIONS139
from .death139 import word139,guid139
from .spawn_schedule139_v4 import from_combat139

@dataclass(frozen=True)
class SpawnCombatSource139:
 opening:object
 cold_source:object
 actor:object
 units:PhysicalNPCVector139
 scheduler:object
 extra_controls:tuple
 extra_results:tuple


def prepare_spawn_combat_source139(world,dead_count):
 if dead_count not in(1,2,4):raise ValueError('Three genuine prefix death counts')
 opening,_,_,_=prepare_thunder_world139(11,world)
 source=prepare_autocast_dead_source139(world);actor=source.actor;controls=[];results=[]
 definition=CleaveDefinition139(5882740,b'cleave',bytes.fromhex(DEFINITIONS139['cleave'][1]))
 while sum(word139(r,0)==1 for r in actor.damage.records432)<dead_count:
  index=next(i for i,r in enumerate(actor.damage.records432)if word139(r,0)==0);guid=guid139(actor.damage.records432[index]);xyz=position_xyz139(actor.damage.records432[index],actor.damage.now_bits);sample=world.height(*xyz[:2])
  if not sample.found:raise ValueError('True canonical player placement required')
  player=(*xyz[:2],sample.value_bits);actor=replace(actor,player=replace(actor.player,player_xyz=player));g=actor.player.growth
  result=cast_cleave_default139(actor.damage,player,{str(k):v for k,v in g.derived_bits.items()},definition,g.owned_records80[0],actor.player.spell_sets,world,healing=actor.ledger,healing_sources=DefaultHealingSources139(1,g.source_counts),inherited_context908=0,source_id=0,heal_on_kill1600_bits=g.derived_bits[1600]);controls.append(dict(anchor_index=index,anchor_guid=str(guid),now_bits=actor.damage.now_bits,player_xyz=list(player)));results.append(result);actor=_adopt(actor,result)
  if len(controls)>12:raise RuntimeError('Actual-damage model prefix deadline')
 units=PhysicalNPCVector139(actor.damage.records432,len(actor.damage.records432));state=from_combat139(opening,actor,units,distance_map=source.ai.distance_map)
 return SpawnCombatSource139(opening,source,actor,units,state,tuple(controls),tuple(results))

def kill_live_normals139(actor,world):
 """Actual-cleave model calls after a real scheduler step, never writes NPC HP."""
 controls=[];results=[];definition=CleaveDefinition139(5882740,b'cleave',bytes.fromhex(DEFINITIONS139['cleave'][1]))
 while any(word139(r,0)==0 for r in actor.damage.records432):
  index=next(i for i,r in enumerate(actor.damage.records432)if word139(r,0)==0);guid=guid139(actor.damage.records432[index]);xyz=position_xyz139(actor.damage.records432[index],actor.damage.now_bits);sample=world.height(*xyz[:2]);assert sample.found;player=(*xyz[:2],sample.value_bits);actor=replace(actor,player=replace(actor.player,player_xyz=player));g=actor.player.growth
  result=cast_cleave_default139(actor.damage,player,{str(k):v for k,v in g.derived_bits.items()},definition,g.owned_records80[0],actor.player.spell_sets,world,healing=actor.ledger,healing_sources=DefaultHealingSources139(1,g.source_counts),inherited_context908=0,source_id=0,heal_on_kill1600_bits=g.derived_bits[1600]);controls.append(dict(anchor_index=index,anchor_guid=str(guid),now_bits=actor.damage.now_bits,player_xyz=list(player)));results.append(result);actor=_adopt(actor,result)
  if len(controls)>64:raise RuntimeError('Bounded genuine-cleave clearing producer')
 return actor,tuple(controls),tuple(results)

@dataclass(frozen=True)
class SpawnMovingSource139:
 opening:object
 probe:object
 actor:object
 units:PhysicalNPCVector139
 scheduler:object


def prepare_spawn_moving_source139(world,source_id):
 """Frozen continuous producer; previous packets are not acceptance evidence."""
 from .player_enemy_probe_source139 import prepare_player_enemy_probe_source139
 opening,_,_,_=prepare_thunder_world139(11,world);probe=prepare_player_enemy_probe_source139(world,source_id);actor=probe.after_target_player.actor;state=from_combat139(opening,actor,probe.units,distance_map=probe.target_ai.distance_map)
 return SpawnMovingSource139(opening,probe,actor,probe.units,state)
