#!/usr/bin/env python3
"""Check85387 against its original body and XP projection against recomposition.

Only helper cases are original-function differential tests. JS recomposition
independently checks the selected XP arithmetic, never the full original3231.
"""
from dataclasses import asdict
import hashlib
import json
import os
import random
import signal
import subprocess
import sys

from build_progression_oracle import ROOT, BODY_HASHES, build
from wasm_index import ORIGINAL_SHA, sha

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.binary32 import from_float, is_nan
from core_spec.progression import (ProgressionState, apply_xp, card_choice_eligible,
                                   round_85387_bits, xp_threshold, xp_threshold_bits)

SEED = 0xa2e03231


def corpus():
    cases = []
    def add(mode, group, **fields):
        cases.append({'id': len(cases), 'mode': mode, 'group': group, **fields})
    edges = (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x807fffff,
             0x00800000, 0x80800000, 0x3efffffe, 0x3effffff, 0x3f000000,
             0x3f000001, 0xbeffffff, 0xbf000000, 0xbf000001,
             0x3f7fffff, 0x3f800000, 0x3f800001, 0xbf800000,
             0x4affffff, 0x4b000000, 0x4b000001, 0x4b7fffff,
             0x7f7fffff, 0xff7fffff, 0x7f800000, 0xff800000,
             0x7fc00000, 0x7fa00001, 0xffc12345)
    for bits in edges:
        add('helper', 'helper_special_values', input_bits=bits)
    for exponent in range(256):
        for fraction in (0, 1, 0x3fffff, 0x7fffff):
            for sign in (0, 0x80000000):
                add('helper', 'helper_all_exponents_signs_fraction_boundaries', input_bits=sign | exponent << 23 | fraction)
    for half in range(-256, 257):
        bits = from_float(half / 2)
        for step in (-2, -1, 0, 1, 2):
            add('helper', 'helper_integer_half_adjacent_bits', input_bits=(bits + step) & 0xffffffff)
    rng = random.Random(SEED)
    for _ in range(20000):
        add('helper', 'helper_seeded_raw_bits', input_bits=rng.getrandbits(32))
    levels = set(range(256))
    for power in range(1, 33):
        for step in (-2, -1, 0, 1, 2):
            level = (1 << power) + step
            if 0 <= level <= 0xffffffff:
                levels.add(level)
    for level in sorted(levels):
        add('threshold_composition', 'threshold_small_levels_u32_conversion_boundaries', level=level)
    for _ in range(2000):
        add('threshold_composition', 'threshold_seeded_u32_levels', level=rng.getrandbits(32))
    for level in range(101):
        needed = xp_threshold(level)
        for delta in (-1, 0, 1):
            amount = needed + delta
            add('xp_projection_composition', 'xp_exact_threshold_and_neighbors',
                state=asdict(ProgressionState(level, 0, 0)), amount=amount)
            add('xp_projection_composition', 'xp_existing_balance_amount_zero',
                state=asdict(ProgressionState(level, amount, 0xffffffff)), amount=0)
    for level in (0, 1, 2, 50, 97, 98, 99, 100, 0xffffffff):
        for xp, amount in ((0xffffffff, 1), (0xffffffff, 2), (0xfffffffe, 1),
                           (0xfffffffe, 2), (0, 0xffffffff), (1, 0xffffffff)):
            add('xp_projection_composition', 'xp_add_wrap_cap_pending_wrap',
                state=asdict(ProgressionState(level, xp, 0xffffffff)), amount=amount)
    total = 0
    for level in range(1, 99):
        total += xp_threshold(level)
        for delta in (-1, 0, 1):
            add('xp_projection_composition', 'xp_multilevel_cumulative_threshold_boundaries',
                state=asdict(ProgressionState(1, 0, 0)), amount=total + delta)
    for _ in range(1000):
        add('xp_projection_composition', 'xp_seeded_balances_levels_pending',
            state=asdict(ProgressionState(rng.randrange(102), rng.getrandbits(32), rng.getrandbits(32))),
            amount=rng.getrandbits(32))
    for pending in (0, 1, 0xffffffff):
        for phase in (0, 1, 2, 255):
            for flags in (0, 1, 2, 3, 254, 255):
                for gate in (0, 1, 2, 255):
                    for ready in (0, 1, 2, 255):
                        add('card_guard_composition', 'card_guard_canonical_and_noncanonical_bytes',
                            pending_upgrades=pending, phase2299=phase, flags2288=flags,
                            gate2284=gate, flags2285=ready)
    return cases


def model(case):
    mode = case['mode']
    if mode == 'helper':
        result = {'bits': round_85387_bits(case['input_bits'])}
    elif mode == 'threshold_composition':
        result = {'bits': xp_threshold_bits(case['level']), 'threshold': xp_threshold(case['level'])}
    elif mode == 'xp_projection_composition':
        result = asdict(apply_xp(ProgressionState(**case['state']), case['amount']))
        result['thresholds_spent'] = list(result['thresholds_spent'])
    elif mode == 'card_guard_composition':
        result = {'eligible': card_choice_eligible(*(case[k] for k in
                   ('pending_upgrades', 'phase2299', 'flags2288', 'gate2284', 'flags2285')))}
    else:
        raise ValueError('Unknown mode')
    return {'id': case['id'], **result}


