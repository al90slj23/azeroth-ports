"""Complete fixed135 live32 physical owner operations.

G1704/1708/1712 are capacity/pointer/count. The pointer is an original allocator
observation, not an independent producer input. Storage retains every capacity
row, including inactive known bytes and None cells. A semantic zero for a
payload-free variant never writes a zero into physical storage.
"""
from dataclasses import dataclass
from . import binary32 as f
from .derived_stats135 import LiveEffect
from .record_cells135 import cells135,encode_row,u32,u64,put_u32
from .resource_consumer135 import LiveVector135


class PendingLiveOwner135(NotImplementedError):
    pass


@dataclass(frozen=True)
class ScratchAuxiliaryWord135:
    """An explicit922 effect8/9 entry-frame+48 source, not an unwritten slot.

    bits=None deliberately records a still-unresolved caller-stack value. A
    controller must carry that source through every physical copy, rather
    than relabel it allocator padding or silently substitute semantic zero.
    """
    bits: int|None
    source: str = '922.effect8or9.caller_frame+48'

    def __post_init__(self):
        if self.source != '922.effect8or9.caller_frame+48':
            raise ValueError('Exact922 frame-source identity required')
        if self.bits is not None:
            _word(self.bits)


def _owner(value):
    if not isinstance(value,LiveVector135):
        raise TypeError('Explicit complete LiveVector135 storage/count owner required')
    if type(value.storage)is not tuple or type(value.count)is not int or any(type(row)is not tuple for row in value.storage):
        raise TypeError('Immutable live32 backing and exact count required')
    return value


def _word(value):
    if type(value)is not int or not 0<=value<=f.MASK:
        raise ValueError('A physical live word write requires an explicit u32, never None')
    return value


def live_active_cells135(owner):
    """Checked physical active view; neither hex materialization nor zero fill."""
    owner=_owner(owner)
    return owner.storage[:owner.count]


def retain_live135(owner,predicate):
    """Original forward retain: whole32B copies into holes; tail untouched.

    The predicate receives immutable original active rows. Its exact family
    rule belongs to the admitted consumer, never inferred from final semantics.
    """
    owner=_owner(owner)
    if not callable(predicate):raise TypeError('Explicit live retain predicate required')
    rows=list(owner.storage);write=0
    for read,row in enumerate(owner.storage[:owner.count]):
        keep=predicate(row)
        if type(keep)is not bool:raise TypeError('Retain predicate must return a bool')
        if keep:
            if write!=read:rows[write]=row
            write+=1
    return LiveVector135(tuple(rows),write)


def append_live135(owner,word_writes):
    """65320 reserve then append partial words; omitted offsets inherit slot.

    Newly allocated cells are unknown. Existing capacity rows are retained
    exactly. Unknown *written* source values require a separate typed producer
    and are deliberately rejected here instead of masking an old known word.
    """
    owner=_owner(owner)
    if type(word_writes)is not tuple or not word_writes:
        raise TypeError('Explicit ordered tuple of nonempty u32 word writes required')
    offsets=[]
    for item in word_writes:
        if type(item)is not tuple or len(item)!=2:raise TypeError('Word write is(offset,u32)')
        offset,value=item
        if type(offset)is not int or offset not in range(0,32,4):raise ValueError('Aligned live32 offset required')
        offsets.append(offset);_word(value)
    if len(set(offsets))!=len(offsets):raise ValueError('A physical word may be written only once')
    rows=list(owner.storage)
    if owner.count==owner.capacity:
        capacity=max(4,2*owner.capacity)
        if capacity>4096:raise PendingLiveOwner135('Live allocation exceeds admitted4096 capacity')
        rows.extend([(None,)*32]*(capacity-owner.capacity))
    row=list(rows[owner.count])
    for offset,value in word_writes:put_u32(row,offset,value)
    rows[owner.count]=tuple(row)
    return LiveVector135(tuple(rows),owner.count+1)


