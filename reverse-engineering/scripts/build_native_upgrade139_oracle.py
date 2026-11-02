#!/usr/bin/env python3
"""Static extraction of actual513B Native and export-only wholeWASM25511."""
from pathlib import Path
import hashlib,json,struct
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,function_proof,static_reader,sha,save

FOCUS=ROOT/'evidence/native139-upgrade-focus-20261102T115527.969158Z'
NATIVE=ROOT/'originals/official-release-20261102T011227.335145Z/windows-0.139.0/AzerothSurvivors.exe'
NATIVE_SHA='0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274'
START=0x145f64cc0
END=0x145f64ec1
NATIVE_TABLES=(0x147a1fc5c,0x147a1fc88,0x147a1fcb8,0x147a1fce8,0x147a1fd18)
WASM_TABLES=(5405004,5405040,5405076,5405112,5405148)
SCALARS={0x1464d5d10:0x3f000000,0x1464d5b60:0x3f800000,0x147a1f88c:0xbe4ccccd,0x14653d154:0x3f4ccccd,0x1464d5e04:0x40a00000,0x1464e2df8:0x3e800000,0x1464d5ea0:0x40c00000}


def build(out):
    assert sha(FOCUS/'prepared.json')=='8f35e936f291dcc6e39cccaf353d145f7beab655c63eb77037d9e943242e0d2f'and sha(FOCUS/'run-summary.json')=='986479747f915a1e9752005373bade2f50ab2d85ffaeed56294b8e76f03ddb20'
    pe=NATIVE.read_bytes();assert len(pe)==150595584 and hashlib.sha256(pe).hexdigest()==NATIVE_SHA;header=struct.unpack_from('<I',pe,60)[0];assert pe[:2]==b'MZ'and pe[header:header+4]==b'PE\0\0';machine,nsections=struct.unpack_from('<HH',pe,header+4);optsize=struct.unpack_from('<H',pe,header+20)[0];opt=header+24;assert machine==0x8664 and struct.unpack_from('<H',pe,opt)[0]==0x20b;image=struct.unpack_from('<Q',pe,opt+24)[0];assert image==0x140000000
    sections=[]
    for j in range(nsections):
        p=opt+optsize+j*40;name=pe[p:p+8].rstrip(b'\0').decode();virtual,rva,n,offset=struct.unpack_from('<4I',pe,p+8);sections.append(dict(name=name,virtual_bytes=virtual,rva=rva,raw_bytes=n,file_offset=offset))
    def read(va,n):
        row=next(s for s in sections if image+s['rva']<=va and va+n<=image+s['rva']+s['raw_bytes']);offset=row['file_offset']+va-image-row['rva'];return pe[offset:offset+n]
    pdata=next(s for s in sections if s['name']=='.pdata');matches=[(i//12,struct.unpack_from('<3I',pe,pdata['file_offset']+i))for i in range(0,pdata['raw_bytes']-11,12)if struct.unpack_from('<II',pe,pdata['file_offset']+i)==(START-image,END-image)];assert len(matches)==1
    native_code=read(START,END-START);assert hashlib.sha256(native_code).hexdigest()=='ea9dc1a05053d7b28fd70a1af296556e92df40408b3da9891b66ab97635d7d25';assert sha(FOCUS/'functions.json')==json.loads((FOCUS/'run-summary.json').read_text())['functions_sha256'];focus=json.loads((FOCUS/'functions.json').read_text())['functions'][0];instructions=focus['instructions'];cursor=START
    for row in instructions:
        va=int(row['address'],16);blob=bytes.fromhex(row['bytes']);assert va==cursor and read(va,len(blob))==blob;cursor+=len(blob)
    assert cursor==END and len(native_code)==513
    raw,identity,ranges=original();static=out/'static';static.mkdir();functions,_=function_proof(raw,identity,ranges,{25511},static);wread=static_reader(raw,identity)
    tables=[]
    for native,wasm in zip(NATIVE_TABLES,WASM_TABLES):
        n,w=read(native,20),wread(wasm,20);assert n==w;tables.append(list(struct.unpack('<5I',n)))
    for va,expected in SCALARS.items():assert read(va,4)==struct.pack('<I',expected)
    wasm_defs={}
    for i in range(114):
        p=5882740+88*i;r=wread(p,88);name=wread(*struct.unpack_from('<II',r,12)).decode();wasm_defs[name]=(p,r)
    definitions=[];pages=set();add=lambda p,n:pages.update(range(p&~4095,(p+n+4095)&~4095,4096))
    for i in range(114):
        va=0x147323958+120*i;r=read(va,120);p,n=struct.unpack_from('<QQ',r);assert 0<n<256;slug=read(p,n).decode();wasmp,w=wasm_defs[slug];assert r[117]==w[84]
        definitions.append(dict(index=i,slug=slug,native_va=va,native_string_va=p,name_bytes=n,wasm_va=wasmp,execution=r[117],native120_hex=r.hex(),wasm88_hex=w.hex()));add(va,120);add(p,n)
    assert len({d['slug']for d in definitions})==114
    add(START,END-START);add(0x147a205a0,20)
    for p in NATIVE_TABLES:add(p,20)
    for p in SCALARS:add(p,4)
    page_dir=out/'pe-pages';page_dir.mkdir();page_rows=[]
    for p in sorted(pages):
        blob=read(p,4096);name=f'{p:016x}.bin';(page_dir/name).write_bytes(blob);page_rows.append(dict(va=p,bytes=4096,file='pe-pages/'+name,sha256=sha(page_dir/name),permissions='RX'if p==START&~4095 else'R'))
    switch=read(0x147a205a0,20);targets=[0x147a205a0+x for x in struct.unpack('<5i',switch)];assert targets==[0x145f64cd8,0x145f64df8,0x145f64d3c,0x145f64dd0,0x145f64d11]
    (out/'native513.bin').write_bytes(native_code);added=[('research139_upgrade25511',0,25511),('research139_upgrade_stack',3,0)];filename='native-upgrade139-full25511-exports.wasm';(out/filename).write_bytes(private_exports(raw,identity,added))
    manifest=dict(version='0.139.0',build='f79c5e2b4',native_file=str(NATIVE),native_sha256=NATIVE_SHA,wasm_file=str(SOURCE),wasm_sha256=SOURCE_SHA,native_start=START,native_end=END,native513_sha256=sha(out/'native513.bin'),native_instructions=instructions,native_pdata_match=matches[0],native_pe_sections=sections,native_pages=page_rows,native_tables=NATIVE_TABLES,wasm_tables=WASM_TABLES,native_scalars=SCALARS,switch_va=0x147a205a0,switch_targets=targets,tables=tables,definitions=definitions,wasm_module_file=filename,wasm_module_sha256=sha(out/filename),wasm_original_imports=identity['imports'],wasm_added_exports=added,wasm_functions=functions,only_WASM_export_section_changed=True,native_original_bytes_unchanged=True,builder_original_executions=0)
    save(out/'manifest.json',manifest);return manifest
