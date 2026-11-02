#!/usr/bin/env python3
"""Private unchanged1560/5620/1073 exports; no target executes here."""
import hashlib,json
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries
from build_upgrade134_oracle import unsigned,sha
ROLES={
 'constructor1560':(1560,'7f7f7f','','064fd2a7ae947b934f9a398c75aaf17923188e8fad36ddf60849f69f960837fe'),
 'death5620':(5620,'7f','','1d51323f6e17b292370737fd21a849b0ecc80dbb96804a62c9ab73eb13f7b451'),
 'incoming1073':(1073,'7f7d7e7f7f7f','','ae8055c998f7dad212a404de8cee67a5375c9f4f94750f1e69fd5119f4f9e076'),
}
def build(out):
 raw=SOURCE.read_bytes();assert len(raw)==90959080 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
 types,imports,decl,bodies,_=parse_source(raw);parts=section_list(raw);ex=next(x for x in parts if x[0]==7);old,first=export_entries(raw,ex);add=b'';roles=[]
 for name,(index,p,r,h)in ROLES.items():
  params,results=types[decl[index-len(imports)]];a,b=bodies[index]
  assert params.hex()==p and results.hex()==r and hashlib.sha256(raw[a:b]).hexdigest()==h
  export='research_death135_'+name;value=export.encode();add+=unsigned(len(value))+value+b'\0'+unsigned(index)
  roles.append(dict(role=name,index=index,export=export,params_hex=p,results_hex=r,body_sha256=h))
 name=b'research_death135_stack0';add+=unsigned(len(name))+name+b'\3\0'
 payload=unsigned(len(old)+4)+raw[first:ex[3]]+add;changed=raw[:ex[1]]+b'\7'+unsigned(len(payload))+payload+raw[ex[3]:]
 fresh=section_list(changed);assert [p[0]for p in parts]==[p[0]for p in fresh] and not any(p[0]==8 for p in parts)
 assert all(raw[a[1]:a[3]]==changed[b[1]:b[3]] for a,b in zip(parts,fresh) if a[0]!=7)
 path=out/'player-death135-private.wasm';path.write_bytes(changed)
 manifest=dict(kind='full135_no_revival_mode0_death_component',version='0.135.1',actual_build='90898d5e3',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=path.name,module_sha256=sha(path),roles=roles,original_exports=old,only_changed_section=7,stack_global=0,stack_initial=1048576,malloc_index=91941,denied_imports=878,memory_page_cap=512,target_executed=False,validation='Node WebAssembly.compile before any instance/target call')
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
