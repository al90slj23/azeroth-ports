#!/usr/bin/env python3
"""Read back a completed fixed-0.135.1 static profile; never execute the target."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time

from wasm_index import body_ranges
from wasm135_profile import SOURCE, SOURCE_SHA, SOURCE_BYTES, VERSION, BUILD


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(run):
    run = run.resolve()
    manifest = json.loads((run / 'manifest.json').read_text())
    state = json.loads((run / 'run-state.json').read_text())
    assert state['status'] == 'complete'
    assert manifest['target_version'] == VERSION and manifest['embedded_build'] == BUILD
    assert manifest['original_sha256'] == SOURCE_SHA and SOURCE.stat().st_size == SOURCE_BYTES
    assert sha(SOURCE) == SOURCE_SHA
    for name, digest in manifest['local_tool_sources'].items():
        assert sha(Path(name)) == digest, name
    binary = SOURCE.read_bytes()
    ranges = body_ranges(binary)
    identity_path = Path(manifest['binary_identity_path'])
    assert sha(identity_path) == manifest['binary_identity_sha256']
    identity = json.loads(identity_path.read_text())
    for section in identity['sections']:
        assert hashlib.sha256(binary[section['start']:section['end']]).hexdigest() == section['sha256']
    for segment in identity['data_segments']:
        at, size = segment['file_offset'], segment['bytes']
        assert hashlib.sha256(binary[at:at + size]).hexdigest() == segment['sha256']
    database, wat = Path(manifest['database_path']), Path(manifest['wat_path'])
    assert sha(database) == manifest['database_sha256']
    assert sha(wat) == manifest['wat_sha256']
    con = sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True)
    meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
    for key in ('original_sha256', 'target_version', 'embedded_build', 'wat_sha256', 'index_schema'):
        assert meta[key] == manifest[key], key
    assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    counts = {table: con.execute('SELECT count(*) FROM ' + table).fetchone()[0]
              for table in ('functions', 'calls', 'iconsts', 'memops')}
    assert counts == manifest['counts']
    previous_end, checked = 0, 0
    selected = []
    selected_ids = {878, 879, 880, 1073, 1513, 2159, 2862, 35877, 85719, 95997, 95998, max(ranges)}
    with wat.open('rb') as stream:
        for idx, start, end, line, begin, finish, size in con.execute('SELECT * FROM functions ORDER BY idx'):
            assert ranges[idx] == (begin, finish, size)
            assert previous_end <= start < end <= wat.stat().st_size
            stream.seek(start)
            header = stream.readline()
            assert header.startswith(f'  (func (;{idx};)'.encode()), idx
            previous_end = end
            checked += 1
            if idx in selected_ids:
                selected.append({'idx': idx, 'wat_line': line, 'wat_start': start, 'wat_end': end,
                                 'body_start': begin, 'body_end': finish, 'body_bytes': size,
                                 'body_sha256': hashlib.sha256(binary[begin:finish]).hexdigest(),
                                 'header': header.decode().rstrip()})
        assert checked == len(ranges) == counts['functions']
        call_samples = []
        for offset in sorted({0, 1, 4, counts['calls'] // 2, counts['calls'] - 2, counts['calls'] - 1}):
            row = con.execute('SELECT * FROM calls ORDER BY rowid LIMIT 1 OFFSET ?', (offset,)).fetchone()
            caller, callee, at, line, operation = row
            stream.seek(at)
            actual = stream.readline().strip().rstrip(b')').strip().decode()
            assert actual == f'{operation} {callee}', row
            call_samples.append({'caller': caller, 'callee': callee, 'wat_line': line,
                                 'instruction': actual})
        memop_samples = []
        for offset in (0, counts['memops'] // 2, counts['memops'] - 1):
            row = con.execute('SELECT * FROM memops ORDER BY rowid LIMIT 1 OFFSET ?', (offset,)).fetchone()
            idx, operation, field, at, line = row
            stream.seek(at)
            actual = stream.readline().strip().decode()
            assert actual.split()[0].rstrip(')') == operation
            encoded = re.search(r'\boffset=(\d+)', actual)
            assert (int(encoded[1]) if encoded else 0) == field
            memop_samples.append({'function_idx': idx, 'wat_line': line, 'operation': operation,
                                  'encoded_offset': field})
        constant_samples = []
        for offset in (0, counts['iconsts'] // 2, counts['iconsts'] - 1):
            row = con.execute('SELECT * FROM iconsts ORDER BY rowid LIMIT 1 OFFSET ?', (offset,)).fetchone()
            idx, value, at, line, operation = row
            stream.seek(at)
            actual = stream.readline().strip().rstrip(b')').strip().decode()
            assert actual == f'{operation} {value}'
            constant_samples.append({'function_idx': idx, 'wat_line': line, 'instruction': actual})
    kinds = dict(con.execute('SELECT instruction,count(*) FROM calls GROUP BY instruction'))
    integer_kinds = dict(con.execute('SELECT operation,count(*) FROM iconsts GROUP BY operation'))
    con.close()
    assert sha(database) == manifest['database_sha256']
    exports = identity['exports']
    assert next(e for e in exports if e['name'] == '__wbindgen_malloc')['index'] == 91941
    assert next(e for e in exports if e['name'] == 'start')['index'] == 4253
    assert not identity['implicit_start_section']
    return {'status': 'passed', 'target_version': VERSION, 'build': BUILD,
            'original_sha256': SOURCE_SHA, 'database_sha256': manifest['database_sha256'],
            'wat_sha256': manifest['wat_sha256'], 'read_only_sqlite': True,
            'function_headers_and_binary_ranges_checked': checked, 'counts': counts,
            'call_instruction_counts': kinds, 'integer_instruction_counts': integer_kinds,
            'all_sections_hash_checked': len(identity['sections']),
            'all_data_payloads_hash_checked': len(identity['data_segments']),
            'exports': len(exports), 'selected_function_readback': selected,
            'call_readback_samples': call_samples, 'memop_readback_samples': memop_samples,
            'constant_readback_samples': constant_samples,
            'target_executed': False, 'network_used': False, 'installed_app_or_save_writes': False,
            'scope': 'Static range/header/hash and sampled indexed-instruction readback; not gameplay or runtime proof'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = verify(args.profile)
    result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    result['verification_script_sha256'] = sha(Path(__file__))
    path = args.profile / 'verification.json'
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'path': str(path), 'status': result['status'],
                      'functions_checked': result['function_headers_and_binary_ranges_checked'],
                      'sha256': sha(path), 'elapsed_seconds': result['elapsed_seconds']}))


if __name__ == '__main__':
    main()
