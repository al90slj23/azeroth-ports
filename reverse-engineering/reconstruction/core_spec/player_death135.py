"""Fixed135 no-revival fatal continuation, complete mode0 death5620 slice.

The caller supplies the post-callback HP and proves the three revival sources
absent/inactive. This never bypasses incoming1073 registry/proc/history work.
Movement-stop semantics follow the validated terminal135 consumers through a
new lazy byte/None adapter. The older full-hex terminal source is unchanged.
"""
from dataclasses import dataclass,replace,fields
import struct
from . import binary32 as f
from .terminal_transition135 import (
    TerminalInput135,COUNTER_KEYS,CLASSES,RACES,ZONES,
    _quote,_number,_f64,_finite,_packed,
)
from .incoming_history135 import IncomingHistory135
from .player_death_recap135 import death_recap135
from .record_cells135 import cells135,u32,u64,put_u32,encode_row

class UnknownPlayerDeath135(NotImplementedError):pass

@dataclass(frozen=True)
class PlayerDeathState135(TerminalInput135):
    """Terminal metadata plus explicit byte/None motion backing.

    Unlike the older terminal fixture adapter, this accepts preserved unknown
    padding/inactive payload. Only the selected original stop branch consumes
    coordinates/GUIDs. No unknown cell is replaced by an invented zero.
    """
    def __post_init__(self):
        values={item.name:getattr(self,item.name)for item in fields(TerminalInput135)}
        for name,stride in(('units',424),('auxiliary',112),('claims',88)):
            rows=values[name+'_storage'];count=values[name+'_count']
            if type(rows)is not tuple or len(rows)>512 or type(count)is not int or not 0<=count<=len(rows):raise ValueError('Explicit bounded motion backing/count required')
            for row in rows:cells135(row,stride)
            values[name+'_storage']=();values[name+'_count']=0
        # Validate all scalar/counter/summary fields using the existing schema.
        TerminalInput135(**values)

@dataclass(frozen=True)
class FatalBoundary135:
    hp_after_callbacks_bits:int
    mode2582:int|None
    innate_definition_kind:int|None
    innate_cooldown_bits:int|None
    modifier31_absent:bool|None
    lives1632:int|None
    incoming_callbacks_complete:bool|None

@dataclass(frozen=True)
class PlayerDeathResult135:
    state:TerminalInput135
    hp1440_bits:int
    paused408:int
    paused_time412_bits:int
    packets:tuple
    notifications:tuple
    stopped_guids:tuple
    status:str

def _stop_motion135(state):
    """Exact common17119/17217/16340 finite absent-terrain stop domain."""
    records={name:[cells135(row,stride)for row in getattr(state,name+'_storage')]for name,stride in(('units',424),('auxiliary',112),('claims',88))}
    sequence=state.movement_sequence2412;packets=[];stopped=[];now=f.to_float(state.now_bits)
    def word(row,offset):return u32(row,offset,consumer='player_death135.stop')
    def position(row,origin,end,start,duration,claim):
        if state.terrain_grid_absent is not True or state.collision_grid_absent is not True:raise UnknownPlayerDeath135('Movement stop requires restored terrain/collision adapter or explicit absence')
        _finite(state.now_bits);duration_bits=_finite(word(row,duration));start_bits=_finite(word(row,start))
        destination=tuple(_finite(word(row,end+j*4))for j in range(3))
        if claim and f.to_float(duration_bits)<=0:xyz=destination
        else:
            source=tuple(_finite(word(row,origin+j*4))for j in range(3));ratio=f.div(f.sub(state.now_bits,start_bits),duration_bits)
            if f.to_float(ratio)<0:ratio=0
            if f.to_float(ratio)>1:ratio=0x3f800000
            xyz=tuple(f.add(a,f.mul(f.sub(b,a),ratio))for a,b in zip(source,destination))
        return (*xyz[:2],_finite(state.flat_height_bits))if state.flat_height_enabled else xyz
    def stop(row,origin,end,start,duration,guid_offset,timer=None,claim=False):
        nonlocal sequence
        xyz=position(row,origin,end,start,duration,claim)
        for offset in(origin,end):
            for j,value in enumerate(xyz):put_u32(row,offset+j*4,value)
        put_u32(row,start,state.now_bits);put_u32(row,duration,0)
        if timer is not None:put_u32(row,timer,state.now_bits)
        guid=u64(row,guid_offset,consumer='player_death135.stop.GUID');sequence=(sequence+1)&f.MASK
        packets.append((221,32,(_packed(guid)+struct.pack('<3II',*xyz,sequence)+b'\1').hex()));stopped.append(guid)
    for row in records['units'][:state.units_count]:
        if word(row,0)==0 and f.to_float(word(row,344))>0 and now<f.to_float(f.add(word(row,344),word(row,340))):stop(row,316,328,340,344,112)
    for row in records['auxiliary'][:state.auxiliary_count]:
        if f.to_float(word(row,60))>0 and now<f.to_float(f.add(word(row,60),word(row,56))):stop(row,32,44,56,60,16,68)
    for row in records['claims'][:state.claims_count]:
        if not now>=f.to_float(f.add(word(row,68),word(row,72))):stop(row,44,56,68,72,24,76,True)
    return {name:tuple(encode_row(row)for row in rows)for name,rows in records.items()},sequence,tuple(packets),tuple(stopped)

