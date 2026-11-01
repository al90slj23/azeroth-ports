"""Fixed135 canonical ADT object placements and explicit world selection.

The actual1446 output is two ordered44B record vectors.  The String pointer is
represented by its bytes; numeric fields retain their exact binary32/u32 words.
The container parser accepts the declared canonical successful-file domain,
not malformed-file recovery.  Selection is6730's independent static rule and
must not be counted as a new full6730 original execution.
"""
from dataclasses import dataclass
import math
import struct

from core_spec import binary32 as f
from .entry_resources135 import (chunks,canonical_chain_name,wdt_name,
    wdt_tile_mask,neighboring_adt_names)

HALF_WORLD = 0x46855555
ONE = 0x3f800000
FORTY = 0x42200000
FOUR_HUNDRED = 0x43c80000


class UnknownWorldPlacements135(NotImplementedError): pass


def _finite(word):
    if type(word)is not int or not 0<=word<=0xffffffff or not math.isfinite(f.to_float(word)):
        raise UnknownWorldPlacements135('Explicit finite binary32 placement domain required')
    return word


@dataclass(frozen=True)
class Placement135:
    kind: str
    name_utf8: bytes
    position_xyz_bits: tuple
    rotation_degrees_bits: tuple
    scale_bits: int
    unique_id: int
    wmo_sets_word: int = 0
    source_record_index: int = 0
    source_file: bytes | None = None

    def __post_init__(self):
        if self.kind not in ('m2','wmo'):raise ValueError('Actual m2/wmo kind required')
        if type(self.name_utf8)is not bytes:raise TypeError('Actual UTF8 name bytes required')
        self.name_utf8.decode('utf8')
        if len(self.position_xyz_bits)!=3 or len(self.rotation_degrees_bits)!=3:
            raise ValueError('Three explicit coordinate/rotation words required')
        for w in (*self.position_xyz_bits,*self.rotation_degrees_bits,self.scale_bits):_finite(w)
        for n in (self.unique_id,self.wmo_sets_word,self.source_record_index):
            if type(n)is not int or not 0<=n<=0xffffffff:raise ValueError('Actual u32 required')

    @property
    def scalar_words(self):
        """Original44B record's bytes12..43, excluding RustString ownership."""
        tail=(self.scale_bits,self.unique_id)if self.kind=='m2'else(self.unique_id,self.wmo_sets_word)
        return (*self.position_xyz_bits,*self.rotation_degrees_bits,*tail)

    @property
    def chain(self):
        name=m2_collision_name(self.name_utf8)if self.kind=='m2'else self.name_utf8
        return canonical_chain_name(name)


@dataclass(frozen=True)
class AdtPlacements135:
    m2: tuple
    wmo: tuple


def m2_collision_name(name):
    """Successful13850 path: ASCII lowercase basename + .m2 for MDX/MDL/M2.

    The original scans at most259 source bytes.  Truncation, invalid UTF8 and
    unrecognized-extension fallback stay outside this successful path domain.
    """
    if type(name)is not bytes:raise TypeError('Actual UTF8 filename bytes required')
    name.decode('utf8')
    if len(name)>259:raise UnknownWorldPlacements135('Long/truncated13850 name outside restored domain')
    dot=name.rfind(b'.')
    lower=bytes(c+32 if 65<=c<=90 else c for c in name)
    if dot<0 or lower[dot:]not in(b'.mdx',b'.mdl',b'.m2'):
        raise UnknownWorldPlacements135('13850 unrecognized-extension fallback not restored')
    return lower[:dot]+b'.m2'


def _names(table,offsets):
    if len(offsets)%4:raise UnknownWorldPlacements135('Canonical4B name-offset table required')
    result=[]
    for (offset,)in struct.iter_unpack('<I',offsets):
        if offset>=len(table):raise UnknownWorldPlacements135('Out-of-range name offset not restored')
        end=table.find(b'\0',offset)
        if end<0:raise UnknownWorldPlacements135('Canonical NUL-terminated names required')
        name=table[offset:end];name.decode('utf8');result.append(name)
    return tuple(result)


