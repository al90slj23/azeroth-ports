#!/usr/bin/env python3
"""Differentially check log1p helper35684 and a recovered radius composition.

Original35684 alone is executed; the934 callsite is composed separately in
JS around that helper, and is explicitly not original934 execution. Non-NaN
results compare by uint32 bits, NaNs only by category. No game, network/save.
"""
import hashlib
import json
import os
import random
import signal
import subprocess
import sys

from build_radius_oracle import ROOT, build

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.radius import log1p_helper_bits, radius_bits

SEED = 0xa2e35684
FUNCTIONS = {'helper': log1p_helper_bits, 'radius_composition': radius_bits}


def corpus():
    cases = []
    def add(group, mode, bits):
        cases.append({'id': len(cases), 'group': group, 'mode': mode, 'input_bits': bits})
    def near(group, mode, center, distance=8):
        for delta in range(-distance, distance + 1):
            bits = center + delta
            if 0 <= bits <= 0xffffffff:
                add(group, mode, bits)
    edges = (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x807fffff,
             0x00800000, 0x80800000, 0x3f7fffff, 0x3f800000, 0x3f800001,
             0xbf7fffff, 0xbf800000, 0xbf800001, 0x7f7fffff, 0xff7fffff,
             0x7f800000, 0xff800000, 0x7fc00000, 0x7fa00001, 0xffc12345,
             0x7fffffff, 0xffffffff)
    for mode in FUNCTIONS:
        for bits in edges:
            add('special_values', mode, bits)
    for threshold in (0x3ed413cf, 0xbf7fffff, 0xbf800000, 0x33800000,
                      0xb3800000, 0xbe95f619, 0x00800000, 0x80800000,
                      0x7f7fffff):
        near('helper_branch_neighbors', 'helper', threshold, 32)
    # Powers and neighboring inputs exercise all magnitude/exponent ranges,
    # both series-only paths and range reduction, with deterministic coverage.
    for exponent in range(1, 255):
        for sign in (0, f.SIGN):
            near('helper_exponent_neighbors', 'helper', sign | (exponent << 23), 1)
    for value in (-1, -.9999999, -.5, -.2928932, -.1, .1, .4142135,
                  .5, 1, 2, 3, 7, 8, 15, 16, 127, 128, 255, 256,
                  2**23, 2**24, 2**25):
        near('helper_magnitude_neighbors', 'helper', f.from_float(value))
    for bits in (0x3fd863ef, 0x410ab6b7, 0x419e8f4f, 0x410425b7,
                 0x3fd25615, 0x7baa2333, 0x3ee2e2cc, 0x3eab109d):
        # These previously differ by one ULP from a correctly rounded
        # mathematical log1p. They distinguish the recovered approximation.
        add('known_mathematical_log1p_one_ulp_distinctions', 'helper', bits)
    near('radius_threshold_neighbors', 'radius_composition', f.from_float(70), 128)
    for value in (-100, -1, 0, 1, 69, 70, 71, 75, 80, 90, 100, 140, 200, 1000, 1000000):
        near('radius_game_magnitude_neighbors', 'radius_composition', f.from_float(value))
    rng = random.Random(SEED)
    for _ in range(20000):
        add('helper_seeded_raw_binary32', 'helper', rng.getrandbits(32))
    for _ in range(2000):
        add('helper_seeded_domain', 'helper', f.from_float(rng.uniform(-1, 10000)))
    for _ in range(3000):
        add('radius_seeded_raw_binary32', 'radius_composition', rng.getrandbits(32))
    for _ in range(1000):
        add('radius_seeded_game_range', 'radius_composition', f.from_float(rng.uniform(0, 10000)))
    return cases


