"""Fixed135 resource-live2088 prefix on one canonical level/context owner.

Only inert23451/23505 kind0, unique1020 kind12 and positive kind8 source
families are admitted. Full2088 is the oracle; owned/basic1076 scheduling and
1453's presentation/statistics remain the composition owner's next domains.
"""
from dataclasses import asdict,dataclass,replace
import math,struct

from . import binary32 as f
from .derived_stats135 import StatsInput,LiveEffect,recalculate
from .level_cycle135 import LevelCycleState
from .mixed_resource135 import MixedResourceContext135,validate_mixed_resource135
from .resource_consumer135 import LiveVector135,_semantics
from .resource_aura135 import rebuild_resource_aura135
from .record_cells135 import u32
from .opening_entities135 import packed_guid
from .player_update135 import _minnum,_positive,_ceil_u32


class PendingResourcePlayerUpdate135(NotImplementedError):pass


@dataclass(frozen=True)
class ResourcePlayerUpdateResult135:
    level:LevelCycleState
    context:MixedResourceContext135
    expired_spell_ids:tuple
    recalculated:bool
    regen_request_bits:int
    heal_delta_bits:int
    events:tuple
    packets:tuple
    pending:tuple=('1453 healaccount presentation/statistics remain raw observations',
        '1076 owned/basic dispatch follows this prefix and is not executed by this component')


def _word(value):
    if type(value)is not int or not 0<=value<=f.MASK:raise ValueError('Explicit u32/binary32 input required')


def prepare_resource_player_update135(level,context,now_bits,dt_bits,last_hit_bits,*,
        periodic_input=None,explicit_other_sources_absent=False):
    validate_mixed_resource135(level,context)
    for value in(now_bits,dt_bits,last_hit_bits):_word(value)
    if not all(math.isfinite(f.to_float(value))for value in(now_bits,dt_bits,last_hit_bits)):
        raise PendingResourcePlayerUpdate135('Finite now/dt/last-hit domain required')
    if explicit_other_sources_absent is not True or type(periodic_input)is not tuple or periodic_input:
        raise PendingResourcePlayerUpdate135('Explicit empty other/periodic source snapshots required')
    if any(getattr(level.sources,k)for k in('adjustments','item_modifiers','owned_skills','timed_records','definitions')):
        raise PendingResourcePlayerUpdate135('External stat/aura/proc producers remain separate')
    for entry in level.sources.passives:
        if entry.tag!=13 or not math.isfinite(f.to_float(entry.value_bits))or f.to_float(entry.value_bits)<0:
            raise PendingResourcePlayerUpdate135('Only explicit typed passive13 regen source restored; its grant producer remains separate')
    if level.stats.conditional1344_id or level.stats.conditional1348_bits:
        raise PendingResourcePlayerUpdate135('Shield/conditional owner cleanup remains a separate family')
    seen=set();protection_seen=False;rows=[list(row)for row in context.live.storage]
    for row in rows[:context.live.count]:
        kind=u32(row,8,'2088 live kind');spell=u32(row,20,'2088 live spell')
        if kind==0:
            if spell not in(23451,23505):raise PendingResourcePlayerUpdate135('Only resource23451/23505 kind0 producers admitted')
        elif kind==8:
            magnitude=u32(row,12,'2088 kind8 magnitude')
            if not math.isfinite(f.to_float(magnitude))or not f.to_float(magnitude)>0 or spell in seen:
                raise PendingResourcePlayerUpdate135('Only finite positive unique kind8 producers admitted')
            seen.add(spell)
        elif kind==12:
            if spell!=1020 or protection_seen:
                raise PendingResourcePlayerUpdate135('Only unique producer1020 kind12 admitted')
            protection_seen=True
        else:raise PendingResourcePlayerUpdate135('Other live family remains unresolved')
        if not f.is_zero(u32(row,28,'2088 periodic budget')):
            raise PendingResourcePlayerUpdate135('Nonzero periodic budget remains unresolved')
    now=f.to_float(now_bits);level=replace(level,stats=replace(level.stats,now_bits=now_bits))
    expired=tuple(u32(row,20,'2088 expired spell')for row in rows[:context.live.count]
        if now>=f.to_float(u32(row,24,'2088 expiry')))
    events=[];packets=[]
    if expired:
        write=0
        for read in range(context.live.count):
            if now<f.to_float(u32(rows[read],24,'2088 stable-retain expiry')):
                if read!=write:rows[write]=rows[read].copy()
                write+=1
        live=LiveVector135(tuple(tuple(row)for row in rows),write)
        level=replace(level,sources=replace(level.sources,live_effects=tuple(_semantics(live))))
        stats=StatsInput(level=level.progression.level,**asdict(level.stats),**level.sources.keywords())
        rebuilt=recalculate(stats);derived={int(k):v for k,v in rebuilt['derived_bits'].items()};aux=rebuilt['auxiliary_bits'];fields=dict(level.player_fields)
        fields.update({int(k):v for k,v in rebuilt['object_fields'].items()})
        old_action=context.action_sequence1644
        if rebuilt['speed_changed']:
            packets.append((226,(packed_guid(context.player_guid)+struct.pack('<II',old_action,rebuilt['speed_bits'])).hex()))
            context=replace(context,action_sequence1644=(old_action+1)&f.MASK)
        level=replace(level,stats=replace(level.stats,old_max_hp_bits=derived[1536],current_hp_bits=rebuilt['current_hp_bits'],
            previous_speed_bits=rebuilt['speed_bits'],pool1532_bits=aux['1444'],pool1536_bits=aux['1448'],
            conditional1348_bits=aux['1348'],pool768_bits=aux['768']),derived_bits=tuple(sorted(derived.items())),player_fields=tuple(sorted(fields.items())))
        aura=rebuild_resource_aura135(live.storage,live.count,now_bits,context.aura,level.player_fields)
        level=replace(level,player_fields=aura.player_fields)
        context=replace(context,live=live,aura=aura.aura)
        events.extend((('expire_live',expired),('recalculate1512',),*aura.events))
    stats=level.stats;stats=replace(stats,pool1536_bits=_minnum(stats.pool1532_bits,stats.pool1536_bits))
    d=dict(level.derived_bits);half=0x3f000000 if level.heal_gate387>4 else 0x3f800000
    extra=f.mul(d[1536],d[1620])if f.to_float(f.sub(now_bits,last_hit_bits))>=3 else 0
    regen=f.mul(half,f.mul(dt_bits,f.add(d[1576],extra)))
    old=stats.current_hp_bits;hp=old;fields=dict(level.player_fields)
    if f.to_float(old)<f.to_float(d[1536]):
        hp=_minnum(d[1536],f.add(0,f.add(old,regen)));fields[22]=_ceil_u32(hp);fields[28]=_ceil_u32(d[1536]);events.append(('regen_keys22_28',))
    delta=_positive(f.sub(hp,old));level=replace(level,stats=replace(stats,current_hp_bits=hp),player_fields=tuple(sorted(fields.items())))
    events.append(('healaccount1453_pending',_minnum(delta,regen)))
    validate_mixed_resource135(level,context)
    return ResourcePlayerUpdateResult135(level,context,expired,bool(expired),regen,delta,tuple(events),tuple(packets))
