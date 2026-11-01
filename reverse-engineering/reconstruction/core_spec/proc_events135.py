"""Independent984 kind27 timed-source mutation and1512 recalculation.

The complete36B declarations are explicit inputs. This first branch accepts
the exactly-zero8157 gate used by the retained12 failing fixtures; other gate
families and producer kinds reject. It never clears the timed vector.
"""
from dataclasses import dataclass,replace,asdict
import struct
from . import binary32 as f
from .derived_stats135 import StatsInput,TimedRecord,recalculate
from .level_cycle135 import LevelCycleState
from .death_pickup135 import apply_damage_lifesteal


class UnresolvedProc135(NotImplementedError):pass


@dataclass(frozen=True)
class ProcDefinition135:
    words:tuple

    def __post_init__(self):
        if type(self.words)is not tuple or len(self.words)!=9 or any(type(x)is not int or not 0<=x<=f.MASK for x in self.words):
            raise ValueError('Complete36B definition words required')
        if self.words[0]!=27:raise UnresolvedProc135('Only984 kind27 timed-source producer restored')
        if any(self.words[1:5]):raise UnresolvedProc135('Nonzero8157 event-gate family remains unresolved')
    @classmethod
    def from_hex(cls,raw):
        data=bytes.fromhex(raw)
        if len(data)!=36:raise ValueError('Complete36B definition required')
        return cls(struct.unpack('<9I',data))
    def hex(self):return struct.pack('<9I',*self.words).hex()


@dataclass(frozen=True)
class ProcEvent135:
    raw_hex:str
    def __post_init__(self):
        if len(bytes.fromhex(self.raw_hex))!=36:raise ValueError('Complete36B event required')
    @property
    def bytes(self):return bytes.fromhex(self.raw_hex)


@dataclass(frozen=True)
class ProcState135:
    level:LevelCycleState
    definitions:tuple
    other_sources_absent:bool

    def __post_init__(self):
        if not isinstance(self.level,LevelCycleState)or type(self.definitions)is not tuple:
            raise TypeError('Resolved level and ordered definition snapshots required')
        if self.other_sources_absent is not True:raise UnresolvedProc135('Explicit absence of other984 producers required')
        if len(self.definitions)!=len(self.level.sources.definitions):raise ValueError('Definition source length differs')
        for raw,semantic in zip(self.definitions,self.level.sources.definitions):
            if not isinstance(raw,ProcDefinition135):raise TypeError('Full36B definition snapshots required')
            w=raw.words
            if(w[0],w[1],w[5],w[8]&255)!=(semantic.kind,semantic.value4_bits,semantic.value20_bits,semantic.modifier_tag&255):
                raise ValueError('Full producer and stats definition fields disagree')


@dataclass(frozen=True)
class ProcResult135:
    state:ProcState135
    dirty:bool
    mutations:tuple
    pending:tuple=('Physical source allocation capacity, event messages and speed packet bytes remain separate',)


def zero_gate_matches(event):
    """Exact8157 gate-kind0/selector0: category0 OR flag34 lowbit."""
    raw=event.bytes
    return raw[29]==0 or bool(raw[34]&1)


def _recalculate(level):
    result=recalculate(StatsInput(level=level.progression.level,**asdict(level.stats),**level.sources.keywords()))
    derived={int(k):v for k,v in result['derived_bits'].items()};aux=result['auxiliary_bits'];fields=dict(level.player_fields)
    fields.update({int(k):v for k,v in result['object_fields'].items()})
    stats=replace(level.stats,old_max_hp_bits=derived[1536],current_hp_bits=result['current_hp_bits'],
        previous_speed_bits=result['speed_bits'],pool1532_bits=aux['1444'],pool1536_bits=aux['1448'],
        conditional1348_bits=aux['1348'],pool768_bits=aux['768'])
    return replace(level,stats=stats,derived_bits=tuple(sorted(derived.items())),player_fields=tuple(sorted(fields.items())))


def dispatch_event(state,event):
    if not isinstance(state,ProcState135)or not isinstance(event,ProcEvent135):raise TypeError('Resolved proc state/event required')
    if not zero_gate_matches(event):return ProcResult135(state,False,())
    timed=list(state.level.sources.timed_records);now=state.level.stats.now_bits;mutations=[]
    for index,definition in enumerate(state.definitions):
        cap,duration=definition.words[6:8]
        found=next((j for j,x in enumerate(timed)if x.definition_index==index),None)
        expiry=f.add(now,duration)
        if found is None:
            # Original append is intentionally not capped. A future event on
            # this same definition will take the existing-record min branch.
            timed.append(TimedRecord(index,1,expiry));mutations.append((index,'append',len(timed)-1,1,expiry))
        else:
            old=timed[found]
            # Original !(expiry<=now) also increments NaN expiry.
            stack=(old.stack_count+1)&f.MASK if not f.to_float(old.expires_bits)<=f.to_float(now)else 1
            stack=cap if stack>cap else stack
            timed[found]=TimedRecord(index,stack,expiry);mutations.append((index,'update',found,stack,expiry))
    if not mutations:return ProcResult135(state,False,())
    level=replace(state.level,sources=replace(state.level.sources,timed_records=tuple(timed)))
    level=_recalculate(level)
    return ProcResult135(replace(state,level=level),True,tuple(mutations))


def after_accepted_damage(state,damage_bits,*,context774=None,nonfatal=None):
    """914 context774==0:18353 selfheal, primary0 event, optional secondary2 event.

    Only accepted nonfatal hits are supported; actual lethal914 emits loot
    before post-damage984 and cannot use the predeath cast callback.
    This callback domain is kind27/modifier14 only; its1512 pass changes source
    pools/HP but not cast coefficients. Other modifier types need independent
    proof of cast-loop scalar reloads before they can use this callback.
    """
    if nonfatal is not True:
        raise UnresolvedProc135('Explicit accepted nonfatal hit required; lethal914 loot/proc ordering remains unresolved')
    if type(context774)is not int or context774!=0:
        raise UnresolvedProc135('Explicit original context774==0 required; unknown/nonzero context remains unresolved')
    if type(damage_bits)is not int or not 0<=damage_bits<=f.MASK or not f.to_float(damage_bits)>=1:
        raise ValueError('Accepted914 final minimum1 damage word required')
    if any(d.words[8]&255!=14 for d in state.definitions):
        raise UnresolvedProc135('Accepted-hit callback currently restores kind27/modifier14 only')
    if state.level.sources.live_effects or state.level.sources.passives or state.level.sources.owned_skills:
        raise UnresolvedProc135('Additional damage/event source domain unresolved')
    if any(x.tag&255!=14 for x in state.level.sources.item_modifiers)or any(x.tag&255!=18 for x in state.level.sources.adjustments):
        raise UnresolvedProc135('Only explicit item14/adjustment18 lifesteal sources accepted')
    level=apply_damage_lifesteal(state.level,damage_bits);state=replace(state,level=level)
    primary=ProcEvent135(bytes(36).hex())
    first=dispatch_event(state,primary)
    raw=bytearray(36);raw[29]=2
    second=dispatch_event(first.state,ProcEvent135(raw.hex()))
    return ProcResult135(second.state,first.dirty or second.dirty,first.mutations+second.mutations)
