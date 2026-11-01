#!/usr/bin/env python3
"""Read-only fixed135 zone/enemy/spawn extraction; never execute the game."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import struct

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source

PROFILE = ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT_SHA = '15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
ZONE_BASE = 5456016
IDS = ('elwynn','duskwood','wsg','ungoro','ab','feralas','arena','sm','av','brm','aq','naxx')
FUNCTIONS = (947,2376,20272,5736,2785,8751,26361,6449,95997,95998,1525,21454)


def extract():
    binary=SOURCE.read_bytes()
    assert hashlib.sha256(binary).hexdigest()==SOURCE_SHA
    types,imports,declarations,bodies,segments=parse_source(binary)
    memory=bytearray(max(s['address']+s['length'] for s in segments if s['address'] is not None))
    for s in segments:
        if s['address'] is not None:
            memory[s['address']:s['address']+s['length']]=binary[s['file_offset']:s['file_offset']+s['length']]
    def text(ptr,length):
        if not 0<=length<=1024 or ptr+length>len(memory):raise ValueError('Static string bounds')
        return memory[ptr:ptr+length].decode('utf8')
    zones=[]
    for index,identifier in enumerate(IDS):
        address=ZONE_BASE+index*152;raw=bytes(memory[address:address+152]);w=struct.unpack('<38I',raw)
        assert text(w[2],w[3])==identifier
        normals=[]
        for j in range(w[17]):
            ptr=w[16]+72*j;data=bytes(memory[ptr:ptr+72]);u=struct.unpack('<18I',data)
            normals.append(dict(index=j,pointer=ptr,name=text(u[4],u[5]),entry=u[6],display=u[7],
                scale_bits=u[8],classification=u[9],hp_bits=u[10],attack_bits=u[11],field48_bits=u[12],
                field52_bits=u[13],xp=u[14],cost_bits=u[15],unlock_bits=u[16],elite=data[68],raw72_hex=data.hex()))
        bosses=[]
        for j in range(w[19]):
            ptr=w[18]+72*j;data=bytes(memory[ptr:ptr+72]);u=struct.unpack('<18I',data)
            bosses.append(dict(index=j,pointer=ptr,name=text(u[0],u[1]),announcement=text(u[4],u[5]),
                entry=u[8],display=u[9],scale_bits=u[10],classification=u[11],minute_bits=u[12],
                hp_bits=u[13],attack_bits=u[14],field60_bits=u[15],final=data[68],raw72_hex=data.hex()))
        assert len(normals)==(16 if index==11 else 12) and len(bosses)==5
        zones.append(dict(index=index,identifier=identifier,pointer=address,name=text(w[4],w[5]),
            scale_bits=w[34],late_scale_bits=w[35],normals=normals,bosses=bosses,raw152_hex=raw.hex()))
    difficulty=[list(struct.unpack_from('<2I',memory,1585976+i*32)) for i in range(1,6)]
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('spawn0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    con=sqlite3.connect(f'file:{PROFILE/"index.sqlite"}?mode=ro',uri=True)
    wat=PROFILE/'official-0.135.1-full.wat'
    with wat.open('rb') as source:
        assert hashlib.file_digest(source,'sha256').hexdigest()==WAT_SHA
        functions=[]
        for i in FUNCTIONS:
            ws,we,bs,be=con.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(i,)).fetchone()
            assert bodies[i]==(bs,be)
            source.seek(ws);text_bytes=source.read(we-ws)
            assert text_bytes.startswith(f'  (func (;{i};) '.encode())
            (out/f'function-{i}.wat').write_bytes(text_bytes)
            params,returns=types[declarations[i-len(imports)]]
            functions.append(dict(index=i,body_start=bs,body_end=be,body_sha256=hashlib.sha256(binary[bs:be]).hexdigest(),
                wat_sha256=hashlib.sha256(text_bytes).hexdigest(),params_hex=params.hex(),results_hex=returns.hex()))
    result=dict(version='0.135.1',build='0898d5e3',source_sha256=SOURCE_SHA,zone_base=ZONE_BASE,zones=zones,
        difficulty_bits=difficulty,functions=functions,target_executed=False,
        source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'spawn-data.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'directory':str(out),'zones':len(zones),'normal_and_elite_definitions':sum(len(z['normals'])for z in zones),
        'boss_definitions':sum(len(z['bosses'])for z in zones),'functions':len(functions),'target_executed':False}))
    return result,out


if __name__=='__main__':extract()
