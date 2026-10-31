#!/usr/bin/env python3
"""Compare independent ordered-f32 enemy curves against unchanged WASM bodies.

Finite results, infinities and signed zeros compare by uint32 bits. NaNs only
compare by category; neither JavaScript nor our model preserves NaN payloads.
No full game, official service, user save or installed package is accessed.
"""
import hashlib
import json
import os
import random
import signal
import subprocess
import sys

from build_enemy_scaling_oracle import ROOT, build

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.binary32 import from_float, is_nan
from core_spec.enemy_scaling import elite_growth_bits, normal_growth_bits

FUNCTIONS = {'elite_growth': elite_growth_bits, 'normal_growth': normal_growth_bits}
SEED = 0xa2e95640


def corpus():
    cases = []
    def add(group, name, time, zone):
        cases.append({'id': len(cases), 'group': group, 'export': name,
                      'time_bits': time, 'zone_bits': zone})
    edges = (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x807fffff,
             0x00800000, 0x80800000, 0x3dcccccc, 0x3dcccccd, 0x3dccccce,
             0x3f7fffff, 0x3f800000, 0x3f800001, 0xbf800000,
             0x4affffff, 0x4b000000, 0x4b000001, 0x7f7fffff, 0xff7fffff,
             0x7f800000, 0xff800000, 0x7fc00000, 0x7fa00001, 0xffc12345)
    for name in FUNCTIONS:
        for time in edges:
            for zone in edges:
                add('raw_bit_boundary_cross_product', name, time, zone)
        for time in (0, .001, .5, 1, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 16, 18, 20, 30, 60, 120, 1000):
            for zone in (.82, .97, 1.17, 1.32, 1.5, 2.05, 2.95, 2.33, 4.14, 3.26, 6.25):
                t = from_float(time); z = from_float(zone)
                for near in (-1, 0, 1):
                    add('game_minutes_zones_adjacent_representations', name, max(0, t + near), z)
    rng = random.Random(SEED)
    for index in range(20000):
        add('seeded_raw_binary32_patterns', tuple(FUNCTIONS)[index % 2], rng.getrandbits(32), rng.getrandbits(32))
    for index in range(2000):
        add('seeded_game_range', tuple(FUNCTIONS)[index % 2], from_float(rng.uniform(0, 240)), from_float(rng.uniform(.1, 100)))
    return cases


def main():
    output, oracle = build()
    cases = corpus(); cases_file = output / 'cases.jsonl'
    cases_file.write_text(''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in cases))
    expected = [{'id': c['id'], 'bits': FUNCTIONS[c['export']](c['time_bits'], c['zone_bits'])} for c in cases]
    (output / 'model-results.jsonl').write_text(''.join(json.dumps(c) + '\n' for c in expected))
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    observed_file = output / 'original-function-results.jsonl'
    command = [str(runtime), '--max-old-space-size=128', str(ROOT / 'scripts/run_enemy_scaling_oracle.mjs'),
               str(output / oracle['module_file']), str(cases_file)]
    with observed_file.open('w') as out, (output / 'oracle.stderr.log').open('w') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait()
            raise SystemExit('Owned numerical oracle exceeded its deadline and was stopped')
    if code:
        raise SystemExit('Pure-function oracle failed; inspect its local stderr')
    actual = [json.loads(x) for x in observed_file.read_text().splitlines()]
    if len(actual) != len(cases) or [x['id'] for x in actual] != list(range(len(cases))):
        raise SystemExit('Oracle fixture coverage/order differs')
    mismatches = []
    nan_pairs = bit_pairs = 0
    for c, want, got in zip(cases, expected, actual):
        if is_nan(want['bits']) and is_nan(got['bits']):
            nan_pairs += 1
        elif want['bits'] == got['bits']:
            bit_pairs += 1
        else:
            mismatches.append({'input': c, 'model': want, 'original': got})
    (output / 'mismatches.json').write_text(json.dumps(mismatches, indent=2) + '\n')
    groups = {}
    for c in cases:
        groups[c['group']] = groups.get(c['group'], 0) + 1
    files = [ROOT / 'scripts/build_enemy_scaling_oracle.py', ROOT / 'scripts/check_enemy_scaling.py',
             ROOT / 'scripts/run_enemy_scaling_oracle.mjs', ROOT / 'reconstruction/core_spec/binary32.py',
             ROOT / 'reconstruction/core_spec/enemy_scaling.py']
    summary = {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': oracle['original_wasm_sha256'],
               'original_functions': [{k: f[k] for k in ('original_function_index', 'oracle_function_index', 'body_bytes', 'body_sha256')} for f in oracle['functions']],
               'oracle_module_sha256': oracle['module_sha256'], 'body_byte_identical': True,
               'case_count': len(cases), 'groups': groups, 'mismatch_count': len(mismatches),
               'non_nan_pairs_compared_by_u32_bits': bit_pairs, 'nan_pairs_compared_by_category_only': nan_pairs,
               'seed': hex(SEED), 'isolated_original_functions_executed': True,
               'full_game_started': False, 'host_imports': [], 'network_used': False, 'user_saves_accessed': False,
               'installed_game_modified': False,
               'arithmetic_model': 'exact rational operations with per-operation binary32 nearest-even rounding; original evaluation order',
               'runtime_version': subprocess.check_output([str(runtime), '--version'], text=True).strip(),
               'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
               'limitations': ['These two HP-growth functions do not reconstruct the entire spawn formula or game.',
                               'NaN payload, sign and signaling state are not compared or preserved.',
                               'Deterministic differential agreement is evidence, not exhaustive verification of all 2^64 inputs per function.']}
    (output / 'differential-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'run_directory': str(output), 'case_count': len(cases), 'mismatch_count': len(mismatches),
                      'non_nan_bit_pairs': bit_pairs, 'nan_category_pairs': nan_pairs,
                      'isolated_original_functions_executed': True, 'full_game_started': False, 'network_used': False}))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
