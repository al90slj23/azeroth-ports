"""WIP current139922 exec2/effect11/spell1160 over explicit real owners.

Direct922 component.1238 cooldown application and925 expiry are separate
consumers; callback preserves the caller's complete actor type and owners.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .death139 import OrdinaryDamageState139,word139,guid139
from .demo_damage139 import resolve_demo_damage139
from .thunder_clap139 import targets_thunder_clap139,thunder_launch306139
from .opening_actor139 import _values,_guid
from .rng import next_u32_words
from .radius import radius_bits
from .candidates139_data import DEFINITIONS139

class PendingDemoShout139(NotImplementedError):pass

def _word(value):
 if type(value)is not int or not 0<=value<=f.MASK:raise ValueError('Actual u32/binary32 word required')
 return value

def _put(row,at,value):row[at:at+4]=struct.pack('<I',value)

def merge_demo_debuff21553(words,strength_bits,deadline_bits,now_bits):
    """Exact16B two-slot merge; ordered comparisons preserve NaN and signed0.

    Expired primary promotes a still-live backup first. A stronger incoming
    primary can retain the old weaker effect until its later expiry. Fallback
    is positive, live and strictly outlasts the resulting primary; ties retain
    the existing backup. This is neither unconditional overwrite nor max().
    """
    if type(words)is not tuple or len(words)!=4:
        raise ValueError('Complete four-word21553 owner required')
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
class DemoShoutDefinition139:
 pointer:int
 raw88:bytes
 def __post_init__(self):
  if self.pointer!=5883180 or type(self.raw88)is not bytes or len(self.raw88)!=88 or word139(self.raw88,0)!=11 or self.raw88[84:86]!=bytes([2,0])or word139(self.raw88,44)!=1160:raise PendingDemoShout139('CurrentdeclaredDemo1160/effect11/exec2required')

def demo_aura139(state,guid,spell,add):
 """Current4593 first live GUID,16inline slots,empty240 logical packet."""
 for index,old in enumerate(state.records432):
  if guid139(old)!=guid or word139(old,0)==1:continue
  if word139(old,240)!=0:raise PendingDemoShout139('Actual nonempty44B NPC ability owner')
  slots=[word139(old,168+4*i)for i in range(16)]
  if add:
   if spell in slots or 0 not in slots:return state,(),(),()
   slot=slots.index(0);slots[slot]=spell
  else:
   if spell not in slots:return state,(),(),()
   slot=slots.index(spell);slots[slot]=0
  row=list(old);_put(row,168+4*slot,slots[slot]);rows=list(state.records432);rows[index]=tuple(row);group=slot>>3;flags=sum(2<<(4*i)for i,value in enumerate(slots[group*8:group*8+8])if value);fields=((79+slot,slots[slot]),(99+group,flags),(121+(slot>>2),0));payload=(struct.pack('<IB',1,0)+bytes(1)+_guid(guid)+_values(dict(fields))).hex()
  return replace(state,records432=tuple(rows)),((169,payload),),((guid,168+4*slot,slots[slot]),),fields
 return state,(),(),()

def apply_demo_effect139(state,target,strength,duration,spell=1160):
 for index,old in enumerate(state.records432):
  if guid139(old)!=target or word139(old,0)==1:continue
  if word139(old,360)not in(0,1160):raise PendingDemoShout139('Other weakness spell source replacement not declared')
  deadline=f.add(state.now_bits,duration);merged=merge_demo_debuff21553(tuple(word139(old,p)for p in(128,132,136,140)),strength,deadline,state.now_bits);row=list(old);writes=[]
  for k,value in enumerate(merged):_put(row,128+4*k,value);writes.append((target,128+4*k,value))
  if f.to_float(merged[0])==f.to_float(strength)and f.to_float(merged[1])==f.to_float(deadline):_put(row,364,duration);writes.append((target,364,duration))
  previous=word139(row,360);changed=bool(spell and spell!=previous)
  if changed:_put(row,360,spell);writes.append((target,360,spell))
  rows=list(state.records432);rows[index]=tuple(row);state=replace(state,records432=tuple(rows));packets=[];fields=[]
  if changed:
   if previous:
    state,ps,ws,fs=demo_aura139(state,target,previous,False);packets.extend(ps);writes.extend(ws);fields.append((target,fs))
   state,ps,ws,fs=demo_aura139(state,target,spell,True);packets.extend(ps);writes.extend(ws);fields.append((target,fs))
  return state,tuple(writes),tuple(packets),tuple(fields)
 return state,(),(),()

def begin_demo_expiry139(records,now):
 rows=list(records);queue=[]
 for index,old in enumerate(rows):
  if word139(old,0)!=0 or word139(old,360)==0:continue
  if word139(old,360)!=1160:raise PendingDemoShout139('Undeclared weakness spell360')
  primary,backup=word139(old,132),word139(old,140);expiry=primary if f.to_float(primary)>f.to_float(now)else backup
  if f.to_float(expiry)<=f.to_float(now):
   row=list(old);_put(row,360,0);rows[index]=tuple(row);queue.append((guid139(old),1160))
 return tuple(rows),tuple(queue)

def finish_demo_expiry139(state,queue):
 packets=[];writes=[];fields=[]
 for guid,spell in queue:
  state,ps,ws,fs=demo_aura139(state,guid,spell,False);packets.extend(ps);writes.extend(ws);fields.append((guid,fs))
 return state,tuple(packets),tuple(writes),tuple(fields)

def demo_cooldown139(definition,owned80,derived):
 value=f.mul(f.mul(f.mul(f.mul(word139(definition.raw88,52),0x3fb33333),word139(owned80,16)),word139(owned80,56)),derived['1544'])
 return value if f.to_float(value)>.25 else 0x3e800000

@dataclass(frozen=True)
class DemoShoutResult139:
 state:OrdinaryDamageState139
 spell_sets:tuple
 healing:object
 success:int
 selected_ids:tuple
 base_damage_bits:int
 radius_bits:int
 strength_bits:int
 duration_bits:int
 hits:tuple
 effect_writes:tuple
 aura_fields:tuple
 known_packets:tuple
 heal_events:tuple
 player_key_writes:tuple
 cooldown_if_success_bits:int
 owned80:bytes
 physical_packet_stream_complete:bool=False

def cast_demo_shout139(state,player_xyz,derived,definition,owned80,spell_sets,world,*,healing,healing_sources,resolve_damage=None,source_id=0,suppress_primary_attempt=False,context908=0,heal_on_kill1600_bits=0):
 if not isinstance(definition,DemoShoutDefinition139)or not isinstance(state,OrdinaryDamageState139):raise TypeError('CurrenttypedDemo/damageownersrequired')
 if type(owned80)is not bytes or len(owned80)!=80 or word139(owned80,0)!=definition.pointer or word139(owned80,4)!=1:raise PendingDemoShout139('Actualrank1Demo80required;qualitytierdoesnotchangethisrank')
 if context908 or state.sources.hit_sources.event_definitions36.count or not state.sources.hit_sources.owned_execution_scan.execution11_arm_skipped:raise PendingDemoShout139('Inherited/nonemptyproc/event/ownedexecution11source')
 if len(player_xyz)!=3 or any(f.is_nan(v)or f.is_inf(v)for v in player_xyz):raise PendingDemoShout139('FiniteactualplayerXYZ')
 raw=definition.raw88;value=f.mul(f.mul(f.mul(f.mul(word139(raw,48),0x3fb33333),word139(owned80,12)),word139(owned80,52)),0x3f000000);life=f.mul(derived['1536'],word139(owned80,72))if f.to_float(word139(raw,48))>0 else 0;base=f.mul(derived['1540'],f.add(value,life));radius=radius_bits(f.mul(derived['1580'],f.mul(word139(raw,60),f.mul(word139(owned80,24),word139(owned80,64)))));targets=targets_thunder_clap139(state.records432,player_xyz,state.now_bits,radius);duration=f.mul(word139(raw,8),word139(owned80,68));strength=f.mul(word139(raw,4),word139(owned80,76));strength=0x3f666666 if f.is_nan(strength)or not f.to_float(strength)<f.to_float(0x3f666666) else strength
 sets=[tuple(v)for v in spell_sets]
 if len(sets)!=3 or any(len(v)!=len(set(v))for v in sets):raise ValueError('Actualordereduniquespellsetsrequired')
 for k in range(3):
  if not(k==2 and suppress_primary_attempt)and 1160 not in sets[k]:sets[k]+=(1160,)
 packets=[(306,thunder_launch306139(source_id,1160,targets))]if targets else[];hits=[];writes=[];fields=[];heals=[];keys=();resolver=resolve_demo_damage139 if resolve_damage is None else resolve_damage
 for target in targets:
  sample,words=next_u32_words(state.rng_words);roll=f.mul(f.from_u32(sample>>8),0x33800000);critical=int(f.to_float(derived['1548'])>f.to_float(roll));amount=f.mul(base,derived['1552'])if critical else base
  result=resolver(replace(state,rng_words=words),target,amount,world,spell_id=1160,school=0,critical=critical,inherited_context908=context908,healing=healing,healing_sources=healing_sources,outgoing_owned80=owned80,suppress_spell_damage_packet=0,heal_on_kill1600_bits=heal_on_kill1600_bits);state=result.state;healing=result.healing;packets.extend(result.known_packets);heals.extend(result.heal_events);keys=result.player_key_writes or keys;hits.append((target,amount,critical,result))
  state,ws,ps,fs=apply_demo_effect139(state,target,strength,duration);writes.extend(ws);packets.extend(ps);fields.extend(fs)
 return DemoShoutResult139(state,tuple(sets),healing,int(bool(targets)),targets,base,radius,strength,duration,tuple(hits),tuple(writes),tuple(fields),tuple(packets),tuple(heals),keys,demo_cooldown139(definition,owned80,derived),owned80)

def cast_demo_actor139(actor,index,world,*,resolve_damage=None):
 p=actor.player;g=p.growth;owned=g.owned_records80[index];definition=DemoShoutDefinition139(5883180,bytes.fromhex(DEFINITIONS139['demo_shout'][1]))
 from .healing139 import DefaultHealingSources139
 result=cast_demo_shout139(actor.damage,p.player_xyz,{str(k):v for k,v in g.derived_bits.items()},definition,owned,p.spell_sets,world,healing=actor.ledger,healing_sources=DefaultHealingSources139(1,g.source_counts),resolve_damage=resolve_damage,source_id=actor.player_guid,context908=actor.inherited_context908,heal_on_kill1600_bits=g.derived_bits[1600]);d=result.state;fields=dict(g.player_fields);fields.update(result.player_key_writes);g=replace(g,units432_cells=d.records432,rng_words=d.rng_words,current_hp_bits=d.player_hp1440_bits,player_fields=fields);p=replace(p,growth=g,spell_sets=result.spell_sets);return replace(actor,player=p,damage=d,ledger=result.healing),result
