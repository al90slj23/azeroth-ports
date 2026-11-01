"""Read already independently parsed451-asset world artifacts, never snapshots."""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction'))
from resource_spec.terrain135 import TerrainChunk135, TerrainTile135, HeightRaster135
from resource_spec.world_query135 import NavGrid135, WorldQueries135

ASSET_WORLD = ROOT / 'evidence/asset-world0135-independent-20261101T111736.050879Z'
HASHES = {'terrain-query.bin':'3ecb0d08bc2202524a0b2a86cf43b7a6eba7d201de70f104c4dc675bf1e12b9e',
    'navigation.bin':'239b456859bedd6c4e1ebcdf5dadeefc6da66b344ec108e17f8b85819157fd79',
    'secondary-height.u32le':'07c7ab72911e7425456abdbad2a16b3d9fe068db17367996693f70a8be2df1d5'}


def load_asset_world135():
    receipt = json.loads((ASSET_WORLD / 'receipt.json').read_text())
    assert receipt['version'] == '0.135.1' and receipt['original_program_executed'] is False and receipt['original_memory_read'] is False
    data = {}
    for name, digest in HASHES.items():
        raw = (ASSET_WORLD / name).read_bytes(); assert hashlib.sha256(raw).hexdigest() == digest; data[name] = raw
    raw = data['terrain-query.bin']; offset = 0
    def unpack(fmt):
        nonlocal offset
        size = struct.calcsize(fmt); result = struct.unpack_from(fmt, raw, offset); offset += size; return result
    count = unpack('<I')[0]; tiles = []
    for _ in range(count):
        *bounds, nchunks = unpack('<5I'); chunks = []
        for _ in range(nchunks):
            holes, vertices = unpack('<HI')
            chunks.append(TerrainChunk135(tuple(unpack('<3I') for _ in range(vertices)), holes))
        tiles.append(TerrainTile135(tuple(chunks), tuple(bounds)))
    assert offset == len(raw) and count == 9
    origin = (3323265024, 3292610560)
    nav = NavGrid135(data['navigation.bin'], origin, 280)
    secondary = HeightRaster135(struct.unpack('<313600I', data['secondary-height.u32le']), origin, 560)
    return WorldQueries135(tuple(tiles), None, secondary, nav, 1116209152, None)


def asset_world_description135():
    return dict(kind='independently_parsed451_asset_world_inputs', directory=str(ASSET_WORLD),
        artifacts={name:dict(path=str(ASSET_WORLD / name), sha256=digest) for name, digest in HASHES.items()},
        origin_xy_bits=[3323265024, 3292610560], nav_width=280, secondary_width=560,
        fallback_height_bits=1116209152, primary=None, flat_height_bits=None)


def controlled_world135(desc):
    nav = desc['nav']
    nav = None if nav is None else NavGrid135(bytes.fromhex(nav['hex']), tuple(nav['origin_xy_bits']), nav['width'])
    primary = desc.get('primary')
    primary = None if primary is None else HeightRaster135(tuple(primary['values_bits']), tuple(primary['origin_xy_bits']), primary['width'])
    return WorldQueries135((), primary, None, nav, desc['fallback_height_bits'], desc['flat_height_bits'])
