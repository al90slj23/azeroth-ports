"""Independent fixed135 player-motion consumer2328, with explicit geometry.

The supplied Game bytes and world views are inputs, not independent producers.
No file, snapshot, WASM, headless or original callback is imported here. Phase0
returns the exact pre1089 boundary and a required continuation, never silently
claims that a real run has started. Physical queue allocation is not modelled.
"""
from dataclasses import dataclass
import math
import struct

from . import binary32 as f
from .spawn_geometry135 import hypot_bits, sin_bits, cos_bits
from .spawn_position135_data import ZONE_GEOMETRY
from .opening_entities135_data import ZONE_OPENING
from resource_spec.terrain135 import HeightSample135
from resource_spec.world_query135 import QueryBoundsTrap135


SOURCE_WASM_SHA256 = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
MOVEMENT_OPCODES135 = tuple(range(181,199))+tuple(range(200,204))+(218,219,238)
OUTSIDE_TEXT135 = b'|cffff4040You cannot leave the battlefield.|r'


class UnknownPlayerMotion135(NotImplementedError): pass


class MotionUnknownRead135(UnknownPlayerMotion135):
    def __init__(self,offset,size,unknown_offsets):
        self.offset,self.size,self.unknown_offsets=offset,size,tuple(unknown_offsets)
        super().__init__(f'2328 unknown Game read at+{offset} size{size}: {self.unknown_offsets}')


def _game_cells(value):
    if type(value) is bytes:
        if len(value)<2592:raise ValueError('Explicit Game backing>=2592 bytes')
        return bytearray(value),True
    if type(value) is not tuple or len(value)<2592 or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in value):
        raise ValueError('Game backing must be bytes or tuple[byte|None] >=2592')
    return list(value),False


def _read_cells(raw,offset,size):
    value=raw[offset:offset+size]
    unknown=[offset+j for j,x in enumerate(value)if x is None]
    if len(value)!=size:raise ValueError('Game read outside explicit backing')
    if unknown:raise MotionUnknownRead135(offset,size,unknown)
    return int.from_bytes(bytes(value),'little')


def _put_word(raw,offset,value):raw[offset:offset+4]=struct.pack('<I',_word(value))


def _word(value):
    if type(value) is not int or not 0 <= value <= f.MASK: raise ValueError('Explicit u32 word required')
    return value


def _finite(value):
    _word(value)
    if value & ~f.SIGN >= f.INF: raise ValueError('Finite movement float word required')
    return value


def _lt(a,b): return f.to_float(a) < f.to_float(b)
def _gt(a,b): return f.to_float(a) > f.to_float(b)
def _ge(a,b): return f.to_float(a) >= f.to_float(b)
def _eq(a,b): return f.to_float(a) == f.to_float(b)
def _c(value): return f.from_float(value)
def _distance(ax,ay,bx,by): return hypot_bits(f.sub(ax,bx),f.sub(ay,by))
def _d2(ax,ay,bx,by):
    x,y=f.sub(ax,bx),f.sub(ay,by)
    return f.add(f.mul(x,x),f.mul(y,y))
def _minimum_floor(value,floor):
    # Rust f32::max: NaN selects the finite argument, unlike a compare alone.
    return floor if f.is_nan(value) or _lt(value,floor) else value


@dataclass(frozen=True)
class MotionInput135:
    flags: int
    timestamp_ms: int
    xyz_bits: tuple
    facing_bits: int

    def __post_init__(self):
        _word(self.flags);_word(self.timestamp_ms)
        if len(self.xyz_bits)!=3: raise ValueError('XYZ12 input required')
        for x in (*self.xyz_bits,self.facing_bits): _finite(x)

    def payload24(self): return struct.pack('<6I',self.flags,self.timestamp_ms,*self.xyz_bits,self.facing_bits)


