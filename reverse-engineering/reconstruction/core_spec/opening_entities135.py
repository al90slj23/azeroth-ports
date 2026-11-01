"""Independent default-mode135 opening entity, window and geometry producers.

World query results come from an explicit pure provider. This module performs
no file/host/original access. Unknown allocator bytes are None, never zero.
Profile selection/world production, NPC/kind2 and multiplayer entry are separate.
"""
from dataclasses import dataclass
import math
import struct
from . import binary32 as f
from .ai_trig135 import sin_bits,cos_bits
from .spawn_geometry135 import hypot_bits
from .rng import next_u32_words,uniform_range_bits
from .spawn135_data import NORMALS
from .spawn_position135_data import ZONE_GEOMETRY
from .opening_entities135_data import ZONE_OPENING

TAU=0x40c90fdb
BASE_SPEEDS=(1075838976,1088421888,1083179008,1083645041,1075838976,1078530011)


class UnknownOpeningEntities135(NotImplementedError):pass


def _u(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:raise ValueError('Exact unsigned word required')
    return value


@dataclass(frozen=True)
class PhysicalVector135:
    stride:int
    storage:tuple
    count:int=0

    def __post_init__(self):
        if self.stride not in(8,40,88)or not 0<=self.count<=len(self.storage)<=4096:raise ValueError('Explicit physical vector required')
        for row in self.storage:
            if len(row)!=self.stride or any(x is not None and(type(x)is not int or not 0<=x<256)for x in row):raise ValueError('Exact record backing bytes required')

    @property
    def capacity(self):return len(self.storage)


def vector_from_hex(stride,storage,count):
    return PhysicalVector135(stride,tuple(tuple(bytes.fromhex(x))for x in storage),count)


def _append(vector,writes):
    rows=list(vector.storage)
    if vector.count==len(rows):rows.extend([(None,)*vector.stride]*(max(4,2*len(rows))-len(rows)))
    row=list(rows[vector.count])
    for offset,data in writes:row[offset:offset+len(data)]=data
    rows[vector.count]=tuple(row)
    return PhysicalVector135(vector.stride,tuple(rows),vector.count+1)


def packed_guid(guid):
    _u(guid,64);raw=guid.to_bytes(8,'little');mask=sum(1<<i for i,x in enumerate(raw)if x)
    return bytes([mask])+bytes(x for x in raw if x)


def _values(fields):
    rows=dict(fields)
    if any(type(k)is not int or not 0<=k<8160 for k in rows):raise ValueError('Bounded u16 object keys required')
    for value in rows.values():_u(value)
    words=max(rows,default=-1)//32+1;masks=[0]*words
    for key in rows:masks[key//32]|=1<<(key%32)
    return bytes([words])+struct.pack('<'+'I'*words,*masks)+b''.join(struct.pack('<I',rows[k])for k in sorted(rows))


def _with_guid(guid,fields):
    values={0:guid&f.MASK,1:guid>>32};values.update(fields)
    return tuple(sorted(values.items()))


def unit_create169(guid,xyz,heading,speeds,fields):
    """Full10823→50798 payload for kind3/selfFlag0, not all movement variants."""
    if len(xyz)!=3 or len(speeds)!=6:raise ValueError('Exact position/speed tuple required')
    return (struct.pack('<IB',1,0)+bytes([3])+packed_guid(guid)+bytes([3,112])+
        struct.pack('<2I',0,0)+struct.pack('<4I',*xyz,heading)+struct.pack('<I',0)+
        struct.pack('<6I',*speeds)+struct.pack('<I',1)+_values(fields))


def actor_create169(guid,xyz,heading,fields):
    """Full26970→50798 payload for kind5, fixed0x50 movement flags."""
    if len(xyz)!=3:raise ValueError('Exact XYZ required')
    return (struct.pack('<IB',1,0)+bytes([2])+packed_guid(guid)+bytes([5,80])+
        struct.pack('<4I',*xyz,heading)+struct.pack('<I',1)+_values(fields))


@dataclass(frozen=True)
class LogicalCreate135:
    guid:int
    kind:int
    position_bits:tuple
    heading_bits:int
    fields:tuple
    payload169_hex:str


@dataclass(frozen=True)
class ActorResult135:
    create:LogicalCreate135
    counter:int
    rng_words:tuple
    draws:int


def create_world_actor(entry,display,scale_bits,xyz,kind21,flags9,counter,rng_words):
    """Complete1821 logical fields, angle/RNG, GUID and exact169 payload."""
    for word in(entry,display,scale_bits,kind21,flags9,counter,*xyz):_u(word)
    counter=(counter+1)&f.MASK;guid=0xf110000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
    angle=uniform_range_bits(rng_words,0,TAU);yaw=f.add(angle.bits,0);half=f.mul(yaw,0x3f000000)
    fields=_with_guid(guid,{2:33,3:entry,4:scale_bits,8:display,9:flags9,12:sin_bits(half),13:cos_bits(half),
        14:1,15:xyz[0],16:xyz[1],17:xyz[2],18:yaw,20:35,21:kind21})
    create=LogicalCreate135(guid,5,tuple(xyz),yaw,fields,actor_create169(guid,xyz,yaw,fields).hex())
    return ActorResult135(create,counter,angle.state,angle.draws)


def _height_or_fallback(world,x,y):
    value=world.height(x,y)
    if value.found:return value.value_bits
    nearest=world.nearest_primary(x,y)
    return nearest.xyz_bits[2]if nearest.found else world.fallback_height_bits


@dataclass(frozen=True)
class CompanionSlot135:
    pointer:int
    tag:int
    entry40:int
    display32:int
    scale36_bits:int

    def __post_init__(self):
        _u(self.tag,8)
        for x in(self.pointer,self.entry40,self.display32,self.scale36_bits):_u(x)


@dataclass(frozen=True)
class CompanionResult135:
    vector:PhysicalVector135
    counter:int
    creates:tuple


def create_companions(slots,player_xyz,heading,now_bits,stat1556_bits,rank273,counter,world,
                      vector=None,protection2576=0):
    """Complete1744 producer from two explicit inline equipment declarations."""
    if len(slots)!=2 or any(not isinstance(x,CompanionSlot135)for x in slots):raise ValueError('Two inline8B slot declarations required')
    vector=vector or PhysicalVector135(88,());_u(rank273,8);_u(protection2576,8);_u(counter)
    if vector.stride!=88:raise ValueError('Companion backing must be88B')
    if protection2576:return CompanionResult135(vector,counter,())
    stat=0x3f800000 if f.is_nan(stat1556_bits)or not f.to_float(stat1556_bits)>1 else stat1556_bits
    speeds=list(BASE_SPEEDS);speeds[1]=f.mul(stat,f.mul(f.add(f.mul(f.from_u32(rank273),0x3e4ccccd),0x3f800000),0x41600000))
    creates=[]
    for index,slot in enumerate(x for x in slots if x.tag!=255):
        relative=f.mul(f.add(f.mul(f.from_u32(index),0x3eb33333),0x3f933333),0x40490fdb)
        absolute=f.add(relative,heading);co,si=cos_bits(absolute),sin_bits(absolute)
        x=f.add(player_xyz[0],f.add(co,co));y=f.add(player_xyz[1],f.add(si,si));z=_height_or_fallback(world,x,y)
        xyz=(x,y,z);counter=(counter+1)&f.MASK;guid=0xf130000000000000|((slot.entry40&0xffffff)<<24)|(counter&0xffffff)
        fields=_with_guid(guid,{2:9,3:slot.entry40,4:slot.scale36_bits,22:1,28:1,34:1,35:35,46:33554434,
             129:1050253722,130:1056964608,131:slot.display32,132:slot.display32,145:0x3f800000})
        payload=unit_create169(guid,xyz,heading,tuple(speeds),fields).hex()
        creates.append(LogicalCreate135(guid,3,xyz,heading,fields,payload))
        vector=_append(vector,((0,struct.pack('<2I',0,f.add(now_bits,0x3f800000))),(16,struct.pack('<I',slot.pointer)),
            (20,bytes([slot.tag])),(24,struct.pack('<Q',guid)),(32,struct.pack('<3I',0,4,0)),
            (44,struct.pack('<3I',*xyz)),(56,struct.pack('<3I',*xyz)),(68,struct.pack('<5I',now_bits,0,now_bits,relative,now_bits))))
    return CompanionResult135(vector,counter,tuple(creates))


@dataclass(frozen=True)
class WindowResult135:
    vector:PhysicalVector135
    rng_words:tuple
    count_draws:int
    window_draws:int


def create_opening_windows(zone,rng_words,vector=None):
    """Actual2..3 event windows, absolute time, no counter or entity writes."""
    vector=vector or PhysicalVector135(8,())
    if vector.stride!=8:raise ValueError('Window records are8B')
    words=tuple(rng_words);count_draws=0
    while True:
        output,words=next_u32_words(words);count_draws+=1;product=output*2
        if(product&f.MASK)<=0x7fffffff:count=2+(product>>32);break
        if count_draws>100000:raise UnknownOpeningEntities135('Independent RNG watchdog')
    width=f.div(f.mul(ZONE_OPENING[zone][6],0x42700000),f.from_u32(count))
    vector=PhysicalVector135(8,vector.storage,0);draws=0
    for i in range(count):
        value=uniform_range_bits(words,0x3f19999a,0x3f800000);words=value.state;draws+=value.draws
        start=f.mul(width,f.from_u32(i));end=f.add(start,f.mul(width,value.bits))
        vector=_append(vector,((0,struct.pack('<2I',start,end)),))
    return WindowResult135(vector,words,count_draws,draws)


def boundary_candidates(zone):
    """Circle except WSG/SM, whose exact static polygons are interpolated."""
    _,_,_,_,_,polygon,_=ZONE_OPENING[zone];cx,cy,radius=ZONE_GEOMETRY[zone]
    if zone in(2,7):
        result=[]
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            dx,dy=f.sub(b[0],a[0]),f.sub(b[1],a[1]);n=max(1,math.ceil(f.to_float(f.div(hypot_bits(dx,dy),0x41400000))))
            for i in range(n):
                t=f.div(f.from_u32(i),f.from_u32(n));result.append((f.add(a[0],f.mul(dx,t)),f.add(a[1],f.mul(dy,t))))
        return tuple(result)
    radius=f.add(radius,0x41200000);count=math.ceil(f.to_float(f.div(f.mul(radius,TAU),0x41400000)));result=[]
    for i in range(count):
        angle=f.div(f.mul(f.from_u32(i),TAU),f.from_u32(count))
        result.append((f.add(cx,f.mul(radius,cos_bits(angle))),f.add(cy,f.mul(radius,sin_bits(angle)))))
    return tuple(result)


@dataclass(frozen=True)
class BoundaryResult135:
    vector:PhysicalVector135
    counter:int
    rng_words:tuple
    draws:int
    creates:tuple
    skipped_positions:tuple


def create_boundaries(zone,world,counter,rng_words,vector=None):
    vector=vector or PhysicalVector135(8,());cx,cy,_=ZONE_GEOMETRY[zone];flag=ZONE_OPENING[zone][2]
    creates=[];skipped=[];words=tuple(rng_words);draws=0
    for x,y in boundary_candidates(zone):
        sample=world.height(x,y)
        if not sample.found and flag:skipped.append((x,y));continue
        z=sample.value_bits if sample.found else _height_or_fallback(world,x,y)
        if flag:
            dx,dy=f.sub(cx,x),f.sub(cy,y);distance=hypot_bits(dx,dy)
            if f.is_nan(distance)or not f.to_float(distance)>f.to_float(0x3c23d70a):distance=0x3c23d70a
            probe=world.nav_probe(f.add(x,f.div(dx,distance)),f.add(y,f.div(dy,distance)))
            if probe.present and probe.in_bounds and probe.value:skipped.append((x,y));continue
        actor=create_world_actor(9013,4831,0x3f800000,(x,y,z),5,16,counter,words)
        counter,words=actor.counter,actor.rng_words;draws+=actor.draws;creates.append(actor.create)
        vector=_append(vector,((0,struct.pack('<Q',actor.create.guid)),))
    return BoundaryResult135(vector,counter,words,draws,tuple(creates),tuple(skipped))


def _special_blocked(world,x,y):
    # The first13 queries are LLVM-inlined bool loads; remaining12 call60939
    # and retain its low-bit normalization. Canonical game grids are0/1.
    index=0
    for dx in range(-2,3):
        for dy in range(-2,3):
            q=world.nav_probe(f.add(x,f.from_float(dx)),f.add(y,f.from_float(dy)))
            if q.present and q.in_bounds:
                blocked=q.value==1 if index==0 else(bool(q.value)if index<13 else bool(q.value&1))
                if blocked:return True
            index+=1
    return False


def create_special_records(zone,world,vector=None):
    """1089 four40B delayed-elite declarations, without entity/RNG writes."""
    vector=vector or PhysicalVector135(40,());radius,heading,_,corners,explicit,_,_=ZONE_OPENING[zone];cx,cy,_=ZONE_GEOMETRY[zone]
    eligible=explicit if zone==11 else tuple(row[0]for row in NORMALS[zone]if row[14]==1 and(row[13]&~f.SIGN)<f.INF)
    if not eligible:return vector
    centre_z=_height_or_fallback(world,cx,cy)
    coefficients=(0x3f333333,0x3f1eb852,0x3f0a3d71,0x3eeb851f,0x3ec28f5c)
    for i in range(4):
        angle=f.add(f.mul(f.mul(f.from_u32(i),TAU),0x3e800000),f.add(heading,0x3f490fdb));co,si=cos_bits(angle),sin_bits(angle)
        declared=next((p for p in corners if p[0]==i),None);xyz=None
        if declared is not None:
            x,y=declared[1:];xyz=(x,y,_height_or_fallback(world,x,y))
        else:
            for coefficient in coefficients:
                distance=f.mul(radius,coefficient);x=f.add(cx,f.mul(co,distance));y=f.add(cy,f.mul(si,distance))
                if _special_blocked(world,x,y):continue
                sample=world.height(x,y)
                if sample.found and f.to_float(f.sub(sample.value_bits,centre_z)&~f.SIGN)<30:xyz=(x,y,sample.value_bits);break
            if xyz is None:
                distance=f.mul(radius,0x3f000000);x=f.add(cx,f.mul(distance,co));y=f.add(cy,f.mul(distance,si));xyz=(x,y,_height_or_fallback(world,x,y))
        vector=_append(vector,((0,struct.pack('<Q',0)),(16,struct.pack('<3I',*xyz)),(28,struct.pack('<2I',eligible[i%len(eligible)],0x41a00000))))
    return vector


def start_banner150(title,subtitle):
    """17979 successful UTF8 packet payload; caller resolves locale strings."""
    if not isinstance(title,bytes)or not isinstance(subtitle,bytes):raise ValueError('Resolved UTF8 bytes required')
    title.decode('utf8');subtitle.decode('utf8')
    return (bytes([90])+struct.pack('<2I',0,len(title)+1)+title+b'\0'+bytes(8)+struct.pack('<I',len(subtitle)+1)+subtitle+b'\0\0')
