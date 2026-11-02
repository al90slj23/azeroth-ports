#!/usr/bin/env python3
"""Refine source-bound139 role identities using literal callers and callsite anchors.
No target/model/native code execution; trigram scores are candidate diagnostics only.
"""
from collections import defaultdict,Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,difflib,hashlib,json,re,sqlite3,time
import map_engine139_incremental as base
ROOT=base.ROOT
INITIAL=ROOT/'evidence/engine138-to139-static-20261102T013242.588510Z/mapping.json'
INITIAL_SHA='bf2c484911b3edb9c534ee621fed9d245f9e154c430fc412eef17af3973f5d37'
OLD_PROFILE=ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z'
NEW_PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'

def main():
 began=time.monotonic();deadline=began+150
 assert base.sha(INITIAL)==INITIAL_SHA
 inp=json.loads(INITIAL.read_text());baseline=json.loads(base.BASELINE.read_text());old=base.catalog(base.OLD,base.OLD_SHA,base.identity138);new=base.catalog(base.SOURCE,base.SOURCE_SHA,base.identity139)
 before={p:base.sha(ROOT/p)for p in ['scripts/refine_engine139_entry_map.py','scripts/map_engine139_incremental.py','scripts/wasm138_profile.py','scripts/wasm139_profile.py','scripts/wasm134_profile.py','scripts/wasm_index.py']}
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('engine139-refined-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 for p,h in before.items():
  d=out/'source-snapshot'/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes((ROOT/p).read_bytes());assert base.sha(d)==h
 dbs=[];streams=[];cache={};wat_bytes=[0,0]
 for profile in [OLD_PROFILE,NEW_PROFILE]:
  db=sqlite3.connect(f'file:{profile}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');dbs.append(db)
  streams.append(Path(json.loads((profile/'manifest.json').read_text())['wat_path']).open('rb'))
 def read(version,idx):
  key=(version,idx)
  if key in cache:return cache[key]
  assert time.monotonic()<deadline
  row=dict(dbs[version].execute('select * from functions where idx=?',(idx,)).fetchone());n=row['wat_end']-row['wat_start'];assert n<=6500000 and wat_bytes[version]+n<45000000,(version,idx,n,wat_bytes)
  streams[version].seek(row['wat_start']);t=streams[version].read(n).decode();wat_bytes[version]+=n;cache[key]=t;return t
 roles={e['role']:e for e in inp['entries']};bindings=dict(inp['bindings']);proofs={r:[dict(kind='initial_exact_or_full_normalized',method=roles[r]['match_method'],index=i)]for r,i in bindings.items()}
 #A complete14-call window is constrained by eight already independently located
 #literal stages. No relative function index is used in this selection.
 anchors=['hits','area','effects','deadline','secondary','collect','claims','terminal'];callers=None
 for r in anchors:
  s={q[0]for q in dbs[1].execute('select distinct caller from calls where callee=?',(bindings[r],))};callers=s if callers is None else callers&s
 appold=roles['application_tick']['old']['index'];candidates=[i for i in callers if new['sig'][i]==old['sig'][appold]];assert len(candidates)==1,candidates;app=candidates[0]
 stage_roles=[e['role']for e in baseline['entries'][:14]];pattern=[bindings.get(r)for r in stage_roles];calls=list(dbs[1].execute('select callee,wat_line,wat_offset from calls where caller=? order by wat_offset',(app,)));windows=[]
 for i in range(len(calls)-13):
  window=calls[i:i+14]
  if all(p is None or window[j][0]==p for j,p in enumerate(pattern)):windows.append(window)
 assert len(windows)==1,len(windows);window=windows[0];bindings['application_tick']=app;proofs['application_tick']=[dict(kind='unique_eight_bound_stage_caller_and_complete14window',anchor_roles=anchors,eligible_callers=candidates,first_wat_line=window[0]['wat_line'],last_wat_line=window[-1]['wat_line'])]
 for r,row in zip(stage_roles,window):
  i=row['callee'];o=roles[r]['old']['index'];assert new['sig'][i]==old['sig'][o]
  if r in bindings:assert bindings[r]==i
  bindings[r]=i;proofs.setdefault(r,[]).append(dict(kind='literal_complete14_stage_slot',caller=app,old_slot=stage_roles.index(r),wat_line=row['wat_line'],wat_offset=row['wat_offset']))
 #A full normalized body preserves exact instruction positions; corresponding
 #direct calls therefore supply explicit original-caller/callsite identity edges.
 edges=defaultdict(list)
 for r in inp['bindings']:
  e=roles[r];oi=e['old']['index'];ni=e['new_index'];a=read(0,oi);b=read(1,ni)
  assert base.normalized(a,old,True)==base.normalized(b,new,True)
  ca=list(dbs[0].execute('select callee,wat_line from calls where caller=? order by wat_offset',(oi,)));cb=list(dbs[1].execute('select callee,wat_line from calls where caller=? order by wat_offset',(ni,)));assert len(ca)==len(cb)
  for k,(x,y)in enumerate(zip(ca,cb)):
   edges[x['callee']].append(dict(new_index=y['callee'],caller_role=r,old_caller=oi,new_caller=ni,ordinal=k,old_wat_line=x['wat_line'],new_wat_line=y['wat_line'],kind='full_normalized_parent_call_ordinal'))
 for r,e in roles.items():
  oi=e['old']['index'];good=[x for x in edges.get(oi,[])if x['new_index']in new['sig']and new['sig'][x['new_index']]==old['sig'][oi]];cs={x['new_index']for x in good}
  if len(cs)==1:
   ni=next(iter(cs));assert r not in bindings or bindings[r]==ni
   bindings[r]=ni;proofs.setdefault(r,[]).extend(good)
 #For changed parent bodies, an exact literal-context around a target call plus
 #its ABI and unique candidate slot can locate remaining producers. All context
 #words (including locals, memory offsets, branch depths) are preserved.
 #A shorter context is not silently substituted when this explicit7/11/15-row
 #sequence is absent or ambiguous.
 def contexts(text,model,width):
  rows=base.normalized(text,model,True);result=defaultdict(list)
  for k,line in enumerate(rows):
   if re.fullmatch(r'(?:call|return_call) CALLEE\)*',line):
    if k>=width and k+width<len(rows):result[tuple(rows[k-width:k+width+1])].append(k)
  return rows,result
 context_attempts=[]
 for _ in range(3):
  changed=False
  for pr,pi in list(bindings.items()):
   po=roles[pr]['old']['index'];a=read(0,po);b=read(1,pi);oldcalls={j:int(x.strip().split()[1])for j,x in enumerate(a.splitlines())if x.strip().startswith(('call ','return_call '))};newcalls={j:int(x.strip().split()[1])for j,x in enumerate(b.splitlines())if x.strip().startswith(('call ','return_call '))}
   for width in [7,5,3]:
    ar,ac=contexts(a,old,width);br,bc=contexts(b,new,width)
    for r,e in roles.items():
     if r in bindings:continue
     target=e['old']['index'];xs=[(context,k)for context,ks in ac.items()for k in ks if oldcalls.get(k)==target];hits=[]
     for context,k in xs:
      for nk in bc.get(context,[]):
       ni=newcalls[nk]
       if new['sig'].get(ni)==old['sig'][target]:hits.append(dict(new_index=ni,parent_role=pr,old_caller=po,new_caller=pi,old_relative_line=k+1,new_relative_line=nk+1,width_each_side=width,context=list(context),context_old_occurrences=len(ac[context]),context_new_occurrences=len(bc[context])))
     cs={x['new_index']for x in hits}
     #Every admitted hit has a unique full context in both actual caller bodies.
     unique=[x for x in hits if x['context_old_occurrences']==x['context_new_occurrences']==1]
     uc={x['new_index']for x in unique}
     if len(cs)==len(uc)==1:
      ni=next(iter(cs));bindings[r]=ni;proofs[r]=[dict(kind='unique_exact_bound_parent_call_context',**x)for x in unique];changed=True
  if not changed:break
 #Global ABI+literal graph intersections supply an independent location for
 #functions whose optimizer changed local instruction layout. At least two
 #named owner edges, or one edge plus an exact64-row entry prefix, are required.
 #A signature/size/similarity match alone is never admitted.
 for _ in range(4):
  changed=False
  for r,e in roles.items():
   if r in bindings:continue
   oi=e['old']['index'];constraints=[]
   for br,ni in bindings.items():
    bo=roles[br]['old']['index']
    for side,query,args0 in [('out','select count(*) from calls where caller=? and callee=?',(oi,bo)),('in','select count(*) from calls where caller=? and callee=?',(bo,oi))]:
     count=dbs[0].execute(query,args0).fetchone()[0]
     if count:constraints.append(dict(direction=side,role=br,new_bound_index=ni,call_count=count))
   if not constraints:continue
   pool={i for i,s in new['sig'].items()if s==old['sig'][oi]}
   for c in constraints:
    query='select caller from calls where callee=? group by caller having count(*)=?'if c['direction']=='out'else'select callee from calls where caller=? group by callee having count(*)=?'
    pool&={x[0]for x in dbs[1].execute(query,(c['new_bound_index'],c['call_count']))}
   a=base.normalized(read(0,oi),old,True);prefix=[]
   #The prefix is sought only among a bounded graph-filtered set; retain an
   #unknown if that set unexpectedly grows beyond64 actual functions.
   if len(pool)<=64:
    for ni in sorted(pool):
     if a[:64]==base.normalized(read(1,ni),new,True)[:64]:prefix.append(ni)
   if len(pool)==1 and len({c['role']for c in constraints})>=2:
    ni=next(iter(pool));kind='global_unique_abi_and_multiple_bound_role_edges'
   elif len(prefix)==1:
    ni=prefix[0];kind='unique_exact64_instruction_entry_prefix_and_bound_role_edges'
   else:continue
   bindings[r]=ni;proofs[r]=[dict(kind=kind,constraints=constraints,global_graph_candidates=sorted(pool),exact64_prefix_candidates=prefix,old_prefix=a[:64])];changed=True
  if not changed:break
 final=[]
 for r,e in roles.items():
  ni=bindings.get(r);oi=e['old']['index'];row=dict(role=r,old=e['old'],new_index=ni,binding_proofs=proofs.get(r,[]),semantic_acceptance_transferred=False)
  if ni is not None:
   a=read(0,oi);b=read(1,ni);np=out/f'139-{r}-{ni}.wat';np.write_text(b);op=out/f'138-{r}-{oi}.wat';op.write_text(a);loc=dict(dbs[1].execute('select * from functions where idx=?',(ni,)).fetchone());row['new']=dict(index=ni,params_hex=new['sig'][ni][0],results_hex=new['sig'][ni][1],body_sha256=new['hashes'][ni],wat_sha256=base.sha(np),**loc)
   an=base.normalized(a,old,True);bn=base.normalized(b,new,True);row['full_call_data_normalized_equal']=an==bn;row['body_bytes_delta']=new['ranges'][ni][2]-old['ranges'][oi][2]
   #SequenceMatcher provides a diff only after a graph binding is independently
   #established; no similarity threshold is used to decide the identity.
   dp=out/(r+'.diff');dp.write_text('\n'.join(difflib.unified_diff(a.splitlines(),b.splitlines(),fromfile=f'138/{oi}',tofile=f'139/{ni}',n=2))+'\n');row['raw_diff_sha256']=base.sha(dp)
   row['changed_normalized_opcodes']=dict(old_lines=len(an),new_lines=len(bn),equal=an==bn)
  final.append(row)
  base.save(out/'entries-in-progress.json',final)
 after={p:base.sha(ROOT/p)for p in before};assert before==after
 result=dict(kind='139_source_bound_static_role_graph_no_dynamic_acceptance',initial_mapping_sha256=INITIAL_SHA,old_source_sha256=base.OLD_SHA,new_source_sha256=base.SOURCE_SHA,bindings=bindings,entries=final,
  app14=dict(index=app,old_index=appold,roles=stage_roles,actual_calls=[dict(x)for x in window],unique_eight_stage_callers=candidates),wat_seek_bytes=wat_bytes,source_sha256_before=before,source_sha256_after=after,
  target_executions=0,model_executions=0,native_executions=0,old_acceptance_transferred=False,seconds=time.monotonic()-began,
  limitations=['Bindings establish static source identity, not semantic equivalence or dynamic acceptance','Changed referenced static data and callees remain separate migration work','Unresolved roles remain unknown; neither same index nor similarity alone is an identity proof','Absolute heap layouts and network protocol semantics require fresh independent recovery'])
 base.save(out/'mapping.json',result);print(json.dumps(dict(directory=str(out),sha256=base.sha(out/'mapping.json'),bound=len(bindings),entries=len(final),unresolved=[r for r in roles if r not in bindings],wat_seek_bytes=wat_bytes,seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
