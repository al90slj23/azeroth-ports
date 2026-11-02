#!/usr/bin/env python3
"""Different-author static source/declaration migration review, no target execution."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_combat139 import sha,parse_module,local_closure
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
NEW=ROOT/'originals/official-release-v2-20261102T133059.984802Z/latest-wenilla_bg.wasm'
HASHES=['71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299','8831b4a21314cefd0b9f56dcb5681ac822a9ee30770ab1acae473f9e8f2aec71']
BATCH=ROOT/'evidence/engine1391-data-delta-20261102T135030.000122Z'
HAND='cb65945763a99b74f09ba9991e2cc134d26a117f6a88e31c909d18a876a5326f'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]

def normalize(text,model):
 bounds=[(at,at+n)for at,_,n in model['data_segments']if at is not None];lo=min(a for a,b in bounds);hi=max(b for a,b in bounds);out=[]
 def addr(v):return lo<=v<hi
 for rawline in text.splitlines():
  line=rawline.strip();line=re.sub(r'^\(func \(;\d+;\) \(type \d+\)','(func (type SIGNATURE)',line)
  line=re.sub(r'^(call|return_call) \d+(\)*)$',r'\1 CALLEE\2',line)
  line=re.sub(r'\(type (\d+)\)',lambda q:'(type '+'->'.join(model['types'][int(q[1])])+')',line)
  m=re.fullmatch(r'i32.const (-?\d+)(\)*)',line)
  if m and addr(int(m[1])&0xffffffff):line='i32.const DATA_ADDRESS'+m[2]
  m=re.fullmatch(r'i64.const (-?\d+)(\)*)',line)
  if m:
   v=int(m[1])&((1<<64)-1);a=v&0xffffffff;b=v>>32
   if addr(a)or addr(b):line='i64.const '+('DATA'if addr(b)else str(b))+':'+('DATA'if addr(a)else str(a))+m[2]
  line=re.sub(r'offset=(\d+)',lambda q:'offset=DATA_ADDRESS'if addr(int(q[1]))else q[0],line);out.append(line)
 return out

def main():
 began=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
 assert sha(BATCH/'task-handoff.json')==HAND;hand=load(BATCH/'task-handoff.json');authors=hand['frozen_author_files'];assert len(authors)==6
 for n,h in authors.items():assert sha(ROOT/n)==h
 report=load(ROOT/'reports/2026-11-02-engine0139-1-incremental.json');delta=load(BATCH/'delta.json');mapping=load(ROOT/report['refined_mapping']);initial=load(ROOT/report['initial_mapping']);assert sha(ROOT/report['refined_mapping'])==report['refined_mapping_sha256']==hand['refined_mapping_sha256']and sha(BATCH/'delta.json')==report['data_delta_sha256']==hand['data_delta_sha256']
 source=report['source_hashes'];assert len(source)==8 and len(local_closure(source))==10 and local_closure(source)==sorted(report['local_edges'])
 for n,h in source.items():assert sha(ROOT/n)==h
 raw=[p.read_bytes()for p in(OLD,NEW)];assert [hashlib.sha256(b).hexdigest()for b in raw]==HASHES;models=[parse_module(b)for b in raw]
 profiles=[ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z',ROOT/'evidence/wasm01391-profile-20261102T133454.115329Z'];dbs=[];streams=[];cache={};readbytes=[0,0];bindings={}
 for p in profiles:
  db=sqlite3.connect((p/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;dbs.append(db);streams.append(Path(load(p/'manifest.json')['wat_path']).open('rb'))
 def body(v,idx):
  key=(v,idx)
  if key not in cache:
   loc=dict(dbs[v].execute('select * from functions where idx=?',(idx,)).fetchone());a,z=models[v]['bodies'][idx];assert(a,z)==(loc['body_start'],loc['body_end']);n=loc['wat_end']-loc['wat_start'];assert 0<n<6500000 and readbytes[v]+n<45000000;streams[v].seek(loc['wat_start']);b=streams[v].read(n);readbytes[v]+=n;assert b.startswith(f'  (func (;{idx};)'.encode());cache[key]=b.decode();bindings[f'{v}:{idx}']=dict(body_sha256=hashlib.sha256(raw[v][a:z]).hexdigest(),wat_sha256=hashlib.sha256(b).hexdigest(),wat_start=loc['wat_start'],wat_end=loc['wat_end']);
  return cache[key]
 def signature(v,idx):return models[v]['types'][models[v]['decl'][idx-882]]
 byrole={e['role']:e for e in mapping['entries']};assert len(byrole)==30 and len(mapping['bindings'])==30 and report['unresolved_roles']==[]
 norms={(v,role):normalize(body(v,e['old']['index']if v==0 else e['new_index']),models[v])for role,e in byrole.items()for v in(0,1)};equal=[];proofcounts=Counter()
 for role,e in byrole.items():
  oi=e['old']['index'];ni=e['new_index'];assert signature(0,oi)==signature(1,ni)
  for v,idx,label in((0,oi,'old'),(1,ni,'new')):
   text=body(v,idx);claim=e[label];actual=bindings[f'{v}:{idx}'];assert actual['body_sha256']==claim['body_sha256']and actual['wat_sha256']==claim['wat_sha256'];assert text==(ROOT/report['refined_mapping']).parent.joinpath(f'{1390 if v==0 else 1391}-{role}-{idx}.wat').read_text()
   norms[(v,role)]=normalize(text,models[v])
  same=norms[0,role]==norms[1,role];assert same==e['full_call_data_normalized_equal'];equal.append((role,same))
  for proof in e['binding_proofs']:
   kind=proof['kind'];proofcounts[kind]+=1
   if kind=='initial_exact_or_full_normalized':
    parent=next(x for x in initial['entries']if x['role']==role);assert parent['new_index']==ni and parent['unique_within_declared_search']and not parent['candidate_pool_truncated'];assert norms[0,role]==norms[1,role]
    if proof['method']=='exact_body_and_signature':assert bindings[f'0:{oi}']['body_sha256']==bindings[f'1:{ni}']['body_sha256']
   elif kind=='full_normalized_parent_call_ordinal':
    parent=proof['caller_role'];assert norms[0,parent]==norms[1,parent]
    calls=[]
    for v,idx in((0,proof['old_caller']),(1,proof['new_caller'])):calls.append([tuple(r)for r in dbs[v].execute('select callee,wat_line from calls where caller=? order by wat_offset',(idx,))])
    k=proof['ordinal'];assert calls[0][k]==(oi,proof['old_wat_line'])and calls[1][k]==(ni,proof['new_wat_line'])
   elif kind=='unique_exact_bound_parent_call_context':
    width=proof['width_each_side'];assert width in(3,5,7);context=proof['context'];assert len(context)==2*width+1
    for v,idx,pos in((0,proof['old_caller'],proof['old_relative_line']),(1,proof['new_caller'],proof['new_relative_line'])):
     lines=body(v,idx).splitlines();n=normalize(body(v,idx),models[v]);assert int(lines[pos-1].strip().split()[1])==(oi if v==0 else ni);assert n[pos-width-1:pos+width]==context;assert sum(n[k:k+len(context)]==context for k in range(len(n)-len(context)+1))==1
   elif kind=='unique_exact64_instruction_entry_prefix_and_bound_role_edges':
    pool={idx for idx in models[1]['bodies']if signature(1,idx)==signature(0,oi)}
    for constraint in proof['constraints']:
     bound=constraint['new_bound_index'];n=constraint['call_count'];query='select caller from calls where callee=? group by caller having count(*)=?'if constraint['direction']=='out'else'select callee from calls where caller=? group by callee having count(*)=?';pool&={r[0]for r in dbs[1].execute(query,(bound,n))}
    assert sorted(pool)==proof['global_graph_candidates']and len(pool)<=64;selected=[i for i in sorted(pool)if normalize(body(1,i),models[1])[:64]==norms[0,role][:64]];assert selected==proof['exact64_prefix_candidates']==[ni]and norms[0,role][:64]==proof['old_prefix']
   elif kind in('literal_complete14_stage_slot','unique_seven_bound_stage_caller_and_complete14window'):pass
   else:raise AssertionError(('Unreviewedidentityproof',kind))
 assert len(equal)==30 and sum(b for _,b in equal)==15
 anchors=['hits','area','effects','deadline','secondary','collect','terminal'];callers=None
 for r in anchors:
  cs={x[0]for x in dbs[1].execute('select distinct caller from calls where callee=?',(mapping['bindings'][r],))};callers=cs if callers is None else callers&cs
 app=mapping['bindings']['application_tick'];callers={i for i in callers if signature(1,i)==signature(0,byrole['application_tick']['old']['index'])};assert callers=={app}==set(mapping['app14']['unique_seven_stage_callers'])
 roles=mapping['app14']['roles'];sequence=[mapping['bindings'][r]for r in roles];calls=[dict(r)for r in dbs[1].execute('select callee,wat_line,wat_offset from calls where caller=? order by wat_offset',(app,))];windows=[calls[i:i+14]for i in range(len(calls)-13)if [x['callee']for x in calls[i:i+14]]==sequence];assert len(windows)==1 and windows[0]==mapping['app14']['actual_calls'];assert len(roles)==14
 for j,r in enumerate(roles):assert any(p['kind']=='literal_complete14_stage_slot'and p['old_slot']==j and p['caller']==app and p['wat_line']==windows[0][j]['wat_line']for p in byrole[r]['binding_proofs'])
 # Same index is not used as identity; the14 literal callsites are fixed by7 anchors.
 imports=[]
 for model in models:
  assert len(model['imports'])==882;imports.append({(r['module'],r['name']):r['signature']for r in model['imports']})
 assert imports[0]==imports[1]and report['imports']==dict(old_count=882,new_count=882,added={},removed={},signature_changed={})
 def read(v,at,n):
  result=bytearray(n)
  for start,pos,length in models[v]['data_segments']:
   if start is None:continue
   lo,hi=max(at,start),min(at+n,start+length)
   if lo<hi:result[lo-at:hi-at]=raw[v][pos+lo-start:pos+hi-start]
  return bytes(result)
 decoded=[]
 for v,key in enumerate(('1390','1391')):
  claim=delta['decoded'][key];a=claim['addresses'];word=lambda at:u(read(v,at,4));text=lambda at,n:read(v,at,n).decode('ascii');abilities=[]
  for i in range(114):
   at=a['abilities']+88*i;record=read(v,at,88);reduced=bytearray(record);payload={}
   for k in(12,20,28,36):payload[str(k)]=read(v,word(at+k),word(at+k+4)).hex();reduced[k:k+4]=bytes(4)
   semantic=dict(non_pointer88_hex=reduced.hex(),resolved_payload_hex=payload);abilities.append(dict(index=i,pointer=at,ability_id=text(word(at+12),word(at+16)),effect_tag=word(at),execution_kind=record[84],school=record[85],base_damage_bits=word(at+48),raw88_hex=record.hex(),raw88_sha256=hashlib.sha256(record).hexdigest(),semantic=semantic,semantic_sha256=hashlib.sha256(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
  byid={q['ability_id']:q for q in abilities};assert len(byid)==114;classes=[];races=[];zones=[]
  for identifier in(1,2,3,4,5,7,8,9,11):
   at=a['class_default']if identifier==1 else word(a['class_table']+4*(identifier-2));name=text(word(at+40),word(at+44));assert name in byid;classes.append(dict(class_byte=identifier,pointer=at,starter_id=name,hp_bits=word(at+72),armor_bits=word(at+76),numeric8_hex=read(v,at+72,8).hex(),raw88_hex=read(v,at,88).hex()))
  for identifier in range(1,9):
   at=a['race_default']if identifier==1 else word(a['race_table']+4*(identifier-2));name=text(word(at+24),word(at+28));ability=byid[name];races.append(dict(race_byte=identifier,pointer=at,racial_id=name,effect_tag=ability['effect_tag'],execution_kind=ability['execution_kind'],raw44_hex=read(v,at,44).hex()))
  for identifier in range(12):
   at=a['zones']+152*identifier;zones.append(dict(index=identifier,pointer=at,identifier=text(word(at+8),word(at+12)),x_bits=word(at+104),y_bits=word(at+108),field116_bits=word(at+116),position16_hex=read(v,at+104,16).hex(),raw152_hex=read(v,at,152).hex()))
  d=dict(addresses=a,abilities=abilities,classes=classes,races=races,zones=zones);assert d==claim;decoded.append(d)
 for proof in delta['constructor_literal_consumers']:
  v=0 if proof['version']==1390 else 1;text=body(v,proof['function']);lines=[r.strip()for r in text.splitlines()];seq=proof['instructions'];sites=[k+1 for k in range(len(lines)-len(seq)+1)if lines[k:k+len(seq)]==seq];assert sites==proof['relative_sites'];binding=bindings[f'{v}:{proof["function"]}'];assert binding['body_sha256']==proof['body_sha256']and binding['wat_sha256']==proof['wat_sha256']
 assert len(delta['constructor_literal_consumers'])==16
 comparisons=[]
 for domain,fields in [('abilities',('ability_id','semantic')),('classes',('class_byte','starter_id','hp_bits','armor_bits')),('races',('race_byte','racial_id','effect_tag','execution_kind')),('zones',('index','identifier','x_bits','y_bits','field116_bits'))]:
  for i,(a,b)in enumerate(zip(decoded[0][domain],decoded[1][domain],strict=True)):
   aa={k:a[k]for k in fields};bb={k:b[k]for k in fields};comparisons.append(dict(domain=domain,index=i,fields=list(fields),old=aa,new=bb,equal=aa==bb))
 assert comparisons==delta['comparison']and len(comparisons)==143 and all(q['equal']for q in comparisons)
 bridge=[p.parent/'official-wenilla.js'for p in(OLD,NEW)];js=[p.read_bytes()for p in bridge];lines=[b.splitlines(keepends=True)for b in js];assert len(lines[0])==len(lines[1])and js[0]!=js[1];different=[i for i,(a,b)in enumerate(zip(*lines))if a!=b];audit=load(BATCH/'bridge-comment-audit.json');assert [i+1 for i in different]==audit['changed_line_numbers']and len(different)==17
 for i in different:
  a,b=lines[0][i],lines[1][i];assert a.lstrip().startswith(b'// Cast intrinsic for `Closure(')and b.lstrip().startswith(b'// Cast intrinsic for `Closure(');assert re.sub(rb'shim_idx: \d+',b'shim_idx: INDEX',a)==re.sub(rb'shim_idx: \d+',b'shim_idx: INDEX',b)
 retained=[b''.join(line for i,line in enumerate(ls)if i not in different)for ls in lines];assert retained[0]==retained[1]and hashlib.sha256(retained[0]).hexdigest()==audit['remaining_sha256'];assert sum(b'// Cast intrinsic for `'in row for i,row in enumerate(lines[0])if i not in different)==9
 assert [sha(p)for p in bridge]==[audit['raw_old_sha256'],audit['raw_new_sha256']]
 # Byte occurrence search is explicitly weaker than a Native structure/ABI claim.
 native=NEW.parent/'windows-0.139.1/AzerothSurvivors.exe';assert sha(native)==delta['windows_numeric_references']['exe_sha256'];pe=native.read_bytes();assert pe[:2]==b'MZ'and pe[u(pe,60):u(pe,60)+4]==b'PE\0\0'
 for claim in delta['windows_numeric_references']['fields']:
  pattern=bytes.fromhex(claim['pattern_hex']);sites=[];cursor=0
  while len(sites)<33:
   at=pe.find(pattern,cursor)
   if at<0:break
   sites.append(at);cursor=at+1
  assert sites[:32]==claim['offsets']and(len(sites)>32)==claim['truncated']
 assert report['failed_static_path_probe']and report['target_executions']==report['model_executions']==report['native_executions']==report['new_behavior_cases']==report['complete_games']==0 and not report['old_acceptance_transferred']
 for n,h in authors.items():assert sha(ROOT/n)==h
 save(out/'independent-declarations.json',dict(decoded=decoded,comparison=comparisons))
 result=dict(status='pass_finite1391_static_identity_declarations_and_bridge_only',reviewer='/root/growth139_world',author='/root',handoff_sha256=HAND,author6=authors,source8=source,local_edges=local_closure(source),wasm_sha256=HASHES,current_body_bindings=bindings,normalized_equal_roles=[r for r,b in equal if b],normalized_different_roles=[r for r,b in equal if not b],identity_proof_counts=dict(proofcounts),main14=mapping['app14'],declarations143=143,imports882_unchanged=True,bridge_changed_generated_comments=17,other_generated_comments_retained=9,bridge_remaining_sha256=hashlib.sha256(retained[0]).hexdigest(),failed_probe_preserved=report['failed_static_path_probe'],wat_bounded_seek_bytes=readbytes,author_executions=0,original_executions=0,native_executions=0,old_behavior_acceptance_transferred=False,reviewer_source_sha256=sha(__file__),declarations_sha256=sha(out/'independent-declarations.json'),seconds=time.monotonic()-began,limitations=['30static identity bindings only;15complete normalized call/data bodies equal and15different; erased callees/static-address envelopes cannot prove semantics.','Initial full-normalized role matches retain their declared constrained candidate-pool uniqueness receipt; downstream literal contexts/multirole graph/intersection andexact64prefix are independently recalculated.','143records compare finite listed declarative fields; ability88B four pointer-length payloads resolved; nested complete objects/all114skill execution unproven.','Exact17generated changed comment lines removed;9unchanged generated lines andallremaining bytes retained. JS rawbytes differ. No browser behavior inferred.','Windows numeric byte occurrences are not structure/ABI/runtime; failedWindows path probe remains retained.','No1391behavior cases,App/bootstrap/full884/completegame andno139.0 acceptance transfer.'])
 save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),body_bindings=len(bindings),seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
