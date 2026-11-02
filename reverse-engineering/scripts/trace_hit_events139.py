#!/usr/bin/env python3
"""Bounded current139 empty hit-event owner/route recovery; zero originals."""
from datetime import datetime, timezone
from pathlib import Path
import ast
import re
import sqlite3
import struct
import sys

from incoming139_tools import ROOT, PROFILE, SOURCE_SHA, original, function_proof, static_reader, save, sha
from production_closure135 import production_sources135


def main():
    files = production_sources135(ROOT, 'core_spec.hit_events139')
    sources = {p: sha(ROOT / p) for p in (*files, 'scripts/trace_hit_events139.py',
              'scripts/incoming139_tools.py', 'scripts/production_closure135.py')}
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('hit-events139-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    raw, identity, ranges = original()
    ids = (994, 913, 1600, 25911, 9819, 20442, 2004, 1542)
    functions, texts = function_proof(raw, identity, ranges, ids, out)
    assert functions[994]['signature'] == ('7f7f7f', '')
    assert functions[913]['signature'] == ('7f7e7d7f7f7f7f', '')
    assert functions[1600]['signature'] == ('7f7f7f', '')
    read = static_reader(raw, identity)
    data_path = ROOT / 'reconstruction/core_spec/hit_events139_data.py'
    data = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(data_path.read_text()).body
            if isinstance(n, ast.Assign)}
    declarations = []
    for pointer, (name, value) in data['DECLARATIONS139'].items():
        record = read(pointer, 88)
        p, size = struct.unpack_from('<II', record, 12)
        assert read(p, size).decode() == name and record.hex() == value
        assert record[84] != 11
        declarations.append(dict(pointer=pointer, name=name, raw88_hex=value,
                                 execution84=record[84], effect_tag0=struct.unpack_from('<I', record)[0]))
    assert data['SOURCE_WASM_SHA256'] == SOURCE_SHA
    assert [r['pointer'] for r in declarations[1:]] == list(data['RACIAL_POINTERS139'])
    assert declarations[0]['execution84'] == 5
    assert not re.search(r'(?:i32|i64|f32|f64)\.store(?:8|16)? offset=(?:2048|2052|2056|770)(?:\s|$)', texts[1542])
    windows = {}

    def window(name, index, first, last, required):
        rows = texts[index].splitlines()
        value = '\n'.join(rows[first - 1:last])
        for match in required:
            assert match in value, (name, match)
        windows[name] = dict(function=index, first_line_1based=first, last_line_1based=last, text=value)

    window('994_count0_outer_return', 994, 1, 29,
           ['i32.load offset=2056', 'i32.const 36', 'i32.eqz\n          br_if 2 (;@1;)'])
    window('994_tail_common_restore_optional_stats', 994, 5755, 5790,
           ['call 73034', 'i32.store offset=476', 'i32.store offset=472', 'local.get 41', 'call 1542'])
    window('913_execution11_only_owned_arm', 913, 8775, 8813,
           ['i32.load offset=1664', 'i32.load offset=1660', 'i32.load8_u offset=84', 'i32.const 11',
            'i32.ne\n              br_if 0 (;@5;)'])
    window('913_tail_skip_before_events', 913, 12790, 12831,
           ['i32.load8_u offset=770', 'i32.const 3', 'i32.load offset=2056',
            'br_if 0 (;@10;)', 'i32.const -3', 'call 73034', 'br 5 (;@4;)'])
    window('913_hit994_event35', 913, 12948, 12997,
           ['i32.store8 offset=1298', 'i32.store offset=1272', 'i64.store offset=1264',
            'i32.const 0\n            call 994'])
    window('913_dead994_event35_context44', 913, 12998, 13071,
           ['i32.const 2\n            i32.store8 offset=557', 'i64.store offset=528',
            'i32.const 1088', 'call 994', 'i32.const 44', 'call 73034'])
    window('1600_calls_profile_source_producer', 1600, 200, 208,
           ['i32.const 24', 'local.get 1\n                call 25911'])
    window('1600_event36_header_copy', 1600, 1247, 1254,
           ['i64.load offset=56', 'i64.store offset=2144', 'i64.load offset=48', 'i64.store offset=2136'])
    window('1600_mode770_zero', 1600, 1363, 1371,
           ['i64.const 0\n                  i64.store offset=851 align=1'])
    window('1600_game_output', 1600, 2693, 2708,
           ['i32.const 88', 'call 1542', 'local.get 0', 'i32.const 2592', 'memory.copy'])
    window('25911_talent_and_equipment', 25911, 8, 60,
           ['i32.const 152', 'call 9819', 'i32.const 260', 'i32.const 352', 'call 20442',
            'i32.const 2\n          i32.ne'])
    window('9819_empty_header_initializers', 9819, 8, 37,
           ['i64.const 0\n    i64.store offset=44', 'i64.const 17179869184\n    i64.store offset=36'])
    window('9819_talent_count0', 9819, 47, 60, ['local.get 1\n    i32.load offset=8'])
    window('20442_zeroID_absent_loop', 20442, 25, 82,
           ['local.get 1', 'i32.load', 'call 2004', 'i32.const -1', 'br_if 0 (;@4;)'])
    window('2004_ID0_absent_guard', 2004, 449, 460,
           ['i32.const 1\n                                i32.sub', 'i32.const 99999', 'i32.lt_u',
            'i32.const 100000', 'br_if 3 (;@11;)'])
    window('2004_ID0_absent_exit', 2004, 1345, 1349,
           ['local.get 0', 'i32.const -1', 'i32.store', 'br 8 (;@1;)'])
    # For P160=0 the first9819 walk is skipped; its temporary40 vector count
    # remains0, so the second walk and optional tag42 mutation are skipped.
    # 20442 makes19 absent item lookups and returns discriminator2.
    with sqlite3.connect((PROFILE / 'index.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
        calls = {str(i): [dict(callee=c, wat_line=line) for c, line in
                         db.execute('select callee,wat_line from calls where caller=?order by wat_offset', (i,))]
                 for i in ids}
    sys.path.insert(0, str(ROOT / 'reconstruction'))
    from core_spec.hit_events139 import (EventDefinitions139, PendingHitEvents139,
        produce_empty_profile_event_definitions139, produce_default_cleave_hit_sources139,
        prove_owned_execution11_absent139, dispatch_hit_event139, plan_damage_tail_events139)
    checks = []

    def check(name, fn, error=False):
        try:
            value = fn()
        except PendingHitEvents139:
            assert error, name
            checks.append(dict(name=name, outcome='explicit_pending'))
        else:
            assert not error, name
            checks.append(dict(name=name, outcome='model_selfcheck', result=repr(value)))

    profile = [None] * 376
    for offset in [160, *range(260, 336, 4)]:
        profile[offset:offset + 4] = [0] * 4
    profile[344] = 1
    empty = produce_empty_profile_event_definitions139(tuple(profile))
    check('unconsumed_profile_bytes_unknown', lambda: empty)
    for race in range(1, 9):
        profile[345] = race
        owned = tuple(struct.pack('<I', 5882740)) + (None,) * 76
        racial = tuple(struct.pack('<I', data['RACIAL_POINTERS139'][race - 1])) + (None,) * 76
        check('default_cleave_racial_' + str(race),
              lambda p=tuple(profile), o=owned, r=racial: produce_default_cleave_hit_sources139(p, (o,), r))
    for count in (0, MASK := (1 << 32) - 1, 1, 4):
        check('tail_count_' + str(count), lambda c=count: plan_damage_tail_events139(0, empty, c))
    check('mode3_unknown_source', lambda: plan_damage_tail_events139(3, None, 1))
    check('count0_unknown_mode', lambda: plan_damage_tail_events139(None, empty, 1))
    check('empty994_no_event_or_pointer_read', lambda: dispatch_hit_event139(EventDefinitions139(None, None, 0, ())))
    check('nonempty994_rejected', lambda: dispatch_hit_event139(EventDefinitions139(None, None, 1, None)), True)
    check('unknown994_rejected', lambda: dispatch_hit_event139(EventDefinitions139(None, None, None, None)), True)
    check('unknown_tail_rejected', lambda: plan_damage_tail_events139(None, None, 0), True)
    changed = profile.copy()
    changed[260] = 1
    check('equipment_source_rejected', lambda: produce_empty_profile_event_definitions139(tuple(changed)), True)
    changed = profile.copy()
    changed[160] = 1
    check('talent_source_rejected', lambda: produce_empty_profile_event_definitions139(tuple(changed)), True)
    unknown = profile.copy()
    unknown[160] = None
    check('unknown_consumed_source_rejected', lambda: produce_empty_profile_event_definitions139(tuple(unknown)), True)
    definition = bytearray(88)
    definition[84] = 11
    check('execution11_rejected', lambda: prove_owned_execution11_absent139(
          (struct.pack('<I', 1) + bytes(76),), ((1, bytes(definition)),)), True)
    current = {p: sha(ROOT / p) for p in sources}
    assert sources == current
    result = dict(version='0.139.0', build='f79c5e2b4', source_WASM_sha256=SOURCE_SHA,
                  production_sources=files, source_before=sources, source_after=current,
                  functions=functions, direct_calls=calls, windows=windows, static_reads=read.proof,
                  default_ability_declarations=declarations,
                  owner_copy_chain=dict(profile_talent_count160=0, equipment_ID_offsets=list(range(260, 336, 4)),
                      origin='9819 third Vec36 cap0/ptr4/count0;25911 out24/28/32 ->1600 SP48/52/56 ->SP2136/2140/2144 ->Game2048/2052/2056',
                      mode770='1600 SP851..858 zero64 coversGame770 atSP858; copied fromSP88'),
                  original_executions=0, original_behavior_cases=0, static_target_execution=False,
                  model_selfchecks=checks, model_selfchecks_original_coverage=False,
                  unknowns=['Nonempty994 selector dispatch, allocations, callbacks, schedules and stats-recalculation effects remain pending.',
                            'Owned execution11 is rejected, not silently skipped.',
                            'No general post-selection/equipment owner preservation or naturalApp/profile producer is proved.',
                            '913 tail plan excludes earlier death/XP/spell-set/proc phases and later20752 cleanup.',
                            'No new runtime, native execution, fullGame or fullopening acceptance.'])
    save(out / 'trace.json', result)
    print(str(out))
    print(sha(out / 'trace.json'))


if __name__ == '__main__':
    main()
