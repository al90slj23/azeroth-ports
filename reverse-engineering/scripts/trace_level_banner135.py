#!/usr/bin/env python3
"""RO SQLite/WAT and original data provenance for4630 growth150; no execution."""
from pathlib import Path
import hashlib
import json
import sqlite3
import struct

from build_full135_oracle import SOURCE, SOURCE_SHA, parse_source

ROOT = Path(__file__).resolve().parents[1]


def trace_level_banner135(out):
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    _, _, _, bodies, segments = parse_source(raw)

    def data(pointer, count):
        assert 0 <= count <= 1048576
        result = bytearray(count)
        for segment in segments:
            if segment['address'] is None:
                continue
            a = max(pointer, segment['address'])
            b = min(pointer + count, segment['address'] + segment['length'])
            if a < b:
                offset = segment['file_offset'] + a - segment['address']
                result[a - pointer:b - pointer] = raw[offset:offset + b - a]
        return bytes(result)

    profile = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
    db = sqlite3.connect((profile / 'index.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('pragma query_only=on')
    functions = []
    with (profile / 'official-0.135.1-full.wat').open('rb') as stream:
        for index in (4630, 1512, 19964, 82070, 28964, 32246, 8628):
            row = dict(db.execute('select * from functions where idx=?', (index,)).fetchone())
            assert bodies[index] == (row['body_start'], row['body_end'])
            assert row['wat_end'] - row['wat_start'] < 524288
            stream.seek(row['wat_start'])
            text = stream.read(row['wat_end'] - row['wat_start'])
            (out / f'level-banner-{index}.wat').write_bytes(text)
            functions.append(dict(row,
                body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),
                wat_sha256=hashlib.sha256(text).hexdigest(),
                callees=[r[0] for r in db.execute(
                    'select distinct callee from calls where caller=? order by callee', (index,))]))
    db.close()
    growth = data(1587933, 88).decode('utf8')
    stacks = data(1588041, 62).decode('utf8')
    languages = []
    for index in (0, 11):
        pointer = 5212184 + 28 * index
        row = struct.unpack('<7I', data(pointer, 28))
        assert row[1] < 16 and row[3] < 64 and row[5] < 1048576
        dictionary_raw = data(row[4], row[5])
        dictionary = json.loads(dictionary_raw)
        languages.append(dict(index=index, table_pointer=pointer,
            table28_hex=data(pointer, 28).hex(),
            code=data(row[0], row[1]).decode('utf8'),
            label=data(row[2], row[3]).decode('utf8'),
            dictionary_pointer=row[4], dictionary_bytes=row[5],
            dictionary_sha256=hashlib.sha256(dictionary_raw).hexdigest(),
            growth=dictionary.get(growth, growth), stacks=dictionary.get(stacks, stacks)))
    result = dict(version='0.135.1', actual_build='90898d5e3',
        historical_build_alias='0898d5e3', original_sha256=SOURCE_SHA,
        original_executed=False, full_WAT_read=False, SQLite_mode='ro/query_only',
        functions=functions, growth_key_pointer=1587933, growth_key_bytes=88,
        growth_key=growth, stacks_key_pointer=1588041, stacks_key_bytes=62,
        stacks_key=stacks, format_damage_health_hex=data(1588021, 6).hex(),
        format_regeneration_hex=data(1588033, 8).hex(),
        initial_locale_words28_hex=data(14384320, 28).hex(),
        locale_default_index_pointer=14384328, locale_Once_byte_pointer=14384344,
        locale_Once_unmodified=True, declared_languages=languages,
        rules=['Every successful per-level4630 transition calls1512, emits growth150/type10, then heals and loops.',
            'Growth has no phase/mode/difficulty/choice flag gate; choice2159 guards occur after the level loop.',
            'Damage=f32(f32(new1540-old1540)*100),health=f32(new1536-old1536),regen=f32(new1576-old1576).',
            'Rust format specifications are signed fixed precision0/0/2.',
            'If any owned definition84==6 and new1608>old1608, append DOTstack banner with min(new1608,3)+1.',
            '28964 payload=type10:u8,zero:u32,zero:u64,len(UTF8)+1:u32,UTF8,NUL,NUL.',
            '19964 naturally invokes82070 when Once byte!=3; no injected Once/hashmap is used.'])
    (out / 'level-banner135-static.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result
