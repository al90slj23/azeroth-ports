#!/usr/bin/env python3
"""Expected-first guardian idle/return versus complete unchanged original921.

Rows come from the independent first-expiry special producer, never captures.
Only original-side typed fixture allocation concretizes the unknown U68 owner.
"""
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
from build_full135_oracle import SOURCE, SOURCE_SHA
from build_distance_map135_oracle import build_distance_map135
from production_closure135 import production_sources135
from ai_world135_inputs import ASSET_WORLD, HASHES, load_asset_world135, asset_world_description135
from core_spec import binary32 as f
from core_spec.opening135 import EmptyOpeningInput135
from core_spec.opening_handoff135 import initialize_absent_companion_handoff
from core_spec.profile_companions135 import EmptyCompanionProfile135
from core_spec.opening_npc_pickups135 import OpeningVector135
from core_spec.special2376_135 import SpecialState2376_135
from core_spec.special2376_notify135 import SpecialLocale2376_135, ELWYNN_ENGLISH_NAMES
from core_spec.special2376_spawn135 import SpecialSpawnInput135, tick_special_spawn135
from core_spec.guardian_ai135 import (GuardianContext135, PendingGuardianAi135,
    step_guardian_unit135, guardian_cleanup_admitted135)
from core_spec.distance_map135 import produce_distance_map135, update_distance_map135
from core_spec.record_cells135 import cells135, u32, put_u32, encode_row

NODE = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def cooldown_view(owner):
    result = asdict(owner)
    result['guid'] = str(result['guid'])
    for key in ('physical_pointer_offset', 'physical_pointer_known'):
        result.pop(key)
    return json.loads(json.dumps(result))


def map_view(path):
    return None if path is None else dict(start_index=path.start_index, field24=path.field24,
        length=len(path.values_u16), sha256=hashlib.sha256(
            b''.join(struct.pack('<H', value) for value in path.values_u16)).hexdigest())


