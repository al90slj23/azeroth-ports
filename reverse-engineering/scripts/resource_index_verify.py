#!/usr/bin/env python3
"""Read back a completed resource index, every named block and extracted DBC."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from mpq_toolchain import sha, verify
from resource_index import EXPECTED, ORIGINALS, ROOT
sys.path.insert(0, str(ROOT / 'reconstruction'))
from resource_spec.mpq import Archive, normalized_name
from resource_spec.dbc import DBC


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--synthetic-directory', type=Path, required=True)
    args = parser.parse_args()
    out = args.directory.resolve()
    synthetic = args.synthetic_directory.resolve()
    if not out.is_relative_to((ROOT / 'evidence').resolve()) or not synthetic.is_relative_to((ROOT / 'evidence').resolve()):
        raise ValueError('Only project-local evidence is accepted')
    summary = json.loads((out / 'summary.json').read_text())
    if summary['status'] != 'passed' or summary['mismatch_files']:
        raise ValueError('A complete passed differential is required')
    for name, value in summary['source_sha256_before'].items():
        if summary['source_sha256_after'][name] != value or sha(ROOT / name) != value or sha(out / 'source-snapshot' / name) != value:
            raise ValueError('Current/frozen source identity differs')
    if sha(out / 'index.sqlite') != summary['index_sha256']:
        raise ValueError('Index digest differs')
    for name, value in summary['artifact_sha256'].items():
        if sha(out / name) != value:
            raise ValueError('Index artifact identity differs')
    tool = verify()
    if tool['library_sha256'] != summary['reference_library_sha256']:
        raise ValueError('Reference library identity differs')
    con = sqlite3.connect(f'file:{out / "index.sqlite"}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ValueError('Index integrity differs')
    count = 0
    for filename in EXPECTED:
        archive = Archive(ORIGINALS / filename)
        rows = con.execute('SELECT * FROM files WHERE archive=?', (filename,)).fetchall()
        if {row['name'] for row in rows} != set((*archive.listfile(), '(listfile)')):
            raise ValueError('Indexed paths do not match original listfile')
        block_indices = set()
        for row in rows:
            entry = archive.lookup(row['name'])
            block = archive.blocks[entry.block]
            if (entry.slot, entry.block, entry.locale, entry.platform, block.offset, block.compressed_size, block.size, block.flags) != tuple(row[name] for name in ('hash_slot', 'block_index', 'locale', 'platform', 'data_offset', 'stored_bytes', 'decoded_bytes', 'flags')):
                raise ValueError('Indexed block metadata differs from original table')
            if row['decoded_sha256'] != row['reference_sha256'] or row['normalized_name'] != normalized_name(row['name']).decode('latin1'):
                raise ValueError('Persisted original/reference metadata differs')
            block_indices.add(entry.block)
            count += 1
        if block_indices != set(range(len(archive.blocks))):
            raise ValueError('A block remains unnamed or is missing from index')
    if count != summary['compared_named_files_including_internal_listfiles']:
        raise ValueError('Indexed named block count differs')
    dbc_count = packed = 0
    for row in con.execute('SELECT * FROM dbc'):
        data = (out / row['extracted_path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Extracted DBC readback differs')
        dbc = DBC.parse(data)
        if (dbc.rows, dbc.fields, dbc.record_bytes, dbc.strings_bytes) != tuple(row[name] for name in ('rows', 'fields', 'record_bytes', 'strings_bytes')):
            raise ValueError('DBC persisted layout differs')
        if len(dbc.records) + len(dbc.strings) + 20 != len(data):
            raise ValueError('DBC framing differs')
        if dbc.record_bytes != dbc.fields * 4:
            packed += 1
            try:
                dbc.word(0, 0)
                raise AssertionError('Packed field schema was silently assumed')
            except ValueError:
                pass
        dbc_count += 1
    if dbc_count != summary['dbc_count']:
        raise ValueError('DBC count differs')
    synth = json.loads((synthetic / 'summary.json').read_text())
    if synth['status'] != 'passed' or synth['payload_mismatches'] or synth['actual_game_asset_cases']:
        raise ValueError('Synthetic evidence scope differs')
    for name, value in synth['source_sha256_before'].items():
        if synth['source_sha256_after'][name] != value or sha(ROOT / name) != value or sha(synthetic / 'source-snapshot' / name) != value:
            raise ValueError('Synthetic source identity differs')
    for name, value in synth['artifact_sha256'].items():
        if sha(synthetic / name) != value:
            raise ValueError('Synthetic artifact identity differs')
    fixtures = json.loads((synthetic / 'fixtures.json').read_text())
    results = json.loads((synthetic / 'results.json').read_text())
    if len(fixtures) != synth['synthetic_payload_cases'] or len(results) != len(fixtures):
        raise ValueError('Synthetic case count differs')
    for i, (fixture, result) in enumerate(zip(fixtures, results)):
        if fixture['id'] != i or result['id'] != i or fixture['payload_sha256'] != result['sha256'] or hashlib.sha256(bytes.fromhex(fixture['payload_hex'])).hexdigest() != result['sha256']:
            raise ValueError('Synthetic persisted payload digest differs')
    result = {'at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'passed',
              'index_rows_and_original_block_bindings_revalidated': count,
              'dbc_readbacks_revalidated': dbc_count, 'packed_unknown_schema_dbc': packed,
              'synthetic_cases_revalidated': len(fixtures),
              'original_payload_differential_reexecuted': False,
              'reference_library_reexecuted': False, 'original_game_executed': False,
              'verifier_source_sha256': sha(__file__),
              'index_summary_sha256': sha(out / 'summary.json'),
              'synthetic_summary_sha256': sha(synthetic / 'summary.json')}
    (out / 'readback-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
