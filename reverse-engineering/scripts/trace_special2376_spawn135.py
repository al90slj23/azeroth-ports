#!/usr/bin/env python3
"""Fixed135 indexed2376/1525/scalar/default-skill provenance;0 execution."""
import hashlib,json,sqlite3,struct
from trace_special2376_135 import build_special2376_135,ROOT,SOURCE,SOURCE_SHA,PROFILE
from build_full135_oracle import parse_source

def build_special_spawn135(out):
    manifest=build_special2376_135(out);raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,segs=parse_source(raw);con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    functions=[]
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        for idx in(2376,1525,16341,42327,32969):
            ws,we,bs,be=con.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(idx,)).fetchone()
            assert bodies[idx]==(bs,be);wat.seek(ws);text=wat.read(we-ws);(out/f'{idx}.wat').write_bytes(text)
            sig=types[decl[idx-len(imports)]];functions.append(dict(index=idx,wat_start=ws,wat_end=we,wat_sha256=hashlib.sha256(text).hexdigest(),
                body_start=bs,body_end=be,body_sha256=hashlib.sha256(raw[bs:be]).hexdigest(),parameters_hex=sig[0].hex(),results_hex=sig[1].hex()))
    con.close();memory=bytearray(max(s['address']+s['length']for s in segs if s['address']is not None))
    for s in segs:
        if s['address']is not None:memory[s['address']:s['address']+s['length']]=raw[s['file_offset']:s['file_offset']+s['length']]
    skills=[]
    for entry,pointer in((609,5484048),(610,5484076),(611,5484104)):
        w=struct.unpack_from('<7I',memory,pointer);assert w[3]==0 and w[1]==3
        skills.append(dict(entry=entry,header_pointer=pointer,header28_hex=bytes(memory[pointer:pointer+28]).hex(),
            ability_pointer=w[0],count=w[1],records44_hex=[bytes(memory[w[0]+j*44:w[0]+(j+1)*44]).hex()for j in range(w[1])],
            source_clock_bits=[struct.unpack_from('<I',memory,w[0]+j*44+40)[0]for j in range(w[1])]))
    evidence=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,index_seek_only=True,full_wat_read=False,
        functions=functions,skills=skills,target_executed=False,caller='2376 full unchanged1525/16341/42327/32969',
        admitted='Elwynn9/10/11, first-expiry clock<=21; >21 localized150 pending')
    (out/'producer-static.json').write_text(json.dumps(evidence,indent=2)+'\n');return manifest,evidence