def decode_motion135(opcode,payload):
    """968 canonical complete24B domain; unknown opcodes/NaN/Inf are rejected.

    Original968 also has zero/default semantics for truncated payloads. That
    malformed domain is deliberately not inferred from this canonical decoder.
    """
    if type(opcode) is not int or opcode & 0xffff not in MOVEMENT_OPCODES135: return None
    if type(payload) is not bytes or len(payload)!=24: raise UnknownPlayerMotion135('Canonical exact24 payload domain only')
    flags,ms,x,y,z,o=struct.unpack('<6I',payload)
    if any(v & ~f.SIGN >= f.INF for v in (x,y,z,o)): return None
    return MotionInput135(flags,ms,(x,y,z),o)


@dataclass(frozen=True)
class MotionMap135:
    zone: int
    center_xy_bits: tuple
    radius_bits: int
    polygon_bits: tuple
    collision_policy148: int

    @classmethod
    def fixed_zone(cls,zone):
        if type(zone) is not int or not 0<=zone<len(ZONE_GEOMETRY): raise ValueError('Fixed135 zone')
        x,y,r=ZONE_GEOMETRY[zone]
        return cls(zone,(x,y),r,ZONE_OPENING[zone][5],ZONE_OPENING[zone][2])

    def outside(self,x,y):
        if self.zone not in (2,7): return _gt(_distance(x,y,*self.center_xy_bits),f.add(self.radius_bits,_c(10)))
        if not self.polygon_bits: raise UnknownPlayerMotion135('Original nonempty polygon required')
        inside=False;a=self.polygon_bits[-1]
        for b in self.polygon_bits:
            if _gt(b[1],y) != _gt(a[1],y):
                edge=f.add(b[0],f.div(f.mul(f.sub(y,b[1]),f.sub(a[0],b[0])),f.sub(a[1],b[1])))
                if _lt(x,edge): inside=not inside
            a=b
        return not inside

    def clamp_inward(self,x,y):
        cx,cy=self.center_xy_bits
        if self.zone not in (2,7):
            d=_minimum_floor(_distance(x,y,cx,cy),_c(.01));r=f.add(f.add(self.radius_bits,_c(10)),_c(-4))
            return f.add(cx,f.mul(f.div(f.sub(x,cx),d),r)),f.add(cy,f.mul(f.div(f.sub(y,cy),d),r))
        best=None
        vertices=self.polygon_bits
        for a,b in zip(vertices,vertices[1:]+vertices[:1]):
            dx,dy=f.sub(b[0],a[0]),f.sub(b[1],a[1])
            den=_minimum_floor(f.add(f.mul(dx,dx),f.mul(dy,dy)),_c(.000001))
            t=f.div(f.add(f.mul(dx,f.sub(x,a[0])),f.mul(dy,f.sub(y,a[1]))),den)
            if _lt(t,0):t=0
            if _gt(t,_c(1)):t=_c(1)
            px,py=f.add(a[0],f.mul(dx,t)),f.add(a[1],f.mul(dy,t))
            distance=_d2(px,py,x,y)
            if best is None or _lt(distance,best[0]):best=(distance,px,py)
        _,px,py=best
        dx,dy=f.sub(cx,px),f.sub(cy,py);den=_minimum_floor(hypot_bits(dx,dy),_c(.01))
        return f.add(px,f.mul(f.div(dx,den),_c(4))),f.add(py,f.mul(f.div(dy,den),_c(4)))


