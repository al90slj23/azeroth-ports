#!/usr/bin/env python3
"""Recover the exact current-core ability/class tables and reviewed cast paths.

Static memory reconstruction and original function extraction only. This local
aid does not execute the target, inspect saves, or connect to a game server.
Uninterpreted fields remain raw words rather than guessed gameplay names.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct

from core_type_map import data_segments
from wasm_index import ORIGINAL_SHA, body_ranges, sha
from trace_ecs_forward import structural_targets

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
ABILITY_BASE, ABILITY_STRIDE, ABILITY_COUNT = 1719492, 88, 113
CLASS_BASE, CLASS_STRIDE, CLASS_COUNT = 1714716, 88, 9
FUNCTIONS = (917, 934, 933, 1065, 1472, 22136, 25242, 26457,
             26840, 27428, 35825, 19912, 46955, 55177, 35826)
SCHOOLS = ('Physical', 'Holy', 'Fire', 'Nature', 'Frost', 'Shadow', 'Arcane')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reconstruct_memory(binary):
    segments = data_segments(binary)
    if any(s['memory_start'] is None or s['memory_start'] < 0 for s in segments):
        raise ValueError('Unexpected static-memory data profile')
    memory = bytearray(max(s['memory_start'] + s['bytes'] for s in segments))
    # WASM linear memory starts zeroed; omitted zero runs in active segments are
    # meaningful. Segment file bytes are not a contiguous copy of Rust tables.
    for s in segments:
        memory[s['memory_start']:s['memory_start'] + s['bytes']] = binary[s['file_start']:s['file_end']]
    return memory, segments


def extract_catalogues(memory, segments):
    def u32(p):
        return struct.unpack_from('<I', memory, p)[0]

    def f32(p):
        return struct.unpack_from('<f', memory, p)[0]

    def span(address, length):
        if address < 0 or length < 0 or address + length > len(memory):
            raise ValueError('Static span outside reconstructed memory')
        return bytes(memory[address:address + length])

    def string(p):
        address, length = struct.unpack_from('<II', memory, p)
        if length > 2048:
            raise ValueError('Unexpected static string size')
        return span(address, length).decode('utf-8', errors='strict')

    def source_spans(address, length):
        end = address + length
        result = []
        covered = 0
        for s in segments:
            lo, hi = max(address, s['memory_start']), min(end, s['memory_start'] + s['bytes'])
            if lo < hi:
                covered += hi - lo
                result.append({'segment_index': s['index'], 'memory_start': lo,
                               'memory_end_exclusive': hi,
                               'original_file_start': s['file_start'] + lo - s['memory_start'],
                               'original_file_end_exclusive': s['file_start'] + hi - s['memory_start']})
        return {'active_segment_spans': result, 'implicit_zero_bytes': length - covered}

    abilities = []
    for index in range(ABILITY_COUNT):
        address = ABILITY_BASE + index * ABILITY_STRIDE
        raw = span(address, ABILITY_STRIDE)
        identifier = string(address + 12)
        if not re.fullmatch(r'[a-z][a-z0-9_]*', identifier):
            raise ValueError('Unexpected ability identifier')
        upgrade_pointer, upgrade_count = struct.unpack_from('<II', memory, address + 36)
        kinds = list(span(upgrade_pointer, upgrade_count))
        if not kinds or any(k > 4 for k in kinds) or len(set(kinds)) != len(kinds):
            raise ValueError('Unexpected declared upgrade-kind list')
        school = memory[address + 85]
        if school >= len(SCHOOLS) or memory[address + 84] > 11:
            raise ValueError('Unexpected declared execution-kind/school byte')
        abilities.append({
            'index': index, 'memory_address': address, 'record_bytes': ABILITY_STRIDE,
            'record_sha256': digest(raw), 'identifier': identifier,
            'display_name': string(address + 20), 'icon_key': string(address + 28),
            'declared_upgrade_kinds': kinds, 'upgrade_kind_bytes_address': upgrade_pointer,
            'effect_tag_u32': u32(address),
            'effect_parameter_4_f32': f32(address + 4),
            'effect_parameter_8_f32': f32(address + 8),
            'spell_id_u32': u32(address + 44), 'base_damage_f32': f32(address + 48),
            'base_cooldown_f32': f32(address + 52), 'base_range_f32': f32(address + 56),
            'base_radius_f32': f32(address + 60), 'base_count_u32': u32(address + 64),
            'base_duration_f32': f32(address + 68), 'word72_u32': u32(address + 72),
            'projectile_speed_candidate_f32': f32(address + 76), 'word80_u32': u32(address + 80),
            'execution_kind_u8': memory[address + 84], 'school_code_u8': school,
            'school_label': SCHOOLS[school], 'reserved_86_87_hex': raw[86:88].hex(),
        })
    by_id = {x['identifier']: x for x in abilities}
    if len(by_id) != ABILITY_COUNT:
        raise ValueError('Duplicate ability identifiers')
    classes = []
    for index in range(CLASS_COUNT):
        address = CLASS_BASE + index * CLASS_STRIDE
        raw = span(address, CLASS_STRIDE)
        kit_pointer, kit_count = struct.unpack_from('<II', memory, address + 32)
        kit = [string(kit_pointer + i * 8) for i in range(kit_count)]
        if any(x not in by_id for x in kit) or string(address + 40) not in kit:
            raise ValueError('Class kit does not resolve to the ability catalogue')
        classes.append({'index': index, 'memory_address': address, 'record_sha256': digest(raw),
                        'identifier': string(address + 16), 'display_name': string(address + 24),
                        'ability_ids': kit, 'starting_ability_id': string(address + 40),
                        'color': string(address + 48), 'icon_key': string(address + 56),
                        'header_words_0_to_12': list(struct.unpack_from('<4I', raw)),
                        'uninterpreted_tail_words_72_to_84': list(struct.unpack_from('<4I', raw, 72))})
    kit_ids = {x for c in classes for x in c['ability_ids']}
    if len(kit_ids) != 103 or sum(len(c['ability_ids']) for c in classes) != 103:
        raise ValueError('Observed class-kit cardinality changed')
    return {'abilities': abilities, 'classes': classes,
            'outside_class_kits': sorted(set(by_id) - kit_ids),
            'ability_table': {'memory_start': ABILITY_BASE, 'stride': ABILITY_STRIDE,
                              'count': ABILITY_COUNT, 'bytes': ABILITY_STRIDE * ABILITY_COUNT,
                              'reconstructed_initial_memory_sha256': digest(span(ABILITY_BASE, ABILITY_STRIDE * ABILITY_COUNT)),
                              **source_spans(ABILITY_BASE, ABILITY_STRIDE * ABILITY_COUNT)},
            'class_table': {'memory_start': CLASS_BASE, 'stride': CLASS_STRIDE,
                            'count': CLASS_COUNT, 'bytes': CLASS_STRIDE * CLASS_COUNT,
                            'reconstructed_initial_memory_sha256': digest(span(CLASS_BASE, CLASS_STRIDE * CLASS_COUNT)),
                            **source_spans(CLASS_BASE, CLASS_STRIDE * CLASS_COUNT)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original) != ORIGINAL_SHA:
        raise SystemExit('Original core identity differs')
    binary = original.read_bytes(); ranges = body_ranges(binary)
    memory, segments = reconstruct_memory(binary)
    catalogues = extract_catalogues(memory, segments)
    con = sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True)
    try:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('abilities-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []; normalized = {}
        with wat.open('rb') as stream:
            for index in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (index,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[index]:
                    raise ValueError('Indexed function body differs from original')
                stream.seek(row[0]); data = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', data, re.M) != [str(index).encode()]:
                    raise ValueError('Expected one complete original function')
                (run / f'function-{index}.wat').write_bytes(data)
                normalized[index] = [x.strip() for x in data.decode().splitlines()]
                functions.append({'function_index': index, 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': row[5], 'body_sha256': digest(binary[row[3]:row[4]]),
                                  'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(data), 'wat_sha256': digest(data)})
        guards = []
        def require(index, sequence, label):
            joined = '\n'.join(normalized[index]); needle = '\n'.join(sequence)
            if needle not in joined:
                raise ValueError('Reviewed path differs: ' + label)
            guards.append({'function_index': index, 'label': label,
                           'function_line': joined[:joined.index(needle)].count('\n') + 1,
                           'instructions': sequence})
        require(1472, ['local.get 6', 'i32.const 88', 'i32.add', 'local.tee 6',
                       'i32.const 9944', 'i32.ne'], '113 definitions at stride88')
        require(1472, ['local.get 6', 'i32.const 1719492', 'i32.add',
                       'local.tee 7', 'i32.store offset=304'], 'runtime definition pointer uses table record start')
        require(1065, ['local.get 0', 'i32.load8_u offset=2299', 'i32.const 2', 'i32.ne'], 'real choice-phase guard')
        require(1065, ['local.get 0', 'i32.load offset=1468', 'local.get 8', 'i32.const 80',
                       'i32.mul', 'i32.add', 'local.tee 1'], 'owned ability selected for mutation')
        require(1065, ['local.get 1', 'local.get 6', 'local.get 11', 'call 25242'], 'upgrade uses original numeric helper')
        require(1065, ['local.get 1', 'local.get 31', 'f32.const 0x1p+0 (;=1;)', 'f32.add',
                       'local.get 1', 'f32.load offset=12', 'f32.mul', 'f32.store offset=12'], 'owned damage multiplier write')
        require(1065, ['local.get 1', 'local.get 1', 'f32.load offset=16', 'local.get 31',
                       'f32.sub', 'f32.store offset=16'], 'owned cooldown multiplier write')
        require(1065, ['local.get 0', 'i32.load offset=1468', 'local.get 5', 'i32.const 80',
                       'i32.mul', 'i32.add', 'local.get 3', 'i32.const 192', 'i32.add',
                       'i32.const 80', 'memory.copy'], 'new ability appended to the same owned vector')
        require(22136, ['local.get 1', 'i32.load offset=1468'], 'cast lookup reads owned ability vector')
        require(22136, ['local.get 2', 'i32.load offset=12', 'local.set 10',
                        'local.get 2', 'i32.load offset=16', 'local.set 7'], 'cast lookup compares definition identifier')
        require(917, ['local.get 0', 'i32.load offset=548', 'local.get 4', 'i32.add', 'i32.const 8',
                      'i32.add', 'local.tee 7', 'local.get 7', 'f32.load', 'local.get 1',
                      'f32.sub', 'f32.store'], 'active countdown subtracts tick delta')
        require(917, ['local.get 3', 'i32.const 48', 'i32.add', 'local.get 0', 'local.get 7',
                      'i32.load', 'local.tee 8', 'call 22136'], 'countdown expiry resolves live effective ability')
        require(917, ['local.get 0', 'local.get 3', 'i32.const 48', 'i32.add', 'call 934'], 'automatic cast enters execution')
        require(917, ['local.get 33', 'local.get 38', 'local.get 40', 'local.get 39', 'local.get 45',
                      'f32.const 0x1.666666p+0 (;=1.4;)', 'f32.mul', 'f32.mul', 'f32.mul', 'f32.mul'], 'successful ordinary cooldown product')
        require(917, ['i32.const 8', 'i32.add', 'i32.const 1050253722', 'i32.store'], 'failed cast sets0.3 retry countdown')
        require(934, ['local.get 30', 'local.get 8', 'f32.load offset=60', 'local.get 1',
                      'f32.load offset=24', 'local.get 1', 'f32.load offset=64',
                      'f32.mul', 'f32.mul', 'f32.mul'], 'radius uses definition60 and ability24/64')
        require(934, ['local.get 0', 'local.get 3', 'i32.const 72', 'i32.add', 'local.get 29',
                      'i32.const 8', 'i32.const 0', 'call 27428'], 'radial execution queries unit targets')
        require(934, ['local.get 8', 'i32.load offset=44', 'local.get 8', 'i32.load8_u offset=85',
                      'local.get 1', 'i32.const 0', 'call 933'], 'radial hit enters actual damage consumer')
        require(934, ['local.get 8', 'f32.load offset=68', 'local.tee 32',
                      'f32.const 0x1.666666p+0 (;=1.4;)', 'f32.mul', 'local.get 1',
                      'f32.load offset=28', 'local.tee 35', 'f32.mul', 'local.get 1',
                      'f32.load offset=68', 'f32.mul'], 'duration uses definition68 and ability28/68')
        require(19912, ['local.get 4', 'i32.load', 'br_if 0 (;@3;)',
                        'local.get 4', 'i64.load offset=112', 'local.set 3'], 'target iterator accepts only state0 units')
        require(19912, ['local.tee 21', 'local.get 13', 'f32.load', 'f32.le',
                        'i32.eqz', 'br_if 0 (;@3;)'], 'inclusive squared-distance test')
        require(35826, ['local.get 1', 'i32.const 255', 'i32.and', 'i32.const 1', 'i32.sub'], 'school code normalization')
        branches = structural_targets(normalized[934], {524: 0})
        if branches[524]['target']['end_function_line'] != 585:
            raise ValueError('Execution-kind2 radial branch differs')
        report = {'version': '0.126.0', 'build': '3e72472a', 'original_sha256': ORIGINAL_SHA,
                  'complete_wat_sha256': WAT_SHA, 'complete_functions': functions,
                  'catalogues': catalogues, 'instruction_guards': guards,
                  'structural_branch_targets': {'934': branches},
                  'target_executed': False, 'network_used': False,
                  'limitations': [
                      'Tables describe the exact zero-initialized/active-data static image; no runtime mutation is observed.',
                      'This is a local exact-byte extraction and manual semantic navigation aid, not stock REA semantic analysis.',
                      'Numeric fields with unconfirmed consumers remain word72/word80 or candidate labels.',
                      'The radial cast and owned-upgrade path are traced; all113 complete execution behaviors are not recovered.',
                      'Effect variants, delayed hits, all talents/procs, and all failure/tie-order branches remain incomplete.',
                  ]}
        (run / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        if sha(original) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
            raise SystemExit('An original changed during extraction')
        print(json.dumps({'run_directory': str(run), 'abilities': len(catalogues['abilities']),
                          'classes': len(catalogues['classes']), 'class_kit_ids': 103,
                          'complete_functions': len(functions), 'instruction_guards_passed': len(guards),
                          'structural_branch_matches': 1, 'target_executed': False, 'network_used': False}))
    finally:
        con.close()


if __name__ == '__main__':
    main()
