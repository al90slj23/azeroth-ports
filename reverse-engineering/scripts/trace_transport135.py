#!/usr/bin/env python3
"""Six private export-only Web32 transport entries and constructor evidence."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,struct
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries,VALIDATOR_SHA
from build_upgrade134_oracle import Reader,unsigned,sha,source_memory

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ROLES={
 'transport135_send':(28425,'7f7f7f','','9ffd408d805557e5edfc9e1efe1f7fe59a3b180072abb2e1f53207f9fd1fa7a0'),
 'transport135_snapshot':(52236,'7f7f7f','','e6d7295cd921000039197411f36759df6dea8155a4a8d1d8b048b05993ea815f'),
 'transport135_poll':(45626,'7f7f','','00004ff1b8e9a4f6b5b867474f4c50b8b0664f45c25809c8f1274aecbaa440f0'),
 'transport135_rows88':(21513,'7f7f7f','','d3139042d626e0e9c8abcdc0cce151acf3ad463fa5668c69bd8b646f60a7c715'),
 'transport135_rows12':(47313,'7f7f7f','','d836969e4687366121145d4043220a5fffbe9d1d7c34ab5e01efc3744f77d7b7'),
 'transport135_false':(176109,'7f','7f','ffa2edca2d3a0ef88bfcea9e5cf488eb6a4d98e7f1b4011ce4fa3de388c0b4ea')}


def build(out):
    raw=SOURCE.read_bytes();assert len(raw)==90959080 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,segs=parse_source(raw);sections=section_list(raw);assert len(imports)==878 and all(s[0]!=8 for s in sections)
    ex=next(s for s in sections if s[0]==7);exports,first=export_entries(raw,ex);added=b'';roles=[]
    for name,(idx,params,results,h)in ROLES.items():
        assert types[decl[idx-len(imports)]]==(bytes.fromhex(params),bytes.fromhex(results));a,b=bodies[idx]
        assert hashlib.sha256(raw[a:b]).hexdigest()==h
        n=name.encode();added+=unsigned(len(n))+n+b'\0'+unsigned(idx)
        roles.append(dict(name=name,index=idx,parameters_hex=params,results_hex=results,body_start=a,body_end=b,body_sha256=h))
    payload=unsigned(len(exports)+len(roles))+raw[first:ex[3]]+added
    changed=raw[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+raw[ex[3]:];newer=section_list(changed);same=[]
    assert[s[0]for s in sections]==[s[0]for s in newer]
    for a,b in zip(sections,newer):
        if a[0]!=7:assert raw[a[1]:a[3]]==changed[b[1]:b[3]];same.append(dict(section=a[0],sha256=hashlib.sha256(raw[a[1]:a[3]]).hexdigest()))
    assert export_entries(changed,next(s for s in newer if s[0]==7))[0]==exports+[(r['name'],0,r['index'])for r in roles]
    module=out/'transport135.wasm';module.write_bytes(changed)
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    run=subprocess.run([str(validator),'--enable-all',str(module)],capture_output=True,timeout=45)
    (out/'validation.stdout').write_bytes(run.stdout);(out/'validation.stderr').write_bytes(run.stderr);assert run.returncode==0
    vtable,vo,vs=source_memory(raw,segs,1495776,36);assert struct.unpack('<9I',vtable)==(1721,24,8,1722,1723,1724,1725,1726,1727)
    element=next(s for s in sections if s[0]==9);r=Reader(raw,element[2],element[3]);assert r.uint()==1 and r.uint()==0 and r.byte()==0x41
    base=r.sint();assert base==1 and r.byte()==0x0b;count=r.uint();entries=[r.uint()for _ in range(count)];r.finished()
    assert[entries[slot-base]for slot in range(1722,1728)]==[r['index']for r in roles]
    index=PROFILE/'index.sqlite';assert sha(index)=='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
    con=sqlite3.connect(index.resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row;functions=[]
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(*[v[0]for v in ROLES.values()],55793,53014,60918,48383,4253):
            row=dict(con.execute('SELECT * FROM functions WHERE idx=?',(idx,)).fetchone());stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start'])
            assert text.startswith(f'  (func (;{idx};)'.encode());a,b=bodies[idx]
            if idx==4253:
                lines=text.splitlines(keepends=True);fragment=b''.join(lines[4136:4216]);(out/'4253-4137-4216-transport-constructor.wat').write_bytes(fragment)
                assert b'i32.const 76'in fragment and b'i64.const 34359738368'in fragment and b'i32.store16 offset=20'in fragment
            else:(out/f'{idx}.wat').write_bytes(text)
            functions.append(dict(**row,body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),wat_sha256=hashlib.sha256(text).hexdigest()))
    con.close()
    manifest=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,module_file=module.name,module_sha256=sha(module),
        roles=roles,original_exports=exports,unchanged_nonexport_sections=same,only_changed_section=7,source_implicit_start=False,
        denied_imports=878,memory_page_cap=512,functions=functions,vtable=dict(address=1495776,raw_hex=vtable.hex(),file_offset=vo,data_segment=vs,
            element_base=base,element_function_count=count,slots_to_functions={str(slot):entries[slot-base]for slot in range(1722,1728)}),
        quiet_constructor_domain=dict(cell_bytes=76,transport_bytes=24,log_flag20=0,choice_flag21=0,timer_nanos_tag8=0xffffffff),
        shared52_role_whitelist_changed=False,original_executed=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
