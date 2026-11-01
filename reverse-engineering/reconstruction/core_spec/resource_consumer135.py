"""Independent135 resource10298 effects over explicit empty-profile sources.

Full original10298/2862 must execute1512/1202 and real localization as oracle.
This model predicts numeric/live/pickup/aura owners and keyed fields in its
explicit source domain, plus170/306/226/150 and English rune notification JSON.
No original binary, memory, files, host callback or original result is read.
"""
from dataclasses import dataclass,replace
import json,math,struct

from . import binary32 as f
from .derived_stats135 import StatsInput,LiveEffect,recalculate
from .record_cells135 import cells135,u32,u64,put_u32
from .opening_npc_pickups135 import OpeningVector135
from .binary32_sqrt import sqrt_bits
from .opening_entities135 import packed_guid
from .resource_aura135 import ResourceAuraState135,rebuild_resource_aura135


class PendingResourceConsumer135(NotImplementedError):
    pass


@dataclass(frozen=True)
class LiveVector135:
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
class ResourceConsumerState135:
    stats: StatsInput
    derived_bits: tuple
    player_fields: tuple
    live: LiveVector135
    heal_gate387: int
    rng_words: tuple
    counter2408: int
    message_sequence2412: int
    action_sequence1644: int
    player_guid: int
    aura: ResourceAuraState135
    aura_external_sources_absent: bool
    notification_next_id14340336: int
    locale_code: str


@dataclass(frozen=True)
class ResourceConsumerResult135:
    state: ResourceConsumerState135
    kind: int
    spell_id: int
    removed_live_count: int
    heal_request_bits: int
    heal_delta_bits: int
    packets: tuple = ()
    events: tuple = ()
    notifications: tuple = ()
    pending: tuple = ('Non-English resource labels remain a separate localization domain',
        'Nonempty external sources, negative/duplicate-kind8 and other aura producers are separate')


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
        if kind not in(0,8):
            raise PendingResourceConsumer135('Only effect0 and explicit positive Battlekind8 live sources restored')
        magnitude=0 if kind==0 else u32(row,12,'Battle effect strength')
        if kind==8:
            _finite(magnitude)
            if f.to_float(magnitude)<0:raise PendingResourceConsumer135('Negative kind8 aura domain remains separate')
        #Kind0's loaded raw magnitude is not consumed by1512 or the admitted
        #1202 dominance branch. Preserve its physical bytes, including None.
        effects.append(LiveEffect(kind,magnitude,spell,expires))
    return effects


def resource_spell_go306_135(guid,spell):
    if type(guid)is not int or not 0<=guid<1<<64:raise ValueError('Exact playerGUID required')
    packed=packed_guid(guid)
    return(packed+packed+struct.pack('<IHBQBH',spell,256,1,guid,0,0)).hex()


def resource_notification135(state,kind):
    if state.locale_code!='en':raise PendingResourceConsumer135('Only explicit original English rune labels restored')
    number=state.notification_next_id14340336
    if type(number)is not int or not 0<=number<=f.MASK:raise ValueError('Explicit14340336 notification owner word required')
    name={3:'Speed Rune',4:'Berserker Rune',5:'Restoration Rune'}[kind]
    text=name+'!'
    #10434 serializes this ordered record.15915's name/text sanitization has no
    #effect on the declared constant English labels (no tab/newline/; or =).
    raw=json.dumps(dict(type='banner',id=number,kind='rune',text=text,name=name,boss=False),
        ensure_ascii=False,separators=(',',':')).encode('utf8')
    chat=('AZSBANNER\tid='+str(number)+';kind=rune;boss=0;name='+name+';text='+text).encode('utf8')
    payload=struct.pack('<BIQI',6,f.MASK,state.player_guid,len(chat)+1)+chat+b'\0\0'
    return payload.hex(),raw.hex(),(number+1)&f.MASK


