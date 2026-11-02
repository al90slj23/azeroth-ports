"""Independent full49961 victory transition in explicit canonical-world domain.

Ordered17209 NPC→17319 auxiliary→16380 claims stops,232 terminal packet and
complete1965 victory notification. No original module, runtime output or IO.
"""
from dataclasses import dataclass, replace
import math
import struct
from . import binary32 as f

CLASSES={1:'Warrior',2:'Paladin',3:'Hunter',4:'Rogue',5:'Priest',7:'Shaman',8:'Mage',9:'Warlock',11:'Druid'}
RACES={1:'Human',2:'Orc',3:'Dwarf',4:'Night Elf',5:'Undead',6:'Tauren',7:'Gnome',8:'Troll'}
ZONES=('Elwynn Forest','Duskwood','Warsong Gulch',"Un'Goro Crater",'Arathi Basin','Feralas','Gurubashi Arena','Scarlet Monastery','Alterac Valley','Blackrock Mountain',"Gates of Ahn'Qiraj",'Naxxramas')
COUNTER_KEYS=((1432,'level'),(1084,'kills'),(1088,'elites'),(1092,'guardians'),(1096,'bosses'),(1100,'gold'),(1104,'chests'))


class UnknownTerminalTransition139(NotImplementedError): pass


def _u(v,bits=32):
    if type(v)is not int or not 0<=v<1<<bits:raise ValueError('Explicit unsigned word required')
    return v
def _word(raw,offset):
    part=raw[offset:offset+4]
    if None in part:raise UnknownTerminalTransition139('Unproduced physical word')
    return int.from_bytes(bytes(part),'little')
def _put(raw,offset,value):raw[offset:offset+4]=value.to_bytes(4,'little')
def _finite(v):
    _u(v)
    if v&0x7fffffff>=f.INF:raise UnknownTerminalTransition139('Processed movement needs finite exact words')
    return v
def _records(values,size,count):
    _u(count)
    if type(values)is not tuple or len(values)>512 or count>len(values):raise ValueError('Explicit complete bounded storage and count required')
    result=[]
    for x in values:
        if type(x)is str:raw=list(bytes.fromhex(x))
        elif type(x)in(tuple,list):raw=list(x)
        else:raise TypeError('Full known/None physical record required')
        if len(raw)!=size or any(v is not None and(type(v)is not int or not 0<=v<=255)for v in raw):raise ValueError('Physical record stride/byte differs')
        result.append(raw)
    return result
def _packed(guid):
    b=guid.to_bytes(8,'little');return bytes([sum(1<<j for j,v in enumerate(b)if v)])+bytes(v for v in b if v)
def _quote(text):
    if type(text)is not str:raise TypeError('Explicit UTF8 text required')
    text.encode('utf8');out='"'
    for c in text:
        if c=='"':out+='\\"'
        elif c=='\\':out+='\\\\'
        elif c=='\n':out+='\\n'
        elif ord(c)<32:out+='\\u'+format(ord(c),'04x')
        else:out+=c
    return (out+'"').encode('utf8')
def _number(value):
    #53225 uses0 fornonfinite, decimalinteger forabs<1e15 integral, otherwise
    #the original format descriptor requests exactly3 fractional digits.
    if not math.isfinite(value):return b'0'
    if math.trunc(value)==value and abs(value)<1e15:return str(int(value)).encode()
    return format(value,'.3f').encode()
def _f64(bits):return struct.unpack('<d',struct.pack('<Q',_u(bits,64)))[0]


@dataclass(frozen=True)
class TerminalInput139:
    field400:int
    phase2587:int
    endless2568:int
    now_bits:int
    action_sequence1644:int
    movement_sequence2412:int
    source_id:int
    units_storage:tuple
    units_count:int
    auxiliary_storage:tuple
    auxiliary_count:int
    claims_storage:tuple
    claims_count:int
    packet_capacity:int
    packet_count:int
    notification_vector_capacity:int
    notification_count:int
    counters:tuple
    damage984_f64_bits:int
    taken992_f64_bits:int
    class_byte:int
    race_byte:int
    region_index:int
    hero:str
    left2567:int
    recap408:int
    localization_profile:str|None=None

    def __post_init__(self):
        for v in(self.field400,self.now_bits,self.action_sequence1644,self.movement_sequence2412,self.recap408,self.packet_capacity,self.packet_count,self.notification_vector_capacity,self.notification_count):_u(v)
        for v in(self.phase2587,self.endless2568,self.class_byte,self.race_byte,self.left2567):_u(v,8)
        for v in(self.source_id,self.damage984_f64_bits,self.taken992_f64_bits):_u(v,64)
        if self.packet_count>self.packet_capacity or self.notification_count>self.notification_vector_capacity:raise ValueError('Active message count exceeds capacity')
        if type(self.counters)is not tuple or {k for k,v in self.counters}!={k for k,_ in COUNTER_KEYS} or len(self.counters)!=len(COUNTER_KEYS):raise ValueError('All explicit1965 counters required')
        for k,v in self.counters:_u(v)
        if self.class_byte!=1 or self.race_byte!=1 or self.region_index!=0:raise UnknownTerminalTransition139('Unrestored class/race/zone labels')
        _quote(self.hero)
        _records(self.units_storage,432,self.units_count);_records(self.auxiliary_storage,112,self.auxiliary_count);_records(self.claims_storage,88,self.claims_count)


@dataclass(frozen=True)
class TerminalResult139:
    state:TerminalInput139
    packets:tuple
    notifications:tuple
    stopped_guids:tuple
    status:str


