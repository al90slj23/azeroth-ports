#!/usr/bin/env python3
"""Source-bound139→1391 static entry mapping;0 target/model executions.

Body+signature is strongest. Normalized structure/call graph remains explicit
static identity evidence, not runtime/behavior acceptance. Similarity alone
never establishes a binding. Reads finite function ranges, not full old WAT.
"""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import argparse,difflib,hashlib,json,re,sqlite3,time
from wasm139_profile import binary_identity as identity139old
from wasm1391_profile import binary_identity as identity139new,Reader,SOURCE,SOURCE_SHA

ROOT=Path(__file__).resolve().parents[1]
BASELINE=ROOT/'evidence/engine1391-baseline139-20261102T134438.745261Z/baseline.json'
BASELINE_SHA='b4dc9feb86ef3e1a2e31d9f08eb8334ccb07ab0b2eab74370065b7e4394630d2'
OLD=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
OLD_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'

def sha(path):
 with path.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def catalog(path,digest,parser):
 raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
 identity,ranges=parser(raw);sections={row['kind']:row for row in identity['sections']}
 r=Reader(raw,sections[1]['payload_start'],sections[1]['end']);types=[]
 for _ in range(r.uint()):
  assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
 r.finish();r=Reader(raw,sections[3]['payload_start'],sections[3]['end']);decl=[r.uint()for _ in range(r.uint())];r.finish();imp=identity['function_imports']
 sig={idx:types[decl[idx-imp]]for idx in ranges}
 hashes={idx:hashlib.sha256(raw[a:b]).hexdigest()for idx,(a,b,_)in ranges.items()}
 seg=[row for row in identity['data_segments']if row['address']is not None]
 return dict(raw=raw,identity=identity,ranges=ranges,sig=sig,hashes=hashes,types=types,
  static_bounds=(min(row['address']for row in seg),max(row['address']+row['bytes']for row in seg)))

