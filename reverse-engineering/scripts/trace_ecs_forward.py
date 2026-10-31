#!/usr/bin/env python3
"""Retain the original decode -> SessionEvent conversion -> channel-send path.

Static exact-target navigation only. This does not run WASM, contact a server,
or by itself establish the receiver/ECS dispatcher side of the channel.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
FUNCTIONS = (878, 4642, 7001, 1434, 907, 10914, 922, 19385, 37811)


def structural_targets(lines, branches):
    """Resolve selected known br/br_if/br_table arms to exact block ends."""
    frames = []
    targets = {}
    for number, line in enumerate(lines, 1):
        if line.startswith(('block ', 'loop ', 'if ')):
            frames.append({'start_function_line': number, 'header': line})
        elif line in ('end', 'end)') and frames:
            frames.pop()['end_function_line'] = number
        if number not in branches:
            continue
        selector = branches[number]
        if line.startswith('br_table '):
            depths = [int(x) for x in re.findall(r'(\d+) \(;@\d+;\)', line)]
            if not depths:
                raise ValueError('Expected annotated WABT br_table')
            slot = min(selector, len(depths) - 1)
            depth = depths[slot]
        elif line.startswith(('br ', 'br_if ')):
            slot = None
            depth = int(line.split()[1])
        else:
            raise ValueError('Reviewed branch instruction changed')
        if depth >= len(frames):
            raise ValueError('Reviewed branch targets an unsupported function frame')
        targets[number] = {'branch_function_line': number, 'instruction': line,
                           'selector': selector, 'table_slot': slot,
                           'depth': depth, 'target': frames[-1 - depth]}
    if set(targets) != set(branches) or any('end_function_line' not in x['target'] for x in targets.values()):
        raise ValueError('A reviewed target was not fully matched')
    return targets


def guard(lines, first, expected):
    actual = lines[first - 1:first - 1 + len(expected)]
    if actual != expected:
        raise ValueError(f'Reviewed instructions differ at function line {first}')
    return {'first_function_line': first, 'instructions': expected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    wasm = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(wasm) != ORIGINAL_SHA:
        raise SystemExit('Current target identity differs')
    binary = wasm.read_bytes()
    binary_ranges = body_ranges(binary)
    with sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as connection:
        meta = {key: json.loads(value) for key, value in connection.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT identity differs')
        output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('ecs-forward-%Y%m%dT%H%M%S.%fZ')
        output.mkdir(parents=True, exist_ok=False)
        functions = []
        normalized = {}
        with wat.open('rb') as text:
            for index in FUNCTIONS:
                row = connection.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                         'FROM functions WHERE idx=?', (index,)).fetchone()
                if row is None or tuple(row[3:]) != binary_ranges[index]:
                    raise ValueError('Function bounds disagree with original code section')
                text.seek(row[0])
                decoded = text.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', decoded, re.M) != [str(index).encode()]:
                    raise ValueError('Expected one complete selected function')
                (output / f'function-{index}.wat').write_bytes(decoded)
                normalized[index] = [x.strip() for x in decoded.decode().splitlines()]
                functions.append({'function_index': index, 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': row[5], 'body_sha256': hashlib.sha256(binary[row[3]:row[4]]).hexdigest(),
                                  'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(decoded), 'wat_sha256': hashlib.sha256(decoded).hexdigest()})

        guards = {}
        guards[878] = [
            guard(normalized[878], 4816, ['i32.const -2147483641', 'local.set 7', 'br 577 (;@8;)']),
            guard(normalized[878], 84376, ['local.get 0', 'local.get 7', 'i32.store']),
        ]
        guards[4642] = [
            guard(normalized[4642], 335, ['i64.const 2', 'local.set 30', 'br 4 (;@9;)']),
            guard(normalized[4642], 871, ['local.get 3', 'local.get 30', 'i64.store']),
        ]
        guards[907] = [
            guard(normalized[907], 387, ['local.get 1', 'i32.load8_u offset=16', 'local.set 27',
                                        'local.get 3', 'local.get 1', 'i32.load offset=12', 'i32.store offset=24']),
            guard(normalized[907], 1975, ['local.tee 2', 'local.get 67', 'i64.store offset=8',
                                         'local.get 2', 'i64.const 22', 'i64.store']),
            guard(normalized[907], 2038, ['local.tee 2', 'local.get 67', 'i64.store offset=8',
                                         'local.get 2', 'i64.const 22', 'i64.store']),
            guard(normalized[907], 4270, ['local.get 5', 'i32.load offset=8', 'local.get 9',
                                         'i32.const 176', 'i32.mul', 'i32.add', 'i64.const 26', 'i64.store']),
        ]
        guards[1434] = [
            guard(normalized[1434], 27081, ['local.get 4', 'i32.const 624', 'i32.add', 'local.tee 2',
                                          'local.get 4', 'i32.const 424', 'i32.add', 'i32.const 160', 'memory.copy',
                                          'local.get 4', 'i32.load offset=584', 'local.set 5', 'local.get 4',
                                          'i32.const 1888', 'i32.add', 'local.get 2', 'call 907']),
            guard(normalized[1434], 28433, ['local.get 2', 'local.get 8', 'i32.const 176', 'i32.mul',
                                          'i32.add', 'local.set 14']),
            guard(normalized[1434], 28958, ['local.get 6', 'i32.load offset=892', 'local.set 5',
                                          'local.get 4', 'i32.const 424', 'i32.add', 'local.tee 8',
                                          'local.get 4', 'i32.const 1888', 'i32.add', 'i32.const 176', 'memory.copy',
                                          'local.get 4', 'i32.const 624', 'i32.add', 'local.get 5',
                                          'local.get 8', 'call 10914']),
        ]
        guards[1434] += [
            guard(normalized[1434], 27, ['local.get 0', 'local.get 0', 'i64.load', 'i64.store offset=32']),
            guard(normalized[1434], 290, ['local.get 0', 'local.get 0', 'i32.const 32', 'i32.add',
                                         'local.tee 77', 'i32.store offset=288']),
            guard(normalized[1434], 358, ['local.get 0', 'local.get 77', 'i32.store offset=312']),
            guard(normalized[1434], 31716, ['local.get 0', 'i64.load offset=312', 'local.set 147']),
            guard(normalized[1434], 31742, ['local.get 0', 'local.get 147', 'i64.store offset=864']),
            guard(normalized[1434], 996, ['local.get 6', 'local.get 6', 'i32.load offset=520',
                                         'local.tee 3', 'i32.store offset=552']),
            guard(normalized[1434], 25954, ['local.get 6', 'local.get 6', 'i32.load offset=552',
                                           'local.tee 114', 'i32.store offset=872']),
            guard(normalized[1434], 18289, ['local.get 6', 'local.get 114', 'i32.store offset=892']),
        ]
        guards[922] = [
            guard(normalized[922], 885, ['local.get 9', 'local.get 7', 'i32.store offset=4',
                                        'local.get 9', 'i32.const 1', 'i32.store']),
            guard(normalized[922], 761, ['local.get 0', 'local.get 7', 'i32.store offset=12',
                                        'local.get 0', 'i32.const 1', 'i32.store offset=8']),
            guard(normalized[922], 932, ['local.get 0', 'local.get 7', 'i32.store offset=12',
                                        'local.get 0', 'i32.const 1', 'i32.store offset=8']),
            guard(normalized[922], 5782, ['local.get 4', 'i32.load offset=80', 'local.set 11',
                                         'local.get 4', 'i32.load offset=76', 'local.set 13']),
            guard(normalized[922], 6185, ['local.get 4', 'local.get 11', 'i32.store offset=540',
                                         'local.get 4', 'local.get 13', 'i32.store offset=536']),
        ]
        guards[922] += [
            guard(normalized[922], 6200, ['local.get 8', 'local.get 3', 'local.get 5',
                                          'local.get 4', 'i32.const 120', 'i32.add',
                                          'call 24517', 'local.tee 2', 'i32.load8_u offset=32',
                                          'i32.const 1', 'i32.eq', 'if  ;; label = @11',
                                          'local.get 2', 'i32.const 0', 'local.get 4',
                                          'i32.const 536', 'i32.add', 'call 91493']),
            guard(normalized[922], 6220, ['local.get 2', 'i32.load offset=4', 'local.tee 3',
                                          'if  ;; label = @11', 'local.get 2', 'i32.load offset=8',
                                          'local.get 4', 'i32.const 536', 'i32.add',
                                          'local.get 3', 'memory.copy']),
        ]
        guards[37811] = [
            guard(normalized[37811], 149, ['local.get 4', 'i32.load offset=8', 'local.set 7',
                                           'global.get 0', 'i32.const 384', 'i32.sub',
                                           'local.tee 4', 'global.set 0', 'local.get 4',
                                           'local.get 7', 'i32.store offset=8', 'local.get 4',
                                           'i32.const 24', 'i32.add', 'local.tee 7',
                                           'local.get 4', 'i32.const 8', 'i32.add', 'call 19385']),
        ]
        guards[10914] = [guard(normalized[10914], 8,
                              ['local.get 1', 'i32.load offset=4', 'local.set 3'])]
        guards[19385] = [guard(normalized[19385], 8,
                              ['local.get 1', 'i32.load', 'local.tee 1', 'i32.const 4',
                               'i32.add', 'i32.load', 'local.set 3'])]
        receiver_typeid_references = []
        for function in (922, 37811):
            for word in (-7652179191381602884, 8322580366045022567):
                positions = [n + 1 for n, line in enumerate(normalized[function])
                             if line == f'i64.const {word}']
                if not positions:
                    raise ValueError('Receiver resource TypeId comparison is missing')
                receiver_typeid_references.append({'function_index': function,
                                                   'signed_word': word,
                                                   'function_lines': positions})
        branches = {
            878: structural_targets(normalized[878], {4818: 0}),
            907: structural_targets(normalized[907], {309: 5, 700: 0xffffffff}),
            1434: structural_targets(normalized[1434], {19000: 0, 28512: 9}),
        }
        if (branches[878][4818]['target']['end_function_line'] != 84332
                or branches[907][309]['target']['end_function_line'] != 386
                or branches[907][700]['target']['end_function_line'] != 709
                or branches[1434][19000]['target']['end_function_line'] != 27080
                or branches[1434][28512]['target']['end_function_line'] != 28957):
            raise ValueError('Reviewed decode/conversion/send branch targets differ')
        report = {
            'version': '0.126.0', 'build': '3e72472a', 'original_sha256': ORIGINAL_SHA,
            'complete_wat_sha256': WAT_SHA, 'complete_functions': functions,
            'instruction_guards': guards, 'structural_branch_targets': branches,
            'observed_path': [
                'Opcode169 decodes to message discriminant0x80000007 in878.',
                'Wire update-kind0 becomes internal update-record discriminant2 in4642.',
                '1434 converts decoded message using907 after the success branch.',
                '907 iterates update records with stride168 and constructs stride176 tag22 events.',
                'Tag22 stores the original64-bit GUID at+8 and28-byte Fields at+16.',
                'Two temporary event vectors merge before batch-end eventtag26 is appended.',
                '1434 iterates the returned vector with stride176 and sends tag22 unchanged through10914.',
            ],
            'sender_capture': {
                'future_state_base': 'poll param0+344', 'send_field_offset': 892,
                'endpoint_pointer': 'future+32', 'endpoint_flavor': 1,
                'shared_channel_pointer': 'future+36 = constructor922 local7',
                'lineage': ['constructor future+0/+4 endpoint{1,local7}',
                            'first poll copies future+0 i64 to future+32',
                            'future+32 address -> future+288 -> future+312(low32)',
                            'future+312 i64 -> future+864 (=nested_state+520)',
                            'nested_state+520 -> +552 -> local114 -> +892',
                            'nested_state+892 endpoint pointer ->10914'],
            },
            'same_channel_constructor_pair': {
                'constructor_function': 922, 'shared_allocation_local': 7,
                'future_capture': 'future+0 flavor1, future+4 shared local7',
                'session_constructor_output': 'frame4+68; output+8 flavor1, output+12 shared local7',
                'receiver_resource_staging': 'frame4+76/80 -> locals13/11 -> frame4+536/540',
                'receiver_resource_typeid_lo': -7652179191381602884,
                'receiver_resource_typeid_hi': 8322580366045022567,
                'qualification': 'Same constructor allocation and exact captured pointer lineage; not payload-type similarity.',
                'receiver_resource_typeid_references': receiver_typeid_references,
                'receiver_resource_installation': '922 stages endpoint at frame+536/+540, then installs it through24517/91493 or direct storage copy.',
                'receiver_consumption': '37811 retrieves this resource, takes data+8, then passes its address to19385.',
                'endpoint_dereference': '10914 reads sender_handle+4;19385 reads *receiver_handle_address then endpoint+4, reaching the same constructor allocation.',
            },
            'target_executed': False, 'network_used': False,
            'limitations': [
                'Names describe manually reviewed binary behavior, not recovered Rust source.',
                'The receiver-resource insertion/consumption and pointer indirections are guarded here; registered-system execution is covered by the companion dispatcher/backward traces.',
                'Static parsing/conversion/channel send does not prove runtime delivery or UI convergence.',
            ],
        }
        (output / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if sha(wasm) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise SystemExit('An original changed while extracting')
    print(json.dumps({'run_directory': str(output), 'complete_functions': len(functions),
                      'instruction_guards_passed': sum(len(x) for x in guards.values()),
                      'structural_branches_passed': sum(len(x) for x in branches.values()),
                      'target_executed': False, 'network_used': False}))


if __name__ == '__main__':
    main()
