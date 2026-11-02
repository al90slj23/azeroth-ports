#!/usr/bin/env python3
"""Private complete1391600 admission; original functions/callees unchanged."""
from pathlib import Path
import hashlib,json,os,signal,sqlite3,subprocess,time
from build_combat139_oracle import (
    ROOT,SOURCE,SOURCE_SHA,PROFILE,ROLE_MAP,ROLE_MAP_SHA,Reader,binary_identity,
    sha,save,unsigned,export_entries,tool_identity,
)

ENTRY=1600
BODY_SHA='17f2335fc31fe91be1509ffcabe89e56662b61cc2c684f862c54c681eb69b8b1'


def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==92511151 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    assert sha(ROLE_MAP)==ROLE_MAP_SHA
    roles=json.loads(ROLE_MAP.read_text());role=next(x for x in roles['entries']if x['role']=='constructor')
    assert roles['new_source_sha256']==SOURCE_SHA and roles['bindings']['constructor']==ENTRY
    assert role['new']['body_sha256']==BODY_SHA and role['new']['params_hex']=='7f7f7f'and role['new']['results_hex']==''
    identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']
    a,b,_=ranges[ENTRY];assert hashlib.sha256(raw[a:b]).hexdigest()==BODY_SHA
    sec=next(s for s in sections if s['kind']==6)
    assert raw[sec['payload_start']:sec['end']].hex()=='017f01418080c0000b'
    sec=next(s for s in sections if s['kind']==1);r=Reader(raw,sec['payload_start'],sec['end']);types=[]
    for _ in range(r.uint()):assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
    sec=next(s for s in sections if s['kind']==3);r=Reader(raw,sec['payload_start'],sec['end']);decl=[r.uint()for _ in range(r.uint())]
    assert types[decl[ENTRY-882]]==('7f7f7f','')and decl[ENTRY-882]==1
    ex=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,ex)
    allocator=next(x for x in identity['exports']if x['name']=='__wbindgen_malloc')
    assert allocator['index']==93344 and allocator['params_hex']=='7f7f'and allocator['results_hex']=='7f'and allocator['type_index']==6
    extra=b'';added=[('research139_initial1600',0,ENTRY),('research139_initial_stack0',3,0)]
    for name,kind,index in added:
        n=name.encode();extra+=unsigned(len(n))+n+bytes([kind])+unsigned(index)
    payload=unsigned(len(prior)+2)+raw[start:ex['end']]+extra
    changed=raw[:ex['start']]+b'\x07'+unsigned(len(payload))+payload+raw[ex['end']:]
    after,_=binary_identity(changed)
    for x,y in zip(sections,after['sections']):
        assert x['kind']==y['kind']
        if x['kind']!=7:assert raw[x['start']:x['end']]==changed[y['start']:y['end']]
    assert export_entries(changed,next(s for s in after['sections']if s['kind']==7))[0]==prior+added
    module=out/'initial139-original-exports.wasm';module.write_bytes(changed)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');entry=dict(db.execute('select *from functions where idx=?',(ENTRY,)).fetchone())
        calls=[dict(row)for row in db.execute('select callee,wat_offset,wat_line,instruction from calls where caller=?',(ENTRY,))]
    assert(entry['body_start'],entry['body_end'])==(a,b)
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:stream.seek(entry['wat_start']);wat=stream.read(entry['wat_end']-entry['wat_start'])
    assert hashlib.sha256(wat).hexdigest()==role['new']['wat_sha256']
    (out/'1600.wat').write_bytes(wat);validator=Path(tool_identity()['tools']['wasm-validate']['path']);began=time.monotonic()
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
    manifest=dict(version='0.139.0',actual_build='f79c5e2b4',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=module.name,module_sha256=sha(module),
        entry=dict(index=ENTRY,type_index=1,params_hex='7f7f7f',results_hex='',body_sha256=BODY_SHA,WAT_sha256=hashlib.sha256(wat).hexdigest()),
        original_exports=prior,added_exports=added,only_changed_section=7,allocator_index=93344,memory_page_cap=512,denied_imports=882,stack_initial=1048576,
        original_imports=identity['imports'],direct_calls=calls,role_mapping_sha256=ROLE_MAP_SHA,original_sections=sections,
        physical_layout=dict(game_bytes=2592,selected_profile_bytes=376,timed_pointer=596,timed_count=600,reserve=764,decay_pool=752,active84_capacity=640,active84_pointer=644,active84_count=648,flags768=768),
        validator=terminal,original_executed_by_builder=False,old_acceptance_transferred=False)
    save(out/'manifest.json',manifest);return manifest
