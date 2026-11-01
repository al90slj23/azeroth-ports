#!/usr/bin/env python3
"""Expected-before-original same-G constructor/gameplay/selection composition."""
from collections import Counter
from dataclasses import asdict
import argparse, json, os, re, signal, struct, subprocess, sys, time
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
from source_closure135 import core_sources

FILES = ('scripts/check_headless135.py', 'scripts/run_headless135_oracle.mjs',
    'scripts/source_closure135.py', 'scripts/build_full135_oracle.py', 'scripts/full135_host.mjs',
    'scripts/build_upgrade134_oracle.py', 'scripts/extract_cast_catalogue135.py') + core_sources(ROOT, 'headless135.py')
IMPORTED = {name: sha(ROOT / name) for name in FILES}
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.initial_state135 import ConstructorInput135, initialize_empty_profile
from core_spec.initial_state135_data import ZONE_ENTRIES
from core_spec.headless135 import from_initial, resolve_controlled_entry, step_frame, select, projection

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def corpus(pilot, frame_budget=400):
    rows = []
    for seed in ([1] if pilot else list(range(8))):
        value = ConstructorInput135(8, 1, 0, seed, 42, 0)
        state = from_initial(initialize_empty_profile(value), flat_height_bits=0,
            zeroed_unit_storage_resolved=True, zeroed_area_storage_resolved=True)
        state = resolve_controlled_entry(state, phase1_entry_explicitly_resolved=True)
        actions, expected, boundary = [], [], 'frame_budget'
        for frame in range(8 if pilot else frame_budget):
            updated, stages, status = step_frame(state, f.from_float(.1))
            if status != 'ordered_frame_projection':
                boundary = status; break
            state = updated; actions.append(dict(kind='frame', dt_bits=f.from_float(.1)))
            expected.extend(dict(kind=kind, projection=projection(snapshot)) for kind, snapshot in stages)
            if state.collection.level.phase2587 == 2:
                cards = state.collection.level.candidates
                #A fixed ordinary player policy, independent of implemented
                #ability coverage. Unsupported future casts become boundaries.
                index = next((i for i, card in enumerate(cards) if card.variant == 'upgrade'), 0)
                state, status = select(state, index)
                actions.append(dict(kind='select', index=index))
                expected.append(dict(kind='select', projection=projection(state)))
        raw = asdict(value); raw['seed_u64'] = str(value.seed_u64); raw['object_id_u64'] = str(value.object_id_u64)
        rows.append(dict(id=len(rows), group='constructor-mage-human-single-state-loop', input=raw,
            region_id=ZONE_ENTRIES[value.region_index][0], controlled_phase1=True, zeroed_unit_capacity=128,
            zeroed_area_capacity=128, frame_budget=8 if pilot else frame_budget,
            actions=actions, expected=expected, boundary=boundary,
            independent_frames=state.frames, independent_selections=state.selections,
            final_level=state.collection.level.progression.level,
            pending_abilities=[x.ability_id for x in state.collection.level.choice_inputs.owned]))
    return json.loads(json.dumps(rows))


