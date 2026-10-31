#!/usr/bin/env python3
"""Index selected current-core source locations and literal references, statically.

This is an auxiliary exact-byte/WAT index, not a stock REA semantic analyzer.
Original target code is never executed. Findings are candidates, not recovered types.
"""
import argparse
from bisect import bisect_right
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
WASM_SHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
SOURCE_PATTERN = re.compile(rb'crates\\wenilla-rogue\\src\\(?:game\\[a-z_]+|coop\\[a-z_]+|proto|server|realmd)\.rs')
LITERALS = (b'AZSMETER', b'AZSTAKEN', b'AZSBOSSDMG', b'AZSUNITS', b'AZSPARTY',
            b'AZSTGT', b'AZSZONE', b'\x03hp=', b'/presence', b'hp=', b';dmg=',
            b'coop-relay', b'ws://', b'wss://')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def leb(data, p, signed=False):
    result = shift = 0
    while True:
        b = data[p]; p += 1
        result |= (b & 127) << shift
        shift += 7
        if b < 128:
            if signed and b & 64:
                result -= 1 << shift
            return result, p
        if shift >= 70:
            raise ValueError('Unexpected LEB encoding')


def data_segments(data):
    if data[:8] != b'\0asm\1\0\0\0':
        raise ValueError('WASM v1 required')
    p = 8
    while p < len(data):
        kind = data[p]; size, begin = leb(data, p + 1); end = begin + size
        if end > len(data):
            raise ValueError('Section extends beyond original')
        if kind == 11:
            break
        p = end
    else:
        raise ValueError('Missing data section')
    count, p = leb(data, begin)
    segments = []
    for index in range(count):
        flags, p = leb(data, p)
        memory_address = None
        if flags in (0, 2):
            if flags == 2:
                memory, p = leb(data, p)
                if memory != 0:
                    raise ValueError('Unexpected nonzero memory index')
            if data[p] != 0x41:
                raise ValueError('Expected constant i32 data offset')
            memory_address, p = leb(data, p + 1, signed=True)
            if data[p] != 0x0b:
                raise ValueError('Unexpected data offset expression')
            p += 1
        elif flags != 1:
            raise ValueError('Unexpected data flags')
        length, p = leb(data, p)
        segments.append({'index': index, 'file_start': p, 'file_end': p + length,
                         'memory_start': memory_address, 'bytes': length})
        p += length
    if p != end:
        raise ValueError('Data section boundary mismatch')
    return segments


def selected_bodies(data, selected):
    p = 8
    sections = {}
    while p < len(data):
        kind = data[p]; size, begin = leb(data, p + 1)
        sections[kind] = (begin, begin + size)
        p = begin + size
    imports, p = leb(data, sections[2][0])
    for _ in range(imports):
        for _ in range(2):
            length, p = leb(data, p); p += length
        if data[p] != 0:
            raise ValueError('This exact target is expected to have only function imports')
        _, p = leb(data, p + 1)
    count, p = leb(data, sections[10][0])
    result = {}
    for local in range(count):
        length, begin = leb(data, p); end = begin + length
        index = imports + local
        if index in selected:
            result[index] = {'function_index': index, 'code_body_index': local,
                             'body_start': begin, 'body_end': end, 'body_bytes': length,
                             'body_sha256': hashlib.sha256(data[begin:end]).hexdigest()}
        p = end
    if p != sections[10][1] or set(result) != set(selected):
        raise ValueError('Selected functions or code-section boundary changed')
    return result


