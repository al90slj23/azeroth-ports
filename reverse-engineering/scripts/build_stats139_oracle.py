#!/usr/bin/env python3
"""Private complete1391542 admission; no shared builder or callee changes."""
from pathlib import Path
import hashlib,json,os,signal,sqlite3,subprocess,sys,time
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,Reader,binary_identity,tool_identity
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
TRACE=ROOT/'evidence/stats139-static-20261102T015922.236942Z/trace.json'
TRACE_SHA='557b4841cd3043f229b7c7f0f7f10315c210d5935476c4b8f8b9701e5e6c6125'
BODY_SHA='43d5e3cd844d1cf156dd0cb058dc05c0a33ce41280649000a7a2b2d3a8f0a72c'
def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def unsigned(value):
    out=bytearray()
    while True:
        b=value&127;value>>=7;out.append(b|(128 if value else 0))
        if not value:return bytes(out)
def export_entries(raw,section):
    r=Reader(raw,section['payload_start'],section['end']);n=r.uint();start=r.pos;out=[]
    for _ in range(n):out.append((r.name(),r.byte(),r.uint()))
    r.finish();return out,start



def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==92511151 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']
    assert sha(TRACE)==TRACE_SHA
    trace=json.loads(TRACE.read_text());assert trace['source_sha256']==SOURCE_SHA and trace['full_normalized_body_after_explicit_codegen_rewrites_equal']
    index,params,result,bodysha=1542,'7f','',BODY_SHA;a,b,_=ranges[index];assert hashlib.sha256(raw[a:b]).hexdigest()==bodysha
    sec=next(s for s in sections if s['kind']==1);r=Reader(raw,sec['payload_start'],sec['end']);types=[]
    for _ in range(r.uint()):assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
    sec=next(s for s in sections if s['kind']==3);r=Reader(raw,sec['payload_start'],sec['end']);decl=[r.uint()for _ in range(r.uint())]
    assert types[decl[index-882]]==(params,result)
    ex=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,ex);assert('__wbindgen_malloc',0,93344)in prior
    extra=b'';added=[('research139_stats1542',0,index),('research139_stats_stack0',3,0)]
    for name,kind,idx in added:
        n=name.encode();extra+=unsigned(len(n))+n+bytes([kind])+unsigned(idx)
    payload=unsigned(len(prior)+2)+raw[start:ex['end']]+extra
    changed=raw[:ex['start']]+b'\x07'+unsigned(len(payload))+payload+raw[ex['end']:]
    after,_=binary_identity(changed)
    for x,y in zip(sections,after['sections']):
        assert x['kind']==y['kind']
        if x['kind']!=7:assert raw[x['start']:x['end']]==changed[y['start']:y['end']]
    assert export_entries(changed,next(s for s in after['sections']if s['kind']==7))[0]==prior+added
    module=out/'stats139-original-exports.wasm';module.write_bytes(changed)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');entry=dict(db.execute('select *from functions where idx=?',(index,)).fetchone())
    assert(entry['body_start'],entry['body_end'])==(a,b)
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:stream.seek(entry['wat_start']);wat=stream.read(entry['wat_end']-entry['wat_start'])
    assert hashlib.sha256(wat).hexdigest()==trace['functions'][0]['wat_sha256']
    (out/'1542.wat').write_bytes(wat);validator=Path(tool_identity()['tools']['wasm-validate']['path']);began=time.monotonic()
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
    m=dict(version='0.139.0',actual_build='f79c5e2b4',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=module.name,module_sha256=sha(module),
        entry=dict(index=index,params_hex=params,results_hex=result,body_sha256=bodysha,WAT_sha256=hashlib.sha256(wat).hexdigest()),
        static_trace_sha256=TRACE_SHA,source_headers=trace['seven_source_headers'],full_direct_callees=trace['direct_callees'],original_imports=identity['imports'],
        function_imports=882,implicit_start=False,allocator_signature=['7f7f','7f'],
        original_exports=prior,added_exports=added,only_changed_section=7,allocator_index=93344,memory_page_cap=512,denied_imports=882,stack_initial=1048576,
        physical_layout=dict(timed_pointer=596,timed_count=600,reserve=764),validator=terminal,original_executed_by_builder=False)
    save(out/'manifest.json',m);return m
