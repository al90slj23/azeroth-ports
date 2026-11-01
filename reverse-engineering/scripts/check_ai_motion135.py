#!/usr/bin/env python3
"""Fresh medium-angle trig and real full921 long-motion differentials."""
from collections import Counter
from dataclasses import asdict, replace
import argparse, json, math, os, random, signal, struct, subprocess, sys, time
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha

FILES = tuple('scripts/' + n for n in ('check_ai_motion135.py', 'run_trig135_oracle.mjs',
    'check_ai135_spec.py', 'run_ai135_oracle.mjs', 'build_full135_oracle.py', 'full135_host.mjs',
    'build_upgrade134_oracle.py')) + tuple('reconstruction/core_spec/' + n + '.py' for n in (
    '__init__', 'ai135', 'ai_motion135', 'ai_trig135', 'ai135_data', 'incoming135', 'incoming134',
    'spawn135', 'spawn135_data', 'spawn_math135', 'spawn_geometry135', 'binary32', 'binary32_sqrt',
    'enemy_scaling', 'progression134', 'rng', 'upgrade_values'))
IMPORTED = {n: sha(ROOT / n) for n in FILES}
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.ai_trig135 import sin_bits, cos_bits, MEDIUM_MAX_BITS, REDUCTION_START_BITS
from core_spec.ai_motion135 import update_ordinary_units
from core_spec.ai135 import AiFrame135
from core_spec.incoming135 import input_from_dict
from check_ai135_spec import corpus, record, incoming, FIELDS

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def trig_cases(pilot):
    words = [0, f.SIGN, 1, 0x007fffff, 0x00800000, f.INF, f.INF | f.SIGN, 0x7fc00001]
    boundaries = (1061752795, 1075235812, 1081824210, 1085271520, 0x40c90fdb,
                  REDUCTION_START_BITS, MEDIUM_MAX_BITS)
    for boundary in boundaries:
        for offset in range(-3, 4):
            for sign in (0, f.SIGN):
                if boundary + offset <= MEDIUM_MAX_BITS:
                    words.append((boundary + offset) | sign)
    if not pilot:
        rng = random.Random(0x13511428)
        words += [rng.randrange(MEDIUM_MAX_BITS + 1) | (f.SIGN if j & 1 else 0) for j in range(2500)]
        for k in (1, 2, 3, 7, 99, 1000, 100000, 10000000, 200000000):
            middle = f.from_float(k * math.pi / 2)
            for offset in range(-3, 4):
                for sign in (0, f.SIGN):
                    if middle + offset <= MEDIUM_MAX_BITS:
                        words.append((middle + offset) | sign)
        angle = 0
        for j in range(4000):
            angle = f.add(angle, 0x3e19999a)
            words.append(angle | (f.SIGN if j & 1 else 0))
    return [dict(id=j, bits=bits, expected=dict(id=j, sin_bits=sin_bits(bits), cos_bits=cos_bits(bits)))
            for j, bits in enumerate(words)]


