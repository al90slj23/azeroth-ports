#!/usr/bin/env python3
"""Index base MPQs and differentially read every named block against StormLib.

Original assets remain local. Only DBC containers are copied to ignored
evidence, without executing any game or resource script. Asset precedence and
semantic DBC columns remain unknown until their original consumers are traced.
"""
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import sqlite3
import sys
import time

from mpq_storm_reference import Storm
from mpq_toolchain import sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction'))
from resource_spec.mpq import Archive, EXISTS, normalized_name
from resource_spec.dbc import DBC

ORIGINALS = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'
EXPECTED = {
    'patch.MPQ': '6828b191789acdf61b0b8749327cfaed726bea7f015f8be4cc9b0abbfcb696f4',
    'patch-2.MPQ': '366edee41642a5dda22ed90cc252b543ee375755b7e8bee81e2a6cd59fd7b286',
    'patch-3.MPQ': '75c35ca5b8075197252581e301e8900143007fdf37b493ad271ae1bd39f95a29',
    'patch-4.MPQ': '2e895e0e0ff6a4781d0e0aaa6ea7d32ed1fe36841e17806fe1855cb880d18865',
    'patch-5.MPQ': '5008e56873718b468fa5ae1b697dcbe4f5da9ffe6c793f3ef9939dbd7716f3d8',
    'patch-6.MPQ': 'cad6ff59b5df028a507581befb836fce07894057e15fe63d9fdc553a95b7ceb5',
    'patch-7.MPQ': 'f5fb15b181cf01cc6b5cf2ee9948a27ecc4ba27bab9a8bec584df4381932aae6',
}
SOURCES = ('scripts/resource_index.py', 'scripts/mpq_toolchain.py', 'scripts/mpq_storm_reference.py',
           'reconstruction/resource_spec/__init__.py', 'reconstruction/resource_spec/mpq.py',
           'reconstruction/resource_spec/dbc.py')


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deadline-seconds', type=int, default=180)
    args = parser.parse_args()
    started = time.monotonic()
    deadline = started + args.deadline_seconds
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('resource-index-base-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    (out / 'dbc').mkdir()
    source_before = {name: sha(ROOT / name) for name in SOURCES}
    originals_before = {name: sha(ORIGINALS / name) for name in EXPECTED}
    if originals_before != EXPECTED:
        raise ValueError('Base MPQ identities differ')
    storm = Storm()
    save(out / 'source-before.json', source_before)
    for name in SOURCES:
        snapshot = out / 'source-snapshot' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((ROOT / name).read_bytes())
    save(out / 'originals-before.json', originals_before)
    save(out / 'reference-toolchain.json', storm.identity)
    database = out / 'index.sqlite'
    con = sqlite3.connect(database)
    con.executescript('''
      CREATE TABLE archives (name TEXT PRIMARY KEY, sha256 TEXT, bytes INTEGER,
        hash_entries INTEGER, block_entries INTEGER, listfile_names INTEGER,
        hash_live INTEGER, named_blocks INTEGER, unnamed_blocks INTEGER,
        sector_bytes INTEGER, hash_table_sha256 TEXT, block_table_sha256 TEXT);
      CREATE TABLE files (archive TEXT, name TEXT, normalized_name TEXT,
        extension TEXT, hash_slot INTEGER, block_index INTEGER, locale INTEGER,
        platform INTEGER, data_offset INTEGER, stored_bytes INTEGER,
        decoded_bytes INTEGER, flags INTEGER, decoded_sha256 TEXT,
        reference_sha256 TEXT, first16_hex TEXT, PRIMARY KEY(archive,name));
      CREATE TABLE dbc (archive TEXT, name TEXT, rows INTEGER, fields INTEGER,
        record_bytes INTEGER, strings_bytes INTEGER, first_column_distinct INTEGER,
        extracted_path TEXT, sha256 TEXT, PRIMARY KEY(archive,name));
    ''')
    archive_rows, dbc_rows = [], []
    extensions = Counter()
    actual_bytes = mismatches = count = 0
    # Physical archive order here is inventory order, not proven game priority.
    for filename in EXPECTED:
        if time.monotonic() > deadline:
            raise TimeoutError('Owned indexing deadline exceeded')
        path = ORIGINALS / filename
        archive = Archive(path)
        names = (*archive.listfile(), '(listfile)')
        if len(set(names)) != len(names):
            raise ValueError('Duplicate exact path in listfile')
        named_blocks = set()
        with storm.archive(path) as reference:
            for name in names:
                if time.monotonic() > deadline:
                    raise TimeoutError('Owned indexing deadline exceeded')
                entry = archive.lookup(name)
                block = archive.blocks[entry.block]
                decoded = archive.read(name)
                original = reference.read(name)
                digest = hashlib.sha256(decoded).hexdigest()
                other = hashlib.sha256(original).hexdigest()
                if decoded != original:
                    mismatches += 1
                named_blocks.add(entry.block)
                ext = PureWindowsPath(name).suffix.lower()
                extensions[ext] += 1
                con.execute('INSERT INTO files VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (filename, name, normalized_name(name).decode('latin1'), ext,
                     entry.slot, entry.block, entry.locale, entry.platform, block.offset,
                     block.compressed_size, block.size, block.flags, digest, other, decoded[:16].hex()))
                if ext == '.dbc':
                    container = DBC.parse(decoded)
                    dest = out / 'dbc' / (filename + '--' + PureWindowsPath(name).name)
                    dest.write_bytes(decoded)
                    if sha(dest) != digest:
                        raise ValueError('DBC extracted readback differs')
                    distinct = (len({container.word(i, 0) for i in range(container.rows)})
                                if container.record_bytes == container.fields * 4 else None)
                    item = {'archive': filename, 'name': name, 'rows': container.rows,
                            'fields': container.fields, 'record_bytes': container.record_bytes,
                            'strings_bytes': container.strings_bytes, 'first_column_distinct': distinct,
                            'extracted_path': str(dest.relative_to(out)), 'sha256': digest}
                    dbc_rows.append(item)
                    con.execute('INSERT INTO dbc VALUES (?,?,?,?,?,?,?,?,?)', tuple(item.values()))
                actual_bytes += len(decoded)
                count += 1
        live = {i for i, block in enumerate(archive.blocks) if block.flags & EXISTS}
        if not named_blocks <= live:
            raise ValueError('Named blocks do not refer to live files')
        item = {'name': filename, 'sha256': EXPECTED[filename], 'bytes': path.stat().st_size,
                'hash_entries': len(archive.hashes), 'block_entries': len(archive.blocks),
                'listfile_names': len(names) - 1, 'hash_live': sum(e.block < 0xfffffffe for e in archive.hashes),
                'named_blocks': len(named_blocks), 'unnamed_blocks': len(live - named_blocks),
                'sector_bytes': archive.sector_size,
                'hash_table_sha256': hashlib.sha256(archive.hash_table_bytes).hexdigest(),
                'block_table_sha256': hashlib.sha256(archive.block_table_bytes).hexdigest()}
        archive_rows.append(item)
        con.execute('INSERT INTO archives VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', tuple(item.values()))
        con.commit()
        print(json.dumps({'archive': filename, 'named_blocks': len(named_blocks),
                          'unnamed_blocks': item['unnamed_blocks'], 'total_compared': count}, allow_nan=False), flush=True)
    con.executescript('CREATE INDEX file_paths ON files(normalized_name); CREATE INDEX file_extensions ON files(extension);')
    integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
    unique_names = con.execute('SELECT count(DISTINCT normalized_name) FROM files').fetchone()[0]
    duplicates = con.execute('SELECT normalized_name, count(*) FROM files GROUP BY normalized_name HAVING count(*)>1').fetchall()
    con.commit()
    con.close()
    if integrity != 'ok':
        raise ValueError('Index integrity differs')
    source_after = {name: sha(ROOT / name) for name in SOURCES}
    originals_after = {name: sha(ORIGINALS / name) for name in EXPECTED}
    if source_after != source_before or originals_after != originals_before:
        raise ValueError('Source or original changed during indexing')
    save(out / 'source-after.json', source_after)
    save(out / 'originals-after.json', originals_after)
    save(out / 'dbc-manifest.json', dbc_rows)
    save(out / 'duplicate-paths.json', duplicates)
    result = {'at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'passed' if not mismatches else 'failed',
              'source_kind': 'User complete base RAR, partially byte-matched to official source; all-local CRC verified',
              'base_archive_exe_version': '0.102.3', 'latest_program_version_is_separate': '0.135.1',
              'archives': archive_rows, 'compared_named_files_including_internal_listfiles': count,
              'decoded_bytes_compared': actual_bytes, 'mismatch_files': mismatches,
              'unique_normalized_paths': unique_names, 'duplicate_paths_across_archives': len(duplicates),
              'extensions': dict(extensions.most_common()), 'dbc_count': len(dbc_rows),
              'dbc_rows_total': sum(x['rows'] for x in dbc_rows),
              'dbc_decoded_bytes': sum((out / x['extracted_path']).stat().st_size for x in dbc_rows),
              'index_sha256': sha(database), 'index_integrity': integrity,
              'source_sha256_before': source_before, 'source_sha256_after': source_after,
              'reference_library_sha256': storm.identity['library_sha256'],
              'reference_release': storm.identity['release_tag'], 'reference_commit': storm.identity['commit'],
              'artifact_sha256': {name: sha(out / name) for name in ('source-before.json', 'source-after.json', 'originals-before.json', 'originals-after.json', 'reference-toolchain.json', 'dbc-manifest.json', 'duplicate-paths.json')},
              'elapsed_seconds': time.monotonic() - started, 'deadline_seconds': args.deadline_seconds,
              'original_game_executed': False, 'asset_scripts_executed': False,
              'installed_apps_or_user_saves_modified': False,
              'limitations': ['Archive bytes belong to the base resource pack, not proof of0.135.1 asset equivalence.',
                  'All actual files are uncompressed/unencrypted classic blocks; unsupported/other codec branches are not accepted by this real-asset differential.',
                  'DBC container layout only: semantic column mappings and game consumers remain unresolved.',
                  'Cross-archive override priority, runtime path aliases and resource lifecycle are not yet proven.',
                  'Models, textures, terrain, animation, effects and audio are indexed, not rendered or integrated into a playable replacement.']}
    save(out / 'summary.json', result)
    print(json.dumps({'evidence_directory': str(out), 'files': count, 'mismatches': mismatches,
                      'dbc_count': len(dbc_rows), 'elapsed_seconds': result['elapsed_seconds']}, allow_nan=False), flush=True)
    if mismatches:
        raise SystemExit('Independent MPQ file payload differs from pinned StormLib')


if __name__ == '__main__':
    main()
