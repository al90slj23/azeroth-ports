#!/usr/bin/env python3
"""Expected-first current139 complete922/nonlethal cleave differential."""
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import replace
import argparse, hashlib, json, os, random, signal, struct, subprocess, sys, time
sys.dont_write_bytecode = True
from build_cast139_oracle import ROOT, SOURCE_SHA, build, sha, save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0, str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.cast139 import CleaveState139, CleaveDefinition139, cast_cleave139
from core_spec.combat139 import DamageState139, EmptyDamageSources139

NODE = ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def closure():
    files = set(production_sources135(ROOT, 'core_spec.cast139')) | {
        'scripts/check_cast139.py', 'scripts/build_cast139_oracle.py',
        'scripts/run_cast139_oracle.mjs', 'scripts/source_closure137.py',
        'scripts/production_closure135.py'}
    while True:
        try:
            edges = verify_local_source_closure(sorted(files))
            return sorted(files), edges
        except AssertionError as error:
            pair = error.args[0]
            assert isinstance(pair, tuple) and len(pair) == 2 and pair[1] not in files
            files.add(pair[1])


def corpus(definition, phase):
    rows, expected, labels, diagnostics = [], [], [], []
    d = CleaveDefinition139(definition['pointer'], b'cleave', bytes.fromhex(definition['raw88_hex']))
    def add(label, *, n=5, seed=1, repeats=1, chance=.2, critical=2., scale=1.,
            owned_scale=1., life=0., extras=(0, 0, 0), phase2587=1,
            suppress=False, sets=((), (), ()), moving=False, mixed=False,
            priority_offset=380, layout=None, guid_base=0x123456789abcdef0,
            source_id=999):
        r = random.Random(0x139845+seed)
        records = []
        for index in range(n):
            row = bytearray(432)
            struct.pack_into('<Q', row, 112, (guid_base+index) & ((1<<64)-1))
            for offset, value in ((40, f.MASK), (64, f.MASK), (244, f.MASK),
                    (288, f.from_float(1000000-index*1000)), (292, f.from_float(1000000))):
                struct.pack_into('<I', row, offset, value)
            x, y = (r.uniform(-9, 9), r.uniform(-9, 9)) if mixed else (1+index*.7, index%2*.3)
            if layout == 'ties':
                x, y = ((1, 0), (0, 1), (-1, 0), (0, -1))[index%4]
                struct.pack_into('<I', row, 288, f.from_float(1000000))
            elif layout == 'edges':
                x, y = ((7, 0), (-7, 0), (0, 7), (0, -7),
                    (7.000000476837158, 0), (1, 0), (-5, 0),
                    (-5.000000476837158, 0))[index%8]
            for offset, number in ((316, x-4), (320, y+2), (328, x), (332, y),
                    (340, 0), (344, 20 if moving else 0)):
                struct.pack_into('<I', row, offset, f.from_float(number))
            if mixed:
                row[424] = index%2
                if index%7 == 0:
                    struct.pack_into('<I', row, 0, 1)
                if index%5 == 0:
                    struct.pack_into('<I', row, priority_offset, f.from_float(11))
            row[429:432] = bytes((0xa5, index, 0x69))
            records.append(bytes(row))
        combat = DamageState139(tuple(records), f.from_float(10), phase2587,
            struct.unpack('<Q', struct.pack('<d', 16777217.25))[0],
            tuple(r.getrandbits(32) for _ in range(4)),
            EmptyDamageSources139((), (), (), True))
        state = CleaveState139(combat, (0, 0, 0), f.from_float(230),
            f.from_float(scale), f.from_float(chance), f.from_float(critical),
            extras[2], sets, suppress, source_id)
        initial = dict(units432_hex=[x.hex() for x in records], now_bits=combat.now_bits,
            phase2587=phase2587, accounted_total_bits=str(combat.accounted_total_bits),
            rng_words=combat.rng_words, player_xyz=state.player_xyz,
            max_hp_bits=state.max_hp_bits, damage_multiplier_bits=state.damage_multiplier_bits,
            critical_chance_bits=state.critical_chance_bits,
            critical_multiplier_bits=state.critical_multiplier_bits,
            extra_targets=state.extra_targets, spell_sets=sets,
            suppress_primary_attempt=suppress, source_id=str(source_id))
        words = [d.pointer, 1, 0x3f000000, f.from_float(owned_scale), 0x3f800000,
            extras[0], 0x3f800000, 0x3f800000, 0, 0, 0, 0, 0,
            0x3f800000, 0x3f800000, extras[1], 0x3f800000, 0x3f800000,
            f.from_float(life), 0x3f800000]
        owned = struct.pack('<20I', *words)
        answers, diag = [], []
        for _ in range(repeats):
            result = cast_cleave139(state, d, owned)
            state = result.state
            answers.append(dict(success=result.success,
                units432_hex=[x.hex() for x in state.combat.units432],
                rng_words=state.combat.rng_words,
                accounted_total_bits=str(state.combat.accounted_total_bits),
                spell_sets=state.spell_sets, owned80_hex=owned.hex(),
                launch306_packets=[] if result.launch306_hex is None else [[306, result.launch306_hex]]))
            diag.append(dict(selected_ids=[str(x) for x in result.selected_ids],
                base_damage_bits=result.base_damage_bits,
                hits=[[str(h[0]), *h[1:]] for h in result.hits],
                scope='Independent model diagnostics, not original trace instrumentation'))
        index = len(rows)
        rows.append(dict(id=index, state=initial, owned80_hex=owned.hex(), repeats=repeats))
        expected.append(dict(id=index, answers=answers))
        labels.append(dict(id=index, group=label))
        diagnostics.append(dict(id=index, stages=diag))
    add('pilot-no-target-prefix', n=0)
    add('pilot-default-three', repeats=2)
    add('pilot-elite-priority', n=12, mixed=True)
    add('pilot-phase0-still-critical-noHP', phase2587=0)
    if phase == 'full':
        add('372-decoy-does-not-defer-current380', n=32, mixed=True, priority_offset=372)
        for n in (20, 21, 32, 63):
            add('equal-distance-HP-stable-sort-full-ordered306', n=n,
                layout='ties', extras=(63, 0, 0), chance=.5)
        add('radius7-and-near6-inclusive-edges', n=32, layout='edges', extras=(63, 0, 0))
        for guid_base in (0, 0x0100000000000000):
            add('packed-GUID-zero-bytes-launch306', n=6, guid_base=guid_base,
                source_id=guid_base, extras=(10, 0, 0))
        for n in (1, 2, 3, 4, 6, 12, 20, 21, 24, 32, 63):
            for seed in range(6):
                add('current432-priority-distance-nearHP-sort', n=n, seed=100*n+seed,
                    repeats=2 if seed%2 else 1, mixed=True, moving=bool(seed%2),
                    extras=(seed%3, seed%2, seed%4), chance=(0, 1, .5)[seed%3])
        for chance in (-1, 0, 0.00000001, .25, .5, .9999999, 1, 2):
            add('strict-critical', chance=chance, repeats=3)
        for extras in ((f.MASK, 0, 0), (f.MASK-2, 0, 0), (0, f.MASK-1, 0),
                       (0, 0, f.MASK), (2, 3, 4)):
            add('wrapping-target-count', n=12, extras=extras)
        for scale in (0, -.5, .1, 1, 2, 11):
            add('base-ordered-rounding-and-life', scale=scale, owned_scale=1.3,
                life=.001, critical=2.3, repeats=3)
        for count in (0, 1, 4, 16, 17, 31):
            values=tuple(100+i for i in range(count))
            for exists in (False, True):
                sets=tuple((values+(845,) if exists else values) for _ in range(3))
                add('ordered-spell-set-dedup-and-growth', sets=sets, suppress=bool(count%2), repeats=2)
        add('suppressed-first-spellset-no-target', n=0, suppress=True)
    return json.loads(json.dumps((rows, expected, labels, diagnostics)))


