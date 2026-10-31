#!/usr/bin/env python3
"""Retain the registered SessionEvent system's registration and invocation path.

Static original-byte and decoded-instruction checks only. The resource receiver
and event-kind selection are covered by the companion forward/dispatch traces.
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
FUNCTIONS = (922, 4292, 9713, 27452, 34970, 25537, 38361, 53951, 3634)
SYSTEM = b'benilla_app::net::objects::update::on_object_values'
REGISTERED_TYPE = (b'bevy_ecs::system::system_registry::RegisteredSystem<'
                   b'bevy_ecs::system::input::In<benilla_protocol::events::SessionEvent>, ()>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(source) != ORIGINAL_SHA:
        raise SystemExit('Original core identity differs')
    binary = source.read_bytes(); ranges = body_ranges(binary)
    segments, table_base, elements = module_data(binary)

    def memory(address, size):
        hits = [s for s in segments if s['address'] <= address
                and address + size <= s['address'] + s['size']]
        if len(hits) != 1:
            raise ValueError('Static data span is not uniquely mapped')
        offset = hits[0]['file_start'] + address - hits[0]['address']
        return {'memory_address': address, 'file_offset': offset, 'bytes': size,
                'sha256': hashlib.sha256(binary[offset:offset + size]).hexdigest()}, binary[offset:offset + size]

    with sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Full decoded WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('ecs-backward-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []; normalized = {}
        with wat.open('rb') as stream:
            for idx in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[idx]:
                    raise ValueError('Indexed function bounds differ from original module')
                stream.seek(row[0]); data = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', data, re.M) != [str(idx).encode()]:
                    raise ValueError('Expected one complete original decoded function')
                (run / f'function-{idx}.wat').write_bytes(data)
                normalized[idx] = '\n'.join(x.strip() for x in data.decode().splitlines())
                functions.append({'function_index': idx, 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': row[5], 'body_sha256': hashlib.sha256(binary[row[3]:row[4]]).hexdigest(),
                                  'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(data), 'wat_sha256': hashlib.sha256(data).hexdigest()})

        guards = []
        def require(idx, instructions, label):
            needle = '\n'.join(instructions)
            if needle not in normalized[idx]:
                raise ValueError(f'Reviewed instruction path changed: {label}')
            guards.append({'function_index': idx, 'label': label,
                           'function_line': normalized[idx][:normalized[idx].index(needle)].count('\n') + 1,
                           'normalized_instructions': instructions})

        require(922, ['i32.const 6033116', 'i32.store offset=56'], 'boxed system vtable')
        require(922, ['local.get 2', 'i32.const 5885211', 'i32.store offset=8',
                      'local.get 2', 'i32.load offset=16', 'i32.const 20',
                      'local.get 2', 'i32.const 0', 'call 27452'], 'named system registry key20')
        require(27452, ['local.get 6', 'local.get 0', 'local.get 1', 'call 39474'], 'registry entry by input key')
        require(27452, ['local.get 1', 'local.get 2', 'i64.load offset=8', 'i64.store offset=8',
                        'local.get 1', 'local.get 2', 'i64.load', 'i64.store'], '16-byte handler descriptor append')
        require(4292, ['i32.const 6038078', 'i32.const 124'], 'RegisteredSystem<In<SessionEvent>> component name')
        for idx in (4292, 34970):
            require(idx, ['i64.const -5355875713241034512', 'i64.xor', 'local.get 11' if idx == 34970 else 'local.get 9',
                          'i64.load offset=8 align=4', 'i64.const 8875168251625424859', 'i64.xor'],
                    'same registered-system component TypeId')
        require(25537, ['local.get 3', 'i32.const 104', 'i32.add', 'local.tee 10',
                       'local.get 4', 'i32.const 176', 'memory.copy',
                       'local.get 3', 'i32.const 76', 'i32.add', 'local.get 9',
                       'local.get 10', 'local.get 0', 'local.get 8', 'i32.load offset=44',
                       'call_indirect (type 2)'], 'copy event176 and invoke vtable+44')
        require(38361, ['local.get 4', 'i32.const 32', 'i32.add', 'local.tee 3',
                       'local.get 2', 'i32.const 176', 'memory.copy',
                       'local.get 3', 'local.get 6', 'call 3634'], 'runtime callback forwards same-size input')
        require(3634, ['local.get 2', 'i64.load offset=992', 'i64.const 22', 'i64.eq'], 'object-values internal event tag22')

        system_record, system_bytes = memory(5885211, len(SYSTEM))
        type_record, type_bytes = memory(6038078, len(REGISTERED_TYPE))
        if system_bytes != SYSTEM or type_bytes != REGISTERED_TYPE or len(REGISTERED_TYPE) != 124:
            raise ValueError('Recorded original system/type name changed')
        vtable_record, raw = memory(6033116, 84)
        slot = struct.unpack_from('<I', raw, 44)[0]
        if slot != 14258 or elements[slot - table_base] != 38361:
            raise ValueError('Original vtable+44 callback binding changed')
        report = {
            'version': '0.126.0', 'build': '3e72472a', 'original_sha256': ORIGINAL_SHA,
            'complete_wat_sha256': WAT_SHA, 'complete_functions': functions,
            'system_name': {**system_record, 'text': SYSTEM.decode()},
            'registered_component_type': {**type_record, 'text': REGISTERED_TYPE.decode(),
                                          'type_id_words_signed': [-5355875713241034512, 8875168251625424859]},
            'registry': {'registration_function': 922, 'entry_append_function': 27452,
                         'resource_accessor_function': 9713, 'key_u16': 20, 'descriptor_bytes': 16},
            'runtime_invocation': {'caller_function': 37811, 'runner_function': 25537,
                                   'component_lookup_function': 34970, 'input_bytes': 176,
                                   'vtable_field_offset': 44, 'table_slot': slot,
                                   'callback_function': 38361, 'handler_function': 3634,
                                   'handler_internal_event_tag': 22},
            'system_vtable': {**vtable_record, 'raw_hex': raw.hex(), 'table_base': table_base},
            'instruction_guards': guards, 'target_executed': False, 'network_used': False,
            'limitations': [
                'Registration, typed component lookup and invocation are statically observed, not runtime execution.',
                'The conversion and channel/receiver/event-kind selection belong to companion traces.',
                'Registry key20 and internal enum tag22 are different representations and require the dispatch mapping proof.',
            ]}
        (run / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if sha(source) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise SystemExit('Original changed during backward trace extraction')
    print(json.dumps({'run_directory': str(run), 'complete_functions': len(functions),
                      'instruction_guards_passed': len(guards), 'target_executed': False,
                      'network_used': False}))


if __name__ == '__main__':
    main()
