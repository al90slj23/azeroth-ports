"""WIP current139 opening windows,special40 and boundary composition.

Actor/rune primitives are separately frozen in opening_actor139. Unknown
branches stay explicit; complete1108 acceptance is reported separately.
"""
from dataclasses import dataclass
import math,struct
from . import binary32 as f
from .rng import next_u32_words,uniform_range_bits
from .position_math139 import sin_bits,cos_bits
from .ai_trig135 import sin_bits as extended_sin_bits,cos_bits as extended_cos_bits
from .opening_aux139_data import(CENTER_XY_BITS,HEADING_BITS,RADIUS_BITS,BOUNDARY_FLAG148,WINDOW_COUNT_RANGE,LAST_BOSS_MINUTES_BITS,BOUNDARY_DESCRIPTOR)
from .opening_actor139 import(OpeningVector139,UnknownOpeningAux139,vector_from_hex139,create_world_actor139,append_kind2_pickup139,create_initial_kind2_139,_append,_height)
TAU=0x40c90fdb
#1108 enumerates normal72, filters flag68==1/finite64, then pushes the
#enumeration index. IDs609/610/611 at record24 are a different field.
ELITE_DEFINITION_INDICES139=(9,10,11)

@dataclass(frozen=True)
class WindowResult139:
    vector:OpeningVector139
    rng_words:tuple
    count_draws:int
    window_draws:int
def create_opening_windows139(rng_words,vector=None):
    vector=vector if vector is not None else OpeningVector139(8,())
    if vector.stride!=8:raise ValueError('Eight-byte window records')
    words=tuple(rng_words);count_draws=0
    while True:
        output,words=next_u32_words(words);product=output*2;count_draws+=1
        if product&f.MASK<=0x7fffffff:count=WINDOW_COUNT_RANGE[0]+(product>>32);break
        if count_draws>100000:raise UnknownOpeningAux139('Bounded independent count RNG watchdog')
    width=f.div(f.mul(LAST_BOSS_MINUTES_BITS,0x42700000),f.from_u32(count));vector=OpeningVector139(8,vector.storage,0);draws=0
    for i in range(count):
        value=uniform_range_bits(words,0x3f19999a,0x3f800000);words=value.state;draws+=value.draws;start=f.mul(width,f.from_u32(i));end=f.add(start,f.mul(width,value.bits));vector=_append(vector,((0,struct.pack('<2I',start,end)),))
    return WindowResult139(vector,tuple(words),count_draws,draws)

def _blocked(world,x,y):
    for dx in range(-2,3):
        for dy in range(-2,3):
            probe=world.nav_probe(f.add(x,f.from_float(dx)),f.add(y,f.from_float(dy)))
            if probe.present and probe.in_bounds:
                if probe.value not in(0,1):raise UnknownOpeningAux139('Only canonical0/1 navigation byte semantics restored')
                if probe.value:return True
    return False
def create_special_records139(world,vector=None):
    vector=vector if vector is not None else OpeningVector139(40,())
    if vector.stride!=40:raise ValueError('Forty-byte special records')
    cx,cy=CENTER_XY_BITS;centre_z=_height(world,cx,cy)
    for i in range(4):
        angle=f.add(f.mul(f.mul(f.from_u32(i),TAU),0x3e800000),f.add(HEADING_BITS,0x3f490fdb));co=cos_bits(angle)if angle&0x7fffffff<=TAU else extended_cos_bits(angle);si=sin_bits(angle)if angle&0x7fffffff<=TAU else extended_sin_bits(angle);xyz=None
        for coefficient in(0x3f333333,0x3f1eb852,0x3f0a3d71,0x3eeb851f,0x3ec28f5c):
            distance=f.mul(RADIUS_BITS,coefficient);x=f.add(cx,f.mul(co,distance));y=f.add(cy,f.mul(si,distance))
            if _blocked(world,x,y):continue
            sample=world.height(x,y)
            if sample.found and f.to_float(f.sub(sample.value_bits,centre_z)&0x7fffffff)<30:xyz=(x,y,sample.value_bits);break
        if xyz is None:
            distance=f.mul(RADIUS_BITS,0x3f000000);x=f.add(cx,f.mul(distance,co));y=f.add(cy,f.mul(distance,si));xyz=(x,y,_height(world,x,y))
        vector=_append(vector,((0,bytes(8)),(16,struct.pack('<3I',*xyz)),(28,struct.pack('<2I',ELITE_DEFINITION_INDICES139[i%len(ELITE_DEFINITION_INDICES139)],0x41a00000))))
    return vector

@dataclass(frozen=True)
class BoundaryResult139:
    vector:OpeningVector139
    counter:int
    rng_words:tuple
    creates:tuple
    draws:int
def boundary_candidates139():
    radius=f.add(RADIUS_BITS,0x41200000);count=math.ceil(f.to_float(f.div(f.mul(radius,TAU),0x41400000)));result=[]
    for i in range(count):
        angle=f.div(f.mul(f.from_u32(i),TAU),f.from_u32(count));result.append((f.add(CENTER_XY_BITS[0],f.mul(radius,cos_bits(angle))),f.add(CENTER_XY_BITS[1],f.mul(radius,sin_bits(angle)))))
    return tuple(result)
def create_boundaries139(world,counter,rng_words,vector=None):
    vector=vector if vector is not None else OpeningVector139(8,())
    if vector.stride!=8 or BOUNDARY_FLAG148:raise UnknownOpeningAux139('Only current default circle/flag0 boundary path')
    creates=[];words=tuple(rng_words);draws=0
    for x,y in boundary_candidates139():
        actor=create_world_actor139(*BOUNDARY_DESCRIPTOR,(x,y,_height(world,x,y)),5,16,counter,words);counter,words=actor.counter,actor.rng_words;creates.append(actor.create);draws+=actor.draws;vector=_append(vector,((0,struct.pack('<Q',actor.create.guid)),))
    return BoundaryResult139(vector,counter,words,tuple(creates),draws)
