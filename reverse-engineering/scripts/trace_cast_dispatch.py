#!/usr/bin/env python3
"""Retain execution-kind branches and the original scheduled fireball hit path.

Read-only original WASM/WAT analysis. No target execution, server, or save access.
Branch inventories are structural and lexical; they are not a whole-program CFG.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from trace_abilities import reconstruct_memory, extract_catalogues
from trace_ecs_forward import structural_targets
from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
FUNCTIONS = (917, 934, 8239, 1819, 1940, 8610, 1874, 933)
CASE_SPANS = {0: [(526, 585), (1003, 1885)],
              1: [(526, 585), (1003, 1885)], 2: [(586, 1002)],
              3: [(10243, 10709)], 4: [(9497, 10242)],
              5: [(8977, 9496)], 6: [(6536, 8976)],
              7: [(8977, 9496)], 8: [(5723, 6535)],
              9: [(4096, 5722)], 10: [(1886, 4095)], 11: []}
CASE_ENTRIES = (526, 526, 586, 10243, 9497, 8977, 6536, 8977,
                5723, 4096, 1886, 10710)
EFFECT_TABLES = (811, 1722, 4241, 4379, 6386, 8809, 9347, 10080, 10578)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def all_tables(index, lines):
    result = []
    for number, line in enumerate(lines, 1):
        if not line.startswith('br_table '):
            continue
        depths = re.findall(r'(\d+) \(;@\d+;\)', line)
        arms = []
        for slot in range(len(depths)):
            target = structural_targets(lines, {number: slot})[number]
            target['is_default_slot'] = slot == len(depths) - 1
            target['execution_entry_function_line'] = target['target']['end_function_line'] + 1
            arms.append(target)
        result.append({'function_index': index, 'branch_function_line': number,
                       'selector_context': lines[max(0, number - 9):number - 1],
                       'arms': arms})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original) != ORIGINAL_SHA:
        raise SystemExit('Original core identity differs')
    binary = original.read_bytes()
    ranges = body_ranges(binary)
    memory, segments = reconstruct_memory(binary)
    catalogues = extract_catalogues(memory, segments)
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('cast-dispatch-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    normalized, functions = {}, []
    with sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as con:
        con.execute('PRAGMA query_only=ON')
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT identity differs')
        with wat.open('rb') as stream:
            for index in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (index,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[index]:
                    raise ValueError('Original/index function bounds disagree')
                stream.seek(row[0]); data = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', data, re.M) != [str(index).encode()]:
                    raise ValueError('Expected one complete original function')
                (run / f'function-{index}.wat').write_bytes(data)
                normalized[index] = [x.strip() for x in data.decode().splitlines()]
                functions.append({'function_index': index, 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': row[5], 'body_sha256': digest(binary[row[3]:row[4]]),
                                  'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(data), 'wat_sha256': digest(data)})
        callers = {str(index): [{'caller': caller, 'call_count': count} for caller, count in
                               con.execute('SELECT caller,count(*) FROM calls WHERE callee=? '
                                           'GROUP BY caller ORDER BY caller', (index,))]
                   for index in (8239, 1819, 1940)}
    guards = []

    def require(index, sequence, label):
        lines = normalized[index]
        hits = [n + 1 for n in range(len(lines) - len(sequence) + 1)
                if lines[n:n + len(sequence)] == sequence]
        if not hits:
            raise ValueError('Reviewed instructions differ: ' + label)
        guards.append({'function_index': index, 'label': label,
                       'function_lines': hits, 'instructions': sequence})

    require(934, ['local.get 8', 'i32.load8_u offset=84', 'local.tee 7',
                  'i32.const 2', 'i32.sub'], 'execution kind comes from definition84')
    require(934, ['local.get 7', 'i32.const 2', 'i32.sub', normalized[934][523]],
            'main dispatch uses kind minus2 with unsigned br_table default')
    require(934, ['local.get 3', 'i32.const 216', 'i32.add', 'local.get 0',
                  'local.get 3', 'i32.const 72', 'i32.add', 'local.get 29', 'call 8610'],
            'kind0/1 initial target list')
    require(934, ['local.get 3', 'i32.const 0', 'i32.store offset=72', 'local.get 0',
                  'local.get 8', 'i32.load offset=44', 'local.get 1', 'i32.load8_u',
                  'local.get 3', 'i32.const 232', 'i32.add', 'local.get 41',
                  'local.get 33', 'local.get 32', 'local.get 3', 'i32.const 72',
                  'i32.add', 'call 8239'], 'shared kind0/1 schedules each chosen target')
    require(8239, ['local.get 1', 'i32.const 116', 'i32.sub', normalized[8239][352]],
            'spell133 speed branch selector')
    require(8239, ['f32.const 0x1.8p+4 (;=24;)', 'local.set 15'], 'default speed24')
    require(8239, ['f32.add', 'f32.sqrt', 'local.get 15', 'f32.div', 'local.set 18'],
            'distance divided by selected speed gives travel time')
    require(8239, ['local.get 18', 'local.get 6', 'local.get 0', 'f32.load offset=2064',
                   'f32.add', 'f32.add', 'local.set 6'], 'due equals travel plus per-target delay plus now')
    require(8239, ['local.get 0', 'i32.load offset=1656', 'local.get 10', 'i32.const 112',
                   'i32.mul', 'i32.add', 'local.tee 8'], 'scheduled hit vector112 address')
    require(8239, ['local.get 8', 'i32.const 2', 'i32.store8 offset=61'], 'scheduled hit context byte61=2')
    require(8239, ['local.get 8', 'local.get 6', 'f32.store offset=92'], 'due time at record92')
    require(1819, ['local.get 0', 'i32.load offset=1660', 'local.set 7',
                   'local.get 0', 'i32.load offset=1656', 'local.set 11'], 'consumer takes same scheduled vector')
    require(1819, ['local.get 35', 'local.get 36', 'f32.ge', 'i32.eqz', 'if  ;; label = @4'],
            'not now greater-equal due remains pending including unordered NaN')
    require(1819, ['local.get 0', 'local.get 42', 'local.get 35', 'local.get 8',
                   'local.get 1', 'i32.load8_u offset=210', 'local.get 27', 'i32.const 1',
                   'i32.and', 'i32.const 0', 'call 933'], 'due positive damage hits original933')
    require(1819, ['local.get 0', 'local.get 42', 'local.get 17', 'local.get 35',
                   'local.get 8', 'call 1940'], 'after damage original effect payload consumer1940')
    require(1940, ['local.get 2', 'i32.load', 'i32.const 1', 'i32.sub', normalized[1940][29]],
            'effect payload tag minus1 dispatch')
    require(917, ['local.get 3', 'i32.load offset=48', 'local.tee 7',
                  'i32.load offset=16', 'i32.const 8', 'i32.sub', normalized[917][321]],
            '917 first jump is identifier length minus8 not execution kind')
    require(934, ['local.get 0', 'i32.load offset=1608', 'local.get 2',
                  'i32.const 88', 'i32.mul', 'i32.add', 'local.tee 1'],
            'kind3 original88-byte object creation address')
    require(934, ['local.get 0', 'i32.load offset=1656', 'local.get 12',
                  'i32.const 112', 'i32.mul', 'i32.add', 'local.tee 1'],
            'kind4 scheduled112-byte creation address')
    require(934, ['local.get 0', 'i32.load offset=1668', 'local.get 4',
                  'i32.const 112', 'i32.mul', 'i32.add', 'local.tee 2'],
            'kind10 separate112-byte object creation address')
    require(1874, ['local.get 0', 'i32.load offset=1668', 'local.tee 3',
                   'local.get 11', 'i32.const 112', 'i32.mul', 'local.tee 5', 'i32.add'],
            '1874 reads kind10 vector at same112 stride')
    require(1819, ['local.get 35', 'f32.const 0x0p+0 (;=0;)', 'f32.gt',
                   'if  ;; label = @3', 'local.get 0', 'local.get 42', 'local.get 35',
                   'local.get 8', 'local.get 1', 'i32.load8_u offset=210', 'local.get 27',
                   'i32.const 1', 'i32.and', 'i32.const 0', 'call 933'],
            'scheduled933 call is guarded by positive damage')
    tables = [table for index in FUNCTIONS for table in all_tables(index, normalized[index])]
    dispatch = []
    for kind in range(12):
        selector = (kind - 2) & 0xffffffff
        branch = structural_targets(normalized[934], {524: selector})[524]
        if branch['target']['end_function_line'] + 1 != CASE_ENTRIES[kind]:
            raise ValueError('Reviewed execution-kind entry differs')
        spans = CASE_SPANS[kind]
        calls = [{'function_line': n, 'callee': int(normalized[934][n - 1].split()[1])}
                 for begin, end in spans for n in range(begin, end + 1)
                 if re.fullmatch(r'call \d+', normalized[934][n - 1])]
        dispatch.append({'execution_kind_u8': kind,
                         'ability_ids': [a['identifier'] for a in catalogues['abilities']
                                         if a['execution_kind_u8'] == kind],
                         'selector_u32': selector, 'structural_target': branch,
                         'entry_function_line': CASE_ENTRIES[kind],
                         'reviewed_lexical_regions': [{'first_function_line': a, 'last_function_line': b}
                                                      for a, b in spans],
                         'lexical_direct_calls': calls,
                         'lexical_direct_damage933_lines': [c['function_line'] for c in calls if c['callee'] == 933],
                         'lexical_effect1940_lines': [c['function_line'] for c in calls if c['callee'] == 1940]})
    effects = []
    for tag in range(14):
        branch = structural_targets(normalized[1940], {30: (tag - 1) & 0xffffffff})[30]
        effects.append({'effect_tag_u32': tag,
                        'ability_ids': [a['identifier'] for a in catalogues['abilities'] if a['effect_tag_u32'] == tag],
                        'consumer1940_structural_target': branch,
                        'consumer1940_entry_function_line': branch['target']['end_function_line'] + 1,
                        'consumer1940_returns_without_case_body': branch['target']['end_function_line'] == 1774,
                        'definition_tag_transforms_in934': [
                            {'branch_function_line': n,
                             'structural_target': structural_targets(normalized[934],
                                 {n: ((tag - (6 if n == 4241 else 1)) & 0xffffffff)})[n]}
                            for n in EFFECT_TABLES]})
    # spell133 takes br_table slot17 -> block@3 end490: keep the initialized24.
    speed_branch = structural_targets(normalized[8239], {353: 133 - 116})[353]
    if speed_branch['target']['end_function_line'] != 490:
        raise ValueError('Reviewed fireball speed branch differs')
    associations = [{'identifier': a['identifier'], 'definition_index': a['index'],
                     'execution_kind_u8': a['execution_kind_u8'], 'effect_tag_u32': a['effect_tag_u32'],
                     'class_ids': [c['identifier'] for c in catalogues['classes'] if a['identifier'] in c['ability_ids']],
                     'spell_id_u32': a['spell_id_u32'], 'definition_record_sha256': a['record_sha256']}
                    for a in catalogues['abilities']]
    report = {'schema': 'cast-dispatch-v1', 'date': '2026-11-01', 'version': '0.126.0',
              'build': '3e72472a', 'original_wasm_sha256': ORIGINAL_SHA,
              'complete_wat_sha256': WAT_SHA,
              'method': 'Complete original functions; structural jump resolution; manual static data flow; no target execution.',
              'local_extraction_run': str(run.relative_to(ROOT)),
              'complete_functions': functions, 'instruction_guards': guards,
              'execution_kind_dispatch': dispatch, 'ability_associations': associations,
              'effect_tag_dispatch': effects, 'all_retained_br_tables': tables,
              'indexed_direct_callers': callers,
              'fireball_scheduled_flight_chain': {
                  'definition': next(a for a in associations if a['identifier'] == 'fireball'),
                  'path': [
                      {'function': 917, 'line': 466, 'fact': 'automatic countdown expiry calls934 with live effective80-byte ability'},
                      {'function': 934, 'line': 524, 'fact': 'kind0 -> u32(-2) -> default at526'},
                      {'function': 934, 'line': 568, 'fact': '8610 gets target GUID list inside definition range56'},
                      {'function': 934, 'line': 1860, 'fact': 'each selected target enters8239 with spell133, school2 and computed damage'},
                      {'function': 8239, 'line': 353, 'fact': '133-116=17 -> block end490 -> no speed overwrite, initialized24 retained'},
                      {'function': 8239, 'line': 506, 'fact': 'travel=sqrt(dx*dx+dy*dy)/speed using target interpolated position and player1320/1324'},
                      {'function': 8239, 'line': 569, 'fact': 'due=travel+(per_target_delay+state.time2064)'},
                      {'function': 8239, 'line': 600, 'fact': 'append112-byte record to state1656/1660'},
                      {'function': 1819, 'line': 101, 'fact': 'split same vector by now>=record.due92; unordered comparison stays pending'},
                      {'function': 1819, 'line': 1018, 'fact': 'positive damage enters933 with record target64,damage100,spell96,school106,crit104&1'},
                      {'function': 1819, 'line': 1127, 'fact': 'effect payload80 is then passed to1940 where tag0 takes return case'}],
                  'speed_branch': speed_branch, 'speed_f32': 24.0,
                  'record_layout': {'stride': 112, 'state_capacity_offset': 1652,
                                    'state_pointer_offset': 1656, 'state_count_offset': 1660,
                                    'record64': 'target GUID i64', 'record72': 'source GUID i64',
                                    'record80_to88': 'effect payload tag and two parameter words',
                                    'record92': 'due time f32', 'record96': 'spellID u32',
                                    'record100': 'already selected critical/noncritical damage f32',
                                    'record104': 'critical byte', 'record105': 'captured state820 byte',
                                    'record106': 'school byte', 'record61': 'context byte2'},
                  'boundary': 'This proves scheduled travel and hit consumption. A rendered moving projectile or per-tick physical collision object is not established.'},
              'creation_sites': [
                  {'execution_kinds': [0, 1], 'function': 8239, 'vector_pointer': 1656,
                   'vector_count': 1660, 'stride': 112, 'consumer': 1819, 'status': 'full reviewed fireball path'},
                  {'execution_kinds': [3], 'function': 934, 'vector_pointer': 1608,
                   'vector_count': 1612, 'stride': 88, 'status': 'original append retained; consumer not restored here'},
                  {'execution_kinds': [4], 'function': 934, 'vector_pointer': 1656,
                   'vector_count': 1660, 'stride': 112, 'consumer': 1819, 'status': 'append retained; full chain-lightning details pending'},
                  {'execution_kinds': [10], 'function': 934, 'vector_pointer': 1668,
                   'vector_count': 1672, 'stride': 112, 'consumer': 1874, 'status': 'append and matching consumer retained; semantics pending'}],
              'validation': {'ability_count': len(associations), 'execution_kind_count': len(dispatch),
                             'effect_tag_count': len(effects), 'complete_function_count': len(functions),
                             'instruction_guard_count': len(guards), 'retained_br_table_count': len(tables),
                             'structural_arms_including_defaults': sum(len(t['arms']) for t in tables),
                             'target_executed': False, 'original_unchanged': sha(original) == ORIGINAL_SHA,
                             'wat_unchanged': sha(wat) == WAT_SHA},
              'limitations': [
                  'Case regions list lexical calls, not all dynamically reachable calls. Shared helpers and nested conditions require separate semantic work.',
                  'Execution kind11 branches to epilogue with initial result0; 934 prologue side effects and passive consumers are not decoded here.',
                  '917 tables are retained structurally. They include identifier-length, object, and NPC domains; they are not all ability execution-kind tables.',
                  '1940 does not implement every declared effect tag. Other934 cases and passive writers handle additional tags; no guessed tag names are assigned. Effect table targets do not establish reachability through earlier gates.',
                  'Only the fireball scheduled damage chain is reviewed end to end. Full semantics of other112/88-byte records, all effects, and visual flight remain pending.']}
    if not all((report['validation']['original_unchanged'], report['validation']['wat_unchanged'])):
        raise ValueError('Inputs changed during extraction')
    encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    (run / 'manifest.json').write_text(encoded)
    destination = ROOT / 'reports/2026-11-01-cast-dispatch.json'
    destination.write_text(encoded)
    print(json.dumps({'report': str(destination), 'run': str(run), **report['validation']}, allow_nan=False))


if __name__ == '__main__':
    main()
