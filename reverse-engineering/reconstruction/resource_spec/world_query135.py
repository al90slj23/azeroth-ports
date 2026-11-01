"""Pure 0.135 world query consumers over explicitly resolved world payloads.

Snapshot decoding is an input adapter, never an independent world producer.
Terrain/raster height arithmetic is reused from the validated terrain module.
The byte navigation grid is kept raw because callers use different predicates.
"""
from dataclasses import dataclass
import math
import struct
from core_spec import binary32 as f
from .terrain135 import (HeightRaster135,HeightSample135,TerrainChunk135,
                         TerrainTile135,sample_world,UnknownTerrain135)


class UnknownWorldQuery135(NotImplementedError):pass


class QueryBoundsTrap135(ValueError):
    def __init__(self,index,length,consumer):
        super().__init__(f'{consumer} original bounds trap: index{index},length{length}')
        self.index,self.length,self.consumer=index,length,consumer


def _word(x):
    if type(x) is not int or not 0<=x<=0xffffffff:raise ValueError('Exact u32 word required')
    return x


def _finite(x):
    _word(x)
    if f.is_nan(x)or f.is_inf(x):raise UnknownWorldQuery135('Finite query coordinate domain required')
    return x


def _trunc_sat_u(bits):
    value=f.to_float(bits)
    if math.isnan(value)or value<=0:return 0
    if value>=4294967295:return 4294967295
    return math.trunc(value)


@dataclass(frozen=True)
class NavGrid135:
    values: bytes
    origin_xy_bits: tuple
    width: int

    def __post_init__(self):
        if type(self.values)is not bytes or len(self.values)>16777216:raise ValueError('Explicit byte-grid backing required')
        if type(self.width)is not int or not 0<=self.width<=4096:raise ValueError('Navigation grid width budget')
        if len(self.origin_xy_bits)!=2:raise ValueError('Navigation origin XY')
        for x in self.origin_xy_bits:_finite(x)


@dataclass(frozen=True)
class NavProbe135:
    present: bool
    in_bounds: bool
    value: int|None
    index: int|None


def probe_nav(grid,x_bits,y_bits):
    """Inline8751/13516 byte lookup, before caller-specific blocked decisions.

    A missing/outside grid is not called blocked here. Bounds panic is distinct
    from a normal outside point. Raw bytes other than0/1 remain meaningful.
    """
    _word(x_bits);_word(y_bits)
    if grid is None:return NavProbe135(False,False,None,None)
    dx=f.sub(x_bits,grid.origin_xy_bits[0]);dy=f.sub(y_bits,grid.origin_xy_bits[1])
    if f.to_float(dx)<0 or f.to_float(dy)<0:return NavProbe135(True,False,None,None)
    x,y=_trunc_sat_u(dx),_trunc_sat_u(dy)
    if x>=grid.width or y>=grid.width:return NavProbe135(True,False,None,None)
    index=x+grid.width*y
    if index>=len(grid.values):raise QueryBoundsTrap135(index,len(grid.values),'nav-inline')
    return NavProbe135(True,True,grid.values[index],index)


@dataclass(frozen=True)
class SearchRaster135:
    """23181 view permits short count so original bounds traps remain explicit."""
    values_bits: tuple
    origin_xy_bits: tuple
    width: int

    def __post_init__(self):
        if type(self.width)is not int or not 0<=self.width<=4096:raise ValueError('Search raster width budget')
        if len(self.values_bits)>16777216 or len(self.origin_xy_bits)!=2:raise ValueError('Explicit raster input')
        for x in self.values_bits:_word(x)
        for x in self.origin_xy_bits:_finite(x)


@dataclass(frozen=True)
class NearestSample135:
    found: bool
    xyz_bits: tuple|None


def nearest_raster(raster,x_bits,y_bits):
    """Original23181, first nonempty Chebyshev ring0..20, then strict d².

    This is a cached raster lookup, not a geometric mesh raycast. Equal scores
    keep the first candidate in ascending Y-offset then ascending X-offset.
    """
    _finite(x_bits);_finite(y_bits)
    if raster is None:return NearestSample135(False,None)
    dx=f.sub(x_bits,raster.origin_xy_bits[0]);dy=f.sub(y_bits,raster.origin_xy_bits[1])
    xx=f.to_float(f.add(dx,dx));yy=f.to_float(f.add(dy,dy))
    if not math.isfinite(xx)or not math.isfinite(yy)or abs(xx)>=2**30 or abs(yy)>=2**30:
        raise UnknownWorldQuery135('23181 signed-index overflow domain unresolved')
    cx,cy=math.floor(xx),math.floor(yy)
    for radius in range(21):
        best=None
        for oy in range(-radius,radius+1):
            y=cy+oy
            if y<0 or y>=raster.width:continue
            for ox in range(-radius,radius+1):
                if max(abs(ox),abs(oy))!=radius:continue
                x=cx+ox
                if x<0 or x>=raster.width:continue
                index=x+raster.width*y
                if index>=len(raster.values_bits):raise QueryBoundsTrap135(index,len(raster.values_bits),'nearest23181')
                height=raster.values_bits[index]
                if f.is_nan(height):continue
                score=ox*ox+oy*oy
                if best is not None and score>=best[0]:continue
                px=f.add(raster.origin_xy_bits[0],f.mul(f.add(f.from_u32(x),0x3f000000),0x3f000000))
                py=f.add(raster.origin_xy_bits[1],f.mul(f.add(f.from_u32(y),0x3f000000),0x3f000000))
                best=(score,(px,py,height))
        if best is not None:return NearestSample135(True,best[1])
    return NearestSample135(False,None)


