#!/usr/bin/env python3
"""Check XP projection fields against complete original3231 on paused states.

No original2098/card generation or application start. All original internal
callees reached by3231 are unchanged; every host import throws in the runner.
"""
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from build_full_function_oracle import ROOT, build
from wasm_index import sha
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.progression import ProgressionState, apply_xp
from check_progression_spec import corpus


def main():
    run, manifest = build([3231, 106495])
    cases = [c for c in corpus() if c['mode'] == 'xp_projection_composition']
    for i, c in enumerate(cases):
        c['id'] = i
    path = run / 'full-xp-cases.jsonl'
    path.write_text(''.join(json.dumps(c, allow_nan=False) + '\n' for c in cases))
    expected = [dict(id=c['id'], state=asdict(apply_xp(ProgressionState(**c['state']), c['amount']).state)) for c in cases]
    (run / 'full-xp-model-results.json').write_text(json.dumps(expected, indent=2, allow_nan=False) + '\n')
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    command = [str(runtime), '--max-old-space-size=768', '--wasm-max-mem-pages=512',
               str(ROOT / 'scripts/run_full_progression_oracle.mjs'), str(run),
               str(ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'), str(path)]
    with (run / 'full-xp-original-results.jsonl').open('w') as out, (run / 'full-xp-stderr.log').open('w') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait()
            raise SystemExit('Owned full-function oracle exceeded60s and was stopped')
    if code:
        raise SystemExit(f'Controlled original3231 failed; inspect {run}')
    rows = [json.loads(line) for line in (run / 'full-xp-original-results.jsonl').read_text().splitlines()]
    if len(rows) != len(cases) or [x['id'] for x in rows] != list(range(len(cases))):
        raise SystemExit('Result coverage/order differs')
    mismatch = [dict(input=c, model=e, original=a) for c, e, a in zip(cases, expected, rows)
                if a['state'] != e['state'] or a['phase2299'] != 3]
    (run / 'full-xp-mismatches.json').write_text(json.dumps(mismatch, indent=2, allow_nan=False) + '\n')
    scripts = ('build_full_function_oracle.py', 'full_function_host.mjs', 'run_full_progression_oracle.mjs',
               'check_full_progression_spec.py', 'check_progression_spec.py')
    receipt = {'original_wasm_sha256': manifest['original_wasm_sha256'],
               'module_sha256': manifest['module_sha256'], 'original3231_executed': True,
               'original_internal_callees_unchanged': True, 'dependency_shims': [],
               'case_count': len(rows), 'mismatch_count': len(mismatch),
               'fields_compared': ['u32 level1336', 'u32 XP1340', 'u32 pending2088', 'phase2299'],
               'fixture_scope': 'Paused phase3, empty auxiliary game state, synthetic original-allocator allocations. Original2098 skipped by real phase guard.',
               'other_sideeffect_fields_not_compared': True, 'full_game_started': False,
               'actual_host_calls': 0, 'runtime': json.loads((run / 'full-progression-runtime.json').read_text()),
               'source_sha256': {f'scripts/{n}': sha(ROOT / 'scripts' / n) for n in scripts},
               'model_sha256': {n: sha(ROOT / 'reconstruction/core_spec' / n) for n in ('progression.py', 'binary32.py')}}
    (run / 'full-progression-comparison.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'run': str(run), 'cases': len(rows), 'mismatches': len(mismatch), 'original3231_executed': True}))
    if mismatch:
        raise SystemExit('Original3231 and projection differ')


if __name__ == '__main__':
    main()