def corpus(full):
    world = load_asset_world135()
    opening = initialize_absent_companion_handoff(EmptyOpeningInput135(1, 1, 0, 0, 42), world,
        companion_profile=EmptyCompanionProfile135(()), title_utf8=b'Elwynn Forest', subtitle_utf8=b'').opening
    initial = opening.initial
    special = SpecialState2376_135(tuple(encode_row(row) for row in opening.special.storage),
        opening.special.count, f.from_float(20), initial.player_xyz[:2], 0, 0, 0, 0, 0, 0)
    value = SpecialSpawnInput135(special, OpeningVector135(424, (), 0), initial.level.rng_words,
        opening.counter, initial.player_xyz, initial.source_id, 1, 0x3f800000, 0, 0, 1, 0, 0, 0, 0)
    spawned = tick_special_spawn135(value, locale=SpecialLocale2376_135(ELWYNN_ENGLISH_NAMES))
    assert len(spawned.cooldowns) == 4
    cases, expected, labels, map_cache = [], [], [], {}

    def add(label, selected, *, offset=0, duration=0, lock=0, steps=1, dt=.1,
            timer=None, home_index=None, poison=0xa5, player=None):
        xyz = initial.player_xyz if player is None else player
        records, owners = [], []
        for index in selected:
            raw = cells135(spawned.units.storage[index], 424)
            home_x = u32(raw, 328)
            put_u32(raw, 316, f.add(home_x, f.from_float(offset)))
            if not duration:
                put_u32(raw, 328, f.add(home_x, f.from_float(offset)))
            put_u32(raw, 344, f.from_float(duration))
            put_u32(raw, 400, f.from_float(lock))
            if timer is not None:
                put_u32(raw, 352, f.from_float(timer))
            if home_index is not None:
                put_u32(raw, 92, home_index)
            records.append(encode_row(raw))
            owners.append(spawned.cooldowns[index])
        initial_records = records[:]
        stages, trace, statuses = [], [], []
        now, path, updated, sequence, packets = f.from_float(20), None, 0, 123, 0
        for _ in range(steps):
            now = f.add(now, f.from_float(dt))
            if path is None:
                key = xyz[:2]
                if key not in map_cache:
                    map_cache[key] = produce_distance_map135(world.nav, key)
                path, updated = map_cache[key], now
            else:
                refreshed = update_distance_map135(world.nav, xyz[:2], now, previous=path, updated_at_bits=updated)
                path, updated = refreshed.distance_map, refreshed.updated_at_bits
            context = GuardianContext135(now, f.from_float(dt), tuple(xyz), spawned.special.storage,
                spawned.special.count, world, other_sources_absent=True)
            movements = []
            for j, (record, owner) in enumerate(zip(records, owners)):
                result = step_guardian_unit135(record, owner, context, unit_index=j)
                assert guardian_cleanup_admitted135(result.record, result.cooldowns, context)
                records[j], owners[j] = result.record, result.cooldowns
                statuses.append(result.status)
                for movement in result.movement_geometry:
                    sequence = (sequence + 1) & f.MASK
                    item = asdict(movement)
                    item.update(target_id=str(item['target_id']), sequence=sequence)
                    movements.append(item)
                    packets += 1
            trace.append(dict(now_bits=now, dt_bits=f.from_float(dt), player_xyz_bits=list(xyz)))
            stages.append(dict(records=[cells135(row, 424) for row in records],
                cooldowns=[cooldown_view(owner) for owner in owners], sequence=sequence, packet_count=packets,
                rng_words=list(spawned.rng_words), hp_bits=f.from_float(10000), incoming_total_hex='0000000000000000',
                distance_map=map_view(path), distance_map_updated_at_bits=updated,
                movement_geometry=movements, unknown_preserved=True))
        cases.append(dict(id=len(cases), world=asset_world_description135(),
            records=[cells135(row, 424) for row in initial_records],
            cooldowns=[cooldown_view(spawned.cooldowns[index]) for index in selected],
            special_storage=[cells135(row, 40) for row in spawned.special.storage], special_count=spawned.special.count,
            capacity=max(4, len(records)), poison=poison, sequence=123, hp_bits=f.from_float(10000),
            rng_words=list(spawned.rng_words), steps=trace))
        expected.append(dict(id=len(expected), stages=stages))
        labels.append(dict(id=len(labels), group=label, statuses=dict(Counter(statuses)), steps=steps,
            unit_updates=len(records) * steps))

    add('actual-first-expiry-four-stationary', (0, 1, 2, 3), steps=40 if full else 3)
    for index in range(3):
        add('each-real-Elwynn-guardian-idle', (index,), steps=3, poison=(0xa5, 0x69, 0xcc)[index])
    add('actual-idle-return-home', (0, 1, 2), offset=5, steps=3)
    if full:
        for index in range(3):
            for offset in (2, 2.01, 3, 4):
                add('home-distance-return-boundaries', (index,), offset=offset, steps=2,
                    poison=(0x11, 0x69, 0xcc, 0xff)[int(offset) % 4])
            add('existing-return-movement-keeps-timers', (index,), offset=5, duration=2, steps=5)
            for timer in (0, -.5, 10):
                add('common-melee-timer-does-not-cast-while-idle', (index,), timer=timer)
            add('future400-exits-before-common-timer', (index,), lock=21, timer=.25)
            add('exact400-resumes-common-timer', (index,), lock=20.1)
            add('out-of-range-home-index-current-position-fallback', (index,), home_index=0xffffffff)
        add('zero-dt-stationary', (0, 1, 2, 3), dt=0)
        add('clamped-small-frame-step', (0, 1, 2, 3), dt=.025, steps=5)

    # Pure-model refusal and owner checks are separate from original cases.
    record = spawned.units.storage[0]
    owner = spawned.cooldowns[0]
    context = GuardianContext135(f.from_float(20.1), f.from_float(.1), initial.player_xyz,
        spawned.special.storage, spawned.special.count, world, other_sources_absent=True)
    refused = []
    for label, offset, number in (('dead', 0, 1), ('engaged', 108, 1), ('damaged', 288, f.from_float(1)),
                                  ('wrong capacity', 64, 0), ('unrestored status', 360, 1)):
        raw = cells135(record, 424)
        if offset == 108:
            raw[offset] = number
        else:
            put_u32(raw, offset, number)
        try:
            step_guardian_unit135(raw, owner, context)
        except (PendingGuardianAi135, ValueError) as error:
            refused.append(dict(label=label, error=type(error).__name__, reason=str(error)))
        else:
            raise AssertionError('Expected explicit guardian refusal: ' + label)
        assert not guardian_cleanup_admitted135(raw, owner, context)
    near = replace(context, player_xyz_bits=tuple(u32(record, offset) for offset in (328, 332, 336)))
    try:
        step_guardian_unit135(record, owner, near)
    except PendingGuardianAi135 as error:
        refused.append(dict(label='contact/engage boundary', error=type(error).__name__, reason=str(error)))
    else:
        raise AssertionError('Contact branch silently treated as idle')
    # Compare the exact frozen JSON representation, including XYZ tuple/list
    # normalization; Python dataclass tuples are not a runtime difference.
    return json.loads(json.dumps(cases)), json.loads(json.dumps(expected)), labels, refused


