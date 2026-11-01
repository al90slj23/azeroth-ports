"""Independent fixed135 terrain/placement bytes -> final navigation/height cache.

Production never reads snapshots or original programs. Existing independent
terrain, M2/WMO geometry and raster primitives are composed without changing
their frozen sources. Only the successful nonflat/no-primary world path is
admitted; physical Rc/cache ownership and other map paths remain separate.
"""
from collections import Counter,deque
from dataclasses import dataclass
import math

from core_spec import binary32 as f
from .terrain135 import sample_terrain,HeightRaster135
from .world_query135 import NavGrid135,WorldQueries135
from .world_raster135 import (CollisionMesh135,CandidateRaster135,
    parse_classic_m2_collision,transform_mesh,height_candidates,mark_navigation)
from .wmo_geometry135 import (WmoRoot135,parse_wmo_collision,
    append_group_collision,root_group_paths)

NAN=0x7fc00000
HALF=0x3f000000
ELWYNN_FALLBACK_BITS=0x42880000 # Original zone152 at5456016+112, not snapshot.


class UnknownWorldCache135(NotImplementedError):pass


class CacheBoundsTrap135(ValueError):pass


def _word(value):
    if type(value)is not int or not 0<=value<=0xffffffff:raise ValueError('Explicit u32 word required')
    return value


def _finite(value):
    _word(value)
    if not math.isfinite(f.to_float(value)):raise UnknownWorldCache135('Finite cache grid domain required')
    return value


@dataclass(frozen=True)
class CacheGrid135:
    center_xy_bits:tuple
    origin_xy_bits:tuple
    nav_width:int
    secondary_width:int

    def __post_init__(self):
        if len(self.center_xy_bits)!=2 or len(self.origin_xy_bits)!=2:raise ValueError('Explicit XY required')
        for x in(*self.center_xy_bits,*self.origin_xy_bits):_finite(x)
        if not 1<=self.nav_width<=512 or not 1<=self.secondary_width<=1024:
            raise UnknownWorldCache135('Independent cache grid budget')


def cache_grid135(center_xy_bits,radius_bits):
    """6730:zone.radius+20, diameter, ceil widths; preserve each f32 operation."""
    center=tuple(center_xy_bits);_finite(radius_bits)
    extent=f.add(radius_bits,0x41a00000)
    if not f.to_float(extent)>0:raise UnknownWorldCache135('Positive world extent required')
    diameter=f.add(extent,extent)
    nav_width=math.ceil(f.to_float(diameter))
    secondary_width=math.ceil(f.to_float(f.add(diameter,diameter)))
    return CacheGrid135(center,tuple(f.sub(x,extent)for x in center),nav_width,secondary_width)


def ground_grid135(tiles,grid,*,progress=None):
    """6730's no-primary path:18670 at each1m cell centre, canonical NaN miss."""
    ox,oy=grid.origin_xy_bits;result=[];width=grid.nav_width
    for y in range(width):
        py=f.add(oy,f.add(f.from_u32(y),HALF))
        for x in range(width):
            px=f.add(ox,f.add(f.from_u32(x),HALF));sample=sample_terrain(tiles,px,py)
            result.append(sample.value_bits if sample.found else NAN)
        if progress and(y%8==0 or y==width-1):progress(dict(phase='ground',rows=y+1,total_rows=width))
    return tuple(result)


