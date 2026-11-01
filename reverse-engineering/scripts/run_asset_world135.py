#!/usr/bin/env python3
"""Build Elwynn queries and its default opening from a real local asset bundle.

This independent runner never reads an original memory capture or executes the
original program. Its asset manifest supplies names, files, sizes and SHA256s,
not parsed world/geometry outputs. The separate checker owns oracle comparison.
"""
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = Path('/Volumes/RuiRui4TB').resolve()
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.opening135 import EmptyOpeningInput135, initialize_empty_opening, projection
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from resource_spec.entry_resources135 import canonical_chain_name
from resource_spec.terrain135 import load_terrain_tiles
from resource_spec.world_placements135 import load_world_placements, select_collision_instances
from resource_spec.world_cache135 import produce_world_cache135

# Fixed original zone152[0] at5456016: map+96=0, center+104/+108,
# fallback+112=68, radius+120=120. These are static declarations, not captured
# world fields. The cache trace binds them to the original data and6730 reads.
ELWYNN_FALLBACK_BITS = 0x42880000


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def external_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to(EXTERNAL):
        raise ValueError('Research inputs and outputs must stay on the4T volume')
    return path


class ManifestAssets135:
    """Explicit local file provider; not an emulation of the original VFS."""
    def __init__(self, manifest):
        self.path = external_path(manifest)
        self.manifest_sha256 = sha(self.path)
        rows = json.loads(self.path.read_text())['requests']
        self.assets, self.loaded, self.requests = {}, {}, []
        for row in rows:
            if row['status'] != 200:
                raise ValueError('An unsuccessful asset row cannot supply a complete bundle')
            name = canonical_chain_name(row['chain'].encode('utf8'))
            if name == b'__index':
                continue
            if not name or any(p in (b'.', b'..') for p in name.split(b'\\')):
                raise ValueError('Invalid chain name')
            path = external_path(row['file'])
            if path.suffix.lower() in ('.memory', '.wasm', '.exe', '.wat'):
                raise ValueError('A game asset provider cannot consume original code/memory')
            value = (path, row['bytes'], row['sha256'])
            if type(value[1]) is not int or not 0 <= value[1] <= 16 * 1024 * 1024:
                raise ValueError('Single asset budget exceeded')
            if name in self.assets and self.assets[name] != value:
                raise ValueError('Ambiguous asset identity')
            self.assets[name] = value
        if not self.assets or len(self.assets) > 1024:
            raise ValueError('Explicit nonempty bounded asset manifest required')
        self.decoded_bytes = 0

    def __call__(self, name):
        if type(name) is not bytes:
            raise TypeError('The independent loader requests UTF8 chain-name bytes')
        key = canonical_chain_name(name)
        self.requests.append(key.decode('utf8'))
        if key not in self.loaded:
            path, size, digest = self.assets[key]
            if self.decoded_bytes + size > 256 * 1024 * 1024:
                raise ValueError('Decoded asset budget exceeded')
            data = path.read_bytes()
            if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('Asset size or SHA differs: ' + key.decode('utf8'))
            self.loaded[key] = data
            self.decoded_bytes += size
        return self.loaded[key]


