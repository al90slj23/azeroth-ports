#!/usr/bin/env python3
"""Freeze fixed0.135.1 static empty-account companion discriminator lineage."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sqlite3
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source

PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT_SHA = '15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
INDICES = (2922, 880, 6730, 1560, 1744, 1089)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def compact(text):
    return '\n'.join(line.strip() for line in text.splitlines())


def main():
    script = Path(__file__).resolve(); before = sha(script)
    raw = SOURCE.read_bytes(); assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    _, _, _, bodies, _ = parse_source(raw)
    wat = PROFILE / 'official-0.135.1-full.wat'
    assert sha(wat) == WAT_SHA
    con = sqlite3.connect((PROFILE / 'index.sqlite').resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('profile-companions0135-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(); functions = []; texts = {}
    with wat.open('rb') as stream:
        for index in INDICES:
            row = dict(con.execute('select * from functions where idx=?', (index,)).fetchone())
            assert (row['body_start'], row['body_end']) == bodies[index]
            stream.seek(row['wat_start']); source = stream.read(row['wat_end']-row['wat_start'])
            assert source.splitlines()[0].startswith(f'  (func (;{index};)'.encode())
            (out / f'{index}.wat').write_bytes(source); texts[index] = compact(source.decode())
            functions.append(dict(index=index, **row, wat_sha256=hashlib.sha256(source).hexdigest(),
                body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest()))
    required = {
        2922: ('local.get 1\ni32.load offset=244',
            'i32.const 255\nlocal.set 11\nlocal.get 8\nlocal.get 10\ni32.add\nlocal.tee 15\ni32.eqz\nif  ;; label = @5\ni32.const 255\nlocal.set 10\nbr 4 (;@1;)',
            'local.get 0\nlocal.get 11\ni32.store8 offset=12',
            'local.get 0\nlocal.get 10\ni32.store8 offset=4'),
        880: ('local.get 0\ni32.const 3600\ni32.add\nlocal.set 111',
            'local.get 4\nlocal.get 76\ncall 2922',
            'local.get 111\nlocal.get 3\ni64.load offset=1488\ni64.store',
            'local.get 111\nlocal.get 3\ni64.load offset=1496\ni64.store offset=8'),
        6730: ('local.get 18\nlocal.get 1\ni64.load offset=3600\ni64.store offset=3544',
            'local.get 18\nlocal.get 1\ni64.load offset=3608\ni64.store offset=3552',
            'local.get 18\ni32.const 3136\ni32.add\nlocal.get 18\ni32.const 32\ni32.add\ni32.const 152\nmemory.copy',
            'local.get 18\ni32.const 352\ni32.add\nlocal.get 4\nlocal.get 2\ncall 1560'),
        1560: ('local.get 3\ni32.const 104\ni32.add\nlocal.get 1\ni32.const 376\nmemory.copy',
            'local.get 0\nlocal.get 1\ni32.const 2592\nmemory.copy'),
        1744: ('local.get 0\ni32.const 256\ni32.add\ni32.store offset=52',
            'local.get 0\ni32.const 240\ni32.add\ni32.store offset=48',
            'i32.load8_u\nlocal.tee 4\ni32.const 255\ni32.eq\nbr_if 0 (;@6;)'),
        1089: ('local.get 0\ncall 1744',),
    }
    snippets = []
    for index, needles in required.items():
        lines = (out / f'{index}.wat').read_text().splitlines()
        for needle in needles:
            assert needle in texts[index], (index, needle)
            line = texts[index][:texts[index].index(needle)].count('\n') + 1
            snippets.append(dict(function=index, first_line=line,
                last_line=line+needle.count('\n'), instructions=needle.splitlines()))
    result = dict(version='0.135.1', build='0898d5e3', original_sha256=SOURCE_SHA,
        full_wat_sha256=WAT_SHA, script_sha256=before, functions=functions, verified_snippets=snippets,
        lineage=[
            'Explicit empty account16B flags: account+244 count0 in2922.',
            'No flags leaves the two entitlement booleans0;2922 sets both tags255 and exits before definition lookup.',
            '2922 output+4/+12 ->880 temporary4648+4/+12 ->1488+4/+12 ->App3600+4/+12.',
            '6730 App3600/3608 ->temp3544/3552 ->selected376+224/+232; tags+228/+236.',
            '1560 copies selected376 toGame+16: slot startsGame240/248, tagsGame244/252.',
            '1744 walksGame240..256 by8 and skips255 before dereferencing a definition or incrementing counter.',
            '1089 calls1744 before four5736 NPCs, two kind2 pickups and boundaries.'],
        scope='Only empty account companion absence; no other2922/profile/account producer claim.',
        original_executed=False, source_changed=False, new_original_cases=0)
    target = out / 'trace.json'; target.write_text(json.dumps(result, indent=2) + '\n')
    assert sha(script) == before and sha(SOURCE) == SOURCE_SHA
    print(json.dumps(dict(directory=str(out), trace_sha256=sha(target), functions=len(functions),
                          verified_snippets=len(snippets), original_executed=False)))


if __name__ == '__main__':
    main()
