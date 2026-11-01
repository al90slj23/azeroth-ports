#!/usr/bin/env python3
"""Read-only final75 supply-kind2 evidence review; never runs a producer/oracle."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import ast,hashlib,json,math,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,static_reader,missing,allowed_unknown
from review_combat137 import exports
from review_battle_shout135 import F,B,add,sub,mul,literal
from review_resource_spawn135 import advance,uniform,decode169,clamp_xy
from review_resource_consumer137 import source_edges,identities
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/full0135-oracle-20261101T192704.946829Z'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
MASK=0xffffffff

def sha(p):
 with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def word(row,o):
 values=row[o:o+4];assert len(values)==4 and all(type(x)is int and 0<=x<=255 for x in values);return int.from_bytes(bytes(values),'little')
def put(row,o,value):row[o:o+4]=list(struct.pack('<I',value))
def div(a,b):return B(F(a)/F(b))
def round85719(w):
 r=add(w,0x3effffff);e=(r>>23)&255
 if e<=149:r&=0x80000000 if e<127 else((-8388608)>>((e-127)&31))&MASK
 return max(0,min(MASK,int(F(r))))
def caps(s):
 if s['mode']==0:return 0x3f800000,3,5,None
 assert s['mode']==1;total=(s['party_count2140']+1)&MASK;remaining=(total-s['excluded2548'])&MASK;guarded=remaining if remaining<=total else 0
 factor=add(mul(sub(B(float(max(1,guarded))),0x3f800000),0x3f000000),0x3f800000)
 return factor,round85719(mul(factor,B(3))),round85719(mul(factor,B(5))),guarded
def compare(want,got,path,counts):
 if want is None:
  assert len(path)>=4 and path[-4]in('units','pickups')and path[-3]=='storage'and type(got)is int and 0<=got<=255,path
  counts['unknown_cells']+=1;counts['nonzero_unknown_original_cells']+=bool(got);return
 assert type(want)is type(got),(path,type(want),type(got))
 if isinstance(want,dict):
  assert set(want)==set(got),(path,set(want),set(got))
  for k,v in want.items():compare(v,got[k],path+(k,),counts)
 elif isinstance(want,list):
  assert len(want)==len(got),(path,len(want),len(got))
  for i,(a,b)in enumerate(zip(want,got)):compare(a,b,path+(i,),counts)
 else:assert want==got,(path,want,got);counts['known_values']+=1

def review_case(c,w,a,label,geometry,counts,sem):
 assert c['id']==w['id']==a['id']==label['id'];s=c['input'];old=s['pickups'];want=w['result'];actual=a['result'];tick=c['operation']=='tick';assert tick or c['operation']=='produce'
 rows=[row.copy()for row in old['storage']];count=old['count'];words=tuple(s['rng_words']);counter=s['counter'];factor,outer,inner,guarded=caps(s);ordinary=[];opaque=[];removed=[]
 before,after=(bytes.fromhex(a[k])for k in('game_before8192_hex','game_after8192_hex'));assert len(before)==len(after)==8192
 u=lambda b,o:struct.unpack_from('<I',b,o)[0]
 assert struct.unpack_from('<4I',before,1720)==words and u(before,2408)==counter and before[2582]==s['mode']and u(before,2140)==s['party_count2140']and u(before,2548)==s['excluded2548']
 assert(u(before,1868),u(before,1876))==(len(rows),count)and u(before,1872)>0
 assert u(before,2352)==s['now_bits']and u(before,2412)==c['message_sequence']==1 and u(before,1880)==u(before,1888)==u(before,1900)==0
 if tick:
  frame=c['frame'];assert frame['mode']==s['mode']and frame['now_bits']==s['now_bits'];ordinary=label['ordinary_requests'];words=advance(words,label['ordinary_draws']);counter=(counter+len(ordinary))&MASK
  assert len(ordinary)==actual['units']['count']-c['units']['count']and c['units']['count']==4
  assert all(u(before,o)==v for o,v in c['initial_scalars']if o not in(2416,2420,2428,2432,2436,2448)and str(o)not in c['other_clocks'])
  assert u(before,2448)==s['next_supply2448_bits']and u(before,2416)==frame['budget_bits']and u(before,2420)==frame['kill_cost_bits']
  assert struct.unpack_from('<3I',before,1416)==tuple(s['player_xyz_bits'])
  assert all(F(v)>F(s['now_bits'])and u(before,int(o))==v and u(after,int(o))==v for o,v in c['other_clocks'].items())
  assert c['other_clocks']==actual['other_clocks']and actual['previous_player_xyz']==(frame['player_xyz']if s['mode']==0 else frame['previous_player_xyz'])
  peers=c['peer_positions16'];assert u(before,2228)==u(before,2236)==len(peers)and u(before,2232)>0
  if s['mode']==1:
   assert peers==label['mode1_peer_positions_explicit']and 1<=len(peers)<=64
   for row in c['units']['storage'][:c['units']['count']]:
    x,y=word(row,328),word(row,332);distances=[]
    for peer in peers:
     assert len(peer)==4 and all(math.isfinite(F(v))for v in peer[:3]);dx,dy=sub(x,peer[0]),sub(y,peer[1]);distances.append(F(add(mul(dx,dx),mul(dy,dy))))
    assert min(distances)<=3025,'Actual947 relocation precondition not established'
   sem['mode1_near_peer_cases']+=1;sem['mode1_original_NPC_near_peer_proofs']+=c['units']['count']
   sem['mode1_underflow_cases']+=((s['party_count2140']+1-s['excluded2548'])&MASK)>((s['party_count2140']+1)&MASK)
  else:assert not peers
  due=F(s['now_bits'])>=F(s['next_supply2448_bits']);matching=sum(word(row,8)==2 for row in rows[:count]);spawned=due and matching<outer
  status='supply2448_spawned'if spawned else'supply2448_cap'if due else'supply2448_future';assert label['status']==status;sem[status]+=1
  assert actual['next_supply2448_bits']==(add(s['now_bits'],div(B(70),factor))if due else s['next_supply2448_bits'])
  if due:assert(label['factor_bits'],label['cap'],label['counted_kind2'])==(factor,outer,matching)
  else:assert label['factor_bits']is label['cap']is label['counted_kind2']is None
  if spawned:words=advance(words,label['position_draws']);assert label['position_draws']>=2
  else:assert label['position_draws']==label['actor_draws']==0
  for i,row in enumerate(c['units']['storage'][:c['units']['count']]):assert bytes.fromhex(actual['units']['storage'][i])==bytes(c['unknown_poison']if v is None else v for v in row),'Prior NPC changed/relocated'
  for i,row in enumerate(want['units']['storage']):
   for o,v in enumerate(row):
    if v is None and i>=c['units']['count']and i<want['units']['count']:allowed_unknown('units',row,o)
    elif v is None and i<c['units']['count']:assert c['units']['storage'][i][o]is None
  if label['group']=='complete947-opening2-resource40-first60':
   assert c['id']in(16,31,46,61)and count==3 and matching==2 and spawned and s['counter']==86 and sorted(word(r,8)for r in rows[:count])in([2,2,3],[2,2,4],[2,2,5]);sem['resource40_mixed_count3_owner176']+=1
 else:spawned=True;sem['direct1417']+=1
 packet_offset=len(ordinary)
 for request,p in zip(ordinary,actual['packets']):
  d=decode169(p['payload_hex']);assert p['opcode']==169 and d['variant']==3 and d['guid']==request['guid']and d['xyz']==tuple(request['position_bits']);sem['ordinary169_payload_semantic_bindings']+=1
 if spawned:
  matching=[i for i,row in enumerate(rows[:count])if word(row,8)==2]
  if matching and len(matching)>=inner:
   def totalkey(i):
    v=word(rows[i],52);v^=0x7fffffff if v&0x80000000 else 0;return v-(1<<32)if v&0x80000000 else v
   index=min(matching,key=totalkey);row=rows[index];assert word(row,0)!=2 and word(row,24)==word(row,32)==0
   guid=int.from_bytes(bytes(row[16:24]),'little');removed.append(guid)
   assert actual['packets'][packet_offset]==dict(opcode=170,payload_hex=struct.pack('<Q',guid).hex());packet_offset+=1
   for i in range(index,count-1):rows[i]=rows[i+1].copy()
   count-=1;sem['full56_stable_oldest_replacements']+=1
   if label['group']=='direct1417-oldest-last-nonmonotonic':assert index==4;sem['oldest_nonmonotonic_last']+=1
   if label['group']=='direct1417-oldest-tie-first':assert index==0;sem['oldest_first_tie']+=1
  if tick and old['count']:
   n=old['count'];delta=176+224*(n//4)if n%4==0 else 8+56*n;amount=None
  else:delta=None;amount=guarded if tick else s['amount'];assert type(amount)is int
  if count==len(rows):rows.extend([[None]*56 for _ in range(max(4,2*len(rows))-len(rows))]);sem['physical_pickup_capacity_growths']+=1
  observed=bytes.fromhex(actual['pickups']['storage'][count]);xyz=tuple(struct.unpack_from('<3I',observed,40));assert xyz==tuple(label['final_position_bits'])
  if not tick:
   xy,clamped=clamp_xy(s['position_bits'],geometry);assert xyz[:2]==xy;sem['direct1417_clamp_cases']+=clamped
  counter=(counter+1)&MASK;guid=0xf110000000000000|(9005<<24)|(counter&0xffffff)
  original_padding=rows[count][4:8].copy()
  for o,v in((0,0),(8,2),(16,guid&MASK),(20,guid>>32),(24,0),(28,8),(32,0),(36,9005),(40,xyz[0]),(44,xyz[1]),(48,xyz[2]),(52,s['now_bits'])):put(rows[count],o,v)
  if amount is None:
   rows[count][12:16]=[None]*4;opaque=[dict(guid=str(guid),offset=12,bytes=4,owner_symbol='pickup56_owner_before2448',active_count=old['count'],byte_delta=delta,expression='pre_owner_base+byte_delta modulo2^32')]
   assert len(a['amount_observations'])==1;obs=a['amount_observations'][0]
   assert obs==dict(guid=str(guid),actual_word=word(list(observed),12),pre_owner_base=u(before,1872),byte_delta=delta,derived_word=(u(before,1872)+delta)&MASK)
   assert obs['actual_word']==obs['derived_word']and sum(int.from_bytes(bytes.fromhex(r)[16:24],'little')==guid for r in actual['pickups']['storage'][:actual['pickups']['count']])==1
   counts['opaque_amount_words_exact_owner_formula_checked']+=1;sem['newGUID_exact_four_None_bytes_for_address_word']+=4
  else:put(rows[count],12,amount);assert not a['amount_observations'];sem['known_amount_words']+=1
  assert rows[count][4:8]==original_padding;sem['preserved_known_padding4_bytes']+=sum(v is not None for v in original_padding)
  yaw,words,draws=uniform(words,0x40c90fdb);assert draws==label['actor_draws'];p=actual['packets'][packet_offset];d=decode169(p['payload_hex'])
  assert p['opcode']==169 and d['variant']==2 and d['guid']==guid and d['xyz']==xyz and d['yaw']==add(yaw,0)
  assert {k:v for k,v in d['fields'].items()if k not in(12,13)}=={0:guid&MASK,1:guid>>32,2:33,3:9005,4:0x3f800000,8:259,9:0,14:1,15:xyz[0],16:xyz[1],17:xyz[2],18:add(yaw,0),20:35,21:3}
  assert set(d['fields'])=={0,1,2,3,4,8,9,12,13,14,15,16,17,18,20,21}and abs(F(d['fields'][12])-math.sin(F(mul(yaw,0x3f000000))))<0.0000004 and abs(F(d['fields'][13])-math.cos(F(mul(yaw,0x3f000000))))<0.0000004
  count+=1;packet_offset+=1;sem['supply169_complete_semantic_payloads']+=1
 else:assert not a['amount_observations']
 assert packet_offset==len(actual['packets'])and want['pickups']==dict(capacity=len(rows),count=count,storage=rows),'Independent full56B prediction/mask differs from expected'
 assert want['opaque_word_provenance']==opaque and tuple(actual['rng_words'])==words and actual['counter']==counter and actual['message_sequence']==1 and actual['notifications_count']==0
 if not tick:assert label['removed_guids']==removed
 converted=dict(actual)
 for name in('pickups','units'):
  if name in converted:
   v=converted[name];converted[name]={**v,'storage':[list(bytes.fromhex(r))for r in v['storage']]};stride=56 if name=='pickups'else 424;off=1868 if name=='pickups'else 1784
   assert(u(after,off),u(after,off+8))==(v['capacity'],v['count'])and len(v['storage'])==v['capacity']and all(len(bytes.fromhex(r))==stride for r in v['storage'])
 assert struct.unpack_from('<4I',after,1720)==words and u(after,2408)==counter and u(after,2412)==actual['message_sequence']and u(after,1900)==actual['notifications_count']and u(after,1888)==len(actual['packets'])and u(after,1880)>=len(actual['packets'])
 if tick:
  assert all(actual[key]==u(after,o)for key,o in(('next_supply2448_bits',2448),('budget_bits',2416),('kill_cost_bits',2420)))and actual['velocity_xy']==list(struct.unpack_from('<2I',after,1736))and actual['previous_player_xyz']==list(struct.unpack_from('<3I',after,2428))
 allowed=set(range(1720,1736))|set(range(1868,1892))|set(range(2408,2412))
 if tick:allowed|=set(range(1736,1744))|set(range(1784,1796))|set(range(2416,2424))|set(range(2428,2440))|set(range(2448,2452))
 assert all(x==y or i in allowed for i,(x,y)in enumerate(zip(before,after)))
 counts['unchanged_Game_bytes_outside_allowed_ranges']+=8192-len(allowed);compare(want,converted,(),counts)
 counts['packets']+=len(actual['packets']);counts['packet_bytes']+=sum(len(bytes.fromhex(p['payload_hex']))for p in actual['packets'])

def main():
 began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('supply-kind2-135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();report=json.loads((RUN/'supply-kind2-comparison.json').read_text());assert sha(RUN/'supply-kind2-comparison.json')=='716b3d327aa5fcc05ed85911b5da869fa6af3e2ee8c3e83056523f1c4d0f1c76'
 assert report['status']=='compared'and report['comparison_complete']and report['differences']==0 and report['source_unchanged']and report['expected_before_original']and report['source_sha256_before']==report['source_sha256_after'];source=RUN/'source-snapshot';files=report['source_sha256_before'];assert len(files)==61
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 assert files['reconstruction/core_spec/supply_kind2_135.py']=='e765fd68b5615a76a084e6f02b7f94ddbbc48dc944e2a3d323c0fbcbb5f2ae13'
 edges=source_edges(source,files);reachable={'scripts/check_supply_kind2_135.py','scripts/run_supply_kind2_135_oracle.mjs'}
 while True:
  expanded=reachable|{b for a,b in edges if a in reachable}
  if expanded==reachable:break
  reachable=expanded
 assert reachable==set(files),(set(files)-reachable,reachable-set(files));production=[n for n in files if n.startswith('reconstruction/')];assert len(production)==51
 for n in production:
  for node in ast.walk(ast.parse((source/n).read_text())):
   if isinstance(node,ast.Call):
    f=node.func;name=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else'';assert name not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__')
 for n,h in report['frozen_artifacts'].items():assert sha(RUN/n)==h
 for n,h in report['world_inputs'].items():assert sha(Path(n))==h
 original=ORIGINAL.read_bytes();manifest=json.loads((RUN/'manifest.json').read_text());changed=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(original).hexdigest()==manifest['original_wasm_sha256']=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'and hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
 a,b=sections(original),sections(changed);assert[x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]and all(original[x:y]==changed[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
 assert exports(changed)==exports(original)+[['research135_spawn_pickup',0,1417],['research135_spawn_tick',0,947],['research135_resource_stack0',3,0]]
 trace=json.loads((RUN/'supply-kind2-static.json').read_text());ids=identities(original,tuple(r['idx']for r in trace['functions'])+(1465,1560));assert ids[1417]['signature']==['7f7f7f7f','']and ids[947]['signature']==['7f7d',''];static=[];texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  db.execute('pragma query_only=ON')
  for index,identity in ids.items():
   lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone();assert(bs,be)==(identity['body_start'],identity['body_end'])and hi-lo<=1048576;wat.seek(lo);raw=wat.read(hi-lo);texts[index]=raw.decode();static.append(dict(**identity,wat_start=lo,wat_end=hi,wat_sha256=hashlib.sha256(raw).hexdigest()));(out/f'function-{index}.wat').write_bytes(raw)
   if index not in(1465,1560):
    entry=next(r for r in trace['functions']if r['idx']==index);assert raw==(RUN/f'supply-{index}.wat').read_bytes()and static[-1]['wat_sha256']==entry['wat_sha256']and identity['body_sha256']==entry['body_sha256']
 guard='local.get 10\n              i32.const 9\n              i32.store offset=676\n              local.get 10\n              i32.const 1409996\n              i32.store offset=672';assert guard in texts[1465]
 read=static_reader(original);assert read(1409996,9)==b'90898d5e3'and read(1410005,7)==b'0.135.1';assert report['actual_build']==trace['actual_build']=='90898d5e3'and report['historical_build_alias']==manifest['build']=='0898d5e3'
 assert 'i32.const 1114636288\n                  i32.store offset=2536'in texts[1560]
 rules=[]
 for idx,lo,hi,tag in((947,8059,8235,'deadline_factor_count_iterator_outercap'),(1417,514,684,'innercap_oldest_firsttie'),(31732,1,80,'full56_copy_decrement_then_marker2panic'),(1417,875,925,'kind2_row56_writes_skip_padding4'),(85719,1,80,'exact85719_rounding'),(1560,1122,1136,'constructor_scratch2536_is_G2448')):
  rules.append(dict(function=idx,function_lines=[lo,hi],meaning=tag,instructions=texts[idx].splitlines()[lo-1:hi]))
 assert texts[31732].index('memory.copy')<texts[31732].index('i32.store offset=1876')<texts[31732].index('i32.const 2\n          i32.eq\n          br_if')
 assert 'i32.load offset=2236'in texts[947]and'i32.load offset=2232'in texts[947]
 (out/'static-proofs.json').write_text(json.dumps(dict(functions=static,rules=rules,static_image_intervals=read.proofs),indent=2)+'\n');del original,changed
 inputs=json.loads((RUN/'supply-input.json').read_text());wanted=json.loads((RUN/'supply-expected.json').read_text());actual=[json.loads(x)for x in(RUN/'supply-results.jsonl').read_text().splitlines()];labels=json.loads((RUN/'supply-labels.json').read_text());assert len(inputs)==len(wanted)==len(actual)==len(labels)==75
 geometry=literal(source/'reconstruction/core_spec/spawn_position135_data.py','ZONE_GEOMETRY')[0];counts=Counter();semantic=Counter()
 for c,w,a,label in zip(inputs,wanted,actual,labels):
  assert time.monotonic()-began<60
  assert c['world']==inputs[0]['world']and c['world']['kind']=='independently_parsed451_asset_world_inputs'and c['world']['primary']is None and c['world']['flat_height_bits']is None
  for entry in c['world']['artifacts'].values():assert report['world_inputs'][entry['path']]==entry['sha256']
  review_case(c,w,a,label,geometry,counts,semantic)
 assert{k:counts[k]for k in report['comparison']}==report['comparison']and semantic['resource40_mixed_count3_owner176']==4 and semantic['supply2448_spawned']==44 and semantic['supply2448_cap']==12 and semantic['supply2448_future']==4 and semantic['direct1417']==15
 assert Counter(p['opcode']for a in actual for p in a['result']['packets'])=={169:239,170:10}
 runtime=report['runtime'];assert runtime==json.loads((RUN/'supply-kind2-runtime.json').read_text())and runtime['cases']==runtime['fresh_instances']==75 and runtime['functions']=={'1417':15,'947':60}and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['stack_all_restored']and len(runtime['stack_checks'])==2123 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])and runtime['max_memory_bytes']<=runtime['memory_cap_bytes']==33554432
 assert all(runtime[k]is False for k in('application_start_called','full_game_started','network_used','user_saves_accessed','original_memory_snapshot_read','amount_pointer_used_as_model_input'))and runtime['failure']is None
 prepared=json.loads((RUN/'supply-prepared.json').read_text());owned=json.loads((RUN/'supply-owned-process.json').read_text());terminal=json.loads((RUN/'supply-process-terminal.json').read_text());assert prepared['artifacts']==report['frozen_artifacts']and prepared['source_sha256']==files and prepared['world_inputs']==report['world_inputs']and prepared['expected_before_original']and prepared['cases']==75 and prepared['deadline_seconds']==owned['deadline_seconds']==60 and prepared['command']==owned['command']
 assert '--max-old-space-size=512'in prepared['command']and'--wasm-max-mem-pages=512'in prepared['command']and sha(Path(prepared['command'][0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
 assert terminal==report['process']and terminal['exit_code']==0 and terminal['error']is None and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
 assert runtime['output_bytes']==(RUN/'supply-results.jsonl').stat().st_size<=16777216 and max(len(x)for x in(RUN/'supply-results.jsonl').read_bytes().splitlines(keepends=True))<=2097152
 assert not(RUN/'supply-stderr.log').stat().st_size and json.loads((RUN/'supply-differences.json').read_text())==[]
 checker=(source/'scripts/check_supply_kind2_135.py').read_text();runner=(source/'scripts/run_supply_kind2_135_oracle.mjs').read_text();core=(source/'reconstruction/core_spec/supply_kind2_135.py').read_text()
 assert checker.index('cases,expected,labels=corpus(')<checker.index('child=subprocess.Popen(')and'child.wait(timeout=60)'in checker and'start_new_session=True'in checker and'finally:'in checker and'os.killpg(child.pid,signal.SIGTERM)'in checker
 assert not any(isinstance(n,ast.Name)and n.id in('pre_owner_base','prePickupPointer')or isinstance(n,ast.Attribute)and n.attr in('pre_owner_base','prePickupPointer')for n in ast.walk(ast.parse(core)))and'prePickupPointer=r(G+1872)'in runner and'actual!==derived'in runner
 assert 'Mode0 empty-vector amount depends on earlier947 local2 provenance'in core and'Original31732 marker2 enters panic after compaction'in core and json.loads((RUN/'supply-refusals.json').read_text())==report['pure_model_refusals']
 asset=Path(inputs[0]['world']['directory'])/'receipt.json';ar=json.loads(asset.read_text());assert ar['version']=='0.135.1'and ar['original_program_executed']is False and ar['original_memory_read']is False
 primary=json.loads((ROOT/'reports/2026-11-02-supply-kind2-0135.json').read_text());history=[]
 for old in primary['prior_attempts']:
  p=ROOT/old['path'];assert sha(p)==old['sha256']and old['included_in_final_count']is False;r=json.loads(p.read_text());assert r['cases']==old['cases']and r['process']['exit_code']==old['exit_code'];history.append(dict(path=old['path'],sha256=old['sha256'],classification=old['classification']))
 failed=json.loads((ROOT/primary['prior_attempts'][0]['path']).read_text());assert failed['runtime']is None and failed['process']['exit_code']==1
 badmode=json.loads((ROOT/primary['prior_attempts'][2]['path']).read_text());assert badmode['differences']==5127
 alias=json.loads((ROOT/primary['prior_attempts'][-1]['path']).read_text());assert alias['actual_build']=='0898d5e3'
 assert report['full880_frames']==report['natural60_second_runs']==0 and report['amount_pointer_used_as_model_input']is False
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 result=dict(status='passed_scoped_read_only_review',comparison=str(RUN/'supply-kind2-comparison.json'),comparison_sha256=sha(RUN/'supply-kind2-comparison.json'),reviewer_script_sha256=sha(Path(__file__)),source_files=61,production_files=51,local_dependency_edges=len(edges),current_and_frozen_sources_verified=True,private_exports_only_and_all_original_bodies_callees_unchanged=True,original_build='90898d5e3',historical_alias='0898d5e3',original_sha256=manifest['original_wasm_sha256'],static_proofs_sha256=sha(out/'static-proofs.json'),cases=75,original_calls=runtime['functions'],comparison_counts=dict(counts),independent_semantic_checks=dict(semantic),complete56B_active_inactive_compaction_and_None_source_rebuilt=True,exact40_GUID_bound_pre2448_owner_amount_words=True,all249_complete_packet_payloads_and_order_compared=True,ordinary_prefix_scope='Frozen independent ordinary requests and draw count are explicit provenance; reviewer replays shared RNG and checks each ordinary packet/GUID/position and retained four NPCs. Terrain/ordinary model is not executed again.',height_scope='Direct1417 finalXY clamp independently recomputed, finalXYZ/packets strictly compare frozen expected with original; static clamp/height order is verified. Query models are not rerun.',world_scope='Four frozen independently parsed451-asset query inputs, manually packed known Game8192/Rc124 fields and complete backing, explicit unconsumed fixture zeros; no original snapshot or original constructor claim.',mode1_scope='24 cases prove all four original NPCs are within55 of explicit finite16B peer rows bound to G2232/G2236; no missing-peer or far-relocation equivalence claim.',known_limits=['mode0 empty-vector local2 pending','marker2 real post-compaction panic pending; not a positive case or0host claim','nonempty aux ownership/drop pending','primary-present nearest-miss fallback pending','simultaneously due2444/2448 not exercised','fullkind2 consumer/UI effects pending'],historical_attempts_not_added=history,process=terminal,actual_host_calls=0,stack_checks=2123,stack_all_restored=True,output_bytes=runtime['output_bytes'],world_inputs=report['world_inputs'],artifact_sha256={p.name:sha(p)for p in RUN.iterdir()if p.is_file()and p.suffix in('.json','.jsonl','.log')},model_or_original_or_checker_executed_by_reviewer=False,new_original_cases=0,natural60_second_runs=0,full880_frames=0,native_executions=0,elapsed_seconds=time.monotonic()-began)
 assert result['elapsed_seconds']<60
 (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],counts=dict(counts),semantic=dict(semantic))),flush=True)
if __name__=='__main__':main()
