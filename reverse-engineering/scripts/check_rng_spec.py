#!/usr/bin/env python3
"""Differential range results AND four-word state, including chained calls.

The original sampler body is unmodified. Its invalid-range panic callee is a
replacement trap; agreement there is limited to branch/trap and unchanged
RNG memory. The original panic implementation/initializer/game is not run.
"""
import hashlib
import json
import os
import random
import signal
import subprocess
import sys

from build_rng_oracle import ROOT, build

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.binary32 import from_float, to_float
from core_spec.rng import RngRangeError, uniform_range_bits

SEED = 0xa2e32475


def corpus():
    cases = []
    def add(group, state, low, high, **extra):
        c = {'id': len(cases), 'group': group, 'low_bits': low, 'high_bits': high, **extra}
        if state is not None:
            c['state'] = state
        cases.append(c)
    edges = (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x807fffff,
             0x00800000, 0x80800000, 0x3f000000, 0x3f7fffff, 0x3f800000,
             0x3f800001, 0xbf800001, 0xbf800000, 0xbf7fffff,
             0x4b000000, 0x4b000001, 0x7f7ffffe, 0x7f7fffff, 0xff7fffff,
             0x7f800000, 0xff800000, 0x7fc00000, 0x7fa00001, 0xffc12345)
    states = ([0, 0, 0, 0], [1, 2, 3, 4], [0xffffffff] * 4,
              [0, 0, 0, 0xffffffff], [1, 0, 0, 0], [0, 1, 0, 0],
              [0, 0, 1, 0], [0, 0xffffffff, 0, 0xffffffff])
    for state in states:
        for low in edges:
            for high in edges:
                add('raw_boundary_cross_product', state, low, high)
    rng = random.Random(SEED)
    for _ in range(5000):
        add('seeded_raw_bits', [rng.getrandbits(32) for _ in range(4)],
            rng.getrandbits(32), rng.getrandbits(32))
    for _ in range(2000):
        low = from_float(rng.uniform(-10000, 10000))
        high = from_float(rng.uniform(-10000, 10000))
        add('seeded_finite_sorted_bounds', [rng.getrandbits(32) for _ in range(4)],
            *sorted((low, high), key=to_float))
    intervals = [(0, from_float(1)), (0, from_float(.001)),
                 (from_float(1), from_float(1) + 1),
                 (from_float(-1) + 1, from_float(-1)),
                 (0, 1), (0x80000001, 0),
                 (from_float(-100), from_float(100)),
                 (0, from_float(1_000_000)), (0x7f7ffffe, 0x7f7fffff),
                 (0x3f800000, 0x3f800000), (0xff7fffff, 0x7f7fffff)]
    for sequence in range(24):
        state = [rng.getrandbits(32) for _ in range(4)]
        for step in range(256):
            low, high = intervals[(step + sequence) % len(intervals)]
            add('seeded_chained_sequence', state if step == 0 else None,
                low, high, sequence=sequence, sequence_step=step)
    return cases