def source_files():
    """All already imported independent modules plus this host runner."""
    paths = {Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        value = getattr(module, '__file__', None)
        if value:
            path = Path(value).resolve()
            if path.is_relative_to(ROOT / 'reconstruction') and path.suffix == '.py':
                paths.add(path)
    return sorted(paths)


def build_asset_world135(provider, *, progress=None):
    """Fixed Elwynn declarations to independent terrain, instances and caches."""
    center_x, center_y, radius = ZONE_GEOMETRY[0]
    center = center_x, center_y
    tiles = load_terrain_tiles(0, center, provider)
    placements = load_world_placements(0, center, provider)
    #6730 expands the configured radius by20 before its collision selection.
    from core_spec import binary32 as f
    extent = f.add(radius, 0x41a00000)
    selected = {phase: select_collision_instances(placements, center, extent, phase=phase)
                for phase in ('nav_m2', 'nav_wmo', 'secondary_wmo')}
    built = produce_world_cache135(tuple(tile for _, tile in tiles), center, radius,
        ELWYNN_FALLBACK_BITS, selected['nav_m2'], selected['nav_wmo'],
        selected['secondary_wmo'], provider, progress=progress)
    return built, tiles, selected


def write_world_outputs(built, output):
    world = built.world
    # Canonical query projection, not a pretend original heap/Rc layout.
    terrain = bytearray(struct.pack('<I', len(world.tiles)))
    for tile in world.tiles:
        terrain.extend(struct.pack('<5I', *tile.bounds_bits, len(tile.chunks)))
        for chunk in tile.chunks:
            terrain.extend(struct.pack('<HI', chunk.holes, len(chunk.vertices)))
            for vertex in chunk.vertices:
                terrain.extend(struct.pack('<3I', *vertex))
    (output / 'terrain-query.bin').write_bytes(terrain)
    (output / 'navigation.bin').write_bytes(world.nav.values)
    (output / 'secondary-height.u32le').write_bytes(
        b''.join(struct.pack('<I', w) for w in world.secondary.values_bits))
    return {'terrain': {'file': 'terrain-query.bin', 'bytes': len(terrain),
                        'sha256': sha(output / 'terrain-query.bin'),
                        'projection': 'tilecount:u32,each(bounds:4u32,chunkcount:u32,each(holes:u16,vertexcount:u32,XYZ:3u32[]))'},
            'navigation': {'file': 'navigation.bin', 'bytes': len(world.nav.values),
                          'sha256': sha(output / 'navigation.bin'),
                          'origin_xy_bits': world.nav.origin_xy_bits, 'width': world.nav.width},
            'secondary': {'file': 'secondary-height.u32le',
                          'bytes': len(world.secondary.values_bits) * 4,
                          'sha256': sha(output / 'secondary-height.u32le'),
                          'origin_xy_bits': world.secondary.origin_xy_bits,
                          'width': world.secondary.width}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--class-byte', type=int, default=1)
    parser.add_argument('--race-byte', type=int, default=1)
    parser.add_argument('--app-seed', type=lambda s: int(s, 0), default=0)
    parser.add_argument('--object-id', type=lambda s: int(s, 0), default=0)
    args = parser.parse_args()
    output = external_path(args.output or ROOT / 'evidence' / datetime.now(timezone.utc).strftime(
        'asset-world0135-independent-%Y%m%dT%H%M%S.%fZ'))
    output.mkdir(parents=True, exist_ok=False)
    files = source_files()
    before = {str(p.relative_to(ROOT)): sha(p) for p in files}
    snapshot = output / 'source-snapshot'
    for path in files:
        target = snapshot / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    (output / 'source-before.json').write_text(json.dumps(before, indent=2) + '\n')
    provider = ManifestAssets135(args.asset_manifest)
    opening_input = EmptyOpeningInput135(args.class_byte, args.race_byte, 0,
                                        args.app_seed, args.object_id)
    inputs = {'opening': asdict(opening_input),
              'world': {'map_id': 0, 'center_xy_bits': ZONE_GEOMETRY[0][:2],
                        'radius_bits': ZONE_GEOMETRY[0][2],
                        'fallback_height_bits': ELWYNN_FALLBACK_BITS},
              'asset_manifest': str(provider.path),
              'asset_manifest_sha256': provider.manifest_sha256}
    (output / 'inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
    began = time.monotonic()
    with (output / 'progress.jsonl').open('w', buffering=1) as log:
        def progress(*values, **fields):
            log.write(json.dumps({'elapsed_seconds': time.monotonic()-began,
                                  'values': values, **fields}, default=str) + '\n')
        built, tiles, selected = build_asset_world135(provider, progress=progress)
    artifacts = write_world_outputs(built, output)
    opening = initialize_empty_opening(opening_input, built.world,
        title_utf8=b'Elwynn Forest',
        subtitle_utf8='The Defias Uprising — survive the onslaught!'.encode('utf8'))
    opening_path = output / 'opening.json'
    opening_path.write_text(json.dumps(projection(opening), ensure_ascii=False) + '\n')
    after = {str(p.relative_to(ROOT)): sha(p) for p in files}
    assert before == after
    assert set(source_files()) == set(files), 'A late imported model escaped source freeze'
    receipt = {'version': '0.135.1', 'build': '0898d5e3',
        'kind': 'independent_asset_to_world_to_default_opening',
        'inputs': inputs, 'inputs_sha256': sha(output / 'inputs.json'),
        'asset_manifest': str(provider.path), 'asset_manifest_sha256': provider.manifest_sha256,
        'asset_names': sorted(x.decode('utf8') for x in provider.loaded),
        'asset_files': len(provider.loaded), 'decoded_asset_bytes': provider.decoded_bytes,
        'asset_requests': provider.requests, 'terrain_tiles': len(tiles),
        'instances': {p: len(xs) for p, xs in selected.items()},
        'world_artifacts': artifacts, 'world_stats': built.stats,
        'query_scalars': {'primary_present': built.world.primary is not None,
                          'flat_height_bits': built.world.flat_height_bits,
                          'fallback_height_bits': built.world.fallback_height_bits},
        'opening': {'file': opening_path.name, 'sha256': sha(opening_path),
                    'phase2587': opening.phase2587, 'counter': opening.counter,
                    'packet_count': len(opening.packets), 'rng_words': opening.rng_words},
        'source_sha256_before': before, 'source_sha256_after': after,
        'elapsed_seconds': time.monotonic()-began,
        'original_program_executed': False, 'original_memory_read': False,
        'new_original_differential_cases': 0, 'mainloop_frames': 0,
        'limitations': ['Fixed empty-profile Elwynn/English opening only.',
                        'Asset bundle name-to-file mapping is explicit input, not original VFS ownership.',
                        'Original opaque/unwritten record bytes are unknown, not zero.',
                        'Full world ownership, all maps/modes/rendering/mainloop/saves/multiplayer remain incomplete.'],
        'whole_game_complete': False}
    (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'directory': str(output), 'world': artifacts,
                      'opening_packets': len(opening.packets), 'elapsed_seconds': receipt['elapsed_seconds']}))


if __name__ == '__main__':
    main()
