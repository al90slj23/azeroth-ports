"""WIP current139913 defaultordinary damage including actualdemo1160 identity.

Frozen death139 remains unchanged. This new implementation restores its real
positive1.5% leech caller/accounting branch over actual hurt HP. Nonzero healing
on kill, positive overheal modifiers and other sources remain explicit stops.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .death139 import (OrdinaryDamageState139,OrdinaryDamageResult139,
    UnknownDeath139,DEFAULT_POINTER139,word139,guid139,position3_139,
    _u,_set,_finite,_bits64,_double,_next24,_bounded3)
from .death_pickups139 import append_death_pickup139
from .hit_events139 import plan_damage_tail_events139
from .healing139 import (HealingLedger139,DefaultHealingSources139,
    PendingHealing139,leech_player139)
from .thunder_clap139 import (ThunderClapDefinition139,ThunderClapResult139,
    PendingThunderClap139,targets_thunder_clap139,thunder_launch306139,_slow139)
from .rng import next_u32_words
from .radius import radius_bits


def targets8673_cells139(records,player_xyz,now,radius):
    """Current8673 ordinary known/None selector, including actual motion."""
    def distance(a,b):
        x,y=f.sub(a[0],b[0]),f.sub(a[1],b[1])
        return f.add(f.mul(x,x),f.mul(y,y))
    key=lambda v:(~v&f.MASK)if v&f.SIGN else v|f.SIGN
    square=f.mul(radius,radius);candidates=[]
    for row in records:
        marker=word139(row,0)
        if marker:
            if marker!=1:raise UnknownDeath139('OtherNPCmarkerselector')
            continue
        if any(word139(row,o)!=f.MASK for o in(40,64,244))or row[424]not in(0,1):
            raise UnknownDeath139('Onlyknownnormal8673classifications')
        xyz=position3_139(row,now)
        if any(not _finite(v)for v in xyz):raise UnknownDeath139('Finiteselectorpositions')
        d=distance(xyz,player_xyz)
        if f.to_float(d)<=f.to_float(square):candidates.append((row,d,xyz))
    candidates.sort(key=lambda x:key(x[1]))
    priority=lambda x:3 if f.to_float(now)<f.to_float(word139(x[0],380))else 2-x[0][424]
    candidates.sort(key=priority)
    prefix=[r for r in candidates if priority(r)<2]
    ordinary=[r for r in candidates if priority(r)==2]
    deferred=[r for r in candidates if priority(r)==3]
    if ordinary:
        anchor=ordinary[0][2];near=[];far=[]
        for row in ordinary:
            (near if f.to_float(distance(row[2],anchor))<=36 else far).append(row)
        near.sort(key=lambda r:key(word139(r[0],288)));ordinary=near+far
    return tuple(guid139(row)for row,d,xyz in prefix+ordinary+deferred)


@dataclass(frozen=True)
class DefaultCleaveResult139:
    state: OrdinaryDamageState139
    spell_sets: tuple
    success: int
    selected_ids: tuple
    base_damage_bits: int
    radius_bits: int
    owned80: bytes
    hits: tuple
    effect_writes: tuple
    known_packets: tuple
    healing: HealingLedger139
    heal_events: tuple
    player_key_writes: tuple


def cast_cleave_natural139(state,player_xyz,derived,definition,owned80,spell_sets,
                          world,*,healing,healing_sources,inherited_context908,
                          source_id=0,heal_on_kill1600_bits=0):
    raw=definition.raw88
    if definition.pointer!=5882740 or raw[84]!=5 or word139(raw,0)!=0 or word139(raw,44)!=845:
        raise UnknownDeath139('ActualcurrentCleave declaration required')
    if type(owned80)is not bytes or len(owned80)!=80 or word139(owned80,0)!=5882740:
        raise UnknownDeath139('ActualcompleteCleaveowned80required')
    if inherited_context908:raise UnknownDeath139('Inheritedproccontext')
    count=1 if word139(raw,64)==0 else max(1,(word139(raw,64)+word139(owned80,60)+word139(owned80,20)+derived['1592'])&f.MASK)
    radius=word139(raw,56);selected=targets8673_cells139(state.records432,player_xyz,state.now_bits,radius)[:count]
    sets=tuple(v if 845 in v else v+(845,)for v in spell_sets)
    value=f.mul(f.mul(f.mul(f.mul(word139(raw,48),0x3fb33333),word139(owned80,12)),word139(owned80,52)),0x3f800000)
    life=f.mul(derived['1536'],word139(owned80,72))if f.to_float(word139(raw,48))>0 else 0
    base=f.mul(derived['1540'],f.add(value,life));packets=[];hits=[];events=[];keys=[];ledger=healing
    if selected:
        from .cast139 import cleave_launch306139
        packets.append((306,cleave_launch306139(source_id,845,selected)))
    for target in selected:
        sample,words=next_u32_words(state.rng_words);roll=f.mul(f.from_u32(sample>>8),0x33800000)
        critical=int(f.to_float(f.add(0,derived['1548']))>f.to_float(roll))
        amount=f.mul(base,derived['1552'])if critical else base
        result=resolve_demo_damage139(replace(state,rng_words=words),target,amount,world,
            spell_id=845,school=raw[85],critical=critical,inherited_context908=inherited_context908,
            healing=ledger,healing_sources=healing_sources,outgoing_owned80=owned80,
            suppress_spell_damage_packet=0,heal_on_kill1600_bits=heal_on_kill1600_bits)
        state,ledger=result.state,result.healing;packets.extend(result.known_packets)
        events.extend(result.heal_events);keys.extend(result.player_key_writes);hits.append((target,amount,critical,result))
    return DefaultCleaveResult139(state,sets,int(bool(selected)),selected,base,radius,owned80,
        tuple(hits),(),tuple(packets),ledger,tuple(events),tuple(keys))


@dataclass(frozen=True)
class NaturalOutgoingLedger139(HealingLedger139):
    """Shared G960/G1000 domain: outgoing damage and positive heals."""
    def __post_init__(self):
        if any(type(v)is not int or not 0<=v<1<<64 for v in
               (self.event_counter960,self.accepted_count1016)):
            raise ValueError('Actual inherited u64 counters required')
        if len({k for k,v in self.reason_totals64})!=len(self.reason_totals64):
            raise ValueError('Unique semantic source totals required')
        for key,bits in self.reason_totals64:
            if key not in('regen','leech','level_up','melee','ability:cleave:r1','ability:thunder_clap:r1','ability:demo_shout:r1') or not math.isfinite(_double(bits)):
                raise PendingHealing139('Other outgoing event attribution pending')


def _account_default_damage139(ledger,account,spell_id):
    identities={0:'melee',845:'ability:cleave:r1',6343:'ability:thunder_clap:r1',1160:'ability:demo_shout:r1'}
    if spell_id not in identities:raise PendingHealing139('Unbound default outgoing source identity')
    rows=list(ledger.reason_totals64);reason=identities[spell_id]
    j=next((j for j,(key,_)in enumerate(rows)if key==reason),None)
    value=_bits64(account+(0.0 if j is None else _double(rows[j][1])))
    if j is None:rows.append((reason,value))
    else:rows[j]=(reason,value)
    return replace(ledger,event_counter960=(ledger.event_counter960+1)&((1<<64)-1),accepted_count1016=(ledger.accepted_count1016+1)&((1<<64)-1),reason_totals64=tuple(rows))


@dataclass(frozen=True,kw_only=True)
class DefaultDamageResult139(OrdinaryDamageResult139):
    healing: HealingLedger139
    heal_events: tuple
    player_key_writes: tuple

def resolve_demo_damage139(state,target_guid,amount_bits,world,*,spell_id=6343,school=0,critical=0,inherited_context908,healing,healing_sources,outgoing_owned80,suppress_spell_damage_packet,heal_on_kill1600_bits=0):
 if not isinstance(state,OrdinaryDamageState139):raise TypeError('OrdinaryDamageState139')
 if not isinstance(healing,HealingLedger139)or not isinstance(healing_sources,DefaultHealingSources139):raise TypeError('Actual healing/source owners required')
 if spell_id==0:
  if outgoing_owned80 is not None or suppress_spell_damage_packet!=1:raise PendingHealing139('Actualbasicspell0/packetflag1required')
 elif spell_id in(845,6343,1160):
  if type(outgoing_owned80)is not bytes or len(outgoing_owned80)!=80 or word139(outgoing_owned80,0)!={845:5882740,6343:5882916,1160:5883180}[spell_id]or word139(outgoing_owned80,4)!=1 or suppress_spell_damage_packet!=0:raise PendingHealing139('Actualrank1ownedsourceandpacketflag0required')
 else:raise PendingHealing139('Otheroutgoingabilitysourcepending')
 if heal_on_kill1600_bits!=0:raise PendingHealing139('Nonzero death-heal-on-kill11033 branch pending')
 ledger=NaturalOutgoingLedger139(healing.event_counter960,healing.accepted_count1016,healing.reason_totals64);heal_events=();player_keys=()
 _u(target_guid,64)
 for v in(amount_bits,spell_id):_u(v)
 for v in(school,critical,inherited_context908):_u(v,8)
 if inherited_context908:raise UnknownDeath139('InheritedGame908proccontext')
 if state.phase2587!=1:return DefaultDamageResult139(state,False,False,0,None,(),(),None,None,0,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)
 index=next((i for i,row in enumerate(state.records432)if guid139(row)==target_guid),None)
 if index is None:return DefaultDamageResult139(state,False,False,0,None,(),(),None,None,0,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)
 oldrow=state.records432[index]
 if word139(oldrow,0)==1:return DefaultDamageResult139(state,False,False,0,None,(),(),None,None,0,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)
 if any(word139(oldrow,o)!=f.MASK for o in(40,64,244))or word139(oldrow,284)!=DEFAULT_POINTER139:raise UnknownDeath139('Onlyactualdefaultordinarydefinition/tags')
 if oldrow[424]not in(0,1):raise UnknownDeath139('Knownclassification424 required')
 now=f.to_float(state.now_bits);mult=0x3f800000
 if now<f.to_float(word139(oldrow,148)):mult=f.add(mult,word139(oldrow,144))
 term=word139(oldrow,152)if now<f.to_float(word139(oldrow,156))else(word139(oldrow,160)if now<f.to_float(word139(oldrow,164))else 0)
 mult=f.add(f.add(f.add(mult,term),word139(oldrow,368)),0)
 school_add=0x3dcccccd if school&254==2 and f.to_float(word139(oldrow,372))>now else 0
 damage=f.mul(f.mul(amount_bits,f.add(mult,school_add)),0x3f800000)
 if f.is_nan(damage)or not f.to_float(damage)>1:damage=0x3f800000
 hp=word139(oldrow,288);newhp=f.sub(hp,damage)
 if any(not _finite(x)for x in(hp,newhp,state.now_bits,state.player_hp1440_bits,state.maximum1536_bits)):raise UnknownDeath139('Finiteordinarydamage domain')

 account=min(max(f.to_float(hp),0),f.to_float(damage));total=_bits64(_double(state.accounted_total_bits)+account)
 spell_totals=list(state.spell_totals64);found=next((j for j,(key,_)in enumerate(spell_totals)if key==spell_id),None)
 if found is None:spell_totals.append((spell_id,_bits64(account)))
 else:spell_totals[found]=(spell_id,_bits64(_double(spell_totals[found][1])+account))
 row=list(oldrow);_set(row,288,newhp);records=list(state.records432);records[index]=tuple(row);newstate=replace(state,records432=tuple(records),accounted_total_bits=total,spell_totals64=tuple(spell_totals))
 ledger=_account_default_damage139(ledger,account,spell_id)
 heal=leech_player139(newstate.player_hp1440_bits,newstate.maximum1536_bits,damage,newstate.now_bits,ledger,healing_sources)
 ledger,heal_events,player_keys=heal.ledger,heal.events,heal.key_writes
 newstate=replace(newstate,player_hp1440_bits=heal.hp_bits)
 key22=max(0,math.ceil(f.to_float(newhp)))
 if f.to_float(newhp)>0:return DefaultDamageResult139(newstate,True,False,damage,None,(),(),key22,None,0,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)
 if word139(oldrow,240)!=0:raise UnknownDeath139('Nonemptyunit44effectsource')
 xyz=position3_139(oldrow,state.now_bits);start=word139(oldrow,340);duration=word139(oldrow,344);packets=[];sequence=state.movement_sequence2412
 if f.to_float(duration)>0 and now<f.to_float(f.add(start,duration)):
  sequence=(sequence+1)&f.MASK;height=world.height(xyz[0],xyz[1]);stopxyz=(xyz[0],xyz[1],height.value_bits if height.found else xyz[2])
  if not height.found and world.primary is not None:raise UnknownDeath139('Movementsnapprimarynearest')
  raw=target_guid.to_bytes(8,'little');packed=bytes([sum(1<<j for j,v in enumerate(raw)if v)])+bytes(v for v in raw if v);packets.append((221,(packed+struct.pack('<4I',*stopxyz,sequence)+bytes([1])).hex()))
 _set(row,0,1);_set(row,4,state.now_bits);_set(row,240,0)
 for off in(316,328):row[off:off+12]=struct.pack('<3I',*xyz)
 _set(row,340,state.now_bits);_set(row,344,0);records[index]=tuple(row)
 words=state.rng_words;xp_random,words=_next24(words);xp_scaled=f.mul(f.from_u32(1),0x3fd33333);whole=int(f.to_float(xp_scaled));fraction=f.sub(xp_scaled,f.from_float(math.trunc(f.to_float(xp_scaled))));xp=(whole+int(f.to_float(fraction)>f.to_float(xp_random)))&f.MASK;direct=1;vec=state.pickups;counter=state.counter2408;events=[]
 if xp:
  r=append_death_pickup139(0,xp,xyz,world,words,counter,state.now_bits,vector=vec);vec,counter,words=r.vector,r.counter,r.rng_words;packets.extend(r.packets);events.append(('XP',xp,r.guid,r.position_bits,r.merged_index))
 coin_random,words=_next24(words);direct+=1
 if f.to_float(coin_random)<f.to_float(0x3e28f5c3):
  amount,words,n=_bounded3(words);direct+=n;coinxyz=(f.add(xyz[0],0x3f4ccccd),f.add(xyz[1],0x3f4ccccd),xyz[2]);r=append_death_pickup139(1,amount,coinxyz,world,words,counter,state.now_bits,vector=vec);vec,counter,words=r.vector,r.counter,r.rng_words;packets.extend(r.packets);events.append(('currency',amount,r.guid,r.position_bits,None))
 plan=plan_damage_tail_events139(state.sources.hit_sources.initial_mode770,state.sources.hit_sources.event_definitions36,0)
 newstate=replace(newstate,records432=tuple(records),rng_words=tuple(words),pickups=vec,counter2408=counter,movement_sequence2412=sequence,kills1084=(state.kills1084+1)&f.MASK,elites1088=(state.elites1088+(oldrow[424]&1))&f.MASK,killcost2420_bits=f.add(0x3f800000,state.killcost2420_bits))
 return DefaultDamageResult139(newstate,True,True,damage,xyz,tuple(events),tuple(packets),0,plan,direct,healing=ledger,heal_events=heal_events,player_key_writes=player_keys)


@dataclass(frozen=True,kw_only=True)
class DefaultThunderResult139(ThunderClapResult139):
    healing: HealingLedger139
    heal_events: tuple
    player_key_writes: tuple

def cast_thunder_clap_natural139(state, player_xyz, derived, definition, owned80,
                        spell_sets, world, *, source_id=0,
                        suppress_primary_attempt=False, context908=0,healing,healing_sources,heal_on_kill1600_bits=0):
    """Full known922 area2 damage/effect branch with real ordinary death.

    The caller must provide actual inherited source owners. Unsupported slow
    spell removal, proc sources and target kinds stop explicitly. No NPC or
    live record is removed to make the source contract fit.
    """
    if not isinstance(state, OrdinaryDamageState139):
        raise TypeError('Actual ordinary139 damage/source/pickup owner required')
    if not isinstance(definition, ThunderClapDefinition139):
        raise TypeError('Bound current139 Thunder Clap declaration required')
    if (type(owned80) is not bytes or len(owned80) != 80
            or word139(owned80, 0) != definition.pointer):
        raise ValueError('Actual complete selected80B owned record required')
    if context908:
        raise PendingThunderClap139('Inherited proc context pending')
    if len(player_xyz) != 3 or any(f.is_nan(v) or f.is_inf(v) for v in player_xyz):
        raise PendingThunderClap139('Finite actual playerXYZ required')
    scan = state.sources.hit_sources.owned_execution_scan
    if (scan.definition_pointers != (5882740, 5882916)
            or scan.execution_bytes84 != (5, 2)
            or not scan.execution11_arm_skipped):
        raise PendingThunderClap139('Actual cleave+selected thunder owned source required')
    raw = definition.raw88
    value = f.mul(word139(raw, 48), 0x3fb33333)
    value = f.mul(value, word139(owned80, 12))
    value = f.mul(value, word139(owned80, 52))
    value = f.mul(value, 0x3f000000)  #current table1601276, execution2 coefficient
    life = f.mul(derived['1536'], word139(owned80, 72)) if f.to_float(word139(raw, 48)) > 0 else 0
    base = f.mul(derived['1540'], f.add(value, life))
    radius = f.mul(word139(owned80, 24), word139(owned80, 64))
    radius = f.mul(word139(raw, 60), radius)
    radius = radius_bits(f.mul(derived['1580'], radius))
    selected = targets_thunder_clap139(state.records432, player_xyz, state.now_bits, radius)
    spell = word139(raw, 44)
    sets = [tuple(v) for v in spell_sets]
    if len(sets) != 3 or any(len(v) != len(set(v)) for v in sets):
        raise ValueError('Three actual ordered unique spell sets required')
    for index in range(3):
        if not (index == 2 and suppress_primary_attempt) and spell not in sets[index]:
            sets[index] += (spell,)
    hits, writes, packets = [], [], [];ledger=healing;healevents=[];keys=[]
    #Area variant2 is mask0; cleave's variant0 instead has mask2/firstGUID.
    if selected:
        packets.append((306, thunder_launch306139(source_id, spell, selected)))
    duration = f.mul(word139(raw, 8), word139(owned80, 68))
    for target in selected:
        sample, words = next_u32_words(state.rng_words)
        roll = f.mul(f.from_u32(sample >> 8), 0x33800000)
        critical = int(f.to_float(derived['1548']) > f.to_float(roll))
        amount = f.mul(base, derived['1552']) if critical else base
        result = resolve_demo_damage139(replace(state, rng_words=words), target,
            amount, world, spell_id=spell, school=raw[85], critical=critical,
            healing=ledger,healing_sources=healing_sources,outgoing_owned80=owned80,
            inherited_context908=context908,suppress_spell_damage_packet=0,
            heal_on_kill1600_bits=heal_on_kill1600_bits)
        state = result.state;ledger=result.healing;healevents.extend(result.heal_events);keys.extend(result.player_key_writes)
        packets.extend(result.known_packets)
        state, effect = _slow139(state, target, word139(raw, 4), duration)
        writes.extend(effect)
        hits.append((target, amount, critical, result))
    return DefaultThunderResult139(state, tuple(sets), int(bool(selected)), selected,
        base, radius, owned80, tuple(hits), tuple(writes), tuple(packets),
        healing=ledger,heal_events=tuple(healevents),player_key_writes=tuple(keys))
