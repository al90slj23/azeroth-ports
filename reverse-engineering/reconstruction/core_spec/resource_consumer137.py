"""Independent137 resource10291 effects over explicit empty-profile sources.

The original full10291 must execute1514/1151 and real localization when used
as an oracle. This model currently predicts numeric/live owner state; aura,
full keyed-tree and wire/notification outputs remain explicitly unmodeled.
No original binary, memory, files, host callback or original result is read.
"""
from dataclasses import dataclass,replace
import math,struct

from . import binary32 as f
from .derived_stats135 import StatsInput,LiveEffect,recalculate
from .record_cells135 import cells135,u32,u64,put_u32
from .opening_npc_pickups135 import OpeningVector135
from .binary32_sqrt import sqrt_bits


class PendingResourceConsumer137(NotImplementedError):
    pass


@dataclass(frozen=True)
class LiveVector137:
    storage: tuple
    count: int

    def __post_init__(self):
        if not 0<=self.count<=len(self.storage)<=4096:
            raise ValueError('Explicit physical32B live vector required')
        for row in self.storage:
            if len(row)!=32 or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in row):
                raise ValueError('Each live32 cell must be an exact byte or None')

    @property
    def capacity(self):return len(self.storage)


@dataclass(frozen=True)
class ResourceConsumerState137:
    stats: StatsInput
    derived_bits: tuple
    player_fields: tuple
    live: LiveVector137
    heal_gate387: int
    rng_words: tuple
    counter2408: int
    message_sequence2412: int
    action_sequence1644: int


@dataclass(frozen=True)
class ResourceConsumerResult137:
    state: ResourceConsumerState137
    kind: int
    spell_id: int
    removed_live_count: int
    heal_request_bits: int
    heal_delta_bits: int
    pending: tuple = ('1151 aura48/full keyed fields and complete wire messages/notifications not independently predicted',
        'Collection2862 geometry/destruction and physical56B compaction remain separate')


def _finite(bits):
    if type(bits)is not int or not 0<=bits<=f.MASK or bits&0x7fffffff>=f.INF:
        raise ValueError('Finite binary32 input required')


def _ceil_u(bits):
    value=f.to_float(bits)
    return 0 if math.isnan(value)or value<=0 else min(math.ceil(value),f.MASK)


def _semantics(live):
    effects=[]
    for row in live.storage[:live.count]:
        kind=u32(row,8,'Live kind');spell=u32(row,20,'Live spell');expires=u32(row,24,'Live expiry')
        if kind!=0:
            raise PendingResourceConsumer137('Only effect0 resource/other inert live sources restored in this domain')
        #1514 kind0 does not consume the raw magnitude at+12. Keep its
        #physical bytes untouched instead of assigning them a numeric meaning.
        effects.append(LiveEffect(kind,0,spell,expires))
    return effects


def consume_resource137(state: ResourceConsumerState137,kind):
    if not isinstance(state,ResourceConsumerState137)or not isinstance(state.stats,StatsInput):
        raise TypeError('Explicit137 resource state and stat sources required')
    if kind not in(3,4,5):raise PendingResourceConsumer137('Only resource kinds3..5 restored')
    stats=state.stats
    if any(getattr(stats,name)for name in('passives','adjustments','item_modifiers','owned_skills','timed_records','timed_definitions')):
        raise PendingResourceConsumer137('Nonempty external item/talent/timed source producers remain separate')
    if stats.conditional1344_id==11426:raise PendingResourceConsumer137('Icebarrier source cleanup requires separate137 mapping')
    if not 0<=state.heal_gate387<=255:raise ValueError('Explicit healing gate byte required')
    for bits in(stats.now_bits,stats.old_max_hp_bits,stats.current_hp_bits):_finite(bits)
    derived=dict(state.derived_bits);fields=dict(state.player_fields);live=state.live
    if derived[1536]!=stats.old_max_hp_bits:raise ValueError('Canonical maxHP owners disagree')
    _semantics(live)
    if kind==5:
        request=f.mul(derived[1536],0x3f000000)
        request=f.mul(request,0x3f000000 if state.heal_gate387>4 else 0x3f800000)
        candidate=f.add(stats.current_hp_bits,request)
        hp=candidate if f.to_float(candidate)<f.to_float(derived[1536])else derived[1536]
        delta=f.sub(hp,stats.current_hp_bits)
        fields.update({22:_ceil_u(hp),28:_ceil_u(derived[1536])})
        result=replace(state,stats=replace(stats,current_hp_bits=hp),player_fields=tuple(sorted(fields.items())))
        return ResourceConsumerResult137(result,kind,23493,0,request,delta)
    spell,duration=(23451,0x41200000)if kind==3 else(23505,0x41700000)
    rows=[list(row)for row in live.storage];write=0
    for read in range(live.count):
        if u32(rows[read],20,'Live stable-removal spell')==spell:continue
        if read!=write:rows[write]=rows[read].copy()
        write+=1
    removed=live.count-write
    if write==len(rows):
        capacity=max(4,2*len(rows));rows.extend([[None]*32 for _ in range(capacity-len(rows))])
    row=rows[write]
    for offset,value in((0,0),(4,0),(8,0),(20,spell),(24,f.add(stats.now_bits,duration)),(28,0)):
        put_u32(row,offset,value)
    live=LiveVector137(tuple(tuple(row)for row in rows),write+1)
    rebuilt=recalculate(replace(stats,live_effects=_semantics(live)))
    aux=rebuilt['auxiliary_bits'];new_derived={int(k):v for k,v in rebuilt['derived_bits'].items()}
    fields.update({int(k):v for k,v in rebuilt['object_fields'].items()})
    new_stats=replace(stats,old_max_hp_bits=new_derived[1536],current_hp_bits=rebuilt['current_hp_bits'],
        previous_speed_bits=rebuilt['speed_bits'],pool1532_bits=aux['1444'],pool1536_bits=aux['1448'],
        conditional1348_bits=aux['1348'],pool768_bits=aux['768'],live_effects=_semantics(live))
    result=replace(state,stats=new_stats,derived_bits=tuple(sorted(new_derived.items())),
        player_fields=tuple(sorted(fields.items())),live=live,
        action_sequence1644=(state.action_sequence1644+int(rebuilt['speed_changed']))&f.MASK)
    return ResourceConsumerResult137(result,kind,spell,removed,0,0)


