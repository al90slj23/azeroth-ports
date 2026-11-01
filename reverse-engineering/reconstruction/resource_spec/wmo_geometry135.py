"""Independent fixed135 WMO collision projections from explicit real bytes.

This restores the bounded canonical REVM17 root/group geometry projection of
1510 and the flags/index-order part of4464. It is not a complete160B parser
record, VFS loader9513, material renderer, world/cache producer or validation
claim. Original differential admission is a separate step.
"""
from dataclasses import dataclass
import math
import struct


class UnknownWmoGeometry135(NotImplementedError): pass


@dataclass(frozen=True)
class WmoRoot135:
    group_count: int


@dataclass(frozen=True)
class WmoGroup135:
    vertices_bits: tuple
    indices_u16: tuple
    triangle_attributes: tuple
    group_flags: int
    liquid_type: int


@dataclass(frozen=True)
class WmoCollisionMesh135:
    """4464 appends XYZ12 vertices and u32 indices, deduplicating per group."""
    vertices: tuple = ()
    indices: tuple = ()

    def __post_init__(self):
        if len(self.vertices)>1048576 or len(self.indices)>4194304:
            raise UnknownWmoGeometry135('Explicit independent WMO mesh budget')
        if any(type(i)is not int or not 0<=i<len(self.vertices) for i in self.indices):
            raise UnknownWmoGeometry135('Malformed WMO index behavior is outside the canonical domain')


def _chunks(data,start=0):
    out=[];at=start
    while at<len(data):
        if at+8>len(data):raise UnknownWmoGeometry135('Truncated canonical WMO chunk header')
        tag,size=struct.unpack_from('<4sI',data,at);end=at+8+size
        if end>len(data):raise UnknownWmoGeometry135('Truncated canonical WMO chunk payload')
        out.append((tag,data[at+8:end]));at=end
    return tuple(out)


def _one(chunks,tag):
    selected=[v for k,v in chunks if k==tag]
    if len(selected)!=1:raise UnknownWmoGeometry135('Canonical WMO requires one '+repr(tag))
    return selected[0]


def parse_wmo_collision(data):
    """1510's MOVT words, MOVI u16 and MOPY byte pairs, without float conversion.

    Actual1510 first searches for MOHD or MOGP. MOGP has a68B header; flags at8
    and liquid type at52 are retained. Duplicate/partial chunks, error enum,
    root materials, doodads, lighting, BSP and allocator layout remain unknown.
    """
    if type(data)is not bytes or len(data)>32*1024*1024:
        raise UnknownWmoGeometry135('Explicit bounded actual WMO bytes required')
    top=_chunks(data)
    if _one(top,b'REVM')!=struct.pack('<I',17):
        raise UnknownWmoGeometry135('Only actual canonical WMO version17 is admitted')
    selected=next(((tag,payload) for tag,payload in top if tag in(b'DHOM',b'PGOM')),None)
    if selected is None:raise UnknownWmoGeometry135('Original1510 failure enum is not reconstructed')
    tag,payload=selected
    if tag==b'DHOM':
        if len(payload)!=64:raise UnknownWmoGeometry135('Canonical64B MOHD required')
        count=struct.unpack_from('<I',payload,4)[0]
        if count>4096:raise UnknownWmoGeometry135('Explicit WMO group count budget')
        return WmoRoot135(count)
    if len(payload)<68:raise UnknownWmoGeometry135('Canonical68B MOGP header required')
    group_flags,liquid_type=struct.unpack_from('<I',payload,8)[0],struct.unpack_from('<I',payload,52)[0]
    group=_chunks(payload,68)
    vertex_bytes=_one(group,b'TVOM');index_bytes=_one(group,b'IVOM');attributes=_one(group,b'YPOM')
    if len(vertex_bytes)%12 or len(index_bytes)%6 or len(attributes)%2:
        raise UnknownWmoGeometry135('Partial canonical WMO geometry record')
    vertices=tuple(struct.iter_unpack('<3I',vertex_bytes))
    indices=struct.unpack('<'+'H'*(len(index_bytes)//2),index_bytes)
    flags=tuple(struct.iter_unpack('<2B',attributes))
    if len(vertices)>65536 or len(flags)*3!=len(indices):
        raise UnknownWmoGeometry135('Canonical source vertices and full triangle attributes required')
    if any(i>=len(vertices) for i in indices):
        raise UnknownWmoGeometry135('Original per-index invalid bounds branch is outside this domain')
    for vertex in vertices:
        for word in vertex:
            value=struct.unpack('<f',struct.pack('<I',word))[0]
            if not math.isfinite(value)or abs(value)>1000000:
                raise UnknownWmoGeometry135('Nonfinite/extreme WMO vertex domain')
    return WmoGroup135(vertices,tuple(indices),flags,group_flags,liquid_type)


def append_group_collision(group,mesh=None,*,exclude_flags=4,required_flags=0):
    """Complete4464 canonical geometry projection in original triangle order.

    Reject(flags&exclude)!=0; require(flags&required)==(required&255).
    Group-local source-index hash semantics preserve first appearance, while
    the assigned index is the full current global vertex count, not u16.
    The second MOPY material byte has no collision filter role here.
    """
    if not isinstance(group,WmoGroup135):raise TypeError('Explicit parsed WMO group required')
    if mesh is None:mesh=WmoCollisionMesh135()
    if not isinstance(mesh,WmoCollisionMesh135):raise TypeError('Explicit WMO accumulation mesh required')
    if type(exclude_flags)is not int or type(required_flags)is not int or not 0<=exclude_flags<=0xffffffff or not 0<=required_flags<=0xffffffff:
        raise ValueError('Actual u32 4464 flag arguments required')
    vertices=list(mesh.vertices);indices=list(mesh.indices);seen={}
    for triangle,(flags,material) in enumerate(group.triangle_attributes):
        if flags&exclude_flags or flags&required_flags!=(required_flags&255):continue
        for source_index in group.indices_u16[triangle*3:triangle*3+3]:
            index=seen.get(source_index)
            if index is None:
                index=len(vertices);seen[source_index]=index;vertices.append(group.vertices_bits[source_index])
            indices.append(index)
    return WmoCollisionMesh135(tuple(vertices),tuple(indices))


def root_group_paths(root_path,root):
    """9513's actual lowercase.wmo suffix and _%03d.wmo group request order."""
    if type(root_path)is not str or not isinstance(root,WmoRoot135):raise TypeError('Explicit root path and parsed root required')
    stem=root_path[:-4]if root_path.endswith('.wmo')else root_path
    return tuple(stem+'_'+str(i).zfill(3)+'.wmo' for i in range(root.group_count))
