"""Static135 entry resource/path contracts, independent of the original runtime.

Reads caller-supplied genuine asset bytes. This does not manufacture SELF,
original VFS/Once handles, a world124 object, or completed1089 state. WDT/ADT
support below is a bounded container/request planner, not terrain reconstruction.
"""
from dataclasses import dataclass
import json
import struct
from urllib.parse import quote_from_bytes

from core_spec import binary32 as f
from .dbc import DBC

GLOBAL_ENTRY_DBCS = (b'DBFilesClient\\Spell.dbc', b'DBFilesClient\\SpellIcon.dbc')
MAP_DIRECTORIES = {0:b'Azeroth',1:b'Kalimdor',30:b'PVPZone01',189:b'MonasteryInstances',
                   529:b'PVPZone04',533:b'Stratholme Raid'}
DEFAULT_MAP_DIRECTORY = b'PVPZone03'  # Actual6730 fallback, includes map489.
HALF_WORLD_BITS = 0x46855555
TILE_SIZE_BITS = 0x44055555


class UnknownEntryResource135(NotImplementedError): pass


def canonical_chain_name(value):
    """Exact23187 byte rule: slash->backslash, ASCII A..Z->a..z only."""
    if type(value) is not bytes: raise TypeError('Explicit UTF8 chain-name bytes required')
    value.decode('utf8')
    return bytes(92 if c == 47 else c + 32 if 65 <= c <= 90 else c for c in value)


def parse_name_index(data):
    """Semantic successful78412 JSON-array index; not its physical hash table."""
    if type(data) is not bytes: raise TypeError('Actual index bytes required')
    names = json.loads(data)
    if type(names) is not list or not all(type(n) is str for n in names):
        raise ValueError('Explicit JSON array of chain-name strings required')
    return frozenset(canonical_chain_name(n.encode('utf8')) for n in names)


def static_relative_path(name):
    """Successful static48920 path; original index normalization is separate."""
    value = canonical_chain_name(name)
    parts = [x for x in value.split(b'\\') if x]
    if any(x in (b'.', b'..') for x in parts):
        raise UnknownEntryResource135('Traversal-like paths outside restored asset request domain')
    return '/'.join(quote_from_bytes(p, safe="~!*'()-._") for p in parts)


def resource_url(base, name, *, layout, stamp):
    """78412 reserved index URL or48920 ordinary URL, from explicit config."""
    if not all(type(x) is str for x in (base, layout, stamp)) or type(name) is not bytes:
        raise TypeError('Explicit base/layout/stamp and UTF8 name required')
    if name == b'__index': return base.rstrip('/') + '/__index' + stamp
    if layout == 'static': return base.rstrip('/') + '/' + static_relative_path(name)
    # Original48920 uses the configured base even outside static layout.
    return base.rstrip('/') + '/' + quote_from_bytes(name, safe="~!*'()-._")


def load_entry_dbcs(provider):
    """Actual4546 first-request order, with stronger exact-container checking.

    provider is an independent real-file/MPQ reader. It is not registered as a
    WASM import. Parsed schema column semantics/cache construction remain open.
    """
    return tuple((name, DBC.parse(provider(name))) for name in GLOBAL_ENTRY_DBCS)


@dataclass(frozen=True)
class Chunk135:
    tag: bytes
    offset: int
    payload: bytes


def chunks(data):
    if type(data) is not bytes: raise TypeError('Actual container bytes required')
    result = []; at = 0
    while at < len(data):
        if at + 8 > len(data): raise ValueError('Truncated chunk header')
        tag, size = struct.unpack_from('<4sI', data, at); end = at + 8 + size
        if end > len(data): raise ValueError('Truncated chunk payload')
        result.append(Chunk135(tag, at, data[at+8:end])); at = end
    return tuple(result)


def wdt_tile_mask(data):
    """Real seven observed WDTs: NIAM32768, first byte&1 per8B entry."""
    rows = [c for c in chunks(data) if c.tag == b'NIAM']
    if len(rows) != 1 or len(rows[0].payload) != 32768:
        raise UnknownEntryResource135('Only one canonical32768B MAIN payload restored')
    return bytes(rows[0].payload[i*8] & 1 for i in range(4096))


def directory_for_map(map_id):
    if type(map_id) is not int or not -(1<<31) <= map_id < 1<<31: raise ValueError('Actual i32 map ID required')
    return MAP_DIRECTORIES.get(map_id, DEFAULT_MAP_DIRECTORY)


def wdt_name(map_id):
    d = directory_for_map(map_id)
    return b'World\\Maps\\' + d + b'\\' + d + b'.wdt'


def _tile(coordinate_bits):
    if type(coordinate_bits) is not int or not 0 <= coordinate_bits <= f.MASK:
        raise ValueError('Explicit coordinate binary32 required')
    n = f.to_float(f.div(f.sub(HALF_WORLD_BITS, coordinate_bits), TILE_SIZE_BITS))
    if not -100000 < n < 100000: raise UnknownEntryResource135('Nonfinite/extreme coordinate domain not restored')
    return min(63, max(0, int(n)))


def neighboring_adt_names(map_id, center_xy_bits, mask):
    """6730 requests a3x3 neighborhood, WDT mask[x*64+y], filename_y_x.

    This establishes path requests only. ADT parse success, geometry filtering,
    MCVT interpolation, walkability, pathfinding and world124 output are pending.
    """
    if type(mask) is not bytes or len(mask) != 4096 or any(x not in (0,1) for x in mask):
        raise ValueError('Resolved4096-byte WDT MAIN mask required')
    if type(center_xy_bits) is not tuple or len(center_xy_bits) != 2: raise ValueError('Explicit XY bits required')
    x, y = (_tile(v) for v in center_xy_bits); d = directory_for_map(map_id); result = []
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            tx, ty = x+dx, y+dy
            if 0 <= tx < 64 and 0 <= ty < 64 and mask[tx*64+ty]:
                result.append(b'World\\Maps\\'+d+b'\\'+d+b'_'+str(ty).encode()+b'_'+str(tx).encode()+b'.adt')
    return tuple(result)


def adt_declared_model_names(data):
    """Candidate MMDX/MWMO strings only, not proof each model is loaded."""
    return tuple((c.tag, s) for c in chunks(data) if c.tag in (b'XDMM',b'OMWM')
                 for s in c.payload.split(b'\0') if s)


def default_opening_calls(*, mode, protection_flags, empty_initial_pickups):
    if mode != 0 or protection_flags != 0 or empty_initial_pickups is not True:
        raise UnknownEntryResource135('Only explicit default mode0/protection0/empty pickups restored')
    return (('1744',), *(('5736',0,False,0x41d00000,0x42100000,0x3f000000) for _ in range(4)),
            ('13516_then1417',0x41900000,0x42480000,2,2),
            ('13516_then1417',0x41900000,0x42480000,2,1))


KIND2_ACTOR_DESCRIPTOR = (9005,259,0x3f800000)
KIND2_ENTITY_ARGUMENTS = (3,0)
PENDING = ('No original VFS64/Once/cache/host object is forged.',
           'Local base-asset identity is not latest135 complete-asset equivalence.',
           'Resource loading/world124 and all1089 event/UI/packet effects are not implemented.',
           'Opening requests are static contracts; their full original continuation has not been executed.')
