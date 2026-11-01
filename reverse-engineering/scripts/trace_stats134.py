#!/usr/bin/env python3
"""Pin current1513 fields, dispatches, tables and original internal callees.

Static only. The production module does not import this script or read original
files. Full function text comes from a read-only index and checked full WAT;
class/race bytes are independently reconstructed from active WASM data segments.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct
import sys

from build_full134_oracle import ROOT, SOURCE, SOURCE_SHA
from build_upgrade134_oracle import sha
from trace_abilities import reconstruct_memory
from trace_ecs_forward import structural_targets
from wasm_index import body_ranges

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.derived_stats134 import CLASS_HP_ARMOR, RACE_MODIFIERS

PROFILE = ROOT / 'evidence/wasm0134-profile-20261101T001728.222975Z'
WAT_SHA = '6014dab110e40ae279a6450ae15dcc0d84727c31e2da71f18f2cab1f21ec8422'
INDEX_SHA = 'f131b4454ac1a8754f5b0417e4192efbaada6478df737e09490154c71fd340f9'
FUNCTIONS = (1513, 3735, 48065, 65323, 65326, 71888, 106890)
INPUTS = {'class_byte': [360], 'race_byte': [361], 'level': [1520],
          'old_max_hp': [1360], 'current_hp': [1528], 'now': [2344],
          'conditional': [268, 2574], 'passives': [1692, 1696, 8],
          'adjustments': [1668, 1672, 16], 'item_modifiers': [2020, 2024, 8],
          'owned_skills': [172, 176, 8], 'skill_definition_id': [32, 36],
          'timed_definitions': [2044, 2048, 36], 'timed_records': [600, 604, 12],
          'live_effects': [1704, 1708, 32], 'auxiliary_pools': [1532, 1536, 1344, 1348, 768],
          'previous_speed_sequence': [1644, 1640], 'entity_id_i64': [1336],
          'movement_queue_cap_ptr_len': [1872, 1876, 1880], 'field_btree_root_height': [2468, 2472]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index', type=Path, default=PROFILE / 'index.sqlite')
    args = p.parse_args(); index = args.index.resolve(strict=True)
    if sha(SOURCE) != SOURCE_SHA or sha(index) != INDEX_SHA:
        raise ValueError('Current source or index identity differs')
    binary = SOURCE.read_bytes(); ranges = body_ranges(binary)
    memory, segments = reconstruct_memory(binary)
    digest = lambda b: hashlib.sha256(b).hexdigest()
    u32 = lambda p: struct.unpack_from('<I', memory, p)[0]
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('stats0134-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    functions = []; text = {}
    with sqlite3.connect(index.as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if meta.get('original_sha256') != SOURCE_SHA or meta.get('wat_sha256') != WAT_SHA:
            raise ValueError('Index source binding differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise ValueError('Complete current WAT identity differs')
        with wat.open('rb') as stream:
            for idx in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[idx]:
                    raise ValueError('Function code/index bounds differ')
                stream.seek(row[0]); data = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', data, re.M) != [str(idx).encode()]:
                    raise ValueError('Expected one complete function')
                (out / f'function-{idx}.wat').write_bytes(data)
                text[idx] = [line.strip() for line in data.decode().splitlines()]
                functions.append({'function_index': idx, 'wat_start': row[0], 'wat_end': row[1],
                    'wat_line': row[2], 'wat_sha256': digest(data), 'body_start': row[3],
                    'body_end': row[4], 'body_bytes': row[5],
                    'body_sha256': digest(binary[row[3]:row[4]])})
    guards = []
    def guard(sequence, role):
        source = '\n'.join(text[1513]); needle = '\n'.join(sequence)
        if needle not in source: raise ValueError('Reviewed instruction sequence differs: ' + role)
        guards.append({'role': role, 'first_function_line': source[:source.index(needle)].count('\n') + 1,
                       'instructions': sequence})
    for sequence, role in (
        (['local.get 0', 'i32.load8_u offset=360', 'i32.const 2', 'i32.sub'], 'class selector'),
        (['local.get 0', 'i32.load8_u offset=361', 'i32.const 2', 'i32.sub'], 'race selector'),
        (['local.get 0', 'i32.load offset=1520', 'f32.convert_i32_u',
          'f32.const -0x1p+0 (;=-1;)', 'f32.add'], 'level baseline'),
        (['local.get 0', 'local.get 33', 'f32.store offset=1388'], 'XP scalar output'),
        (['local.get 0', 'local.get 29', 'f32.store offset=1384'], 'pickup radius output'),
        (['f32.const 0x1p+0 (;=1;)', 'local.get 24', 'local.get 24', 'local.get 24',
          'f32.ne', 'select', 'local.tee 21', 'f32.const 0x1p+0 (;=1;)',
          'local.get 21', 'f32.const 0x1p+0 (;=1;)', 'f32.lt', 'select'], 'new adjustment cap1'),
        (['local.tee 6', 'i32.load offset=36', 'i32.const 9', 'i32.eq'], 'owned skill ID length'),
        (['local.get 6', 'i32.load offset=32', 'local.tee 6', 'i64.load align=1',
          'i64.const 7956009373824020339'], 'owned soul_link ID pointer'),
        (['local.get 0', 'i32.load offset=1344', 'i32.const 11426', 'i32.eq'], 'conditional pool write'),
        (['local.get 0', 'i64.load offset=1336', 'local.get 3', 'local.get 23',
          'call 48065'], 'original movement packet callee')):
        guard(sequence, role)
    outputs = []
    for number, line in enumerate(text[1513], 1):
        match = re.fullmatch(r'(f32|i32)\.store offset=(\d+)', line)
        if match and 1360 <= int(match[2]) <= 1444:
            outputs.append({'function_line': number, 'store_type': match[1], 'offset': int(match[2]),
                            'instructions': text[1513][max(0, number - 17):number]})
    if len(outputs) != 22 or {x['offset'] for x in outputs} != set(range(1360, 1445, 4)):
        raise ValueError('Derived output store set differs')
    dispatches = []
    for line, count, role in ((530, 12, 'race'), (654, 15, 'passive'),
                              (854, 20, 'adjustment'), (1082, 33, 'item_and_timed')):
        if not text[1513][line - 1].startswith('br_table '): raise ValueError('Dispatch line differs')
        arms = [{'tag': tag, **structural_targets(text[1513], {line: (tag - 1) & 0xffffffff})[line]}
                for tag in range(count)]
        dispatches.append({'role': role, 'function_line': line, 'selector': 'u32(tag-1)', 'arms': arms})
    classes = []
    for key, wanted in CLASS_HP_ARMOR.items():
        address = 5458652 if key == 1 else u32(1595872 + (key - 2) * 4)
        actual = (u32(address + 72), u32(address + 76))
        if actual != wanted: raise ValueError('Independent class table differs')
        classes.append({'selector': key, 'address': address, 'hp_bits': actual[0], 'armor_bits': actual[1],
                        'record_sha256': digest(memory[address:address + 88])})
    races = []
    for key, wanted in RACE_MODIFIERS.items():
        address = 5455348 if key == 1 else u32(1595712 + (key - 2) * 4)
        ptr, count = u32(address + 16), u32(address + 20)
        if count > 12: raise ValueError('Race modifier bound')
        actual = tuple((u32(ptr + 8*i), u32(ptr + 8*i + 4)) for i in range(count))
        if actual != wanted: raise ValueError('Independent race table differs')
        races.append({'selector': key, 'address': address, 'modifier_ptr': ptr, 'modifier_count': count,
                      'modifiers': actual, 'modifier_hex': memory[ptr:ptr + count*8].hex(),
                      'record_sha256': digest(memory[address:address + 44])})
    receipt = {'version': '0.134.0', 'build': '983346a7', 'original_wasm_sha256': SOURCE_SHA,
        'complete_wat_sha256': WAT_SHA, 'index_sha256': INDEX_SHA, 'functions': functions,
        'input_layout': INPUTS, 'derived_outputs': outputs, 'dispatches': dispatches,
        'instruction_guards': guards, 'classes': classes, 'races': races,
        'class_default': 5458652, 'class_lookup': [u32(1595872 + 4*i) for i in range(10)],
        'race_default': 5455348, 'race_lookup': [u32(1595712 + 4*i) for i in range(7)],
        'reconstructed_active_data_bytes': len(memory), 'active_data_segments': len(segments),
        'reconstructed_active_data_sha256': digest(memory),
        'current_numeric_changes_from_prior_model': ['race1 XP-tag8 .1->.2', 'adjustment cap .4->1',
            'new pool1532/1536 clamps plus conditional1348 and768 writes'],
        'accumulator_label_old_to_new_local': {'22':23,'23':24,'24':22,'25':26,'26':27,'27':28,'28':25},
        'source_sha256': {str(path.relative_to(ROOT)): sha(path) for path in
            (Path(__file__), ROOT/'scripts/trace_abilities.py', ROOT/'scripts/trace_ecs_forward.py',
             ROOT/'scripts/wasm_index.py', ROOT/'scripts/core_type_map.py',
             ROOT/'reconstruction/core_spec/derived_stats134.py')},
        'target_executed': False, 'network_used': False, 'user_saves_read': False,
        'limitations': ['Static tables/dispatch/input/write recovery; producer semantics, game integration and UI unproved.',
            'Accumulator names remain prior semantic labels; local mapping is explicit.']}
    if sha(SOURCE) != SOURCE_SHA or sha(index) != INDEX_SHA or sha(wat) != WAT_SHA:
        raise ValueError('Static source changed during extraction')
    (out/'manifest.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'directory':str(out),'functions':len(functions),'derived_outputs':len(outputs),
                      'classes':len(classes),'races':len(races),'target_executed':False}))


if __name__ == '__main__': main()
