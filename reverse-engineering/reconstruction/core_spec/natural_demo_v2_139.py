"""WIP current139 natural2123→925→2890→952 composition.

The scheduler is persistent from the genuine opening. UI selection is a
separate action after this four-stage slice, including when2890 entersphase2.
This omits ten other late884 systems and never claims a complete frame.
"""
from dataclasses import dataclass,replace
from .natural_demo_run_v2_139 import (prepare_natural_demo_run139,advance_natural_demo_run139,
    _incoming)
from .natural_demo_run_v2_139 import choose_natural_demo_card139
from .enemy_ai_dead139_v2 import PhysicalNPCVector139
from .spawn_schedule139_v4 import (from_opening139,from_combat139,
    update_spawn_schedule139,thread_spawn_result139)


@dataclass(frozen=True)
class NaturalDemoSpawnState139:
    opening:object
    run:object
    scheduler:object


@dataclass(frozen=True)
class NaturalDemoSpawnResult139:
    state:NaturalDemoSpawnState139
    natural:object
    spawn:object
    packets:tuple


def prepare_natural_demo139(seed,world):
    opening,run=prepare_natural_demo_run139(seed,world)
    return NaturalDemoSpawnState139(opening,run,from_opening139(opening))


def advance_natural_demo139(state,now,dt,world,*,pause_world):
    natural=advance_natural_demo_run139(state.run,now,dt,world,pause_world=pause_world)
    run=natural.state
    source=from_combat139(state.opening,run.actor,run.units,
        previous=state.scheduler,distance_map=run.distance_map)
    spawned=update_spawn_schedule139(source,now,dt,world)
    actor=thread_spawn_result139(run.actor,spawned)
    units=PhysicalNPCVector139(spawned.state.records432,spawned.state.count)
    run=replace(run,actor=actor,units=units,
        incoming=_incoming(run.incoming,actor.player,units))
    return NaturalDemoSpawnResult139(replace(state,run=run,scheduler=spawned.state),
        natural,spawned,natural.packets+spawned.packets)


def choose_natural_demo_spawn_card139(state,index,world,*,resume_world):
    run,result=choose_natural_demo_card139(state.run,index,world,resume_world=resume_world)
    return replace(state,run=run),result
