"""WIP current139952 wave2424, source-rebound default mode0/Elwynn.

Algorithm ported from the older pure specification only after rebinding current
952/5719/1586 and geometry/math helpers. No old runtime acceptance transfers.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .rng import next_u32_words,uniform_range_bits
from .spawn_geometry135 import hypot_bits
from .ai_trig135 import sin_bits,cos_bits
from .npc_heading139 import atan2_bits
from .progression134 import trunc_sat_u32
@dataclass(frozen=True)
class WaveVector139:
 stride:int
 storage:tuple
 count:int
 def __post_init__(self):
  if self.stride!=432 or not 0<=self.count<=len(self.storage)<=4096:raise ValueError('Complete bounded NPC432 storage required')
  if any(len(r)!=432 for r in self.storage):raise ValueError('Full432 physical rows required')
 @property
 def capacity(self):return len(self.storage)
from .opening_aux139_data import CENTER_XY_BITS,RADIUS_BITS
from .spawn_schedule139_v2 import DEFS,word,choose_normal139,_npc139
from .spawn_wave139_data import NORMAL_NAMES139
ZONE_GEOMETRY=((*CENTER_XY_BITS,RADIUS_BITS),)

def u32(row,at,label='word'):return word(row,at)
def u64(row,at,label='guid'):
 b=tuple(row[at:at+8])
 if len(b)!=8 or None in b:raise ValueError('Consumed unknown GUID')
 return int.from_bytes(bytes(b),'little')
def put_u32(row,at,v):row[at:at+4]=struct.pack('<I',v)
def eligible_normals(zone,minute):
 if zone!=0:raise NotImplementedError('Current default zone only')
 return tuple(i for i,d in enumerate(DEFS)if d[68]==0 and f.to_float(word(d,64))<=f.to_float(minute))
def definition(zone,index):
 d=DEFS[index]
 return dict(cost_bits=word(d,60),field52_bits=word(d,52),entry=word(d,24),name=NORMAL_NAMES139[index])
@dataclass(frozen=True)
class Choice139:
 index:int
 rng_words:tuple
 draws:int
def choose_spawn(zone,candidates,minute,words):
 index,words,n=choose_normal139(candidates,minute,words);return Choice139(index,tuple(words),n)
MESSAGES139=(b'Swarm surrounds you!',b'A stampede charges through!',b'A wall of foes closes in!',b'A pack hunts you!')
CONSTRUCTOR_LAST_EVENT2586=255  #1560 scratch2674, copied from scratch+88 toG2586.
TAU=0x40c90fdb

class PendingEventWave139(NotImplementedError):pass

@dataclass(frozen=True)
class EventWaveLocale139:
    """Explicit already-selected dictionary values; None means lookup miss."""
    language_index:int
    enemy_names:tuple=()
    messages:tuple=()
    def resolve(self,key,fallback):
        values=dict(self.enemy_names if key.startswith(b'enemy.')else self.messages)
        value=values.get(key)
        return fallback if value is None else value

@dataclass(frozen=True)
class EventWaveInput139:
    zone:int
    now_bits:int
    next_event2424_bits:int
    last_event2586:int
    player_xyz_bits:tuple
    velocity_xy:tuple
    rng_words:tuple
    counter:int
    message_sequence:int
    units:WaveVector139
    player_guid:int
    level1432:int
    zone_multiplier_bits:int
    difficulty:int=0
    mode:int=0
    members:int|None=None
    victory_field400:int=0
    endless_flag:int=0
    endless_start_bits:int|None=None
    distance_map:object|None=None

@dataclass(frozen=True)
class EventWaveResult139:
    status:str
    next_event2424_bits:int
    last_event2586:int
    units:WaveVector139
    rng_words:tuple
    counter:int
    message_sequence:int
    packets:tuple=()
    creates:tuple=()
    event:int|None=None
    definition_index:int|None=None
    requested:int=0
    draws:int=0
    positions:tuple=()
    charged_guids:tuple=()


def _word(v):
    if type(v)is not int or not 0<=v<=f.MASK:raise ValueError('Explicit unsigned32 required')
    return v

def _finite(v):
    _word(v)
    if v&0x7fffffff>=f.INF:raise ValueError('Finite event wave input required')
    return v

def _index(words,count):
    if count<1:raise ValueError('Empty event selection is not a successful path')
    # Exact multiply-high range rejection: n<<(clz(n))-1, not modulo bias.
    mask=((count<<(32-count.bit_length()))-1)&f.MASK
    for draws in range(1,100001):
        output,words=next_u32_words(words);product=output*count
        if(product&f.MASK)<=mask:return product>>32,words,draws
    raise RuntimeError('Event index independent RNG watchdog')


def probe_event_position139(value,world,x,y,*,inline=False):
    """31520/inlined event probe: no RNG and no invented height fallback."""
    cx,cy,limit=ZONE_GEOMETRY[value.zone]
    distance=hypot_bits(f.sub(x,cx),f.sub(y,cy))
    if f.to_float(distance)>f.to_float(f.add(limit,0x41900000)):return None
    hit=world.height(x,y)
    if not hit.found:return None
    threshold=8 if f.to_float(distance)>f.to_float(limit)else 25
    if f.to_float(f.sub(hit.value_bits,value.player_xyz_bits[2])&~f.SIGN)>threshold:return None
    nav=world.nav_probe(x,y);path=value.distance_map
    if nav.present:
        if path is None:
            if nav.in_bounds and(nav.value==1 if inline else bool(nav.value)):return None
        else:
            if nav.in_bounds and nav.value:return None
            if path.field24>=401:
                if not nav.in_bounds:return None
                if nav.index>=len(path.values_u16):raise PendingEventWave139('Actual distance map index bounds')
                cost=path.values_u16[nav.index]
                maximum=f.add(f.mul(hypot_bits(f.sub(x,value.player_xyz_bits[0]),f.sub(y,value.player_xyz_bits[1])),0x3fc00000),0x41400000)
                if cost==65535 or f.to_float(f.from_u32(cost))>f.to_float(maximum):return None
    return x,y,hit.value_bits


def _packet150(name,message):
    if not isinstance(name,bytes)or not isinstance(message,bytes):raise ValueError('Explicit UTF8 event input required')
    name.decode('utf8');message.decode('utf8')
    return (bytes((90,))+struct.pack('<II',0,len(name)+1)+name+b'\0'+bytes(8)+struct.pack('<I',len(message)+1)+message+b'\0\0').hex()


def step_event_wave139(value:EventWaveInput139,world,*,locale=None):
    for x in(value.now_bits,value.next_event2424_bits,value.zone_multiplier_bits,*value.player_xyz_bits,*value.velocity_xy):_finite(x)
    for x in(*value.rng_words,value.counter,value.message_sequence,value.level1432):_word(x)
    if len(value.rng_words)!=4 or len(value.player_xyz_bits)!=3 or len(value.velocity_xy)!=2:raise ValueError('Explicit RNG/XYZ/velocity lengths required')
    if not 0<=value.zone<len(ZONE_GEOMETRY)or not 0<=value.last_event2586<=255:raise ValueError('Explicit zone/previous event byte required')
    if not isinstance(value.units,WaveVector139)or value.units.stride!=432:raise ValueError('Complete physical432B unit vector required')
    def result(status,**extra):
        return EventWaveResult139(status,deadline,event_byte,units,words,counter,value.message_sequence,tuple(packets),tuple(creates),**extra)
    deadline=value.next_event2424_bits;event_byte=value.last_event2586;units=value.units;words=value.rng_words;counter=value.counter;packets=[];creates=[]
    if not f.to_float(value.now_bits)>=f.to_float(deadline):return result('event2424_future')
    if value.mode!=0:raise PendingEventWave139('Mode1 event scale/party owner input remains unvalidated')
    if value.victory_field400==1 and value.endless_flag&1:
        if value.endless_start_bits is None:raise PendingEventWave139('Consumed endless start404 requires actual producer')
        _finite(value.endless_start_bits)
    minute=f.div(value.now_bits,0x42700000);delay=f.add(f.mul(minute,0xbfc00000),0x42700000)
    delay=delay if f.to_float(delay)>35 else 0x420c0000;deadline=f.add(value.now_bits,delay)
    eligible=eligible_normals(value.zone,minute)
    if not eligible:return result('event2424_no_eligible')
    if world is None or not all(callable(getattr(world,k,None))for k in('height','nav_probe')):raise PendingEventWave139('Actual world query provider required')
    if not isinstance(locale,EventWaveLocale139):raise PendingEventWave139('Explicit already-initialized selected locale input required')
    choices=tuple(i for i in range(4)if i!=event_byte);selected,words,draws=_index(words,len(choices));event_byte=choices[selected]
    cheap=tuple(i for i in eligible if f.to_float(definition(value.zone,i)['cost_bits'])<=f.to_float(0x3f99999a))or eligible
    selected,words,n=_index(words,len(cheap));draws+=n;index=cheap[selected]
    scale=0x3f19999a;positions=[];charged=[]
    def uniform(low=0,high=TAU):
        nonlocal words,draws
        x=uniform_range_bits(words,low,high);words=x.state;draws+=x.draws;return f.add(x.bits,0)
    def append(xyz):
        nonlocal units,words,counter,draws
        if units.count>=50:return None
        rows=list(units.storage)
        if units.count==len(rows):rows.extend([(None,)*432]*(max(4,2*len(rows))-len(rows)))
        row,words,counter,packet,n=_npc139(index,value.now_bits,xyz,value.player_xyz_bits,words,counter,rows[units.count])
        rows[units.count]=row;units=WaveVector139(432,tuple(rows),units.count+1);draws+=n
        guid=u64(row,112);creates.append((units.count-1,index,str(guid)));packets.append(packet);positions.append(xyz)
        return guid
    def radial(theta,radii,*,inline=False):
        sine,cosine=sin_bits(theta),cos_bits(theta)
        for radius in radii:
            xyz=probe_event_position139(value,world,f.add(value.player_xyz_bits[0],f.mul(cosine,f.from_u32(radius))),f.add(value.player_xyz_bits[1],f.mul(sine,f.from_u32(radius))),inline=inline)
            if xyz is not None:return xyz
        return None
    moving=f.to_float(f.add(f.mul(value.velocity_xy[0],value.velocity_xy[0]),f.mul(value.velocity_xy[1],value.velocity_xy[1])))>4
    if event_byte==0:
        count=max(1,trunc_sat_u32(f.mul(f.add(f.mul(minute,0x40200000),0x41400000),scale)))
        for i in range(count):
            theta=f.mul(f.div(f.from_u32(i),f.from_u32(count)),TAU);xyz=radial(theta,range(26,7,-2),inline=True)
            if xyz is not None:append(xyz)
    elif event_byte==3:
        choice=choose_spawn(value.zone,eligible,minute,words);index=choice.index;words=choice.rng_words;draws+=choice.draws
        theta=uniform();anchor=radial(theta,range(32,13,-2))
        count=max(2,trunc_sat_u32(f.mul(f.add(f.mul(minute,0x3f4ccccd),0x40a00000),scale)))
        if anchor is None:return result('event2424_anchor_failed',event=event_byte,definition_index=index,requested=count,draws=draws)
        for i in range(count):
            fi=f.from_u32(i);angle=f.mul(fi,0x4019999a);radius=f.add(f.mul(sqrt_bits(fi),0x3fcccccd),0x3f800000)
            xyz=probe_event_position139(value,world,f.add(anchor[0],f.mul(cos_bits(angle),radius)),f.add(anchor[1],f.mul(sin_bits(angle),radius)))
            append(anchor if xyz is None else xyz)
    else:
        count=max(1,trunc_sat_u32(f.mul(f.add(f.add(minute,minute),0x41200000),scale)))
        if event_byte==1:
            # All retained static field52 values are finite positive. Equal speeds pick the later pool row.
            index=cheap[0]
            for other in cheap[1:]:
                if not f.to_float(definition(value.zone,index)['field52_bits'])>f.to_float(definition(value.zone,other)['field52_bits']):index=other
            if moving:
                output,words=next_u32_words(words);draws+=1
                theta=f.add(f.add(atan2_bits(value.velocity_xy[1],value.velocity_xy[0]),0x3fc8f5c3 if output&f.SIGN else 0xbfc8f5c3),uniform(0xbecccccd,0x3ecccccd))
            else:theta=uniform()
            anchor=radial(f.add(theta,0x40490fdb),range(34,13,-2))
            if anchor is None:return result('event2424_anchor_failed',event=event_byte,definition_index=index,requested=count,draws=draws)
            sine,cosine=sin_bits(theta),cos_bits(theta);distance=hypot_bits(f.sub(anchor[0],value.player_xyz_bits[0]),f.sub(anchor[1],value.player_xyz_bits[1]));travel_distance=f.add(f.add(distance,distance),0x41400000)
            speed=f.mul(f.mul(definition(value.zone,index)['field52_bits'],0x3f866666),0x3fb33333);speed=speed if f.to_float(speed)>1 else 0x3f800000;travel=f.div(travel_distance,speed)
            columns=(count+1)//2;center=f.mul(f.sub(f.from_u32(columns),0x3f800000),0x3f000000)
            for i in range(count):
                row,column=divmod(i,columns);lateral=f.mul(f.sub(f.from_u32(column),center),0x40266666)
                x=f.sub(f.sub(anchor[0],f.mul(sine,lateral)),f.mul(f.mul(cosine,f.from_u32(row)),0x40400000));y=f.sub(f.add(anchor[1],f.mul(cosine,lateral)),f.mul(f.mul(sine,f.from_u32(row)),0x40400000))
                xyz=probe_event_position139(value,world,x,y)
                if xyz is None:continue
                guid=append(xyz)
                if guid is not None:
                    rows=list(units.storage);found=next(j for j,r in enumerate(rows[:units.count])if u64(r,112,'Stampede GUID owner')==guid);r=list(rows[found])
                    for offset,bits in((16,1),(20,f.add(xyz[0],f.mul(cosine,travel_distance))),(24,f.add(xyz[1],f.mul(sine,travel_distance))),(28,f.add(f.add(travel,value.now_bits),0x40400000)),(348,value.now_bits)):put_u32(r,offset,bits)
                    rows[found]=tuple(r);units=WaveVector139(432,tuple(rows),units.count);charged.append(guid)
        else:
            theta=atan2_bits(value.velocity_xy[1],value.velocity_xy[0])if moving else uniform();start=f.sub(theta,0x3f99999a)
            for i in range(count):
                angle=f.add(start,f.div(f.mul(f.add(f.from_u32(i),0x3f000000),0x4019999a),f.from_u32(count)));xyz=radial(angle,range(30,11,-2),inline=True)
                if xyz is not None:append(xyz)
    desc=definition(value.zone,index);key=b'enemy.'+str(desc['entry']).encode();name=locale.resolve(key,desc['name'].encode());message=locale.resolve(MESSAGES139[event_byte],MESSAGES139[event_byte]);packets.append((150,_packet150(name,message)))
    return result('event2424_complete',event=event_byte,definition_index=index,requested=count,draws=draws,positions=tuple(positions),charged_guids=tuple(charged))
