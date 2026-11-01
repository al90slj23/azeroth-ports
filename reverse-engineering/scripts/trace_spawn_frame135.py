#!/usr/bin/env python3
"""Retain fixed135 ordinary-frame/position algorithms and concrete guards."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
FUNCTIONS=(947,8751,29631,11428,11503,49503,13516,5736,20272,26361,2785,2376)


def main():
    source=SOURCE.read_bytes();assert hashlib.sha256(source).hexdigest()==SOURCE_SHA
    *_,bodies,segments=parse_source(source)
    con=sqlite3.connect(f'file:{PROFILE/"index.sqlite"}?mode=ro',uri=True)
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('spawn-frame0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    wat=PROFILE/'official-0.135.1-full.wat';texts={};functions=[]
    with wat.open('rb')as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==WAT_SHA
        for idx in FUNCTIONS:
            a,z,bs,be=con.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(idx,)).fetchone()
            assert bodies[idx]==(bs,be);f.seek(a);text=f.read(z-a)
            assert text.startswith(f'  (func (;{idx};) '.encode());(out/f'function-{idx}.wat').write_bytes(text)
            texts[idx]=[s.strip()for s in text.decode().splitlines()]
            functions.append(dict(index=idx,body_start=bs,body_end=be,body_sha256=hashlib.sha256(source[bs:be]).hexdigest(),wat_sha256=hashlib.sha256(text).hexdigest()))
    guards=[]
    def guard(idx,label,block):
        wanted=[s.strip()for s in block.strip().splitlines()]
        matches=[i for i in range(len(texts[idx])-len(wanted)+1)if texts[idx][i:i+len(wanted)]==wanted]
        assert matches,(idx,label)
        guards.append(dict(function=idx,label=label,one_based_lines=[i+1 for i in matches],instructions=wanted))
    guard(8751,'actual world view is G2348+8', '''local.get 1
i32.load offset=2348
local.tee 5
i32.const 8
i32.add
local.set 10''')
    guard(29631,'flat-height discriminant at view112 (world120)', '''local.get 1
i32.load8_u offset=112
i32.eqz
if  ;; label = @3''')
    guard(29631,'flat-height value at view108 (world116)', '''local.get 1
f32.load offset=108
local.set 4
i32.const 1
local.set 8
br 1 (;@1;)''')
    guard(8751,'no-path branch accepts absent obstacle grid world32=-1', '''local.get 5
i32.load offset=32
i32.const -1
i32.eq
br_if 5 (;@5;)''')
    guard(8751,'radius shrinks by2 before next attempt', '''local.get 17
f32.const -0x1p+1 (;=-2;)
f32.add
local.tee 17
f32.const 0x1.8p+3 (;=12;)
f32.ge
br_if 0 (;@9;)''')
    guard(8751,'sixteen attempts precede original fallback13516', '''local.get 16
i32.const 1
i32.add
local.tee 16
i32.const 16
i32.ne
br_if 0 (;@6;)''')
    guard(947,'kill cost is decayed by original26361(dt/-12)', '''local.get 0
local.get 0
f32.load offset=2420
local.get 1
f32.const -0x1.8p+3 (;=-12;)
f32.div
call 26361
f32.mul
local.tee 23
f32.store offset=2420''')
    guard(947,'ordinary budget stops after eight successes', '''local.get 5
i32.const 7
i32.lt_u
local.get 5
i32.const 1
i32.add
local.set 5
br_if 1 (;@5;)''')
    record=dict(version='0.135.1',build='0898d5e3',original_wasm_sha256=SOURCE_SHA,wat_sha256=WAT_SHA,
        functions=functions,guards=guards,target_executed=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Actual full947/8751 definitions and original flat-terrain/obstacle/retry guards. Runtime composition is separately verified.',
        unknown=['Grid/pathfinding, nonaxis motion heading and fallback13516 independent algorithm','Elite/event/Boss timed branches and complete AI/world/rendering'])
    (out/'trace.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),functions=len(functions),guards=len(guards),target_executed=False)))


if __name__=='__main__':main()
