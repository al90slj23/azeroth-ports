#!/usr/bin/env python3
"""Observe all single-state880 tail entries, not an independent880 implementation.

Original seed0..7 and first-upgrade-else-first policy remain fixed. Original
runtime may continue beyond the previous model's unknown-skill boundaries;
those observations are never labelled independent-model validation.
"""
from collections import Counter
import argparse
import json
import os
import signal
import subprocess
import time
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha

BASELINE = ROOT / 'evidence/full0135-oracle-20261101T072329.149731Z'
BASE_RECEIPT = json.loads((BASELINE / 'headless135-comparison.json').read_text())
FILES = tuple(dict.fromkeys(('scripts/probe_main_tail135.py', 'scripts/probe_main_tail135.mjs',
    *BASE_RECEIPT['source_sha256_before'])))
BEFORE = {name: sha(ROOT / name) for name in FILES}
from check_headless135 import compare

NODE = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
CHAIN = [('player', 'player_tick'), ('extra', 'auto_cast'), ('owned_effects', 'owned_effect_tick'),
    ('hits', 'process_hits'), ('area', 'area_tick'), ('effects', 'effect_tick'),
    ('deadline', 'deadline_tick'), ('secondary', 'secondary_hits'), ('ai', 'update_units'),
    ('collect', 'collect_pickups'), ('claims', 'claim_tick'), ('spawn', 'spawn_tick'),
    ('special', 'special_tick'), ('terminal', 'terminal_tick')]


