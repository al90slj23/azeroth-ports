#!/usr/bin/env python3
"""Static138 consumed branding identity and exact137/138 official JS delta.

Neither target is executed. Reuses136 web() with explicit paths/SHA/version;
the fixed136 guard is untouched. Existing acquisition receipts stay immutable.
The already finished138 full profile is only queried/read at finite ranges.
"""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,os,re,signal,sqlite3,stat,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from verify_build136_identity import web
ROOT=Path(__file__).resolve().parents[1]
NEW=ROOT/'originals/official-release-20261101T201508.341687Z'
OLD=ROOT/'originals/official-acquisition-20261101T154517.001467Z'
PROFILE=ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z'
PROFILE_OWNED=ROOT/'evidence/wasm0138-profile-owned-20261101T202034.856715Z'
WASM_SHA='c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b'
EXE_SHA='eb5fd1c1b96e6180fcf5f3d685d90a61471af28d22e5f060c02b7b7663fbf79e'
ACQUISITION_SHA='a4d5af63a32fb2956f3c3206026b95e2c0a895a0c787c86966e29dcd5edaa0a0'
def sha(path):
 with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False

def native(identity,out):
 path=NEW/'windows-0.138.0/AzerothSurvivors.exe';raw=path.read_bytes();assert len(raw)==147995648 and hashlib.sha256(raw).hexdigest()==EXE_SHA
 pe=struct.unpack_from('<I',raw,0x3c)[0];assert raw[pe:pe+4]==b'PE\0\0';count=struct.unpack_from('<H',raw,pe+6)[0];optional_size=struct.unpack_from('<H',raw,pe+20)[0];optional=pe+24;assert struct.unpack_from('<H',raw,optional)[0]==0x20b
 image_base=struct.unpack_from('<Q',raw,optional+24)[0];sections=[]
 for i in range(count):
  p=optional+optional_size+i*40;name=raw[p:p+8].split(b'\0')[0].decode();vsize,rva,size,start=struct.unpack_from('<4I',raw,p+8);sections.append(dict(name=name,rva=rva,file_offset=start,file_size=size,virtual_size=vsize))
 needle=(identity['build']+identity['version']).encode();at=raw.find(needle);assert at>=0 and raw.find(needle,at+1)<0
 data=next(s for s in sections if s['file_offset']<=at<s['file_offset']+s['file_size']);pointer=image_base+data['rva']+at-data['file_offset'];vp=pointer+identity['build_length'];descriptor=struct.pack('<QQ',vp,len(identity['version']));assert raw[at+len(needle):at+len(needle)+16]==descriptor
 text=next(s for s in sections if s['name']=='.text');code=raw[text['file_offset']:text['file_offset']+text['file_size']];pattern=rb'\x48\x8d\x05(.{4})\x48\x89\x85(.{4})\x48\xc7\x85(.{4})(.{4})';found=[]
 for m in re.finditer(pattern,code,re.S):
  instruction=image_base+text['rva']+m.start();target=instruction+7+struct.unpack('<i',m[1])[0]
  if target!=pointer:continue
  pfield=struct.unpack('<i',m[2])[0];lfield=struct.unpack('<i',m[3])[0];length=struct.unpack('<I',m[4])[0];assert lfield==pfield+8 and length==identity['build_length']
  found.append(dict(instruction_va=hex(instruction),instruction_file_offset=text['file_offset']+m.start(),pointer=hex(pointer),pointer_stack_offset=pfield,length_stack_offset=lfield,length=length,exact_instruction_bytes_hex=m[0].hex()))
 assert len(found)==1;start=int(found[0]['instruction_va'],16);command=['/usr/bin/objdump','--disassemble','--start-address='+hex(start),'--stop-address='+hex(start+50),str(path)];began=time.monotonic();error=None
 with(out/'native-build-consumer.stdout').open('wb')as stdout,(out/'native-build-consumer.stderr').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'objdump-owned.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=20,target_executed=False))
  try:child.wait(timeout=20)
  except Exception as exc:error=repr(exc)
  finally:
   try:os.killpg(child.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:child.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,seconds=time.monotonic()-began,error=error,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True),target_executed=False);save(out/'objdump-terminal.json',terminal);assert child.returncode==0 and error is None and terminal['pid_missing']and terminal['pgid_missing']
 assert(out/'native-build-consumer.stdout').stat().st_size<65536 and(out/'native-build-consumer.stderr').stat().st_size<4096
 return dict(version=identity['version'],build=identity['build'],build_length=identity['build_length'],exe_path=str(path),exe_sha256=EXE_SHA,exe_bytes=len(raw),image_base=hex(image_base),build_file_offset=at,build_pointer=hex(pointer),version_pointer=hex(vp),version_descriptor_hex=descriptor.hex(),instruction_guard=found[0],disassembly_command=command,disassembly_file='native-build-consumer.stdout',disassembly_sha256=sha(out/'native-build-consumer.stdout'),objdump_terminal=terminal,target_executed=False)

