"""Current139913 ordinaryNPC accepted-hit/death gameplay projection.

Explicit known/None432 records, constructor-derived empty event owners and
resolved raw139 world queries are inputs. Every consumed unknown raises.
The full592/HP169 packet stream and physical heapowners remain separate.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .rng import next_u32_words
from .death_pickups139 import PickupVector139,append_death_pickup139
from .hit_events139 import ConstructorHitSources139,plan_damage_tail_events139

DEFAULT_POINTER139=5830904
DEFAULT72_139=bytes.fromhex('0000000000000000000000000000000050f858000d000000580200001a0000006666663f070000000000c04100004040cdcccc3f0000a040010000000000803f0000000000000000')
class UnknownDeath139(NotImplementedError):pass

def _u(v,bits=32):
 if type(v)is not int or not 0<=v<1<<bits:raise ValueError('Explicit unsigned scalar')
 return v

def record139(row):
 row=tuple(row)
 if len(row)!=432 or any(v is not None and(type(v)is not int or not 0<=v<=255)for v in row):raise ValueError('432 known/None bytes')
 return row

def word139(row,o):
 part=tuple(row[o:o+4])
 if len(part)!=4 or None in part:raise UnknownDeath139('Actuallyreadunknown NPCword '+str(o))
 return struct.unpack('<I',bytes(part))[0]
def guid139(row):return word139(row,112)|(word139(row,116)<<32)
def _set(row,o,value,width=4):row[o:o+width]=value.to_bytes(width,'little')
def _finite(b):return not f.is_nan(b)and not f.is_inf(b)
def _next24(words):
 output,words=next_u32_words(words);return f.mul(f.from_u32(output>>8),0x33800000),tuple(words)
def _bounded3(words):
 for count in range(1,100001):
  output,words=next_u32_words(words);product=output*3
  if product&f.MASK<=0xbfffffff:return(product>>32)+2,tuple(words),count
 raise UnknownDeath139('Independentbounded3watchdog;notoriginalguard')
def _double(b):return struct.unpack('<d',struct.pack('<Q',b))[0]
def _bits64(v):return struct.unpack('<Q',struct.pack('<d',v))[0]

def position3_139(row,now):
 duration=word139(row,344)
 if f.to_float(duration)<=0:return tuple(word139(row,o)for o in(328,332,336))
 t=f.div(f.sub(now,word139(row,340)),duration)
 if f.to_float(t)<0:t=0
 if f.to_float(t)>1:t=0x3f800000
 return tuple(f.add(word139(row,a),f.mul(f.sub(word139(row,b),word139(row,a)),t))for a,b in((316,328),(320,332),(324,336)))

@dataclass(frozen=True)
class DefaultDeathSources139:
 hit_sources:ConstructorHitSources139
 items8:tuple
 adjustments8:tuple
 timed32:tuple
 onkill_sources:tuple
 scheduled_procs:tuple
 def __post_init__(self):
  if not isinstance(self.hit_sources,ConstructorHitSources139):raise TypeError('Actualconstructor-derivedhit owner')
  for value in(self.items8,self.adjustments8,self.timed32,self.onkill_sources,self.scheduled_procs):
   if type(value)is not tuple:raise TypeError('Explicitorderedsource snapshots')
   if value:raise UnknownDeath139('Nonemptyitem/timed/adjustment/onkill/proc source')
  if self.hit_sources.event_definitions36.count!=0 or not self.hit_sources.owned_execution_scan.execution11_arm_skipped:raise UnknownDeath139('Defaulttrueemptyevent/noexecution11 owner required')

@dataclass(frozen=True)
class OrdinaryDamageState139:
 records432:tuple
 rng_words:tuple
 now_bits:int
 phase2587:int
 accounted_total_bits:int
 spell_totals64:tuple
 kills1084:int
 elites1088:int
 counter2408:int
 movement_sequence2412:int
 killcost2420_bits:int
 player_hp1440_bits:int
 maximum1536_bits:int
 pickups:PickupVector139
 sources:DefaultDeathSources139
 def __post_init__(self):
  if type(self.records432)is not tuple or len(self.records432)>128:raise ValueError('ExplicitboundedNPC source')
  for row in self.records432:record139(row)
  if type(self.rng_words)is not tuple or len(self.rng_words)!=4:raise ValueError('FourRNGwords')
  for v in(*self.rng_words,self.now_bits,self.kills1084,self.elites1088,self.counter2408,self.movement_sequence2412,self.killcost2420_bits,self.player_hp1440_bits,self.maximum1536_bits):_u(v)
  _u(self.phase2587,8);_u(self.accounted_total_bits,64)
  if not isinstance(self.pickups,PickupVector139)or not isinstance(self.sources,DefaultDeathSources139):raise TypeError('Explicitpickup/source owners')
  if len({x[0]for x in self.spell_totals64})!=len(self.spell_totals64):raise ValueError('Uniqueordered spell total keys')
  for spell,bits in self.spell_totals64:_u(spell);_u(bits,64)

@dataclass(frozen=True)
class OrdinaryDamageResult139:
 state:OrdinaryDamageState139
 applied:bool
 dead:bool
 damage_bits:int
 death_xyz:tuple|None
 reward_events:tuple
 known_packets:tuple
 target_key22:int|None
 event_tail_plan:object|None
 direct_reward_draws:int
 physical_packet_stream_complete:bool=False
 pending:tuple=('592damage/HP169fullpacketstream','physicalBTree/heap/pointers/packetqueueheaders')

def resolve_ordinary_damage139(state,target_guid,amount_bits,world,*,spell_id=845,school=0,critical=0,context=0):
 if not isinstance(state,OrdinaryDamageState139):raise TypeError('OrdinaryDamageState139')
 _u(target_guid,64)
 for v in(amount_bits,spell_id):_u(v)
 for v in(school,critical,context):_u(v,8)
 if context:raise UnknownDeath139('Recursiveproccontext')
 if state.phase2587!=1:return OrdinaryDamageResult139(state,False,False,0,None,(),(),None,None,0)
 index=next((i for i,row in enumerate(state.records432)if guid139(row)==target_guid),None)
 if index is None:return OrdinaryDamageResult139(state,False,False,0,None,(),(),None,None,0)
 oldrow=state.records432[index]
 if word139(oldrow,0)==1:return OrdinaryDamageResult139(state,False,False,0,None,(),(),None,None,0)
 if any(word139(oldrow,o)!=f.MASK for o in(40,64,244))or word139(oldrow,284)!=DEFAULT_POINTER139:raise UnknownDeath139('Onlyactualdefaultordinarydefinition/tags')
 if oldrow[424]not in(0,1):raise UnknownDeath139('Knownclassification424 required')
 now=f.to_float(state.now_bits);mult=0x3f800000
 if now<f.to_float(word139(oldrow,148)):mult=f.add(mult,word139(oldrow,144))
 term=word139(oldrow,152)if now<f.to_float(word139(oldrow,156))else(word139(oldrow,160)if now<f.to_float(word139(oldrow,164))else 0)
 mult=f.add(f.add(f.add(mult,term),word139(oldrow,368)),0)
 school_add=0x3dcccccd if school&254==2 and f.to_float(word139(oldrow,372))>now else 0
 damage=f.mul(f.mul(amount_bits,f.add(mult,school_add)),0x3f800000)
 if f.is_nan(damage)or not f.to_float(damage)>1:damage=0x3f800000
 hp=word139(oldrow,288);newhp=f.sub(hp,damage)
 if any(not _finite(x)for x in(hp,newhp,state.now_bits,state.player_hp1440_bits,state.maximum1536_bits)):raise UnknownDeath139('Finiteordinarydamage domain')
 if state.player_hp1440_bits!=state.maximum1536_bits:raise UnknownDeath139('FullHPdefaultWarrior lifesteal domain; positivehealing1466 pending')
 account=min(max(f.to_float(hp),0),f.to_float(damage));total=_bits64(_double(state.accounted_total_bits)+account)
 spell_totals=list(state.spell_totals64);found=next((j for j,(key,_)in enumerate(spell_totals)if key==spell_id),None)
 if found is None:spell_totals.append((spell_id,_bits64(account)))
 else:spell_totals[found]=(spell_id,_bits64(_double(spell_totals[found][1])+account))
 row=list(oldrow);_set(row,288,newhp);records=list(state.records432);records[index]=tuple(row);newstate=replace(state,records432=tuple(records),accounted_total_bits=total,spell_totals64=tuple(spell_totals));key22=max(0,math.ceil(f.to_float(newhp)))
 if f.to_float(newhp)>0:return OrdinaryDamageResult139(newstate,True,False,damage,None,(),(),key22,None,0)
 if word139(oldrow,240)!=0:raise UnknownDeath139('Nonemptyunit44effectsource')
 xyz=position3_139(oldrow,state.now_bits);start=word139(oldrow,340);duration=word139(oldrow,344);packets=[];sequence=state.movement_sequence2412
 if f.to_float(duration)>0 and now<f.to_float(f.add(start,duration)):
  sequence=(sequence+1)&f.MASK;height=world.height(xyz[0],xyz[1]);stopxyz=(xyz[0],xyz[1],height.value_bits if height.found else xyz[2])
  if not height.found and world.primary is not None:raise UnknownDeath139('Movementsnapprimarynearest')
  raw=target_guid.to_bytes(8,'little');packed=bytes([sum(1<<j for j,v in enumerate(raw)if v)])+bytes(v for v in raw if v);packets.append((221,(packed+struct.pack('<4I',*stopxyz,sequence)+bytes([1])).hex()))
 _set(row,0,1);_set(row,4,state.now_bits);_set(row,240,0)
 for off in(316,328):row[off:off+12]=struct.pack('<3I',*xyz)
 _set(row,340,state.now_bits);_set(row,344,0);records[index]=tuple(row)
 words=state.rng_words;xp_random,words=_next24(words);xp_scaled=f.mul(f.from_u32(1),0x3fd33333);whole=int(f.to_float(xp_scaled));fraction=f.sub(xp_scaled,f.from_float(math.trunc(f.to_float(xp_scaled))));xp=(whole+int(f.to_float(fraction)>f.to_float(xp_random)))&f.MASK;direct=1;vec=state.pickups;counter=state.counter2408;events=[]
 if xp:
  r=append_death_pickup139(0,xp,xyz,world,words,counter,state.now_bits,vector=vec);vec,counter,words=r.vector,r.counter,r.rng_words;packets.extend(r.packets);events.append(('XP',xp,r.guid,r.position_bits,r.merged_index))
 coin_random,words=_next24(words);direct+=1
 if f.to_float(coin_random)<f.to_float(0x3e28f5c3):
  amount,words,n=_bounded3(words);direct+=n;coinxyz=(f.add(xyz[0],0x3f4ccccd),f.add(xyz[1],0x3f4ccccd),xyz[2]);r=append_death_pickup139(1,amount,coinxyz,world,words,counter,state.now_bits,vector=vec);vec,counter,words=r.vector,r.counter,r.rng_words;packets.extend(r.packets);events.append(('currency',amount,r.guid,r.position_bits,None))
 plan=plan_damage_tail_events139(state.sources.hit_sources.initial_mode770,state.sources.hit_sources.event_definitions36,0)
 newstate=replace(newstate,records432=tuple(records),rng_words=tuple(words),pickups=vec,counter2408=counter,movement_sequence2412=sequence,kills1084=(state.kills1084+1)&f.MASK,elites1088=(state.elites1088+(oldrow[424]&1))&f.MASK,killcost2420_bits=f.add(0x3f800000,state.killcost2420_bits))
 return OrdinaryDamageResult139(newstate,True,True,damage,xyz,tuple(events),tuple(packets),0,plan,direct)

@dataclass(frozen=True)
class DeathCleaveResult139:
 state:OrdinaryDamageState139
 spell_sets:tuple
 success:int
 selected_ids:tuple
 owned80:bytes
 launch306_hex:str|None
 hits:tuple
 known_packets:tuple
 private_selection_checks:int=2


def cast_cleave_with_ordinary_death139(state,player_xyz,derived,definition,owned80,spell_sets,world,*,source_id=0,suppress_primary_attempt=False):
 """New adapter around frozen139selection/launch; known/None records persist.

 Two localopaque carriers are only for statically declared selector reads;
 no carrier bytes are returned as owned records. Full damage/death reads use
 word139 and therefore cannot silently consume any unknown byte.
 """
 from .cast139 import CleaveState139,cleave_targets139,cleave_launch306139
 from .combat139 import DamageState139,EmptyDamageSources139
 if not isinstance(state,OrdinaryDamageState139):raise TypeError('OrdinaryDamageState139')
 raw=definition.raw88
 if definition.pointer!=5882740 or bytes(raw)[84]!=5 or word139(owned80,0)!=definition.pointer:raise UnknownDeath139('Onlydefaultcleave')
 read32=(0,40,64,144,148,152,156,160,164,244,288,316,320,328,332,340,344,368,372,380,416,420)
 for row in state.records432:
  for off in read32:word139(row,off)
  guid139(row)
  if row[424]is None:raise UnknownDeath139('Unknownclassification')
 selections=[]
 for poison in(0xa5,0x5a):
  carriers=tuple(bytes(poison if v is None else v for v in row)for row in state.records432)
  combat=DamageState139(carriers,state.now_bits,state.phase2587,state.accounted_total_bits,state.rng_words,EmptyDamageSources139((),(),(),True))
  carrier=CleaveState139(combat,tuple(player_xyz),derived['1536'],derived['1540'],derived['1548'],derived['1552'],derived['1592'],source_id=source_id)
  selections.append(cleave_targets139(carrier,word139(raw,56)))
 if selections[0]!=selections[1]:raise UnknownDeath139('OpaqueNPCselectorinfluence')
 count=1 if word139(raw,64)==0 else max(1,(word139(raw,64)+word139(owned80,60)+word139(owned80,20)+derived['1592'])&f.MASK)
 selected=selections[0][:count];spell=word139(raw,44);sets=[tuple(x)for x in spell_sets]
 for j in range(3):
  if not(j==2 and suppress_primary_attempt)and spell not in sets[j]:sets[j]=sets[j]+(spell,)
 value=f.mul(f.mul(f.mul(f.mul(word139(raw,48),0x3fb33333),word139(owned80,12)),word139(owned80,52)),0x3f800000)
 life=f.mul(derived['1536'],word139(owned80,72))if f.to_float(word139(raw,48))>0 else 0;base=f.mul(derived['1540'],f.add(value,life));hits=[];packets=[]
 launch=None if not selected else cleave_launch306139(source_id,spell,selected)
 if launch:packets.append((306,launch))
 for target in selected:
  chance,words=_next24(state.rng_words);critical=int(f.to_float(f.add(0,derived['1548']))>f.to_float(chance));amount=f.mul(base,derived['1552'])if critical else base
  result=resolve_ordinary_damage139(replace(state,rng_words=words),target,amount,world,spell_id=spell,school=raw[85],critical=critical)
  state=result.state;hits.append((target,amount,critical,result));packets.extend(result.known_packets)
 return DeathCleaveResult139(state,tuple(sets),int(bool(selected)),selected,owned80,launch,tuple(hits),tuple(packets))