def ai_cases(pilot):
    rows = corpus(pilot)
    if not pilot:
        rng = random.Random(0x135921)
        for k, angle in enumerate((7, 10, 20, -30, 100, -1000, 10000, -1e6, 1e8, -4e8)):
            s = incoming(hp_1528_bits=f.from_float(1e6)); raw = asdict(s); raw['map_id'] = s.map_id.decode()
            rows.append(dict(id=len(rows), group='medium-angle-real-movement',
                input=dict(records=[record(position=(25, -5, 2), **{'396': angle, '348': 0})],
                    incoming=raw, incoming_item_effects=[], other_incoming_sources_absent=True),
                max_hp_bits=f.from_float(1e6), steps=[dict(now_bits=f.from_float(10),
                    dt_bits=f.from_float(.05), player_xyz_bits=[0, 0, 0])]))
        for count in (1, 3, 8):
            s = incoming(hp_1528_bits=f.from_float(1e6)); raw = asdict(s); raw['map_id'] = s.map_id.decode()
            steps = [dict(now_bits=f.from_float(10 + j * .1), dt_bits=f.from_float(.1),
                player_xyz_bits=[f.from_float(100 if j // 15 % 2 else -100), f.from_float(j % 7), 0]) for j in range(800)]
            rows.append(dict(id=len(rows), group='eighty-second-repath-orbit-accumulation',
                input=dict(records=[record(position=(20 + j, 0, 0), counter=j,
                    **{'396': rng.uniform(5, 6), '348': 0}) for j in range(count)],
                    incoming=raw, incoming_item_effects=[], other_incoming_sources_absent=True),
                max_hp_bits=f.from_float(1e6), steps=steps))
    for row in rows:
        state = input_from_dict(row['input']['incoming']); current = tuple(row['input']['records']); queued = 0; outputs = []
        for step in row['steps']:
            result = update_ordinary_units(AiFrame135(current, step['now_bits'], step['dt_bits'],
                tuple(step['player_xyz_bits']), state, incoming_item_effects=(), other_incoming_sources_absent=True))
            current, state = result.records, result.incoming
            queued += len(result.attacks) + len(result.movements)
            output = dict(records=list(current), **{name: getattr(state, name) for name in FIELDS})
            output.update(incoming_total_992_bits=struct.pack('>d', state.incoming_total_992).hex(),
                phase2579=state.phase_2579, queued_packets=queued, world_reference=0)
            outputs.append(output)
        row['expected'] = dict(id=row['id'], steps=outputs)
    return json.loads(json.dumps(rows))


def equal(a, b, path=''):
    if type(a) != type(b): return False
    if isinstance(a, dict): return a.keys() == b.keys() and all(equal(v, b[k], path + '.' + k) for k, v in a.items())
    if isinstance(a, list): return len(a) == len(b) and all(equal(x, y, path + f'[{j}]') for j, (x, y) in enumerate(zip(a, b)))
    return a == b or path.endswith(('.sin_bits', '.cos_bits')) and type(a) is int and f.is_nan(a) and f.is_nan(b)


def run(kind, rows):
    before = {n: sha(ROOT / n) for n in FILES}; assert before == IMPORTED
    roles, runner = (['sin_angle', 'cos_angle'], 'run_trig135_oracle.mjs') if kind == 'trig' else (['update_units'], 'run_ai135_oracle.mjs')
    out, manifest = build(roles); snap = out / 'source-snapshot'; snap.mkdir()
    for name in FILES:
        p = snap / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes((ROOT / name).read_bytes()); assert sha(p) == before[name]
    fixtures = out / f'{kind}-motion135-fixtures.jsonl'
    fixtures.write_text(''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in rows))
    assert [json.loads(line) for line in fixtures.read_text().splitlines()] == rows
    frozen = {p.name: sha(p) for p in (fixtures, out / 'manifest.json', out / manifest['module_file'])}
    assert sha(RUNTIME) == RUNTIME_SHA
    assert subprocess.check_output([str(RUNTIME), '--version'], text=True).strip() == 'v22.23.4'
    command = [str(RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512', str(ROOT / 'scripts' / runner), str(out), str(fixtures)]
    result, stderr = out / f'{kind}-motion135-results.jsonl', out / f'{kind}-motion135-stderr.log'; start = time.monotonic()
    with result.open('w') as stream, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stream, stderr=err, start_new_session=True)
        try: code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait(); raise RuntimeError(f'Owned60s timeout: {out}')
    duration = time.monotonic() - start
    if code: raise RuntimeError(f'Original exit{code}: {out}')
    actual = [json.loads(line) for line in result.read_text().splitlines()]; assert [a['id'] for a in actual] == list(range(len(rows)))
    failures = [dict(id=c['id'], group=c.get('group'), expected=c['expected'], actual=a) for c, a in zip(rows, actual) if not equal(c['expected'], a)]
    mismatch = out / 'mismatches.json'; mismatch.write_text(json.dumps(failures, indent=2) + '\n')
    assert before == {n: sha(ROOT / n) for n in FILES} and sha(SOURCE) == SOURCE_SHA and sha(RUNTIME) == RUNTIME_SHA
    assert frozen == {p.name: sha(p) for p in (fixtures, out / 'manifest.json', out / manifest['module_file'])}
    runtime = out / ('trig135-runtime.json' if kind == 'trig' else 'ai135-runtime.json')
    receipt = dict(version='0.135.1', web_build='0898d5e3', kind=kind, cases=len(rows),
        steps=sum(len(c.get('steps', ())) for c in rows), mismatches=len(failures),
        groups=dict(Counter(c.get('group', 'trigonometry') for c in rows)), original_wasm_sha256=SOURCE_SHA,
        source_sha256_before=before, source_sha256_after=before,
        artifacts={p.name: sha(p) for p in (fixtures, result, stderr, mismatch, runtime, out / 'manifest.json', out / manifest['module_file'])},
        runtime=json.loads(runtime.read_text()), process=dict(command=command, exit_code=code, pid=child.pid, pgid=child.pid, seconds=duration, deadline_seconds=60),
        independent_expected_before_original=True, source_snapshots=True, only_changed_section=7,
        limitations=['Finite trig beyond421657408 requires unrecovered1814; nonfinite trig compares NaN category.',
            'AI retains ordinary124-melee/local-owner/flat-world/source-producer/nonfatal restrictions.',
            'Original921 is tested directly; complete880/constructor/frame integration and full game are not established.'])
    (out / f'{kind}-motion135-comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), kind=kind, cases=len(rows), steps=receipt['steps'], mismatches=len(failures), seconds=duration)), flush=True)
    if failures: raise SystemExit(1)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--phase', choices=('pilot', 'full'), default='pilot'); args = p.parse_args()
    run('trig', trig_cases(args.phase == 'pilot'))
    run('ai', ai_cases(args.phase == 'pilot'))


if __name__ == '__main__': main()
