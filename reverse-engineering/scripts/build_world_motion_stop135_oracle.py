#!/usr/bin/env python3
"""Private full17119 and stack0 export, unmodified original/callees; no execution."""
import hashlib,json
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries
from build_upgrade134_oracle import unsigned,sha
BODY={17119:'33b9a485e73d8f0e4c9e13cb1dce1b6ce3d022be1cf2906cadfd5978349bfad6',17217:'904cef82c034dd51f03386943cec632629467cb54dbc6d6c332707faf3acb8df',16340:'4e0bc9ee76b1df145b4b2a4fe4f6ae78aca3b17645515d4336a3ef30941982a7',29631:'26ad625360e80687c9aa00161d60e8cb2cfde429209ef361bb0c325b93441650',23181:'a46874e377eac8590d923753e6a5e26289b8388144a0241b6b29cc1f77640666',45845:'c6502e4033836dcb50eb72024a9ae6418ccbd3c93c72270f07da8eb6a35aa947'}
def build(out):
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA and len(raw)==90959080
 types,imports,decl,bodies,_=parse_source(raw);identities={}
 for index,h in BODY.items():
  a,b=bodies[index];p,r=types[decl[index-len(imports)]];assert hashlib.sha256(raw[a:b]).hexdigest()==h;identities[str(index)]=dict(index=index,params_hex=p.hex(),results_hex=r.hex(),body_start=a,body_end=b,body_sha256=h)
 assert identities['17119']['params_hex']=='7f'and identities['17119']['results_hex']==''
 parts=section_list(raw);ex=next(x for x in parts if x[0]==7);old,first=export_entries(raw,ex);add=b''
 for name,kind,index in(('research_world_motion_stop135_stop',0,17119),('research_world_motion_stop135_stack0',3,0)):
  encoded=name.encode();add+=unsigned(len(encoded))+encoded+bytes([kind])+unsigned(index)
 payload=unsigned(len(old)+2)+raw[first:ex[3]]+add;changed=raw[:ex[1]]+b'\7'+unsigned(len(payload))+payload+raw[ex[3]:]
 fresh=section_list(changed);assert[x[0]for x in parts]==[x[0]for x in fresh]and not any(x[0]==8 for x in parts)
 assert all(raw[a[1]:a[3]]==changed[b[1]:b[3]]for a,b in zip(parts,fresh)if a[0]!=7)
 globals=next(x for x in parts if x[0]==6);assert raw[globals[2]:globals[3]].hex()=='017f01418080c0000b'
 path=out/'world-motion-stop135-private.wasm';path.write_bytes(changed)
 manifest=dict(kind='snapshot_world_full17119_not_world_constructor',version='0.135.1',actual_build='90898d5e3',original_sha256=SOURCE_SHA,module_file=path.name,module_sha256=sha(path),original_exports=old,only_changed_section=7,body_guards=identities,stack_global=0,stack_initial=1048576,allocator91941=True,memory_page_cap=4096,denied_imports=878,target_executed=False)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
