#!/usr/bin/env python3
"""Expected-first ordinary-NPC source metadata through complete original1073.

The original receives physical unit records and source GUIDs, never expected
labels. This is a history/scalar component, not full registry/proc acceptance.
"""
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
import argparse, json, os, signal, struct, subprocess, sys, time

sys.dont_write_bytecode = True
import check_incoming_history135 as H
from production_closure135 import production_sources135
ROOT = H.ROOT
sys.path.insert(0, str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.incoming135 import IncomingState135, input_from_dict, resolve_incoming_prefix
from core_spec.incoming_history135 import from_raw_storage, append_incoming_history, projection
from core_spec.incoming_source135 import resolve_incoming_source135, ordinary_english_source_names135

INPUT_KEYS = H.INPUT_KEYS + ('source_records',)
FILES = tuple(sorted(set(H.FILES + (
    'scripts/check_incoming_source135.py', 'scripts/run_incoming_source135_oracle.mjs',
    'scripts/production_closure135.py', 'scripts/trace_coop.py', 'scripts/wasm_index.py',
) + production_sources135(ROOT, 'core_spec.incoming_source135',
    'core_spec.incoming135', 'core_spec.incoming_history135'))))
IMPORTED = {p: H.sha(ROOT/p) for p in FILES}


def expected(case):
    raw = dict(case['input']); maximum = raw.pop('max_hp_bits')
    state = input_from_dict(raw)
    ring = from_raw_storage(case['storage'], case['head'], case['count'])
    names = ordinary_english_source_names135(); stages = []
    for op in case['ops']:
        state = replace(state, now_bits=op['now_bits']); before = state
        result = resolve_incoming_prefix(state, op['amount_bits'], int(op['source_guid']))
        if result.stage not in ('scalar_nonfatal_projection', 'phase_guard', 'protection_guard'):
            raise NotImplementedError(result.stage)
        state = result.state
        if result.status == 'pending':
            source = resolve_incoming_source135(case['source_records'], int(op['source_guid']),
                resolved_definition_names=names)
            ring = append_incoming_history(ring, now_bits=op['now_bits'], damage_bits=result.amount_bits,
                absorbed_bits=result.absorbed_bits, hp_after_prefix_bits=f.sub(before.hp_1528_bits, result.amount_bits),
                maximum_hp_bits=maximum, category=op['category'], source_label=source.source_label,
                source_classification=source.source_classification)
        stages.append(dict(**projection(ring), scalar=H.scalar_projection(state)))
    return stages


def corpus(pilot):
    names = ordinary_english_source_names135(); rows = []; pointers = sorted(names)
    def unit(guid, pointer, rank=0, marker=0):
        raw = bytearray([0xa5] * 424)
        for offset, value in ((0, marker), (40, 0xffffffff), (244, 0xffffffff), (280, 0), (284, pointer)):
            struct.pack_into('<I', raw, offset, value)
        struct.pack_into('<Q', raw, 112, guid); raw[416] = rank
        return raw.hex()
    def add(group, records, guid, *, phase=1, critical=0, category=0):
        state = IncomingState135(hp_1528_bits=f.from_float(1000), map_id=b'sw', phase_2579=phase)
        value = asdict(state); value.update(map_id='sw', max_hp_bits=f.from_float(1000))
        case = dict(id=len(rows), group=group, input=value, capacity=0, head=0, count=0, storage=[],
            source_records=records, ops=[dict(now_bits=f.from_float(20), amount_bits=f.from_float(7.5),
                source_guid=str(guid), critical=critical, category=category)])
        case['expected'] = expected(case); rows.append(case)
    add('matched-normal', [unit(101, pointers[0])], 101)
    add('unmatched-GUID', [unit(101, pointers[0])], 202)
    add('matched-second-vector-slot', [unit(11, pointers[0]), unit(22, pointers[-1], 1)], 22)
    if pilot: return rows
    for index, pointer in enumerate(pointers):
        add('all148-English-normal-definitions', [unit(0xf130000001000001 + index, pointer, index & 1)],
            0xf130000001000001 + index, critical=index & 1)
    for rank in (0, 1, 2, 3, 4, 7, 255):
        add('raw-rank-byte', [unit(101, pointers[0], rank)], 101)
    add('duplicate-GUID-first-wins', [unit(101, pointers[0], 1), unit(101, pointers[-1], 4)], 101)
    add('dead-entry-still-matched', [unit(101, pointers[-1], 1, marker=1)], 101)
    add('null-definition-keeps-rank', [unit(101, 0, 7)], 101)
    add('zero-GUID-can-match', [unit(0, pointers[0])], 0)
    add('phase-guard-no-name-consumed', [unit(101, pointers[0])], 101, phase=4)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot'); args = parser.parse_args()
    before = {p: H.sha(ROOT/p) for p in FILES}
    assert before == IMPORTED
    cases = corpus(args.phase == 'pilot')
    out, manifest = H.build(['incoming_damage'])
    for name, digest in before.items():
        target = out/'source-snapshot'/name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes()); assert H.sha(target) == digest
    fixture = out/'incoming-source135-fixtures.json'; inputs = out/'incoming-source135-inputs.json'
    fixture.write_text(json.dumps(cases, separators=(',', ':'))+'\n')
    inputs.write_text(json.dumps([{k: c[k] for k in INPUT_KEYS} for c in cases], separators=(',', ':'))+'\n')
    frozen = {p.name: H.sha(p) for p in (fixture, inputs, out/'manifest.json', out/manifest['module_file'])}
    assert H.sha(H.RUNTIME) == H.RUNTIME_SHA
    command = [str(H.RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT/'scripts/run_incoming_source135_oracle.mjs'), str(out), str(inputs)]
    results = out/'incoming-source135-results.jsonl'; stderr = out/'stderr.log'; began = time.monotonic()
    with results.open('w') as stdout, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stdout, stderr=err, start_new_session=True)
        (out/'owned-process.json').write_text(json.dumps(dict(pid=child.pid, pgid=child.pid, command=command, deadline_seconds=60)))
        timed_out = False
        try: child.wait(timeout=60)
        except subprocess.TimeoutExpired: timed_out = True
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try: child.wait(timeout=3)
                except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
    def missing(group=False):
        try: (os.killpg if group else os.kill)(child.pid, 0)
        except ProcessLookupError: return True
        return False
    terminal = dict(pid=child.pid, pgid=child.pid, exit_code=child.returncode, pid_missing=missing(),
        pgid_missing=missing(True), seconds=time.monotonic()-began, deadline_seconds=60, timed_out=timed_out)
    (out/'process-terminal.json').write_text(json.dumps(terminal, indent=2)+'\n')
    if child.returncode or timed_out: raise RuntimeError(f'Original exit{child.returncode}; preserved at {out}')
    failures = []; counters = Counter()
    with results.open() as stream:
        for case in cases:
            actual = json.loads(next(stream)); assert actual['id'] == case['id']
            assert len(actual['stages']) == len(case['expected'])
            for j, (want, observed) in enumerate(zip(case['expected'], actual['stages'])):
                assert observed['source_records_after'] == case['source_records']
                H.compare(want, observed, f'case{case["id"]}.stage{j}', failures, counters)
        assert not stream.read().strip()
    after = {p: H.sha(ROOT/p) for p in FILES}; assert before == after
    assert H.sha(H.SOURCE) == H.SOURCE_SHA
    assert frozen == {p.name: H.sha(p) for p in (fixture, inputs, out/'manifest.json', out/manifest['module_file'])}
    runtime_path = out/'incoming-source135-runtime.json'
    receipt = dict(version='0.135.1', actual_build='90898d5e3', original_sha256=H.SOURCE_SHA,
        phase=args.phase, cases=len(cases), differences=counters['differences'], comparison=dict(counters),
        source_sha256_before=before, source_sha256_after=after, groups=dict(Counter(c['group'] for c in cases)),
        runtime=json.loads(runtime_path.read_text()), process=terminal, independent_expected_before_original=True,
        original_input_contains_expected=False, artifacts={p.name:H.sha(p)for p in (fixture,inputs,results,stderr,runtime_path,out/'manifest.json')},
        scope='Complete1073 nonfatal ordinary-NPC matched-GUID English fallback source→history and scalar projection; explicit424 fixtures, empty proc/buff/item/modifier vectors.',
        limitations=['Registry1112/other keyed physical layout is captured, not independently modeled.',
            'Localization-map producer, custom/summon labels, spell metadata, fatal/revival and headless integration pending.'],
        full880_frames=0, native_executions=0, complete_games=0)
    (out/'differences.json').write_text(json.dumps(failures, indent=2)+'\n')
    target = out/'incoming-source135-comparison.json'; target.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),comparison_sha256=H.sha(target),cases=len(cases),differences=counters['differences'],failures=failures[:3],process=terminal)))
    if failures: raise SystemExit(1)


if __name__ == '__main__': main()