def consume_resource135(state: ResourceConsumerState135,kind):
    if not isinstance(state,ResourceConsumerState135)or not isinstance(state.stats,StatsInput):
        raise TypeError('Explicit135 resource state and stat sources required')
    if kind not in(3,4,5):raise PendingResourceConsumer135('Only resource kinds3..5 restored')
    stats=state.stats
    if state.aura_external_sources_absent is not True:
        raise PendingResourceConsumer135('Owned/default-kind12, definition38 and other external aura sources require explicit continuation')
    if any(getattr(stats,name)for name in('passives','adjustments','item_modifiers','owned_skills','timed_records','timed_definitions')):
        raise PendingResourceConsumer135('Nonempty external item/talent/timed source producers remain separate')
    if stats.conditional1344_id==11426:raise PendingResourceConsumer135('Icebarrier source cleanup requires separate135 mapping')
    if not 0<=state.heal_gate387<=255:raise ValueError('Explicit healing gate byte required')
    for bits in(stats.now_bits,stats.old_max_hp_bits,stats.current_hp_bits):_finite(bits)
    derived=dict(state.derived_bits);fields=dict(state.player_fields);live=state.live
    if derived[1536]!=stats.old_max_hp_bits:raise ValueError('Canonical maxHP owners disagree')
    _semantics(live)
    if not isinstance(state.aura,ResourceAuraState135):raise ValueError('Explicit physical aura owner required')
    banner,notification,next_id=resource_notification135(state,kind)
    if kind==5:
        request=f.mul(derived[1536],0x3f000000)
        request=f.mul(request,0x3f000000 if state.heal_gate387>4 else 0x3f800000)
        candidate=f.add(stats.current_hp_bits,request)
        hp=candidate if f.to_float(candidate)<f.to_float(derived[1536])else derived[1536]
        delta=f.sub(hp,stats.current_hp_bits)
        fields.update({22:_ceil_u(hp),28:_ceil_u(derived[1536])})
        result=replace(state,stats=replace(stats,current_hp_bits=hp),player_fields=tuple(sorted(fields.items())),
            notification_next_id14340336=next_id)
        return ResourceConsumerResult135(result,kind,23493,0,request,delta,
            packets=((306,resource_spell_go306_135(state.player_guid,23493)),(150,banner)),
            events=(('resource_heal',kind,23493,request,delta),('resource_notification',kind,9008,state.notification_next_id14340336)),
            notifications=(notification,))
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
    live=LiveVector135(tuple(tuple(row)for row in rows),write+1)
    rebuilt=recalculate(replace(stats,live_effects=_semantics(live)))
    aux=rebuilt['auxiliary_bits'];new_derived={int(k):v for k,v in rebuilt['derived_bits'].items()}
    fields.update({int(k):v for k,v in rebuilt['object_fields'].items()})
    new_stats=replace(stats,old_max_hp_bits=new_derived[1536],current_hp_bits=rebuilt['current_hp_bits'],
        previous_speed_bits=rebuilt['speed_bits'],pool1532_bits=aux['1444'],pool1536_bits=aux['1448'],
        conditional1348_bits=aux['1348'],pool768_bits=aux['768'],live_effects=_semantics(live))
    aura_result=rebuild_resource_aura135(live.storage,live.count,stats.now_bits,state.aura,tuple(sorted(fields.items())))
    result=replace(state,stats=new_stats,derived_bits=tuple(sorted(new_derived.items())),
        player_fields=aura_result.player_fields,live=live,aura=aura_result.aura,
        action_sequence1644=(state.action_sequence1644+int(rebuilt['speed_changed']))&f.MASK,
        notification_next_id14340336=next_id)
    packets=[(306,resource_spell_go306_135(state.player_guid,spell))]
    if rebuilt['speed_changed']:
        packets.append((226,(packed_guid(state.player_guid)+struct.pack('<II',state.action_sequence1644,rebuilt['speed_bits'])).hex()))
    packets.append((150,banner))
    return ResourceConsumerResult135(result,kind,spell,removed,0,0,
        packets=tuple(packets),events=(('resource_buff',kind,spell,f.add(stats.now_bits,duration)),*aura_result.events,
         ('resource_notification',kind,9006 if kind==3 else 9007,state.notification_next_id14340336)),notifications=(notification,))