def parse_adt_placements(data,*,source_file=None):
    """Complete1446's canonical MDDF/MODF44B placement projection.

    MDDF and MODF source order is retained.  Name indices beyond the resolved
    name vector are skipped, as original1446 does; corrupt name offsets and
    noncanonical/truncated containers stop explicitly.
    """
    wanted=(b'XDMM',b'DIMM',b'OMWM',b'DIWM',b'FDDM',b'FDOM')
    selected={}
    for c in chunks(data):
        if c.tag in wanted:
            if c.tag in selected:raise UnknownWorldPlacements135('Repeated placement/name chunk outside restored domain')
            selected[c.tag]=c.payload
    for tag in wanted:
        if tag not in selected:raise UnknownWorldPlacements135('Explicit canonical placement/name chunks required')
    names_m2=_names(selected[b'XDMM'],selected[b'DIMM'])
    names_wmo=_names(selected[b'OMWM'],selected[b'DIWM'])
    out={}
    for kind,tag,stride,names in [('m2',b'FDDM',36,names_m2),('wmo',b'FDOM',64,names_wmo)]:
        raw=selected[tag]
        if len(raw)%stride:raise UnknownWorldPlacements135('Canonical whole placement records required')
        if len(raw)//stride>65536:raise UnknownWorldPlacements135('Declared placement record budget exceeded')
        records=[]
        for i in range(len(raw)//stride):
            at=i*stride;name_index,uid=struct.unpack_from('<2I',raw,at)
            if name_index>=len(names):continue
            xyz=struct.unpack_from('<3I',raw,at+8);rot=struct.unpack_from('<3I',raw,at+20)
            for w in (*xyz,*rot):_finite(w)
            position=(f.sub(HALF_WORLD,xyz[2]),f.sub(HALF_WORLD,xyz[0]),xyz[1])
            if kind=='m2':
                scale=f.mul(f.from_u32(struct.unpack_from('<H',raw,at+32)[0]),0x3a800000);sets=0
            else:
                scale=ONE;doodad,name_set=struct.unpack_from('<2H',raw,at+58);sets=doodad|(name_set<<16)
            records.append(Placement135(kind,names[name_index],position,rot,scale,uid,sets,i,source_file))
        out[kind]=tuple(records)
    return AdtPlacements135(out['m2'],out['wmo'])


def load_world_placements(map_id,center_xy_bits,provider):
    """Independent WDT request plan -> actual ADT bytes -> placements, in6730 order."""
    mask=wdt_tile_mask(provider(wdt_name(map_id)))
    return tuple((name,parse_adt_placements(provider(name),source_file=name))
        for name in neighboring_adt_names(map_id,center_xy_bits,mask))


def select_collision_instances(tiles,center_xy_bits,extent_bits,*,phase):
    """6730 nav_m2/nav_wmo/secondary_wmo instance rules, in original source order.

    Each pass has its own unique-ID set.  IDs are inserted after XY selection,
    so an out-of-range duplicate does not hide a later in-range instance.
    Secondary WMO does not apply the navigation pass's XY range check.
    """
    if phase not in ('nav_m2','nav_wmo','secondary_wmo','primary_wmo'):
        raise ValueError('Explicit restored collision pass required')
    if len(center_xy_bits)!=2:raise ValueError('Explicit center XY required')
    for w in (*center_xy_bits,extent_bits):_finite(w)
    if f.to_float(extent_bits)<0:raise UnknownWorldPlacements135('Nonnegative extent required')
    kind='m2'if phase=='nav_m2'else'wmo';seen=set();result=[]
    for _,tile in tiles:
        for instance in getattr(tile,kind):
            if phase.startswith('nav_'):
                if kind=='m2':
                    scale=instance.scale_bits if f.to_float(instance.scale_bits)>1 else ONE
                    margin=f.add(extent_bits,f.mul(scale,FORTY))
                else:margin=f.add(extent_bits,FOUR_HUNDRED)
                if not all(f.to_float(f.sub(instance.position_xyz_bits[j],center_xy_bits[j])&~f.SIGN)<f.to_float(margin)for j in(0,1)):
                    continue
            if instance.unique_id in seen:continue
            seen.add(instance.unique_id);result.append(instance)
    return tuple(result)


def first_chain_requests(instances):
    """Logical first-request order from an already selected ordered instance pass."""
    seen=set();result=[]
    for instance in instances:
        chain=instance.chain
        if chain not in seen:seen.add(chain);result.append(chain)
    return tuple(result)
