"""Independent default-mode0 opening fourNPC/two kind2 producers.

The world is a resolved pure query input. This module performs no IO and never
reads an original snapshot. Initial vectors must be empty, but caller-owned
preallocated backing, including prior unwritten bytes, is retained exactly.
Only the resulting whole1089 differential can validate the final composition.
"""
from dataclasses import dataclass
import math
import struct

from . import binary32 as f
from .spawn135 import SpawnInput,spawn_normal,definition
from .spawn_geometry135 import hypot_bits
from .spawn_heading135 import atan2_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .world_position135 import WorldPositionInput135,sample_spawn_position,sample_random_position
from .opening_entities135 import BASE_SPEEDS,LogicalCreate135,unit_create169,create_world_actor

NPC_WRITTEN_RANGES=((0,4),(8,4),(16,4),(40,4),(64,4),(112,136),(280,139))


class UnknownOpeningNPCPickups135(NotImplementedError):pass


def _u(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:raise ValueError('Exact unsigned word required')
    return value


def _finite(value):
    _u(value)
    if value&0x7fffffff>=f.INF:raise ValueError('Finite binary32 input required')
    return value


@dataclass(frozen=True)
class OpeningVector135:
    stride:int
    storage:tuple
    count:int=0

    def __post_init__(self):
        if self.stride not in(56,424)or not 0<=self.count<=len(self.storage)<=4096:
            raise ValueError('Explicit56/424 physical opening vector required')
        for row in self.storage:
            if len(row)!=self.stride or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in row):
                raise ValueError('Every physical byte must be known or explicitly unknown')

    @property
    def capacity(self):return len(self.storage)


def opening_vector_from_hex(stride,storage,count=0):
    return OpeningVector135(stride,tuple(tuple(bytes.fromhex(row))for row in storage),count)


def _reserve_row(vector):
    if vector.count<vector.capacity:return vector
    capacity=max(4,2*vector.capacity)
    return OpeningVector135(vector.stride,vector.storage+((None,)*vector.stride,)*(capacity-vector.capacity),vector.count)


def _write_row(vector,writes):
    vector=_reserve_row(vector);rows=list(vector.storage);row=list(rows[vector.count])
    for offset,payload in writes:
        if offset<0 or offset+len(payload)>vector.stride:raise ValueError('Physical write exceeds row')
        row[offset:offset+len(payload)]=payload
    rows[vector.count]=tuple(row)
    return OpeningVector135(vector.stride,tuple(rows),vector.count+1)


def _ceil_u32(word):
    value=f.to_float(word)
    if math.isnan(value)or value<=0:return 0
    if value>=4294967295:return 4294967295
    return math.ceil(value)


def npc_create_fields(guid,entry,display,scale_bits,hp_bits,elite,player_guid,level1432):
    """Complete1525 logical keyed fields, including zero-valued target16/17."""
    _u(guid,64);_u(player_guid,64);_u(level1432)
    hp=_ceil_u32(hp_bits);level=min((level1432+(3 if elite else 0))&f.MASK,63)
    return tuple(sorted({0:guid&f.MASK,1:guid>>32,2:9,3:entry,4:scale_bits,
        16:player_guid&f.MASK,17:player_guid>>32,22:hp,28:hp,34:level,35:14,36:256,46:0,
        126:2000,127:2000,129:f.mul(scale_bits,0x3f000000),130:f.mul(scale_bits,0x3fc00000),
        131:display,132:display,134:0x40a00000,135:0x41200000,145:0x3f800000}.items()))


@dataclass(frozen=True)
class OpeningNPCResult135:
    vector:OpeningVector135
    counter:int
    rng_words:tuple
    position_draws:int
    entity_draws:int
    creates:tuple
    positions:tuple

    @property
    def draws(self):return self.position_draws+self.entity_draws


