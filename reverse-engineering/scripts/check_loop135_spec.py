#!/usr/bin/env python3
"""Independent clock/phase projections against complete original0.135.1 entries.

Every expectation is serialized before the original runner launches. The full
tick and command functions keep all callees; only approved research exports are
added. These are controlled state projections, not a complete game simulator.
"""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha

SOURCE_FILES = ('scripts/check_loop135_spec.py', 'scripts/run_loop135_full_oracle.mjs',
                'scripts/build_full135_oracle.py', 'scripts/build_upgrade134_oracle.py',
                'scripts/full135_host.mjs',
                'reconstruction/core_spec/loop135.py', 'reconstruction/core_spec/binary32.py')
NODE = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def hashes():
    return {p: sha(ROOT / p) for p in SOURCE_FILES}


IMPORT_HASHES = hashes()
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f32
from core_spec.loop135 import ClockState, project_tick_clock, apply_pause_command, float64_bits


def corpus(phase):
    cases = []
    def add(kind, group, *, marker=1, previous=0.0, now=0.125, clock=0x41200000,
            mode=0, game_phase=3, global_phase=3, tag=0, payload=1,
            raw_previous=None, raw_now=None, skip_spawn=True):
        state = ClockState(marker, float64_bits(previous) if raw_previous is None else raw_previous,
                           clock, tag, mode, game_phase, global_phase)
        data = asdict(state)
        for key in ('previous_marker', 'previous_time_bits', 'game_discriminant'):
            data[key] = str(data[key])
        want = dict(previous_marker=str(marker), previous_time_bits=data['previous_time_bits'],
                    simulation_clock_bits=clock, actual_host_calls=0)
        now_bits = float64_bits(now) if raw_now is None else raw_now
        if kind == 'pause':
            result = apply_pause_command(game_discriminant=tag, mode=mode,
                                         phase=game_phase, payload_byte=payload)
            want.update(phase=result.phase, global_phase=global_phase)
        else:
            result = project_tick_clock(state, now_bits)
            want.update(previous_marker=str(result.previous_marker),
                        previous_time_bits=str(result.previous_time_bits),
                        simulation_clock_bits=result.simulation_clock_bits)
        cases.append(dict(id=len(cases), kind=kind, group=group, clock=data,
                          payload_byte=payload, now_bits=str(now_bits), skip_spawn=skip_spawn,
                          inspect_mutations=phase == 'pilot', expected=want))
    # Actual transitions and wrong-phase/odd-mode/nonexistent-game guards.
    for mode,game_phase,payload,tag in [(0,1,1,0),(0,3,0,0),(2,1,255,0),(2,3,0,0),
            (1,1,1,0),(1,3,0,0),(0,2,1,0),(0,1,1,2)]:
        add('pause','pilot_pause_transitions',mode=mode,game_phase=game_phase,payload=payload,tag=tag)
    for mode,game_phase,global_phase,tag in [(0,3,3,2),(0,3,3,0),(0,2,3,0),
                                           (0,1,3,0),(2,2,1,0)]:
        add('tick','pilot_tick_modes',mode=mode,game_phase=game_phase,global_phase=global_phase,tag=tag)
    if phase == 'pilot':
        return cases
    # Every byte mode: exact==0 simulation gate versus lowbit pause permission.
    for mode in range(256):
        for game_phase in (0,1,2,3,4,5,255):
            for payload in (0,1,255):
                add('pause','all_mode_bytes_pause_guards',mode=mode,game_phase=game_phase,payload=payload)
    for tag in (0,1,2,0xffffffffffffffff):
        for game_phase in (1,3):
            for payload in (0,1):
                add('pause','game_discriminant_gate',tag=tag,game_phase=game_phase,payload=payload)
    # Timestamp delta and f32 accumulation boundaries. These execute full880.
    clocks = [0,0x80000000,1,0x007fffff,0x00800000,f32.from_float(0.1),f32.from_float(10),
              f32.from_float(2**20),0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00001]
    times = [(0.0,-1.0),(0.0,-0.0),(0.0,0.0),(0.0,2**-149),(0.0,0.05),
             (0.0,math.nextafter(0.1,0.0)),(0.0,0.1),(0.0,math.nextafter(0.1,math.inf)),
             (0.0,1.0),(1000.0,1000.05),(1000.0,1001.0),
             (0.0,math.inf),(0.0,-math.inf),(math.inf,math.inf),(-math.inf,-math.inf),
             (math.inf,0.0),(math.nan,1.0),(1.0,math.nan)]
    for marker in (0,1,2,0xffffffffffffffff):
        for previous,now in times:
            for clock in clocks:
                add('tick','binary64_delta_binary32_clock',marker=marker,previous=previous,now=now,
                    clock=clock,game_phase=1,global_phase=1)
    for mode in (0,1,2,255):
        for game_phase in (0,1,2,3,4,5,255):
            for global_phase in (0,1,2,3,4,5,255):
                # With no additional player records, a multi-state running
                # session with no phase1/2 participant ends the session. The
                # original then reaches an account-save host dependency. That
                # retained exploratory case is a pending constructor boundary,
                # not accepted as a successful complete-tick differential.
                if mode != 0 and global_phase == 1 and game_phase not in (1,2):
                    continue
                add('tick','single_and_multi_phase_clock_gate',mode=mode,game_phase=game_phase,
                    global_phase=global_phase)
    for mode in (0,2):
        for game_phase in (0,2,3,4,5,255):
            for marker in (0,1,2):
                add('tick','paused_and_initial_timestamp_still_updated',mode=mode,game_phase=game_phase,
                    global_phase=game_phase,marker=marker,previous=10.0,now=100.0)
    return cases


