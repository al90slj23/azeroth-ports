#!/usr/bin/env python3
"""Static139 native/Web consumed build identity, without a full profile.

WASM ptr/len instructions are located in original function-body boundaries and
checked against a bounded seek in the single original139 WAT profile. PE RIP LEA
and the adjacent stack length store independently bind the same nine bytes.
Neither original, WASM start nor game entry executes. Old receipts stay intact.
"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os,re,signal,sqlite3,stat,struct,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
VERSION='0.139.0'
WASM_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
EXE_SHA='0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274'
ACQUISITION_SHA='35c0e6b106056c47d3826581941174917e970133a46646e49cda8a0296b6e332'
class Reader:
 def __init__(self,data,a=0,b=None):self.data=data;self.pos=a;self.end=len(data)if b is None else b
 def take(self,n):
  assert 0<=n<=self.end-self.pos;out=self.data[self.pos:self.pos+n];self.pos+=n;return out
 def byte(self):return self.take(1)[0]
 def u(self):
  value=shift=0
  while True:
   v=self.byte();value|=(v&127)<<shift;shift+=7;assert shift<=35
   if v<128:return value
 def s(self):
  value=shift=0
  while True:
   v=self.byte();value|=(v&127)<<shift;shift+=7;assert shift<=35
   if v<128:return value-(1<<shift)if v&64 else value
 def string(self):return self.take(self.u())
 def finish(self):assert self.pos==self.end
def sha(p):
 with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
def native(directory,out):
 path=directory/f'windows-{VERSION}/AzerothSurvivors.exe';raw=path.read_bytes();assert len(raw)==150595584 and hashlib.sha256(raw).hexdigest()==EXE_SHA and raw[:2]==b'MZ'
 pe=struct.unpack_from('<I',raw,60)[0];assert raw[pe:pe+4]==b'PE\0\0';count=struct.unpack_from('<H',raw,pe+6)[0];opt=pe+24;size=struct.unpack_from('<H',raw,pe+20)[0];assert struct.unpack_from('<H',raw,opt)[0]==0x20b
 base=struct.unpack_from('<Q',raw,opt+24)[0];sections=[]
 for i in range(count):
  p=opt+size+i*40;vsize,rva,n,start=struct.unpack_from('<4I',raw,p+8);assert start+n<=len(raw);sections.append(dict(name=raw[p:p+8].split(b'\0')[0].decode(),rva=rva,file_offset=start,file_size=n,virtual_size=vsize))
 text=next(s for s in sections if s['name']=='.text');code=raw[text['file_offset']:text['file_offset']+text['file_size']]
 candidates=[];pattern=rb'\x48\x8d\x05(.{4})\x48\x89\x85(.{4})\x48\xc7\x85(.{4})(.{4})'
 for literal in re.finditer(rb'([0-9a-f]{1,16})'+re.escape(VERSION.encode()),raw):
  at=literal.start();build=literal[1];data=next(s for s in sections if s['file_offset']<=at<s['file_offset']+s['file_size']);pointer=base+data['rva']+at-data['file_offset'];vp=pointer+len(build);descriptor=struct.pack('<QQ',vp,len(VERSION))
  if raw[literal.end():literal.end()+16]!=descriptor:continue
  for m in re.finditer(pattern,code,re.S):
   instruction=base+text['rva']+m.start();target=instruction+7+struct.unpack('<i',m[1])[0]
   if target!=pointer:continue
   pf,lf,length=struct.unpack('<i',m[2])[0],struct.unpack('<i',m[3])[0],struct.unpack('<I',m[4])[0]
   if lf!=pf+8 or length!=len(build):continue
   candidates.append(dict(version=VERSION,build=build.decode(),build_length=length,exe_path=str(path),exe_sha256=EXE_SHA,exe_bytes=len(raw),image_base=hex(base),build_file_offset=at,build_pointer=hex(pointer),version_pointer=hex(vp),version_descriptor_hex=descriptor.hex(),
    instruction_guard=dict(instruction_va=hex(instruction),instruction_file_offset=text['file_offset']+m.start(),pointer_stack_offset=pf,length_stack_offset=lf,length=length,exact_instruction_bytes_hex=m[0].hex())))
 assert len(candidates)==1 and candidates[0]['build_length']==9
 result=candidates[0];start=int(result['instruction_guard']['instruction_va'],16);cmd=['/usr/bin/objdump','--disassemble','--start-address='+hex(start),'--stop-address='+hex(start+50),str(path)];began=time.monotonic()
 with(out/'native-build-consumer.stdout').open('wb')as stdout,(out/'native-build-consumer.stderr').open('wb')as stderr:
  child=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,start_new_session=True)
  try:code=child.wait(timeout=20)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
 terminal=dict(command=cmd,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-began,deadline_seconds=20,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True),target_executed=False)
 save(out/'native-objdump-terminal.json',terminal);assert code==0 and terminal['pid_missing']and terminal['pgid_missing']and(out/'native-build-consumer.stdout').stat().st_size<65536
 result.update(disassembly_file='native-build-consumer.stdout',disassembly_sha256=sha(out/'native-build-consumer.stdout'),objdump_terminal=terminal,target_executed=False)
 save(out/'native-identity.json',result);return result
def signed_bytes(n):
 out=bytearray()
 while True:
  b=n&127;n>>=7;done=(n==0 and not b&64)or(n==-1 and b&64);out.append(b if done else b|128)
  if done:return bytes(out)
def web_binary(directory,identity):
 path=directory/'latest-wenilla_bg.wasm';raw=path.read_bytes();assert len(raw)==92511151 and hashlib.sha256(raw).hexdigest()==WASM_SHA and raw[:8]==b'\0asm\1\0\0\0'
 r=Reader(raw,8);sections={}
 while r.pos<r.end:
  kind=r.byte();n=r.u();a=r.pos;r.take(n)
  if kind:assert kind not in sections;sections[kind]=(a,r.pos)
 r.finish();needle=(identity['build']+VERSION).encode();at=raw.find(needle);assert at>=0 and raw.find(needle,at+1)<0
 data=Reader(raw,*sections[11]);segment=None
 for i in range(data.u()):
  flags=data.u();assert flags in(0,1,2);address=None
  if flags!=1:
   if flags==2:data.u()
   assert data.byte()==0x41;address=data.s()&0xffffffff;assert data.byte()==0x0b
  n=data.u();begin=data.pos;data.take(n)
  if begin<=at and at+len(needle)<=begin+n:segment=dict(index=i,address=address,file_offset=begin,bytes=n)
 data.finish();assert segment is not None and segment['address']is not None
 pointer=segment['address']+at-segment['file_offset'];vp=pointer+identity['build_length'];descriptor=struct.pack('<II',vp,len(VERSION));assert descriptor in raw[segment['file_offset']:segment['file_offset']+segment['bytes']]
 imports=Reader(raw,*sections[2]);total_imports=imports.u();function_imports=0
 for _ in range(total_imports):
  imports.string();imports.string();assert imports.byte()==0;imports.u();function_imports+=1
 imports.finish();decl=Reader(raw,*sections[3]);declared=decl.u();types=[decl.u()for _ in range(declared)];decl.finish()
 code=Reader(raw,*sections[10]);assert code.u()==declared;marker=b'\x41'+signed_bytes(pointer);bindings=[]
 for j in range(declared):
  n=code.u();begin=code.pos;body=code.take(n);p=0
  while True:
   hit=body.find(marker,p)
   if hit<0:break
   p=hit+1
   for start in range(max(0,hit-40),hit):
    q=Reader(body,start);ops=[]
    try:
     def op(expected,name,arg):
      offset=q.pos;assert q.byte()==expected;values=[arg()];ops.append(dict(file_offset=begin+offset,mnemonic=name,operands=values));return values[0]
     local=op(0x20,'local.get',q.u);length=op(0x41,'i32.const',q.s)
     offset=q.pos;assert q.byte()==0x36;align=q.u();length_field=q.u();ops.append(dict(file_offset=begin+offset,mnemonic='i32.store',operands=[align,length_field]))
     same=op(0x20,'local.get',q.u);value=op(0x41,'i32.const',q.s)
     offset=q.pos;assert q.byte()==0x36;palign=q.u();pointer_field=q.u();ops.append(dict(file_offset=begin+offset,mnemonic='i32.store',operands=[palign,pointer_field]))
     if local!=same or length!=identity['build_length']or value!=pointer or length_field!=pointer_field+4:continue
     bindings.append(dict(function=function_imports+j,body_start=begin,body_end=begin+n,body_sha256=hashlib.sha256(body).hexdigest(),function_type=types[j],guard_start=begin+start,guard_end=begin+q.pos,guard_bytes_hex=body[start:q.pos].hex(),guard_instructions=ops,length_store_offset=length_field,pointer_store_offset=pointer_field))
    except(AssertionError,IndexError):continue
 code.finish();assert len(bindings)==1
 return dict(version=VERSION,build=identity['build'],build_length=identity['build_length'],wasm_path=str(path),wasm_sha256=WASM_SHA,wasm_bytes=len(raw),build_file_offset=at,build_pointer=pointer,version_pointer=vp,version_descriptor_hex=descriptor.hex(),data_segment=segment,total_imports=total_imports,function_imports=function_imports,defined_functions=declared,**bindings[0])
def web_indexed(identity,profile,out):
 manifest_path=profile/'manifest.json';manifest=json.loads(manifest_path.read_text())
 assert manifest['target_version']==VERSION and manifest['original_sha256']==WASM_SHA and manifest['function_imports']==identity['function_imports']and manifest['defined_functions']==identity['defined_functions']and manifest['full_module_validated']and manifest['sqlite_integrity_check']=='ok'
 database=profile/'index.sqlite';assert stat.S_IMODE(database.stat().st_mode)==0o444
 with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)as db:
  db.execute('pragma query_only=ON');a,b,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(identity['function'],)).fetchone()
 assert(bs,be)==(identity['body_start'],identity['body_end'])and b-a<=1048576
 wat=profile/'official-0.139.0-full.wat'
 with wat.open('rb')as stream:stream.seek(a);raw=stream.read(b-a)
 assert raw.startswith(('  (func (;'+str(identity['function'])+';)').encode())
 lines=[line.strip()for line in raw.decode().splitlines()];instructions=identity['guard_instructions'];local=instructions[0]['operands'][0]
 wanted=[f'local.get {local}',f"i32.const {identity['build_length']}",f"i32.store offset={identity['length_store_offset']}",f'local.get {local}',f"i32.const {identity['build_pointer']}",f"i32.store offset={identity['pointer_store_offset']}"]
 hits=[j for j in range(len(lines)-len(wanted)+1)if lines[j:j+len(wanted)]==wanted];assert len(hits)==1
 target=out/'web-branding-function.wat';target.write_bytes(raw)
 identity.update(function_wat_file=target.name,function_wat_sha256=sha(target),wat_bytes_read=len(raw),guard_first_function_line=hits[0]+1,guard_WAT=wanted,
  instruction_boundaries_confirmed_by_original_disassembler=True,profile_manifest=str(manifest_path),profile_manifest_sha256=sha(manifest_path),profile_database=str(database),profile_database_mode='0444',
  profile_WAT=str(wat),profile_WAT_sha256_from_producer=manifest['wat_sha256'],profile_database_sha256_from_producer=manifest['database_sha256'],single_existing_profile_reused=True,full_WAT_or_database_rehashed=False,target_executed=False)
 return identity
def main():
 assert len(sys.argv)==3;directory=Path(sys.argv[1]).resolve();profile=Path(sys.argv[2]).resolve();assert directory.is_relative_to(ROOT/'originals')and str(directory).startswith('/Volumes/RuiRui4TB/')
 acquisition=directory/'release-acquisition-resumed.json';assert sha(acquisition)==ACQUISITION_SHA;acq=json.loads(acquisition.read_text());assert acq['sources_unchanged']and acq['native_manifest_equal_before_after']and acq['raw_html_equal_before_after']and not acq['target_executed']and not acq['wasm_instantiated']
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('branding0139-identity-%Y%m%dT%H%M%S.%fZ');out.mkdir();before=sha(Path(__file__));(out/'source-snapshot').mkdir();(out/'source-snapshot'/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(dict(directory=str(out))),flush=True)
 native_identity=native(directory,out);web=web_indexed(web_binary(directory,native_identity),profile,out);save(out/'web-identity.json',web)
 assert before==sha(Path(__file__))and sha(acquisition)==ACQUISITION_SHA
 result=dict(kind='actual139_consumed_native_web_build_identity',status='native_web_same_version_build_and_explicit_nine_byte_consumers_proved',version=VERSION,actual_build=web['build'],actual_build_length=9,
  native=native_identity,web=web,native_web_same_version_build_and_length=True,stamp=acq['web']['stamp'],acquisition_receipt=str(acquisition),acquisition_receipt_sha256=ACQUISITION_SHA,
  source_sha256_before=before,source_sha256_after=before,target_executed=False,wasm_instantiated=False,new_original_cases=0,new_runtime_cases=0,new_full880_frames=0,
  full_profile_started=False,old_acceptance_transferred=False,installed_packages_or_saves_modified=False,
  limitations=['Static branding consumer identity only; not runtime, protocol/gameplay compatibility or transferred135/138 acceptance.','Original139 WAT comes from the separately owned single full profile; this pass only seeks one bounded branding function and does not rehash the whole WAT or database.','No second full WAT/index/profile is produced here; the separate single139 profiler owns that work.'])
 save(out/'identity.json',result);print(json.dumps(dict(directory=str(out),identity_sha256=sha(out/'identity.json'),actual_build=result['actual_build'],length=9,web_function=web['function'],target_executed=False)),flush=True)
if __name__=='__main__':main()
