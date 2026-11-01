"""0.135 terrain height rules, from genuine ADT bytes and explicit world input.

The format parser covers canonical MCNK128/MCVT145 chunks. It does not load
M2/WMO collision, populate the original VFS, or claim a complete world producer.
All gameplay arithmetic below rounds after each binary32 operation.
"""
from dataclasses import dataclass
import math
import struct

from core_spec import binary32 as f
from .entry_resources135 import chunks,wdt_name,wdt_tile_mask,neighboring_adt_names

TILE = 0x44055555                 # 533.3333129882812
CHUNK = 0x42055555                # 33.33333206176758
STEP = 0x40855555                 # 4.166666507720947
HALF_STEP = 0x40055555
ZERO, ONE, TWO, EIGHT, SIXTEEN = 0,0x3f800000,0x40000000,0x41000000,0x41800000
NUDGE = 0x3d8f5c29
DEGENERATE = 0x3089705f            # Actual5795 1e-9
SNAP_WORLD = float.fromhex('0x1.0aaaaaaaaaaabp+14')
SNAP_STEP = float.fromhex('0x1.0aaaaaaaaaaabp+2')


class UnknownTerrain135(NotImplementedError): pass


def _finite(word):
    if type(word) is not int or not 0 <= word <= f.MASK or f.is_nan(word) or f.is_inf(word):
        raise UnknownTerrain135('Explicit finite binary32 coordinate/height domain required')
    return word


def _round84194(value):
    """Finite, |x|<2**52 branch of original f64 round-away helper."""
    if not math.isfinite(value) or abs(value)>=2**51: raise UnknownTerrain135('Grid snap magnitude outside restored domain')
    value += math.copysign(float.fromhex('0x1.fffffffffffffp-2'),value)
    n=math.trunc(value)
    return float(n) if n else math.copysign(0.0,value)


def _snap(word):
    return f.from_float(SNAP_WORLD-_round84194((SNAP_WORLD-f.to_float(word))/SNAP_STEP)*SNAP_STEP)


@dataclass(frozen=True)
class TerrainChunk135:
    vertices: tuple  # Exact145 XYZ binary32 triples, or explicit generic mesh.
    holes: int = 0
    indices: tuple = ()
    source_chunk_offset: int | None = None
    source_index_xy: tuple | None = None

    def __post_init__(self):
        if not 0<=self.holes<=65535: raise ValueError('Actual u16 terrain holes required')
        for v in self.vertices:
            if type(v) is not tuple or len(v)!=3: raise ValueError('Explicit XYZ triples required')
            for w in v:_finite(w)
        if any(type(i) is not int or not 0<=i<=f.MASK for i in self.indices):raise ValueError('Actual u32 mesh indices required')


@dataclass(frozen=True)
class HeightSample135:
    found: bool
    value_bits: int


def parse_adt_height(data):
    """Canonical successful1446 MCVT producer, retaining real MCNK order.

    Stronger exact-format guards deliberately reject malformed/short/alternate
    files rather than guessing the original error path or silently skipping.
    """
    result=[]
    for c in chunks(data):
        if c.tag!=b'KNCM':continue
        p=c.payload
        if len(p)<128:raise UnknownTerrain135('Short MCNK header')
        offset=struct.unpack_from('<I',p,20)[0]
        matches=[n for n in (offset,offset-8) if 0<=n<=len(p)-8 and p[n:n+4]==b'TVCM']
        if not matches:raise UnknownTerrain135('MCVT offset not restored')
        at=matches[0];size=struct.unpack_from('<I',p,at+4)[0]
        if size!=580 or at+8+size>len(p):raise UnknownTerrain135('Canonical145 MCVT words required')
        heights=struct.unpack_from('<145I',p,at+8)
        origin=struct.unpack_from('<3I',p,104)
        for w in (*origin,*heights):_finite(w)
        holes=struct.unpack_from('<H',p,60)[0];vertices=[]
        for row in range(9):
            rowstep=f.mul(f.from_u32(row),STEP)
            x=_snap(f.sub(origin[0],rowstep))
            for col in range(9):
                y=_snap(f.add(origin[1],f.mul(f.from_u32(col),STEP^f.SIGN)))
                vertices.append((x,y,f.add(origin[2],heights[len(vertices)])))
            if row<8:
                x=f.sub(origin[0],f.add(rowstep,HALF_STEP))
                for col in range(8):
                    y=f.sub(origin[1],f.add(f.mul(f.from_u32(col),STEP),HALF_STEP))
                    vertices.append((x,y,f.add(origin[2],heights[len(vertices)])))
        assert len(vertices)==145
        result.append(TerrainChunk135(tuple(vertices),holes,source_chunk_offset=c.offset,
            source_index_xy=struct.unpack_from('<2I',p,4)))
    if not result:raise UnknownTerrain135('No canonical terrain chunks')
    return tuple(result)


