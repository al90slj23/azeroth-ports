#!/usr/bin/env python3
"""Export-only full1367 admission, no shared builder edits or execution."""
from pathlib import Path
import hashlib,json,sqlite3
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries
from build_upgrade134_oracle import unsigned,sha

BODY='f5b307b9d13c9e9c899ddca880349c2ba03815cf12508b3669dc02c37db502d7'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'

def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==90959080 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,_=parse_source(raw);a,b=bodies[1367]
    bodysha=hashlib.sha256(raw[a:b]).hexdigest();assert bodysha==BODY
    assert types[decl[1367-len(imports)]]==(b'\x7f\x7f\x7d',b'')and b-a==6517
    sections=section_list(raw);assert not any(x[0]==8 for x in sections)
    ex=next(x for x in sections if x[0]==7);old,first=export_entries(raw,ex)
    additions=[('research135_death_recap1367',0,1367),('research135_death_recap_stack0',3,0)];payload=bytearray(unsigned(len(old)+2)+raw[first:ex[3]])
    for name,kind,index in additions:
        name=name.encode();payload+=unsigned(len(name))+name+bytes([kind])+unsigned(index)
    changed=raw[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+raw[ex[3]:]
    fresh=section_list(changed);assert [x[0]for x in sections]==[x[0]for x in fresh]
    assert all(x[0]==7 or raw[x[1]:x[3]]==changed[y[1]:y[3]]for x,y in zip(sections,fresh))
    assert export_entries(changed,next(x for x in fresh if x[0]==7))[0]==old+additions
    module=out/'player-death-recap135-private-exports.wasm';module.write_bytes(changed)
    functions=[]
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for idx in(1367,13106,6332,85719,44448,51418):
            row=dict(db.execute('select *from functions where idx=?',(idx,)).fetchone());start,end=bodies[idx]
            assert(row['body_start'],row['body_end'])==(start,end)
            stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start']);assert len(wat)<=131072
            (out/f'{idx}.wat').write_bytes(wat);functions.append(dict(index=idx,body_start=start,body_end=end,body_sha256=hashlib.sha256(raw[start:end]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest()))
    manifest=dict(version='0.135.1',actual_build='90898d5e3',original_wasm_sha256=SOURCE_SHA,module_file=module.name,module_sha256=sha(module),
        functions=functions,entry=dict(index=1367,parameters_hex='7f7f7d',results_hex='',body_sha256=bodysha),added_exports=additions,
        original_exports=old,only_changed_section=7,implicit_start=False,stack_initial=1048576,allocator_index=91941,
        memory_page_cap=512,denied_imports=878,original_executed_by_builder=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
