#!/usr/bin/env python3
"""Retain reviewed damage paths from an identity-bound WAT index.

This is a local static evidence extractor, not an automatic recovery of game
semantics. It never executes the original WASM or changes the game. The separate
damage-core report explains the manual control/data-flow interpretation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from wasm_index import body_ranges

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
FUNCTIONS = (933, 934, 1107, 2017, 7654, 13409)

# These guards preserve the exact reviewed instruction paths. They do not imply
# that every other instruction in each function has been interpreted.
GUARDS = {
    933: [
        ['local.get 18', 'i32.const 288', 'i32.add', 'local.tee 7',
         'local.get 7', 'f32.load', 'local.tee 32'],
        ['local.tee 33', 'f32.sub', 'f32.store'],
        ['local.get 7', 'i32.const 416', 'i32.sub', 'local.tee 11',
         'i32.const 1', 'i32.store'],
    ],
    934: [
        ['local.get 1', 'f32.load offset=12', 'local.set 34'],
        ['local.get 0', 'f32.load offset=1188'],
        ['local.get 0', 'f32.load offset=1192', 'f32.mul'],
        ['local.get 1', 'i32.const 0', 'call 933'],
    ],
    1107: [
        ['local.get 1', 'f32.const 0x1p+0 (;=1;)', 'local.get 0',
         'f32.load offset=1208', 'f32.sub', 'f32.mul', 'local.set 30'],
        ['local.get 0', 'local.get 0', 'f32.load offset=1344',
         'local.get 30', 'f32.sub', 'f32.store offset=1344'],
    ],
    7654: [
        ['local.get 0', 'i32.const 4', 'i32.store8 offset=2299'],
    ],
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True,
                        help='Read-only index.sqlite produced by wasm_index.py')
    args = parser.parse_args()
    wasm = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if digest(wasm) != ORIGINAL_SHA:
        raise SystemExit('Current original identity differs; refusing old instruction guards')
    ranges = body_ranges(wasm.read_bytes())
    index = args.index.resolve(strict=True)
    connection = sqlite3.connect(index.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        meta = {r['key']: json.loads(r['value'])
                for r in connection.execute('SELECT key,value FROM meta')}
        if (meta['original_sha256'] != ORIGINAL_SHA or meta['wat_sha256'] != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index provenance differs from the reviewed original')
        wat = Path(meta['wat_path']).resolve(strict=True)
        if digest(wat) != WAT_SHA:
            raise SystemExit('Complete WAT digest differs from index provenance')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('damage-core-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        records = []
        with wat.open('rb') as text, wasm.open('rb') as binary:
            for idx in FUNCTIONS:
                row = connection.execute('SELECT * FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None:
                    raise SystemExit('Selected complete function is missing from index')
                if (row['body_start'], row['body_end'], row['body_bytes']) != ranges[idx]:
                    raise SystemExit('Index function bounds differ from original code section')
                record = dict(row)
                text.seek(row['wat_start'])
                source = text.read(row['wat_end'] - row['wat_start'])
                headers = re.findall(rb'^  \(func \(;(\d+);\)', source, re.M)
                if not source.startswith(f'  (func (;{idx};)'.encode()) or headers != [str(idx).encode()]:
                    raise SystemExit('Selected WAT header disagrees with index')
                lines = [line.strip() for line in source.decode('utf-8').splitlines()]
                normalized = '\n'.join(lines)
                guard_hits = []
                for pattern in GUARDS.get(idx, []):
                    needle = '\n'.join(pattern)
                    if needle not in normalized:
                        raise SystemExit(f'Reviewed instruction guard differs in function {idx}')
                    guard_hits.append({'normalized_instructions': pattern,
                                       'first_function_line': normalized[:normalized.index(needle)].count('\n') + 1})
                binary.seek(row['body_start'])
                body = binary.read(row['body_end'] - row['body_start'])
                if len(body) != row['body_bytes']:
                    raise SystemExit('Truncated original function body')
                file = run / f'function-{idx}.wat'
                file.write_bytes(source)
                record.update({'wat_bytes': len(source), 'wat_sha256': hashlib.sha256(source).hexdigest(),
                               'body_sha256': hashlib.sha256(body).hexdigest(),
                               'wat_file': file.name, 'instruction_guards': guard_hits,
                               'observed_direct_callers': [r[0] for r in connection.execute(
                                   'SELECT DISTINCT caller FROM calls WHERE callee=? ORDER BY caller', (idx,))]})
                records.append(record)
        if digest(wasm) != ORIGINAL_SHA or digest(wat) != WAT_SHA:
            raise SystemExit('An original changed during extraction')
        result = {
            'target_version': '0.126.0', 'target_build': '3e72472a',
            'original_sha256': ORIGINAL_SHA, 'complete_wat_sha256': WAT_SHA,
            'analysis_method': 'identity-bound static WAT extraction and reviewed instruction guards',
            'functions': records, 'target_executed': False,
            'original_preserved': True, 'semantic_runtime_validation': False,
            'limitations': [
                'Instruction guards preserve reviewed locations, not a proof of all-function semantics.',
                'Function/field names in the companion report are interpretations supported by separate UI/source anchors.',
                'This extractor does not establish runtime reachability, final gameplay balance or cooperative authority.',
                'No target execution, binary patch, installed app change or save mutation is performed.',
            ],
        }
        (run / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'run_directory': str(run), 'complete_functions': len(records),
                          'instruction_guards_passed': sum(len(r['instruction_guards']) for r in records),
                          'original_preserved': True, 'target_executed': False}))
    finally:
        connection.close()


if __name__ == '__main__':
    main()
