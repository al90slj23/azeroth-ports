#!/usr/bin/env python3
"""Index-seek proof of ordinary921 nav/path planning and packet-height queries."""
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source

PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'


def main():
    binary = SOURCE.read_bytes(); assert hashlib.sha256(binary).hexdigest() == SOURCE_SHA
    types, imports, decl, bodies, _ = parse_source(binary)
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('ai-world0135-static-%Y%m%dT%H%M%S.%fZ'); out.mkdir()
    texts, functions = {}, []
    with sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro', uri=True) as con:
        with (PROFILE / 'official-0.135.1-full.wat').open('rb') as wat:
            for index in (921, 29894, 28963, 27457, 45628, 80447, 69798, 29631, 23181):
                ws, we, bs, be = con.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?', (index,)).fetchone()
                assert bodies[index] == (bs, be); wat.seek(ws); raw = wat.read(we - ws)
                assert raw.startswith(f'  (func (;{index};) '.encode())
                (out / f'{index}.wat').write_bytes(raw); texts[index] = [line.strip() for line in raw.decode().splitlines()]
                params, results = types[decl[index - len(imports)]]
                functions.append(dict(index=index, wat_start=ws, wat_end=we,
                    body_sha256=hashlib.sha256(binary[bs:be]).hexdigest(), wat_sha256=hashlib.sha256(raw).hexdigest(),
                    parameters_hex=params.hex(), results_hex=results.hex()))
    guards = []
    def guard(index, sequence, label):
        lines = texts[index]; hits = [n + 1 for n in range(len(lines) - len(sequence) + 1) if lines[n:n + len(sequence)] == sequence]
        assert hits, (index, label); guards.append(dict(function=index, label=label, lines=hits, instructions=sequence))
    guard(921, ['call 29894'], 'inline path shortcut performs actual nav segment tests')
    guard(921, ['call 28963'], 'unreachable adjustment and downhill/lookahead use same finite-neighbor helper')
    guard(921, ['i32.const 39', 'local.set 7', 'loop  ;; label = @10'], 'forty candidate lookahead bound')
    guard(921, ['local.get 5', 'local.get 38', 'f32.store offset=336'], 'logical destination Z written before message projection')
    guard(921, ['call 29631'], 'message start/end height query is original world consumer')
    guard(921, ['call 23181'], 'missing direct height has nearest-primary-only-Z fallback')
    guard(29894, ['f32.const 0x1.333334p-2 (;=0.3;)', 'f32.div', 'f32.ceil', 'i32.trunc_sat_f32_u'], 'segment sample count ceil(distance/0.3)')
    guard(29894, ['i32.const -1', 'i32.xor', 'i32.or', 'i32.const 1', 'i32.and', 'i32.eqz'], 'blocking transition consumes only occupancy bit0')
    guard(28963, ['i32.const 65535', 'i32.eq'], 'u16 sentinel excluded from finite neighbor minimum')
    guard(27457, ['i32.const 221', 'i32.store16 offset=44'], 'positive move packet221 producer')
    result = dict(version='0.135.1', build='0898d5e3', original_wasm_sha256=SOURCE_SHA,
        target_executed=False, index_seek_only=True, full_wat_read=False, functions=functions, guards=guards,
        scope='ordinary non-ranged melee branch, explicit empty status producers, local/finite/nonfatal',
        rules=['logical orbit uses player Z;14-unit clamp retains current unit Z',
            'if nav/map exist and segment blocked, use distance-map finite descent, cell centres and at most40 lookahead candidates',
            'a selected flow centre uses current unit interpolated Z; packet-only terrain queries do not rewrite unit U336',
            '29894 permits exit from initial blocked region, tests bit0 transitions every0.3 units and returns last clear fraction',
            '28963 uses first strict minimum finite neighbor in fixed eight-direction order; success requires lower than current or current65535',
            'positive221 start/end XY stay logical; only Z is replaced by29631 height then23181 nearest-primary Z',
            'zero-duration stop221 uses raw current position without positive-move height branch'],
        source_file='scripts/trace_ai_world135.py', source_sha256=hashlib.sha256((ROOT / 'scripts/trace_ai_world135.py').read_bytes()).hexdigest())
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), functions=len(functions), guards=len(guards), target_executed=False)))


if __name__ == '__main__': main()
