#!/usr/bin/env python3
"""Read-only pinned135 AI definitions and actual internal-call evidence."""
import hashlib,json,sqlite3,struct,sys
from datetime import datetime,timezone
from pathlib import Path
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.spawn135_data import NORMALS

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
FUNCTIONS=(880,921,1073,27375,80447,69798,11428,11503)


def extract():
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,declarations,bodies,segments=parse_source(raw)
    memory=bytearray(max(s['address']+s['length']for s in segments if s['address']is not None))
    for s in segments:
        if s['address']is not None:memory[s['address']:s['address']+s['length']]=raw[s['file_offset']:s['file_offset']+s['length']]
    definitions=[]
    for zone in NORMALS:
        for row in zone:
            pointer=row[1];words=struct.unpack_from('<4I',memory,pointer)
            definitions.append(dict(pointer=pointer,name=row[2],prefix16=list(words),melee=words[0]==0))
    assert len(definitions)==148 and sum(x['melee']for x in definitions)==124
    con=sqlite3.connect(f'file:{PROFILE/"index.sqlite"}?mode=ro',uri=True)
    wat=PROFILE/'official-0.135.1-full.wat'
    with wat.open('rb')as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==WAT_SHA
        functions=[]
        for index in FUNCTIONS:
            start,end=con.execute('select wat_start,wat_end from functions where idx=?',(index,)).fetchone()
            stream.seek(start);text=stream.read(end-start).decode()
            a,b=bodies[index]
            callers=[r[0]for r in con.execute('select distinct caller from calls where callee=? order by caller',(index,))]
            callees=[r[0]for r in con.execute('select distinct callee from calls where caller=? order by callee',(index,))]
            functions.append(dict(index=index,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),
                signature=text.splitlines()[0].strip(),direct_callers=callers,direct_callees=callees))
    assert 921 in next(x['direct_callees']for x in functions if x['index']==880)
    assert 1073 in next(x['direct_callees']for x in functions if x['index']==921)
    assert 27375 in next(x['direct_callees']for x in functions if x['index']==1073)
    return dict(original_sha256=SOURCE_SHA,wat_sha256=WAT_SHA,functions=functions,definitions=definitions,
        contract=dict(unit_stride=424,world_pointer=2348,units=[1784,1788,1792],now=2352,
          player_xyz=[1416,1420,1424],hp=1440,maximum_hp=1536,armor=1568,armor_cap=1572,
          note='G268 is not a world cache;921 stack+268 temporarily holds G2348 world pointer.'))


if __name__=='__main__':
    report=extract();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('ai0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    (out/'ai135-static.json').write_text(json.dumps(report,indent=2)+'\n')
    expected=tuple(x['pointer']for x in report['definitions']if x['melee'])
    sys.path.insert(0,str(ROOT/'reconstruction'))
    from core_spec.ai135_data import MELEE_DEFINITIONS
    assert expected==MELEE_DEFINITIONS
    print(json.dumps(dict(directory=str(out),functions=len(report['functions']),ordinary_melee_definitions=len(expected))))
