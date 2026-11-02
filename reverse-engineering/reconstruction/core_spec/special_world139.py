"""Current2372 special selection, notification and first due20 Guardian source.

Complete physical40/432 storage is retained, and newtimer pointer staysNone
with a separately typed logical owner. Nondefault scaling, variants, respawn
banner and AI of the produced Guardian are explicit subsequent boundaries.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .rng import uniform_range_bits,next_u32_words
from .npc_spawn139 import BASE_SPEEDS,_values,_packed_guid
from .npc_heading139 import atan2_bits
from .special_world139_data import SPECIAL_DECLARATIONS139,ZONE136_BITS,FIRST_MILESTONE139


class PendingSpecialWorld139(NotImplementedError):pass


def word(row,offset):
    part=tuple(row[offset:offset+4])
    if len(part)!=4 or None in part:raise PendingSpecialWorld139('Actually consumed unknown cell '+str(offset))
    return struct.unpack('<I',bytes(part))[0]


def qword(row,offset):return word(row,offset)|(word(row,offset+4)<<32)
def total_key(value):
    value^=0x7fffffff if value&f.SIGN else 0
    return value-(1<<32)if value&f.SIGN else value


@dataclass(frozen=True)
class SpecialWorldState139:
    special40_storage:tuple
    special_count:int
    units432_storage:tuple
    units_count:int
    rng_words:tuple
    counter2408:int
    now_bits:int
    player_xyz:tuple
    selected392:int
    target396:int|None
    announced2565:int
    stamp2392_bits:int
    timer_owners:tuple=()
    navigation2564:int=1
    protection2576:int=0
    level1432:int=1
    difficulty387:int=0
    field1092:int=0
    zone_multiplier2516_bits:int=0x3f800000
    victory400:int=0
    endless2568:int=0
    mode2582:int=0

    def __post_init__(self):
        for rows,count,width in((self.special40_storage,self.special_count,40),(self.units432_storage,self.units_count,432)):
            if not 0<=count<=len(rows)<=512 or any(len(r)!=width or any(v is not None and(type(v)is not int or not 0<=v<=255)for v in r)for r in rows):raise ValueError('Complete physical capacity/count knownNone records')
        if self.selected392 not in(0,1)or self.navigation2564 not in(0,1)or self.announced2565 not in(0,1):raise PendingSpecialWorld139('Boolean default selection flags required')
        if self.selected392 and self.target396 is None:raise ValueError('Active selected target requires actual index')


@dataclass(frozen=True)
class GuardianTimers139:
    unit_slot:int
    guid:int
    capacity:int
    timers_bits:tuple
    header_pointer:int
    ability_pointer:int


@dataclass(frozen=True)
class SpecialWorldResult139:
    state:SpecialWorldState139
    packets:tuple
    timers:tuple
    creates:tuple
    rng_draws:int


def from_opening_special139(opening):
    rows=tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells'])
    #Additional1600 producers are source-bound by the private tracer.396is
    #unwritten and only read when392Some, so it remainsNone at construction.
    return SpecialWorldState139(opening.special.storage,opening.special.count,
        rows,4,tuple(opening.rng_words),opening.counter,0,
        tuple(opening.constructor.player_xyz),0,None,0,0)


def guardian_scalars139(state,definition):
    if(state.difficulty387,state.field1092,state.zone_multiplier2516_bits,state.victory400,state.endless2568,state.mode2582)!=(0,0,0x3f800000,0,0,0):raise PendingSpecialWorld139('Nondefault16381/42922 scaling source not yet admitted')
    t=f.div(state.now_bits,0x42700000)
    if not 0<=f.to_float(t)<=3:raise PendingSpecialWorld139('Beyond first current boss milestone interpolation')
    first,hp=FIRST_MILESTONE139
    milestone=f.mul(f.add(f.div(f.mul(t,0x3ecccccd),first),0x3f19999a),hp)
    poly=f.add(f.add(f.mul(t,0x3df5c28f),0x3f800000),f.mul(t,f.mul(t,0x3c1374bc)))
    a=f.mul(f.mul(f.mul(ZONE136_BITS,poly),word(definition,40)),0x40200000)
    b=f.mul(ZONE136_BITS,f.mul(milestone,0x3f19999a))
    hp=f.mul(a if f.to_float(a)>f.to_float(b)else b,0x40400000)
    #All remaining currentdefault factors are exactly1 but retain every
    #ordered f32 multiplication rather than algebraically canceling them.
    for factor in(0x3f800000,0x3f800000,0x3f800000,0x3f800000):hp=f.mul(hp,factor)
    poly=f.add(f.add(f.mul(t,0x3da3d70a),0x3f800000),f.mul(t,f.mul(t,0x3b83126f)))
    attack=f.mul(word(definition,44),f.mul(poly,sqrt_bits(ZONE136_BITS)))
    attack=f.mul(attack,0x3fb33333)
    for _ in range(3):attack=f.mul(attack,0x3f800000)
    return hp,attack


def _guardian(state,definition_index,special_slot,row,storage,count,words,counter):
    try:decl=next(d for d in SPECIAL_DECLARATIONS139 if d[0]==definition_index)
    except StopIteration:raise PendingSpecialWorld139('Unbound Guardian declaration')from None
    _,pointer,rawhex,name,header,headerhex,abilities,records=decl;definition=bytes.fromhex(rawhex)
    if word(bytes.fromhex(headerhex),12):raise PendingSpecialWorld139('Guardian random ability variants')
    xyz=tuple(word(row,16+4*j)for j in range(3));hp,attack=guardian_scalars139(state,definition);scale=f.mul(word(definition,32),0x3faccccd)
    counter=(counter+1)&f.MASK;entry=word(definition,24);guid=0xf130000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
    fields={0:guid&f.MASK,1:guid>>32,2:9,3:entry,4:scale,16:0,17:0,22:math.ceil(f.to_float(hp)),28:math.ceil(f.to_float(hp)),34:min(state.level1432+3,63),35:14,36:256,46:0,126:2000,127:2000,129:f.mul(scale,0x3f000000),130:f.mul(scale,0x3fc00000),131:word(definition,28),132:word(definition,28),134:0x40a00000,135:0x41200000,145:0x3f800000}
    heading=atan2_bits(f.sub(state.player_xyz[1],xyz[1]),f.sub(state.player_xyz[0],xyz[0]))
    payload=struct.pack('<IB',1,0)+bytes([3])+_packed_guid(guid)+bytes([3,112])+struct.pack('<2I',0,0)+struct.pack('<4I',*xyz,heading)+struct.pack('<I',0)+struct.pack('<6I',*BASE_SPEEDS)+struct.pack('<I',1)+_values(fields)
    angle=uniform_range_bits(words,0,0x40c90fdb);words=angle.state;draws=angle.draws
    for _ in range(100000):
        output,words=next_u32_words(words);draws+=1
        if not output&0x02000000:break
    else:raise PendingSpecialWorld139('Bounded variant draw watchdog')
    timers=tuple(f.mul(word(bytes.fromhex(record),40),0x3f000000)for record in records)
    if count==len(storage):storage.extend([(None,)*432]*(max(4,2*len(storage))-len(storage)))
    cells=list(storage[count]);raw=bytearray(432)
    def put(o,v):struct.pack_into('<I',raw,o,v)
    for o in(40,244):put(o,f.MASK)
    for o,v in((64,len(records)),(72,len(records)),(76,abilities),(80,len(records)),(84,abilities),(88,len(records)),(92,special_slot),(96,header),(280,0),(284,pointer),(288,hp),(292,hp),(296,attack),(300,word(definition,52)),(304,word(definition,48)),(308,f.add(f.mul(scale,0x3f99999a),0x400ccccd)),(312,scale),(340,state.now_bits),(344,0),(348,state.now_bits),(352,f.mul(word(definition,48),0x3f000000)),(404,f.add(angle.bits,0))):put(o,v)
    struct.pack_into('<Q',raw,112,guid);struct.pack_into('<Q',raw,236,4)
    for o in(316,328):struct.pack_into('<3I',raw,o,*xyz)
    raw[424]=definition[68]
    for offset,length in((0,4),(8,4),(16,4),(40,4),(64,4),(72,37),(112,136),(280,147)):cells[offset:offset+length]=raw[offset:offset+length]
    cells[68:72]=(None,)*4;storage[count]=tuple(cells)
    return tuple(words),counter,guid,(169,None,payload.hex()),GuardianTimers139(count,guid,len(records),timers,header,abilities),draws


def update_special_world139(state):
    if not isinstance(state,SpecialWorldState139):raise TypeError('Typed special owner required')
    if f.is_nan(state.now_bits)or f.is_inf(state.now_bits):raise PendingSpecialWorld139('Finite explicit Game clock')
    if state.protection2576 or not state.special_count:return SpecialWorldResult139(state,(),(),(),0)
    rows=[list(r)for r in state.special40_storage];units=list(state.units432_storage);count=state.units_count;words=state.rng_words;counter=state.counter2408;packets=[];timers=[];creates=[];draws=0;selected=state.selected392
    for index,row in enumerate(rows[:state.special_count]):
        if qword(row,0)or not f.to_float(state.now_bits)>=f.to_float(word(row,32)):continue
        if f.to_float(state.now_bits)>21:raise PendingSpecialWorld139('2372 localized150 respawn banner beyond firstdue21s requires its own source')
        words,counter,guid,packet,owner,n=_guardian(state,word(row,28),index,row,units,count,words,counter)
        count+=1;packets.append(packet);timers.append(owner);creates.append((index,guid,word(row,28)));draws+=n
        row[0:16]=struct.pack('<QQ',1,guid);selected=0
    active=[i for i,row in enumerate(rows[:state.special_count])if qword(row,0)]
    def distance(i):
        row=rows[i];dx=f.sub(word(row,16),state.player_xyz[0]);dy=f.sub(word(row,20),state.player_xyz[1])
        return total_key(sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy))))
    target=min(active,key=distance)if active else min(range(state.special_count),key=lambda i:total_key(word(rows[i],32)))
    final=replace(state,special40_storage=tuple(tuple(r)for r in rows),units432_storage=tuple(units),units_count=count,rng_words=tuple(words),counter2408=counter,selected392=selected,timer_owners=state.timer_owners+tuple(timers))
    if not state.navigation2564:
        final=replace(final,selected392=1,target396=target,announced2565=0)
        if state.announced2565:packets.append((548,32,(struct.pack('<5I',99,*state.player_xyz[:2],6,0)+b'\0').hex()))
    elif not(selected and state.target396==target and state.announced2565&1 and not f.to_float(f.sub(state.now_bits,state.stamp2392_bits))>300):
        row=rows[target];definition_index=word(row,28);name=next((d[3]for d in SPECIAL_DECLARATIONS139 if d[0]==definition_index),None)
        if name is None:raise PendingSpecialWorld139('Unbound notification target')
        text=name+(' (Guardian)'if qword(row,0)else"'s lair (empty)");payload=struct.pack('<5I',99,word(row,16),word(row,20),6,0)+text.encode()+b'\0';cap=32
        length=20+len(text.encode())
        if length>cap:cap=max(2*cap,length)
        if length==cap:cap*=2
        packets.append((548,cap,payload.hex()));final=replace(final,selected392=1,target396=target,announced2565=1,stamp2392_bits=state.now_bits)
    return SpecialWorldResult139(final,tuple(packets),tuple(timers),tuple(creates),draws)
