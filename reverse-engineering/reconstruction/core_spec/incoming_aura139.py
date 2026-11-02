"""Current1391173 empty-output Aura producer and1076 shield cleanup domain.

The complete original1173 has additional nonempty-source branches. This model
rejects those rather than replacing their effects with an empty container.
It reads no original, resource, capture or oracle output.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .incoming139 import IncomingState139,PrefixResult139,UnknownIncoming139,uint,_min,_max

@dataclass(frozen=True)
class AuraInputs139:
    owned_definition_kinds:tuple
    racial_definition_kind:int
    live32:tuple
    modifiers36:tuple
    previous_count:int
    previous_flag2569:int|None
    previous_storage:tuple
    player_fields:tuple

@dataclass(frozen=True)
class AuraResult139:
    capacity:int
    count:int
    storage:tuple
    flag2569:int
    player_fields:tuple
    written_keys:tuple

def empty_aura139(owner):
    if not isinstance(owner,AuraInputs139):raise TypeError('Explicit current139 Aura sources required')
    if owner.live32 or owner.modifiers36:raise UnknownIncoming139('1173 nonempty live/modifier sources need their actual producer')
    for kind in owner.owned_definition_kinds+(owner.racial_definition_kind,):
        uint(kind)
        if kind==12:raise UnknownIncoming139('1173 owned/racial kind12 cooldown Aura source unresolved')
    if owner.previous_count not in(0,48)or len(owner.previous_storage)!=owner.previous_count:raise UnknownIncoming139('1173 prior Aura shape outside declared empty48 domain')
    if owner.previous_count==48:
        if owner.previous_flag2569 is None:raise UnknownIncoming139('1173 prior48 consumes2569 flag')
        uint(owner.previous_flag2569,8)
        for row in owner.previous_storage:
            if len(row)!=16 or any(x is None for x in row[:4]):raise UnknownIncoming139('1173 prior Aura tag unknown')
            if any(row[:4]):raise UnknownIncoming139('1173 prior nonempty Aura diff/hash needs actual continuation')
    known=tuple((0,0,0,0)+(None,)*12 for _ in range(48))
    # Only the old count48 and ready low bit permit all-equal writes to skip.
    writes=()if owner.previous_count==48 and owner.previous_flag2569&1 else tuple(range(47,101))+tuple(range(113,125))
    fields=dict(owner.player_fields)
    for key in writes:fields[key]=0
    return AuraResult139(48,48,known,1,tuple(sorted(fields.items())),writes)

@dataclass(frozen=True)
class ShieldCleanupResult139:
    prefix:PrefixResult139
    aura:AuraResult139
    reason:str

def resolve_cleanup_incoming139(state,amount_bits,owner,*,source_guid=0,contact_flag=0):
    if not isinstance(state,IncomingState139):raise TypeError('Explicit current139 incoming state required')
    uint(amount_bits);uint(source_guid,64);uint(contact_flag)
    if state.phase2587!=1 or state.protection2576&1 or state.mode2582!=0:raise UnknownIncoming139('Cleanup component requires entered phase1/mode0')
    if source_guid or contact_flag or state.records432 or state.modifiers36:raise UnknownIncoming139('Cleanup component currently requires source0/contact0/empty NPC and modifier sources')
    if any(b.kind!=7 for b in state.live32):raise UnknownIncoming139('Cleanup component currently requires explicit shield-only live source')
    if not f.to_float(state.shield1444_bits)>0:raise UnknownIncoming139('Cleanup requires positive shield')
    values=(state.barrier1448_bits,state.shield_source1344,state.shield_remaining1348_bits,state.reserve764_bits,state.absorbed736_bits,state.maximum_shield740_bits)
    for value in values:
        if value is None:raise UnknownIncoming139('Unknown consumed139 shield scalar')
        uint(value)
    damage=f.mul(amount_bits,f.sub(0x3f800000,state.armor1568_bits));absorbed=_min(state.shield1444_bits,damage)
    shield=f.sub(state.shield1444_bits,absorbed);barrier=_max(f.sub(state.barrier1448_bits,absorbed),0)
    if state.shield_source1344:
        spill=_max(f.sub(absorbed,state.shield_remaining1348_bits),0);depleted=f.to_float(state.shield_remaining1348_bits)<=f.to_float(absorbed)
        remaining=0 if depleted else f.sub(state.shield_remaining1348_bits,absorbed);source=0 if depleted else state.shield_source1344
    else:
        spill=absorbed;depleted=False;remaining=f.sub(state.shield_remaining1348_bits,absorbed);source=0
    if f.to_float(_min(state.reserve764_bits,spill))>0:raise UnknownIncoming139('Positive reserve spill28155/1466 still unresolved')
    reserve=_min(shield,state.reserve764_bits);exhausted=f.to_float(shield)<=0
    if not(exhausted or depleted):raise UnknownIncoming139('No1173 cleanup; use the partial-shield component')
    if not exhausted and any(b.spell_id!=state.shield_source1344 for b in state.live32):raise UnknownIncoming139('Remaining live sources require nonempty1173 recovery')
    if owner.live32 or owner.modifiers36:raise UnknownIncoming139('Aura owner must be the actual post-retain empty source')
    aura=empty_aura139(owner)
    if exhausted:barrier=0;source=0;remaining=0
    damage=f.sub(damage,absorbed);hp=f.sub(state.hp1440_bits,damage)
    if state.minimum_one2578:hp=_max(0x3f800000,hp)
    if f.to_float(hp)<=0:raise UnknownIncoming139('Fatal/revival after1173 remains a separate continuation')
    categories=dict(state.category1112);categories['area']=categories.get('area',0.0)+f.to_float(damage)
    updated=replace(state,shield1444_bits=shield,barrier1448_bits=barrier,shield_source1344=source,shield_remaining1348_bits=remaining,reserve764_bits=reserve,absorbed736_bits=0,maximum_shield740_bits=0,live32=(),hp1440_bits=hp,last_hit1652_bits=state.now_bits,incoming992=state.incoming992+f.to_float(damage),category1112=tuple(sorted(categories.items())))
    return ShieldCleanupResult139(PrefixResult139(updated,'shield_cleanup1173_nonfatal',damage,absorbed,True,True,('physical BTree/resource pointers retained as unknown',)),aura,'shield_exhausted'if exhausted else'shield_source_depleted')
