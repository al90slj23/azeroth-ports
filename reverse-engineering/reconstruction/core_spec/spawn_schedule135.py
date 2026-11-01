"""Independent947 ordinary-budget/density frame with actual spawn composition.

Input explicitly declares timed event/elite/Boss paths not due. Their producers
are not replaced by this ordinary subsystem. Flat-terrain placement is composed
with weighted selection, full normal records and ordered shared RNG state.
"""
from dataclasses import dataclass,replace
import math
import struct
from . import binary32 as f
from .spawn135 import SpawnInput,spawn_normal,choose_spawn,eligible_normals,max_numeric,min_numeric
from .spawn_math135 import exp_bits
from .spawn_geometry135 import hypot_bits
from .spawn_position135 import PositionInput,sample_position
from .spawn_schedule135_data import BOSS_FINAL_FLAGS
from .spawn135_data import NORMALS
from .progression134 import trunc_sat_u32
from .record_cells135 import u32

ONE=0x3f800000


@dataclass(frozen=True)
class FrameInput:
    zone:int
    now_bits:int
    dt_bits:int
    budget_bits:int
    kill_cost_bits:int
    mode:int
    members:int
    difficulty:int
    zone_multiplier_bits:int
    victory_field400:int
    endless_flag:int
    endless_start_bits:int
    player_xyz:tuple
    previous_player_xyz:tuple
    velocity_xy:tuple
    flat_height_bits:int
    rng_words:tuple
    counter:int
    unit_records:tuple
    other_event_timers_future:bool


@dataclass(frozen=True)
class FrameResult:
    status:str
    budget_bits:int
    kill_cost_bits:int
    rng_words:tuple
    counter:int
    unit_records:tuple
    velocity_xy:tuple
    requests:tuple
    draws:int


def _word(raw,offset):return u32(raw,offset,'947 ordinary schedule')


def _slowdown(units):
    value=ONE;boss_flags=dict(BOSS_FINAL_FLAGS)
    for raw in units:
        if _word(raw,0)==0 and _word(raw,244)!=f.MASK:
            pointer=_word(raw,256)
            if pointer not in boss_flags:raise ValueError('Unknown active Boss definition source')
            value=min_numeric(value,f.from_float(.3 if boss_flags[pointer] else .45))
    return value


def budget_rate(state,units):
    minute=f.div(state.now_bits,f.from_float(60))
    killed=f.mul(state.kill_cost_bits,exp_bits(f.div(state.dt_bits,f.from_float(-12))))
    base=f.mul(f.add(f.add(f.mul(minute,f.from_float(.32)),f.from_float(.9)),
                     f.mul(minute,f.mul(minute,f.from_float(.025)))),f.from_float(.6))
    r=_slowdown(units);ordinary=f.mul(base,r);denominator=ordinary
    elapsed=0
    if state.victory_field400==1:elapsed=max_numeric(f.div(f.sub(state.now_bits,state.endless_start_bits),f.from_float(60)),0)
    multiplier=f.add(f.mul(elapsed,f.from_float(.1)),f.from_float(1.5))
    if state.endless_flag==1:ordinary=f.mul(ordinary,multiplier)
    if state.endless_flag!=0:denominator=f.mul(denominator,multiplier)
    catchup=f.div(f.mul(f.div(killed,f.from_float(12)),f.from_float(1.25)),max_numeric(f.from_float(.001),denominator))
    catchup=ONE if f.to_float(catchup)<1 else catchup
    catchup=f.from_float(3)if f.to_float(catchup)>3 else catchup
    group=f.add(f.mul(f.mul(f.from_float(.7)if state.zone<3 else ONE,f.from_u32((state.members-1)&f.MASK)),f.from_float(.312)),ONE)if state.mode==1 else ONE
    budget=f.add(state.budget_bits,f.mul(state.dt_bits,f.mul(f.mul(ordinary,catchup),group)))
    return budget,killed,minute,group


