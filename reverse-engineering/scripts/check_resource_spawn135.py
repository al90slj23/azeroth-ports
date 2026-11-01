#!/usr/bin/env python3
"""Expected-first full1417 and controlled full947 G2444 differential."""
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction'))
from build_full135_oracle import SOURCE, SOURCE_SHA, VALIDATOR_SHA, build, section_list, export_entries
from build_upgrade134_oracle import unsigned
from production_closure135 import production_sources135
from trace_resource_spawn135 import trace_resource_spawn135
from ai_world135_inputs import ASSET_WORLD, HASHES, load_asset_world135, asset_world_description135
from core_spec import binary32 as f
from core_spec.opening135 import EmptyOpeningInput135
from core_spec.opening_handoff135 import initialize_absent_companion_handoff
from core_spec.profile_companions135 import EmptyCompanionProfile135
from core_spec.opening_npc_pickups135 import OpeningVector135, npc_create_fields
from core_spec.opening_entities135 import unit_create169, BASE_SPEEDS
from core_spec.record_cells135 import cells135, u32, u64
from core_spec.resource_spawn135 import (PendingResourceSpawn135, ResourcePickupInput135,
    ResourceSpawnInput135, produce_resource_pickup135, step_resource_spawn135)
from core_spec.spawn_schedule135 import FrameInput
from core_spec.spawn_frame_motion135 import step_ordinary_frame
from core_spec.spawn_heading135 import atan2_bits
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from core_spec.spawn135 import definition

NODE = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def physical(vector):
    return dict(capacity=vector.capacity, count=vector.count, storage=vector.storage)


def fixture_vector(kinds=(), capacity=None, partial=False):
    capacity = max(len(kinds), 4) if capacity is None else capacity
    rows = []
    for i in range(capacity):
        row = bytearray((i * 31 + j * 17 + 37) & 255 for j in range(56))
        if i < len(kinds):
            struct.pack_into('<I', row, 0, 99 if i & 1 else 0)
            struct.pack_into('<I', row, 8, kinds[i])
        row = list(row)
        if partial:
            row[4:8] = [None, row[5], None, row[7]]
        rows.append(tuple(row))
    return OpeningVector135(56, tuple(rows), len(kinds))


