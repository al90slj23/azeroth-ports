"""Independent914 death interpolation and1417 flat-world pickup placement.

The input is the live, pre-hit424B unit record, not the post-death zero-duration
record. Grid/terrain/navigation producers are rejected. Flat/base height is an
explicit world input; this module reads no original, assets or test artifacts.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .pickups134 import Placement
from .spawn_geometry135 import hypot_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .spawn135_data import NORMALS


def _finite(bits):
    if type(bits)is not int or not 0<=bits<=f.MASK or bits&0x7fffffff>=f.INF:
        raise ValueError('Finite binary32 word required')
    return bits


def _world_gate(terrain_grid_absent,navigation_absent):
    if terrain_grid_absent is not True or navigation_absent is not True:
        raise ValueError('Real terrain/grid/navigation pickup placement remains unresolved')


def clamp_pickup_position(zone,xyz_bits,flat_height_bits,*,terrain_grid_absent=False,navigation_absent=False):
    """1417's ordered circular clamp then final height query, for kinds0/1.

    XY is unchanged at distance<=max(1,zoneRadius-2). Otherwise each axis is
    centre+((axis-centre)/distance)*limit, with a binary32 rounding at every
    operation. Input Z is not the resulting pickup height.
    """
    _world_gate(terrain_grid_absent,navigation_absent)
    if type(zone)is not int or not 0<=zone<12 or len(xyz_bits)!=3:raise ValueError('Fixed map and XYZ required')
    x,y,z=tuple(_finite(b)for b in xyz_bits);height=_finite(flat_height_bits)
    cx,cy,radius=ZONE_GEOMETRY[zone];dx=f.sub(x,cx);dy=f.sub(y,cy);distance=hypot_bits(dx,dy)
    limit=f.add(radius,0xc0000000)
    limit=limit if f.to_float(limit)>1 else 0x3f800000
    if not f.to_float(distance)<=f.to_float(limit):
        x=f.add(cx,f.mul(f.div(dx,distance),limit));y=f.add(cy,f.mul(f.div(dy,distance),limit))
    return Placement(x,y,height)


@dataclass(frozen=True)
class OrdinaryPlacement135:
    death_xyz:tuple
    xp_placement:Placement
    currency_placement:Placement
    movement_message:bool


def project_from_record(zone,now_bits,pre_hit_record_hex,flat_height_bits,*,terrain_grid_absent=False,navigation_absent=False):
    """Produce both potential ordinary-death requests, before chance selection.

    This geometry consumes no RNG. The existing death arithmetic still owns
    reward chance and entity RNG, merging/caps, counters and actual append.
    """
    _world_gate(terrain_grid_absent,navigation_absent);now=_finite(now_bits)
    raw=bytes.fromhex(pre_hit_record_hex)
    if len(raw)!=424:raise ValueError('Full pre-hit424B record required')
    u=lambda o:struct.unpack_from('<I',raw,o)[0]
    if u(0)!=0 or any(u(o)!=f.MASK for o in(40,64,244)):
        raise ValueError('Live ordinary tags required; alternate death families unresolved')
    if not 0<=zone<12 or u(284)not in{d[1]for d in NORMALS[zone]if d[-1]==0}:
        raise ValueError('Unflagged ordinary definition from explicit fixed zone required')
    duration=_finite(u(344));start=_finite(u(340));orig=tuple(_finite(u(o))for o in(316,320,324));end=tuple(_finite(u(o))for o in(328,332,336))
    if f.to_float(duration)<=0:xyz=end
    else:
        ratio=f.div(f.sub(now,start),duration)
        ratio=0 if f.to_float(ratio)<0 else ratio
        ratio=0x3f800000 if f.to_float(ratio)>1 else ratio
        xyz=tuple(f.add(a,f.mul(f.sub(b,a),ratio))for a,b in zip(orig,end))
    xp=clamp_pickup_position(zone,xyz,flat_height_bits,terrain_grid_absent=True,navigation_absent=True)
    coin_xyz=(f.add(xyz[0],0x3f4ccccd),f.add(xyz[1],0x3f4ccccd),xyz[2])
    coin=clamp_pickup_position(zone,coin_xyz,flat_height_bits,terrain_grid_absent=True,navigation_absent=True)
    moving=f.to_float(duration)>0 and f.to_float(now)<f.to_float(f.add(start,duration))
    return OrdinaryPlacement135(xyz,xp,coin,moving)
