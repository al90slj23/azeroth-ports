"""947 ordinary phase followed by due scheduled/endless Boss production.

Other elite and timed-event deadlines must be explicitly not due. This executable
projection preserves shared RNG and full unit records and creates actual Bosses.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .spawn_frame_motion135 import step_ordinary_frame
from .spawn_boss135 import BossInput,spawn_boss,bounded_index
from .spawn_boss135_data import BOSSES


@dataclass(frozen=True)
class BossScheduleResult:
    status:str
    ordinary:object
    next_boss_index:int
    next_endless_bits:int
    rng_words:tuple
    counter:int
    unit_records:tuple
    boss_timers:tuple
    requests:tuple
    draws:int


def step_boss_frame(frame,next_boss_index,next_endless_bits):
    ordinary=step_ordinary_frame(frame)
    if ordinary.status!='ordinary_projection':raise ValueError('Ordinary phase unresolved')
    words=ordinary.rng_words;counter=ordinary.counter;units=list(ordinary.unit_records);requests=[];timers=[];draws=ordinary.draws
    def produce(index,scalar,origin):
        nonlocal words,counter,draws
        result=spawn_boss(BossInput(frame.zone,index,frame.now_bits,frame.zone_multiplier_bits,frame.difficulty,frame.mode,
            frame.members,frame.victory_field400,frame.endless_flag,frame.endless_start_bits,words,counter,
            frame.player_xyz,ordinary.velocity_xy,frame.flat_height_bits,scalar,0,bytes(424).hex()))
        if result.status!='boss_projection':raise ValueError('Boss placement unresolved: '+result.status)
        words=result.rng_words;counter=result.counter;draws+=result.draws;units.append(result.record_hex);timers.append(result.timers_bits)
        requests.append(dict(origin=origin,index=index,guid=result.guid,position_route=result.position_route))
    if next_boss_index>=5:
        if frame.endless_flag!=0 and f.to_float(frame.now_bits)>=f.to_float(next_endless_bits):
            index,words,used=bounded_index(words,5);draws+=used;produce(index,0x3f800000,'endless')
            next_endless_bits=f.add(frame.now_bits,0x43960000)
    elif f.to_float(f.div(frame.now_bits,0x42700000))>=f.to_float(BOSSES[frame.zone][next_boss_index][5]):
        index=next_boss_index;next_boss_index+=1;produce(index,0x3f800000,'schedule')
        if frame.difficulty>=5 and BOSSES[frame.zone][index][9]==1:
            index,words,used=bounded_index(words,4);draws+=used;produce(index,0x3f19999a,'difficulty5-final-extra')
    return BossScheduleResult('boss_frame_projection',ordinary,next_boss_index,next_endless_bits,words,counter,tuple(units),tuple(timers),tuple(requests),draws)
