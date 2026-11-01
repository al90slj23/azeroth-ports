#!/usr/bin/env python3
"""Regenerate model expectations and compare a completed original CAS capture.

This never launches the original program. Capture sources remain immutable;
only the evidence decoder may differ, after an explicitly recorded repair.
Model expectations are regenerated before any original state record is read.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def logical_model_identity(path):
    digest, size, records = hashlib.sha256(), 0, 0
    with gzip.open(path, 'rb') as stream:
        while raw := stream.readline(2 * 1024 * 1024 + 1):
            if len(raw) > 2 * 1024 * 1024 or not raw.endswith(b'\n'):
                raise ValueError('Model expectation record bound')
            size += len(raw)
            records += 1
            if size > 1024**3:
                raise ValueError('Model expectation stream bound')
            digest.update(raw)
    return dict(records=records, bytes=size, sha256=digest.hexdigest())


def missing(pid, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-directory', type=Path, required=True)
    args = parser.parse_args()
    capture = args.capture_directory.resolve(strict=True)
    if not capture.is_relative_to((ROOT / 'evidence').resolve()):
        raise ValueError('Only4T project evidence captures are admitted')
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime(
        'opening-combat135-recomparison-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    print(json.dumps(dict(directory=str(out), phase='source_binding')), flush=True)
    began = time.monotonic()
    snapshot = capture / 'source-snapshot'
    sources = {str(p.relative_to(snapshot)): sha(p)
               for p in sorted(snapshot.rglob('*')) if p.is_file()}
    if not sources or any(not n.endswith(('.py', '.mjs')) for n in sources):
        raise ValueError('Complete frozen capture source files required')
    current = {n: sha(ROOT / n) for n in sources}
    allowed = {'scripts/opening_combat135_cas.py'}
    drift = {n: dict(captured=sources[n], current=current[n])
             for n in sources if current[n] != sources[n]}
    if set(drift) != allowed:
        raise ValueError('Only the declared read-only decoder repair may differ: ' + str(list(drift)))
    comparison_sources = {**current, str(Path(__file__).resolve().relative_to(ROOT)): sha(Path(__file__))}
    for name in comparison_sources:
        target = out / 'source-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    artifacts = ('fixtures.json', 'inputs.json', 'config.json', 'manifest.json',
                 'stage-expectations.jsonl.gz', 'results.cas.jsonl.gz',
                 'opening-combat135-cas-runtime.json', 'process-terminal.json',
                 'owned-process.json', 'blob-index.jsonl', 'blob-references.jsonl', 'stderr.log')
    captured_before = {n: sha(capture / n) for n in artifacts}
    fixture = json.loads((capture / 'fixtures.json').read_text())
    config = json.loads((capture / 'config.json').read_text())
    manifest = json.loads((capture / 'manifest.json').read_text())
    module = capture / manifest['module_file']
    captured_before[module.name] = sha(module)
    if sha(module) != manifest['module_sha256']:
        raise ValueError('Captured private module hash differs')
    if config['input_sha256'] != captured_before['inputs.json']:
        raise ValueError('Captured input hash differs')
    if (fixture['input']['class_byte'], fixture['input']['race_byte'],
            fixture['input']['region_index'], fixture['input']['object_id_u64']) != (1, 1, 0, '42'):
        raise ValueError('Explicit human-warrior/Elwynn/object42 domain required')
    steps = {a['dt_bits'] for a in fixture['actions'] if a['kind'] == 'controlled_tail_frame'}
    if steps != {1036831949} or not 1 <= fixture['independent_frames'] <= 750:
        raise ValueError('Controlled full-phase .1s frame domain required')
    save(out / 'capture-binding.json', dict(capture_directory=str(capture),
        frozen_capture_sources=sources, current_comparison_sources=comparison_sources,
        only_decoder_changed=drift, capture_artifacts_before=captured_before,
        original_execution_restarted=False, new_original_calls=0))

    # Import only after identities are bound. All production files must match
    # the files frozen by the original expected-first launcher, byte-for-byte.
    from check_opening_combat135 import (
        corpus, original_view, compare, load_independent_world, DEFAULT_WORLD,
        SOURCE, SOURCE_SHA, SNAPSHOT, SNAPSHOT_SHA, NODE, NODE_SHA)
    from opening_pickup_provenance135 import PickupAddressVerifier135
    from opening_combat135_cas import CaptureCAS135, CAPTURE_RECORD_LIMIT
    from core_spec import binary32 as f
    world, _, world_inputs = load_independent_world(DEFAULT_WORLD)
    world_inputs.update({str(p): sha(p) for p in
                        (DEFAULT_WORLD / 'receipt.json', DEFAULT_WORLD / 'inputs.json')})
    expected_path = out / 'regenerated-expectations.jsonl.gz'
    regenerated = corpus(world, int(fixture['input']['app_lcg_seed_u64']),
        fixture['independent_frames'], f.from_float(.1), expected_path)
    if regenerated != fixture:
        raise ValueError('Regenerated model fixture differs from the captured expected-first fixture')
    original_model = logical_model_identity(capture / 'stage-expectations.jsonl.gz')
    regenerated_model = logical_model_identity(expected_path)
    if original_model != regenerated_model:
        raise ValueError('Regenerated model expectation bytes differ')
    save(out / 'model-regeneration.json', dict(
        mode='independent_model_regeneration_after_original_execution_before_original_state_read',
        no_original_state_used=True, captured_and_regenerated_logical_bytes_equal=True,
        captured_expectation_sha256=captured_before['stage-expectations.jsonl.gz'],
        regenerated_expectation_sha256=sha(expected_path), logical=regenerated_model,
        fixture=regenerated, elapsed_seconds=time.monotonic() - began))
    print(json.dumps(dict(phase='model_regenerated_before_raw_read',
        frames=regenerated['independent_frames'], stages=regenerated['stage_count'])), flush=True)

    runtime = json.loads((capture / 'opening-combat135-cas-runtime.json').read_text())
    terminal = json.loads((capture / 'process-terminal.json').read_text())
    owned = json.loads((capture / 'owned-process.json').read_text())
    if (terminal['exit_code'] != 0 or terminal['deadline_exceeded']
            or not missing(owned['pid']) or not missing(owned['pgid'], True)):
        raise ValueError('Original capture process is not proven terminal')
    if (runtime['original_wasm_sha256'] != SOURCE_SHA
            or runtime['module_sha256'] != manifest['module_sha256']
            or runtime['input_sha256'] != captured_before['inputs.json']
            or runtime['completed_controlled_tail_frames'] != fixture['independent_frames']
            or runtime['completed_stages'] != fixture['stage_count']
            or runtime['boundaries'] != 0 or runtime['cases'] != 1
            or runtime['denied_imports'] != 878 or runtime['host_imports_throw'] is not True
            or runtime['output_records'] > CAPTURE_RECORD_LIMIT):
        raise ValueError('Original completed-capture identity/domain differs')
    save(out / 'prior-reader-failure.json', dict(
        capture_parent_tool_session=98934, capture_parent_exit_code=1,
        phase='CAS constructor before any stage comparison', error='CAS first record index',
        captured_decoder_metadata_index_maximum=10000, compared_stages=0,
        original_wasm_process_exit_code=0, original_completed_frames=runtime['completed_controlled_tail_frames'],
        captured_records=runtime['output_records'], repaired_record_count_maximum=CAPTURE_RECORD_LIMIT,
        source_of_failure='Frozen capture decoder hard limit and observed parent traceback; game execution completed.',
        original_capture_overwritten=False))
    decoder = CaptureCAS135(capture)
    verifier = PickupAddressVerifier135()
    errors, counts, kinds = [], Counter(), Counter()
    observed, compressed_stream_bytes = 0, 0
    stream_sha = hashlib.sha256()
    npc_aura_observations = 0
    with gzip.open(capture / 'results.cas.jsonl.gz', 'rb') as stream, gzip.open(expected_path, 'rt') as expected:
        while line := stream.readline(2 * 1024 * 1024 + 1):
            if len(line) > 2 * 1024 * 1024 or not line.endswith(b'\n'):
                raise ValueError('Original envelope record bound/truncation')
            compressed_stream_bytes += len(line)
            if compressed_stream_bytes > 1024**3:
                raise ValueError('Original envelope stream bound')
            stream_sha.update(line)
            raw = decoder.decode_line(line)
            kind = raw['record_kind']
            kinds[kind] += 1
            if raw['id'] != 0:
                raise ValueError('Unexpected captured case')
            if kind in ('opening', 'stage'):
                wanted = json.loads(next(expected))
                if wanted['record_kind'] != kind:
                    raise ValueError('Model/original record kind order differs')
                if kind == 'stage':
                    if raw['stage_index'] != observed or wanted['stage_index'] != observed:
                        raise ValueError('Stage index order differs')
                    for key in ('action_index', 'kind'):
                        compare(wanted[key], raw[key], f'stage[{observed}].{key}', errors, counts)
                    observed += 1
                path = 'opening' if kind == 'opening' else f'stage[{observed-1}]'
                target = wanted['expected']
                opaque = verifier.observe(raw, target)
                comparable = {k: v for k, v in target.items() if k != 'opaque_pickup_amount_origins'}
                compare(comparable, original_view(raw, target), path, errors, counts,
                        opaque_pickup_indices=opaque)
                npc_aura_observations = len(target['projection']['npc_aura_updates169'])
                if kind == 'stage' and observed % 1000 == 0:
                    print(json.dumps(dict(phase='compare', stages=observed,
                        differences=counts['differences'])), flush=True)
            elif kind == 'case_end':
                if raw['boundary'] is not None or raw['host_calls'] or raw['stage_count'] != fixture['stage_count']:
                    raise ValueError('Original case ending differs')
        if next(expected, None) is not None:
            raise ValueError('Unconsumed model expectation records')
    if (any(kinds[k] != 1 for k in ('case_start', 'constructor', 'opening', 'case_end'))
            or kinds['clock_control'] != fixture['independent_frames']
            or observed != fixture['stage_count']):
        raise ValueError('Incomplete original/model record coverage')
    cas = decoder.finish(runtime['capture_cas'])
    if (runtime['uncompressed_output_bytes'] != compressed_stream_bytes
            or runtime['uncompressed_sha256'] != stream_sha.hexdigest()
            or runtime['output_sha256'] != captured_before['results.cas.jsonl.gz']):
        raise ValueError('Captured output stream identity differs')
    after = {n: sha(ROOT / n) for n in comparison_sources}
    if after != comparison_sources or sources != {n: sha(snapshot / n) for n in sources}:
        raise ValueError('Source changed during recomparison')
    if captured_before != {n: sha(capture / n) for n in captured_before}:
        raise ValueError('Original captured artifacts changed')
    if any(sha(Path(p)) != h for p, h in world_inputs.items()):
        raise ValueError('Independent query-world input changed')
    if sha(SOURCE) != SOURCE_SHA or sha(NODE) != NODE_SHA or sha(SNAPSHOT) != SNAPSHOT_SHA:
        raise ValueError('Original/tool/context hash binding differs')
    save(out / 'differences.json', errors)
    result = dict(version='0.135.1', actual_build='90898d5e3',
        kind='completed_original_capture_recomparison_after_decoder_record_bound_repair',
        status='matched_existing_complete_capture' if not counts['differences'] else 'differences_preserved',
        capture_directory=str(capture), capture_artifacts_sha256=captured_before,
        referenced_original_executions=1, referenced_original_entry_calls=runtime['original_entry_calls'],
        new_original_executions=0, new_original_entry_calls=0,
        independent_frames=fixture['independent_frames'], independent_selections=fixture['independent_selections'],
        compared_stages=observed, differences=counts['differences'], comparison=dict(counts),
        source_files=len(comparison_sources), source_sha256_before=comparison_sources, source_sha256_after=after,
        captured_source_sha256=sources, only_decoder_changed=drift,
        model_regenerated_before_original_state_read=True,
        captured_expectations_generated_before_original_per_frozen_launcher=True,
        logical_model_expectations=regenerated_model, capture_cas_verification=cas,
        pickup_address_proof=verifier.report(), final_declared_npc_aura_updates169=npc_aura_observations,
        original_process={**terminal, 'pid_missing': True, 'pgid_missing': True},
        runtime=runtime, elapsed_seconds=time.monotonic() - began,
        full880_frames=0, native_Windows_execution=False, playable_replacement=False,
        limitations=['Regeneration and comparison of one completed750 capture, not a second original execution.',
            'Controlled14-tail/real6730+1089, historical original memory context, independent preparsed world, externalf32 clock.',
            'Only declared state/known physical cells/all150/declaredactor169/provenNPCaura169; otherUI/keyed/proc/wire remains unmodeled.',
            'Static-player trajectory has no nearby resource345 consumption; mixed component acceptance is separate.',
            'No full880, independent complete game, Windows runtime or latest138 gameplay-flow acceptance.'])
    save(out / 'comparison.json', result)
    print(json.dumps(dict(directory=str(out), stages=observed,
        differences=counts['differences'], comparison_sha256=sha(out / 'comparison.json'),
        referenced_original_calls=runtime['original_entry_calls'], new_original_calls=0)), flush=True)
    if counts['differences']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
