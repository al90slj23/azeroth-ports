#!/usr/bin/env python3
"""Private fixed135 full1512/1202/10298/2088 self-buff exports; original sections remain intact."""
from pathlib import Path
import hashlib
import json
import os
import signal
import sqlite3
import struct
import subprocess
import time

from build_full135_oracle import (ROOT,SOURCE,SOURCE_SHA,VALIDATOR_SHA,
    parse_source,section_list,export_entries,unsigned)

ENTRY='research135_self_player2088'
AURA='research135_self_aura1202'
EFFECT='research135_self_effect10298'
STATS='research135_self_stats1512'
STACK='research135_self_stack0'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==90959080 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,segs=parse_source(raw);assert len(imports)==878
    assert types[decl[2088-878]]==(b'\x7f\x7d',b'')
    assert types[decl[1202-878]]==(b'\x7f',b'')and types[decl[1512-878]]==(b'\x7f',b'')and types[decl[10298-878]]==(b'\x7f\x7f',b'')
    sections=section_list(raw);assert 8 not in[x[0]for x in sections]
    global_section=next(s for s in sections if s[0]==6)
    assert raw[global_section[2]:global_section[3]].hex()=='017f01418080c0000b'
    ex=next(s for s in sections if s[0]==7);prior,start=export_entries(raw,ex)
    assert('__wbindgen_malloc',0,91941)in prior
    additions=[(ENTRY,0,2088),(AURA,0,1202),(EFFECT,0,10298),(STATS,0,1512),(STACK,3,0)];extra=b''
    for name,kind,index in additions:
        encoded=name.encode();extra+=unsigned(len(encoded))+encoded+bytes([kind])+unsigned(index)
    payload=unsigned(len(prior)+5)+raw[start:ex[3]]+extra
    changed=raw[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+raw[ex[3]:]
    after=section_list(changed);assert len(after)==len(sections)
    for a,b in zip(sections,after):
        assert a[0]==b[0]
        if a[0]!=7:assert raw[a[1]:a[3]]==changed[b[1]:b[3]]
    assert export_entries(changed,next(s for s in after if s[0]==7))[0]==prior+additions
    path=out/'self-buffs135-original-exports.wasm';path.write_bytes(changed)
    functions=[]
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(2088,1512,1202,10298,1453,1076,4600,10529,29537):
            row=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone())
            assert bodies[idx]==(row['body_start'],row['body_end'])and row['wat_end']-row['wat_start']<524288
            stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);(out/f'{idx}.wat').write_bytes(text)
            functions.append(dict(row,body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),
                WAT_sha256=hashlib.sha256(text).hexdigest(),callees=[r[0]for r in db.execute('select distinct callee from calls where caller=? order by callee',(idx,))]))
    db.close()
    def initialized_data(pointer,size):
        assert size<=4096
        result=bytearray(size)
        for seg in segs:
            if seg['address']is None:continue
            a=max(pointer,seg['address']);b=min(pointer+size,seg['address']+seg['length'])
            if a<b:result[a-pointer:b-pointer]=raw[seg['file_offset']+a-seg['address']:seg['file_offset']+b-seg['address']]
        return bytes(result)
    labels=[]
    for visual in(9006,9007,9008):
        index=visual-9004
        size=struct.unpack('<I',initialized_data(5505504+4*index,4))[0]
        pointer=struct.unpack('<I',initialized_data(5505544+4*index,4))[0]
        labels.append(dict(visual=visual,pointer=pointer,bytes=size,English=initialized_data(pointer,size).decode('ascii')))
    notification_initial=struct.unpack('<I',initialized_data(14340336,4))[0]
    assert notification_initial==1
    # Default ability is an explicit original cleave declaration, not pointer0.
    data=bytearray(88);pointer=5467428
    for seg in segs:
        if seg['address']is None:continue
        a=max(pointer,seg['address']);b=min(pointer+88,seg['address']+seg['length'])
        if a<b:data[a-pointer:b-pointer]=raw[seg['file_offset']+a-seg['address']:seg['file_offset']+b-seg['address']]
    assert int.from_bytes(data[:4],'little')!=12
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    began=time.monotonic()
    with(out/'validation.stdout').open('wb')as stdout,(out/'validation.stderr').open('wb')as stderr:
        child=subprocess.Popen([str(validator),'--enable-all',str(path)],stdout=stdout,stderr=stderr,start_new_session=True)
        save(out/'validator-owned.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=45))
        try:child.wait(timeout=45)
        finally:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    assert child.returncode==0 and missing(child.pid)and missing(child.pid,True)
    manifest=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,
        original_bytes=len(raw),module_file=path.name,module_sha256=sha(path),entry=dict(index=2088,signature=['7f7d','']),aura_index=1202,effect_index=10298,stats_index=1512,
        functions=functions,only_changed_section=7,added_exports=additions,original_exports=prior,
        implicit_start=False,allocator_index=91941,memory_page_cap=512,denied_imports=878,stack_initial=1048576,
        default_ability_pointer=pointer,default_ability88_hex=bytes(data).hex(),default_ability_definition_kind=int.from_bytes(data[:4],'little'),
        English_resource_labels=labels,notification_global_pointer=14340336,notification_initial_next_id=notification_initial,
        notification_text_format4_hex=initialized_data(1376537,4).hex(),banner_field_format_hex=initialized_data(1054294,40).hex(),
        validator=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=True,pgid_missing=True,seconds=time.monotonic()-began,sha256=VALIDATOR_SHA),
        full_WAT_read=False,SQLite_mode='ro/query_only',original_function_bodies_unchanged=True,original_executed_by_builder=False)
    save(out/'manifest.json',manifest);return manifest