def _triangle(a,b,c,x,y):
    axcx=f.sub(a[0],c[0]);bycy=f.sub(b[1],c[1]);cxbx=f.sub(c[0],b[0]);aycy=f.sub(a[1],c[1])
    det=f.add(f.mul(axcx,bycy),f.mul(cxbx,aycy))
    if f.to_float(det&~f.SIGN)<f.to_float(DEGENERATE):return None
    pycy=f.sub(y,c[1]);pxcx=f.sub(x,c[0])
    alpha=f.div(f.add(f.mul(cxbx,pycy),f.mul(pxcx,bycy)),det)
    if f.to_float(alpha)<0:return None
    beta=f.div(f.add(f.mul(axcx,pycy),f.mul(pxcx,f.sub(c[1],a[1]))),det)
    if f.to_float(beta)<0:return None
    gamma=f.sub(f.sub(ONE,alpha),beta)
    if f.to_float(gamma)<0:return None
    return f.add(f.add(f.mul(alpha,a[2]),f.mul(beta,b[2])),f.mul(gamma,c[2]))


def sample_chunk(chunk,x_bits,y_bits):
    """Original5795: four ordered triangles for145, generic index list otherwise."""
    x_bits=_finite(x_bits);y_bits=_finite(y_bits);v=chunk.vertices
    if not v:return HeightSample135(False,0)
    fx=f.mul(f.div(f.sub(v[0][0],x_bits),TILE),SIXTEEN)
    fy=f.mul(f.div(f.sub(v[0][1],y_bits),TILE),SIXTEEN)
    if not 0<=f.to_float(fx)<=1 or not 0<=f.to_float(fy)<=1:return HeightSample135(False,0)
    if len(v)==145:
        row=min(7,int(f.to_float(f.mul(fx,EIGHT))));col=min(7,int(f.to_float(f.mul(fy,EIGHT))))
        if chunk.holes >> (((row<<1)&12)|(col>>1)) & 1:return HeightSample135(False,0)
        base=row*17+col;center=base+9
        triangles=((center,base,base+17),(center,base+17,base+18),
                   (center,base+18,base+1),(center,base+1,base))
    else:
        triangles=tuple(tuple(chunk.indices[j:j+3]) for j in range(0,len(chunk.indices)-2,3))
    for indices in triangles:
        if any(i>=len(v) for i in indices):continue
        value=_triangle(*(v[i] for i in indices),x_bits,y_bits)
        if value is not None:return HeightSample135(True,value)
    return HeightSample135(False,0)


def sample_tile(chunks_,x_bits,y_bits):
    """Original46295:256-chunk direct lookup has no second scan after a miss."""
    x_bits=_finite(x_bits);y_bits=_finite(y_bits)
    if len(chunks_)==256 and chunks_[0].vertices:
        fx=f.div(f.sub(chunks_[0].vertices[0][0],x_bits),CHUNK)
        fy=f.div(f.sub(chunks_[0].vertices[0][1],y_bits),CHUNK)
        if 0<=f.to_float(fx)<16 and 0<=f.to_float(fy)<16:
            return sample_chunk(chunks_[int(f.to_float(fx))*16+int(f.to_float(fy))],x_bits,y_bits)
    for chunk in chunks_:
        found=sample_chunk(chunk,x_bits,y_bits)
        if found.found:return found
    return HeightSample135(False,0)


@dataclass(frozen=True)
class TerrainTile135:
    chunks: tuple
    bounds_bits: tuple  # minX,minY,maxX,maxY from actual6730 or explicit input.


def tile_from_chunks(chunks_):
    """Finite6730 bbox producer: ordered XY min/max over every terrain vertex."""
    words=[v for chunk in chunks_ for v in chunk.vertices]
    if not words:raise UnknownTerrain135('Empty tile min/max sentinel domain not restored')
    values=(min(f.to_float(v[0])for v in words),min(f.to_float(v[1])for v in words),
            max(f.to_float(v[0])for v in words),max(f.to_float(v[1])for v in words))
    return TerrainTile135(tuple(chunks_),tuple(f.from_float(x)for x in values))