def strict_loads(raw):
    return json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-strict JSON: ' + value)))


def main():
    output, oracle = build()
    cases_file = output / 'cases.jsonl'
    model_file = output / 'independent-model-results.jsonl'
    cases = corpus()
    cases_file.write_text(''.join(json.dumps(c, separators=(',', ':'), allow_nan=False) + '\n' for c in cases))
    model_file.write_text(''.join(json.dumps(model(c), separators=(',', ':'), allow_nan=False) + '\n' for c in cases))
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    observed_file = output / 'original-helper-and-recomposition-results.jsonl'
    command = [str(runtime), '--max-old-space-size=128', str(ROOT / 'scripts/run_progression_oracle.mjs'),
               str(output / oracle['module_file']), str(cases_file), str(output / 'manifest.json')]
    with observed_file.open('w') as out, (output / 'oracle.stderr.log').open('w') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait()
            raise SystemExit('Owned micro-oracle exceeded deadline and was stopped')
    if code:
        raise SystemExit('Micro-oracle failed; inspect local stderr')
    # Compare persisted artifacts, not only in-memory expected values/counters.
    cases = [strict_loads(line) for line in cases_file.read_text().splitlines()]
    expected = [strict_loads(line) for line in model_file.read_text().splitlines()]
    actual = [strict_loads(line) for line in observed_file.read_text().splitlines()]
    for rows in (cases, expected, actual):
        if len(rows) != len(cases) or [row['id'] for row in rows] != list(range(len(cases))):
            raise SystemExit('Persisted corpus/results coverage or order differs')
    mismatch = []; modes = {}; groups = {}
    for c, want, got in zip(cases, expected, actual):
        stats = modes.setdefault(c['mode'], {'case_count': 0, 'mismatch_count': 0, 'nan_category_pairs': 0})
        stats['case_count'] += 1; groups[c['group']] = groups.get(c['group'], 0) + 1
        same = want == got
        if c['mode'] == 'helper' and is_nan(want['bits']) and is_nan(got['bits']):
            stats['nan_category_pairs'] += 1; same = True
        if not same:
            stats['mismatch_count'] += 1
            mismatch.append({'input': c, 'model': want, 'observed': got})
    mismatch_file = output / 'mismatches.json'
    mismatch_file.write_text(json.dumps(mismatch, indent=2, allow_nan=False) + '\n')
    if strict_loads(mismatch_file.read_text()) != mismatch:
        raise SystemExit('Persisted mismatch receipt differs')
    files = [ROOT / 'scripts/build_progression_oracle.py', ROOT / 'scripts/check_progression_spec.py',
             ROOT / 'scripts/run_progression_oracle.mjs', ROOT / 'reconstruction/core_spec/binary32.py',
             ROOT / 'reconstruction/core_spec/progression.py']
    if sha(ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm') != ORIGINAL_SHA:
        raise SystemExit('Original module changed during check')
    summary = {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': ORIGINAL_SHA,
               'complete_wat_sha256': oracle['complete_wat_sha256'],
               'original_helper_function': 85387, 'original_helper_body_sha256': BODY_HASHES[85387],
               'original_helper_body_bytes': 68, 'oracle_module_sha256': oracle['module_sha256'],
               'oracle_module_bytes': oracle['module_bytes'], 'copied_body_byte_identical': True,
               'case_count': len(cases), 'mismatch_count': len(mismatch), 'modes': modes, 'groups': groups,
               'seed': hex(SEED), 'original85387_executed': True,
               'original3231_executed': False, 'original13409_executed': False,
               'threshold_xp_guard_comparisons': 'JS recomposition around copied85387; not original3231 differential execution',
               'full_game_started': False, 'host_imports': [], 'memory': None,
               'network_used': False, 'user_saves_accessed': False, 'installed_game_modified': False,
               'static_guard_count': len(oracle['static_guards']),
               'runtime_version': subprocess.check_output([str(runtime), '--version'], text=True).strip(),
               'runtime_sha256': sha(runtime), 'validator_sha256': oracle['validator_sha256'],
               'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in files},
               'artifact_sha256': {p.name: sha(p) for p in (cases_file, model_file, observed_file, mismatch_file)},
               'evidence_directory': str(output.relative_to(ROOT)),
               'limitations': ['Only85387 is an unchanged original function executed in isolation.',
                               'XP/threshold/card-guard modes check an independently recomposed instruction projection, not the full original3231.',
                               'Attribute/heal recalculation1573, messages, notifications and2098 card side effects are excluded.',
                               'NaN payload, sign and signaling state are compared by category only.',
                               'Deterministic differential checks do not exhaust all binary32 inputs.']}
    (output / 'differential-summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'run_directory': str(output), 'case_count': len(cases), 'mismatch_count': len(mismatch),
                      'modes': modes, 'original85387_executed': True, 'original3231_executed': False,
                      'full_game_started': False}, allow_nan=False))
    if mismatch:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
