#!/usr/bin/env python3
"""Read only fixed1351202/29629 source ranges; no original execution."""
from pathlib import Path
import hashlib
import json
import sqlite3

from build_full135_oracle import SOURCE, SOURCE_SHA, parse_source

ROOT = Path(__file__).resolve().parents[1]


def trace_resource_aura135(out):
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    _, _, _, bodies, _ = parse_source(raw)
    profile = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
    db = sqlite3.connect((profile / 'index.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('pragma query_only=on')
    records = []
    with (profile / 'official-0.135.1-full.wat').open('rb') as stream:
        for index in (1202, 29629, 30834, 23583):
            row = dict(db.execute('select * from functions where idx=?', (index,)).fetchone())
            assert bodies[index] == (row['body_start'], row['body_end'])
            assert row['wat_end'] - row['wat_start'] < 524288
            stream.seek(row['wat_start'])
            wat = stream.read(row['wat_end'] - row['wat_start'])
            (out / f'aura-{index}.wat').write_bytes(wat)
            records.append(dict(row, wat_sha256=hashlib.sha256(wat).hexdigest(),
                body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),
                callees=[r[0] for r in db.execute(
                    'select distinct callee from calls where caller=? order by callee', (index,))]))
    db.close()
    sources = ('reconstruction/core_spec/resource_aura135.py',
        'reconstruction/core_spec/binary32.py', 'reconstruction/core_spec/record_cells135.py',
        'reconstruction/core_spec/__init__.py', 'scripts/trace_resource_aura135.py',
        'scripts/build_full135_oracle.py', 'scripts/build_upgrade134_oracle.py')
    result = dict(version='0.135.1', actual_build='90898d5e3',
        historical_build_alias='0898d5e3', original_sha256=SOURCE_SHA,
        status='static_rules_restored_pending_original_differential',
        original_calls=0, model_differential_cases=0, native_executions=0,
        SQLite_mode='ro/query_only', full_WAT_read=False, functions=records,
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
        source_domains=['Live kind0, or unique finite nonnegative kind8; other aura producers must be absent by caller-established domain.',
            'Physical old cache is empty or complete48-slot canonical0/1 tags; only bit0 of initialized2569 controls old comparisons.'],
        rules=[
            'Ordered live expiry>now precedes all kind/spell/magnitude reads; expired/NaN expiry contributes no aura.',
            'Ordinary duplicate kind0 same-spell effective magnitudes tie at0: stable first wins before aggregation; it retains first expiry.',
            'Spell774 bypasses dominance filtering and aggregates stack count with maximum expiry.',
            'First32 selected aggregate buffs fill slots0..31; the separate16 negative/control slots are empty in this domain.',
            'Each new slot initially receives only a zero u32 tag; inactive+4..15 remain unknown allocation storage.',
            'An active16B slot is(tag1,spell,expiry_bits,stack_count) as four little-endian u32 words.',
            'Old count!=48 resets comparison cache and initialized2569=0, forcing logical writes for slots/flags/applications.',
            'Old48 and initialized2569 bit0 set only writes logical fields when their compared spelling/packed values change.',
            'Logical spell keys47..94; flag keys95..100 use8 nibbles per field,9 buff/8 debuff for each present slot.',
            'Application keys113..124 pack4 bytes per field: present stack_count>0 maps to min(count,255)-1; absent/zero count maps0.',
            'No key101..112 is written by1202; final cache cap/count48 and initialized2569=1.',
            'No original allocation pointer, full BTree layout or queue payload is predicted by this helper.'],
        pending=['Duplicate kind8 dominance and negative/control sources',
            'Nonempty external timed definitions38, active owned/shield kind12 and kind7 producers',
            'Physical BTree/allocator identity and wire/UI effects',
            'Full1202 beyond the declared live-only source domain'])
    (out / 'resource-aura135-static.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    from datetime import datetime, timezone
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('resource-aura0135-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    trace_resource_aura135(out)
    print(json.dumps(dict(directory=str(out), original_calls=0)))
