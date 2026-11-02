"""Current139 cleave upgrade selection with ordered25511/1093 numeric loop.

Only the actual first ordinary cleave card domain is admitted. New cards use
the separately frozen inactive-world path; gold and saturated/other skills
remain pending. No card or owner is converted into another variant.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .growth139 import GrowthState139,PendingGrowth139,recalculate_growth139
from .growth_world139 import check_inactive_world139,select_card_world139

UPGRADE_TABLES139=(
    (1043878380,1048576000,1051595899,1055622431,1059481190),
    (1032805417,1036831949,1040522936,1043207291,1047233823),
    (1,1,1,2,2),
    (1039516303,1043878380,1048576000,1051931443,1056964608),
    (1041865114,1046562734,1050253722,1053609165,1058642330),
)
UPGRADE_TABLE_POINTERS139=(5405004,5405040,5405076,5405112,5405148)


def _word(raw,offset):return int.from_bytes(raw[offset:offset+4],'little')


def upgrade_value_cleave139(words,kind,tier):
    if kind not in(0,1,2)or tier not in range(5):raise PendingGrowth139('Only declared current cleave upgrade kinds0/1/2 and tiers0..4')
    if kind==0:
        denominator=f.add(f.mul(f.from_u32(words[8]),0x3f000000),0x3f800000)
        return f.div(UPGRADE_TABLES139[0][tier],denominator)
    if kind==1:
        factor=f.div(f.add(words[4],0xbe4ccccd),0x3f4ccccd)
        if f.is_nan(factor)or not f.to_float(factor)>0:factor=0
        return f.mul(UPGRADE_TABLES139[1][tier],factor)
    remaining=max(0,12-words[5]);return f.from_u32(min(remaining,UPGRADE_TABLES139[2][tier]))


def apply_first_cleave_upgrade139(raw80,kinds,tier):
    if type(raw80)is not bytes or len(raw80)!=80 or _word(raw80,0)!=5882740:raise PendingGrowth139('Actual current constructor cleave80 required')
    if tier not in range(5)or type(kinds)is not tuple or len(kinds)!=(2 if tier==4 else 1)or len(set(kinds))!=len(kinds)or any(k not in((0,1)if tier==0 else(0,1,2))for k in kinds):
        raise PendingGrowth139('Actual first-candidate cleave kind/tier shape required')
    words=list(struct.unpack('<20I',raw80))
    if words[1]!=1 or any(words[i]for i in(5,8,9,10,11,12))or any(words[i]!=0x3f800000 for i in(3,4,6,7)):
        raise PendingGrowth139('Only first constructor cleave upgrade,not saturated/repeated selection')
    if tuple(words[13:])!=(0x3f800000,0x3f800000,0,0x3f800000,0x3f800000,0,0x3f800000):
        raise PendingGrowth139('Constructor-derived neutral additional modifier words required')
    for kind in kinds:
        words[1]=(words[1]+1)&f.MASK;value=upgrade_value_cleave139(words,kind,tier)
        if kind==0:words[3]=f.mul(f.add(value,0x3f800000),words[3])
        elif kind==1:words[4]=f.sub(words[4],value)
        else:words[5]=(words[5]+int(f.to_float(value)))&f.MASK
        words[8+kind]=(words[8+kind]+1)&f.MASK
        denominator=f.add(f.mul(f.from_u32(max(0,words[1]-2)),0x3e000000),0x3f800000)
        factor=f.add(f.div(0x3d23d70a,denominator),0x3f800000)
        words[3]=f.mul(factor,words[3])
    return struct.pack('<20I',*words)


@dataclass(frozen=True)
class SelectionAnyResult139:
    state:GrowthState139
    accepted:bool
    new_owned_index:int|None
    upgraded_index:int|None
    pending:tuple=()


def select_card_upgrade139(state,index):
    if not isinstance(state,GrowthState139):raise TypeError('GrowthState139 required')
    if state.phase2587!=2 or not 0<=index<len(state.candidates)or state.selection_kind2585==255:
        return SelectionAnyResult139(state,False,None,None)
    if state.selection_kind2585!=0:raise PendingGrowth139('Only ordinary kind0 selection')
    card=state.candidates[index]
    if card.variant!='upgrade' or card.ability_id!='cleave' or card.owned_index!=0:
        raise PendingGrowth139('Actual existing cleave upgrade candidate required')
    if len(state.owned_records80)!=1 or state.source_counts!=(0,)*7:
        raise PendingGrowth139('First constructor owned cleave/empty modifier sources required')
    check_inactive_world139(state)
    if state.pending!=1 or state.live32_cells:raise PendingGrowth139('First completion/no prior live source required')
    upgraded=apply_first_cleave_upgrade139(state.owned_records80[0],card.kinds,card.tier)
    state=recalculate_growth139(replace(state,owned_records80=(upgraded,)),state.level)
    live=[None]*32;live[:8]=bytes(8);live[8:12]=struct.pack('<I',12);live[20:32]=struct.pack('<III',1020,f.add(state.now_bits,0x3f800000),0)
    state=replace(state,pending=0,phase2587=1,selection_kind2585=255,flag2581=1,flags2573=0,candidates=(),live32_cells=(tuple(live),))
    return SelectionAnyResult139(state,True,None,0,
        ('Currentfirstcleaveonly;other/saturated/repeated upgrades remain pending',
         'UI/appearance/additionalkeys/completepackets/Aura48/physicalallocations remain observations',
         'InactiveNPC/aux/claim owners retained;active movement/nonemptylive recalc pending'))


def select_card_any139(state,index):
    """Route actual new and cleave-upgrade variants; never redraw or coerce."""
    if not isinstance(state,GrowthState139):raise TypeError('GrowthState139 required')
    if state.phase2587!=2 or not 0<=index<len(state.candidates)or state.selection_kind2585==255:
        return SelectionAnyResult139(state,False,None,None)
    variant=state.candidates[index].variant
    if variant=='new':
        result=select_card_world139(state,index)
        return SelectionAnyResult139(result.state,result.accepted,result.new_owned_index,None,result.pending)
    if variant=='upgrade':return select_card_upgrade139(state,index)
    raise PendingGrowth139('Gold/other candidate variants remain pending')