def corpus(full):
    world, description = load_asset_world135(), asset_world_description135()
    cases, expected, labels, provenance = [], [], [], []
    handoffs = {}
    def handoff(seed):
        if seed not in handoffs:
            handoffs[seed] = initialize_absent_companion_handoff(EmptyOpeningInput135(1, 1, 0, seed, 42), world,
                companion_profile=EmptyCompanionProfile135(()), title_utf8=b'Elwynn Forest', subtitle_utf8=b'')
        return handoffs[seed]
    initial = handoff(0)
    center = ZONE_GEOMETRY[0]
    positions = (initial.initial.player_xyz,
        (f.add(initial.initial.player_xyz[0], f.from_float(40)), f.add(initial.initial.player_xyz[1], f.from_float(25)), 0),
        (f.add(center[0], f.from_float(1200)), f.add(center[1], f.from_float(-900)), f.from_float(-100)))
    def add(operation, group, value, *, frame=None, h=None, poison=0xa5):
        i = len(cases)
        raw = asdict(value); raw['pickups'] = dict(count=value.pickups.count, storage=value.pickups.storage)
        case = dict(id=i, operation=operation, input=raw, unknown_poison=poison, world=description,
            message_sequence=1)
        packets = []
        if operation == 'produce':
            result = produce_resource_pickup135(value, world)
            projection = dict(pickups=physical(result.pickups), rng_words=result.rng_words, counter=result.counter,
                message_sequence=1, packets=[dict(opcode=169, payload_hex=x.payload169_hex) for x in result.creates],
                notifications_count=0)
            meta = dict(kind=value.kind, final_position_bits=result.position_bits, draws=result.draws)
        else:
            units = h.opening.units
            ordinary = step_ordinary_frame(frame, destination_slots=units.storage, world=world,
                distance_map=None, allow_unknown_storage_growth=True)
            assert ordinary.status == 'ordinary_projection'
            # Scheduler consumes exactly the shared values returned by ordinary947.
            value = replace(value, rng_words=ordinary.rng_words, counter=ordinary.counter,
                velocity_xy=ordinary.velocity_xy)
            result = step_resource_spawn135(value, world)
            storage = list(units.storage)
            while len(storage) < len(ordinary.unit_records):
                storage.extend([(None,) * 424] * (max(4, len(storage) * 2) - len(storage)))
            for j, row in enumerate(ordinary.unit_records):
                storage[j] = tuple(cells135(row, 424))
            for request, row in zip(ordinary.requests, ordinary.unit_records[units.count:]):
                desc = definition(0, request['index']); xyz = tuple(request['position_bits'])
                heading = atan2_bits(f.sub(frame.player_xyz[1], xyz[1]), f.sub(frame.player_xyz[0], xyz[0]))
                fields = npc_create_fields(request['guid'], desc['entry'], desc['display'], desc['scale_bits'],
                    u32(row, 288), desc['elite'], h.initial.source_id, h.initial.level.progression.level)
                packets.append(dict(opcode=169, payload_hex=unit_create169(request['guid'], xyz, heading, BASE_SPEEDS, fields).hex()))
            packets.extend(dict(opcode=169, payload_hex=x.payload169_hex) for x in result.creates)
            scalars = dict(h.initial.initial_scalar_words)
            projection = dict(pickups=physical(result.pickups), rng_words=result.rng_words, counter=result.counter,
                message_sequence=1, packets=packets, notifications_count=0,
                next_resource2444_bits=result.next_resource2444_bits, budget_bits=ordinary.budget_bits,
                kill_cost_bits=ordinary.kill_cost_bits, velocity_xy=ordinary.velocity_xy,
                previous_player_xyz=frame.player_xyz if frame.mode == 0 else frame.previous_player_xyz,
                units=dict(capacity=len(storage), count=len(ordinary.unit_records), storage=storage),
                other_clocks={str(o):scalars[o] for o in (2424, 2440, 2448, 2456, 2460)})
            case.update(frame=asdict(frame), units=dict(count=units.count, storage=units.storage),
                initial_scalars=h.initial.initial_scalar_words, level=h.initial.level.progression.level,
                player_guid=str(h.initial.source_id))
            meta = dict(status=result.status, chosen_kind=result.chosen_kind, amount=result.amount,
                selection_draws=result.selection_draws, position_draws=result.position_draws,
                actor_draws=result.actor_draws, position=asdict(result.position) if result.position else None,
                final_position_bits=result.final_position_bits, counted_resources=result.counted_resources,
                ordinary_requests=ordinary.requests, ordinary_draws=ordinary.draws)
        cases.append(case); expected.append(dict(id=i, result=projection)); labels.append(dict(id=i, group=group, **meta))

    direct_n = 12 if full else 2
    for j in range(direct_n):
        kind = 3 + j % 3
        vec = (OpeningVector135(56, ()) if j % 4 == 0 else
            fixture_vector((0, 2, 1) if j % 4 == 1 else (2,), capacity=3 if j % 4 == 1 else 4, partial=j % 2 == 1))
        add('produce', '1417-real-world-kind' + str(kind), ResourcePickupInput135(0, kind,
            (0, 1, 0xffffffff, 0xdeadbeef)[j % 4], positions[j % 3], f.from_float(40),
            handoff(j % 4).rng_words, (0xffffffff if j == 5 else 85 + j), vec), poison=(0xa5, 0x5a)[j % 2])
    configs = [(0, None, 40, 40, .1, 0), (1, (), 40, 40, 0, 0)]
    if full:
        configs += [(seed, kinds, now, deadline, .1, 0) for seed in range(6)
            for kinds, now, deadline in ((None, 40, 40), ((3,), 40, 40), ((3, 4), 40, 40),
                ((0, 2, 1, 5, 4), 40, 40), ((5, 2, 0, 1), 40, 40), ((3, 4), 40, 40.000004),
                ((), 39.999996, 40), ((2,), 40, 39.5))]
        configs += [(seed, None, 40, 40, .1, 100) for seed in (0, 2)]
    for seed, kinds, now, deadline, dt, z_delta in configs:
        h = handoff(seed); initial = h.initial; scalars = dict(initial.initial_scalar_words)
        vec = h.opening.pickups if kinds is None else fixture_vector(kinds, partial=bool(seed & 1))
        player_xyz = (*initial.player_xyz[:2], f.add(initial.player_xyz[2], f.from_float(z_delta)))
        frame = FrameInput(0, f.from_float(now), f.from_float(dt), scalars[2416], initial.kill_cost_bits,
            0, initial.member_count, initial.level.heal_gate387, scalars[2516], 0, 0, 0,
            player_xyz, tuple(scalars[o] for o in (2428, 2432, 2436)), (0, 0),
            world.fallback_height_bits, h.rng_words, h.counter,
            tuple(tuple(row) for row in h.records), True)
        value = ResourceSpawnInput135(0, frame.now_bits, f.from_float(deadline), player_xyz,
            frame.velocity_xy, h.rng_words, h.counter, vec)
        add('tick', '947-real-world-13th-unclamped' if z_delta else '947-opening-ordinary-resource-explicit40',
            value, frame=frame, h=h, poison=(0xa5, 0x5a)[seed & 1])
        provenance.append(dict(id=len(cases)-1, app_lcg_seed=seed, opening_rng=h.rng_words,
            opening_counter=h.counter, opening_units=h.opening.units.count, opening_pickups=h.opening.pickups.count,
            explicit_clock_bits=frame.now_bits, explicit_player_z_delta=z_delta, natural_elapsed_frames=0))
    return cases, expected, labels, provenance


