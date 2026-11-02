#!/usr/bin/env python3
"""Freeze thirty indexed139 entry bodies as the1391 migration baseline."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, sqlite3, sys
sys.dont_write_bytecode = True
from wasm139_profile import ROOT, SOURCE, SOURCE_SHA, binary_identity

MAPPING = ROOT / 'evidence/engine139-refined-static-20261102T013743.612949Z/mapping.json'
MAPPING_SHA = '7b41961bce7f45e74a8d2a24305cf84d0d64f2f2d739c723b1e445af208c40f0'
PROFILE = ROOT / 'evidence/wasm0139-profile-20261102T012426.951871Z'


def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert sha(MAPPING) == MAPPING_SHA and sha(SOURCE) == SOURCE_SHA
    mapping = json.loads(MAPPING.read_text())
    manifest = json.loads((PROFILE / 'manifest.json').read_text())
    assert manifest['original_sha256'] == SOURCE_SHA and manifest['full_module_validated']
    raw = SOURCE.read_bytes()
    identity, ranges = binary_identity(raw)
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('engine1391-baseline139-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    before = {n: sha(ROOT / n) for n in ('scripts/prepare_engine1391_baseline139.py', 'scripts/wasm139_profile.py',
                                        'scripts/wasm134_profile.py', 'scripts/wasm_index.py')}
    for n, digest in before.items():
        target = out / 'source-snapshot' / n
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / n).read_bytes())
        assert sha(target) == digest
    entries, total = [], 0
    with sqlite3.connect((PROFILE / 'index.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db, Path(manifest['wat_path']).open('rb') as stream:
        db.row_factory = sqlite3.Row
        db.execute('pragma query_only=on')
        for entry in mapping['entries']:
            binding = entry['new']
            idx = binding['index']
            a, b, size = ranges[idx]
            assert hashlib.sha256(raw[a:b]).hexdigest() == binding['body_sha256']
            row = dict(db.execute('select * from functions where idx=?', (idx,)).fetchone())
            assert (a, b, size) == (row['body_start'], row['body_end'], row['body_bytes'])
            length = row['wat_end'] - row['wat_start']
            assert length <= 6_500_000 and total + length <= 20_000_000
            stream.seek(row['wat_start'])
            wat = stream.read(length)
            total += length
            assert wat.startswith(f'  (func (;{idx};)'.encode()) and hashlib.sha256(wat).hexdigest() == binding['wat_sha256']
            (out / f'139-{idx}.wat').write_bytes(wat)
            entries.append(dict(role=entry['role'], binding=binding, binding_proofs=entry['binding_proofs'],
                                original_executions=0, behavioral_acceptance_transferred=False))
    assert len(entries) == 30 and len({e['role'] for e in entries}) == 30
    assert before == {n: sha(ROOT / n) for n in before} and sha(SOURCE) == SOURCE_SHA
    result = dict(version='0.139.0', build='f79c5e2b4', kind='bounded139_thirty_entry_static_baseline_for1391',
                  mapping_sha256=MAPPING_SHA, original_sha256=SOURCE_SHA, entries=entries,
                  profile_manifest_sha256=sha(PROFILE / 'manifest.json'), WAT_seek_bytes=total,
                  sources_before=before, sources_after=before, target_executions=0,
                  model_executions=0, native_executions=0, acceptance_transferred=False)
    save(out / 'baseline.json', result)
    print(json.dumps(dict(directory=str(out), baseline_sha256=sha(out / 'baseline.json'), entries=30,
                          WAT_seek_bytes=total, original_executions=0)), flush=True)


if __name__ == '__main__':
    main()