def main():
    output, oracle = build()
    cases = corpus()
    cases_file = output / 'cases.jsonl'
    cases_file.write_text(''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in cases))
    expected = [{'id': c['id'], 'bits': FUNCTIONS[c['mode']](c['input_bits'])} for c in cases]
    model_file = output / 'model-results.jsonl'
    model_file.write_text(''.join(json.dumps(c) + '\n' for c in expected))
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    observed_file = output / 'original-helper-results.jsonl'
    command = [str(runtime), '--max-old-space-size=128', str(ROOT / 'scripts/run_radius_oracle.mjs'),
               str(output / oracle['module_file']), str(cases_file), str(output / 'manifest.json')]
    with observed_file.open('w') as out, (output / 'oracle.stderr.log').open('w') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            raise SystemExit('Owned one-helper oracle exceeded deadline and was stopped')
    if code:
        raise SystemExit('One-helper oracle failed; inspect its local stderr')
    actual = [json.loads(line) for line in observed_file.read_text().splitlines()]
    if len(actual) != len(cases) or [x['id'] for x in actual] != list(range(len(cases))):
        raise SystemExit('Oracle case coverage/order differs')
    mismatches = []
    comparisons = {name: {'case_count': 0, 'non_nan_u32_bit_pairs': 0, 'nan_category_pairs': 0,
                          'mismatch_count': 0} for name in FUNCTIONS}
    groups = {}
    for c, want, got in zip(cases, expected, actual):
        counts = comparisons[c['mode']]
        counts['case_count'] += 1
        groups[c['group']] = groups.get(c['group'], 0) + 1
        if f.is_nan(want['bits']) and f.is_nan(got['bits']):
            counts['nan_category_pairs'] += 1
        elif want['bits'] == got['bits']:
            counts['non_nan_u32_bit_pairs'] += 1
        else:
            counts['mismatch_count'] += 1
            mismatches.append({'input': c, 'model': want, 'original_helper_or_composition': got})
    mismatch_file = output / 'mismatches.json'
    mismatch_file.write_text(json.dumps(mismatches, indent=2) + '\n')
    files = [ROOT / 'scripts/build_radius_oracle.py', ROOT / 'scripts/check_radius_spec.py',
             ROOT / 'scripts/run_radius_oracle.mjs', ROOT / 'scripts/wasm_index.py',
             ROOT / 'reconstruction/core_spec/binary32.py', ROOT / 'reconstruction/core_spec/radius.py']
    artifacts = [cases_file, model_file, observed_file, mismatch_file, output / 'manifest.json',
                 output / 'oracle.stderr.log', output / oracle['module_file']]
    summary = {'version': '0.126.0', 'build': '3e72472a',
               'original_wasm_sha256': oracle['original_wasm_sha256'],
               'original_wasm_bytes': oracle['original_wasm_bytes'],
               'original_function_index': oracle['original_function_index'],
               'original_body_sha256': oracle['body_sha256'], 'original_body_bytes': oracle['body_bytes'],
               'oracle_module_sha256': oracle['module_sha256'], 'oracle_module_bytes': oracle['module_bytes'],
               'body_byte_identical': True, 'defined_original_functions': 1,
               'case_count': len(cases), 'comparisons': comparisons, 'groups': groups,
               'mismatch_count': len(mismatches), 'seed': hex(SEED),
               'original_helper35684_executed': True, 'original_function934_executed': False,
               'radius_composition_scope': 'JS ordered-f32 extracted934 callsite plus original35684; not execution of original934',
               'full_game_started': False, 'host_imports': [], 'start_function': None,
               'network_used': False, 'user_saves_accessed': False, 'installed_game_modified': False,
               'memory': oracle['memory'], 'global0': oracle['global0'],
               'arithmetic_model': 'exact rational add/sub/mul/div with each binary32 nearest-even rounding; instruction-order helper approximation',
               'runtime_version': subprocess.check_output([str(runtime), '--version'], text=True).strip(),
               'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
               'artifact_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
               'limitations': ['Finite deterministic corpus is not exhaustive verification of all2^32 inputs.',
                               'NaN payload/sign/signaling state are not compared or generally preserved.',
                               'Radius composition is recovered callsite arithmetic, not original934 or all ability radius state.',
                               'No complete game loop, graphics, official server or user save was executed.']}
    (output / 'differential-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'run_directory': str(output), 'case_count': len(cases), 'comparisons': comparisons,
                      'mismatch_count': len(mismatches), 'original_helper35684_executed': True,
                      'original_function934_executed': False, 'full_game_started': False, 'network_used': False}))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