def missing(pid, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return True
    return False


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot')
    args=parser.parse_args()
    files, edges=closure();before={n:sha(ROOT/n) for n in files}
    assert sha(NODE) == NODE_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('cast139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    manifest, proof=build(out)
    rows, expected, labels, diagnostics=corpus(manifest['definition'], args.phase)
    for name in files:
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True, exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    for name, value in (('inputs.json', rows), ('expected.json', expected),
                        ('labels.json', labels), ('model-diagnostics.json', diagnostics)):
        save(out/name, value)
    save(out/'config.json', dict(inputs=str(out/'inputs.json'), inputs_sha256=sha(out/'inputs.json')))
    frozen={p.name:sha(p) for p in [out/'inputs.json', out/'expected.json', out/'config.json', out/'manifest.json', out/manifest['module_file']]}
    assert before == {n:sha(ROOT/n) for n in files}
    save(out/'prepared.json', dict(source_before=before, source_import_edges=edges,
        frozen=frozen, expected_before_original=True, inputs_contain_expected=False,
        phase=args.phase, snapshot_restores=0))
    command=[str(NODE), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT/'scripts/run_cast139_oracle.mjs'), str(out), str(out/'config.json')]
    began=time.monotonic()
    with (out/'stdout.jsonl').open('wb') as so, (out/'stderr.log').open('wb') as se:
        p=subprocess.Popen(command, stdout=so, stderr=se, start_new_session=True)
        save(out/'owned-process.json', dict(pid=p.pid, pgid=p.pid, command=command, deadline_seconds=90))
        try:
            p.wait(timeout=90)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL);p.wait()
    terminal=dict(pid=p.pid, pgid=p.pid, exit_code=p.returncode,
        seconds=time.monotonic()-began, pid_missing=missing(p.pid), pgid_missing=missing(p.pid, True))
    save(out/'owned-terminal.json', terminal)
    actual=[json.loads(line) for line in (out/'stdout.jsonl').read_text().splitlines()]
    differences=[]
    for e,a in zip(expected, actual):
        if e['id'] != a.get('id'):
            differences.append(dict(field='case_id', expected=e['id'], actual=a.get('id')))
        if len(e['answers']) != len(a.get('answers', [])):
            differences.append(dict(id=e['id'], field='stage_count',
                expected=len(e['answers']), actual=len(a.get('answers', []))))
        if e != a:
            for stage,(es,as_) in enumerate(zip(e['answers'], a['answers'])):
                for key in set(es)|set(as_):
                    if es.get(key)!=as_.get(key):
                        differences.append(dict(id=e['id'], stage=stage, field=key,
                            expected=es.get(key), actual=as_.get(key)))
    if len(actual)!=len(expected):differences.append(dict(field='completed_rows', expected=len(expected), actual=len(actual)))
    assert before == {n:sha(ROOT/n) for n in files}
    assert frozen == {n:sha(out/n) for n in frozen}
    save(out/'differences.json', differences)
    runtime=json.loads((out/'runtime.json').read_text()) if (out/'runtime.json').exists() else None
    if p.returncode == 0:
        assert runtime['full922_calls'] == sum(x['repeats'] for x in rows)
        assert runtime['fresh_instances'] == len(rows)
        assert runtime['actual_host_calls'] == 0 and runtime['all_normal_returns']
        assert runtime['snapshot_restores'] == 0
    report=dict(version='0.139.0', build='f79c5e2b4', phase=args.phase,
        original_sha256=SOURCE_SHA, cases=len(rows), completed=len(actual),
        target_calls=sum(x['repeats'] for x in rows), differences=len(differences),
        process=terminal, runtime=runtime, source_before=before, source_after=before,
        source_import_edges=edges, original_side_snapshot_used=False,
        pure_model_reads_original=False,
        expected_definition_source='Current139 static88B extracted by builder; pure model gets explicit definition data; no captured Game or original execution supplies expectations',
        static_trace_sha256=sha(out/'static/trace.json'),
        manifest_sha256=sha(out/'manifest.json'), inputs_sha256=sha(out/'inputs.json'),
        expected_sha256=sha(out/'expected.json'), actual_sha256=sha(out/'stdout.jsonl'),
        compared=dict(full_unit_byte_occurrences=sum(len(x['state']['units432_hex'])*432*x['repeats'] for x in rows),
            owned80_byte_occurrences=80*sum(x['repeats'] for x in rows),
            complete_launch306_messages=sum(len(stage['launch306_packets']) for x in expected for stage in x['answers']),
            complete_launch306_payload_bytes=sum(len(p[1])//2 for x in expected for stage in x['answers'] for p in stage['launch306_packets']),
            original_592_or_HP169_packet_semantics_predicted=False),
        limitations=['Only current139 cleave/effect0, normal432targets, empty proc/item/modifier inputs and nonlethal numeric continuation.',
            'All432unit bytes,owned80,RNG,f64accounting,three logical spell sets and return are compared.',
            'Complete cleave launch306 packet is predicted; damage592/HP169 and other packet payloads and rawGame are observations.',
            'Model selectedIDs are checked as ordered306 target list; internal hits/draw counts remain model diagnostics,not original instrumentation.',
            'SyntheticGame,no naturalApp/world/input/owned scheduler/death or Windows/fullgame acceptance.'],
        complete_games=0, full_mainloop_frames=0, native_executions=0)
    save(out/'comparison.json', report)
    print(json.dumps(dict(directory=str(out), cases=len(rows), completed=len(actual),
        target_calls=report['target_calls'], differences=len(differences),
        comparison_sha256=sha(out/'comparison.json'), process=terminal,
        first_fields=[x['field'] for x in differences[:8]])), flush=True)
    if p.returncode or differences:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
