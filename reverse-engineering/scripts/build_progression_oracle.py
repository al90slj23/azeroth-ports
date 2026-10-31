#!/usr/bin/env python3
"""Retain XP static evidence; copy only pure original85387 into micro-WASM.

No original3231/13409 execution, imports, start, memory, globals or table.
The helper body has no function-index references, so remapping to0 is safe.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

from trace_coop import module_data
from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'evidence/wasm-index-20261031T213003.825753Z/index.sqlite'
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
BODY_HASHES = {
    3231: '0b00363c3b7539f785134a2c23528b101183a02dbd61616502a1e6ce8af7a2aa',
    85387: '3f9127d30eefb0c9bad49101460ed45df1f6069e63c42d87e351ffbb67151c36',
    13409: 'b04f3a72d6c2ef9d6f849d3eb6b8a2fbce5d136d5756317c09b9f744c4db4931',
}


def unsigned(value):
    raw = bytearray()
    while True:
        byte = value & 127; value >>= 7
        raw.append(byte | (128 if value else 0))
        if not value:
            return bytes(raw)


def section(kind, payload):
    return bytes((kind,)) + unsigned(len(payload)) + payload


def read_leb(raw, p):
    value = shift = 0
    while p < len(raw) and shift <= 28:
        byte = raw[p]; p += 1; value |= (byte & 127) << shift
        if byte < 128:
            return value, p
        shift += 7
    raise ValueError('Malformed bounded LEB')


def pure_helper_guard(body):
    if body[:3] != b'\x01\x02\x7f':
        raise ValueError('Expected two i32 locals')
    p = 3; instructions = []
    names = {0x0b: 'end', 0x05: 'else', 0x1b: 'select', 0x76: 'i32.shr_u',
             0x71: 'i32.and', 0x4d: 'i32.le_u', 0x6b: 'i32.sub',
             0x75: 'i32.shr_s', 0x49: 'i32.lt_u', 0x92: 'f32.add',
             0x98: 'f32.copysign', 0xbc: 'i32.reinterpret_f32', 0xbe: 'f32.reinterpret_i32'}
    while p < len(body):
        op = body[p]; p += 1
        if op in (0x20, 0x21, 0x22):
            index, p = read_leb(body, p)
            if index > 2:
                raise ValueError('Unexpected local reference')
            instructions.append([{0x20: 'local.get', 0x21: 'local.set', 0x22: 'local.tee'}[op], index])
        elif op == 0x41:
            start = p; _, p = read_leb(body, p)
            instructions.append(['i32.const_leb_hex', body[start:p].hex()])
        elif op == 0x43:
            instructions.append(['f32.const_hex_le', body[p:p + 4].hex()]); p += 4
        elif op == 0x04:
            if body[p] != 0x7d:
                raise ValueError('Expected if(result f32)')
            p += 1; instructions.append(['if', 'f32'])
        elif op in names:
            instructions.append([names[op]])
        else:
            raise ValueError(f'Non-pure or unrecognized helper opcode: {op:x}')
    if p != len(body) or body[-1] != 0x0b:
        raise ValueError('Helper boundary differs')
    return instructions


def copied_body(module):
    p = 8; sections = []; result = None
    if module[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Bad WASM header')
    while p < len(module):
        kind = module[p]; size, begin = read_leb(module, p + 1); end = begin + size
        if end > len(module):
            raise ValueError('Section out of bounds')
        sections.append(kind)
        if kind == 10:
            count, q = read_leb(module, begin)
            length, start = read_leb(module, q)
            if count != 1 or start + length != end:
                raise ValueError('Unexpected code entries')
            result = module[start:end]
        p = end
    if sections != [1, 3, 7, 10] or p != len(module) or result is None:
        raise ValueError('Imports/start/memory/globals/table/data are forbidden')
    return result


def build():
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original) != ORIGINAL_SHA:
        raise ValueError('Original module identity differs')
    binary = original.read_bytes(); ranges = body_ranges(binary)
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('progression-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    with sqlite3.connect(INDEX.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA:
            raise ValueError('Index identity differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise ValueError('Full WAT identity differs')
        records = []; texts = {}
        with wat.open('rb') as stream:
            for index, expected_hash in BODY_HASHES.items():
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?', (index,)).fetchone()
                ws, we, line, begin, end, length = row
                body = binary[begin:end]
                if ranges[index] != (begin, end, length) or hashlib.sha256(body).hexdigest() != expected_hash:
                    raise ValueError('Indexed/original function body differs')
                stream.seek(ws); raw = stream.read(we - ws)
                if not raw.startswith(f'  (func (;{index};)'.encode()):
                    raise ValueError('Indexed WAT boundary differs')
                (output / f'function-{index}.wat').write_bytes(raw)
                texts[index] = raw.decode()
                records.append({'function_index': index, 'wat_start': ws, 'wat_end': we,
                                'wat_line': line, 'wat_sha256': hashlib.sha256(raw).hexdigest(),
                                'body_start': begin, 'body_end': end, 'body_bytes': length,
                                'body_sha256': expected_hash,
                                'original_body_executed': index == 85387})
    guards = []
    def require(index, sequence, role):
        lines = [line.strip() for line in texts[index].splitlines()]
        candidates = [i for i in range(len(lines)) if lines[i:i + len(sequence)] == sequence]
        if not candidates:
            raise ValueError('Static guard missing: ' + role)
        guards.append({'function_index': index, 'role': role,
                       'function_relative_start_lines': [i + 1 for i in candidates],
                       'instructions': sequence})
    require(3231, ['local.get 0', 'local.get 0', 'i32.load offset=1340', 'local.get 1',
                   'i32.add', 'local.tee 4', 'i32.store offset=1340'], 'XP addition wraps at32 bits')
    require(3231, ['local.get 3', 'i32.const 98', 'i32.le_u'], 'unsigned guard limits ordinary level to99')
    require(3231, ['local.get 0', 'local.get 3', 'i32.const 1', 'i32.add', 'local.tee 10',
                   'i32.store offset=1336', 'local.get 0', 'local.get 4', 'local.get 1',
                   'i32.sub', 'i32.store offset=1340', 'local.get 0', 'local.get 0',
                   'i32.load offset=2088', 'i32.const 1', 'i32.add', 'i32.store offset=2088'],
            'level+1 XP-threshold pending+1 are real state stores')
    require(3231, ['local.get 0', 'i32.load offset=1340', 'local.set 4', 'br 1 (;@2;)'],
            'XP reloaded before reentering upgrade loop')
    for index, n, level_local in ((3231, 14, 3), (13409, 28, 1)):
        require(index, ['i32.load offset=1336', f'local.tee {level_local}',
                        f'local.get {level_local}', 'i32.const 0', 'i32.ne',
                        'i32.sub', 'f32.convert_i32_u'], 'unsigned level-minus-nonzero conversion')
        require(index, [f'local.tee {n}', 'f32.const 0x1p+2 (;=4;)', 'f32.mul',
                        'f32.const 0x1.4p+2 (;=5;)', 'f32.add', f'local.get {n}',
                        'f32.const 0x1.666666p-2 (;=0.35;)', 'f32.mul',
                        f'local.get {n}', 'f32.mul', 'f32.add', 'call 85387'],
                'ordered threshold formula shared by XP apply and HUD serializer')
    require(3231, ['local.get 0', 'i32.load offset=2088', 'i32.eqz', 'br_if 0 (;@1;)',
                   'local.get 0', 'i32.load8_u offset=2299', 'i32.const 1', 'i32.ne',
                   'br_if 0 (;@1;)', 'local.get 0', 'i32.load8_u offset=2288',
                   'i32.const 1', 'i32.and', 'br_if 0 (;@1;)'], 'pending phase and open-card guard')
    require(3231, ['local.get 0', 'i32.load8_u offset=2284', 'i32.const 1', 'i32.eq',
                   'if  ;; label = @2', 'local.get 0', 'i32.load8_u offset=2285',
                   'i32.const 1', 'i32.and', 'i32.eqz', 'br_if 1 (;@1;)', 'end',
                   'local.get 0', 'i32.const 0', 'i32.const 1', 'call 2098'], 'conditional ready guard and2098 arguments')
    require(13409, ['i32.const 1340', 'i32.add', 'i64.extend_i32_u', 'i64.const 335007449088',
                    'i64.or', 'i64.store offset=184'], 'serializer carries a typed pointer to real XP field')
    require(13409, ['i32.const 1336', 'i32.add', 'local.set 5'], 'serializer retains the real level field pointer')
    require(13409, ['i32.const 1567017', 'local.get 3', 'i32.const 160', 'i32.add', 'call 32068'],
            'serializer uses the t/ph/lvl/xp/xpn formatting template')
    # Reconstruct only this source string prefix, including data-segment mapping.
    segments, _, _ = module_data(binary)
    address, size = 1567017, 36
    raw = bytearray(size); covered = bytearray(size); fragments = []
    for segment in segments:
        lo = max(address, segment['address']); hi = min(address + size, segment['address'] + segment['size'])
        if lo < hi:
            start = segment['file_start'] + lo - segment['address']
            raw[lo - address:hi - address] = binary[start:start + hi - lo]
            covered[lo - address:hi - address] = b'\x01' * (hi - lo)
            fragments.append({'memory_start': lo, 'bytes': hi - lo, 'file_start': start})
    if not all(covered) or raw.hex() != '02743dc5200000700200043b70683dc0053b6c766c3dc0043b78703dc0053b78706e3dc0':
        raise ValueError('Known lvl/xp/xpn formatting prefix differs')
    (output / 'hud-format-prefix.bin').write_bytes(raw)
    template = {'memory_start': address, 'bytes': size, 'raw_hex': raw.hex(),
                'sha256': hashlib.sha256(raw).hexdigest(), 'file_fragments': fragments,
                'field_order': ['t', 'ph', 'lvl', 'xp', 'xpn']}
    begin, end, _ = ranges[85387]; body = binary[begin:end]
    instructions = pure_helper_guard(body)
    name = b'round85387'
    module = (b'\0asm\1\0\0\0' + section(1, b'\x01\x60\x01\x7d\x01\x7d')
              + section(3, b'\x01\x00') + section(7, b'\x01' + unsigned(len(name)) + name + b'\x00\x00')
              + section(10, b'\x01' + unsigned(len(body)) + body))
    if copied_body(module) != body:
        raise ValueError('Copied body bytes differ')
    target = output / 'isolated-progression-round.wasm'; target.write_bytes(module)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    provenance = json.loads((ROOT / '.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    if sha(validator) != provenance['tools']['wasm-validate']['sha256']:
        raise ValueError('WABT validator identity differs')
    subprocess.run([str(validator), str(target)], check=True, timeout=30)
    if sha(original) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise ValueError('Original/decoded inputs changed during extraction')
    manifest = {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': ORIGINAL_SHA,
                'complete_wat_sha256': WAT_SHA, 'static_functions': records,
                'original_function_index': 85387, 'oracle_function_index': 0,
                'body_sha256': BODY_HASHES[85387], 'copied_body_byte_identical': True,
                'pure_helper_instructions': instructions, 'static_guards': guards,
                'hud_format_prefix': template,
                'module_file': target.name, 'module_sha256': sha(target), 'module_bytes': len(module),
                'sections': [1, 3, 7, 10], 'imports': [], 'start_function': None,
                'memory': None, 'globals': None, 'table': None, 'exports': ['round85387'],
                'validator_sha256': sha(validator), 'validation': 'WABT1.0.42 exit0; copied body re-extracted and compared',
                'original3231_executed': False, 'original13409_executed': False}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    return output, manifest


if __name__ == '__main__':
    directory, manifest = build()
    print(json.dumps({'run_directory': str(directory), 'module_bytes': manifest['module_bytes'],
                      'copied_body_byte_identical': True, 'full_game_started': False}))
