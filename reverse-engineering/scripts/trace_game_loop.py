#!/usr/bin/env python3
"""Retain current-game clock, phase, pause and start/end paths statically.

This is an original-byte/WAT evidence extractor, not target execution or a claim
that the complete game state type/scheduler has been recovered.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from trace_coop import module_data
from trace_ecs_forward import structural_targets
from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
FUNCTIONS = (880, 1084, 1366, 1678, 2098, 4391, 4595, 7654, 39211,
             48790, 58247, 83471, 173617, 25345, 35322, 26076,
             45603, 27317, 1065)
LITERALS = ((1567007, b'paused'), (1570916, b'unpaused'),
            (1566470, b'victory'), (1566464, b'defeat'),
            (1567940, b'start'), (1567964, b'revived'),
            (1569243, b'Endless'), (1569250, b'The onslaught never ends...'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(source) != ORIGINAL_SHA:
        raise SystemExit('Original current core identity differs')
    binary = source.read_bytes(); ranges = body_ranges(binary)
    segments, _, _ = module_data(binary)
    with sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('game-loop-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []; lines = {}
        with wat.open('rb') as text:
            for idx in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[idx]:
                    raise ValueError('Indexed body differs from original code section')
                text.seek(row[0]); data = text.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', data, re.M) != [str(idx).encode()]:
                    raise ValueError('Expected one complete indexed function')
                (run / f'function-{idx}.wat').write_bytes(data)
                lines[idx] = [x.strip() for x in data.decode().splitlines()]
                functions.append({'function_index': idx, 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': row[5], 'body_sha256': hashlib.sha256(binary[row[3]:row[4]]).hexdigest(),
                                  'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(data), 'wat_sha256': hashlib.sha256(data).hexdigest()})
        guards = []
        def check(idx, first, expected, label):
            if lines[idx][first - 1:first - 1 + len(expected)] != expected:
                raise ValueError('Reviewed path differs: ' + label)
            guards.append({'function_index': idx, 'first_function_line': first,
                           'label': label, 'instructions': expected})
        check(880, 8, ['local.get 0', 'i64.load', 'i64.const 1', 'i64.eq', 'if  ;; label = @1',
                       'f64.const 0x1.999999999999ap-4 (;=0.1;)', 'f64.const 0x0p+0 (;=0;)',
                       'local.get 1', 'local.get 0', 'f64.load offset=8', 'f64.sub', 'local.tee 158',
                       'local.get 158', 'f64.const 0x0p+0 (;=0;)', 'f64.lt', 'select', 'local.tee 158',
                       'local.get 158', 'f64.const 0x1.999999999999ap-4 (;=0.1;)', 'f64.gt', 'select',
                       'f32.demote_f64', 'local.set 153', 'end', 'local.get 0', 'local.get 1',
                       'f64.store offset=8', 'local.get 0', 'i64.const 1', 'i64.store'],
              'first-zero tick and ordered lower/upper delta clamp')
        check(880, 31895, ['local.get 6', 'i32.load8_u offset=2294', 'i32.eqz', 'if  ;; label = @15',
                           'local.get 6', 'i32.load8_u offset=2299', 'local.tee 2', 'br_if 2 (;@13;)',
                           'local.get 6', 'i32.load8_u offset=2287', 'i32.const 1', 'i32.and',
                           'br_if 1 (;@14;)', 'br 2 (;@13;)'], 'single/multi state branch and pending start')
        check(880, 44374, ['local.get 6', 'i32.const 0', 'i32.store8 offset=2287',
                           'local.get 6', 'call 1084', 'local.get 6', 'i32.load8_u offset=2299',
                           'local.set 2'], 'consume pending start and initialize run')
        check(880, 44383, ['block  ;; label = @13', 'local.get 2', 'i32.const 255', 'i32.and',
                           'i32.const 1', 'i32.ne', 'br_if 0 (;@13;)', 'local.get 6', 'local.get 153',
                           'local.get 6', 'f32.load offset=2064', 'f32.add', 'local.tee 147',
                           'f32.store offset=2064'], 'single-state clock advances only for phase1')
        check(880, 31945, ['block  ;; label = @15', 'local.get 2', 'i32.const 255', 'i32.and',
                           'i32.const 1', 'i32.ne', 'br_if 0 (;@15;)', 'local.get 6', 'local.get 153',
                           'local.get 6', 'f32.load offset=2064', 'f32.add', 'f32.store offset=2064'],
              'multi-state global-phase clock update')
        check(880, 31920, ['block  ;; label = @15', 'local.get 6', 'i32.load8_u offset=2300',
                           'local.tee 2', 'br_if 0 (;@15;)'], 'multi-state phase source is2300')
        check(1084, 8, ['local.get 0', 'i32.const 1', 'i32.store8 offset=2299'], 'run initialization phase1')
        check(1084, 4809, ['local.get 0', 'i32.load8_u offset=2294', 'i32.eqz', 'br_if 0 (;@3;)',
                           'local.get 0', 'i32.const 1', 'i32.store8 offset=2300'], 'multi-state start global phase1')
        check(1366, 11396, ['local.get 1', 'i32.load8_u offset=4', 'i32.eqz', 'if  ;; label = @23'],
              'pause input boolean selects resume versus pause')
        check(1366, 46, ['i32.const 11', 'local.get 1', 'i32.load', 'local.tee 2',
                         'i32.const 2', 'i32.sub', 'local.get 2', 'i32.const 1',
                         'i32.le_u', 'select', 'local.tee 19', 'i32.const 1', 'i32.sub'],
              'raw command tag7 normalizes to switch selector4')
        check(1366, 11407, ['local.get 2', 'i32.load8_u offset=2299', 'i32.const 3', 'i32.ne',
                            'br_if 0 (;@25;)', 'local.get 2', 'i32.load8_u offset=2294',
                            'i32.const 1', 'i32.and', 'br_if 0 (;@25;)', 'local.get 2', 'i32.const 1',
                            'i32.store8 offset=2299', 'local.get 2', 'call 25345'], 'paused3 to running1')
        check(1366, 11599, ['local.get 2', 'i32.load8_u offset=2299', 'i32.const 1', 'i32.ne',
                            'br_if 0 (;@23;)', 'local.get 2', 'i32.load8_u offset=2294',
                            'i32.const 1', 'i32.and', 'br_if 0 (;@23;)', 'local.get 2', 'i32.const 3',
                            'i32.store8 offset=2299', 'local.get 2', 'call 35322'], 'running1 to paused3')
        check(2098, 2037, ['local.get 0', 'local.get 1', 'i32.store8 offset=2297', 'local.get 0',
                           'local.get 0', 'i32.load offset=2112', 'i32.const 1', 'i32.add',
                           'i32.store offset=2112', 'local.get 2', 'i32.eqz', 'br_if 1 (;@1;)',
                           'local.get 0', 'i32.const 2', 'i32.store8 offset=2299', 'local.get 0',
                           'i32.load8_u offset=2294', 'br_if 1 (;@1;)', 'local.get 0', 'call 35322'],
              'offer-choice entry and single-state movement stop')
        check(4595, 430, ['local.get 0', 'i32.const 1', 'i32.store8 offset=2299', 'local.get 0',
                          'i32.load8_u offset=2294', 'i32.eqz', 'if  ;; label = @6',
                          'local.get 0', 'call 25345'], 'choice completion resumes phase1')
        check(1678, 32, ['local.get 0', 'i32.load8_u offset=2299', 'local.set 2', 'local.get 0',
                         'local.get 1', 'i32.load8_u offset=1800', 'i32.store8 offset=2299',
                         'local.get 1', 'local.get 2', 'i32.store8 offset=1800'], 'per-player phase swap')
        check(7654, 8, ['local.get 0', 'i32.const 4', 'i32.store8 offset=2299'], 'defeat-state entry')
        check(48790, 9, ['local.get 0', 'i32.load offset=400', 'i32.eqz', 'br_if 0 (;@1;)',
                          'local.get 0', 'i32.load8_u offset=2299', 'i32.const 1', 'i32.ne',
                          'br_if 0 (;@1;)', 'local.get 0', 'i32.load8_u offset=2280', 'i32.const 1',
                          'i32.and', 'br_if 0 (;@1;)', 'local.get 0', 'i32.const 5',
                          'i32.store8 offset=2299'], 'running to victory5 guarded by400 and endless flag')
        check(39211, 9, ['local.get 0', 'i32.load8_u offset=2299', 'i32.const 5', 'i32.ne',
                         'br_if 0 (;@1;)', 'local.get 0', 'i32.const 1', 'i32.store8 offset=2299',
                         'local.get 0', 'i32.load8_u offset=2280', 'local.get 0', 'i32.const 1',
                         'i32.store8 offset=2280', 'local.get 0', 'local.get 0', 'f32.load offset=2064',
                         'f32.const 0x1.2cp+8 (;=300;)', 'f32.add', 'f32.store offset=2172'],
              'victory to endless continuation and next300 deadline')
        check(4391, 8, ['local.get 0', 'i32.const 1', 'i32.store8 offset=2299', 'local.get 0',
                        'i32.const 0', 'i32.store offset=2264', 'local.get 0', 'i32.const 0',
                        'i32.store offset=408'], 'revived-handler phase1 and flags')
        check(58247, 23, ['local.get 1', 'i32.const 16', 'i32.add', 'local.get 3',
                          'f64.const 0x1.f4p+9 (;=1000;)', 'f64.div', 'call 880'], 'clock adapter division1000')
        check(83471, 23, ['local.get 0', 'i32.const 16', 'i32.add', 'local.get 1',
                          'f64.const 0x1.f4p+9 (;=1000;)', 'f64.div', 'call 880'], 'second clock adapter division1000')
        check(173617, 2, ['local.get 0', 'i32.load', 'table.get 1', 'call 681)'], 'externref now import')
        check(880, 39868, ['local.get 2', 'if  ;; label = @19', 'local.get 2', 'i32.const 1',
                           'i32.sub', 'local.set 2', 'local.get 5', 'i32.load8_u', 'local.get 5',
                           'i32.const 1', 'i32.add', 'local.set 5', 'i32.const 1', 'i32.sub',
                           'i32.const 255', 'i32.and', 'i32.const 2', 'i32.ge_u',
                           'br_if 1 (;@18;)', 'br 2 (;@17;)'], 'phase1-or2 prevents global terminal aggregation')
        check(880, 39901, ['local.get 7', 'i32.load8_u', 'local.get 7', 'i32.const 1',
                           'i32.add', 'local.set 7', 'i32.const 5', 'i32.ne', 'br_if 0 (;@21;)',
                           'end', 'local.get 6', 'i32.const 5', 'i32.store8 offset=2300'],
              'any victory phase selects global victory')
        check(880, 39939, ['local.get 6', 'i32.const 4', 'i32.store8 offset=2300'],
              'no active players and no victory selects global defeat')
        branch_specs = {31902: 0, 31907: 0, 31908: 0, 31951: 0, 44372: 0, 44389: 0}
        branches = structural_targets(lines[880], branch_specs)
        expected_ends = {31902: 44382, 31907: 44373, 31908: 44382,
                         31951: 40324, 44372: 46581, 44389: 46451}
        if any(branches[n]['target']['end_function_line'] != end for n, end in expected_ends.items()):
            raise ValueError('Reviewed mode/phase branch extent differs')
        aggregate_branches = structural_targets(lines[880], {39886: 0, 39887: 0, 39896: 0, 39909: 0})
        aggregate_expected = {39886: 39889, 39887: 40311, 39896: 39938, 39909: 39910}
        if any(aggregate_branches[n]['target']['end_function_line'] != end
               for n, end in aggregate_expected.items()):
            raise ValueError('Reviewed party terminal aggregation branch differs')
        pause_branch = structural_targets(lines[1366], {59: 4})[59]
        if pause_branch['target']['end_function_line'] != 11386:
            raise ValueError('Command-tag7 pause branch dispatch differs')
        literals = []
        for address, value in LITERALS:
            spans = [s for s in segments if s['address'] <= address
                     and address + len(value) <= s['address'] + s['size']]
            if len(spans) != 1:
                raise ValueError('Phase literal does not map uniquely')
            offset = spans[0]['file_start'] + address - spans[0]['address']
            if binary[offset:offset + len(value)] != value:
                raise ValueError('Observed phase literal changed')
            literals.append({'memory_address': address, 'file_offset': offset, 'bytes': len(value),
                             'text': value.decode(), 'sha256': hashlib.sha256(value).hexdigest()})
        low_calls = []
        for number in range(46330, 46369):
            match = re.fullmatch(r'call (\d+)\)?', lines[880][number - 1])
            if match:
                low_calls.append({'function_line': number, 'callee': int(match[1])})
        report = {'version': '0.126.0', 'build': '3e72472a', 'original_sha256': ORIGINAL_SHA,
                  'complete_wat_sha256': WAT_SHA, 'complete_functions': functions,
                  'instruction_guards': guards, 'mode_phase_branches': branches,
                  'party_terminal_branches': aggregate_branches,
                  'pause_command_branch': pause_branch, 'phase_literals': literals,
                  'clock': {'tick_function': 880, 'wall_previous_flag_offset': 0,
                            'wall_previous_time_offset': 8, 'game_view_offset_in_tick_context': 16,
                            'game_clock_offset': 2064, 'initial_delta': 0,
                            'delta_formula': 'f32(ordered_clamp(now_f64-previous_f64,0,0.1))',
                            'wall_previous_updated_even_when_paused': True,
                            'clock_adapter_functions': [58247, 83471], 'clock_import': 681,
                            'clock_adapter_divisor': 1000,
                            'nan_caveat': 'Comparisons are ordered; NaN delta is not sanitized to zero.'},
                  'observed_phase_values': {'0': 'not-started/pending-start path', '1': 'running',
                                            '2': 'choice open', '3': 'paused', '4': 'defeat/end', '5': 'victory'},
                  'multi_state': {'mode_byte_offset': 2294, 'single_mode_value': 0,
                                  'global_phase_offset': 2300, 'current_player_phase_offset': 2299,
                                  'player_record_stride': 1808, 'player_phase_offset': 1800,
                                  'swap_function': 1678,
                                  'global_end_rule': 'If any player phase is1 or2, retain the global running state; otherwise global victory5 if any player phase5, else defeat4.',
                                  'qualification': 'Two phase layers are observed; not equated to external co-op role enum at2320.'},
                  'single_running_tail_call_order': low_calls,
                  'post_simulation_drains': {'main_function': 880, 'first_function_line': 46586,
                                            'observation': 'Queued client/notification/network handling continues outside the single-state running block.'},
                  'target_executed': False, 'official_network_used': False,
                  'limitations': ['Names are explanatory phase names, not recovered Rust enum identifiers.',
                                  'Only selected main-loop paths are interpreted; all commands/systems and initial construction remain incomplete.',
                                  'The callback frequency, browser clock object type and all scheduler timing are not established here.',
                                  'A common numeric field offset does not identify the same Rust structure; bases are tracked separately.',
                                  'Static pause/phase behavior does not establish physical-device timing, delivery or full multiplayer conformance.']}
        (run / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if sha(source) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise SystemExit('Original inputs changed while retaining game-loop evidence')
    print(json.dumps({'run_directory': str(run), 'complete_functions': len(functions),
                      'instruction_guards_passed': len(guards),
                      'structured_branch_matches': len(branches) + len(aggregate_branches) + 1,
                      'phase_literals_passed': len(literals), 'target_executed': False}))


if __name__ == '__main__':
    main()
