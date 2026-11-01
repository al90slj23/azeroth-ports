#!/usr/bin/env python3
"""Private fixed135922/1076/2244/21455 exports, unchanged bodies/callees."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,signal,sqlite3,subprocess,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,VALIDATOR_SHA,parse_source,section_list,export_entries
ROLES=((922,'cast',b'\x7f\x7f',b'\x7f'),(1076,'owned',b'\x7f\x7d',b''),
       (2244,'effect',b'\x7f\x7e\x7f\x7d\x7f',b''),(21455,'merge',b'\x7f\x7d\x7d\x7d',b''))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def unsigned(x):
 out=bytearray()
 while x>=128:out.append((x&127)|128);x>>=7
 out.append(x);return bytes(out)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
def source_definition():
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;segments=parse_source(raw)[4]
 def data(address,n):
  out=bytearray(n)
  for s in segments:
   if s['address']is None:continue
   lo,hi=max(address,s['address']),min(address+n,s['address']+s['length'])
   if lo<hi:out[lo-address:hi-address]=raw[s['file_offset']+lo-s['address']:s['file_offset']+hi-s['address']]
  return bytes(out)
 import struct
 found={}
 for j in range(114):
  pointer=5467428+j*88;row=data(pointer,88);w=struct.unpack('<22I',row);name=data(w[3],w[4])
  if name in(b'demo_shout',b'fireball'):
   found[name.decode()]=dict(pointer=pointer,ability_id=name.decode(),execution_kind=row[84],effect_tag=w[0],spell_id=w[11],school=row[85],damage_bits=w[12],cooldown_bits=w[13],range_bits=w[14],radius_bits=w[15],count=w[16],definition_hex=row.hex())
 found['class_leech_bits']={}
 for cls in(1,2,3,4,5,7,8,9,11):
  pointer=int.from_bytes(data(1595888+((cls-2)&255)*4,4),'little')if((cls-2)&255)<=9 else 5462608
  found['class_leech_bits'][str(cls)]=int.from_bytes(data(pointer+80,4),'little')
 assert found['demo_shout']['pointer']==5467868 and found['demo_shout']['effect_tag']==11;return found
def build_demo():
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('demo-shout135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
 types,imports,decl,bodies,_=parse_source(raw);assert len(imports)==878;parts=section_list(raw);assert 8 not in[x[0]for x in parts];section=next(s for s in parts if s[0]==7);exports,first=export_entries(raw,section);extra=b'';entries=[]
 for index,name,params,returns in ROLES:
  assert types[decl[index-878]]==(params,returns);start,end=bodies[index];entry='demo135_'+name;encoded=entry.encode();extra+=unsigned(len(encoded))+encoded+b'\0'+unsigned(index);entries.append(dict(index=index,role=name,export=entry,signature=[params.hex(),returns.hex()],body_start=start,body_end=end,body_sha256=hashlib.sha256(raw[start:end]).hexdigest()))
 name=b'demo135_stack0';extra+=unsigned(len(name))+name+b'\3'+unsigned(0);payload=unsigned(len(exports)+len(ROLES)+1)+raw[first:section[3]]+extra;changed=raw[:section[1]]+b'\7'+unsigned(len(payload))+payload+raw[section[3]:];new=section_list(changed)
 assert[x[0]for x in parts]==[x[0]for x in new]and all(raw[a[1]:a[3]]==changed[b[1]:b[3]]for a,b in zip(parts,new)if a[0]!=7)
 path=out/'demo-shout135-exports.wasm';path.write_bytes(changed);validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA;command=[str(validator),'--enable-all',str(path)]
 with(out/'validation.stdout').open('wb')as stdout,(out/'validation.stderr').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'validator-owned.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=45,command=command));began=time.monotonic()
  try:child.wait(timeout=45)
  finally:
   try:os.killpg(child.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:child.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True),seconds=time.monotonic()-began);save(out/'validator-terminal.json',terminal);assert child.returncode==0 and terminal['pid_missing']and terminal['pgid_missing']
 static=[];profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
 with sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(profile/'official-0.135.1-full.wat').open('rb')as wat:
  db.execute('pragma query_only=on')
  for index in(21455,2244,922,1076,4543,15511,914,27562,18353):
   lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone();assert hi-lo<1048576 and bodies[index]==(bs,be);wat.seek(lo);text=wat.read(hi-lo);(out/f'demo-{index}.wat').write_bytes(text);static.append(dict(index=index,wat_start=lo,wat_end=hi,wat_bytes=len(text),wat_sha256=hashlib.sha256(text).hexdigest(),body_start=bs,body_end=be,body_sha256=hashlib.sha256(raw[bs:be]).hexdigest()))
 manifest=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,module_file=path.name,module_sha256=sha(path),only_changed_section=7,entries=entries,private_stack_global0=True,original_bodies_and_callees_unchanged=True,function_imports=878,target_executed=False,static_functions=static,definitions=source_definition());save(out/'manifest.json',manifest);return out,manifest
if __name__=='__main__':
 out,m=build_demo();print(json.dumps(dict(directory=str(out),module_sha256=m['module_sha256'],target_executed=False)))
