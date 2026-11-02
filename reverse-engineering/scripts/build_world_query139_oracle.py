#!/usr/bin/env python3
"""Export-only139 world/terrain/nearest entry admission; no callee changes."""
from pathlib import Path
import hashlib,json,subprocess
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,Reader,binary_identity,tool_identity
from build_stats139_oracle import unsigned,export_entries

TRACE=ROOT/'evidence/world139-static-20261102T032207.619660Z/trace.json'
TRACE_SHA='7a66273b70a4a5c215092a0981a1652d67786576087510933f05adc810b11d16'
ROLES={'world_height':29912,'terrain_height':18742,'nearest_height':23333}


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def build(out):
    out=Path(out).resolve();assert out.is_relative_to(Path('/Volumes/RuiRui4TB'));out.mkdir(parents=True,exist_ok=True)
    assert sha(TRACE)==TRACE_SHA
    trace=json.loads(TRACE.read_text());raw=SOURCE.read_bytes();assert len(raw)==92511151 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']and identity['function_imports']==882
    sec=next(x for x in sections if x['kind']==6);assert raw[sec['payload_start']:sec['end']].hex()=='017f01418080c0000b'
    sec=next(x for x in sections if x['kind']==1);r=Reader(raw,sec['payload_start'],sec['end']);types=[]
    for _ in range(r.uint()):assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
    r.finish();sec=next(x for x in sections if x['kind']==3);r=Reader(raw,sec['payload_start'],sec['end']);decl=[r.uint()for _ in range(r.uint())];r.finish()
    roles={}
    for name,index in ROLES.items():
        begin,end,_=ranges[index];h=hashlib.sha256(raw[begin:end]).hexdigest();assert h==trace['functions']['139:'+str(index)]['body_sha256']
        assert types[decl[index-882]]==('7f7f7d7d','')
        roles[name]=dict(index=index,export='research139_'+name,parameters_hex='7f7f7d7d',results_hex='',body_sha256=h)
    assert types[decl[93344-882]]==('7f7f','7f')
    ex=next(x for x in sections if x['kind']==7);prior,start=export_entries(raw,ex);assert('__wbindgen_malloc',0,93344)in prior
    added=[(x['export'],0,x['index'])for x in roles.values()]+[('research139_world_stack0',3,0)];extra=b''
    for name,kind,index in added:
        n=name.encode();extra+=unsigned(len(n))+n+bytes([kind])+unsigned(index)
    payload=unsigned(len(prior)+len(added))+raw[start:ex['end']]+extra
    changed=raw[:ex['start']]+b'\x07'+unsigned(len(payload))+payload+raw[ex['end']:];after,_=binary_identity(changed)
    unchanged=[]
    for x,y in zip(sections,after['sections']):
        assert x['kind']==y['kind']
        if x['kind']!=7:
            assert raw[x['start']:x['end']]==changed[y['start']:y['end']];unchanged.append(dict(kind=x['kind'],sha256=hashlib.sha256(raw[x['start']:x['end']]).hexdigest()))
    assert export_entries(changed,next(x for x in after['sections']if x['kind']==7))[0]==prior+added
    module=out/'world-query139-exports.wasm';module.write_bytes(changed)
    validator=Path(tool_identity()['tools']['wasm-validate']['path']);done=subprocess.run([str(validator),'--enable-all',str(module)],capture_output=True,timeout=45)
    (out/'validation.stdout').write_bytes(done.stdout);(out/'validation.stderr').write_bytes(done.stderr);assert done.returncode==0
    m=dict(version='0.139.0',build='f79c5e2b4',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=module.name,module_sha256=sha(module),
        roles=roles,original_imports=identity['imports'],function_imports=882,allocator_index=93344,allocator_signature=['7f7f','7f'],
        original_exports=prior,added_exports=added,only_changed_section=7,unchanged_sections=unchanged,stack_export='research139_world_stack0',stack_initial=1048576,
        memory_page_cap=4096,host_imports_denied=882,trace_sha256=TRACE_SHA,original_executed=False)
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');return m
