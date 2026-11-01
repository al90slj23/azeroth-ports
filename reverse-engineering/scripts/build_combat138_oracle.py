#!/usr/bin/env python3
"""Private138 original913+global0 export admission; shared builders unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,signal,sqlite3,subprocess,time
from wasm138_profile import ROOT,SOURCE,SOURCE_SHA,tool_identity,Reader,binary_identity

PROFILE=ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z'
STACK='research138_stack0';DAMAGE='research138_damage913'
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
    raw=SOURCE.read_bytes();assert len(raw)==90946299 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']
    global_section=next(s for s in sections if s['kind']==6)
    assert raw[global_section['payload_start']:global_section['end']].hex()=='017f01418080c0000b'
    sec=next(s for s in sections if s['kind']==1);t=Reader(raw,sec['payload_start'],sec['end']);types=[]
    for _ in range(t.uint()):assert t.byte()==0x60;types.append((t.raw(t.uint()).hex(),t.raw(t.uint()).hex()))
    sec=next(s for s in sections if s['kind']==3);t=Reader(raw,sec['payload_start'],sec['end']);decl=[t.uint()for _ in range(t.uint())]
    assert types[decl[913-878]]==('7f7e7d7f7f7f7f','')
    ex=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,ex)
    assert ('__wbindgen_malloc',0,92072)in prior
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
    module=out/'combat138-original-exports.wasm';module.write_bytes(changed)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as c:
        c.row_factory=sqlite3.Row;entry=dict(c.execute('select * from functions where idx=913').fetchone());assert ranges[913][:2]==(entry['body_start'],entry['body_end'])
        calls=[dict(row)for row in c.execute('select callee,wat_offset,wat_line,instruction from calls where caller=913')]
    with(PROFILE/'official-0.138.0-full.wat').open('rb')as f:f.seek(entry['wat_start']);wat=f.read(entry['wat_end']-entry['wat_start'])
    (out/'913.wat').write_bytes(wat)
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
    native=SOURCE.parent/'windows-0.138.0/AzerothSurvivors.exe';exe=native.read_bytes();assert hashlib.sha256(exe).hexdigest()=='eb5fd1c1b96e6180fcf5f3d685d90a61471af28d22e5f060c02b7b7663fbf79e'
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
    manifest=dict(version='0.138.0',build='382771e6c',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=module.name,module_sha256=sha(module),
        profile_manifest_sha256=sha(PROFILE/'manifest.json'),entry=dict(index=913,signature=['7f7e7d7f7f7f7f',''],body_start=a,body_end=b,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest()),
        only_changed_section=7,original_sections=sections,added_exports=additions,original_exports=prior,implicit_start=False,
        allocator_index=92072,memory_page_cap=512,denied_imports=878,stack_initial=1048576,
        direct_calls=calls,npc_definition=dict(pointer=npc,name='Kobold Vermin',raw72_hex=declaration.hex()),
        windows_reference=dict(path=str(native),sha256=hashlib.sha256(exe).hexdigest(),bytes=len(exe),scalar_tail45_hex=scalar_tail.hex(),scalar_tail_file_matches=native_matches,
            scope='Exact declaration scalar-tail byte correspondence only; Windows gameplay ABI/913 function identity not established',executed=False),
        validator=dict(pid=child.pid,pgid=child.pid,exit_code=code,pgid_missing=missing,seconds=time.monotonic()-began,tools=tools),original_executed_by_builder=False)
    save(out/'manifest.json',manifest);return manifest
