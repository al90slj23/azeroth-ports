#!/usr/bin/env python3
"""Read-only Windows package inventory and PE/Rust/web-wrapper evidence.

No target is executed, no tool is installed, and no old native offset is used.
Input and all generated evidence must remain on the RuiRui4TB external volume.
The report separates literal matches from recovered behavior and version identity.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import mmap
from pathlib import Path
import re
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = Path('/Volumes/RuiRui4TB')
SOURCE_PATTERN = re.compile(rb'crates[\\/][A-Za-z0-9_.-]+[\\/]src(?:[\\/][A-Za-z0-9_.-]+){1,10}\.rs')
DEPENDENCY_PATTERN = re.compile(rb'(?:bevy(?:_[a-z_]+)?|wgpu(?:-[a-z_]+)?|winit|mlua(?:-sys)?|luajit|luau|wasmtime|wasmer|rustyscript|deno_core|v8)-[0-9][0-9A-Za-z_.+-]*[\\/]src')
VERSION_PATTERN = re.compile(rb'(?<![0-9.])([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,4})(?![0-9.])')
MARKERS = {
    'rust': [b'/rustc/', b'\\rustc\\', b'library/std/src', b'library\\std\\src',
             b'.cargo/registry/src', b'.cargo\\registry\\src', b'rust_begin_unwind',
             b'crates\\wenilla-rogue\\src', b'crates/wenilla-rogue/src'],
    'web_wrapper': [b'Electron', b'electron.asar', b'app.asar', b'WebView2Loader.dll',
                    b'CreateCoreWebView2Environment', b'ICoreWebView2', b'chrome_elf.dll',
                    b'libcef.dll', b'node.dll', b'Chromium', b'webview2', b'tao::', b'wry::'],
    'native_graphics': [b'wgpu', b'winit', b'D3D12CreateDevice', b'D3D11CreateDevice',
                        b'CreateDXGIFactory', b'vulkan-1.dll', b'opengl32.dll', b'CreateWindowExW'],
    'game_labels': [b'+{p}% damage', b'-{p}% cooldown', b'Reroll', b'AZSMETER', b'AZSBOSSDMG'],
}
CONSTANTS = {
    'upgrade_damage_f32': ('f', [0.18, 0.25, 0.34, 0.46, 0.65]),
    'upgrade_cooldown_f32': ('f', [0.07, 0.10, 0.13, 0.17, 0.23]),
    'upgrade_count_u32': ('I', [1, 1, 1, 2, 2]),
    'upgrade_radius_f32': ('f', [0.12, 0.18, 0.25, 0.35, 0.50]),
    'upgrade_duration_f32': ('f', [0.15, 0.22, 0.30, 0.40, 0.60]),
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def on_external(path):
    return path == EXTERNAL or EXTERNAL in path.parents


def occurrences(data, needle, limit=8):
    offsets, count, start = [], 0, 0
    while True:
        at = data.find(needle, start)
        if at < 0:
            return {'count': count, 'first_file_offsets': offsets, 'offset_limit': limit}
        count += 1
        if len(offsets) < limit:
            offsets.append(at)
        start = at + max(1, len(needle))


def safe_text(raw):
    return ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw)


class PE:
    """Small bounded PE reader; offsets are computed from this input's headers."""
    def __init__(self, data):
        self.data = data
        if len(data) < 64 or data[:2] != b'MZ':
            raise ValueError('DOS header missing')
        self.pe = self.unpack('<I', 0x3c)[0]
        if self.read(self.pe, 4) != b'PE\0\0':
            raise ValueError('PE signature missing')
        machine, section_count, timestamp, _, _, optional_size, characteristics = self.unpack('<HHIIIHH', self.pe + 4)
        self.optional = self.pe + 24
        magic = self.unpack('<H', self.optional)[0]
        if magic not in (0x10b, 0x20b):
            raise ValueError('Unrecognized optional header magic')
        self.bits = 64 if magic == 0x20b else 32
        self.image_base = self.unpack('<Q' if self.bits == 64 else '<I', self.optional + (24 if self.bits == 64 else 28))[0]
        directory_at = self.optional + (112 if self.bits == 64 else 96)
        directory_count = self.unpack('<I', directory_at - 4)[0]
        self.directories = [self.unpack('<II', directory_at + i * 8)
                            for i in range(min(directory_count, 16, max(0, (self.optional + optional_size - directory_at) // 8)))]
        self.sections = []
        for i in range(section_count):
            at = self.optional + optional_size + i * 40
            raw = self.read(at, 40)
            virtual_size, rva, raw_size, raw_offset = struct.unpack_from('<IIII', raw, 8)
            self.sections.append({'name': raw[:8].rstrip(b'\0').decode('ascii', 'replace'),
                                  'rva': rva, 'virtual_size': virtual_size, 'file_offset': raw_offset,
                                  'raw_bytes': raw_size, 'characteristics': hex(struct.unpack_from('<I', raw, 36)[0])})
        self.headers_size = self.unpack('<I', self.optional + 60)[0]
        raw_end = max([self.headers_size] + [s['file_offset'] + s['raw_bytes'] for s in self.sections])
        self.identity = {'format': 'PE32+' if self.bits == 64 else 'PE32', 'machine': hex(machine),
                         'machine_name': {0x8664: 'x86-64', 0x14c: 'x86', 0xaa64: 'ARM64'}.get(machine, 'other'),
                         'coff_timestamp': timestamp, 'timestamp_is_not_version_proof': True,
                         'characteristics': hex(characteristics), 'image_base': hex(self.image_base),
                         'entry_point_rva': hex(self.unpack('<I', self.optional + 16)[0]),
                         'subsystem': self.unpack('<H', self.optional + 68)[0],
                         'sections': self.sections, 'section_raw_end': raw_end,
                         'overlay_bytes': max(0, len(data) - raw_end),
                         'clr_directory_present': bool(self.directory(14)[0])}

    def read(self, at, size):
        if at < 0 or size < 0 or at + size > len(self.data):
            raise ValueError('Read extends beyond input')
        return self.data[at:at + size]

    def unpack(self, pattern, at):
        return struct.unpack(pattern, self.read(at, struct.calcsize(pattern)))

    def directory(self, index):
        return self.directories[index] if index < len(self.directories) else (0, 0)

    def offset(self, rva, size=1):
        if 0 <= rva and rva + size <= self.headers_size:
            return rva
        matches = [s['file_offset'] + rva - s['rva'] for s in self.sections
                   if s['rva'] <= rva and rva + size <= s['rva'] + s['raw_bytes']]
        if len(matches) != 1:
            raise ValueError('RVA lacks one raw-file mapping')
        self.read(matches[0], size)
        return matches[0]

    def location(self, offset):
        result = {'file_offset': offset}
        for s in self.sections:
            if s['file_offset'] <= offset < s['file_offset'] + s['raw_bytes']:
                rva = s['rva'] + offset - s['file_offset']
                result.update({'section': s['name'], 'rva': hex(rva), 'virtual_address': hex(self.image_base + rva)})
                break
        return result

    def cstring(self, at, maximum=1024):
        raw = self.read(at, min(maximum, len(self.data) - at))
        return raw.split(b'\0', 1)[0].decode('ascii', 'replace')

    def imports(self, delay=False):
        rva, size = self.directory(13 if delay else 1)
        if not rva or not size:
            return []
        start = self.offset(rva)
        stride = 32 if delay else 20
        output = []
        for i in range(min(size // stride, 4096)):
            words = self.unpack('<' + 'I' * (stride // 4), start + i * stride)
            if not any(words):
                break
            if delay:
                attributes, name, _, _, thunk, _, _, _ = words
                if not attributes & 1:
                    name -= self.image_base
                    thunk -= self.image_base
            else:
                thunk, _, _, name, first_thunk = words
                thunk = thunk or first_thunk
            entry = {'dll': self.cstring(self.offset(name)), 'symbols': []}
            if thunk:
                at = self.offset(thunk)
                width = self.bits // 8
                for j in range(65536):
                    value = self.unpack('<Q' if width == 8 else '<I', at + j * width)[0]
                    if not value:
                        break
                    if value & (1 << (self.bits - 1)):
                        entry['symbols'].append({'ordinal': value & 0xffff})
                    else:
                        symbol_at = self.offset(value)
                        entry['symbols'].append({'name': self.cstring(symbol_at + 2), 'hint': self.unpack('<H', symbol_at)[0]})
            output.append(entry)
        return output

    def version_resources(self):
        rva, size = self.directory(2)
        if not rva or not size:
            return []
        root = self.offset(rva)
        def directory(relative):
            if relative < 0 or relative + 16 > size:
                raise ValueError('Resource directory outside declared range')
            named, ids = self.unpack('<HH', root + relative + 12)
            if named + ids > 16384 or relative + 16 + (named + ids) * 8 > size:
                raise ValueError('Resource entries outside declared range')
            return [self.unpack('<II', root + relative + 16 + i * 8) for i in range(named + ids)]
        leaves = []
        def walk(relative, path, seen):
            if relative in seen or len(path) > 4:
                raise ValueError('Cyclic/deep resource directory')
            for key, target in directory(relative):
                label = key & 0x7fffffff
                if key & 0x80000000:
                    n = self.unpack('<H', root + label)[0]
                    label = self.read(root + label + 2, n * 2).decode('utf-16-le', 'replace')
                if target & 0x80000000:
                    walk(target & 0x7fffffff, path + [label], seen | {relative})
                else:
                    data_rva, data_size, codepage, _ = self.unpack('<IIII', root + target)
                    at = self.offset(data_rva, data_size)
                    leaves.append({'resource_path': path + [label], 'codepage': codepage,
                                   **self.location(at), 'bytes': data_size,
                                   'version': parse_version(self.read(at, data_size))})
        for key, target in directory(0):
            if key == 16 and target & 0x80000000:
                walk(target & 0x7fffffff, [16], {0})
        return leaves


def parse_version(raw):
    """Decode VS_VERSION_INFO, fixed fields and StringFileInfo blocks."""
    def align(value):
        return (value + 3) & ~3
    blocks = []
    def walk(start, end, depth=0):
        if depth > 8 or start + 6 > end:
            return
        length, value_length, kind = struct.unpack_from('<HHH', raw, start)
        if length < 6 or start + length > end:
            return
        cursor = start + 6
        key_end = cursor
        while key_end + 2 <= start + length and raw[key_end:key_end + 2] != b'\0\0':
            key_end += 2
        key = raw[cursor:key_end].decode('utf-16-le', 'replace')
        value_at = align(key_end + 2)
        value_bytes = value_length * (2 if kind else 1)
        if value_at + value_bytes > start + length:
            return
        value = raw[value_at:value_at + value_bytes]
        block = {'key': key, 'value_type': kind, 'value_bytes': value_bytes}
        if key == 'VS_VERSION_INFO' and len(value) >= 52 and struct.unpack_from('<I', value)[0] == 0xfeef04bd:
            fields = struct.unpack_from('<13I', value)
            def version(ms, ls):
                return '.'.join(str(x) for x in (ms >> 16, ms & 0xffff, ls >> 16, ls & 0xffff))
            block.update({'file_version': version(fields[2], fields[3]), 'product_version': version(fields[4], fields[5]),
                          'file_flags': hex(fields[7]), 'file_os': hex(fields[8]), 'file_type': fields[9]})
        elif kind == 1 and value:
            block['text'] = value.decode('utf-16-le', 'replace').rstrip('\0')
        elif value:
            block['hex'] = value.hex()
        blocks.append(block)
        child = align(value_at + value_bytes)
        while child + 6 <= start + length:
            child_length = struct.unpack_from('<H', raw, child)[0]
            if child_length < 6 or child + child_length > start + length:
                break
            walk(child, child + child_length, depth + 1)
            child = align(child + child_length)
    walk(0, len(raw))
    return blocks


def scan(data, pe, catalogue):
    locate = pe.location if pe else lambda at: {'file_offset': at}
    result = {}
    for category, markers in MARKERS.items():
        result[category] = []
        for marker in markers:
            matches = occurrences(data, marker)
            if matches['count']:
                result[category].append({'literal': marker.decode('ascii'), **matches,
                                         'locations': [locate(at) for at in matches['first_file_offsets']],
                                         'contexts_ascii': [safe_text(data[max(0, at - 60):at + len(marker) + 80])
                                                            for at in matches['first_file_offsets']],
                                         'literal_is_identity_proof': False})
    sources = {}
    for match in SOURCE_PATTERN.finditer(data):
        name = match[0].decode('ascii').replace('\\', '/')
        item = sources.setdefault(name, {'path': name, 'count': 0, 'locations': []})
        item['count'] += 1
        if len(item['locations']) < 8:
            item['locations'].append(locate(match.start()))
    result['rust_source_paths'] = sorted(sources.values(), key=lambda x: x['path'])
    dependencies = {}
    for match in DEPENDENCY_PATTERN.finditer(data):
        name = match[0].decode('ascii').replace('\\', '/')
        item = dependencies.setdefault(name, {'path_literal': name, 'count': 0, 'locations': []})
        item['count'] += 1
        if len(item['locations']) < 3:
            item['locations'].append(locate(match.start()))
    result['rust_dependency_path_literals'] = sorted(dependencies.values(), key=lambda x: x['path_literal'])
    versions = {}
    for match in VERSION_PATTERN.finditer(data):
        name = match[1].decode('ascii')
        item = versions.setdefault(name, {'candidate': name, 'count': 0, 'examples': []})
        item['count'] += 1
        if len(item['examples']) < 3:
            item['examples'].append({**locate(match.start(1)),
                                     'context_ascii': safe_text(data[max(0, match.start() - 60):match.end() + 80])})
    result['version_literal_candidates'] = sorted(versions.values(), key=lambda x: x['candidate'])
    result['version_caveat'] = 'Dotted literals can be dependency/protocol versions; no game version is inferred from them alone.'
    result['wasm_magic_candidates'] = occurrences(data, b'\0asm\1\0\0\0', 32)
    result['wasm_caveat'] = 'Magic matches are candidates only; embedded modules require boundary/section validation.'
    result['constant_sequence_matches'] = []
    for name, (kind, values) in CONSTANTS.items():
        raw = struct.pack('<' + kind * len(values), *values)
        found = occurrences(data, raw)
        if found['count']:
            result['constant_sequence_matches'].append({'name': name, 'hex': raw.hex(), **found,
                                                       'locations': [locate(at) for at in found['first_file_offsets']]})
    if catalogue:
        matches = {}
        for group in ('abilities', 'classes'):
            entries = []
            for entry in catalogue[group]:
                identifier = entry['identifier']
                found = occurrences(data, identifier.encode('utf-8'), 3)
                entries.append({'identifier': identifier, **found,
                                'locations': [locate(at) for at in found['first_file_offsets']]})
            matches[group] = {'reference_count': len(entries), 'literal_presence_count': sum(x['count'] > 0 for x in entries),
                              'entries': entries}
        result['web_baseline_catalogue_literal_matches'] = matches
    result['semantic_caveat'] = 'Literal/constant overlap locates comparison candidates; it does not establish table layout, equal formulas, or equal behavior.'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Already extracted official package directory; never the archive itself')
    parser.add_argument('--output', type=Path, help='New directory under reverse-engineering/evidence on RuiRui4TB')
    parser.add_argument('--wasm', type=Path, help='Optional pinned web baseline; defaults to configured repository baseline if present')
    args = parser.parse_args()
    source = args.directory.resolve(strict=True)
    if not source.is_dir() or not on_external(source):
        parser.error('Input must be an extracted directory on /Volumes/RuiRui4TB')
    run = (args.output or ROOT / 'evidence' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ-official-windows-inventory')).resolve()
    evidence_root = (ROOT / 'evidence').resolve()
    if not on_external(run) or evidence_root not in run.parents or source == run or source in run.parents or run in source.parents:
        parser.error('Output must be a separate new subdirectory of reverse-engineering/evidence on RuiRui4TB')
    if run.exists():
        parser.error('Output already exists; use a fresh evidence directory')
    run.mkdir(parents=True, exist_ok=False)
    target_config = json.loads((ROOT / 'targets.json').read_text())
    catalogue_path = ROOT / 'reports/2026-11-01-abilities.json'
    catalogue = json.loads(catalogue_path.read_text()) if catalogue_path.is_file() else None
    if catalogue and catalogue.get('original_wasm_sha256') != target_config['web_core']['wasm_sha256']:
        raise SystemExit('Catalogue identity differs from configured web baseline')
    inventory, binary_reports = [], []
    for path in sorted(source.rglob('*')):
        relative = str(path.relative_to(source))
        if path.is_symlink():
            inventory.append({'path': relative, 'kind': 'symlink', 'followed': False})
            continue
        if not path.is_file():
            continue
        before = path.stat()
        item = {'path': relative, 'kind': 'file', 'bytes': before.st_size, 'sha256': digest(path)}
        if shutil.which('file'):
            process = subprocess.run(['file', '-b', str(path)], check=False, capture_output=True, text=True, timeout=20)
            item['file_description'] = process.stdout.strip()
            item['file_exit_code'] = process.returncode
        inventory.append(item)
        if not before.st_size:
            continue
        with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
            pe = None
            if data[:2] == b'MZ':
                report = {'path': relative, 'sha256': item['sha256'], 'bytes': before.st_size}
                try:
                    pe = PE(data)
                    report['pe'] = pe.identity
                    for name, action in [('imports', lambda: pe.imports()), ('delay_imports', lambda: pe.imports(True)),
                                         ('version_resources', pe.version_resources)]:
                        try:
                            report[name] = action()
                        except (ValueError, struct.error) as error:
                            report[name + '_error'] = str(error)
                except (ValueError, struct.error) as error:
                    report['pe_error'] = str(error)
                report['static_scan'] = scan(data, pe, catalogue)
                binary_reports.append(report)
            elif path.suffix.lower() in ('.wasm', '.js', '.json', '.html', '.asar') or data[:8] == b'\0asm\1\0\0\0':
                item['web_asset_signature'] = {'wasm_v1_at_start': data[:8] == b'\0asm\1\0\0\0',
                                              'first_16_bytes_hex': data[:16].hex()}
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise SystemExit('Input changed during inventory: ' + relative)
    web_reference = None
    configured = target_config['web_core']
    wasm = (args.wasm or ROOT.parent / configured['repository_path'] / configured['wasm_filename']).resolve()
    if wasm.is_file():
        if not on_external(wasm):
            raise SystemExit('Web baseline must also be on RuiRui4TB')
        wasm_sha = digest(wasm)
        if wasm_sha != configured['wasm_sha256']:
            raise SystemExit('Web reference identity differs from configured baseline; add a separate baseline first')
        with wasm.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
            web_reference = {'version': configured['version'], 'build': configured['build'], 'bytes': len(data),
                             'sha256': wasm_sha, 'static_scan': scan(data, None, None)}
        baseline_paths = {entry['path'] for entry in web_reference['static_scan']['rust_source_paths']}
        for report in binary_reports:
            native_paths = {entry['path'] for entry in report['static_scan']['rust_source_paths']}
            report['web_source_path_overlap'] = {'shared': sorted(native_paths & baseline_paths),
                                                  'only_in_native_scan': sorted(native_paths - baseline_paths),
                                                  'only_in_web_scan': sorted(baseline_paths - native_paths)}
    before_paths = {entry['path'] for entry in inventory if entry['kind'] == 'file'}
    after_paths = {str(path.relative_to(source)) for path in source.rglob('*') if path.is_file() and not path.is_symlink()}
    preserved = before_paths == after_paths and all(digest(source / entry['path']) == entry['sha256']
                                                   for entry in inventory if entry['kind'] == 'file')
    if web_reference:
        preserved = preserved and digest(wasm) == web_reference['sha256']
    wrapper_paths = [entry['path'] for entry in inventory if any(token in entry['path'].lower()
                     for token in ('app.asar', 'electron', 'webview2', 'chrome_elf', 'libcef', 'icudtl.dat', 'snapshot_blob', 'v8_context_snapshot'))]
    summary = {'schema': 'official-windows-static-inventory-v1', 'source_directory': str(source),
               'created_utc': datetime.now(timezone.utc).isoformat(), 'script_sha256': digest(Path(__file__).resolve()),
               'target_executed': False, 'old_native_offsets_used': False, 'originals_preserved': preserved,
               'file_count': len(before_paths), 'total_file_bytes': sum(x.get('bytes', 0) for x in inventory),
               'extensions': dict(Counter(Path(x['path']).suffix.lower() or '<none>' for x in inventory if x['kind'] == 'file')),
               'pe_files': len(binary_reports), 'wrapper_package_path_candidates': wrapper_paths,
               'catalogue_reference': {'path': str(catalogue_path), 'sha256': digest(catalogue_path),
                                       'wasm_sha256': catalogue['original_wasm_sha256']} if catalogue else None,
               'tools_observed': {name: shutil.which(name) for name in ('file', 'bsdtar', '7zz', '7z', 'objdump')},
               'limitations': ['This is static inventory, not decompilation or execution.',
                               'No matching wrapper marker is not proof of absence; compressed/encrypted payloads are not expanded.',
                               'PE resource versions and literal version candidates are observations; game identity requires its own corroborated record.',
                               'String and numeric overlap do not transfer Rust layouts, function addresses, or semantics between targets.']}
    for name, value in [('inventory', inventory), ('pe-reports', binary_reports), ('web-reference', web_reference), ('summary', summary)]:
        (run / (name + '.json')).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'run_directory': str(run), **{key: summary[key] for key in ('file_count', 'pe_files', 'total_file_bytes', 'originals_preserved', 'target_executed')}}))
    if not preserved:
        raise SystemExit('Input identity changed; evidence is incomplete')


if __name__ == '__main__':
    main()
