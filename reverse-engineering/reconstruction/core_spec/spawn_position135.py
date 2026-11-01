"""Independent8751 flat-terrain position/retry projection for actual spawns.

Grid/pathfinding and original fallback13516 are explicit unresolved branches.
The constant-height original29631 guard and absent obstacle grid are modeled;
no original game or host math trig is called.
"""
from dataclasses import dataclass
from . import binary32 as f
from .rng import uniform_range_bits,next_u32_words
from .spawn_geometry135 import sin_bits,cos_bits,hypot_bits
from .spawn_position135_data import ZONE_GEOMETRY


@dataclass(frozen=True)
class PositionInput:
    zone:int
    player_xyz:tuple
    velocity_xy:tuple
    low_radius_bits:int
    high_radius_bits:int
    bias_probability_bits:int
    flat_height_bits:int
    obstacle_grid_absent:bool
    pathfinding_absent:bool
    rng_words:tuple


@dataclass(frozen=True)
class PositionResult:
    status:str
    position_bits:tuple|None
    rng_words:tuple
    draws:int
    attempts:int
    radius_shrinks:int


def _axis_heading(x,y):
    if f.is_zero(y) and f.to_float(x)>0:return y&f.SIGN
    if f.is_zero(y) and f.to_float(x)<0:return 0x40490fdb|(y&f.SIGN)
    if f.is_zero(x) and f.to_float(y)>0:return 0x3fc90fdb
    if f.is_zero(x) and f.to_float(y)<0:return 0xbfc90fdb
    return None


def sample_position(state:PositionInput):
    if not state.obstacle_grid_absent or not state.pathfinding_absent:
        return PositionResult('pending_grid_pathfinding',None,state.rng_words,0,0,0)
    vx,vy=state.velocity_xy
    moving=f.to_float(f.add(f.mul(vx,vx),f.mul(vy,vy)))>4
    heading=_axis_heading(vx,vy) if moving else 0
    words=state.rng_words;draws=shrinks=0
    cx,cy,limit=ZONE_GEOMETRY[state.zone];px,py,pz=state.player_xyz
    for attempt in range(1,17):
        biased=False
        if moving:
            output,words=next_u32_words(words);draws+=1
            probability=f.mul(f.from_u32(output>>8),0x33800000)
            biased=f.to_float(probability)<f.to_float(state.bias_probability_bits)
        if biased:
            if heading is None:return PositionResult('pending_nonaxis_heading',None,words,draws,attempt,shrinks)
            angle=uniform_range_bits(words,0xbf99999a,0x3f99999a);words=angle.state;draws+=angle.draws
            theta=f.add(heading,angle.bits)
        else:
            angle=uniform_range_bits(words,0,0x40c90fdb);words=angle.state;draws+=angle.draws;theta=f.add(angle.bits,0)
        radius=uniform_range_bits(words,state.low_radius_bits,state.high_radius_bits);words=radius.state;draws+=radius.draws
        r=radius.bits;sine=sin_bits(theta);cosine=cos_bits(theta)
        while f.to_float(r)>=12:
            x=f.add(px,f.mul(cosine,r));y=f.add(py,f.mul(sine,r))
            distance=hypot_bits(f.sub(x,cx),f.sub(y,cy))
            if not f.to_float(distance)>f.to_float(f.add(limit,0x41900000)):
                threshold=0x41000000 if f.to_float(limit)<f.to_float(distance) else 0x41c80000
                if not f.to_float(f.sub(state.flat_height_bits,pz)&0x7fffffff)>f.to_float(threshold):
                    return PositionResult('resolved_flat', (x,y,state.flat_height_bits),words,draws,attempt,shrinks)
            r=f.add(r,0xc0000000);shrinks+=1
    return PositionResult('pending_fallback13516',None,words,draws,16,shrinks)
