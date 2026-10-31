#!/usr/bin/env python3
"""Build a host-free micro-WASM containing the unchanged original numeric body.

Only function25242 is copied from the original. Original function indices are
preserved with trap-only placeholders; bounds-panic80330 is also a trap stub.
There are no imports, start function, table, game entrypoint or user-save access.
The result is a research oracle, not a standalone game or a rebuilt core.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 25242
PANIC = 80330
BODY_SHA = 'f9534cbe556e1d07b3c464d9ffff601d7ac45b9615cfb06bac794d406a1eb023'
TABLES = ((5308472, 81305158), (5308508, 81305194), (5308544, 81305230),
          (5308580, 81305266), (5308616, 81305302))


def unsigned(value):
    result = bytearray()
    while True:
        byte = value & 127; value >>= 7
        result.append(byte | (128 if value else 0))
        if not value:
            return bytes(result)


def signed(value):
    result = bytearray()
    while True:
        byte = value & 127; value >>= 7
        done = (value == 0 and not byte & 64) or (value == -1 and byte & 64)
        result.append(byte | (0 if done else 128))
        if done:
            return bytes(result)


def section(kind, payload):
    return bytes((kind,)) + unsigned(len(payload)) + payload


def export(name, kind, index):
    raw = name.encode()
    return unsigned(len(raw)) + raw + bytes((kind,)) + unsigned(index)


def build():
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original) != ORIGINAL_SHA:
        raise ValueError('Original module identity differs')
    binary = original.read_bytes()
    begin, end, length = body_ranges(binary)[TARGET]
    body = binary[begin:end]
    if length != 620 or hashlib.sha256(body).hexdigest() != BODY_SHA:
        raise ValueError('Original numeric function identity differs')
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('upgrade-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    # Types: target(i32,i32,i32)->f32; panic/trap placeholders(i32,i32,i32)->().
    types = b'\x02\x60\x03\x7f\x7f\x7f\x01\x7d\x60\x03\x7f\x7f\x7f\x00'
    count = PANIC + 1
    declarations = bytearray(b'\x01' * count); declarations[TARGET] = 0
    functions = unsigned(count) + declarations
    memory = b'\x01\x01' + unsigned(82) + unsigned(82)  # Fixed5.125MiB, no growth.
    exports = b'\x02' + export('upgrade', 0, TARGET) + export('memory', 2, 0)
    stub = b'\x03\x00\x00\x0b'  # body length3: no locals, unreachable, end.
    target_body = unsigned(len(body)) + body
    code = unsigned(count) + stub * TARGET + target_body + stub * (count - TARGET - 1)
    data = bytearray(unsigned(len(TABLES)))
    tables = []
    for address, file_offset in TABLES:
        raw = binary[file_offset:file_offset + 20]
        data += b'\x00\x41' + signed(address) + b'\x0b' + unsigned(len(raw)) + raw
        tables.append({'linear_memory_address': address, 'original_file_offset': file_offset,
                       'bytes': 20, 'raw_hex': raw.hex(), 'sha256': hashlib.sha256(raw).hexdigest()})
    module = (b'\0asm\1\0\0\0' + section(1, types) + section(3, functions)
              + section(5, memory) + section(7, exports) + section(10, code) + section(11, data))
    target_file = output / 'isolated-upgrade.wasm'; target_file.write_bytes(module)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    provenance = json.loads((ROOT / '.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    if sha(validator) != provenance['tools']['wasm-validate']['sha256']:
        raise ValueError('WABT validator differs from the verified local release')
    subprocess.run([str(validator), str(target_file)], check=True, timeout=30)
    # Independently parse the built code section: original body bytes must match exactly.
    rebuilt = body_ranges_for_oracle(module)
    if rebuilt != body:
        raise ValueError('The isolated target body was changed during assembly')
    manifest = {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': ORIGINAL_SHA,
                'original_function_index': TARGET, 'original_body_start': begin,
                'original_body_end': end, 'original_body_bytes': length,
                'original_body_sha256': BODY_SHA, 'copied_body_byte_identical': True,
                'module_file': target_file.name, 'module_bytes': len(module), 'module_sha256': sha(target_file),
                'defined_functions': count, 'original_function_bodies_copied': 1,
                'trap_placeholder_count': count - 1, 'bounds_panic_stub_function_index': PANIC,
                'imports': [], 'start_function': None, 'table': None,
                'memory_initial_pages': 82, 'memory_maximum_pages': 82,
                'exports': ['upgrade', 'memory'], 'tables': tables,
                'validation': 'verified WABT1.0.42 wasm-validate exit0; target body re-extracted and compared',
                'qualification': 'Valid upgrade inputs execute the original pure numeric body. Bounds failures trap at a replacement stub; original panic behavior is not reconstructed.'}
    if sha(original) != ORIGINAL_SHA:
        raise ValueError('Original changed while building oracle')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return output, manifest


def body_ranges_for_oracle(data):
    """Small independent code-entry reader (the oracle intentionally has no imports)."""
    def read(p):
        value = shift = 0
        while True:
            byte = data[p]; p += 1; value |= (byte & 127) << shift
            if byte < 128:
                return value, p
            shift += 7
    p = 8
    sections = []
    result = None
    while p < len(data):
        kind = data[p]; size, begin = read(p + 1); end = begin + size
        sections.append(kind)
        if kind == 10:
            count, q = read(begin)
            if count != PANIC + 1:
                raise ValueError('Wrong oracle function count')
            for index in range(count):
                length, body_begin = read(q); q = body_begin + length
                if index == TARGET:
                    result = data[body_begin:q]
                elif data[body_begin:q] != b'\x00\x00\x0b':
                    raise ValueError('Non-target body is not a trap-only placeholder')
            if q != end:
                raise ValueError('Oracle code section boundary differs')
        p = end
    if sections != [1, 3, 5, 7, 10, 11] or p != len(data) or result is None:
        raise ValueError('Unexpected oracle sections: imports/start/table are not admitted')
    return result


if __name__ == '__main__':
    directory, record = build()
    print(json.dumps({'run_directory': str(directory), 'module_bytes': record['module_bytes'],
                      'copied_body_byte_identical': True, 'original_game_started': False}))