def private_build():
    out, manifest = build(['spawn_pickup', 'spawn_tick'])
    path = out / manifest['module_file']; raw = path.read_bytes()
    section = next(row for row in section_list(raw) if row[0] == 7)
    exports, start = export_entries(raw, section); name = b'research135_resource_stack0'
    added = unsigned(len(name)) + name + b'\x03' + unsigned(0)
    payload = unsigned(len(exports) + 1) + raw[start:section[3]] + added
    changed = raw[:section[1]] + b'\x07' + unsigned(len(payload)) + payload + raw[section[3]:]
    for a, b in zip(section_list(raw), section_list(changed)):
        assert a[0] == b[0]
        if a[0] != 7:
            assert raw[a[1]:a[3]] == changed[b[1]:b[3]]
    path.write_bytes(changed)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    assert sha(validator) == VALIDATOR_SHA
    child = subprocess.Popen([str(validator), '--enable-all', str(path)], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, start_new_session=True)
    save(out / 'resource-validator-owned.json', dict(pid=child.pid, pgid=child.pid, deadline_seconds=45))
    try:
        stdout, stderr = child.communicate(timeout=45)
    finally:
        try: os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        child.wait()
    (out / 'resource-validation.stdout').write_bytes(stdout); (out / 'resource-validation.stderr').write_bytes(stderr)
    assert child.returncode == 0
    manifest.update(module_sha256=sha(path), private_stack_export=dict(name=name.decode(), index=0, read_only=True),
        original_function_bodies_unchanged=True)
    save(out / 'manifest.json', manifest); trace_resource_spawn135(out)
    return out, manifest