@dataclass(frozen=True)
class MotionWorld135:
    """Existing canonical height views plus Rc60 auxiliary collision raster.

    Auxiliary shares primary origin/width but has its own pointer/count. It is
    not the separate secondary raster at Rc92. Missing auxiliary when a live
    primary exists is an unresolved input, not synthesized zeros.
    """
    queries: object
    auxiliary_values_bits: tuple|None

    def auxiliary_min(self,x,y):
        p=self.queries.primary
        if p is None:return HeightSample135(False,f.NAN)
        if self.auxiliary_values_bits is None:raise UnknownPlayerMotion135('Explicit Rc60 auxiliary backing required')
        xx=math.floor(f.to_float(f.add(f.sub(x,p.origin_xy_bits[0]),f.sub(x,p.origin_xy_bits[0]))))
        yy=math.floor(f.to_float(f.add(f.sub(y,p.origin_xy_bits[1]),f.sub(y,p.origin_xy_bits[1]))))
        best=None
        for iy in range(max(0,yy-2),min(p.width-1,yy+2)+1):
            for ix in range(max(0,xx-2),min(p.width-1,xx+2)+1):
                index=ix+p.width*iy
                if index>=len(self.auxiliary_values_bits):raise QueryBoundsTrap135(index,len(self.auxiliary_values_bits),'aux33324')
                v=self.auxiliary_values_bits[index]
                if not f.is_nan(v) and (best is None or _lt(v,best)):best=v
        return HeightSample135(best is not None,0 if best is None else best)

    def max_height_radius12(self,x,y):
        best=None
        for ix in range(-12,13):
            for iy in range(-12,13):
                if _gt(hypot_bits(_c(ix),_c(iy)),_c(12)):continue
                h=self.queries.height(f.add(x,_c(ix)),f.add(y,_c(iy)))
                if h.found and (best is None or _gt(h.value_bits,best)):best=h.value_bits
        return HeightSample135(best is not None,0 if best is None else best)

    def nav_blocked_special(self,x,y):
        """All three42184 row predicates zero: left/mid==1,right!=0."""
        grid=self.queries.nav
        if grid is None:return False
        def byte(xx,yy):
            p=self.queries.nav_probe(xx,yy)
            return p.value if p.in_bounds else None
        for dy in (-1,0,1):
            yy=f.add(y,_c(dy))
            if byte(f.add(x,_c(-1)),yy)!=1 or byte(f.add(x,0),yy)!=1 or not byte(f.add(x,_c(1)),yy):return False
        return True

    def nearest_walkable(self,x,y,radius=20):
        """9234 strict nearest cell centre with all9 bytes exactly0."""
        grid=self.queries.nav
        if grid is None:return None
        best=None
        for oy in range(-radius,radius+1):
            for ox in range(-radius,radius+1):
                p=self.queries.nav_probe(f.add(x,_c(ox)),f.add(y,_c(oy)))
                if not p.in_bounds:continue
                ix,iy=p.index%grid.width,p.index//grid.width
                px=f.add(grid.origin_xy_bits[0],f.add(f.from_u32(ix),_c(.5)))
                py=f.add(grid.origin_xy_bits[1],f.add(f.from_u32(iy),_c(.5)))
                d=_d2(px,py,x,y)
                if _gt(d,_c(radius*radius)) or (best is not None and _ge(d,best[0])):continue
                clear=True
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        b=self.queries.nav_probe(f.add(px,_c(dx)),f.add(py,_c(dy)))
                        if not b.in_bounds or b.value!=0:clear=False;break
                    if not clear:break
                if clear:best=(d,px,py)
        return None if best is None else best[1:]

    def ring_fallback(self,map_,x,y):
        """2328 inline nonpolicy rescue: radii1..20, ordered ceil(r*2pi)."""
        for radius in range(1,21):
            r=_c(radius);n=math.ceil(f.to_float(f.mul(r,0x40c90fdb)))
            for index in range(n):
                angle=f.div(f.mul(f.from_u32(index),0x40c90fdb),f.from_u32(n))
                px=f.add(x,f.mul(r,cos_bits(angle)));py=f.add(y,f.mul(r,sin_bits(angle)))
                if map_.outside(px,py):continue
                h=self.queries.height(px,py)
                if not h.found:continue
                if all(self.queries.height(f.add(px,_c(dx)),f.add(py,_c(dy))).found for dx,dy in ((2,0),(-2,0),(0,2),(0,-2))):return px,py,h.value_bits
        return None


