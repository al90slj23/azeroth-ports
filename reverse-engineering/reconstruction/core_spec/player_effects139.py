"""Current139 Human perception922 and live12/8→1173 Aura production.

Physical live32 storage is retained. Inactive Aura payload and the scratch
word written to perception live+16 stay None. This module does not read any
original program, snapshot, DBC, captured output, file or host resource.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .growth139 import GrowthState139
from .player_update139 import LiveVector139,PlayerUpdateState139,recalculate_player139
from .candidates139_data import DEFINITIONS139

PERCEPTION_POINTER139=5891892
PERCEPTION_DEFINITION88_139=bytes.fromhex('080000009a99193e00000000309e59000a0000004fc259000a00000059c2590012000000b9b659000200000078500000000000000000f0410000000000000000000000000000204100000000000000000000000009010000')


class PendingPlayerEffects139(NotImplementedError):pass


def _word(row,offset,width=4):
    cells=tuple(row[offset:offset+width])
    if len(cells)!=width or None in cells:raise PendingPlayerEffects139('Unknown actually consumed player effect word '+str(offset))
    return int.from_bytes(bytes(cells),'little')


def _finite(word):return not f.is_nan(word)and not f.is_inf(word)


def self_launch306139(source_guid,spell):
    """10490 target variant2 emits mask0,without a packed explicit target."""
    raw=source_guid.to_bytes(8,'little');packed=bytes([sum((v!=0)<<i for i,v in enumerate(raw))])+bytes(v for v in raw if v)
    return(packed+packed+struct.pack('<IHBQBH',spell,256,1,source_guid,0,0)).hex()


@dataclass(frozen=True)
class AuraSnapshot139:
    capacity:int
    count:int
    storage:tuple
    flag2569:int|None
    def __post_init__(self):
        if(self.capacity,self.count)not in((0,0),(48,48))or len(self.storage)!=self.count:raise PendingPlayerEffects139('Onlyconstructor-empty or complete48 Aura owner')
        for row in self.storage:
            if len(row)!=16 or any(v is not None and(type(v)is not int or not 0<=v<=255)for v in row):raise ValueError('16known/None Aura cells')
        if self.flag2569 is not None and(type(self.flag2569)is not int or not 0<=self.flag2569<=255):raise ValueError('Aura readyflag byte')
    @classmethod
    def empty_constructor139(cls):return cls(0,0,(),None)


def _validate(context):
    growth=context['growth'];live=context['live'];aura=context['aura']
    if not isinstance(growth,GrowthState139)or not isinstance(live,LiveVector139)or not isinstance(aura,AuraSnapshot139):raise TypeError('Typed current139 growth/live/Aura owners required')
    if growth.live32_cells!=live.active:raise ValueError('Growth/live physical owner mismatch')
    if growth.source_counts!=(0,)*7:raise PendingPlayerEffects139('Nonempty modifier/timed/definition sources')
    if growth.mode2582!=0:raise PendingPlayerEffects139('Current singleplayer callback domain')
    if not _finite(growth.now_bits):raise PendingPlayerEffects139('Finite current clock')
    if context['racial80']!=growth.racial_record80 or _word(context['racial80'],0)!=PERCEPTION_POINTER139:raise PendingPlayerEffects139('Actual Human racial record source required')
    for record in growth.owned_records80:
        pointer=_word(record,0);known=next((bytes.fromhex(raw)for p,raw,_ in DEFINITIONS139.values()if p==pointer),None)
        if known is None or _word(known,0)==12:raise PendingPlayerEffects139('Unknown/owned cooldown Aura source')
    for row in live.active:
        kind,spell=_word(row,8),_word(row,20)
        if not(kind==12 and spell==1020 or kind==8 and spell==20600):raise PendingPlayerEffects139('Only actual selected1020 and Human perception live sources')
        if _word(row,0,8)!=0 or _word(row,28)!=0:raise PendingPlayerEffects139('Other source GUID/periodic budget')
        if not _finite(_word(row,24)):raise PendingPlayerEffects139('Finite live expiry')
        if kind==8 and not _finite(_word(row,12)):raise PendingPlayerEffects139('Finite actual perception value12')
    return growth,live,aura


def _slot_tag(row):
    tag=_word(row,0)
    if tag not in(0,1):raise PendingPlayerEffects139('Unknown/noncanonical Aura option tag')
    return tag


def _spell(row):return _word(row,4)if _slot_tag(row)else 0


def _flags(storage,group):
    result=0
    for index in range(group*8,group*8+8):
        if _slot_tag(storage[index]):result|=(9 if index<32 else 8)<<(4*(index&7))
    return result


def _stacks(storage,group):
    result=0
    for index in range(group*4,group*4+4):
        if _slot_tag(storage[index]):
            count=_word(storage[index],12);value=min(count,255)-1 if count else 0
            result|=value<<(8*(index&3))
    return result


def sync_aura139(context):
    """1173 active live12/8,empty modifiers/no effect12 owned cooldown Aura."""
    growth,live,previous=_validate(context);now=growth.now_bits;accepted=[]
    for index,row in enumerate(live.active):
        if not f.to_float(_word(row,24))>f.to_float(now):continue
        kind,spell=_word(row,8),_word(row,20)
        # Kind12 has no consumed numeric payload. Its +12/+16 remain unknown.
        value=_word(row,12)if kind==8 else 0;dominated=False
        for other_index,other in enumerate(live.active):
            if index==other_index or _word(other,20)!=spell or not f.to_float(_word(other,24))>f.to_float(now):continue
            other_value=_word(other,12)if _word(other,8)==8 else 0
            if f.to_float(other_value)>f.to_float(value)or other_index<index and other_value==value:dominated=True;break
        if not dominated:accepted.append(row)
    groups=[]
    for row in accepted:
        spell,expires=_word(row,20),_word(row,24);found=next((i for i,v in enumerate(groups)if v[0]==spell),None)
        if found is None:groups.append((spell,expires,1))
        else:
            old=groups[found];minimum=expires if f.to_float(expires)<f.to_float(old[1])else old[1];groups[found]=(spell,minimum,(old[2]+1)&f.MASK)
    if len(groups)>32:raise PendingPlayerEffects139('Morethan32 accepted positive Aura groups')
    storage=[tuple(bytes(4))+(None,)*12 for _ in range(48)]
    for i,(spell,expires,count)in enumerate(groups):storage[i]=tuple(struct.pack('<4I',1,spell,expires,count))
    ready=previous.count==48
    if ready and previous.flag2569 is None:raise PendingPlayerEffects139('Previous48 consumes ready flag2569')
    ready=ready and bool(previous.flag2569&1);fields=dict(growth.player_fields);updates={}
    for i,row in enumerate(storage):
        value=_spell(row)
        if not ready or _spell(previous.storage[i])!=value:updates[47+i]=value
    for group in range(6):
        value=_flags(storage,group)
        if not ready or _flags(previous.storage,group)!=value:updates[95+group]=value
    for group in range(12):
        value=_stacks(storage,group)
        if not ready or _stacks(previous.storage,group)!=value:updates[113+group]=value
    fields.update(updates);new=replace(growth,player_fields=fields);aura=AuraSnapshot139(48,48,tuple(storage),1)
    transitions=tuple((i,_spell(previous.storage[i])if previous.count==48 else 0,_spell(row))for i,row in enumerate(storage)if previous.count!=48 or _spell(previous.storage[i])!=_spell(row))
    result=dict(growth=new,live=live,spell_sets=context['spell_sets'],aura=aura,packets=(),
        known_player_field_updates=updates,logical_Aura_transitions=transitions,
        plan=('1173:active_live_filter_and_dominance','1173:logical_groups','1173:48x16_Aura_and_conditional_keys'),
        pointer_and_physical_BTree_predictions=False)
    owner=context.get('player_state')
    if owner is not None:
        if not isinstance(owner,PlayerUpdateState139)or owner.growth!=growth or owner.live!=live:raise ValueError('Caller Aura owner snapshot mismatch')
        result['player_state']=replace(owner,growth=new,live=live,spell_sets=tuple(tuple(v)for v in context['spell_sets']),aura_state=aura)
    return result


def _nearby_alive139(growth,player):
    chosen=[];now=growth.now_bits
    for row in growth.units432_cells:
        marker=_word(row,0)
        if marker:
            if marker!=1:raise PendingPlayerEffects139('Other NPC marker source')
            continue
        duration=_word(row,344)
        if not _finite(duration):raise PendingPlayerEffects139('Finite NPC duration')
        if f.to_float(duration)<=0:x,y=_word(row,328),_word(row,332)
        else:
            fraction=f.div(f.sub(now,_word(row,340)),duration)
            if f.to_float(fraction)<0:fraction=0
            if f.to_float(fraction)>1:fraction=0x3f800000
            x=f.add(_word(row,316),f.mul(f.sub(_word(row,328),_word(row,316)),fraction));y=f.add(_word(row,320),f.mul(f.sub(_word(row,332),_word(row,320)),fraction))
        dx,dy=f.sub(x,player[0]),f.sub(y,player[1]);distance=f.add(f.mul(dx,dx),f.mul(dy,dy))
        if f.to_float(distance)<=900:chosen.append(_word(row,112,8))
    return tuple(chosen)


def cast_perception139(context):
    """922 exec9/effect8: real30-radius query,self306,live8,1542,1173."""
    growth,live,aura=_validate(context);owner=context.get('player_state')
    if not isinstance(owner,PlayerUpdateState139):raise TypeError('Actual caller player_state needed for stat/pool/speed owners')
    if owner.growth!=growth or owner.live!=live:raise ValueError('Caller effect owner snapshot mismatch')
    if growth.phase2587!=1:raise PendingPlayerEffects139('Running parent2123 component domain')
    racial=context['racial80'];player=context['player_xyz']
    if len(player)!=3:raise ValueError('Explicit player XYZ')
    sets=tuple(row if 20600 in row else tuple(row)+(20600,)for row in context['spell_sets'])
    targets=_nearby_alive139(growth,player)
    if not targets:return dict(growth=growth,live=live,spell_sets=sets,aura=aura,packets=(),success=0,
        plan=('922:attempt_ledgers','27754:actual30radius_no_alive_NPC'),nearby_NPC_guids=())
    duration=f.mul(f.mul(f.mul(_word(PERCEPTION_DEFINITION88_139,68),0x3fb33333),_word(racial,28)),_word(racial,68))
    if f.is_nan(duration)or not f.to_float(duration)>f.to_float(0x3dcccccd):duration=0x3dcccccd
    expires=f.add(growth.now_bits,duration);value=f.mul(_word(racial,76),_word(PERCEPTION_DEFINITION88_139,4))
    rows=list(live.storage);retained=[row for row in live.active if not(_word(row,20)==20600 and _word(row,0,8)==0)]
    for i,row in enumerate(retained):rows[i]=row
    count=len(retained)
    if count==len(rows):rows.extend([tuple([None]*32)for _ in range(max(4,2*len(rows))-len(rows))])
    record=list(rows[count]);record[0:16]=struct.pack('<QII',0,8,value);record[16:20]=[None]*4;record[20:32]=struct.pack('<III',20600,expires,0);rows[count]=tuple(record)
    updated_live=LiveVector139(tuple(rows),count+1);updated_growth=replace(growth,live32_cells=updated_live.active)
    numeric=recalculate_player139(replace(owner,growth=updated_growth,live=updated_live,spell_sets=sets))
    next_context=dict(context,growth=numeric.growth,live=updated_live,spell_sets=sets,aura=aura,player_state=numeric)
    synced=sync_aura139(next_context);synced.update(success=1,
        packets=((306,self_launch306139(0,20600)),),
        plan=('922:attempt_ledgers','27754:actual30radius_alive_NPC','10490:self306','922:retain_same_spell_owner0','922:append_live8_unknown_word16','1542:actual_live8_value12')+synced['plan'],
        nearby_NPC_guids=targets,live_written_bytes=28,live_unknown_written_bytes=4)
    return synced
