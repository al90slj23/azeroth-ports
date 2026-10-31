#!/usr/bin/env python3
"""Retain decoder dispatch and an independently named client field-update system.

This is static navigation/byte evidence. It deliberately does not claim that
the decoded message has been traced through the missing ECS event-delivery hop.
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
from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
FUNCTIONS = (878, 922, 3634, 4642, 9445, 9772, 10095, 10310, 26862,
             38361, 53951, 65110, 65528)
SYSTEM = b'benilla_app::net::objects::update::on_object_values'


def first_table_target(lines, selector):
    """Resolve one known initial br_table target to its matching end."""
    frames = []
    selected = None
    dispatch_line = None
    for number, line in enumerate(lines, 1):
        if line.startswith(('block ', 'loop ', 'if ')):
            frames.append({'function_line': number, 'header': line})
        elif line in ('end', 'end)') and frames:
            frames.pop()['end_function_line'] = number
        if line.startswith('br_table') and selected is None:
            depths = [int(x) for x in re.findall(r'(\d+) \(;@\d+;\)', line)]
            if not 0 <= selector < len(depths) - 1:
                raise ValueError('Selected explicit switch arm is missing')
            depth = depths[selector]
            selected = frames[-1 - depth]
            selected['branch_depth'] = depth
            dispatch_line = number
    if selected is None or 'end_function_line' not in selected:
        raise ValueError('Switch frame was not matched completely')
    return {'dispatch_function_line': dispatch_line, 'selector': selector, **selected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(source) != ORIGINAL_SHA:
        raise SystemExit('Original target identity differs')
    binary = source.read_bytes()
    bounds = body_ranges(binary)
    segments, table_base, elements = module_data(binary)

    def memory(address, length):
        spans = [s for s in segments if s['address'] <= address
                 and address + length <= s['address'] + s['size']]
        if len(spans) != 1:
            raise ValueError('Static memory span does not map uniquely')
        offset = spans[0]['file_start'] + address - spans[0]['address']
        return offset, binary[offset:offset + length]

    index = args.index.resolve(strict=True)
    with sqlite3.connect(index.as_uri() + '?mode=ro', uri=True) as connection:
        meta = {k: json.loads(v) for k, v in connection.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT digest differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('client-values-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []
        normalized = {}
        with wat.open('rb') as text:
            for idx in FUNCTIONS:
                row = connection.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                         'FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None or tuple(row[3:]) != bounds[idx]:
                    raise ValueError('Function index body bounds differ from original')
                text.seek(row[0]); decoded = text.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', decoded, re.M) != [str(idx).encode()]:
                    raise ValueError('Expected exactly one selected complete function')
                (run / f'function-{idx}.wat').write_bytes(decoded)
                normalized[idx] = [line.strip() for line in decoded.decode().splitlines()]
                functions.append({'function_index': idx, 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': row[5], 'body_sha256': hashlib.sha256(binary[row[3]:row[4]]).hexdigest(),
                                  'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(decoded), 'wat_sha256': hashlib.sha256(decoded).hexdigest()})

        opcode = first_table_target(normalized[878], 169 - 58)
        before = normalized[878][opcode['dispatch_function_line'] - 7:opcode['dispatch_function_line'] - 1]
        if before != ['local.get 1', 'i32.const 65535', 'i32.and', 'local.tee 13', 'i32.const 58', 'i32.sub']:
            raise ValueError('Opcode selector normalization changed')
        arm = normalized[878][opcode['end_function_line']:opcode['end_function_line'] + 7]
        if arm != ['local.get 4', 'i32.const 648', 'i32.add', 'local.get 4',
                   'i32.const 8', 'i32.add', 'call 4642']:
            raise ValueError('Opcode169 dispatch does not enter the reviewed parser')
        opcode.update({'opcode_u16': 169, 'selector_subtraction': 58,
                       'next_instructions': arm, 'parser_function': 4642})
        kind0 = first_table_target(normalized[4642], 0)
        kind_arm = normalized[4642][kind0['end_function_line']:kind0['end_function_line'] + 15]
        if kind_arm[-1] != 'call 9772' or 'call 10095' not in kind_arm:
            raise ValueError('Update-kind0 parser route differs')
        kind0['next_instructions'] = kind_arm

        file_offset, name = memory(5885211, len(SYSTEM))
        if name != SYSTEM:
            raise ValueError('Named system string differs')
        init = '\n'.join(normalized[922])
        marker = 'i32.const 5885211\ni32.store offset=8'
        position = init.index(marker)
        span = init[max(0, position - 1500):position + len(marker) + 150]
        if ('i32.const 6033116\ni32.store offset=56' not in span or
                'i32.const 51\ni32.store offset=12' not in span):
            raise ValueError('Named-system/vtable construction association differs')
        vtable_file, raw_vtable = memory(6033116, 84)
        words = struct.unpack('<21I', raw_vtable)
        bindings = []
        for offset, slot_expected, function_expected in [(36, 14256, 53951), (44, 14258, 38361)]:
            slot = words[offset // 4]
            if slot != slot_expected or elements[slot - table_base] != function_expected:
                raise ValueError('Known system callback binding differs')
            bindings.append({'vtable_field_offset': offset, 'table_slot': slot,
                             'function_index': function_expected})
        required_edges = [(53951, 3634), (38361, 3634), (3634, 9445),
                          (3634, 10310), (9445, 26862), (10310, 26862)]
        for caller, callee in required_edges:
            if f'call {callee}' not in normalized[caller] and f'call {callee})' not in normalized[caller]:
                raise ValueError('Reviewed client update call edge differs')
        for getter in (65110, 65528):
            text = '\n'.join(normalized[getter])
            if ('i32.load8_u offset=2\ni32.const 64\ni32.and' not in text or
                    'i32.load offset=16\ni32.load offset=88' not in text):
                raise ValueError('Field22 getter bit/value path differs')
        report = {
            'version': '0.126.0', 'build': '3e72472a', 'original_sha256': ORIGINAL_SHA,
            'complete_wat_sha256': WAT_SHA, 'complete_functions': functions,
            'opcode169_dispatch': opcode, 'update_kind0_dispatch': kind0,
            'named_system': {'name': SYSTEM.decode(), 'memory_address': 5885211,
                             'file_offset': file_offset, 'bytes': len(SYSTEM),
                             'sha256': hashlib.sha256(name).hexdigest(),
                             'initializer_function': 922, 'normalized_constructor_span': span},
            'system_vtable': {'memory_address': 6033116, 'file_offset': vtable_file,
                              'bytes': len(raw_vtable), 'raw_hex': raw_vtable.hex(),
                              'sha256': hashlib.sha256(raw_vtable).hexdigest(),
                              'table_base': table_base, 'callback_bindings': bindings},
            'verified_direct_call_edges': [{'caller': a, 'callee': b} for a, b in required_edges],
            'field22_getters': [65110, 65528], 'field22_mask_bit': 22, 'field22_value_byte_offset': 88,
            'target_executed': False, 'network_used': False,
            'limitations': [
                'Opcode dispatch/parser and named ECS field-update system are separately evidenced.',
                'The decoded-message to on_object_values event-delivery hop has not been traced.',
                'Static callback registration does not prove runtime delivery, UI convergence or cooperative behavior.',
                'Function10095 is a local auxiliary extraction; companion reports identify which functions have separate REA Evidence.',
            ],
        }
        (run / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if sha(source) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise SystemExit('An original changed while retaining client values evidence')
    print(json.dumps({'run_directory': str(run), 'complete_functions': len(functions),
                      'system_callback_bindings': len(bindings), 'direct_call_edges': len(required_edges),
                      'target_executed': False, 'network_used': False}))


if __name__ == '__main__':
    main()
