"""Current139 Bloodrage owner: actual983 stage and913 nonproc side effect.

No inferred HP sacrifice/live buff: current922 exec11 returns0 and1238 skips
its dispatch after decrementing CD. 983 owns resource fill/idle decay and the
10285 burst; outgoing913 can also cause that burst synchronously.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .death139 import OrdinaryDamageState139,DefaultDeathSources139,word139,guid139
from .hit_events139 import OwnedExecutionScan139,ConstructorHitSources139
from .player_update139 import _minnum,_maxnum
from .candidates139_data import DEFINITIONS139
from .radius import radius_bits
from .natural_demo_casts139 import targets8673_cells139
from .thunder_clap139 import targets_thunder_clap139,thunder_launch306139
from .rng import next_u32_words

POINTER139=5883620
RAW139=bytes.fromhex(DEFINITIONS139['bloodrage'][1])
class PendingBloodrage139(NotImplementedError):pass


def scan_bloodrage_sources139(owned):
    pointers=tuple(word139(r,0)for r in owned)
    declarations={p:bytes.fromhex(raw)for p,raw,kinds in DEFINITIONS139.values()}
    if pointers not in((5882740,5883180,POINTER139),):raise PendingBloodrage139('Actual ordered cleave/Demo/Bloodrage owners required')
    codes=tuple(declarations[p][84]for p in pointers)
    if codes!=(5,2,11):raise AssertionError('Current declarations')
    return OwnedExecutionScan139(pointers,codes,False)


@dataclass(frozen=True)
class BloodrageDeathSources139(DefaultDeathSources139):
    def __post_init__(self):
        if not isinstance(self.hit_sources,ConstructorHitSources139):raise TypeError('ConstructorHitSources139')
        if any(type(v)is not tuple or v for v in(self.items8,self.adjustments8,self.timed32,self.onkill_sources,self.scheduled_procs)):
            raise PendingBloodrage139('Other owned source families')
        scan=self.hit_sources.owned_execution_scan
        if self.hit_sources.event_definitions36.count!=0 or scan.definition_pointers!=(5882740,5883180,POINTER139)or scan.execution_bytes84!=(5,2,11)or scan.execution11_arm_skipped:
            raise PendingBloodrage139('Explicit actual exec11 Bloodrage source required')


@dataclass(frozen=True)
class BloodrageResource139:
    rage868_bits:int=0
    reservoir872_bits:int=0
    last_hit876_bits:int=0
    # 22428 Vec12 is keyed by actual ability name, not spell ID.
    cooldown_registry:tuple=()
    display_tag784:int=0
    display_key788:int|None=None
    display_value792:int|None=None
    #1600 staged source+88 copy binds these five empty queue counts.
    other983_counts:tuple=(0,0,0,0,0)

    def __post_init__(self):
        if self.other983_counts!=(0,0,0,0,0):raise PendingBloodrage139('Other983 passive queues')
        for bits in(self.rage868_bits,self.reservoir872_bits,self.last_hit876_bits):
            if type(bits)is not int or not 0<=bits<=f.MASK or f.is_nan(bits)or f.is_inf(bits):raise PendingBloodrage139('Finite resource/clock domain')
        if any(name!='bloodrage'or f.is_nan(bits)or f.is_inf(bits)for name,bits in self.cooldown_registry)or len(self.cooldown_registry)>1:raise PendingBloodrage139('Only actualBloodrage named registry')


@dataclass(frozen=True,kw_only=True)
class BloodrageDamageState139(OrdinaryDamageState139):
    bloodrage:BloodrageResource139
    actual_owned80:tuple
    derived:tuple
    player_xyz:tuple

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.bloodrage,BloodrageResource139):raise TypeError('Explicit Bloodrage resource owner')
        pointers=tuple(word139(row,0)for row in self.actual_owned80)
        if pointers not in((5882740,),(5882740,5883180),(5882740,5883180,POINTER139)):
            raise PendingBloodrage139('Current naturally selected ordered owners')
        if len(pointers)==3:
            if not isinstance(self.sources,BloodrageDeathSources139)or self.sources.hit_sources.owned_execution_scan!=scan_bloodrage_sources139(self.actual_owned80):raise PendingBloodrage139('Actual exec11 source declaration')
        if len(self.player_xyz)!=3 or any(f.is_nan(v)or f.is_inf(v)for v in self.player_xyz):raise PendingBloodrage139('Finite component player XYZ')


def attach_bloodrage_state139(damage,player,resource=None):
    if isinstance(damage,BloodrageDamageState139):
        return replace(damage,actual_owned80=player.growth.owned_records80,
            derived=tuple(player.growth.derived_bits.items()),player_xyz=player.player_xyz)
    fields={k:getattr(damage,k)for k in OrdinaryDamageState139.__dataclass_fields__}
    return BloodrageDamageState139(**fields,bloodrage=resource or BloodrageResource139(),
        actual_owned80=player.growth.owned_records80,derived=tuple(player.growth.derived_bits.items()),player_xyz=player.player_xyz)


def _rowword(row,offset,value):
    b=bytearray(row);struct.pack_into('<I',b,offset,value);return bytes(b)


def bloodrage_interval139(owned80,derived):
    """33222/50267 current name-special minimum8, inner minimum.25, speed1544."""
    if word139(owned80,0)!=POINTER139 or RAW139[84]!=11:raise PendingBloodrage139('CurrentBloodrage definition')
    interval=f.mul(f.mul(f.mul(f.mul(word139(RAW139,52),0x3fb33333),word139(owned80,16)),word139(owned80,56)),derived[1544])
    return f.div(_maxnum(0x41000000,_maxnum(interval,0x3e800000)),_maxnum(0x3dcccccd,word139(owned80,76)))


def release_bloodrage139(state,ledger,world,*,healing_sources):
    """10285: when rage>=100 and registry due, query actual living radius9.

    A successful burst resets rage, writes Vec12/ownedCD, emits308/309 then
    visual306 spell5246, and performs ordered critical913 spell2687 hits in
    mode770=3 (no recursive resource generation). No-target preserves rage.
    """
    if not isinstance(state,BloodrageDamageState139):raise TypeError('BloodrageDamageState139')
    resource=state.bloodrage;packets=[];events=[];heals=[];keys=[]
    if not f.to_float(resource.rage868_bits)>=100:return state,ledger,(),(),(),()
    owned_index=next((j for j,r in enumerate(state.actual_owned80)if word139(r,0)==POINTER139),None)
    if owned_index is None:raise PendingBloodrage139('Rage without actual owner')
    due=next((expiry for name,expiry in resource.cooldown_registry if name=='bloodrage'),0xff7fffff)
    if not f.to_float(due)<=f.to_float(state.now_bits):return state,ledger,(),(),(),()
    row=state.actual_owned80[owned_index];derived=dict(state.derived)
    radius=radius_bits(f.mul(derived[1580],f.mul(word139(RAW139,60),f.mul(word139(row,24),word139(row,64)))))
    targets=targets_thunder_clap139(state.records432,state.player_xyz,state.now_bits,radius)
    if not targets:return state,ledger,(('bloodrage_no_target',),),(),(),()
    interval=bloodrage_interval139(row,derived);expiry=f.add(interval,state.now_bits)
    registry=list(resource.cooldown_registry);found=next((j for j,(name,t)in enumerate(registry)if name=='bloodrage'),None)
    if found is None:registry.append(('bloodrage',expiry))
    else:registry[found]=('bloodrage',expiry)
    own=list(state.actual_owned80);own[owned_index]=_rowword(row,8,interval)
    state=replace(state,actual_owned80=tuple(own),bloodrage=replace(resource,rage868_bits=0,cooldown_registry=tuple(registry)))
    ms=max(0,min(f.MASK,int(f.to_float(f.mul(interval,0x447a0000)))))
    packets.extend(((308,struct.pack('<QII',0,2687,ms).hex()),(309,struct.pack('<IQ',2687,0).hex()),(306,thunder_launch306139(0,5246,targets))))
    base=f.mul(derived[1540],f.add(f.mul(f.mul(f.mul(word139(row,12),f.mul(word139(RAW139,48),0x3fb33333)),word139(row,52)),0x3f800000),f.mul(derived[1536],word139(row,72))))
    from .bloodrage_damage139 import resolve_bloodrage_damage139
    for target in targets:
        sample,words=next_u32_words(state.rng_words);critical=int(f.to_float(derived[1548])>f.to_float(f.mul(f.from_u32(sample>>8),0x33800000)))
        amount=f.mul(base,derived[1552])if critical else base
        value=resolve_bloodrage_damage139(replace(state,rng_words=words),target,amount,world,
            spell_id=2687,school=RAW139[85],critical=critical,inherited_context908=0,healing=ledger,
            healing_sources=healing_sources,outgoing_owned80=row,suppress_spell_damage_packet=0,
            source_mode770=3)
        state,ledger=value.state,value.healing;packets.extend(value.known_packets);heals.extend(value.heal_events);keys.extend(value.player_key_writes)
        events.append(('bloodrage_hit',target,amount,critical,value.dead))
    return state,ledger,tuple(events),tuple(packets),tuple(heals),tuple(keys)


def damage_bloodrage_tail139(state,ledger,world,*,healing_sources,source_mode770=0,source552=0,source748=0,context908=0):
    """913 only for actual nonproc mode0, after accepted damage and Leech."""
    if not isinstance(state,BloodrageDamageState139):raise TypeError('BloodrageDamageState139')
    if not any(word139(r,0)==POINTER139 for r in state.actual_owned80):return state,ledger,(),(),(),()
    if source552 or source748 or context908 or source_mode770:return state,ledger,(),(),(),()
    r=state.bloodrage;spent=_maxnum(0,_minnum(r.reservoir872_bits,0x40000000))
    r=replace(r,last_hit876_bits=state.now_bits,reservoir872_bits=f.sub(r.reservoir872_bits,spent),rage868_bits=_minnum(0x42c80000,f.add(r.rage868_bits,spent)))
    state=replace(state,bloodrage=r)
    return release_bloodrage139(state,ledger,world,healing_sources=healing_sources)


@dataclass(frozen=True)
class BloodrageStageResult139:
    state:object
    packets:tuple
    events:tuple
    heal_events:tuple
    player_key_writes:tuple


def update_owned_effects983_139(state,dt,world,*,healing_sources):
    """Complete983 Bloodrage-only owned branch with other passive queues empty.

    Source guards are typed (all other exec11 names absent and empty queues
    are constructor/preceding-stage owner projections). This is not full884.
    """
    if not isinstance(state.damage,BloodrageDamageState139):raise TypeError('Bloodrage damage owner required')
    if f.is_nan(dt)or f.is_inf(dt)or f.to_float(dt)<0:raise PendingBloodrage139('Finite nonnegative983 dt')
    d=attach_bloodrage_state139(state.damage,state.player);g=state.player.growth
    if not any(word139(r,0)==POINTER139 for r in d.actual_owned80):return BloodrageStageResult139(replace(state,damage=d),(),(),(),())
    scan_bloodrage_sources139(d.actual_owned80)
    row=next(r for r in d.actual_owned80 if word139(r,0)==POINTER139);interval=bloodrage_interval139(row,g.derived_bits)
    rate=f.div(0x42c80000,interval);cap=_maxnum(0x40000000,f.mul(rate,0x3f000000));r=d.bloodrage
    r=replace(r,reservoir872_bits=_minnum(cap,f.add(r.reservoir872_bits,f.mul(dt,rate))))
    if f.to_float(f.sub(g.now_bits,r.last_hit876_bits))>3:r=replace(r,rage868_bits=_maxnum(0,f.add(r.rage868_bits,f.mul(dt,0xc1700000))))
    d=replace(d,bloodrage=r);d,ledger,events,packets,heals,keys=release_bloodrage139(d,state.ledger,world,healing_sources=healing_sources)
    shown=max(0,min(f.MASK,int(f.to_float(f.mul(d.bloodrage.rage868_bits,0x41200000)))))
    r=replace(d.bloodrage,display_tag784=1,display_key788=24,display_value792=shown);d=replace(d,bloodrage=r)
    p=state.player;fields=dict(p.growth.player_fields);fields.update(keys);fields[24]=shown
    p=replace(p,growth=replace(p.growth,owned_records80=d.actual_owned80,units432_cells=d.records432,rng_words=d.rng_words,current_hp_bits=d.player_hp1440_bits,player_fields=fields))
    return BloodrageStageResult139(replace(state,damage=d,player=p,ledger=ledger),packets,events,heals,tuple(keys)+((24,shown),))


def resource_projection139(resource):
    return dict(rage868_bits=resource.rage868_bits,reservoir872_bits=resource.reservoir872_bits,
        last_hit876_bits=resource.last_hit876_bits,cooldown_registry=[[name,bits]for name,bits in resource.cooldown_registry],
        display_tag784=resource.display_tag784,display_key788=resource.display_key788,display_value792=resource.display_value792,other983_counts=list(resource.other983_counts))
