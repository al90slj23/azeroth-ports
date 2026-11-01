"""Fixed135 demo_shout execution2/effect11 and helper21455, independently owned.

All debuff/Aura owners are explicit inputs. No game, memory, index or oracle
output is read. Empty auxiliary/proc sources and ordinary nonlethal consumers
use the shared cast contract. AI expiry/attack scheduling is a separate owner.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .cast135 import (CastResult,CastDeathBoundary,UnresolvedCast,base_damage,
    query_targets,_critical)
from .cast_events135 import apply_hit,cast_ability as cast_common
from .opening_entities135 import packed_guid,_values
from .owned_cast135 import OwnedEntry135,tick_owned
from .radius import radius_bits

def _word(value):
    if type(value)is not int or not 0<=value<=f.MASK:
        raise ValueError('Explicit unsigned32 demo word required')
    return value

def merge_demo_debuff21455(words,strength_bits,deadline_bits,now_bits):
    """Exact16B two-slot merge; ordered comparisons preserve NaN and signed0.

    Expired primary promotes a still-live backup first. A stronger incoming
    primary can retain the old weaker effect until its later expiry. Fallback
    is positive, live and strictly outlasts the resulting primary; ties retain
    the existing backup. This is neither unconditional overwrite nor max().
    """
    if type(words)is not tuple or len(words)!=4:
        raise ValueError('Complete four-word21455 owner required')
    for word in(*words,strength_bits,deadline_bits,now_bits):_word(word)
    a,ae,b,be=words;now=f.to_float(now_bits)
    if now>=f.to_float(ae):
        a,ae=(b,be)if now<f.to_float(be)else(0,0)
        b,be=0,0
    incoming=(strength_bits,deadline_bits)
    replace_primary=(now>=f.to_float(ae)or f.to_float(strength_bits)>f.to_float(a)
        or(f.to_float(strength_bits)==f.to_float(a)and f.to_float(deadline_bits)>f.to_float(ae)))
    if replace_primary:
        other=(a,ae);a,ae=incoming
    else:other=incoming
    winner=None
    for value,expiry in((b,be),other):
        if not(f.to_float(value)>0 and now<f.to_float(expiry)and f.to_float(ae)<f.to_float(expiry)):
            continue
        if winner is None or f.to_float(value)>f.to_float(winner[0])or(
            f.to_float(value)==f.to_float(winner[0])and f.to_float(expiry)>f.to_float(winner[1])):
            winner=(value,expiry)
    return(a,ae,*(winner if winner is not None else(0,0)))

@dataclass(frozen=True)
class DemoDebuff135:
    guid:int
    marker:int
    words128_140:tuple
    spell360:int
    duration364_bits:int
    aura_slots168:tuple
    ability_count240:int

    def __post_init__(self):
        if type(self.guid)is not int or not 0<=self.guid<1<<64:
            raise ValueError('Exact demo target GUID required')
        _word(self.marker);_word(self.spell360);_word(self.duration364_bits);_word(self.ability_count240)
        if type(self.words128_140)is not tuple or len(self.words128_140)!=4:
            raise ValueError('Complete128..140 owner required')
        if type(self.aura_slots168)is not tuple or len(self.aura_slots168)!=16:
            raise ValueError('Complete16-slot NPC Aura owner required')
        for word in(*self.words128_140,*self.aura_slots168):_word(word)

@dataclass(frozen=True)
class DemoEffectResult135:
    debuffs:tuple
    writes:tuple
    aura_actions:tuple
    aura_packets:tuple
    aura_fields:tuple

def _aura(row,spell,add):
    slots=list(row.aura_slots168)
    if add:
        if spell in slots or 0 not in slots:return row,None,None
        index=slots.index(0);slots[index]=spell
    else:
        if spell not in slots:return row,None,None
        index=slots.index(spell);slots[index]=0
    if row.ability_count240:
        raise UnresolvedCast('4543/15511 nonempty44B NPC ability-count owner remains pending')
    group=index>>3;flags=sum((2<<(4*i))for i,spell in enumerate(slots[group*8:group*8+8])if spell)
    fields=((79+index,slots[index]),(99+group,flags),(121+(index>>2),0))
    payload=struct.pack('<IB',1,0)+b'\0'+packed_guid(row.guid)+_values(fields)
    return replace(row,aura_slots168=tuple(slots)),(169,payload.hex()),fields

def apply_demo_effect135(debuffs,target_guid,strength_bits,duration_bits,now_bits,spell_id):
    """2244 effect11: first matching GUID with marker!=1, then21455 and4543.

    Other2244 effect kinds and effect1's effect49 override lookup are not used
    by this branch. The caller must still resolve922's wider proc sources.
    """
    if type(debuffs)is not tuple or any(not isinstance(row,DemoDebuff135)for row in debuffs):
        raise TypeError('Explicit ordered demo/NPC Aura owners required')
    if type(target_guid)is not int or not 0<=target_guid<1<<64:raise ValueError('GUID required')
    for word in(strength_bits,duration_bits,now_bits,spell_id):_word(word)
    rows=list(debuffs);writes=[];actions=[];packets=[];fields=[]
    for index,row in enumerate(rows):
        if row.guid!=target_guid or row.marker==1:continue
        deadline=f.add(now_bits,duration_bits);merged=merge_demo_debuff21455(row.words128_140,strength_bits,deadline,now_bits)
        row=replace(row,words128_140=merged)
        writes.extend((index,row.guid,128+j*4,word)for j,word in enumerate(merged))
        if f.to_float(merged[0])==f.to_float(strength_bits)and f.to_float(merged[1])==f.to_float(deadline):
            row=replace(row,duration364_bits=duration_bits);writes.append((index,row.guid,364,duration_bits))
        if spell_id and row.spell360!=spell_id:
            previous=row.spell360;row=replace(row,spell360=spell_id);writes.append((index,row.guid,360,spell_id))
            for spell,add in(((previous,False),)if previous else())+((spell_id,True),):
                actions.append((index,row.guid,spell,add));before=row.aura_slots168;row,packet,keys=_aura(row,spell,add)
                if packet is not None:
                    writes.extend((index,row.guid,168+j*4,value)for j,value in enumerate(row.aura_slots168)if value!=before[j])
                    packets.append(packet);fields.append((index,row.guid,keys))
        rows[index]=row;break
    return DemoEffectResult135(tuple(rows),tuple(writes),tuple(actions),tuple(packets),tuple(fields))

def _require(definition):
    if(definition.pointer!=5467868 or definition.ability_id!=b'demo_shout'
            or definition.execution_kind!=2 or definition.effect_tag!=11
            or definition.spell_id!=1160 or definition.school!=0):
        raise UnresolvedCast('Only fixed135 demo_shout execution2/effect11 admitted')

@dataclass(frozen=True)
class DemoShoutOwnedEntry135(OwnedEntry135):
    def __post_init__(self):
        _require(self.definition)
        if self.record.definition_pointer!=self.definition.pointer:raise ValueError('Resolved demo owned definition required')

@dataclass(frozen=True)
class DemoShoutResult135(CastResult):
    debuffs:tuple=()
    effect_writes:tuple=()
    aura_actions:tuple=()
    aura_packets:tuple=()
    aura_fields:tuple=()

def cast_demo_shout135(state,definition,owned,*,debuffs,after_hit=None,after_death=None,
                       effect49_sources=(),other_proc_sources_absent=True):
    _require(definition)
    if type(effect49_sources)is not tuple or effect49_sources or other_proc_sources_absent is not True:
        raise UnresolvedCast('Explicit empty922 auxiliary/effect49/proc sources required')
    if state.context908!=0:raise UnresolvedCast('Inherited proc context remains pending')
    if owned.definition_pointer!=definition.pointer:raise ValueError('Owned definition differs')
    if type(debuffs)is not tuple or len(debuffs)!=len(state.combat.units)or any(
        (row.guid,row.marker)!=(unit.target_id,unit.marker)for row,unit in zip(debuffs,state.combat.units)):
        raise ValueError('Debuff physical owners must match ordered combat units')
    base=base_damage(state,definition,owned);attempts=state.attempted_spell_ids
    if definition.spell_id not in attempts:attempts+=(definition.spell_id,)
    state=replace(state,attempted_spell_ids=attempts)
    radius=f.mul(owned.area_bits,owned.additional_area_bits);radius=f.mul(definition.radius_bits,radius)
    radius=radius_bits(f.mul(state.area_multiplier_bits,radius));targets=query_targets(state.spatial,state.player_xy,radius,state.combat.now_bits)
    duration=f.mul(0x40c00000,owned.additional_duration_bits)
    strength=f.mul(0x3eb33333,owned.field76_bits);strength=0x3f666666 if f.is_nan(strength)else strength
    strength=strength if f.to_float(strength)<f.to_float(0x3f666666)else 0x3f666666
    rows=debuffs;hits=[];writes=[];actions=[];packets=[];fields=[]
    for index,guid in enumerate(targets):
        state,damage,critical=_critical(state,base)
        try:state,result=apply_hit(state,guid,damage,definition.spell_id,after_hit=after_hit,after_death=after_death)
        except CastDeathBoundary as boundary:
            boundary.remaining_targets=targets[index+1:];boundary.pending_demo_effect=(guid,strength,duration)
            boundary.completed_demo_debuffs=rows;boundary.completed_demo_writes=tuple(writes);raise
        rows=tuple(replace(row,marker=unit.marker)for row,unit in zip(rows,state.combat.units))
        effect=apply_demo_effect135(rows,guid,strength,duration,state.combat.now_bits,definition.spell_id)
        rows=effect.debuffs;writes.extend(effect.writes);actions.extend(effect.aura_actions);packets.extend(effect.aura_packets);fields.extend(effect.aura_fields)
        hits.append((guid,damage,critical,result.new_hp_bits))
    return DemoShoutResult135(state,int(bool(targets)),targets,base,radius,tuple(hits),
        status='demo_shout_numeric_effect11_empty_NPC_ability_Aura_projection',debuffs=rows,
        effect_writes=tuple(writes),aura_actions=tuple(actions),aura_packets=tuple(packets),aura_fields=tuple(fields))

@dataclass(frozen=True)
class DemoShoutOwnedResult135:
    owned_tick:object
    debuffs:tuple
    effect_writes:tuple
    aura_actions:tuple
    aura_packets:tuple

def tick_owned_demo_shout135(state,entries,basic,dt_bits,*,debuffs,**kwargs):
    if 'cast_dispatch'in kwargs:raise TypeError('Demo wrapper owns explicit dispatcher')
    rows=debuffs;writes=[];actions=[];packets=[]
    def dispatch(state,definition,owned,**callbacks):
        nonlocal rows
        if definition.ability_id!=b'demo_shout':return cast_common(state,definition,owned,**callbacks)
        result=cast_demo_shout135(state,definition,owned,debuffs=rows,**callbacks);rows=result.debuffs
        writes.extend(result.effect_writes);actions.extend(result.aura_actions);packets.extend(result.aura_packets);return result
    result=tick_owned(state,entries,basic,dt_bits,cast_dispatch=dispatch,**kwargs)
    return DemoShoutOwnedResult135(result,rows,tuple(writes),tuple(actions),tuple(packets))
