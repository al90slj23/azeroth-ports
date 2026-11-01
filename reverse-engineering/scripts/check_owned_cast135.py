#!/usr/bin/env python3
"""Independent learned80B/basic80B1076 + per-hit HP original differential."""
from collections import Counter
from dataclasses import asdict, replace
import argparse, json, os, random, re, signal, struct, subprocess, sys, time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
from check_cast135_full_spec import definition_catalogue, inputs, unit, state_from_input, projection
from check_level_cycle135 import make_input
from check_death_pickup135 import SOURCE_FILES as DEATH_FILES
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.cast_events135 import process_hits
from core_spec.owned_cast135 import OwnedEntry135, OwnedSources135, tick_owned
from core_spec.death_pickup135 import apply_damage_lifesteal
from core_spec.level_cycle135 import from_dict

FILES = tuple(dict.fromkeys(('scripts/check_owned_cast135.py', 'scripts/run_owned_cast135_oracle.mjs',
    'reconstruction/core_spec/__init__.py',
    'reconstruction/core_spec/cast_events135.py', 'reconstruction/core_spec/owned_cast135.py',
    'reconstruction/core_spec/owned_prelude135.py',
    *DEATH_FILES)))
IMPORT_SHA = {n: sha(ROOT / n) for n in FILES}
RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def corpus(phase):
    definitions = definition_catalogue()
    byid = {d.ability_id: (d, raw) for d, raw in definitions}
    rows = []
    rng = random.Random(0x1351076)

    def add(group, names, *, count=3, class_byte=8, phase_byte=1, records=None,
            basic_name=b'fireball', basic=None, steps=None, overrides=None, seed=(1, 2, 3, 4), heal_gate=0,
            timer1628_bits=0):
        rawlevel = make_input(class_byte=class_byte, race_byte=1, level=1,
            phase=phase_byte, mode=1, heal_gate=heal_gate, hp_fraction=.3, rng_words=seed)
        level = from_dict(rawlevel)
        selected = [byid[name] for name in names]
        records = records if records is not None else [AbilityRecord(d.pointer) for d, _ in selected]
        entries = tuple(OwnedEntry135(d, a) for (d, _), a in zip(selected, records))
        bd, bh = byid[basic_name]
        basic = basic or AbilityRecord(bd.pointer, remaining_cooldown_bits=f.INF)
        basic_entry = OwnedEntry135(bd, basic)
        derived = dict(level.derived_bits)
        s = inputs([unit(j + 1, 1 + j * 2, (j % 2) * .3,
            hp_bits=f.from_float(1e9), max_hp_bits=f.from_float(1e9)) for j in range(count)],
            phase=phase_byte, rng_words=list(seed), max_hp_bits=derived[1536],
            current_hp_bits=level.stats.current_hp_bits, damage_multiplier_bits=derived[1540],
            critical_chance_bits=derived[1548], critical_multiplier_bits=derived[1552],
            cooldown_multiplier_bits=derived[1544], area_multiplier_bits=derived[1580],
            extra_targets=derived[1592])
        s.update(overrides or {})
        # Keep the independent HP consumer's maximum identical to cast input.
        derived[1536] = s['max_hp_bits']
        level = replace(level, derived_bits=tuple(sorted(derived.items())),
            stats=replace(level.stats, current_hp_bits=s['current_hp_bits']))
        state = state_from_input(s)
        ops, stages, accepted = [], [], []

        def on_hit(cast, damage):
            nonlocal level
            level = replace(level, stats=replace(level.stats, now_bits=cast.combat.now_bits))
            level = apply_damage_lifesteal(level, damage.damage_bits)
            accepted.append((damage.target.target_id, damage.damage_bits))
            return cast

        now = s['now_bits']
        timer = timer1628_bits
        for delta in (steps if steps is not None else [.1, .4, 8]):
            dt = delta if isinstance(delta, dict) else {'bits': f.from_float(delta)}
            now = f.add(now, dt['bits'])
            state = replace(state, combat=replace(state.combat, now_bits=now))
            result = tick_owned(state, entries, basic_entry, dt['bits'],
                sources=OwnedSources135((), (), True), class_byte=class_byte,
                timer1628_bits=timer, after_hit=on_hit)
            state, entries, basic_entry = result.state, result.entries, result.basic
            timer = result.prelude.timer1628_bits
            ops.append(dict(kind='owned', now_bits=now, dt_bits=dt['bits']))
            stages.append(snapshot(state, entries, basic_entry, level, timer))
            state, _ = process_hits(state, now, after_hit=on_hit)
            ops.append(dict(kind='process', now_bits=now))
            stages.append(snapshot(state, entries, basic_entry, level, timer))
        if state.queued:
            finite = [h.due_bits for h in state.queued if -float('inf') < f.to_float(h.due_bits) < float('inf')]
            if finite:
                now = max(finite, key=f.to_float)
                state, _ = process_hits(state, now, after_hit=on_hit)
                ops.append(dict(kind='process', now_bits=now))
                stages.append(snapshot(state, entries, basic_entry, level, timer))
        def dd(d):
            value = asdict(d); value['ability_id'] = d.ability_id.decode(); return value
        rows.append(dict(id=len(rows), group=group, input=s, level=rawlevel,
            definitions=[dd(d) for d, _ in selected], definition_hex=[h for _, h in selected],
            owned_hex=[a.to_bytes().hex() for a in records], basic_definition=dd(bd),
            basic_definition_hex=bh, basic_hex=basic.to_bytes().hex(), ops=ops,
            expected=stages, accepted_hit_count=len(accepted), timer1628_bits=timer1628_bits))

    add('pilot-learned-area', [b'whirlwind'])
    add('pilot-empty-retry', [b'fireball'], count=0)
    add('pilot-main-and-basic', [b'fireball', b'whirlwind'],
        basic=AbilityRecord(byid[b'fireball'][0].pointer, remaining_cooldown_bits=0))
    add('pilot-hellfire-floor', [b'hellfire'])
    add('pilot-earth-shock', [b'earth_shock', b'lightning_bolt'])
    add('pilot-warrior-melee-prelude', [b'whirlwind'], class_byte=1)
    if phase == 'pilot':
        return rows
    for d, _ in definitions:
        for count in (0, 1, 3):
            for remaining in (0, f.from_float(.5), f.INF, 0x7fc00001):
                a = AbilityRecord(d.pointer, remaining_cooldown_bits=remaining)
                add('all25-owned-countdown-and-empty', [d.ability_id], count=count, records=[a])
        add('all25-real-basic-only', [], basic_name=d.ability_id,
            basic=AbilityRecord(d.pointer, remaining_cooldown_bits=0))
    for k in range(160):
        chosen = [definitions[(k + j * 7) % len(definitions)] for j in range(1 + k % 6)]
        records = [replace(AbilityRecord(d.pointer), level=1 + k % 20,
            remaining_cooldown_bits=f.from_float([0, .1, .7][j % 3]),
            damage_bits=f.from_float(rng.uniform(.1, 3)), additional_damage_bits=f.from_float(rng.uniform(.2, 2)),
            cooldown_bits=f.from_float(rng.uniform(-.2, 2)), additional_cooldown_bits=f.from_float(rng.uniform(.1, 2)),
            area_bits=f.from_float(rng.uniform(.2, 3)), additional_area_bits=f.from_float(rng.uniform(.2, 2)),
            extra_targets=j % 3, additional_targets=k % 3, life_damage_bits=f.from_float((k % 3) * .02))
            for j, (d, _) in enumerate(chosen)]
        bd, _ = definitions[(k * 11) % len(definitions)]
        basic = replace(AbilityRecord(bd.pointer), remaining_cooldown_bits=f.from_float(k % 3 / 10))
        add('ordered-owned-and-basic-mixed-multipliers', [d.ability_id for d, _ in chosen],
            count=k % 9, records=records, basic_name=bd.ability_id, basic=basic,
            overrides=dict(critical_chance_bits=f.from_float([0, .3, 1][k % 3]),
                cooldown_multiplier_bits=f.from_float([0, .3, 1, 2][k % 4])),
            seed=tuple(rng.getrandbits(32) for _ in range(4)))
    for k, bits in enumerate((0, 0x80000000, f.from_float(-1), f.from_float(.25), f.INF, f.INF | f.SIGN, 0x7fc00001)):
        for initial in (0, f.INF, 0x7fc00001):
            d, _ = byid[b'whirlwind']
            add('NaN-and-nonfinite-countdown-CD', [d.ability_id],
                records=[AbilityRecord(d.pointer, remaining_cooldown_bits=initial, cooldown_bits=bits)],
                basic_name=d.ability_id, basic=AbilityRecord(d.pointer, remaining_cooldown_bits=initial, cooldown_bits=bits))
    for cls in (1, 2, 3, 4, 5, 7, 8, 9, 11, 0, 6, 10, 255):
        for gate in (0, 5):
            for count in (0, 1, 3):
                add('all-classes-prelude-hit-selfheal-and-fallback', [b'whirlwind', b'fireball'],
                    class_byte=cls, heal_gate=gate, count=count)
    for timer in (0, 0x80000000, f.from_float(-1), f.from_float(.1), f.from_float(1), f.INF, f.INF | f.SIGN, 0x7fc00001):
        for cls in (1, 2, 4, 8):
            add('prelude-countdown-nonfinite', [b'whirlwind'], class_byte=cls, timer1628_bits=timer)
    for k in range(12):
        add('continuous-owned-prelude-delayed-hit-order', [b'whirlwind', b'fireball', b'earth_shock'],
            class_byte=(1, 2, 4, 8)[k % 4], count=1 + k % 6, steps=[.1] * 80,
            basic=AbilityRecord(byid[b'fireball'][0].pointer, remaining_cooldown_bits=0))
    for value in (0, -.2):
        for name in (b'whirlwind', b'hellfire'):
            add('minimum-one-post-core-heal', [name],
                overrides=dict(damage_multiplier_bits=f.from_float(value)))
    d, _ = byid[b'fireball']
    add('repeated-same-GUID-ordered-projectile-heals', [b'fireball', b'fireball', b'whirlwind'],
        count=1, records=[AbilityRecord(byid[name][0].pointer, remaining_cooldown_bits=0)
            for name in (b'fireball', b'fireball', b'whirlwind')],
        basic=AbilityRecord(d.pointer, remaining_cooldown_bits=0))
    return rows


