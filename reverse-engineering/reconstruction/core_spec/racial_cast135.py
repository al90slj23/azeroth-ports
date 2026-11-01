"""Explicit fixed135 kind9 racial self-buff cast projection.

Preserves complete32B live records and declared unwritten words. Generic
effects8/9 require a valid target within30 and recalculate1512 before aura1202.
Stoneform7 and protection12 do not immediately call1512. Physical callbacks remain
pending. Production code reads no binary, original results or external state.
"""
from dataclasses import asdict,dataclass,replace
import struct
from . import binary32 as f
from .ability_state import AbilityRecord
from .binary32_sqrt import sqrt_bits
from .cast135 import CastState,query_targets
from .derived_stats135 import LiveEffect,StatsInput,recalculate
from .level_cycle135 import LevelCycleState

RACIALS={b'perception':(5476580,8,20600),b'blood_fury':(5476668,8,23234),
 b'stoneform':(5476756,7,20594),b'shadowmeld':(5476844,12,20580),
 b'will_of_the_forsaken':(5476932,12,7744),b'berserking':(5477196,9,26635)}


@dataclass(frozen=True)
class RacialDefinition135:
    pointer:int
    ability_id:bytes
    raw88_hex:str

    def words(self):
        raw=bytes.fromhex(self.raw88_hex)
        if len(raw)!=88 or self.ability_id not in RACIALS:raise ValueError('Explicit fixed racial88B definition required')
        p,tag,spell=RACIALS[self.ability_id];w=struct.unpack('<22I',raw)
        if self.pointer!=p or w[0]!=tag or w[11]!=spell or raw[84]!=9:raise ValueError('Fixed racial identity/type differs')
        return w


@dataclass(frozen=True)
class RacialCastResult135:
    cast:CastState
    level:LevelCycleState
    success:int
    live_records:tuple
    unspecified_live_words:tuple
    callbacks:tuple
    pending:tuple
    attempted_spell_sets:tuple


def _maxnum(a,b):
    a=b if f.is_nan(a)else a;b=a if f.is_nan(b)else b
    return a if f.to_float(a)>f.to_float(b)else b


def _rebuild(level):
    stats=level.stats;result=recalculate(StatsInput(level=level.progression.level,**asdict(stats),**level.sources.keywords()))
    aux=result['auxiliary_bits'];d=result['derived_bits'];fields=dict(level.player_fields);fields.update((int(k),v)for k,v in result['object_fields'].items())
    return replace(level,derived_bits=tuple(sorted((int(k),v)for k,v in d.items())),player_fields=tuple(sorted(fields.items())),
        stats=replace(stats,old_max_hp_bits=d['1536'],current_hp_bits=result['current_hp_bits'],previous_speed_bits=result['speed_bits'],
            pool1532_bits=aux['1444'],pool1536_bits=aux['1448'],conditional1348_bits=aux['1348'],pool768_bits=aux['768']))


