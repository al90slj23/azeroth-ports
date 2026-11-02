#!/usr/bin/env python3
"""Independent read-only1391600 review; no author production/oracle execution.

Default level1 statistics are recomputed from actual139static class/race bytes
using stdlib binary32 arithmetic. PCG uses the conventional xorshift-rotate
expression; explicit known-byte map retains everyother cell asNone.
"""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import ast,hashlib,json,math,sqlite3,struct,time
#Previously frozen independent-review parsing helpers only; no author/model code.
from review_combat139 import parse_module,local_closure,bits,fp,f32
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/initial139-oracle-20261102T021151.357713Z'
SHA='e6b35679f013dc8be3467279606125a76d425b66821928a65ebbfdc30a6a0072'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
BODY='17f2335fc31fe91be1509ffcabe89e56662b61cc2c684f862c54c681eb69b8b1'
STATS_REVIEW=ROOT/'reports/2026-11-02-stats0139-independent-review.json'
STATS_REVIEW_SHA='3e0c974cb0b06c0540b7d0ebaf2bbc88c8bbc247a54524ab26fcecd55c5ef393'
STATS_REVIEW_RECEIPT_SHA='772dee0e4e70f9e9b4af463ecd8473b33cddc19706dccaf6a9c1d556c1b7ffb7'
MASK64=(1<<64)-1
SCALARS={488:0,736:0,740:0,1652:0xc1200000,2416:0x40400000,2424:0x42700000,2428:0,2432:0,2436:0,2440:0x43700000,2444:0x42200000,2448:0x42700000,2452:20,2456:0,2460:0,2464:0,2468:0,2472:0,2516:0x3f800000}
FLAGS={k:0 for k in[768,2568,2572,2573,2576,2578,2581,2583]}
TAGS={k:0 for k in[416,440,448,456,464,1744,1764]}

def sha(p):
 with Path(p).open('rb')as s:return hashlib.file_digest(s,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_text())
def u32(r,p):return struct.unpack_from('<I',r,p)[0]
def u64(r,p):return struct.unpack_from('<Q',r,p)[0]

def rng(seed):
 values=[]
 for multiply,increment in[(7520897724310334953,-2259998930035483990),(793875393913628917,5507651024068337109),(-338549647893938671,-3398641427998916252),(6364136223846793005,-6812164046247290893)]:
  state=(multiply*seed+increment)&MASK64;shifted=(((state>>18)^state)>>27)&0xffffffff;rotate=state>>59;values.append(((shifted>>rotate)|(shifted<<((32-rotate)&31)))&0xffffffff)
 if not any(values):return list(struct.unpack('<4I',struct.pack('<QQ',(-2152535657050944081)&MASK64,7960286522194355700)))
 return values[-1:]+values[:-1]

def default_stats(classdata,racemods):
 hp,armor=map(fp,classdata);damage=1.;cooldown=0.;critical=fp(0x3d4ccccd);critmult=2.;speed=1.;radius=9.;xp=1.;regen=fp(0x3f4ccccd);spells=1.;pickup=1.;dodge=0.;special=0.;healthscale=1.
 for tag,word in racemods:
  value=fp(word)
  if tag==0:healthscale=f32(healthscale+value)
  elif tag==1:damage=f32(damage+value)
  elif tag==2:cooldown=f32(cooldown+value)
  elif tag==3:speed=f32(speed+value)
  elif tag==4:critical=f32(critical+value)
  elif tag==5:armor=f32(armor+value)
  elif tag==6:regen=f32(regen+value)
  elif tag==7:radius=f32(radius*f32(1.+value))
  elif tag==8:xp=f32(xp+value)
  elif tag==9:pickup=f32(pickup+value)
  elif tag==10:dodge=f32(dodge+value)
  elif tag==11:special=f32(special+value)
  else:raise AssertionError('Unrecovered139race modifier')
 mhp=f32(hp*healthscale);speed=min(speed,fp(0x400ccccd));speedbits=bits(f32(speed*7.));changed=abs(f32(fp(speedbits)-7.))>fp(0x3c23d70a)
 derived={1536:bits(mhp),1540:bits(damage),1544:bits(f32(1./f32(1.+cooldown))),1548:bits(min(critical,1.)),1552:bits(critmult),1556:bits(speed),1560:bits(radius),1564:bits(xp),1568:bits(min(armor,fp(0x3f19999a))),1572:0x3f19999a,1576:bits(regen),1580:bits(spells),1584:bits(dodge),1588:bits(pickup),1592:0,1596:0,1600:bits(special),1604:0,1608:0,1612:0,1616:bits(f32(f32(mhp/max(hp,1.))-1.)),1620:0,1624:0}
 return derived,speedbits,changed,{'22':math.ceil(mhp),'28':math.ceil(mhp),'1109':bits(f32(critical*100.))}

