#!/usr/bin/env python3
"""Compare the unchanged production numeric model against official 0.134.0.

The deterministic 11,560-case corpus is regenerated here, with its serialized
identity pinned to the historical corpus for like-for-like version acceptance.
Every observation comes from the new 25368 body; historical result files are
neither read nor accepted as current evidence.
"""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import struct
import subprocess
import sys
import time

from build_upgrade134_oracle import (ROOT, SOURCE, SOURCE_SHA, SIDE, SIDE_SHA, VALIDATOR,
                                     VALIDATOR_SHA, ARCHIVE, ARCHIVE_SHA, BODY_SHA,
                                     VERSION, BUILD, TARGET, PANIC, build, require, sha,
                                     save, strict_json, verify_micro)

MODEL_HASHES = {
    'reconstruction/core_spec/__init__.py': '2d4def898123e75c5e15d0586ccaedb98017833663f6cbefd13c73991e0502e2',
    'reconstruction/core_spec/binary32.py': '7a2cba21a680d30986c0ff730348bd2f29ef6f412cbb204ceaf730a3112ed482',
    'reconstruction/core_spec/upgrade_values.py': 'aaefe8bca626a25589b51f454a20ff1b9654c77f33e5a23e32930444e95efc00',
}
require(all(sha(ROOT / name) == digest for name, digest in MODEL_HASHES.items()), 'Pinned production model identity differs before import')
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import UpgradeState, upgrade_value_bits
from core_spec.upgrade_values import TABLES

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
RUNTIME_VERSION = 'v22.23.4'
CORPUS_SHA = 'fb64c891ee1e72b3876e5e2b94a2818f648da8b2f8a61642d99e4ab9c7dd4373'