@dataclass(frozen=True)
class WorldQueries135:
    tiles: tuple
    primary: HeightRaster135|None
    secondary: HeightRaster135|None
    nav: NavGrid135|None
    fallback_height_bits: int
    flat_height_bits: int|None=None
    source_ranges: tuple=()

    def height(self,x_bits,y_bits):
        return sample_world(self.tiles,x_bits,y_bits,flat_height_bits=self.flat_height_bits,
                            primary=self.primary,secondary=self.secondary)

    def nav_probe(self,x_bits,y_bits):return probe_nav(self.nav,x_bits,y_bits)

    def nearest_primary(self,x_bits,y_bits):return nearest_raster(self.primary,x_bits,y_bits)


def decode_world_snapshot(memory_bytes,rc_pointer):
    """Decode only fields consumed by validated height/nav queries.

    Geometry/model production, ownership, other vector payloads and lifetimes
    remain unresolved. The full caller-provided snapshot remains authoritative.
    """
    if not isinstance(memory_bytes,(bytes,bytearray,memoryview)):raise ValueError('Explicit immutable memory bytes required')
    memory=memoryview(memory_bytes);ranges=[]
    def take(p,n,label):
        if type(p)is not int or type(n)is not int or p<0 or n<0 or p+n>len(memory):raise ValueError('Snapshot range outside memory')
        ranges.append((label,p,n));return memory[p:p+n]
    def u(p):return struct.unpack('<I',take(p,4,'word'))[0]
    def vec(cap,ptr,count,stride,label,budget):
        if count>cap or count>budget:raise UnknownWorldQuery135(label+' vector budget/shape')
        return take(ptr,count*stride,label)
    raw=take(rc_pointer,124,'worldRc124');words=struct.unpack('<31I',raw)
    tiles_raw=vec(words[2],words[3],words[4],36,'tiles36',512)
    bounds=vec(words[5],words[6],words[7],16,'tileBounds16',512)
    tiles=[]
    for j in range(min(words[4],words[7])):
        tile_words=struct.unpack_from('<9I',tiles_raw,j*36)
        chunks_raw=vec(tile_words[0],tile_words[1],tile_words[2],264,f'tile{j}.chunks264',1024)
        chunks=[]
        for k in range(tile_words[2]):
            q=chunks_raw[k*264:(k+1)*264];cap,ptr,count=struct.unpack_from('<3I',q)
            if count!=145:raise UnknownWorldQuery135('Snapshot adapter currently requires canonical145 terrain chunks')
            vertex_raw=vec(cap,ptr,count,12,f'tile{j}.chunk{k}.vertices',145)
            vertices=tuple(struct.iter_unpack('<3I',vertex_raw))
            holes=struct.unpack_from('<H',q,260)[0]
            chunks.append(TerrainChunk135(vertices,holes))
        tiles.append(TerrainTile135(tuple(chunks),struct.unpack_from('<4I',bounds,j*16)))
    def raster(tag_index,ptr_index,length_index,origin_index,width_index,label):
        if words[tag_index]==0xffffffff:return None
        count=words[length_index];width=words[width_index]
        if not 0<width<=4096 or count!=width*width:raise UnknownWorldQuery135(label+' square raster domain')
        values=tuple(struct.unpack('<'+'I'*count,take(words[ptr_index],count*4,label)))
        return HeightRaster135(values,(words[origin_index],words[origin_index+1]),width)
    primary=raster(14,18,19,20,22,'primaryRaster')
    secondary=raster(23,24,25,26,28,'secondaryRaster')
    nav=None
    if words[8]!=0xffffffff:
        count=words[10]
        values=bytes(vec(words[8],words[9],count,1,'navBytes',16777216))
        nav=NavGrid135(values,(words[11],words[12]),words[13])
    fallback=_finite(words[29]);flat=fallback if raw[120] else None
    return WorldQueries135(tuple(tiles),primary,secondary,nav,fallback,flat,tuple(ranges))
