#!/usr/bin/env python3
"""Read-only full921 demo AI review. Never executes target/model/checker."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import ast,hashlib,json,math,os,re,signal,sqlite3,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,missing
from review_combat137 import exports
from review_resource_consumer137 import source_edges,identities
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/full0135-oracle-20261101T205618.153296Z'
WORLD=ROOT/'evidence/full0135-oracle-20261101T205735.949915Z'
FLAT=ROOT/'evidence/ai-world0135-flat-regression-20261101T205733.699998Z'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
OFFSETS=dict(armor_1392_bits=1568,armor_cap_1572_bits=1572,nearby_reduction_1444_bits=1624,hp_1528_bits=1440,shield_1532_bits=1444,barrier_1536_bits=1448,shield_source_1344=1344,shield_source_remaining_1348_bits=1348,reserve_768_bits=768,absorbed_740_bits=740,maximum_shield_744_bits=744,last_hit_1648_bits=1652)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def F(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def B(v):return struct.unpack('<I',struct.pack('<f',v))[0]
def add(a,b):return B(F(a)+F(b))
def sub(a,b):return B(F(a)-F(b))
def mul(a,b):return B(F(a)*F(b))
def div(a,b):return B(F(a)/F(b))
def u(b,o):return struct.unpack_from('<I',b,o)[0]
def guid(b):return struct.unpack_from('<Q',b,112)[0]
def put(b,o,v):struct.pack_into('<I',b,o,v)
def equal(w,a,count):
 if w is None:
  assert a is None;count['strict_structural_nulls']+=1;return
 assert type(w)is type(a),(type(w),type(a))
 if isinstance(w,dict):
  assert set(w)==set(a)
  for k in w:equal(w[k],a[k],count)
 elif isinstance(w,list):
  assert len(w)==len(a)
  for x,y in zip(w,a):equal(x,y,count)
 else:assert w==a,(w,a);count['strict_known_values']+=1

def packet_fields(encoded):
 b=bytes.fromhex(encoded);assert b[:6]==b'\1\0\0\0\0\0';p=7;mask=b[6];owner=0
 for i in range(8):
  if mask>>i&1:owner|=b[p]<<(8*i);p+=1
 blocks=b[p];p+=1;bits=struct.unpack_from('<'+'I'*blocks,b,p);p+=4*blocks;fields={}
 for i,word in enumerate(bits):
  for k in range(32):
   if word>>k&1:fields[i*32+k]=u(b,p);p+=4
 assert p==len(b);return owner,fields

def model_step(records,step,counts):
 now,dt=step['now_bits'],step['dt_bits'];player=step['player_xyz_bits'];out=[bytearray(x)for x in records];attacks=[];expirations=[];moves=[]
 for b in out:
  assert u(b,0)==u(b,8)==u(b,16)==u(b,240)==0 and all(u(b,o)==0xffffffff for o in(40,64,244))
  assert u(b,360)in(0,1160)and all(u(b,168+4*i)in(0,1160)for i in range(16))
  if u(b,360):
   expiry=u(b,132)if F(u(b,132))>F(now)else u(b,140)
   if F(expiry)<=F(now):put(b,360,0);expirations.append((guid(b),1160))
  if F(u(b,400))>F(now):counts['U400_frozen_rows']+=1;continue
  duration=u(b,344)
  if F(duration)>0:
   ratio=div(sub(now,u(b,340)),duration);ratio=0 if F(ratio)<0 else B(1)if F(ratio)>1 else ratio
   pos=[add(u(b,a),mul(sub(u(b,z),u(b,a)),ratio))for a,z in((316,328),(320,332),(324,336))]
  else:pos=[u(b,o)for o in(328,332,336)]
  timer=sub(u(b,352),dt);put(b,352,timer)
  dx,dy=sub(pos[0],player[0]),sub(pos[1],player[1]);distance=B(math.sqrt(F(add(mul(dx,dx),mul(dy,dy)))))
  if F(distance)<=F(u(b,308)):
   if F(duration)>0 and F(now)<F(add(u(b,340),duration)):
    for i,v in enumerate(pos):put(b,316+4*i,v);put(b,328+4*i,v)
    put(b,340,now);put(b,344,0);moves.append((guid(b),pos,pos,0))
   if F(timer)<=0 and F(u(b,404))<=F(now):
    put(b,352,u(b,304));weak=u(b,128)if F(u(b,132))>F(now)else u(b,136)if F(u(b,140))>F(now)else 0
    kind='primary'if F(u(b,132))>F(now)else'backup'if F(u(b,140))>F(now)else'none';counts['weakness_'+kind]+=1
    attacks.append((guid(b),mul(u(b,296),sub(B(1),weak))))
   continue
  if F(u(b,348))>F(now):continue
  assert u(b,120)==u(b,124)==u(b,404)==0
  angle=add(u(b,396),0x3e19999a);put(b,396,angle);radius=mul(u(b,308),0x3f4ccccd);radius=radius if F(radius)>1.5 else B(1.5)
  dest=[add(player[0],mul(radius,B(math.cos(F(angle))))),add(player[1],mul(radius,B(math.sin(F(angle))))),player[2]]
  def dist(a,z):
   x,y=sub(a[0],z[0]),sub(a[1],z[1]);return B(math.sqrt(F(add(mul(x,x),mul(y,y)))))
  length=dist(pos,dest)
  if F(length)>14:
   factor=div(B(14),length);dest=[add(pos[0],mul(sub(dest[0],pos[0]),factor)),add(pos[1],mul(sub(dest[1],pos[1]),factor)),pos[2]]
  speed=u(b,300);duration=div(dist(pos,dest),speed if F(speed)>.5 else B(.5))
  for i,v in enumerate(pos):put(b,316+4*i,v)
  for i,v in enumerate(dest):put(b,328+4*i,v)
  put(b,340,now);put(b,344,duration);deadline=duration if F(duration)>.25 else B(.25);deadline=B(.7)if F(deadline)>.7 else deadline;put(b,348,add(now,deadline));moves.append((guid(b),pos,dest,duration))
 # This only verifies AI's owner/slot transition. The reused cast Aura encoder
 # is an authored dependency, not independently reimplemented in this review.
 aura_owners=[]
 for owner,spell in expirations:
  b=next(x for x in out if guid(x)==owner);slots=[u(b,168+4*i)for i in range(16)]
  if spell in slots:index=slots.index(spell);put(b,168+4*index,0);aura_owners.append((owner,index))
 return out,attacks,expirations,moves,aura_owners

def audit_cases(rows,expected,actual,labels):
 counts=Counter();changed=set()
 for c,w,a,label in zip(rows,expected,actual,labels):
  assert c['id']==w['id']==a['id']==label['id'];assert c['world']==dict(kind='controlled_query_world',nav=None,primary=None,fallback_height_bits=0,flat_height_bits=0)
  assert len(c['steps'])==len(w['stages'])==len(a['stages'])==len(label['stages'])
  records=[bytearray.fromhex(x)for x in c['records']];assert all(len(x)==424 for x in records)and len({guid(x)for x in records})==len(records)
  incoming=dict(c['incoming']);hp=incoming['hp_1528_bits'];total=incoming['incoming_total_992'];last=incoming['last_hit_1648_bits'];seq=c['sequence'];packetcount=0;previous=[]
  assert incoming['mode_2574']==incoming['protection_2568']==incoming['minimum_one_2578']==0 and not incoming['buffs']and not incoming['modifiers']
  assert all(incoming[x]==0 for x in OFFSETS if x not in('hp_1528_bits','armor_cap_1572_bits'))
  for index,(step,want,row,detail)in enumerate(zip(c['steps'],w['stages'],a['stages'],label['stages'])):
   counts['stages']+=1;equal(want,row['known'],counts);before=[bytes(x)for x in records];records,attacks,expired,moves,aura=model_step(records,step,counts)
   assert detail['attacks']==[[str(g),x]for g,x in attacks]and detail['expirations']==[[str(g),s]for g,s in expired]and detail['movements']==len(moves)
   assert [bytes(x).hex()for x in records]==row['known']['records']
   for x,y in zip(before,records):changed.update(i for i,(v,z)in enumerate(zip(x,y))if v!=z)
   if incoming['phase_2579']==1:
    for _,amount in attacks:hp=sub(hp,amount);total+=F(amount);last=step['now_bits'];counts['incoming_scalar_applied']+=1
   else:counts['incoming_phase_guard']+=len(attacks)
   k=row['known'];assert(k['hp_1528_bits'],k['last_hit_1648_bits'],k['incoming_total_992_bits'])==(hp,last,struct.pack('>d',total).hex())
   assert all(k[key]==incoming[key]for key in OFFSETS if key not in('hp_1528_bits','last_hit_1648_bits'))
   counts['contact_attacks']+=len(attacks);counts['expirations']+=len(expired);counts['movements']+=len(moves);counts['new169']+=len(aura);counts['strict_record_bytes']+=424*len(records)
   assert len(detail['known_demo_after'])==len(records)
   for b,d in zip(records,detail['known_demo_after']):
    assert d==dict(guid=guid(b),marker=u(b,0),words128_140=[u(b,o)for o in(128,132,136,140)],spell360=u(b,360),duration364_bits=u(b,364),aura_slots168=[u(b,168+4*i)for i in range(16)],ability_count240=u(b,240))
    assert bytes(b[128:144])==next(x[128:144]for x in before if guid(x)==guid(b))and u(b,364)==u(next(x for x in before if guid(x)==guid(b)),364)
   game=bytes.fromhex(row['raw_game8192_hex']);assert len(game)==8192
   assert all(u(game,o)==k[key]for key,o in OFFSETS.items())and struct.unpack_from('<Q',game,992)[0]==int(k['incoming_total_992_bits'],16)
   assert list(struct.unpack_from('<4I',game,1720))==k['rng_words']==[1,2,3,4]and u(game,1784)==u(game,1792)==len(records)and u(game,1788)==row['unit_pointer']
   q=row['raw_packets'];assert(u(game,1880),u(game,1884),u(game,1888))==(q['capacity'],q['pointer'],q['count'])and q['count']<=q['capacity']
   meta=bytes.fromhex(q['metadata_hex']);assert len(meta)==16*q['count']==16*len(q['active'])
   for j,p in enumerate(q['active']):assert struct.unpack_from('<3I',meta,j*16)==(p['capacity'],p['pointer'],p['length'])and struct.unpack_from('<H',meta,j*16+12)[0]==p['opcode']and p['length']==len(bytes.fromhex(p['payload_hex']))<=p['capacity']and p['pointer']+p['length']<=33554432
   stable=[(p['opcode'],p['payload_hex'])for p in q['active']];assert stable[:len(previous)]==previous;added=q['active'][len(previous):];previous=stable
   assert row['new_packet_opcodes']==[p['opcode']for p in added];actual_aura=[p for p in added if p['opcode']==169];first=next((j for j,p in enumerate(added)if p['opcode']==169),len(added));assert all(p['opcode']==169 for p in added[first:])
   assert len(actual_aura)==len(aura)and len(added)==len(moves)+len(attacks)+len(aura)
   for (owner,slot),packet in zip(aura,actual_aura):
    decoded,fields=packet_fields(packet['payload_hex']);assert owner==decoded and fields=={79+slot:0,99+(slot>>3):0,121+(slot>>2):0}
   seq+=len(moves);packetcount+=len(added);assert(k['sequence'],k['packet_count'])==(seq,packetcount)and u(game,2412)==seq
 return dict(counts),sorted(changed)

def worker(out):
 began=time.monotonic();report=load(RUN/'comparison.json');assert sha(RUN/'comparison.json')=='01c93350943b0f20956298fdf1908ae7ee2b66c40d902b7eac817cdf2657b07e'
 assert report['source_sha256_before']==report['source_sha256_after']and report['source_files']==48 and report['comparison_complete']and report['differences']==0
 sources=report['source_sha256_before'];frozen=RUN/'source-snapshot'
 for n,h in sources.items():assert sha(ROOT/n)==h==sha(frozen/n)
 assert source_edges(frozen,list(sources))==report['local_source_import_edges']and len(report['local_source_import_edges'])==145
 production=[n for n in sources if n.startswith('reconstruction/')]
 for n in production:
  for node in ast.walk(ast.parse((frozen/n).read_text())):
   if isinstance(node,ast.Call):
    fun=node.func;name=fun.id if isinstance(fun,ast.Name)else fun.attr if isinstance(fun,ast.Attribute)else'';assert name not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'),(n,name)
 for n,h in(report['frozen_artifacts']|report['artifacts']).items():assert sha(RUN/n)==h
 assert sha(Path(report['fixture_input']['path']))==report['fixture_input']['sha256']
 original=ORIGINAL.read_bytes();assert hashlib.sha256(original).hexdigest()==report['original_sha256'];manifest=load(RUN/'manifest.json');changed=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
 before,after=sections(original),sections(changed);assert[x[0]for x in before]==[x[0]for x in after]and 8 not in[x[0]for x in before]
 assert all(original[a:b]==changed[c:d]for(k,a,_,b),(_,c,_,d)in zip(before,after)if k!=7)
 assert exports(changed)==exports(original)+[['research135_update_units',0,921],['research135_distance_stack0',3,0]]
 funcs=identities(original,[921,4543,15511,13814,1073,27375]);assert funcs[921]['signature']==['7f7d',''];assert funcs[921]['body_sha256']=='5c2c1cdc75e805e7d4e7ed51f5dddde34eda6331617c9ea8ee2a26da90329a37'
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
  for item in manifest['demo_ai_static_functions']:
   idx=item['idx'];a,b=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(a);raw=stream.read(b-a);assert raw==(RUN/f'demo-ai-{idx}.wat').read_bytes()and hashlib.sha256(raw).hexdigest()==item['wat_sha256']and funcs[idx]['body_sha256']==item['body_sha256']
 lines=(RUN/'demo-ai-921.wat').read_text().splitlines();proofs={}
 for a,b,label in((1695,1718,'strict primary or backup expiry'),(1808,1842,'clear360 andGUID-bound deferred queue'),(2518,2537,'later U400 freeze guard'),(2665,2705,'contact primary orbackup strength'),(7477,7497,'ordinary contact queued1073'),(8917,8934,'late4543 remove')):proofs[label]=dict(start=a,end=b,lines=lines[a-1:b])
 save(out/'static-proofs.json',proofs)
 rows=load(RUN/'input.json');expected=load(RUN/'expected.json');actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];labels=load(RUN/'labels.json');assert len(rows)==len(expected)==len(actual)==len(labels)==58
 counts,offsets=audit_cases(rows,expected,actual,labels);assert counts.get('strict_structural_nulls',0)==0;assert counts['stages']==66 and counts['contact_attacks']==61 and counts['expirations']==28 and counts['new169']==27 and counts['movements']==1
 runtime=load(RUN/'demo-ai135-runtime.json');assert runtime==report['runtime']and runtime['fresh_instances']==58 and runtime['entry_calls']==66 and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['max_memory_bytes']<=33554432 and runtime['stack_all_restored']and runtime['error']is None
 assert len(runtime['stack_checks'])==298 and all(x['entered']and x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])
 terminal=load(RUN/'process-terminal.json');assert terminal==report['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
 prepared=load(RUN/'prepared.json');assert prepared['expected_before_original']and prepared['deadline_seconds']==60 and '--max-old-space-size=512'in prepared['command']and '--wasm-max-mem-pages=512'in prepared['command']
 assert all((RUN/n).stat().st_size<=8388608 for n in('input.json','expected.json'))and(RUN/'stdout.jsonl').stat().st_size<=33554432 and all(len(x)<=2097152 for x in(RUN/'stdout.jsonl').read_bytes().splitlines())
 assert len(load(RUN/'refusals.json'))==6 and load(RUN/'differences.json')==[]
 # Review the default fresh regression without executing its model, then keep
 # the416/1013 historical expected re-comparison in a separate evidence layer.
 wr=load(WORLD/'ai-world135-comparison.json');assert sha(WORLD/'ai-world135-comparison.json')=='c19b3d1e512923bea71c1d9cc8d2f8ba864b6a4e78cd3ad0d6d206303f6de8e7'and(wr['cases'],wr['stages'],wr['mismatch_cases'])==(20,45,0)
 for n,h in wr['artifacts'].items():assert sha(WORLD/n)==h
 for n,h in wr['source_sha256_before'].items():assert sha(WORLD/'source-snapshot'/n)==h==wr['source_sha256_after'][n]==sha(ROOT/n)
 wi=load(WORLD/'ai-world135-fixtures.json');wa=[json.loads(x)for x in(WORLD/'ai-world135-results.jsonl').read_text().splitlines()];wc=Counter()
 for c,a in zip(wi,wa):assert c['id']==a['id'];equal(c['expected'],a['stages'],wc)
 assert len(wi)==len(wa)==20 and sum(len(x['stages'])for x in wa)==45 and wc['strict_structural_nulls']==1
 assert wi[19]['expected'][0]['distance_map']is None and wa[19]['stages'][0]['distance_map']is None
 for n,h in wr['independent_world_input']['hashes'].items():assert sha(ROOT/wr['independent_world_input']['directory']/n)==h
 assert wr['runtime']['actual_host_calls']==0 and wr['runtime']['stack_all_restored']and wr['process']['exit_code']==0 and missing(wr['process']['pid'])and missing(wr['process']['pgid'],True)
 flat=load(FLAT/'comparison.json');assert sha(FLAT/'comparison.json')=='6af72fb6db488221935e431455f2889221e667a22347ee72329d7f963ab56529'and(flat['cases'],flat['stages'],flat['differences'],flat['new_original_cases'],flat['original_calls'])==(416,1013,0,0,0)
 failed=ROOT/'evidence/full0135-oracle-20261101T205455.500232Z';fr=load(failed/'comparison.json');assert sha(failed/'comparison.json')=='5644cd52a281a443af772970165a67dae6f59e361d64ad7ce6c06eabd2a6cc4a'and not fr['comparison_complete']and fr['runtime']is None and fr['process']['exit_code']!=0
 for n in('input.json','expected.json','labels.json',manifest['module_file']):assert sha(failed/n)==sha(RUN/n)
 assert fr['source_sha256_before']==fr['source_sha256_after']
 failure_drift=[n for n,h in sources.items()if fr['source_sha256_before'][n]!=h];assert failure_drift==['scripts/check_demo_ai135.py','scripts/run_demo_ai135_oracle.mjs']
 assert len((failed/'stdout.jsonl').read_text().splitlines())==34
 # AI-only admission/order audit. The authored Aura encoder is referenced as a
 # dependency and exact bytes re-compared; it is not called or self-rederived.
 demo=(frozen/'reconstruction/core_spec/demo_ai135.py').read_text();world=(frozen/'reconstruction/core_spec/ai_world135.py').read_text();ai=(frozen/'reconstruction/core_spec/ai135.py').read_text()
 assert 'if actual!=expected:'in demo and 'Demo producer declaration differs'in demo and 'declaration.marker!=0 or declaration.ability_count240'in demo
 assert 'elif _get(raw,360):'in ai and 'known_demo_statuses:tuple=()'in ai
 # Compare body position rather than imported identifier occurrence.
 body=world[world.index('def update_world_ordinary_units135'):];assert body.index('demo_bindings=demo_bindings135')<body.index('_validate(raw, state.now_bits')<body.index('removal=begin_demo_expiry135')<body.index('if _float(raw, 400)')<body.index('for guid, amount in attacks:')<body.index('declarations,packets,fields=finish_demo_expiry135')
 assert all(sha(ROOT/n)==h for n,h in sources.items())
 reviewer_files=['scripts/review_demo_ai135.py','scripts/review_opening_combat135.py','scripts/review_combat137.py','scripts/review_resource_consumer137.py','scripts/review_battle_shout135.py']
 reviewer_hashes={n:sha(ROOT/n)for n in reviewer_files}
 for n,h in reviewer_hashes.items():
  dest=out/'reviewer-source-snapshot'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes());assert sha(dest)==h
 save(out/'review.json',dict(reviewer_sources=reviewer_hashes,status='passed_scoped_read_only_review',version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),cases=58,stages=66,new_original_cases=0,original_model_checker_executed_by_reviewer=False,source_files=48,production_files=len(production),source_edges=145,current_and_frozen_sources_match=True,source_hashes=sources,only_export_section_changed=True,full921_and_callees_preserved=True,function_identities=funcs,independent_AI_and_scalar_audit=counts,strict_record_bytes=counts['strict_record_bytes'],physical_unknown_bytes=0,actual_changed_unit_byte_offsets=offsets,full_raw_game_and_queue_metadata_rebound=True,exact169_payloads_equal_frozen_expected=True,Aura_encoder_authorship_boundary='Reviewer authored frozen demo_shout135._aura. This review independently verifies AI owner/expiry/contact/order and payload identity, not a second independent reconstruction of that encoder. Separate cast review referenced by primary.',static_proofs_sha256=sha(out/'static-proofs.json'),runtime={k:v for k,v in runtime.items()if k!='stack_checks'},stack_checks=298,original_terminal=terminal,refusal_artifacts_observed=6,refusals_not_rerun=True,default_world_regression=dict(receipt_sha256=sha(WORLD/'ai-world135-comparison.json'),cases=20,stages=45,expected_all_equal=True,strict_values=wc['strict_known_values'],independently_parsed_asset_world_hashes_verified=True,separate_batch_not_added=True),flat_regression=dict(receipt_sha256=sha(FLAT/'comparison.json'),cases=416,stages=1013,new_original_calls=0,separate_historical_layer=True),failed_heap_batch=dict(receipt_sha256=sha(failed/'comparison.json'),retained_not_positive=True,actual_host_calls='unknown; no runtime',input_expected_labels_module_identical=True,changed_execution_sources=failure_drift,stdout_partial_case_rows=34),limitations=report['pending'],reviewer_source_sha256=sha(Path(__file__)),seconds=time.monotonic()-began))

def main():
 if len(sys.argv)==3 and sys.argv[1]=='--worker':worker(Path(sys.argv[2]));return
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('demo-ai135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();command=[sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(out)];began=time.monotonic();error=None
 with(out/'stdout.log').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
  try:child.wait(timeout=60)
  except BaseException as e:error=repr(e)
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True),seconds=time.monotonic()-began,deadline_seconds=60,error=error);save(out/'process-terminal.json',terminal)
 if child.returncode or error:print(json.dumps(dict(directory=str(out),process=terminal,error_log=(out/'stderr.log').read_text()[-3000:])));raise SystemExit(1)
 r=load(out/'review.json');r['review_owned_terminal']=terminal;save(out/'review.json',r);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=r['status'],counts=r['independent_AI_and_scalar_audit'],process=terminal)))
if __name__=='__main__':main()
