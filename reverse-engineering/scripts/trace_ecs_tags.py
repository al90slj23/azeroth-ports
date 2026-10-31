#!/usr/bin/env python3
"""Locate selected i64 constants in the identity-bound full WAT, statically.

Literal occurrences are navigation candidates, not proof of event identity or
runtime dispatch. This helper never executes the original game.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3

from wasm_index import ORIGINAL_SHA, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--values', type=int, nargs='+', required=True)
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(source) != ORIGINAL_SHA:
        raise SystemExit('Original core identity differs')
    wanted = set(args.values)
    if any(not -(1 << 63) <= value < (1 << 63) for value in wanted):
        parser.error('Use signed i64 values as printed by WABT')
    with sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA:
            raise SystemExit('Index provenance differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Full WAT identity differs')
        header = re.compile(rb'^  \(func \(;(\d+);\)')
        literal = re.compile(rb'i64\.const (-?\d+)\)*')
        function = None; offset = 0; hits = []
        with wat.open('rb') as stream:
            for number, line in enumerate(stream, 1):
                if line.startswith(b'  ('):
                    match = header.match(line)
                    function = int(match[1]) if match else None
                elif line == b')\n':
                    function = None
                stripped = line.strip()
                if function is not None and stripped.startswith(b'i64.const '):
                    match = literal.fullmatch(stripped)
                    if match is None:
                        raise ValueError('Unexpected decoded i64 constant syntax')
                    value = int(match[1])
                    if value in wanted:
                        hits.append({'function_index': function, 'value': value,
                                     'wat_offset': offset, 'wat_line': number})
                offset += len(line)
        functions = []
        for index in sorted({h['function_index'] for h in hits}):
            row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                              'FROM functions WHERE idx=?', (index,)).fetchone()
            if row is None:
                raise ValueError('Constant hit lacks a local function range')
            functions.append(dict(zip(('function_index', 'wat_start', 'wat_end', 'wat_line',
                                       'body_start', 'body_end', 'body_bytes'), (index, *row))))
    if sha(source) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise SystemExit('Original inputs changed while searching')
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('ecs-tag-refs-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    report = {'original_sha256': ORIGINAL_SHA, 'full_wat_sha256': WAT_SHA,
              'values': sorted(wanted), 'literal_references': hits,
              'candidate_functions': functions, 'target_executed': False,
              'qualification': 'Exact literal references; not typed-event or execution proof'}
    (run / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'run_directory': str(run), 'references': len(hits),
                      'candidate_functions': len(functions), 'target_executed': False}))


if __name__ == '__main__':
    main()
