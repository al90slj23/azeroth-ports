"""Fixed1391076 numeric/no-callback prefix over explicit current-layout inputs.

No original files, assets, snapshots or runtime output are read. This is a
bounded component,not a natural Game/owner producer or complete1076 model.
Unsupported shield/callback/revival branches raise instead of inventing state.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f

ONE=0x3f800000
class UnknownIncoming139(NotImplementedError):pass
def uint(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:raise ValueError('Explicit uint'+str(bits)+' required')
    return value
def word(row,offset):
    part=row[offset:offset+4]
    if len(part)!=4 or None in part:raise UnknownIncoming139('Unknown consumed record word '+str(offset))
    return struct.unpack('<I',bytes(part))[0]
def guid(row):return word(row,112)|(word(row,116)<<32)
def record432(value):
    row=tuple(bytes.fromhex(value))if isinstance(value,str)else tuple(value)
    if len(row)!=432 or any(v is not None and(type(v)is not int or not 0<=v<=255)for v in row):raise ValueError('Explicit complete432 NPC cells required')
    return row
def position139(row,now):
    duration=word(row,344)
    if f.to_float(duration)<=0:return tuple(word(row,o)for o in(328,332))
    ratio=f.div(f.sub(now,word(row,340)),duration)
    ratio=0 if f.to_float(ratio)<0 else ONE if f.to_float(ratio)>1 else ratio
    return tuple(f.add(word(row,a),f.mul(f.sub(word(row,b),word(row,a)),ratio))for a,b in((316,328),(320,332)))

@dataclass(frozen=True)
class Buff139:
    kind:int
    value_bits:int
    spell_id:int
    expires_bits:int
@dataclass(frozen=True)
class Modifier139:
    tag:int
    byte4:int
    byte5:int
@dataclass(frozen=True)
class IncomingState139:
    phase2587:int
    protection2576:int
    mode2582:int
    now_bits:int
    hp1440_bits:int
    maximum1536_bits:int
    armor1568_bits:int
    armor_cap1572_bits:int
    nearby1624_bits:int=0
    shield1444_bits:int=0
    barrier1448_bits:int|None=None
    shield_source1344:int|None=None
    shield_remaining1348_bits:int|None=None
    reserve764_bits:int|None=None
    absorbed736_bits:int|None=None
    maximum_shield740_bits:int|None=None
    last_hit1652_bits:int=0
    incoming992:float=0.0
    minimum_one2578:int=0
    player_xy:tuple=(0,0)
    records432:tuple=()
    live32:tuple=()
    modifiers36:tuple=()
    items8:tuple|None=None
    lightning_shield_spell_id:int|None=None
    category1112:tuple=()

    def __post_init__(self):
        for v in(self.phase2587,self.protection2576,self.mode2582,self.minimum_one2578):uint(v,8)
        for v in(self.now_bits,self.hp1440_bits,self.maximum1536_bits,self.armor1568_bits,self.armor_cap1572_bits,self.nearby1624_bits,self.shield1444_bits,self.last_hit1652_bits,*self.player_xy):uint(v)
        if len(self.player_xy)!=2 or len(self.records432)>512:raise ValueError('Bounded explicit spatial input required')
        for row in self.records432:record432(row)
        if not isinstance(self.incoming992,float):raise TypeError('Explicit f64 incoming total required')
        if self.lightning_shield_spell_id is not None:uint(self.lightning_shield_spell_id)

@dataclass(frozen=True)
class PrefixResult139:
    state:IncomingState139
    branch:str
    damage_bits:int
    absorbed_bits:int=0
    history_required:bool=False
    callbacks_complete:bool=False
    pending:tuple=('physical registry/history/keyed state/packets',)

def _min(a,b):
    x=b if f.is_nan(a)else a;y=x if f.is_nan(b)else b
    return x if f.to_float(x)<f.to_float(y)else y
def _max(a,b):
    x=b if f.is_nan(a)else a;y=x if f.is_nan(b)else b
    return x if f.to_float(x)>f.to_float(y)else y
def effective_armor139(state):
    first=next((m for m in state.modifiers36 if m.tag==54 and m.byte4==1),None)
    if first is None:return state.armor1568_bits
    if state.lightning_shield_spell_id is None:raise UnknownIncoming139('Current139 lightning_shield definition/spell producer unresolved')
    active=any(b.spell_id==state.lightning_shield_spell_id and f.to_float(b.expires_bits)>f.to_float(state.now_bits)for b in state.live32)
    if not active:return state.armor1568_bits
    bonus=f.div(f.mul(f.from_u32(first.byte5),f.from_float(3)),f.from_float(100))
    if not f.to_float(bonus)>0:return state.armor1568_bits
    return _min(_max(state.armor1568_bits,state.armor_cap1572_bits),f.add(bonus,state.armor1568_bits))
def nearby_count139(state):
    count=0
    for value in state.records432:
        row=record432(value)
        if word(row,0):continue
        xy=position139(row,state.now_bits);dx,dy=f.sub(xy[0],state.player_xy[0]),f.sub(xy[1],state.player_xy[1])
        if f.to_float(f.add(f.mul(dx,dx),f.mul(dy,dy)))<=64:count+=1
    return count
def resolve_prefix139(state,amount_bits,*,source_guid=0,contact_flag=0):
    if not isinstance(state,IncomingState139):raise TypeError('Explicit current139 state required')
    uint(amount_bits);uint(source_guid,64);uint(contact_flag)
    if state.phase2587!=1:return PrefixResult139(state,'phase_guard',amount_bits,pending=())
    if state.protection2576&1:return PrefixResult139(state,'protection_guard',amount_bits,pending=())
    if state.mode2582!=0:raise UnknownIncoming139('139 mode1 map38882/wave2540 scaling is not yet restored')
    now=f.to_float(state.now_bits)
    if any(b.kind==12 and f.to_float(b.expires_bits)>now for b in state.live32):return PrefixResult139(state,'active_raw12_guard',amount_bits,pending=())
    damage=f.mul(amount_bits,f.sub(ONE,effective_armor139(state)))
    if f.to_float(state.nearby1624_bits)>0 and nearby_count139(state)>=5:damage=f.mul(damage,f.sub(ONE,state.nearby1624_bits))
    absorbed=0;updated=state
    if f.to_float(state.shield1444_bits)>0:
        fields=(state.barrier1448_bits,state.shield_source1344,state.shield_remaining1348_bits,state.reserve764_bits,state.absorbed736_bits,state.maximum_shield740_bits)
        if any(v is None for v in fields):raise UnknownIncoming139('Explicit139 shield/barrier/source/reserve764/736/740 inputs required')
        for v in fields:uint(v)
        absorbed=_min(state.shield1444_bits,damage);shield=f.sub(state.shield1444_bits,absorbed);barrier=_max(f.sub(state.barrier1448_bits,absorbed),0)
        if state.shield_source1344:
            spill=_max(f.sub(absorbed,state.shield_remaining1348_bits),0);depleted=f.to_float(state.shield_remaining1348_bits)<=f.to_float(absorbed)
            remaining=0 if depleted else f.sub(state.shield_remaining1348_bits,absorbed);source=0 if depleted else state.shield_source1344
        else:
            spill=absorbed;depleted=False;remaining=f.sub(state.shield_remaining1348_bits,absorbed);source=0
        used=_min(state.reserve764_bits,spill)
        if f.to_float(used)>0:raise UnknownIncoming139('139 positive reserve spill enters28155/1466 before HP;producer/callback unresolved')
        reserve=_min(shield,state.reserve764_bits);exhausted=f.to_float(shield)<=0
        if exhausted or depleted:
            raise UnknownIncoming139('139 exhausted/depleted shield enters1173 and keyed Aura projection; continuation not yet restored even with empty live/modifier inputs')
        accumulated=f.add(absorbed,state.absorbed736_bits);maximum=_max(state.shield1444_bits,state.maximum_shield740_bits)
        if exhausted or depleted:accumulated=maximum=0
        updated=replace(state,shield1444_bits=shield,barrier1448_bits=barrier,shield_source1344=source,shield_remaining1348_bits=remaining,reserve764_bits=reserve,absorbed736_bits=accumulated,maximum_shield740_bits=maximum)
        damage=f.sub(damage,absorbed)
    hp=f.sub(state.hp1440_bits,damage);updated=replace(updated,hp1440_bits=hp,last_hit1652_bits=state.now_bits,incoming992=state.incoming992+f.to_float(damage))
    key=source_category139(state.records432,source_guid,contact_flag)
    categories=dict(state.category1112);categories[key]=categories.get(key,0.0)+f.to_float(damage)
    updated=replace(updated,category1112=tuple(sorted(categories.items())))
    inert=source_guid==0 or contact_flag==0
    if not inert:
        if state.items8 is None:raise UnknownIncoming139('139 actual item8 source was not supplied')
        raw13=0x80000000
        for buff in state.live32:
            if buff.kind==13 and f.to_float(buff.expires_bits)>now:raw13=f.add(raw13,buff.value_bits)
        if f.to_float(raw13)>0 or state.modifiers36 or state.items8:raise UnknownIncoming139('139 active retaliation/event994 callback source unresolved')
        inert=True  # Only explicitly complete empty item8/modifier36 sources.
    if state.minimum_one2578:updated=replace(updated,hp1440_bits=_max(ONE,hp))
    if f.to_float(updated.hp1440_bits)<=0:raise UnknownIncoming139('139 fatal/revival continuation remains separate')
    return PrefixResult139(updated,'no_reserve_spill_nonfatal_prefix',damage,absorbed_bits=absorbed,history_required=True,callbacks_complete=inert)

@dataclass(frozen=True)
class Source139:
    name:str
    classification:int
    matched_index:int|None
def source_category139(records432,source_guid,contact_flag):
    for value in records432:
        row=record432(value)
        if guid(row)!=source_guid:continue
        if word(row,244)!=f.MASK:return 'boss melee'if contact_flag else'boss spell'
        if row[424]is None:raise UnknownIncoming139('Unknown139 classification424 category')
        return 'elite'if row[424]else'mob melee'if contact_flag else'mob spell'
    return 'area'
def resolve_source139(records432,source_guid,*,english_names):
    uint(source_guid,64)
    for i,value in enumerate(records432):
        row=record432(value)
        if guid(row)!=source_guid:continue
        if word(row,244)!=f.MASK or word(row,40)!=f.MASK:raise UnknownIncoming139('139 boss/pet source producer/localization unresolved')
        pointer=word(row,284)
        if pointer and pointer not in english_names:raise UnknownIncoming139('Missing current139 English NPC definition '+str(pointer))
        if row[424]is None:raise UnknownIncoming139('139 classification byte424 is unknown')
        return Source139(english_names.get(pointer,''),row[424],i)
    return Source139('',4,None)