def load_terrain_tiles(map_id,center_xy_bits,provider):
    """Real local-file provider and restored6730 request order, without VFS state.

    Missing bytes/error paths remain explicit provider errors. This function
    does not synthesize a flat fallback, M2/WMO or either cached height raster.
    """
    mask=wdt_tile_mask(provider(wdt_name(map_id)))
    return tuple((name,tile_from_chunks(parse_adt_height(provider(name))))
                 for name in neighboring_adt_names(map_id,center_xy_bits,mask))


def sample_terrain(tiles,x_bits,y_bits):
    """Original18670 with explicit parallel-vector zip already resolved by caller."""
    x_bits=_finite(x_bits);y_bits=_finite(y_bits)
    if not tiles:return HeightSample135(False,x_bits)
    for delta in (0,NUDGE,NUDGE^f.SIGN):
        x=f.add(x_bits,delta);y=f.add(y_bits,delta)
        for tile in tiles:
            a,b,c,d=map(f.to_float,tile.bounds_bits)
            if a<=f.to_float(x)<=c and b<=f.to_float(y)<=d:
                sample=sample_tile(tile.chunks,x,y)
                if sample.found:return sample
    return HeightSample135(False,f.add(x_bits,NUDGE^f.SIGN))


@dataclass(frozen=True)
class HeightRaster135:
    values_bits: tuple
    origin_xy_bits: tuple
    width: int

    def __post_init__(self):
        if type(self.width) is not int or not 0<self.width<=4096 or len(self.values_bits)!=self.width**2:
            raise UnknownTerrain135('Explicit square half-unit raster required')
        for w in self.origin_xy_bits:_finite(w)
        if len(self.origin_xy_bits)!=2 or any(type(w) is not int or not 0<=w<=f.MASK for w in self.values_bits):
            raise ValueError('Raw binary32 raster words required')


def _raster(raster,x,y):
    dx=f.sub(x,raster.origin_xy_bits[0]);dx=f.add(dx,dx)
    dy=f.sub(y,raster.origin_xy_bits[1]);dy=f.add(dy,dy)
    if not 0<=f.to_float(dx)<raster.width or not 0<=f.to_float(dy)<raster.width:return None
    return raster.values_bits[int(f.to_float(dx))+raster.width*int(f.to_float(dy))]


def sample_world(tiles,x_bits,y_bits,*,flat_height_bits=None,primary=None,secondary=None):
    """29631 consumer, explicit cache data only; no inferred cache producer.

    A primary NaN is a failed sample, without a terrain fallback. Secondary
    values only raise a successful terrain result. Physical invalid-payload
    words remain deterministic where29631 explicitly writes them.
    """
    x_bits=_finite(x_bits);y_bits=_finite(y_bits)
    if flat_height_bits is not None:
        return HeightSample135(True,_finite(flat_height_bits))
    if primary is not None:
        #29631 reuses local4 for each half-grid displacement. An early miss
        #still stores that raw local into result+4; it is not universally0.
        dx=f.sub(x_bits,primary.origin_xy_bits[0]);xx=f.add(dx,dx)
        if f.to_float(xx)<0:return HeightSample135(False,dx)
        dy=f.sub(y_bits,primary.origin_xy_bits[1]);yy=f.add(dy,dy)
        if f.to_float(yy)<0 or f.to_float(xx)>=primary.width or f.to_float(yy)>=primary.width:
            return HeightSample135(False,dy)
        value=primary.values_bits[int(f.to_float(xx))+primary.width*int(f.to_float(yy))]
        return HeightSample135(not f.is_nan(value),value)
    result=sample_terrain(tiles,x_bits,y_bits)
    if not result.found:return HeightSample135(False,0)
    if secondary is not None:
        extra=_raster(secondary,x_bits,y_bits)
        if extra is not None and not f.is_nan(extra) and f.to_float(extra)>f.to_float(result.value_bits):
            result=HeightSample135(True,extra)
    return result


PENDING=('Base asset files are not a proof of latest135 complete asset equality.',
         'Canonical145 producer is not the whole1446 output, M2/WMO, raster or navigation construction.',
         'World29631 primary/secondary cached-raster producer and full116B payload remain separate work.',
         'No original VFS, Once, SELF, world cache or resource handle is forged.')
