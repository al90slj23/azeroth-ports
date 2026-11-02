#!/usr/bin/env python3
"""Private complete1381571 admission; no shared builder or callee changes."""
from pathlib import Path
import hashlib,json,os,signal,sqlite3,subprocess,sys,time
from build_combat138_oracle import (
    ROOT,SOURCE,SOURCE_SHA,PROFILE,Reader,binary_identity,sha,save,unsigned,
    export_entries,tool_identity,
)
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.flow138_contract import ROLES


def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==90946299 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']
    index,params,result,bodysha=ROLES['constructor'];a,b,_=ranges[index];assert hashlib.sha256(raw[a:b]).hexdigest()==bodysha
    sec=next(s for s in sections if s['kind']==1);r=Reader(raw,sec['payload_start'],sec['end']);types=[]
    for _ in range(r.uint()):assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
    sec=next(s for s in sections if s['kind']==3);r=Reader(raw,sec['payload_start'],sec['end']);decl=[r.uint()for _ in range(r.uint())]
    assert types[decl[index-878]]==(params,result)
    ex=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,ex);assert('__wbindgen_malloc',0,92072)in prior
    extra=b'';added=[('research138_initial1571',0,index),('research138_initial_stack0',3,0)]
    for name,kind,idx in added:
        n=name.encode();extra+=unsigned(len(n))+n+bytes([kind])+unsigned(idx)
    payload=unsigned(len(prior)+2)+raw[start:ex['end']]+extra
    changed=raw[:ex['start']]+b'\x07'+unsigned(len(payload))+payload+raw[ex['end']:]
    after,_=binary_identity(changed)
    for x,y in zip(sections,after['sections']):
        assert x['kind']==y['kind']
        if x['kind']!=7:assert raw[x['start']:x['end']]==changed[y['start']:y['end']]
    assert export_entries(changed,next(s for s in after['sections']if s['kind']==7))[0]==prior+added
    module=out/'initial138-original-exports.wasm';module.write_bytes(changed)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');entry=dict(db.execute('select *from functions where idx=?',(index,)).fetchone())
    assert(entry['body_start'],entry['body_end'])==(a,b)
    with(PROFILE/'official-0.138.0-full.wat').open('rb')as stream:stream.seek(entry['wat_start']);wat=stream.read(entry['wat_end']-entry['wat_start'])
    (out/'1571.wat').write_bytes(wat);validator=Path(tool_identity()['tools']['wasm-validate']['path']);began=time.monotonic()
    with(out/'validation.stdout').open('wb')as stdout,(out/'validation.stderr').open('wb')as stderr:
        p=subprocess.Popen([str(validator),'--enable-all',str(module)],stdout=stdout,stderr=stderr,start_new_session=True)
        try:p.wait(timeout=45)
        finally:
            if p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
    def missing(group=False):
        try:(os.killpg if group else os.kill)(p.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,deadline_seconds=45)
    save(out/'validator-terminal.json',terminal);assert p.returncode==0 and terminal['pid_missing']and terminal['pgid_missing']
    m=dict(version='0.138.0',actual_build='382771e6c',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=module.name,module_sha256=sha(module),
        entry=dict(index=index,params_hex=params,results_hex=result,body_sha256=bodysha,WAT_sha256=hashlib.sha256(wat).hexdigest()),
        original_exports=prior,added_exports=added,only_changed_section=7,allocator_index=92072,memory_page_cap=512,denied_imports=878,stack_initial=1048576,
        physical_layout=dict(game_bytes=2592,selected_profile_bytes=376,timed_pointer=596,timed_count=600,reserve=764,decay_pool=752,active84_capacity=640,active84_pointer=644,active84_count=648,flags768=768),validator=terminal,original_executed_by_builder=False)
    save(out/'manifest.json',m);return m
