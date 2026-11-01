#!/usr/bin/env python3
"""Bind selected resource paths to exact static0.135.1 instruction references.

This preserves raw functions and initial-data addresses only. It does not infer
column semantics, prove runtime reachability, or execute the original WASM.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from extract_catalogue134 import parse_binary
from mpq_toolchain import sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT = PROFILE / 'official-0.135.1-full.wat'
WAT_SHA = '15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
DB_SHA = 'b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
NAMES = ('Map.dbc', 'CreatureModelData.dbc', 'CreatureDisplayInfo.dbc', 'Spell.dbc')


def main():
    if sha(SOURCE) != SOURCE_SHA or sha(WAT) != WAT_SHA or sha(PROFILE / 'index.sqlite') != DB_SHA:
        raise ValueError('Fixed latest static profile identity differs')
    before = {name: sha(ROOT / name) for name in ('scripts/resource_index_consumers135.py', 'scripts/extract_catalogue134.py', 'scripts/mpq_toolchain.py')}
    binary = SOURCE.read_bytes()
    profile = parse_binary(binary)
    if profile['function_imports'] != 878 or profile['defined_functions'] != 175317:
        raise ValueError('Latest source function profile differs')
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('resource-consumers0135-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    con = sqlite3.connect(f'file:{PROFILE / "index.sqlite"}?mode=ro', uri=True)
    paths, functions = [], {}
    with WAT.open('rb') as wat:
        for name in NAMES:
            literal = ('DBFilesClient\\' + name).encode()
            start = 0
            while True:
                file_offset = binary.find(literal, start)
                if file_offset < 0:
                    break
                start = file_offset + len(literal)
                segments = [s for s in profile['segments'] if s['file_start'] <= file_offset < s['file_end']]
                if len(segments) != 1:
                    raise ValueError('Path string is not uniquely backed by initial data')
                segment = segments[0]
                address = segment['memory_start'] + file_offset - segment['file_start']
                refs = []
                for function, offset, line in con.execute('SELECT function_idx,wat_offset,wat_line FROM iconsts WHERE operation="i32.const" AND value=?', (address,)):
                    wat.seek(offset)
                    if wat.readline().strip() != f'i32.const {address}'.encode():
                        raise ValueError('Indexed original path reference differs')
                    refs.append({'function_index': function, 'wat_offset': offset, 'wat_line': line})
                    if function not in functions:
                        a, z, ba, bz = con.execute('SELECT wat_start,wat_end,body_start,body_end FROM functions WHERE idx=?', (function,)).fetchone()
                        wat.seek(a)
                        text = wat.read(z - a)
                        (out / f'function-{function}.wat').write_bytes(text)
                        body = binary[ba:bz]
                        functions[function] = {'index': function, 'body_start': ba, 'body_end': bz,
                            'body_sha256': hashlib.sha256(body).hexdigest(), 'wat_start': a, 'wat_end': z,
                            'wat_sha256': hashlib.sha256(text).hexdigest()}
                paths.append({'path': literal.decode(), 'file_offset': file_offset,
                              'memory_address': address, 'byte_length': len(literal), 'references': refs})
    after = {name: sha(ROOT / name) for name in before}
    if before != after or sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Source changed during trace')
    summary = {'version': '0.135.1', 'build': '0898d5e3', 'source_sha256': SOURCE_SHA,
               'paths': paths, 'complete_original_functions': list(functions.values()),
               'tool_sources_before': before, 'tool_sources_after': after,
               'original_game_executed': False, 'static_path_reference_only': True,
               'dbc_column_semantics_recovered': False}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'evidence_directory': str(out), 'path_literals': len(paths),
                      'functions': sorted(functions), 'static_only': True}))


if __name__ == '__main__':
    main()
