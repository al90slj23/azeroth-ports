#!/usr/bin/env python3
"""Bounded static terrain body evidence; no original execution or host cache."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, sqlite3

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
PROFILE = ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
SOURCE_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
INDEX_SHA = 'b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
DEFAULT = (29631,18670,46295,5795,1446,22634,14947,13850)


def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--functions',nargs='+',type=int,default=DEFAULT)
    indices=tuple(dict.fromkeys(p.parse_args().functions));assert len(indices)<=40 and all(878<=i<176195 for i in indices)
    assert sha(SOURCE)==SOURCE_SHA and sha(PROFILE/'index.sqlite')==INDEX_SHA
    script_sha=sha(Path(__file__));raw=SOURCE.read_bytes()
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('terrain0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    con=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);con.row_factory=sqlite3.Row
    rows=[]
    with (PROFILE/'official-0.135.1-full.wat').open('rb') as wat:
        for index in indices:
            row=dict(con.execute('select * from functions where idx=?',(index,)).fetchone())
            wat.seek(row['wat_start']);body=wat.read(row['wat_end']-row['wat_start']);header=body.splitlines()[0].decode()
            assert header.startswith(f'  (func (;{index};)')
            (out/f'{index}.wat').write_bytes(body)
            rows.append(dict(row,signature=header.strip(),body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),
                wat_sha256=hashlib.sha256(body).hexdigest(),direct_callees=[dict(x) for x in con.execute('select callee,count(*) sites from calls where caller=? group by callee',(index,))]))
    assert sha(Path(__file__))==script_sha
    result=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,index_sha256=INDEX_SHA,
        script_sha256=script_sha,functions=rows,original_executed=False,host_or_cache_forged=False,downloads=False,user_saves_accessed=False)
    (out/'trace.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),functions=len(rows),original_executed=False)))


if __name__=='__main__':main()
