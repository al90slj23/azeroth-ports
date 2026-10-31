#!/usr/bin/env python3
"""Recover current original derived-stat inputs, dispatch tables and writes.

Static only: no target execution, user saves or network. Accumulator names are
analysis labels; declaration extraction does not establish every talent rule.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct

from trace_abilities import reconstruct_memory, extract_catalogues
from trace_ecs_forward import structural_targets
from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
FUNCTIONS = (1573, 2017)
DISPATCHES = ((530, 12, 'race_modifiers'), (654, 15, 'passive_records'),
              (854, 20, 'owned_adjustments'), (1082, 33, 'copied_item_and_timed_modifiers'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    index = args.index.resolve(strict=True)
    index_hash = sha(index)
    binary = source.read_bytes()
    if digest(binary) != ORIGINAL_SHA:
        raise SystemExit('Original current core identity differs')
    ranges = body_ranges(binary)
    memory, segments = reconstruct_memory(binary)
    catalogues = extract_catalogues(memory, segments)

    def span(address, length):
        if address < 0 or length < 0 or address + length > len(memory):
            raise ValueError('Static memory span outside initialized profile')
        data = bytes(memory[address:address + length])
        return {'memory_address': address, 'bytes': length, 'sha256': digest(data), 'hex': data.hex()}

    def u32(address):
        return struct.unpack_from('<I', memory, address)[0]

    def string(address):
        p, n = u32(address), u32(address + 4)
        if n > 256:
            raise ValueError('Unexpected static label size')
        return bytes.fromhex(span(p, n)['hex']).decode('utf-8', errors='strict')

    class_lookup = [u32(1577992 + i * 4) for i in range(10)]
    classes = []
    for item in catalogues['classes']:
        address = item['memory_address']
        classes.append({'identifier': item['identifier'],
                        'observed_selector_bytes': [i + 2 for i, p in enumerate(class_lookup) if p == address],
                        'default_for_outside_2_through_11': address == 1714716,
                        'header_word0_uninterpreted_u32': u32(address),
                        'definition_address': address,
                        'base_hp_bits_hex': f'{u32(address + 72):08x}',
                        'base_arm_bits_hex': f'{u32(address + 76):08x}',
                        'word80_uninterpreted_hex': f'{u32(address + 80):08x}',
                        'source': span(address, 88)})
    race_addresses = [1711412] + [u32(1577904 + i * 4) for i in range(7)]
    if race_addresses != [1711412 + 44 * i for i in range(8)]:
        raise ValueError('Observed race-definition order differs')
    races = []
    for i, address in enumerate(race_addresses, 1):
        p, count = u32(address + 16), u32(address + 20)
        if count > 12:
            raise ValueError('Unexpected racial modifier count')
        races.append({'race_byte': i, 'name': string(address), 'display_token': string(address + 8),
                      'active_ability_id': string(address + 24), 'definition_address': address,
                      'modifiers': [{'tag': u32(p + j * 8),
                                     'value_bits_hex': f'{u32(p + j * 8 + 4):08x}'} for j in range(count)],
                      'source': span(address, 44), 'modifier_source': span(p, count * 8)})

    with sqlite3.connect(index.as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True
                or meta.get('direct_call_kinds') != ['call', 'return_call']):
            raise SystemExit('Index identity/coverage profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('derived-stats-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions, lines = [], {}
        with wat.open('rb') as stream:
            for idx in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[idx]:
                    raise ValueError('Original code-body/index ranges differ')
                stream.seek(row[0]); data = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', data, re.M) != [str(idx).encode()]:
                    raise ValueError('Expected exactly one complete function')
                (run / f'function-{idx}.wat').write_bytes(data)
                lines[idx] = [x.strip() for x in data.decode().splitlines()]
                functions.append({'function_index': idx, 'wat_start': row[0], 'wat_end': row[1],
                                  'wat_line': row[2], 'wat_bytes': len(data), 'wat_sha256': digest(data),
                                  'body_start': row[3], 'body_end': row[4], 'body_bytes': row[5],
                                  'body_sha256': digest(binary[row[3]:row[4]])})
        guards = []

        def require(sequence, label):
            text = '\n'.join(lines[1573]); needle = '\n'.join(sequence)
            if needle not in text:
                raise ValueError('Reviewed instruction sequence differs: ' + label)
            guards.append({'label': label, 'first_function_line': text[:text.index(needle)].count('\n') + 1,
                           'instructions': sequence})

        require(['local.get 0', 'i32.load8_u offset=360', 'i32.const 2', 'i32.sub', 'i32.const 255', 'i32.and'], 'class selector')
        require(['local.get 0', 'i32.load8_u offset=361', 'i32.const 2', 'i32.sub'], 'race selector')
        require(['local.get 0', 'i32.load offset=1012', 'local.set 6'], 'base modifier vector')
        require(['local.get 8', 'local.get 6', 'local.get 1', 'memory.copy'], 'copy original modifier vector')
        require(['local.get 0', 'i32.load offset=500', 'local.tee 1'], '12B timed-modifier vector')
        require(['local.tee 2', 'i32.load', 'i32.const 27', 'i32.ne'], 'timed effect tag27 contributes modifier')
        require(['local.get 0', 'i32.load offset=1336', 'f32.convert_i32_u', 'f32.const -0x1p+0 (;=-1;)', 'f32.add'], 'level-derived baseline')
        require(['local.get 3', 'f32.load offset=72', 'local.set 49'], 'class base HP')
        require(['local.get 3', 'f32.load offset=76', 'local.set 22'], 'class base armor')
        require(['local.get 0', 'i32.load offset=1504', 'local.set 1'], '8B passive-vector source')
        require(['local.get 0', 'i32.load offset=1480', 'local.set 1'], '16B owned-adjustment vector')
        require(['local.get 0', 'i32.load offset=1516', 'local.tee 7'], '32B live-effect vector')
        require(['local.get 0', 'local.get 35', 'f32.store offset=1216'], 'area scalar output')
        require(['local.get 0', 'local.get 33', 'f32.store offset=1204'], 'XP scalar output')
        require(['local.get 0', 'f32.const 0x1p+0 (;=1;)', 'local.get 30', 'f32.const 0x1p+0 (;=1;)', 'f32.add', 'f32.div', 'f32.store offset=1184'], 'haste becomes reciprocal cooldown scalar')
        require(['local.get 0', 'local.get 32', 'local.get 26', 'f32.const -0x1p+0 (;=-1;)', 'f32.add', 'f32.add', 'local.get 32', 'local.get 3', 'select', 'f32.store offset=1192'], 'critical overflow feeds critical multiplier')
        dispatches = []
        for line, count, role in DISPATCHES:
            if not lines[1573][line - 1].startswith('br_table '):
                raise ValueError('Reviewed dispatch line differs')
            arms = []
            for tag in range(count):
                selector = (tag - 1) & 0xffffffff
                target = structural_targets(lines[1573], {line: selector})[line]
                first = target['target']['end_function_line'] + 1
                arms.append({'tag': tag, **target, 'following_instructions_preview': lines[1573][first - 1:first + 11]})
            dispatches.append({'role': role, 'branch_function_line': line, 'selector': 'u32(tag-1)', 'arms': arms})
        outputs = []
        for number, line in enumerate(lines[1573], 1):
            match = re.fullmatch(r'(f32|i32)\.store offset=(\d+)', line)
            if match and 1176 <= int(match[2]) <= 1260:
                outputs.append({'function_line': number, 'type': match[1], 'state_offset': int(match[2]),
                                'preceding_instructions': lines[1573][max(0, number - 15):number]})
        result = {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': ORIGINAL_SHA,
                  'complete_wat_sha256': WAT_SHA, 'index_sha256': index_hash,
                  'evidence_directory': str(run.relative_to(ROOT)), 'complete_functions': functions,
                  'classes': classes, 'races': races, 'class_lookup_source': span(1577992, 40),
                  'race_lookup_source': span(1577904, 28), 'dispatches': dispatches,
                  'instruction_guards': guards, 'derived_output_stores': outputs,
                  'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
                      (Path(__file__), ROOT / 'scripts/trace_abilities.py', ROOT / 'scripts/trace_ecs_forward.py', ROOT / 'scripts/wasm_index.py')},
                  'validation': {'complete_functions': len(functions), 'classes': len(classes), 'races': len(races),
                                 'dispatch_tables': len(dispatches), 'resolved_tag_arms': sum(len(x['arms']) for x in dispatches),
                                 'instruction_guards': len(guards), 'derived_output_stores': len(outputs)},
                  'target_executed': False, 'network_used': False, 'user_saves_read': False,
                  'limitations': ['Static input/accumulator/output recovery, not an independent complete stat recalculation model.',
                                  'Dispatch tables use separate tag spaces; shared tag numbers do not imply shared meaning.',
                                  'Instruction previews identify branch destinations, not complete branch semantics.',
                                  'Timed-effect dominance, all talent writers, modifier production and network side effects remain incomplete.']}
        (run / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    if sha(source) != ORIGINAL_SHA or sha(wat) != WAT_SHA or sha(index) != index_hash:
        raise SystemExit('Original or index changed during static extraction')
    print(json.dumps({'evidence_directory': str(run), **result['validation'], 'target_executed': False}))


if __name__ == '__main__':
    main()
