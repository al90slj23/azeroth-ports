#!/usr/bin/env python3
"""Indexed fixed135 G2448/1417 kind2 provenance, no original execution."""
from pathlib import Path
import hashlib
import json
import sqlite3
from build_full135_oracle import SOURCE, SOURCE_SHA, parse_source

ROOT=Path(__file__).resolve().parents[1]


def trace_supply_kind2_135(out):
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    _,_,_,bodies,_=parse_source(raw)
    directory=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
    db=sqlite3.connect((directory/'index.sqlite').as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');rows=[]
    with(directory/'official-0.135.1-full.wat').open('rb')as stream:
        for index in(947,1417,13516,1821,31732,85719,26970,50798,65337,2862):
            row=dict(db.execute('select * from functions where idx=?',(index,)).fetchone())
            assert row['wat_end']-row['wat_start']<=524288
            assert bodies[index]==(row['body_start'],row['body_end'])
            stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start'])
            (out/f'supply-{index}.wat').write_bytes(text)
            rows.append(dict(row,body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),
                wat_sha256=hashlib.sha256(text).hexdigest(),callees=[r[0]for r in db.execute('select distinct callee from calls where caller=? order by callee',(index,))]))
    db.close()
    result=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,functions=rows,
        original_executed=False,full_WAT_read=False,SQLite_mode='ro/query_only',
        rules=['G2448 due comparison writes now+70/factor before kind2 count/cap.',
            'factor=1 inmode0;mode1 uses wrapping(total=G2140+1)-G2548, rejects underflow then max1, f32 factor1+.5*(n-1).',
            '947 outer cap uses original85719(3*factor);1417 inner cap uses85719(5*factor).85719 is rounded via addition0x3effffff and integer masks,not generic ceil.',
            'Defaulttwo openingkind2 are belowmode0 cap3,so the first60s admitted call actually creates the third.',
            '13516 position18..50 consumes shared RNG before1417;1417 createsvisual9005/display259/scale1/kind21=3.',
            '947amount is a caller-local counting iterator;for count>0 its provenance is preVecBase+8+56*count except multiple4→preVecBase+176+224*(count/4).',
            'Complete947 mode1 far-NPC prelude reads explicit peer-position Vec2232/2236; absent peers legitimately relocateNPCs and consumeRNG/movement packets,which cannot be skipped as ordinary-only.',
            'Mode1 count0 retains guarded remaining count as amount;mode0 count0 retains earlier947 local2 and is not restored.',
            '1417 copies amount unchanged to record+12;this word is absent fromactor169 fields.',
            '1417 at its own cap removes oldestkind2 bytotal-f32 +52 order via31732,stable copies full56B backing;marker2 branches into panic after compaction,not a successful skip.',
            'Defaultempty auxiliary owner produces one170 for removed GUID,then the new169;nonempty aux GUID ownership remains pending.'])
    (out/'supply-kind2-static.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
