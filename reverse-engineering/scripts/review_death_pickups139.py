#!/usr/bin/env python3
"""Independent read-only139 XP/coin1446 reference and whole43 review."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sqlite3
import struct

import review_cast139 as C
from review_combat139 import sha, parse_module, local_closure, fp, bits, f32
from review_world_position139 import load_world, hypot_ref, trig

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'evidence/death-pickups139-oracle-20261102T051256.926584Z'
SOURCE = ROOT / 'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE = ROOT / 'evidence/wasm0139-profile-20261102T012426.951871Z'
COMPARISON = '0ebed7dbfd74f9d2f85be62eb91cf1449b5ecbf841123c44fd6c5db3b7fdcf47'
HANDOFF = '9580c57aa935fb7cd98c7c853ec398294584c64b7921715226dd92df68c60b97'
SOURCE_SHA = '71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS = {'scripts/review_cast139.py': 'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b',
           'scripts/review_combat139.py': '158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
           'scripts/review_world_position139.py': 'd842c619169a582ab8eb540cab2829233eb633bbd79d10ab674c50e71c92ab7e',
           'scripts/review_player_motion135.py': '8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2',
           'scripts/review_npc_spawn139.py': 'aa1c8a9d5ca4fe0363f97cbdad71f13ce00ebccf238fe89b213f354627ef5074'}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def values_payload(fields):
    keys = sorted(fields)
    count = keys[-1] // 32 + 1
    mask = [sum(1 << (k % 32) for k in keys if k // 32 == group) for group in range(count)]
    return bytes([count]) + struct.pack('<' + 'I' * count, *mask) + b''.join(struct.pack('<I', fields[k]) for k in keys)


def geometry(c, world, scalars):
    x, y = c['xyz'][:2]
    cx, cy = scalars['center_xy_bits']
    dx, dy = C.sub(x, cx), C.sub(y, cy)
    distance = bits(hypot_ref(fp(dx), fp(dy)))
    limit = C.add(scalars['radius_bits'], 0xc0000000)
    if C.rational(limit) < 1:
        limit = C.ONE
    clamped = C.rational(distance) > C.rational(limit)
    if clamped:
        x = C.add(cx, C.mul(C.div(dx, distance), limit))
        y = C.add(cy, C.mul(C.div(dy, distance), limit))
    height = world.height(x, y)
    assert not scalars['primary_present']
    return [x, y, scalars['fallback_height_bits'] if height is None else height], clamped


def reference(c, world, scalars, speeds):
    kind, amount = c['kind'], c['amount']
    assert kind in (0, 1)
    rows = [list(bytes.fromhex(hx)) for hx in c['initial_backing']]
    count = c['initial_count']
    assert 0 <= count <= len(rows)
    placed, clamped = geometry(c, world, scalars)
    counter, words = c['counter'], tuple(c['rng_words'])
    packets, fields = [], None
    idle = [i for i, row in enumerate(rows[:count]) if C.u(bytes(row), 8) == 0 and C.u(bytes(row), 0) == 0]
    # Admitted caller markers are0/1. Current1446 sums(kind==0 ? marker^1 :0).
    assert all(C.u(bytes(row), 0) in (0, 1) for row in rows[:count])
    merged = None
    guid = None
    draws = 0
    if kind == 0 and len(idle) >= 45:
        def distance(i):
            row = bytes(rows[i])
            return C.distance((C.u(row, 40), C.u(row, 44)), placed[:2])
        merged = idle[0]
        for index in idle[1:]:
            if C.totalkey(distance(index)) < C.totalkey(distance(merged)):
                merged = index
        old = C.u(bytes(rows[merged]), 12)
        rows[merged][12:16] = struct.pack('<I', (old + amount) & C.M)
    else:
        counter = (counter + 1) & C.M
        if kind == 0:
            guid = 0xf130002329000000 | (counter & 0xffffff)
            if amount >= 20:
                scale, display = 0x3f666666, 16587
            elif amount >= 4:
                scale, display = 0x3eb33333, 1825
            else:
                scale, display = 0x3e6147ae, 1825
            fields = {0: guid & C.M, 1: guid >> 32, 2: 9, 3: 9001, 4: scale,
                      22: 1, 28: 1, 34: 1, 35: 35, 46: 33554434,
                      129: 1036831949, 130: 1036831949, 131: display, 132: display}
            packet = (b'\x01\x00\x00\x00\x00\x03' + C.packguid(guid) + b'\x03\x70'
                      + bytes(8) + struct.pack('<4I', *placed, 0) + bytes(4)
                      + struct.pack('<6I', *speeds) + struct.pack('<I', 1) + values_payload(fields))
            visual = 9001
        else:
            guid = 0xf110000000000000 | (9004 << 24) | (counter & 0xffffff)
            while True:
                word, words = C.nextword(words)
                draws += 1
                assert draws <= 10000
                unit = C.sub((word >> 9) | C.ONE, C.ONE)
                yaw = C.mul(unit, 0x40c90fdb)
                if C.rational(yaw) < C.rational(0x40c90fdb):
                    break
            half = C.mul(yaw, 0x3f000000)
            sine, cosine = trig(fp(half))
            fields = {0: guid & C.M, 1: guid >> 32, 2: 33, 3: 9004, 4: 0x3f19999a,
                      8: 2614, 9: 0, 12: bits(sine), 13: bits(cosine), 14: 1,
                      15: placed[0], 16: placed[1], 17: placed[2], 18: yaw, 20: 35, 21: 5}
            packet = (b'\x01\x00\x00\x00\x00\x02' + C.packguid(guid) + b'\x05\x50'
                      + struct.pack('<4I', *placed, yaw) + struct.pack('<I', 1) + values_payload(fields))
            visual = 9004
        packets = [[169, packet.hex()]]
        if count == len(rows):
            rows.extend([[None] * 56 for _ in range(max(4, 2 * len(rows)) - len(rows))])
        row = rows[count]
        row[0:4] = bytes(4)
        row[8:24] = struct.pack('<IIQ', kind, amount, guid)
        row[24:40] = struct.pack('<4I', 0, 8, 0, visual)
        row[40:56] = struct.pack('<4I', *placed, c['now_bits'])
        count += 1
    return (dict(capacity=len(rows), count=count, storage56_cells=rows, counter=counter,
                 rng_words=list(words), packets=packets),
            dict(position_bits=placed, clamped=clamped, merged_index=merged, guid=None if guid is None else str(guid),
                 RNG_draws_model_only=draws, fields=fields))


def main():
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('death-pickups139-independent-review-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    assert sha(BATCH / 'comparison.json') == COMPARISON and sha(BATCH / 'task-handoff.json') == HANDOFF
    for name, digest in HELPERS.items():
        assert sha(ROOT / name) == digest
    comp = json.loads((BATCH / 'comparison.json').read_text())
    handoff = json.loads((BATCH / 'task-handoff.json').read_text())
    prep = json.loads((BATCH / 'prepared.json').read_text())
    manifest = json.loads((BATCH / 'manifest.json').read_text())
    sources = comp['source_before']
    assert sources == comp['source_after'] == prep['source_before']
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest == sha(BATCH / 'source-snapshot' / name)
    for name, digest in handoff['frozen_author_files'].items():
        assert sha(ROOT / name) == digest
    edges = local_closure(sources)
    assert edges == sorted(comp['source_import_edges'])
    assert len(sources) == 23 and sum(n.startswith('reconstruction/') for n in sources) == 13 and len(edges) == 44
    for name, digest in comp['artifacts'].items():
        assert sha(BATCH / name) == digest
    for name, digest in prep['frozen'].items():
        assert sha(BATCH / name) == digest
    assert prep['expected_before_original'] and not prep['original_inputs_contain_expected']
    assert comp['expectation_reads_forbidden'] == [] and comp['old_badcontext_loaded'] is False
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    original = parse_module(raw)
    private = (BATCH / manifest['module_file']).read_bytes()
    assert hashlib.sha256(private).hexdigest() == manifest['module_sha256']
    changed = parse_module(private)
    assert len(original['imports']) == 882
    assert changed['exports'] == original['exports'] + [('research139_drop1446', 0, 1446), ('research139_drop_stack0', 3, 0)]
    for a, b in zip(original['sections'], changed['sections'], strict=True):
        assert a['kind'] == b['kind']
        if a['kind'] != 7:
            assert raw[a['start']:a['end']] == private[b['start']:b['end']]
    bodies, texts = {}, {}
    with sqlite3.connect((PROFILE / 'index.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db, (PROFILE / 'official-0.139.0-full.wat').open('rb') as wat:
        for key, proof in manifest['functions'].items():
            a, b = original['bodies'][int(key)]
            assert hashlib.sha256(raw[a:b]).hexdigest() == proof['body_sha256']
            start, end = db.execute('select wat_start,wat_end from functions where idx=?', (int(key),)).fetchone()
            wat.seek(start)
            text = wat.read(end - start)
            assert text == (BATCH / 'static' / (key + '.wat')).read_bytes()
            assert hashlib.sha256(text).hexdigest() == proof['WAT_sha256']
            bodies[key], texts[int(key)] = proof, text.decode()
    assert original['types'][original['decl'][1446 - 882]] == ('7f7f7f7f', '')
    assert 'i32.const 45' in texts[1446] and 'i32.gt_s\n                                select' in texts[1446]
    assert texts[1446].index('f32.const 0x1.ccccccp-1') > texts[1446].index('i32.const 19')
    assert 'i32.const 8\n    i32.const 56\n    call 57285' in texts[66558]
    assert 'call 11425' in texts[1886] and 'call 11499' in texts[1886]
    assert 'i32.const 9\n      i32.shr_u' in texts[1886]
    assert struct.unpack('<II', struct.pack('<Q', 4546834185511242294)) == (2614, 0x3f19999a)
    assert (-1067352960675086336) & ((1 << 64) - 1) == 0xf130002329000000
    assert (-1076360310941548544) & ((1 << 64) - 1) == 0xf110000000000000
    def data(address, size):
        value = bytearray(size)
        for base, pos, count in original['data_segments']:
            if base is None:
                continue
            low, high = max(base, address), min(base + count, address + size)
            if low < high:
                value[low - address:high - address] = raw[pos + low - base:pos + high - base]
        return bytes(value)
    speeds = struct.unpack('<6I', data(1593032, 24))
    assert struct.pack('<6I', *speeds).hex() == manifest['XP_speeds_hex']
    world, _, scalars = load_world(comp['world_provenance'])
    assert list(struct.unpack('<2I', data(5871452, 8))) == scalars['center_xy_bits']
    assert C.u(data(5871468, 4)) == scalars['radius_bits'] and not scalars['primary_present']
    inputs = json.loads((BATCH / 'inputs.json').read_text())
    expected = json.loads((BATCH / 'expected.json').read_text())
    actual = [json.loads(s) for s in (BATCH / 'stdout.jsonl').read_text().splitlines()]
    assert len(inputs) == len(expected) == len(actual) == 43
    counter, groups = Counter(), Counter()
    refs, diagnostics = [], []
    allowed = set(range(1720, 1736)) | set(range(1868, 1892)) | set(range(2408, 2412))
    for c, e, a in zip(inputs, expected, actual, strict=True):
        assert c['id'] == e['id'] == a['id'] and c == e['input']
        projection, diag = reference(c, world, scalars, speeds)
        assert projection == e['expected'], ('stored_expected', c['id'])
        got = a['projection']
        assert {k: v for k, v in projection.items() if k != 'storage56_cells'} == {k: v for k, v in got.items() if k != 'storage56_hex'}, ('actual', c['id'])
        for row, hx in zip(projection['storage56_cells'], got['storage56_hex'], strict=True):
            value = bytes.fromhex(hx)
            assert len(value) == len(row) == 56
            for known, observed in zip(row, value, strict=True):
                if known is None:
                    counter['None'] += 1
                    counter['nonzero_None'] += observed != 0
                else:
                    assert known == observed, ('raw56', c['id'])
                    counter['known'] += 1
        before, after = bytes.fromhex(a['raw_game_before_hex']), bytes.fromhex(a['raw_game_after_hex'])
        assert len(before) == len(after) == 2592
        changed_bytes = [i for i, (v, w) in enumerate(zip(before, after)) if v != w]
        assert changed_bytes == a['changed_bytes'] and set(changed_bytes) <= allowed
        assert [C.u(before, 1720 + 4 * i) for i in range(4)] == c['rng_words']
        assert [C.u(after, 1720 + 4 * i) for i in range(4)] == projection['rng_words']
        assert C.u(before, 2408) == c['counter'] and C.u(after, 2408) == projection['counter']
        assert C.u(before, 1868) == len(c['initial_backing']) and C.u(before, 1876) == c['initial_count']
        assert C.u(after, 1868) == projection['capacity'] and C.u(after, 1876) == projection['count']
        assert C.u(before, 1888) == 0 and C.u(after, 1888) == len(projection['packets'])
        assert a['input12_hex'] == struct.pack('<3I', *c['xyz']).hex()
        assert a['canaries'] == ['c3' * 16, 'd7' * 16]
        assert a['world_source_ranges'] == 2318 and a['world_source_bytes'] == 5950608
        assert a['world_digest_before'] == a['world_digest_after'] and a['stack_after'] == 1048576
        groups[e['group']] += 1
        counter['kind' + str(c['kind'])] += 1
        counter['clamped'] += diag['clamped']
        counter['merged'] += diag['merged_index'] is not None
        counter['new169'] += len(projection['packets'])
        counter['169_bytes'] += sum(len(bytes.fromhex(hx)) for _, hx in projection['packets'])
        counter['nonowned_Game_bytes'] += 2592 - len(allowed)
        refs.append(dict(id=c['id'], expected=projection))
        diagnostics.append(dict(id=c['id'], **diag))
    assert counter['known'] == 17996 and counter['None'] == 8884 and counter['nonzero_None'] == 6205
    assert counter['merged'] == 3 and counter['new169'] == 40 and counter['169_bytes'] == 5052
    terminal = json.loads((BATCH / 'process-terminal.json').read_text())
    runtime = json.loads((BATCH / 'runtime.json').read_text())
    assert terminal == comp['process'] and terminal['exit_code'] == 0 and terminal['pid_missing'] and terminal['pgid_missing']
    assert runtime == comp['runtime'] and runtime['cases'] == runtime['full1446_calls'] == runtime['snapshot_restores'] == 43
    assert runtime['denied_imports'] == 882 and runtime['actual_host_calls'] == 0 and runtime['stack_checks'] == 108 == runtime['allocations'] + 43
    assert all(sha(ROOT / name) == digest for name, digest in sources.items())
    assert all(sha(ROOT / name) == digest for name, digest in handoff['frozen_author_files'].items())
    history = []
    for directory, digest, cases, differences in (
        ('death-pickups139-oracle-20261102T051123.365745Z', '85d316262e34da20b328f685c7b002c3a8fcf3acd9b382a57022e3cbc74b7d1f', 2, 0),
        ('death-pickups139-oracle-20261102T051141.724383Z', 'abf7125af13f18bc802546eaf16d4ea3956ba5c1f880e7a156039dc2121c597e', 43, 5)):
        prior = ROOT / 'evidence' / directory
        assert sha(prior / 'comparison.json') == digest
        record = json.loads((prior / 'comparison.json').read_text())
        assert record['cases'] == cases and record['differences'] == differences
        history.append(dict(directory=directory, comparison_sha256=digest, full1446_calls=cases, differences=differences, counted_in_current_coverage=False))
    failed = ROOT / 'evidence/death-pickups139-oracle-20261102T051141.724383Z'
    old_source = failed / 'source-snapshot/reconstruction/core_spec/death_pickups139.py'
    assert sha(old_source) == '4059122cdd83a60364af6b112c0668faf6de17722e42918b8ed46705bc7bbf7e'
    old_diffs = json.loads((failed / 'differences.json').read_text())
    assert len(old_diffs) == 5 and all(d['field'] == 'packets' for d in old_diffs)
    save(out / 'independent-reference.json', refs)
    save(out / 'independent-diagnostics.json', diagnostics)
    result = dict(status='accepted_scoped_kind0XP_kind1currency', version='0.139.0', build='f79c5e2b4',
                  review_script_sha256=sha(__file__), original_executions=0, author_production_checker_builder_executions=0,
                  comparison_sha256=COMPARISON, handoff_sha256=HANDOFF, counters=dict(counter), groups=dict(groups),
                  source_count=len(sources), production_source_count=13, import_edges=len(edges), sources=sources, helpers=HELPERS,
                  current_functions=bodies, history=history, original_study_calls_including_pilot_failure=88, independent_reference_sha256=sha(out / 'independent-reference.json'),
                  diagnostics_sha256=sha(out / 'independent-diagnostics.json'),
                  postrun_artifacts_bound_by_author_comparison=comp['artifacts'],
                  runtime_inline_bound_and_as_read_sha256=sha(BATCH / 'runtime.json'),
                  stack108_is_runner_aggregate=True, author_sources_unchanged=True,
                  unknowns=['43 healthyv2 snapshot restores,not fresh constructor/world owners.',
                            'Only kind0/1 defaultElwynn/no-primary finite-coordinate domain.',
                            'No full913 death or XPpickup consumption/progression acceptance.',
                            "Eachnew56record retains4unwrittenbytes asNone;newinactive backing isnot zero-filled.",
                            'Exact packet projection predicts logicalBTree values,not itsphysicalallocation topology.',
                            'Draws/mergeindex/placedposition diagnostics are independentlyinferred,not extra original counters.',
                            'runtime JSON separately unhashed inauthor artifactlist;its content iscomparison-inline bound andcurrentSHA pinned byreview.',
                            'Pythonopen audit isnot OSsyscall proof;native/fullgame0.'])
    save(out / 'review.json', result)
    print(str(out))
    print(sha(out / 'review.json'))
    print(json.dumps(dict(counter)))


if __name__ == '__main__':
    main()
