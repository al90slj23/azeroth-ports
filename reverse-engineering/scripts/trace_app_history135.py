#!/usr/bin/env python3
"""Private immutable-body history/entropy exports and bounded static trace."""
from datetime import datetime,timezone
import hashlib,json,sqlite3,subprocess
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries,VALIDATOR_SHA
from build_upgrade134_oracle import unsigned,sha

ROLES={'history135_empty':(53845,'7f','943285579e1934d411fe1e4d465a1d523be0705216068352f3acbbbe48dcf1c0'),
 'history135_drop':(28797,'7f','6e6c0f5317cbe15e579b2a02f43fc54f974c0aca8bf914cdf814fd41ed507aaf'),
 'history135_seed':(60416,'','6fd41e5c89903d91cf1ef1a431191632961b37d7e592701d3e62f22740d22e30'),
 'history135_entropy':(81334,'7f','f78993c4e711bf523a1890b24a97835b3b487350e9bc2a3de72913f87e6313a5')}

def build(out):
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
 types,imports,decl,bodies,_=parse_source(raw);old=section_list(raw);assert len(imports)==878 and 8 not in[x[0]for x in old]
 glob=next(x for x in old if x[0]==6);assert raw[glob[2]:glob[3]].hex()=='017f01418080c0000b'
 ex=next(x for x in old if x[0]==7);exports,first=export_entries(raw,ex);added=b'';roles=[]
 for name,(index,params,digest)in ROLES.items():
  assert types[decl[index-len(imports)]]==(bytes.fromhex(params),b'');a,z=bodies[index];assert hashlib.sha256(raw[a:z]).hexdigest()==digest
  n=name.encode();added+=unsigned(len(n))+n+b'\0'+unsigned(index);roles.append(dict(name=name,index=index,params=params,body_sha256=digest))
 n=b'history135_stack';added+=unsigned(len(n))+n+b'\x03\0'
 payload=unsigned(len(exports)+len(ROLES)+1)+raw[first:ex[3]]+added
 changed=raw[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+raw[ex[3]:];new=section_list(changed)
 assert[x[0]for x in old]==[x[0]for x in new]
 for x,y in zip(old,new):
  if x[0]!=7:assert raw[x[1]:x[3]]==changed[y[1]:y[3]]
 path=out/'app-history135.wasm';path.write_bytes(changed)
 validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
 r=subprocess.run([str(validator),'--enable-all',str(path)],capture_output=True,timeout=45);assert r.returncode==0
 profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';con=sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row;rows=[]
 with(profile/'official-0.135.1-full.wat').open('rb')as f:
  for i in(53845,28797,60416,81334,4253):
   row=dict(con.execute('select *from functions where idx=?',(i,)).fetchone());f.seek(row['wat_start']);wat=f.read(row['wat_end']-row['wat_start']);(out/f'{i}.wat').write_bytes(wat);rows.append(dict(**row,wat_sha256=hashlib.sha256(wat).hexdigest(),body_sha256=hashlib.sha256(raw[slice(*bodies[i])]).hexdigest()))
 result=dict(version='0.135.1',build='0898d5e3',module_file=path.name,module_sha256=sha(path),original_sha256=SOURCE_SHA,only_changed_section=7,roles=roles,stack_global_index=0,stack_mutable_original_unchanged=True,functions=rows,allocator=91941,shared52_unchanged=True)
 (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result