def record(pointer):
 #Literal80B initialization: pointer/rank/cooldown and scalar1 defaults.
 words=[0]*20
 for i in[1,3,4,6,7,13,14,16,17,19]:words[i]=0x3f800000
 words[0]=pointer;words[1]=1;words[2]=0x3f000000
 return struct.pack('<20I',*words).hex()

def reference(inp,classes,races,zones):
 cls,race,region=inp['class_byte'],inp['race_byte'],inp['region_index'];seed=int(inp['seed_u64']);guid=int(inp['object_id_u64']);data=classes[cls];r=races[race];derived,speed,changed,fields=default_stats(data['hp_armor'],r['modifiers']);zone=zones[region];xyz=zone['xyz'][:2]+[inp['flat_height_bits']];packets=[]
 if changed:
  raw=guid.to_bytes(8,'little');packed=bytes([sum(1<<i for i,v in enumerate(raw)if v)])+bytes(v for v in raw if v);packets=[[226,(packed+struct.pack('<II',1,speed)).hex()]]
 p=dict(progression=dict(level=1,xp=0,pending_upgrades=0),derived_bits={str(k):v for k,v in derived.items()},current_hp_bits=derived[1536],auxiliary_bits={str(k):0 for k in[1444,1448,1348,764,752]},speed_bits=speed,player_fields=fields,rng_words=rng(seed),candidates=[],phase2587=0,selection_kind2585=255,generation_counter2400=0,owned_records_hex=[record(data['ability_pointer'])],racial_record_hex=record(r['ability_pointer']),player_xyz=xyz,source_id=str(guid),timer1628_bits=0,spawn_counter=10,message_sequence=1,kill_cost_bits=0,action_sequence1644=1+changed,movement_packets=packets,game_tag='0',member_count=1,initial_scalar_words={str(k):v for k,v in SCALARS.items()},initial_byte_flags={str(k):v for k,v in FLAGS.items()},constructor_tags={str(k):v for k,v in TAGS.items()},now_bits=0,mode2582=0,owned_capacity=1,owned_count=1,source_counts={k:0 for k in['passives','adjustments','item_modifiers','owned_skills','timed_records','definitions','live_effects','ability_modifiers','active84']},unit_count=0,pickup_count=0,gold=0,earned=0,flags768=0,context908=0,extra_cast1596_bits=0)
 cells=[None]*2592
 def put(o,raw):cells[o:o+len(raw)]=raw
 def word(o,v):put(o,struct.pack('<I',v))
 put(0,b'\0'*8);put(1336,struct.pack('<Q',guid));put(1256,bytes.fromhex(p['racial_record_hex']));cells[360]=cls;cells[361]=race
 for o,v in zip([1416,1420,1424],xyz):word(o,v)
 word(1428,zone['xyz'][2])
 for o,v in derived.items():word(o,v)
 for o in[1444,1448,1348,764,752]:word(o,0)
 for o,v in(SCALARS|TAGS).items():word(o,v)
 for o,v in FLAGS.items():cells[o]=v
 for o,v in{1432:1,1436:0,1440:derived[1536],1456:0,1100:0,1644:1+changed,1648:speed,1628:0,2352:0,2376:0,2400:0,2408:10,2412:1,2540:1}.items():word(o,v)
 for i,v in enumerate(p['rng_words']):word(1720+i*4,v)
 for cap,ptr,count,sentinel in[(592,596,600,4),(640,644,648,4),(1668,1672,1676,4),(1704,1708,1712,8)]:word(cap,0);word(ptr,sentinel);word(count,0)
 for o in[1700,2032,176,2056,2044,1792,1876]:word(o,0)
 for o in[1656,1664]:word(o,1)
 word(1888,len(packets));cells[2582]=0;cells[2585]=255;cells[2587]=0;cells[908]=0
 return p,cells