@dataclass(frozen=True)
class PlayerMotionResult135:
    game_bytes: bytes|tuple
    writes: tuple
    packets: tuple
    unchanged_input_xyz: bool
    branch: str
    begin_run_required: bool
    complete2328: bool


def apply_player_motion135(game_bytes,xyz_bits,facing_bits,world,map_):
    """Pure2328 state+semantic packets, exact f32 operation ordering.

    Existing queue capacity must suffice; pointers and heap storage are never
    fabricated. Count is advanced with complete semantic payloads returned.
    `writes` lists every actual scalar store, including
    idempotent stores. All other supplied Game bytes are preserved.
    """
    raw,physical_bytes=_game_cells(game_bytes)
    if len(xyz_bits)!=3:raise ValueError('InputXYZ')
    for v in (*xyz_bits,facing_bits):_finite(v)
    writes=[];packets=[]
    def u(o):return _read_cells(raw,o,4)
    def byte(o):return _read_cells(raw,o,1)
    def w(o,v):v=_word(v);_put_word(raw,o,v);writes.append((o,v))
    x,y,z=xyz_bits;now=u(2352)
    if u(416):
        if _gt(_d2(u(420),u(424),x,y),_c(9)) and _lt(f.sub(now,u(436)),_c(3)):
            return PlayerMotionResult135(game_bytes,(),(),False,'pending-correction-rejected',False,True)
        w(416,0)
    clock=u(444) if u(440)&1 else now
    q=world.queries;cx,cy=map_.center_xy_bits;center=q.height(cx,cy)
    if center.found:center_z=center.value_bits
    elif q.primary is None:center_z=q.fallback_height_bits
    else:
        near=q.nearest_primary(cx,cy);center_z=near.xyz_bits[2] if near.found else q.fallback_height_bits
    outside=map_.outside(x,y);policy=bool(map_.collision_policy148)
    near=q.nearest_primary(x,y) if policy else None
    aux=world.auxiliary_min(x,y) if policy else HeightSample135(False,f.NAN)
    if u(464):raise UnknownPlayerMotion135('Original debug464 format/log side effects remain separate')
    under=aux.found and _gt(f.add(aux.value_bits,_c(-.35)),z)
    def timer(condition,flag,at,delay):
        if not condition:w(flag,0);return False
        if u(flag)==1:start=u(at)
        else:w(at,clock);w(flag,1);start=clock
        return _ge(f.sub(clock,start),_c(delay))
    under_due=timer(under,448,452,.75)
    nav_due=timer(policy and world.nav_blocked_special(x,y),456,460,1)
    moving=policy and byte(2587)==1 and bool(u(2496)&15) and not bool(u(2496)&4096)
    stuck_due=False
    if not moving:w(1744,0)
    else:
        if u(1744)==1:start=u(1748)
        else:
            w(1748,clock);w(1744,1)
            for j,v in enumerate(xyz_bits):w(1752+4*j,v)
            start=clock
        stuck_due=_ge(f.sub(clock,start),_c(1.5))
        if _gt(_distance(x,y,u(1752),u(1756)),_c(.75)):
            w(1748,clock);w(1744,1)
            for j,v in enumerate(xyz_bits):w(1752+4*j,v)
            stuck_due=False
    height=q.height(x,y)
    forced=under_due or nav_due or stuck_due
    if policy:
        if height.found:too_low=_lt(z,f.add(height.value_bits,_c(-5)))
        elif near is not None and near.found:too_low=_lt(z,f.add(near.xyz_bits[2],_c(-5)))
        else:too_low=_lt(z,f.add(center_z,_c(-120)))
    elif height.found:too_low=_lt(z,f.add(height.value_bits,_c(-15)))
    else:
        sweep=world.max_height_radius12(x,y)
        too_low=_lt(z,f.add(sweep.value_bits,_c(-15))) if sweep.found else _lt(z,f.add(center_z,_c(-120)))
    corrected=forced or too_low or outside
    if corrected:
        w(1744,0);w(456,0);w(448,0)
        px,py=map_.clamp_inward(x,y) if outside else (x,y)
        if stuck_due or under_due:
            previous=u(1764)==1 and _lt(f.sub(clock,u(1768))&~f.SIGN,_c(6))
            close=previous and _lt(_distance(px,py,u(1772),u(1776)),_c(3))
            w(1768,clock);w(1764,1)
            for j,v in enumerate(xyz_bits):w(1772+j*4,v)
            if close:
                dx,dy=f.sub(cx,px),f.sub(cy,py);d=_minimum_floor(hypot_bits(dx,dy),_c(.01));step=d if _lt(d,_c(4)) else _c(4)
                py=f.add(py,f.mul(f.div(dy,d),step));px=f.add(px,f.mul(f.div(dx,d),step))
        if policy and q.nav is not None and world.nav_blocked_special(px,py):
            v=world.nearest_walkable(px,py)
            if v is not None:px,py=v
        sampled=q.height(px,py);ground=center_z
        if sampled.found:ground=sampled.value_bits
        else:
            nearest=q.nearest_primary(px,py)
            if nearest.found:px,py,ground=nearest.xyz_bits
            elif not policy:
                fallback=world.ring_fallback(map_,px,py)
                if fallback is not None:px,py,ground=fallback
        pz=f.add(ground,_c(.5));sequence=u(1644);w(1644,(sequence+1)&f.MASK)
        guid=_read_cells(raw,1336,8);guid_bytes=guid.to_bytes(8,'little');mask=sum(1<<j for j,v in enumerate(guid_bytes) if v)
        packed=bytes([mask])+bytes(v for v in guid_bytes if v)
        packets.append((199,(packed+struct.pack('<8I',sequence,0,0,px,py,pz,facing_bits,0)).hex()))
        if outside:packets.append((150,(struct.pack('<BIQI',10,0,0,len(OUTSIDE_TEXT135)+1)+OUTSIDE_TEXT135+b'\0\0').hex()))
        count=u(1888)
        if count+len(packets)>u(1880):raise UnknownPlayerMotion135('Original packet queue growth allocation is not synthesized')
        for j in range(len(packets)):w(1888,count+j+1)
        w(432,sequence);w(428,pz);w(424,py);w(420,px);w(416,1);w(436,now)
        last=now;branch='corrected'
    else:px,py,pz=x,y,z;last=now;branch='unchanged-input'
    w(2500,last);w(1428,facing_bits);w(1424,pz);oldx,oldy=u(1416),u(1420);w(1420,py);w(1416,px)
    begin=byte(2587)==0 and _gt(_d2(oldx,oldy,px,py),_c(.04)) and not u(2528) and not byte(2583)&1
    same=all(_eq(a,b) for a,b in zip((px,py,pz),xyz_bits))
    return PlayerMotionResult135(bytes(raw)if physical_bytes else tuple(raw),tuple(writes),tuple(packets),same,branch,begin,not begin)


def consume_motion_payload135(game_bytes,opcode,payload,world,map_):
    """968 local-player core segment only; excludes17726 dispatch/broadcast."""
    motion=decode_motion135(opcode,payload)
    if motion is None:return None
    raw,physical_bytes=_game_cells(game_bytes);_put_word(raw,2496,motion.flags);_put_word(raw,440,1)
    client_clock=f.div(f.from_u32(motion.timestamp_ms),_c(1000));_put_word(raw,444,client_clock)
    result=apply_player_motion135(bytes(raw)if physical_bytes else tuple(raw),motion.xyz_bits,motion.facing_bits,world,map_)
    raw,physical_bytes=_game_cells(result.game_bytes);_put_word(raw,440,0)
    before=((2496,motion.flags),(440,1),(444,client_clock))
    return PlayerMotionResult135(bytes(raw)if physical_bytes else tuple(raw),before+result.writes+((440,0),),result.packets,result.unchanged_input_xyz,
        result.branch,result.begin_run_required,result.complete2328)