def refusal_checks(cases):
    world = load_asset_world135()
    raw = next(c['input'] for c in cases if c['operation'] == 'produce')
    value = ResourcePickupInput135(**{**raw, 'pickups':OpeningVector135(56,
        tuple(tuple(row) for row in raw['pickups']['storage']), raw['pickups']['count'])})
    answered = []
    for name, changed, provider in (('1417-other-kind', replace(value, kind=6), world),
            ('1417-no-world', value, None)):
        try: produce_resource_pickup135(changed, provider)
        except PendingResourceSpawn135: answered.append(name)
        else: raise AssertionError('Unrestored resource producer accepted: ' + name)
    unknown = OpeningVector135(56, ((None,) * 56,), 1)
    due = ResourceSpawnInput135(0, f.from_float(40), f.from_float(40), (0,0,0), (0,0),
        (1,2,3,4), 7, unknown)
    try: step_resource_spawn135(due, world)
    except PendingResourceSpawn135: answered.append('947-active-kind-unknown')
    else: raise AssertionError('Unknown active kind was silently counted')
    future = step_resource_spawn135(replace(due, next_resource2444_bits=f.from_float(41)), None)
    assert future.status == 'resource2444_future' and future.pickups is unknown and future.draws == 0
    answered.append('947-future-does-not-read-kind-or-world')
    cap = replace(due, pickups=fixture_vector((3,4)))
    capped = step_resource_spawn135(cap, None)
    assert capped.status == 'resource2444_cap' and capped.rng_words == cap.rng_words and capped.counter == cap.counter
    assert capped.next_resource2444_bits == f.from_float(85) and capped.draws == 0
    answered.append('947-cap-does-not-read-world-or-draw-rng')
    return answered


