"""Current916 rawtag7 Charge via normalized4, selector3, br_table depth23.

The genuine default100 record contributes its spellID. The branch uses fixed
one-second cast/effect, twice current attack, clamped navigation geometry and a
56B deferred action. This produces queues for later stages, never same925 hits.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .death139 import word139,guid139,position3_139
from .npc_heading139 import atan2_bits
from .enemy_ai139 import _trig139
from .ai_world135 import segment_fraction135
from .frame_systems139 import ScheduledSpellVector139
from .special_world139_data import SPECIAL_DECLARATIONS139


class PendingGuardianCharge139(NotImplementedError):pass


@dataclass(frozen=True)
class QueuedGuardianSkill139:
    unit_index:int
    ability_index:int
    ability_pointer:int
    raw40:bytes

    def __post_init__(self):
        if type(self.raw40)is not bytes or len(self.raw40)!=40:raise ValueError('Actual925copies exactfirst40of44Bability into its action')
        rows=next((d[-1]for d in SPECIAL_DECLARATIONS139 if d[-2]==self.ability_pointer),None)
        if rows is None or not 0<=self.ability_index<len(rows)or bytes.fromhex(rows[self.ability_index])[:40]!=self.raw40:raise PendingGuardianCharge139('Only producer-bound currentGuardian ability source')


@dataclass(frozen=True)
class EffectVector120139:
    storage:tuple
    count:int
    def __post_init__(self):_validate_vector(self.storage,self.count,120)


@dataclass(frozen=True)
class DeferredGuardianVector56139:
    storage:tuple
    count:int
    def __post_init__(self):_validate_vector(self.storage,self.count,56)


def _validate_vector(storage,count,width):
    if type(storage)is not tuple or not 0<=count<=len(storage)<=512 or any(type(r)is not tuple or len(r)!=width or any(v is not None and(type(v)is not int or not 0<=v<=255)for v in r)for r in storage):raise ValueError('Complete knownNone physical backing required')


@dataclass(frozen=True)
class GuardianChargeState139:
    records432:tuple
    now_bits:int
    player_xyz:tuple
    effects:EffectVector120139
    deferred:DeferredGuardianVector56139
    scheduled:ScheduledSpellVector139
    counter2356:int
    sequence2412:int
    difficulty387:int=0


@dataclass(frozen=True)
class GuardianChargeResult139:
    state:GuardianChargeState139
    packets:tuple
    accepted:bool
    queued_effect_index:int|None
    queued_deferred_index:int|None


def _packed(guid):
    raw=guid.to_bytes(8,'little');return bytes([sum(1<<i for i,b in enumerate(raw)if b)])+bytes(b for b in raw if b)
def _put(row,o,value):row[o:o+4]=struct.pack('<I',value)
def _max(a,b):return a if f.to_float(a)>f.to_float(b)else b
def _min(a,b):return a if f.to_float(a)<f.to_float(b)else b
def _distance(a,b):
    x,y=f.sub(a[0],b[0]),f.sub(a[1],b[1]);return sqrt_bits(f.add(f.mul(x,x),f.mul(y,y)))
def _project(world,xyz,*,fallback_to_current):
    result=world.height(*xyz[:2])
    if result.found:return(*xyz[:2],result.value_bits)
    if world.primary is not None:raise PendingGuardianCharge139('Currentcanonical no-primary world required onheightmiss')
    return(*xyz[:2],xyz[2]if fallback_to_current else world.fallback_height_bits)
def _reserve(storage,count,width):
    rows=list(storage)
    if count==len(rows):rows.extend([(None,)*width]*(max(4,2*len(rows))-len(rows)))
    return rows,list(rows[count])
def _navigation_stop(world,start,end):
    if world.nav is None:return end
    fraction=segment_fraction135(world.nav,start[:2],end[:2])
    if f.to_float(fraction)>=1:return end
    t=_max(f.sub(fraction,f.div(0x3f000000,_max(_distance(start,end),0x3f000000))),0)
    return tuple(f.add(a,f.mul(f.sub(b,a),t))for a,b in zip(start,end))


def cast_guardian_charge139(state,action,world):
    if not isinstance(state,GuardianChargeState139)or not isinstance(action,QueuedGuardianSkill139):raise TypeError('Typed current925action and complete owners required')
    if state.difficulty387!=0:raise PendingGuardianCharge139('Nondefault35067durationfactor pending')
    if action.raw40[37]!=7:raise PendingGuardianCharge139('Onlycurrent916rawtag7 dispatch recovered')
    if not 0<=action.unit_index<len(state.records432):return GuardianChargeResult139(state,(),False,None,None)
    old=state.records432[action.unit_index]
    if word139(old,0)!=0:return GuardianChargeResult139(state,(),False,None,None)
    if word139(old,244)!=f.MASK or word139(old,64)!=3 or word139(old,76)!=action.ability_pointer:raise PendingGuardianCharge139('Actual2372Guardian64familyandmatchingabilityowner')
    for value in(state.now_bits,*state.player_xyz):
        if f.is_nan(value)or f.is_inf(value):raise PendingGuardianCharge139('Finite componentcoordinates/clocks')
    spell=word139(action.raw40,0);xyz=position3_139(old,state.now_bits)
    #4860 exits at currentGuardian244==-1 after playerXYZ projection. The
    #rawtag7 branch passes1, and does not read the record's zero param words.
    target=_project(world,state.player_xyz,fallback_to_current=True)
    yaw=atan2_bits(f.sub(target[1],xyz[1]),f.sub(target[0],xyz[0]))
    length=f.add(_distance(xyz,target),0x40c00000)
    planned=(f.add(xyz[0],f.mul(_trig139(yaw,True),length)),f.add(xyz[1],f.mul(_trig139(yaw,False),length)),target[2])
    endpoint=_project(world,_navigation_stop(world,xyz,planned),fallback_to_current=True)
    #47161 uses genuine30179 and subtracts.5/max(segmentlength,.5) when
    #blocked.58587 height-corrects the resulting endpoint before measuring.
    distance=_max(_distance(xyz,endpoint),0x40800000)
    stop_duration=f.add(f.div(distance,0x42200000),0x3f800000)
    weakness=word139(old,128)if f.to_float(state.now_bits)<f.to_float(word139(old,132))else word139(old,136)if f.to_float(word139(old,140))>f.to_float(state.now_bits)else 0
    attack=f.mul(word139(old,296),f.sub(0x3f800000,weakness));damage=f.add(attack,attack)
    stopped=_project(world,xyz,fallback_to_current=True);row=list(old)
    #Common916preface32071 extends the Guardian100castlock before dispatch.
    _put(row,100,_max(word139(old,100),f.add(f.add(state.now_bits,0x3fcccccd),0x3ecccccd)))
    for at in(316,328):row[at:at+12]=struct.pack('<3I',*stopped)
    _put(row,340,state.now_bits);_put(row,344,0)
    expiry=_max(f.add(stop_duration,state.now_bits),word139(old,408));_put(row,408,expiry);_put(row,348,expiry)
    _put(row,352,_max(f.add(stop_duration,0x3e99999a),word139(old,352)))
    guid=guid139(old);sequence=(state.sequence2412+1)&f.MASK
    move=_packed(guid)+struct.pack('<4I',*stopped,sequence)+b'\4'+struct.pack('<4I3I',yaw,256,1,1,*stopped)
    packets=[(221,move.hex())]
    if spell:packets.append((305,(_packed(guid)*2+struct.pack('<IHIH',spell,2,1000,0)).hex()))
    rows,effect=_reserve(state.effects.storage,state.effects.count,120);counter=(state.counter2356+1)&f.MASK
    _put(effect,0,0);_put(effect,8,0);effect[12:24]=(None,)*12
    effect[24:40]=struct.pack('<QQ',guid,0)
    width=_min(_max(f.mul(word139(old,312),0x3f99999a),0x40800000),0x40e00000)
    effect[40:52]=struct.pack('<3I',2,distance,width)
    origin=_project(world,xyz,fallback_to_current=False)
    for at,value in((52,counter),(56,origin[0]),(60,origin[1]),(64,origin[2]),(68,yaw),(72,state.now_bits),(76,f.add(state.now_bits,0x3f800000)),(80,0),(84,0),(88,damage),(92,f.INF)):_put(effect,at,value)
    effect[96:119]=bytes(23);effect_index=state.effects.count;rows[effect_index]=tuple(effect)
    effects=EffectVector120139(tuple(rows),effect_index+1)
    #64899 copies a40B tagged action into its56B owner. Only XYZ and tag35
    #are initialized in this branch; the other copied scratch bytes stayNone.
    rows,deferred=_reserve(state.deferred.storage,state.deferred.count,56)
    deferred[:24]=struct.pack('<QI3I',guid,f.add(state.now_bits,0x3f800000),*endpoint)
    deferred[24:52]=(None,)*28;deferred[49]=35
    deferred_index=state.deferred.count;rows[deferred_index]=tuple(deferred)
    pending=DeferredGuardianVector56139(tuple(rows),deferred_index+1)
    records=list(state.records432);records[action.unit_index]=tuple(row)
    final=replace(state,records432=tuple(records),effects=effects,deferred=pending,counter2356=counter,sequence2412=sequence)
    return GuardianChargeResult139(final,tuple(packets),True,effect_index,deferred_index)