def cast_self_buff(cast,level,definition,owned,*,live_records,busy488=0,unspecified_live_words=(),attempted_spell_sets=None):
    if not isinstance(cast,CastState)or not isinstance(level,LevelCycleState)or not isinstance(owned,AbilityRecord):raise TypeError('Resolved cast/level/owned states required')
    if not isinstance(definition,RacialDefinition135):raise TypeError('Explicit88B racial definition required')
    w=definition.words();tag=w[0];spell=w[11];now=cast.combat.now_bits
    if owned.definition_pointer!=definition.pointer or now!=level.stats.now_bits or cast.rng_words!=level.rng_words:
        raise ValueError('Racial pointer/clock/shared RNG snapshots disagree')
    if type(live_records)is not tuple or len(live_records)!=len(level.sources.live_effects):raise ValueError('Explicit complete32B live records required')
    records=[struct.unpack('<8I',bytes.fromhex(h))for h in live_records]
    if any(len(bytes.fromhex(h))!=32 for h in live_records):raise ValueError('Live record length')
    unknown=set(tuple(x)for x in unspecified_live_words)
    for i,off in unknown:
        if not 0<=i<len(records)or off not in(12,16)or(off==12 and records[i][2]!=12):raise ValueError('Unspecified active magnitude is not allowed')
    for row,e in zip(records,level.sources.live_effects):
        if (row[2],row[5],row[6])!=(e.kind,e.spell_id,e.expires_bits)or(row[2]!=12 and row[3]!=e.value_bits):
            raise ValueError('Raw and semantic live snapshots disagree')
    if attempted_spell_sets is None:
        if busy488 or cast.context908&1:raise ValueError('Three explicit attempt ledgers required when only set3 is gated')
        ledgers=(cast.attempted_spell_ids,)*3
    else:
        ledgers=tuple(tuple(r)for r in attempted_spell_sets)
        if len(ledgers)!=3 or ledgers[0]!=cast.attempted_spell_ids:raise ValueError('Three attempt ledgers and CastState first ledger must agree')
        if any(type(v)is not int or not 0<=v<=f.MASK for r in ledgers for v in r):raise ValueError('Attempt spell IDs must be u32')
    callbacks=[]
    def result(success):
        return RacialCastResult135(cast,level,success,tuple(struct.pack('<8I',*r).hex()for r in records),tuple(sorted(unknown)),tuple(callbacks),
            ('1202 physical aura/object keys and message packet bytes remain pending','Entry busy488 is explicit; caller owns real racial1256 cooldown and scheduling'),ledgers)
    ledgers=tuple((row if spell in row else row+(spell,))if i<2 or(not busy488 and not cast.context908&1)else row for i,row in enumerate(ledgers))
    cast=replace(cast,attempted_spell_ids=ledgers[0])
    now_value=f.to_float(now)
    if tag in(8,9)and not query_targets(cast.spatial,cast.player_xy,0x41f00000,now):return result(0)
    if tag==12:
        if f.to_float(level.stats.current_hp_bits)>f.to_float(f.mul(cast.max_hp_bits,0x3eb33333)):return result(0)
        if any(r[2]==12 and f.to_float(r[6])>now_value for r in records):return result(0)
    if tag==7 and any(r[5]==spell for r in records):return result(0)
    duration=_maxnum(f.mul(f.mul(f.mul(w[17],0x3fb33333),owned.duration_bits),owned.additional_duration_bits),0x3dcccccd)
    value=f.mul(owned.field76_bits,w[1])if tag in(7,8,9)else w[1]
    if tag==7:
        strength=f.mul(sqrt_bits(f.mul(owned.damage_bits,owned.additional_damage_bits)),0x3fb33333)
        amount=f.mul(f.mul(strength,f.mul(cast.max_hp_bits,value)),f.add(dict(level.derived_bits)[1604],0x3f800000))
        remaining=_maxnum(f.sub(level.stats.pool1532_bits,level.stats.conditional1348_bits),0)
        level=replace(level,stats=replace(level.stats,pool1532_bits=f.add(amount,remaining),conditional1344_id=spell,conditional1348_bits=amount))
        callbacks.extend(('shield-write','cast-message'))
    else:callbacks.append('cast-message')
    kept=[];remapped=set()
    for i,row in enumerate(records):
        if tag in(8,9)and row[5]==spell and row[0]==0 and row[1]==0:continue
        j=len(kept);kept.append(row);remapped.update((j,o)for q,o in unknown if q==i)
    records=kept;unknown=remapped;index=len(records)
    records.append((0,0,tag,value,w[2]if tag==12 else 0,spell,f.add(now,duration),0))
    if tag in(7,8,9):unknown.add((index,16))
    semantic=tuple(LiveEffect(r[2],0 if r[2]==12 else r[3],r[5],r[6])for r in records)
    level=replace(level,sources=replace(level.sources,live_effects=semantic))
    callbacks.append('live-append')
    if tag in(8,9):
        level=_rebuild(level);callbacks.append('1512')
        d=dict(level.derived_bits);cast=replace(cast,damage_multiplier_bits=d[1540],max_hp_bits=d[1536],critical_chance_bits=d[1548],critical_multiplier_bits=d[1552],
            area_multiplier_bits=d[1580],cooldown_multiplier_bits=d[1544],extra_targets=d[1592])
    callbacks.append('1202')
    return result(1)
