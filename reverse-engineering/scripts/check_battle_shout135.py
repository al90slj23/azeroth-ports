#!/usr/bin/env python3
"""Expected-first learned Battle Shout922/1076/2088 numeric differential."""
from collections import Counter
from dataclasses import asdict, dataclass, replace
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction'))
from build_full135_oracle import SOURCE, SOURCE_SHA, VALIDATOR_SHA, build, section_list, export_entries
from build_upgrade134_oracle import unsigned
from production_closure135 import production_sources135
from trace_battle_shout135 import trace_battle_shout135
from check_level_cycle135 import make_input, empty_sources
from check_cast135_full_spec import inputs, unit, state_from_input
from ai_world135_inputs import ASSET_WORLD, HASHES, load_asset_world135
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.battle_shout135 import (POINTER, RAW88_HEX, BattleShoutDefinition135,
    PendingBattleShout135, cast_battle_shout135, expire_battle_shout135)
from core_spec.cast_catalogue135 import definition
from core_spec.cast135 import CastResult
from core_spec.level_cycle135 import from_dict
from core_spec.owned_cast135 import OwnedEntry135, OwnedSources135, tick_owned

NODE = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


@dataclass(frozen=True)
class FixtureEntry135(OwnedEntry135):
    def __post_init__(self):
        if self.record.definition_pointer != self.definition.pointer or (
                self.definition.pointer, self.definition.effect_tag, self.definition.execution_kind) not in (
                (POINTER, 8, 9), (5476580, 8, 9)):
            raise ValueError('Only exact Battle Shout and inactive real Perception fixture entries admitted')


def level_raw(level):
    result = {name: asdict(getattr(level, name)) for name in ('progression', 'stats', 'sources')}
    result.update(derived_bits=dict(level.derived_bits), player_fields=dict(level.player_fields), rng_words=level.rng_words,
        choice_inputs=dict(owned=[dict(ability_id=x.ability_id, record_hex=x.record.to_bytes().hex())
            for x in level.choice_inputs.owned], blocked_ids=level.choice_inputs.blocked_ids,
            banished_keys=level.choice_inputs.banished_keys, flag275=level.choice_inputs.flag275,
            flag2581=level.choice_inputs.flag2581))
    result.update({key: getattr(level, key) for key in ('phase2587', 'selection_kind2585', 'generation_counter2400',
        'flags2576', 'gate2572', 'flags2573', 'heal_gate387', 'pool756_bits')})
    return result


def sync(cast, level, now):
    d = dict(level.derived_bits)
    return replace(cast, combat=replace(cast.combat, now_bits=now), rng_words=level.rng_words,
        damage_multiplier_bits=d[1540], max_hp_bits=d[1536], critical_chance_bits=d[1548],
        critical_multiplier_bits=d[1552], area_multiplier_bits=d[1580], cooldown_multiplier_bits=d[1544], extra_targets=d[1592])


def projection(cast, level, records, basic, live, attempts, timer, success):
    return dict(success=success, live_records=live, owned_hex=[row.to_bytes().hex() for row in records],
        basic_hex=basic.to_bytes().hex(), derived_bits=dict(level.derived_bits), current_hp_bits=level.stats.current_hp_bits,
        auxiliary_bits={1444: level.stats.pool1532_bits, 1448: level.stats.pool1536_bits,
            1348: level.stats.conditional1348_bits, 768: level.stats.pool768_bits, 756: level.pool756_bits},
        shield_source=level.stats.conditional1344_id, speed_bits=level.stats.previous_speed_bits,
        player_fields={key: value for key, value in level.player_fields if key in (22, 28, 1109)},
        rng_words=cast.rng_words, attempted_spell_sets=attempts, timer1628_bits=timer,
        message_sequence=123, action_sequence=1, effect_counter=0)


