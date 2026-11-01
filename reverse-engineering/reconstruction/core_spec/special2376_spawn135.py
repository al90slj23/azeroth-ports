"""Fixed135 Elwynn due-special NPC producer, complete first-expiry slice.

Explicit record/capacity/locale inputs only; no original/asset/snapshot IO.
Elwynn default9/10/11 definitions and their no-variant skill lists are retained.
The >21s localized respawn150 branch remains pending. Newly owned timer pointer
words are None in physical records and have explicit semantic payloads below;
they are never forged zero handles or copied from original output.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .rng import uniform_range_bits,next_u32_words
from .spawn135 import definition,max_numeric
from .spawn135_data import ZONES,DIFFICULTY
from .spawn_boss135_data import BOSSES
from .spawn_math135 import endless_power
from .spawn_heading135 import atan2_bits
from .opening_entities135 import BASE_SPEEDS,LogicalCreate135,unit_create169
from .opening_npc_pickups135 import OpeningVector135,npc_create_fields,_reserve_row
from .record_cells135 import cells135,u32,u64,put_u32,put_u64,encode_row
from .special2376_135 import SpecialState2376_135,UnknownSpecial2376_135,tick_special2376_135
from .special2376_notify135 import tick_special2376_notify135
from .special2376_spawn135_data import (ELWYNN_SPECIAL_SKILLS135,
    special_ability_records135,special_header135)


@dataclass(frozen=True)
class SpecialSpawnInput135:
    special:SpecialState2376_135
    units:OpeningVector135
    rng_words:tuple
    counter:int
    player_xyz_bits:tuple
    player_guid:int
    level1432:int
    zone_multiplier_bits:int
    difficulty:int
    mode:int
    members:int|None
    field1092:int
    victory400:int
    endless_flag2568:int
    endless_start404_bits:int|None
    zone:int=0


@dataclass(frozen=True)
class SpecialCooldowns135:
    unit_index:int
    guid:int
    capacity:int
    timers_bits:tuple
    ability_pointer:int
    header_pointer:int
    ability_records44_hex:tuple
    header28_hex:str
    physical_pointer_offset:int=68
    physical_pointer_known:bool=False


@dataclass(frozen=True)
class SpecialSpawnResult135:
    special:SpecialState2376_135
    units:OpeningVector135
    rng_words:tuple
    counter:int
    rng_draws:int
    creates:tuple
    cooldowns:tuple
    packets:tuple
    status:str


def _finite(word):
    if type(word)is not int or not 0<=word<=f.MASK or word&0x7fffffff>=f.INF:
        raise ValueError('Finite explicit binary32 input required')


def special_scalars135(value,index):
    """Ordered16341/42327 numeric rules, admitted finite fixed-Elwynn inputs.

    First expiry samples validate the before-first-milestone branch. Later
    interpolation is implemented for explicit reuse but not promoted to a
    validated independent full16341 domain by this producer's evidence.
    """
    d=definition(value.zone,index);t=f.div(value.special.now_bits,0x42700000)
    milestones=tuple((row[5],row[6])for row in BOSSES[value.zone]if row[9]!=1)
    milestone=0
    if len(milestones)==1:milestone=milestones[0][1]
    elif milestones:
        first,hp=milestones[0]
        if f.to_float(t)<=f.to_float(first):
            milestone=f.mul(f.add(f.div(f.mul(t,0x3ecccccd),max_numeric(first,0x3a83126f)),0x3f19999a),hp)
        else:
            right=next((i for i,(minute,_)in enumerate(milestones)if f.to_float(minute)>=f.to_float(t)),len(milestones)-1)
            right=max(right,1);left=right-1;lm,lh=milestones[left];rm,rh=milestones[right]
            milestone=f.add(lh,f.div(f.mul(f.sub(t,lm),f.sub(rh,lh)),max_numeric(f.sub(rm,lm),0x3a83126f)))
    exponent=0
    if value.victory400==1 and value.endless_flag2568&1:
        exponent=max_numeric(f.div(f.sub(value.special.now_bits,value.endless_start404_bits),0x42700000),0)
    scale=f.mul(ZONES[value.zone][1],value.zone_multiplier_bits)
    poly=f.add(f.add(f.mul(t,0x3df5c28f),0x3f800000),f.mul(t,f.mul(t,0x3c1374bc)))
    a=f.mul(f.mul(f.mul(scale,poly),d['hp_bits']),0x40200000)
    b=f.mul(scale,f.mul(milestone,0x3f19999a))
    dh,da=DIFFICULTY[value.difficulty-1]if 1<=value.difficulty<=5 else(0x3f800000,0x3f800000)
    hp=f.mul(f.mul(max_numeric(a,b),0x40400000),endless_power(0x3f9c28f6,exponent))
    #WASM ``a b cond select`` chooses a on true: >1 uses .35, else .25.
    hp=f.mul(hp,f.add(f.mul(0x3eb33333 if value.difficulty>1 else 0x3e800000,f.from_u32(value.field1092)),0x3f800000))
    hp=f.mul(hp,dh)
    group=0x3f800000
    if value.mode==1:
        group=f.mul(f.add(f.mul(f.mul(0x3f333333 if value.zone<3 else 0x3f800000,
            f.from_u32((value.members-1)&f.MASK)),0x3f851eb8),0x3f800000),0x3f4ccccd)
    hp=f.mul(hp,group)
    poly=f.add(f.add(f.mul(t,0x3da3d70a),0x3f800000),f.mul(t,f.mul(t,0x3b83126f)))
    attack=f.mul(d['attack_bits'],f.mul(poly,sqrt_bits(scale)))
    attack=f.mul(f.mul(attack,0x3fb33333),endless_power(0x3f8c49ba,exponent))
    attack=f.mul(attack,f.add(f.mul(0x3d8f5c29 if value.difficulty>1 else 0x3d4ccccd,f.from_u32(value.field1092)),0x3f800000))
    return hp,f.mul(attack,da)


def tick_special_spawn135(value,*,locale=None):
    if not isinstance(value,SpecialSpawnInput135)or value.zone!=0 or value.units.stride!=424:
        raise UnknownSpecial2376_135('Fixed135 first-expiry Elwynn input required')
    if type(value.player_xyz_bits)is not tuple or len(value.player_xyz_bits)!=3 or type(value.rng_words)is not tuple or len(value.rng_words)!=4:
        raise ValueError('Explicit XYZ and four RNG words required')
    for word in (*value.player_xyz_bits,value.zone_multiplier_bits,value.special.now_bits):_finite(word)
    #1560 leaves404 unwritten. The producer reads it only in this endless
    #branch; absence must not be replaced by an invented zero timestamp.
    if value.victory400==1 and value.endless_flag2568&1:
        if value.endless_start404_bits is None:
            raise UnknownSpecial2376_135('Endless scaling requires its actual404 producer timestamp')
        _finite(value.endless_start404_bits)
    if not 0<=f.to_float(value.special.now_bits):raise ValueError('Admitted nonnegative game clock required')
    for n,bits in ((value.counter,32),(value.player_guid,64),(value.level1432,32),(value.difficulty,8),
            (value.mode,8),(value.field1092,32),(value.victory400,32),(value.endless_flag2568,8)):
        if type(n)is not int or not 0<=n<1<<bits:raise ValueError('Explicit unsigned scalar required')
    if value.mode==1:
        if value.members is None:raise UnknownSpecial2376_135('Party scaling requires actual G2540 member producer')
        if type(value.members)is not int or not 0<=value.members<=f.MASK:raise ValueError('Explicit member u32 required')
    state=value.special;rows=[cells135(row,40)for row in state.storage];vector=value.units
    words=tuple(value.rng_words);counter=value.counter;creates=[];cooldowns=[];packets=[];draws=0
    if not state.protection2576:
        for i,row in enumerate(rows[:state.count]):
            if u64(row,0,'special2376.marker')or not f.to_float(state.now_bits)>=f.to_float(u32(row,32,'special2376.deadline')):continue
            if f.to_float(state.now_bits)>21:
                raise UnknownSpecial2376_135('Due clock>21 requires localized150 respawn banner continuation')
            index=u32(row,28,'special2376.definition')
            if index not in (9,10,11):raise UnknownSpecial2376_135('Only actual Elwynn special definitions9/10/11 restored')
            d=definition(0,index);hp,attack=special_scalars135(value,index)
            counter=(counter+1)&f.MASK;guid=0xf130000000000000|((d['entry']&0xffffff)<<24)|(counter&0xffffff)
            xyz=tuple(u32(row,16+4*j,'special2376.xyz')for j in range(3))
            for word in xyz:_finite(word)
            scale=f.mul(d['scale_bits'],0x3faccccd)
            fields=npc_create_fields(guid,d['entry'],d['display'],scale,hp,1,value.player_guid,value.level1432)
            heading=atan2_bits(f.sub(value.player_xyz_bits[1],xyz[1]),f.sub(value.player_xyz_bits[0],xyz[0]))
            payload=unit_create169(guid,xyz,heading,BASE_SPEEDS,fields)
            creates.append(LogicalCreate135(guid,3,xyz,heading,fields,payload.hex()));packets.append((169,payload.hex()))
            angle=uniform_range_bits(words,0,0x40c90fdb);words=angle.state;draws+=angle.draws
            for _ in range(100000):
                output,words=next_u32_words(words);draws+=1
                if not output&0x02000000:break
            else:raise RuntimeError('Independent special variant RNG watchdog')
            header,abilities,source_clocks=ELWYNN_SPECIAL_SKILLS135[d['entry']]
            timers=tuple(f.mul(x,0x3f000000)for x in source_clocks)
            vector=_reserve_row(vector);slot=cells135(vector.storage[vector.count],424)
            def w(offset,word):put_u32(slot,offset,word)
            for offset in (0,8,16,344):w(offset,0)
            for offset in (40,244):w(offset,f.MASK)
            for offset,word in ((64,3),(72,3),(76,abilities),(80,3),(84,abilities),(88,3),(92,i),(96,header),(100,0),(104,0)):w(offset,word)
            slot[68:72]=[None]*4;slot[108]=0;put_u64(slot,112,guid);slot[120:236]=bytes(116);put_u64(slot,236,4)
            for offset,word in ((280,0),(284,d['pointer']),(288,hp),(292,hp),(296,attack),(300,d['field52_bits']),
                    (304,d['field48_bits']),(308,f.add(f.mul(scale,0x3f99999a),0x400ccccd)),(312,scale),
                    (340,state.now_bits),(348,state.now_bits),(352,f.mul(d['field48_bits'],0x3f000000)),(396,f.add(angle.bits,0))):w(offset,word)
            for offset in (316,328):
                for j,word in enumerate(xyz):w(offset+4*j,word)
            slot[356:396]=bytes(40);slot[400:416]=bytes(16);slot[416]=d['elite'];slot[417:419]=bytes(2)
            storage=list(vector.storage);storage[vector.count]=tuple(slot)
            cooldowns.append(SpecialCooldowns135(vector.count,guid,3,timers,abilities,header,
                special_ability_records135(abilities),special_header135(header)))
            vector=OpeningVector135(424,tuple(storage),vector.count+1)
            put_u64(row,0,1);put_u64(row,8,guid);state=replace(state,selected392=0)
    state=replace(state,storage=tuple(encode_row(row)for row in rows))
    try:follow=tick_special2376_135(state)
    except UnknownSpecial2376_135 as error:
        if not str(error).startswith('Selected-target localized548'):raise
        if locale is None:raise UnknownSpecial2376_135('Selected-target localized548 requires explicit initialized names')
        follow=tick_special2376_notify135(state,value.zone,locale)
    packets.extend((opcode,payload)for opcode,capacity,payload in follow.packets)
    return SpecialSpawnResult135(follow.state,vector,words,counter,draws,tuple(creates),tuple(cooldowns),tuple(packets),
        'special_first_expiry_numeric_create_projection')
