"""Narrow1073 post-history callback completion proof over complete sources.

This does not run the incoming prefix, registry/history producer, minimum-one
clamp, revival, death, keyedHP or Aura. It never replaces missing sources with
empty vectors. The caller supplies sources at the point after history append,
including shield-break/earlier-callback effects already reflected in the owner.
"""
from dataclasses import dataclass
from . import binary32 as f
from .record_cells135 import cells135,u32,UnknownRecordRead135

class UnknownIncomingCallbacks135(NotImplementedError):pass

def _uint(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:raise ValueError('Explicit uint'+str(bits)+' required')
    return value

@dataclass(frozen=True)
class CallbackVector135:
    stride:int
    count:int
    storage:tuple
    capacity_word:int|None=None

    def __post_init__(self):
        if self.stride not in(8,32,36):raise ValueError('Only item8/live32/modifier36 callback sources')
        if type(self.storage)is not tuple or len(self.storage)>4096 or type(self.count)is not int or not 0<=self.count<=len(self.storage):raise ValueError('Complete bounded active source records/count required')
        if self.capacity_word is not None:
            _uint(self.capacity_word)
            if not len(self.storage)<=self.capacity_word<=4096:raise ValueError('Explicit capacity cannot be smaller than supplied backing')
        for row in self.storage:cells135(row,self.stride)

    @property
    def capacity(self):return self.capacity_word

@dataclass(frozen=True)
class IncomingCallbacksInput135:
    now_bits:int
    hp_after_history1440_bits:int
    source_guid:int
    contact_flag3:int
    phase2587:int
    item_retaliation_base_bits:int
    live32:CallbackVector135
    items8:CallbackVector135
    modifiers36:CallbackVector135

    def __post_init__(self):
        for value in(self.now_bits,self.hp_after_history1440_bits,self.contact_flag3,self.item_retaliation_base_bits):_uint(value)
        _uint(self.source_guid,64);_uint(self.phase2587,8)
        for source,stride in((self.live32,32),(self.items8,8),(self.modifiers36,36)):
            if source is None:raise UnknownIncomingCallbacks135('Unresolved physical callback source vector'+str(stride))
            if not isinstance(source,CallbackVector135)or source.stride!=stride:raise TypeError('Complete typed callback source vector required')

@dataclass(frozen=True)
class IncomingCallbacksProof135:
    hp_before_minimum_one1440_bits:int
    raw13_sum_bits:int
    item22_sum_bits:int|None
    skipped_914_calls:tuple
    returned_984_calls:int
    modifier_noevent_tags:tuple
    input_counts:tuple
    branch:str

    @property
    def callbacks_complete(self):return True

def active_raw13_sum135(live32,now_bits):
    """1073 ordered active32 reduction;not a whole-callback completion proof."""
    _uint(now_bits)
    if not isinstance(live32,CallbackVector135)or live32.stride!=32:raise TypeError('Complete live32 source required')
    result=0x80000000
    for row in live32.storage[:live32.count]:
        if f.to_float(now_bits)<f.to_float(u32(row,24,'1073 raw13 expiry')):
            if u32(row,8,'1073 raw13 kind')==13:result=f.add(result,u32(row,12,'1073 raw13 value'))
    return result

def prove_post_history_callbacks135(value):
    """Return proof only when every post-history callback is known to be inert.

    A positive active raw13 sum can call914 and is rejected. Positive item22
    sum with positive original/mode-scaled input amount likewise is rejected.
    984 accepts empty sources or explicit full36B tag54 records: its dispatch
    selector41 jumps directly to common exit, never enabling1512 or an event.
    Other modifier kinds are unresolved, not assumed inactive from event flags.
    Unknown consumed bytes raise UnknownRecordRead135; None padding is retained.
    """
    if not isinstance(value,IncomingCallbacksInput135):raise TypeError('Explicit post-history callback input required')
    if value.phase2587!=1:raise UnknownIncomingCallbacks135('Narrow proof requires current phase1')
    raw13=active_raw13_sum135(value.live32,value.now_bits)
    counts=(value.live32.count,value.items8.count,value.modifiers36.count)
    if value.source_guid==0 or value.contact_flag3==0:
        return IncomingCallbacksProof135(value.hp_after_history1440_bits,raw13,None,('raw13','item22'),0,(),counts,'source_or_contact_gate_skips_entire_callback_block')
    if f.to_float(raw13)>0:raise UnknownIncomingCallbacks135('Active raw13 retaliation can enter914 and change full state before HP reread')
    item22=0x80000000
    for row in value.items8.storage[:value.items8.count]:
        cells=cells135(row,8)
        if cells[0]is None:
            raise UnknownRecordRead135(0,1,'1073 item22 kind byte')
        if cells[0]==22:item22=f.add(item22,u32(cells,4,'1073 item22 value'))
    if value.items8.count and f.to_float(value.item_retaliation_base_bits)>0 and f.to_float(item22)>0:
        raise UnknownIncomingCallbacks135('Positive item22 retaliation can enter914;temporary774=3 is not an inertness proof')
    noevent=[]
    for row in value.modifiers36.storage[:value.modifiers36.count]:
        kind=u32(row,0,'984 modifier kind')
        if kind!=54:raise UnknownIncomingCallbacks135('Unrestored984 modifier kind '+str(kind))
        #984 snapshots the entire36B record before dispatch. Require those
        #actual consumed bytes; never invent its payload from semantic fields.
        full=cells135(row,36)
        if any(v is None for v in full):
            for offset in range(0,36,4):u32(row,offset,'984 copied modifier36 payload')
        noevent.append(kind)
    return IncomingCallbacksProof135(value.hp_after_history1440_bits,raw13,item22,('raw13','item22'),2,tuple(noevent),counts,'source_contact_active_no914_and_two_inert984')
