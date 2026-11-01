#!/usr/bin/env python3
"""None-aware AI/corpse migration: frozen default cases and pure-model guards.

Unknown rows never enter an original runtime. Original921 receives only the
preexisting complete hex fixtures, without expanding its admitted source domain.
"""
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.ai135 import AiFrame135, update_ordinary_units
from core_spec.ai_lifecycle135 import cleanup_ordinary_corpses
from core_spec.incoming135 import input_from_dict
from core_spec.record_cells135 import (cells135, u32, i32, u64, put_u32,
    put_u64, encode_row, known_bytes, optional_u32, optional_u64,
    UnknownRecordRead135)

AI_BASE = ROOT / 'evidence/full0135-oracle-20261101T044817.224194Z'
CORPSE_BASE = ROOT / 'evidence/full0135-oracle-20261101T060633.862339Z'
RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
FIELDS = ('armor_1392_bits', 'armor_cap_1572_bits', 'nearby_reduction_1444_bits',
    'hp_1528_bits', 'shield_1532_bits', 'barrier_1536_bits', 'shield_source_1344',
    'shield_source_remaining_1348_bits', 'reserve_768_bits', 'absorbed_740_bits',
    'maximum_shield_744_bits', 'last_hit_1648_bits')


def loaded_baselines():
    ai_receipt = json.loads((AI_BASE / 'ai135-comparison.json').read_text())
    corpse_receipt = json.loads((CORPSE_BASE / 'player-update135-comparison.json').read_text())
    for directory, receipt in ((AI_BASE, ai_receipt), (CORPSE_BASE, corpse_receipt)):
        assert receipt['original_sha256'] == SOURCE_SHA
        for name, digest in receipt['artifacts'].items():
            assert sha(directory / name) == digest
    ai = [json.loads(line) for line in (AI_BASE / 'ai135-fixtures.jsonl').read_text().splitlines()]
    ai_actual = [json.loads(line) for line in (AI_BASE / 'ai135-results.jsonl').read_text().splitlines()]
    assert [c['expected'] for c in ai] == ai_actual
    all_player = json.loads((CORPSE_BASE / 'player-update135-fixtures.json').read_text())
    all_actual = [json.loads(line) for line in (CORPSE_BASE / 'player-update135-results.jsonl').read_text().splitlines()]
    corpse = [c for c in all_player if c['kind'] == 'corpse']
    for c in corpse:
        assert c['expected'] == all_actual[c['id']]['result']
    return ai, corpse


def replay_ai(cases):
    outputs = []
    for c in cases:
        state = input_from_dict(c['input']['incoming'])
        records = tuple(c['input']['records'])
        queued, steps = 0, []
        for step in c['steps']:
            result = update_ordinary_units(AiFrame135(records, step['now_bits'], step['dt_bits'],
                tuple(step['player_xyz_bits']), state, incoming_item_effects=(),
                other_incoming_sources_absent=True))
            records, state = result.records, result.incoming
            queued += len(result.attacks) + len(result.movements)
            output = dict(records=list(records), **{name: getattr(state, name) for name in FIELDS})
            output.update(incoming_total_992_bits=struct.pack('>d', state.incoming_total_992).hex(),
                phase2579=state.phase_2579, queued_packets=queued, world_reference=0)
            steps.append(output)
        actual = dict(id=c['id'], steps=steps)
        assert actual == c['expected'], ('AI default changed', c['id'])
        outputs.append(actual)
    return outputs


def replay_corpses(cases):
    outputs = []
    for c in cases:
        result = cleanup_ordinary_corpses(tuple(c['records']), c['now_bits'],
            mode=c['mode'], local_peer=c['peer'], explicit_other_sources_absent=True)
        actual = dict(records=list(result.records), packet_count=result.packet_count,
            removed_guids=[str(guid) for guid in result.removed_guids], rng_words=[1, 2, 3, 4], sequence=123)
        assert actual == c['expected'], ('Corpse default changed', c['id'])
        outputs.append(dict(source_case_id=c['id'], result=actual))
    return outputs