def snapshot(state, entries, basic, level, timer):
    result = projection(state)
    result.pop('active_remaining_bits')
    result.update(owned_words=[list(e.record.words()) for e in entries], basic_words=list(basic.record.words()),
        current_hp_bits=level.stats.current_hp_bits,
        player_fields={str(k): v for k, v in level.player_fields}, refresh_flag772=0,
        timer1628_bits=timer)
    return result


FLOAT_WORDS = {2, 3, 4, 6, 7, 13, 14, 16, 17, 18, 19}


def equivalent(want, actual, path=''):
    if type(want) != type(actual): return False
    if isinstance(want, dict):
        return set(want) == set(actual) and all(equivalent(v, actual[k], path + '.' + k) for k, v in want.items())
    if isinstance(want, list):
        return len(want) == len(actual) and all(equivalent(v, a, path + f'[{j}]') for j, (v, a) in enumerate(zip(want, actual)))
    word = re.search(r'\.(?:owned_words\[\d+\]|basic_words)\[(\d+)\]$', path)
    floating = ('.hp_bits[' in path or path.endswith(('.current_hp_bits', '.timer1628_bits')) or
        ('.queued[' in path and path.endswith(('.due_bits', '.damage_bits'))) or
        word is not None and int(word[1]) in FLOAT_WORDS)
    return want == actual or floating and type(want) is int and f.is_nan(want) and f.is_nan(actual)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot'); args = parser.parse_args()
    before = {n: sha(ROOT / n) for n in FILES}; assert before == IMPORT_SHA
    rows = corpus(args.phase)
    out, manifest = build(['owned_tick', 'process_hits'])
    snapshots = out / 'source-snapshot'; snapshots.mkdir()
    for name in FILES:
        target = snapshots / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes()); assert sha(target) == before[name]
    fixtures = out / 'owned-cast135-fixtures.jsonl'
    fixtures.write_text(''.join(json.dumps(c, allow_nan=False, separators=(',', ':')) + '\n' for c in rows))
    assert [json.loads(line) for line in fixtures.read_text().splitlines()] == rows
    artifacts = [fixtures, out / 'manifest.json', out / manifest['module_file']]
    frozen = {p.name: sha(p) for p in artifacts}
    assert sha(RUNTIME) == RUNTIME_SHA
    assert subprocess.check_output([str(RUNTIME), '--version'], text=True).strip() == 'v22.23.4'
    command = [str(RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/run_owned_cast135_oracle.mjs'), str(out), str(fixtures)]
    result = out / 'owned-cast135-results.jsonl'; stderr = out / 'owned-cast135-stderr.log'; start = time.monotonic()
    with result.open('w') as stream, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stream, stderr=err, start_new_session=True)
        try: code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL); child.wait(); raise RuntimeError(f'Owned1076 deadline; {out}')
    duration = time.monotonic() - start
    if code: raise RuntimeError(f'Original exit{code}; inspect{out}')
    actual = [json.loads(line) for line in result.read_text().splitlines()]
    assert [r['id'] for r in actual] == list(range(len(rows)))
    failures = [dict(id=c['id'], group=c['group'], expected=c['expected'], actual=a['stages'])
        for c, a in zip(rows, actual) if not equivalent(c['expected'], a['stages'])]
    mismatch = out / 'owned-cast135-mismatches.json'; mismatch.write_text(json.dumps(failures, indent=2) + '\n')
    after = {n: sha(ROOT / n) for n in FILES}; assert before == after
    assert sha(SOURCE) == SOURCE_SHA and sha(RUNTIME) == RUNTIME_SHA
    assert frozen == {p.name: sha(p) for p in artifacts}
    receipt = dict(version='0.135.1', build='0898d5e3', phase=args.phase,
        cases=len(rows), stages=sum(len(c['ops']) for c in rows), mismatch_cases=len(failures),
        accepted_hits=sum(c['accepted_hit_count'] for c in rows), groups=dict(Counter(c['group'] for c in rows)),
        original_wasm_sha256=SOURCE_SHA, source_sha256_before=before, source_sha256_after=after,
        artifacts={p.name: sha(p) for p in [*artifacts, result, stderr, mismatch, out / 'owned-cast135-runtime.json']},
        process=dict(command=command, pid=child.pid, pgid=child.pid, exit_code=code, deadline_seconds=60, seconds=round(duration, 3)),
        runtime=json.loads((out / 'owned-cast135-runtime.json').read_text()),
        independent_expected_before_original=True, source_snapshots=True, only_changed_section=7,
        limitations=['Resolved-state1076/1754 phases; complete2088/player producers and880 scheduling remain pending.',
            'Empty item/definition/proc snapshots, G1596=0/G908=0/G772=0, nonlethal ordinary targets.',
            'Main cast supports25 effect0 execution0/2 definitions; other effects require independent recovery.',
            'Physical packet bytes/metadata/account heal logs/complete game remain pending.',
            'Only declared float fields use NaN classification equality; integer fields are strict.'])
    (out / 'owned-cast135-comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), cases=len(rows), stages=receipt['stages'], mismatch_cases=len(failures),
        first_ids=[c['id'] for c in failures[:12]], seconds=duration)))
    if failures: raise SystemExit(1)


if __name__ == '__main__': main()
