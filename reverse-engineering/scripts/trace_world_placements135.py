#!/usr/bin/env python3
"""Bounded SQLiteRO/WAT-seek evidence for135 placements and inline selection."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sqlite3
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'

def trace(out):
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    _,_,_,bodies,_=parse_source(raw)
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    rows=[]
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(1446,6730,41532,75442,20468,27961,13850):
            row=dict(con.execute('select * from functions where idx=?',(idx,)).fetchone())
            stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start'])
            assert wat.startswith(f'  (func (;{idx};)'.encode());(out/f'{idx}.wat').write_bytes(wat)
            a,b=bodies[idx];rows.append(dict(index=idx,**row,wat_sha256=hashlib.sha256(wat).hexdigest(),body_sha256=hashlib.sha256(raw[a:b]).hexdigest()))
    con.close()
    result=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,functions=rows,
        original_calls=0,whole_world_producer=False)
    (out/'placement-trace.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-placements0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    result=trace(out);print(json.dumps(dict(directory=str(out),functions=len(result['functions']),original_calls=0)))
