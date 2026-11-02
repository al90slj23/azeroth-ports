"""New current139 growth adapter using the source-bound two-owned2181 producer.
Existing typed player/ledger/world context and11033 levels are retained.
"""
from dataclasses import replace
from . import binary32 as f
from .growth139 import threshold139
from .player_update139 import recalculate_player139
from .natural_growth139 import (PlayerGrowthContext139,PlayerGrowthResult139,PendingNaturalGrowth139,_level_heal11033,_world_packets,select_first_new_player139)
from .candidates_second139 import second_candidates139

def gain_xp_player139(context,amount,world,*,pause_world):
    if not isinstance(context,PlayerGrowthContext139)or type(amount)is not int or not 0<=amount<=f.MASK:raise TypeError('Typed current owner and actual u32 award')
    p=context.player;g=replace(p.growth,xp=(p.growth.xp+amount)&f.MASK);context=replace(context,player=replace(p,growth=g))
    events=[];heals=[];packets=[];levels=0
    while g.level<=119 and g.xp>=threshold139(g.level):
        cost=threshold139(g.level);before=g.level
        g=replace(g,level=before+1,pending=(g.pending+1)&f.MASK,xp=(g.xp-cost)&f.MASK)
        p=recalculate_player139(replace(context.player,growth=g));fields=dict(p.growth.player_fields);fields[34]=p.growth.level
        p=replace(p,growth=replace(p.growth,player_fields=fields));context=replace(context,player=p)
        context,request,delta,new_heals=_level_heal11033(context);heals.extend(new_heals);g=context.player.growth;levels+=1
        events.append(dict(kind='level_up',before=before,after=g.level,threshold_spent=cost,heal_request_bits=request,heal_delta_bits=delta))
    fields=dict(g.player_fields);fields[716],fields[717]=g.xp,threshold139(g.level)
    g=replace(g,player_fields=fields);context=replace(context,player=replace(context.player,growth=g))
    eligible=g.pending!=0 and g.phase2587==1 and not g.flags2576&1 and(g.gate2572!=1 or g.flags2573&1)
    if eligible:
        #2181 sets phase2, then35988 gathers/sends stops without changing raw
        #motions. Card generation consumes the actual ongoing RNG afterwards.
        context=replace(context,player=replace(context.player,growth=replace(g,phase2587=2)))
        context,new_packets=_world_packets(context,world,pause_world,False);packets.extend(new_packets);g=context.player.growth
        cards=second_candidates139(g.rng_words,g.owned_records80,g.level,luck_bits=g.derived_bits[1584],cooldown_bits=g.derived_bits[1544],
            blocked_count2092=g.blocked_count2092,banished_count2104=g.banished_count2104,flag275=g.flag275,flag2581=g.flag2581)
        g=replace(g,candidates=cards.candidates,rng_words=cards.rng_words,selection_kind2585=0,generation_counter2400=(g.generation_counter2400+1)&f.MASK)
        context=replace(context,player=replace(context.player,growth=g));events.append(dict(kind='candidate_choice',count=len(cards.candidates),draws=cards.draws))
    return PlayerGrowthResult139(context,tuple(events),levels,tuple(packets),tuple(heals))

