#!/usr/bin/env python3
"""Isolate unchanged original35684 in one host-free, bounded scratch micro-WASM.

The full90MB game module is identity-checked and parsed, never instantiated.
No imported function, start, table, data segment or game host is copied.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
INDEX = 35684
BODY_SHA = '31ccd3fd72d9691629a6df855cf68a38be6fc19ca2679165bf2fa0e368a63162'
WAT_SHA = '7edf6871861810b58e006e6207b6e848654bbf5c7ceff677249ad618ef376f4b'
SIDECAR = ROOT / 'evidence/abilities-log1p-helper-20261031T225046.228952Z'
STACK_POINTER = 1024


def unsigned(value):
    result = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        result.append(byte | (128 if value else 0))
        if not value:
            return bytes(result)


def read_leb(data, position, signed=False):
    value = shift = 0
    while position < len(data) and shift <= 28:
        byte = data[position]
        position += 1
        value |= (byte & 127) << shift
        shift += 7
        if byte < 128:
            if signed and byte & 64:
                value -= 1 << shift
            return value, position
    raise ValueError('Invalid bounded i32/u32 LEB')


def section(kind, payload):
    return bytes((kind,)) + unsigned(len(payload)) + payload


def instruction_guard(body):
    """Decode all instructions; reject calls, unknown ops or external references."""
    groups, p = read_leb(body, 0)
    locals_ = []
    for _ in range(groups):
        count, p = read_leb(body, p)
        locals_.append([count, body[p]])
        p += 1
    if locals_ != [[2, 0x7f], [2, 0x7d]]:
        raise ValueError('Original local declarations differ')
    depth = 1
    global_reads = []
    memory = []
    instructions = []
    plain = {0x0f: 'return', 0x1a: 'drop', 0x1b: 'select',
             0x45: 'i32.eqz', 0x49: 'i32.lt_u', 0x4b: 'i32.gt_u',
             0x4c: 'i32.le_s', 0x4d: 'i32.le_u', 0x4f: 'i32.ge_u',
             0x5c: 'f32.ne', 0x6a: 'i32.add', 0x6b: 'i32.sub',
             0x71: 'i32.and', 0x74: 'i32.shl', 0x76: 'i32.shr_u',
             0x92: 'f32.add', 0x93: 'f32.sub', 0x94: 'f32.mul',
             0x95: 'f32.div', 0xb2: 'f32.convert_i32_s',
             0xbc: 'i32.reinterpret_f32', 0xbe: 'f32.reinterpret_i32'}
    while p < len(body):
        opcode = body[p]
        p += 1
        if opcode in plain:
            item = [plain[opcode]]
        elif opcode in (0x02, 0x04):
            if body[p] != 0x40:
                raise ValueError('Unexpected control signature')
            p += 1
            depth += 1
            item = ['block' if opcode == 0x02 else 'if']
        elif opcode == 0x0b:
            depth -= 1
            item = ['end']
            if depth == 0 and p != len(body):
                raise ValueError('Bytes follow final function end')
        elif opcode in (0x0c, 0x0d):
            label, p = read_leb(body, p)
            if label >= depth:
                raise ValueError('Invalid branch depth')
            item = ['br' if opcode == 0x0c else 'br_if', label]
        elif opcode in (0x20, 0x21, 0x22):
            index, p = read_leb(body, p)
            if index > 4:
                raise ValueError('Unexpected local index')
            item = [{0x20: 'local.get', 0x21: 'local.set', 0x22: 'local.tee'}[opcode], index]
        elif opcode == 0x23:
            index, p = read_leb(body, p)
            if index != 0:
                raise ValueError('Unexpected global reference')
            global_reads.append(index)
            item = ['global.get', index]
        elif opcode == 0x41:
            number, p = read_leb(body, p, signed=True)
            item = ['i32.const', number]
        elif opcode == 0x43:
            if p + 4 > len(body):
                raise ValueError('Truncated f32 constant')
            item = ['f32.const.bits', body[p:p + 4].hex()]
            p += 4
        elif opcode in (0x2a, 0x38):
            align, p = read_leb(body, p)
            offset, p = read_leb(body, p)
            if (align, offset) != (2, 12):
                raise ValueError('Unexpected memory addressing')
            name = 'f32.load' if opcode == 0x2a else 'f32.store'
            memory.append([name, align, offset])
            item = [name, align, offset]
        else:
            raise ValueError(f'Forbidden or unknown opcode 0x{opcode:02x}')
        if depth < 0:
            raise ValueError('Unbalanced controls')
        instructions.append(item)
    if depth != 0 or global_reads != [0] or memory != [['f32.store', 2, 12], ['f32.load', 2, 12]]:
        raise ValueError('Unexpected control/global/scratch structure')
    return {'locals': locals_, 'global_reads': global_reads, 'global_writes': [],
            'memory_instructions': memory, 'calls': [], 'instructions': instructions}


def inspect_micro_module(module, expected_body):
    """Independently parse every section and exact code boundary after construction."""
    if module[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Unexpected WASM header')
    p = 8
    sections = []
    bodies = []
    expected = {1: b'\x01\x60\x01\x7d\x01\x7d', 3: b'\x01\x00',
                5: b'\x01\x01\x01\x01',
                6: b'\x01\x7f\x00\x41' + unsigned(STACK_POINTER) + b'\x0b',
                7: b'\x01\x0clog1p_helper\x00\x00'}
    while p < len(module):
        kind = module[p]
        size, begin = read_leb(module, p + 1)
        end = begin + size
        if end > len(module):
            raise ValueError('Section outside micro-module')
        sections.append(kind)
        if kind == 10:
            count, q = read_leb(module, begin)
            if count != 1:
                raise ValueError('Only one original function body permitted')
            length, start = read_leb(module, q)
            q = start + length
            bodies.append(module[start:q])
            if q != end:
                raise ValueError('Code body count/boundary mismatch')
        elif kind not in expected or module[begin:end] != expected[kind]:
            raise ValueError('Unexpected section payload or external facility')
        p = end
    if sections != [1, 3, 5, 6, 7, 10] or bodies != [expected_body] or p != len(module):
        raise ValueError('Micro-module sections/body differ; imports/start/data forbidden')
    return {'section_ids': sections, 'defined_functions': 1, 'imports': [],
            'start_function': None, 'data_segments': [], 'table': None,
            'copied_body_byte_identical': True}


def build():
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original) != ORIGINAL_SHA:
        raise ValueError('Entire original module identity differs')
    binary = original.read_bytes()
    # This hash protects the bytes actually passed to body_ranges, independently
    # of both the preliminary file hash and the final on-disk identity recheck.
    if hashlib.sha256(binary).hexdigest() != ORIGINAL_SHA:
        raise ValueError('Original changed during read')
    begin, end, length = body_ranges(binary)[INDEX]
    body = binary[begin:end]
    if length != 364 or hashlib.sha256(body).hexdigest() != BODY_SHA:
        raise ValueError('Original indexed body identity differs')
    # The complete original and pinned body digest are sufficient to reproduce
    # the oracle on a fresh checkout. An earlier ignored investigation is an
    # optional corroboration, never a required unpublished dependency.
    sidecar_checked = SIDECAR.is_dir()
    if sidecar_checked and (body != (SIDECAR / 'function-35684.body.bin').read_bytes()
                            or sha(SIDECAR / 'function-35684.wat') != WAT_SHA):
        raise ValueError('Existing optional sidecar identity differs')
    decoded = instruction_guard(body)
    payloads = [(1, b'\x01\x60\x01\x7d\x01\x7d'), (3, b'\x01\x00'),
                (5, b'\x01\x01\x01\x01'),
                (6, b'\x01\x7f\x00\x41' + unsigned(STACK_POINTER) + b'\x0b'),
                (7, b'\x01\x0clog1p_helper\x00\x00'),
                (10, b'\x01' + unsigned(len(body)) + body)]
    module = b'\0asm\1\0\0\0' + b''.join(section(kind, payload) for kind, payload in payloads)
    inspection = inspect_micro_module(module, body)
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('radius-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    target = output / 'isolated-radius-helper.wasm'
    target.write_bytes(module)
    # Verify persisted file too, rather than only the construction buffer.
    inspect_micro_module(target.read_bytes(), body)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    provenance = json.loads((ROOT / '.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    if sha(validator) != provenance['tools']['wasm-validate']['sha256']:
        raise ValueError('WABT validator identity differs')
    subprocess.run([str(validator), str(target)], check=True, timeout=30)
    manifest = {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': ORIGINAL_SHA,
                'original_wasm_bytes': len(binary), 'original_function_index': INDEX,
                'oracle_function_index': 0, 'body_start': begin, 'body_end': end,
                'body_bytes': length, 'body_sha256': BODY_SHA,
                'optional_sidecar_checked': sidecar_checked,
                'sidecar_body_matches_indexed_original': True if sidecar_checked else None,
                'sidecar_wat_sha256': WAT_SHA if sidecar_checked else None, 'module_file': target.name,
                'module_bytes': len(module), 'module_sha256': sha(target),
                **inspection, 'memory': {'minimum_pages': 1, 'maximum_pages': 1, 'exported': False},
                'global0': {'type': 'i32', 'mutable': False, 'value': STACK_POINTER, 'exported': False},
                'scratch_address': STACK_POINTER - 16 + 12, 'export': 'log1p_helper',
                'decoded_body': decoded,
                'validation': 'verified WABT1.0.42 wasm-validate exit0; persisted code/sections independently reparsed'}
    if sha(original) != ORIGINAL_SHA:
        raise ValueError('Original changed while building oracle')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return output, manifest


if __name__ == '__main__':
    directory, manifest = build()
    print(json.dumps({'run_directory': str(directory), 'module_bytes': manifest['module_bytes'],
                      'copied_body_byte_identical': True, 'full_game_started': False}))
