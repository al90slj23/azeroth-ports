#!/usr/bin/env python3
"""Private137 full10291/2862 export; never alter original code or shared builders."""
from pathlib import Path
import hashlib,os,signal,sqlite3,struct,subprocess,time
from wasm137_profile import ROOT,SOURCE,SOURCE_SHA,Reader,binary_identity,tool_identity
from build_combat137_oracle import unsigned,export_entries,sha,save,PROFILE

ENTRY='research137_resource_effect10291'
STACK='research137_resource_consumer_stack0'
COLLECT='research137_resource_collect2862'


def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==90941108 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']
    sec=next(s for s in sections if s['kind']==1);r=Reader(raw,sec['payload_start'],sec['end']);types=[]
    for _ in range(r.uint()):
        assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
    sec=next(s for s in sections if s['kind']==3);r=Reader(raw,sec['payload_start'],sec['end']);decl=[r.uint()for _ in range(r.uint())]
    assert types[decl[10291-878]]==('7f7f','')
    global_section=next(s for s in sections if s['kind']==6)
    assert raw[global_section['payload_start']:global_section['end']].hex()=='017f01418080c0000b'
    ex=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,ex)
    assert ('__wbindgen_malloc',0,91933)in prior
    additions=[(ENTRY,0,10291),(COLLECT,0,2862),(STACK,3,0)];extra=b''
    for name,kind,index in additions:
        text=name.encode();extra+=unsigned(len(text))+text+bytes([kind])+unsigned(index)
    payload=unsigned(len(prior)+len(additions))+raw[start:ex['end']]+extra
    changed=raw[:ex['start']]+b'\x07'+unsigned(len(payload))+payload+raw[ex['end']:]
    after,_=binary_identity(changed)
    assert len(sections)==len(after['sections'])
    for a,b in zip(sections,after['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    assert export_entries(changed,next(s for s in after['sections']if s['kind']==7))[0]==prior+additions
    path=out/'resource-consumer137-original-exports.wasm';path.write_bytes(changed)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        db.execute('pragma query_only=on');db.row_factory=sqlite3.Row
        entry=dict(db.execute('select * from functions where idx=10291').fetchone())
        calls=[dict(row)for row in db.execute('select callee,wat_offset,wat_line,instruction from calls where caller=10291')]
    assert ranges[10291][:2]==(entry['body_start'],entry['body_end'])
    with(PROFILE/'official-0.137.0-full.wat').open('rb')as stream:
        stream.seek(entry['wat_start']);wat=stream.read(entry['wat_end']-entry['wat_start'])
    assert len(wat)<512*1024;(out/'10291.wat').write_bytes(wat)
    tools=tool_identity();validator=Path(tools['tools']['wasm-validate']['path']);began=time.monotonic()
    with(out/'validation.stdout').open('wb')as stdout,(out/'validation.stderr').open('wb')as stderr:
        child=subprocess.Popen([str(validator),'--enable-all',str(path)],stdout=stdout,stderr=stderr,start_new_session=True)
        save(out/'validator-owned.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=45))
        try:code=child.wait(timeout=45)
        finally:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait()
    try:os.killpg(child.pid,0)
    except ProcessLookupError:missing=True
    else:missing=False
    assert code==0 and missing
    a,b,_=ranges[10291]
    manifest=dict(version='0.137.0',build='d171b8f9f',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=path.name,module_sha256=sha(path),
        entry=dict(index=10291,signature=['7f7f',''],body_start=a,body_end=b,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest()),
        only_changed_section=7,added_exports=additions,original_exports=prior,implicit_start=False,allocator_index=91933,
        memory_page_cap=512,denied_imports=878,stack_initial=1048576,direct_calls=calls,collector_index=2862,
        validator=dict(pid=child.pid,pgid=child.pid,exit_code=code,pgid_missing=missing,seconds=time.monotonic()-began,tools=tools),
        original_executed_by_builder=False)
    save(out/'manifest.json',manifest);return manifest
