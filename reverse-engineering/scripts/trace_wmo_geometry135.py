#!/usr/bin/env python3
"""Private export-only1510/4464 module, bounded SQLite/WAT evidence; no run."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sqlite3,subprocess
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries,VALIDATOR_SHA
from build_upgrade134_oracle import unsigned,sha

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ROLES={
 'wmo135_parse':(1510,'7f7f','','2f1b0db5ff4235ab674e720d57ba8a520107b959bf1708cf140aab5492fe8cb0'),
 'wmo135_append_collision':(4464,'7f7f7f7f7f7f','','ba1477e3eddfc9b96a6d67be12a4af02e4d283ed787bb717e160b299bad8d5d1')}


def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==90959080 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,_=parse_source(raw);sections=section_list(raw)
    assert len(imports)==878 and 8 not in[x[0]for x in sections]
    glob=next(x for x in sections if x[0]==6);assert raw[glob[2]:glob[3]].hex()=='017f01418080c0000b'
    ex=next(x for x in sections if x[0]==7);exports,first=export_entries(raw,ex);added=b'';roles=[]
    for name,(index,params,results,identity)in ROLES.items():
        assert types[decl[index-len(imports)]]==(bytes.fromhex(params),bytes.fromhex(results))
        a,b=bodies[index];assert hashlib.sha256(raw[a:b]).hexdigest()==identity
        n=name.encode();added+=unsigned(len(n))+n+b'\0'+unsigned(index)
        roles.append(dict(name=name,index=index,parameters_hex=params,results_hex=results,body_start=a,body_end=b,body_sha256=identity))
    payload=unsigned(len(exports)+2)+raw[first:ex[3]]+added
    changed=raw[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+raw[ex[3]:]
    newer=section_list(changed);assert[x[0]for x in sections]==[x[0]for x in newer];same=[]
    for x,y in zip(sections,newer):
        if x[0]!=7:
            assert raw[x[1]:x[3]]==changed[y[1]:y[3]]
            same.append(dict(section=x[0],sha256=hashlib.sha256(raw[x[1]:x[3]]).hexdigest()))
    assert export_entries(changed,next(x for x in newer if x[0]==7))[0]==exports+[(x['name'],0,x['index'])for x in roles]
    path=out/'wmo-geometry135.wasm';path.write_bytes(changed)
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    result=subprocess.run([str(validator),'--enable-all',str(path)],capture_output=True,timeout=45)
    (out/'validation.stdout').write_bytes(result.stdout);(out/'validation.stderr').write_bytes(result.stderr);assert result.returncode==0
    index=PROFILE/'index.sqlite';assert sha(index)=='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
    con=sqlite3.connect(index.resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row;functions=[]
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as fh:
        for idx in(1510,4464,9513,60913,60916,81334,65313,65321,65323,39629,44774):
            row=dict(con.execute('SELECT * FROM functions WHERE idx=?',(idx,)).fetchone())
            fh.seek(row['wat_start']);wat=fh.read(row['wat_end']-row['wat_start'])
            assert wat.splitlines()[0].startswith(f'  (func (;{idx};)'.encode())
            (out/f'{idx}.wat').write_bytes(wat);a,b=bodies[idx]
            functions.append(dict(**row,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest(),
                direct_callees=[x[0]for x in con.execute('SELECT callee FROM calls WHERE caller=?',(idx,))]))
    con.close()
    manifest=dict(version='0.135.1',build='0898d5e3',module_file=path.name,module_sha256=sha(path),original_sha256=SOURCE_SHA,
        roles=roles,original_exports=exports,unchanged_nonexport_sections=same,only_changed_section=7,
        source_implicit_start=False,mutable_global0_initial=1048576,global_section_hex='017f01418080c0000b',
        original_allocator=dict(index=91941,body_sha256=hashlib.sha256(raw[slice(*bodies[91941])]).hexdigest()),
        memory_page_cap=512,denied_imports=878,functions=functions,profile_index_sha256=sha(index),validator_sha256=VALIDATOR_SHA,
        research_exports_do_not_modify_shared_admission=True,target_executed=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert sha(SOURCE)==SOURCE_SHA
    return manifest


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('wmo-geometry0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();build(out)
    print(json.dumps(dict(directory=str(out),original_executed=False)))