def actual_selection_input():
    from core_spec.headless135 import from_opening_handoff, step_frame, select, _cast_state
    from core_spec.opening135 import EmptyOpeningInput135
    from core_spec.opening_handoff135 import initialize_absent_companion_handoff
    from core_spec.profile_companions135 import EmptyCompanionProfile135
    from core_spec.special2376_notify135 import SpecialLocale2376_135, ELWYNN_ENGLISH_NAMES
    world = load_asset_world135()
    handoff = initialize_absent_companion_handoff(EmptyOpeningInput135(1, 1, 0, 0, 42), world,
        companion_profile=EmptyCompanionProfile135(()), title_utf8=b'Elwynn Forest', subtitle_utf8=b'')
    state = from_opening_handoff(handoff, navigation_enabled=False,
        special_locale=SpecialLocale2376_135(ELWYNN_ENGLISH_NAMES))
    selections = []
    for _ in range(379):
        state, _, status = step_frame(state, f.from_float(.1))
        if status != 'ordered_frame_projection':
            raise ValueError('Actual selection replay stopped before379: ' + status)
        while state.collection.level.phase2587 == 2:
            cards = state.collection.level.candidates
            index = next((i for i, card in enumerate(cards) if card.variant == 'upgrade'), 0)
            selections.append(dict(frame=state.frames, index=index, card=asdict(cards[index])))
            state, status = select(state, index)
            if status not in ('running', 'choice_regenerated'):
                raise ValueError('Actual selection replay boundary: ' + status)
    owned = state.collection.level.choice_inputs.owned
    index = next(i for i, row in enumerate(owned) if row.ability_id == 'battle_shout')
    assert state.selections == 4 and state.frames == 379 and selections[-1]['card']['ability_id'] == 'battle_shout'
    _, _, boundary = step_frame(state, f.from_float(.1))
    assert boundary == 'pending_selected_ability'
    cast = _cast_state(state)
    # The actual spatial/HP/owner states are retained. LinkedNone is not read
    # by the actual effect8 target query, and original fixture rows are explicit.
    units = []
    for spatial in cast.spatial:
        u = spatial.unit
        units.append(unit(u.target_id, 0, marker=u.marker, kind_40=u.kind_40, kind_64=u.kind_64,
            elite_244=u.elite_244, elite_416=u.elite_416,
            linked_id=str(0xa55aa55aa55aa55a if u.linked_id_32 is None else u.linked_id_32),
            hp_bits=u.hp_bits, max_hp_bits=u.max_hp_bits, from_xy=spatial.from_xy, to_xy=spatial.to_xy,
            duration_bits=u.movement_duration_344_bits, movement_time_bits=u.movement_time_340_bits,
            phase_until408_bits=u.phase_until_408_bits, phase_until412_bits=u.phase_until_412_bits,
            priority_until372_bits=spatial.priority_until372_bits))
    return state, cast, units, index, selections


