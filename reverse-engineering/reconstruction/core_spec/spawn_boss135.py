"""Independent2785 Boss record/ability-clock production on explicit flat terrain.

Object-registry, UI announcements and spell-object side effects are outside this
projection. Owner lookup is an explicit resolved input. No original is loaded.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .rng import next_u32_words
from .spawn135 import max_numeric,min_numeric
from .spawn135_data import ZONES,DIFFICULTY
from .spawn_boss135_data import BOSSES,POINTS
from .spawn_geometry135 import hypot_bits
from .spawn_math135 import endless_power
from .spawn_position135 import PositionInput
from .spawn_position_motion135 import sample_position


def bounded_index(words,count):
    if not 0<count<0x80000000:raise ValueError('Positive bounded table count required')
    mask=((count<<(32-count.bit_length()))-1)&f.MASK
    for draws in range(1,100001):
        output,words=next_u32_words(words);product=output*count
        if (product&f.MASK)<=mask:return product>>32,words,draws
    raise RuntimeError('Independent bounded-index watchdog exceeded')


@dataclass(frozen=True)
class BossInput:
    zone:int
    definition_index:int
    now_bits:int
    zone_multiplier_bits:int
    difficulty:int
    mode:int
    members:int
    victory_field400:int
    endless_flag:int
    endless_start_bits:int
    rng_words:tuple
    counter:int
    player_xyz:tuple
    velocity_xy:tuple
    flat_height_bits:int
    scalar_bits:int
    resolved_owner:int
    initial_slot_hex:str


@dataclass(frozen=True)
class BossResult:
    status:str
    guid:int
    counter:int
    rng_words:tuple
    draws:int
    record_hex:str|None
    timers_bits:tuple
    position_route:str
    selected_point:int|None


def spawn_boss(state:BossInput):
    if not 0<=state.zone<12 or not 0<=state.definition_index<5:raise ValueError('Invalid Boss table index')
    raw=bytearray.fromhex(state.initial_slot_hex)
    if len(raw)!=424:raise ValueError('Explicit full destination slot required')
    words=tuple(state.rng_words);draws=0;points=POINTS[state.zone]
    distances=[hypot_bits(f.sub(x,state.player_xyz[0]),f.sub(y,state.player_xyz[1]))for x,y in points]
    eligible=[i for i,d in enumerate(distances)if f.to_float(d)>=20]
    selected=None
    if eligible:
        index,words,used=bounded_index(words,len(eligible));draws+=used;selected=eligible[index];route='eligible-static-point'
    elif state.zone in(7,11):
        if not points:raise ValueError('Fixed constrained zone requires point declarations')
        # Finite positive hypot words have the same total order as unsigned bits;
        # equality chooses the later static point, as original i32.gt_s/select.
        selected=max(range(len(points)),key=lambda i:(distances[i],i));route='farthest-static-point'
    else:
        placed=sample_position(PositionInput(state.zone,state.player_xyz,state.velocity_xy,0x41c00000,0x41e00000,0,
            state.flat_height_bits,True,True,words))
        words=placed.rng_words;draws+=placed.draws;route='sample8751'
        if placed.status!='resolved_flat':return BossResult(placed.status,0,state.counter,words,draws,None,(),route,None)
        position=placed.position_bits
    if selected is not None:position=(*points[selected],state.flat_height_bits)
    d=BOSSES[state.zone][state.definition_index]
    pointer,entry,display,scale,classification,minute,basehp,baseattack,movement,final,abilities,n,cooldowns=d
    exponent=0
    if state.victory_field400==1 and state.endless_flag&1:
        exponent=max_numeric(f.div(f.sub(state.now_bits,state.endless_start_bits),0x42700000),0)
    eh=endless_power(0x3f9c28f6,exponent);ea=endless_power(0x3f8c49ba,exponent)
    dh,da=DIFFICULTY[state.difficulty-1]if 1<=state.difficulty<=5 else(0x3f800000,0x3f800000)
    group=0x3f800000
    if state.mode==1:
        group=f.mul(f.add(f.mul(f.mul(0x3f333333 if state.zone<3 else 0x3f800000,
            f.from_u32((state.members-1)&f.MASK)),0x3f851eb8),0x3f800000),0x3f4ccccd)
    hp=f.mul(state.scalar_bits,f.mul(f.mul(f.mul(eh,f.mul(f.mul(f.mul(basehp,0x40b80000),ZONES[state.zone][1]),state.zone_multiplier_bits)),dh),group))
    attack=f.mul(f.mul(ea,f.mul(baseattack,sqrt_bits(f.mul(ZONES[state.zone][1],state.zone_multiplier_bits)))),da)
    radius=min_numeric(f.add(f.mul(scale,0x3fc00000),0x40600000),0x41100000)
    counter=(state.counter+1)&f.MASK;guid=0xf130000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
    def w(o,v):struct.pack_into('<I',raw,o,v)
    def q(o,v):struct.pack_into('<Q',raw,o,v)
    for o in(0,8,16):w(o,0)
    w(40,f.MASK);w(64,f.MASK);q(112,guid);raw[120:236]=bytes(116);q(236,4)
    # Allocator address is a canonical zero handle; semantic payload is separate.
    for o,v in((244,n),(248,0),(252,n),(256,pointer),(260,abilities),(264,n),(280,state.resolved_owner),
        (284,0),(288,hp),(292,hp),(296,attack),(300,movement),(304,0x40000000),(308,radius),(312,scale),
        (340,state.now_bits),(344,0),(348,f.add(state.now_bits,0x3f800000)),(352,0x40000000),
        (380,f.add(state.now_bits,0x3fc00000)),(384,state.now_bits),(412,0)):w(o,v)
    q(268,0);raw[276]=0
    for j,v in enumerate(position):w(316+4*j,v);w(328+4*j,v)
    for o in(356,364,372,388,396,404):q(o,0)
    struct.pack_into('<H',raw,416,1);raw[418]=0
    timers=tuple(f.mul(t,0x3f19999a)for t in cooldowns)
    return BossResult('boss_projection',guid,counter,words,draws,raw.hex(),timers,route,selected)