@dataclass(frozen=True)
class ResourceCollectionInput135:
    state: ResourceConsumerState135
    pickups: OpeningVector135
    player_xyz_bits: tuple
    claims_empty: bool


@dataclass(frozen=True)
class ResourceCollectionResult135:
    state: ResourceConsumerState135
    pickups: OpeningVector135
    consumed: tuple
    destroy170_hex: tuple
    packets: tuple
    events: tuple
    notifications: tuple
    pending: tuple = ('Non-resource nearby consumers, claims/auxiliary GUIDs and XP/coin remain outside this resource slice',
        'Non-English resource notification labels and external aura sources remain separate')


def collect_resources135(value: ResourceCollectionInput135):
    """2862 resource geometry→reverse31732 compaction→actual effect order.

    Eligibility snapshots XY at entry and uses binary32 sqrt<=3 independent
    of amount or Z, within the valid live marker0/1 input domain. Original
    selected marker2 compacts then panics in31732; it is not a successful
    destroy-suppression variant. Far kind2 records are retained untouched.
    """
    if value.claims_empty is not True:raise PendingResourceConsumer135('Claim producer/membership requires separate135 ownership')
    if not isinstance(value.pickups,OpeningVector135)or value.pickups.stride!=56:
        raise ValueError('Complete physical56B owner required')
    if len(value.player_xyz_bits)!=3:raise ValueError('Explicit playerXYZ required')
    for x in value.player_xyz_bits:_finite(x)
    selected=[];rows=[list(row)for row in value.pickups.storage]
    for index,row in enumerate(rows[:value.pickups.count]):
        kind=u32(row,8,'Pickup kind')
        if kind in(0,1):raise PendingResourceConsumer135('XP/coin first-pass attraction and consumers are separate')
        if u32(row,0,'Live pickup marker')not in(0,1):
            raise PendingResourceConsumer135('Only live marker0/1 admitted; selected marker2 has original31732 partial-compaction/panic evidence')
        dx=f.sub(u32(row,40,'Pickup x'),value.player_xyz_bits[0]);dy=f.sub(u32(row,44,'Pickup y'),value.player_xyz_bits[1])
        distance=sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy)))
        if not f.to_float(distance)<=3:continue
        if kind not in(3,4,5):raise PendingResourceConsumer135('Nearby non-resource kind consumer remains unknown')
        if u32(row,24,'Pickup auxiliary capacity')or u32(row,32,'Pickup auxiliary count'):
            raise PendingResourceConsumer135('Auxiliary GUID destruction/free requires explicit producer')
        selected.append(index)
    state=value.state;count=value.pickups.count;events=[];packets=[];wire=[];effects=[];notifications=[]
    for index in reversed(selected):
        row=rows[index];kind=u32(row,8,'Resource dispatch kind');guid=u64(row,16,'Resource destruction GUID')
        marker=u32(row,0,'Resource destruction marker')
        for j in range(index,count-1):rows[j]=rows[j+1].copy()
        count-=1
        destroy=struct.pack('<Q',guid).hex();packets.append(destroy);wire.append((170,destroy))
        result=consume_resource135(state,kind);state=result.state;wire.extend(result.packets);effects.extend(result.events);notifications.extend(result.notifications)
        events.append((index,kind,guid,result.spell_id))
    return ResourceCollectionResult135(state,OpeningVector135(56,tuple(tuple(row)for row in rows),count),tuple(events),tuple(packets),tuple(wire),tuple(effects),tuple(notifications))
