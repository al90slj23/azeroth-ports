#!/usr/bin/env python3
"""Read-only, function-bounded fixed135 player movement source receipt.

No WASM instantiation, original/model/checker execution or profile mutation.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE = ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
INDICES = (880, 968, 1371, 2328, 4328, 42184, 9234, 33324, 29219, 28964, 49503)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def main():
    source_sha = sha(Path(__file__))
    assert SOURCE.stat().st_size == 90959080 and sha(SOURCE) == SOURCE_SHA
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('player-motion135-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    con = sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    rows = []
    with (PROFILE/'official-0.135.1-full.wat').open('rb') as wat, SOURCE.open('rb') as wasm:
        for index in INDICES:
            row = dict(con.execute('select * from functions where idx=?', (index,)).fetchone())
            wat.seek(row['wat_start']); text = wat.read(row['wat_end']-row['wat_start'])
            assert text.splitlines()[0].startswith(f'  (func (;{index};)'.encode())
            wasm.seek(row['body_start']); body = wasm.read(row['body_end']-row['body_start'])
            (out/f'{index}.wat').write_bytes(text)
            (out/f'{index}.compact.txt').write_text('\n'.join(f'{i+1}: {line.strip()}' for i,line in enumerate(text.decode().splitlines()))+'\n')
            rows.append(dict(index=index, **row, wat_bytes=len(text), wat_sha256=hashlib.sha256(text).hexdigest(),
                body_sha256=hashlib.sha256(body).hexdigest(),
                callers=[dict(x) for x in con.execute('select caller,count(*) sites from calls where callee=? group by caller', (index,))],
                callees=[dict(x) for x in con.execute('select callee,count(*) sites from calls where caller=? group by callee', (index,))]))
    trace = dict(version='0.135.1', build='90898d5e3', source_sha256=source_sha, original_wasm_sha256=SOURCE_SHA,
        original_executed=False, original_modified=False, sqlite_mode='ro', profile_full_scan=False, functions=rows,
        input=dict(entry968='(App, ownerRoute, peer, opcode, payloadPointer, payloadLength)',
            movement_opcodes=list(range(181,199))+list(range(200,204))+[218,219,238],
            canonical_payload_bytes=24, fields=[['flags2496',0,'u32le'],['client_clock_ms',4,'u32le'],
                ['x',8,'f32le'],['y',12,'f32le'],['z',16,'f32le'],['facing',20,'f32le']],
            finite_rejection='All four float absolute words >0x7f7fffff are rejected before Game mutation.',
            short_payload='Original zero/default-byte parser is not admitted by independent canonical24 API.'),
        update=dict(entry2328='(Game, pointerToXYZ12, facing:f32)->i32', game_xyz_offsets=[1416,1420,1424],
            game_facing_offset=1428, clock_override=[440,444], flags=2496, last_position_clock=2500,
            return_semantics='Final XYZ equals input XYZ by f32.eq, not a generic acceptance flag.',
            rejection='Pending correction distanceSquared>9 and GameNow-pendingSince<3 returns0 without clearing pending.',
            correction=['outside circle(radius+10) or polygon', 'below-surface for>=0.75 client seconds',
                '3x3 special blocked-nav for>=1 client second', 'active movement<=0.75 displacement for>=1.5 client seconds',
                'below map-dependent Z threshold'],
            correction_packet199='packedGUID + oldActionSequence:u32 + 0:u32 + 0:u32 + XYZ12 + facing:f32 + 0:u32',
            correction_packet150='chat type10,language0,sender0,text byte length+1,outside message,NUL,NUL',
            started_run='If phase2587=0, moved d2>0.04,remote2528=0 and bit0(2583)=0, calls full1089.'),
        geometry=dict(world_rc=2348, primary_tag=56, primary_values=[72,76], primary_origin=[80,84], primary_width=88,
            auxiliary_min_raster=dict(pointer=60,count=64,origin=[80,84],width=88,consumer=33324,window='floor(2*(xy-origin)) +/-2; minimum non-NaN'),
            nav=dict(tag=32,pointer=36,count=40,origin=[44,48],width=52,blocked_window_consumer=42184,walkable_search_consumer=9234),
            primary_nearest=23181,height=29631,terrain_only=18670,
            rollback='Boundary clamp inward4; optional3x3-zero nav search radius20;29631 then23181 XYZ; nonpolicy height-miss rings1..20 require five29631 samples.'),
        unknown=['Upstream keyboard/WASD/joystick producer and native-client motion integration are not yet restored.',
            'Multiplayer peer/state swap2080 and outgoing rebroadcast following968 need independent differential.',
            'Phase0 actual1089 start side effects must use separately reconstructed full entry; semantic event alone is insufficient.',
            'Original allocation/vector physical backing and diagnostics464 side effects are not implied by static rules.'])
    target=out/'trace.json';target.write_text(json.dumps(trace,indent=2)+'\n')
    assert sha(Path(__file__))==source_sha
    print(json.dumps(dict(directory=str(out),trace_sha256=sha(target),functions=len(rows),original_executed=False)))


if __name__=='__main__': main()
