"""Current1392123 defaultHumanWarrior live expiry/regen/owned scheduling.

Every input owner is explicit. Quiet-center learned failures are proved from
the retained NPC positions. Human perception is a required real callback,
never disabled or replaced by a no-op. Main884/AI/input are separate phases.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .growth139 import GrowthState139
from .derived_stats139 import StatsInput,LiveEffect,recalculate
from .candidates139_data import DEFINITIONS139
from .hit_events139_data import DECLARATIONS139


class PendingPlayerUpdate139(NotImplementedError):pass


def word139(row,offset):
    part=tuple(row[offset:offset+4])
    if len(part)!=4 or None in part:raise PendingPlayerUpdate139('Unknown consumed word '+str(offset))
    return int.from_bytes(bytes(part),'little')


def _uint(value):
    if type(value)is not int or not 0<=value<=f.MASK:raise ValueError('Explicit u32/binary32 required')
    return value


def _record(row):
    row=tuple(row)
    if len(row)!=32 or any(v is not None and(type(v)is not int or not 0<=v<=255)for v in row):raise ValueError('32 known/None cells required')
    return row


def _put(row,offset,value):
    row=list(row);row[offset:offset+4]=struct.pack('<I',value);return tuple(row)


def _minnum(a,b):
    x=a if f.is_nan(b)else b;y=x if f.is_nan(a)else a
    return x if f.to_float(x)<f.to_float(y)else y


def _maxnum(a,b):
    x=a if f.is_nan(b)else b;y=x if f.is_nan(a)else a
    return x if f.to_float(x)>f.to_float(y)else y


@dataclass(frozen=True)
class LiveVector139:
    storage:tuple
    count:int
    def __post_init__(self):
        if type(self.storage)is not tuple or type(self.count)is not int or not 0<=self.count<=len(self.storage)<=256:raise ValueError('Explicit bounded live physical vector')
        for row in self.storage:_record(row)
    @property
    def capacity(self):return len(self.storage)
    @property
    def active(self):return self.storage[:self.count]


@dataclass(frozen=True)
class PlayerUpdateState139:
    growth:GrowthState139
    live:LiveVector139
    player_xyz:tuple
    spell_sets:tuple
    timer1628_bits:int
    aura_state:object
    pool1444_bits:int=0
    pool1448_bits:int=0
    conditional1344:int=0
    conditional1348_bits:int=0
    pool764_bits:int=0
    previous_speed1648_bits:int=0x40e00000
    last_hit1652_bits:int=0xc1200000
    heal_gate387:int=0
    flags768:int=0
    flags548:int=0
    refresh772:int=0
    def __post_init__(self):
        if not isinstance(self.growth,GrowthState139)or not isinstance(self.live,LiveVector139):raise TypeError('Current growth/live owners required')
        if self.growth.live32_cells!=self.live.active:raise ValueError('Growth and physical live owners disagree')
        if len(self.player_xyz)!=3 or len(self.spell_sets)!=3:raise ValueError('XYZ and three spell ledgers')
        for v in(*self.player_xyz,self.timer1628_bits,self.pool1444_bits,self.pool1448_bits,self.conditional1344,self.conditional1348_bits,self.pool764_bits,self.previous_speed1648_bits,self.last_hit1652_bits):_uint(v)
        if self.growth.source_counts!=(0,)*7:raise PendingPlayerUpdate139('Nonempty item/stat/proc sources')
        if any((self.flags768,self.flags548,self.refresh772)):raise PendingPlayerUpdate139('23328 cooldown-refresh source flags')
        if self.growth.mode2582!=0 or self.heal_gate387!=0:raise PendingPlayerUpdate139('Defaultmode/heal gate only')
        if type(self.growth.units432_cells)is not tuple or len(self.growth.units432_cells)>128:raise ValueError('Bounded actual NPC owner')
        for row in self.growth.units432_cells:
            if len(row)!=432 or any(v is not None and(type(v)is not int or not 0<=v<=255)for v in row):raise ValueError('432 known/None NPC cells')


def _replace_live(state,vector):
    return replace(state,live=vector,growth=replace(state.growth,live32_cells=vector.active))


def recalculate_player139(state):
    live=[]
    for row in state.live.active:
        kind,spell,expires=word139(row,8),word139(row,20),word139(row,24)
        if kind==12:value=0
        elif kind==8 and spell==20600:value=word139(row,12)
        else:raise PendingPlayerUpdate139('Only selected1020/perception live sources restored')
        live.append(LiveEffect(kind,value,spell,expires))
    g=state.growth
    answer=recalculate(StatsInput(class_byte=1,race_byte=1,level=g.level,old_max_hp_bits=g.derived_bits[1536],current_hp_bits=g.current_hp_bits,now_bits=g.now_bits,previous_speed_bits=state.previous_speed1648_bits,conditional268_bits=0,flag2574=0,pool1532_bits=state.pool1444_bits,pool1536_bits=state.pool1448_bits,conditional1344_id=state.conditional1344,conditional1348_bits=state.conditional1348_bits,pool768_bits=state.pool764_bits,live_effects=live))
    fields=dict(g.player_fields);fields.update({int(k):v for k,v in answer['object_fields'].items()});aux=answer['auxiliary_bits']
    return replace(state,growth=replace(g,current_hp_bits=answer['current_hp_bits'],derived_bits={int(k):v for k,v in answer['derived_bits'].items()},player_fields=fields),pool1444_bits=aux['1444'],pool1448_bits=aux['1448'],conditional1348_bits=aux['1348'],pool764_bits=aux['764'],previous_speed1648_bits=answer['speed_bits'])


def _quiet_outside139(state,radius):
    square=f.mul(radius,radius)
    for row in state.growth.units432_cells:
        marker=word139(row,0)
        if marker:
            if marker!=1:raise PendingPlayerUpdate139('Other NPC marker')
            continue
        if word139(row,344)!=0:raise PendingPlayerUpdate139('Moving NPC quiet query')
        x,y=word139(row,328),word139(row,332);dx=f.sub(x,state.player_xyz[0]);dy=f.sub(y,state.player_xyz[1]);distance=f.add(f.mul(dx,dx),f.mul(dy,dy))
        if not f.to_float(distance)>f.to_float(square):return False
    return True


def _attempt_sets139(state,spell):
    return replace(state,spell_sets=tuple(row if spell in row else row+(spell,)for row in state.spell_sets))


def _definition139(pointer):
    for name,(p,raw,kinds)in DEFINITIONS139.items():
        if p==pointer:return name,bytes.fromhex(raw)
    if pointer==5891892:return'perception',bytes.fromhex(DECLARATIONS139[pointer][1])
    raise PendingPlayerUpdate139('Unknown learned/racial declaration')


def _failed_quiet_cast139(state,owned):
    pointer=word139(owned,0);name,definition=_definition139(pointer);spell=word139(definition,44);state=_attempt_sets139(state,spell)
    if name=='cleave'and definition[84]==5:
        radius=word139(definition,56)
    elif name=='thunder_clap'and definition[84]==2 and word139(definition,0)!=6:
        radius=f.mul(f.mul(f.mul(state.growth.derived_bits[1580],word139(definition,60)),word139(owned,24)),word139(owned,64))
        if f.to_float(radius)>70:raise PendingPlayerUpdate139('Expanded area radius helper')
    else:raise PendingPlayerUpdate139('New learned spell execution '+name)
    if not _quiet_outside139(state,radius):raise PendingPlayerUpdate139('Learned ability has actual nearby target')
    return state,spell


def _callback139(state,fn,role):
    if not callable(fn):raise PendingPlayerUpdate139('Actual '+role+' producer callback required')
    result=fn(dict(player_state=state,growth=state.growth,live=state.live,spell_sets=state.spell_sets,aura=state.aura_state,racial80=state.growth.racial_record80,player_xyz=state.player_xyz))
    for key in('growth','live','spell_sets','aura','packets','plan'):
        if key not in result:raise TypeError('Incomplete '+role+' result '+key)
    updated=result.get('player_state')
    if updated is None:updated=replace(state,growth=result['growth'],live=result['live'],spell_sets=tuple(tuple(v)for v in result['spell_sets']),aura_state=result['aura'])
    elif not isinstance(updated,PlayerUpdateState139)or updated.growth!=result['growth']or updated.live!=result['live']or updated.spell_sets!=tuple(tuple(v)for v in result['spell_sets'])or updated.aura_state!=result['aura']:raise ValueError('Callback complete state/projection mismatch')
    return updated,result


def tick_default_owned139(state,dt_bits,*,cast_perception139):
    """Full1238 declared quiet-center path, including real Human racial."""
    if state.growth.phase2587!=1:raise PendingPlayerUpdate139('Running phase1 component only')
    packets=[];events=[];timer=f.sub(state.timer1628_bits,dt_bits)
    if f.to_float(timer)<=0:
        if not _quiet_outside139(state,0x40c00000):raise PendingPlayerUpdate139('Actual warrior basic attack target')
        timer=0x3e19999a;events.append(('warrior_no_target',))
    state=replace(state,timer1628_bits=timer);owned=list(state.growth.owned_records80)
    for j,row in enumerate(owned):
        name,definition=_definition139(word139(row,0))
        if definition[84]==11 or word139(definition,0)==12:raise PendingPlayerUpdate139('Special learned scheduler '+name)
        remaining=f.sub(word139(row,8),dt_bits);changed=bytearray(row);changed[8:12]=struct.pack('<I',remaining)
        if not f.to_float(remaining)>0:
            state,spell=_failed_quiet_cast139(state,bytes(changed));remaining=0x3e4ccccd;changed[8:12]=struct.pack('<I',remaining);events.append(('owned_failed_retry',j,spell))
        owned[j]=bytes(changed)
    state=replace(state,growth=replace(state.growth,owned_records80=tuple(owned)))
    racial=bytearray(state.growth.racial_record80)
    if word139(racial,0)!=5891892:raise PendingPlayerUpdate139('Only real Human perception racial')
    remaining=f.sub(word139(racial,8),dt_bits);racial[8:12]=struct.pack('<I',remaining);state=replace(state,growth=replace(state.growth,racial_record80=bytes(racial)))
    if f.to_float(remaining)<=0:
        state,result=_callback139(state,cast_perception139,'perception922')
        if result.get('success')not in(0,1):raise TypeError('Perception success flag')
        if result['success']:
            definition=bytes.fromhex(DECLARATIONS139[5891892][1]);record=state.growth.racial_record80
            remaining=_maxnum(f.mul(f.mul(f.mul(f.mul(word139(definition,52),0x3fb33333),word139(record,16)),word139(record,56)),state.growth.derived_bits[1544]),0x3e800000)
            milliseconds=max(0,min(f.MASK,int(f.to_float(f.mul(remaining,0x447a0000)))));packets.extend(((308,struct.pack('<QII',0,20600,milliseconds).hex()),(309,struct.pack('<IQ',20600,0).hex())))
        else:remaining=0x3f000000
        racial=bytearray(state.growth.racial_record80);racial[8:12]=struct.pack('<I',remaining);state=replace(state,growth=replace(state.growth,racial_record80=bytes(racial)));packets[:0]=list(result['packets']);events.append(('perception',result['success'],tuple(result['plan'])))
    return state,tuple(packets),tuple(events)


@dataclass(frozen=True)
class PlayerUpdateResult139:
    state:PlayerUpdateState139
    expired_spells:tuple
    retained_source_indices:tuple
    expiry_recalculate1542_called:bool
    expiry_sync1173_called:bool
    regen_request_bits:int
    packets:tuple
    events:tuple
    pending:tuple=('FullAura/presentation stream and physical heap allocation remain explicitly projected separately',)


def update_player139(state,now_bits,dt_bits,*,sync_aura139,cast_perception139):
    """2123 retain→1542→1173→regen→1466→full1238 quiet projection."""
    if not isinstance(state,PlayerUpdateState139):raise TypeError('PlayerUpdateState139')
    for v in(now_bits,dt_bits):
        _uint(v)
        if f.is_nan(v)or f.is_inf(v):raise PendingPlayerUpdate139('Finite clock/dt only')
    if f.to_float(dt_bits)<0:raise PendingPlayerUpdate139('Nonnegative clock delta')
    if state.conditional1344 or state.conditional1348_bits or state.pool1444_bits or state.pool1448_bits or state.pool764_bits:raise PendingPlayerUpdate139('Nonempty shield/pool owner')
    state=replace(state,growth=replace(state.growth,now_bits=now_bits));expired=[]
    for row in state.live.active:
        kind,spell=word139(row,8),word139(row,20)
        if not(kind==12 and spell==1020 or kind==8 and spell==20600):raise PendingPlayerUpdate139('Other nonempty live kind/spell')
        if word139(row,28)!=0:raise PendingPlayerUpdate139('Periodic live budget')
        if f.to_float(now_bits)>=f.to_float(word139(row,24)):expired.append(spell)
    packets=[];events=[];retained=tuple(range(state.live.count))
    if expired:
        rows=list(state.live.storage);retained=tuple(j for j,row in enumerate(state.live.active)if f.to_float(now_bits)<f.to_float(word139(row,24)))
        for j,i in enumerate(retained):rows[j]=state.live.storage[i]
        state=_replace_live(state,LiveVector139(tuple(rows),len(retained)));state=recalculate_player139(state);state,result=_callback139(state,sync_aura139,'Aura1173');packets.extend(result['packets']);events.append(('expire',tuple(expired),'1542','1173',tuple(result['plan'])))
    state=replace(state,pool1448_bits=_minnum(state.pool1444_bits,state.pool1448_bits));g=state.growth
    if g.current_hp_bits!=g.derived_bits[1536]:raise PendingPlayerUpdate139('Positive regeneration/heal accounting1466')
    extra=f.mul(g.derived_bits[1536],g.derived_bits[1620])if f.to_float(f.sub(now_bits,state.last_hit1652_bits))>=3 else 0
    regen=f.mul(dt_bits,f.add(g.derived_bits[1576],extra));events.append(('regen_full_HP_zero_account','28155','1466'))
    state,new_packets,owned_events=tick_default_owned139(state,dt_bits,cast_perception139=cast_perception139);packets.extend(new_packets);events.extend(owned_events)
    return PlayerUpdateResult139(state,tuple(expired),retained,bool(expired),bool(expired),regen,tuple(packets),tuple(events))
