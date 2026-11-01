#!/usr/bin/env python3
"""Private export-only raster producer module and targeted static evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sqlite3,subprocess
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries,VALIDATOR_SHA
from build_upgrade134_oracle import unsigned,sha

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ROLES={
 'raster135_height_candidates':(12375,'7f7f7f7f7f7d','','ad87b93e4482062ad563e9672ca279afc4cbb3000bb3be271f25f3dea815b3e5'),
 'raster135_transform':(18572,'7f7f7f7f7f7d','','a82a1c8b0e230958331c9c8ef152086c33ab373a7edda7dcc2b61cce7c340983'),
 'raster135_navigation':(9328,'7f7f7f7f7d7f7f','','a8e943e5af2103c6fd9c7d3d7e6e1d05dceb844eee84733fdcf540822b2d6179'),
 'raster135_parse_m2':(14947,'7f7f7f','','aa1609794c1d3e3275cd9ae4f2b2dc0457e9c09a7379d6770e1bc53d6b4713ad')}

def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==90959080 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,segs=parse_source(raw);sections=section_list(raw);assert len(imports)==878 and 8 not in[s[0]for s in sections]
    ex=next(s for s in sections if s[0]==7);exports,first=export_entries(raw,ex);addition=b'';roles=[]
    for name,(fn,params,results,h)in ROLES.items():
        assert types[decl[fn-len(imports)]]==(bytes.fromhex(params),bytes.fromhex(results));a,b=bodies[fn];assert hashlib.sha256(raw[a:b]).hexdigest()==h
        n=name.encode();addition+=unsigned(len(n))+n+b'\0'+unsigned(fn);roles.append(dict(name=name,index=fn,parameters_hex=params,results_hex=results,body_start=a,body_end=b,body_sha256=h))
    payload=unsigned(len(exports)+len(roles))+raw[first:ex[3]]+addition
    changed=raw[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+raw[ex[3]:];new_sections=section_list(changed);same=[]
    assert len(new_sections)==len(sections)
    for a,b in zip(sections,new_sections):
        assert a[0]==b[0]
        if a[0]!=7:assert raw[a[1]:a[3]]==changed[b[1]:b[3]];same.append(dict(section=a[0],sha256=hashlib.sha256(raw[a[1]:a[3]]).hexdigest()))
    assert export_entries(changed,next(s for s in new_sections if s[0]==7))[0]==exports+[(x['name'],0,x['index'])for x in roles]
    path=out/'world-raster135.wasm';path.write_bytes(changed)
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    result=subprocess.run([str(validator),'--enable-all',str(path)],capture_output=True,timeout=45);(out/'validation.stderr').write_bytes(result.stderr);assert result.returncode==0
    identities=[];con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as h:
        for fn in(6730,1104,12375,18572,9328,14947,65327):
            r=dict(con.execute('select * from functions where idx=?',(fn,)).fetchone());h.seek(r['wat_start']);text=h.read(r['wat_end']-r['wat_start'])
            assert text.splitlines()[0].startswith(f'  (func (;{fn};)'.encode());(out/f'{fn}.wat').write_bytes(text)
            a,b=bodies[fn];identities.append(dict(index=fn,**r,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),wat_sha256=hashlib.sha256(text).hexdigest()))
    manifest=dict(version='0.135.1',build='0898d5e3',module_file=path.name,module_sha256=sha(path),original_sha256=SOURCE_SHA,
        original_exports=exports,roles=roles,unchanged_nonexport_sections=same,source_implicit_start=False,original_allocator91941=True,
        functions=identities,source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},new_original_calls=0)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.parse_args();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-raster0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    print(json.dumps(dict(directory=str(out),roles=len(m['roles']),original_executed=False)))
