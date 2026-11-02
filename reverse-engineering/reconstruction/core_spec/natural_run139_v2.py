"""Natural first-level v2: retain actual4603 immediate pickup consumption.

Preparation, player/AI/2890 use their frozen owners unchanged. Only a new
selection producer replaces the old selection's incomplete pickup-empty arm.
"""
from dataclasses import replace
from .natural_run139 import (prepare_natural_run139,advance_natural_run139,
    _adopt_player,_incoming)
from .natural_growth139 import PlayerGrowthContext139
from .natural_choice139 import select_natural_choice139
from .hit_events139 import prove_owned_execution11_absent139
from .candidates139_data import DEFINITIONS139
from .natural_growth139 import PendingNaturalGrowth139


def choose_natural_card_v2_139(state,index,world,*,resume_world):
    if state.incoming.mode2582 or state.xp_queue.entries:
        raise PendingNaturalGrowth139('4603 first local Elwynn mode0/empty forwarding owner only')
    context=PlayerGrowthContext139(state.actor.player,state.actor.ledger,
        state.units,state.actor.damage.movement_sequence2412)
    choice=select_natural_choice139(context,state.actor.damage.pickups,index,
        world,pause_world=resume_world,resume_world=resume_world)
    if not choice.accepted:return state,choice
    result=choice.growth_result
    actor=_adopt_player(state.actor,result.context.player,state.units,
        pickups=choice.pickups,sequence=result.context.movement_sequence2412,
        ledger=result.context.ledger)
    declarations=tuple((DEFINITIONS139[name][0],bytes.fromhex(DEFINITIONS139[name][1]))for name in('cleave','thunder_clap'))
    hit=replace(actor.damage.sources.hit_sources,
        owned_execution_scan=prove_owned_execution11_absent139(actor.player.growth.owned_records80,declarations))
    actor=replace(actor,damage=replace(actor.damage,sources=replace(actor.damage.sources,hit_sources=hit)))
    return replace(state,actor=actor,incoming=_incoming(state.incoming,actor.player,state.units)),choice
