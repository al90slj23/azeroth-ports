#!/usr/bin/env python3
"""SHA-bound Windows 0.134.0 PE scan and bounded, read-only Ghidra decompilation.

Never executes the target. All generated files, JVM temporary files, Ghidra
settings and cache are placed on the same external volume as this repository.
No old native function address is imported. The only switch override is derived
from this input's exact dispatch bytes and five independently mapped i32 entries.
"""
import argparse
import bisect
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
EXTERNAL = Path('/Volumes/RuiRui4TB')
SHA256 = 'ed7dc687778ef7a613531f1eb6e25766fe06a63552115ebbd024fdede7d1a3f6'
SIZE = 147793408
DEFAULT_EXE = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/windows-0.134.0/AzerothSurvivors.exe'
TABLES = {
    'damage': ('f', [.18, .25, .34, .46, .65]),
    'cooldown': ('f', [.07, .10, .13, .17, .23]),
    'count': ('I', [1, 1, 1, 2, 2]),
    'radius': ('f', [.12, .18, .25, .35, .50]),
    'duration': ('f', [.15, .22, .30, .40, .60]),
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


class PE:
    def __init__(self, data):
        self.data = data
        pe = struct.unpack_from('<I', data, 0x3c)[0]
        if data[:2] != b'MZ' or data[pe:pe + 4] != b'PE\0\0':
            raise ValueError('Invalid PE signature')
        machine, count = struct.unpack_from('<HH', data, pe + 4)
        optional_size = struct.unpack_from('<H', data, pe + 20)[0]
        optional = pe + 24
        if machine != 0x8664 or struct.unpack_from('<H', data, optional)[0] != 0x20b:
            raise ValueError('Expected x86-64 PE32+')
        self.base = struct.unpack_from('<Q', data, optional + 24)[0]
        self.sections = {}
        for index in range(count):
            at = optional + optional_size + 40 * index
            name = data[at:at + 8].rstrip(b'\0').decode('ascii')
            virtual_size, rva, size, raw = struct.unpack_from('<IIII', data, at + 8)
            if raw + size > len(data):
                raise ValueError('Section outside input')
            self.sections[name] = dict(rva=rva, file_offset=raw, raw_bytes=size, virtual_bytes=virtual_size)
        p = self.sections['.pdata']
        self.ranges = []
        for at in range(p['file_offset'], p['file_offset'] + p['virtual_bytes'] - 11, 12):
            begin, end, unwind = struct.unpack_from('<III', data, at)
            if begin and begin < end:
                self.ranges.append((self.base + begin, self.base + end, unwind))
        self.ranges.sort()
        self.starts = [r[0] for r in self.ranges]

    def offset(self, va, length=1):
        rva = va - self.base
        offsets = [s['file_offset'] + rva - s['rva'] for s in self.sections.values()
                   if s['rva'] <= rva and rva + length <= s['rva'] + s['raw_bytes']]
        if len(offsets) != 1:
            raise ValueError('VA lacks unique raw mapping')
        return offsets[0]

    def containing(self, va):
        index = bisect.bisect_right(self.starts, va) - 1
        return self.ranges[index] if index >= 0 and va < self.ranges[index][1] else None


def scan(pe):
    data = pe.data
    rdata = pe.sections['.rdata']
    constants, targets = [], {}
    for name, (fmt, values) in TABLES.items():
        raw = struct.pack('<' + fmt * len(values), *values)
        at = data.find(raw, rdata['file_offset'], rdata['file_offset'] + rdata['raw_bytes'])
        while at >= 0:
            va = pe.base + rdata['rva'] + at - rdata['file_offset']
            targets[va] = name
            constants.append(dict(name=name, address=hex(va), file_offset=at, bytes=len(raw),
                                  hex=raw.hex(), value=list(struct.unpack('<' + fmt * 5, raw)),
                                  sha256=hashlib.sha256(raw).hexdigest()))
            at = data.find(raw, at + 1, rdata['file_offset'] + rdata['raw_bytes'])
    text = pe.sections['.text']
    hits, groups = [], {}
    for prefix in (b'\x48\x8d', b'\x4c\x8d'):
        at = data.find(prefix, text['file_offset'], text['file_offset'] + text['raw_bytes'])
        while at >= 0:
            if data[at + 2] & 0xc7 == 5:
                va = pe.base + text['rva'] + at - text['file_offset']
                destination = va + 7 + struct.unpack_from('<i', data, at + 3)[0]
                for adjustment in (-4, 0, 4):
                    table = destination + adjustment
                    if table not in targets:
                        continue
                    function = pe.containing(va)
                    hit = dict(instruction=hex(va), file_offset=at, raw_bytes=data[at:at + 7].hex(),
                               destination=hex(destination), table=targets[table], table_base=hex(table),
                               base_adjustment=-adjustment, instruction_boundary_verified=False,
                               function_start=hex(function[0]) if function else None,
                               function_end_exclusive=hex(function[1]) if function else None)
                    hits.append(hit)
                    if function and function[1] - function[0] <= 32768:
                        groups.setdefault(function[:2], []).append(hit)
            at = data.find(prefix, at + 1, text['file_offset'] + text['raw_bytes'])
    # Multi-table consumers are stronger candidates than common integer literals.
    eligible = [(pair, references) for pair, references in groups.items()
                if len({h['table'] for h in references}) >= 2]
    eligible.sort(key=lambda item: (-len({h['table'] for h in item[1]}), item[0][1] - item[0][0]))
    selection = []
    for (start, end), references in eligible[:4]:
        at = pe.offset(start, end - start)
        raw = data[at:at + end - start]
        selected = dict(label='upgrade_' + '_'.join(sorted({h['table'] for h in references})) + '_candidate',
                        start=hex(start), end_exclusive=hex(end), bytes=end - start,
                        range_source='this input PE .pdata', file_offset=at,
                        sha256=hashlib.sha256(raw).hexdigest(), table_references=references,
                        additional_entry_points=[], verified_switches=[])
        # Exact bounded dispatch: sub rsp,28; movzx eax,dl; lea rdx,[rip+disp32];
        # movsxd r9,[rdx+rax*4]; add r9,rdx; jmp r9. Decode five i32 entries.
        if (raw[:7] == bytes.fromhex('4883ec280fb6c2') and raw[7:10] == bytes.fromhex('488d15')
                and raw[14:24] == bytes.fromhex('4c630c824901d141ffe1')):
            table = start + 14 + struct.unpack_from('<i', raw, 10)[0]
            table_at = pe.offset(table, 20)
            entries = [table + x for x in struct.unpack_from('<5i', data, table_at)]
            if len(set(entries)) != 5 or not all(start <= x < end for x in entries):
                raise ValueError('Expected five unique in-range switch arms')
            selected['additional_entry_points'] = [hex(x) for x in entries]
            selected['verified_switches'] = [dict(site=hex(start + 21), table_address=hex(table),
                                                file_offset=table_at, bytes=data[table_at:table_at + 20].hex(),
                                                index_assumption='valid five-variant branch discriminant 0..4',
                                                targets=[hex(x) for x in entries])]
        selection.append(selected)
    return constants, hits, selection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=DEFAULT_EXE)
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--scan-only', action='store_true')
    args = parser.parse_args()
    if not 180 <= args.timeout <= 300:
        parser.error('--timeout must be 180..300 seconds')
    source = args.exe.resolve(strict=True)
    if EXTERNAL not in source.parents or EXTERNAL not in ROOT.parents:
        raise SystemExit('Input/output must be on the external 4TB volume')
    if source.stat().st_size != SIZE or digest(source) != SHA256:
        raise SystemExit('Windows 0.134.0 identity differs; refusing analysis')
    pe = PE(source.read_bytes())
    constants, hits, selection = scan(pe)
    if len(selection) < 2:
        raise SystemExit('Fewer than two multi-table .pdata candidates')
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ-latest-native-focus')
    run.mkdir(parents=True)
    write_json(run / 'constants.json', constants)
    write_json(run / 'lea-candidates.json', hits)
    write_json(run / 'selection.json', selection)
    write_json(run / 'pe-map.json', dict(image_base=hex(pe.base), sections=pe.sections, pdata_ranges=len(pe.ranges)))
    for selected in selection:
        output = subprocess.run(['objdump', '-d', '--x86-asm-syntax=intel',
                                 '--start-address=' + selected['start'],
                                 '--stop-address=' + selected['end_exclusive'], str(source)],
                                capture_output=True, text=True, timeout=30)
        (run / (selected['start'] + '-objdump.txt')).write_text(output.stdout + output.stderr)
        if output.returncode:
            raise SystemExit('Independent LLVM decode failed')
    if args.scan_only:
        print(json.dumps(dict(run_directory=str(run), selected_functions=len(selection), target_executed=False)))
        return
    install = json.loads((ROOT / '.toolchain/native-install.json').read_text())
    env = os.environ.copy()
    for subdir in ('project', 'tmp', 'settings', 'cache'):
        (run / subdir).mkdir()
    env.update({key: install[key] for key in ('JAVA_HOME', 'GHIDRA_INSTALL_DIR')})
    env.update(GHIDRA_HEADLESS_MAXMEM='4G', GHIDRA_JAVA_OPTIONS='', TMPDIR=str(run / 'tmp'))
    env['GHIDRA_HEADLESS_JAVA_OPTIONS'] = ('-Djava.io.tmpdir=' + str(run / 'tmp') +
        ' -Dapplication.settingsdir=' + str(run / 'settings') + ' -Dapplication.cachedir=' + str(run / 'cache'))
    command = [str(Path(install['GHIDRA_INSTALL_DIR']) / 'support/analyzeHeadless'),
               str(run / 'project'), 'latest-focused', '-import', str(source), '-readOnly', '-deleteProject',
               '-noanalysis', '-scriptPath', str(ROOT / 'scripts'), '-log', str(run / 'ghidra.log'),
               '-scriptlog', str(run / 'script.log'), '-postScript', 'AzerothLatestFocusedDecompile.java',
               str(run / 'functions.json'), str(run / 'selection.json')]
    scripts = ('decompile_latest_native_focus.py', 'AzerothLatestFocusedDecompile.java')
    hashes = {name: digest(ROOT / 'scripts' / name) for name in scripts}
    timed_out = False
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
    path = run / 'functions.json'
    functions = json.loads(path.read_text()).get('functions', []) if path.is_file() else []
    warning = re.compile(r'bad instruction|overlaps instruction|Could not find normalized switch variable|'
                         r'truncation of jumptable|unrecovered jumptable|Too many branches', re.I)
    for function in functions:
        function['flow_warning_pattern'] = bool(warning.search(function.get('pseudocode', '') + function.get('diagnostic', '')))
        function['accepted_for_bounded_semantic_inspection'] = (
            function.get('completed') is True and function.get('undecoded_bytes') == 0
            and not function['flow_warning_pattern'] and not function.get('instructions_crossing_selected_end')
            and not function.get('unresolved_computed_jump_sites') and not function.get('error'))
    if path.is_file():
        report = json.loads(path.read_text())
        report['functions'] = functions
        write_json(path, report)
    summary = dict(method='project-local-ghidra-noanalysis-new-pe-selected-functions', original_version='0.134.0',
                   original_sha256=SHA256, original_preserved=digest(source) == SHA256,
                   target_executed=False, automatic_analysis=False, whole_process_timeout_seconds=args.timeout,
                   per_function_timeout_seconds=60, max_heap='4G', timed_out=timed_out, exit_code=returncode,
                   selected_functions=len(selection), pseudocode_completed=sum(f.get('completed') is True for f in functions),
                   accepted_for_bounded_semantic_inspection=sum(f.get('accepted_for_bounded_semantic_inspection') is True for f in functions),
                   complete_program_semantics_verified=False, scripts_sha256=hashes,
                   scripts_preserved_during_run=all(digest(ROOT / 'scripts' / name) == value for name, value in hashes.items()))
    write_json(run / 'run-summary.json', summary)
    print(json.dumps(dict(run_directory=str(run), **summary)))
    if returncode or timed_out or not summary['original_preserved'] or not summary['scripts_preserved_during_run']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