def model_results(cases):
    results = []
    state = None
    for c in cases:
        if 'state' in c:
            state = tuple(c['state'])
        try:
            r = uniform_range_bits(state, c['low_bits'], c['high_bits'])
            state = r.state
            results.append({'id': c['id'], 'bits': r.bits, 'trap': False,
                            'state': list(state), 'model_draws': r.draws})
        except RngRangeError:
            results.append({'id': c['id'], 'bits': None, 'trap': True,
                            'state': list(state), 'model_draws': 0})
    return results


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    output, oracle = build()
    cases = corpus()
    expected = model_results(cases)
    cases_file = output / 'cases.jsonl'
    cases_file.write_text(''.join(json.dumps(c, allow_nan=False) + '\n' for c in cases))
    (output / 'model-results.jsonl').write_text(''.join(json.dumps(r, allow_nan=False) + '\n' for r in expected))
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    observed_file = output / 'original-body-results.jsonl'
    command = [str(runtime), '--max-old-space-size=128', str(ROOT / 'scripts/run_rng_oracle.mjs'),
               str(output / oracle['module_file']), str(cases_file), str(output / 'manifest.json')]
    with observed_file.open('w') as out, (output / 'oracle.stderr.log').open('w') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            raise SystemExit('Owned isolated RNG oracle exceeded deadline and was stopped')
    if code:
        raise SystemExit(f'RNG oracle failed; inspect {output / "oracle.stderr.log"}')
    actual = [json.loads(line) for line in observed_file.read_text().splitlines()]
    if len(actual) != len(cases) or [x['id'] for x in actual] != list(range(len(cases))):
        raise SystemExit('Oracle fixture coverage/order differs')
    mismatches = [{'input': c, 'model': want, 'original_body': got}
                  for c, want, got in zip(cases, expected, actual)
                  if any(want[k] != got[k] for k in ('id', 'bits', 'trap', 'state'))]
    write_json(output / 'mismatches.json', mismatches)
    groups = {}
    for c in cases:
        groups[c['group']] = groups.get(c['group'], 0) + 1
    runtime_sha = hashlib.sha256(runtime.read_bytes()).hexdigest()
    sources = [ROOT / 'scripts/build_rng_oracle.py', ROOT / 'scripts/check_rng_spec.py',
               ROOT / 'scripts/run_rng_oracle.mjs', ROOT / 'reconstruction/core_spec/rng.py',
               ROOT / 'reconstruction/core_spec/binary32.py']
    summary = {'version': '0.126.0', 'build': '3e72472a',
               'original_wasm_sha256': oracle['original_wasm_sha256'],
               'full_wat_sha256': oracle['full_wat_sha256'], 'index_sha256': oracle['index_sha256'],
               'oracle_module_sha256': oracle['module_sha256'], 'oracle_module_bytes': oracle['module_bytes'],
               'original_function_index': 32475, 'original_body_sha256': oracle['original_body_sha256'],
               'original_body_byte_identical': True, 'original_function_index_preserved': True,
               'case_count': len(cases), 'groups': groups, 'mismatch_count': len(mismatches),
               'returned_bits_and_all_four_state_words_compared': True,
               'successful_calls': sum(not x['trap'] for x in actual),
               'replacement_panic_traps_with_unchanged_state': sum(x['trap'] for x in actual),
               'model_calls_requiring_retry': sum(x['model_draws'] > 1 for x in expected),
               'maximum_model_draws': max(x['model_draws'] for x in expected),
               'chained_sequences': 24, 'steps_per_sequence': 256, 'seed': hex(SEED),
               'whole_memory_canary_passed': True, 'globals': [], 'imports': [],
               'isolated_original_body_executed': True, 'original_panic_executed': False,
               'original_initializer95651_executed': False, 'full_game_started': False,
               'network_used': False, 'user_saves_accessed': False, 'installed_game_modified': False,
               'runtime_version': subprocess.check_output([str(runtime), '--version'], text=True).strip(),
               'runtime_sha256': runtime_sha, 'validator_sha256': oracle['validator_sha256'],
               'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
               'limitations': ['No entropy or seed initialization protocol is reconstructed.',
                               'Invalid range observations stop at replacement panic trap; original panic is not run.',
                               'The integer recurrence is inlined in32475, not a separately executed original leaf.',
                               'Draw counts come from the independent model; the original body is not instrumented.',
                               'The selected deterministic corpus is not exhaustive over states and bounds.',
                               'No caller such as spawn selection, crit, death XP, loot or full-game context is executed.']}
    write_json(output / 'differential-summary.json', summary)
    print(json.dumps({'run_directory': str(output), 'case_count': len(cases),
                      'successful_calls': summary['successful_calls'],
                      'replacement_panic_traps': summary['replacement_panic_traps_with_unchanged_state'],
                      'retry_calls': summary['model_calls_requiring_retry'],
                      'mismatch_count': len(mismatches), 'full_game_started': False}, allow_nan=False))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
