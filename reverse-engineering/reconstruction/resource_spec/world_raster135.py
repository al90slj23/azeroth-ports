"""Independent fixed135 mesh -> height candidates / navigation raster producers.

No original code, snapshots, host API or parser is called. Every float is a raw
binary32 word. The upstream WMO parser, object selection and final6730 candidate
merge/cache ownership remain separate work. M2 support is only the real
classicMD20/version256 collision arrays, not a renderer or fullM2 reader.
"""
from dataclasses import dataclass
import math
import struct
from core_spec import binary32 as f
from core_spec.binary32_sqrt import sqrt_bits
from core_spec.ai_trig135 import sin_bits,cos_bits

HALF=0x3f000000
EPSILON=0x38d1b717
NEG_EPSILON=0xb8d1b717
ONE_EPSILON=0x3f800347
NORMAL_EPSILON=0x358637bd
SLOPE=0x3f333333
SAMPLE_DISTANCE=0x3ecccccd

class UnknownWorldRaster135(NotImplementedError):pass

def _word(v):
    if type(v)is not int or not 0<=v<=f.MASK:raise ValueError('Explicit binary32/u32 word required')
    return v

def _finite(v):
    _word(v)
    if not math.isfinite(f.to_float(v))or abs(f.to_float(v))>1000000:
        raise UnknownWorldRaster135('Nonfinite or extreme geometry remains outside this producer domain')

def _xyz(v):
    if type(v)is not tuple or len(v)!=3:raise ValueError('Explicit three-word XYZ required')
    for w in v:_finite(w)

@dataclass(frozen=True)
class CollisionMesh135:
    vertices:tuple
    indices:tuple
    def __post_init__(self):
        if len(self.vertices)>65536 or len(self.indices)>196608:raise UnknownWorldRaster135('Mesh budget')
        for v in self.vertices:_xyz(v)
        if any(type(i)is not int or not 0<=i<len(self.vertices)for i in self.indices):raise UnknownWorldRaster135('Original invalid-index panic/empty fallback domain not restored')

def parse_classic_m2_collision(data):
    """Exact236/240 u16 indices and244/248 XYZ arrays from declared classicMD20.

    Full1104 validation/animations are not replaced. Only valid canonical local
    assets are in this bounded parser domain; malformed assets explicitly stop.
    """
    if type(data)is not bytes or len(data)<260 or data[:8]!=b'MD20\x00\x01\x00\x00':
        raise UnknownWorldRaster135('Only canonical MD20/version256 collision arrays restored')
    ni,pi,nv,pv=struct.unpack_from('<4I',data,236)
    if ni%3 or ni>196608 or nv>65536 or pi+2*ni>len(data)or pv+12*nv>len(data):raise UnknownWorldRaster135('Malformed or excessive M2 collision array')
    vertices=tuple(struct.unpack_from('<3I',data,pv+12*j)for j in range(nv))
    indices=struct.unpack_from('<'+'H'*ni,data,pi)if ni else()
    return CollisionMesh135(vertices,tuple(indices))

def _rotation_matrix(rot):
    """Original18572 basis/Euler composition, ordered binary32 operations.

    The fixed basis contains sin(-pi/2)'s tiny residual. Zero products/additions
    are intentional: dropping them changes signed zero and final roundoff.
    Rows map original localXYZ into the world coordinate convention.
    """
    _xyz(rot);m={}
    v14=f.add(f.mul(rot[1],0x3c8efa35),0xc0490fdb)
    v5=cos_bits(v14);v14=sin_bits(v14)
    v15=f.mul(rot[0],0xbc8efa35);v17=sin_bits(v15);v15=cos_bits(v15)
    v18=f.mul(v14,0);v20=f.sub(v18,v5);v21=f.mul(v17,0)
    v22=f.add(f.sub(v15,v21),0);v19=f.mul(v5,0);v23=f.add(v14,v19)
    v24=f.mul(v15,0);v26=f.add(f.add(v17,v24),0)
    m[28]=f.add(f.mul(v20,0),f.sub(f.mul(v22,v23),f.mul(v26,0x333bbd2e)))
    v27=f.add(f.add(v14,0),v19);v28=f.sub(f.add(v5,0),v18)
    m[16]=f.add(f.mul(v27,0),f.add(f.mul(v26,0),f.mul(v22,v28)))
    v25=f.add(f.mul(rot[2],0x3c8efa35),0xbfc90fdb);v16=sin_bits(v25)
    v18=f.sub(f.add(v18,0),f.mul(v5,0x333bbd2e));v5=cos_bits(v25)
    v25=f.mul(v16,0);v29=f.add(v5,f.sub(0,v25));v30=f.mul(v5,0)
    v31=f.add(v30,f.sub(v21,f.mul(v15,v16)))
    v14=f.add(f.mul(v14,0x333bbd2e),f.add(v19,0))
    v19=f.add(v30,f.add(v24,f.mul(v17,v16)))
    m[48]=f.add(f.mul(v18,v29),f.add(v31,f.mul(v14,v19)))
    v16=f.add(v16,f.add(v30,0));v15=f.add(v25,f.add(v21,f.mul(v15,v5)))
    v5=f.add(v25,f.sub(v24,f.mul(v17,v5)))
    m[44]=f.add(f.mul(v18,v16),f.add(v15,f.mul(v14,v5)))
    m[40]=f.add(f.mul(v18,0),f.add(v26,f.mul(v22,v14)))
    m[36]=f.add(f.mul(v20,v29),f.sub(f.mul(v23,v19),f.mul(v31,0x333bbd2e)))
    m[32]=f.add(f.mul(v20,v16),f.sub(f.mul(v23,v5),f.mul(v15,0x333bbd2e)))
    m[24]=f.add(f.mul(v27,v29),f.add(f.mul(v28,v19),f.mul(v31,0)))
    m[20]=f.add(f.mul(v27,v16),f.add(f.mul(v28,v5),f.mul(v15,0)))
    return tuple(tuple(m[16+12*r+4*c]for c in range(3))for r in range(3))

