#!/usr/bin/env python3
"""Differential classic MPQ codec checks using pinned StormLib-written data.

Synthetic payloads contain no game assets. Original-asset coverage is separately
recorded by resource_index.py; these counts must not be added to that inventory.
"""
from datetime import datetime, timezone
import ctypes as c
import hashlib
import json
from pathlib import Path
import random
import sys

from mpq_storm_reference import Storm
from mpq_toolchain import sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction'))
from resource_spec.mpq import (Archive, COMPRESS, ENCRYPTED, FIX_KEY, SINGLE_UNIT,
                               UnsupportedMPQ, hash_name)


def main():
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('mpq-reader-check-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    source_files = ('scripts/mpq_reader_check.py', 'scripts/mpq_storm_reference.py',
                    'scripts/mpq_toolchain.py', 'reconstruction/resource_spec/mpq.py')
    before = {name: sha(ROOT / name) for name in source_files}
    for name in source_files:
        snapshot = out / 'source-snapshot' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((ROOT / name).read_bytes())
    storm = Storm()
    lib = storm.lib
    signatures = {
        'SFileCreateArchive': ([c.c_char_p, c.c_uint32, c.c_uint32, c.POINTER(c.c_void_p)], c.c_bool),
        'SFileCreateFile': ([c.c_void_p, c.c_char_p, c.c_uint64, c.c_uint32, c.c_uint32, c.c_uint32, c.POINTER(c.c_void_p)], c.c_bool),
        'SFileWriteFile': ([c.c_void_p, c.c_void_p, c.c_uint32, c.c_uint32], c.c_bool),
        'SFileFinishFile': ([c.c_void_p], c.c_bool),
    }
    for name, (args, result) in signatures.items():
        getattr(lib, name).argtypes, getattr(lib, name).restype = args, result
    rng = random.Random(0xa2e0b10c)
    payloads = [b'', b'x', b'abc', b'abcd', b'A' * 4095, b'B' * 4096,
                b'C' * 4097, bytes(range(256)) * 33, rng.randbytes(12291)]
    domains = [(0, 0), (SINGLE_UNIT, 0), (COMPRESS, 2), (COMPRESS, 16),
               (ENCRYPTED, 0), (ENCRYPTED | FIX_KEY, 0),
               (COMPRESS | ENCRYPTED, 2), (COMPRESS | ENCRYPTED | FIX_KEY, 2),
               (COMPRESS | ENCRYPTED | SINGLE_UNIT, 2),
               (COMPRESS | ENCRYPTED | FIX_KEY | SINGLE_UNIT, 16)]
    fixtures = []
    archive_path = out / 'synthetic.mpq'
    handle = c.c_void_p()
    if not lib.SFileCreateArchive(str(archive_path).encode(), 0, 1024, c.byref(handle)):
        raise ValueError('StormLib synthetic archive creation failed')
    try:
        for group, (flags, compression) in enumerate(domains):
            for i, payload in enumerate(payloads):
                name = f'Checks\\group{group}\\payload{i}.bin'
                file = c.c_void_p()
                if not lib.SFileCreateFile(handle, name.encode(), 0, len(payload), 0, flags, c.byref(file)):
                    raise ValueError('StormLib synthetic file creation failed')
                buffer = c.create_string_buffer(payload)
                if not lib.SFileWriteFile(file, buffer, len(payload), compression):
                    raise ValueError('StormLib synthetic payload write failed')
                if not lib.SFileFinishFile(file):
                    raise ValueError('StormLib synthetic file finalization failed')
                fixtures.append({'id': len(fixtures), 'name': name, 'flags_requested': flags,
                                 'compression_requested': compression, 'payload_hex': payload.hex(),
                                 'payload_sha256': hashlib.sha256(payload).hexdigest()})
    finally:
        if not lib.SFileCloseArchive(handle):
            raise ValueError('StormLib writer close failed')
    (out / 'fixtures.json').write_text(json.dumps(fixtures, indent=2) + '\n')
    archive = Archive(archive_path)
    rows = []
    with storm.archive(archive_path) as reference:
        for fixture in fixtures:
            expected = bytes.fromhex(fixture['payload_hex'])
            for name in (fixture['name'], fixture['name'].upper()):
                decoded = archive.read(name)
                original = reference.read(name)
                if expected != decoded or expected != original:
                    raise ValueError('Synthetic independent/reference/payload mismatch')
            entry = archive.lookup(fixture['name'])
            block = archive.blocks[entry.block]
            rows.append({'id': fixture['id'], 'name': fixture['name'],
                         'actual_flags': block.flags, 'stored_bytes': block.compressed_size,
                         'decoded_bytes': len(decoded), 'sha256': hashlib.sha256(decoded).hexdigest()})
    # Negative framing checks are contract checks, not original-game behavior.
    negative = []
    try:
        archive.read(fixtures[-1]['name'], max_bytes=1)
        raise AssertionError('Expected byte-budget rejection')
    except ValueError:
        negative.append('decoded_byte_budget')
    try:
        archive.read('Checks\\missing.bin')
        raise AssertionError('Expected missing name rejection')
    except FileNotFoundError:
        negative.append('missing_path')
    with storm.archive(archive_path) as reference:
        for reader in (archive, reference):
            try:
                reader.read(fixtures[0]['name'].replace('\\', '/'))
                raise AssertionError('Unexpected implicit separator alias')
            except FileNotFoundError:
                pass
        negative.append('slash_alias_not_implicitly_added_both_readers')
    after = {name: sha(ROOT / name) for name in source_files}
    if before != after:
        raise ValueError('Source changed during synthetic comparison')
    (out / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
    summary = {'status': 'passed', 'synthetic_payload_cases': len(fixtures),
               'name_variants_per_case': 2, 'payload_mismatches': 0,
               'contract_checks_not_original_game_cases': negative,
               'source_sha256_before': before, 'source_sha256_after': after,
               'reference_library_sha256': storm.identity['library_sha256'],
               'reference_commit': storm.identity['commit'],
               'artifact_sha256': {name: sha(out / name) for name in ('synthetic.mpq', 'fixtures.json', 'results.json')},
               'original_game_executed': False, 'actual_game_asset_cases': 0}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'evidence_directory': str(out), 'synthetic_cases': len(fixtures),
                      'mismatches': 0, 'original_game_executed': False}))


if __name__ == '__main__':
    main()