def victory_notification(state):
    """Complete1965 nondeath notification, including exactcapacitygrowth."""
    if state.localization_profile!='english_fallback':raise UnknownTerminalTransition139('Explicit original English fallback label domain required')
    data=bytearray(b'{');capacity=1;first=True
    def append(value):
        nonlocal capacity
        if len(data)+len(value)>capacity:capacity=max(capacity*2,len(data)+len(value),8)
        data.extend(value)
    def field(key,value):
        nonlocal first
        if not first:append(b',')
        first=False;append(_quote(key));append(b':');append(value)
    counter=dict(state.counters)
    field('type',_quote('victory'));field('time',_number(f.to_float(state.now_bits)))
    for off,name in COUNTER_KEYS[:5]:field(name,_number(counter[off]))
    field('damage',_number(_f64(state.damage984_f64_bits)));field('taken',_number(_f64(state.taken992_f64_bits)))
    for off,name in COUNTER_KEYS[5:]:field(name,_number(counter[off]))
    for key,value in(('class',CLASSES[state.class_byte]),('hero',state.hero),('race',RACES[state.race_byte]),('bg',ZONES[state.region_index])):field(key,_quote(value))
    field('left',b'true'if state.left2567 else b'false');field('recap',b'{}');append(b'}')
    return capacity,bytes(data).hex()


def transition_terminal(state,world):
    if not isinstance(state,TerminalInput139):raise TypeError('Explicit terminal state required')
    if state.recap408!=0:raise UnknownTerminalTransition139('Unrestored detached recap owner')
    if not state.field400 or state.phase2587!=1 or state.endless2568&1:return TerminalResult139(state,(),(),(),'terminal_guard_complete')
    # Original phase becomes5 before stop helpers and notification creation.
    units=_records(state.units_storage,432,state.units_count);aux=_records(state.auxiliary_storage,112,state.auxiliary_count);claims=_records(state.claims_storage,88,state.claims_count)
    now=f.to_float(state.now_bits);sequence=state.movement_sequence2412;packets=[];stopped=[];capacity=state.packet_capacity;count=state.packet_count
    def append_packet(opcode,payload):
        nonlocal capacity,count
        if count==capacity:capacity=max(4,capacity*2)
        count+=1;packets.append((opcode,32,payload.hex()))
    def position(raw,origin,end,start,duration,claim=False):
        _finite(state.now_bits);duration_bits=_finite(_word(raw,duration));start_bits=_finite(_word(raw,start))
        destination=tuple(_finite(_word(raw,end+j*4))for j in range(3))
        if claim and f.to_float(duration_bits)<=0:result=destination
        else:
            source=tuple(_finite(_word(raw,origin+j*4))for j in range(3))
            ratio=f.div(f.sub(state.now_bits,start_bits),duration_bits)
            if f.to_float(ratio)<0:ratio=0
            if f.to_float(ratio)>1:ratio=0x3f800000
            result=tuple(f.add(a,f.mul(f.sub(b,a),ratio))for a,b in zip(source,destination))
        height=world.height(*result[:2])
        if height.found:result=(*result[:2],height.value_bits)
        else:
            nearest=world.nearest_primary(*result[:2])
            if nearest.found:result=(*result[:2],nearest.xyz_bits[2])
        return result
    def stop(raw,origin,end,start,duration,guid_offset,timer=None,claim=False):
        nonlocal sequence
        xyz=position(raw,origin,end,start,duration,claim)
        for o in(origin,end):
            for j,v in enumerate(xyz):_put(raw,o+j*4,v)
        _put(raw,start,state.now_bits);_put(raw,duration,0)
        if timer is not None:_put(raw,timer,state.now_bits)
        part=raw[guid_offset:guid_offset+8]
        if None in part:raise UnknownTerminalTransition139('Unproduced GUID')
        guid=int.from_bytes(bytes(part),'little');sequence=(sequence+1)&f.MASK
        append_packet(221,_packed(guid)+struct.pack('<3II',*xyz,sequence)+b'\x01');stopped.append(guid)
    for raw in units[:state.units_count]:
        if _word(raw,0)==0 and f.to_float(_word(raw,344))>0 and now<f.to_float(f.add(_word(raw,344),_word(raw,340))):stop(raw,316,328,340,344,112)
    for raw in aux[:state.auxiliary_count]:
        if f.to_float(_word(raw,60))>0 and now<f.to_float(f.add(_word(raw,60),_word(raw,56))):stop(raw,32,44,56,60,16,68)
    for raw in claims[:state.claims_count]:
        if not now>=f.to_float(f.add(_word(raw,68),_word(raw,72))):stop(raw,44,56,68,72,24,76,True)
    append_packet(232,_packed(state.source_id)+struct.pack('<I',state.action_sequence1644))
    notification=victory_notification(state);ncap=state.notification_vector_capacity
    if state.notification_count==ncap:ncap=max(4,ncap*2)
    result=replace(state,phase2587=5,action_sequence1644=(state.action_sequence1644+1)&f.MASK,movement_sequence2412=sequence,
        units_storage=tuple(tuple(r)for r in units),auxiliary_storage=tuple(tuple(r)for r in aux),claims_storage=tuple(tuple(r)for r in claims),packet_capacity=capacity,packet_count=count,notification_vector_capacity=ncap,notification_count=state.notification_count+1)
    return TerminalResult139(result,tuple(packets),(notification,),tuple(stopped),'terminal_complete')
