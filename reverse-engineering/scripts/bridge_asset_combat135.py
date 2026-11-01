#!/usr/bin/env python3
"""Bind a raw-asset model terminal state to an existing scoped differential.

This compares two independent-model executions. It neither executes nor reads
original game memory/WASM, and adds zero original differential cases. The
referenced original differential retains its own declared projection boundary.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json

EXTERNAL = Path('/Volumes/RuiRui4TB').resolve()


def external(path):
    path = Path(path).resolve()
    if not path.is_relative_to(EXTERNAL):
        raise ValueError('Research inputs and outputs must remain on4T')
    return path


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def owner(rows, count):
    digest = hashlib.sha256()
    unknown = 0
    for row in rows:
        unknown += row.count(None)
        digest.update(json.dumps(row, separators=(',', ':')).encode() + b'\n')
    return dict(count=count, capacity=len(rows), backing_sha256=digest.hexdigest(),
                unknown_backing_cells=unknown)


def actor_creates(packets):
    result = []
    for opcode, payload in packets:
        if opcode != 169:
            continue
        raw = bytes.fromhex(payload)
        if len(raw) < 7 or raw[:5] != b'\1\0\0\0\0' or raw[5] not in (2, 3):
            continue
        cursor, guid = 7, 0
        for i in range(8):
            if raw[6] >> i & 1:
                if cursor >= len(raw):
                    raise ValueError('Truncated packed GUID')
                guid |= raw[cursor] << (8 * i)
                cursor += 1
        result.append(dict(guid=str(guid), payload169_hex=payload))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-directory', type=Path, required=True)
    parser.add_argument('--comparison', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    model, comparison, output = map(external,
        (args.model_directory, args.comparison, args.output))
    if output.exists():
        raise ValueError('Existing bridge evidence must not be overwritten')
    receipt = json.loads((model / 'receipt.json').read_text())
    oracle = json.loads(comparison.read_text())
    if (receipt['kind'] != 'independent_raw_asset_to_world_opening_combat_modelselfcheck'
            or receipt['model_version'] != oracle['version']
            or oracle['version'] != '0.135.1'
            or receipt['model_actual_build'] != oracle['actual_build']
            or oracle['differences'] != 0 or not oracle['completed_requested_budget']):
        raise ValueError('A matching135 complete-budget scoped differential is required')
    for name, key in (('inputs.json', 'inputs_sha256'),
            ('stages.jsonl', 'stages_sha256'), ('final-state.json', 'final_state_sha256'),
            ('opaque-pickup-amount-origins.json', 'opaque_pickup_amount_origins_sha256')):
        if sha(model / name) != receipt[key]:
            raise ValueError('Raw model artifact hash differs: ' + name)
    expectations = comparison.parent / 'stage-expectations.jsonl.gz'
    if sha(expectations) != oracle['expectations_sha256']:
        raise ValueError('Historical expectation stream hash differs')
    count, logical_bytes, terminal = 0, 0, None
    with gzip.open(expectations, 'rb') as stream:
        for raw in stream:
            count += 1
            logical_bytes += len(raw)
            if len(raw) > 2 * 1024 * 1024 or logical_bytes > 1024**3:
                raise ValueError('Expectation stream exceeds fixed budgets')
            terminal = json.loads(raw)
    if count != oracle['compared_stages'] + 1 or logical_bytes != oracle['expected_uncompressed_bytes']:
        raise ValueError('Incomplete historical expectation stream')
    expected = terminal['expected']
    state = json.loads((model / 'final-state.json').read_text())
    summary = json.loads((model / 'final-summary.json').read_text())
    last_summary = None
    with (model / 'stages.jsonl').open('rb') as stream:
        for raw in stream:
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError('Model summary record exceeds fixed budget')
            last_summary = json.loads(raw)['summary']
    if summary != last_summary:
        raise ValueError('Final summary is not bound to the recorded model stages')
    summary_content = {k: v for k, v in summary.items() if k != 'summary_sha256'}
    if hashlib.sha256(json.dumps(summary_content, sort_keys=True,
            separators=(',', ':')).encode()).hexdigest() != summary['summary_sha256']:
        raise ValueError('Final summary content hash differs')
    own = state['independent_opening_owner']
    checks = {'terminal.' + key: state[key] == value
        for key, value in expected['projection'].items() if key in state}
    names = dict(units='units424', areas='areas88', pickups='pickups56',
        windows='windows8', boundaries='boundaries8', special='special40', companions='companions88')
    for name, label in names.items():
        vector = expected['vectors'][name]
        checks['owner.' + name] = owner(vector['storage'], vector['count']) == summary['owners'][label]
    checks['guardian_cooldowns'] = own['guardian_cooldowns'] == expected['projection']['guardian_cooldowns']
    packets = own['produced_packets']
    checks['all_declared_actor169'] = actor_creates(packets) == expected['projection']['explicit_actor_creates169']
    checks['all_banner150'] = [p for opcode, p in packets if opcode == 150] == expected['projection']['banner150_packets']
    checks['opaque_pickup_origins'] = json.loads((model / 'opaque-pickup-amount-origins.json').read_text()) == expected['opaque_pickup_amount_origins']
    shared = {n: h for n, h in oracle['source_sha256_before'].items() if n.startswith('reconstruction/')}
    checks['shared_production_sources'] = bool(shared) and all(
        receipt['source_sha256_before'].get(n) == receipt['source_sha256_after'].get(n) == h
        for n, h in shared.items())
    checks['model_sources_stable'] = receipt['production_source_unchanged'] and receipt['source_sha256_before'] == receipt['source_sha256_after']
    checks['assets_stable'] = receipt['assets_unchanged']
    checks['no_original_or_preparsed_inputs'] = all(receipt[k] is False for k in (
        'original_program_executed', 'original_memory_read', 'original_wasm_executed', 'preparsed_world_input_read'))
    checks['frame_and_selection_counts'] = (receipt['independent_frames'], receipt['independent_selections']) == (oracle['independent_frames'], oracle['independent_selections'])
    world_hashes = {Path(n).name: h for n, h in oracle['world_input']['artifacts'].items()}
    for artifact in receipt['world_artifacts'].values():
        path = external(model / artifact['file'])
        checks['world.' + artifact['file']] = sha(path) == artifact['sha256'] == world_hashes.get(artifact['file'])
    result = dict(kind='raw_assets_to_existing_scoped_differential_terminal_model_bridge',
        checks=checks, all_passed=all(checks.values()), shared_production_count=len(shared),
        expected_records=count, model_receipt_sha256=sha(model / 'receipt.json'),
        original_comparison_sha256=sha(comparison), driver_sha256=sha(Path(__file__)),
        model_directory=str(model), comparison=str(comparison),
        final_summary_sha256=sha(model / 'final-summary.json'),
        new_original_cases=0, full880_frames=0, native_windows_execution=False,
        scope='Terminal model composition only; not a new original execution or per-stage raw-asset differential.')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(path=str(output), checks=len(checks), all_passed=result['all_passed'])))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
