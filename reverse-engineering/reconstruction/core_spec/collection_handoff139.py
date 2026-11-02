"""Pure current139 constructor/natural4/ordinarydeath→typedcollection handoff.

Phase1/player relocation are explicit controlled actions. The target Game
borrows matching worldcontext;this does not reconstruct App/input/AI/full1108.
"""
from dataclasses import replace
from .initial_state139 import ConstructorInput139,initialize_empty_profile139
from .natural_npc139 import NaturalNPCInput139,create_four_natural_normals139
from .death139 import OrdinaryDamageState139,DefaultDeathSources139,cast_cleave_with_ordinary_death139
from .death_pickups139 import PickupVector139
from .hit_events139 import produce_default_cleave_hit_sources139
from .growth139 import from_constructor139
from .collection139 import CollectionState139,ForwardQueue139,constructor_empty_claims139
from .world_position139_data import ZONE_GEOMETRY139


def prepare_default_collection139(world,definition,*,rng_words=None,counter=10,backing=(),action='near_first',repeats=2):
 cx,cy=ZONE_GEOMETRY139[0][:2];height=world.height(cx,cy)
 if not height.found:raise NotImplementedError('Independentdefaultconstructorworldheight')
 initial=initialize_empty_profile139(ConstructorInput139(1,1,0,1442695040888963407,0,height.value_bits));owned=bytes.fromhex(initial.owned_records_hex[0]);derived=initial.stats_result['derived_bits'];words=initial.rng_words if rng_words is None else tuple(rng_words)
 npc=create_four_natural_normals139(NaturalNPCInput139(tuple(words),counter,initial.player_xyz,(0,0),tuple(backing),None),world);last=npc['answers'][-1];records=tuple(tuple(row)for row in last['records432_cells'])
 if action not in('near_first','near_second'):raise ValueError('Explicitcontrolledrelocation')
 row=records[0 if action=='near_first'else 1];player=tuple(int.from_bytes(bytes(row[o:o+4]),'little')for o in(316,320,324));profile=[None]*376
 for o in(160,*range(260,336,4)):profile[o:o+4]=bytes(4)
 profile[344]=profile[345]=1;hit=produce_default_cleave_hit_sources139(tuple(profile),(owned,),bytes.fromhex(initial.racial_record_hex));sources=DefaultDeathSources139(hit,(),(),(),(),());death=OrdinaryDamageState139(records,tuple(last['rng_words']),0,1,0,(),0,0,last['counter'],1,0,derived['1536'],derived['1536'],PickupVector139(()),sources);sets=((),(),());casts=[]
 for _ in range(repeats):
  result=cast_cleave_with_ordinary_death139(death,player,derived,definition,owned,sets,world);death,sets=result.state,result.spell_sets;casts.append(result)
 claims=constructor_empty_claims139();growth=from_constructor139(initial,phase2587=1)
 # Preserve actual nonemptyNPC owner through every later growth callback.
 growth=replace(growth,rng_words=death.rng_words,current_hp_bits=death.player_hp1440_bits,units432_cells=death.records432,claims88_cells=claims.storage88)
 state=CollectionState139(growth,death.pickups,claims,player,death.movement_sequence2412,0,0,0,0,1,0,ForwardQueue139(0),ForwardQueue139(0))
 return dict(state=state,initial=initial,natural=npc,death=death,casts=tuple(casts),owned80=owned,profile_knowncells=tuple(profile),controlled_action=action)