def transform_mesh(mesh,position_bits,rotation_degrees_bits,scale_bits):
    _xyz(position_bits);_xyz(rotation_degrees_bits);_finite(scale_bits)
    matrix=_rotation_matrix(rotation_degrees_bits);out=[]
    for vertex in mesh.vertices:
        dot=tuple(f.mul(f.add(f.add(f.mul(row[0],vertex[0]),f.mul(row[1],vertex[1])),f.mul(row[2],vertex[2])),scale_bits)for row in matrix)
        out.append((f.add(position_bits[0],dot[0]),f.add(position_bits[1],dot[1]),f.add(dot[2],position_bits[2])))
    return CollisionMesh135(tuple(out),mesh.indices)

def _normal(a,b,c):
    ab=tuple(f.sub(b[j],a[j])for j in range(3));ac=tuple(f.sub(c[j],a[j])for j in range(3))
    nz=f.sub(f.mul(ab[0],ac[1]),f.mul(ab[1],ac[0]))
    nx=f.sub(f.mul(ab[1],ac[2]),f.mul(ab[2],ac[1]))
    ny=f.sub(f.mul(ab[2],ac[0]),f.mul(ab[0],ac[2]))
    length=sqrt_bits(f.add(f.mul(nz,nz),f.add(f.mul(nx,nx),f.mul(ny,ny))))
    return ab,ac,nz,length

@dataclass(frozen=True)
class CandidateRaster135:
    origin_xy_bits:tuple
    width:int
    def __post_init__(self):
        if type(self.width)is not int or not 0<=self.width<=1024:raise UnknownWorldRaster135('Raster width budget')
        if type(self.origin_xy_bits)is not tuple or len(self.origin_xy_bits)!=2:raise ValueError('Explicit origin')
        for w in self.origin_xy_bits:_finite(w)

def _min3(values):return min(values,key=f.to_float)
def _max3(values):return max(values,key=f.to_float)
def _sat_u(v):
    n=f.to_float(v)
    return 0 if math.isnan(n)or n<=0 else min(0xffffffff,int(n))

def height_candidates(raster,a,b,c,ceiling_bits):
    """Full12375 valid finite-triangle domain, in actual row-major append order."""
    for v in(a,b,c):_xyz(v)
    _word(ceiling_bits);ab,ac,nz,length=_normal(a,b,c)
    if f.to_float(length)<f.to_float(NORMAL_EPSILON):return()
    if f.to_float(f.div(nz&~f.SIGN,length))<f.to_float(SLOPE):return()
    if f.to_float(_min3((a[2],b[2],c[2])))>f.to_float(ceiling_bits):return()
    lower=[];upper=[]
    for axis,origin in enumerate(raster.origin_xy_bits):
        lo=f.sub(_min3((a[axis],b[axis],c[axis])),origin);hi=f.sub(_max3((a[axis],b[axis],c[axis])),origin)
        lo=f.sub(f.add(lo,lo),HALF);hi=f.sub(f.add(hi,hi),HALF)
        lower.append(max(0,math.ceil(f.to_float(lo))))
        upper.append(min(raster.width,max(0,math.floor(f.to_float(hi))+1)))
    result=[]
    for y in range(lower[1],upper[1]):
        py=f.add(raster.origin_xy_bits[1],f.mul(f.add(f.from_u32(y),HALF),HALF));dy=f.sub(py,a[1])
        by=f.mul(ab[0],dy);cy=f.mul(ac[0],dy)
        for x in range(lower[0],upper[0]):
            px=f.add(raster.origin_xy_bits[0],f.mul(f.add(f.from_u32(x),HALF),HALF));dx=f.sub(px,a[0])
            u=f.div(f.sub(f.mul(ac[1],dx),cy),nz)
            if f.to_float(u)<f.to_float(NEG_EPSILON):continue
            v=f.div(f.sub(by,f.mul(ab[1],dx)),nz)
            if f.to_float(v)<f.to_float(NEG_EPSILON)or f.to_float(f.add(u,v))>f.to_float(ONE_EPSILON):continue
            z=f.add(f.mul(ac[2],v),f.add(a[2],f.mul(ab[2],u)))
            if f.to_float(z)<=f.to_float(ceiling_bits):result.append((y*raster.width+x,z))
    return tuple(result)

