"""Ordinary947 frame extension using exact arbitrary motion heading.

The already recovered budget, density and record arithmetic are reused. Other
elite/event/Boss schedules still require separately reconstructed inputs.
"""
from dataclasses import replace
import math
from . import binary32 as f
from .spawn135 import SpawnInput,spawn_normal,choose_spawn,eligible_normals,max_numeric,min_numeric
from .spawn_math135 import exp_bits
from .spawn_geometry135 import hypot_bits
from .spawn_position135 import PositionInput
from .spawn_position_motion135 import sample_position
from .spawn_schedule135 import FrameInput,FrameResult,budget_rate,_word,_slowdown
from .spawn135_data import NORMALS
from .progression134 import trunc_sat_u32
ONE=0x3f800000


def step_ordinary_frame(state:FrameInput, *, destination_slots=None):
    if not state.other_event_timers_future:raise ValueError('Other event schedules are unresolved')
    if not math.isfinite(f.to_float(state.now_bits))or not math.isfinite(f.to_float(state.dt_bits)):
        raise ValueError('Controlled ordinary-frame domain has finite simulation time')
    units=[bytes.fromhex(x)for x in state.unit_records]
    if any(len(x)!=424 for x in units):raise ValueError('Explicit424B unit records required')
    if destination_slots is not None:
        if type(destination_slots)is not tuple or len(destination_slots)<len(units):
            raise ValueError('Explicit allocated destination-slot snapshots required')
        if any(len(bytes.fromhex(raw))!=424 for raw in destination_slots):
            raise ValueError('Each allocated destination slot must be424B')
        if destination_slots[:len(units)]!=state.unit_records:
            raise ValueError('Live vector and allocated backing snapshots disagree')
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
        slot=(destination_slots[len(units)]if destination_slots is not None and len(units)<len(destination_slots)
              else bytes(424).hex())
        raw=SpawnInput(state.zone,index,state.now_bits,state.zone_multiplier_bits,state.difficulty,state.mode,state.members,
            state.victory_field400,state.endless_flag,state.endless_start_bits,tuple(_word(u,0)for u in units),
            words,counter,(0,0,0),0,slot)
        probe=spawn_normal(raw)
        if not probe.success:return False,'cap'
        if destination_slots is not None and len(units)>=len(destination_slots):
            raise ValueError('Allocator growth needs explicit new destination storage')
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
