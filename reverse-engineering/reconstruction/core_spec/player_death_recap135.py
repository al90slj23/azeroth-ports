"""Fixed135 full1367 recap in an explicit resolved incoming48 history domain.

History is a borrowed input: no Game/App, pointer allocation, localization,
original program or IO is used. Ring storage and unknown padding are retained.
Only consumed scalar cells and resolved UTF8 slices must be known.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .incoming_history135 import IncomingHistory135
from .record_cells135 import u32
from .terminal_transition135 import _quote,_number

RANKS=('mob','elite','boss','object','none')


class UnknownDeathRecap135(NotImplementedError):pass


@dataclass(frozen=True)
class DeathRecapResult135:
    capacity:int
    raw_hex:str
    selected_slots:tuple
    hit_groups:tuple
    source_groups:tuple
    total_bits:int
    absorbed_bits:int
    avoidable_bits:int


class _JSON:
    def __init__(self,start=b'{'):
        self.data=bytearray(start);self.capacity=len(start);self.first=True
    def append(self,value):
        if len(self.data)+len(value)>self.capacity:
            self.capacity=max(self.capacity*2,len(self.data)+len(value),8)
        self.data.extend(value)
    def key(self,name):
        if not self.first:self.append(b',')
        self.first=False;self.append(_quote(name));self.append(b':')
    def field(self,name,value):self.key(name);self.append(value)
    def number(self,name,value):self.field(name,_number(f.to_float(value)))


def _round85719(value):
    value=f.add(value,(value&f.SIGN)|0x3effffff)
    exponent=(value>>23)&255
    if exponent<=149:
        mask=f.SIGN if exponent<127 else((-8388608)>>((exponent-127)&31))&f.MASK
        value&=mask
    return value


def _positive(value):
    return value if f.to_float(value)>0 else 0


def _metadata(history,slot):
    row=history.storage[slot];texts=history.strings[slot]
    if type(texts)is not tuple or len(texts)!=3 or any(type(x)is not str for x in texts):
        raise UnknownDeathRecap135('Selected source/name/icon UTF8 slices must be explicitly resolved')
    for index,text in enumerate(texts):
        if len(text.encode('utf8'))!=u32(row,index*8+4,'1367 resolved string length'):
            raise ValueError('History UTF8 byte length disagrees with resolved slice')
    classification=row[44];avoidable=row[45]
    if classification is None or avoidable is None:
        raise UnknownDeathRecap135('Selected history classification/avoidable cells are unknown')
    if not 0<=classification<len(RANKS):
        raise UnknownDeathRecap135('Source classification outside restored five-label table')
    value=_JSON()
    for key,text in(('who',texts[0]),('rank',RANKS[classification]),('what',texts[1]),('icon',texts[2])):
        value.field(key,_quote(text))
    value.field('mechanic',b'true'if avoidable else b'false')
    return value


def _total_key(value):
    # Original f32::total_cmp transform, used in descending damage order.
    key=value^(0x7fffffff if value&f.SIGN else 0)
    return key-(1<<32)if key&f.SIGN else key


def recap135(history,reference_time_bits):
    """Return exact JSON/capacity plus semantic grouping diagnostics.

    Original1367 includes all rows >=f32(reference−10), including future rows;
    NaN timestamps fail that ordered comparison. It does not prune the ring.
    Pointers/padding are never read or replaced with zero.
    """
    if not isinstance(history,IncomingHistory135):raise TypeError('Explicit incoming48 ring required')
    if type(reference_time_bits)is not int or not 0<=reference_time_bits<=f.MASK:
        raise ValueError('Exact binary32 reference time required')
    cutoff=f.add(reference_time_bits,0xc1200000);selected=[]
    for index in range(history.count):
        slot=(history.head+index)%history.capacity
        stamp=u32(history.storage[slot],24,'1367 history timestamp')
        if f.to_float(stamp)>=f.to_float(cutoff):selected.append(slot)
    if not selected:
        result=_JSON();result.append(b'}')
        return DeathRecapResult135(result.capacity,bytes(result.data).hex(),(),(),(),f.SIGN,f.SIGN,f.SIGN)
    scalar=lambda slot,o:u32(history.storage[slot],o,'1367 recap scalar')
    total=absorbed=avoidable=f.SIGN;hits=[];sources=[]
    for slot in selected:
        row=history.storage[slot];metadata=_metadata(history,slot)
        damage,shield=scalar(slot,28),scalar(slot,32)
        total=f.add(total,damage);absorbed=f.add(absorbed,shield)
        if row[45]==1:avoidable=f.add(avoidable,damage)
        pair=history.strings[slot][:2]
        if hits and history.strings[hits[-1][0]][:2]==pair and f.to_float(f.sub(scalar(slot,24),scalar(hits[-1][0],24)))<=1:
            old=hits[-1];hits[-1]=(slot,f.add(damage,old[1]),f.add(shield,old[2]),(old[3]+1)&f.MASK)
        else:hits.append((slot,damage,shield,1))
        group=next((i for i,x in enumerate(sources)if history.strings[x[0]][:2]==pair),None)
        if group is None:sources.append((slot,damage,1))
        else:
            old=sources[group];sources[group]=(old[0],f.add(damage,old[1]),(old[2]+1)&f.MASK)
    sources.sort(key=lambda x:_total_key(x[1]),reverse=True)
    hit_array=_JSON(b'[')
    for slot,damage,shield,count in hits[-8:]:
        row=_metadata(history,slot)
        row.number('ago',_positive(f.sub(reference_time_bits,scalar(slot,24))))
        row.number('n',_round85719(damage));row.number('abs',_round85719(shield));row.field('count',_number(count))
        maximum=scalar(slot,40);maximum=maximum if f.to_float(maximum)>1 else 0x3f800000
        ratio=f.div(scalar(slot,36),maximum)
        if f.to_float(ratio)<0:ratio=0
        if f.to_float(ratio)>1:ratio=0x3f800000
        row.number('hp',ratio);row.append(b'}')
        if not hit_array.first:hit_array.append(b',')
        hit_array.first=False;hit_array.append(bytes(row.data))
    hit_array.append(b']')
    source_array=_JSON(b'[')
    for slot,damage,count in sources[:6]:
        row=_metadata(history,slot);row.number('n',_round85719(damage));row.field('count',_number(count));row.append(b'}')
        if not source_array.first:source_array.append(b',')
        source_array.first=False;source_array.append(bytes(row.data))
    source_array.append(b']')
    last=selected[-1];killer=_metadata(history,last)
    killer.number('n',_round85719(scalar(last,28)))
    killer.number('overkill',_round85719(_positive(scalar(last,36)^f.SIGN)));killer.append(b'}')
    age=f.sub(reference_time_bits,scalar(selected[0],24))
    if f.to_float(age)<0:age=0
    if f.to_float(age)>10:age=0x41200000
    output=_JSON();output.number('secs',age);output.number('total',_round85719(total))
    output.number('absorbed',_round85719(absorbed));output.number('avoidable',_round85719(avoidable))
    output.number('maxhp',_round85719(scalar(last,40)));output.field('killer',bytes(killer.data))
    output.field('hits',bytes(hit_array.data));output.field('by',bytes(source_array.data));output.append(b'}')
    return DeathRecapResult135(output.capacity,bytes(output.data).hex(),tuple(selected),tuple(hits),tuple(sources),total,absorbed,avoidable)


def death_recap135(history,reference_time_bits):
    result=recap135(history,reference_time_bits)
    return result.capacity,result.raw_hex
