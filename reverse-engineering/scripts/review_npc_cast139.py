#!/usr/bin/env python3
"""Read-only current139 sameGame naturalNPC/cast composition review."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import ast
import hashlib
import json
import sqlite3
import struct

import review_cast139 as C
from review_combat139 import sha, parse_module, local_closure, fp
from review_initial139 import default_stats, record, rng
from review_natural_npc139 import reference as natural_reference
from review_world_position139 import load_world

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'evidence/npc-cast139-oracle-20261102T050358.609241Z'
SOURCE = ROOT / 'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE = ROOT / 'evidence/wasm0139-profile-20261102T012426.951871Z'
COMPARISON = '5dc6b3586d2a8ffda83cadff7c79b980a10b5f8cccdb0f871131ec3f2ae5c6cb'
HANDOFF = '59ff3c653a57af91ab122f6e5490a323f5ed199e74c4e0d3207859e911bbdeeb'
SOURCE_SHA = '71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS = {
    'scripts/review_cast139.py': 'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b',
    'scripts/review_combat139.py': '158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
    'scripts/review_initial139.py': '86d33e69c361eef223ad3ef271b6fb987d170f4d94847c0c068148c56ebe6fbc',
    'scripts/review_natural_npc139.py': 'e14d0e0baa3f408380525a78c85ee068d5f5d4c52322e6dae20e76d8c1f4b665',
    'scripts/review_npc_spawn139.py': 'aa1c8a9d5ca4fe0363f97cbdad71f13ce00ebccf238fe89b213f354627ef5074',
    'scripts/review_world_position139.py': 'd842c619169a582ab8eb540cab2829233eb633bbd79d10ab674c50e71c92ab7e',
    'scripts/review_player_motion135.py': '8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2',
}
READS = Counter()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read(row, offset, width=4):
    values = row[offset:offset + width]
    assert len(values) == width and None not in values, ('independent_unknown_read', offset, width)
    READS[offset, width] += 1
    return int.from_bytes(bytes(values), 'little')


def position(row):
    duration = read(row, 344)
    if C.rational(duration) <= 0:
        return read(row, 328), read(row, 332)
    t = C.div(C.sub(0, read(row, 340)), duration)
    if C.rational(t) < 0:
        t = 0
    if C.rational(t) > 1:
        t = C.ONE
    return tuple(C.add(read(row, a), C.mul(C.sub(read(row, b), read(row, a)), t))
                 for a, b in ((316, 328), (320, 332)))


def insertion(values, key):
    result = []
    for value in values:
        at = len(result)
        while at and key(result[at - 1]) > key(value):
            at -= 1
        result.insert(at, value)
    return result


def cast_reference(rows, player, words, total, sets, owned, definition, derived):
    """Canonical cells are read directly; no opaque carrier is constructed."""
    square = C.mul(C.u(definition, 56), C.u(definition, 56))
    candidates = []
    for index, row in enumerate(rows):
        assert read(row, 40) == read(row, 64) == read(row, 244) == C.M
        assert read(row, 424, 1) == 0
        if read(row, 0) == 0 and C.le(C.distance(position(row), player[:2]), square):
            candidates.append(index)
    candidates = insertion(candidates, lambda i: C.totalkey(C.distance(position(rows[i]), player[:2])))
    # Default four normal NPCs use the <=20 stable insertion path. Only
    # priority2 and deferred3 are reachable in this specific composition.
    groups = [[], []]
    for i in candidates:
        groups[int(C.rational(read(rows[i], 380)) > 0)].append(i)
    near, far = [], []
    if groups[0]:
        anchor = position(rows[groups[0][0]])
        for i in groups[0]:
            (near if C.rational(C.distance(position(rows[i]), anchor)) <= 36 else far).append(i)
    near = insertion(near, lambda i: C.totalkey(read(rows[i], 288)))
    limit = C.u(definition, 64)
    limit = max(1, (limit + C.u(owned, 20) + C.u(owned, 60) + derived[1592]) & C.M) if limit else 1
    selected = (near + far + groups[1])[:limit]
    ids = [read(rows[i], 112, 8) for i in selected]
    spell = C.u(definition, 44)
    for values in sets:
        if spell not in values:
            values.append(spell)
    value = C.mul(C.mul(C.mul(C.mul(C.u(definition, 48), 0x3fb33333), C.u(owned, 12)),
                            C.u(owned, 52)), C.ONE)
    life = C.mul(derived[1536], C.u(owned, 72)) if C.rational(C.u(definition, 48)) > 0 else 0
    base = C.mul(derived[1540], C.add(value, life))
    for i in selected:
        word, words = C.nextword(words)
        random01 = C.mul(C.rounded(Fraction(word >> 8)), 0x33800000)
        critical = C.rational(C.add(0, derived[1548])) > C.rational(random01)
        amount = C.mul(base, derived[1552]) if critical else base
        row = rows[i]
        coefficient = C.ONE
        if C.rational(read(row, 148)) > 0:
            coefficient = C.add(coefficient, read(row, 144))
        term = read(row, 152) if C.rational(read(row, 156)) > 0 else (
            read(row, 160) if C.rational(read(row, 164)) > 0 else 0)
        coefficient = C.add(C.add(C.add(coefficient, term), read(row, 368)), 0)
        school = 0x3dcccccd if definition[85] & 254 == 2 and C.rational(read(row, 372)) > 0 else 0
        damage = C.mul(C.mul(amount, C.add(coefficient, school)), C.ONE)
        if C.rational(damage) <= 1:
            damage = C.ONE
        old = read(row, 288)
        new = C.sub(old, damage)
        assert C.rational(new) > 0, 'Lethal remains outside this composition'
        total = C.bits64(C.f64(total) + float(min(max(C.rational(old), 0), C.rational(damage))))
        row[288:292] = struct.pack('<I', new)
    return dict(success=int(bool(ids)), records432_cells=[list(row) for row in rows],
                rng_words=list(words), accounted_total_bits=str(total), spell_sets=[list(v) for v in sets],
                owned80_hex=owned.hex(), launch306_packets=[] if not ids else [[306, C.launch(0, spell, ids)]],
                player_xyz=list(player), phase2587=1), words, total, ids


def main():
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('npc-cast139-independent-review-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    assert sha(BATCH / 'comparison.json') == COMPARISON and sha(BATCH / 'task-handoff.json') == HANDOFF
    for name, digest in HELPERS.items():
        assert sha(ROOT / name) == digest
    comp = json.loads((BATCH / 'comparison.json').read_text())
    handoff = json.loads((BATCH / 'task-handoff.json').read_text())
    prepared = json.loads((BATCH / 'prepared.json').read_text())
    manifest = json.loads((BATCH / 'manifest.json').read_text())
    sources = comp['source_before']
    assert sources == comp['source_after'] == handoff['source_closure'] == prepared['source_before']
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest == sha(BATCH / 'source-snapshot' / name)
    for name, digest in handoff['files'].items():
        assert sha(ROOT / name) == digest
    edges = local_closure(sources)
    assert edges == sorted(comp['source_import_edges'])
    assert len(sources) == 36 and sum(p.startswith('reconstruction/') for p in sources) == 26
    adapter = ast.parse((ROOT / 'reconstruction/core_spec/cast_cells139.py').read_text())
    adapter_reads = next(ast.literal_eval(n.value) for n in adapter.body
                         if isinstance(n, ast.Assign) and n.targets[0].id == 'READ32')
    assert adapter_reads == (0,40,64,144,148,152,156,160,164,244,288,316,320,328,332,340,344,368,372,380,416,420)
    assert prepared['expected_before_original'] and not prepared['input_contains_expected']
    for name, digest in prepared['frozen'].items():
        assert sha(BATCH / name) == digest
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    original = parse_module(raw)
    private = (BATCH / manifest['module_file']).read_bytes()
    assert hashlib.sha256(private).hexdigest() == manifest['module_sha256']
    modified = parse_module(private)
    assert len(original['imports']) == 882
    assert modified['exports'] == original['exports'] + [
        ('research139_spawn5719', 0, 5719), ('research139_npc_cast922', 0, 922), ('research139_spawn_stack0', 3, 0)]
    for a, b in zip(original['sections'], modified['sections'], strict=True):
        assert a['kind'] == b['kind']
        if a['kind'] != 7:
            assert raw[a['start']:a['end']] == private[b['start']:b['end']]
    functions = {}
    with sqlite3.connect((PROFILE / 'index.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db, (PROFILE / 'official-0.139.0-full.wat').open('rb') as wat:
        for key, proof in manifest['functions'].items():
            i = int(key)
            a, b = original['bodies'][i]
            assert hashlib.sha256(raw[a:b]).hexdigest() == proof['body_sha256']
            start, end = db.execute('select wat_start,wat_end from functions where idx=?', (i,)).fetchone()
            wat.seek(start)
            block = wat.read(end - start)
            assert block == (BATCH / 'static' / (key + '.wat')).read_bytes()
            assert hashlib.sha256(block).hexdigest() == proof['WAT_sha256']
            functions[key] = proof
    def data(address, size):
        result = bytearray(size)
        for base, pos, count in original['data_segments']:
            if base is None:
                continue
            low, high = max(base, address), min(base + count, address + size)
            if low < high:
                result[low - address:high - address] = raw[pos + low - base:pos + high - base]
        return bytes(result)
    definition = data(5882740, 88)
    assert definition.hex() == manifest['definition']['raw88_hex']
    classdata, racedata = data(5877920, 108), data(5874636, 44)
    ptr, count = struct.unpack_from('<II', racedata, 16)
    racemods = list(struct.iter_unpack('<II', data(ptr, count * 8)))
    derived, _, _, _ = default_stats(struct.unpack_from('<II', classdata, 72), racemods)
    tables = [list(struct.unpack('<4f', data(p, 16))) for p in (14426512, 14426528, 14426544, 14426560)]
    speeds = list(struct.unpack('<6I', data(1593032, 24)))
    speeds[1] = 1088421888
    npc_def = data(5830904, 72)
    world, nav, scalars = load_world(comp['world_provenance'])
    cx, cy = scalars['center_xy_bits']
    height = world.height(cx, cy)
    assert type(height) is int
    # The frozen pure World.height returns the exact value bits directly.
    initial_player = [cx, cy, height]
    seed = 1442695040888963407
    constructor_words = rng(seed)
    actor = dict(derived_bits={str(k): v for k, v in derived.items()}, owned80_hex=record(5882740),
                 initial_rng=constructor_words, player_xyz=initial_player, phase2587=0, source_id='0')
    cases = json.loads((BATCH / 'inputs.json').read_text())
    expected = json.loads((BATCH / 'expected.json').read_text())
    actual = [json.loads(line) for line in (BATCH / 'stdout.jsonl').read_text().splitlines()]
    assert len(cases) == len(expected) == len(actual) == 8
    counter = Counter()
    ref, details = [], []
    def compare_rows(cells, rawhex, previous=None):
        assert len(cells) == len(rawhex) == 4
        for index, (row, hx) in enumerate(zip(cells, rawhex, strict=True)):
            value = bytes.fromhex(hx)
            assert len(value) == len(row) == 432
            prior = None if previous is None else bytes.fromhex(previous[index])
            for offset, known in enumerate(row):
                if known is None:
                    counter['None'] += 1
                    counter['nonzero_None'] += value[offset] != 0
                    if prior is not None:
                        assert prior[offset] == value[offset]
                        counter['opaque_conserved'] += 1
                else:
                    assert known == value[offset], ('unit_byte', index, offset)
                    counter['known'] += 1
    allowed = set(range(1720, 1736)) | set(range(1784, 1796)) | set(range(1880, 1892)) | set(range(2408, 2412))
    for case, e, a in zip(cases, expected, actual, strict=True):
        assert case['id'] == e['id'] == a['id']
        words = constructor_words if case['rng_words'] is None else case['rng_words']
        state = dict(id=case['id'], rng_words=words, counter=case['counter'], player_xyz=initial_player,
                     velocity_xy=[0, 0], initial_backing=case['initial_backing'], distance_map=None)
        npc, diagnostic = natural_reference(state, world, nav, scalars, tables, npc_def, speeds)
        assert npc == e['npc_answers']
        assert actor == e['actor_before'] == a['actor_before']
        assert a['constructor_rng_before'] == constructor_words and a['constructor_counter_before'] == 10
        assert int(a['App4928_after_controlled_seed0_LCG']) == seed
        assert a['preserve_constructor_rng'] == (case['rng_words'] is None)
        previous_game = bytes.fromhex(a['declared_game_before_hex'])
        for j, (p, got) in enumerate(zip(npc, a['answers'], strict=True)):
            compare_rows(p['records432_cells'], got['records432_hex'])
            assert {k: v for k, v in p.items() if k != 'records432_cells'} == {k: v for k, v in got.items() if k != 'records432_hex'}
            rawgame = a['raw_games2592'][j]
            before, after = bytes.fromhex(rawgame['before_hex']), bytes.fromhex(rawgame['after_hex'])
            assert len(before) == len(after) == 2592
            assert before == previous_game, 'NPC rawGame continuation'
            previous_game = after
            changed = [i for i, (v, w) in enumerate(zip(before, after)) if v != w]
            assert changed == rawgame['changed_bytes'] and set(changed) <= allowed
            counter['NPC_Game_constant_bytes'] += 2592 - len(allowed)
        rows = [list(row) for row in npc[-1]['records432_cells']]
        player = initial_player
        if case['action'] != 'keep_start':
            row = rows[0 if case['action'] == 'near_first' else 1]
            player = [read(row, offset) for offset in (316, 320, 324)]
        owned = bytearray.fromhex(actor['owned80_hex'])
        if case['gentle_owned_multiplier']:
            struct.pack_into('<I', owned, 12, 0x3dcccccd)
        words, total, sets = tuple(npc[-1]['rng_words']), 0, [[], [], []]
        previous = a['answers'][-1]['records432_hex']
        stages = []
        assert len(a['cast_stages']) == len(e['stages']) == case['repeats']
        for stage in range(case['repeats']):
            old_words, old_total, old_sets = tuple(words), total, [list(v) for v in sets]
            p, words, total, selected = cast_reference(rows, player, words, total, sets, owned, definition, derived)
            got = a['cast_stages'][stage]
            assert p == e['stages'][stage]
            compare_rows(p['records432_cells'], got['records432_hex'], previous)
            assert {k: v for k, v in p.items() if k != 'records432_cells'} == {k: v for k, v in got.items() if k != 'records432_hex'}
            previous = got['records432_hex']
            counter['cast_calls'] += 1
            counter['selected_hits'] += len(selected)
            for _, packet in p['launch306_packets']:
                decoded = C.decode306(packet)
                assert decoded['targets'] == selected
                counter['new306'] += 1
                counter['306_bytes'] += decoded['bytes']
            g = a['cast_raw_games'][stage]
            before, after = bytes.fromhex(g['before_hex']), bytes.fromhex(g['after_hex'])
            assert len(before) == len(after) == 2592
            if stage == 0:
                action_writes = set(range(1416, 1428)) | {2587}
                assert all(v == w for offset, (v, w) in enumerate(zip(previous_game, before))
                           if offset not in action_writes), 'Scripted action changed unexpected Game byte'
                counter['first_cast_inherited_Game_bytes'] += 2592 - len(action_writes)
            else:
                assert before == previous_game, 'Cast rawGame continuation'
                counter['later_cast_inherited_Game_bytes'] += 2592
            previous_game = after
            assert C.q(before, 984) == old_total
            assert [C.u(before, 1720 + 4 * k) for k in range(4)] == list(old_words)
            assert [C.u(before, count) for count in (672, 684, 732)] == [len(v) for v in old_sets]
            assert C.u(before, 1788) == C.u(after, 1788) and C.u(before, 1792) == C.u(after, 1792) == 4
            assert [C.u(after, count) for count in (672, 684, 732)] == [len(v) for v in sets]
            assert C.q(after, 984) == total and after[2587] == 1
            assert [C.u(after, 1720 + 4 * k) for k in range(4)] == list(words)
            assert [C.u(before, 1416 + 4 * k) for k in range(3)] == player
            assert C.u(before, 2032) == C.u(before, 2056) == C.u(before, 1972) == 0
            stages.append(p)
        assert e['unknowns_preserved'] and e['model_private_completion_runs'] == 2 * case['repeats']
        assert a['option16_hex'] == '00000000' + 'a5' * 12
        assert a['option_canaries'] == a['result_canaries'] == ['c3' * 16, 'd7' * 16]
        assert a['world124_before_hex'] == a['world124_after_hex'] and a['world_data_digest_before'] == a['world_data_digest_after']
        assert a['path_view'] is None and a['stack_after'] == 1048576
        counter['NPC_calls'] += 4
        ref.append(dict(id=case['id'], npc_answers=npc, actor_before=actor, stages=stages))
        details.append(dict(id=case['id'], position_diagnostics_are_model_only=diagnostic))
    assert counter['known'] == 58824 and counter['None'] == 31032 and counter['nonzero_None'] == 14664
    assert counter['opaque_conserved'] == 7740 and counter['cast_calls'] == 20 and counter['NPC_calls'] == 32
    assert all((width == 4 and (offset in adapter_reads or offset == 324))
               or (offset, width) in ((112, 8), (424, 1)) for offset, width in READS)
    runtime = json.loads((BATCH / 'runtime.json').read_text())
    terminal = json.loads((BATCH / 'owned-terminal.json').read_text())
    assert runtime == comp['runtime'] and terminal == comp['process']
    assert runtime['snapshot_restores'] == 8 and runtime['denied_imports'] == 882 and runtime['actual_host_calls'] == 0
    assert runtime['full5719_calls'] == 32 and runtime['full922_calls'] == 20
    assert runtime['stack_checks'] == runtime['allocator_calls'] + 52 == 70
    assert terminal['exit_code'] == 0 and terminal['pid_missing'] and terminal['pgid_missing']
    assert all(sha(ROOT / name) == digest for name, digest in sources.items())
    assert all(sha(ROOT / name) == digest for name, digest in handoff['files'].items())
    save(out / 'independent-reference.json', ref)
    save(out / 'diagnostics.json', details)
    receipt = dict(status='accepted_scoped_composition', review_script_sha256=sha(__file__), comparison_sha256=COMPARISON,
        author_handoff_sha256=HANDOFF, author_files_untouched=True, original_executions=0,
        author_production_checker_builder_executions=0, all_original_output_read=True,
        source_count=len(sources), production_source_count=sum(p.startswith('reconstruction/') for p in sources),
        import_edges=len(edges), sources=sources, helpers=HELPERS, current_functions=functions,
        counters=dict(counter), canonical_read_ranges=[dict(offset=o, width=n, reads=count) for (o, n), count in sorted(READS.items())],
        reference_sha256=sha(out / 'independent-reference.json'), diagnostics_sha256=sha(out / 'diagnostics.json'),
        artifacts_as_read={p.name: sha(p) for p in BATCH.iterdir() if p.is_file() and p.suffix != '.wasm'},
        original_output_hashes_were_not_in_author_comparison=True,
        private_carriers_executed_by_reviewer=False, no_opaque_None_materialization=True,
        current_runtime_is_original_runner_observation=True, stack70_is_original_runner_aggregate=True,
        limitations=['8 restored healthy-v2 consumer fixtures,not fresh1600/6786/1108 or naturalApp.',
                     'PlayerXYZ relocation andphase1 are explicit inputs,not AI/input/motion.',
                     'Four gentle fixtures setowned multiplier0.1 for repeats;default secondlethal remains pending.',
                     'Complete306 andknown432bytes are predicted;other592/169,physical Game/container state remain observations.',
                     'Independent canonicalreader usesNone-aware reads directly;author A5/5A carriers are modelselfchecks only.',
                     'Author comparison binds pre-runartifacts but not post-runstdout/runtime;review pins current bytes asread without retrofreezing.'])
    save(out / 'review.json', receipt)
    print(str(out))
    print(sha(out / 'review.json'))
    print(json.dumps(dict(counter)))


if __name__ == '__main__':
    main()
