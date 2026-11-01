#!/usr/bin/env python3
"""Cleave135 independent922/1076 differential in admitted quiet Node fixture.

Synthetic resolved-state inputs only. A separately identified case reuses the
80B shape observed at UI Game installation, never the UI's full memory/state.
"""
from collections import Counter
from dataclasses import asdict, replace
import argparse
import hashlib
import json
import os
import random
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build, parse_source, section_list
from build_upgrade134_oracle import Reader, sha
from build_cleave135_oracle import build_cleave135_stack
from check_cast135_full_spec import definition_catalogue, inputs, unit, state_from_input
from check_level_cycle135 import make_input
from check_owned_cast135 import snapshot, equivalent

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.cast135 import CastDefinition, UnresolvedCast
from core_spec.cast_events135 import process_hits
from core_spec.cleave135 import (CleaveOwnedEntry135, cast_dispatch135,
    cast_cleave135, tick_owned_cleave135)
from core_spec.owned_cast135 import OwnedEntry135, OwnedSources135
from core_spec.death_pickup135 import apply_damage_lifesteal
from core_spec.level_cycle135 import from_dict

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
OBSERVATION = ROOT / 'evidence/game-entry0135-probe-20261101T135403.797895Z/observation-before-upload.json'
OBSERVED_OWNED_HEX = '246d5300010000000000003f0000803f0000803f000000000000803f0000803f00000000000000000000000000000000000000000000803f0000803f000000000000803f0000803f000000000000803f'
BASELINE_DIRECTORIES = dict(pilot='full0135-oracle-20261101T140325.761855Z', full='full0135-oracle-20261101T140356.630952Z')


def cleave_definition():
    binary = SOURCE.read_bytes()
    assert hashlib.sha256(binary).hexdigest() == SOURCE_SHA
    _, _, _, _, segments = parse_source(binary)
    memory = bytearray(max(s['address'] + s['length'] for s in segments if s['address'] is not None))
    for s in segments:
        if s['address'] is not None:
            memory[s['address']:s['address'] + s['length']] = binary[s['file_offset']:s['file_offset'] + s['length']]
    p = 5467428
    raw = bytes(memory[p:p + 88])
    w = struct.unpack('<22I', raw)
    name = bytes(memory[w[3]:w[3] + w[4]])
    assert (name, w[0], raw[84], w[11]) == (b'cleave', 0, 5, 845)
    # Original unmodified global0 is the fixture's linear-memory stack pointer.
    global_section = next(s for s in section_list(binary) if s[0] == 6)
    reader = Reader(binary, global_section[2], global_section[3])
    assert reader.uint() > 0 and reader.byte() == 0x7f and reader.byte() == 1 and reader.byte() == 0x41
    assert reader.sint() == 1048576 and reader.byte() == 0x0b
    return CastDefinition(p, name, raw[84], w[0], w[11], raw[85],
        w[12], w[13], w[14], w[15], w[16]), raw.hex()


def _entry(d, record):
    return (CleaveOwnedEntry135 if d.execution_kind == 5 else OwnedEntry135)(d, record)