def normalized(text,model,erase_data):
 lo,hi=model['static_bounds'];rows=[]
 for line in text.splitlines():
  line=line.strip()
  line=re.sub(r'^\(func \(;\d+;\) \(type \d+\)','(func (type SIGNATURE)',line)
  line=re.sub(r'^(call|return_call) \d+(\)*)$',r'\1 CALLEE\2',line)
  line=re.sub(r'\(type (\d+)\)',lambda m:'(type '+'->'.join(model['types'][int(m[1])])+')',line)
  if erase_data:
   m=re.fullmatch(r'i32.const (-?\d+)(\)*)',line)
   if m and lo<=(int(m[1])&0xffffffff)<hi:line='i32.const DATA_ADDRESS'+m[2]
   m=re.fullmatch(r'i64.const (-?\d+)(\)*)',line)
   if m:
    value=int(m[1])&((1<<64)-1);a=value&0xffffffff;b=value>>32
    if lo<=a<hi or lo<=b<hi:line='i64.const '+('DATA'if lo<=b<hi else str(b))+':'+('DATA'if lo<=a<hi else str(a))+m[2]
   line=re.sub(r'offset=(\d+)',lambda m:'offset=DATA_ADDRESS'if lo<=int(m[1])<hi else m[0],line)
  rows.append(line)
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--new-profile',required=True,type=Path);p.add_argument('--deadline-seconds',type=int,default=240);args=p.parse_args()
 began=time.monotonic();assert 30<=args.deadline_seconds<=600;deadline=began+args.deadline_seconds
 assert sha(BASELINE)==BASELINE_SHA;baseline=json.loads(BASELINE.read_text())
 before={name:sha(ROOT/name)for name in('scripts/map_engine1391_incremental.py','scripts/wasm139_profile.py','scripts/wasm1391_profile.py','scripts/wasm134_profile.py','scripts/wasm_index.py')}
 old=catalog(OLD,OLD_SHA,identity139old);new=catalog(SOURCE,SOURCE_SHA,identity139new)
 profile=args.new_profile.resolve();manifest=json.loads((profile/'manifest.json').read_text());assert manifest['original_sha256']==SOURCE_SHA and manifest['identities_preserved']and manifest['full_module_validated']
 db=sqlite3.connect(f'file:{profile}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
 locations={row['idx']:dict(row)for row in db.execute('select * from functions')};assert len(locations)==len(new['ranges'])
 exact=defaultdict(list)
 for idx in new['ranges']:exact[(new['sig'][idx],new['hashes'][idx])].append(idx)
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('engine139-to1391-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 save(out/'run-state.json',dict(status='running',pid=None,deadline_seconds=args.deadline_seconds,target_executed=False))
 for name,value in before.items():
  dest=out/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes());assert sha(dest)==value
 watched_bytes=0;cache={};entries=[];bindings={};texts={}
 with Path(manifest['wat_path']).open('rb')as stream:
  def read(index):
   nonlocal watched_bytes
   if time.monotonic()>deadline:raise TimeoutError('Finite entry-mapping deadline')
   if index in cache:return cache[index]
   row=locations[index];n=row['wat_end']-row['wat_start'];assert n<=6500000 and watched_bytes+n<=300000000,(index,n,watched_bytes)
   assert new['ranges'][index]==(row['body_start'],row['body_end'],row['body_bytes'])
   stream.seek(row['wat_start']);text=stream.read(n).decode();assert text.startswith(f'  (func (;{index};)');watched_bytes+=n
   cache[index]=text;return text
  #Large App mapping is resolved last from mapped game-call anchors.
  todo=[entry for entry in baseline['entries']if entry['role']!='application_tick']
  todo+=[entry for entry in baseline['entries']if entry['role']=='application_tick']
  for item in todo:
   role=item['role'];prior=item['binding'];idx=prior['index'];sig=(prior['params_hex'],prior['results_hex']);assert old['sig'][idx]==sig and old['hashes'][idx]==prior['body_sha256']
   oldpath=BASELINE.parent/f'139-{idx}.wat';assert sha(oldpath)==prior['wat_sha256'];source=oldpath.read_text()
   raw_exact=exact[(sig,prior['body_sha256'])];same_calls=[];same_static=[];scores=[]
   old_static=normalized(source,old,True);old_call=normalized(source,old,False);og=Counter(zip(old_static,old_static[1:],old_static[2:]))
   size=prior['body_bytes'];pool=[i for i,(_,_,length)in new['ranges'].items()if new['sig'][i]==sig and max(1,size*65//100)<=length<=size*150//100]
   all_candidates=len(pool);truncated=all_candidates>4096
   if truncated:pool=sorted(pool,key=lambda i:(abs(new['ranges'][i][2]-size),i))[:4096]
   graph=[]
   if role=='application_tick':
    core=[bindings[name]for name in('player','ai','spawn','collect')if name in bindings]
    if len(core)==4:
     callers=Counter()
     for target in core:
      for row in db.execute('select caller,count(*) n from calls where callee=? group by caller',(target,)):callers[row['caller']]+=1
     graph=[i for i,n in callers.items()if n==4 and new['sig'].get(i)==sig]
    if len(graph)==1:pool=graph;truncated=False
   if raw_exact:
    selected=raw_exact;method='exact_body_and_signature'
   else:
    for i in pool:
     text=read(i);ns=normalized(text,new,True)
     if ns==old_static:same_static.append(i)
     if normalized(text,new,False)==old_call:same_calls.append(i)
     ng=Counter(zip(ns,ns[1:],ns[2:]));den=sum(og.values())+sum(ng.values());score=2*sum((og&ng).values())/den if den else 1
     scores.append((score,i))
    selected=same_calls or same_static
    method='full_call_normalized_structure'if same_calls else'full_call_and_data_normalized_structure'if same_static else'four_mapped_core_caller_anchors'if len(graph)==1 else'unresolved_similarity_only'
    if not selected and len(graph)==1:selected=graph
   scores.sort(reverse=True);unique=len(selected)==1 and not truncated
   chosen=selected[0]if unique else None
   if chosen is not None:bindings[role]=chosen
   record=dict(role=role,old=prior,eligible_candidates=all_candidates,scanned_candidates=len(pool)if not raw_exact else 0,candidate_pool_truncated=truncated,
    exact_candidates=raw_exact,call_normalized_candidates=same_calls,call_data_normalized_candidates=same_static,
    mapped_core_caller_candidates=graph,selected_candidates=selected,match_method=method,unique_within_declared_search=unique,
    new_index=chosen,identity_is_static_only=True,semantic_acceptance_transferred=False,
    diagnostic_top3=[dict(index=i,trigram_similarity=score)for score,i in scores[:3]])
   if chosen is not None:
    text=read(chosen);n=new['ranges'][chosen];new_lines=text.splitlines();old_lines=source.splitlines();texts[role]=(source,text)
    (out/f'1390-{role}-{idx}.wat').write_text(source);np=out/f'1391-{role}-{chosen}.wat';np.write_text(text)
    record['new']=dict(index=chosen,params_hex=new['sig'][chosen][0],results_hex=new['sig'][chosen][1],body_sha256=new['hashes'][chosen],wat_sha256=sha(np),**locations[chosen])
    record['body_bytes_delta']=n[2]-size
    ns=normalized(text,new,True);record['opcode_sequence_equal']=[x.split()[0]for x in old_static]==[x.split()[0]for x in ns]
    if len(old_static)==len(ns):record['normalized_instruction_changes']=[dict(line=i+1,old=a,new=b)for i,(a,b)in enumerate(zip(old_static,ns))if a!=b]
    if same_static or same_calls:
     pairs=[]
     for line,(a,b)in enumerate(zip(old_lines,new_lines),1):
      a,b=a.strip(),b.strip()
      if a!=b and(a.startswith(('i32.const','i64.const'))or b.startswith(('i32.const','i64.const'))):pairs.append(dict(relative_line=line,old=a,new=b))
     record['raw_integer_immediate_changes']=pairs
    patch='\n'.join(difflib.unified_diff(old_lines,new_lines,fromfile=f'139.0/{idx}',tofile=f'139.1/{chosen}',n=2))+'\n';dp=out/(role+'.diff');dp.write_text(patch);record['raw_diff_sha256']=sha(dp)
   entries.append(record)
   save(out/'entries-in-progress.json',entries)
   print(json.dumps(dict(role=role,old_index=idx,new_index=chosen,method=method,scanned=record['scanned_candidates'],seek_bytes=watched_bytes)),flush=True)
 #Every import name/signature delta is retained; no bridge execution occurs.
 def imports(model):
  return {row['module']+'::'+row['name']:model['types'][row['type_index']]for row in model['identity']['imports']}
 oi,ni=imports(old),imports(new)
 import_delta=dict(old_count=len(oi),new_count=len(ni),added={k:ni[k]for k in ni.keys()-oi.keys()},removed={k:oi[k]for k in oi.keys()-ni.keys()},signature_changed={k:dict(old=oi[k],new=ni[k])for k in oi.keys()&ni.keys()if oi[k]!=ni[k]})
 #The original14 sequence is checked inside the mapped App, not inferred from
 #relative function numbers. A nonconsecutive change stays an explicit gap.
 sequence=[bindings.get(item['role'])for item in baseline['entries'][:14]];windows=[]
 if 'application_tick'in bindings and all(i is not None for i in sequence):
  app=texts['application_tick'][1].splitlines();calls=[(line+1,int(x.strip().split()[1]))for line,x in enumerate(app)if x.strip().startswith('call ')]
  for i in range(len(calls)-13):
   if[callee for _,callee in calls[i:i+14]]==sequence:
    a,b=calls[i][0],calls[i+13][0]
    window_lines=[dict(line=j+1,instruction=app[j].strip())for j in range(max(0,a-4),min(len(app),b+3))]
    windows.append(dict(first_line=a,last_line=b,calls=sequence,lines=window_lines))
 after={name:sha(ROOT/name)for name in before};assert before==after and sha(SOURCE)==SOURCE_SHA and sha(OLD)==OLD_SHA
 result=dict(kind='incremental139_to1391_static_entry_map_not_runtime_acceptance',baseline_sha256=BASELINE_SHA,old_source_sha256=OLD_SHA,new_source_sha256=SOURCE_SHA,
  old_build='f79c5e2b4',new_build='b89633f9b',old_version='0.139.0',new_version='0.139.1',new_profile=str(profile.relative_to(ROOT)),new_profile_manifest_sha256=sha(profile/'manifest.json'),
  entries=entries,bindings=bindings,new_app14_windows=windows,imports=import_delta,wat_seek_bytes=watched_bytes,full_old_WAT_scanned=False,
  source_sha256_before=before,source_sha256_after=after,original_executions=0,model_executions=0,native_executions=0,old_acceptance_transferred=False,seconds=time.monotonic()-began,
  limitations=['Fullnormalizedstructure binding is static identity evidence only;differentreferenceddata/callees requirefreshrecovery','Data-address-envelope normalization may hide nonaddress integers;rawimmediates/diffs preserved','A truncated candidate pool cannot give auniquebinding','Similarity-only results remainunresolved','This doesnot prove gameplay rulesunchanged,complete enginebehavior,or1391 originaldifferential acceptance'])
 save(out/'mapping.json',result);save(out/'run-state.json',dict(status='complete',seconds=result['seconds'],target_executed=False));print(json.dumps(dict(directory=str(out),mapping_sha256=sha(out/'mapping.json'),bound=len(bindings),entries=len(entries),new_app14_windows=len(windows),wat_seek_bytes=watched_bytes,original_executions=0)),flush=True)
if __name__=='__main__':main()