def none_checks(ai, corpses):
    checks = []
    base = ai[0]
    state = input_from_dict(base['input']['incoming'])
    step = base['steps'][0]
    baseline = base['input']['records'][0]

    def update(row):
        return update_ordinary_units(AiFrame135((encode_row(row),), step['now_bits'], step['dt_bits'],
            tuple(step['player_xyz_bits']), state, other_incoming_sources_absent=True))

    def require_error(name, call, offset, width):
        try:
            call()
        except UnknownRecordRead135 as exc:
            assert (exc.offset, exc.width) == (offset, width)
            checks.append(dict(case=name, expected_unknown=True, offset=exc.offset,
                width=exc.width, consumer=exc.consumer))
        else:
            raise AssertionError('Unknown read was accepted: ' + name)

    row = cells135(tuple([None] * 424))
    put_u32(row, 0, 0xffffffff); put_u64(row, 112, 0x123456789abcdef0)
    assert u32(row, 0) == 0xffffffff and i32(row, 0) == -1 and u64(row, 112) == 0x123456789abcdef0
    assert optional_u32(row, 4) is None and optional_u64(row, 32) is None
    assert isinstance(encode_row(row), tuple) and cells135(tuple(row)) is not row
    require_error('helper-field4', lambda: u32(row, 4, consumer='none_test.field4'), 4, 4)
    require_error('helper-known-bytes', lambda: known_bytes(row), 0, 424)
    assert known_bytes(baseline).hex() == baseline and encode_row(cells135(baseline)) == baseline
    checks.append(dict(case='helper-roundtrip-sign-width-and-copy', passed=True))
    for invalid in ((0,) * 423, (0,) * 423 + (256,), (0,) * 423 + (True,)):
        try:
            cells135(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid cells accepted')
    checks.append(dict(case='helper-invalid-length-cell-and-bool', passed=True))

    row = cells135(baseline)
    unknown_offsets = (4, 12, 20, 28, 32, 33, 34, 35, 36, 37, 38, 39, 44, 68, 276, 419, 420)
    for offset in unknown_offsets:
        row[offset] = None
    result = update(row)
    assert isinstance(result.records[0], tuple)
    assert all(result.records[0][offset] is None for offset in unknown_offsets)
    checks.append(dict(case='AI-unconsumed-padding-preserved', passed=True,
        input_cells=tuple(row), output_cells=result.records[0]))
    row = cells135(baseline)
    for offset in (120, 128, 136):
        row[offset:offset + 4] = [None] * 4
    result = update(row)
    assert all(result.records[0][offset:offset + 4] == (None,) * 4 for offset in (120, 128, 136))
    checks.append(dict(case='AI-inactive-slow-and-weakness-magnitudes-not-read', passed=True))
    put_u32(row, 132, f.from_float(20))
    put_u32(row, 352, 0)
    require_error('AI-active-weakness-required', lambda: update(row), 128, 4)
    row = cells135(baseline); row[344:348] = [None] * 4
    require_error('AI-duration-required', lambda: update(row), 344, 4)
    row = cells135(baseline); row[0:4] = [None] * 4
    require_error('AI-domain-marker-required', lambda: update(row), 0, 4)

    # Select a preexisting chase input: active slow magnitude is consumed only
    # when the movement branch calls the speed helper.
    chase = next(c for c in ai if c['group'] == 'pilot-contact-or-chase' and
        len(c['input']['records']) == 1 and u32(c['input']['records'][0], 328) == f.from_float(20))
    chase_raw = cells135(chase['input']['records'][0]); chase_raw[120:124] = [None] * 4
    put_u32(chase_raw, 124, f.from_float(20))
    require_error('AI-active-slow-required-on-chase', lambda: update(chase_raw), 120, 4)
    contact = cells135(baseline); contact[120:124] = [None] * 4; put_u32(contact, 124, f.from_float(20))
    assert isinstance(update(contact).records[0], tuple)
    checks.append(dict(case='AI-slow-not-read-on-contact', passed=True))

    raw = cells135(corpses[0]['records'][0]); put_u32(raw, 0, 0)
    raw[4:8] = [None] * 4; raw[112:120] = [None] * 8
    def cleanup(row, mode=0):
        return cleanup_ordinary_corpses((encode_row(row),), f.from_float(10), mode=mode,
            local_peer=0, explicit_other_sources_absent=True)
    assert cleanup(raw).records == (tuple(raw),)
    checks.append(dict(case='corpse-live-marker-skips-age-and-no-removal-guid', passed=True))
    put_u32(raw, 0, 1)
    require_error('corpse-dead-marker-requires-age', lambda: cleanup(raw), 4, 4)
    raw = cells135(corpses[0]['records'][0]); put_u32(raw, 4, f.from_float(8)); raw[280:284] = [None] * 4
    assert cleanup(raw, 0).packet_count == 1
    checks.append(dict(case='corpse-mode0-skips-owner', passed=True))
    require_error('corpse-mode1-requires-owner', lambda: cleanup(raw, 1), 280, 4)
    put_u32(raw, 4, f.from_float(10)); raw[112:120] = [None] * 8
    assert cleanup(raw, 1).records == (tuple(raw),)
    checks.append(dict(case='corpse-young-skips-owner-and-guid', passed=True))
    return checks


def run_original(kind, rows, results_expected):
    roles = ['update_units'] if kind == 'ai' else ['player_tick', 'update_units']
    runner = 'run_ai135_oracle.mjs' if kind == 'ai' else 'run_player_update135_oracle.mjs'
    out, manifest = build(roles)
    fixture = out / ('record-cells-ai135-fixtures.jsonl' if kind == 'ai' else 'record-cells-corpse135-fixtures.json')
    if kind == 'ai':
        fixture.write_text(''.join(json.dumps(c, allow_nan=False) + '\n' for c in rows))
    else:
        # Only transport IDs change; physical records, clock/owner domain and
        # expected outputs stay identical to the old35 corpse cases.
        rows = [dict(c, id=index) for index, c in enumerate(rows)]
        fixture.write_text(json.dumps(rows, allow_nan=False) + '\n')
    frozen = {p.name: sha(p) for p in (fixture, out / 'manifest.json', out / manifest['module_file'])}
    command = [str(RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts' / runner), str(out), str(fixture)]
    result, stderr = out / 'record-cells-original-results.jsonl', out / 'record-cells-stderr.log'
    started = time.monotonic()
    with result.open('w') as stdout, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stdout, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=60)
        finally:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
    try:
        os.killpg(child.pid, 0)
    except ProcessLookupError:
        absent = True
    else:
        absent = False
    assert code == 0 and absent, (kind, out)
    actual = [json.loads(line) for line in result.read_text().splitlines()]
    if kind == 'ai':
        assert actual == results_expected
    else:
        assert [c['result'] for c in actual] == [c['result'] for c in results_expected]
    assert frozen == {p.name: sha(p) for p in (fixture, out / 'manifest.json', out / manifest['module_file'])}
    runtime = out / ('ai135-runtime.json' if kind == 'ai' else 'player-update135-runtime.json')
    return dict(kind=kind, directory=str(out.relative_to(ROOT)), cases=len(rows),
        steps=sum(len(c.get('steps', [0])) for c in rows), mismatches=0,
        process=dict(command=command, pid=child.pid, pgid=child.pid, exit_code=code,
            deadline_seconds=60, seconds=round(time.monotonic() - started, 3), process_group_absent_after=absent),
        runtime=json.loads(runtime.read_text()),
        artifacts={p.name: sha(p) for p in (fixture, result, stderr, runtime, out / 'manifest.json', out / manifest['module_file'])})


def main():
    files = sorted({str(Path(m.__file__).resolve().relative_to(ROOT)) for m in tuple(sys.modules.values())
        if getattr(m, '__file__', None) and str(Path(m.__file__).resolve()).startswith(str(ROOT) + '/')}
        | {'scripts/check_record_cells_ai135.py', 'scripts/run_ai135_oracle.mjs',
           'scripts/run_player_update135_oracle.mjs', 'scripts/full135_host.mjs'})
    before = {name: sha(ROOT / name) for name in files}
    ai, corpses = loaded_baselines()
    ai_results, corpse_results = replay_ai(ai), replay_corpses(corpses)
    guards = none_checks(ai, corpses)
    assert sha(RUNTIME) == RUNTIME_SHA and sha(SOURCE) == SOURCE_SHA
    assert subprocess.check_output([str(RUNTIME), '--version'], text=True, timeout=5).strip() == 'v22.23.4'
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('record-cells-ai0135-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    for name in files:
        target = out / 'source-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes())
        assert sha(target) == before[name]
    (out / 'none-model-checks.json').write_text(json.dumps(guards, indent=2) + '\n')
    batches = [run_original('ai', ai, ai_results), run_original('corpse', corpses, corpse_results)]
    after = {name: sha(ROOT / name) for name in files}
    assert before == after and sha(SOURCE) == SOURCE_SHA
    receipt = dict(version='0.135.1', build='0898d5e3', original_wasm_sha256=SOURCE_SHA,
        batches=batches, none_model_checks=len(guards), source_sha256_before=before, source_sha256_after=after,
        explicit_unknown_rows_never_materialized_or_sent_to_original=True,
        independent_model_replayed_before_fresh_original=True,
        default_ai_baseline=str(AI_BASE.relative_to(ROOT)), default_corpse_baseline=str(CORPSE_BASE.relative_to(ROOT)),
        evidence_artifacts={'none-model-checks.json':sha(out / 'none-model-checks.json')},
        limitations=['Unchanged0.135.1 flat ordinary melee and corpse domains; no0.136 acceptance.',
            'None cases are pure-model conditional-read checks; only existing fully known hex cases enter921.',
            'Original exports retain source global0; this batch does not dynamically instrument stack.',
            'No headless, spawn, combat, unit adapter, cast or area code edited by this migration.'])
    (out / 'comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), ai_cases=len(ai), ai_steps=sum(len(c['steps']) for c in ai),
        corpse_cases=len(corpses), none_model_checks=len(guards), mismatches=0)))


if __name__ == '__main__':
    main()
