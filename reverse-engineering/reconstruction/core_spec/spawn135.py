"""Independent135 weighted enemy choice and full ordinary424B spawn projection.

Explicit positions and owner lookup results are resolved inputs. World sampling,
object/packet production and complete AI/scheduler producers remain separate;
the production model reads no original runtime, binary or evidence.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .enemy_scaling import elite_growth_bits,normal_growth_bits
from .progression134 import round_85718_bits as rounded_bits,trunc_sat_u32
from .rng import uniform_range_bits
from .spawn_math135 import endless_power
from .spawn135_data import ZONES,NORMALS,NORMAL_FIELDS,DIFFICULTY


def definition(zone,index):
    rows=NORMALS[zone]
    return dict(zip(NORMAL_FIELDS,rows[min(index,len(rows)-1)]))


def max_numeric(a,b):
    x=b if f.is_nan(a) else a;y=x if f.is_nan(b) else b
    return x if f.to_float(x)>f.to_float(y) else y


def min_numeric(a,b):
    x=b if f.is_nan(a) else a;y=x if f.is_nan(b) else b
    return x if f.to_float(x)<f.to_float(y) else y


def eligible_normals(zone,minutes_bits):
    return tuple(i for i,row in enumerate(NORMALS[zone])
                 if row[-1]==0 and f.to_float(row[-2])<=f.to_float(minutes_bits))


@dataclass(frozen=True)
class SpawnChoice:
    index:int
    rng_words:tuple
    draws:int
    weight_bits:tuple
    total_bits:int


def choose_spawn(zone,candidates,minutes_bits,rng_words):
    if not candidates:raise ValueError('Empty candidate panic path is not a successful choice')
    weights=[]
    for index in candidates:
        if not 0<=index<len(NORMALS[zone]):raise ValueError('Definition index outside actual table')
        d=definition(zone,index)
        age=max_numeric(f.sub(minutes_bits,d['unlock_bits']),0)
        weight=f.div(min_numeric(0x40800000,f.add(f.mul(age,0x3f000000),0x3f800000)),d['cost_bits'])
        weights.append(weight)
    total=f.SIGN
    for weight in weights:total=f.add(total,weight)
    drawn=uniform_range_bits(rng_words,0,max_numeric(0x3a83126f,total))
    residual=drawn.bits;selected=candidates[0]
    for index,weight in zip(candidates,weights):
        if f.to_float(residual)<f.to_float(weight):selected=index;break
        residual=f.sub(residual,weight)
    return SpawnChoice(selected,drawn.state,drawn.draws,tuple(weights),total)


@dataclass(frozen=True)
class SpawnInput:
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
    existing_states:tuple
    rng_words:tuple
    counter:int
    position_bits:tuple
    resolved_owner:int
    initial_slot_hex:str


@dataclass(frozen=True)
class SpawnResult:
    success:bool
    guid:int
    counter:int
    rng_words:tuple
    draws:int
    record_hex:str|None
    hp_bits:int|None
    attack_bits:int|None
    cap:int


def spawn_normal(state:SpawnInput):
    if not 0<=state.zone<12 or not 0<=state.definition_index<=f.MASK:
        raise ValueError('Invalid explicit zone/index')
    if len(state.position_bits)!=3 or len(bytes.fromhex(state.initial_slot_hex))!=424:
        raise ValueError('Explicit xyz and full existing destination slot are required')
    group=f.mul(0x3f333333 if state.zone<3 else 0x3f800000,f.from_u32((state.members-1)&f.MASK))
    cap=(trunc_sat_u32(rounded_bits(f.mul(f.add(f.mul(group,0x3e9fbe77),0x3f800000),0x42480000)))
         if state.mode==1 else 50)
    count=0
    for value in state.existing_states:count=(count+(value^1))&f.MASK
    if not cap>count:return SpawnResult(False,0,state.counter,state.rng_words,0,None,None,None,cap)
    d=definition(state.zone,state.definition_index)
    t=f.div(state.now_bits,0x42700000)
    exponent=0
    if state.victory_field400==1 and state.endless_flag&1:
        exponent=max_numeric(f.div(f.sub(state.now_bits,state.endless_start_bits),0x42700000),0)
    scale=f.mul(ZONES[state.zone][1],state.zone_multiplier_bits)
    curve=(elite_growth_bits if d['elite'] else normal_growth_bits)(t,scale)
    hp=f.mul(f.mul(0x4099999a if d['elite'] else 0x409e6666,d['hp_bits']),curve)
    q=f.div(t,0x41a00000)
    q=0 if f.to_float(q)<0 else q;q=0x3f800000 if f.to_float(q)>1 else q
    hp=f.mul(hp,f.add(f.mul(q,f.mul(q,ZONES[state.zone][2])),0x3f800000))
    dh,da=DIFFICULTY[state.difficulty-1] if 1<=state.difficulty<=5 else (0x3f800000,0x3f800000)
    modehp=f.mul(f.add(f.mul(group,0x3f3851ec),0x3f800000),0x3f4ccccd) if state.mode==1 else 0x3f800000
    hp=f.mul(f.mul(f.mul(endless_power(0x3f9c28f6,exponent),hp),dh),modehp)
    poly=f.add(f.mul(t,0x3d8f5c29),0x3f800000)
    poly=f.add(poly,f.mul(t,f.mul(t,0x3c75c28f)))
    poly=f.add(poly,f.mul(t,f.mul(t,f.mul(t,0x3951b717))))
    attack=f.mul(f.mul(0x3f800000 if d['elite'] else 0x3fa00000,d['attack_bits']),f.mul(poly,sqrt_bits(scale)))
    attack=f.mul(f.mul(endless_power(0x3f8c49ba,exponent),attack),da)
    counter=(state.counter+1)&f.MASK
    guid=0xf130000000000000|((d['entry']&0xffffff)<<24)|(counter&0xffffff)
    angle=uniform_range_bits(state.rng_words,0,0x40c90fdb)
    jitter=uniform_range_bits(angle.state,0,0x3e99999a)
    raw=bytearray.fromhex(state.initial_slot_hex)
    def u(offset,value):struct.pack_into('<I',raw,offset,value&f.MASK)
    def qword(offset,value):struct.pack_into('<Q',raw,offset,value&0xffffffffffffffff)
    for offset in (0,8,16,344):u(offset,0)
    for offset in (40,64,244):u(offset,f.MASK)
    qword(112,guid);raw[120:236]=bytes(116);qword(236,4)
    for offset,value in ((280,state.resolved_owner),(284,d['pointer']),(288,hp),(292,hp),(296,attack),
        (300,f.mul(d['field52_bits'],0x3f866666)),(304,d['field48_bits']),
        (308,f.add(f.mul(d['scale_bits'],0x3f99999a),0x400ccccd)),(312,d['scale_bits']),
        (340,state.now_bits),(348,f.add(state.now_bits,f.add(jitter.bits,0))),
        (352,f.mul(d['field48_bits'],0x3f000000)),(396,f.add(angle.bits,0))):u(offset,value)
    for offset in (316,328):
        for i,value in enumerate(state.position_bits):u(offset+4*i,value)
    raw[356:396]=bytes(40);raw[400:416]=bytes(16);raw[416]=d['elite'];raw[417:419]=bytes(2)
    return SpawnResult(True,guid,counter,jitter.state,angle.draws+jitter.draws,raw.hex(),hp,attack,cap)
