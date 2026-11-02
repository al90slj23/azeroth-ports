#!/usr/bin/env python3
"""Expected-first fresh current139 first-level phase2/selection component."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import os
import signal
import subprocess
import sys
import time

from build_growth139_oracle import ROOT, build, sha, save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.initial_state139 import ConstructorInput139, initialize_empty_profile139
from core_spec.growth139 import from_constructor139, gain_xp139, projection139
from core_spec.select139 import select_card139

NODE = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def closure():
    files = set(production_sources135(ROOT, 'core_spec.growth139', 'core_spec.select139')) | {
        'scripts/check_growth139.py', 'scripts/build_growth139_oracle.py', 'scripts/run_growth139_oracle.mjs',
        'scripts/production_closure135.py', 'scripts/source_closure137.py'}
    while True:
        try:
            return sorted(files), verify_local_source_closure(sorted(files))
        except AssertionError as error:
            edge = error.args[0]
            assert isinstance(edge, tuple) and len(edge) == 2 and edge[1] not in files
            files.add(edge[1])


def corpus(pilot):
    rows = []
    for amount, select in ((2, None), (5, 0), (6, 0)):
        rows.append(dict(id=len(rows), amount=amount, seed_u64='1442695040888963407', select_index=select))
    if not pilot:
        for amount in (0, 1, 3, 4, 5, 6, 8, 13):
            rows.append(dict(id=len(rows), amount=amount, seed_u64='1442695040888963407', select_index=0 if amount >= 5 else None))
        # These are input-only independent-model searches, never original
        # observations; the first card is selected only in the admitted new
        # variant domain. All seeds still enter real2181 with three cards.
        for seed in (0, 1, 2, 42, 123456789, 0xffffffff, 0xffffffffffffffff):
            initial = initialize_empty_profile139(ConstructorInput139(1,1,0,seed,0,1116212265))
            generated = gain_xp139(from_constructor139(initial,phase2587=1),5).state
            index = 0 if generated.candidates[0].variant == 'new' else None
            rows.append(dict(id=len(rows),amount=5,seed_u64=str(seed),select_index=index))
        # Default second new card is tier3, exercising28657's nonzero table.
        rows.append(dict(id=len(rows),amount=5,seed_u64='1442695040888963407',select_index=1))
        tiers = set()
        for seed in range(4096):
            initial = initialize_empty_profile139(ConstructorInput139(1,1,0,seed,0,1116212265))
            generated = gain_xp139(from_constructor139(initial,phase2587=1),5).state
            first = generated.candidates[0]
            if first.variant == 'new' and first.tier not in tiers:
                tiers.add(first.tier)
                rows.append(dict(id=len(rows),amount=5,seed_u64=str(seed),select_index=0))
            if len(tiers) == 5:
                break
        assert tiers == set(range(5)), 'Bounded independent input search'
    return rows


def missing(pid, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot')
    args = parser.parse_args()
    files, edges = closure()
    before = {name: sha(ROOT / name) for name in files}
    assert sha(NODE) == NODE_SHA
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('growth139-oracle-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    manifest = build(out)
    expected = []
    read_audit = []
    model_audit = True
    def hook(event, values):
        if model_audit and event == 'open' and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(values[0])).resolve()
            if path.suffix.lower() in ('.wasm', '.wat', '.memory', '.exe'):
                read_audit.append(str(path))
                raise RuntimeError('Original input read during expectation')
    sys.addaudithook(hook)
    inputs = corpus(args.phase == 'pilot')
    for c in inputs:
        initial = initialize_empty_profile139(ConstructorInput139(1, 1, 0, int(c['seed_u64']), 0, 1116212265))
        state = from_constructor139(initial, phase2587=1)
        initial_projection = projection139(state)
        gain = gain_xp139(state, c['amount'])
        selected = None
        if c['select_index'] is not None:
            result = select_card139(gain.state, c['select_index'])
            assert result.accepted
            selected = dict(projection=projection139(result.state), live32_cells=[list(row) for row in result.state.live32_cells])
        expected.append(dict(id=c['id'], before=initial_projection, gain=projection139(gain.state), selection=selected,
                             model_events=list(gain.events)))
    assert not read_audit
    model_audit = False
    save(out / 'inputs.json', inputs)
    save(out / 'expected.json', expected)
    for name, digest in before.items():
        p = out / 'source-snapshot' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes())
        assert sha(p) == digest
    save(out / 'config.json', dict(input_path=str(out / 'inputs.json'), input_sha256=sha(out / 'inputs.json')))
    frozen = {name: sha(out / name) for name in ('inputs.json', 'expected.json', 'config.json', 'manifest.json', manifest['module_file'])}
    save(out / 'prepared.json', dict(source_before=before, source_import_edges=edges, frozen=frozen,
        expected_before_original=True, original_inputs_contain_expected=False, forbidden_model_reads=read_audit,
        explicit_phase1=True, real_phase2_path=True, snapshot_input=False))
    # Disable only the expectation audit before Node opens the originalmodule.
    assert model_audit is False
    command = [str(NODE), '--expose-gc', '--max-old-space-size=512', '--wasm-max-mem-pages=1024',
               str(ROOT / 'scripts/run_growth139_oracle.mjs'), str(out), str(out / 'config.json')]
    started = time.monotonic()
    with (out / 'stdout.jsonl').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
        save(out / 'owned-process.json', dict(pid=process.pid, pgid=process.pid, command=command, deadline_seconds=60))
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
    terminal = dict(pid=process.pid, pgid=process.pid, exit_code=process.returncode, seconds=time.monotonic() - started,
                    pid_missing=missing(process.pid), pgid_missing=missing(process.pid, True))
    save(out / 'process-terminal.json', terminal)
    actual = [json.loads(line) for line in (out / 'stdout.jsonl').read_text().splitlines()]
    differences = []
    known_live = unknown_live = 0
    def compare(want, got, case, stage):
        for key, value in want.items():
            observed = got.get(key)
            if key == 'player_fields':
                for field, expected_value in value.items():
                    if observed.get(field) != expected_value:
                        differences.append(dict(id=case, stage=stage, field='player_fields.' + field, expected=expected_value, actual=observed.get(field)))
            elif observed != value:
                differences.append(dict(id=case, stage=stage, field=key, expected=value, actual=observed))
    for e, a in zip(expected, actual, strict=False):
        assert e['id'] == a['id']
        compare(e['before'], a['before']['projection'], e['id'], 'before')
        compare(e['gain'], a['gain']['projection'], e['id'], 'gain')
        if e['selection'] is not None:
            if a['selection'] is None:
                differences.append(dict(id=e['id'], stage='selection', field='missing'))
                continue
            compare(e['selection']['projection'], a['selection']['projection'], e['id'], 'selection')
            for row, raw in zip(e['selection']['live32_cells'], a['selection']['live32_hex'], strict=True):
                data = bytes.fromhex(raw)
                for at, value in enumerate(row):
                    if value is None:
                        unknown_live += 1
                    else:
                        known_live += 1
                        if value != data[at]:
                            differences.append(dict(id=e['id'], stage='live32', offset=at, expected=value, actual=data[at]))
        assert a['profile376_before_hex'] == a['profile376_after_hex'] and a['view128_before_hex'] == a['view128_after_hex']
        assert a['stack_after'] == 1048576
    if len(actual) != len(expected):
        differences.append(dict(field='completed', expected=len(expected), actual=len(actual)))
    assert before == {name: sha(ROOT / name) for name in files}
    assert frozen == {name: sha(out / name) for name in frozen}
    runtime = json.loads((out / 'runtime.json').read_text()) if (out / 'runtime.json').is_file() else None
    save(out / 'differences.json', differences)
    result = dict(version='0.139.0', build='f79c5e2b4', phase=args.phase, cases=len(inputs), completed=len(actual),
        differences=len(differences), source_before=before, source_after=before, source_import_edges=edges,
        process=terminal, runtime=runtime, expected_before_original=True, model_forbidden_reads=[],
        live32_known=known_live, live32_None=unknown_live, full2181_notinstrumented=True,
        limitations=['Freshcomplete1600+real83304;borrowedflatquery andemptyresearchprofile are explicit inputs,notApp/worldRc.',
                     'Real4677 invokes2181 inphase1 andreal1093 selectsfirstcard;no mode/phase bypass.',
                     'CandidateUI80strings,allpresentation packets,fullkeyedfields andAura topology areobservations.',
                     'Only firstHumanWarrior/emptyworld firstnewability-selection;nonemptyworld/resume orupgradecardexplicitPending.'],
        artifacts={name: sha(out / name) for name in ('inputs.json', 'expected.json', 'config.json', 'manifest.json', 'stdout.jsonl', 'stderr.log', 'runtime.json', 'process-terminal.json') if (out / name).is_file()})
    save(out / 'comparison.json', result)
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out / 'comparison.json'),differences=len(differences),first=differences[:5],process=terminal)), flush=True)
    if process.returncode or differences:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
