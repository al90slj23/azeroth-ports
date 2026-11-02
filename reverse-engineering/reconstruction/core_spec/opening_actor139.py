"""Independent current139 world actor1886 and opening kind2 pickups1446.

The world is an explicit pure provider and the source data are newly rebound
to1391108/1886/1446. Allocator-unwritten bytes stayNone. This module does not
read an original,snapshot,capture,asset,account,App,save or host.
"""
from dataclasses import dataclass
import math,struct
from . import binary32 as f
from .rng import next_u32_words,uniform_range_bits
from .position_math139 import sin_bits,cos_bits,hypot_bits
from .world_position139_v2 import WorldPositionInput139V2,sample_random_position
from .opening_aux139_data import(CENTER_XY_BITS,HEADING_BITS,RADIUS_BITS,FALLBACK_BITS,BOUNDARY_FLAG148,ELITE_IDS,WINDOW_COUNT_RANGE,LAST_BOSS_MINUTES_BITS,KIND2_DESCRIPTOR,BOUNDARY_DESCRIPTOR)

TAU=0x40c90fdb
class UnknownOpeningAux139(NotImplementedError):pass
def _uint(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:raise ValueError('Explicit unsigned word required')
    return value
def _finite(value):
    _uint(value)
    if f.is_nan(value)or f.is_inf(value):raise UnknownOpeningAux139('Explicit finite opening coordinate required')
    return value

@dataclass(frozen=True)
class OpeningVector139:
    stride:int
    storage:tuple
    count:int=0
    def __post_init__(self):
        if self.stride not in(8,40,56,88)or type(self.count)is not int or not 0<=self.count<=len(self.storage)<=4096:raise ValueError('Bounded explicit auxiliary vector required')
        for row in self.storage:
            if len(row)!=self.stride or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in row):raise ValueError('Complete known/None physical backing required')
    @property
    def capacity(self):return len(self.storage)

def vector_from_hex139(stride,storage,count):return OpeningVector139(stride,tuple(tuple(bytes.fromhex(row))for row in storage),count)
def _append(vector,writes):
    rows=list(vector.storage)
    if vector.count==len(rows):rows.extend([(None,)*vector.stride]*(max(4,2*len(rows))-len(rows)))
    row=list(rows[vector.count])
    for offset,value in writes:
        if not 0<=offset<=offset+len(value)<=vector.stride:raise ValueError('Record store bounds')
        row[offset:offset+len(value)]=value
    rows[vector.count]=tuple(row);return OpeningVector139(vector.stride,tuple(rows),vector.count+1)

def _guid(guid):
    _uint(guid,64);raw=guid.to_bytes(8,'little');return bytes([sum(1<<i for i,b in enumerate(raw)if b)])+bytes(b for b in raw if b)