def append_self_buff_scratch135(owner,word_writes,source):
    """Append only after an explicit typed source binds922's live+16 write.

    The general append still rejects None. This exact source-specific writer
    may overwrite even a previously known+16 word with caller-stack unknown
    cells, and its caller must preserve the returned source-write descriptor.
    """
    if not isinstance(source,ScratchAuxiliaryWord135):
        raise TypeError('Explicit typed922 scratch+48 source required')
    if any(offset==16 for offset,value in word_writes):
        raise ValueError('Auxiliary+16 is owned only by the typed scratch source')
    writes=word_writes+((16,source.bits),)if source.bits is not None else word_writes
    result=append_live135(owner,writes)
    if source.bits is None:
        rows=list(result.storage);row=list(rows[result.count-1]);row[16:20]=[None]*4
        rows[result.count-1]=tuple(row);result=LiveVector135(tuple(rows),result.count)
    return result,(result.count-1,16,source)


def live_semantics135(owner,*,allowed_kinds,zero_magnitude_kinds=(0,12)):
    """Layout projection only; caller must prove its admitted source families.

    Current kind0/12 variants have no consumed magnitude. Returning their
    semantic zero leaves physical+12, including known bytes or None, untouched.
    Other variants require an actually known magnitude word.
    """
    owner=_owner(owner)
    if type(allowed_kinds)is not tuple or not set(allowed_kinds)<={0,7,8,9,12}:
        raise ValueError('Explicit admitted fixed135 live kind tuple required')
    if type(zero_magnitude_kinds)is not tuple or not set(zero_magnitude_kinds)<={0,12}:
        raise ValueError('Only proven payload-free0/12 semantic variants admitted')
    result=[]
    for row in owner.storage[:owner.count]:
        kind=u32(row,8,'live_owner135.kind')
        if kind not in allowed_kinds:raise PendingLiveOwner135('Live family outside explicit consumer contract')
        value=0 if kind in zero_magnitude_kinds else u32(row,12,'live_owner135.magnitude')
        result.append(LiveEffect(kind,value,u32(row,20,'live_owner135.spell'),u32(row,24,'live_owner135.expiry')))
    return tuple(result)


def retain_owner0_spell_live135(owner,spell_id):
    """922 effect8/9 removes matching spell only for owner64==0."""
    _word(spell_id)
    return retain_live135(owner,lambda row:u32(row,20,'922 spell')!=spell_id or u64(row,0,'922 owner')!=0)


def resume_live1020_135(owner,now_bits,*,resumption_explicit=False):
    """4600 running resumption: remove1020, append12 without+12/+16 writes."""
    _word(now_bits)
    if resumption_explicit is not True:
        raise PendingLiveOwner135('Explicit proven running-resumption branch required')
    if now_bits&0x7fffffff>=f.INF:raise PendingLiveOwner135('Finite resumption clock domain required')
    retained=retain_live135(owner,lambda row:u32(row,20,'4600 old spell')!=1020)
    return append_live135(retained,((0,0),(4,0),(8,12),(20,1020),(24,f.add(now_bits,0x3f800000)),(28,0)))


def live_view_cells135(owner,records,unspecified=()):
    """Bind a legacy/typed active view to its one authoritative full backing.

    The legacy unspecified marks can only remove knowledge already absent in
    the canonical owner. They can never hide a canonical known byte.
    """
    owner=_owner(owner)
    if type(records)is not tuple or len(records)!=owner.count or type(unspecified)is not tuple:
        raise ValueError('Exact active view/count and immutable unknown-word marks required')
    rows=[cells135(row,32)for row in records]
    seen=set()
    for item in unspecified:
        if type(item)is not tuple or len(item)!=2:raise ValueError('Unknown word mark is(index,offset)')
        index,offset=item
        if type(index)is not int or not 0<=index<owner.count or type(offset)is not int or offset not in range(0,32,4)or item in seen:
            raise ValueError('Unique aligned unknown word mark required')
        seen.add(item)
        if owner.storage[index][offset:offset+4]!=(None,)*4:
            raise ValueError('Unknown view mark cannot erase canonical known bytes')
        rows[index][offset:offset+4]=[None]*4
    if tuple(tuple(row)for row in rows)!=owner.storage[:owner.count]:
        raise ValueError('Active view and canonical physical owner disagree')
    return tuple(tuple(row)for row in rows)


def live_active_view135(owner):
    """Return None-aware rows and exactly whole-unknown-word compatibility marks."""
    rows=live_active_cells135(owner)
    marks=tuple((i,o)for i,row in enumerate(rows)for o in range(0,32,4)if row[o:o+4]==(None,)*4)
    return tuple(encode_row(row)for row in rows),marks
