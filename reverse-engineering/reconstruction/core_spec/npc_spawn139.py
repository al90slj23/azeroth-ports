"""Narrow1395719 initial Elwynn normal NPC with explicit Some(position).

Full139 source is the rule authority. Earlier ordinary-spawn work supplies
algorithm expressions only; no old model, original or observation is imported.
Only time0/mode0/difficulty0/member1/definition0/playerGUID0/level1 is admitted.
Destination432 can be caller backing or a freshly reserved row with unknown
inactive bytes. The latter keeps None and never uses observed padding.
World sampling and the actual full1108 composition remain separate.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .rng import uniform_range_bits
from .initial_state139_data import ZONE_ENTRIES
from .npc_heading139 import atan2_bits

DEFINITION_POINTER=5830904
DEFINITION72_HEX='0000000000000000000000000000000050f858000d000000580200001a0000006666663f070000000000c04100004040cdcccc3f0000a040010000000000803f0000000000000000'
ZONE_SCALING_BITS=1062333317
BASE_SPEEDS=(1075838976,1088421888,1083179008,1083645041,1075838976,1078530011)
NPC_WRITTEN_RANGES=((0,4),(8,4),(16,4),(40,4),(64,4),(112,136),(280,147))


def _u(x,bits=32):
    if type(x)is not int or not 0<=x<1<<bits:raise ValueError('Explicit unsigned input required')
    return x


@dataclass(frozen=True)
class InitialNPCInput139:
    rng_words:tuple
    counter:int
    position_bits:tuple
    initial_record_hex:str
    existing_states:tuple=()

    def __post_init__(self):
        if type(self.rng_words)is not tuple or len(self.rng_words)!=4:raise ValueError('Four explicit RNG words')
        for x in(self.counter,*self.rng_words,*self.position_bits):_u(x)
        if len(self.position_bits)!=3 or any(f.is_nan(x)or f.is_inf(x)for x in self.position_bits):raise ValueError('Three finite explicit position words')
        if type(self.existing_states)is not tuple or len(self.existing_states)>3 or any(type(x)is not int or x!=0 for x in self.existing_states):raise NotImplementedError('InitialfourNPC: atmost3 explicitly active state0 records')
        if len(bytes.fromhex(self.initial_record_hex))!=432:raise ValueError('Full explicit432B destination backing')


def _packed_guid(guid):
    raw=guid.to_bytes(8,'little');return bytes([sum(1<<j for j,x in enumerate(raw)if x)])+bytes(x for x in raw if x)


def _values(fields):
    words=max(fields)//32+1;masks=[0]*words
    for key in fields:masks[key//32]|=1<<(key%32)
    return bytes([words])+struct.pack('<'+'I'*words,*masks)+b''.join(struct.pack('<I',fields[k])for k in sorted(fields))


def initial_normal139(value):
    if not isinstance(value,InitialNPCInput139):raise TypeError('InitialNPCInput139 required')
    desc=struct.unpack('<18I',bytes.fromhex(DEFINITION72_HEX));entry,display,scale,hpbase,attackbase,speed,field52=desc[6],desc[7],desc[8],desc[10],desc[11],desc[12],desc[13]
    #97427(0,zone136*1) is exactlyzone136, then5719's ordered factors.
    hp=f.mul(f.mul(0x409e6666,hpbase),ZONE_SCALING_BITS)
    attack=f.mul(f.mul(0x3fa00000,attackbase),sqrt_bits(ZONE_SCALING_BITS))
    counter=(value.counter+1)&f.MASK;guid=0xf130000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
    yaw=uniform_range_bits(value.rng_words,0,0x40c90fdb);jitter=uniform_range_bits(yaw.state,0,0x3e99999a)
    raw=bytearray.fromhex(value.initial_record_hex)
    def u(o,x):struct.pack_into('<I',raw,o,x)
    def q(o,x):struct.pack_into('<Q',raw,o,x)
    for o in(0,8,16,344):u(o,0)
    for o in(40,64,244):u(o,f.MASK)
    q(112,guid);raw[120:236]=bytes(116);q(236,4)
    for o,x in((280,0),(284,DEFINITION_POINTER),(288,hp),(292,hp),(296,attack),(300,f.mul(field52,0x3f866666)),(304,speed),
        (308,f.add(f.mul(scale,0x3f99999a),0x400ccccd)),(312,scale),(340,0),(348,f.add(0,f.add(jitter.bits,0))),(352,f.mul(speed,0x3f000000)),(404,f.add(yaw.bits,0))):u(o,x)
    for o in(316,328):struct.pack_into('<3I',raw,o,*value.position_bits)
    raw[356:404]=bytes(48);q(408,0);q(416,0);raw[424:427]=bytes(3)
    #1586 fields: HP ceil is positivefinite, targetGUID0, level1, normaltype.
    import math
    hpceil=math.ceil(f.to_float(hp));fields={0:guid&f.MASK,1:guid>>32,2:9,3:entry,4:scale,16:0,17:0,22:hpceil,28:hpceil,34:1,35:14,36:256,46:0,
        126:2000,127:2000,129:f.mul(scale,0x3f000000),130:f.mul(scale,0x3fc00000),131:display,132:display,134:0x40a00000,135:0x41200000,145:0x3f800000}
    heading=atan2_bits(f.sub(ZONE_ENTRIES[0][2],value.position_bits[1]),f.sub(ZONE_ENTRIES[0][1],value.position_bits[0]))
    payload=(struct.pack('<IB',1,0)+bytes([3])+_packed_guid(guid)+bytes([3,112])+struct.pack('<2I',0,0)+struct.pack('<4I',*value.position_bits,heading)+struct.pack('<I',0)+struct.pack('<6I',*BASE_SPEEDS)+struct.pack('<I',1)+_values(fields))
    return dict(success=True,guid=str(guid),counter=counter,rng_words=list(jitter.state),draws=yaw.draws+jitter.draws,record432_hex=raw.hex(),HP288_bits=hp,attack296_bits=attack,packets=[[169,payload.hex()]])


def initial_four_normals139(rng_words,counter,positions,initial_backing):
    """Four real5719 transitions; emptyreserve gives unknown inactive bytes.

    initial_backing is either () (declared cap0) or four explicit432B records.
    Placeholder zeros only evaluate functions that write their own scalar
    fields; no placeholder escapes into a retained/compared inactive cell.
    """
    if type(positions)is not tuple or len(positions)!=4:raise ValueError('Four explicit SomeXYZ positions')
    if type(initial_backing)is not tuple or len(initial_backing)not in(0,4):raise ValueError('Explicit emptyor4row backing')
    storage=[tuple(bytes.fromhex(x))for x in initial_backing]
    if any(len(x)!=432 for x in storage):raise ValueError('Four432B rows')
    words=tuple(rng_words);packets=[];answers=[];total_draws=0
    for index,position in enumerate(positions):
        if not storage:storage=[(None,)*432 for _ in range(4)]
        old=storage[index];concrete=bytes(0 if x is None else x for x in old)
        result=initial_normal139(InitialNPCInput139(words,counter,tuple(position),concrete.hex(),(0,)*index));generated=bytes.fromhex(result['record432_hex']);new=list(old)
        for offset,length in NPC_WRITTEN_RANGES:new[offset:offset+length]=generated[offset:offset+length]
        storage[index]=tuple(new);counter=result['counter'];words=tuple(result['rng_words']);packets.extend(result['packets']);total_draws+=result['draws']
        answers.append(dict(success=result['success'],guid=result['guid'],counter=counter,rng_words=list(words),capacity=4,count=index+1,
            records432_cells=[list(row)for row in storage],packets=[list(row)for row in packets],HP288_bits=result['HP288_bits'],attack296_bits=result['attack296_bits']))
    return dict(answers=answers,model_rng_draws=total_draws)
