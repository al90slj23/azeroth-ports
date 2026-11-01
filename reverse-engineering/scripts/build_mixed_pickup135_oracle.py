#!/usr/bin/env python3
"""Private complete2862 fixture module plus bounded mixed/notification provenance."""
import hashlib
import sqlite3

from build_resource_consumer135_oracle import (ROOT,SOURCE,SOURCE_SHA,PROFILE,build as resource_build,sha,save)
from build_full135_oracle import parse_source


def build(out):
    manifest=resource_build(out)
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    *_,bodies,segments=parse_source(raw)
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
    functions=[]
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(4630,2159,35514,1089,23581,44447):
            row=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone())
            assert bodies[idx]==(row['body_start'],row['body_end'])and row['wat_end']-row['wat_start']<524288
            stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);(out/f'mixed-{idx}.wat').write_bytes(text)
            functions.append(dict(row,body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),
                WAT_sha256=hashlib.sha256(text).hexdigest(),callees=[r[0]for r in db.execute('select distinct callee from calls where caller=? order by callee',(idx,))]))
    literal_accesses=[dict(r)for r in db.execute('select function_idx,value,wat_line,wat_offset from iconsts where value=? order by function_idx,wat_line',(14340336,))]
    callers=[r[0]for r in db.execute('select distinct caller from calls where callee=42920 order by caller')]
    db.close()
    initial=bytearray(4)
    for segment in segments:
        if segment['address']is None:continue
        a=max(14340336,segment['address']);b=min(14340340,segment['address']+segment['length'])
        if a<b:initial[a-14340336:b-14340336]=raw[segment['file_offset']+a-segment['address']:segment['file_offset']+b-segment['address']]
    assert bytes(initial)==b'\1\0\0\0'
    result=dict(version='0.135.1',actual_build='90898d5e3',original_sha256=SOURCE_SHA,
        module_manifest_sha256=sha(out/'manifest.json'),functions=functions,original_executed=False,
        full_WAT_read=False,SQLite_mode='ro/query_only',notification_pointer=14340336,
        notification_initial4_hex=bytes(initial).hex(),notification_literal_accesses=literal_accesses,
        notification_42920_callers=callers,
        notification_scope='Cold module initial nextID1 is exact.42920/23581/44447 share this owner. A prior App notification may advance it; mixed input must supply retained owner, never reset per frame.',
        pending=['Default1089 optional2785 guard and fullApp pre-opening notification history not inferred from a function-call graph'])
    save(out/'mixed-static.json',result)
    return manifest