def compare(want, actual, path, failures, counters):
    counters['leaves_or_shapes'] += 1
    if want is None:
        allowed = re.search(r'\.pickup_words\[\d+\]\[1\]$|\.live_words\[\d+\]\[(3|4)\]$', path)
        if allowed and type(actual) is int and 0 <= actual <= f.MASK:
            counters['explicit_unwritten_words'] += 1; return
    if type(want) != type(actual):
        counters['differences'] += 1
        if len(failures) < 80: failures.append(dict(field=path, expected=want, actual=actual))
    elif isinstance(want, dict):
        if want.keys() != actual.keys():
            counters['differences'] += 1; failures.append(dict(field=path, expected_keys=list(want), actual_keys=list(actual))); return
        for key, value in want.items(): compare(value, actual[key], path + '.' + key, failures, counters)
    elif isinstance(want, list):
        if len(want) != len(actual):
            counters['differences'] += 1
            if len(failures) < 80: failures.append(dict(field=path, expected_length=len(want), actual_length=len(actual)))
        for i, (w, a) in enumerate(zip(want, actual)): compare(w, a, path + f'[{i}]', failures, counters)
    elif want != actual:
        counters['differences'] += 1
        if len(failures) < 80:
            record = dict(field=path, expected=want, actual=actual)
            if '.records[' in path and isinstance(want, str) and isinstance(actual, str) and len(want) == len(actual) == 848:
                w, a = struct.unpack('<106I', bytes.fromhex(want)), struct.unpack('<106I', bytes.fromhex(actual))
                record = dict(field=path, differing_words=[dict(offset=i * 4, expected=x, actual=y) for i, (x, y) in enumerate(zip(w, a)) if x != y])
            failures.append(record)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--phase', choices=('pilot', 'full'), default='pilot'); args = p.parse_args()
    before = {name: sha(ROOT / name) for name in FILES}; assert before == IMPORTED
    rows = corpus(args.phase == 'pilot')
    out, manifest = build(['initial_game', 'player_tick', 'process_hits', 'area_tick', 'effect_tick', 'update_units', 'collect_pickups', 'spawn_tick', 'select_ability'])
    snapshots = out / 'source-snapshot'; snapshots.mkdir()
    for name in FILES:
        target = snapshots / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes()); assert sha(target) == before[name]
    fixtures = out / 'headless135-fixtures.jsonl'; fixtures.write_text(''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in rows))
    assert [json.loads(line) for line in fixtures.read_text().splitlines()] == rows
    frozen = {p.name: sha(p) for p in (fixtures, out / 'manifest.json', out / manifest['module_file'])}
    assert sha(RUNTIME) == RUNTIME_SHA
    assert subprocess.check_output([str(RUNTIME), '--version'], text=True).strip() == 'v22.23.4'
    command = [str(RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/run_headless135_oracle.mjs'), str(out), str(fixtures)]
    result, stderr = out / 'headless135-results.jsonl', out / 'headless135-stderr.log'; start = time.monotonic()
    with result.open('w') as stream, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stream, stderr=err, start_new_session=True)
        try: code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait(); raise RuntimeError(f'Owned60s timeout:{out}')
    duration = time.monotonic() - start
    if code: raise RuntimeError(f'Original exit{code}: {out}')
    actual = [json.loads(line) for line in result.read_text().splitlines()]
    assert [a['id'] for a in actual] == list(range(len(rows)))
    failures, counters, unmodeled, unmodeled_effects = [], Counter(), [], []
    for case, observed in zip(rows, actual):
        observations = [dict(kind=s['kind'], projection=s['projection']) for s in observed['stages']]
        compare(case['expected'], observations, f'case{case["id"]}', failures, counters)
        unmodeled.append(dict(id=case['id'], stages=[s['unmodeled_player_fields'] for s in observed['stages']]))
        unmodeled_effects.append(dict(id=case['id'], stages=[s['unmodeled_effect_fields'] for s in observed['stages']]))
    mismatches = out / 'headless135-mismatches.json'; mismatches.write_text(json.dumps(failures, indent=2) + '\n')
    omitted = out / 'headless135-unmodeled-player-fields.json'; omitted.write_text(json.dumps(unmodeled, separators=(',', ':')) + '\n')
    omitted_effects = out / 'headless135-unmodeled-effect-fields.json'; omitted_effects.write_text(json.dumps(unmodeled_effects, separators=(',', ':')) + '\n')
    assert before == {name: sha(ROOT / name) for name in FILES}
    assert sha(SOURCE) == SOURCE_SHA and sha(RUNTIME) == RUNTIME_SHA
    assert frozen == {p.name: sha(p) for p in (fixtures, out / 'manifest.json', out / manifest['module_file'])}
    runtime = out / 'headless135-runtime.json'
    receipt = dict(version='0.135.1', build='0898d5e3', cases=len(rows),
        stages=sum(len(c['expected']) for c in rows), frames=sum(c['independent_frames'] for c in rows),
        selections=sum(c['independent_selections'] for c in rows), boundaries=dict(Counter(c['boundary'] for c in rows)),
        comparison=dict(counters), differences=counters['differences'], source_sha256_before=before, source_sha256_after=before,
        artifacts={p.name: sha(p) for p in (fixtures, result, stderr, mismatches, omitted, omitted_effects, runtime, out / 'manifest.json', out / manifest['module_file'])},
        original_sha256=SOURCE_SHA, runtime=json.loads(runtime.read_text()),
        process=dict(command=command, pid=child.pid, pgid=child.pid, seconds=duration, exit_code=code, deadline_seconds=60),
        independent_expected_before_original=True, source_snapshots=True,
        limitations=['Explicit phase1 research resolution;1089/resource boot is incomplete and real entry has additional spawns/kind2 objects.',
            'Unit and area destination memory explicitly pre-reserved as128 zeroed424B/88B slots;live allocator padding determinism is not claimed.',
            'Same-G controlled2088/1754/3757/915/921/2862/947 sequence;complete880 and other915 families not established.',
            '915 integrated with real-observed idle vectors;active56/120 headless continuation remains pending, separately modeled delayed56 component has its own receipt.',
            'Inactive player action payload420..436 and physical vec pointers retained separately, not assumed zero or cosmetic.',
            'Seven persistent-area definitions;modifiers36/49,hostile/following areas and other effects remain pending.',
            'Only declared unwritten pickup arrival and inactive live words may be unspecified;all other compared data strict.',
            'Unknown selected abilities and due event clocks stop before another frame;all seeds and boundaries retained.',
            'Unmodeled player object keys retained separately, not assumed cosmetic;whole game incomplete.'])
    (out / 'headless135-comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), cases=len(rows), stages=receipt['stages'], frames=receipt['frames'], selections=receipt['selections'], differences=counters['differences'], first_fields=[f['field'] for f in failures[:8]])))
    if counters['differences']: raise SystemExit(1)


if __name__ == '__main__': main()
