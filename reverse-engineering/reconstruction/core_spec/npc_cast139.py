"""Independent139 constructor→natural4NPC→controlled-player-action→cleave.

The world provider and actions are explicit. No original memory or executable
is read. Scripted relocation is not an input/motion/AI implementation; lethal
hits retain the existing explicit death boundary instead of inventing rewards.
"""
from dataclasses import dataclass, replace
from . import binary32 as f
from .initial_state139 import ConstructorInput139, initialize_empty_profile139
from .opening_profile139 import advance_app_seed139
from .natural_npc139 import NaturalNPCInput139, create_four_natural_normals139
from .cast139 import CleaveState139, CleaveDefinition139
from .cast_cells139 import cast_cleave_cells139
from .combat139 import DamageState139, EmptyDamageSources139
from .record_cells135 import u32
from .initial_state139_data import ZONE_ENTRIES


@dataclass(frozen=True)
class NPCCombatInput139:
    rng_words: tuple | None = None
    counter: int = 10
    action: str = 'near_first'
    repeats: int = 1
    gentle_owned_multiplier: bool = False
    initial_backing: tuple = ()

    def __post_init__(self):
        if self.action not in ('keep_start','near_first','near_second'):
            raise ValueError('Explicit controlled player action required')
        if type(self.repeats)is not int or not 1<=self.repeats<=4:
            raise ValueError('Bounded explicit invocation count required')


def compose_npc_cleave139(value,world,definition):
    if not isinstance(value,NPCCombatInput139)or not isinstance(definition,CleaveDefinition139):
        raise TypeError('Explicit current139 input/definition required')
    cx,cy=ZONE_ENTRIES[0][1:3];height=world.height(cx,cy)
    if not height.found:
        raise NotImplementedError('Default constructor ground height unavailable')
    initial=initialize_empty_profile139(ConstructorInput139(1,1,0,
        advance_app_seed139(0),0,height.value_bits))
    initial_rng=initial.rng_words if value.rng_words is None else tuple(value.rng_words)
    npc=create_four_natural_normals139(NaturalNPCInput139(initial_rng,value.counter,
        initial.player_xyz,(0,0),value.initial_backing,None),world)
    last=npc['answers'][-1];records=tuple(tuple(row)for row in last['records432_cells'])
    player=initial.player_xyz
    if value.action!='keep_start':
        row=records[0 if value.action=='near_first'else 1]
        player=tuple(u32(row,o,'controlled139 player placement')for o in(316,320,324))
    derived=initial.stats_result['derived_bits']
    combat=DamageState139((),0,1,0,tuple(last['rng_words']),EmptyDamageSources139((),(),(),True))
    cast=CleaveState139(combat,player,derived['1536'],derived['1540'],
        derived['1548'],derived['1552'],derived['1592'],source_id=0)
    owned=bytes.fromhex(initial.owned_records_hex[0])
    assert u32(owned,0)==definition.pointer
    if value.gentle_owned_multiplier:
        raw=bytearray(owned);raw[12:16]=f.from_float(.1).to_bytes(4,'little');owned=bytes(raw)
    stages=[]
    for _ in range(value.repeats):
        result=cast_cleave_cells139(cast,records,definition,owned)
        cast=result.empty_unit_state;records=result.records432_cells
        stages.append(dict(success=result.success,
            records432_cells=[list(row)for row in records],
            rng_words=list(cast.combat.rng_words),
            accounted_total_bits=str(cast.combat.accounted_total_bits),
            spell_sets=[list(row)for row in cast.spell_sets],owned80_hex=owned.hex(),
            launch306_packets=[]if result.launch306_hex is None else[[306,result.launch306_hex]],
            player_xyz=list(player),phase2587=1))
    return dict(npc_answers=npc['answers'],stages=stages,
        actor_before=dict(derived_bits=derived,owned80_hex=initial.owned_records_hex[0],
            initial_rng=list(initial.rng_words),player_xyz=list(initial.player_xyz),
            phase2587=0,source_id='0'),
        controlled_action=value.action,
        gentle_owned_multiplier=value.gentle_owned_multiplier,
        model_private_completion_runs=2*len(stages),
        unknowns_preserved=True)