def corpus():
    inputs = []
    def add(group, kind, tier, state):
        inputs.append({'id': len(inputs), 'group': group, 'kind': kind, 'tier': tier,
                       'state': {'counts': list(state.counts), 'field16_bits': state.field16_bits,
                                 'field20_u32': state.field20_u32, 'field24_bits': state.field24_bits,
                                 'field28_bits': state.field28_bits, 'definition_kind': state.definition_kind,
                                 'definition_id_hex': state.definition_id.hex()}})
    default = UpgradeState()
    for kind in range(5):
        for tier in range(5):
            add('all_kind_tier_pairs', kind, tier, default)
    for count in (0, 1, 2, 3, 255, 65535, 16777215, 16777216, 16777217, 0x80000000, 0xffffffff):
        for tier in range(5):
            add('u32_counter_rounding', 0, tier, replace(default, counts=(count, 0, 0, 0, 0)))
    edges = (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x00800000,
             0x3e4ccccc, 0x3e4ccccd, 0x3e4cccce, 0x3f4ccccd,
             0x3f7fffff, 0x3f800000, 0x3f800001, 0x409fffff, 0x40a00000,
             0x40a00001, 0x40bfffff, 0x40c00000, 0x40c00001,
             0x7f7fffff, 0xff7fffff, 0x7f800000, 0xff800000,
             0x7fc00000, 0x7fa00001, 0xffc12345)
    for kind, field in ((1, 'field16_bits'), (3, 'field24_bits'), (4, 'field28_bits')):
        for bits in edges:
            for tier in range(5):
                add('f32_edges_thresholds_nan_infinity', kind, tier, replace(default, **{field: bits}))
    names = (b'', b'seal_fate', b'soul_fire', b'lightwell', b'faerie_fire', b'fireball',
             b'SEAL_FATE', b'seal_fatf', b'\xff' * 9)
    for definition_kind in (0, 11, 255):
        for name in names:
            for count in (0, 1, 2, 3, 11, 12, 13, 0xffffffff):
                for tier in range(5):
                    add('caps_identifiers_and_u32_edges', 2, tier,
                        replace(default, field20_u32=count, definition_kind=definition_kind, definition_id=name))
    rng = random.Random(0xA2E2026)
    for index in range(10000):
        state = UpgradeState(counts=tuple(rng.getrandbits(32) for _ in range(5)),
                             field16_bits=rng.getrandbits(32), field20_u32=rng.getrandbits(32),
                             field24_bits=rng.getrandbits(32), field28_bits=rng.getrandbits(32),
                             definition_kind=rng.choice((0, 11, 255)), definition_id=rng.choice(names))
        add('seeded_raw_bit_patterns', index // 5 % 5, index % 5, state)
    for kind in range(5):
        for tier in (5, -1):
            add('invalid_tier_trap', kind, tier, default)
    return inputs


def state_from_case(case):
    values = dict(case['state'])
    values['counts'] = tuple(values['counts'])
    values['definition_id'] = bytes.fromhex(values.pop('definition_id_hex'))
    return UpgradeState(**values)


def write_jsonl(path, records, compact=False):
    options = {'separators': (',', ':')} if compact else {}
    path.write_text(''.join(json.dumps(c, allow_nan=False, **options) + '\n' for c in records))
    require([strict_json(line) for line in path.read_text().splitlines()] == records,
            'JSONL artifact readback differs')


def main():
    files = [ROOT / 'scripts/build_upgrade134_oracle.py', ROOT / 'scripts/check_upgrade134_spec.py',
             ROOT / 'scripts/run_upgrade134_oracle.mjs', ROOT / 'reconstruction/core_spec/__init__.py',
             ROOT / 'reconstruction/core_spec/binary32.py', ROOT / 'reconstruction/core_spec/upgrade_values.py']
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    require(sha(RUNTIME) == RUNTIME_SHA, 'Pinned Node executable identity differs')
    require(subprocess.check_output([str(RUNTIME), '--version'], text=True, timeout=10).strip() == RUNTIME_VERSION,
            'Pinned Node runtime version differs')
    output, oracle = build()
    require(len(TABLES) == len(oracle['tables']) == 5, 'Model/table count differs')
    for model, table in zip(TABLES, oracle['tables']):
        require(struct.pack('<5I', *model).hex() == table['raw_hex'], 'Production model differs from new source table')
    inputs = corpus()
    require(len(inputs) == 11560, 'Deterministic corpus coverage differs')
    cases = output / 'cases.jsonl'
    write_jsonl(cases, inputs, compact=True)
    require(sha(cases) == CORPUS_SHA, 'Regenerated corpus is not the same 11,560-case comparison')
    expected = []
    for case in inputs:
        try:
            expected.append({'id': case['id'], 'bits': upgrade_value_bits(case['kind'], case['tier'], state_from_case(case))})
        except ValueError:
            require(case['group'] == 'invalid_tier_trap' and case['tier'] in (-1, 5), 'Unexpected model error')
            expected.append({'id': case['id'], 'trapped': True})
    write_jsonl(output / 'model-results.jsonl', expected)
    before = {p.name: sha(p) for p in output.iterdir() if p.is_file()}
    actual_file = output / 'official0134-function-results.jsonl'
    command = [str(RUNTIME), '--max-old-space-size=512', str(ROOT / 'scripts/run_upgrade134_oracle.mjs'),
               str(output / oracle['module_file']), str(cases), oracle['module_sha256'], CORPUS_SHA]
    started = time.monotonic()
    invocation = {'arguments': command, 'deadline_seconds': 45, 'started_utc': datetime.now(timezone.utc).isoformat(),
                  'stdout_file': actual_file.name, 'stderr_file': 'oracle.stderr.log'}
    with actual_file.open('w') as out, (output / 'oracle.stderr.log').open('w') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        invocation.update({'pid': child.pid, 'process_group_id': child.pid})
        save(output / 'invocation.json', invocation)
        try:
            code = child.wait(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            invocation.update({'deadline_exceeded': True, 'exit_code': child.returncode})
            save(output / 'invocation.json', invocation)
            raise SystemExit('Owned 0.134.0 pure-function oracle exceeded its deadline and was stopped')
    invocation.update({'exit_code': code, 'elapsed_seconds': round(time.monotonic() - started, 6),
                       'finished_utc': datetime.now(timezone.utc).isoformat(), 'deadline_exceeded': False})
    save(output / 'invocation.json', invocation)
    require(code == 0, '0.134.0 numeric oracle failed; inspect local stderr')
    actual = [strict_json(line) for line in actual_file.read_text().splitlines()]
    require(len(actual) == len(inputs), 'Oracle result coverage differs')
    for index, record in enumerate(actual):
        require(type(record.get('id')) is int and record['id'] == index, 'Oracle result order differs')
        if 'bits' in record:
            require(set(record) == {'id', 'bits'} and type(record['bits']) is int
                    and 0 <= record['bits'] <= 0xffffffff, 'Invalid numeric result schema')
        else:
            require(set(record) == {'id', 'trapped'} and record['trapped'] is True, 'Invalid trap result schema')
    mismatches = [{'input': c, 'model': p, 'official0134': a}
                  for c, p, a in zip(inputs, expected, actual) if p != a]
    save(output / 'mismatches.json', mismatches)
    for filename, digest in before.items():
        require(sha(output / filename) == digest, 'Input artifact changed during oracle execution: ' + filename)
    require({str(p.relative_to(ROOT)): sha(p) for p in files} == source_hashes, 'Implementation/model changed during run')
    require(sha(SOURCE) == SOURCE_SHA and sha(SIDE) == SIDE_SHA and sha(RUNTIME) == RUNTIME_SHA
            and sha(VALIDATOR) == VALIDATOR_SHA and sha(ARCHIVE) == ARCHIVE_SHA, 'Pinned source/tool changed during run')
    manifest = strict_json((output / 'manifest.json').read_text())
    require(manifest == oracle and sha(output / oracle['module_file']) == oracle['module_sha256'], 'Oracle manifest/module readback differs')
    # Re-extract from official source independently after execution and reparse the entire artifact again.
    binary = SOURCE.read_bytes()
    original_body = binary[oracle['original_body_start']:oracle['original_body_end']]
    require(hashlib.sha256(original_body).hexdigest() == BODY_SHA, 'Final official body readback differs')
    signatures = [(bytes.fromhex(x['parameters_hex']), bytes.fromhex(x['results_hex'])) for x in oracle['source_signatures']]
    require(verify_micro((output / oracle['module_file']).read_bytes(), original_body, signatures, oracle['tables'])
            == oracle['independent_artifact_reparse'], 'Final independent module reparse differs')
    groups = {}
    for case in inputs:
        groups[case['group']] = groups.get(case['group'], 0) + 1
    artifacts = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                 for p in sorted(output.iterdir()) if p.is_file()}
    summary = {'status': 'passed' if not mismatches else 'failed', 'date': '2026-11-01',
               'version': VERSION, 'build': BUILD, 'original_wasm_sha256': SOURCE_SHA,
               'original_function_index': TARGET, 'original_body_sha256': BODY_SHA,
               'original_target_type_index': oracle['original_target_type_index'],
               'original_panic_type_index': oracle['original_panic_type_index'],
               'oracle_module_sha256': oracle['module_sha256'], 'body_byte_identical': True,
               'case_count': len(inputs), 'groups': groups, 'mismatch_count': len(mismatches),
               'valid_numeric_results_compared_by_u32_bits': sum('bits' in x for x in expected),
               'invalid_tier_traps_compared': sum('trapped' in x for x in expected),
               'invalid_tier_domain': [-1, 5], 'supported_kind_domain': [0, 1, 2, 3, 4],
               'supported_tier_domain': [0, 1, 2, 3, 4], 'seed': '0xA2E2026',
               'corpus_sha256': CORPUS_SHA, 'historical_case_and_result_files_read': False,
               'isolated_original0134_function_executed': True, 'full_original_module_instantiated': False,
               'full_game_started': False, 'host_imports': [], 'network_used': False,
               'user_saves_accessed': False, 'installed_game_modified': False,
               'arithmetic_model': 'unchanged production core_spec/upgrade_values.py; exact rational arithmetic with per-operation binary32 nearest-even rounding',
               'runtime': {'version': RUNTIME_VERSION, 'sha256': RUNTIME_SHA},
               'tool_identity': oracle['tool_identity'], 'source_sha256': source_hashes,
               'static_helper_sidecar': oracle['static_helper_sidecar'],
               'tables': oracle['tables'], 'source_locations': oracle['source_locations'],
               'artifact_reparse': oracle['independent_artifact_reparse'],
               'owned_oracle_process': invocation, 'run_directory': str(output), 'artifacts': artifacts,
               'source_and_artifact_readback_verified': True,
               'support_claim': 'The existing independent upgrade-value model is accepted against official 0.134.0 function25368 for this supported API and deterministic corpus.',
               'limitations': ['This validates one numeric helper, not card application, other models, the complete core, or whole-game behavior.',
                               'The production model docstring retains its historical 0.126.0 origin; its unchanged source was accepted here against the new official body.',
                               'NaN inputs exercise the original clamp-to-zero behavior; no general NaN payload preservation is claimed.',
                               'Bounds-panic80662 is replaced with unreachable. Only invalid-tier trap class is compared; original panic text and host behavior are outside scope.',
                               'Kinds outside0..4 are not part of this independent API; the official dispatcher masks kind with255 and has separate defaults.',
                               'A matching deterministic corpus is differential evidence, not exhaustive enumeration of every possible input.']}
    if mismatches:
        summary['support_claim'] = 'No 0.134.0 acceptance: differential mismatches require investigation.'
    save(output / 'differential-summary.json', summary)
    report = {**summary, 'evidence_summary_file': str(output / 'differential-summary.json'),
              'evidence_summary_sha256': sha(output / 'differential-summary.json')}
    reports = ROOT / 'reports'
    save(reports / '2026-11-01-upgrade0134-spec.json', report)
    text = f'''# Official 0.134.0 upgrade-value differential acceptance

The unchanged independent `core_spec/upgrade_values.py` model was compared with
the **new official 0.134.0 / 983346a7 function25368**: **{len(inputs):,} cases,
{len(mismatches)} mismatches**. Valid values are compared by exact binary32 u32
bits; 10 invalid-tier cases compare the trap class. Status: **{summary['status']}**.

| Evidence | Result |
| --- | --- |
| Official WASM SHA256 | `{SOURCE_SHA}` |
| New original body | `[49645485,49646105)`, 620B; `{BODY_SHA}` |
| Re-read signatures | original type94 `(i32,i32,i32)->f32`; panic80662 type1 `(i32,i32,i32)->()` |
| Micro-module | 404145B; `{oracle['module_sha256']}` |
| Reparse | 80,663 declarations and complete bodies, two signatures, all five active data segments verified |
| Memory | fixed83 pages; no imports, start, globals, table or game entrypoint |
| Corpus | regenerated locally; `{CORPUS_SHA}`; historical result files not read |
| Node | {RUNTIME_VERSION}; `{RUNTIME_SHA}` |
| WABT | 1.0.42; pinned archive/executable; wasm-validate exit0 |
| Process | owned PID/PGID; 45s deadline; exit{code}; {invocation['elapsed_seconds']}s |

| Corpus group | Cases |
| --- | ---: |
''' + ''.join(f"| {name} | {count:,} |\n" for name, count in groups.items()) + f'''

Five tables were extracted again through the new source's active-data mappings,
then compared with the existing model and re-read from the assembled module.
The new abilities.rs source locations are202/204/211/214/217. The complete new
body is copied byte-for-byte; the previous version's body and fixture outputs
are not used. All non-target bodies, including panic80662, are trap placeholders.

This acceptance covers upgrade kinds0..4 and tiers0..4 plus invalid tiers-1/5.
It supports this one existing independent numeric model against official
0.134.0. It does not establish card-application behavior, other model support,
whole-core equivalence or a playable replacement. Invalid-tier observations
establish a trap category; original panic text/host behavior is not reproduced.
NaN inputs exercise clamp-to-zero behavior without a NaN-payload claim.

No full original module was instantiated. No game, host binding, network, save,
installed-game mutation, commit or push was performed by this checker.

Reproduce: `python3 reverse-engineering/scripts/check_upgrade134_spec.py`.
Raw ignored artifacts: `{output.relative_to(ROOT)}`. The adjacent JSON records
all script/model/tool hashes, every artifact's size/hash, per-group coverage,
process provenance and the summary artifact hash. Source and artifact readback
checks completed after the run.
'''
    (reports / '2026-11-01-upgrade0134-spec.md').write_text(text)
    require((reports / '2026-11-01-upgrade0134-spec.md').read_text() == text, 'Markdown artifact readback differs')
    print(json.dumps({'run_directory': str(output), 'version': VERSION, 'case_count': len(inputs),
                      'mismatch_count': len(mismatches), 'isolated_original0134_function_executed': True,
                      'full_game_started': False, 'network_used': False}, allow_nan=False))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
