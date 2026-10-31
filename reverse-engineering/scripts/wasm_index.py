#!/usr/bin/env python3
"""Index exact full WAT for local, read-only static research; never run the game.

This is a local navigation aid, not a stock REA semantic analysis. The database
records instruction locations, not inferred runtime calls or field types.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def body_ranges(data):
    def uint(p):
        value = shift = 0
        while p < len(data) and shift <= 28:
            byte = data[p]; p += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, p
            shift += 7
        raise ValueError('Invalid u32 LEB')
    if data[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Wrong WASM header')
    sections = {}; p = 8
    while p < len(data):
        kind = data[p]; size, begin = uint(p + 1)
        end = begin + size
        if end > len(data):
            raise ValueError('WASM section outside file')
        sections[kind] = (begin, end); p = end
    imports, p = uint(sections[2][0])
    for _ in range(imports):
        for _ in range(2):
            length, p = uint(p); p += length
        if data[p] != 0:
            raise ValueError('This exact target profile expects function imports only')
        _, p = uint(p + 1)
    count, p = uint(sections[10][0]); result = {}
    for index in range(imports, imports + count):
        length, begin = uint(p); p = begin + length
        result[index] = (begin, p, length)
    if p != sections[10][1]:
        raise ValueError('Code section boundary differs')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--producer', type=Path, required=True,
                        help='Existing full WABT producer directory with provenance')
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    provenance = json.loads((args.producer / 'producer-provenance.json').read_text())
    wat = args.producer / 'original-full.wat'
    if (sha(source) != ORIGINAL_SHA or provenance['original_sha256'] != ORIGINAL_SHA
            or sha(wat) != provenance['wat_sha256']):
        raise SystemExit('Original/decoded input identity differs')
    ranges = body_ranges(source.read_bytes())
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('wasm-index-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    database = run / 'index.sqlite'
    con = sqlite3.connect(database)
    con.executescript('''
        PRAGMA page_size=32768;
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE functions (idx INTEGER PRIMARY KEY, wat_start INTEGER,
            wat_end INTEGER, wat_line INTEGER, body_start INTEGER,
            body_end INTEGER, body_bytes INTEGER);
        CREATE TABLE calls (caller INTEGER, callee INTEGER, wat_offset INTEGER, wat_line INTEGER);
        CREATE TABLE iconsts (function_idx INTEGER, value INTEGER, wat_offset INTEGER, wat_line INTEGER);
        CREATE TABLE memops (function_idx INTEGER, operation TEXT, field_offset INTEGER,
            wat_offset INTEGER, wat_line INTEGER);
    ''')
    meta = {'original_sha256': ORIGINAL_SHA, 'wat_sha256': provenance['wat_sha256'],
            'wat_path': str(wat.resolve()), 'target_executed': False,
            'direct_call_kinds': ['call', 'return_call'], 'terminal_parentheses_supported': True,
            'method': 'local full-WAT lexical instruction index; not runtime or stock REA'}
    con.executemany('INSERT INTO meta VALUES (?,?)', [(k, json.dumps(v)) for k, v in meta.items()])
    header = re.compile(rb'^  \(func \(;(\d+);\)')
    call = re.compile(rb'^\s+(?:call|return_call) (\d+)\)*\s*$')
    iconst = re.compile(rb'^\s+i32.const (-?\d+)\)*\s*$')
    memop = re.compile(rb'^\s+((?:i32|i64|f32|f64|v128)\.(?:load|store)[a-z0-9_]*)(?: offset=(\d+))?(?: align=\d+)?\)*\s*$')
    functions = []; calls = []; constants = []; memory = []
    current = None; start = first_line = 0; offset = 0; started = time.monotonic()

    def finish(end):
        if current is not None:
            functions.append((current, start, end, first_line, *ranges[current]))

    with wat.open('rb') as stream:
        for line_number, line in enumerate(stream, 1):
            if line.startswith(b'  ('):
                finish(offset); current = None
                found = header.match(line)
                if found:
                    current = int(found[1]); start = offset; first_line = line_number
                    if current not in ranges:
                        raise ValueError('WAT function does not map to original code body')
            elif line == b')\n':
                finish(offset); current = None
            elif current is not None:
                stripped = line.lstrip()
                if stripped.startswith((b'call ', b'return_call ')):
                    found = call.match(line)
                    if found:
                        calls.append((current, int(found[1]), offset, line_number))
                elif stripped.startswith(b'i32.const '):
                    found = iconst.match(line)
                    if found:
                        constants.append((current, int(found[1]), offset, line_number))
                elif stripped.startswith((b'i32.', b'i64.', b'f32.', b'f64.', b'v128.')):
                    found = memop.match(line)
                    if found:
                        memory.append((current, found[1].decode(), int(found[2] or 0), offset, line_number))
            offset += len(line)
            if len(calls) + len(constants) + len(memory) >= 25000:
                con.executemany('INSERT INTO calls VALUES (?,?,?,?)', calls); calls.clear()
                con.executemany('INSERT INTO iconsts VALUES (?,?,?,?)', constants); constants.clear()
                con.executemany('INSERT INTO memops VALUES (?,?,?,?,?)', memory); memory.clear()
    finish(offset)
    con.executemany('INSERT INTO functions VALUES (?,?,?,?,?,?,?)', functions)
    con.executemany('INSERT INTO calls VALUES (?,?,?,?)', calls)
    con.executemany('INSERT INTO iconsts VALUES (?,?,?,?)', constants)
    con.executemany('INSERT INTO memops VALUES (?,?,?,?,?)', memory)
    con.executescript('CREATE INDEX callers ON calls(callee); CREATE INDEX callees ON calls(caller);'
                      'CREATE INDEX values_by_function ON iconsts(value,function_idx);'
                      'CREATE INDEX constants_in_function ON iconsts(function_idx);'
                      'CREATE INDEX memory_by_offset ON memops(field_offset,operation);')
    counts = {table: con.execute('SELECT count(*) FROM ' + table).fetchone()[0]
              for table in ('functions', 'calls', 'iconsts', 'memops')}
    if counts['functions'] != len(ranges):
        raise ValueError('Full WAT function coverage mismatch')
    con.commit(); con.close()
    if sha(source) != ORIGINAL_SHA or sha(wat) != provenance['wat_sha256']:
        raise SystemExit('Input changed while indexing')
    summary = {**meta, 'counts': counts, 'elapsed_seconds': round(time.monotonic() - started, 3),
               'database_bytes': database.stat().st_size, 'database_sha256': sha(database)}
    (run / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'database': str(database), **summary}))


if __name__ == '__main__':
    main()
