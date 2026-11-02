"""Current139 natural2890 kind0XP/kind1coin collection over known/None56 storage.

The gain_xp callback is an explicit typed growth component,not an empty stub.
Radius/player/time are entry snapshots; each reverse-ordered award reads the
latest growth.derived_bits. Claims are real ordered88 sources,never a boolean.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .death_pickups139 import PickupVector139,word139

class UnknownCollection139(NotImplementedError):pass
MIN_DELAY139=0x3df5c28f

def _uint(v,bits=32):
 if type(v)is not int or not 0<=v<1<<bits:raise ValueError('Explicitunsignedscalar')
 return v

def _guid(row):return word139(row,16)|(word139(row,20)<<32)
def _packed(v):
 raw=v.to_bytes(8,'little');return bytes([sum(1<<j for j,x in enumerate(raw)if x)])+bytes(x for x in raw if x)
def _distance(row,player):
 dx,dy=f.sub(word139(row,40),player[0]),f.sub(word139(row,44),player[1]);return sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy)))
def round86979_139(value):
 # Exact WAT adds the signed predecessor of .5 then masks fractional bits.
 value=f.add(value,0x3effffff|(value&f.SIGN));exponent=(value>>23)&255
 if exponent<=149:
  mask=f.SIGN if exponent<127 else ((-0x800000)>>((exponent-127)&31))&f.MASK
  value&=mask
 return value

def _truncsat(value):
 x=f.to_float(value)
 if math.isnan(x)or x<=0:return 0
 if x>=f.MASK:return f.MASK
 return int(x)

def mode_factor139(mode,member_count,zone_index):
 if mode!=1:return 0x3f800000
 coefficient=0x3f333333 if zone_index<3 else 0x3f800000
 denominator=f.add(f.mul(f.mul(coefficient,f.from_u32((member_count-1)&f.MASK)),0x3e9fbe77),0x3f800000)
 return f.div(0x3f800000,denominator)

def attract221_139(guid,from_xyz,to_xyz,sequence,delay_bits):
 milliseconds=_truncsat(f.mul(delay_bits,0x447a0000))
 return(221,(_packed(guid)+struct.pack('<4I',*from_xyz,sequence)+bytes([0])+struct.pack('<3I',256,max(1,milliseconds),1)+struct.pack('<3I',*to_xyz)).hex())
def despawn170_139(guid):return(170,struct.pack('<Q',guid).hex())

@dataclass(frozen=True)
class ClaimSource139:
 storage88:tuple
 count:int
 capacity2108:int|None
 pointer2112:int|None
 def __post_init__(self):
  if type(self.storage88)is not tuple or type(self.count)is not int or not 0<=self.count<=len(self.storage88)<=512:raise ValueError('Boundedreal88Bclaimsource')
  for row in self.storage88:
   if len(row)!=88 or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in row):raise ValueError('88known/Nonecells')
  if self.capacity2108 is not None and(self.capacity2108<len(self.storage88)or self.count>self.capacity2108):raise ValueError('Claimheadercapacity')

def constructor_empty_claims139():
 """1600 Game=SP+88: SP2196 i64(8<<32);SP2204 i64zero."""
 return ClaimSource139((),0,0,8)

@dataclass(frozen=True)
class ForwardQueue139:
 capacity:int
 entries:tuple=()
 def __post_init__(self):
  _uint(self.capacity)
  if type(self.entries)is not tuple or len(self.entries)>self.capacity:raise ValueError('Explicitlogical8Bqueue')
  for pair in self.entries:
   if len(pair)!=2:raise ValueError('Peer/baseamountpairs')
   for v in pair:_uint(v)
 def append(self,peer,amount):
  capacity=self.capacity
  if len(self.entries)==capacity:capacity=max(4,capacity*2)
  if capacity>f.MASK:raise UnknownCollection139('Queueallocationoverflow')
  return ForwardQueue139(capacity,self.entries+((peer,amount),))

@dataclass(frozen=True)
class NaturalCollectionState139:
 growth:object
 pickups:PickupVector139
 claims:ClaimSource139
 player_xyz:tuple
 movement_sequence2412:int
 gold1456:int
 earned1100:int
 mode2582:int
 peer2528:int
 member_count2540:int
 zone_index:int
 xp_queue2144:ForwardQueue139
 coin_queue2156:ForwardQueue139
 def __post_init__(self):
  if not isinstance(self.pickups,PickupVector139)or not isinstance(self.claims,ClaimSource139):raise TypeError('Explicitphysicalpickup/claimowners')
  if not isinstance(self.xp_queue2144,ForwardQueue139)or not isinstance(self.coin_queue2156,ForwardQueue139):raise TypeError('Typedforwardqueueowners')
  if len(self.player_xyz)!=3:raise ValueError('EntryplayerXYZ')
  for v in(*self.player_xyz,self.movement_sequence2412,self.gold1456,self.earned1100,self.peer2528,self.member_count2540,self.zone_index):_uint(v)
  _uint(self.mode2582,8)
  if not isinstance(self.growth.derived_bits,dict)or not isinstance(self.growth.player_fields,dict):raise TypeError('TypedGrowthState139dictfields')

@dataclass(frozen=True)
class NaturalCollectionResult139:
 state:NaturalCollectionState139
 packets:tuple
 attraction_events:tuple
 consumption_events:tuple
 growth_results:tuple
 claimed_pickup_guids:tuple
 precompaction_storage56:tuple
 complete_growth_packet_stream:bool=False
 pending:tuple=('growth/choicepacketsarenotpartofcollectorpacketencoder','physicalheap/queuepointers')


def collect_natural_pickups139(state,now_bits,*,gain_xp139):
 if not isinstance(state,NaturalCollectionState139)or not callable(gain_xp139):raise TypeError('NaturalCollectionState139andrealtypedgrowthcallbackrequired')
 _uint(now_bits)
 if f.is_nan(now_bits)or f.is_inf(now_bits):raise UnknownCollection139('Finiteclockdomain')
 growth=replace(state.growth,now_bits=now_bits);radius=growth.derived_bits[1560];player=state.player_xyz;rows=list(state.pickups.storage);count=state.pickups.count;claimed=[]
 # Original gathers only marker1 claims whose GUID8 matches a pickup.
 for row in rows[:count]:
  guid=_guid(row)
  for claim in state.claims.storage88[:state.claims.count]:
   if word139(claim,0)==1:
    part=tuple(claim[8:16])
    if None in part:raise UnknownCollection139('ConsumedunknownclaimGUID8')
    if int.from_bytes(bytes(part),'little')==guid:claimed.append(guid);break
 # Unsupported selected resource routes stop before returning any mutation.
 for row in rows[:count]:
  kind=word139(row,8)
  if kind not in(0,1)and f.to_float(_distance(row,player))<=3:raise UnknownCollection139('Nearbykind2+/resourceconsumer')
 attractions=[];sequence=state.movement_sequence2412;packets=[]
 for index in range(count):
  row=rows[index]
  if word139(row,8)!=0 or word139(row,0)!=0:continue
  distance=_distance(row,player);age=f.to_float(f.sub(now_bits,word139(row,52)))>6 and _guid(row)not in claimed
  if not age and not f.to_float(distance)<=f.to_float(radius):continue
  delay=f.div(distance,0x42000000 if age else 0x41c00000)
  if f.is_nan(delay)or not f.to_float(delay)>f.to_float(MIN_DELAY139):delay=MIN_DELAY139
  updated=list(row);updated[0:4]=struct.pack('<I',1);updated[4:8]=struct.pack('<I',f.add(now_bits,delay));rows[index]=tuple(updated);guid=_guid(row);sequence=(sequence+1)&f.MASK
  source=tuple(word139(row,o)for o in(40,44,48));packets.append(attract221_139(guid,source,player,sequence,delay));attractions.append((index,guid,delay,age,sequence))
 precompaction=tuple(rows);eligible=[]
 for index in range(count):
  row=rows[index];kind=word139(row,8)
  if kind==0:accept=word139(row,0)!=0 and f.to_float(word139(row,4))<=f.to_float(now_bits)
  elif kind==1:
   accept=f.to_float(_distance(row,player))<=f.to_float(radius)
   if not accept:accept=word139(row,0)==1 and f.to_float(word139(row,4))<=f.to_float(now_bits)
  else:accept=False
  if accept:eligible.append(index)
 events=[];results=[];xpq=state.xp_queue2144;coinq=state.coin_queue2156;gold=state.gold1456;earned=state.earned1100
 for index in reversed(eligible):
  row=rows[index];kind=word139(row,8);amount=word139(row,12);guid=_guid(row);marker=word139(row,0)
  #32070 marker2 exits to81894 panic after its partialcompaction.
  if marker==2:raise UnknownCollection139('Selectedmarker2trapsinoriginal32070;notnormalreturn')
  #Normal32070 copies the complete56B tail down;capacity/tailbytes stayinplace.
  if word139(row,32)!=0:raise UnknownCollection139('NonemptyauxiliaryGUIDdestructionowner')
  for j in range(index,count-1):rows[j]=rows[j+1]
  count-=1
  packets.append(despawn170_139(guid))
  factor=mode_factor139(state.mode2582,state.member_count2540,state.zone_index)
  if kind==0:
   if state.mode2582:xpq=xpq.append(state.peer2528,amount)
   scaled=f.mul(factor,f.mul(growth.derived_bits[1564],f.from_u32(amount)));rounded=round86979_139(scaled)
   if f.is_nan(rounded)or not f.to_float(rounded)>1:rounded=0x3f800000
   award=_truncsat(rounded);result=gain_xp139(growth,award,sequence);growth=result.state;sequence=result.context.movement_sequence2412;packets.extend(result.packets);results.append(result)
  else:
   if state.mode2582:coinq=coinq.append(state.peer2528,amount)
   award=_truncsat(round86979_139(f.mul(factor,f.mul(growth.derived_bits[1588],f.from_u32(amount)))));gold=(gold+award)&f.MASK;earned=(earned+award)&f.MASK;fields=dict(growth.player_fields);fields[1176]=(gold*10000)&f.MASK;growth=replace(growth,player_fields=fields)
  events.append((index,kind,guid,amount,award))
 new=replace(state,growth=growth,pickups=PickupVector139(tuple(rows),count),movement_sequence2412=sequence,gold1456=gold,earned1100=earned,xp_queue2144=xpq,coin_queue2156=coinq)
 return NaturalCollectionResult139(new,tuple(packets),tuple(attractions),tuple(events),tuple(results),tuple(claimed),precompaction)