def main():
    p = argparse.ArgumentParser(); p.add_argument('--pilot', action='store_true'); args = p.parse_args()
    before = {name: sha(ROOT / name) for name in FILES}; assert before == BEFORE
    base_fixture = BASELINE / 'headless135-fixtures.jsonl'
    assert sha(base_fixture) == BASE_RECEIPT['artifacts'][base_fixture.name]
    for name, digest in BASE_RECEIPT['source_sha256_before'].items():
        assert sha(BASELINE / 'source-snapshot' / name) == digest
        if name not in ('scripts/build_full135_oracle.py', 'scripts/full135_host.mjs'):
            assert before[name] == digest, name
    old = [json.loads(line) for line in base_fixture.read_text().splitlines()]
    if args.pilot: old = old[:1]
    rows = [dict(id=i, input=c['input'], region_id=c['region_id'], controlled_phase1=True,
        zeroed_unit_capacity=128, zeroed_area_capacity=128, frame_budget=8 if args.pilot else 400,
        dt_bits=0x3dcccccd) for i, c in enumerate(old)]
    out, manifest = build(['initial_game', 'select_ability', *(role for _, role in CHAIN)])
    snap = out / 'source-snapshot'
    for name in FILES:
        dest = snap / name; dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / name).read_bytes()); assert sha(dest) == before[name]
    fixture = out / 'main-tail135-probe-fixtures.jsonl'
    fixture.write_text(''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in rows))
    saved_expected = out / 'prior-independent-expected.jsonl'; saved_expected.write_bytes(base_fixture.read_bytes())
    frozen = {q.name: sha(q) for q in (fixture, saved_expected, out / 'manifest.json', out / manifest['module_file'])}
    assert [json.loads(line) for line in fixture.read_text().splitlines()] == rows
    assert sha(NODE) == NODE_SHA and subprocess.check_output([str(NODE), '--version'], text=True).strip() == 'v22.23.4'
    command = [str(NODE), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/probe_main_tail135.mjs'), str(out), str(fixture)]
    result, stderr = out / 'main-tail135-probe-results.jsonl', out / 'main-tail135-probe-stderr.log'
    start = time.monotonic()
    with result.open('w') as stdout, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stdout, stderr=err, start_new_session=True)
        try: code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait()
            raise RuntimeError(f'Owned60s main-tail probe deadline:{out}')
    seconds = time.monotonic() - start
    if code: raise RuntimeError(f'Probe runner exit{code}:{out}')
    failures, comparison, cases, totals = [], Counter(), [], Counter()
    with result.open() as stream:
        for c in old:
            observed = json.loads(next(stream)); assert observed['id'] == c['id']
            lookup, frame, offset = {}, 0, 0
            legacy_kinds = ('player', 'hits', 'area', 'effects', 'ai', 'collect', 'spawn')
            for action in c['actions']:
                if action['kind'] == 'frame':
                    frame += 1
                    for kind in legacy_kinds:
                        e = c['expected'][offset]; assert e['kind'] == kind
                        lookup[frame, kind] = e['projection']; offset += 1
                else:
                    e = c['expected'][offset]; assert e['kind'] == 'select'
                    lookup[frame, 'select'] = e['projection']; offset += 1
            assert offset == len(c['expected'])
            local, first, prior = Counter(), {}, None
            for stage in observed['stages']:
                kind, frame = stage['kind'], stage['frame']; local['snapshots'] += 1
                expected = lookup.get((frame, kind))
                if expected is not None:
                    local['legacy_model_stages_compared'] += 1
                    compare(expected, stage['projection'], f'case{c["id"]}.frame{frame}.{kind}', failures, comparison)
                domains = dict(stage['main_domains'])
                domains['delayed56'] = stage['effect_domains']['delayed56']
                domains['effects120'] = stage['effect_domains']['effects120']
                for name, vector in domains.items():
                    if isinstance(vector, dict) and vector.get('length', 0):
                        local[name + '_nonempty_snapshots'] += 1
                        first.setdefault(name, dict(frame=frame, kind=kind, length=vector['length']))
                local['packets_' + kind] += len(stage['new_messages']['packets'])
                local['notifications_' + kind] += len(stage['new_messages']['notifications'])
                if prior is not None and kind in ('extra', 'owned_effects', 'deadline', 'secondary', 'claims', 'special', 'terminal'):
                    local[kind + '_changed_legacy_projection'] += stage['projection'] != prior['projection']
                    local[kind + '_raw_game_word_changes'] += len(stage['game_delta_words'])
                prior = stage
            cases.append(dict(id=c['id'], seed=c['input']['seed_u64'], frames=observed['frames'],
                selections=observed['selections'], skipped=observed['skipped'], outcome=observed['outcome'],
                failure=observed['failure'], first_nonempty=first, observations=dict(local)))
            totals.update(local)
        assert not stream.read().strip()
    mismatches = out / 'main-tail135-prior-model-mismatches.json'; mismatches.write_text(json.dumps(failures, indent=2) + '\n')
    assert before == {name: sha(ROOT / name) for name in FILES}
    assert sha(SOURCE) == SOURCE_SHA and sha(NODE) == NODE_SHA
    assert frozen == {q.name: sha(q) for q in (fixture, saved_expected, out / 'manifest.json', out / manifest['module_file'])}
    runtime = out / 'main-tail135-probe-runtime.json'
    receipt = dict(version='0.135.1', build='0898d5e3', kind='observational_full_single_state_tail_not_independent880',
        original_sha256=SOURCE_SHA, cases=cases, totals=dict(totals),
        prior_model_comparison=dict(comparison), prior_model_differences=comparison['differences'],
        original_input_policy='same seeds0..7; actual first upgrade else first; no skill-coverage filtering',
        original_effect_or_resource_vectors_overwritten=False, complete880_called=False,
        source_sha256_before=before, source_sha256_after=before,
        baseline_receipt=str((BASELINE / 'headless135-comparison.json').relative_to(ROOT)),
        baseline_receipt_sha256=sha(BASELINE / 'headless135-comparison.json'),
        runtime=json.loads(runtime.read_text()),
        process=dict(command=command, pid=child.pid, pgid=child.pid, exit_code=code, deadline_seconds=60, seconds=seconds),
        artifacts={q.name: sha(q) for q in (fixture, saved_expected, result, stderr, mismatches,
            runtime, out / 'manifest.json', out / manifest['module_file'])},
        limitations=['Actual observations beyond the old model boundaries are not independent game implementation validation.',
            'Complete single-state tail, not880front/party/transport/realentry;phase1/zeroed unit+area storage remain explicit fixtures.',
            'New source differences or host boundaries are retained, never turned into passing model cases.',
            'Packet/notification bodies and full rawGame deltas are observations unless a separate independent codec proves them.'])
    p = out / 'main-tail135-probe-receipt.json'; p.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), outcomes=dict(Counter(c['outcome'] for c in cases)),
        totals=dict(totals), prior_model_differences=receipt['prior_model_differences'],
        first_fields=[x['field'] for x in failures[:6]])))


if __name__ == '__main__': main()