def seal_unreachable_nav135(storage,grid):
    """6730 final four-neighbour connectivity, seeded by free perimeter/centre.

    Every nonzero raw byte blocks. The final operation is old|(visited^1),
    not boolean normalization. Disconnected rooms are sealed; free components
    connected to any edge, or the free centre cell, remain traversable.
    """
    width=grid.nav_width
    if type(storage)is not bytes or len(storage)!=width*width:raise ValueError('Exact nav backing required')
    visited=bytearray(len(storage));pending=deque()
    def seed(index):
        if not storage[index]and not visited[index]:visited[index]=1;pending.append(index)
    dx=f.to_float(f.sub(grid.center_xy_bits[0],grid.origin_xy_bits[0]));dy=f.to_float(f.sub(grid.center_xy_bits[1],grid.origin_xy_bits[1]))
    if 0<=dx<width and 0<=dy<width:seed(int(dy)*width+int(dx))
    for i in range(width):
        seed(i);seed((width-1)*width+i);seed(i*width);seed(i*width+width-1)
    while pending:
        index=pending.popleft();x,y=index%width,index//width
        if x:seed(index-1)
        if x+1<width:seed(index+1)
        if y:seed(index-width)
        if y+1<width:seed(index+width)
    return bytes(value|(flag^1)for value,flag in zip(storage,visited))


def merge_secondary135(tiles,grid,candidates,*,stats=None):
    """6730 candidate order -> NaN grid; terrain+.1<z<=terrain+3, keep max.

    Terrain is sampled at the half-unit cell centre, not the nav ground point.
    A candidate index is bounds-checked only after the original terrain/filter
    guards. An all-rejected result is absent, not a present all-NaN raster.
    """
    width=grid.secondary_width;values=[NAN]*(width*width);cache={};counts=Counter();updated=False
    for index,z in candidates:
        _word(index);_word(z);counts['candidate_pairs']+=1
        if index not in cache:
            x,y=index%width,index//width
            px=f.add(grid.origin_xy_bits[0],f.mul(f.add(f.from_u32(x),HALF),HALF))
            py=f.add(grid.origin_xy_bits[1],f.mul(f.add(f.from_u32(y),HALF),HALF))
            cache[index]=sample_terrain(tiles,px,py);counts['secondary_terrain_queries']+=1
        terrain=cache[index]
        if not terrain.found:counts['candidate_terrain_miss']+=1;continue
        if not f.to_float(z)>f.to_float(f.add(terrain.value_bits,0x3dcccccd)):
            counts['candidate_not_above_point1']+=1;continue
        if not f.to_float(z)<=f.to_float(f.add(terrain.value_bits,0x40400000)):
            counts['candidate_above_3']+=1;continue
        if index>=len(values):raise CacheBoundsTrap135('Original6730 accepted candidate index exceeds grid')
        counts['eligible_candidate_pairs']+=1
        previous=values[index]
        if not f.is_nan(previous)and not f.to_float(previous)<f.to_float(z):continue
        values[index]=z;updated=True;counts['secondary_updates']+=1
    counts['secondary_finite_cells']=sum(not f.is_nan(x)for x in values)
    if stats is not None:stats.update(counts)
    return HeightRaster135(tuple(values),grid.origin_xy_bits,width)if updated else None


@dataclass(frozen=True)
class WorldCacheBuild135:
    world:WorldQueries135
    ground_bits:tuple
    nav_before_connectivity:bytes
    grid:CacheGrid135
    stats:dict


class _GeometryProvider135:
    """Exact chain names only. Missing bytes/errors propagate, never fallback."""
    def __init__(self,provider):self.provider=provider;self.meshes={};self.reads=[]

    def __call__(self,instance):
        chain=instance.chain
        if type(chain)is not bytes:raise TypeError('Placement chain must be exact canonical bytes')
        key=(instance.kind,chain)
        if key in self.meshes:return self.meshes[key]
        data=self.provider(chain);self.reads.append(chain)
        if instance.kind=='m2':meshes=(parse_classic_m2_collision(data),)
        elif instance.kind=='wmo':
            root=parse_wmo_collision(data)
            if not isinstance(root,WmoRoot135):raise UnknownWorldCache135('Actual WMO root path required')
            groups=[]
            for name in root_group_paths(chain.decode('utf8'),root):
                raw_name=name.encode('utf8');group=parse_wmo_collision(self.provider(raw_name));self.reads.append(raw_name)
                mesh=append_group_collision(group)
                # Actual387groups fit the frozen single-mesh domain. Preserve
                # every group's vertices/triangle order; never sort by chain.
                groups.append(CollisionMesh135(mesh.vertices,mesh.indices))
            meshes=tuple(groups)
        else:raise ValueError('Explicit m2/wmo placement required')
        self.meshes[key]=meshes;return meshes