def javascript(acquisition,out):
 old=json.loads((OLD/'web-acquisition.json').read_text());records=[]
 for name in('rogue.js','boot.js','wenilla.js'):
  filename='official-'+name;a=(OLD/filename).read_bytes();b=(NEW/filename).read_bytes();assert len(a)==old['scripts'][name]['bytes']and hashlib.sha256(a).hexdigest()==old['scripts'][name]['sha256'];assert len(b)==acquisition['web']['scripts'][name]['bytes']and hashlib.sha256(b).hexdigest()==acquisition['web']['scripts'][name]['sha256']
  sa,sb=a.decode('utf8'),b.decode('utf8');patch=''.join(difflib.unified_diff(sa.splitlines(True),sb.splitlines(True),fromfile='0.137.0/'+filename,tofile='0.138.0/'+filename));target=out/(name+'.diff');target.write_text(patch)
  # Normalize only the numeric shim_idx token on these whole-line generated
  # comments. Nothing in executable JavaScript or string literals is removed.
  pattern=r'(?m)^(\s*// Cast intrinsic for `.*?\bshim_idx: )(\d+)(,.*)$';ma=list(re.finditer(pattern,sa));mb=list(re.finditer(pattern,sb));assert len(ma)==len(mb)==(17 if name=='wenilla.js'else 0)
  na=re.sub(pattern,lambda m:m[1]+'<shim_idx>'+m[3],sa);nb=re.sub(pattern,lambda m:m[1]+'<shim_idx>'+m[3],sb)
  pairs=[dict(old_line=sa[:x.start()].count('\n')+1,new_line=sb[:y.start()].count('\n')+1,old=int(x[2]),new=int(y[2]),delta=int(y[2])-int(x[2]))for x,y in zip(ma,mb)if x[2]!=y[2]]
  if name=='wenilla.js':assert a!=b and na==nb and len(pairs)==17 and all(x['delta']==141 for x in pairs)
  else:assert a==b and not pairs
  api=r'(?m)^\s*(__wbg_[A-Za-z0-9_]+|__wbindgen_[A-Za-z0-9_]+): function\(';ka=re.findall(api,sa);kb=re.findall(api,sb);assert ka==kb
  exports=r'(?m)^export (?:async )?function ([A-Za-z0-9_]+)\(';assert re.findall(exports,sa)==re.findall(exports,sb)
  records.append(dict(name=name,old_path=str(OLD/filename),old_bytes=len(a),old_sha256=hashlib.sha256(a).hexdigest(),new_path=str(NEW/filename),new_bytes=len(b),new_sha256=hashlib.sha256(b).hexdigest(),byte_identical=a==b,diff_file=target.name,diff_bytes=len(patch.encode()),diff_sha256=sha(target),changed_comment_shim_indices=pairs,identical_after_only_exact_comment_numeric_normalization=na==nb,bridge_function_property_keys=ka,bridge_property_key_list_identical=True,exported_function_names=re.findall(exports,sb)))
 return dict(comparison='Frozen official137 versus138 saved HTTPS JS; not target execution',old_version='0.137.0',new_version='0.138.0',files=records,executable_JS_text_identical_after_only_exact_comment_numeric_normalization=True,new_or_removed_bridge_property_keys=[],world_coordinate_API_added_in_these_JS_files=False,release_note_claim=acquisition['native']['notes'],semantic_inference='The publisher describes addon combat numbers anchored in world space. The three compared JS files contain no executable delta; attributing the feature to WASM/internal addon implementation is an inference, not a localized function or behavioral proof.',not_proven=['New WASM/Lua API spelling/signature/ABI','World-to-screen projection/visibility implementation','Built-in combat-number behavior equivalence','Gameplay rules equal between137 and138'])

