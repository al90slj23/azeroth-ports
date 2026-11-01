"""Independent fixed135 raw9 NPC-action producer and rectangular120B consumer.

The supported declarations are actual40B Boss records, not inferred spell IDs.
Only the normal0/type0/shape2 family is implemented. Full physical storage is
retained; the producer copies an unspecified scratch word into record+20, which
is represented explicitly rather than read from an original result. Wire bytes,
effect JSON serialization and incoming registry/history/procs remain pending.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .spawn_heading135 import atan2_bits
from .spawn_geometry135 import cos_bits,sin_bits,hypot_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .spawn135 import max_numeric
from .ai135 import position,unit_position
from .incoming135 import IncomingState135,resolve_incoming_prefix

RECTANGLE_DECLARATIONS=(
    ('Tendris Warpwood',5,5433104,'c01500000000f0410000a0403333b33fcdcc0c400000000000000000000000000000000000090000'),
    ("Anub'Rekhan",11,5453396,'6f7000000000f0410000a0403333b33f9a9919400000000000000000000000000000000000090000'),
    ('Patchwerk',11,5454132,'946e0000000040410000c0400000803f000040400000000000000000000000000000000000090000'),
)
ONE=0x3f800000


def get(raw,o):return struct.unpack_from('<I',raw,o)[0]
def put(raw,o,v):struct.pack_into('<I',raw,o,v)
def val(raw,o):return f.to_float(get(raw,o))
def finite(v):return -1e20<f.to_float(v)<1e20


@dataclass(frozen=True)
class Effect120135:
    raw_hex:str
    unspecified_bytes:tuple=()

    def __post_init__(self):
        if len(bytes.fromhex(self.raw_hex))!=120:raise ValueError('Full120B effect record required')
        if self.unspecified_bytes not in((),(20,21,22,23)):
            raise ValueError('Only the genuine raw9 producer scratch+444 word may be unspecified')


@dataclass(frozen=True)
class EffectGeometryState135:
    storage:tuple
    length:int
    units:tuple
    now_bits:int
    zone:int
    player_xyz_bits:tuple
    incoming:IncomingState135
    effect_counter2356:int=0
    movement_sequence2412:int=0
    action_sequence1644:int=1
    clock2364_bits:int=0
    rng_words:tuple=(1,2,3,4)
    spawn_counter2408:int=0
    difficulty387:int=0
    endless2568:int=0
    mode2582:int=0
    local_peer2528:int=0
    player_flags2496:int=0
    flat_height_bits:int=0
    flat_height_enabled:bool=True
    delayed_records56:tuple=()
    terrain_grid_absent:bool=False
    collision_grid_absent:bool=False
    navigation_absent:bool=False
    other_incoming_sources_absent:bool=False
    entry_pending:bool=False

    @property
    def records(self):return self.storage[:self.length]


@dataclass(frozen=True)
class EffectGeometryResult135:
    state:EffectGeometryState135
    events:tuple
    damage_bits:int=0
    pending:tuple=('encoded_packets','effect_JSON_serialization','incoming_registry_history_aura_metadata')
    status:str='normal_rectangle_projection'


class PendingEffectGeometry135(ValueError):
    def __init__(self,state,reason):super().__init__(reason);self.state=state


def validate(s):
    def reject(reason):raise PendingEffectGeometry135(s,reason)
    if s.entry_pending:reject('An interrupted original entry cannot be resumed as a complete state')
    if any(type(x)is not int or not 0<=x<=f.MASK for x in(s.effect_counter2356,s.movement_sequence2412,s.action_sequence1644,s.spawn_counter2408,*s.rng_words)):
        reject('Explicit u32 counters/RNG required')
    if len(s.rng_words)!=4 or any(type(x)is not int or not 0<=x<=255 for x in(s.difficulty387,s.endless2568)):
        reject('Four RNG words and byte flags required')
    if not 0<=s.length<=len(s.storage)<=64 or len(s.units)>128:reject('Storage budget')
    if not 0<=s.zone<12 or len(s.player_xyz_bits)!=3:reject('Zone/input shape')
    if any(not isinstance(x,Effect120135)for x in s.storage):reject('Explicit full storage required')
    if any(len(bytes.fromhex(x))!=424 for x in s.units):reject('Full424B units required')
    if s.player_flags2496!=0:reject('Player movement prediction remains unresolved')
    if s.mode2582!=0:reject('Remote owner routing remains unresolved')
    if not all((s.terrain_grid_absent,s.collision_grid_absent,s.navigation_absent)):reject('World geometry remains unresolved')
    if s.other_incoming_sources_absent is not True:reject('Explicit empty incoming producers required')
    if s.delayed_records56:reject('Compose the delayed56 consumer separately; no silent queue deletion')
    if s.incoming.buffs or s.incoming.modifiers or f.to_float(s.incoming.reserve_768_bits)>0:
        reject('Buff/modifier/reserve producer boundary')
    if s.incoming.shield_source_1344:reject('Named shield/aura source boundary')
    if s.clock2364_bits!=0:reject('Compose clock2364 separately')
    if any(not finite(x)for x in(s.now_bits,s.flat_height_bits,*s.player_xyz_bits)):
        reject('Finite bounded world inputs required')


def predicted_player(s):
    x,y,z=s.player_xyz_bits
    #4865 Boss prediction, flags0, no collision/height grids. Zone clamp occurs
    #before the zero-velocity anticipation length check (<.05).
    cx,cy,rad=ZONE_GEOMETRY[s.zone];dx=f.sub(x,cx);dy=f.sub(y,cy);dist=hypot_bits(dx,dy);limit=f.sub(rad,0x40800000)
    if f.to_float(dist)>=.01 and f.to_float(dist)>f.to_float(limit):
        x=f.add(cx,f.mul(f.div(dx,dist),limit));y=f.add(cy,f.mul(f.div(dy,dist),limit))
    return x,y,s.flat_height_bits if s.flat_height_enabled else z


def produce_rectangle(s:EffectGeometryState135,unit_index:int,descriptor_pointer:int,raw40_hex:str):
    """Complete raw9 branch910→4865/21024/61441→34693, with explicit scope."""
    validate(s)
    if not any((s.zone,descriptor_pointer,raw40_hex)==(z,ptr,h)for _,z,ptr,h in RECTANGLE_DECLARATIONS):
        raise PendingEffectGeometry135(s,'Unknown or non-raw9 declaration retained')
    if not 0<=unit_index<len(s.units):return EffectGeometryResult135(s,())
    raw=bytearray.fromhex(s.units[unit_index]);d=bytes.fromhex(raw40_hex)
    if get(raw,0)!=0:return EffectGeometryResult135(s,())
    if get(raw,244)==f.MASK or get(raw,64)!=f.MASK:
        raise PendingEffectGeometry135(s,'Genuine Boss244 family and absent ranged64 required')
    if get(raw,256)!={5433104:5434088,5453396:5455432,5454132:5455576}[descriptor_pointer]:
        raise PendingEffectGeometry135(s,'Only the matched genuine Boss/declaration family is verified')
    if s.length==len(s.storage):raise PendingEffectGeometry135(s,'Capacity growth remains unresolved')
    if any(not finite(get(raw,o))for o in(128,132,136,140,268,296,316,320,324,328,332,336,340,344,348,352,400)):
        raise PendingEffectGeometry135(s,'Finite Boss producer fields required')
    xyz=position(raw,s.now_bits);delay=get(d,12)
    #31733 norm6 returns descriptor+12; ordered maxnum update precedes stop.
    put(raw,268,max_numeric(get(raw,268),f.add(f.add(s.now_bits,delay),0x3ecccccd)))
    target=predicted_player(s);heading=atan2_bits(f.sub(target[1],xyz[1]),f.sub(target[0],xyz[0]))
    stopped=(*xyz[:2],s.flat_height_bits if s.flat_height_enabled else xyz[2])
    for o in(316,328):
        for j,x in enumerate(stopped):put(raw,o+4*j,x)
    put(raw,344,0);put(raw,340,s.now_bits)
    stop=max_numeric(get(raw,400),f.add(s.now_bits,delay));put(raw,400,stop);put(raw,348,stop)
    put(raw,352,max_numeric(get(raw,352),f.add(delay,0x3e99999a)))
    weakness=get(raw,128)if val(raw,132)>f.to_float(s.now_bits)else get(raw,136)if val(raw,140)>f.to_float(s.now_bits)else 0
    attack=f.mul(get(raw,296),f.sub(ONE,weakness))
    if raw[276]:attack=f.mul(attack,0x3fb33333)
    damage=f.mul(attack,get(d,16));counter=(s.effect_counter2356+1)&f.MASK
    physical=bytearray.fromhex(s.storage[s.length].raw_hex)
    put(physical,0,0);put(physical,8,0);put(physical,12,target[1]);put(physical,16,target[2]);put(physical,20,0)
    physical[24:32]=raw[112:120];physical[32:40]=bytes(8)
    put(physical,40,2);physical[44:52]=d[4:12];put(physical,52,counter)
    for j,x in enumerate((*xyz[:2],s.flat_height_bits)):put(physical,56+4*j,x)
    put(physical,68,heading);put(physical,72,s.now_bits)
    put(physical,76,f.add(s.now_bits,f.mul(delay,0x3f59999a if s.difficulty387 else ONE)))
    put(physical,80,0);put(physical,84,get(d,0));put(physical,88,damage);put(physical,92,f.INF)
    physical[96:119]=bytes(23)
    store=list(s.storage);store[s.length]=Effect120135(physical.hex(),(20,21,22,23))
    units=list(s.units);units[unit_index]=raw.hex();guid=struct.unpack_from('<Q',raw,112)[0]
    state=replace(s,storage=tuple(store),length=s.length+1,units=tuple(units),effect_counter2356=counter,
        movement_sequence2412=(s.movement_sequence2412+1)&f.MASK)
    return EffectGeometryResult135(state,(('stop221',guid,stopped,heading),('spell_start305',guid,get(d,0),delay),('append120',s.length,counter)))


def _supported(s,e):
    r=bytes.fromhex(e.raw_hex)
    if (get(r,0),get(r,8),get(r,40))!=(0,0,2):raise PendingEffectGeometry135(s,'Unrecovered120 family retained')
    if struct.unpack_from('<Q',r,32)[0]or any(get(r,o)for o in(80,96,100,104,108,112))or r[116]or r[117]:
        raise PendingEffectGeometry135(s,'Unrecovered120 auxiliary state retained')
    if get(r,92)!=f.INF or r[118]not in(0,1):raise PendingEffectGeometry135(s,'Unrecovered120 timing retained')
    if any(not finite(get(r,o))for o in(44,48,56,60,64,68,72,76,88)):
        raise PendingEffectGeometry135(s,'Finite120 geometry/timing required')
    return r


def _inside(r,xy):
    dx=f.sub(xy[0],get(r,56));dy=f.sub(xy[1],get(r,60));a=get(r,68);cs=cos_bits(a);sn=sin_bits(a)
    forward=f.add(f.mul(dx,cs),f.mul(dy,sn));side=f.sub(f.mul(dy,cs),f.mul(dx,sn))&0x7fffffff
    return 0<=f.to_float(forward)<=val(r,44) and f.to_float(side)<=f.to_float(f.mul(get(r,48),0x3f000000))


def tick_rectangles(s:EffectGeometryState135,dt_bits:int):
    """915 type0: initial preview, one due attempt, reverse stable compaction.

    Even a miss expires. All overlapping damage accumulates in record order,
    then exactly one incoming1073 scalar projection runs with the last hit source.
    The real serializer/wire payload and registry/history side effects are not
    substituted with fabricated bytes.
    """
    validate(s)
    if not finite(dt_bits):raise PendingEffectGeometry135(s,'Finite frame dt required')
    for e in s.records:_supported(s,e)  # Validate all before any write.
    store=list(s.storage);remove=[];events=[];damage=0;last_guid=0;last_spell=0
    guids={struct.unpack_from('<Q',bytes.fromhex(u),112)[0]for u in s.units if get(bytes.fromhex(u),0)!=1}
    for i,e in enumerate(s.records):
        r=bytearray.fromhex(e.raw_hex);guid=struct.unpack_from('<Q',r,24)[0]
        if guid not in guids:
            remove.append(i);events.append(('orphan_remove120',i))
            if r[118]&1:events.append(('remove_JSON',get(r,52)))
            continue
        if not r[118]:
            r[118]=1
            #915 queues a preview index, then filters it against the removal
            #indices before serialization (fullWAT5237..5414). A first due
            #entry therefore writes118 but never emits a transient hz preview.
            if f.to_float(s.now_bits)<val(r,76):events.append(('preview_JSON',get(r,52)))
        if f.to_float(s.now_bits)>=val(r,76):
            hit=_inside(r,s.player_xyz_bits)
            if hit:damage=f.add(damage,get(r,88));last_guid=guid;last_spell=get(r,84)
            events.append(('impact306',guid,get(r,84),hit));events.append(('remove_JSON',get(r,52)));remove.append(i)
        store[i]=Effect120135(r.hex(),e.unspecified_bytes)
    n=s.length
    for index in reversed(remove):
        for j in range(index,n-1):store[j]=store[j+1]
        n-=1  # The old final slot is retained by memory.copy/pop.
    #The actual JSON notification clock is emitted for each nonempty120 entry,
    #even when no geometry changed. It is not the one-shot2364 action clock.
    if s.length:events.append(('hzt_JSON',s.now_bits))
    incoming=replace(s.incoming,now_bits=s.now_bits,player_x_1504_bits=s.player_xyz_bits[0],
        player_y_1508_bits=s.player_xyz_bits[1],units=tuple(unit_position(bytes.fromhex(u))for u in s.units))
    boundary=False
    if f.to_float(damage)>0:
        factor=ONE if s.endless2568==1 and s.difficulty387<4 else 0x40400000 if s.difficulty387>3 else 0x40000000
        amount=f.mul(damage,factor);result=resolve_incoming_prefix(incoming,amount,last_guid)
        if result.stage not in('scalar_nonfatal_projection','phase_guard','protection_guard','active_raw_buff12_guard'):
            raise PendingEffectGeometry135(s,'Incoming death/callback boundary:'+result.stage)
        incoming=result.state;events.append(('incoming1073',last_guid,last_spell,amount,result.stage))
        #1073 category2/nonzero spell next reaches4546's genuine Spell.dbc
        #initializer. The controlled host-denied original can validate this
        #scalar prefix; no normal completion or resumable state is claimed.
        boundary=result.stage=='scalar_nonfatal_projection'
    state=replace(s,storage=tuple(store),length=n,incoming=incoming,entry_pending=boundary)
    return EffectGeometryResult135(state,tuple(events),damage,status='pending_original_spell_database'if boundary else'normal_rectangle_projection')