def corpus(full):
    cases, expectations, labels = [], [], []
    b = f.from_float
    def add(group, *, cls=1, race=1, distance=1, live=(), unknown=(), changes=None,
            attempts=((), (), ()), busy=0, context=0, ops=None, actual=None, isolated_owned=False):
        if actual is None:
            sources = empty_sources()
            sources['live_effects'] = [dict(kind=row[2], value_bits=0 if row[2] == 12 else row[3],
                spell_id=row[5], expires_bits=row[6]) for row in live]
            raw = make_input(class_byte=cls, race_byte=race, level=1, phase=1, mode=0, hp_fraction=.3,
                sources=sources, owned=('battle_shout',))
            raw['stats'].update(conditional1344_id=0, conditional1348_bits=0, pool1532_bits=0, pool1536_bits=0, pool768_bits=0)
            level = from_dict(raw)
            records = [replace(AbilityRecord(POINTER), **(changes or {}))]
            d = dict(level.derived_bits)
            s = inputs([] if distance is None else [unit(2, distance)], source_id='1', now_bits=level.stats.now_bits,
                rng_words=list(level.rng_words), context908=context, max_hp_bits=d[1536], current_hp_bits=level.stats.current_hp_bits,
                damage_multiplier_bits=d[1540], cooldown_multiplier_bits=d[1544], critical_chance_bits=d[1548],
                critical_multiplier_bits=d[1552], area_multiplier_bits=d[1580], extra_targets=d[1592])
            cast = replace(state_from_input(s), attempted_spell_ids=tuple(attempts[0]))
            live_records = tuple(struct.pack('<8I', *row).hex() for row in live)
            battle_index, z = 0, 0
        else:
            state, cast, units, battle_index, selections = actual
            level = state.collection.level
            records = [row.record for row in level.choice_inputs.owned]
            if isolated_owned:
                records, battle_index = [records[battle_index]], 0
            attempts = (cast.attempted_spell_ids,) * 3
            live_records, unknown = state.live_records, state.unspecified_live_words
            raw = level_raw(level)
            s = inputs(units, now_bits=cast.combat.now_bits, phase=cast.combat.phase_2579,
                player_xy=cast.player_xy, rng_words=list(cast.rng_words), source_id=str(cast.source_id),
                current_target_id=str(cast.current_target_id), max_hp_bits=cast.max_hp_bits,
                current_hp_bits=level.stats.current_hp_bits, damage_multiplier_bits=cast.damage_multiplier_bits,
                cooldown_multiplier_bits=cast.cooldown_multiplier_bits, critical_chance_bits=cast.critical_chance_bits,
                critical_multiplier_bits=cast.critical_multiplier_bits, area_multiplier_bits=cast.area_multiplier_bits,
                extra_targets=cast.extra_targets, context908=0)
            z = state.collection.player_xyz[2]
        initial_live, initial_records, initial_unknown = live_records, records[:], unknown
        basic = replace(AbilityRecord(5476580), remaining_cooldown_bits=f.INF)
        timer, ledgers, snapshots, masks = f.INF, tuple(tuple(row) for row in attempts), [], []
        operations = ops or [dict(kind='cast', now_bits=level.stats.now_bits, dt_bits=0)]
        def dispatch(value, declaration, record, **callbacks):
            nonlocal level, live_records, unknown, ledgers
            if declaration.pointer != POINTER:
                raise PendingBattleShout135('Inactive basic unexpectedly became due')
            result = cast_battle_shout135(value, level, BattleShoutDefinition135(), record,
                live_records=live_records, unspecified_live_words=unknown, busy488=busy,
                attempted_spell_sets=ledgers, explicit_other_sources_absent=True)
            level, live_records, unknown, ledgers = result.level, result.live_records, result.unspecified_live_words, result.attempted_spell_sets
            return CastResult(result.cast, result.success, (), 0, 0, ())
        for op in operations:
            now, dt = op['now_bits'], op['dt_bits']
            level = replace(level, stats=replace(level.stats, now_bits=now))
            cast = sync(cast, level, now)
            success = None
            if op['kind'] == 'cast':
                result = cast_battle_shout135(cast, level, BattleShoutDefinition135(), records[battle_index],
                    live_records=live_records, unspecified_live_words=unknown, busy488=busy,
                    attempted_spell_sets=ledgers, explicit_other_sources_absent=True)
                cast, level, live_records, unknown, ledgers, success = (result.cast, result.level,
                    result.live_records, result.unspecified_live_words, result.attempted_spell_sets, result.success)
            else:
                if op['kind'] == 'player':
                    prepared = expire_battle_shout135(level, live_records, unknown, now, dt, 0,
                        explicit_other_sources_absent=True)
                    level, live_records, unknown = prepared.level, prepared.live_records, prepared.unspecified_live_words
                    cast = sync(cast, level, now)
                entries = tuple(FixtureEntry135(definition(POINTER), record) for record in records)
                tick = tick_owned(cast, entries, FixtureEntry135(definition(5476580), basic), dt,
                    sources=OwnedSources135((), (), True), class_byte=level.stats.class_byte,
                    timer1628_bits=timer, cast_dispatch=dispatch)
                cast, records, basic, timer = tick.state, [entry.record for entry in tick.entries], tick.basic.record, tick.prelude.timer1628_bits
            snapshots.append(projection(cast, level, records, basic, live_records, ledgers, timer, success))
            masks.append(unknown)
        cases.append(dict(id=len(cases), group=group, level=raw, cast=s, owned_hex=[record.to_bytes().hex() for record in initial_records],
            battle_index=battle_index, basic_hex=replace(AbilityRecord(5476580), remaining_cooldown_bits=f.INF).to_bytes().hex(),
            live_records=initial_live, initial_unknown=initial_unknown, unknown_poison=0xa55aa55a,
            context908=context, busy488=busy, timer1628_bits=f.INF, last_hit_bits=0, player_z_bits=z,
            sequence=123, action_sequence=1, effect_counter=0, attempts=attempts,
            definition_pointer=POINTER, definition88_hex=RAW88_HEX, ops=operations))
        expectations.append(dict(id=len(expectations), stages=snapshots, unspecified_live_words=masks))
        labels.append(dict(id=len(labels), group=group, operations=len(operations)))

    add('direct-new-learned-effect8')
    add('target30-empty-failure-still-records-attempts', distance=None)
    repeated = ((0, 0, 8, b(.2), 0x12345678, 6673, b(9), 0),
                (123, 0, 8, b(.1), 0x87654321, 6673, b(30), 0),
                (0, 0, 9, b(.1), 0x11111111, 26635, b(40), 0))
    add('repeated-owner0-stable-reset-other-owner-retained', live=repeated,
        ops=[dict(kind='cast', now_bits=b(now), dt_bits=0) for now in (10, 10.25, 11)])
    add('1076-initial-half-second-real-countdown', cls=8,
        ops=[dict(kind='owned', now_bits=b(10 + j * .1), dt_bits=b(.1)) for j in range(1, 9)])
    expiry = f.add(b(10), f.mul(b(8), 0x3fb33333))
    add('2088-exact-expiry-before-at-after', cls=8, ops=[dict(kind='cast', now_bits=b(10), dt_bits=0)] +
        [dict(kind='player', now_bits=word, dt_bits=0) for word in (expiry - 1, expiry, expiry + 1)])
    add('1076-retry-0point2-without-target', cls=8, distance=None,
        ops=[dict(kind='owned', now_bits=b(10 + j * .1), dt_bits=b(.1)) for j in range(1, 12)])
    if full:
        for cls in (1, 2, 3, 4, 5, 7, 8, 9, 11):
            for race in range(1, 9):
                add('all-class-race-23derived-rebuild', cls=cls, race=race)
        for duration in (-1, 0, .001, .5, 2):
            for magnitude in (-.2, 0, .5, 1, 2):
                add('owned-duration-magnitude', changes=dict(duration_bits=b(duration),
                    additional_duration_bits=b(.7), field76_bits=b(magnitude)))
        for distance in (29.999, 30, 30.001, 50):
            add('actual-target30-distance-boundary', distance=distance)
        for busy in (0, 1):
            for context in (0, 1):
                for attempts in (((), (), ()), ((1, 6673), (2,), (3, 6673))):
                    add('three-independent-attempt-ledgers', busy=busy, context=context, attempts=attempts)
        for expiry_value in (9, 10, 11):
            for low, high in ((0, 0), (123, 0), (0, 123)):
                row = (low, high, 8, b(.3), 0x56781234, 6673, b(expiry_value), 0)
                add('same-spell-expiry-and-full-ownerGUID', live=(row, repeated[2], row))
        for cooldown in (0, .5, 10, float('inf')):
            add('direct922-retains-all80-owned-bytes', changes=dict(remaining_cooldown_bits=b(cooldown)))
        for cooldown in (.01, .5, 2):
            add('1076-effective-CD-and-repeat-reset', cls=8, changes=dict(cooldown_bits=b(cooldown), additional_cooldown_bits=b(.7), remaining_cooldown_bits=0),
                ops=[dict(kind='owned', now_bits=b(now), dt_bits=b(dt)) for now, dt in ((10.1, .1), (10.4, .3), (30, 20))])
        add('2088-expire-then-later1076-recast', cls=8, changes=dict(remaining_cooldown_bits=0),
            ops=[dict(kind='owned', now_bits=b(10), dt_bits=0), dict(kind='player', now_bits=expiry, dt_bits=b(12)), dict(kind='player', now_bits=b(34), dt_bits=b(12))])
        actual = actual_selection_input()
        now = actual[0].collection.level.stats.now_bits
        add('actual379-fourth-card-direct922', actual=actual,
            ops=[dict(kind='cast', now_bits=f.add(now, b(.1)), dt_bits=0)])
        add('actual-selected80-isolated1076-real-countdown', actual=actual, isolated_owned=True,
            ops=[dict(kind='owned', now_bits=f.add(now, b(j * .1)), dt_bits=b(.1)) for j in range(1, 9)])
        provenance = dict(frames=379, selections=actual[4], battle_owned80_hex=actual[0].collection.level.choice_inputs.owned[actual[3]].record.to_bytes().hex(),
            pre_component_boundary='pending_selected_ability', input_kind='deterministic independent opening/gameplay replay, never original observation',
            isolation='Direct922 retains full learned vector;1076 case retains selected Battle Shout80 and suppresses other casts with absent learned slots/infinite genuine basic/prelude timers.')
    else:
        provenance = None
    return json.loads(json.dumps(cases)), json.loads(json.dumps(expectations)), labels, provenance


