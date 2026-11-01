#!/usr/bin/env python3
"""Build a private complete2376 export and read-only stack observation export."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries,VALIDATOR_SHA
from build_upgrade134_oracle import unsigned,sha

BODY_SHA='6b985b23a141a82085f021e7bedf0247ea2a61a99bda05cf820e38a369be29ff'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'


def build_special2376_135(out):
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,_=parse_source(raw)
    assert len(imports)==878 and types[decl[2376-878]]==(b'\x7f',b'')
    a,b=bodies[2376];assert hashlib.sha256(raw[a:b]).hexdigest()==BODY_SHA
    old=section_list(raw);assert all(v[0]!=8 for v in old)
    ex=next(v for v in old if v[0]==7);prior,start=export_entries(raw,ex)
    additions=[('special2376_135_tick',0,2376),('research_special2376_stack',3,0)]
    encoded=b''
    for name,kind,index in additions:
        text=name.encode();encoded+=unsigned(len(text))+text+bytes([kind])+unsigned(index)
    payload=unsigned(len(prior)+len(additions))+raw[start:ex[3]]+encoded
    changed=raw[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+raw[ex[3]:]
    newer=section_list(changed);same=[]
    assert [v[0]for v in old]==[v[0]for v in newer]
    for one,two in zip(old,newer):
        if one[0]!=7:
            assert raw[one[1]:one[3]]==changed[two[1]:two[3]]
            same.append(dict(section=one[0],sha256=hashlib.sha256(raw[one[1]:one[3]]).hexdigest()))
    assert export_entries(changed,next(v for v in newer if v[0]==7))[0]==prior+additions
    file=out/'special2376_135.wasm';file.write_bytes(changed)
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    checked=subprocess.run([str(validator),'--enable-all',str(file)],capture_output=True,timeout=45)
    (out/'validation.stdout').write_bytes(checked.stdout);(out/'validation.stderr').write_bytes(checked.stderr);assert checked.returncode==0
    assert sha(PROFILE/'index.sqlite')=='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    row=dict(con.execute('select * from functions where idx=2376').fetchone());assert (row['body_start'],row['body_end'])==(a,b)
    with (PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start'])
    assert hashlib.sha256(wat).hexdigest()=='fe58aacaa1fec0fbbfad926474e61730dedf259974904e1f373bf9c2cd2ec548'
    (out/'2376.wat').write_bytes(wat);con.close()
    manifest=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,module_file=file.name,module_sha256=sha(file),
        entry=dict(index=2376,parameters_hex='7f',results_hex='',body_sha256=BODY_SHA,**{k:v for k,v in row.items()if k!='idx'}),
        additions=additions,original_exports=prior,unchanged_nonexport_sections=same,only_changed_section=7,
        all_original_callees_preserved=True,stack_export_read_only_by_research=True,source_implicit_start=False,
        memory_page_cap=512,denied_imports=878,shared52_role_whitelist_changed=False,original_executed=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
