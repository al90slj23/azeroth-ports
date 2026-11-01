"""Independent135 numeric constructor1560 for an empty selected-profile.

This restores a real constructor boundary, not account creation or asset boot.
The376B input producer above1560 remains explicit and incomplete. This scope
has no purchased gear, talent ranks, enabled gear slots or appearance overrides;
constructor10319 still produces its own default visual equipment. No runtime IO.
"""
from dataclasses import dataclass,replace

from . import binary32 as f
from .ability_state import AbilityRecord
from .candidates135 import Owned
from .derived_stats135 import StatsInput,recalculate
from .level_cycle135 import (LevelCycleState,StatScalars,StatSources,ChoiceInputs,projection as level_projection)
from .progression134 import ProgressionState
from .initial_state135_data import CLASS_STARTERS,RACIAL_ABILITIES,ZONE_ENTRIES

MASK64=(1<<64)-1


def _u(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:
        raise ValueError('Explicit uint'+str(bits)+' required')
    return value


@dataclass(frozen=True)
class ConstructorInput135:
    class_byte:int
    race_byte:int
    region_index:int
    seed_u64:int
    object_id_u64:int
    flat_height_bits:int

    def __post_init__(self):
        _u(self.class_byte,8);_u(self.race_byte,8);_u(self.seed_u64,64);_u(self.object_id_u64,64);_u(self.flat_height_bits)
        if type(self.region_index)is not int or not 0<=self.region_index<len(ZONE_ENTRIES):
            raise ValueError('Explicit fixed region index required')


@dataclass(frozen=True)
class InitialState135:
    level:LevelCycleState
    owned:tuple
    racial:AbilityRecord
    player_xyz:tuple
    source_id:int
    timer1628_bits:int
    spawn_counter:int
    message_sequence:int
    kill_cost_bits:int
    region_index:int
    game_tag:int
    member_count:int
    initial_scalar_words:tuple
    initial_byte_flags:tuple
    pending:tuple


def seed_rng_words(seed):
    """1560's inlined deterministic four PCG seed words, before game draws."""
    _u(seed,64)
    def draw(multiplier,increment):
        n=(seed*multiplier+increment)&MASK64
        value=((n>>45)^(n>>27))&f.MASK
        rotate=(n>>59)&31
        return ((value>>rotate)|(value<<((-rotate)&31)))&f.MASK
    a=draw(7520897724310334953,-2259998930035483990)
    b=draw(793875393913628917,5507651024068337109)
    c=draw(-338549647893938671,-3398641427998916252)
    d=draw(6364136223846793005,-6812164046247290893)
    ab=a|b;abd=ab|d
    check=(ab>>24)|(c&0xffffff)|(d>>24)|((ab|(abd>>8)|(abd>>16)|d)&255)
    if check or c>=0x1000000:
        return(d,a,b,c)
    raw=(-2152535657050944081)&MASK64
    high=7960286522194355700
    return(raw&f.MASK,raw>>32,high&f.MASK,high>>32)


def initialize_empty_profile(value):
    """Execute the proven numeric/stat-source slice of full constructor1560.

    Caller-provided high-level class/race/region/seed are constructor inputs.
    Output stats, RNG, starters and their cooldowns are derived here. Account
    creation, character48 -> selected-profile376 assembly and entering the
    world/phase1 remain explicit pending boundaries, not silently supplied.
    """
    if not isinstance(value,ConstructorInput135):
        raise TypeError('Explicit constructor input required')
    class_id,class_pointer,hp=CLASS_STARTERS.get(value.class_byte,CLASS_STARTERS[1])
    race_id,race_pointer,execution,effect=RACIAL_ABILITIES.get(value.race_byte,RACIAL_ABILITIES[1])
    owned=AbilityRecord(class_pointer);racial=AbilityRecord(race_pointer)
    sources=StatSources((),(),(),(),(),(),())
    before=StatsInput(class_byte=value.class_byte,race_byte=value.race_byte,level=1,
        old_max_hp_bits=hp,current_hp_bits=hp,now_bits=0,previous_speed_bits=0x40e00000,
        conditional268_bits=0,flag2574=0,pool1532_bits=0,pool1536_bits=0,
        conditional1344_id=0,conditional1348_bits=0,pool768_bits=0)
    result=recalculate(before);derived=tuple(sorted((int(k),v)for k,v in result['derived_bits'].items()))
    maximum=dict(derived)[1536]
    # Constructor writes1440=1536 after1512, regardless of1512's HP preservation.
    stats=StatScalars(value.class_byte,value.race_byte,maximum,maximum,0,result['speed_bits'],0,0,0,0,0,0,0)
    fields=tuple(sorted((int(k),v)for k,v in result['object_fields'].items()))
    state=LevelCycleState(ProgressionState(1,0,0),stats,sources,derived,fields,
        seed_rng_words(value.seed_u64),ChoiceInputs((Owned(class_id,owned),),(),(),0,0),(),0,255,0,0,0,0,0,0)
    zone=ZONE_ENTRIES[value.region_index]
    # Raw-width construction constants.2456 is read as an integer by947;
    # these generic names deliberately avoid guessing every counter's role.
    scalars=((488,0),(740,0),(744,0),(1652,0xc1200000),
        (2416,0x40400000),(2424,0x42700000),(2428,0),(2432,0),(2436,0),
        (2440,0x43700000),(2444,0x42200000),(2448,0x42700000),(2452,20),
        (2456,0),(2460,0),(2464,0),(2468,0),(2472,0),(2516,0x3f800000))
    flags=tuple((offset,0)for offset in(772,2568,2572,2573,2576,2578,2581,2583))
    return InitialState135(state,(owned,),racial,(zone[1],zone[2],value.flat_height_bits),
        value.object_id_u64,0,10,1,0,value.region_index,0,1,scalars,flags,
        ('Upstream account/character48 to selected-profile376 producer is not fully reconstructed',
         'Default visual equipment/physical trees and heap resources are not projected',
         'Full world registration/entry1089 and racial execution/effect paths remain pending'))


def projection(state):
    value=level_projection(state.level)
    value.update(owned_records_hex=[r.to_bytes().hex()for r in state.owned],
        racial_record_hex=state.racial.to_bytes().hex(),player_xyz=list(state.player_xyz),
        source_id=str(state.source_id),timer1628_bits=state.timer1628_bits,
        spawn_counter=state.spawn_counter,message_sequence=state.message_sequence,kill_cost_bits=state.kill_cost_bits,
        game_tag=str(state.game_tag),member_count=state.member_count,
        initial_scalar_words=dict(state.initial_scalar_words),initial_byte_flags=dict(state.initial_byte_flags),
        now_bits=0,mode2582=0,owned_capacity=1,owned_count=1,
        source_counts={'passives':0,'adjustments':0,'item_modifiers':0,'owned_skills':0,'timed_records':0,'definitions':0,'live_effects':0,'ability_modifiers':0,'active84':0},
        unit_count=0,pickup_count=0,gold=0,earned=0,flags772=0,context908=0,
        extra_cast1596_bits=dict(state.level.derived_bits)[1596])
    return value
