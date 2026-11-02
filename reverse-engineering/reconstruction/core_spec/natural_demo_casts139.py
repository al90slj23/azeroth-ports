"""New current139 basic/cleave/Thunder dispatch to frozen bound family913."""
from dataclasses import replace
from . import binary32 as f
from .natural_damage139 import targets8673_cells139,DefaultCleaveResult139,DefaultThunderResult139
from .ordinary_family_damage139 import resolve_family_damage139
from .death139 import OrdinaryDamageState139,UnknownDeath139,word139
from .thunder_clap139 import ThunderClapDefinition139,PendingThunderClap139,targets_thunder_clap139,thunder_launch306139,_slow139
from .rng import next_u32_words
from .radius import radius_bits
def cast_cleave_demo_family139(state,player_xyz,derived,definition,owned80,spell_sets,
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
        result=resolve_family_damage139(replace(state,rng_words=words),target,amount,world,
            spell_id=845,school=raw[85],critical=critical,inherited_context908=inherited_context908,
            healing=ledger,healing_sources=healing_sources,outgoing_owned80=owned80,
            suppress_spell_damage_packet=0,heal_on_kill1600_bits=heal_on_kill1600_bits)
        state,ledger=result.state,result.healing;packets.extend(result.known_packets)
        events.extend(result.heal_events);keys.extend(result.player_key_writes);hits.append((target,amount,critical,result))
    return DefaultCleaveResult139(state,sets,int(bool(selected)),selected,base,radius,owned80,
        tuple(hits),(),tuple(packets),ledger,tuple(events),tuple(keys))


def cast_thunder_clap_demo_family139(state, player_xyz, derived, definition, owned80,
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
        result = resolve_family_damage139(replace(state, rng_words=words), target,
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
