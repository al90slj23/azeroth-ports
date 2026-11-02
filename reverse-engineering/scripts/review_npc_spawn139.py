#!/usr/bin/env python3
"""Read-only independent 139 NPC review; executes no author or original code."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math
import sqlite3
import struct
import time

from review_combat139 import bits, fp, f32, local_closure, parse_module, sha, u32, u64

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'evidence/npc-spawn139-fresh-oracle-20261102T031841.270631Z'
STATIC = ROOT / 'evidence/npc-spawn139-static-20261102T031838.749854Z'
SOURCE = ROOT / 'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE = ROOT / 'evidence/wasm0139-profile-20261102T012426.951871Z'
SOURCE_SHA = '71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMPARISON_SHA = '97a19153ff42e9b3ad692bd0edf134a52ecc0c4e2db5fc1f36a52b43f427e3e4'
PROOF_SHA = 'fe75f664b7d05627cb94e964d2750a24a929d83114ff192c6f543b2038ccd72d'
HANDOFF_SHA = '0b76c780dcbe17e31edbd25e8d8bf018c833256fc0dca8a2e0a0e52af7d67903'
HELPER_SHA = '158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9'
WRITES = ((0, 4), (8, 4), (16, 4), (40, 4), (64, 4), (112, 136), (280, 147))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def rounded_sqrt(value):
    """Host sqrt proposes a result; exact rational midpoint bounds prove it."""
    candidate = bits(math.sqrt(value))
    center = Fraction(fp(candidate))
    lower = (Fraction(fp(candidate - 1)) + center) / 2
    upper = (Fraction(fp(candidate + 1)) + center) / 2
    assert lower * lower < Fraction(value) < upper * upper
    return fp(candidate)


def rng_sample(state, high):
    # Integer recurrence is read directly from the two loops in full5719.
    state = tuple(state)
    for draws in range(1, 10001):
        a, b, c, d = state
        rot = lambda x, n: ((x << n) | (x >> (32 - n))) & 0xffffffff
        output = (rot((a + d) & 0xffffffff, 7) + a) & 0xffffffff
        state = (a ^ b ^ d, a ^ b ^ c,
                 (a ^ c ^ (b << 9)) & 0xffffffff, rot(b ^ d, 11))
        value = f32(f32(fp((output >> 9) | 0x3f800000) - 1.) * high)
        if value < high:
            return value, state, draws
    raise AssertionError('Independent bounded sampler exhausted')


def atan_ref(value, tables):
    """Ordered f32 arithmetic transcribed independently from 35202 WAT."""
    raw = bits(value)
    magnitude = raw & 0x7fffffff
    if magnitude > 1283457023:
        return value if math.isnan(value) else fp(0xbfc90fda if raw >> 31 else 0x3fc90fda)
    if magnitude < 964689920:
        return value
    x = value
    index = None
    absolute = fp(magnitude)
    if magnitude >= 1054867456:
        if magnitude >= 1075576832:
            x, index = f32(-1. / absolute), 3
        elif magnitude >= 1066926080:
            x, index = f32(f32(absolute - 1.5) / f32(f32(absolute * 1.5) + 1.)), 2
        elif magnitude >= 1060110336:
            x, index = f32(f32(absolute - 1.) / f32(absolute + 1.)), 1
        else:
            x, index = f32(f32(f32(absolute + absolute) - 1.) / f32(absolute + 2.)), 0
    square = f32(x * x)
    fourth = f32(square * square)
    even = f32(fourth * f32(f32(fourth * fp(0xbdda1247)) + fp(0xbe4cca98)))
    odd = f32(square * f32(f32(fourth * f32(f32(fourth * fp(0x3d7cac25)) + fp(0x3e11f50d))) + fp(0x3eaaaaa9)))
    correction = f32(x * f32(even + odd))
    if index is None:
        return f32(x - correction)
    result = f32(tables[0][index] - f32(f32(correction - tables[1][index]) - x))
    return -result if raw >> 31 else result


def heading_ref(y, x, tables):
    # This review dynamically covers finite-coordinate fixtures only.
    assert math.isfinite(y) and math.isfinite(x)
    by, bx = bits(y), bits(x)
    if bx == 0x3f800000:
        return atan_ref(y, tables)
    quadrant = ((bx >> 30) & 2) | (by >> 31)
    ay, ax = by & 0x7fffffff, bx & 0x7fffffff
    if ay == 0:
        return fp(0x40490fdb) if quadrant == 2 else fp(0xc0490fdb) if quadrant == 3 else y
    if ax == 0 or ((ax + 218103808) & 0xffffffff) < ay:
        return fp(0xbfc90fdb if by >> 31 else 0x3fc90fdb)
    angle = 0. if (quadrant & 2 and ((ay + 218103808) & 0xffffffff) < ax) else atan_ref(abs(f32(y / x)), tables)
    if quadrant == 0:
        return angle
    if quadrant == 1:
        return -angle
    corrected = f32(angle + fp(0x33bbbd2e))
    return f32(fp(0x40490fdb) - corrected) if quadrant == 2 else f32(corrected + fp(0xc0490fdb))


def packed_guid(guid):
    raw = guid.to_bytes(8, 'little')
    return bytes([sum(1 << i for i, value in enumerate(raw) if value)]) + bytes(x for x in raw if x)


def packet169(guid, entry, display, scale, hp, position, heading, speeds):
    fields = {0: guid & 0xffffffff, 1: guid >> 32, 2: 9, 3: entry,
              4: bits(scale), 16: 0, 17: 0, 22: math.ceil(hp), 28: math.ceil(hp),
              34: 1, 35: 14, 36: 256, 46: 0, 126: 2000, 127: 2000,
              129: bits(f32(scale * .5)), 130: bits(f32(scale * 1.5)),
              131: display, 132: display, 134: bits(5.), 135: bits(10.), 145: bits(1.)}
    masks = [sum(1 << (key % 32) for key in fields if key // 32 == group) for group in range(5)]
    values = bytes([5]) + struct.pack('<5I', *masks) + struct.pack('<' + 'I' * len(fields), *(fields[key] for key in sorted(fields)))
    movement = bytes([3, 112]) + struct.pack('<2I', 0, 0) + struct.pack('<4I', *position, bits(heading))
    movement += struct.pack('<I6II', 0, *speeds, 1)
    return [169, (struct.pack('<IBB', 1, 0, 3) + packed_guid(guid) + movement + values).hex()]


def reference(case, definition, zone_scale, tables, speeds):
    words = struct.unpack('<18I', definition)
    entry, display = words[6:8]
    scale, hpbase, attackbase, speed, field52 = [fp(words[o // 4]) for o in [32, 40, 44, 48, 52]]
    hp = f32(f32(fp(0x409e6666) * hpbase) * zone_scale)
    attack = f32(f32(1.25 * attackbase) * rounded_sqrt(zone_scale))
    backing = [list(bytes.fromhex(row)) for row in case['initial_backing']] if case['initial_backing'] else [[None] * 432 for _ in range(4)]
    state, counter, packets = tuple(case['rng_words']), case['counter'], []
    stages, branches, draw_count = [], [], 0
    for index, position in enumerate(case['positions']):
        yaw, state, draws = rng_sample(state, fp(0x40c90fdb)); draw_count += draws
        jitter, state, draws = rng_sample(state, fp(0x3e99999a)); draw_count += draws
        counter = (counter + 1) & 0xffffffff
        guid = 0xf130000000000000 | ((entry & 0xffffff) << 24) | (counter & 0xffffff)
        # Separate a value buffer from its knownness: unwritten allocation bytes
        # never become known from either this temporary or captured raw memory.
        row = bytearray(432)
        def put(offset, value): struct.pack_into('<I', row, offset, value & 0xffffffff)
        for offset in [0, 8, 16, 344]: put(offset, 0)
        for offset in [40, 64, 244]: put(offset, 0xffffffff)
        struct.pack_into('<Q', row, 112, guid)
        struct.pack_into('<Q', row, 236, 4)
        assignments = {280: 0, 284: 5830904, 288: bits(hp), 292: bits(hp),
                       296: bits(attack), 300: bits(f32(field52 * fp(0x3f866666))),
                       304: bits(speed), 308: bits(f32(f32(scale * fp(0x3f99999a)) + fp(0x400ccccd))),
                       312: bits(scale), 340: 0, 348: bits(f32(0. + f32(jitter + 0.))),
                       352: bits(f32(speed * .5)), 404: bits(f32(yaw + 0.))}
        for offset, value in assignments.items(): put(offset, value)
        struct.pack_into('<3I', row, 316, *position)
        struct.pack_into('<3I', row, 328, *position)
        for start, size in WRITES: backing[index][start:start + size] = row[start:start + size]
        dy, dx = [f32(fp(case['player_xy'][i]) - fp(position[i])) for i in [1, 0]]
        heading = heading_ref(dy, dx, tables)
        packets.append(packet169(guid, entry, display, scale, hp, position, heading, speeds))
        branches.append(dict(case=case['id'], stage=index, dx_bits=bits(dx), dy_bits=bits(dy), heading_bits=bits(heading), zero_axis=dx == 0. or dy == 0.))
        stages.append(dict(success=True, guid=str(guid), counter=counter, rng_words=list(state), capacity=4,
                           count=index + 1, records432_cells=[list(x) for x in backing],
                           packets=list(packets), HP288_bits=bits(hp), attack296_bits=bits(attack)))
    return stages, branches, draw_count


def main():
    start = time.monotonic()
    assert sha(CASE / 'comparison.json') == COMPARISON_SHA
    assert sha(CASE / 'task-handoff.json') == HANDOFF_SHA
    assert sha(STATIC / 'proof.json') == PROOF_SHA
    assert sha(ROOT / 'scripts/review_combat139.py') == HELPER_SHA
    receipt = json.loads((CASE / 'comparison.json').read_text())
    handoff = json.loads((CASE / 'task-handoff.json').read_text())
    prepared = json.loads((CASE / 'prepared.json').read_text())
    proof = json.loads((STATIC / 'proof.json').read_text())
    manifest = json.loads((CASE / 'manifest.json').read_text())
    runtime = json.loads((CASE / 'runtime.json').read_text())
    assert receipt['source_before'] == receipt['source_after'] == prepared['source_before']
    assert len(handoff['owned_files']) == 9
    for name, digest in handoff['owned_files'].items(): assert sha(ROOT / name) == digest
    for name, digest in receipt['source_before'].items():
        assert sha(ROOT / name) == digest == sha(CASE / 'source-snapshot' / name)
    edges = local_closure(receipt['source_before'])
    assert edges == sorted(receipt['source_import_edges']) and len(edges) == 29
    assert len(receipt['source_before']) == 18
    for name, digest in receipt['artifacts'].items(): assert sha(CASE / name) == digest
    for name, digest in prepared['frozen'].items(): assert sha(CASE / name) == digest
    assert prepared['expected_before_original'] and not prepared['original_inputs_contain_expected']
    assert sha(SOURCE) == SOURCE_SHA
    raw = SOURCE.read_bytes(); original = parse_module(raw)
    changed = (CASE / manifest['module_file']).read_bytes(); modified = parse_module(changed)
    for left, right in zip(original['sections'], modified['sections']):
        assert left['kind'] == right['kind']
        if left['kind'] != 7: assert raw[left['start']:left['end']] == changed[right['start']:right['end']]
    assert len(original['sections']) == len(modified['sections'])
    assert modified['exports'] == original['exports'] + [('research139_spawn5719', 0, 5719), ('research139_spawn_stack0', 3, 0), ('research139_spawn_constructor1600', 0, 1600)]
    assert original['decl'][5719 - 882] == 2 and original['types'][2] == ('7f7f7f7f', '')
    assert original['types'][original['decl'][1600 - 882]] == ('7f7f7f', '')
    assert [dict(module=x['module'], name=x['name'], type_index=x['type_index']) for x in original['imports']] == manifest['original_imports']
    assert len(original['imports']) == 882
    def data(address, size):
        result = bytearray(size)
        for base, offset, count in original['data_segments']:
            if base is None: continue
            lo, hi = max(base, address), min(base + count, address + size)
            if lo < hi: result[lo - address:hi - address] = raw[offset + lo - base:offset + hi - base]
        return bytes(result)
    definition = data(5830904, 72)
    assert definition.hex() == receipt['data']['raw72_hex'] and u32(definition, 68) == 0
    zone = data(5871348, 152)
    assert (u32(zone, 64), u32(zone, 68), u32(zone, 136), u32(zone, 140)) == (5830904, 12, 1062333317, 0)
    assert data(u32(definition, 16), u32(definition, 20)) == b'Kobold Vermin'
    tables = [list(struct.unpack('<4f', data(address, 16))) for address in [14426512, 14426528, 14426544, 14426560]]
    speeds = list(struct.unpack('<6I', data(1593032, 24))); speeds[1] = 1088421888
    db = sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro', uri=True); db.row_factory = sqlite3.Row; db.execute('pragma query_only=on')
    static_functions, allocation_functions = [], []
    with (PROFILE / 'official-0.139.0-full.wat').open('rb') as stream:
        for key, record in proof['functions'].items():
            idx = int(key); loc = dict(db.execute('select * from functions where idx=?', (idx,)).fetchone())
            assert original['bodies'][idx] == (loc['body_start'], loc['body_end'])
            assert hashlib.sha256(raw[loc['body_start']:loc['body_end']]).hexdigest() == record['body_sha256']
            stream.seek(loc['wat_start']); text = stream.read(loc['wat_end'] - loc['wat_start'])
            assert hashlib.sha256(text).hexdigest() == record['wat_sha256'] == sha(STATIC / f'{idx}.wat')
            calls = [dict(q) for q in db.execute('select caller,callee,wat_offset,wat_line,instruction from calls where caller=?', (idx,))]
            assert calls == record['direct_calls']
            static_functions.append(dict(index=idx, body_sha256=record['body_sha256'], wat_sha256=record['wat_sha256'], calls=len(calls)))
        for idx in [57285, 108362, 1711]:
            loc = dict(db.execute('select * from functions where idx=?', (idx,)).fetchone())
            assert original['bodies'][idx] == (loc['body_start'], loc['body_end'])
            stream.seek(loc['wat_start']); text = stream.read(loc['wat_end'] - loc['wat_start'])
            allocation_functions.append(dict(index=idx, **loc, body_sha256=hashlib.sha256(raw[loc['body_start']:loc['body_end']]).hexdigest(),
                                             wat_sha256=hashlib.sha256(text).hexdigest(), wat=text.decode()))
    assert 'local.get 1\n            if' in allocation_functions[0]['wat']
    assert 'local.get 3\n            local.get 4\n            call 108362' in allocation_functions[0]['wat']
    assert 'local.get 0\n    call 1711' in allocation_functions[1]['wat']
    assert 'memory.fill' not in allocation_functions[2]['wat']
    body = (STATIC / '5719.wat').read_text()
    assert body.count('local.get 0\n') == 2 and not any(x in body for x in ['local.set 0\n', 'local.tee 0\n'])
    assert 'local.get 0\n        local.get 24\n        i64.store offset=8' in body
    assert 'i64.store\n      local.get 8\n      i32.const 16\n      i32.add\n      global.set 0\n      return' in body
    assert 'i32.const 432\n' in body and 'i32.store16 offset=425 align=1' in body
    assert 'call 66565' in body and 'i32.const 4\n' in (STATIC / '66565.wat').read_text()
    runner = (ROOT / 'scripts/run_npc_spawn139_fresh_oracle.mjs').read_text()
    assert 'research139_spawn_constructor1600(G,profile,V)' in runner and 'research139_spawn5719(O,G,0,P)' in runner
    assert 'const P=alloc(16),O=alloc(16)' in runner and 'snapshot' not in runner.replace('// Fresh1600 then four complete5719 calls; all882 imports denied, no snapshot.', '').split('snapshot_restores')[0]
    assert 'raw_games2592_hex' in runner and 'hostCount++;throw Error' in runner
    assert 'if(stack.value!==1048576)' in runner and 'stackChecks++' in runner
    cases = json.loads((CASE / 'inputs.json').read_text()); expected = json.loads((CASE / 'expected.json').read_text())
    actual = [json.loads(line) for line in (CASE / 'stdout.jsonl').read_text().splitlines()]
    assert len(cases) == len(expected) == len(actual) == 16
    known = unknown = unknown_nonzero = messages = raw_bytes = draws = 0
    branches, ids = [], set()
    modes = Counter()
    for case, want, got in zip(cases, expected, actual):
        assert case['id'] == want['id'] == got['id'] and case == want['input'] and case['id'] not in ids
        ids.add(case['id']); modes['caller_backing' if case['initial_backing'] else 'reserve0to4'] += 1
        assert set(case) == {'id', 'rng_words', 'counter', 'positions', 'initial_backing', 'player_xy'}
        assert len(case['positions']) == 4 and all(len(p) == 3 and all(math.isfinite(fp(v)) for v in p) for p in case['positions'])
        stages, detail, count = reference(case, definition, fp(u32(zone, 136)), tables, speeds)
        assert stages == want['expected'] and count == want['model_rng_draws']
        draws += count; branches.extend(detail)
        assert len(got['answers']) == len(got['raw_games2592_hex']) == 4 and got['stack_after'] == 1048576 and got['phase2587'] == 0
        for index, (stage, result, gamehex) in enumerate(zip(stages, got['answers'], got['raw_games2592_hex'])):
            assert {k: v for k, v in stage.items() if k != 'records432_cells'} == {k: v for k, v in result.items() if k != 'records432_hex'}
            assert len(result['records432_hex']) == 4
            for cells, rowhex in zip(stage['records432_cells'], result['records432_hex']):
                row = bytes.fromhex(rowhex); assert len(cells) == len(row) == 432
                for value, observed in zip(cells, row):
                    if value is None: unknown += 1; unknown_nonzero += observed != 0
                    else: known += 1; assert value == observed
            messages += len(result['packets'])
            game = bytes.fromhex(gamehex); assert len(game) == 2592; raw_bytes += len(game)
            assert u32(game, 1784) == 4 and u32(game, 1792) == index + 1 and u32(game, 1888) == index + 1
            assert u32(game, 2408) == stage['counter'] and list(struct.unpack_from('<4I', game, 1720)) == stage['rng_words']
            assert [u32(game, o) for o in [1416, 1420]] == case['player_xy']
            assert u32(game, 1432) == u32(game, 2540) == 1 and u32(game, 2352) == u32(game, 400) == 0
            assert u32(game, 2516) == 0x3f800000 and all(game[o] == 0 for o in [2582, 387, 2568, 2587])
    assert (known, unknown, unknown_nonzero, messages, raw_bytes) == (79536, 31056, 15028, 160, 165888)
    assert modes == {'caller_backing': 8, 'reserve0to4': 8}
    assert runtime == receipt['runtime'] and runtime['stack_checks'] == 184 and runtime['actual_host_calls'] == 0 and runtime['denied_imports'] == 882
    assert runtime['full5719_calls'] == 64 and runtime['fresh_instances'] == runtime['full1600_calls'] == 16
    assert runtime['snapshot_restores'] == 0 and not runtime['old_snapshot_loaded'] and not runtime['fullworldRc_produced']
    assert runtime['peak_memory_bytes'] == 20709376 and runtime['memory_cap_bytes'] == 33554432
    terminal = json.loads((CASE / 'process-terminal.json').read_text())
    assert terminal['exit_code'] == 0 and terminal['pid_missing'] and terminal['pgid_missing'] and terminal['seconds'] < 60
    for name in ['validator-terminal.json', 'fresh-validator-terminal.json']:
        value = json.loads((CASE / name).read_text()); assert value['exit_code'] == 0 and value['pid_missing'] and value['pgid_missing']
    assert (CASE / 'stderr.log').stat().st_size == 0 and json.loads((CASE / 'differences.json').read_text()) == []
    assert receipt['expected_before_original'] and receipt['snapshot_sha256'] is None and not receipt['model_rng_draws_observed_independently']
    assert sum(size for _, size in WRITES) == 303
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('npc-spawn139-independent-review-%Y%m%dT%H%M%S.%fZ'); out.mkdir()
    for function in allocation_functions:
        (out / f"{function['index']}.wat").write_text(function.pop('wat'))
    review = dict(status='pass_with_declared_controlled_SomeXYZ_time0_limits', reviewer='/root/self_buffs119_review', author='/root/stats138_review',
                  comparison_sha256=COMPARISON_SHA, author_handoff_sha256=HANDOFF_SHA, static_proof_sha256=PROOF_SHA, source_sha256=SOURCE_SHA,
                  script_sha256=sha(Path(__file__)), pure_review_helper_sha256=HELPER_SHA,
                  independent_reference='stdlib struct per-operation f32; independent xoshiro loops, exact-rational-checked sqrt, full WAT atan/atan2 tables,169 serialization and knownness overlay',
                  author_model_checker_builder_original_executions_by_reviewer=0, native_executions_by_reviewer=0,
                  independent_cases=16, full5719_captured_calls_checked=64, author_full1600_calls=16, independent_mismatches=0,
                  allocation_modes=dict(modes), record_known_bytes=known, record_unknown_bytes=unknown, observed_nonzero_unknown_bytes=unknown_nonzero,
                  unknowns_retained=True, bytes_written_per_active_record=303, unknown_padding_per_new_active_record=129,
                  packet_prefix_observations=messages, distinct_new169_messages=64, raw_game_observation_bytes=raw_bytes,
                  independent_reference_rng_draws=draws, original_rng_draw_count_directly_captured=False,
                  output_ABI=dict(size=16, tag_store='u64@0', guid_store='u64@8', param0_gets=2, param0_reassignments=0, whole_function_pinned=True),
                  source_closure=receipt['source_before'], source_import_edges=edges, frozen_production_sources=8,
                  fresh_static_functions=static_functions, current_definition72_sha256=hashlib.sha256(definition).hexdigest(),
                  reserve_allocation_functions=allocation_functions,
                  reserve_allocation_path='66565 computes max(2*oldcapacity,4);57285 oldcapacity0 bypasses realloc and calls108362(size1728,align8);108362 selects1711 allocator;no NPC-specific initialization before303B writes',
                  current_zone152_sha256=hashlib.sha256(zone).hexdigest(), heading_tables=[dict(address=a, hex=data(a,16).hex()) for a in [14426512,14426528,14426544,14426560]],
                  export_delta=modified['exports'][len(original['exports']):], nonexport_sections_byte_identical=True, all_original_callees_retained=True,
                  runtime=runtime, owned_process=terminal, heading_cases=branches,
                  artifact_hashes_as_read={p.name:sha(p) for p in CASE.iterdir() if p.is_file() and p.suffix != '.wasm'},
                  author_owned_files=handoff, seconds=time.monotonic()-start,
                  limitations=['Only SomeXYZ, Elwynn definition0, initialtime0, mode0,difficulty0,member1,level1. No8740,naturalplacement,realWorldRc,phase1/full1108 or native/fullgame acceptance.',
                               'Original1600 is a true constructor with explicit research profile and borrowed flat query view; this is not natural menu/App production.',
                               '64 complete5719 include all natural callees but no assertion every branch/callee was reached. Eight preallocated caller backings and eight real capacity0-to4 reserve cases only.',
                               'Raw2592B Game is observed; only declared inputs,counters,RNG,headers and phase were independently cross-checked. It is not a full Game knownness prediction.',
                               '184 stack guard successes are runner assertions plus aggregate output, not184 separately serialized per-call stack records.',
                               'Original RNG state is checked after every full entry; loop draw counts are independently recomputed but not separately captured from original.',
                               '160 packet occurrences are cumulative prefixes, exactly64 new169 producers. Unknown allocation padding remainsNone even when15028 raw observations are nonzero.',
                               'Prior restricted snapshot batches3+64+64 and previous legal east-only64 do not contribute to this16/64 acceptance; study total2595719 and32constructor calls remains historical.',
                               'Static helper/body/data checks do not establish nonfinite atan coverage or arbitrary NPC/difficulty/time behavior; no author negative guard is counted as an original case.',
                               'Artifact and output hashes recorded here bind bytes as read, not a retroactive pre-run freeze. Prepared receipt binds expected/input/module before original.'])
    save(out / 'review.json', review)
    print(json.dumps(dict(directory=str(out), review_sha256=sha(out/'review.json'), cases=16, calls=64, known=known, unknown=unknown, seconds=review['seconds'])), flush=True)


if __name__ == '__main__':
    main()
