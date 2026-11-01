"""Independent135 guarded915 clock and ordered delayed56 consumers.

Full caller-supplied queue/backing/unit bytes are preserved. Effect120 and910
dispatch remain explicit boundaries. No original code, outputs, assets or IO.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .spawn_heading135 import atan2_bits
from .ai_trig135 import sin_bits,cos_bits
from .spawn_geometry135 import hypot_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .progression134 import trunc_sat_u32
from .record_cells135 import cells135,u32,u64,put_u32,encode_row


class PendingEffectSystem135(NotImplementedError):
    def __init__(self,message,state):
        super().__init__(message);self.state=state


def _u(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:raise ValueError('Explicit unsigned integer required')
    return value


def _raw(value,size):
    raw=bytes.fromhex(value)
    if len(raw)!=size:raise ValueError(f'Complete{size}B record required')
    return raw


def _word(raw,offset):return u32(raw,offset,'915 record field')
def _guid(raw,offset=112):return u64(raw,offset,'915 record GUID')
def _put(raw,offset,value):put_u32(raw,offset,value)
def _finite(value):
    _u(value)
    if value&0x7fffffff>=f.INF:raise ValueError('Finite movement input required')
    return value


def _maxnum(a,b):
    a=b if f.is_nan(a)else a;b=a if f.is_nan(b)else b
    return a if f.to_float(a)>f.to_float(b)else b


@dataclass(frozen=True)
class EffectSystemState135:
    now_bits:int
    delayed_records:tuple
    delayed_storage:tuple
    effect_records120:tuple
    units:tuple
    clock2364_bits:int
    action_sequence1644:int
    movement_sequence2412:int
    player_xyz_bits:tuple
    player_action_words:tuple
    source_id:int
    phase2587:int
    mode2582:int
    local_peer2528:int
    zone:int
    flat_height_bits:int
    flat_height_enabled:bool
    terrain_grid_absent:bool=False
    collision_grid_absent:bool=False
    navigation_absent:bool=False
    rng_words:tuple=(0,0,0,0)
    spawn_counter2408:int=0

    def __post_init__(self):
        for value in(self.now_bits,self.clock2364_bits,self.action_sequence1644,self.movement_sequence2412,
                     self.local_peer2528,self.flat_height_bits,self.spawn_counter2408,*self.player_xyz_bits,*self.player_action_words,*self.rng_words):_u(value)
        _u(self.source_id,64);_u(self.phase2587,8);_u(self.mode2582,8)
        if len(self.player_xyz_bits)!=3 or len(self.player_action_words)!=6 or len(self.rng_words)!=4:raise ValueError('Explicit player/movement/RNG snapshots required')
        if type(self.zone)is not int or not 0<=self.zone<12:raise ValueError('Fixed zone required')
        if type(self.flat_height_enabled)is not bool:raise ValueError('Explicit flat-height enable flag required')
        for values,size in((self.delayed_records,56),(self.delayed_storage,56),(self.effect_records120,120),(self.units,424)):
            if type(values)is not tuple or len(values)>512:raise ValueError('Bounded ordered record vectors required')
            for raw in values:
                if size==424:cells135(raw,424)
                else:_raw(raw,size)
        if len(self.delayed_records)>len(self.delayed_storage)or self.delayed_storage[:len(self.delayed_records)]!=self.delayed_records:raise ValueError('Delayed active prefix and full backing differ')


@dataclass(frozen=True)
class EffectSystemResult135:
    state:EffectSystemState135
    status:str
    events:tuple
    pending_record56:str|None=None
    pending_target_index:int|None=None
    pending:tuple=('Physical221/306/199/169/234 payloads and120/910 families remain pending',)


def _position(raw,now):
    duration=_finite(_word(raw,344));start=_finite(_word(raw,340))
    a=tuple(_finite(_word(raw,o))for o in(316,320,324));b=tuple(_finite(_word(raw,o))for o in(328,332,336))
    if f.to_float(duration)<=0:return b
    ratio=f.div(f.sub(now,start),duration)
    ratio=0 if f.to_float(ratio)<0 else ratio
    ratio=0x3f800000 if f.to_float(ratio)>1 else ratio
    return tuple(f.add(x,f.mul(f.sub(y,x),ratio))for x,y in zip(a,b))


def step_effect_system(state,dt_bits):
    """Full915 entry-domain projection; never clear an unsupported effect120.

    The ordinary910 boundary is after the actual due record has been removed.
    Its raw record and target index are returned explicitly for continuation.
    dt is unused in915's supported prefix, but retains its actual binary32 word.
    """
    if not isinstance(state,EffectSystemState135):raise TypeError('Resolved effect system state required')
    _u(dt_bits);_finite(state.now_bits)
    if state.effect_records120:raise PendingEffectSystem135('Nonempty120B effects require actual unresolved915 continuation',state)
    now=state.now_bits;events=[];rows=list(state.delayed_records);backing=list(state.delayed_storage);units=[cells135(x,424)for x in state.units]
    clock=state.clock2364_bits;sequence=state.action_sequence1644;movement=state.movement_sequence2412
    player=state.player_xyz_bits;action=state.player_action_words
    def snapshot():
        return replace(state,delayed_records=tuple(rows),delayed_storage=tuple(backing),units=tuple(encode_row(x)for x in units),
            clock2364_bits=clock,action_sequence1644=sequence,movement_sequence2412=movement,player_xyz_bits=player,player_action_words=action)
    if f.to_float(clock)>0 and f.to_float(clock)<=f.to_float(now):
        clock=0;old=sequence;sequence=(sequence+1)&f.MASK
        events.append(('clock',234,state.source_id,old))
    index=0
    while index<len(rows):
        record=bytes.fromhex(rows[index]);guid=_guid(record,0)
        due=not(f.to_float(_word(record,8))>f.to_float(now))
        if due and state.mode2582:
            owner=next((_word(u,280)for u in units if _guid(u)==guid),0)
            due=owner==state.local_peer2528
        if not due:index+=1;continue
        #Original copies each following56B record left and retains the last
        #inactive slot. Later removals see this already-shifted full backing.
        for j in range(index,len(rows)-1):backing[j]=backing[j+1]
        rows.pop(index)
        tag=record[49]
        if tag==255:
            #915 line230 exits block101→end1232 and reaches80660 at1238.
            #This is a real original trap after compaction, not a skip marker.
            return EffectSystemResult135(snapshot(),'trap_invalid255_after_pop',tuple(events),record.hex())
        target=next((j for j,u in enumerate(units)if _guid(u)==guid and not(_word(u,0)&1)),None)
        if target is None:continue
        if tag not in(35,36,37):
            return EffectSystemResult135(snapshot(),'pending_910_dispatch',tuple(events),record.hex(),target)
        if tag==37:
            #4543 performs its own marker!=1 lookup, independently of the
            #outer marker&1 guard. This matters for duplicate GUID snapshots.
            aura_target=next((j for j,u in enumerate(units)if _guid(u)==guid and _word(u,0)!=1),None)
            if aura_target is not None:
                raw=units[aura_target];spell=_word(record,12)
                slot=next((i for i in range(16)if _word(raw,168+4*i)==spell),None)
                if slot is not None:
                    _put(raw,168+4*slot,0);events.append(('aura_remove',169,guid,spell,slot))
            continue
        if tag==36 and state.phase2587!=1:continue
        if state.terrain_grid_absent is not True or state.navigation_absent is not True or(tag==36 and state.collision_grid_absent is not True):
            return EffectSystemResult135(snapshot(),'pending_world_geometry',tuple(events),record.hex(),target)
        raw=units[target];xyz=_position(raw,now)
        if tag==35:
            start=(xyz[0],xyz[1],_finite(state.flat_height_bits)if state.flat_height_enabled else xyz[2])
            end=tuple(_finite(_word(record,o))for o in(12,16,20))
            dx=f.sub(start[0],end[0]);dy=f.sub(start[1],end[1])
            #Actual sqrt(add(mul,mul)), not a scaled hypot helper.
            duration=_maxnum(f.div(sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy))),0x42200000),0x3e19999a)
            movement=(movement+1)&f.MASK;ms=trunc_sat_u32(f.mul(duration,0x447a0000))
            events.extend((('unit_move',221,guid,start,end,movement,ms),('cast',306,guid,100,end)))
            for j,value in enumerate(start):_put(raw,316+4*j,value)
            for j,value in enumerate(end):_put(raw,328+4*j,value)
            _put(raw,340,now);_put(raw,344,duration);_put(raw,348,f.add(f.add(now,duration),0x3e4ccccd))
            _put(raw,352,_maxnum(_word(raw,352),f.add(duration,0x3ecccccd)))
        else:
            for value in(*player,_word(raw,308)):_finite(value)
            heading=atan2_bits(f.sub(player[1],xyz[1]),f.sub(player[0],xyz[0]))
            distance=f.add(_word(raw,308),0x3fc00000)
            x=f.add(xyz[0],f.mul(distance,cos_bits(heading)));y=f.add(xyz[1],f.mul(distance,sin_bits(heading)))
            cx,cy,radius=ZONE_GEOMETRY[state.zone];dx=f.sub(x,cx);dy=f.sub(y,cy);length=hypot_bits(dx,dy);limit=f.add(radius,0xc0800000)
            if not f.to_float(length)<f.to_float(0x3c23d70a)and not f.to_float(length)<=f.to_float(limit):
                x=f.add(cx,f.mul(f.div(dx,length),limit));y=f.add(cy,f.mul(f.div(dy,length),limit))
            z=f.add(_finite(state.flat_height_bits)if state.flat_height_enabled else xyz[2],0x3f000000)
            player=(x,y,z);old=sequence;sequence=(sequence+1)&f.MASK;action=(1,x,y,z,old,now)
            events.extend((('player_relocate',199,state.source_id,old,player,f.add(heading,0x40490fdb)),('cast',306,guid,21147,player)))
    return EffectSystemResult135(snapshot(),'delayed_prefix_projection',tuple(events))
