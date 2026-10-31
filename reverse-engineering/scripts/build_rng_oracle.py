#!/usr/bin/env python3
"""Copy unchanged32475 into a bounded no-host micro-WASM at its original index.

All other bodies are trap-only placeholders, including panic121709. Invalid
input observations stop at that replacement trap; original panic is not run.
95651 is retained as static evidence only: its entropy/allocation path is not
safe or necessary for this isolated sampler. The full game is never instantiated.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
TARGET, PANIC = 32475, 121709
BODY_SHA = '479e1d7542e72a4768f5148d6f2fba741286751e87095bbd90669007e6a2b473'
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
INDEX = ROOT / 'evidence/wasm-index-20261031T213003.825753Z/index.sqlite'
INDEX_SHA = '0716743732ad8756c81167b27712456a944c07420146e142ba2d88c7168b1e8e'
BODY_WAT_SHA = '2952b56645bb58dddeee8189ea53f74d60cd4e7265771486950ecebf99c42553'
INIT_BODY_SHA = '76e3f6aeb52f1f69e838ad154ec6f758167015115fb75f947745c042df415a6e'


def unsigned(value):
    result = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        result.append(byte | (128 if value else 0))
        if not value:
            return bytes(result)


def leb(data, position, signed=False):
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
    raise ValueError('Invalid bounded LEB')


def section(kind, payload):
    return bytes((kind,)) + unsigned(len(payload)) + payload


def export(name, kind, index):
    raw = name.encode()
    return unsigned(len(raw)) + raw + bytes((kind,)) + unsigned(index)


def instruction_guard(body):
    """Decode the complete pinned body; enumerate all external-state operations."""
    groups, p = leb(body, 0)
    locals_ = []
    for _ in range(groups):
        count, p = leb(body, p)
        locals_.append([count, body[p]])
        p += 1
    if locals_ != [[8, 0x7f], [2, 0x7d]]:
        raise ValueError('Unexpected local declarations')
    depth, calls, memory, decoded = 1, [], [], []
    plain = {0x00: 'unreachable', 0x0f: 'return', 0x45: 'i32.eqz',
             0x4b: 'i32.gt_u', 0x4d: 'i32.le_u', 0x4f: 'i32.ge_u',
             0x5d: 'f32.lt', 0x5e: 'f32.gt', 0x6a: 'i32.add', 0x6b: 'i32.sub',
             0x71: 'i32.and', 0x72: 'i32.or', 0x73: 'i32.xor',
             0x74: 'i32.shl', 0x76: 'i32.shr_u', 0x77: 'i32.rotl',
             0x92: 'f32.add', 0x93: 'f32.sub', 0x94: 'f32.mul',
             0xbc: 'i32.reinterpret_f32', 0xbe: 'f32.reinterpret_i32', 0x05: 'else'}
    while p < len(body):
        op = body[p]
        p += 1
        if op in plain:
            item = [plain[op]]
        elif op in (0x02, 0x03, 0x04):
            if body[p] != 0x40:
                raise ValueError('Unexpected control type')
            p += 1
            depth += 1
            item = [{2: 'block', 3: 'loop', 4: 'if'}[op]]
        elif op == 0x0b:
            depth -= 1
            item = ['end']
            if depth == 0 and p != len(body):
                raise ValueError('Bytes after function end')
        elif op in (0x0c, 0x0d):
            label, p = leb(body, p)
            if label >= depth:
                raise ValueError('Invalid branch depth')
            item = ['br' if op == 0x0c else 'br_if', label]
        elif op in (0x20, 0x21, 0x22):
            index, p = leb(body, p)
            if index > 12:
                raise ValueError('Unexpected local')
            item = [{0x20: 'local.get', 0x21: 'local.set', 0x22: 'local.tee'}[op], index]
        elif op == 0x10:
            index, p = leb(body, p)
            calls.append(index)
            item = ['call', index]
        elif op == 0x41:
            value, p = leb(body, p, signed=True)
            item = ['i32.const', value]
        elif op == 0x43:
            item = ['f32.const.bits', body[p:p + 4].hex()]
            p += 4
        elif op in (0x28, 0x36):
            align, p = leb(body, p)
            offset, p = leb(body, p)
            if align != 2 or offset not in (0, 4, 8, 12):
                raise ValueError('Unexpected memory address')
            item = ['i32.load' if op == 0x28 else 'i32.store', align, offset]
            memory.append(item)
        else:
            raise ValueError(f'Unexpected or forbidden opcode0x{op:02x}')
        decoded.append(item)
    if depth != 0 or calls != [PANIC, PANIC] or len(memory) != 8:
        raise ValueError('Unexpected control, calls or memory')
    if [x[0] for x in memory] != ['i32.load'] * 4 + ['i32.store'] * 4:
        raise ValueError('Expected four loads before any four stores')
    return {'locals': locals_, 'calls': calls, 'memory_instructions': memory,
            'global_reads': [], 'global_writes': [], 'decoded_instructions': decoded}


def payloads(body):
    count = PANIC + 1
    declarations = bytearray(b'\x01' * count)
    declarations[TARGET] = 0
    # Target(i32,f32,f32)->f32; panic/placeholders(i32,i32,i32)->().
    types = b'\x02\x60\x03\x7f\x7d\x7d\x01\x7d\x60\x03\x7f\x7f\x7f\x00'
    stub = b'\x03\x00\x00\x0b'
    code = unsigned(count) + stub * TARGET + unsigned(len(body)) + body + stub * (count - TARGET - 1)
    return {1: types, 3: unsigned(count) + declarations, 5: b'\x01\x01\x01\x01',
            7: b'\x02' + export('range', 0, TARGET) + export('memory', 2, 0), 10: code}


def inspect(module, body):
    """Reparse every section and every body, accepting no other executable code."""
    if module[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Unexpected module header')
    expected = payloads(body)
    p, seen = 8, []
    while p < len(module):
        kind = module[p]
        size, begin = leb(module, p + 1)
        end = begin + size
        seen.append(kind)
        if end > len(module) or kind not in expected:
            raise ValueError('Unexpected section or bounds')
        if kind == 10:
            count, q = leb(module, begin)
            if count != PANIC + 1:
                raise ValueError('Wrong function count')
            for idx in range(count):
                length, start = leb(module, q)
                q = start + length
                if q > end or module[start:q] != (body if idx == TARGET else b'\x00\x00\x0b'):
                    raise ValueError('Original body differs or placeholder contains code')
            if q != end:
                raise ValueError('Code boundary differs')
        elif module[begin:end] != expected[kind]:
            raise ValueError('Section payload differs')
        p = end
    if seen != [1, 3, 5, 7, 10] or p != len(module):
        raise ValueError('Forbidden or missing section')
    return {'section_ids': seen, 'original_body_byte_identical': True,
            'original_function_index_preserved': True, 'imports': [], 'start': None,
            'table': None, 'globals': [], 'data_segments': [],
            'defined_functions': PANIC + 1, 'original_body_count': 1,
            'trap_placeholder_count': PANIC, 'panic_trap_index': PANIC,
            'memory': {'minimum_pages': 1, 'maximum_pages': 1},
            'exports': ['range:function', 'memory:memory']}


def build():
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original) != ORIGINAL_SHA or sha(INDEX) != INDEX_SHA:
        raise ValueError('Original or read-only index identity differs')
    binary = original.read_bytes()
    if hashlib.sha256(binary).hexdigest() != ORIGINAL_SHA:
        raise ValueError('Original changed during read')
    con = sqlite3.connect(f'file:{INDEX.resolve()}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    meta = {r[0]: json.loads(r[1]) for r in con.execute('select key,value from meta')}
    wat = Path(meta['wat_path'])
    if meta['original_sha256'] != ORIGINAL_SHA or meta['wat_sha256'] != WAT_SHA or sha(wat) != WAT_SHA:
        raise ValueError('Full WAT identity differs')
    ranges = body_ranges(binary)
    static = []
    for idx, digest in ((TARGET, BODY_SHA), (95651, INIT_BODY_SHA)):
        row = dict(con.execute('select * from functions where idx=?', (idx,)).fetchone())
        begin, end, length = ranges[idx]
        if (begin, end, length) != (row['body_start'], row['body_end'], row['body_bytes']):
            raise ValueError('Index and original code boundaries differ')
        body = binary[begin:end]
        with wat.open('rb') as stream:
            stream.seek(row['wat_start'])
            text = stream.read(row['wat_end'] - row['wat_start'])
        if hashlib.sha256(body).hexdigest() != digest:
            raise ValueError('Pinned body identity differs')
        if idx == TARGET and hashlib.sha256(text).hexdigest() != BODY_WAT_SHA:
            raise ValueError('Sampler WAT identity differs')
        row.update(body_sha256=digest, wat_sha256=hashlib.sha256(text).hexdigest(),
                   calls=[dict(r) for r in con.execute('select * from calls where caller=?', (idx,))])
        static.append((row, body, text))
    con.close()
    body = static[0][1]
    decoded = instruction_guard(body)
    module = b'\0asm\1\0\0\0' + b''.join(section(k, p) for k, p in payloads(body).items())
    inspection = inspect(module, body)
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('rng-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    target = output / 'isolated-rng.wasm'
    target.write_bytes(module)
    inspect(target.read_bytes(), body)
    for row, raw, text in static:
        (output / f"function-{row['idx']}.body.bin").write_bytes(raw)
        (output / f"function-{row['idx']}.wat").write_bytes(text)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    provenance = json.loads((ROOT / '.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    validator_sha = sha(validator)
    if validator_sha != provenance['tools']['wasm-validate']['sha256']:
        raise ValueError('WABT validator identity differs')
    subprocess.run([str(validator), str(target)], check=True, timeout=30)
    manifest = {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': ORIGINAL_SHA,
                'original_wasm_bytes': len(binary), 'full_wat_sha256': WAT_SHA,
                'index_sha256': INDEX_SHA, 'index': str(INDEX.relative_to(ROOT)),
                'original_function_index': TARGET, 'original_body_sha256': BODY_SHA,
                'functions': [x[0] for x in static], 'initializer95651_static_only': True,
                'module_file': target.name, 'module_bytes': len(module), 'module_sha256': sha(target),
                'validator_sha256': validator_sha, 'validator_version': 'WABT1.0.42',
                'decoded_body': decoded, **inspection,
                'qualification': 'Valid ranges execute unchanged32475. Invalid ranges stop at replacement panic trap121709; original panic/initializer/game are not executed.'}
    if sha(original) != ORIGINAL_SHA or sha(wat) != WAT_SHA or sha(INDEX) != INDEX_SHA:
        raise ValueError('Read-only source changed during extraction')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    return output, manifest


if __name__ == '__main__':
    output, manifest = build()
    print(json.dumps({'run_directory': str(output), 'module_bytes': manifest['module_bytes'],
                      'original_body_byte_identical': True, 'full_game_started': False}, allow_nan=False))
