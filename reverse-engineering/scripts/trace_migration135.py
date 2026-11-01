#!/usr/bin/env python3
"""Record fixed134->135 function correspondence and actual layout differences.

Numeric normalization is only a discovery aid. It does not prove equivalence:
the raw bodies/WAT/diffs, signatures and changed sites remain available. Runtime
acceptance is recorded by separate full-original comparison receipts.
"""
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re
import sqlite3

import build_full134_oracle as old
import build_full135_oracle as new

ROOT = new.ROOT
PROFILES = (
    ('0.134.0', ROOT/'evidence/wasm0134-profile-20261101T001728.222975Z',
     'official-0.134.0-full.wat', '6014dab110e40ae279a6450ae15dcc0d84727c31e2da71f18f2cab1f21ec8422',
     'f131b4454ac1a8754f5b0417e4192efbaada6478df737e09490154c71fd340f9'),
    ('0.135.1', ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z',
     'official-0.135.1-full.wat', '15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2',
     'b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'),
)


def normalized(line):
    line = re.sub(r'\(;\d+;\)|\(type \d+\)', '@', line)
    line = re.sub(r'\b((?:return_)?call) \d+', r'\1 @', line)
    line = re.sub(r'\bi(?:32|64)\.const -?\d+', 'i.const @', line)
    return re.sub(r'offset=\d+', 'offset=@', line)


def main():
    binaries = (old.SOURCE.read_bytes(), new.SOURCE.read_bytes())
    assert [hashlib.sha256(b).hexdigest() for b in binaries] == [old.SOURCE_SHA, new.SOURCE_SHA]
    parsed = (old.parse_source(binaries[0]), new.parse_source(binaries[1]))
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('migration0135-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    connections = []
    streams = []
    for _, directory, filename, whash, dhash in PROFILES:
        assert new.sha(directory/filename) == whash and new.sha(directory/'index.sqlite') == dhash
        connections.append(sqlite3.connect(f'file:{directory/"index.sqlite"}?mode=ro', uri=True))
        streams.append((directory/filename).open('rb'))

    def function(side, index, role):
        row = connections[side].execute('SELECT wat_start,wat_end,body_start,body_end FROM functions WHERE idx=?', (index,)).fetchone()
        ws,we,bs,be = row
        assert parsed[side][3][index] == (bs,be)
        streams[side].seek(ws)
        text = streams[side].read(we-ws).decode()
        assert text.startswith(f'  (func (;{index};) ')
        path = out/f'{role}-{side}.wat'; path.write_text(text)
        type_index = parsed[side][2][index-len(parsed[side][1])]
        signature = parsed[side][0][type_index]
        return text, dict(index=index, body_start=bs, body_end=be,
                          body_sha256=hashlib.sha256(binaries[side][bs:be]).hexdigest(),
                          wat_sha256=new.sha(path), parameters_hex=signature[0].hex(),
                          results_hex=signature[1].hex())

    rows = []
    for role in old.ROLES:
        at, ar = function(0, old.ROLES[role][0], role)
        bt, br = function(1, new.ROLES[role][0], role)
        assert ar['parameters_hex'] == br['parameters_hex'] and ar['results_hex'] == br['results_hex']
        assert br['body_sha256'] == new.APPROVED_BODY_SHA[role]
        a,b = at.splitlines(),bt.splitlines()
        na,nb = list(map(normalized,a)),list(map(normalized,b))
        rawdiff = out/f'{role}.diff'
        rawdiff.write_text('\n'.join(difflib.unified_diff(a,b,fromfile='fixed134',tofile='fixed135'))+'\n')
        offsets = Counter()
        for match in difflib.SequenceMatcher(None,na,nb,autojunk=False).get_matching_blocks():
            for j in range(match.size):
                x,y = a[match.a+j],b[match.b+j]
                u,v = re.search(r'offset=(\d+)',x),re.search(r'offset=(\d+)',y)
                if u and v and u[1] != v[1]: offsets[int(u[1]),int(v[1])] += 1
        rows.append(dict(role=role, old=ar, new=br,
                         discovery_normalized_equal=na==nb,
                         raw_diff_sha256=new.sha(rawdiff),
                         aligned_memory_offset_sites=[dict(old=x,new=y,sites=n) for (x,y),n in sorted(offsets.items())]))
    extra = []
    for role in ('tick','command','effective_armor'):
        text,record = function(1,new.ROLES[role][0],role)
        assert record['body_sha256'] == new.APPROVED_BODY_SHA[role]
        extra.append(dict(role=role,**record))
    source_names = ('scripts/trace_migration135.py','scripts/build_full135_oracle.py',
                    'scripts/build_full134_oracle.py','scripts/build_upgrade134_oracle.py')
    record = dict(old_version='0.134.0',new_version='0.135.1',new_build='0898d5e3',
        original_sha256=[old.SOURCE_SHA,new.SOURCE_SHA],functions=rows,new_only_roles=extra,
        source_sha256={p:new.sha(ROOT/p) for p in source_names}, target_executed=False,
        conclusions=['G layout is reordered: derived1360->1536, level1520->1432, currentHP1528->1440, clock2344->2352.',
                     'New1512 adds G1572 armor-cap store from local24, distinct from capped armorG1568.',
                     'New1073 incoming damage calls effective-armor27375 instead of loading old1392 directly.',
                     'Aligned offset pairs are instruction sites, not a universal mapping of every structure.'],
        limitations=['Structural normalization masks integer constants/call destinations/field offsets solely to find candidate correspondences.',
                     'Changed table content, caller state and all side effects require separate validation.',
                     'This static receipt is not runtime or whole-game acceptance.'])
    (out/'migration.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'directory':str(out),'mapped_old_roles':len(rows),'new_only_roles':len(extra),'target_executed':False}))


if __name__ == '__main__':
    main()