def main():
 began=time.monotonic();assert sha(CASE/'comparison.json')==SHA and sha(SOURCE)==SOURCE_SHA and sha(ROOT/'scripts/review_combat139.py')=='158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9'
 assert sha(STATS_REVIEW)==STATS_REVIEW_SHA
 stats_review=load(STATS_REVIEW);stats_receipt=ROOT/stats_review['independent_receipt']
 assert sha(stats_receipt)==stats_review['independent_receipt_sha256']==STATS_REVIEW_RECEIPT_SHA
 c=load(CASE/'comparison.json');m=load(CASE/'manifest.json');prep=load(CASE/'prepared.json');runtime=load(CASE/'runtime.json');hand=load(CASE/'task-handoff.json');assert sha(CASE/'task-handoff.json')=='1ba8847fb628a31d55609123629af90ffeff3e76bb4f13a9e4a3942d0c4519f2'
 for n,h in hand['owned_files'].items():assert sha(ROOT/n)==h
 assert c['source_sha256_before']==c['source_sha256_after']and len(c['source_sha256_before'])==17
 for n,h in c['source_sha256_before'].items():assert sha(ROOT/n)==h and sha(CASE/'source-snapshot'/n)==h
 assert local_closure(c['source_sha256_before'])==sorted(c['source_import_edges'])and len(c['source_import_edges'])==25
 for n,h in c['artifacts'].items():assert sha(CASE/n)==h
 raw=SOURCE.read_bytes();original=parse_module(raw);mutated=(CASE/m['module_file']).read_bytes();changed=parse_module(mutated);assert sha(CASE/m['module_file'])==c['module_sha256']==m['module_sha256']
 assert len(original['sections'])==len(changed['sections'])
 for a,b in zip(original['sections'],changed['sections']):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==mutated[b['start']:b['end']]
 assert changed['exports']==original['exports']+[('research139_initial1600',0,1600),('research139_initial_stack0',3,0)]and original['types'][original['decl'][1600-882]]==('7f7f7f','')and original['decl'][1600-882]==1
 ba,bb=original['bodies'][1600];assert hashlib.sha256(raw[ba:bb]).hexdigest()==BODY
 assert len(original['imports'])==882 and runtime['denied_import_surface']==[{k:x[k]for k in['module','name','kind']}for x in original['imports']]
 def read(p,n):
  assert n<=1048576 and 0<=p<=p+n<=original['minimum_memory_pages']*65536;answer=bytearray(n)
  for a,b,size in original['data_segments']:
   if a is None:continue
   lo,hi=max(a,p),min(a+size,p+n)
   if lo<hi:answer[lo-p:hi-p]=raw[b+lo-a:b+hi-a]
  return bytes(answer)
 def u(p):return u32(read(p,4),0)
 def text(p,n):return read(p,n).decode('ascii')
 abilities={}
 for j in range(114):
  p=5882740+j*88;abilities[text(u(p+12),u(p+16))]=p
 classes={};races={};zones=[]
 for cls in[1,2,3,4,5,7,8,9,11]:
  p=5877920 if cls==1 else u(1601376+4*(cls-2));name=text(u(p+40),u(p+44));classes[cls]=dict(starter=name,ability_pointer=abilities[name],hp_armor=[u(p+72),u(p+76)])
 for race in range(1,9):
  p=5874636 if race==1 else u(1601216+4*(race-2));name=text(u(p+24),u(p+28));ptr,count=u(p+16),u(p+20);races[race]=dict(id=name,ability_pointer=abilities[name],modifiers=[(read(ptr+8*j,1)[0],u(ptr+8*j+4))for j in range(count)])
 for j in range(12):
  p=5871348+152*j;zones.append(dict(id=text(u(p+8),u(p+12)),xyz=[u(p+104),u(p+108),u(p+116)]))
 literal={}
 for node in ast.parse((ROOT/'reconstruction/core_spec/initial_state139_data.py').read_text()).body:
  if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):literal[node.targets[0].id]=ast.literal_eval(node.value)
 assert literal['CLASS_STARTERS']=={k:(v['starter'],v['ability_pointer'],v['hp_armor'][0])for k,v in classes.items()}
 assert literal['RACIAL_ABILITIES']=={k:(v['id'],v['ability_pointer'],read(v['ability_pointer']+84,1)[0],u(v['ability_pointer']))for k,v in races.items()}
 assert literal['ZONE_ENTRIES']==tuple((v['id'],*v['xyz'])for v in zones)
 static=load(Path(c['data']['path']));assert sha(Path(c['data']['path']))==c['data']['sha256'];assert static['original_wasm_sha256']==SOURCE_SHA and static['functions']['1600']['body_sha256']==BODY
 db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');watfile=PROFILE/'official-0.139.0-full.wat';proof=[];texts={}
 with watfile.open('rb')as stream:
  for idx in[1600,29912,6786]:
   row=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());assert(row['body_start'],row['body_end'])==original['bodies'][idx];stream.seek(row['wat_start']);value=stream.read(row['wat_end']-row['wat_start']);assert value.startswith(f'  (func (;{idx};)'.encode());assert hashlib.sha256(value).hexdigest()==static['functions'][str(idx)]['wat_sha256'];texts[idx]=[x.strip()for x in value.decode().splitlines()];proof.append(dict(index=idx,body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),wat_sha256=hashlib.sha256(value).hexdigest(),**row))
 lines=texts[1600];guards=[]
 def guard(name,seq,idx=1600):
  t=texts[idx];sites=[j+1 for j in range(len(t)-len(seq)+1)if t[j:j+len(seq)]==seq];assert sites,name;guards.append(dict(name=name,index=idx,sites=sites,instructions=seq))
 guard('profile376copied_toSP104',['i32.const 104','i32.add','local.get 1','i32.const 376','memory.copy'])
 guard('full2592copied_fromSP88_after1542',['local.get 3','i32.const 88','i32.add','local.tee 1','call 1542','local.get 3','local.get 3','f32.load offset=1624','f32.store offset=1528','local.get 0','local.get 1','i32.const 2592','memory.copy'])
 guard('2944frame',['global.get 0','i32.const 2944','i32.sub'])
 guard('borrowedVplus8query',['local.get 3','local.get 2','i32.const 8','i32.add','local.get 8','f32.load offset=104','local.tee 29','local.get 8','f32.load offset=108','local.tee 30','call 29912'])
 guard('borrowedflag120readsheight116',['local.get 1','f32.load offset=108','local.set 4','i32.const 1','local.set 8'],29912)
 for literal in['i64.const 7520897724310334953','i64.const 793875393913628917','i64.const -338549647893938671','i64.const 6364136223846793005','i64.const 2259998930035483990','i64.const 5507651024068337109','i64.const 3398641427998916252','i64.const 6812164046247290893']:
  assert literal in lines
 assert lines.count('i32.rotr')==4 and 'i64.load offset=184'in lines
 calls=[dict(q)for q in db.execute('select callee,wat_offset,wat_line,instruction from calls where caller=1600')];assert calls==m['direct_calls']and len(calls)==48 and len({x['callee']for x in calls})==21
 cases=load(CASE/'inputs.json');expected=load(CASE/'expected.json');actual=[json.loads(x)for x in(CASE/'stdout.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==162
 checked=unknown=nonzero=packets=0;group=Counter();differences=[];masksha=None
 for i,(inp,e,a)in enumerate(zip(cases,expected,actual)):
  assert inp['id']==e['id']==a['id']==i and set(inp)=={'id','input','region_id'};assert inp['region_id']==zones[inp['input']['region_index']]['id']
  projection,known=reference(inp['input'],classes,races,zones);group[e['group']]+=1
  if projection!=e['expected']['projection']or projection!=a['projection']:differences.append(dict(id=i,kind='projection',fields=[k for k,v in projection.items()if v!=a['projection'].get(k)]))
  assert known==e['expected']['canonical_cells']and sum(x is not None for x in known)==502
  rawgame=bytes.fromhex(a['raw_game2592_hex']);assert len(rawgame)==2592 and bytes.fromhex(a['output_before_hex'])==bytes([0xa5])*2592
  for o,x in enumerate(known):
   if x is None:unknown+=1;nonzero+=rawgame[o]!=0
   else:checked+=1;assert rawgame[o]==x,(i,o,x,rawgame[o])
  pbefore=bytes.fromhex(a['profile376_before_hex']);pafter=bytes.fromhex(a['profile376_after_hex']);view=bytes.fromhex(a['query128_before_hex']);assert pbefore==pafter and len(pbefore)==376 and view==bytes.fromhex(a['query128_after_hex'])and len(view)==128
  profile=bytearray(376);struct.pack_into('<I',profile,156,4);profile[168:172]=pbefore[168:172];assert 0<u32(profile,168)<33554432;struct.pack_into('<I',profile,172,len(inp['region_id']));struct.pack_into('<Q',profile,176,int(inp['input']['object_id_u64']));struct.pack_into('<Q',profile,184,int(inp['input']['seed_u64']));profile[344]=inp['input']['class_byte'];profile[345]=inp['input']['race_byte'];assert bytes(profile)==pbefore
  v=bytearray([0x5a])*128;v[120]=1;struct.pack_into('<I',v,116,inp['input']['flat_height_bits']);struct.pack_into('<I',v,56,0xffffffff);struct.pack_into('<I',v,32,0xffffffff);assert bytes(v)==view
  owned=a['ownership'];assert owned['borrowed_query']==owned['game_query']==u32(rawgame,2348)and owned['Rc_owner_producer_executed']is False and owned['App_produced']is False;assert a['stack_after']==1048576 and a['host_calls']==0
  packets+=len(projection['movement_packets'])
 assert not differences and checked==81324 and unknown==338580 and nonzero==23706 and packets==40 and dict(group)==c['groups']
 assert runtime['fresh_instances']==runtime['full1600_calls']==runtime['completed_cases']==162 and runtime['stack_guards']==810 and runtime['actual_host_calls']==0 and runtime['peak_memory_bytes']==20709376
 assert not any(runtime[k]for k in['old_snapshot_loaded','App_produced','externref_forged','world_Rc_producer_executed','application_start_called','phase1_started','user_saves_accessed','network_used'])
 terminal=load(CASE/'process-terminal.json');assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<60
 #Independent stored pilot/prior-run provenance only;do notcount asnewcoverage.
 prior=[]
 for folder in['initial139-oracle-20261102T021030.924777Z','initial139-oracle-20261102T021049.780758Z']:
  p=ROOT/'evidence'/folder/'comparison.json';x=load(p);prior.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),cases=x['cases'],original_calls=x['original1600_calls'],not_added_to_final_coverage=True))
 assert [x['original_calls']for x in prior]==[3,162]
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('initial139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 result=dict(status='pass_fresh139_default_constructor_partial_projection_only',comparison_sha256=SHA,original_wasm_sha256=SOURCE_SHA,constructor_body_sha256=BODY,independently_recomputed_cases=162,independent_reference_mismatches=differences,known_bytes=checked,None_bytes=unknown,observed_nonzero_None_bytes=nonzero,complete226_packets=packets,
  independent_reference='Fresh139staticclass/raceslices + standardPCGxorshiftrotate + defaultlevel1binary32 expression;no author production import/call',stats139_dependency='Separate10569matrix and motion38_review independentreview;this reviewdefault-onlycalculation doesnot rereviewfullnonemptystats',
  stats139_independent_review_dependency=dict(report_path=str(STATS_REVIEW.relative_to(ROOT)),report_sha256=STATS_REVIEW_SHA,receipt_path=str(stats_receipt.relative_to(ROOT)),receipt_sha256=STATS_REVIEW_RECEIPT_SHA,format_only_refresh_no_new_original=True),
  source_files=17,production_sources=7,source_edges=25,all_source_snapshot_and_current_hashes_checked=True,source_closure_edges=c['source_import_edges'],body_signature=['7f7f7f',''],type_index=1,all_nonexport_sections_byte_identical=True,direct_call_sites=48,unique_direct_callees=21,static_functions=proof,static_guards=guards,
  initial_profile376_and_borrowed_query128_full_bytes_unchanged=True,outputA5poison_checked=True,stack_guards=810,stack_root_restored_everycase=True,denied_imports=882,actual_host_calls=0,author_owned_process=terminal,peak_memory_bytes=20709376,
  formal_original_calls=162,prior_experiments_not_added_to_formal=prior,total_author_research_original_calls=327,reviewer_author_model_executions=0,reviewer_author_checker_executions=0,reviewer_author_builder_executions=0,reviewer_original_executions=0,reviewer_native_executions=0,
  author_negative_model_guards=8,author_negative_guards_count_as_original=False,script_sha256=sha(Path(__file__)),review_parser_helper_sha256=sha(ROOT/'scripts/review_combat139.py'),seconds=time.monotonic()-began,
  limits=['Onlyexplicitzero376profileandfiniteborrowedflatquery;no naturalApp/profileorworldRcownerproducer','502/2592knownbytes;2090otherbytespercase remainNone,includingunmodeledaddresses/inactivepayload','No cached6786 or opening1108 execution;6786 WAT isstaticprovenance only;phase0notphase1','40packet226payloadsfullychecked;no networkserverdelivery or fullUI/App/BTreeheaplayoutaccepted','RNGallzero fallback staticallybound butnoforcedfallbackseedclaim','8storedmodelrejectionsnotrerun/countedasoriginal;no135/138acceptancetransfer','No full139game/save/win/nativeWindowsflowaccepted'])
 (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),cases=162,known=checked,unknown=unknown,packets=packets,mismatches=len(differences),seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
