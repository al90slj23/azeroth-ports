#!/usr/bin/env python3
"""Observe unchanged915 on the fixed eight-seed trace; do not invent its inputs.

Old independent expectations are reused unchanged. This is an observational
insertion probe, not an independently implemented full effect system.
"""
from collections import Counter
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha

BASELINE = ROOT / 'evidence/full0135-oracle-20261101T064308.759593Z'
OLD_RECEIPT = json.loads((BASELINE / 'headless135-comparison.json').read_text())
FILES = tuple(dict.fromkeys(('scripts/probe_effect_system135.py',
    'scripts/probe_effect_system135.mjs', *OLD_RECEIPT['source_sha256_before'])))
IMPORTED = {name: sha(ROOT / name) for name in FILES}
from check_headless135 import compare

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
ROLES = ['initial_game', 'player_tick', 'process_hits', 'area_tick', 'effect_tick',
    'update_units', 'collect_pickups', 'spawn_tick', 'select_ability']


def main():
    before = {name: sha(ROOT / name) for name in FILES}
    assert before == IMPORTED
    for name, digest in OLD_RECEIPT['source_sha256_before'].items():
        assert sha(BASELINE / 'source-snapshot' / name) == digest
        if name not in ('scripts/build_full135_oracle.py', 'scripts/full135_host.mjs'):
            assert before[name] == digest, 'Old expectation producer changed: ' + name
    baseline_file = BASELINE / 'headless135-fixtures.jsonl'
    assert sha(baseline_file) == OLD_RECEIPT['artifacts'][baseline_file.name]
    baseline = [json.loads(line) for line in baseline_file.read_text().splitlines()]
    assert len(baseline) == 8
    rows = [{key: value for key, value in row.items() if key != 'expected'} for row in baseline]
    out, manifest = build(ROLES)
    snap = out / 'source-snapshot'
    for name in FILES:
        p = snap / name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes()); assert sha(p) == before[name]
    saved_baseline = out / 'prior-independent-expected.jsonl'
    saved_baseline.write_bytes(baseline_file.read_bytes())
    fixtures = out / 'effect-system135-probe-fixtures.jsonl'
    fixtures.write_text(''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in rows))
    assert [json.loads(line) for line in fixtures.read_text().splitlines()] == rows
    frozen = {p.name: sha(p) for p in (saved_baseline, fixtures,
        out / 'manifest.json', out / manifest['module_file'])}
    assert sha(RUNTIME) == RUNTIME_SHA
    assert subprocess.check_output([str(RUNTIME), '--version'], text=True).strip() == 'v22.23.4'
    command = [str(RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/probe_effect_system135.mjs'), str(out), str(fixtures)]
    result = out / 'effect-system135-probe-results.jsonl'
    stderr = out / 'effect-system135-probe-stderr.log'
    start = time.monotonic()
    with result.open('w') as stream, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stream, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait()
            raise RuntimeError(f'Owned60s probe deadline: {out}')
    duration = time.monotonic() - start
    if code:
        raise RuntimeError(f'Probe runner exit{code}: {out}')
    failures, counts, cases = [], Counter(), []
    with result.open() as stream:
        for c in baseline:
            actual = json.loads(next(stream))
            assert actual['id'] == c['id']
            at, local, prior = 0, Counter(), None
            for index, stage in enumerate(actual['stages']):
                domains = stage['effect_domains']
                local['observed_snapshots'] += 1
                local['delayed56_nonempty_snapshots'] += domains['delayed56']['length'] != 0
                local['effects120_nonempty_snapshots'] += domains['effects120']['length'] != 0
                local['nonzero_clock_snapshots'] += domains['clock2364_bits'] != 0
                local['new_packets'] += len(stage['new_messages']['packets'])
                local['new_notifications'] += len(stage['new_messages']['notifications'])
                if stage['kind'] == 'effects':
                    assert prior and prior['kind'] == 'area'
                    local['original915_calls'] += 1
                    local['915_changed_prior_projection'] += prior['projection'] != stage['projection']
                    local['915_changed_effect_domains'] += prior['effect_domains'] != domains
                    local['915_packets'] += len(stage['new_messages']['packets'])
                    local['915_notifications'] += len(stage['new_messages']['notifications'])
                    local['915_unit_backing_delta_words'] += len(stage['unit_storage_delta_words'])
                    local['915_area_backing_delta_words'] += len(stage['area_storage_delta_words'])
                    # A retained independent no-op hypothesis, never fitted to
                    # this original run. Active domains invalidate its scope.
                    compare(c['expected'][at - 1]['projection'], stage['projection'],
                        f'case{c["id"]}.inserted915_{index}', failures, counts)
                else:
                    expected = c['expected'][at]
                    assert stage['kind'] == expected['kind']
                    compare(expected['projection'], stage['projection'],
                        f'case{c["id"]}.retained_{at}', failures, counts)
                    at += 1
                prior = stage
            local['retained_model_stages_compared'] = at
            initial = actual['constructor_effect_domains']
            cases.append(dict(id=c['id'], seed=c['input']['seed_u64'], outcome=actual['outcome'],
                failure=actual['failure'], expected_old_stages=len(c['expected']),
                constructor_effect_domains=initial, observations=dict(local)))
            if actual['outcome'] == 'returned': assert at == len(c['expected'])
        assert not stream.read().strip()
    mismatch_file = out / 'effect-system135-probe-mismatches.json'
    mismatch_file.write_text(json.dumps(failures, indent=2) + '\n')
    after = {name: sha(ROOT / name) for name in FILES}
    assert before == after and sha(SOURCE) == SOURCE_SHA and sha(RUNTIME) == RUNTIME_SHA
    assert frozen == {p.name: sha(p) for p in (saved_baseline, fixtures,
        out / 'manifest.json', out / manifest['module_file'])}
    runtime = out / 'effect-system135-probe-runtime.json'
    totals = Counter()
    for case in cases: totals.update(case['observations'])
    receipt = dict(version='0.135.1', build='0898d5e3',
        kind='observational_original915_insertion_with_retained_prior_model_hypothesis',
        original_sha256=SOURCE_SHA, cases=cases, totals=dict(totals),
        outcomes=dict(Counter(c['outcome'] for c in cases)),
        comparison=dict(counts), differences=counts['differences'],
        baseline_receipt=str((BASELINE / 'headless135-comparison.json').relative_to(ROOT)),
        baseline_receipt_sha256=sha(BASELINE / 'headless135-comparison.json'),
        independent_expected_reused_before_original=True,
        effect_inputs_overwritten=False, new_independent915_model_verified=False,
        source_sha256_before=before, source_sha256_after=after,
        runtime=json.loads(runtime.read_text()),
        process=dict(command=command, pid=child.pid, pgid=child.pid, seconds=duration,
            exit_code=code, deadline_seconds=60),
        artifacts={p.name: sha(p) for p in (saved_baseline, fixtures, result, stderr,
            mismatch_file, runtime, out / 'manifest.json', out / manifest['module_file'])},
        limitations=['Observes915, not its complete independent implementation.',
            'Preserves prior eight-seed actions, card policy and controlled phase/storage inputs.',
            'Full880, other stages, true entry/resources and a complete independent game remain pending.',
            'Only prior declared pickup/live unwritten-word masks; all effect raw records are observed unchanged.',
            'Packet/notification payloads are retained as observations, not yet independent packet models.'])
    p = out / 'effect-system135-probe-receipt.json'
    p.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), totals=dict(totals),
        outcomes=receipt['outcomes'], differences=receipt['differences'])))


if __name__ == '__main__': main()
