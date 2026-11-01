#!/usr/bin/env python3
"""Check lossless opening handoff; optional private complete6730/1089 oracle.

Independent expected state uses only the frozen independent asset-world query
artifacts. Original memory belongs solely to the optional oracle process after
expected outputs have been written and hashed. No save or installed app is used.
"""
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
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
from core_spec.opening135 import (EmptyOpeningInput135, initialize_empty_opening,
    initialize_absent_companion_opening, projection as opening_projection)
from core_spec.opening_handoff135 import (VECTOR_STRIDES, from_opening, pickup_semantics135,
    PendingOpeningHandoff135, initialize_absent_companion_handoff, projection)
from core_spec.profile_companions135 import EmptyCompanionProfile135, produce_companion_slots
from resource_spec.terrain135 import HeightRaster135, TerrainChunk135, TerrainTile135
from resource_spec.world_query135 import NavGrid135, WorldQueries135

DEFAULT_WORLD = ROOT / 'evidence/asset-world0135-independent-20261101T111736.050879Z'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def external(path):
    path = Path(path).resolve()
    if not path.is_relative_to(Path('/Volumes/RuiRui4TB')):
        raise ValueError('Inputs/evidence must remain on the4T volume')
    return path


def load_independent_world(directory):
    """Decode the independent producer's documented canonical query format."""
    directory = external(directory)
    receipt = json.loads((directory / 'receipt.json').read_text())
    if (receipt['kind'] != 'independent_asset_to_world_to_default_opening'
            or receipt['original_program_executed'] is not False
            or receipt['original_memory_read'] is not False):
        raise ValueError('An independently produced asset world is required')
    if sha(directory / 'inputs.json') != receipt['inputs_sha256']:
        raise ValueError('Independent input hash differs')
    if receipt['source_sha256_before'] != receipt['source_sha256_after']:
        raise ValueError('Independent world source freeze differs')
    artifacts = receipt['world_artifacts']
    payloads = {}
    for name, artifact in artifacts.items():
        path = external(directory / artifact['file'])
        if not path.is_relative_to(directory) or path.suffix in ('.memory', '.wasm', '.wat'):
            raise ValueError('World query payload is not a canonical independent artifact')
        if sha(path) != artifact['sha256']:
            raise ValueError('Independent world artifact hash differs')
        payloads[name] = path.read_bytes()
    raw = payloads['terrain']; cursor = 0
    def take(fmt):
        nonlocal cursor
        value = struct.unpack_from(fmt, raw, cursor)
        cursor += struct.calcsize(fmt)
        return value
    tiles = []
    tilecount, = take('<I')
    if not 0 < tilecount <= 512:
        raise ValueError('Independent terrain tile budget')
    for _ in range(tilecount):
        *bounds, count = take('<5I')
        if not 0 < count <= 1024:
            raise ValueError('Independent terrain chunk budget')
        chunks = []
        for _ in range(count):
            holes, vertices = take('<HI')
            if vertices != 145:
                raise ValueError('Canonical independent terrain vertices required')
            chunks.append(TerrainChunk135(tuple(take('<3I') for _ in range(vertices)), holes))
        tiles.append(TerrainTile135(tuple(chunks), tuple(bounds)))
    if cursor != len(raw):
        raise ValueError('Independent terrain has unconsumed payload')
    nav = artifacts['navigation']; secondary = artifacts['secondary']
    if len(payloads['navigation']) != nav['width'] ** 2:
        raise ValueError('Independent navigation shape differs')
    if len(payloads['secondary']) != secondary['width'] ** 2 * 4:
        raise ValueError('Independent secondary shape differs')
    scalars = receipt['query_scalars']
    if scalars['primary_present']:
        raise NotImplementedError('This producer did not publish a primary-grid artifact')
    world = WorldQueries135(tuple(tiles), None,
        HeightRaster135(tuple(x[0] for x in struct.iter_unpack('<I', payloads['secondary'])),
                        tuple(secondary['origin_xy_bits']), secondary['width']),
        NavGrid135(payloads['navigation'], tuple(nav['origin_xy_bits']), nav['width']),
        scalars['fallback_height_bits'], scalars['flat_height_bits'])
    return world, receipt, {str(directory / artifact['file']): artifact['sha256']
                           for artifact in artifacts.values()}


