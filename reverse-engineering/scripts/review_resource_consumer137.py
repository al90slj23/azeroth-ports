#!/usr/bin/env python3
"""Read-only137 resource consumer review. No model/original/checker executes."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import ast,hashlib,json,math,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,leb,missing
from review_combat137 import exports
from review_battle_shout135 import F,B,add,sub,mul,literal
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/resource-consumer0137-oracle-20261101T190800.110757Z'
PROFILE=ROOT/'evidence/wasm0137-profile-20261101T162221.947222Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T154517.001467Z/latest-wenilla_bg.wasm'
MASK=0xffffffff

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def u(row,offset):
 values=row[offset:offset+4];assert all(type(v)is int and 0<=v<=255 for v in values);return int.from_bytes(bytes(values),'little')
def put(row,offset,value):row[offset:offset+4]=struct.pack('<I',value)
def source_edges(source,files):
 declared=set(files);edges=set()
 for name in files:
  path=source/name
  if path.suffix=='.mjs':
   for relative in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",path.read_text()):
    child=str((path.parent/relative).resolve().relative_to(source));assert child in declared;edges.add((name,child))
   continue
  if path.suffix!='.py':continue
  parts=Path(name).with_suffix('').parts
  for n in ast.walk(ast.parse(path.read_text())):
   modules=[]
   if isinstance(n,ast.Import):modules=[x.name for x in n.names]
   elif isinstance(n,ast.ImportFrom):
    base='.'.join(list(parts[1:-n.level])+([n.module]if n.module else[]))if n.level else n.module or''
    modules=[base]+[base+'.'+x.name if base else x.name for x in n.names]
   for module in modules:
    if not module:continue
    for folder in('scripts','reconstruction'):
     rel=Path(*module.split('.'));py=source/folder/rel.with_suffix('.py');package=source/folder/rel/'__init__.py';child=py if py.is_file()else package if package.is_file()else None
     if child is None:continue
     key=str(child.relative_to(source));assert key in declared,(name,key);edges.add((name,key))
     for parent in child.parents:
      if parent==source/folder:break
      initializer=parent/'__init__.py'
      if initializer.is_file():key=str(initializer.relative_to(source));assert key in declared;edges.add((name,key))
 return [list(x)for x in sorted(edges)]

def production_closure(source):
 todo=['reconstruction/core_spec/resource_consumer137.py'];seen=set()
 while todo:
  name=todo.pop()
  if name in seen:continue
  seen.add(name);path=source/name;parts=Path(name).with_suffix('').parts
  if len(parts)>2:todo.append('reconstruction/'+parts[1]+'/__init__.py')
  for n in ast.walk(ast.parse(path.read_text())):
   modules=[]
   if isinstance(n,ast.Import):modules=[x.name for x in n.names]
   elif isinstance(n,ast.ImportFrom):
    base='.'.join(list(parts[1:-n.level])+([n.module]if n.module else[]))if n.level else n.module or'';modules=[base]+[base+'.'+x.name if base else x.name for x in n.names]
   for module in modules:
    if not module.startswith(('core_spec','resource_spec')):continue
    rel=Path(*module.split('.'));py=source/'reconstruction'/rel.with_suffix('.py');package=source/'reconstruction'/rel/'__init__.py';child=py if py.is_file()else package if package.is_file()else None
    if child is not None:todo.append(str(child.relative_to(source)))
 return sorted(seen)

def identities(raw,wanted):
 top=sections(raw);_,_,p,end=next(x for x in top if x[0]==1);n,p=leb(raw,p);types=[]
 for _ in range(n):
  assert raw[p]==0x60;a,p=leb(raw,p+1);params=raw[p:p+a].hex();p+=a;b,p=leb(raw,p);ret=raw[p:p+b].hex();p+=b;types.append([params,ret])
 assert p==end;_,_,p,end=next(x for x in top if x[0]==3);n,p=leb(raw,p);decl=[]
 for _ in range(n):v,p=leb(raw,p);decl.append(v)
 assert p==end;_,_,p,end=next(x for x in top if x[0]==10);count,p=leb(raw,p);assert count==n;out={}
 for index in range(878,878+n):
  size,start=leb(raw,p);p=start+size
  if index in wanted:out[index]=dict(index=index,signature=types[decl[index-878]],body_start=start,body_end=p,body_sha256=hashlib.sha256(raw[start:p]).hexdigest())
 assert p==end and set(out)==set(wanted);return out

def compare(want,got,path,counts):
 if want is None:
  assert len(path)>=4 and path[-4]in('live','pickups')and path[-3]=='storage'and type(got)is int and 0<=got<=255;counts['explicit_unknown_physical_bytes']+=1;counts['unknown_original_nonzero_bytes']+=bool(got);return
 assert type(want)is type(got),(path,type(want),type(got))
 if isinstance(want,dict):
  assert set(want)==set(got),(path,set(want),set(got))
  for k,v in want.items():compare(v,got[k],path+(k,),counts)
 elif isinstance(want,list):
  assert len(want)==len(got),(path,len(want),len(got))
  for i,(x,y)in enumerate(zip(want,got)):compare(x,y,path+(i,),counts)
 else:assert want==got,(path,want,got);counts['known_values']+=1


def revalidate_raw(raw,runtime):
 game=bytes.fromhex(raw['raw_game8192_hex']);assert len(game)==8192;q=raw['known'];read=lambda o:struct.unpack_from('<I',game,o)[0]
 assert q['derived_bits']=={str(o):read(o)for o in range(1536,1628,4)}
 for key,o in(('current_hp_bits',1440),('speed_bits',1648),('counter2408',2408),('message_sequence2412',2412),('action_sequence1644',1644)):assert q[key]==read(o)
 assert q['rng_words']==list(struct.unpack_from('<4I',game,1720))and q['auxiliary_bits']=={str(o):read(o)for o in(1444,1448,1348,764)}
 for key,value in q['player_fields'].items():assert raw['raw_keyed_fields'][key]==value
 for name,offset,stride in(('live',1704,32),('pickups',1868,56)):
  cap,p,count=struct.unpack_from('<3I',game,offset);v=q[name];assert(v['capacity'],v['count'])==(cap,count)and count<=cap<=4096 and len(v['storage'])==cap and p+cap*stride<=runtime['max_memory_bytes'];assert all(len(bytes.fromhex(x))==stride for x in v['storage'])
 for name,offset,stride in(('raw_packets',1880,16),('raw_notifications',1892,12)):
  cap,p,n=struct.unpack_from('<3I',game,offset);queue=raw[name];assert(queue['capacity'],queue['count'])==(cap,n)and n<=cap and len(queue['active'])==n;metadata=bytes.fromhex(queue['raw_hex']);assert len(metadata)==n*stride
  for index,item in enumerate(queue['active']):
   size,ptr,length=struct.unpack_from('<3I',metadata,index*stride);assert length<=size<=1048576 and ptr+length<=runtime['max_memory_bytes']and len(bytes.fromhex(item['payload_hex']))==length
   if name=='raw_packets':assert item['opcode']==struct.unpack_from('<H',metadata,index*stride+12)[0]
 aura=raw['raw_aura16'];cap,p,n=struct.unpack_from('<3I',game,2000);assert(aura['capacity'],aura['count'])==(cap,n)and n<=cap<=256 and len(bytes.fromhex(aura['storage_hex']))==cap*16 and p+cap*16<=runtime['max_memory_bytes']
 assert q['destroy170_hex']==[x['payload_hex']for x in raw['raw_packets']['active']if x['opcode']==170]
 return q


def review_case(c,w,a,label,counts,semantic):
 assert c['id']==w['id']==a['id']==label['id']and len(c['operations'])==len(w['stages'])==len(a['stages'])
 state=c['state'];t=state['stats'];assert t['flag2574']==0 and all(not t[k]for k in('passives','adjustments','item_modifiers','owned_skills','timed_records','timed_definitions','live_effects'))
 assert all(t[k]==0 for k in('pool1532_bits','pool1536_bits','conditional1344_id','conditional1348_bits','pool768_bits','conditional268_bits'))
 base={str(k):v for k,v in state['derived_bits']};derived=dict(base);hp=t['current_hp_bits'];speed=t['previous_speed_bits'];sequence=state['action_sequence1644'];fields={str(k):v for k,v in state['player_fields']};live=[list(x)for x in state['live']['storage']];lc=state['live']['count'];pickup=c.get('pickups',dict(storage=[],count=0));backing=[list(x)for x in pickup['storage']];pc=pickup['count'];destroys=[];locale_initialized=False
 for op,want,raw,meta in zip(c['operations'],w['stages'],a['stages'],label['operations']):
  now=op['now_bits'];kinds=[]
  if op['operation']=='effect':kinds=[op['kind']];semantic['direct10291']+=1
  else:
   assert op['operation']=='collect';semantic['full2862']+=1;selected=[];xyz=c['player_xyz_bits']
   for index,row in enumerate(backing[:pc]):
    kind=u(row,8);assert kind>=2 and u(row,0)in(0,1)
    dx,dy=sub(u(row,40),xyz[0]),sub(u(row,44),xyz[1]);distance=B(math.sqrt(F(add(mul(dx,dx),mul(dy,dy)))))
    if F(distance)<=3:
     assert kind in(3,4,5)and u(row,24)==u(row,32)==0;selected.append(index)
   events=[]
   for index in reversed(selected):
    row=backing[index].copy();kind=u(row,8);guid=int.from_bytes(bytes(row[16:24]),'little');kinds.append(kind);events.append((index,kind,guid,{3:23451,4:23505,5:23493}[kind]));destroys.append(struct.pack('<Q',guid).hex())
    for j in range(index,pc-1):backing[j]=backing[j+1].copy()
    pc-=1
   assert [list(x)for x in events]==meta['consumed'];semantic['nested_consumed']+=len(kinds);semantic['near_markers0']+=sum(u(pickup['storage'][i],0)==0 for i in selected)if len(a['stages'])==1 else 0
   if not kinds:semantic['empty_collection_stages']+=1
  for kind in kinds:
   assert kind in(3,4,5);locale_initialized=True;semantic['actual_effects_including_nested']+=1;semantic['effect_kind'+str(kind)]+=1
   if kind==5:
    request=mul(derived['1536'],0x3f000000);request=mul(request,0x3f000000 if state['heal_gate387']>4 else 0x3f800000);candidate=add(hp,request);hp=candidate if F(candidate)<F(derived['1536'])else derived['1536'];fields.update({'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(derived['1536'])))})
    semantic['heal_gate_halved']+=state['heal_gate387']>4;semantic['heal_capped']+=hp==derived['1536']
   else:
    spell,duration=(23451,0x41200000)if kind==3 else(23505,0x41700000);write=0
    for read in range(lc):
     if u(live[read],20)==spell:semantic['removed_same_spell_all_owners']+=1;continue
     if read!=write:live[write]=live[read].copy()
     write+=1
    if write==len(live):live.extend([[None]*32 for _ in range(max(4,2*len(live))-len(live))]);semantic['live_capacity_growths']+=1
    row=live[write]
    for o,v in((0,0),(4,0),(8,0),(20,spell),(24,add(now,duration)),(28,0)):put(row,o,v)
    lc=write+1
    assert all(u(x,8)==0 for x in live[:lc]);spells={u(x,20)for x in live[:lc]if F(u(x,24))>F(now)}
    derived=dict(base);derived['1556']=min((add(base['1556'],0x3f19999a)if 23451 in spells else base['1556']),0x400ccccd,key=F);derived['1540']=add(base['1540'],0x3f000000)if 23505 in spells else base['1540']
    new_speed=mul(derived['1556'],0x40e00000)
    if F(sub(new_speed,speed)&0x7fffffff)>F(0x3c23d70a):speed=new_speed;sequence=(sequence+1)&MASK;semantic['speed_sequence_changes']+=1
    hp=hp if F(hp)<F(derived['1536'])else derived['1536'];fields.update({'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(derived['1536']))),'1109':mul(derived['1548'],0x42c80000)})
   semantic['full32B_and_effect_owner_checks']+=1
  prediction=dict(live=dict(capacity=len(live),count=lc,storage=live),pickups=dict(capacity=len(backing),count=pc,storage=backing),destroy170_hex=destroys,derived_bits=derived,current_hp_bits=hp,speed_bits=speed,auxiliary_bits={'1444':0,'1448':0,'1348':0,'764':0},player_fields=fields,rng_words=state['rng_words'],counter2408=state['counter2408'],message_sequence2412=state['message_sequence2412'],action_sequence1644=sequence)
  assert prediction==want,(c['id'],op,'independent prediction differs from frozen expected')
  observed=dict(raw['known']);observed['live']={**observed['live'],'storage':[list(bytes.fromhex(x))for x in observed['live']['storage']]};observed['pickups']={**observed['pickups'],'storage':[list(bytes.fromhex(x))for x in observed['pickups']['storage']]};compare(want,observed,(),counts);counts['stages']+=1;counts['observed_packets']+=raw['raw_packets']['count'];counts['observed_notifications']+=raw['raw_notifications']['count']
  words=struct.unpack('<7I',bytes.fromhex(raw['locale_state_hex']));assert words[6]==(3 if locale_initialized else 0)
  if locale_initialized:assert words[3]==words[5]==14 and(words[1]if words[0]else words[2])==0
 semantic['initialized_locale_cases'if locale_initialized else'far_locale_untouched_cases']+=1


def main():
 began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('resource-consumer137-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();report=json.loads((RUN/'comparison.json').read_text());assert sha(RUN/'comparison.json')=='5797efa62a4852134823656d80c92644b865234f975ab135ab456e217ba065b8'and report['differences']==0 and report['source_sha256_before']==report['source_sha256_after'];source=RUN/'source-snapshot';files=report['source_sha256_before'];assert len(files)==32
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 assert source_edges(source,files)==report['local_source_import_edges']and len(report['local_source_import_edges'])==82
 production=sorted(n for n in files if n.startswith('reconstruction/'));assert production==production_closure(source)and len(production)==23
 for n in production:
  for node in ast.walk(ast.parse((source/n).read_text())):
   if isinstance(node,ast.Call):
    f=node.func;name=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else'';assert name not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__')
 for n,h in(report['frozen_artifacts']|report['artifacts']).items():assert sha(RUN/n)==h
 original=ORIGINAL.read_bytes();manifest=json.loads((RUN/'manifest.json').read_text());changed=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(original).hexdigest()==report['original_sha256']==manifest['original_sha256']and hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
 a,b=sections(original),sections(changed);assert[x[0]for x in a]==[x[0]for x in b]and not any(x[0]==8 for x in a)and all(original[x:y]==changed[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
 assert exports(changed)==exports(original)+[['research137_resource_effect10291',0,10291],['research137_resource_collect2862',0,2862],['research137_resource_consumer_stack0',3,0]]
 ids=identities(original,(10291,2862,31727,1514,1151,10841,19971,82064,29528,10520,42926));assert ids[10291]['signature']==['7f7f','']and ids[2862]['signature']==['7f',''];assert all(manifest['entry'][k]==v for k,v in ids[10291].items()if k!='index')
 static=[]
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.137.0-full.wat').open('rb')as wat:
  for index,row in ids.items():
   begin,end,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone();assert(bs,be)==(row['body_start'],row['body_end'])and end-begin<=1048576;wat.seek(begin);text=wat.read(end-begin);(out/f'function-{index}.wat').write_bytes(text);static.append(dict(**row,wat_start=begin,wat_end=end,wat_sha256=hashlib.sha256(text).hexdigest()))
   if index==10291:assert text==(RUN/'10291.wat').read_bytes()
  assert db.execute('select count(*)from calls where caller=19971 and callee=82064').fetchone()[0]>0
 del original,changed
 inputs=json.loads((RUN/'input.json').read_text());wanted=json.loads((RUN/'expected.json').read_text());actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];labels=json.loads((RUN/'labels.json').read_text());assert len(inputs)==len(wanted)==len(actual)==len(labels)==156
 runtime=report['runtime'];assert runtime==json.loads((RUN/'resource-consumer137-runtime.json').read_text());counts=Counter();semantic=Counter()
 for c,w,a,label in zip(inputs,wanted,actual,labels):
  assert time.monotonic()-began<60
  for stage in a['stages']:revalidate_raw(stage,runtime)
  review_case(c,w,a,label,counts,semantic)
 assert{key:counts[key]for key in report['comparison']}==report['comparison']and semantic['direct10291']==171 and semantic['full2862']==79 and semantic['nested_consumed']==27 and semantic['initialized_locale_cases']==138 and semantic['far_locale_untouched_cases']==18
 assert runtime['fresh_instances']==runtime['cases']==runtime['completed_cases']==156 and runtime['full_original_calls']=={'10291':171,'2862':79}and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['stack_all_restored']and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])and runtime['max_memory_bytes']<=runtime['memory_cap_bytes']==33554432
 assert all(runtime[k]is False for k in('application_start_called','full_game_started','network_used','user_saves_accessed','original_memory_snapshot_read','once_or_locale_state_injected'))
 for row in runtime['locales']:assert bytes.fromhex(row['before_hex'])==bytes(28)and row['first_call_bootstrap_untouched']
 prepared=json.loads((RUN/'prepared.json').read_text());checker=(source/'scripts/check_resource_consumer137.py').read_text();assert checker.index('rows,expected,labels=corpus(')<checker.index('child=subprocess.Popen(')and'child.wait(timeout=60)'in checker and prepared['expected_before_original']and prepared['artifacts']==report['frozen_artifacts']and prepared['source_sha256']==files
 terminal=report['process'];assert terminal==json.loads((RUN/'process-terminal.json').read_text())and terminal['exit_code']==0 and terminal['error']is None and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
 assert not(RUN/'stderr.log').stat().st_size and json.loads((RUN/'differences.json').read_text())==[]
 negative=[]
 for name in('190314.173389','190504.861930'):
  p=ROOT/f'evidence/resource-consumer0137-oracle-20261101T{name}Z';r=json.loads((p/'comparison.json').read_text());assert r['process']['exit_code']==1 and r['runtime']is None and missing(r['process']['pid'])and missing(r['process']['pgid'],True);negative.append(dict(directory=str(p),comparison_sha256=sha(p/'comparison.json'),stderr_sha256=sha(p/'stderr.log'),actual_host_calls='unknown; no final runtime',not_a_positive_case=True))
 assert'wasm-function[31727]'in(ROOT/'evidence/resource-consumer0137-oracle-20261101T190504.861930Z/stderr.log').read_text()
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n)
 result=dict(status='passed_scoped_read_only_review',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),reviewer_script_sha256=sha(Path(__file__)),source_files=32,production_files=23,local_dependency_edges=82,current_and_frozen_sources_verified=True,nonexport_sections_and_all_callees_unchanged=True,static_functions=static,cases=156,stages=250,external_original_calls=runtime['full_original_calls'],nested_consumed_resources=27,comparison_counts=dict(counts),independent_semantic_checks=dict(semantic),full32B_stable_all_owner_filter_and_full56B_reverse_compaction_independently_rebuilt=True,known12_16_and_original_unknown_masks_preserved=True,all23_derived_and_three_known_keyed_fields_rechecked=True,numeric_stat_scope='Input baseline derived23 is an explicit typed dependency. Reviewer independently applies active unique spell23451 +.6 speed and23505 +.5damage; other baseline words remain fixed. Full original1514 freshly executes and complete23 words strictly match.',complete170_payloads_and_queue_order_compared=True,other_aura_all_keyed_wire_and_notifications_semantics_claimed_predicted=False,locale_original82064_initialization_without_injection=True,marker2_preserved_failures=negative,process=terminal,host_calls=0,stack_all_restored=True,model_or_original_or_checker_executed_by_reviewer=False,new_original_cases=0,new_full880_frames=0,native_Windows_execution=False,scope=report['scope'],input_limitations=report['input_limitations'],pending=report['pending'],elapsed_seconds=time.monotonic()-began)
 assert result['elapsed_seconds']<60
 (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],semantic=dict(semantic))),flush=True)
if __name__=='__main__':main()
