#!/usr/bin/env python3
"""Private139 original913+global0 export admission; shared builders unchanged.

The139 source, ABI, allocator,432stride and declaration are reparsed here.
The separately source-bound139 parent call graph identifies913's damage role;
no historical behavioral acceptance is transferred.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,signal,sqlite3,subprocess,time
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,tool_identity,Reader,binary_identity

PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
STACK='research139_stack0';DAMAGE='research139_damage913'
ROLE_MAP=ROOT/'evidence/engine139-refined-static-20261102T013743.612949Z/mapping.json'
ROLE_MAP_SHA='7b41961bce7f45e74a8d2a24305cf84d0d64f2f2d739c723b1e445af208c40f0'
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
    assert sha(ROLE_MAP)==ROLE_MAP_SHA
    roles=json.loads(ROLE_MAP.read_text());assert roles['new_source_sha256']==SOURCE_SHA and roles['bindings']['outgoing_damage']==913 and roles['target_executions']==0 and roles['old_acceptance_transferred']is False
    role=next(e for e in roles['entries']if e['role']=='outgoing_damage');assert role['new_index']==913 and role['new']['params_hex']=='7f7e7d7f7f7f7f'and role['new']['results_hex']==''
    identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']
    global_section=next(s for s in sections if s['kind']==6)
    assert raw[global_section['payload_start']:global_section['end']].hex()=='017f01418080c0000b'
    sec=next(s for s in sections if s['kind']==1);t=Reader(raw,sec['payload_start'],sec['end']);types=[]
    for _ in range(t.uint()):assert t.byte()==0x60;types.append((t.raw(t.uint()).hex(),t.raw(t.uint()).hex()))
    sec=next(s for s in sections if s['kind']==3);t=Reader(raw,sec['payload_start'],sec['end']);decl=[t.uint()for _ in range(t.uint())]
    assert types[decl[913-882]]==('7f7e7d7f7f7f7f','')
    assert decl[913-882]==278
    ex=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,ex)
    assert ('__wbindgen_malloc',0,93344)in prior
    allocator=next(e for e in identity['exports']if e['name']=='__wbindgen_malloc')
    assert allocator['index']==93344 and allocator['params_hex']=='7f7f'and allocator['results_hex']=='7f'and allocator['type_index']==6
    additions=[(DAMAGE,0,913),(STACK,3,0)];extra=b''
    for name,kind,index in additions:
        b=name.encode();extra+=unsigned(len(b))+b+bytes([kind])+unsigned(index)
    payload=unsigned(len(prior)+2)+raw[start:ex['end']]+extra
    changed=raw[:ex['start']]+b'\x07'+unsigned(len(payload))+payload+raw[ex['end']:]
    after,_=binary_identity(changed)
    for a,b in zip(sections,after['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    assert export_entries(changed,next(s for s in after['sections']if s['kind']==7))[0]==prior+additions
    module=out/'combat139-original-exports.wasm';module.write_bytes(changed)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as c:
        c.row_factory=sqlite3.Row;entry=dict(c.execute('select * from functions where idx=913').fetchone());assert ranges[913][:2]==(entry['body_start'],entry['body_end'])
        calls=[dict(row)for row in c.execute('select callee,wat_offset,wat_line,instruction from calls where caller=913')]
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as f:f.seek(entry['wat_start']);wat=f.read(entry['wat_end']-entry['wat_start'])
    (out/'913.wat').write_bytes(wat)
    assert hashlib.sha256(raw[ranges[913][0]:ranges[913][1]]).hexdigest()==role['new']['body_sha256']
    assert hashlib.sha256(wat).hexdigest()==role['new']['wat_sha256']
    save(out/'role-binding.json',dict(mapping=str(ROLE_MAP.relative_to(ROOT)),mapping_sha256=ROLE_MAP_SHA,entry=role))
    lines=[line.strip()for line in wat.decode().splitlines()]
    # Current139 one-past432 addressing and exact scalar branch windows.
    assert lines[18]=='i32.const 432'and lines[41]=='i64.load offset=112'
    assert lines[1427]=='i32.const 288'and lines[1447]=='f32.store'and lines[1579]=='f64.store offset=984'
    assert lines[7964]=='i32.load offset=1972'and lines[7978]=='call 69550'
    windows=[(11,51),(683,738),(888,918),(1111,1172),(1200,1284),(1311,1340),(1427,1461),(1571,1580),(7958,7980)]
    save(out/'numeric-static-contract.json',dict(original_sha256=SOURCE_SHA,function=913,type_index=278,signature=['7f7e7d7f7f7f7f',''],
        record_stride=432,GUID=112,HP=288,phase2587=1,clock2352=True,accounted_total984='f64 += f64(f32 min(max(oldHP,0),damage))',
        empty_source_counts=[2032,2056,1972],school372='(school&254)==2 and U372>now then f32 .1',
        windows=[dict(first=a,last=b,instructions=[dict(line=n,text=lines[n-1])for n in range(a,b+1)])for a,b in windows],
        limitations=['These static branches define the declared no-proc/nonlethal projection. Full913 statistics/messages and nonempty69550 remain unresolved.','Constructor/AI and native gameplay are not implied by a synthetic432-byte input.']))
    memory=bytearray(max(s['address']+s['bytes']for s in identity['data_segments']if s['address']is not None))
    for s in identity['data_segments']:
        if s['address']is not None:memory[s['address']:s['address']+s['bytes']]=raw[s['file_offset']:s['file_offset']+s['bytes']]
    #Declaration identity is discovered in this source, not reused as a135 address.
    import struct
    candidates=[]
    for at in range(0,len(memory)-72,4):
        if struct.unpack_from('<I',memory,at+24)[0]!=600:continue
        ptr,length=struct.unpack_from('<II',memory,at+16)
        if length==13 and bytes(memory[ptr:ptr+length])==b'Kobold Vermin':candidates.append(at)
    assert len(candidates)==1
    npc=candidates[0];declaration=bytes(memory[npc:npc+72])
    native=SOURCE.parent/'windows-0.139.0/AzerothSurvivors.exe';exe=native.read_bytes();assert hashlib.sha256(exe).hexdigest()=='0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274'
    scalar_tail=declaration[24:69];native_matches=[];at=0
    while True:
        at=exe.find(scalar_tail,at)
        if at<0:break
        native_matches.append(at);at+=1
    tools=tool_identity();validator=Path(tools['tools']['wasm-validate']['path']);began=time.monotonic()
    with(out/'validation.stdout').open('wb')as stdout,(out/'validation.stderr').open('wb')as stderr:
        child=subprocess.Popen([str(validator),'--enable-all',str(module)],stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=45)
        finally:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait()
    try:os.killpg(child.pid,0)
    except ProcessLookupError:missing=True
    else:missing=False
    assert code==0 and missing
    a,b,_=ranges[913]
    manifest=dict(version='0.139.0',build='f79c5e2b4',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=module.name,module_sha256=sha(module),
        profile_manifest_sha256=sha(PROFILE/'manifest.json'),entry=dict(index=913,signature=['7f7e7d7f7f7f7f',''],body_start=a,body_end=b,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest()),
        only_changed_section=7,original_sections=sections,added_exports=additions,original_exports=prior,implicit_start=False,
        allocator_index=93344,allocator_signature=['7f7f','7f'],allocator_type_index=6,memory_page_cap=512,denied_imports=882,stack_initial=1048576,
        direct_calls=calls,original_imports=identity['imports'],function_imports=882,type_index=278,role_mapping_sha256=ROLE_MAP_SHA,
        numeric_static_contract_sha256=sha(out/'numeric-static-contract.json'),role_binding_sha256=sha(out/'role-binding.json'),
        npc_definition=dict(pointer=npc,name='Kobold Vermin',raw72_hex=declaration.hex()),
        windows_reference=dict(path=str(native),sha256=hashlib.sha256(exe).hexdigest(),bytes=len(exe),scalar_tail45_hex=scalar_tail.hex(),scalar_tail_file_matches=native_matches,
            scope='Exact declaration scalar-tail byte correspondence only; Windows gameplay ABI/913 function identity not established',executed=False),
        validator=dict(pid=child.pid,pgid=child.pid,exit_code=code,pgid_missing=missing,seconds=time.monotonic()-began,tools=tools),original_executed_by_builder=False)
    save(out/'manifest.json',manifest);return manifest
