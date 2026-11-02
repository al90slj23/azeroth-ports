#!/usr/bin/env python3
"""Bounded current139 AI925/static navigation, motion and contact provenance."""
from datetime import datetime,timezone
import json,struct
from incoming139_tools import ROOT,original,function_proof,static_reader,save,sha,SOURCE_SHA

def trace(out):
    raw,identity,ranges=original();read=static_reader(raw,identity)
    ids={925,30179,29237,52557,81682,70932,27650,50441,11425,11499,29912,23333,1076,59230,20060,15962,13833,5719}
    proof,texts=function_proof(raw,identity,ranges,ids,out)
    pairs=tuple(struct.unpack('<2i',read(5408444+i*8,8))for i in range(8))
    assert pairs==((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
    p,n=struct.unpack('<2I',read(5401532,8));english=json.loads(read(p,n));names={}
    for ptr in(5830904,):
        p,n,identifier=struct.unpack('<3I',read(ptr+16,12));fallback=read(p,n).decode();names[str(ptr)]=english.get('enemy.'+str(identifier),fallback)
    result=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,trace_source_sha256=sha(__file__),functions=proof,neighbors=pairs,english_names=names,data_proof=read.proof,original_calls=0,
        bindings=dict(old921_current925=True,NPC_stride=432,heading=404,stun=408,haste=412,classification=424,path_pointer=2368,path_clock=2372,path_payload=dict(capacity=8,pointer=12,length=16,seed=20,visited=24)),
        limits=['Static recovery only; old135 runtime acceptance is not inherited.','No fullmain/native/complete game.'])
    save(out/'trace.json',result);return result
if __name__=='__main__':
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('enemy-ai139-trace-%Y%m%dT%H%M%S.%fZ');out.mkdir();trace(out);print(json.dumps(dict(directory=str(out),sha256=sha(out/'trace.json'))))
