"""Current139 first natural level with inherited live/player/heal/world owners.

No XP injection is performed by this module: a collector supplies each actual
award. World motion packet production is a caller-supplied current139 API.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f
from .growth139 import GrowthState139,threshold139
from .candidates139 import first_candidates139
from .select139 import initialize_selected139
from .player_update139 import PlayerUpdateState139,LiveVector139,recalculate_player139,_replace_live
from .player_effects139 import sync_aura139
from .natural_damage139 import NaturalOutgoingLedger139
from .healing139 import HealingEvent139
from .enemy_ai_dead139 import PhysicalNPCVector139


class PendingNaturalGrowth139(NotImplementedError):pass


@dataclass(frozen=True)
class PlayerGrowthContext139:
    player:PlayerUpdateState139
    ledger:NaturalOutgoingLedger139
    units:PhysicalNPCVector139
    movement_sequence2412:int
    auxiliary112_storage:tuple=()
    auxiliary_count:int=0
    companions88_storage:tuple=()
    companions_count:int=0

    def __post_init__(self):
        if self.player.growth.units432_cells!=self.units.active:raise ValueError('Actual full count-domain NPC owner required')
        if self.player.growth.source_counts!=(0,)*7:raise PendingNaturalGrowth139('Nonempty derived/stat/modifier owners')
        if self.auxiliary_count or self.companions_count:raise PendingNaturalGrowth139('Natural default empty aux/comp producer only')


@dataclass(frozen=True)
class PlayerGrowthResult139:
    context:PlayerGrowthContext139
    events:tuple
    levels_gained:int
    packets:tuple
    heal_events:tuple=()
    accepted:bool=True
    selected_index:int|None=None

    @property
    def state(self):return self.context.player.growth


def _count_hp(word):return min(f.MASK,max(0,math.ceil(f.to_float(word))))


def _level_heal11033(context):
    """Current4677 reason1593648→28155→11033→1466, default empty sources."""
    p=context.player;g=p.growth
    if p.heal_gate387!=0:raise PendingNaturalGrowth139('Nondefault gate/overheal modifier route')
    request=f.mul(g.derived_bits[1536],0x3e4ccccd)
    candidate=f.add(g.current_hp_bits,f.mul(request,0x3f800000))
    hp=g.derived_bits[1536]if f.to_float(g.derived_bits[1536])<f.to_float(candidate)else candidate
    delta=f.sub(hp,g.current_hp_bits);ledger=context.ledger;events=()
    if f.to_float(delta)>0:
        rows=list(ledger.reason_totals64);index=next((i for i,(key,value)in enumerate(rows)if key=='level_up'),None)
        prior=0. if index is None else struct.unpack('<d',struct.pack('<Q',rows[index][1]))[0]
        total=struct.unpack('<Q',struct.pack('<d',prior+f.to_float(delta)))[0]
        if index is None:rows.append(('level_up',total))
        else:rows[index]=('level_up',total)
        ident=(ledger.event_counter960+1)&((1<<64)-1)
        ledger=replace(ledger,event_counter960=ident,accepted_count1016=(ledger.accepted_count1016+1)&((1<<64)-1),reason_totals64=tuple(rows))
        #28155 generic system reason: spellID0, borrowed arg3 descriptor/-1,
        #arg4 explicit reason head0. Exact heads need new source-bound sampling.
        events=(HealingEvent139('level_up',delta,g.now_bits,ident,0,-1,0),)
    fields=dict(g.player_fields);fields[22]=_count_hp(hp);fields[28]=_count_hp(g.derived_bits[1536])
    return replace(context,player=replace(p,growth=replace(g,current_hp_bits=hp,player_fields=fields)),ledger=ledger),request,delta,events


def _world_packets(context,world,callback,resume):
    if not callable(callback):
        error=PendingNaturalGrowth139('Actual current world-pause/resume producer required');error.context=context;raise error
    # One physical owner, with staleTail preserved. No NPC/live is cleared to
    # satisfy an inactive-world shortcut.
    from .world_pause139 import WorldMotionOwners139
    owners=WorldMotionOwners139(context.units.storage,context.units.count,
        context.auxiliary112_storage,context.auxiliary_count,
        context.companions88_storage,context.companions_count)
    result=callback(owners,context.player.growth.now_bits,context.movement_sequence2412,world,resume=resume)
    if result.owners!=owners:raise ValueError('Pause/resume must not mutate actual actor motion records')
    return replace(context,movement_sequence2412=result.movement_sequence2412),tuple((op,hx)for op,cap,hx in result.packets)


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
        cards=first_candidates139(g.rng_words,g.owned_records80,g.level,luck_bits=g.derived_bits[1584],cooldown_bits=g.derived_bits[1544],
            blocked_count2092=g.blocked_count2092,banished_count2104=g.banished_count2104,flag275=g.flag275,flag2581=g.flag2581)
        g=replace(g,candidates=cards.candidates,rng_words=cards.rng_words,selection_kind2585=0,generation_counter2400=(g.generation_counter2400+1)&f.MASK)
        context=replace(context,player=replace(context.player,growth=g));events.append(dict(kind='candidate_choice',count=len(cards.candidates),draws=cards.draws))
    return PlayerGrowthResult139(context,tuple(events),levels,tuple(packets),tuple(heals))


def select_first_new_player139(context,index,world,*,resume_world):
    p=context.player;g=p.growth
    if g.phase2587!=2 or g.selection_kind2585!=0 or not 0<=index<len(g.candidates):return PlayerGrowthResult139(context,(),0,(),accepted=False)
    if g.pending!=1:raise PendingNaturalGrowth139('Only first completed choice source')
    card=g.candidates[index]
    if card.variant!='new' or card.ability_id!='thunder_clap':raise PendingNaturalGrowth139('Next chosen ability execution/upgrade source not restored')
    g=replace(g,owned_records80=g.owned_records80+(initialize_selected139(card.ability_id,card.tier),))
    p=recalculate_player139(replace(p,growth=g))
    g=replace(p.growth,pending=0,phase2587=1,selection_kind2585=255,flag2581=1,flags2573=0,candidates=())
    context=replace(context,player=replace(p,growth=g));context,packets=_world_packets(context,world,resume_world,True)
    p=context.player;rows=list(p.live.storage)
    if p.live.count==p.live.capacity:rows.extend([(None,)*32 for _ in range(max(4,2*p.live.capacity)-p.live.capacity)])
    row=list(rows[p.live.count]);row[:8]=bytes(8);row[8:12]=struct.pack('<I',12);row[20:32]=struct.pack('<III',1020,f.add(g.now_bits,0x3f800000),0)
    rows[p.live.count]=tuple(row);p=_replace_live(p,LiveVector139(tuple(rows),p.live.count+1))
    aura=sync_aura139(dict(player_state=p,growth=p.growth,live=p.live,spell_sets=p.spell_sets,aura=p.aura_state,racial80=p.growth.racial_record80,player_xyz=p.player_xyz))
    p=aura['player_state'];context=replace(context,player=p)
    return PlayerGrowthResult139(context,('first_natural_new_thunder_selected',),0,packets+tuple(aura['packets']),selected_index=index)
