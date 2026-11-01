#!/usr/bin/env python3
"""Build a host-free oracle from the pinned official 0.134.0 numeric body.

Only original function25368 executes. Original indices are preserved; every
other body, including bounds-panic80662, becomes unreachable/end. No original
module instantiation, imports, start, table, globals or game bindings occur.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/latest-wenilla_bg.wasm'
SOURCE_SHA = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
SOURCE_BYTES = 90953762
VERSION, BUILD = '0.134.0', '983346a7'
TARGET, PANIC = 25368, 80662
BODY_SHA = '1469599a6ddc00f4a9c958d2c1e0db6d70d2c658fa89a2bfe3587b1d693376bf'
SIDE = ROOT / 'evidence/wasm0134-profile-20261101T001728.222975Z/upgrade-helper-sidecar/upgrade-helper-25368.json'
SIDE_SHA = '03b2194f870792e7db88588e8571a9941e1279fc95b0f62adad1c4c0625b867a'
TABLE_ADDRESSES = (5410584, 5410620, 5410656, 5410692, 5410728)
LOCATION_ADDRESSES = (5410604, 5410640, 5410676, 5410712, 5410748)
VALIDATOR = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
VALIDATOR_SHA = 'a17b421f1cca2c0bba48c6ab3a510f9510db44e505cffd5a48c64bb1f0b5659c'
ARCHIVE = ROOT / '.toolchain/rea-wasm-profile/wabt-1.0.42-macos-arm64.tar.gz'
ARCHIVE_SHA = '3f654779b436c628db3ca4323c51538815f5fbc887a6d5f3bb1c18d36281e240'
MEMORY_PAGES = 83


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def bad(value):
        raise ValueError('Non-JSON numeric constant: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=bad)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    require(strict_json(path.read_text()) == value, 'JSON artifact readback differs')


def unsigned(value):
    require(0 <= value <= 0xffffffff, 'Not a u32')
    result = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        result.append(byte | (128 if value else 0))
        if not value:
            return bytes(result)


def signed(value):
    result = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        done = (value == 0 and not byte & 64) or (value == -1 and byte & 64)
        result.append(byte | (0 if done else 128))
        if done:
            return bytes(result)


class Reader:
    """Bounded reader for source sections; no historical parser/constants used."""
    def __init__(self, data, begin=0, end=None):
        self.data, self.pos, self.end = data, begin, len(data) if end is None else end
        require(0 <= begin <= self.end <= len(data), 'Invalid reader bounds')

    def raw(self, size):
        begin = self.pos
        self.pos += size
        require(size >= 0 and self.pos <= self.end, 'Read exceeds section')
        return self.data[begin:self.pos]

    def byte(self):
        return self.raw(1)[0]

    def uint(self):
        value = 0
        for shift in range(0, 35, 7):
            byte = self.byte()
            value |= (byte & 127) << shift
            if not byte & 128:
                require(value <= 0xffffffff, 'Unsigned LEB exceeds u32')
                return value
        raise ValueError('Invalid unsigned LEB')

    def sint(self):
        value = 0
        for shift in range(0, 35, 7):
            byte = self.byte()
            value |= (byte & 127) << shift
            if not byte & 128:
                if byte & 64:
                    value -= 1 << (shift + 7)
                require(-(1 << 31) <= value < (1 << 31), 'Signed LEB exceeds i32')
                return value
        raise ValueError('Invalid signed LEB')

    def name(self):
        return self.raw(self.uint()).decode('utf8')

    def finished(self):
        require(self.pos == self.end, 'Unconsumed section bytes')


def parse_source(data):
    require(data[:8] == b'\0asm\1\0\0\0', 'Wrong source WASM header')
    top, sections = Reader(data, 8), {}
    while top.pos < top.end:
        kind, size = top.byte(), top.uint()
        begin = top.pos
        top.raw(size)
        if kind:
            require(kind not in sections, 'Duplicate non-custom source section')
            sections[kind] = (begin, top.pos)
    def reader(kind):
        return Reader(data, *sections[kind])
    t, types = reader(1), []
    for _ in range(t.uint()):
        require(t.byte() == 0x60, 'Unsupported non-function type')
        params = t.raw(t.uint())
        results = t.raw(t.uint())
        types.append((params, results))
    t.finished()
    imp, imports = reader(2), []
    for _ in range(imp.uint()):
        module, name, kind = imp.name(), imp.name(), imp.byte()
        require(kind == 0, 'Pinned source expects only function imports')
        imports.append((module, name, imp.uint()))
    imp.finished()
    fun = reader(3)
    declarations = [fun.uint() for _ in range(fun.uint())]
    fun.finished()
    require(len(imports) == 878 and len(declarations) == 175316, 'Source function counts differ')
    require(all(x < len(types) for x in declarations), 'Source function type outside section')
    code, bodies = reader(10), {}
    require(code.uint() == len(declarations), 'Function/code counts differ')
    for index in range(len(imports), len(imports) + len(declarations)):
        length = code.uint()
        begin = code.pos
        code.raw(length)
        bodies[index] = (begin, code.pos)
    code.finished()
    dat, segments = reader(11), []
    for index in range(dat.uint()):
        flags = dat.uint()
        require(flags in (0, 1, 2), 'Unknown data segment flags')
        memory, address = None, None
        if flags != 1:
            memory = 0 if flags == 0 else dat.uint()
            require(dat.byte() == 0x41, 'Data offset is not i32.const')
            address = dat.sint() & 0xffffffff
            require(dat.byte() == 0x0b and memory == 0, 'Unsupported active data expression')
        length = dat.uint()
        begin = dat.pos
        dat.raw(length)
        segments.append({'index': index, 'memory': memory, 'address': address,
                         'file_offset': begin, 'length': length})
    dat.finished()
    return types, imports, declarations, bodies, segments


def source_memory(binary, segments, address, length):
    matches = [s for s in segments if s['address'] is not None
               and s['address'] < address + length and address < s['address'] + s['length']]
    require(len(matches) == 1 and matches[0]['address'] <= address
            and address + length <= matches[0]['address'] + matches[0]['length'],
            'Source memory range is not uniquely backed by non-overlapping active data')
    segment = matches[0]
    offset = segment['file_offset'] + address - segment['address']
    return binary[offset:offset + length], offset, segment['index']


def section(kind, payload):
    return bytes((kind,)) + unsigned(len(payload)) + payload


def export(name, kind, index):
    value = name.encode()
    return unsigned(len(value)) + value + bytes((kind,)) + unsigned(index)


def verify_micro(module, original_body, signatures, tables):
    """Independent inverse reader checks every built body, type and data entry."""
    def number(data, pos, signed_value=False):
        value = shift = 0
        while True:
            require(pos < len(data) and shift <= 28, 'Invalid oracle LEB')
            byte = data[pos]
            pos += 1
            value |= (byte & 127) << shift
            shift += 7
            if byte < 128:
                if signed_value and byte & 64:
                    value -= 1 << shift
                return value, pos
    require(module[:8] == b'\0asm\1\0\0\0', 'Wrong oracle header')
    p, entries = 8, []
    while p < len(module):
        kind = module[p]
        size, p = number(module, p + 1)
        end = p + size
        require(end <= len(module), 'Oracle section exceeds file')
        entries.append((kind, module[p:end]))
        p = end
    require([k for k, _ in entries] == [1, 3, 5, 7, 10, 11], 'Forbidden/duplicate oracle section')
    require(p == len(module), 'Oracle trailing bytes')
    parts = dict(entries)
    data, p = parts[1], 0
    count, p = number(data, p)
    require(count == 2, 'Oracle signature count differs')
    observed = []
    for _ in range(count):
        require(data[p] == 0x60, 'Wrong function type')
        size, p = number(data, p + 1)
        params, p = data[p:p + size], p + size
        size, p = number(data, p)
        results, p = data[p:p + size], p + size
        observed.append((params, results))
    require(p == len(data) and observed == signatures, 'Reparsed signatures differ')
    data = parts[3]
    count, p = number(data, 0)
    require(count == PANIC + 1, 'Oracle declaration count differs')
    for index in range(count):
        type_index, p = number(data, p)
        require(type_index == (0 if index == TARGET else 1), 'Oracle function type differs')
    require(p == len(data), 'Oracle declaration boundary differs')
    require(parts[5] == b'\x01\x01' + unsigned(MEMORY_PAGES) * 2, 'Fixed memory differs')
    require(parts[7] == b'\x02' + export('upgrade', 0, TARGET) + export('memory', 2, 0), 'Exports differ')
    data = parts[10]
    count, p = number(data, 0)
    require(count == PANIC + 1, 'Oracle body count differs')
    for index in range(count):
        size, p = number(data, p)
        body, p = data[p:p + size], p + size
        require(body == (original_body if index == TARGET else b'\x00\x00\x0b'),
                'Reparsed oracle body differs at index ' + str(index))
    require(p == len(data), 'Oracle code boundary differs')
    data = parts[11]
    count, p = number(data, 0)
    require(count == 5, 'Oracle data segment count differs')
    for table in tables:
        require(data[p:p + 2] == b'\x00\x41', 'Non-active oracle data segment')
        address, p = number(data, p + 2, True)
        require(data[p] == 0x0b, 'Oracle data expression differs')
        size, p = number(data, p + 1)
        raw, p = data[p:p + size], p + size
        require(address == table['linear_memory_address'] and size == 20
                and raw.hex() == table['raw_hex'], 'Reparsed oracle data differs')
        require(address + size <= MEMORY_PAGES * 65536, 'Oracle data exceeds memory')
    require(p == len(data), 'Oracle data boundary differs')
    return {'all_function_declarations_reparsed': PANIC + 1,
            'all_function_bodies_reparsed': PANIC + 1, 'trap_bodies_verified': PANIC,
            'function_signatures_reparsed': 2, 'active_data_segments_reparsed': 5,
            'allowed_section_ids': [1, 3, 5, 7, 10, 11]}


def build():
    require(SOURCE.stat().st_size == SOURCE_BYTES and sha(SOURCE) == SOURCE_SHA, 'Official 0.134.0 identity differs')
    require(sha(SIDE) == SIDE_SHA, 'Verified helper sidecar identity differs')
    require(sha(VALIDATOR) == VALIDATOR_SHA and sha(ARCHIVE) == ARCHIVE_SHA, 'Pinned WABT identity differs')
    require(subprocess.check_output([str(VALIDATOR), '--version'], text=True, timeout=10).strip() == '1.0.42', 'WABT version differs')
    side = strict_json(SIDE.read_text())
    binary = SOURCE.read_bytes()
    require(hashlib.sha256(binary).hexdigest() == SOURCE_SHA, 'Source read differs')
    types, imports, declarations, bodies, segments = parse_source(binary)
    begin, end = bodies[TARGET]
    body = binary[begin:end]
    require((begin, end) == (49645485, 49646105) and hashlib.sha256(body).hexdigest() == BODY_SHA, 'New target body differs')
    target_type, panic_type = declarations[TARGET - len(imports)], declarations[PANIC - len(imports)]
    signatures = [types[target_type], types[panic_type]]
    require(target_type == 94 and signatures[0] == (b'\x7f\x7f\x7f', b'\x7d')
            and signatures[1] == (b'\x7f\x7f\x7f', b''), 'Re-read source signatures differ')
    tables = []
    for address, expected in zip(TABLE_ADDRESSES, side['tables']):
        raw, offset, segment = source_memory(binary, segments, address, 20)
        require(expected['linear_memory_address'] == address and expected['raw_hex'] == raw.hex()
                and expected['wasm_file_offset'] == offset, 'Independent source table differs from sidecar')
        tables.append({'linear_memory_address': address, 'original_file_offset': offset,
                       'source_data_segment_index': segment, 'bytes': 20,
                       'raw_hex': raw.hex(), 'sha256': hashlib.sha256(raw).hexdigest()})
    locations = []
    for address, line in zip(LOCATION_ADDRESSES, (202, 204, 211, 214, 217)):
        raw, offset, segment = source_memory(binary, segments, address, 16)
        ptr, length, actual_line, column = struct.unpack('<4I', raw)
        path, path_offset, _ = source_memory(binary, segments, ptr, length)
        require(actual_line == line and path == b'crates\\wenilla-rogue\\src\\game\\abilities.rs', 'Source location differs')
        locations.append({'linear_memory_address': address, 'original_file_offset': offset,
                          'raw_hex': raw.hex(), 'path': path.decode(), 'line': line, 'column': column,
                          'path_linear_memory_address': ptr, 'path_original_file_offset': path_offset})
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('upgrade0134-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    type_payload = b'\x02' + b''.join(b'\x60' + unsigned(len(p)) + p + unsigned(len(r)) + r for p, r in signatures)
    count = PANIC + 1
    functions = bytearray(b'\x01' * count)
    functions[TARGET] = 0
    stub = b'\x03\x00\x00\x0b'
    code = unsigned(count) + stub * TARGET + unsigned(len(body)) + body + stub * (count - TARGET - 1)
    data = unsigned(5) + b''.join(b'\x00\x41' + signed(t['linear_memory_address']) + b'\x0b\x14'
                               + bytes.fromhex(t['raw_hex']) for t in tables)
    module = (b'\0asm\1\0\0\0' + section(1, type_payload)
              + section(3, unsigned(count) + functions)
              + section(5, b'\x01\x01' + unsigned(MEMORY_PAGES) * 2)
              + section(7, b'\x02' + export('upgrade', 0, TARGET) + export('memory', 2, 0))
              + section(10, code) + section(11, data))
    target_file = output / 'isolated-upgrade0134.wasm'
    target_file.write_bytes(module)
    require(target_file.read_bytes() == module, 'Module artifact readback differs')
    reparsed = verify_micro(target_file.read_bytes(), body, signatures, tables)
    with (output / 'validation.stdout.txt').open('w') as out, (output / 'validation.stderr.txt').open('w') as err:
        subprocess.run([str(VALIDATOR), str(target_file)], stdout=out, stderr=err, check=True, timeout=30)
    manifest = {'version': VERSION, 'build': BUILD, 'original_wasm_sha256': SOURCE_SHA,
                'original_wasm_bytes': SOURCE_BYTES, 'original_source_path': str(SOURCE),
                'original_function_import_count': len(imports), 'original_defined_function_count': len(declarations),
                'original_data_segment_count': len(segments), 'original_function_index': TARGET,
                'original_target_type_index': target_type, 'original_panic_type_index': panic_type,
                'source_signatures': [{'parameters_hex': p.hex(), 'results_hex': r.hex()} for p, r in signatures],
                'original_body_start': begin, 'original_body_end': end, 'original_body_bytes': len(body),
                'original_body_sha256': BODY_SHA, 'copied_body_byte_identical': True,
                'module_file': target_file.name, 'module_bytes': len(module), 'module_sha256': sha(target_file),
                'defined_functions': count, 'original_function_bodies_copied': 1, 'trap_placeholder_count': count - 1,
                'bounds_panic_stub_function_index': PANIC, 'imports': [], 'start_function': None,
                'table': None, 'globals': [], 'memory_initial_pages': MEMORY_PAGES, 'memory_maximum_pages': MEMORY_PAGES,
                'exports': ['upgrade', 'memory'], 'tables': tables, 'source_locations': locations,
                'independent_artifact_reparse': reparsed, 'validator_exit_code': 0,
                'tool_identity': {'wabt_version': '1.0.42', 'validator_sha256': VALIDATOR_SHA, 'archive_sha256': ARCHIVE_SHA},
                'static_helper_sidecar': {'path': str(SIDE), 'sha256': SIDE_SHA},
                'qualification': 'Original 0.134.0 numeric body for supported kinds/tiers; invalid-tier panic is a replacement trap, not original panic text/host behavior.'}
    require(sha(SOURCE) == SOURCE_SHA and sha(SIDE) == SIDE_SHA
            and sha(VALIDATOR) == VALIDATOR_SHA and sha(ARCHIVE) == ARCHIVE_SHA, 'Inputs changed during build')
    save(output / 'manifest.json', manifest)
    return output, manifest


if __name__ == '__main__':
    directory, manifest = build()
    print(json.dumps({'run_directory': str(directory), 'version': VERSION, 'module_bytes': manifest['module_bytes'],
                      'copied_body_byte_identical': True, 'original_game_started': False}, allow_nan=False))