@dataclass(frozen=True)
class CandidateVector135:
    storage:tuple
    length:int=0
    def __post_init__(self):
        if not 0<=self.length<=len(self.storage):raise ValueError('Candidate vector active length')
        for row in self.storage:
            if row is not None:
                if type(row)is not tuple or len(row)!=2:raise ValueError('Explicit index/height pair')
                for v in row:_word(v)

def append_height_candidates(state,rows):
    values=list(state.storage);n=state.length
    for row in rows:
        if n==len(values):values.extend([None]*(max(4,2*len(values))-len(values)))
        values[n]=row;n+=1
    return CandidateVector135(tuple(values),n)

def mark_navigation(storage,active_length,raster,mesh,position_bits,rotation_degrees_bits,scale_bits,ground_bits):
    """Full9328 finite valid mesh domain, including complete18572 transform.

    Byte raster has1m cells; ground heights are explicit same-index resolved
    input, which6730 builds above this producer. Existingbytes only change to1.
    """
    if type(storage)is not bytes or active_length!=raster.width*raster.width or len(storage)<active_length or len(ground_bits)!=active_length:
        raise UnknownWorldRaster135('Exact full square nav and same-index ground input required')
    for w in ground_bits:_word(w)
    transformed=transform_mesh(mesh,position_bits,rotation_degrees_bits,scale_bits);out=bytearray(storage)
    ox,oy=raster.origin_xy_bits;width=raster.width;maxx=f.add(ox,f.from_u32(width));maxy=f.add(oy,f.from_u32(width))
    for start in range(0,len(mesh.indices)-2,3):
        a,b,c=(transformed.vertices[mesh.indices[start+j]]for j in range(3))
        if f.to_float(_min3((a[1],b[1],c[1])))>f.to_float(maxy)or f.to_float(_min3((a[0],b[0],c[0])))>f.to_float(maxx):continue
        if f.to_float(_max3((a[0],b[0],c[0])))<f.to_float(ox)or f.to_float(_max3((a[1],b[1],c[1])))<f.to_float(oy):continue
        ab,ac,nz,length=_normal(a,b,c)
        if f.to_float(length)<f.to_float(NORMAL_EPSILON)or f.to_float(f.div(nz&~f.SIGN,length))>f.to_float(SLOPE):continue
        edges=(ab,ac,tuple(f.sub(c[j],b[j])for j in range(3)))
        lengths=tuple(sqrt_bits(f.add(f.add(f.mul(v[0],v[0]),f.mul(v[1],v[1])),f.mul(v[2],v[2])))for v in edges)
        steps=min(400,max(1,math.ceil(f.to_float(f.div(_max3(lengths),SAMPLE_DISTANCE)))))
        fractions=tuple(f.div(f.from_u32(i),f.from_u32(steps))for i in range(steps+1))
        for i,u in enumerate(fractions):
            row=tuple(f.add(a[j],f.mul(ab[j],u))for j in range(3))
            for j in range(steps-i+1):
                v=fractions[j];dx=f.sub(f.add(row[0],f.mul(ac[0],v)),ox)
                if f.to_float(dx)<0:continue
                dy=f.sub(f.add(row[1],f.mul(ac[1],v)),oy)
                if f.to_float(dy)<0:continue
                x,y=_sat_u(dx),_sat_u(dy)
                if x>=width or y>=width:continue
                index=y*width+x;ground=ground_bits[index]
                if f.is_nan(ground):continue
                z=f.add(row[2],f.mul(ac[2],v))
                if f.to_float(z)>f.to_float(f.add(ground,0x3eb33333))and f.to_float(z)<f.to_float(f.add(ground,0x4019999a)):out[index]=1
    return bytes(out)