def step_ordinary_frame(state:FrameInput):
    if not state.other_event_timers_future:raise ValueError('Other event schedules are unresolved')
    if not math.isfinite(f.to_float(state.now_bits))or not math.isfinite(f.to_float(state.dt_bits)):
        raise ValueError('Controlled ordinary-frame domain has finite simulation time')
    units=[bytes.fromhex(x)for x in state.unit_records]
    if any(len(x)!=424 for x in units):raise ValueError('Explicit424B unit records required')
    velocity=state.velocity_xy
    if state.mode==0 and f.to_float(state.dt_bits)>0:
        dx=f.div(f.sub(state.player_xyz[0],state.previous_player_xyz[0]),state.dt_bits)
        dy=f.div(f.sub(state.player_xyz[1],state.previous_player_xyz[1]),state.dt_bits)
        if f.to_float(hypot_bits(dx,dy))<40:
            smoothing=f.sub(ONE,exp_bits(state.dt_bits^f.SIGN))
            velocity=(f.add(velocity[0],f.mul(smoothing,f.sub(dx,velocity[0]))),
                      f.add(velocity[1],f.mul(smoothing,f.sub(dy,velocity[1]))))
    budget,killed,minute,group=budget_rate(state,units)
    candidates=eligible_normals(state.zone,minute)
    words=state.rng_words;counter=state.counter;draws=0;requests=[]

    def attempt(index,origin):
        nonlocal words,counter,draws
        # Cap is checked before8751, so failed capacity attempts consume no
        # position or unit-angle randomness. Reuse known numeric spawn guard.
        raw=SpawnInput(state.zone,index,state.now_bits,state.zone_multiplier_bits,state.difficulty,state.mode,state.members,
            state.victory_field400,state.endless_flag,state.endless_start_bits,tuple(_word(u,0)for u in units),
            words,counter,(0,0,0),0,bytes(424).hex())
        probe=spawn_normal(raw)
        if not probe.success:return False,'cap'
        placed=sample_position(PositionInput(state.zone,state.player_xyz,velocity,f.from_float(26),f.from_float(36),
            f.from_float(.5),state.flat_height_bits,True,True,words))
        words=placed.rng_words;draws+=placed.draws
        if placed.status!='resolved_flat':return False,placed.status
        result=spawn_normal(replace(raw,rng_words=words,position_bits=placed.position_bits))
        words=result.rng_words;counter=result.counter;draws+=result.draws
        units.append(bytes.fromhex(result.record_hex));requests.append(dict(origin=origin,index=index,guid=result.guid,position_bits=list(placed.position_bits)))
        return True,'spawned'

    from .spawn135 import definition
    if f.to_float(budget)>=1:
        for _ in range(8):
            choice=choose_spawn(state.zone,candidates,minute,words);words=choice.rng_words;draws+=choice.draws
            cost=definition(state.zone,choice.index)['cost_bits']
            if f.to_float(cost)>f.to_float(budget):break
            ok,status=attempt(choice.index,'budget')
            if not ok:
                if status=='cap':budget=min_numeric(cost,budget);break
                return FrameResult(status,budget,killed,words,counter,tuple(u.hex()for u in units),velocity,tuple(requests),draws)
            budget=f.sub(budget,cost)
            if not f.to_float(budget)>=1:break
    alive=0
    pointers={row[1]:row[-1]for rows in NORMALS for row in rows}
    for raw in units:
        if _word(raw,0)==0 and _word(raw,284):
            ptr=_word(raw,284)
            if ptr not in pointers:raise ValueError('Unknown normal definition source')
            alive=(alive+(pointers[ptr]^1))&f.MASK
    target=trunc_sat_u32(f.mul(min_numeric(f.from_float(36),f.mul(f.add(f.mul(minute,f.from_float(1.6)),f.from_float(4)),_slowdown(units))),group))
    for _ in range(min(3,max(0,target-alive))):
        choice=choose_spawn(state.zone,candidates,minute,words);words=choice.rng_words;draws+=choice.draws
        ok,status=attempt(choice.index,'density')
        if not ok:
            if status=='cap':break
            return FrameResult(status,budget,killed,words,counter,tuple(u.hex()for u in units),velocity,tuple(requests),draws)
    return FrameResult('ordinary_projection',budget,killed,words,counter,tuple(u.hex()for u in units),velocity,tuple(requests),draws)