def private_build():
    out, manifest = build(['cast', 'owned_tick', 'player_tick'])
    path = out / manifest['module_file']
    raw = path.read_bytes()
    section = next(row for row in section_list(raw) if row[0] == 7)
    exports, start = export_entries(raw, section)
    name = b'research135_battle_stack0'
    added = unsigned(len(name)) + name + b'\x03' + unsigned(0)
    payload = unsigned(len(exports) + 1) + raw[start:section[3]] + added
    changed = raw[:section[1]] + b'\x07' + unsigned(len(payload)) + payload + raw[section[3]:]
    old_sections, new_sections = section_list(raw), section_list(changed)
    assert [row[0] for row in old_sections] == [row[0] for row in new_sections]
    for before, after in zip(old_sections, new_sections):
        if before[0] != 7:
            assert raw[before[1]:before[3]] == changed[after[1]:after[3]]
    path.write_bytes(changed)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    assert sha(validator) == VALIDATOR_SHA
    child = subprocess.Popen([str(validator), '--enable-all', str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    save(out / 'battle-validator-owned.json', dict(pid=child.pid, pgid=child.pid, deadline_seconds=45))
    try:
        stdout, stderr = child.communicate(timeout=45)
    finally:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait()
    (out / 'battle-validation.stdout').write_bytes(stdout)
    (out / 'battle-validation.stderr').write_bytes(stderr)
    assert child.returncode == 0
    manifest.update(module_sha256=sha(path), private_stack_export=dict(name=name.decode(), index=0, read_only=True),
        original_function_bodies_unchanged=True, private_validator_pid=child.pid)
    save(out / 'manifest.json', manifest)
    static = trace_battle_shout135(out)
    assert static['definition88_hex'] == RAW88_HEX
    return out, manifest


def compare(expected, actual):
    errors, counts = [], Counter()
    def visit(want, got, path):
        if type(want) is not type(got):
            errors.append(dict(path=path, expected=want, actual=got))
        elif isinstance(want, dict):
            if set(want) != set(got):
                errors.append(dict(path=path, expected_keys=list(want), actual_keys=list(got)))
            else:
                for key in want:
                    visit(want[key], got[key], path + '.' + key)
        elif isinstance(want, list):
            if len(want) != len(got):
                errors.append(dict(path=path, expected_length=len(want), actual_length=len(got)))
            for j, (left, right) in enumerate(zip(want, got)):
                visit(left, right, path + f'[{j}]')
        else:
            counts['known_leaves'] += 1
            if want != got:
                errors.append(dict(path=path, expected=want, actual=got))
    for wanted, value in zip(expected, actual):
        assert wanted['id'] == value['id']
        for j, (left, right) in enumerate(zip(wanted['stages'], value['stages'])):
            left, right = dict(left), dict(right)
            unknown = {tuple(row) for row in wanted['unspecified_live_words'][j]}
            if len(left['live_records']) != len(right['live_records']):
                errors.append(dict(path=f'case{wanted["id"]}.stage{j}.live_count', expected=len(left['live_records']), actual=len(right['live_records'])))
            else:
                for k, (a, b) in enumerate(zip(left['live_records'], right['live_records'])):
                    aw, bw = struct.unpack('<8I', bytes.fromhex(a)), struct.unpack('<8I', bytes.fromhex(b))
                    for n, (x, y) in enumerate(zip(aw, bw)):
                        if (k, n * 4) in unknown:
                            counts['explicit_unknown_words'] += 1
                            if y:
                                counts['nonzero_unknown_words_observed'] += 1
                        else:
                            visit(x, y, f'case{wanted["id"]}.stage{j}.live{k}+{n*4}')
            left.pop('live_records');right.pop('live_records')
            visit(left, right, f'case{wanted["id"]}.stage{j}')
        assert len(wanted['stages']) == len(value['stages'])
    return errors, counts


def refusal_checks(cases):
    sample = cases[0]
    level = from_dict(sample['level'])
    cast = state_from_input(sample['cast'])
    owned = AbilityRecord.from_bytes(bytes.fromhex(sample['owned_hex'][0]))
    def invoke(value=level, state=cast, explicit=True):
        return cast_battle_shout135(state, value, BattleShoutDefinition135(), owned,
            live_records=(), attempted_spell_sets=((), (), ()), explicit_other_sources_absent=explicit)
    tests = [('missing external-source declaration', lambda: invoke(explicit=False)),
             ('inherited proc context', lambda: invoke(state=replace(cast, context908=2))),
             ('icebarrier source continuation', lambda: invoke(value=replace(level,
                 stats=replace(level.stats, conditional1344_id=11426))))]
    for key in ('passives', 'adjustments', 'item_modifiers', 'owned_skills', 'timed_records', 'definitions'):
        # A nonempty unresolved producer is opaque input, never fabricated
        # into a known modifier merely to let the numeric cast continue.
        value = replace(level, sources=replace(level.sources, **{key: (object(),)}))
        tests.append(('nonempty ' + key, lambda value=value: invoke(value=value)))
    answers = []
    for name, call in tests:
        try:
            call()
        except PendingBattleShout135 as error:
            answers.append(dict(name=name, boundary=type(error).__name__, reason=str(error)))
        else:
            raise AssertionError('Unrestored Battle Shout source accepted: ' + name)
    return answers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot')
    args = parser.parse_args()
    scripts = ('check_battle_shout135.py', 'run_battle_shout135_oracle.mjs', 'trace_battle_shout135.py',
        'production_closure135.py', 'build_full135_oracle.py', 'build_upgrade134_oracle.py',
        'check_level_cycle135.py', 'check_cast135_full_spec.py', 'ai_world135_inputs.py')
    files = tuple('scripts/' + name for name in scripts) + production_sources135(ROOT,
        'core_spec.battle_shout135', 'core_spec.headless135')
    before = {name: sha(ROOT / name) for name in files}
    cases, expected, labels, provenance = corpus(args.phase == 'full')
    refusals = refusal_checks(cases)
    assert before == {name: sha(ROOT / name) for name in files}, 'Source changed during expected generation'
    out, manifest = private_build()
    for name, digest in before.items():
        target = out / 'source-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
        assert sha(target) == digest
    for name, value in (('battle-input.json', cases), ('battle-expected.json', expected), ('battle-labels.json', labels), ('battle-selection-input.json', provenance), ('battle-refusals.json', refusals)):
        save(out / name, value)
    assert all((out / name).stat().st_size <= 4194304 for name in ('battle-input.json', 'battle-expected.json'))
    frozen = {name: sha(out / name) for name in ('battle-input.json', 'battle-expected.json', 'battle-labels.json', 'battle-selection-input.json', 'battle-refusals.json', 'manifest.json', manifest['module_file'], 'battle-shout135-static.json')}
    world_inputs = {str(ASSET_WORLD / name): digest for name, digest in HASHES.items()} if provenance else {}
    command = [str(NODE), '--expose-gc', '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/run_battle_shout135_oracle.mjs'), str(out), str(out / 'battle-input.json')]
    save(out / 'battle-prepared.json', dict(source_sha256=before, artifacts=frozen, world_inputs=world_inputs,
        cases=len(cases), command=command, expected_before_original=True, deadline_seconds=60))
    assert sha(SOURCE) == SOURCE_SHA and sha(NODE) == NODE_SHA
    assert before == {name: sha(ROOT / name) for name in files}
    began, launcher_error = time.monotonic(), None
    def interrupted(sig, frame):
        raise KeyboardInterrupt('Owned Battle Shout launcher signal ' + str(sig))
    previous = signal.signal(signal.SIGTERM, interrupted)
    with (out / 'battle-results.jsonl').open('wb') as stdout, (out / 'battle-stderr.log').open('wb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True,
            env=dict(os.environ, TMPDIR=str(out), PYTHONDONTWRITEBYTECODE='1'))
        with (out / 'battle-owned-process.json').open('w') as ledger:
            ledger.write(json.dumps(dict(pid=child.pid, pgid=child.pid, command=command, deadline_seconds=60)) + '\n')
            ledger.flush();os.fsync(ledger.fileno())
        try:
            child.wait(timeout=60)
        except (subprocess.TimeoutExpired, KeyboardInterrupt, OSError) as error:
            launcher_error = str(error)
        finally:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM, previous)
    def missing(group=False):
        try:
            (os.killpg if group else os.kill)(child.pid, 0)
        except ProcessLookupError:
            return True
        return False
    terminal = dict(pid=child.pid, pgid=child.pid, exit_code=child.returncode, pid_missing=missing(),
        pgid_missing=missing(True), seconds=time.monotonic() - began, launcher_error=launcher_error)
    save(out / 'battle-process-terminal.json', terminal)
    errors, counts, runtime = [], Counter(), None
    if child.returncode == 0:
        actual = [json.loads(line) for line in (out / 'battle-results.jsonl').read_text().splitlines()]
        assert len(actual) == len(expected)
        errors, counts = compare(expected, actual)
        runtime = json.loads((out / 'battle-shout135-runtime.json').read_text())
        assert runtime['fresh_instances'] == len(cases) and runtime['actual_host_calls'] == 0 and runtime['stack_all_restored']
    after = {name: sha(ROOT / name) for name in files}
    source_unchanged = before == after
    artifacts_unchanged = all(sha(out / name) == digest for name, digest in frozen.items())
    world_unchanged = all(sha(Path(name)) == digest for name, digest in world_inputs.items())
    save(out / 'battle-differences.json', errors)
    report = dict(version='0.135.1', actual_build='90898d5e3', original_sha256=SOURCE_SHA,
        cases=len(cases), differences=len(errors), comparison=dict(counts), groups=dict(Counter(row['group'] for row in labels)),
        pure_model_refusals=len(refusals),
        expected_before_original=True, source_files=len(files), source_sha256_before=before, source_sha256_after=after,
        source_unchanged=source_unchanged, frozen_artifacts=frozen, artifacts_unchanged=artifacts_unchanged,
        world_inputs=world_inputs, world_unchanged=world_unchanged, process=terminal, runtime=runtime,
        full880_frames=0, component_scope='Battle Shout effect8 numeric/self-buff/learned cooldown/expiry only',
        pending=['1202 physical aura/display keys and encoded packet bytes', 'Nonempty external stat/item/talent/proc sources',
            'Actual379 direct cast input is independent replay, not a new379-frame original acceptance; isolated1076 suppresses other learned/basic/prelude work'],
        artifacts={name: sha(out / name) for name in ('battle-results.jsonl', 'battle-stderr.log', 'battle-differences.json', 'battle-prepared.json')})
    save(out / 'battle-shout135-comparison.json', report)
    print(json.dumps(dict(directory=str(out), cases=len(cases), differences=len(errors), first_errors=errors[:6],
        source_unchanged=source_unchanged, process=terminal, receipt_sha256=sha(out / 'battle-shout135-comparison.json'))))
    if errors or child.returncode or launcher_error or not terminal['pid_missing'] or not terminal['pgid_missing'] or not source_unchanged or not artifacts_unchanged or not world_unchanged:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