def compare(want, actual, path, errors, counts):
    if want is None:
        if '.records[' not in path:
            raise ValueError('Unknown allowed only in physical NPC cells')
        assert type(actual) is int and 0 <= actual <= 255
        counts['unknown_cells'] += 1
        return
    if type(want) is not type(actual):
        if len(errors) < 100:
            errors.append(dict(path=path, expected=want, actual=actual))
        counts['differences'] += 1
        return
    if isinstance(want, dict):
        if set(want) != set(actual):
            errors.append(dict(path=path, expected_keys=list(want), actual_keys=list(actual)))
            counts['differences'] += 1
            return
        for key, value in want.items():
            compare(value, actual[key], path + '.' + key, errors, counts)
    elif isinstance(want, list):
        if len(want) != len(actual):
            errors.append(dict(path=path, expected_length=len(want), actual_length=len(actual)))
            counts['differences'] += 1
        for index, (left, right) in enumerate(zip(want, actual)):
            compare(left, right, path + f'[{index}]', errors, counts)
    else:
        counts['known_leaves'] += 1
        if want != actual:
            counts['differences'] += 1
            if len(errors) < 100:
                errors.append(dict(path=path, expected=want, actual=actual))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    scripts = ('check_guardian_ai135.py', 'run_guardian_ai135_oracle.mjs', 'production_closure135.py',
        'build_distance_map135_oracle.py', 'build_full135_oracle.py', 'build_upgrade134_oracle.py',
        'distance_map135_host.mjs', 'ai_world135_packing.mjs', 'ai_world135_inputs.py')
    files = tuple('scripts/' + name for name in scripts) + production_sources135(ROOT,
        'core_spec.guardian_ai135', 'core_spec.opening_handoff135', 'core_spec.special2376_spawn135')
    before = {name: sha(ROOT / name) for name in files}
    cases, expected, labels, refused = corpus(args.phase == 'full')
    assert before == {name: sha(ROOT / name) for name in files}, 'Source changed during independent expectation generation'
    out, manifest = build_distance_map135()
    for name in files:
        target = out / 'source-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
        assert sha(target) == before[name]
    for name, value in (('input.json', cases), ('expected.json', expected), ('case-labels.json', labels), ('refusals.json', refused)):
        save(out / name, value)
    assert all((out / name).stat().st_size <= 4194304 for name in ('input.json', 'expected.json'))
    frozen = {name: sha(out / name) for name in ('input.json', 'expected.json', 'case-labels.json',
        'refusals.json', 'manifest.json', manifest['module_file'])}
    world_inputs = {str(ASSET_WORLD / name): digest for name, digest in HASHES.items()}
    command = [str(NODE), '--expose-gc', '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/run_guardian_ai135_oracle.mjs'), str(out), str(out / 'input.json')]
    save(out / 'guardian-prepared.json', dict(cases=len(cases), source_sha256=before,
        artifacts=frozen, world_inputs=world_inputs, command=command, expected_first=True,
        scope='Independent first-expiry producer rows and explicit world; full unchanged921; guardian idle/return only',
        budgets=dict(memory_mib=32, denied_imports=878, deadline_seconds=60, io_bytes=4194304)))
    if args.prepare_only:
        print(json.dumps(dict(directory=str(out), cases=len(cases), original_executed=False)))
        return
    assert sha(SOURCE) == SOURCE_SHA and sha(NODE) == NODE_SHA
    assert all(sha(Path(name)) == digest for name, digest in world_inputs.items())
    assert before == {name: sha(ROOT / name) for name in files}
    began, launcher_error = time.monotonic(), None
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Owned guardian921 launcher signal ' + str(signum))
    previous = signal.signal(signal.SIGTERM, interrupted)
    with (out / 'stdout.jsonl').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True,
            env=dict(os.environ, TMPDIR=str(out), PYTHONDONTWRITEBYTECODE='1'))
        with (out / 'guardian-owned-process.json').open('w') as ledger:
            ledger.write(json.dumps(dict(pid=child.pid, pgid=child.pid, command=command, deadline_seconds=60)) + '\n')
            ledger.flush()
            os.fsync(ledger.fileno())
        try:
            child.wait(timeout=60)
        except (subprocess.TimeoutExpired, KeyboardInterrupt, OSError) as error:
            launcher_error = str(error)
        finally:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            signal.signal(signal.SIGTERM, previous)
    def missing(group=False):
        try:
            (os.killpg if group else os.kill)(child.pid, 0)
        except ProcessLookupError:
            return True
        return False
    terminal = dict(pid=child.pid, pgid=child.pid, exit_code=child.returncode,
        pid_missing=missing(), pgid_missing=missing(True), seconds=time.monotonic() - began,
        launcher_error=launcher_error)
    save(out / 'guardian-process-terminal.json', terminal)
    errors, counts, runtime = [], Counter(), None
    if child.returncode == 0:
        rows = [json.loads(line) for line in (out / 'stdout.jsonl').read_text().splitlines()]
        assert len(rows) == len(expected)
        for wanted, actual in zip(expected, rows):
            compare(wanted, actual, 'case', errors, counts)
        runtime = json.loads((out / 'guardian-ai135-runtime.json').read_text())
        assert runtime['fresh_instances'] == len(cases) and runtime['actual_host_calls'] == 0 and runtime['stack_all_restored']
    after = {name: sha(ROOT / name) for name in files}
    source_unchanged = before == after
    artifacts_unchanged = all(sha(out / name) == digest for name, digest in frozen.items())
    world_unchanged = all(sha(Path(name)) == digest for name, digest in world_inputs.items())
    save(out / 'guardian-differences.json', errors)
    report = dict(version='0.135.1', actual_build='90898d5e3', original_sha256=SOURCE_SHA,
        cases=len(cases), original921_calls=0 if runtime is None else runtime['full_original921_calls'],
        unit_updates=sum(label['unit_updates'] for label in labels), differences=counts['differences'], comparison=dict(counts),
        groups=dict(Counter(label['group'] for label in labels)), statuses=dict(sum((Counter(label['statuses']) for label in labels), Counter())),
        pure_model_refusals=len(refused), expected_before_original=True, fresh_original_memory=True,
        guardian_records_from='independent SpecialSpawnInput135/tick_special_spawn135, no observation inputs',
        physical_u68='Unknown in independent model; real distinct typed fixture allocation in original; no fake zero pointer',
        source_files=len(files), source_sha256_before=before, source_sha256_after=after, source_unchanged=source_unchanged,
        frozen_artifacts=frozen, artifacts_unchanged=artifacts_unchanged, world_inputs=world_inputs, world_unchanged=world_unchanged,
        process=terminal, runtime=runtime, full880_frames=0, whole_guardian_ai_complete=False,
        scope='Exact local live guardian idle/return/locked paths only; action910/engage/leash/threshold/timer planning remain explicit boundaries',
        artifacts={name: sha(out / name) for name in ('stdout.jsonl', 'stderr.log', 'guardian-prepared.json', 'guardian-differences.json')})
    save(out / 'guardian-ai135-comparison.json', report)
    print(json.dumps(dict(directory=str(out), cases=len(cases), calls=report['original921_calls'],
        unit_updates=report['unit_updates'], differences=counts['differences'], first_errors=errors[:5],
        source_unchanged=source_unchanged, process=terminal, receipt_sha256=sha(out / 'guardian-ai135-comparison.json'))))
    if (errors or child.returncode or launcher_error or not terminal['pid_missing'] or not terminal['pgid_missing']
            or not source_unchanged or not artifacts_unchanged or not world_unchanged):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