def is_nan64(bits):
    bits = int(bits)
    return bits & 0x7ff0000000000000 == 0x7ff0000000000000 and bits & 0xfffffffffffff != 0


def compare(want, got):
    differences = []
    for key, value in want.items():
        other = got.get(key)
        if key == 'simulation_clock_bits' and f32.is_nan(value) and isinstance(other,int) and f32.is_nan(other):
            continue
        if key == 'previous_time_bits' and other is not None and is_nan64(value) and is_nan64(other):
            continue
        if value != other:
            differences.append(dict(field=key, expected=value, actual=other))
    if 'error' in got:
        differences.append(dict(field='original_entry_error', actual=got['error']))
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('pilot','full'), default='pilot')
    parser.add_argument('--full-directory', type=Path)
    args = parser.parse_args()
    before = hashes()
    if before != IMPORT_HASHES or sha(SOURCE) != SOURCE_SHA or sha(NODE) != NODE_SHA:
        raise ValueError('Pinned original/runtime identity differs')
    if subprocess.check_output([str(NODE),'--version'],text=True,timeout=10).strip() != 'v22.23.4':
        raise ValueError('Pinned runtime version differs')
    cases = corpus(args.phase)
    if args.full_directory:
        directory = args.full_directory.resolve(strict=True)
        manifest = json.loads((directory/'manifest.json').read_text())
    else:
        directory, manifest = build(['tick','command'])
    manifest_sha = sha(directory/'manifest.json')
    module_sha = sha(directory/manifest['module_file'])
    if module_sha != manifest['module_sha256']:
        raise ValueError('Research module identity differs')
    run = directory / datetime.now(timezone.utc).strftime('loop135-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(exist_ok=False)
    # Host validates the module in directory; runtime receipt goes there too.
    casefile = run/'cases.json';casefile.write_text(json.dumps(cases,indent=2,allow_nan=False)+'\n')
    snapshot = run/'source-snapshot'
    for name in SOURCE_FILES:
        p = snapshot/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    (run/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
    if hashes() != before or any(sha(snapshot/name) != before[name] for name in SOURCE_FILES):
        raise ValueError('Source drift before original launch')
    results, stderr = run/'original-results.jsonl', run/'stderr.log'
    command = [str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',
               str(ROOT/'scripts/run_loop135_full_oracle.mjs'),str(directory),str(casefile)]
    started = time.monotonic()
    with results.open('w') as out,stderr.open('w') as err:
        child = subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        try: code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);code=child.wait()
    process = dict(command=command,pid=child.pid,pgid=child.pid,deadline_seconds=60,
                   exit_code=code,elapsed_seconds=round(time.monotonic()-started,3),
                   runtime_sha256=NODE_SHA)
    (run/'process.json').write_text(json.dumps(process,indent=2)+'\n')
    after = hashes();(run/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
    if (after != before or json.loads(casefile.read_text()) != cases
            or sha(SOURCE) != SOURCE_SHA or sha(directory/'manifest.json') != manifest_sha
            or sha(directory/manifest['module_file']) != module_sha):
        raise ValueError('Source/corpus changed during original run')
    rows = [json.loads(line) for line in results.read_text().splitlines()]
    if len(rows) > len(cases):
        raise ValueError('Unexpected extra original rows')
    failures = []
    for index,c in enumerate(cases):
        if index >= len(rows):
            failures.append(dict(id=c['id'],group=c['group'],missing_original_result=True));continue
        row=rows[index]
        if row['id'] != c['id']:
            raise ValueError('Original result IDs differ')
        differences=compare(c['expected'],row)
        if differences:failures.append(dict(id=c['id'],group=c['group'],differences=differences))
    (run/'mismatches.json').write_text(json.dumps(failures,indent=2,allow_nan=False)+'\n')
    runtime_path=directory/'loop135-runtime.json'
    runtime=json.loads(runtime_path.read_text()) if code == 0 and runtime_path.exists() else None
    if runtime:(run/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
    report=dict(version='0.135.1',build='0898d5e3',phase=args.phase,case_count=len(cases),
        result_count=len(rows),mismatch_cases=len(failures),groups=dict(Counter(x['group']for x in cases)),
        original_wasm_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],
        builder_manifest_sha256=manifest_sha,
        full_module_directory=str(directory),runtime_directory=str(run),runtime=runtime,process=process,
        source_sha256=before,source_freeze_before_after=before==after,
        artifacts={p.name:sha(p)for p in (casefile,results,stderr,run/'mismatches.json',run/'process.json')},
        comparison_policy='Float32/f64 NaN classification only; all other compared words exact. Fulltick output phase beyondclock is observed but not independently compared.',
        pending_original_domains=['Multi-state terminal aggregation reaches unresolved account-save host dependency.',
                                  'Initial run construction, incoming commands, full world/spawn and complete scheduler behavior.',
                                  'Party aggregation, victory and Endless independent projections are static-derived; not differential-accepted here.'],
        game_scheduler_reconstructed=False,installation_or_saves_modified=False)
    (run/'comparison.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(runtime_directory=str(run),full_module_directory=str(directory),
                          cases=len(cases),rows=len(rows),mismatches=len(failures),exit_code=code)))
    if code or failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