def produce_world_cache135(terrain_tiles,center_xy_bits,radius_bits,fallback_height_bits,
                          nav_m2,nav_wmo,secondary_wmo,provider,*,progress=None):
    """Assetbundle-derived nonflat/no-primary world cache, no snapshot input.

    Placement selections are the three ordered6730 phases, provided by the
    independent placement module. provider(byteschain)->real bytes. Large WMO
    roots are processed by their unchanged ordered groups: per-vertex transform
    and per-triangle math are identical to concatenation; no extra group sort.
    """
    tiles=tuple(terrain_tiles);_finite(fallback_height_bits)
    grid=cache_grid135(center_xy_bits,radius_bits);geometry=_GeometryProvider135(provider)
    ground=ground_grid135(tiles,grid,progress=progress);nav=bytes(grid.nav_width**2)
    stats=Counter(terrain_tiles=len(tiles),ground_cells=len(ground),nav_width=grid.nav_width,secondary_width=grid.secondary_width)
    nav_raster=CandidateRaster135(grid.origin_xy_bits,grid.nav_width)
    for phase,instances in(('nav_m2',tuple(nav_m2)),('nav_wmo',tuple(nav_wmo))):
        for j,instance in enumerate(instances):
            if instance.kind!=phase[4:]:raise ValueError('Original navigation phase kind/order required')
            for mesh in geometry(instance):
                nav=mark_navigation(nav,len(nav),nav_raster,mesh,instance.position_xyz_bits,instance.rotation_degrees_bits,instance.scale_bits,ground)
                stats['nav_mesh_batches']+=1;stats['nav_triangles']+=len(mesh.indices)//3
            stats[phase+'_instances']+=1
            if progress:progress(dict(phase=phase,index=j+1,total=len(instances)))
    before_connectivity=nav;nav=seal_unreachable_nav135(nav,grid)
    stats['nav_wall_cells_before_connectivity']=sum(x!=0 for x in before_connectivity)
    stats['nav_blocked_cells_after_connectivity']=sum(x!=0 for x in nav)
    stats['nav_additional_sealed_cells']=sum(a!=b for a,b in zip(before_connectivity,nav))
    height_raster=CandidateRaster135(grid.origin_xy_bits,grid.secondary_width)
    instances=tuple(secondary_wmo)
    def candidates():
        for j,instance in enumerate(instances):
            if instance.kind!='wmo':raise ValueError('Originalsecondary only consumes WMO instances')
            for mesh in geometry(instance):
                transformed=transform_mesh(mesh,instance.position_xyz_bits,instance.rotation_degrees_bits,instance.scale_bits)
                stats['secondary_mesh_batches']+=1;stats['secondary_triangles']+=len(mesh.indices)//3
                for start in range(0,len(mesh.indices)-2,3):
                    points=(transformed.vertices[mesh.indices[start+k]]for k in range(3))
                    yield from height_candidates(height_raster,*points,0x7f7fffff)
            stats['secondary_wmo_instances']+=1
            if progress:progress(dict(phase='secondary_wmo',index=j+1,total=len(instances)))
    secondary=merge_secondary135(tiles,grid,candidates(),stats=stats)
    stats['geometry_unique_root_or_m2']=len(geometry.meshes);stats['geometry_resource_reads']=len(geometry.reads)
    world=WorldQueries135(tiles,None,secondary,NavGrid135(nav,grid.origin_xy_bits,grid.nav_width),fallback_height_bits,None)
    return WorldCacheBuild135(world,ground,before_connectivity,grid,dict(stats))