def defeat_notification135(state,*,history=None):
    """Complete1938 wrapper; left0 requires independently restored1367 bytes.

    left0 consumes the explicit history ring through the independently restored
    full1367 model. Unresolved None is not promoted to an empty object.5620 has
    just written408=1 and412=now, so1938's recap reference time is exactlynow.
    The left flag has the original lazy behavior and does not consume history.
    """
    if state.localization_profile!='english_fallback':raise UnknownPlayerDeath135('Explicit English fallback notification labels required')
    if state.left2567:
        recap_bytes=b'{}'
    else:
        if not isinstance(history,IncomingHistory135):raise UnknownPlayerDeath135('left0 defeat requires resolved incoming48 history ring')
        recap_bytes=bytes.fromhex(death_recap135(history,state.now_bits)[1])
    data=bytearray(b'{');capacity=1;first=True
    def append(value):
        nonlocal capacity
        if len(data)+len(value)>capacity:capacity=max(capacity*2,len(data)+len(value),8)
        data.extend(value)
    def field(name,value):
        nonlocal first
        if not first:append(b',')
        first=False;append(_quote(name));append(b':');append(value)
    counters=dict(state.counters)
    field('type',_quote('defeat'));field('time',_number(f.to_float(state.now_bits)))
    for offset,name in COUNTER_KEYS[:5]:field(name,_number(counters[offset]))
    field('damage',_number(_f64(state.damage984_f64_bits)));field('taken',_number(_f64(state.taken992_f64_bits)))
    for offset,name in COUNTER_KEYS[5:]:field(name,_number(counters[offset]))
    for name,value in(('class',CLASSES[state.class_byte]),('hero',state.hero),('race',RACES[state.race_byte]),('bg',ZONES[state.region_index])):field(name,_quote(value))
    field('left',b'true'if state.left2567 else b'false');field('recap',recap_bytes);append(b'}')
    return capacity,bytes(data).hex()

def finish_no_revival_fatal135(state,boundary,*,history=None):
    """Full1073 lives0 boundary -> real5620 mode0, in declared motion domain.

    Exact static original condition: intrinsic raw12 can attempt922 unless its
    cooldown is strictly positive; modifier31 and remaining lives have separate
    earlier branches. No failed-cast or resurrection behavior is invented here.
    """
    if not isinstance(state,TerminalInput135)or not isinstance(boundary,FatalBoundary135):raise TypeError('Explicit fatal and terminal-state inputs required')
    for value in(boundary.hp_after_callbacks_bits,):
        if type(value)is not int or not 0<=value<1<<32:raise ValueError('Explicit HP binary32 required')
    if state.phase2587!=1 or type(boundary.mode2582)is not int or boundary.mode2582!=0 or boundary.incoming_callbacks_complete is not True:
        raise UnknownPlayerDeath135('Only phase1/mode0 post-incoming-callback fatal boundary restored')
    if not f.to_float(boundary.hp_after_callbacks_bits)<=0:raise UnknownPlayerDeath135('Fatal continuation requires actual post-callback HP<=0')
    if type(boundary.innate_definition_kind)is not int or not 0<=boundary.innate_definition_kind<1<<32:
        raise UnknownPlayerDeath135('Intrinsic definition kind unresolved')
    if boundary.innate_definition_kind==12:
        cd=boundary.innate_cooldown_bits
        if type(cd)is not int or not 0<=cd<1<<32 or not f.to_float(cd)>0:
            raise UnknownPlayerDeath135('Intrinsic raw12 may cast/resurrect before lives0')
    if boundary.modifier31_absent is not True or type(boundary.lives1632)is not int or boundary.lives1632!=0:
        raise UnknownPlayerDeath135('Modifier31 and lives revival paths unresolved')
    records,sequence,packets,stopped=_stop_motion135(state);capacity=state.packet_capacity;count=state.packet_count
    for _ in packets:
        if count==capacity:capacity=max(4,capacity*2)
        count+=1
    notification=defeat_notification135(state,history=history);ncap=state.notification_vector_capacity
    if state.notification_count==ncap:ncap=max(4,ncap*2)
    result=replace(state,phase2587=4,movement_sequence2412=sequence,
        units_storage=records['units'],auxiliary_storage=records['auxiliary'],
        claims_storage=records['claims'],packet_capacity=capacity,packet_count=count,
        notification_vector_capacity=ncap,notification_count=state.notification_count+1)
    return PlayerDeathResult135(result,0,1,state.now_bits,packets,(notification,),stopped,'no_revival_mode0_death_complete')
