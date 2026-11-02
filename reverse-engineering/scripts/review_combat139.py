#!/usr/bin/env python3
"""Independent read-only139 nonlethal913 review; never imports author code.

Recomputes captured projections using struct-based binary32 reference arithmetic,
reparses source/export-only module and AST closure, and binds real WAT windows.
No original, author model/checker/builder, native executable or browser is run.
"""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import ast,hashlib,json,math,sqlite3,struct,time
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/combat0139-oracle-20261102T014508.868107Z'
COMPARISON_SHA='87aa5086a5b92546a71924b5c54e7f72dfbf6d0400bf7a5cffe23b1f6baa1c3d'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
MAP=ROOT/'evidence/engine139-refined-static-20261102T013743.612949Z/mapping.json'
MAP_SHA='7b41961bce7f45e74a8d2a24305cf84d0d64f2f2d739c723b1e445af208c40f0'

def sha(p):
 with Path(p).open('rb')as s:return hashlib.file_digest(s,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def u32(r,o):return struct.unpack_from('<I',r,o)[0]
def s32(r,o):return struct.unpack_from('<i',r,o)[0]
def u64(r,o):return struct.unpack_from('<Q',r,o)[0]
def fp(x):return struct.unpack('<f',struct.pack('<I',x))[0]
def bits(x):
 try:return struct.unpack('<I',struct.pack('<f',x))[0]
 except OverflowError:return 0xff800000 if x<0 else 0x7f800000
def f32(x):return fp(bits(x))

class Reader:
 def __init__(self,b,a=0,z=None):self.b=b;self.p=a;self.z=len(b)if z is None else z
 def byte(self):assert self.p<self.z;x=self.b[self.p];self.p+=1;return x
 def uint(self):
  v=0;s=0
  while True:
   x=self.byte();v|=(x&127)<<s
   if x<128:return v
   s+=7;assert s<=35
 def sint(self):
  v=0;s=0
  while True:
   x=self.byte();v|=(x&127)<<s;s+=7
   if x<128:return v-(1<<s)if x&64 else v
   assert s<=35
 def raw(self,n):a=self.p;self.p+=n;assert self.p<=self.z;return self.b[a:self.p]
 def name(self):return self.raw(self.uint()).decode()
 def end(self):assert self.p==self.z

def module_sections(raw):
 assert raw[:8]==b'\0asm\1\0\0\0';r=Reader(raw,8);out=[]
 while r.p<r.z:
  start=r.p;k=r.byte();n=r.uint();a=r.p;r.raw(n);out.append(dict(kind=k,start=start,payload=a,end=r.p))
 return out

def parse_module(raw):
 sections=module_sections(raw);ds={s['kind']:s for s in sections};assert 8 not in ds
 def reader(k):s=ds[k];return Reader(raw,s['payload'],s['end'])
 r=reader(1);types=[]
 for _ in range(r.uint()):assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
 r.end();r=reader(2);imports=[]
 for i in range(r.uint()):
  mod,name,kind=r.name(),r.name(),r.byte();assert kind==0;ty=r.uint();imports.append(dict(module=mod,name=name,kind='function',type_index=ty,signature=types[ty]))
 r.end();r=reader(3);decl=[r.uint()for _ in range(r.uint())];r.end();r=reader(7);exports=[]
 for _ in range(r.uint()):exports.append((r.name(),r.byte(),r.uint()))
 r.end();r=reader(10);bodies={}
 for j in range(r.uint()):n=r.uint();a=r.p;r.raw(n);bodies[len(imports)+j]=(a,r.p)
 r.end();assert len(bodies)==len(decl)
 mr=reader(5);assert mr.uint()==1;flags=mr.uint();assert flags in(0,1);minimum_pages=mr.uint()
 if flags:mr.uint()
 mr.end()
 r=reader(11);segments=[]
 for _ in range(r.uint()):
  flag=r.uint();assert flag in(0,1,2)
  if flag==1:address=None
  else:
   if flag==2:assert r.uint()==0
   assert r.byte()==0x41;address=r.sint();assert r.byte()==0x0b
  n=r.uint();start=r.p;r.raw(n);segments.append((address,start,n))
 r.end()
 return dict(sections=sections,types=types,imports=imports,decl=decl,exports=exports,bodies=bodies,data_segments=segments,minimum_memory_pages=minimum_pages)

def reference(case):
 state=case['state'];units=[bytearray.fromhex(x)for x in state['units432_hex']];assert all(len(x)==432 for x in units)
 assert state['sources']==dict(items2028=[],spells2052=[],proc_schedule1972=[],other_procs_absent=True)
 total=struct.unpack('<d',struct.pack('<Q',int(state['accounted_total_bits'])))[0];answers=[];details=[]
 for op in case['operations']:
  target=int(op['target_id']);i=next((j for j,x in enumerate(units)if u64(x,112)==target),None);reason='phase'if state['phase2587']!=1 else'missing'if i is None else None;damage=None
  if reason is None:
   row=units[i];assert s32(row,244)==-1 and s32(row,40)!=3 and op['context']==0
   now=fp(state['now_bits']);m=1.
   if now<fp(u32(row,148)):m=f32(m+fp(u32(row,144)))
   term=fp(u32(row,152))if now<fp(u32(row,156))else fp(u32(row,160))if now<fp(u32(row,164))else 0.
   m=f32(m+term);m=f32(m+fp(u32(row,368)));m=f32(m+0.)
   school=.10000000149011612 if(op['school']&254)==2 and now<fp(u32(row,372))else 0.
   raw=f32(fp(op['amount_bits'])*f32(m+school));scale=1.
   if s32(row,64)!=-1:
    if now<fp(u32(row,420)):scale=1.5
    elif now<fp(u32(row,416)):scale=.25
    elif any(u32(x,0)==0 and s32(x,40)==2 and u64(x,32)==target for x in units):scale=.25
   raw=f32(raw*scale)
   if u32(row,0)==1:reason='dead_marker1'
   else:
    damage=max(1.,1. if math.isnan(raw)else raw);hp=fp(u32(row,288));after=f32(hp-damage);assert not after<=0,'Fixture escaped nonlethal domain'
    old=0. if math.isnan(hp)or not hp>0 else hp;account=min(old,damage);total+=account;struct.pack_into('<I',row,288,bits(after));reason='accepted'
  answers.append(dict(units432_hex=[x.hex()for x in units],accounted_total_bits=str(struct.unpack('<Q',struct.pack('<d',total))[0]),rng_words=state['rng_words']))
  details.append(dict(reason=reason,damage_bits=None if damage is None else bits(damage)))
 return dict(id=case['id'],answers=answers),details

def local_closure(files):
 #Resolve local Python imports from literal source AST only. Package entry
 #modules participate even when a submodule was imported explicitly.
 sources=set(files);edges=set();known={str((ROOT/n).resolve()):n for n in sources}
 def candidate(parts):
  for base in [ROOT/'scripts',ROOT/'reconstruction']:
   p=base.joinpath(*parts)
   for f in [p.with_suffix('.py'),p/'__init__.py']:
    if f.exists():return f.resolve()
 def targets(parts):
  fs=[]
  for j in range(1,len(parts)):
   q=candidate(parts[:j])
   if q and q.name=='__init__.py':fs.append(q)
  q=candidate(parts)
  if q:fs.append(q)
  return fs
 for name in sorted(sources):
  if not name.endswith('.py'):continue
  p=ROOT/name;tree=ast.parse(p.read_text())
  if name.startswith('reconstruction/'):
   rel=p.relative_to(ROOT/'reconstruction').with_suffix('');package=list(rel.parts[:-1])
  else:package=[]
  for node in ast.walk(tree):
   paths=[]
   if isinstance(node,ast.Import):paths=[x.name.split('.')for x in node.names]
   elif isinstance(node,ast.ImportFrom):
    prefix=package[:len(package)-node.level+1]if node.level else[];parts=prefix+(node.module.split('.')if node.module else[]);paths=[parts]
    paths.extend(parts+[x.name]for x in node.names if x.name!='*')
   for parts in paths:
    for target in targets(parts):
     assert str(target)in known,('unfrozen local dependency',name,str(target));edges.add((name,known[str(target)]))
 return sorted(map(list,edges))

def main():
 start=time.monotonic();assert sha(CASE/'comparison.json')==COMPARISON_SHA and sha(SOURCE)==SOURCE_SHA and sha(MAP)==MAP_SHA
 receipt=json.loads((CASE/'comparison.json').read_text());prepared=json.loads((CASE/'prepared.json').read_text());manifest=json.loads((CASE/'manifest.json').read_text());runtime=json.loads((CASE/'runtime.json').read_text());terminal=json.loads((CASE/'process-terminal.json').read_text())
 assert receipt['complete']and receipt['cases']==80 and receipt['calls']==125 and receipt['mismatch_cases']==0 and receipt['expected_before_original']
 assert receipt['source_before']==receipt['source_after']==prepared['source_closure']
 for n,h in receipt['source_before'].items():assert sha(ROOT/n)==h and sha(CASE/'source-snapshot'/n)==h
 edges=local_closure(receipt['source_before']);assert edges==sorted(receipt['source_import_edges'])
 for n,h in receipt['artifacts'].items():assert sha(CASE/n)==h and prepared['artifacts'][n]==h
 raw=SOURCE.read_bytes();original=parse_module(raw);changed=(CASE/manifest['module_file']).read_bytes();modified=parse_module(changed)
 assert len(original['imports'])==882 and len(original['bodies'])==177101
 assert original['types'][original['decl'][913-882]]==('7f7e7d7f7f7f7f','')and original['decl'][913-882]==278
 assert original['types'][original['decl'][93344-882]]==('7f7f','7f')
 assert len(original['sections'])==len(modified['sections'])
 for a,b in zip(original['sections'],modified['sections']):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
 assert modified['exports']==original['exports']+[('research139_damage913',0,913),('research139_stack0',3,0)]
 assert ('__wbindgen_malloc',0,93344)in original['exports']
 body=original['bodies'][913];assert hashlib.sha256(raw[body[0]:body[1]]).hexdigest()==manifest['entry']['body_sha256']
 def static_read(address,n):
  assert 0<=address<=address+n<=original['minimum_memory_pages']*65536 and n<=4194304
  result=bytearray(n)
  for a,p,size in original['data_segments']:
   if a is None:continue
   lo,hi=max(a,address),min(a+size,address+n)
   if lo<hi:result[lo-address:hi-address]=raw[p+lo-a:p+hi-a]
  return bytes(result)
 declaration=manifest['npc_definition'];npc=static_read(declaration['pointer'],72);assert npc.hex()==declaration['raw72_hex']
 assert static_read(u32(npc,16),u32(npc,20))==b'Kobold Vermin'and u32(npc,24)==600
 native_path=SOURCE.parent/'windows-0.139.0/AzerothSurvivors.exe';native=native_path.read_bytes();assert hashlib.sha256(native).hexdigest()==manifest['windows_reference']['sha256']
 assert npc[24:69].hex()==manifest['windows_reference']['scalar_tail45_hex'];native_at=native.find(npc[24:69]);assert native_at==120664736 and native.find(npc[24:69],native_at+1)<0
 assert manifest['windows_reference']['scalar_tail_file_matches']==[native_at]
 assert sha(CASE/'913.wat')==manifest['entry']['wat_sha256'];lines=[x.strip()for x in(CASE/'913.wat').read_text().splitlines()];guards=[]
 def guard(label,sequence):
  at=[j+1 for j in range(len(lines)-len(sequence)+1)if lines[j:j+len(sequence)]==sequence];assert at,label;guards.append(dict(label=label,relative_sites=at,instructions=sequence))
 guard('phase1',['local.get 0','i32.load8_u offset=2587','i32.const 1','i32.ne','br_if 0 (;@3;)'])
 guard('432countstride',['i32.load offset=1792','local.tee 16','i32.const 432','i32.mul'])
 guard('GUID112',['local.get 7','i64.load offset=112','local.set 48'])
 guard('strict_school372_from_start_minus60_then_plus432',['local.get 9','f32.load','local.get 39','f32.gt','i32.eqz','br_if 0 (;@4;)','f32.const 0x1.99999ap-4 (;=0.1;)'])
 guard('HP288',['local.get 19','i32.const 288','i32.add','local.tee 7','local.get 7','f32.load'])
 guard('accounted_f64_from_f32min',['f64.load offset=984','local.get 36','local.get 37','f32.min','f64.promote_f32','local.tee 53','f64.add','f64.store offset=984'])
 guard('empty1972_skips_newproc',['local.get 0','i32.load offset=1972','i32.eqz','br_if 0 (;@7;)'])
 guard('nonempty1972_pophelper',['local.get 8','local.get 0','i32.const 1964','i32.add','call 69550'])
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('combat139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');watfile=PROFILE/'official-0.139.0-full.wat'
 helpers=[]
 with watfile.open('rb')as stream:
  for idx in [913,69550,93344]:
   loc=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());assert original['bodies'][idx]==(loc['body_start'],loc['body_end']);stream.seek(loc['wat_start']);text=stream.read(loc['wat_end']-loc['wat_start']);assert text.startswith(f'  (func (;{idx};)'.encode());(out/f'{idx}.wat').write_bytes(text);helpers.append(dict(index=idx,body_sha256=hashlib.sha256(raw[loc['body_start']:loc['body_end']]).hexdigest(),wat_sha256=hashlib.sha256(text).hexdigest(),**loc))
 assert helpers[0]['wat_sha256']==sha(CASE/'913.wat')
 helper=(out/'69550.wat').read_text();assert 'i32.load offset=8'in helper and 'i32.load offset=4'in helper and 'i64.load align=4'in helper and 'memory.copy'in helper and 'i32.store offset=8'in helper
 calls=[dict(q)for q in db.execute('select callee,wat_offset,wat_line,instruction from calls where caller=913')];assert calls==manifest['direct_calls']and len(calls)==277
 exactimports=[dict(module=x['module'],name=x['name'],kind=x['kind'])for x in original['imports']];assert exactimports==runtime['denied_import_surface'];assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882
 assert runtime['cases']==runtime['fresh_instances']==80 and runtime['full_original913_calls']==125
 assert runtime['stack_all_restored']and len(runtime['stack_checks'])==285
 assert Counter(x['role']for x in runtime['stack_checks'])==dict(allocator93344=160,damage913=125)
 assert all(x['before']==x['after']==1048576 and x['returned']for x in runtime['stack_checks'])
 assert runtime['peak_memory_bytes']==20709376 and runtime['peak_memory_bytes']<=33554432 and not runtime['application_start_called']and not runtime['windows_exe_executed']and not runtime['network_used']and not runtime['user_saves_accessed']
 assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['launcher_error']is None and terminal['seconds']<60
 assert sha(CASE/'stdout.jsonl')==receipt['output_sha256']and sha(CASE/'raw-games.jsonl')==receipt['raw_game_observations_sha256']
 assert sha(CASE/'stderr.log')==receipt['stderr_sha256']and (CASE/'stderr.log').stat().st_size==0
 cases=json.loads((CASE/'input.json').read_text());expected=json.loads((CASE/'expected.json').read_text());actual=[json.loads(x)for x in(CASE/'stdout.jsonl').read_text().splitlines()];observations=[json.loads(x)for x in(CASE/'raw-games.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==80 and len(observations)==125
 mismatches=[];readcalls=0;unitbytes=0;reasons=Counter();physical_unchanged=0;details=[];ptrs=set();raw_changed=Counter()
 for case,want,got in zip(cases,expected,actual):
  answer,steps=reference(case);reasons.update(x['reason']for x in steps)
  if answer!=want or answer!=got:mismatches.append(case['id'])
  prior=[bytes.fromhex(x)for x in case['state']['units432_hex']]
  for j,(op,value,step)in enumerate(zip(case['operations'],got['answers'],steps)):
   obs=observations[readcalls];readcalls+=1;assert(obs['case_id'],obs['operation'])==(case['id'],j);game=bytes.fromhex(obs['raw_game8192_hex']);assert len(game)==8192
   assert u64(game,984)==int(value['accounted_total_bits']);assert list(struct.unpack_from('<4I',game,1720))==case['state']['rng_words'];assert game[2587]==case['state']['phase2587']and u32(game,2352)==case['state']['now_bits']
   assert struct.unpack_from('<III',game,1784)==(len(prior),obs['unit_pointer'],len(prior));assert all(u32(game,o)==0 for o in [1972,2032,2056])
   current=[bytes.fromhex(x)for x in value['units432_hex']];assert len(prior)==len(current)
   for a,b in zip(prior,current):
    unitbytes+=len(b);changed_offsets=[k for k,(x,y)in enumerate(zip(a,b))if x!=y];assert set(changed_offsets)<=set(range(288,292));physical_unchanged+=len(b)-len(changed_offsets)
   prior=current;ptrs.add((obs['game_pointer'],obs['unit_pointer']));details.append(dict(case=case['id'],operation=j,**step))
 assert not mismatches and readcalls==125
 artifacts={p.name:dict(sha256=sha(p),bytes=p.stat().st_size)for p in CASE.iterdir()if p.is_file()and p.name!='combat139-original-exports.wasm'}
 result=dict(status='pass_with_declared_nonlethal_projection_limits',reviewer='/root/self_buffs119_review',author='/root/stats138_review',comparison_sha256=COMPARISON_SHA,source_sha256=SOURCE_SHA,entry_map_dependency_sha256=MAP_SHA,
  independently_recomputed_cases=80,independently_recomputed_full_original_calls=125,fresh_original_calls_by_reviewer=0,author_model_executions_by_reviewer=0,author_checker_executions_by_reviewer=0,author_builder_executions_by_reviewer=0,native_executions_by_reviewer=0,
  independent_reference='Python stdlib struct IEEE binary32 rounding after each operation;no author/model arithmetic imports',mismatch_cases=mismatches,branch_results=dict(reasons),physical_unit_bytes_checked=unitbytes,physical_unchanged_byte_occurrences=physical_unchanged,observed_game_bytes=8192*125,
  source_closure_count=len(receipt['source_before']),source_closure=receipt['source_before'],source_import_edges=edges,static_guards=guards,helpers=helpers,direct_call_sites=277,unique_direct_callees=len({x['callee']for x in calls}),all_original_nonexport_sections_byte_identical=True,export_delta=modified['exports'][len(original['exports']):],
  npc_static_source=dict(pointer=declaration['pointer'],raw72_sha256=hashlib.sha256(npc).hexdigest(),name='Kobold Vermin',native_scalar_tail45_unique_offset=native_at,native_executed=False,native_scope='Exact scalar bytes only;no native ABI/behavior claim'),
  actual_runtime_summary={k:v for k,v in runtime.items()if k not in ['stack_checks','denied_import_surface']},author_owned_process=terminal,case_artifacts_as_read=artifacts,details=details,script_sha256=sha(Path(__file__)),seconds=time.monotonic()-start,
  caveats=['Only these80controlledcases/125calls;not139full-game or Windows runtime acceptance','Full432B records plus f64G984 and unchanged RNG are predicted;full8192B Game is observation with per-spell statistics/packets/visual allocations outside prediction','Empty1972 proves69550is bypassed;its nonempty behavior is read statically but no producer/proc differential accepted','7U64=0/U68=0 controlled fixtures do not restore timer ownership or natural constructor output','8negative author guards are stored author model checks,not independent or original coverage','Original module functions/all actual callees remain present;no claim every callee/branch was dynamically reached','139role-map is our earlier source identity dependency,not a second independent review of that mapping','Earlier prepare-only/pilot batches are excluded from80/125;old135/138passingcases are not transferred','Source input artifacts were pre-pinned by author prepared receipt;extra output hashes here are as-read bindings,not retroactive pre-run freeze'])
 save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),cases=80,calls=125,mismatches=len(mismatches),unit_bytes=unitbytes,source_closure=len(receipt['source_before']),seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
