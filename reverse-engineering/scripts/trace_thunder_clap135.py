#!/usr/bin/env python3
"""Indexed fixed135 thunder_clap instruction/source evidence;0 execution."""
from datetime import datetime, timezone
import hashlib, json, sqlite3, struct
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source
from trace_ecs_forward import structural_targets

PROFILE = ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
FUNCTIONS=(922,1076,2244,27562,914)

def collect(out):
    binary=SOURCE.read_bytes()
    assert hashlib.sha256(binary).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,segs=parse_source(binary)
    functions=[]; texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as con:
        with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
            for index in FUNCTIONS:
                ws,we,bs,be=con.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone()
                assert bodies[index]==(bs,be)
                wat.seek(ws);raw=wat.read(we-ws)
                assert raw.startswith(f'  (func (;{index};) '.encode())
                (out/f'{index}.wat').write_bytes(raw);texts[index]=[x.strip()for x in raw.decode().splitlines()]
                sig=types[decl[index-len(imports)]]
                functions.append(dict(index=index,wat_start=ws,wat_end=we,
                    wat_sha256=hashlib.sha256(raw).hexdigest(),body_start=bs,body_end=be,
                    body_sha256=hashlib.sha256(binary[bs:be]).hexdigest(),parameters_hex=sig[0].hex(),results_hex=sig[1].hex()))
    memory=bytearray(max(s['address']+s['length']for s in segs if s['address']is not None))
    for s in segs:
        if s['address']is not None:memory[s['address']:s['address']+s['length']]=binary[s['file_offset']:s['file_offset']+s['length']]
    raw=bytes(memory[5467604:5467604+88]);words=struct.unpack('<22I',raw)
    assert bytes(memory[words[3]:words[3]+words[4]])==b'thunder_clap'
    assert(words[0],words[1],words[2],words[11],raw[84],raw[85])==(1,0x3f000000,0x40400000,6343,2,0)
    dispatch=next(i+1 for i,x in enumerate(texts[922])if x.startswith('br_table '))
    effect=next(i+1 for i,x in enumerate(texts[2244])if x.startswith('br_table '))
    windows={str(i):dict(start=a,end=b,lines=[dict(line=n,text=texts[i][n-1])for n in range(a,b+1)])for i,a,b in ((922,909,1159),(2244,25,217))}
    windows['2244_writes']=dict(start=585,end=605,lines=[dict(line=n,text=texts[2244][n-1])for n in range(585,606)])
    result=dict(version='0.135.1',build='0898d5e3',original_wasm_sha256=SOURCE_SHA,
        target_executed=False,index_seek_only=True,full_wat_read=False,functions=functions,
        definition=dict(pointer=5467604,hex=raw.hex(),words=list(words),name='thunder_clap'),
        execution_branch=structural_targets(texts[922],{dispatch:0})[dispatch],
        effect1_branch=structural_targets(texts[2244],{effect:0})[effect],windows=windows,
        rules=['Exec2 radius uses owned24*64 and definition60 then G1580 with radius quantization.',
            '914 and its accepted-hit/death consumers precede2244 per selected GUID;2244 is not conditional on accepted damage.',
            'Effect1 duration is definition8*owned68; owned28 is not read by this branch.',
            'No effect49 source:2244 first matching GUID with marker!=1 writes124=now+duration,120=strength;356 unchanged.',
            'Effect49 nonempty override source, proc sources, packet bytes and unresolved death continuation remain pending.'],
        source_sha256=hashlib.sha256((ROOT/'scripts/trace_thunder_clap135.py').read_bytes()).hexdigest())
    (out/'static-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('thunder-clap0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    r=collect(out);print(json.dumps(dict(directory=str(out),functions=len(r['functions']),target_executed=False)))