@dataclass(frozen=True)
class ResourceCollectionInput137:
    state: ResourceConsumerState137
    pickups: OpeningVector135
    player_xyz_bits: tuple
    claims_empty: bool


@dataclass(frozen=True)
class ResourceCollectionResult137:
    state: ResourceConsumerState137
    pickups: OpeningVector135
    consumed: tuple
    destroy170_hex: tuple
    pending: tuple = ('Non-resource nearby consumers, claims/auxiliary GUIDs and XP/coin remain outside this resource slice',
        'Full aura/wire/localized notification semantics remain unmodeled; original callees run intact')


def collect_resources137(value: ResourceCollectionInput137):
    """2862 resource geometry→reverse31727 compaction→actual effect order.

    Eligibility snapshots XY at entry and uses binary32 sqrt<=3 independent
    of amount or Z, within the valid live marker0/1 input domain. Original
    selected marker2 compacts then panics in31727; it is not a successful
    destroy-suppression variant. Far kind2 records are retained untouched.
    """
    if value.claims_empty is not True:raise PendingResourceConsumer137('Claim producer/membership requires separate137 ownership')
    if not isinstance(value.pickups,OpeningVector135)or value.pickups.stride!=56:
        raise ValueError('Complete physical56B owner required')
    if len(value.player_xyz_bits)!=3:raise ValueError('Explicit playerXYZ required')
    for x in value.player_xyz_bits:_finite(x)
    selected=[];rows=[list(row)for row in value.pickups.storage]
    for index,row in enumerate(rows[:value.pickups.count]):
        kind=u32(row,8,'Pickup kind')
        if kind in(0,1):raise PendingResourceConsumer137('XP/coin first-pass attraction and consumers are separate')
        if u32(row,0,'Live pickup marker')not in(0,1):
            raise PendingResourceConsumer137('Only live marker0/1 admitted; selected marker2 has original31727 partial-compaction/panic evidence')
        dx=f.sub(u32(row,40,'Pickup x'),value.player_xyz_bits[0]);dy=f.sub(u32(row,44,'Pickup y'),value.player_xyz_bits[1])
        distance=sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy)))
        if not f.to_float(distance)<=3:continue
        if kind not in(3,4,5):raise PendingResourceConsumer137('Nearby non-resource kind consumer remains unknown')
        if u32(row,24,'Pickup auxiliary capacity')or u32(row,32,'Pickup auxiliary count'):
            raise PendingResourceConsumer137('Auxiliary GUID destruction/free requires explicit producer')
        selected.append(index)
    state=value.state;count=value.pickups.count;events=[];packets=[]
    for index in reversed(selected):
        row=rows[index];kind=u32(row,8,'Resource dispatch kind');guid=u64(row,16,'Resource destruction GUID')
        marker=u32(row,0,'Resource destruction marker')
        for j in range(index,count-1):rows[j]=rows[j+1].copy()
        count-=1
        packets.append(struct.pack('<Q',guid).hex())
        result=consume_resource137(state,kind);state=result.state
        events.append((index,kind,guid,result.spell_id))
    return ResourceCollectionResult137(state,OpeningVector135(56,tuple(tuple(row)for row in rows),count),tuple(events),tuple(packets))