def create_opening_npcs(zone,player_xyz,world,rng_words,counter,*,player_guid,
                        level1432,now_bits,zone_multiplier_bits,difficulty,
                        velocity_xy=(0,0),members=1,victory_field400=0,
                        endless_flag=0,endless_start_bits=0,vector=None):
    """Four complete5736(defaultdefinition0/positionNone) logical producers.

    This is mode0 and an emptyNPC starting count. Sampling8751 consumes its
    actual RNG before5736's random record yaw and scheduling jitter. Packet
    facing is separately atan2 towards player, not the record's random396.
    """
    vector=vector if vector is not None else OpeningVector135(424,())
    if vector.stride!=424 or vector.count:raise UnknownOpeningNPCPickups135('Default opening requires an explicit emptyNPC starting vector')
    for value in(*player_xyz,*velocity_xy,now_bits,zone_multiplier_bits,endless_start_bits):_finite(value)
    for value in(counter,level1432,members,victory_field400):_u(value)
    _u(player_guid,64);_u(difficulty,8);_u(endless_flag,8)
    words=tuple(rng_words);creates=[];positions=[];position_draws=entity_draws=0
    for _ in range(4):
        location=sample_spawn_position(WorldPositionInput135(zone,tuple(player_xyz),tuple(velocity_xy),
            0x41d00000,0x42100000,0x3f000000,words),world)
        words=location.rng_words;position_draws+=location.draws;positions.append(location)
        vector=_reserve_row(vector);old=vector.storage[vector.count]
        # The numeric spawn projection needs concrete scratch bytes. Unknown
        # placeholders never escape: only actual5736 written ranges are used.
        concrete=bytes(0 if x is None else x for x in old)
        value=spawn_normal(SpawnInput(zone,0,now_bits,zone_multiplier_bits,difficulty,0,members,
            victory_field400,endless_flag,endless_start_bits,(0,)*vector.count,words,counter,
            location.position_bits,0,concrete.hex()))
        if not value.success:raise UnknownOpeningNPCPickups135('Four default openingNPCs unexpectedly reached cap')
        generated=bytes.fromhex(value.record_hex)
        vector=_write_row(vector,tuple((offset,generated[offset:offset+length])for offset,length in NPC_WRITTEN_RANGES))
        counter,words=value.counter,value.rng_words;entity_draws+=value.draws
        desc=definition(zone,0);x,y,_=location.position_bits
        facing=atan2_bits(f.sub(player_xyz[1],y),f.sub(player_xyz[0],x))
        fields=npc_create_fields(value.guid,desc['entry'],desc['display'],desc['scale_bits'],
            value.hp_bits,desc['elite'],player_guid,level1432)
        packet=unit_create169(value.guid,location.position_bits,facing,BASE_SPEEDS,fields)
        creates.append(LogicalCreate135(value.guid,3,location.position_bits,facing,fields,packet.hex()))
    return OpeningNPCResult135(vector,counter,words,position_draws,entity_draws,tuple(creates),tuple(positions))


@dataclass(frozen=True)
class InitialKind2Result135:
    vector:OpeningVector135
    counter:int
    rng_words:tuple
    position_draws:int
    actor_draws:int
    creates:tuple
    positions:tuple
    final_positions:tuple

    @property
    def draws(self):return self.position_draws+self.actor_draws


def _pickup_kind2_xyz(zone,xyz,world):
    """1417 common radius-2 clamp and final height query, ordered f32 ops."""
    cx,cy,radius=ZONE_GEOMETRY[zone];x,y,_=xyz
    dx,dy=f.sub(x,cx),f.sub(y,cy);distance=hypot_bits(dx,dy)
    limit=f.add(radius,0xc0000000)
    limit=limit if not f.is_nan(limit)and f.to_float(limit)>1 else 0x3f800000
    if not f.to_float(distance)<=f.to_float(limit):
        x=f.add(cx,f.mul(f.div(dx,distance),limit));y=f.add(cy,f.mul(f.div(dy,distance),limit))
        # The first clamped-position lookup is present in1417 even though the
        # common kind2 branch below queries again. Queries are pure inputs.
        first=world.height(x,y)
        if not first.found:world.nearest_primary(x,y)
    sampled=world.height(x,y)
    if sampled.found:z=sampled.value_bits
    else:
        nearest=world.nearest_primary(x,y)
        z=nearest.xyz_bits[2]if nearest.found else world.fallback_height_bits
    return(x,y,z)


def create_initial_kind2(zone,player_xyz,world,rng_words,counter,*,now_bits,
                         velocity_xy=(0,0),vector=None):
    """Two13516(18,50)→1417(kind2,amount2then1)→1821 producers.

    Empty initial pickup count makes both requests fall below mode0 kind2 cap5;
    no replacement/merge branch is silently treated as this successful path.
    Every56B write is explicit except the genuinely unwritten word+4.
    """
    vector=vector if vector is not None else OpeningVector135(56,())
    if vector.stride!=56 or vector.count:raise UnknownOpeningNPCPickups135('Default kind2 opening requires empty pickup starting vector')
    for value in(*player_xyz,*velocity_xy,now_bits):_finite(value)
    _u(counter);words=tuple(rng_words);creates=[];positions=[];final=[];position_draws=actor_draws=0
    for amount in(2,1):
        location=sample_random_position(WorldPositionInput135(zone,tuple(player_xyz),tuple(velocity_xy),
            0x41900000,0x42480000,0,words),world)
        words=location.rng_words;position_draws+=location.draws;positions.append(location)
        xyz=_pickup_kind2_xyz(zone,location.position_bits,world);final.append(xyz)
        actor=create_world_actor(9005,259,0x3f800000,xyz,3,0,counter,words)
        counter,words=actor.counter,actor.rng_words;actor_draws+=actor.draws;creates.append(actor.create)
        vector=_write_row(vector,((0,struct.pack('<I',0)),(8,struct.pack('<IIQ',2,amount,actor.create.guid)),
            (24,struct.pack('<III',0,8,0)),(36,struct.pack('<I',9005)),
            (40,struct.pack('<4I',*xyz,now_bits))))
    return InitialKind2Result135(vector,counter,words,position_draws,actor_draws,tuple(creates),tuple(positions),tuple(final))
