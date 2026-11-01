"""Full finite-heading extension of the separately frozen8751 flat sampler.

Only heading resolution differs from spawn_position135: exact34787/42475 is
used for every velocity quadrant. Grid/pathfinding/fallback remain explicit.
"""
from . import binary32 as f
from .rng import uniform_range_bits,next_u32_words
from .spawn_geometry135 import sin_bits,cos_bits,hypot_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .spawn_position135 import PositionInput,PositionResult
from .spawn_heading135 import atan2_bits


def sample_position(state:PositionInput):
    if not state.obstacle_grid_absent or not state.pathfinding_absent:
        return PositionResult('pending_grid_pathfinding',None,state.rng_words,0,0,0)
    vx,vy=state.velocity_xy
    moving=f.to_float(f.add(f.mul(vx,vx),f.mul(vy,vy)))>4
    heading=atan2_bits(vy,vx) if moving else 0
    words=state.rng_words;draws=shrinks=0
    cx,cy,limit=ZONE_GEOMETRY[state.zone];px,py,pz=state.player_xyz
    for attempt in range(1,17):
        biased=False
        if moving:
            output,words=next_u32_words(words);draws+=1
            probability=f.mul(f.from_u32(output>>8),0x33800000)
            biased=f.to_float(probability)<f.to_float(state.bias_probability_bits)
        if biased:
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