def _values(fields):
    values=dict(fields)
    if any(type(k)is not int or not 0<=k<8160 for k in values):raise ValueError('Exact u16 object field keys')
    for value in values.values():_uint(value)
    count=max(values,default=-1)//32+1;mask=[0]*count
    for key in values:mask[key//32]|=1<<(key%32)
    return bytes([count])+struct.pack('<'+'I'*count,*mask)+b''.join(struct.pack('<I',values[key])for key in sorted(values))
def actor_create169_139(guid,xyz,yaw,fields):
    return(struct.pack('<IB',1,0)+bytes([2])+_guid(guid)+bytes([5,80])+struct.pack('<4I',*xyz,yaw)+struct.pack('<I',1)+_values(fields))

@dataclass(frozen=True)
class ActorCreate139:
    guid:int
    xyz_bits:tuple
    yaw_bits:int
    fields:tuple
    payload169:bytes
@dataclass(frozen=True)
class ActorResult139:
    create:ActorCreate139
    counter:int
    rng_words:tuple
    draws:int

def create_world_actor139(entry,display,scale_bits,xyz,kind21,flags9,counter,rng_words):
    for value in(entry,display,scale_bits,kind21,flags9,counter,*xyz):_uint(value)
    if len(xyz)!=3:raise ValueError('Three XYZ words required')
    counter=(counter+1)&f.MASK;guid=0xf110000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
    angle=uniform_range_bits(tuple(rng_words),0,TAU);yaw=f.add(angle.bits,0);half=f.mul(yaw,0x3f000000)
    fields=tuple(sorted({0:guid&f.MASK,1:guid>>32,2:33,3:entry,4:scale_bits,8:display,9:flags9,12:sin_bits(half),13:cos_bits(half),14:1,15:xyz[0],16:xyz[1],17:xyz[2],18:yaw,20:35,21:kind21}.items()))
    return ActorResult139(ActorCreate139(guid,tuple(xyz),yaw,fields,actor_create169_139(guid,xyz,yaw,fields)),counter,tuple(angle.state),angle.draws)

def _height(world,x,y):
    value=world.height(x,y)
    if value.found:return value.value_bits
    if world.primary is not None:raise UnknownOpeningAux139('Default no-primary world required when height misses')
    return world.fallback_height_bits
def _kind2_xyz(xyz,world):
    x,y=xyz[:2];dx,dy=f.sub(x,CENTER_XY_BITS[0]),f.sub(y,CENTER_XY_BITS[1]);distance=hypot_bits(dx,dy);limit=f.sub(RADIUS_BITS,0x40000000)
    if f.to_float(distance)>f.to_float(limit):
        x=f.add(CENTER_XY_BITS[0],f.mul(f.div(dx,distance),limit));y=f.add(CENTER_XY_BITS[1],f.mul(f.div(dy,distance),limit))
        # The original performs a preliminary query here and queries again
        # on the common kind2 path. Only resolved coordinates are retained.
        world.height(x,y)
    return(x,y,_height(world,x,y))

@dataclass(frozen=True)
class Kind2Result139:
    vector:OpeningVector139
    counter:int
    rng_words:tuple
    creates:tuple
    positions:tuple
    final_xyz:tuple
    position_draws:int
    actor_draws:int

def append_kind2_pickup139(xyz,amount,world,rng_words,counter,*,now_bits,vector=None):
    vector=vector if vector is not None else OpeningVector139(56,())
    if vector.stride!=56 or vector.count>=5:raise UnknownOpeningAux139('Only mode0 kind2 count below5 append;replacement/merge remain separate')
    for word in(*xyz,now_bits):_finite(word)
    _uint(amount);_uint(counter);placed=_kind2_xyz(xyz,world)
    actor=create_world_actor139(*KIND2_DESCRIPTOR,placed,3,0,counter,rng_words)
    vector=_append(vector,((0,struct.pack('<I',0)),(8,struct.pack('<IIQ',2,amount,actor.create.guid)),(24,struct.pack('<4I',0,8,0,KIND2_DESCRIPTOR[0])),(40,struct.pack('<4I',*placed,now_bits))))
    return Kind2Result139(vector,actor.counter,actor.rng_words,(actor.create,),(),(placed,),0,actor.draws)

def create_initial_kind2_139(player_xyz,world,rng_words,counter,*,now_bits=0,velocity_xy=(0,0),distance_map=None,vector=None):
    vector=vector if vector is not None else OpeningVector139(56,())
    if vector.stride!=56 or vector.count:raise UnknownOpeningAux139('Two opening kind2 require explicitly empty pickup count')
    words=tuple(rng_words);creates=[];positions=[];final=[];position_draws=actor_draws=0
    for amount in(2,1):
        location=sample_random_position(WorldPositionInput139V2(0,tuple(player_xyz),tuple(velocity_xy),0x41900000,0x42480000,0,words,distance_map),world)
        result=append_kind2_pickup139(location.position_bits,amount,world,location.rng_words,counter,now_bits=now_bits,vector=vector)
        vector,counter,words=result.vector,result.counter,result.rng_words;creates.extend(result.creates);positions.append(location);final.extend(result.final_xyz);position_draws+=location.draws;actor_draws+=result.actor_draws
    return Kind2Result139(vector,counter,words,tuple(creates),tuple(positions),tuple(final),position_draws,actor_draws)