def compare(expected, actual):
    errors, counts = [], Counter()
    def walk(want, got, path):
        if want is None:
            counts['explicit_unknown_cells'] += 1
        elif isinstance(want, dict):
            if set(want) != set(got): errors.append(dict(path=path, expected_keys=list(want), actual_keys=list(got))); return
            for key in want: walk(want[key], got[key], path + '.' + str(key))
        elif isinstance(want, (tuple, list)):
            if len(want) != len(got): errors.append(dict(path=path, expected_length=len(want), actual_length=len(got))); return
            for i, (a, b) in enumerate(zip(want, got)): walk(a, b, path + '[' + str(i) + ']')
        elif want != got:
            errors.append(dict(path=path, expected=want, actual=got))
        else:
            counts['equal_known_values'] += 1
    for left, right in zip(expected, actual):
        assert left['id'] == right['id']
        for key in ('pickups', 'units'):
            if key in right['result']:
                right['result'][key]['storage'] = [list(bytes.fromhex(row)) for row in right['result'][key]['storage']]
        walk(left['result'], right['result'], 'case' + str(left['id']))
        counts['packets'] += len(left['result']['packets'])
        counts['packet_bytes'] += sum(len(p['payload_hex']) // 2 for p in left['result']['packets'])
    return errors, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot')
    args = parser.parse_args()
    scripts = ('check_resource_spawn135.py', 'run_resource_spawn135_oracle.mjs', 'trace_resource_spawn135.py',
        'ai_world135_inputs.py', 'ai_world135_packing.mjs', 'production_closure135.py',
        'build_full135_oracle.py', 'build_upgrade134_oracle.py')
    files = tuple('scripts/' + name for name in scripts) + production_sources135(ROOT,
        'core_spec.resource_spawn135', 'core_spec.opening_handoff135', 'core_spec.spawn_frame_motion135', 'resource_spec.world_query135')
    before = {name: sha(ROOT / name) for name in files}
    cases, expected, labels, provenance = corpus(args.phase == 'full')
    refusals = refusal_checks(cases)
    assert before == {name: sha(ROOT / name) for name in files}, 'Source changed during expected generation'
    out, manifest = private_build()
    for name, digest in before.items():
        target = out / 'source-snapshot' / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes()); assert sha(target) == digest
    for name, value in (('resource-input.json', cases), ('resource-expected.json', expected),
            ('resource-labels.json', labels), ('resource-opening-input.json', provenance), ('resource-refusals.json', refusals)):
        save(out / name, value)
    assert (out / 'resource-input.json').stat().st_size <= 4194304
    frozen = {name: sha(out / name) for name in ('resource-input.json', 'resource-expected.json', 'resource-labels.json',
        'resource-opening-input.json', 'resource-refusals.json', 'manifest.json', manifest['module_file'], 'resource-spawn135-static.json')}
    world_inputs = {str(ASSET_WORLD / name): digest for name, digest in HASHES.items()}
    command = [str(NODE), '--expose-gc', '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/run_resource_spawn135_oracle.mjs'), str(out), str(out / 'resource-input.json')]
    save(out / 'resource-prepared.json', dict(source_sha256=before, artifacts=frozen, world_inputs=world_inputs,
        cases=len(cases), command=command, expected_before_original=True, deadline_seconds=60))
    assert sha(SOURCE) == SOURCE_SHA and sha(NODE) == NODE_SHA and before == {name: sha(ROOT / name) for name in files}
    began, launcher_error = time.monotonic(), None
    def interrupted(sig, frame): raise KeyboardInterrupt('Owned resource launcher signal ' + str(sig))
    previous = signal.signal(signal.SIGTERM, interrupted)
    with (out / 'resource-results.jsonl').open('wb') as stdout, (out / 'resource-stderr.log').open('wb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True,
            env=dict(os.environ, TMPDIR=str(out), PYTHONDONTWRITEBYTECODE='1'))
        with (out / 'resource-owned-process.json').open('w') as ledger:
            ledger.write(json.dumps(dict(pid=child.pid, pgid=child.pid, command=command, deadline_seconds=60)) + '\n')
            ledger.flush(); os.fsync(ledger.fileno())
        try: child.wait(timeout=60)
        except (subprocess.TimeoutExpired, KeyboardInterrupt, OSError) as error: launcher_error = str(error)
        finally:
            try: os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: child.wait(timeout=2)
            except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
            signal.signal(signal.SIGTERM, previous)
    def missing(group=False):
        try: (os.killpg if group else os.kill)(child.pid, 0)
        except ProcessLookupError: return True
        return False
    terminal = dict(pid=child.pid, pgid=child.pid, exit_code=child.returncode, pid_missing=missing(),
        pgid_missing=missing(True), seconds=time.monotonic()-began, launcher_error=launcher_error)
    save(out / 'resource-process-terminal.json', terminal)
    errors, counts, runtime = [], Counter(), None
    if child.returncode == 0:
        actual = [json.loads(line) for line in (out / 'resource-results.jsonl').read_text().splitlines()]
        assert len(actual) == len(expected); errors, counts = compare(expected, actual)
        runtime = json.loads((out / 'resource-spawn135-runtime.json').read_text())
        assert runtime['fresh_instances'] == len(cases) and runtime['actual_host_calls'] == 0 and runtime['stack_all_restored']
    after = {name: sha(ROOT / name) for name in files}
    save(out / 'resource-differences.json', errors)
    report = dict(version='0.135.1', actual_build='90898d5e3', original_sha256=SOURCE_SHA,
        cases=len(cases), differences=len(errors), comparison=dict(counts), groups=dict(Counter(row['group'] for row in labels)),
        pure_model_refusals_and_short_circuit_checks=refusals,
        expected_before_original=True, source_files=len(files), source_sha256_before=before, source_sha256_after=after,
        source_unchanged=before==after, frozen_artifacts=frozen,
        artifacts_unchanged=all(sha(out / name)==digest for name,digest in frozen.items()),
        world_inputs=world_inputs, world_unchanged=all(sha(Path(name))==digest for name,digest in world_inputs.items()),
        process=terminal, runtime=runtime, full880_frames=0, natural40_second_runs=0,
        component_scope='Complete1417 kinds3..5 and single full947 at explicit~40; independent opening→ordinary real-world→resource',
        pending=['Other due947 events/Boss/elite', 'Resource collection/effects', '1417 primary-present nearest-miss low-address read',
            'Natural40-second full880 sequence not validated by component calls'],
        artifacts={name:sha(out/name) for name in ('resource-results.jsonl','resource-stderr.log','resource-differences.json','resource-prepared.json')})
    save(out / 'resource-spawn135-comparison.json', report)
    print(json.dumps(dict(directory=str(out), cases=len(cases), differences=len(errors), first_errors=errors[:6],
        source_unchanged=before==after, process=terminal, receipt_sha256=sha(out/'resource-spawn135-comparison.json'))))
    if errors or child.returncode or launcher_error or not terminal['pid_missing'] or not terminal['pgid_missing'] or not report['source_unchanged'] or not report['artifacts_unchanged'] or not report['world_unchanged']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