def main():
 began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('branding0138-identity-%Y%m%dT%H%M%S.%fZ');out.mkdir();receipt=NEW/'release-acquisition.json';assert sha(receipt)==ACQUISITION_SHA;acq=json.loads(receipt.read_text());assert acq['consumed_build']is None and acq['expected_version']=='0.138.0'and acq['source_sha256_before']==acq['source_sha256_after']and acq['native_manifest_equal_before_after']and acq['raw_html_equal_before_after']and not acq['target_executed']and not acq['wasm_instantiated'];source_files=[Path(__file__),ROOT/'scripts/verify_build136_identity.py',ROOT/'scripts/wasm135_profile.py'];before={str(p):sha(p)for p in source_files}
 profile=json.loads((PROFILE/'manifest.json').read_text());terminal=json.loads((PROFILE_OWNED/'process-terminal.json').read_text());assert terminal['exit_code']==0 and terminal['error']is None and terminal['pid_missing']and terminal['pgid_missing']and missing(terminal['pid'])and missing(terminal['pgid'],True)
 assert profile['target_version']=='0.138.0'and profile['original_sha256']==WASM_SHA and profile['full_module_validated']and profile['sqlite_integrity_check']=='ok'and profile['function_imports']==878 and profile['defined_functions']==175576 and profile['counts']['calls']==824482
 assert(PROFILE/'index.sqlite').stat().st_size==profile['database_bytes']==642973696 and stat.S_IMODE((PROFILE/'index.sqlite').stat().st_mode)==0o444 and(PROFILE/'official-0.138.0-full.wat').stat().st_size==profile['wat_bytes']==1321739458
 current=web(NEW,PROFILE,WASM_SHA,'0.138.0',out);assert current['build']=='382771e6c'and current['build_length']==9 and(out/current['function_wat_file']).stat().st_size<=1048576
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
  db.execute('pragma query_only=ON');row=db.execute('select body_start,body_end,wat_start,wat_end from functions where idx=?',(current['function'],)).fetchone();assert row[3]-row[2]<=1048576
 windows=native(current,out);js=javascript(acq,out);save(out/'javascript-diff.json',js)
 profile_summary=dict(profile_manifest=str(PROFILE/'manifest.json'),profile_manifest_sha256=sha(PROFILE/'manifest.json'),profile_owned_terminal=str(PROFILE_OWNED/'process-terminal.json'),profile_owned_terminal_sha256=sha(PROFILE_OWNED/'process-terminal.json'),profile_process=terminal,defined_functions=profile['defined_functions'],function_imports=profile['function_imports'],counts=profile['counts'],wat_path=profile['wat_path'],wat_bytes=profile['wat_bytes'],wat_sha256=profile['wat_sha256'],database_path=profile['database_path'],database_bytes=profile['database_bytes'],database_sha256=profile['database_sha256'],database_mode='0444',sqlite_integrity_check_from_producer=profile['sqlite_integrity_check'],full_module_validated=profile['full_module_validated'],root_profile_producer_only=True,no_second_profile_started=True,whole_WAT_or_database_rehashed_or_fully_read_by_this_pass=False,limited_branding_function_index=current['function'],limited_branding_WAT_bytes=(out/current['function_wat_file']).stat().st_size,code_and_data_indexing_is_not_runtime_acceptance=True)
 assert before=={str(p):sha(p)for p in source_files}and sha(receipt)==ACQUISITION_SHA and json.loads(receipt.read_text())['consumed_build']is None
 result=dict(kind='actual_consumed138_build_identity_and_static_JS_delta',version='0.138.0',actual_build=current['build'],actual_build_length=current['build_length'],status='coherent_native_web_bytes_actual_consumed_build_and_static_profile_verified',web=current,native=windows,native_web_same_version_build_and_explicit_length=True,acquisition_receipt=str(receipt),acquisition_receipt_sha256=ACQUISITION_SHA,acquisition_consumed_build_null_preserved=True,stamp=acq['web']['stamp'],profile=profile_summary,javascript_diff='javascript-diff.json',javascript_diff_sha256=sha(out/'javascript-diff.json'),source_sha256_before=before,source_sha256_after={str(p):sha(p)for p in source_files},target_executed=False,wasm_instantiated=False,new_runtime_cases=0,new_model_validation_cases=0,new_mainloop_frames=0,old_acceptance_transferred=False,installed_packages_or_saves_modified=False,elapsed_seconds=time.monotonic()-began)
 assert result['elapsed_seconds']<60;save(out/'identity.json',result);print(json.dumps(dict(directory=str(out),identity_sha256=sha(out/'identity.json'),actual_build=current['build'],build_length=current['build_length'],web_function=current['function'],web_build_pointer=current['build_pointer'],native_build_pointer=windows['build_pointer'],seconds=result['elapsed_seconds'],targets_executed=False)))
if __name__=='__main__':main()
