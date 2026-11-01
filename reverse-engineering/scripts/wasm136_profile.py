#!/usr/bin/env python3
"""Create a static full-WAT/SQLite profile of fixed official 0.136.0.

Only WABT analysis tools execute. The original module is never instantiated.
Historical producers and their source guards are not modified or invoked.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time

from wasm_index import body_ranges
from wasm134_profile import command, index, tool_identity, sha, save, utc, TOOLROOT

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261101T142725.754244Z/latest-wenilla_bg.wasm'
SOURCE_SHA = '48c3bce7d690b3be02973bde89903c385e21ef16deca23539dcef60a1eb2eef3'
SOURCE_BYTES = 90927420
VERSION, BUILD, STAMP = '0.136.0', 'fe24fb74c', '4762d2b13821'
DEFINED_FUNCTIONS, FUNCTION_IMPORTS = 175319, 878
SCHEMA = 'azeroth-ports-local-wasm136-index-v1'
EXE_SHA = 'eb744751b4e17ec1397b0cdc85a22af63b6af63c1da1d9c2861762c3c4d8947c'


def deployment_identity():
    """Verify frozen acquisition bytes; never execute native/Web targets."""
    directory = SOURCE.parent
    native = json.loads((directory / 'windows-acquisition.json').read_text())
    web = json.loads((directory / 'web-acquisition.json').read_text())
    manifest = json.loads((directory / 'windows-latest.json').read_text())
    assert manifest['version'] == native['version'] == VERSION
    assert manifest['sha256'] == native['exe_sha256'] == EXE_SHA
    exe = directory / native['exe_relative_path']
    assert exe.resolve().is_relative_to(directory.resolve())
    assert exe.stat().st_size == manifest['size'] == native['exe_bytes'] == 147811840
    assert sha(exe) == EXE_SHA
    assert web['stamp'] == web['stamp_after'] == STAMP
    assert web['page_stamp_stable_during_acquisition'] is True
    assert web['index']['sha256'] == web['index_after']['sha256']
    entries = [native['manifest'], web['index'], web['index_after'], web['wasm'], *web['scripts'].values()]
    verified = []
    for entry in entries:
        path = directory / entry['filename']
        assert path.resolve().is_relative_to(directory.resolve()) and not path.is_symlink()
        assert path.stat().st_size == entry['bytes'] and sha(path) == entry['sha256']
        assert entry['status'] == 200
        verified.append(dict(filename=entry['filename'], bytes=entry['bytes'], sha256=entry['sha256']))
    assert web['wasm']['sha256'] == SOURCE_SHA and web['wasm']['bytes'] == SOURCE_BYTES
    for entry in [web['wasm'], *web['scripts'].values()]:
        assert entry['url'].endswith('?v=' + STAMP)
    menu = (BUILD + VERSION).encode(); branding = b'Made by Aethus'
    embedded = []
    for path in (exe, SOURCE):
        raw = path.read_bytes(); start = raw.find(branding)
        assert start >= 0 and raw.find(branding, start+1) < 0
        at = raw.find(menu, start, start+200)
        assert at >= 0 and raw.find(menu, at+1) < 0
        embedded.append(dict(filename=str(path.relative_to(directory)), branding_offset=start,
            build_version_offset=at, embedded_build=BUILD, embedded_version=VERSION))
    return dict(version=VERSION, build=BUILD, acquisition_stamp=STAMP,
        native_web_menu_identity_equal=True, acquisition_page_stamp_stable=True,
        acquisition_files=verified, embedded_menu=embedded,
        windows_acquisition_sha256=sha(directory/'windows-acquisition.json'),
        web_acquisition_sha256=sha(directory/'web-acquisition.json'),
        scope='Frozen official acquisition consistency, not a later live deployment check.',
        exe_executed=False, wasm_instantiated=False)


def handles(run, stage):
    """Bounded read-only process/handle receipts for this owned analysis."""
    rows = {}
    for label, command_line in (('process', ['/bin/ps', '-p', str(os.getpid()), '-o',
            'pid,ppid,pgid,tty,stat,etime,command']),
            ('handles', ['/usr/sbin/lsof', '-p', str(os.getpid())])):
        target = run / (stage+'-'+label+'.txt')
        try:
            result = subprocess.run(command_line, capture_output=True, timeout=10)
            target.write_bytes(result.stdout + result.stderr)
            rows[label] = dict(command=command_line, exit_code=result.returncode,
                file=target.name, sha256=sha(target))
        except (OSError, subprocess.TimeoutExpired) as error:
            target.write_text(repr(error)+'\n')
            rows[label] = dict(command=command_line, status='unavailable_not_negative',
                error=repr(error), file=target.name, sha256=sha(target))
    save(run / (stage+'-process-receipt.json'), dict(pid=os.getpid(), stage=stage,
        captured_utc=utc(), target_executed=False, observations=rows))


class Reader:
    """Bounded section reader, independent of the old source-guarded parsers."""
    def __init__(self, data, start=0, end=None):
        self.data, self.pos = data, start
        self.end = len(data) if end is None else end
        if not 0 <= start <= self.end <= len(data):
            raise ValueError('Reader outside binary')

    def raw(self, size):
        start = self.pos
        self.pos += size
        if size < 0 or self.pos > self.end:
            raise ValueError('Read exceeds section')
        return self.data[start:self.pos]

    def byte(self):
        return self.raw(1)[0]

    def uint(self):
        value = 0
        for shift in range(0, 35, 7):
            byte = self.byte()
            value |= (byte & 127) << shift
            if byte < 128:
                if value > 0xffffffff:
                    raise ValueError('ULEB exceeds u32')
                return value
        raise ValueError('Invalid ULEB')

    def sint(self):
        value = 0
        for shift in range(0, 35, 7):
            byte = self.byte()
            value |= (byte & 127) << shift
            if byte < 128:
                if byte & 64:
                    value -= 1 << (shift + 7)
                if not -(1 << 31) <= value < (1 << 31):
                    raise ValueError('SLEB exceeds i32')
                return value
        raise ValueError('Invalid SLEB')

    def name(self):
        return self.raw(self.uint()).decode('utf8')

    def finish(self):
        if self.pos != self.end:
            raise ValueError('Unconsumed section bytes')


def binary_identity(data):
    """Reparse imports, exports, types, bodies and data without executing WASM."""
    if data[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Wrong WASM header')
    top, sections, listing = Reader(data, 8), {}, []
    while top.pos < top.end:
        begin = top.pos
        kind, size = top.byte(), top.uint()
        payload = top.pos
        top.raw(size)
        if kind:
            if kind in sections:
                raise ValueError('Duplicate non-custom section')
            sections[kind] = (payload, top.pos)
        listing.append({'kind': kind, 'start': begin, 'payload_start': payload,
                        'end': top.pos, 'bytes': top.pos - begin,
                        'sha256': hashlib.sha256(data[begin:top.pos]).hexdigest()})
    def reader(kind):
        return Reader(data, *sections[kind])
    t, types = reader(1), []
    for _ in range(t.uint()):
        if t.byte() != 0x60:
            raise ValueError('Expected numeric function types')
        types.append((t.raw(t.uint()).hex(), t.raw(t.uint()).hex()))
    t.finish()
    imp, imports = reader(2), []
    for _ in range(imp.uint()):
        module, name, kind = imp.name(), imp.name(), imp.byte()
        if kind != 0:
            raise ValueError('Unexpected non-function import')
        type_index = imp.uint()
        if type_index >= len(types):
            raise ValueError('Import type out of bounds')
        imports.append({'module': module, 'name': name, 'type_index': type_index})
    imp.finish()
    f = reader(3)
    declarations = [f.uint() for _ in range(f.uint())]
    f.finish()
    if any(i >= len(types) for i in declarations):
        raise ValueError('Defined function type out of bounds')
    ranges = body_ranges(data)
    if (len(imports) != FUNCTION_IMPORTS or len(declarations) != DEFINED_FUNCTIONS
            or len(ranges) != DEFINED_FUNCTIONS or min(ranges) != len(imports)):
        raise ValueError('Fixed source function counts differ')
    exp, exports = reader(7), []
    for _ in range(exp.uint()):
        name, kind, idx = exp.name(), exp.byte(), exp.uint()
        entry = {'name': name, 'kind': kind, 'index': idx}
        if kind == 0:
            if idx >= len(imports) + len(declarations):
                raise ValueError('Export function outside code')
            ti = imports[idx]['type_index'] if idx < len(imports) else declarations[idx - len(imports)]
            entry.update(type_index=ti, params_hex=types[ti][0], results_hex=types[ti][1])
        exports.append(entry)
    exp.finish()
    dat, segments = reader(11), []
    for idx in range(dat.uint()):
        flags = dat.uint()
        if flags not in (0, 1, 2):
            raise ValueError('Unexpected data flags')
        memory, address = None, None
        if flags != 1:
            memory = 0 if flags == 0 else dat.uint()
            if dat.byte() != 0x41:
                raise ValueError('Unexpected data offset expression')
            address = dat.sint() & 0xffffffff
            if dat.byte() != 0x0b:
                raise ValueError('Data expression terminator differs')
        size, start = dat.uint(), dat.pos
        payload = dat.raw(size)
        segments.append({'index': idx, 'flags': flags, 'memory': memory,
                         'address': address, 'file_offset': start, 'bytes': size,
                         'sha256': hashlib.sha256(payload).hexdigest()})
    dat.finish()
    return {'sections': listing, 'types': len(types), 'function_imports': len(imports),
            'defined_functions': len(declarations), 'imports': imports, 'exports': exports,
            'data_segments': segments, 'implicit_start_section': 8 in sections,
            'original_module_instantiated': False}, ranges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deadline-seconds', type=int, default=300)
    args = parser.parse_args()
    if not 10 <= args.deadline_seconds <= 900:
        parser.error('Deadline must be between ten and900 seconds')
    started = time.monotonic()
    deadline = started + args.deadline_seconds
    acquisition = deployment_identity()
    if SOURCE.is_symlink() or SOURCE.stat().st_size != SOURCE_BYTES or sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Official 0.136.0 identity differs')
    data = SOURCE.read_bytes()
    identity, ranges = binary_identity(data)
    branding = b'Made by Aethus'
    menu = data.find(branding)
    wanted = (BUILD + VERSION).encode()
    at = data.find(wanted, menu, menu + 200) if menu >= 0 else -1
    if at < 0 or data.find(wanted, at + 1) != -1:
        raise ValueError('Expected unique embedded menu version/build')
    identity['menu_branding'] = {'context_start': menu, 'build_offset': at,
                                 'version_offset': at + len(BUILD),
                                 'build': BUILD, 'version': VERSION}
    del data
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('wasm0136-profile-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    sources = {str(p): sha(p) for p in (Path(__file__).resolve(),
               ROOT / 'scripts/wasm134_profile.py', ROOT / 'scripts/wasm_index.py')}
    tools_before = tool_identity()
    save(run / 'binary-identity.json', identity)
    save(run / 'deployment-identity.json', acquisition)
    save(run / 'identity-before.json', {'source_sha256': SOURCE_SHA, 'source_bytes': SOURCE_BYTES,
         'wabt': tools_before, 'local_tool_sources': sources})
    save(run / 'run-state.json', {'status': 'running', 'pid': os.getpid(), 'started_utc': utc(),
         'deadline_seconds': args.deadline_seconds, 'target_executed': False})
    invocations = []
    handles(run, 'before')
    try:
        binary = TOOLROOT / 'wabt/wabt-1.0.42/bin'
        command([binary / 'wasm-validate', '--enable-all', '--ignore-custom-section-errors', SOURCE],
                run, 'validate', invocations, deadline)
        command([binary / 'wasm-objdump', '-h', SOURCE], run, 'headers', invocations, deadline)
        wat = run / 'official-0.136.0-full.wat'
        command([binary / 'wasm2wat', '--enable-all', '--ignore-custom-section-errors', SOURCE, '-o', wat],
                run, 'decode', invocations, deadline)
        producer = {'target_version': VERSION, 'embedded_build': BUILD, 'official_stamp': STAMP,
                    'original_sha256': SOURCE_SHA, 'original_path': str(SOURCE), 'wabt': tools_before,
                    'wat_path': str(wat), 'wat_sha256': sha(wat), 'wat_bytes': wat.stat().st_size,
                    'invocations': invocations, 'full_module_validated': True, 'target_executed': False,
                    'local_tool_sources': sources}
        save(run / 'producer-provenance.json', producer)
        meta = {'target_version': VERSION, 'embedded_build': BUILD, 'official_stamp': STAMP,
                'original_sha256': SOURCE_SHA, 'original_path': str(SOURCE), 'wat_path': str(wat),
                'wat_sha256': producer['wat_sha256'], 'index_schema': SCHEMA,
                'local_tool_sources': sources, 'wabt_version': '1.0.42',
                'direct_call_kinds': ['call', 'return_call'],
                'integer_constant_kinds': ['i32.const', 'i64.const'],
                'memory_scope': 'scalar/vector/atomic load/store instructions; static offset immediate only',
                'terminal_parentheses_supported': True, 'target_executed': False,
                'method': 'local full-WAT lexical instruction index; not runtime or stock REA'}
        database = run / 'index.sqlite'
        handles(run, 'before-index')
        print(json.dumps({'stage': 'stream-index', 'pid': os.getpid(), 'run': str(run)}), flush=True)
        result = index(wat, database, ranges, meta, deadline)
        # Readers use URI mode=ro; the filesystem mode also prevents accidental
        # writes to this completed evidence artifact.
        database.chmod(0o444)
        with sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True) as con:
            assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        handles(run, 'after-index')
        tools_after = tool_identity()
        identical = (tools_before == tools_after and sha(SOURCE) == SOURCE_SHA
                     and sha(wat) == producer['wat_sha256']
                     and all(sha(Path(p)) == v for p, v in sources.items()))
        save(run / 'identity-after.json', {'source_sha256': sha(SOURCE), 'wabt': tools_after,
             'wat_sha256': sha(wat), 'local_tool_sources': {p: sha(Path(p)) for p in sources},
             'identities_preserved': identical})
        if not identical:
            raise ValueError('Input or producer identity changed')
        summary = {**meta, **result, 'run_directory': str(run), 'database_path': str(database),
                   'database_bytes': database.stat().st_size, 'database_sha256': sha(database),
                   'binary_identity_path': str(run / 'binary-identity.json'),
                   'binary_identity_sha256': sha(run / 'binary-identity.json'),
                   'full_module_validated': True, 'function_imports': FUNCTION_IMPORTS,
                   'defined_functions': DEFINED_FUNCTIONS, 'wat_bytes': wat.stat().st_size,
                   'identities_preserved': identical,
                   'database_mode': '0444; query URI mode=ro',
                   'deployment_identity_sha256': sha(run/'deployment-identity.json'),
                   'elapsed_seconds': round(time.monotonic() - started, 3)}
        save(run / 'manifest.json', summary)
        save(run / 'run-state.json', {'status': 'complete', 'pid': os.getpid(),
             'finished_utc': utc(), 'elapsed_seconds': summary['elapsed_seconds']})
        print(json.dumps(summary), flush=True)
    except BaseException as error:
        save(run / 'run-state.json', {'status': 'failed', 'pid': os.getpid(), 'error': repr(error),
             'finished_utc': utc(), 'elapsed_seconds': round(time.monotonic() - started, 3)})
        raise


if __name__ == '__main__':
    main()