def corpus(phase):
    cd, ch = cleave_definition()
    byid = {d.ability_id: (d, h) for d, h in definition_catalogue()}
    byid[b'cleave'] = (cd, ch)
    rows = []
    rng = random.Random(0x135845)

    def add(group, *, mode='cast', units=None, records=None, names=(b'cleave',),
            basic_name=b'fireball', basic=None, steps=(.1, .4, 8), overrides=None,
            class_byte=1, timer1628_bits=f.INF, seed=(1, 2, 3, 4), heal_gate=0):
        rawlevel = make_input(class_byte=class_byte, race_byte=1, level=1,
            phase=1, mode=1, heal_gate=heal_gate, hp_fraction=.3, rng_words=seed)
        level = from_dict(rawlevel)
        selected = [byid[n] for n in names]
        records = records if records is not None else [AbilityRecord(d.pointer) for d, _ in selected]
        entries = tuple(_entry(d, a) for (d, _), a in zip(selected, records))
        bd, bh = byid[basic_name]
        basic = basic or AbilityRecord(bd.pointer, remaining_cooldown_bits=f.INF)
        basic_entry = _entry(bd, basic)
        derived = dict(level.derived_bits)
        s = inputs([unit(j + 1, 1 + j * 1.3, (j % 2) * .3,
            hp_bits=f.from_float(10000000 - j * 1000), max_hp_bits=f.from_float(10000000))
            for j in range(5)] if units is None else units,
            phase=1, rng_words=list(seed), max_hp_bits=derived[1536],
            current_hp_bits=level.stats.current_hp_bits, damage_multiplier_bits=derived[1540],
            critical_chance_bits=derived[1548], critical_multiplier_bits=derived[1552],
            cooldown_multiplier_bits=derived[1544], area_multiplier_bits=derived[1580],
            extra_targets=derived[1592])
        s.update(overrides or {})
        derived[1536] = s['max_hp_bits']
        level = replace(level, derived_bits=tuple(sorted(derived.items())),
            stats=replace(level.stats, current_hp_bits=s['current_hp_bits']))
        state = state_from_input(s)
        ops, stages, accepted, casts = [], [], [], []

        def on_hit(cast, damage):
            nonlocal level
            level = replace(level, stats=replace(level.stats, now_bits=cast.combat.now_bits))
            level = apply_damage_lifesteal(level, damage.damage_bits)
            accepted.append((damage.target.target_id, damage.damage_bits))
            return cast

        def capture(kind, result=None):
            stage = dict(operation=kind, snapshot=snapshot(state, entries, basic_entry, level, timer))
            if result is not None:
                stage['success'] = result.success
                casts.append(dict(selected=list(result.selected_ids), hits=[list(h) for h in result.hits]))
            stages.append(stage)

        timer = timer1628_bits
        now = s['now_bits']
        if mode == 'cast':
            for index, entry in enumerate(entries):
                result = cast_dispatch135(state, entry.definition, entry.record, after_hit=on_hit)
                state = result.state
                ops.append(dict(kind='cast', entry_index=index, now_bits=now))
                capture('cast', result)
        else:
            for delta in steps:
                dt = delta['bits'] if isinstance(delta, dict) else f.from_float(delta)
                now = f.add(now, dt)
                state = replace(state, combat=replace(state.combat, now_bits=now))
                result = tick_owned_cleave135(state, entries, basic_entry, dt,
                    sources=OwnedSources135((), (), True), class_byte=class_byte,
                    timer1628_bits=timer, after_hit=on_hit)
                state, entries, basic_entry = result.state, result.entries, result.basic
                timer = result.prelude.timer1628_bits
                ops.append(dict(kind='owned', now_bits=now, dt_bits=dt))
                capture('owned')
                state, _ = process_hits(state, now, after_hit=on_hit)
                ops.append(dict(kind='process', now_bits=now))
                capture('process')
        if state.queued:
            finite = [h.due_bits for h in state.queued if -float('inf') < f.to_float(h.due_bits) < float('inf')]
            if finite:
                now = max(finite, key=f.to_float)
                state, _ = process_hits(state, now, after_hit=on_hit)
                ops.append(dict(kind='process', now_bits=now))
                capture('process')
        def dd(d):
            data = asdict(d)
            data['ability_id'] = d.ability_id.decode()
            return data
        rows.append(dict(id=len(rows), group=group, input=s, level=rawlevel,
            definitions=[dd(d) for d, _ in selected], definition_hex=[h for _, h in selected],
            owned_hex=[a.to_bytes().hex() for a in records], basic_definition=dd(bd),
            basic_definition_hex=bh, basic_hex=basic.to_bytes().hex(), ops=ops,
            expected=stages, independent_cast_details=casts,
            accepted_hit_count=len(accepted), timer1628_bits=timer1628_bits))

    add('pilot-full922-immediate')
    add('pilot-empty-full922', units=[])
    add('pilot-owned1076-warrior-prelude', mode='owned', timer1628_bits=0)
    add('pilot-cleave-real-basic1076', mode='owned', basic_name=b'cleave',
        basic=AbilityRecord(cd.pointer, remaining_cooldown_bits=0))
    observed = AbilityRecord.from_bytes(bytes.fromhex(OBSERVED_OWNED_HEX))
    assert observed == AbilityRecord(cd.pointer)
    observed_metadata = json.loads(OBSERVATION.read_text())
    assert observed_metadata['original_sha256'] == SOURCE_SHA and OBSERVED_OWNED_HEX in OBSERVATION.read_text()
    add('observed-UI-owned80B-shape-synthetic1076', mode='owned', records=[observed],
        timer1628_bits=0, steps=(.016, .484, .1, 2))
    if phase == 'pilot':
        return rows
    for n in (0, 1, 2, 3, 4, 8, 20, 21, 32, 65, 128):
        for extra in (0, 1, 7, 0xfffffffd, 0xffffffff):
            add('target-count-sort-and-u32-wrap',
                units=[unit(j + 1, (j % 9 - 4) * .8, (j // 9 - 3) * .8,
                    hp_bits=f.from_float(1000000 - j * 300), max_hp_bits=f.from_float(1000000)) for j in range(n)],
                records=[replace(observed, extra_targets=extra)],
                overrides=dict(extra_targets=2))
    for n in range(9):
        add('range7-boundary-markers-and-distance-ties',
            units=[unit(j + 1, 0, to_xy=[b, 0], from_xy=[b, 0], marker=int(j % 4 == 0))
                for j, b in enumerate((0x40dfffff, 0x40e00000, 0x40e00001,
                    f.from_float(-7), f.from_float(2), f.from_float(-2), 0, f.INF, 0x7fc00001)[:n])],
            records=[replace(observed, extra_targets=20)])
    for k in range(180):
        count = k % 13
        us = [unit(j + 1, rng.uniform(-9, 9), rng.uniform(-9, 9),
            hp_bits=f.from_float(1000000 + rng.uniform(0, 1000000)),
            max_hp_bits=f.from_float(2000000), marker=int(rng.randrange(8) == 0),
            from_xy=[f.from_float(rng.uniform(-10, 10)), f.from_float(rng.uniform(-10, 10))],
            duration_bits=f.from_float([0, 2, 20][j % 3]), movement_time_bits=f.from_float(5)) for j in range(count)]
        a = replace(observed, damage_bits=f.from_float(rng.uniform(.1, 4)),
            additional_damage_bits=f.from_float(rng.uniform(.2, 3)), extra_targets=k % 5,
            additional_targets=(k // 5) % 4, area_bits=f.from_float(15),
            additional_area_bits=f.from_float(.001), life_damage_bits=f.from_float((k % 3) * .01))
        add('random-motion-multipliers-critical-and-area-ignored', units=us, records=[a],
            seed=tuple(rng.getrandbits(32) for _ in range(4)),
            overrides=dict(critical_chance_bits=f.from_float([0, .3, 1, -.1, 1.1][k % 5]),
                critical_multiplier_bits=f.from_float([.5, 1, 1.5, 2, 3][k % 5]),
                area_multiplier_bits=f.from_float([0, .5, 1000][k % 3]),
                damage_multiplier_bits=f.from_float([0, -.1, .1, 1, 4][k % 5])))
    for k in range(36):
        us = [unit(1, 1, kind_40=2), unit(2, 2, elite_416=1),
            unit(3, 3, priority_until372_bits=f.from_float(20)),
            unit(4, 4, elite_244=0, phase_until408_bits=f.from_float(20)),
            unit(5, 5, kind_40=2, linked_id='4'), unit(6, 6, elite_244=0,
                phase_until412_bits=f.from_float(20))]
        add('priority-special-elite-linked-and-deferred', units=us[k % 6:] + us[:k % 6],
            records=[replace(observed, extra_targets=k % 5)],
            seed=tuple(rng.getrandbits(32) for _ in range(4)),
            overrides=dict(critical_chance_bits=f.from_float(.5)))
    for remaining in (0, 0x80000000, f.from_float(-1), f.from_float(.5), f.INF, f.INF | f.SIGN, 0x7fc00001):
        for cd_bits in (0, f.from_float(.2), f.from_float(2), 0x7fc00001):
            add('owned-basic-countdown-floor-and-nonfinite', mode='owned',
                records=[replace(observed, remaining_cooldown_bits=remaining, cooldown_bits=cd_bits)],
                basic_name=b'cleave', basic=replace(observed, remaining_cooldown_bits=remaining, cooldown_bits=cd_bits),
                timer1628_bits=0)
    for k in range(36):
        add('ordered-cleave-common-prelude-and-basic', mode='owned',
            names=(b'cleave', b'whirlwind', b'fireball', b'cleave'),
            basic_name=b'cleave', basic=replace(observed, remaining_cooldown_bits=0),
            class_byte=(1, 2, 4, 8)[k % 4], timer1628_bits=0,
            steps=(.1,) * 20, seed=tuple(rng.getrandbits(32) for _ in range(4)),
            heal_gate=(0, 5)[k % 2])
    for name in (b'fireball', b'whirlwind'):
        add('opt-in-common-dispatch-regression', mode='owned', names=(name,), timer1628_bits=0)
    return rows


def source_files():
    files = {str(Path(module.__file__).resolve().relative_to(ROOT))
        for module in tuple(sys.modules.values())
        if getattr(module, '__file__', None) and str(Path(module.__file__).resolve()).startswith(str(ROOT) + '/')}
    files.update(('scripts/check_cleave135.py', 'scripts/run_cleave135_oracle.mjs',
        'scripts/full135_host.mjs', 'scripts/trace_cleave135.py', 'scripts/cleave135_host.mjs'))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot')
    parser.add_argument('--stack-guard', action='store_true')
    args = parser.parse_args()
    files = source_files()
    before = {n: sha(ROOT / n) for n in files}
    observation_sha = sha(OBSERVATION)
    rows = corpus(args.phase)
    assert files == source_files()
    # The preexisting default gate still rejects cleave; callers opt in above.
    try:
        OwnedEntry135(cleave_definition()[0], AbilityRecord(5467428))
    except UnresolvedCast:
        pass
    else:
        raise AssertionError('Default behavior unexpectedly changed')
    fixture_text = ''.join(json.dumps(c, allow_nan=False, separators=(',', ':')) + '\n' for c in rows)
    baseline = ROOT / 'evidence' / BASELINE_DIRECTORIES[args.phase] / 'cleave135-fixtures.jsonl'
    if args.stack_guard:
        assert fixture_text.encode() == baseline.read_bytes(), 'Stack rerun must preserve baseline input/expected bytes'
    out, manifest = build_cleave135_stack() if args.stack_guard else build(['cast', 'owned_tick', 'process_hits'])
    for name in files:
        target = out / 'source-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
        assert sha(target) == before[name]
    fixtures = out / 'cleave135-fixtures.jsonl'
    fixtures.write_text(fixture_text)
    assert [json.loads(x) for x in fixtures.read_text().splitlines()] == rows
    artifacts = [fixtures, out / 'manifest.json', out / manifest['module_file']]
    if args.stack_guard:
        artifacts += [out / name for name in ('function-only-manifest.json',
            'stack-validation.stdout.txt', 'stack-validation.stderr.txt')]
    frozen = {p.name: sha(p) for p in artifacts}
    assert sha(RUNTIME) == RUNTIME_SHA
    assert subprocess.check_output([str(RUNTIME), '--version'], text=True).strip() == 'v22.23.4'
    command = [str(RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/run_cleave135_oracle.mjs'), str(out), str(fixtures)]
    if args.stack_guard:
        command.append('--stack-guard')
    result = out / 'cleave135-results.jsonl'
    stderr = out / 'cleave135-stderr.log'
    started = time.monotonic()
    with result.open('w') as stream, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stream, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=60)
        finally:
            # This also kills unexpected descendants after a main-process exit.
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
    duration = time.monotonic() - started
    try:
        os.killpg(child.pid, 0)
    except ProcessLookupError:
        group_absent = True
    else:
        group_absent = False
    assert group_absent
    if code:
        raise RuntimeError(f'Original exit{code}; inspect {out}')
    actual = [json.loads(x) for x in result.read_text().splitlines()]
    assert [x['id'] for x in actual] == list(range(len(rows)))
    failures = [dict(id=c['id'], group=c['group'], expected=c['expected'], actual=a['stages'])
        for c, a in zip(rows, actual) if not equivalent(c['expected'], a['stages'])]
    mismatch = out / 'cleave135-mismatches.json'
    mismatch.write_text(json.dumps(failures, indent=2) + '\n')
    after = {n: sha(ROOT / n) for n in files}
    assert before == after
    assert sha(SOURCE) == SOURCE_SHA and sha(RUNTIME) == RUNTIME_SHA
    assert observation_sha == sha(OBSERVATION)
    assert frozen == {p.name: sha(p) for p in artifacts}
    runtime = json.loads((out / 'cleave135-runtime.json').read_text())
    if args.stack_guard:
        assert runtime['stack_all_restored'] is True
        assert len([x for x in runtime['stack_checks'] if x['role'] != '__wbindgen_malloc']) == sum(len(c['ops']) for c in rows)
    receipt = dict(version='0.135.1', build='0898d5e3', phase=args.phase, private_stack_guard=args.stack_guard,
        cases=len(rows), stages=sum(len(c['ops']) for c in rows), mismatch_cases=len(failures),
        accepted_hits=sum(c['accepted_hit_count'] for c in rows),
        groups=dict(Counter(c['group'] for c in rows)), original_wasm_sha256=SOURCE_SHA,
        source_sha256_before=before, source_sha256_after=after,
        artifacts={p.name: sha(p) for p in [*artifacts, result, stderr, mismatch, out / 'cleave135-runtime.json']},
        process=dict(command=command, pid=child.pid, pgid=child.pid, exit_code=code,
            deadline_seconds=60, seconds=round(duration, 3), process_group_absent_after=True),
        runtime=runtime,
        observed_record_provenance=dict(path=str(OBSERVATION.relative_to(ROOT)),
            sha256=observation_sha, record_hex=OBSERVED_OWNED_HEX,
            scope='UI-observed80B input shape only, relocated into a synthetic quiet fixture'),
        independent_expected_before_original=True, source_snapshots=True, only_changed_section=7,
        baseline_input_expected_identity=(dict(path=str(baseline.relative_to(ROOT)),
            sha256=sha(baseline), bytes_equal=True, previous_counts_not_added=True) if args.stack_guard else None),
        default_gate_unchanged_and_cleave_rejected=True,
        limitations=['Complete original922/1076/1754 resolved-state component calls, not natural Game or880.',
            'Empty item/talent/proc snapshots, G1596=0/G908=0/G772=0; nonlethal ordinary914 domain.',
            'G1256 is the actual racial slot; this corpus uses explicit effect0 isolated records there. Legacy basic/real-basic labels do not prove real racial scheduling.',
            'Full packet bytes/visual metadata, physical heal logs and complete game are not projected.',
            ('Original global0 inspected before/after every exposed target/allocator invocation; original internal callee calls are not separately instrumented. No setter exposed or write performed.'
                if args.stack_guard else 'Original linear-memory stack init1048576 is statically checked; no stack export/write or dynamic stack measurement.'),
            'Only the existing declared float fields use NaN-class equality; integer fields remain strict.'])
    receipt_path = out / 'cleave135-comparison.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), cases=len(rows), stages=receipt['stages'],
        accepted_hits=receipt['accepted_hits'], mismatch_cases=len(failures),
        first_ids=[c['id'] for c in failures[:12]], seconds=duration)))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
