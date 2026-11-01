"""Independent2088 live-expiry/regen prefix, before its owned1076 phase.

Explicit empty periodic/proc sources only; complete32B live records preserve
unwritten words. This does not call original code or infer world entry/phase1.
"""
from dataclasses import dataclass,replace,asdict
import math,struct
from . import binary32 as f
from .derived_stats135 import LiveEffect,StatsInput,recalculate
from .level_cycle135 import LevelCycleState
from .progression134 import trunc_sat_u32


class UnresolvedPlayerUpdate135(NotImplementedError):pass


@dataclass(frozen=True)
class PlayerUpdateResult135:
    level:LevelCycleState
    live_records:tuple
    unspecified_live_words:tuple
    expired_spell_ids:tuple
    recalculated:bool
    regen_request_bits:int
    heal_delta_bits:int
    events:tuple
    pending:tuple=('Physical1202 aura/message and1453 healaccount output remain separate',)


def _u(word):
    if type(word)is not int or not 0<=word<=f.MASK:raise ValueError('Explicit binary32/u32 word required')
    return word


def _minnum(a,b):
    x=a if f.is_nan(b)else b;y=x if f.is_nan(a)else a
    return x if f.to_float(y)>f.to_float(x)else y


def _positive(word):return word if f.to_float(word)>0 else 0


def _ceil_u32(word):
    n=f.to_float(_positive(word))
    return trunc_sat_u32(f.from_float(math.ceil(n)))if math.isfinite(n)else trunc_sat_u32(word)


def _rebuild(level):
    result=recalculate(StatsInput(level=level.progression.level,**asdict(level.stats),**level.sources.keywords()))
    d={int(k):v for k,v in result['derived_bits'].items()};a=result['auxiliary_bits'];fields=dict(level.player_fields)
    fields.update({int(k):v for k,v in result['object_fields'].items()})
    return replace(level,derived_bits=tuple(sorted(d.items())),player_fields=tuple(sorted(fields.items())),
        stats=replace(level.stats,old_max_hp_bits=d[1536],current_hp_bits=result['current_hp_bits'],
            previous_speed_bits=result['speed_bits'],pool1532_bits=a['1444'],pool1536_bits=a['1448'],
            conditional1348_bits=a['1348'],pool768_bits=a['768']))


def prepare_player_update(level,live_raw32,unspecified,now_bits,dt_bits,last_hit_bits,*,
                          explicit_other_sources_absent=False,periodic_input=None):
    """2088 prefix: expire ->1512/1202 ifdirty ->shield clamp ->regen ->key22.

    Calls1076 are intentionally left to the composition owner, exactly after
    this result. periodic_input must be explicit empty, and every live+28 must
    independently be zero. Icebarrier11426 special cleanup remains unresolved.
    """
    if not isinstance(level,LevelCycleState):raise TypeError('Resolved LevelCycleState required')
    for value in(now_bits,dt_bits,last_hit_bits):_u(value)
    if not math.isfinite(f.to_float(dt_bits)):
        raise UnresolvedPlayerUpdate135('Finite dt required; nonfinite1076 scheduler continuation not restored in prefix isolation')
    if explicit_other_sources_absent is not True or type(periodic_input)is not tuple or periodic_input:
        raise UnresolvedPlayerUpdate135('Explicit empty other/periodic source snapshots required')
    if any(getattr(level.sources,k)for k in('passives','adjustments','item_modifiers','owned_skills','timed_records','definitions')):
        raise UnresolvedPlayerUpdate135('Empty-profile stat/proc source domain required')
    if type(live_raw32)is not tuple or len(live_raw32)!=len(level.sources.live_effects):
        raise ValueError('Complete ordered32B live source snapshot required')
    rows=[]
    for raw,semantic in zip(live_raw32,level.sources.live_effects):
        data=bytes.fromhex(raw)
        if len(data)!=32:raise ValueError('Complete32B live record required')
        row=struct.unpack('<8I',data)
        if row[2]not in(7,8,9,12):raise UnresolvedPlayerUpdate135('Other live-effect family remains unresolved')
        if not f.is_zero(row[7]):raise UnresolvedPlayerUpdate135('Positive/noncanonical periodic remaining budget not restored')
        if(row[2],row[5],row[6])!=(semantic.kind,semantic.spell_id,semantic.expires_bits)or(row[2]!=12 and row[3]!=semantic.value_bits):
            raise ValueError('Semantic/raw live source mismatch')
        if row[5]==11426:raise UnresolvedPlayerUpdate135('Icebarrier11426 expiry cleanup remains unresolved')
        rows.append(row)
    if level.stats.conditional1344_id==11426:raise UnresolvedPlayerUpdate135('Icebarrier11426 source remains unresolved')
    unknown=set(tuple(x)for x in unspecified)
    for index,offset in unknown:
        if not 0<=index<len(rows)or offset not in(12,16)or(offset==12 and rows[index][2]!=12):
            raise ValueError('Unspecified active live magnitude is not allowed')
    level=replace(level,stats=replace(level.stats,now_bits=now_bits));now=f.to_float(now_bits)
    expired=tuple(row[5]for row in rows if now>=f.to_float(row[6]));events=[]
    if expired:
        if level.stats.conditional1344_id and level.stats.conditional1344_id in expired:
            level=replace(level,stats=replace(level.stats,pool1532_bits=_positive(f.sub(level.stats.pool1532_bits,level.stats.conditional1348_bits)),
                conditional1344_id=0,conditional1348_bits=0))
        kept=[];remapped=set()
        for i,row in enumerate(rows):
            # Filter is strictly now<expiry; aNaN row isco-removed if another
            # record triggered thispass, butalone itdoesnot trigger thepass.
            if now<f.to_float(row[6]):
                j=len(kept);kept.append(row);remapped.update((j,o)for q,o in unknown if q==i)
        rows=kept;unknown=remapped
        semantic=tuple(LiveEffect(r[2],0 if r[2]==12 else r[3],r[5],r[6])for r in rows)
        level=replace(level,sources=replace(level.sources,live_effects=semantic));level=_rebuild(level)
        events.extend(('expire-live','1512','1202'))
    stats=level.stats;stats=replace(stats,pool1536_bits=_minnum(stats.pool1532_bits,stats.pool1536_bits))
    d=dict(level.derived_bits);half=0x3f000000 if level.heal_gate387>4 else 0x3f800000
    extra=f.mul(d[1536],d[1620])if f.to_float(f.sub(now_bits,last_hit_bits))>=3 else 0
    regen=f.mul(half,f.mul(dt_bits,f.add(d[1576],extra)))
    old=stats.current_hp_bits;hp=old;fields=dict(level.player_fields)
    if f.to_float(old)<f.to_float(d[1536]):
        hp=_minnum(d[1536],f.add(0,f.add(old,regen)));fields[22]=_ceil_u32(hp);fields[28]=_ceil_u32(d[1536]);events.append('regen-keys22-28')
    level=replace(level,stats=replace(stats,current_hp_bits=hp),player_fields=tuple(sorted(fields.items())))
    events.append('1453-pending')
    return PlayerUpdateResult135(level,tuple(struct.pack('<8I',*r).hex()for r in rows),tuple(sorted(unknown)),expired,bool(expired),
        regen,_positive(f.sub(hp,old)),tuple(events))
