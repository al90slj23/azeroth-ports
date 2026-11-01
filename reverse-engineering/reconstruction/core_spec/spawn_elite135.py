"""947 due elite-clock projection with real ordinary and optional paired elites.

All other event/Boss clocks must remain future. UI text/object registries are not
part of this record-and-clock projection. Fixed data and pure models only.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .spawn135 import SpawnInput,spawn_normal,max_numeric
from .spawn135_data import NORMALS
from .spawn_boss135 import bounded_index
from .spawn_frame_motion135 import step_ordinary_frame
from .spawn_position135 import PositionInput
from .spawn_position_motion135 import sample_position


@dataclass(frozen=True)
class EliteResult:
    ordinary:object
    next_elite_bits:int
    rng_words:tuple
    counter:int
    unit_records:tuple
    requests:tuple
    draws:int
    candidates:tuple


def step_elite_frame(frame,next_elite_bits):
    ordinary=step_ordinary_frame(frame)
    if ordinary.status!='ordinary_projection':raise ValueError('Ordinary projection unresolved')
    words=ordinary.rng_words;counter=ordinary.counter;units=list(ordinary.unit_records);draws=ordinary.draws;requests=[];candidates=()
    def attempt(index,position=None):
        nonlocal words,counter,draws
        states=tuple(int.from_bytes(bytes.fromhex(u)[:4],'little')for u in units)
        raw=SpawnInput(frame.zone,index,frame.now_bits,frame.zone_multiplier_bits,frame.difficulty,frame.mode,frame.members,
            frame.victory_field400,frame.endless_flag,frame.endless_start_bits,states,words,counter,(0,0,0),0,bytes(424).hex())
        if not spawn_normal(raw).success:return None
        if position is None:
            placed=sample_position(PositionInput(frame.zone,frame.player_xyz,ordinary.velocity_xy,0x41d00000,0x42100000,0x3f000000,
                frame.flat_height_bits,True,True,words));words=placed.rng_words;draws+=placed.draws
            if placed.status!='resolved_flat':raise ValueError('Elite placement unresolved: '+placed.status)
            position=placed.position_bits
        result=spawn_normal(replace(raw,rng_words=words,position_bits=position));words=result.rng_words;counter=result.counter;draws+=result.draws
        units.append(result.record_hex);requests.append(dict(index=index,position_bits=position,guid=result.guid));return position
    if f.to_float(frame.now_bits)>=f.to_float(next_elite_bits):
        minute=f.div(frame.now_bits,0x42700000)
        candidates=tuple(i for i,row in enumerate(NORMALS[frame.zone])if row[-1]==1 and f.to_float(row[-2])<=f.to_float(minute))
        drawn,words,used=bounded_index(words,max(1,len(candidates)));draws+=used
        if candidates:
            index=candidates[min(drawn,len(candidates)-1)];position=attempt(index)
            if position is not None and frame.difficulty!=0:
                attempt(index,(f.add(position[0],0x40200000),f.add(position[1],0x3f800000),position[2]))
        interval=max_numeric(f.add(f.mul(minute,0xc0200000),0x425c0000),0x41c80000)
        next_elite_bits=f.add(frame.now_bits,interval)
    return EliteResult(ordinary,next_elite_bits,words,counter,tuple(units),tuple(requests),draws,candidates)
