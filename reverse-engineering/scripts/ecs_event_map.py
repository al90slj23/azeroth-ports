#!/usr/bin/env python3
"""Retain the current-core network-handler registry and dispatcher evidence.

This is local static extraction, not an automatic recovery of Bevy semantics.
No game code, channel operation or network packet is executed by this script.
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
FUNCTIONS = (922, 9713, 27452, 39474, 37811, 62584, 62585, 78110,
             44683, 33765, 35968, 4126)
REGISTRY_TYPE_ID = (-538272048549998661, -400749426167419993)


def locate(lines, instructions):
    matches = [i for i in range(len(lines) - len(instructions) + 1)
               if lines[i:i + len(instructions)] == instructions]
    if len(matches) != 1:
        raise ValueError('Reviewed instruction sequence is missing or ambiguous')
    return {'first_function_line': matches[0] + 1, 'instructions': instructions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(source) != ORIGINAL_SHA:
        raise SystemExit('Original current core identity differs')
    binary = source.read_bytes()
    ranges = body_ranges(binary)
    segments, table_base, elements = module_data(binary)

    def memory(address, length):
        hits = [s for s in segments if s['address'] <= address
                and address + length <= s['address'] + s['size']]
        if len(hits) != 1:
            raise ValueError('Static memory span does not map uniquely')
        offset = hits[0]['file_start'] + address - hits[0]['address']
        return offset, binary[offset:offset + length]

    database = args.index.resolve(strict=True)
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA
                or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('ecs-event-map-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []; normalized = {}
        with wat.open('rb') as stream:
            for index in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (index,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[index]:
                    raise ValueError('Indexed body does not match original code section')
                stream.seek(row[0]); data = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', data, re.M) != [str(index).encode()]:
                    raise ValueError('Expected exactly one complete selected function')
                (run / f'function-{index}.wat').write_bytes(data)
                normalized[index] = [line.strip() for line in data.decode().splitlines()]
                functions.append({'function_index': index, 'wat_start': row[0], 'wat_end': row[1],
                                  'wat_line': row[2], 'wat_bytes': len(data),
                                  'wat_sha256': hashlib.sha256(data).hexdigest(),
                                  'body_start': row[3], 'body_end': row[4], 'body_bytes': row[5],
                                  'body_sha256': hashlib.sha256(binary[row[3]:row[4]]).hexdigest()})

        registrations = []
        lines = normalized[922]
        for i, line in enumerate(lines):
            if line != 'i32.store offset=8' or i < 4:
                continue
            try:
                address = int(lines[i - 1].split()[1])
                length = int(lines[i - 4].split()[1])
                file_offset, name = memory(address, length)
            except (ValueError, IndexError):
                continue
            if not name.startswith(b'benilla_app::net::'):
                continue
            if lines[i + 6] != 'call 27452':
                raise ValueError('Expected named network-system registration route')
            key = int(lines[i + 3].split()[1])
            vtable = None
            for j in range(i - 1, max(0, i - 100), -1):
                if lines[j] == 'i32.store offset=56':
                    vtable = int(lines[j - 1].split()[1]); break
            if vtable is None:
                raise ValueError('Nearby system vtable constructor is missing')
            table_file, raw = memory(vtable, 48)
            bindings = []
            for offset in (36, 44):
                slot = struct.unpack_from('<I', raw, offset)[0]
                if not table_base <= slot < table_base + len(elements):
                    raise ValueError('Selected callback slot lies outside original element table')
                bindings.append({'vtable_field_offset': offset, 'table_slot': slot,
                                 'function_index': elements[slot - table_base]})
            registrations.append({'initializer_function': 922, 'name_function_line': i + 1,
                                  'name': name.decode(), 'name_address': address,
                                  'name_file_offset': file_offset, 'name_bytes': length,
                                  'registry_key_u16': key, 'vtable_address': vtable,
                                  'vtable_file_offset': table_file, 'callback_bindings': bindings})
        values = [r for r in registrations if r['name'].endswith('::on_object_values')]
        if (len(values) != 1 or values[0]['registry_key_u16'] != 20
                or values[0]['vtable_address'] != 6033116
                or [x['function_index'] for x in values[0]['callback_bindings']] != [53951, 38361]):
            raise ValueError('Observed object-values handler registration differs')
        guards = {
            'event_payload_copy': locate(normalized[37811], [
                'local.get 14', 'local.get 128', 'i64.store offset=40',
                'local.get 110', 'local.get 18', 'i32.const 8', 'i32.add',
                'i32.const 168', 'memory.copy']),
            'event_tag_to_registry_key': locate(normalized[37811], [
                'local.get 1', 'i32.const 16', 'local.get 14', 'i32.const 40',
                'i32.add', 'local.tee 8', 'i64.load', 'local.tee 128', 'i32.wrap_i64',
                'i32.const 2', 'i32.sub', 'local.get 128', 'i64.const 1', 'i64.le_u',
                'select', 'i32.const 65535', 'i32.and', 'local.tee 5', 'i32.store16 offset=304']),
            'handler_descriptor_bounds': locate(normalized[37811], [
                'local.get 3', 'i32.const 8', 'i32.sub', 'i32.load', 'local.tee 54',
                'local.get 2', 'i32.const 4', 'i32.shl', 'local.tee 2', 'i32.add',
                'local.tee 89', 'i32.const 16', 'i32.sub', 'local.set 90']),
            'final_handler_delivery': locate(normalized[37811], [
                'local.get 1', 'i32.const 304', 'i32.add', 'local.tee 7',
                'local.get 8', 'i32.const 176', 'memory.copy', 'local.get 0',
                'local.get 1', 'i32.const 8', 'i32.add', 'local.get 2', 'local.get 4',
                'local.get 7', 'call 25537']),
        }
        for index in (9713, 37811):
            for word in REGISTRY_TYPE_ID:
                if f'i64.const {word}' not in normalized[index]:
                    raise ValueError('Registry resource TypeId comparison differs')
        scheduler_file, scheduler_raw = memory(5999068, 84)
        scheduler_words = struct.unpack('<21I', scheduler_raw)
        if scheduler_words[:3] != (0, 12, 4):
            raise ValueError('Known dispatcher-system vtable layout differs')
        scheduler_bindings = []
        for offset, slot_expected, function_expected in (
                (36, 11737, 78110), (40, 11738, 62585), (44, 11739, 62584)):
            slot = scheduler_words[offset // 4]
            if slot != slot_expected or elements[slot - table_base] != function_expected:
                raise ValueError('Dispatcher-system callback binding differs')
            scheduler_bindings.append({'vtable_field_offset': offset, 'table_slot': slot,
                                       'function_index': function_expected})
            if 'call 37811' not in normalized[function_expected]:
                raise ValueError('Known dispatcher callback does not call the dispatcher')
        scheduler_guards = {
            'constructor_into_system_configs': locate(normalized[922], [
                'local.get 1', 'local.get 7', 'i32.const 5999068', 'call 44683']),
            'configs_handoff': locate(normalized[922], [
                'local.get 0', 'local.get 5', 'call 33765']),
            'retain_system_fat_pointer': locate(normalized[44683], [
                'local.get 0', 'local.get 2', 'i32.store offset=52',
                'local.get 0', 'local.get 1', 'i32.store offset=48']),
            'world_resource_config_application': locate(normalized[33765], [
                'local.get 3', 'i32.const 8', 'i32.add', 'local.get 2',
                'i32.load offset=8', 'call 35968', 'local.get 1', 'i32.const 0',
                'call 4126']),
        }
        report = {
            'version': '0.126.0', 'build': '3e72472a', 'original_sha256': ORIGINAL_SHA,
            'complete_wat_sha256': WAT_SHA, 'complete_functions': functions,
            'named_network_registrations': registrations, 'object_values_registration': values[0],
            'registry_resource_typeid_signed_i64_words': list(REGISTRY_TYPE_ID),
            'observed_dispatcher': {'function': 37811,
                                    'event_stride_bytes': 176, 'handler_stride_bytes': 16,
                                    'key_expression': '(tag_u64 <= 1 ? 16 : wrapping_u32(tag_u64)-2) & 65535',
                                    'object_values_event_tag': 22, 'object_values_registry_key': 20,
                                    'handler_execution_function': 25537, 'instruction_guards': guards},
            'dispatcher_installation': {
                'initializer_function': 922, 'vtable_address': 5999068,
                'vtable_file_offset': scheduler_file, 'vtable_bytes': len(scheduler_raw),
                'vtable_sha256': hashlib.sha256(scheduler_raw).hexdigest(),
                'vtable_raw_hex': scheduler_raw.hex(), 'callback_bindings': scheduler_bindings,
                'config_constructor_function': 44683, 'configuration_handoff_function': 33765,
                'world_resource_lookup_typeid_signed_i64_words': [5332251379967486405, 3138377300317167680],
                'configuration_application_function': 4126, 'instruction_guards': scheduler_guards,
                'qualification': 'Configuration construction/handoff and dispatcher callback bindings are statically observed; schedule label/timing and all Bevy scheduler paths are not inferred here.',
            },
            'target_executed': False, 'network_used': False,
            'limitations': [
                'Named-system constructor association and registration keys are statically observed, not recovered Rust types.',
                'The two vtable fields are callback bindings; other vtable words include metadata and are not all functions.',
                'The tag22-to-key20 relation is derived from original instructions, not numeric coincidence.',
                'Receiver/sender channel association and callback execution semantics require the companion forward/backward investigation.',
                'The script checks reviewed locations; it is not a proof of all dispatcher variants or runtime delivery.',
            ],
        }
        (run / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if sha(source) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise SystemExit('Original changed while extracting event-map evidence')
    print(json.dumps({'run_directory': str(run), 'complete_functions': len(functions),
                      'named_network_registrations': len(registrations),
                      'instruction_guards_passed': len(guards) + len(scheduler_guards),
                      'tag22_registry_key': 20, 'target_executed': False, 'network_used': False}))


if __name__ == '__main__':
    main()
