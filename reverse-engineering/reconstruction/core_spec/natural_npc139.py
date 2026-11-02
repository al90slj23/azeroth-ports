"""Independent139 four natural initialNPCs, interleaving8740 and5719 RNG.

Only defaultElwynn/time0/mode0/definition0/playerGUID0/level1 is admitted.
Worldquery data is anexplicit independentprovider. No original/snapshot isread.
Realworld Rc/profile ownership andthe restof1108 remain separate.
"""
from dataclasses import dataclass
from . import binary32 as f
from .npc_spawn139 import InitialNPCInput139,initial_normal139,NPC_WRITTEN_RANGES
from .world_position139_v2 import WorldPositionInput139V2 as WorldPositionInput139,DistanceMap139V2 as DistanceMap139,sample_spawn_position
from .world_position139_data import ZONE_GEOMETRY139

@dataclass(frozen=True)
class NaturalNPCInput139:
    rng_words:tuple
    counter:int
    player_xyz:tuple
    velocity_xy:tuple
    initial_backing:tuple=()
    distance_map:DistanceMap139|None=None

    def __post_init__(self):
        if type(self.rng_words)is not tuple or len(self.rng_words)!=4 or any(type(x)is not int or not 0<=x<=f.MASK for x in self.rng_words):raise ValueError('Four explicitu32 RNGwords')
        if type(self.counter)is not int or not 0<=self.counter<=f.MASK:raise ValueError('Explicitu32 counter')
        if self.player_xyz[:2]!=ZONE_GEOMETRY139[0][:2]:raise NotImplementedError('InitialElwynn constructorcentre playerXY required')
        if type(self.initial_backing)is not tuple or len(self.initial_backing)not in(0,4):raise ValueError('Explicitcap0 orfour432B callerrecords')
        if any(len(bytes.fromhex(x))!=432 for x in self.initial_backing):raise ValueError('432B callerrecords')
        WorldPositionInput139(0,self.player_xyz,self.velocity_xy,0x41d00000,0x42100000,0x3f000000,self.rng_words,self.distance_map)


def create_four_natural_normals139(value,world):
    if not isinstance(value,NaturalNPCInput139):raise TypeError('NaturalNPCInput139 required')
    storage=[tuple(bytes.fromhex(x))for x in value.initial_backing];words=value.rng_words;counter=value.counter;packets=[];answers=[];diagnostics=[]
    for index in range(4):
        location=sample_spawn_position(WorldPositionInput139(0,value.player_xyz,value.velocity_xy,0x41d00000,0x42100000,0x3f000000,words,value.distance_map),world)
        if not storage:storage=[(None,)*432 for _ in range(4)]
        old=storage[index];concrete=bytes(0 if x is None else x for x in old)
        result=initial_normal139(InitialNPCInput139(tuple(location.rng_words),counter,tuple(location.position_bits),concrete.hex(),(0,)*index));generated=bytes.fromhex(result['record432_hex']);new=list(old)
        for offset,length in NPC_WRITTEN_RANGES:new[offset:offset+length]=generated[offset:offset+length]
        storage[index]=tuple(new);words=tuple(result['rng_words']);counter=result['counter'];packets.extend(result['packets'])
        answers.append(dict(success=result['success'],guid=result['guid'],counter=counter,rng_words=list(words),position_bits=list(location.position_bits),capacity=4,count=index+1,
            records432_cells=[list(row)for row in storage],packets=[list(row)for row in packets],HP288_bits=result['HP288_bits'],attack296_bits=result['attack296_bits']))
        diagnostics.append(dict(position_draws=location.draws,position_attempts=location.attempts,position_radius_shrinks=location.radius_shrinks,position_branch=location.branch,NPC_draws=result['draws'],not_original_internal_counters=True))
    return dict(answers=answers,model_diagnostic=diagnostics)
