#!/usr/bin/env python3
"""Preserve complete0.135.1 clock/phase functions and reviewed instruction guards.

Static source evidence only; no original game entry or function is executed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct

from trace_coop import module_data
from trace_ecs_forward import structural_targets
from wasm_index import body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
WAT_SHA = '15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
FUNCTIONS = (880, 1089, 1371, 2080, 2159, 4401, 4600, 5620,
             39430, 49037, 58521, 83825, 174119, 25472, 35514, 26200,
             4253, 45626, 52236, 28425)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    if SOURCE.stat().st_size != 90959080 or sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Fixed0.135.1 original identity differs')
    binary = SOURCE.read_bytes(); ranges = body_ranges(binary)
    with sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as con:
        meta = {key: json.loads(value) for key, value in con.execute('SELECT key,value FROM meta')}
        if meta.get('original_sha256') != SOURCE_SHA or meta.get('wat_sha256') != WAT_SHA:
            raise ValueError('Index belongs to a different source/profile')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise ValueError('Complete WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('game-loop0135-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []; lines = {}
        with wat.open('rb') as stream:
            for idx in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[idx]:
                    raise ValueError('Index body is not the original binary body')
                stream.seek(row[0]); text = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', text, re.M) != [str(idx).encode()]:
                    raise ValueError('Indexed WAT is not one complete expected function')
                (run / f'function-{idx}.wat').write_bytes(text)
                lines[idx] = [line.strip() for line in text.decode().splitlines()]
                functions.append(dict(index=idx, body_start=row[3], body_end=row[4], body_bytes=row[5],
                                      body_sha256=hashlib.sha256(binary[row[3]:row[4]]).hexdigest(),
                                      wat_start=row[0], wat_end=row[1], wat_line=row[2],
                                      wat_sha256=hashlib.sha256(text).hexdigest()))
        guards = []

        def check(idx, label, expected):
            matches = [i for i in range(len(lines[idx]) - len(expected) + 1)
                       if lines[idx][i:i + len(expected)] == expected]
            if len(matches) != 1:
                raise ValueError(f'{label}: expected one continuous instruction range, got{len(matches)}')
            first = matches[0] + 1
            guards.append(dict(function_index=idx, first_function_line=first,
                               label=label, instructions=expected))
            return first

        check(880, 'first-zero tick and ordered binary64 delta clamp', [
            'local.get 0', 'i64.load', 'i64.const 1', 'i64.eq', 'if  ;; label = @1',
            'f64.const 0x1.999999999999ap-4 (;=0.1;)', 'f64.const 0x0p+0 (;=0;)',
            'local.get 1', 'local.get 0', 'f64.load offset=8', 'f64.sub', 'local.tee 160',
            'local.get 160', 'f64.const 0x0p+0 (;=0;)', 'f64.lt', 'select', 'local.tee 160',
            'local.get 160', 'f64.const 0x1.999999999999ap-4 (;=0.1;)', 'f64.gt', 'select',
            'f32.demote_f64', 'local.set 155', 'end', 'local.get 0', 'local.get 1',
            'f64.store offset=8', 'local.get 0', 'i64.const 1', 'i64.store'])
        check(880, 'game view and unavailable discriminant2', [
            'local.get 0', 'i32.const 16', 'i32.add', 'local.set 6', 'block  ;; label = @12',
            'local.get 0', 'i64.load offset=16', 'i64.const 2', 'i64.eq', 'br_if 0 (;@12;)'])
        check(880, 'single mode and pending start flag', [
            'local.get 6', 'i32.load8_u offset=2582', 'i32.eqz', 'if  ;; label = @16',
            'local.get 6', 'i32.load8_u offset=2587', 'local.tee 4', 'br_if 2 (;@14;)',
            'local.get 6', 'i32.load8_u offset=2575', 'i32.const 1', 'i32.and',
            'br_if 1 (;@15;)', 'br 2 (;@14;)'])
        check(880, 'consume start flag before initialize', [
            'local.get 6', 'i32.const 0', 'i32.store8 offset=2575', 'local.get 6',
            'call 1089', 'local.get 6', 'i32.load8_u offset=2587', 'local.set 4'])
        single_branch = check(880, 'single running clock gate', [
            'block  ;; label = @14', 'local.get 4', 'i32.const 255', 'i32.and',
            'i32.const 1', 'i32.ne', 'br_if 0 (;@14;)', 'local.get 6', 'local.get 155',
            'local.get 6', 'f32.load offset=2352', 'f32.add', 'local.tee 149',
            'f32.store offset=2352'])
        check(880, 'multi global phase source and start guards', [
            'block  ;; label = @16', 'local.get 6', 'i32.load8_u offset=2588', 'local.tee 4',
            'br_if 0 (;@16;)', 'local.get 6', 'i32.load8_u offset=2575', 'i32.const 1',
            'i32.and', 'i32.eqz', 'br_if 0 (;@16;)', 'local.get 6', 'i32.load8_u offset=2583',
            'i32.const 1', 'i32.and', 'br_if 0 (;@16;)'])
        multi_branch = check(880, 'multi global running clock gate', [
            'block  ;; label = @16', 'local.get 4', 'i32.const 255', 'i32.and',
            'i32.const 1', 'i32.ne', 'br_if 0 (;@16;)', 'local.get 6', 'local.get 155',
            'local.get 6', 'f32.load offset=2352', 'f32.add', 'f32.store offset=2352'])
        check(1089, 'start phase1', ['local.get 0', 'i32.const 1', 'i32.store8 offset=2587',
                                   'i32.const 0', 'call 4546', 'drop'])
        check(1371, 'raw command normalization and dispatch', [
            'i32.const 11', 'local.get 1', 'i32.load', 'local.tee 2', 'i32.const 2',
            'i32.sub', 'local.get 2', 'i32.const 1', 'i32.le_u', 'select',
            'local.tee 19', 'i32.const 1', 'i32.sub'])
        check(1371, 'pause command game guard and boolean payload', [
            'local.get 0', 'i64.load offset=16', 'i64.const 2', 'i64.eq', 'br_if 19 (;@3;)',
            'local.get 0', 'i32.const 16', 'i32.add', 'local.set 2', 'local.get 1',
            'i32.load8_u offset=4', 'i32.eqz', 'if  ;; label = @23'])
        check(1371, 'resume phase3 mode lowbit clear', [
            'local.get 2', 'i32.load8_u offset=2587', 'i32.const 3', 'i32.ne', 'br_if 0 (;@25;)',
            'local.get 2', 'i32.load8_u offset=2582', 'i32.const 1', 'i32.and',
            'br_if 0 (;@25;)', 'local.get 2', 'i32.const 1', 'i32.store8 offset=2587',
            'local.get 2', 'call 25472'])
        check(1371, 'pause phase1 mode lowbit clear', [
            'local.get 2', 'i32.load8_u offset=2587', 'i32.const 1', 'i32.ne', 'br_if 0 (;@23;)',
            'local.get 2', 'i32.load8_u offset=2582', 'i32.const 1', 'i32.and',
            'br_if 0 (;@23;)', 'local.get 2', 'i32.const 3', 'i32.store8 offset=2587',
            'local.get 2', 'call 35514'])
        check(2080, 'per player phase swap', [
            'local.get 0', 'i32.load8_u offset=2587', 'local.set 2', 'local.get 0',
            'local.get 1', 'i32.load8_u offset=1996', 'i32.store8 offset=2587',
            'local.get 1', 'local.get 2', 'i32.store8 offset=1996'])
        check(880, 'phase1 or2 prevents global terminal aggregation', [
            'local.get 4', 'if  ;; label = @20', 'local.get 4', 'i32.const 1', 'i32.sub',
            'local.set 4', 'local.get 5', 'i32.load8_u', 'local.get 5', 'i32.const 1',
            'i32.add', 'local.set 5', 'i32.const 1', 'i32.sub', 'i32.const 255', 'i32.and',
            'i32.const 2', 'i32.ge_u', 'br_if 1 (;@19;)', 'br 2 (;@18;)'])
        check(880, 'any victory gives global5', [
            'local.get 8', 'i32.load8_u', 'local.get 8', 'i32.const 1', 'i32.add',
            'local.set 8', 'i32.const 5', 'i32.ne', 'br_if 0 (;@22;)', 'end',
            'local.get 6', 'i32.const 5', 'i32.store8 offset=2588'])
        check(880, 'otherwise global4', [
            'end', 'local.get 6', 'i32.const 4', 'i32.store8 offset=2588',
            'local.get 14', 'i32.const 0', 'i32.store8 offset=4096'])
        check(5620, 'defeat phase4 and stop flag', [
            'local.get 0', 'i32.const 4', 'i32.store8 offset=2587',
            'local.get 0', 'i32.const 1', 'i32.store offset=408'])
        check(49037, 'victory three guards', [
            'local.get 0', 'i32.load offset=400', 'i32.eqz', 'br_if 0 (;@1;)',
            'local.get 0', 'i32.load8_u offset=2587', 'i32.const 1', 'i32.ne',
            'br_if 0 (;@1;)', 'local.get 0', 'i32.load8_u offset=2568', 'i32.const 1',
            'i32.and', 'br_if 0 (;@1;)', 'local.get 0', 'i32.const 5',
            'i32.store8 offset=2587'])
        check(39430, 'victory continue Endless and deadline', [
            'local.get 0', 'i32.load8_u offset=2587', 'i32.const 5', 'i32.ne',
            'br_if 0 (;@1;)', 'local.get 0', 'i32.const 1', 'i32.store8 offset=2587',
            'local.get 0', 'i32.load8_u offset=2568', 'local.get 0', 'i32.const 1',
            'i32.store8 offset=2568', 'local.get 0', 'local.get 0', 'f32.load offset=2352',
            'f32.const 0x1.2cp+8 (;=300;)', 'f32.add', 'f32.store offset=2460'])
        check(4401, 'revive phase1 and cleared flags', [
            'local.get 0', 'i32.const 1', 'i32.store8 offset=2587', 'local.get 0',
            'i32.const 0', 'i32.store offset=2552', 'local.get 0', 'i32.const 0',
            'i32.store offset=408'])
        check(2159, 'enter choice phase2 only after enter_now guard', [
            'local.get 2', 'i32.eqz', 'br_if 1 (;@1;)', 'local.get 0', 'i32.const 2',
            'i32.store8 offset=2587', 'local.get 0', 'i32.load8_u offset=2582',
            'br_if 1 (;@1;)', 'local.get 0', 'call 35514'])
        check(4600, 'finish choice phase1 and mode0 resume', [
            'local.get 0', 'i32.const 1', 'i32.store8 offset=2587', 'local.get 0',
            'i32.load8_u offset=2582', 'i32.eqz', 'if  ;; label = @6',
            'local.get 0', 'call 25472'])
        for idx, local in ((58521, 3), (83825, 1)):
            check(idx, 'clock adapter milliseconds to seconds' + str(idx), [
                f'local.get {1 if idx == 58521 else 0}', 'i32.const 16', 'i32.add',
                f'local.get {local}', 'f64.const 0x1.f4p+9 (;=1000;)', 'f64.div', 'call 880'])
        check(174119, 'externref now host import681', [
            'local.get 0', 'i32.load', 'table.get 1', 'call 681)'])
        check(880, 'absent optional transport niche', [
            'block  ;; label = @12', 'local.get 0', 'i32.load offset=4748',
            'local.tee 4', 'i32.const -1', 'i32.eq', 'br_if 0 (;@12;)'])
        check(880, 'outer session role discriminant and switch', [
            'local.get 0', 'i64.load offset=2608', 'local.tee 138', 'i32.wrap_i64',
            'i32.const 2', 'i32.sub', 'i32.const 2', 'local.get 138', 'i64.const 1',
            'i64.gt_u', 'local.tee 2', 'select', 'i32.const 1', 'i32.sub',
            'br_table 0 (;@14;) 1 (;@13;) 2 (;@12;)'])
        check(4253, 'original constructor transport vtable binding only statically read', [
            'local.get 1', 'i32.const 1495776', 'i32.store offset=4772',
            'local.get 1', 'local.get 9', 'i32.store offset=4768'])
        check(4253, 'original transport object24B allocation and backing pointer', [
            'local.get 13', 'i32.const -1', 'i32.store offset=8', 'i32.const 24',
            'i32.const 8', 'call 106891', 'local.tee 9', 'i32.eqz', 'br_if 2 (;@17;)',
            'local.get 9', 'local.get 16', 'i64.load offset=56', 'i64.store offset=16'])
        check(45626, 'original transport queue drain and empty replacement', [
            'local.get 3', 'i32.load offset=36', 'local.set 4', 'local.get 3',
            'i32.const 0', 'i32.store offset=36', 'local.get 3',
            'i64.load offset=28 align=4', 'local.set 5', 'local.get 3',
            'i64.const 34359738368', 'i64.store offset=28 align=4'])
        check(45626, 'absent elapsed instant niche in original queue', [
            'local.get 1', 'i32.load offset=8', 'local.tee 3', 'i32.const -1',
            'i32.eq', 'br_if 0 (;@2;)'])
        check(880, 'post tick serialized snapshot cadence guard', [
            'block  ;; label = @12', 'local.get 1', 'local.get 0', 'f64.load offset=4840',
            'f64.sub', 'f64.const 0x1.999999999999ap-3 (;=0.2;)', 'f64.ge',
            'i32.eqz', 'br_if 0 (;@12;)'])
        check(880, 'terminal event once per effective phase', [
            'local.get 6', 'i32.const 2588', 'i32.const 2587', 'local.get 0',
            'i32.load8_u offset=2598', 'select', 'i32.add', 'i32.load8_u', 'local.tee 2',
            'i32.const 6', 'i32.and', 'i32.const 4', 'i32.ne', 'br_if 0 (;@13;)',
            'local.get 0', 'i32.load8_u offset=5166', 'local.get 2', 'i32.eq',
            'br_if 0 (;@13;)', 'local.get 0', 'local.get 2', 'i32.store8 offset=5166',
            'local.get 0', 'call 1420'])
        expected_tail = ['local.get 6', 'local.get 155', 'call 2088', 'local.get 6',
                         'local.get 155', 'call 916', 'local.get 6', 'local.get 155',
                         'call 975', 'local.get 6', 'call 1754', 'local.get 6', 'call 3757',
                         'local.get 6', 'local.get 155', 'call 915', 'local.get 6', 'call 38007',
                         'local.get 6', 'call 2602', 'local.get 6', 'local.get 155', 'call 921',
                         'local.get 6', 'call 2862', 'local.get 6', 'call 2573', 'local.get 6',
                         'i32.load8_u offset=2579', 'i32.eqz', 'if  ;; label = @15',
                         'local.get 6', 'local.get 155', 'call 947', 'local.get 6', 'call 2376',
                         'end', 'local.get 6', 'call 49037']
        tail_first = check(880, 'single running ordered scheduler tail', expected_tail)
        branch_lines = {single_branch + 6: 0, multi_branch + 6: 0, 42856: 0, 42857: 0,
                        42866: 0, 42879: 0}
        branches = structural_targets(lines[880], branch_lines)
        if branches[42857]['target']['end_function_line'] <= 42911:
            raise ValueError('Aggregation active-phase exit must skip both terminal writes')
        command_branch = structural_targets(lines[1371], {59: 4})[59]
        if command_branch['target']['end_function_line'] != 11379:
            raise ValueError('Rawtag7 no longer selects retained pause branch')
        segments, element_base, elements = module_data(binary)
        vtable_address = 1495776
        segment = next(s for s in segments if s['address'] <= vtable_address
                       and vtable_address + 32 <= s['address'] + s['size'])
        vtable_file_offset = segment['file_start'] + vtable_address - segment['address']
        vtable = binary[vtable_file_offset:vtable_file_offset + 32]
        words = struct.unpack('<8I', vtable)
        if words[:3] != (1721, 24, 8) or elements[words[5] - element_base] != 45626:
            raise ValueError('Original transport vtable/element binding differs')
        transport_binding = dict(memory_address=vtable_address, file_offset=vtable_file_offset,
                                 bytes_hex=vtable.hex(), sha256=hashlib.sha256(vtable).hexdigest(),
                                 size=words[1], alignment=words[2],
                                 queue_drain_vtable_offset=20, table_slot=words[5],
                                 original_function=elements[words[5] - element_base],
                                 constructor_function4253_executed=False)
        payload = dict(version='0.135.1', build='0898d5e3', original_wasm_sha256=SOURCE_SHA,
                       complete_wat_sha256=WAT_SHA, index_sha256=sha(args.index),
                       complete_functions=functions, instruction_guards=guards,
                       structured_branches=branches, pause_command_branch=command_branch,
                       bindings=dict(tick=880, command=1371, game_view_in_tick_context=16,
                                     previous_marker=0, previous_f64=8, game_clock=2352,
                                     mode=2582, phase=2587, global_phase=2588, start_flag=2575,
                                     global_start_extra_flag=2583, player_stride=2000,
                                     player_phase=1996, swap=2080, endless_flag=2568,
                                     endless_deadline=2460),
                       single_running_tail_call_order=[int(x.split()[1]) for x in expected_tail
                                                       if x.startswith('call ')],
                       single_running_tail_first_function_line=tail_first,
                       controlled_fixture_transport_vtable=transport_binding,
                       target_executed=False, full_scheduler_reconstructed=False,
                       limitations=['Phase/clock/controller projections only; constructors, incoming commands, full scheduler and delivery remain incomplete.',
                                    'Mode uses full byte for single-vs-multi but only low bit for explicit pause command.',
                                    'Offsets are relative to G=context+16; player record1996 is a different base.',
                                    'No runtime, real device, network, save or installation behavior is inferred from static guards.'])
        (run / 'manifest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    if sha(SOURCE) != SOURCE_SHA or sha(wat) != WAT_SHA:
        raise ValueError('Original input identity changed')
    print(json.dumps(dict(evidence_directory=str(run), functions=len(functions), guards=len(guards),
                          structured_branches=len(branches) + 1, target_executed=False)))


if __name__ == '__main__':
    main()
