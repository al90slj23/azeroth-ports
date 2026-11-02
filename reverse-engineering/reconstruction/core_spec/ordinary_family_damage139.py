"""Current139913 natural leech/death over bound normal-melee declarations.

Actual definition+56 XP and+60 cost are consumed. Unsupported definitions,
source owners and spell contexts stop, keeping old frozen default code intact.
Demo1160 identity is statically bound for its explicit future cast callback;
behavior acceptance is recorded per caller experiment, never inferred here.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .death139 import (OrdinaryDamageState139,UnknownDeath139,word139,guid139,
    position3_139,_u,_set,_finite,_bits64,_double,_next24,_bounded3)
from .death_pickups139 import append_death_pickup139
from .hit_events139 import plan_damage_tail_events139
from .healing139 import HealingLedger139,DefaultHealingSources139,PendingHealing139,leech_player139
from .natural_damage139 import DefaultDamageResult139
from .ordinary_family139_data import definition139

IDENTITIES139={0:'melee',845:'ability:cleave:r1',6343:'ability:thunder_clap:r1',1160:'ability:demo_shout:r1'}
@dataclass(frozen=True)
class OrdinaryFamilyLedger139(HealingLedger139):
    def __post_init__(self):
        if any(type(v)is not int or not 0<=v<1<<64 for v in(self.event_counter960,self.accepted_count1016)):raise ValueError('Actual u64 accounting counters')
        if len({k for k,v in self.reason_totals64})!=len(self.reason_totals64):raise ValueError('Unique semantic source totals')
        for key,bits in self.reason_totals64:
            if key not in('regen','leech','level_up',*IDENTITIES139.values())or not math.isfinite(_double(bits)):raise PendingHealing139('Unbound family outgoing attribution')

def _account_family_damage139(ledger,account,spell_id):
    if spell_id not in IDENTITIES139:raise PendingHealing139('Unbound outgoing source identity')
    rows=list(ledger.reason_totals64);reason=IDENTITIES139[spell_id]
    j=next((j for j,(key,_)in enumerate(rows)if key==reason),None)
    value=_bits64(account+(0.0 if j is None else _double(rows[j][1])))
    if j is None:rows.append((reason,value))
    else:rows[j]=(reason,value)
    return replace(ledger,event_counter960=(ledger.event_counter960+1)&((1<<64)-1),accepted_count1016=(ledger.accepted_count1016+1)&((1<<64)-1),reason_totals64=tuple(rows))

def resolve_family_damage139(state,target_guid,amount_bits,world,*,spell_id=6343,school=0,critical=0,inherited_context908,healing,healing_sources,outgoing_owned80,suppress_spell_damage_packet,heal_on_kill1600_bits=0):
 if not isinstance(state,OrdinaryDamageState139):raise TypeError('OrdinaryDamageState139')
 if not isinstance(healing,HealingLedger139)or not isinstance(healing_sources,DefaultHealingSources139):raise TypeError('Actual healing/source owners required')
 if spell_id==0:
  if outgoing_owned80 is not None or suppress_spell_damage_packet!=1:raise PendingHealing139('Actualbasicspell0/packetflag1required')
 elif spell_id in(845,6343,1160):
  if type(outgoing_owned80)is not bytes or len(outgoing_owned80)!=80 or word139(outgoing_owned80,0)!={845:5882740,6343:5882916,1160:5883180}[spell_id]or word139(outgoing_owned80,4)!=1 or suppress_spell_damage_packet!=0:raise PendingHealing139('Actualrank1ownedsourceandpacketflag0required')
 else:raise PendingHealing139('Otheroutgoingabilitysourcepending')
 if heal_on_kill1600_bits!=0:raise PendingHealing139('Nonzero death-heal-on-kill11033 branch pending')
 ledger=OrdinaryFamilyLedger139(healing.event_counter960,healing.accepted_count1016,healing.reason_totals64);heal_events=();player_keys=()
 _u(target_guid,64)
 for v in(amount_bits,spell_id):_u(v)
 for v in(school,critical,inherited_context908):_u(v,8)
 if inherited_context908:raise UnknownDeath139('InheritedGame908proccontext')
 if state.phase2587!=1:return DefaultDamageResult139(state,False,False,0,None,(),(),None,None,0,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)
 index=next((i for i,row in enumerate(state.records432)if guid139(row)==target_guid),None)
 if index is None:return DefaultDamageResult139(state,False,False,0,None,(),(),None,None,0,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)
 oldrow=state.records432[index]
 if word139(oldrow,0)==1:return DefaultDamageResult139(state,False,False,0,None,(),(),None,None,0,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)
 if any(word139(oldrow,o)!=f.MASK for o in(40,64,244)):raise UnknownDeath139('Only actual ordinary definition/tags')
 definition=definition139(word139(oldrow,284))
 if oldrow[424]!=definition.word(68):raise UnknownDeath139('Actual bound ordinary nonelite classification424 required')
 now=f.to_float(state.now_bits);mult=0x3f800000
 if now<f.to_float(word139(oldrow,148)):mult=f.add(mult,word139(oldrow,144))
 term=word139(oldrow,152)if now<f.to_float(word139(oldrow,156))else(word139(oldrow,160)if now<f.to_float(word139(oldrow,164))else 0)
 mult=f.add(f.add(f.add(mult,term),word139(oldrow,368)),0)
 school_add=0x3dcccccd if school&254==2 and f.to_float(word139(oldrow,372))>now else 0
 damage=f.mul(f.mul(amount_bits,f.add(mult,school_add)),0x3f800000)
 if f.is_nan(damage)or not f.to_float(damage)>1:damage=0x3f800000
 hp=word139(oldrow,288);newhp=f.sub(hp,damage)
 if any(not _finite(x)for x in(hp,newhp,state.now_bits,state.player_hp1440_bits,state.maximum1536_bits)):raise UnknownDeath139('Finiteordinarydamage domain')

 account=min(max(f.to_float(hp),0),f.to_float(damage));total=_bits64(_double(state.accounted_total_bits)+account)
 spell_totals=list(state.spell_totals64);found=next((j for j,(key,_)in enumerate(spell_totals)if key==spell_id),None)
 if found is None:spell_totals.append((spell_id,_bits64(account)))
 else:spell_totals[found]=(spell_id,_bits64(_double(spell_totals[found][1])+account))
 row=list(oldrow);_set(row,288,newhp);records=list(state.records432);records[index]=tuple(row);newstate=replace(state,records432=tuple(records),accounted_total_bits=total,spell_totals64=tuple(spell_totals))
 ledger=_account_family_damage139(ledger,account,spell_id)
 heal=leech_player139(newstate.player_hp1440_bits,newstate.maximum1536_bits,damage,newstate.now_bits,ledger,healing_sources)
 ledger,heal_events,player_keys=heal.ledger,heal.events,heal.key_writes
 newstate=replace(newstate,player_hp1440_bits=heal.hp_bits)
 key22=max(0,math.ceil(f.to_float(newhp)))
 if f.to_float(newhp)>0:return DefaultDamageResult139(newstate,True,False,damage,None,(),(),key22,None,0,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)
 if word139(oldrow,240)!=0:raise UnknownDeath139('Nonemptyunit44effectsource')
 xyz=position3_139(oldrow,state.now_bits);start=word139(oldrow,340);duration=word139(oldrow,344);packets=[];sequence=state.movement_sequence2412
 if f.to_float(duration)>0 and now<f.to_float(f.add(start,duration)):
  sequence=(sequence+1)&f.MASK;height=world.height(xyz[0],xyz[1]);stopxyz=(xyz[0],xyz[1],height.value_bits if height.found else xyz[2])
  if not height.found and world.primary is not None:raise UnknownDeath139('Movementsnapprimarynearest')
  raw=target_guid.to_bytes(8,'little');packed=bytes([sum(1<<j for j,v in enumerate(raw)if v)])+bytes(v for v in raw if v);packets.append((221,(packed+struct.pack('<4I',*stopxyz,sequence)+bytes([1])).hex()))
 _set(row,0,1);_set(row,4,state.now_bits);_set(row,240,0)
 for off in(316,328):row[off:off+12]=struct.pack('<3I',*xyz)
 _set(row,340,state.now_bits);_set(row,344,0);records[index]=tuple(row)
 words=state.rng_words;xp_random,words=_next24(words);xp_scaled=f.mul(f.from_u32(definition.word(56)),0x3fd33333);whole=int(f.to_float(xp_scaled));fraction=f.sub(xp_scaled,f.from_float(math.trunc(f.to_float(xp_scaled))));xp=(whole+int(f.to_float(fraction)>f.to_float(xp_random)))&f.MASK;direct=1;vec=state.pickups;counter=state.counter2408;events=[]
 if xp:
  r=append_death_pickup139(0,xp,xyz,world,words,counter,state.now_bits,vector=vec);vec,counter,words=r.vector,r.counter,r.rng_words;packets.extend(r.packets);events.append(('XP',xp,r.guid,r.position_bits,r.merged_index))
 coin_random,words=_next24(words);direct+=1
 if f.to_float(coin_random)<f.to_float(0x3e28f5c3):
  amount,words,n=_bounded3(words);direct+=n;coinxyz=(f.add(xyz[0],0x3f4ccccd),f.add(xyz[1],0x3f4ccccd),xyz[2]);r=append_death_pickup139(1,amount,coinxyz,world,words,counter,state.now_bits,vector=vec);vec,counter,words=r.vector,r.counter,r.rng_words;packets.extend(r.packets);events.append(('currency',amount,r.guid,r.position_bits,None))
 plan=plan_damage_tail_events139(state.sources.hit_sources.initial_mode770,state.sources.hit_sources.event_definitions36,0)
 newstate=replace(newstate,records432=tuple(records),rng_words=tuple(words),pickups=vec,counter2408=counter,movement_sequence2412=sequence,kills1084=(state.kills1084+1)&f.MASK,elites1088=(state.elites1088+(oldrow[424]&1))&f.MASK,killcost2420_bits=f.add(definition.word(60),state.killcost2420_bits))
 return DefaultDamageResult139(newstate,True,True,damage,xyz,tuple(events),tuple(packets),0,plan,direct,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)

