#!/usr/bin/env python3
"""Bounded Ghidra inspection after an interrupted stock REA native session.

Verifies the original and .pdata ranges, imports read-only with -noanalysis,
and decompiles five explicitly selected functions. Does not execute the game.
This is a project-local Ghidra extension, not stock REA native Evidence.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SELECTION = [
    ('damage_label_candidate', 0x145862ab0, 0x145862d03),
    ('cooldown_label_candidate', 0x145862e00, 0x14586305a),
    ('abilities_source_anchor_candidate', 0x1458978c0, 0x145897ac1),
    ('enemy_source_anchor_candidate', 0x145883b70, 0x145884140),
    ('reroll_ui_candidate', 0x14024e290, 0x14025126c),
]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pe_ranges(source):
    data = source.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    if data[pe:pe + 4] != b'PE\0\0':
        raise ValueError('PE signature differs')
    sections, optional_size = struct.unpack_from('<H12xH', data, pe + 6)
    optional = pe + 24
    if struct.unpack_from('<H', data, optional)[0] != 0x20b:
        raise ValueError('PE32+ expected')
    image_base = struct.unpack_from('<Q', data, optional + 24)[0]
    section_table = optional + optional_size
    table = {}
    for index in range(sections):
        offset = section_table + index * 40
        name = data[offset:offset + 8].rstrip(b'\0')
        virtual_size, rva, raw_size, raw = struct.unpack_from('<IIII', data, offset + 8)
        table[name] = (rva, raw, raw_size, virtual_size)
    rva, raw, size, _ = table[b'.pdata']
    ranges = {}
    for index in range(0, size - 11, 12):
        begin, end, unwind = struct.unpack_from('<III', data, raw + index)
        if begin and end:
            ranges[image_base + begin] = (image_base + end, unwind)
    return image_base, table, ranges, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--timeout', type=int, default=480, help='Whole import/script deadline in seconds')
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 1800:
        parser.error('--timeout must be 1..1800 seconds')
    target = json.loads((ROOT / 'targets.json').read_text())['windows_native_reference']
    source = (args.exe or Path(json.loads((ROOT / 'local.sources.json').read_text())['windows_exe'])).resolve(strict=True)
    if source.stat().st_size != target['bytes'] or digest(source) != target['sha256']:
        raise SystemExit('Original native identity differs; refusing to use old offsets')
    image_base, sections, ranges, data = pe_ranges(source)
    selection = []
    for label, start, end in SELECTION:
        if ranges.get(start, (None,))[0] != end:
            raise SystemExit('Selected range does not match original .pdata')
        rva = start - image_base
        mapped = [(raw + rva - section_rva) for section_rva, raw, raw_size, _ in sections.values()
                  if section_rva <= rva and rva + end - start <= section_rva + raw_size]
        if len(mapped) != 1:
            raise SystemExit('Selected range lacks unique raw-file mapping')
        raw = mapped[0]
        selection.append({'label': label, 'start': hex(start), 'end_exclusive': hex(end),
                          'range_source': 'original PE .pdata', 'file_offset': raw,
                          'bytes': end - start, 'sha256': hashlib.sha256(data[raw:raw + end - start]).hexdigest()})
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ-native-focus')
    run.mkdir(parents=True)
    (run / 'selection.json').write_text(json.dumps(selection, indent=2) + '\n')
    def mapped_offset(va, length):
        rva = va - image_base
        offsets = [raw + rva - sr for sr, raw, size, _ in sections.values()
                   if sr <= rva and rva + length <= sr + size]
        if len(offsets) != 1:
            raise ValueError('Constant lacks unique raw-file mapping')
        return offsets[0]
    constants = []
    for name, va, length, kind in [
        ('one', 0x145d4c67c, 4, 'f32'),
        ('minus_one', 0x145d65264, 4, 'f32'),
        ('percent', 0x145d4c7c0, 4, 'f32'),
        ('cooldown_index_1_to_5', 0x146b8ef54, 20, 'f32'),
        ('damage_index_1_to_5', 0x146b8efc0, 20, 'f32'),
        ('healing_label', 0x146b8ef05, 13, 'utf8'),
        ('absorb_label', 0x146b8ef39, 12, 'utf8'),
        ('damage_label', 0x146b8ef45, 12, 'utf8'),
        ('cooldown_label', 0x146b8efb0, 14, 'utf8'),
    ]:
        offset = mapped_offset(va, length)
        raw = data[offset:offset + length]
        value = list(struct.unpack('<' + 'f' * (length // 4), raw)) if kind == 'f32' else raw.decode('utf8')
        constants.append({'name': name, 'address': hex(va), 'file_offset': offset,
                          'bytes': length, 'hex': raw.hex(), 'value': value,
                          'sha256': hashlib.sha256(raw).hexdigest()})
    (run / 'constants.json').write_text(json.dumps(constants, indent=2) + '\n')
    install = json.loads((ROOT / '.toolchain/native-install.json').read_text())
    env = os.environ.copy()
    env.update({key: install[key] for key in ('JAVA_HOME', 'GHIDRA_INSTALL_DIR')})
    env.update({'GHIDRA_HEADLESS_MAXMEM': '4G', 'GHIDRA_HEADLESS_JAVA_OPTIONS': ''})
    (run / 'project').mkdir()
    command = [str(Path(install['GHIDRA_INSTALL_DIR']) / 'support/analyzeHeadless'),
               str(run / 'project'), 'focused-original', '-import', str(source),
               '-readOnly', '-deleteProject', '-noanalysis', '-scriptPath', str(ROOT / 'scripts'),
               '-log', str(run / 'ghidra.log'), '-scriptlog', str(run / 'script.log'),
               '-postScript', 'AzerothFocusedDecompile.java', str(run / 'functions.json'), str(run / 'selection.json')]
    timed_out = False
    script_names = ('decompile_native_focus.py', 'AzerothFocusedDecompile.java')
    script_hashes = {name: digest(ROOT / 'scripts' / name) for name in script_names}
    with (run / 'process.log').open('w') as log:
        child = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            returncode = child.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(child.pid, signal.SIGTERM)
            try:
                returncode = child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                returncode = child.wait()
    preserved = digest(source) == target['sha256']
    function_output = run / 'functions.json'
    functions = json.loads(function_output.read_text()).get('functions', []) if function_output.is_file() else []
    completed = sum(item.get('disassembled') is True and item.get('completed') is True
                    and bool(item.get('pseudocode')) for item in functions)
    warning_pattern = re.compile(r'Control flow encountered bad instruction|overlaps instruction|'
                                 r'Could not find normalized switch variable|truncation of jumptable')
    flow_warning_labels = [item['selection']['label'] for item in functions
                           if warning_pattern.search(item.get('pseudocode', ''))]
    result = {'method': 'project-local-ghidra-noanalysis-selected-pdata-functions',
              'relationship_to_rea': 'Independent fallback, not the stock REA native provider',
              'original_sha256': target['sha256'],
              'original_preserved': preserved, 'target_executed': False, 'automatic_analysis': False,
              'whole_process_timeout_seconds': args.timeout, 'per_function_timeout_seconds': 60,
              'timed_out': timed_out, 'exit_code': returncode,
              'selected_functions': len(selection), 'pseudocode_completed': completed}
    result['pseudocode_with_flow_warning_patterns'] = flow_warning_labels
    result['scripts_sha256'] = script_hashes
    result['scripts_preserved_during_run'] = all(digest(ROOT / 'scripts' / name) == value
                                                for name, value in script_hashes.items())
    result['complete_control_flow_verified'] = False
    (run / 'run-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'run_directory': str(run), **result}))
    if returncode or timed_out or not preserved or completed != len(selection) or not result['scripts_preserved_during_run']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
