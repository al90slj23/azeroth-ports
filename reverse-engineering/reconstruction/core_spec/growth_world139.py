"""Current139 first choice with preserved inactive NPC/auxiliary/claim owners.

The predicate mirrors26364's actual reads. No record/vector is cleared to
call2181 or1093. Background pickups/windows/special/boundary owners are not
read by26364/35988/25613 and remain the caller's unchanged state.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .growth139 import GrowthState139,GrowthResult139,PendingGrowth139,recalculate_growth139,threshold139
from .candidates139 import first_candidates139
from .select139 import SelectResult139,initialize_selected139


def _word(row,offset):
    part=tuple(row[offset:offset+4])
    if len(part)!=4 or None in part:raise PendingGrowth139('Unknown actually consumed world word '+str(offset))
    return int.from_bytes(bytes(part),'little')


@dataclass(frozen=True)
class InactiveWorldProof139:
    NPC_count:int
    dead_markers:int
    stationary_or_expired:int
    gathered_capacity:int=0
    gathered_pointer_sentinel:int=8
    gathered_count:int=0


def check_inactive_world139(state):
    """26364: onlyalive && duration>0 && start+duration>now are gathered.

    Its auxiliary112 and claim88 loops are admitted only with their actual
    empty producer-owned tuples. Dead NPCs do not consume duration/start.
    Active movement remains an explicit pending domain.
    """
    if not isinstance(state,GrowthState139):raise TypeError('GrowthState139 required')
    if state.auxiliary112_cells or state.claims88_cells:
        raise PendingGrowth139('Nonempty auxiliary112/claim88 movement owners')
    if f.is_nan(state.now_bits)or f.is_inf(state.now_bits):raise PendingGrowth139('Finite world clock required')
    if type(state.units432_cells)is not tuple or len(state.units432_cells)>128:
        raise ValueError('Explicit bounded ordered active NPC records')
    dead=inactive=0
    for row in state.units432_cells:
        if len(row)!=432 or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in row):raise ValueError('432 known/None cells')
        marker=_word(row,0)
        if marker not in(0,1):raise PendingGrowth139('Only actual alive/dead NPC markers')
        if marker:
            dead+=1;continue
        duration=_word(row,344)
        if f.is_nan(duration)or f.is_inf(duration):raise PendingGrowth139('Finite NPC duration domain')
        if f.to_float(duration)>0:
            start=_word(row,340)
            if f.is_nan(start)or f.is_inf(start):raise PendingGrowth139('Finite NPC movement start')
            if f.to_float(f.add(duration,start))>f.to_float(state.now_bits):
                raise PendingGrowth139('Active26364 moving-NPC stop/resume projection')
        inactive+=1
    return InactiveWorldProof139(len(state.units432_cells),dead,inactive)


def gain_xp_world139(state,amount):
    """Full4677 numeric/choice projection; original world tuples retained."""
    if not isinstance(state,GrowthState139):raise TypeError('GrowthState139 required')
    if type(amount)is not int or not 0<=amount<=f.MASK:raise ValueError('u32 XP award')
    state=replace(state,xp=(state.xp+amount)&f.MASK);events=[]
    while state.level<=119 and state.xp>=threshold139(state.level):
        cost=threshold139(state.level);before=state.level
        state=replace(state,pending=(state.pending+1)&f.MASK,xp=(state.xp-cost)&f.MASK)
        state=recalculate_growth139(state,before+1);fields=dict(state.player_fields);fields[34]=state.level
        request=f.mul(state.derived_bits[1536],0x3e4ccccd)
        if state.heal_gate387>4:request=f.mul(request,0x3f000000)
        old=state.current_hp_bits;value=f.add(old,request);hp=value if f.to_float(value)<f.to_float(state.derived_bits[1536])else state.derived_bits[1536]
        fields[22]=max(0,math.ceil(f.to_float(hp)));fields[28]=max(0,math.ceil(f.to_float(state.derived_bits[1536])))
        state=replace(state,current_hp_bits=hp,player_fields=fields)
        events.append(dict(kind='level_up',before=before,after=state.level,threshold_spent=cost,heal_request_bits=request,heal_delta_bits=f.sub(hp,old)))
    fields=dict(state.player_fields);fields[716],fields[717]=state.xp,threshold139(state.level);state=replace(state,player_fields=fields)
    eligible=state.pending!=0 and state.phase2587==1 and not state.flags2576&1
    eligible=eligible and(state.gate2572!=1 or state.flags2573&1)
    if eligible:
        proof=check_inactive_world139(state)
        result=first_candidates139(state.rng_words,state.owned_records80,state.level,
            luck_bits=state.derived_bits[1584],cooldown_bits=state.derived_bits[1544],
            blocked_count2092=state.blocked_count2092,banished_count2104=state.banished_count2104,
            flag275=state.flag275,flag2581=state.flag2581)
        state=replace(state,candidates=result.candidates,rng_words=result.rng_words,phase2587=2,
            selection_kind2585=0,generation_counter2400=(state.generation_counter2400+1)&f.MASK)
        events.append(dict(kind='candidate_choice',count=len(result.candidates),draws=result.draws,
            inactive_world=dict(NPC_count=proof.NPC_count,dead=proof.dead_markers,stationary_or_expired=proof.stationary_or_expired)))
    return GrowthResult139(state,tuple(events),sum(x['kind']=='level_up'for x in events))


def select_card_world139(state,index):
    """1093 new-ability choice with proven empty26364 gathered vector."""
    if not isinstance(state,GrowthState139):raise TypeError('GrowthState139 required')
    if state.phase2587!=2 or not 0<=index<len(state.candidates)or state.selection_kind2585==255:
        return SelectResult139(state,False,None,())
    if state.selection_kind2585!=0:raise PendingGrowth139('Nonordinary selection source')
    card=state.candidates[index]
    if card.variant!='new':raise PendingGrowth139('Existing-ability upgrade/gold selection')
    if state.source_counts!=(0,)*7:raise PendingGrowth139('Nonempty stat/ability modifier sources')
    check_inactive_world139(state)
    if state.pending!=1 or state.live32_cells:raise PendingGrowth139('Only first completed level choice without prior live effects')
    owned=state.owned_records80+(initialize_selected139(card.ability_id,card.tier),)
    state=recalculate_growth139(replace(state,owned_records80=owned),state.level)
    live=[None]*32;live[:8]=bytes(8);live[8:12]=struct.pack('<I',12);live[20:32]=struct.pack('<III',1020,f.add(state.now_bits,0x3f800000),0)
    state=replace(state,pending=0,phase2587=1,selection_kind2585=255,flag2581=1,flags2573=0,candidates=(),live32_cells=(tuple(live),))
    return SelectResult139(state,True,len(owned)-1,
        ('Newabilityonly;UI/appearance/additionalkeyedfields/fullpackets remain observations',
         'Nonemptylive32 recalculation and active26364 movements remain pending',
         'All original NPC/auxiliary/claim owner tuples retained;no clear-world bypass'))
