"""Current1093→4603 selection with its real immediate XP-pickup producer.

4603 scans forward and removes every kind0 pickup already attracted, or an
unattracted one inside the post1542 radius. Arrival time is not read here.
The summed rawXP is scaled/rounded once, before world resume/live1020.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .natural_growth139 import (PlayerGrowthContext139,PlayerGrowthResult139,
    PendingNaturalGrowth139,gain_xp_player139,_world_packets,_replace_live)
from .player_update139 import recalculate_player139,LiveVector139
from .player_effects139 import sync_aura139
from .select139 import initialize_selected139
from .natural_collection139 import round86979_139,despawn170_139
from .death_pickups139 import PickupVector139,word139


@dataclass(frozen=True)
class NaturalChoiceResult139:
    growth_result:PlayerGrowthResult139
    pickups:PickupVector139
    consumed:tuple
    raw_XP_sum:int
    scaled_XP_award:int

    @property
    def accepted(self):return self.growth_result.accepted
    @property
    def packets(self):return self.growth_result.packets


def select_natural_demo_choice139(context,pickups,index,world,*,pause_world,resume_world):
    if not isinstance(context,PlayerGrowthContext139)or not isinstance(pickups,PickupVector139):raise TypeError('Actual complete player/physical/pickup owners')
    p=context.player;g=p.growth
    if g.phase2587!=2 or g.selection_kind2585!=0 or not 0<=index<len(g.candidates):
        return NaturalChoiceResult139(PlayerGrowthResult139(context,(),0,(),accepted=False),pickups,(),0,0)
    if g.pending!=1:raise PendingNaturalGrowth139('Currentfirst completed choice only')
    selected_index=index;card=g.candidates[index]
    if card.variant!='new'or card.ability_id not in('thunder_clap','demo_shout'):raise PendingNaturalGrowth139('Chosen ability/upgrade actual execution remains Pending')
    g=replace(g,owned_records80=g.owned_records80+(initialize_selected139(card.ability_id,card.tier),))
    p=recalculate_player139(replace(p,growth=g))
    #4603 first decrements pending/clears cards while remaining in phase2.
    g=replace(p.growth,pending=p.growth.pending-1,flag2581=1,candidates=())
    context=replace(context,player=replace(p,growth=g))
    rows=list(pickups.storage);count=pickups.count;index=0;amount=0;consumed=[];packets=[]
    radius=g.derived_bits[1560];player=p.player_xyz
    while index<count:
        row=rows[index]
        if word139(row,8)!=0:index+=1;continue
        marker=word139(row,0)
        if marker==0:
            dx=f.sub(word139(row,40),player[0]);dy=f.sub(word139(row,44),player[1])
            distance=sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy)))
            if not f.to_float(distance)<=f.to_float(radius):index+=1;continue
        if marker not in(0,1):raise PendingNaturalGrowth139('Actual32070 marker2 destructor panic/other tag Pending')
        if word139(row,32)!=0:raise PendingNaturalGrowth139('Nonempty32070 auxiliary destructor owner')
        raw=tuple(row[16:24])
        if None in raw:raise PendingNaturalGrowth139('Consumed unknown pickup GUID')
        guid=int.from_bytes(bytes(raw),'little');value=word139(row,12)
        amount=(amount+value)&f.MASK;consumed.append((index,str(guid),value,marker))
        for j in range(index,count-1):rows[j]=rows[j+1]
        count-=1;packets.append(despawn170_139(guid))
    awarded=0;events=[];heals=[]
    if amount:
        rounded=round86979_139(f.mul(g.derived_bits[1564],f.from_u32(amount)))
        if f.is_nan(rounded)or not f.to_float(rounded)>1:rounded=0x3f800000
        awarded=min(f.MASK,max(0,int(f.to_float(rounded))))
        result=gain_xp_player139(context,awarded,world,pause_world=pause_world)
        context=result.context;packets.extend(result.packets);events.extend(result.events);heals.extend(result.heal_events)
    g=context.player.growth
    if g.pending:raise PendingNaturalGrowth139('4603 collectedXP produced another pending choice; next-candidate continuation not restored')
    g=replace(g,phase2587=1,selection_kind2585=255,flags2573=0)
    context=replace(context,player=replace(context.player,growth=g))
    context,resumed=_world_packets(context,world,resume_world,True);packets.extend(resumed)
    p=context.player;rows_live=list(p.live.storage)
    if any(word139(r,20)==1020 for r in p.live.active):raise PendingNaturalGrowth139('Existing1020 replacement retain path not yet restored')
    if p.live.count==p.live.capacity:rows_live.extend([(None,)*32 for _ in range(max(4,2*p.live.capacity)-p.live.capacity)])
    row=list(rows_live[p.live.count]);row[:8]=bytes(8);row[8:12]=struct.pack('<I',12);row[20:32]=struct.pack('<III',1020,f.add(g.now_bits,0x3f800000),0)
    rows_live[p.live.count]=tuple(row);p=_replace_live(p,LiveVector139(tuple(rows_live),p.live.count+1))
    aura=sync_aura139(dict(player_state=p,growth=p.growth,live=p.live,spell_sets=p.spell_sets,aura=p.aura_state,racial80=p.growth.racial_record80,player_xyz=p.player_xyz))
    context=replace(context,player=aura['player_state']);packets.extend(aura['packets'])
    growth=PlayerGrowthResult139(context,tuple(events)+('first_new_declared_ability_and_4603_pickups',),0,tuple(packets),tuple(heals),selected_index=selected_index)
    return NaturalChoiceResult139(growth,PickupVector139(tuple(rows),count),tuple(consumed),amount,awarded)