def corpus():
    rows = [(1, 1, 0, 0), (8, 1, 1, 42)]
    rows.extend((1, 1, seed, 0) for seed in (1, 2, 3, 7, 31, 255, 0x123456789abcdef))
    rows.extend(((2,3,2,0x100000000), (3,4,7,0xffffffffffffffff), (4,5,3,0x100000001),
        (7,6,31,0x123456789abcdef0), (9,8,255,42), (11,7,0x123456789abcdef,0x7fffffffffffffff),
        (5,2,0,0xffff000000000001)))
    return tuple(EmptyOpeningInput135(cls, race, 0, seed, guid) for cls, race, seed, guid in rows)


def selfcheck(opening, handoff, world):
    checks = 0
    assert handoff.opening is opening and handoff.world is world; checks += 1
    assert handoff.collection.level is opening.initial.level; checks += 1
    assert handoff.phase2587 == opening.phase2587 == 1; checks += 1
    assert handoff.rng_words == opening.rng_words and handoff.counter == opening.counter; checks += 1
    assert handoff.unit_storage is opening.units.storage and handoff.pickup_storage is opening.pickups.storage; checks += 1
    assert handoff.collection.death.capacity == opening.pickups.capacity; checks += 1
    assert tuple(p.kind for p in handoff.collection.death.records) == (2, 2); checks += 1
    assert tuple(p.amount for p in handoff.collection.death.records) == (2, 1); checks += 1
    assert all(p.arrival_bits is None for p in handoff.collection.death.records); checks += 1
    assert opening.companions.count == opening.companions.capacity == 0; checks += 1
    expected = projection(handoff)
    for name, stride in VECTOR_STRIDES:
        vector = getattr(opening, name)
        assert expected['vectors'][name]['storage'] == [list(row) for row in vector.storage]
        # A nonstandard capacity, known stale tail bytes and partial unknown
        # masks must pass unchanged. This is a synthetic preservation test.
        sentinel = tuple(None if j % 3 == 0 else (j * 37 + 19) & 255 for j in range(stride))
        changed = replace(opening, **{name: replace(vector, storage=vector.storage + (sentinel,))})
        carried = from_opening(changed, world)
        assert getattr(carried.opening, name).storage == vector.storage + (sentinel,)
        assert projection(carried)['vectors'][name]['capacity'] == vector.capacity + 1
        checks += 3
    partial = list(opening.pickups.storage[0]); partial[4] = 165
    assert pickup_semantics135(tuple(partial)).arrival_bits is None; checks += 1
    # No unknown byte may be invented for an actual required read.
    for offset in (0, 8, 12, 16, 24, 40, 52):
        row = list(opening.pickups.storage[0]); row[offset] = None
        try:
            pickup_semantics135(tuple(row))
        except PendingOpeningHandoff135:
            checks += 1
        else:
            raise AssertionError('Unknown required pickup read was accepted')
    bad = replace(opening, initial=replace(opening.initial,
        level=replace(opening.initial.level, phase2587=0)))
    try:
        from_opening(bad, world)
    except ValueError:
        checks += 1
    else:
        raise AssertionError('Constructor phase was accepted as actual opening')
    return checks


