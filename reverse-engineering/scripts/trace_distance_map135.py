#!/usr/bin/env python3
"""Static/index-seek source proof for inline921 distance-map producer."""
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import struct

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source

PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'


def main():
    binary = SOURCE.read_bytes(); assert hashlib.sha256(binary).hexdigest() == SOURCE_SHA
    types, imports, decl, bodies, segments = parse_source(binary)
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('distance-map0135-static-%Y%m%dT%H%M%S.%fZ'); out.mkdir()
    texts, functions = {}, []
    with sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro', uri=True) as con:
        with (PROFILE / 'official-0.135.1-full.wat').open('rb') as wat:
            for index in (880, 921, 82072):
                ws, we, bs, be = con.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?', (index,)).fetchone()
                assert bodies[index] == (bs, be)
                wat.seek(ws); raw = wat.read(we - ws); assert raw.startswith(f'  (func (;{index};) '.encode())
                (out / f'{index}.wat').write_bytes(raw); texts[index] = [line.strip() for line in raw.decode().splitlines()]
                params, results = types[decl[index - len(imports)]]
                functions.append(dict(index=index, wat_start=ws, wat_end=we,
                    body_sha256=hashlib.sha256(binary[bs:be]).hexdigest(), wat_sha256=hashlib.sha256(raw).hexdigest(),
                    parameters_hex=params.hex(), results_hex=results.hex()))
    guards = []
    def guard(index, sequence, label):
        lines = texts[index]; hits = [n + 1 for n in range(len(lines) - len(sequence) + 1) if lines[n:n + len(sequence)] == sequence]
        assert hits, (index, label)
        guards.append(dict(function=index, label=label, lines=hits, instructions=sequence))
    guard(880, ['call 921'], '880 calls actual full921')
    guard(921, ['local.get 4', 'i32.load offset=32', 'i32.const -1', 'i32.eq'], 'nav Vec sentinel absent')
    guard(921, ['local.get 2', 'i32.load offset=20', 'local.get 6', 'local.get 8', 'i32.mul', 'local.get 7', 'i32.add', 'i32.eq'], 'same player-cell seed skips refresh')
    guard(921, ['local.get 37', 'local.get 0', 'f32.load offset=2372', 'f32.sub', 'f32.const 0x1.99999ap-3 (;=0.2;)', 'f32.ge'], 'binary32 clock age >=0.2')
    guard(921, ['local.get 32', 'local.get 28', 'i32.store16'], 'each discovered cost stored as u16')
    guard(921, ['local.get 2', 'local.get 3', 'i32.load offset=288', 'i32.store offset=24'], 'reachable count is Rc map field24')
    guard(921, ['local.get 0', 'local.get 37', 'f32.store offset=2372', 'local.get 0', 'local.get 2', 'i32.store offset=2368'], 'clock then map pointer replacement')
    for segment in segments:
        if segment['address'] is not None and segment['address'] <= 5512232 and segment['address'] + segment['length'] >= 5512296:
            start = segment['file_offset'] + 5512232 - segment['address']
            neighbors = struct.unpack_from('<16i', binary, start)
            break
    else:
        raise AssertionError('Neighbor table data segment absent')
    assert neighbors == (1, 0, -1, 0, 0, 1, 0, -1, 1, 1, 1, -1, -1, 1, -1, -1)
    result = dict(version='0.135.1', build='0898d5e3', original_wasm_sha256=SOURCE_SHA,
        functions=functions, guards=guards, full_wat_read=False, index_seek_only=True, target_executed=False,
        producer='inline at beginning of complete921;880->921',
        neighbor_table=dict(address=5512232, xy=[list(neighbors[n:n + 2]) for n in range(0, 16, 2)]),
        nav_layout=dict(world_rc_offset=2348, cap32=32, pointer36=36, length40=40, origin_xy=[44, 48], width52=52),
        map_rc_layout=dict(bytes=28, strong=0, weak=4, values_cap=8, values_pointer=12, values_length=16, seed_index=20, reachable_count=24),
        game_fields=dict(map_rc=2368, last_refresh_bits=2372),
        rules=['same in-bounds cell retains previous map and clock regardless elapsed time',
            'different/outside cell with previous map requires f32(now-last)>=f32(0.2)',
            'missing previous map builds immediately; missing nav preserves previous map and clock',
            'all width*width u16 values start65535; start cell becomes0 even if its nav byte is nonzero',
            'FIFO eight-neighbor BFS costs one per step; nonzero nav blocks; both orthogonal cells must be free for diagonal',
            'due outside-player rebuild clears previous map and writes current clock',
            'actual shared builder/host and all previously frozen model sources remain unchanged'],
        source_file='scripts/trace_distance_map135.py', source_sha256=hashlib.sha256((ROOT / 'scripts/trace_distance_map135.py').read_bytes()).hexdigest())
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), functions=len(functions), guards=len(guards), target_executed=False)))


if __name__ == '__main__': main()
