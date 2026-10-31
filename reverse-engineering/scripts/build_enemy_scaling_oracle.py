#!/usr/bin/env python3
"""Copy two unchanged pure numeric bodies into a no-import, no-start WASM.

The full game is never instantiated. The two original bodies have only local
reads, f32 constants, add, mul and end: changing their external indices to 0/1
cannot change any internal call/global/memory reference (there are none).
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ((95640, 'elite_growth', '442e45ccda27e06f92ae6e9de53ed80e141a33e4377779c9c06b9184d632e432'),
           (95641, 'normal_growth', 'c351aee9ba131c59f7a97e029e782db6ea97f0dcbebed71556d9d1e940013a18'))


def unsigned(value):
    result = bytearray()
    while True:
        byte = value & 127; value >>= 7
        result.append(byte | (128 if value else 0))
        if not value:
            return bytes(result)


def section(kind, payload):
    return bytes((kind,)) + unsigned(len(payload)) + payload


def pure_instruction_guard(body):
    if body[0] != 0:
        raise ValueError('Unexpected local declarations')
    p = 1; instructions = []
    while p < len(body):
        op = body[p]; p += 1
        if op == 0x20:  # local.get, only two parameters, single-byte index
            if body[p] not in (0, 1):
                raise ValueError('Unexpected local reference')
            instructions.append(['local.get', body[p]]); p += 1
        elif op == 0x43:
            instructions.append(['f32.const', body[p:p + 4].hex()]); p += 4
        elif op in (0x92, 0x94):
            instructions.append(['f32.add' if op == 0x92 else 'f32.mul'])
        elif op == 0x0b and p == len(body):
            instructions.append(['end'])
        else:
            raise ValueError('Non-pure opcode, reference or malformed body')
    return instructions


def copied_bodies(module):
    """Independently parse section and code boundaries of the tiny module."""
    def read(p):
        value = shift = 0
        while True:
            byte = module[p]; p += 1; value |= (byte & 127) << shift
            if byte < 128:
                return value, p
            shift += 7
    p = 8; sections = []; bodies = []
    if module[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Unexpected WASM header')
    while p < len(module):
        kind = module[p]; size, begin = read(p + 1); end = begin + size
        sections.append(kind)
        if kind == 10:
            count, q = read(begin)
            if count != 2:
                raise ValueError('Wrong function count')
            for _ in range(count):
                length, start = read(q); q = start + length
                bodies.append(module[start:q])
            if q != end:
                raise ValueError('Unexpected code boundary')
        p = end
    if sections != [1, 3, 7, 10] or p != len(module) or len(bodies) != 2:
        raise ValueError('Unexpected sections: imports, memory, globals, table and start forbidden')
    return bodies


def build():
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original) != ORIGINAL_SHA:
        raise ValueError('Original module identity differs')
    binary = original.read_bytes(); ranges = body_ranges(binary)
    bodies = []; records = []
    for remapped, (index, name, expected_hash) in enumerate(TARGETS):
        begin, end, length = ranges[index]; body = binary[begin:end]
        if length != 46 or hashlib.sha256(body).hexdigest() != expected_hash:
            raise ValueError('Original function body identity differs')
        instructions = pure_instruction_guard(body)
        bodies.append(body)
        records.append({'original_function_index': index, 'oracle_function_index': remapped,
                        'export': name, 'body_start': begin, 'body_end': end,
                        'body_bytes': length, 'body_sha256': expected_hash,
                        'instructions': instructions})
    types = b'\x01\x60\x02\x7d\x7d\x01\x7d'  # (f32,f32)->f32
    functions = b'\x02\x00\x00'
    exports = bytearray(b'\x02')
    for index, (_, name, _) in enumerate(TARGETS):
        raw = name.encode(); exports += unsigned(len(raw)) + raw + b'\x00' + unsigned(index)
    code = b'\x02' + b''.join(unsigned(len(b)) + b for b in bodies)
    module = b'\0asm\1\0\0\0' + section(1, types) + section(3, functions) + section(7, exports) + section(10, code)
    if copied_bodies(module) != bodies:
        raise ValueError('Copied function bytes differ')
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('enemy-scaling-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    target = output / 'isolated-enemy-scaling.wasm'; target.write_bytes(module)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    provenance = json.loads((ROOT / '.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    if sha(validator) != provenance['tools']['wasm-validate']['sha256']:
        raise ValueError('WABT validator identity differs')
    subprocess.run([str(validator), str(target)], check=True, timeout=30)
    manifest = {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': ORIGINAL_SHA,
                'functions': records, 'copied_bodies_byte_identical': True,
                'module_file': target.name, 'module_bytes': len(module), 'module_sha256': sha(target),
                'defined_functions': 2, 'imports': [], 'start_function': None,
                'memory': None, 'globals': None, 'table': None,
                'exports': [x[1] for x in TARGETS], 'validation': 'verified WABT1.0.42 wasm-validate exit0; code bodies re-extracted and byte-compared'}
    if sha(original) != ORIGINAL_SHA:
        raise ValueError('Original changed while building oracle')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return output, manifest


if __name__ == '__main__':
    directory, manifest = build()
    print(json.dumps({'run_directory': str(directory), 'module_bytes': manifest['module_bytes'],
                      'copied_bodies_byte_identical': True, 'full_game_started': False}))