def sources():
    paths = {Path(__file__).resolve()}
    paths.update(ROOT / 'scripts' / name for name in ('run_opening_handoff135_oracle.mjs',
        'world_snapshot135_host.mjs', 'build_world_snapshot135_oracle.py',
        'check_opening135.py', 'build_full135_oracle.py', 'build_upgrade134_oracle.py',
        'source_closure135.py'))
    for module in tuple(sys.modules.values()):
        source = getattr(module, '__file__', None)
        if source:
            path = Path(source).resolve()
            if path.is_relative_to(ROOT / 'reconstruction') and path.suffix == '.py':
                paths.add(path)
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--independent-world', type=Path, default=DEFAULT_WORLD)
    parser.add_argument('--original-opening', action='store_true')
    parser.add_argument('--phase', choices=('pilot', 'full'), default='full')
    args = parser.parse_args()
    world, world_receipt, artifacts = load_independent_world(args.independent_world)
    out = external(ROOT / 'evidence' / datetime.now(timezone.utc).strftime(
        'opening-handoff0135-%Y%m%dT%H%M%S.%fZ')); out.mkdir()
    before = {str(path.relative_to(ROOT)): sha(path) for path in sources()}
    for path in sources():
        target = out / 'source-snapshot' / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(path.read_bytes())
    title, subtitle = b'Elwynn Forest', 'The Defias Uprising — survive the onslaught!'.encode()
    profile = EmptyCompanionProfile135(())
    slots = produce_companion_slots(profile)
    assert [slot.tag for slot in slots] == [255, 255]
    assert all(slot.pointer is None for slot in slots)
    cases = []; handoffs = []; checks = 0
    inputs = corpus()[:2] if args.phase == 'pilot' else corpus()
    for value in inputs:
        opening = initialize_absent_companion_opening(value, world, companion_profile=profile,
            title_utf8=title, subtitle_utf8=subtitle)
        handoff = from_opening(opening, world)
        checks += selfcheck(opening, handoff, world)
        raw = asdict(value)
        raw.update(app_lcg_seed_u64=str(value.app_lcg_seed_u64), object_id_u64=str(value.object_id_u64),
                   companion_tags=[slot.tag for slot in slots])
        cases.append(dict(id=len(cases), input=raw, expected=opening_projection(opening),
            diagnostic=dict(constructor_seed_u64=str(opening.constructor_seed_u64))))
        handoffs.append(projection(handoff))
    # Exact compatibility with the previous explicit zero-slot fixture is a
    # model/output regression check, never counted as a new original case.
    legacy = initialize_empty_opening(inputs[0], world, title_utf8=title, subtitle_utf8=subtitle)
    assert opening_projection(legacy) == json.loads((args.independent_world / 'opening.json').read_text())
    checks += 1
    direct = initialize_absent_companion_handoff(inputs[0], world, companion_profile=profile,
        title_utf8=title, subtitle_utf8=subtitle)
    assert projection(direct) == handoffs[0]
    checks += 1
    fixture = out / 'opening-handoff135-expected.json'; fixture.write_text(json.dumps(cases) + '\n')
    handoff_path = out / 'handoff.json'; handoff_path.write_text(json.dumps(handoffs) + '\n')
    original_inputs = out / 'opening-handoff135-inputs.json'
    original_inputs.write_text(json.dumps([{key: row[key] for key in ('id', 'input')} for row in cases]) + '\n')
    frozen = {path.name: sha(path) for path in (fixture, handoff_path, original_inputs)}
    report = dict(kind='independent_asset_world_absent_companion_opening_handoff',
        version='0.135.1', build='0898d5e3', cases=len(cases), model_assertions=checks,
        independent_world_directory=str(args.independent_world.resolve()),
        independent_world_receipt_sha256=sha(args.independent_world / 'receipt.json'),
        independent_world_artifacts=artifacts, asset_file_count=world_receipt['asset_files'],
        profile_input=asdict(profile), companion_tags=[255,255],
        legacy_zero_slot_output_unchanged=True, source_sha256_before=before,
        original_program_executed=False, original_memory_read_by_independent_producer=False,
        new_original_cases=0, original_differences=None, new_mainloop_frames=0,
        expected_before_original=True, original_input_exact_keys=['id','input'],
        expected_or_diagnostics_in_original_input=False, output_sha256=frozen,
        whole_game_complete=False, limitations=[
            'Empty account companion flags only; other profile/account/menu fields remain explicit.',
            '2922 absence branch is statically traced; this oracle invokes complete6730/1089, not2922.',
            'Independent world query artifacts are reused, not rebuilt by this checker.',
            'The controlled oracle restores a historical resolved world; no fresh full App bootstrap or880 frame.',
            'Handoff retains all six physical vectors but does not execute their pending consumers.'])
    if args.original_opening:
        from build_world_snapshot135_oracle import build_snapshot135
        from check_opening135 import SNAPSHOT, SNAPSHOT_SHA, APP, WORLD, NODE, NODE_SHA, compare
        assert sha(SNAPSHOT) == SNAPSHOT_SHA and sha(NODE) == NODE_SHA
        oracle, manifest = build_snapshot135(['cached_construct', 'begin_run'])
        config = out / 'oracle-config.json'
        config.write_text(json.dumps(dict(snapshot_path=str(SNAPSHOT), snapshot_sha256=SNAPSHOT_SHA,
            model_snapshot_sha256=None, app_pointer=APP, world_pointer=WORLD,
            input_path=str(original_inputs), input_sha256=sha(original_inputs))) + '\n')
        command = [str(NODE), '--max-old-space-size=512', '--wasm-max-mem-pages=4096',
            str(ROOT / 'scripts/run_opening_handoff135_oracle.mjs'), str(oracle), str(config)]
        results = out / 'original-results.jsonl'; stderr = out / 'original-stderr.log'
        started = time.monotonic(); timed_out = False
        with results.open('w') as stdout, stderr.open('w') as err:
            child = subprocess.Popen(command, stdout=stdout, stderr=err, start_new_session=True)
            try:
                code = child.wait(timeout=60)
            except subprocess.TimeoutExpired:
                timed_out = True; os.killpg(child.pid, signal.SIGKILL); code = child.wait()
        observed = [json.loads(line) for line in results.read_text().splitlines()]
        failures = []; counters = Counter()
        if code != 0 or timed_out or len(observed) != len(cases):
            failures.append(dict(field='oracle_process', exit_code=code, timed_out=timed_out,
                                 result_cases=len(observed), expected_cases=len(cases)))
        for expected, actual in zip(cases, observed):
            assert expected['id'] == actual['id']
            compare(expected, actual, counters, failures)
        (out / 'differences.json').write_text(json.dumps(failures, indent=2) + '\n')
        report.update(original_program_executed=True, new_original_cases=len(observed),
            original_differences=len(failures), comparison=dict(counters),
            oracle_module_directory=str(oracle), oracle_module_sha256=manifest['module_sha256'],
            oracle_manifest_sha256=sha(oracle / 'manifest.json'), oracle_config_sha256=sha(config),
            oracle_runtime=json.loads((oracle / 'opening-handoff135-runtime.json').read_text())
                if (oracle / 'opening-handoff135-runtime.json').exists() else None,
            process=dict(command=command, exit_code=code, timed_out=timed_out,
                         seconds=time.monotonic()-started),
            original_results_sha256=sha(results), original_stderr_sha256=sha(stderr))
    after = {str(path.relative_to(ROOT)): sha(path) for path in sources() if str(path.relative_to(ROOT)) in before}
    report.update(source_sha256_after=after, source_unchanged=before == after)
    assert frozen == {name: sha(out / name) for name in frozen}
    assert all(sha(path) == digest for path, digest in artifacts.items())
    passed = before == after and (not args.original_opening or report['original_differences'] == 0)
    report['status'] = 'passed' if passed else 'failed_preserved'
    target = out / 'report.json'; target.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), report_sha256=sha(target), status=report['status'],
        cases=len(cases), model_assertions=checks, original_differences=report['original_differences'])))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
