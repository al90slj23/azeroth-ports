#!/usr/bin/env python3
"""Differentially compare an independent rule model with one original function.

The isolated micro-module has no host imports/start/game entrypoint. Only the
unchanged original function25242 is executed; all other bodies are trap stubs.
Fixtures are invented deterministic local inputs, never saves or live traffic.
"""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import struct
import subprocess
import sys

from build_upgrade_oracle import ROOT, build

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import UpgradeState, upgrade_value_bits
from core_spec.upgrade_values import TABLES


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


def main():
    output, oracle = build()
    # The independently written numeric constants must match the copied original tables.
    for model, original in zip(TABLES, oracle['tables']):
        assert struct.pack('<5I', *model).hex() == original['raw_hex']
    inputs = corpus()
    cases = output / 'cases.jsonl'
    cases.write_text(''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in inputs))
    expected = []
    for case in inputs:
        try:
            expected.append({'id': case['id'], 'bits': upgrade_value_bits(case['kind'], case['tier'], state_from_case(case))})
        except ValueError:
            expected.append({'id': case['id'], 'trapped': True})
    (output / 'model-results.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in expected))
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    actual_file = output / 'original-function-results.jsonl'
    command = [str(runtime), '--max-old-space-size=512', str(ROOT / 'scripts/run_upgrade_oracle.mjs'),
               str(output / oracle['module_file']), str(cases)]
    with actual_file.open('w') as out, (output / 'oracle.stderr.log').open('w') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait()
            raise SystemExit('Owned pure-function oracle exceeded its deadline and was stopped')
    if code:
        raise SystemExit('Original-function oracle failed; inspect its local stderr')
    actual = [json.loads(line) for line in actual_file.read_text().splitlines()]
    if len(actual) != len(inputs) or [x['id'] for x in actual] != list(range(len(inputs))):
        raise SystemExit('Oracle result coverage/order differs from input corpus')
    mismatches = [{'input': case, 'model': predicted, 'original': observed}
                  for case, predicted, observed in zip(inputs, expected, actual) if predicted != observed]
    (output / 'mismatches.json').write_text(json.dumps(mismatches, indent=2) + '\n')
    groups = {}
    for case in inputs:
        groups[case['group']] = groups.get(case['group'], 0) + 1
    files = [ROOT / 'scripts/build_upgrade_oracle.py', ROOT / 'scripts/check_upgrade_spec.py',
             ROOT / 'scripts/run_upgrade_oracle.mjs', ROOT / 'reconstruction/core_spec/binary32.py',
             ROOT / 'reconstruction/core_spec/upgrade_values.py']
    summary = {'version': '0.126.0', 'build': '3e72472a',
               'original_wasm_sha256': oracle['original_wasm_sha256'],
               'original_function_index': 25242, 'original_body_sha256': oracle['original_body_sha256'],
               'oracle_module_sha256': oracle['module_sha256'], 'body_byte_identical': True,
               'case_count': len(inputs), 'groups': groups, 'mismatch_count': len(mismatches),
               'valid_numeric_results_compared_by_u32_bits': sum('bits' in x for x in expected),
               'invalid_tier_traps_compared': sum('trapped' in x for x in expected),
               'seed': '0xA2E2026', 'isolated_original_function_executed': True,
               'full_game_started': False, 'host_imports': [], 'network_used': False,
               'user_saves_accessed': False, 'installed_game_modified': False,
               'arithmetic_model': 'exact rational operations with per-operation binary32 nearest-even rounding',
               'runtime_version': subprocess.check_output([str(runtime), '--version'], text=True).strip(),
               'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
               'limitations': ['Covers the supported five upgrade kinds/tiers, not the complete game.',
                               'No float32 NaN payload identity claim; recovered routine clamps NaN factors to zero.',
                               'Bounds panic is replaced with an unreachable stub; original panic text/host behavior is not compared.',
                               'Deterministic corpus agreement is differential evidence, not exhaustive enumeration of every possible input.']}
    (output / 'differential-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'run_directory': str(output), 'case_count': len(inputs),
                      'mismatch_count': len(mismatches), 'isolated_original_function_executed': True,
                      'full_game_started': False, 'network_used': False}))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
