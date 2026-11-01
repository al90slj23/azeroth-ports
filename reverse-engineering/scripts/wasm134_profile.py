#!/usr/bin/env python3
"""Reproduce the official 0.134.0 full-WAT and SQLite static analysis profile.

This project-local producer never executes the target. It deliberately has its
own source identity and does not relax the historical 0.126.0 tool guards.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import tarfile
import time

from wasm_index import body_ranges

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/latest-wenilla_bg.wasm'
SOURCE_SHA = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
SOURCE_BYTES = 90953762
VERSION = '0.134.0'
BUILD = '983346a7'
STAMP = 'd1eb6005e172'
DEFINED_FUNCTIONS = 175316
ARCHIVE_SHA = '3f654779b436c628db3ca4323c51538815f5fbc887a6d5f3bb1c18d36281e240'
TOOLROOT = ROOT / '.toolchain/rea-wasm-profile'
SCHEMA = 'azeroth-ports-local-wasm134-index-v1'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def utc():
    return datetime.now(timezone.utc).isoformat()


def tool_identity():
    archive = TOOLROOT / 'wabt-1.0.42-macos-arm64.tar.gz'
    if archive.is_symlink() or sha(archive) != ARCHIVE_SHA:
        raise ValueError('Pinned official WABT archive identity differs')
    identities = {}
    with tarfile.open(archive) as source:
        for name in ('wasm-validate', 'wasm-objdump', 'wasm2wat'):
            path = TOOLROOT / 'wabt/wabt-1.0.42/bin' / name
            with source.extractfile('wabt-1.0.42/bin/' + name) as member:
                expected = hashlib.sha256(member.read()).hexdigest()
            if path.is_symlink() or sha(path) != expected:
                raise ValueError('Installed tool differs from pinned archive: ' + name)
            version = subprocess.check_output([str(path), '--version'], text=True, timeout=10).strip()
            if version != '1.0.42':
                raise ValueError('Unexpected WABT version: ' + name)
            identities[name] = {'path': str(path), 'sha256': expected, 'version': version}
    return {'archive_path': str(archive), 'archive_sha256': ARCHIVE_SHA, 'tools': identities}


def command(argv, run, label, invocations, deadline):
    started = time.monotonic()
    stdout, stderr = run / (label + '.stdout.txt'), run / (label + '.stderr.txt')
    item = {'arguments': [str(x) for x in argv], 'started_utc': utc(),
            'stdout_path': str(stdout), 'stderr_path': str(stderr),
            'deadline_seconds': max(1, round(deadline - started, 3))}
    with stdout.open('wb') as out, stderr.open('wb') as err:
        child = subprocess.Popen(item['arguments'], stdout=out, stderr=err, start_new_session=True)
        item.update({'pid': child.pid, 'process_group_id': child.pid})
        invocations.append(item)
        save(run / 'commands.json', invocations)
        print(json.dumps({'stage': label, 'pid': child.pid, 'run': str(run)}), flush=True)
        try:
            code = child.wait(timeout=max(1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            code = child.wait()
            item['deadline_exceeded'] = True
        item.update({'exit_code': code, 'finished_utc': utc(),
                     'elapsed_seconds': round(time.monotonic() - started, 3)})
        save(run / 'commands.json', invocations)
    if code:
        raise RuntimeError('Owned command failed: ' + label + '; see ' + str(stderr))
    return item


def index(wat, database, ranges, meta, deadline):
    """Stream WABT lines; retain instruction locations and exact function ranges."""
    con = sqlite3.connect(database)
    con.executescript('''
      PRAGMA page_size=32768;
      PRAGMA journal_mode=OFF;
      PRAGMA synchronous=OFF;
      CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
      CREATE TABLE functions (idx INTEGER PRIMARY KEY, wat_start INTEGER,
          wat_end INTEGER, wat_line INTEGER, body_start INTEGER,
          body_end INTEGER, body_bytes INTEGER);
      CREATE TABLE calls (caller INTEGER, callee INTEGER, wat_offset INTEGER,
          wat_line INTEGER, instruction TEXT NOT NULL);
      CREATE TABLE iconsts (function_idx INTEGER, value INTEGER, wat_offset INTEGER,
          wat_line INTEGER, operation TEXT NOT NULL);
      CREATE TABLE memops (function_idx INTEGER, operation TEXT, field_offset INTEGER,
          wat_offset INTEGER, wat_line INTEGER);
    ''')
    con.executemany('INSERT INTO meta VALUES (?,?)', [(k, json.dumps(v)) for k, v in meta.items()])
    header = re.compile(rb'^  \(func \(;(\d+);\)')
    call = re.compile(rb'^\s+(call|return_call) (\d+)\)*\s*$')
    iconst = re.compile(rb'^\s+((?:i32|i64)\.const) (-?\d+)\)*\s*$')
    memop = re.compile(rb'^\s+((?:i32|i64|f32|f64|v128)\.(?:atomic\.)?(?:load|store)[a-z0-9_.]*)(?=\s|\))')
    field_offset = re.compile(rb'\boffset=(\d+)')
    functions, calls, constants, memory = [], [], [], []
    current = None
    start = first_line = offset = 0
    terminal = {'call': 0, 'return_call': 0, 'iconst': 0, 'memop': 0}
    started = time.monotonic()

    def finish(end):
        if current is not None:
            functions.append((current, start, end, first_line, *ranges[current]))

    def flush():
        con.executemany('INSERT INTO calls VALUES (?,?,?,?,?)', calls)
        con.executemany('INSERT INTO iconsts VALUES (?,?,?,?,?)', constants)
        con.executemany('INSERT INTO memops VALUES (?,?,?,?,?)', memory)
        calls.clear(); constants.clear(); memory.clear()

    with wat.open('rb') as stream:
        for line_number, line in enumerate(stream, 1):
            if line.startswith(b'  ('):
                finish(offset); current = None
                found = header.match(line)
                if found:
                    current = int(found[1]); start = offset; first_line = line_number
                    if current not in ranges:
                        raise ValueError('WAT function lacks a matching binary body')
                elif line.startswith(b'  (func '):
                    raise ValueError('Unexpected WABT function header')
            elif line.rstrip(b'\r\n') == b')':
                finish(offset); current = None
            elif current is not None:
                stripped = line.lstrip()
                final = line.rstrip().endswith(b')')
                if stripped.startswith((b'call ', b'return_call ')):
                    found = call.match(line)
                    if not found:
                        raise ValueError('Unrecognized direct call at WAT line ' + str(line_number))
                    operation = found[1].decode()
                    calls.append((current, int(found[2]), offset, line_number, operation))
                    if final: terminal[operation] += 1
                elif stripped.startswith((b'i32.const ', b'i64.const ')):
                    found = iconst.match(line)
                    if not found:
                        raise ValueError('Unrecognized integer constant at WAT line ' + str(line_number))
                    constants.append((current, int(found[2]), offset, line_number, found[1].decode()))
                    if final: terminal['iconst'] += 1
                else:
                    found = memop.match(line)
                    if found:
                        at = field_offset.search(line)
                        memory.append((current, found[1].decode(), int(at[1]) if at else 0, offset, line_number))
                        if final: terminal['memop'] += 1
            offset += len(line)
            if len(calls) + len(constants) + len(memory) >= 25000:
                flush()
            if line_number % 250000 == 0 and time.monotonic() > deadline:
                raise TimeoutError('Owned profile deadline exceeded during streamed index')
    finish(offset)
    flush()
    con.executemany('INSERT INTO functions VALUES (?,?,?,?,?,?,?)', functions)
    counts = {table: con.execute('SELECT count(*) FROM ' + table).fetchone()[0]
              for table in ('functions', 'calls', 'iconsts', 'memops')}
    if counts['functions'] != len(ranges):
        raise ValueError('Full WAT function coverage mismatch')
    if time.monotonic() > deadline:
        raise TimeoutError('Owned profile deadline exceeded before SQLite indexes')
    # SQLite's progress handler bounds index construction as well as the stream.
    con.set_progress_handler(lambda: int(time.monotonic() > deadline), 100000)
    con.executescript('''
      CREATE INDEX callers ON calls(callee);
      CREATE INDEX callees ON calls(caller);
      CREATE INDEX values_by_function ON iconsts(value,function_idx);
      CREATE INDEX constants_in_function ON iconsts(function_idx);
      CREATE INDEX memory_by_offset ON memops(field_offset,operation);
    ''')
    kinds = dict(con.execute('SELECT instruction,count(*) FROM calls GROUP BY instruction'))
    integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
    con.commit(); con.close()
    if integrity != 'ok':
        raise ValueError('SQLite integrity check failed')
    return {'counts': counts, 'direct_call_counts': kinds, 'terminal_parenthesis_counts': terminal,
            'wat_lines': line_number, 'sqlite_integrity_check': integrity,
            'index_elapsed_seconds': round(time.monotonic() - started, 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deadline-seconds', type=int, default=900)
    parser.add_argument('--reuse-producer', type=Path,
                        help='Reuse only a matching completed 0.134.0 producer, retaining its command log')
    args = parser.parse_args()
    if args.deadline_seconds < 10:
        parser.error('Deadline must be at least ten seconds')
    started = time.monotonic(); deadline = started + args.deadline_seconds
    if SOURCE.is_symlink() or SOURCE.stat().st_size != SOURCE_BYTES or sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Official 0.134.0 source identity differs')
    data = SOURCE.read_bytes()
    ranges = body_ranges(data)
    if len(ranges) != DEFINED_FUNCTIONS:
        raise ValueError('Unexpected number of defined functions')
    del data
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('wasm0134-profile-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    helper = ROOT / 'scripts/wasm_index.py'
    sources = {str(path): sha(path) for path in (script, helper)}
    before = tool_identity()
    invocations = []
    save(run / 'identity-before.json', {'source_sha256': SOURCE_SHA,
         'source_bytes': SOURCE_BYTES, 'wabt': before, 'local_tool_sources': sources})
    save(run / 'run-state.json', {'status': 'running', 'pid': os.getpid(), 'started_utc': utc(),
         'deadline_seconds': args.deadline_seconds, 'target_executed': False})
    try:
        binary = TOOLROOT / 'wabt/wabt-1.0.42/bin'
        if args.reuse_producer:
            producer = json.loads((args.reuse_producer / 'producer-provenance.json').read_text())
            wat = Path(producer['wat_path'])
            if (producer['original_sha256'] != SOURCE_SHA or producer['target_version'] != VERSION
                    or producer['wabt'] != before or sha(wat) != producer['wat_sha256']):
                raise ValueError('Reused producer identity differs')
            save(run / 'reused-producer.json', {'producer_path': str(args.reuse_producer.resolve()),
                 'producer_provenance_sha256': sha(args.reuse_producer / 'producer-provenance.json')})
        else:
            command([binary / 'wasm-validate', '--enable-all', '--ignore-custom-section-errors', SOURCE],
                    run, 'validate', invocations, deadline)
            command([binary / 'wasm-objdump', '-h', SOURCE], run, 'headers', invocations, deadline)
            wat = run / 'official-0.134.0-full.wat'
            command([binary / 'wasm2wat', '--enable-all', '--ignore-custom-section-errors', SOURCE, '-o', wat],
                    run, 'decode', invocations, deadline)
            producer = {'target_version': VERSION, 'embedded_build': BUILD, 'official_stamp': STAMP,
                        'original_sha256': SOURCE_SHA, 'original_path': str(SOURCE),
                        'wabt': before, 'wat_path': str(wat), 'wat_sha256': sha(wat),
                        'wat_bytes': wat.stat().st_size, 'invocations': invocations,
                        'full_module_validated': True, 'target_executed': False,
                        'local_tool_sources': sources}
            save(run / 'producer-provenance.json', producer)
        database = run / 'index.sqlite'
        meta = {'target_version': VERSION, 'embedded_build': BUILD, 'official_stamp': STAMP,
                'original_sha256': SOURCE_SHA, 'original_path': str(SOURCE),
                'wat_path': str(wat.resolve()), 'wat_sha256': producer['wat_sha256'],
                'index_schema': SCHEMA, 'local_tool_sources': sources,
                'wabt_version': '1.0.42', 'wabt_archive_sha256': ARCHIVE_SHA,
                'direct_call_kinds': ['call', 'return_call'],
                'integer_constant_kinds': ['i32.const', 'i64.const'],
                'memory_scope': 'scalar/vector/atomic load/store instructions; static offset immediate only',
                'terminal_parentheses_supported': True, 'target_executed': False,
                'method': 'local full-WAT lexical instruction index; not runtime or stock REA'}
        print(json.dumps({'stage': 'stream-index', 'pid': os.getpid(), 'run': str(run)}), flush=True)
        result = index(wat, database, ranges, meta, deadline)
        after = tool_identity()
        identities_preserved = (before == after and sha(SOURCE) == SOURCE_SHA
                                and sha(wat) == producer['wat_sha256']
                                and all(sha(Path(path)) == digest for path, digest in sources.items()))
        save(run / 'identity-after.json', {'source_sha256': sha(SOURCE), 'wabt': after,
             'wat_sha256': sha(wat), 'local_tool_sources': {p: sha(Path(p)) for p in sources},
             'identities_preserved': identities_preserved})
        if not identities_preserved:
            raise ValueError('Input or local tool identity changed during analysis')
        summary = {**meta, **result, 'run_directory': str(run), 'database_path': str(database),
                   'database_bytes': database.stat().st_size, 'database_sha256': sha(database),
                   'full_module_validated': True, 'defined_functions': len(ranges),
                   'function_imports': min(ranges), 'wat_bytes': wat.stat().st_size,
                   'identities_preserved': identities_preserved,
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