def build(data, wat):
    segments = data_segments(data)
    starts = [x['file_start'] for x in segments]

    def location(offset, length=1):
        i = bisect_right(starts, offset) - 1
        if i < 0:
            return None
        s = segments[i]
        if offset + length > s['file_end'] or s['memory_start'] is None:
            return None
        return {'data_segment': s['index'], 'file_offset': offset,
                'memory_address': s['memory_start'] + offset - s['file_start']}

    sources = []
    records = []
    address_anchors = {}
    for match in SOURCE_PATTERN.finditer(data):
        loc = location(match.start(), len(match[0]))
        if not loc:
            continue
        source = {'path': match[0].decode(), 'length': len(match[0]), **loc}
        sources.append(source)
        pattern = struct.pack('<II', source['memory_address'], source['length'])
        p = 0
        while True:
            p = data.find(pattern, p)
            if p < 0:
                break
            record_loc = location(p, 16)
            if record_loc:
                line, column = struct.unpack_from('<II', data, p + 8)
                if 0 < line < 100000 and 0 < column < 10000:
                    record = {'path': source['path'], 'line': line, 'column': column,
                              'filename_pointer': source['memory_address'],
                              'filename_length': source['length'], **record_loc}
                    records.append(record)
                    address_anchors.setdefault(record['memory_address'], []).append(record)
            p += 1
    literals = []
    for value in LITERALS:
        p = 0
        while True:
            p = data.find(value, p)
            if p < 0:
                break
            loc = location(p, len(value))
            if loc:
                anchor = {'literal': value.decode(), 'length': len(value), **loc}
                literals.append(anchor)
                address_anchors.setdefault(anchor['memory_address'], []).append(anchor)
            p += len(value)
    refs = []
    function = None
    function_start = None
    function_line = None
    bounds = []
    offset = line_number = 0
    with wat.open('rb') as stream:
        for line in stream:
            line_number += 1
            if line.startswith(b'  (func '):
                match = re.match(rb'  \(func \(;(\d+);\)', line)
                if not match:
                    raise ValueError('Unexpected function header')
                if function is not None:
                    bounds.append({'function_index': function, 'wat_start': function_start,
                                   'wat_end': offset, 'wat_start_line': function_line})
                function = int(match[1]); function_start = offset; function_line = line_number
            stripped = line.strip()
            if stripped.startswith(b'i32.const '):
                match = re.fullmatch(rb'i32\.const (-?\d+)\)*', stripped)
                if match is None:
                    raise ValueError('Unexpected i32.const instruction')
                address = int(match[1])
                if address in address_anchors:
                    refs.append({'function_index': function, 'wat_offset': offset,
                                 'wat_line': line_number, 'memory_address': address})
            offset += len(line)
    # Full WAT has trailing table/memory/data declarations: only boundaries of
    # functions followed by another function are established by this scanner.
    bound_map = {x['function_index']: x for x in bounds}
    candidates = sorted({x['function_index'] for x in refs})
    return {'data_segment_count': len(segments), 'sources': sources, 'location_records': records,
            'literals': literals, 'constant_references': refs,
            'candidate_function_bounds': [bound_map[x] for x in candidates if x in bound_map],
            'limitations': [
                'Location records are structurally plausible pointer/length/line/column records, not recovered Rust types.',
                'An i32.const address identifies a static constant occurrence, not runtime reachability or complete data flow.',
                'Literal strings can serve unrelated UI/logging paths; callers/consumers require separate interpretation.',
                'Function WAT boundaries are exact only when delimited by a following function header.',
                'This auxiliary index makes no stock REA semantic-analysis claim and executes no target code.',
            ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wasm', type=Path, default=ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm')
    parser.add_argument('--wat', type=Path, default=ROOT / 'evidence/wasm-focused-20261031T190544.818575Z/original-full.wat')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.wasm.stat().st_size != 90116970 or sha(args.wasm) != WASM_SHA:
        raise SystemExit('Current original WASM identity changed')
    if args.wat.stat().st_size != 1315634084 or sha(args.wat) != WAT_SHA:
        raise SystemExit('Complete WAT identity changed')
    output = args.output or ROOT / 'evidence' / datetime.now(timezone.utc).strftime('type-map-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    data = args.wasm.read_bytes()
    result = build(data, args.wat)
    bodies = selected_bodies(data, {2017, 13409})
    bounds = {x['function_index']: x for x in result['candidate_function_bounds']}
    complete = []
    with args.wat.open('rb') as source:
        for index in (2017, 13409):
            bound = bounds[index]
            source.seek(bound['wat_start'])
            contents = source.read(bound['wat_end'] - bound['wat_start'])
            destination = output / f'function-{index}.wat'
            destination.write_bytes(contents)
            complete.append({**bodies[index], **bound, 'wat_bytes': len(contents),
                             'wat_sha256': hashlib.sha256(contents).hexdigest(),
                             'wat_file': destination.name})
    result['selected_complete_functions'] = complete
    result['manually_interpreted_ui_contracts'] = {
        'qualification': 'Static instruction interpretation cross-checked with the separately extracted embedded Lua schema; not target execution.',
        'units': {'producer': 13409, 'prefix': 'AZSUNITS',
                  'lua_ordered_fields': ['kind', 'id', 'name', 'hp', 'hpm', 'state'],
                  'state_vector_pointer_offset': 1596, 'state_vector_length_offset': 1600,
                  'unit_stride_bytes': 416, 'id_offset': 112, 'hp_f32_offset': 288,
                  'max_hp_f32_offset': 292, 'name_helper_function': 35687,
                  'format_template_memory_address': 1581435,
                  'hp_presentation': 'NaN converted to zero, then negative/nonpositive to zero; underlying HP write is not clamped here.',
                  'kind_literals': ['guardian', 'normal', 'elite', 'boss', 'final'],
                  'state_discriminator_semantics': 'unresolved; do not infer alive/dead from HUD filtering alone'},
        'statistics': {'producer': 2017, 'template_memory_address': 1569277,
                       'state_field_offsets': {'hp': 1176, 'dmg': 1180, 'cd': 1184,
                                              'crit': 1188, 'cm': 1192, 'arm': 1208,
                                              'reg': 1212, 'area': 1216, 'cnt': 1228,
                                              'echo': 1232, 'spd': 1196, 'pick': 1200,
                                              'xp': 1204, 'luck': 1220, 'gold': 1224,
                                              'heal': 1236},
                       'modifier_ui_keys': {'16': 'auto', '17': 'pet', '18': 'cc',
                                            '19': 'big', '20': 'exe', '21': 'dotd',
                                            '22': 'thn', '28': 'shd'},
                       'lua_labels': {'auto': 'Melee', 'pet': 'Pet Damage',
                                      'cc': 'Vs Controlled', 'big': 'Vs Elites',
                                      'exe': 'Execute', 'dotd': 'Vs Afflicted',
                                      'thn': 'Thorns', 'shd': 'Shielded'},
                       'semantic_limit': 'Lua labels/tooltips name the displayed statistics; separate combat branches must establish their actual conditions.'},
    }
    result.update({'version': '0.126.0', 'build': '3e72472a', 'original_sha256': WASM_SHA,
                   'complete_wat_sha256': WAT_SHA, 'target_executed': False})
    if sha(args.wasm) != WASM_SHA:
        raise SystemExit('Original changed during indexing')
    (output / 'type-map.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'source_paths': len(result['sources']),
                      'location_records': len(result['location_records']),
                      'constant_references': len(result['constant_references']),
                      'candidate_functions': len(result['candidate_function_bounds'])}))


if __name__ == '__main__':
    main()
