"""Current1391446 kind0XP/kind1currency, caller-owned known/None backing.

DefaultElwynn world queries are explicit pure inputs. No program/snapshot or
captured state is read. Other kinds and primary-present miss stay pending.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .rng import uniform_range_bits
from .position_math139 import sin_bits,cos_bits,hypot_bits
from .world_position139_data import ZONE_GEOMETRY139

class UnknownDeathPickup139(NotImplementedError):pass

def uint139(v):
 if type(v)is not int or not 0<=v<=f.MASK:raise ValueError('Explicitu32 input')
 return v

def word139(row,o):
 v=row[o:o+4]
 if len(v)!=4 or None in v:raise UnknownDeathPickup139('Consumedunknownpickupword'+str(o))
 return struct.unpack('<I',bytes(v))[0]

def _packguid(v):
 raw=struct.pack('<Q',v);return bytes([sum(1<<i for i,x in enumerate(raw)if x)])+bytes(x for x in raw if x)
def _values(values):
 masks=[0]*(max(values)//32+1)
 for key in values:masks[key//32]|=1<<(key%32)
 return bytes([len(masks)])+struct.pack('<'+'I'*len(masks),*masks)+b''.join(struct.pack('<I',values[k])for k in sorted(values))

@dataclass(frozen=True)
class PickupVector139:
 storage:tuple
 count:int=0
 def __post_init__(self):
  if type(self.storage)is not tuple or type(self.count)is not int or not 0<=self.count<=len(self.storage)<=4096:raise ValueError('Explicitbounded56B backing/count')
  for row in self.storage:
   if len(row)!=56 or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in row):raise ValueError('56B known/None cells')
 @property
 def capacity(self):return len(self.storage)

def vector139(backing=(),count=0):return PickupVector139(tuple(tuple(bytes.fromhex(x))for x in backing),count)
def _append(v,writes):
 rows=list(v.storage)
 if v.count==v.capacity:rows.extend([(None,)*56]*(max(4,v.capacity*2)-v.capacity))
 row=list(rows[v.count])
 for o,b in writes:row[o:o+len(b)]=b
 rows[v.count]=tuple(row);return PickupVector139(tuple(rows),v.count+1)

def pickup_geometry139(xyz,world):
 if len(xyz)!=3 or any(f.is_nan(x)or f.is_inf(x)for x in xyz):raise UnknownDeathPickup139('FiniteXYZ')
 cx,cy,radius=ZONE_GEOMETRY139[0];x,y=xyz[:2];dx,dy=f.sub(x,cx),f.sub(y,cy);distance=hypot_bits(dx,dy);limit=f.add(radius,0xc0000000)
 if f.to_float(distance)>f.to_float(limit):x=f.add(cx,f.mul(f.div(dx,distance),limit));y=f.add(cy,f.mul(f.div(dy,distance),limit))
 height=world.height(x,y)
 if height.found:z=height.value_bits
 elif world.primary is None:z=world.fallback_height_bits
 else:raise UnknownDeathPickup139('Currentno-primaryworldrequiredonmiss')
 return(x,y,z)

def _xp_packet(guid,xyz,amount):
 scale=0x3f666666 if amount>19 else 0x3eb33333 if amount>3 else 0x3e6147ae;display=16587 if amount>19 else 1825
 fields={0:guid&f.MASK,1:guid>>32,2:9,3:9001,4:scale,22:1,28:1,34:1,35:35,46:33554434,129:1036831949,130:1036831949,131:display,132:display}
 speeds=(1075838976,1088421888,1083179008,1083645041,1075838976,1078530011)
 payload=(struct.pack('<IB',1,0)+bytes([3])+_packguid(guid)+bytes([3,112])+struct.pack('<2I',0,0)+struct.pack('<4I',*xyz,0)+struct.pack('<I',0)+struct.pack('<6I',*speeds)+struct.pack('<I',1)+_values(fields))
 return(169,payload.hex())

def _coin_actor(counter,words,xyz):
 counter=(counter+1)&f.MASK;guid=0xf110000000000000|(9004<<24)|(counter&0xffffff)
 angle=uniform_range_bits(words,0,0x40c90fdb);yaw=f.add(angle.bits,0);half=f.mul(yaw,0x3f000000)
 fields={0:guid&f.MASK,1:guid>>32,2:33,3:9004,4:0x3f19999a,8:2614,9:0,12:sin_bits(half),13:cos_bits(half),14:1,15:xyz[0],16:xyz[1],17:xyz[2],18:yaw,20:35,21:5}
 packet=(struct.pack('<IB',1,0)+bytes([2])+_packguid(guid)+bytes([5,80])+struct.pack('<4I',*xyz,yaw)+struct.pack('<I',1)+_values(fields))
 return counter,tuple(angle.state),guid,(169,packet.hex()),angle.draws

@dataclass(frozen=True)
class PickupAppendResult139:
 vector:PickupVector139
 counter:int
 rng_words:tuple
 packets:tuple
 position_bits:tuple
 guid:int|None
 merged_index:int|None
 draws:int

def append_death_pickup139(kind,amount,xyz,world,words,counter,now_bits,*,vector=None):
 if kind not in(0,1):raise UnknownDeathPickup139('Only1446kind0or1')
 for x in(amount,counter,now_bits,*xyz,*words):uint139(x)
 if len(words)!=4:raise ValueError('FourRNGwords')
 vector=PickupVector139(())if vector is None else vector
 if not isinstance(vector,PickupVector139):raise TypeError('PickupVector139')
 placed=pickup_geometry139(xyz,world)
 if kind==0:
  idle=[]
  for i in range(vector.count):
   row=vector.storage[i]
   if word139(row,8)==0:
    marker=word139(row,0)
    if marker not in(0,1):raise UnknownDeathPickup139('Canonicallivepickupmarkers0or1')
    if marker==0:idle.append(i)
  if len(idle)>=45:
   def dist(i):
    row=vector.storage[i];dx,dy=f.sub(word139(row,40),placed[0]),f.sub(word139(row,44),placed[1]);return f.add(f.mul(dx,dx),f.mul(dy,dy))
   index=min(idle,key=lambda i:f.to_float(dist(i)));rows=list(vector.storage);row=list(rows[index]);row[12:16]=struct.pack('<I',(word139(row,12)+amount)&f.MASK);rows[index]=tuple(row)
   return PickupAppendResult139(PickupVector139(tuple(rows),vector.count),counter,tuple(words),(),placed,None,index,0)
  counter=(counter+1)&f.MASK;guid=0xf130002329000000|(counter&0xffffff);packets=(_xp_packet(guid,placed,amount),);draws=0;visual=9001
 else:
  counter,words,guid,packet,draws=_coin_actor(counter,tuple(words),placed);packets=(packet,);visual=9004
 writes=((0,struct.pack('<I',0)),(8,struct.pack('<IIQ',kind,amount,guid)),(24,struct.pack('<4I',0,8,0,visual)),(40,struct.pack('<4I',*placed,now_bits)))
 return PickupAppendResult139(_append(vector,writes),counter,tuple(words),packets,placed,guid,None,draws)
