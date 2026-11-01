#!/usr/bin/env python3
"""Read-only complete915 control-flow/producer inventory. No original execution."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import bisect,hashlib,json,re,sqlite3,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT=PROFILE/'official-0.135.1-full.wat'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
BODY915_SHA='7eec05b5e91cbcd797664a0854484e6db03129e9b7b8233e4465b07e9926b3d6'
FUNCTIONS=(915,910,63687,34693,1560,880,921,922,54811,29219,5736,914,1073,24296)


def sha(path):
 with path.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def clean(line):return re.sub(r'\(;.*?;\)','',line).strip()


def control_inventory(lines):
 stack=[];nodes={};branches=[];calls=[];memory=[]
 for i,line in enumerate(lines):
  text=clean(line);parts=text.split();op=parts[0]if parts else''
  if op in('block','loop','if'):
   nodes[i]=dict(line=i,kind=op,parent=stack[-1]if stack else None,children=[],else_line=None)
   if stack:nodes[stack[-1]]['children'].append(i)
   if op=='if':branches.append(dict(line=i,kind='if',control=i,context=list(stack),condition_window=[dict(line=j,text=lines[j].strip())for j in range(max(0,i-16),i)]))
   stack.append(i)
  elif op=='else':
   assert stack and nodes[stack[-1]]['kind']=='if';nodes[stack[-1]]['else_line']=i
  elif op=='end':
   assert stack;nodes[stack.pop()]['end_line']=i
  elif op in('br','br_if','br_table'):
   depths=list(map(int,parts[1:]));assert all(0<=n<len(stack)for n in depths)
   branches.append(dict(line=i,kind=op,depths=depths,target_control_lines=[stack[-n-1]for n in depths],context=list(stack),
    condition_window=[dict(line=j,text=lines[j].strip())for j in range(max(0,i-16),i)]))
  if op=='call':calls.append(dict(line=i,index=int(parts[1]),context=list(stack)))
  if '.load'in op or'.store'in op or op in('memory.copy','memory.fill'):
   m=re.search(r'offset=(\d+)',text)
   memory.append(dict(line=i,instruction=text,memarg_offset=int(m.group(1))if m else 0,context=list(stack),
    previous=[dict(line=j,text=lines[j].strip())for j in range(max(0,i-5),i)]))
 assert not stack and all('end_line'in n for n in nodes.values())
 for b in branches:
  if b['kind']=='if':b['then_range']=[b['line']+1,nodes[b['line']]['else_line']or nodes[b['line']]['end_line']]
  else:b['target_end_lines']=[nodes[n]['end_line']for n in b['target_control_lines']]
 return dict(control_nodes=list(nodes.values()),branches=branches,calls_lexical=calls,memory_operations=memory,
  counts=dict(Counter(clean(l).split()[0]for l in lines if clean(l))))


def main():
 assert sha(SOURCE)==SOURCE_SHA and sha(WAT)==WAT_SHA
 conn=sqlite3.connect('file:'+str(PROFILE/'index.sqlite')+'?mode=ro',uri=True)
 out=ROOT/'evidence'/('effect-system0135-static-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir()
 texts={};identities=[]
 with WAT.open('rb')as wat,SOURCE.open('rb')as binary:
  for index in FUNCTIONS:
   a,b,line,bodya,bodyb=conn.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end FROM functions WHERE idx=?',(index,)).fetchone()
   wat.seek(a);raw=wat.read(b-a);texts[index]=raw.decode().splitlines();(out/f'{index}.wat').write_bytes(raw)
   binary.seek(bodya);body=binary.read(bodyb-bodya);digest=hashlib.sha256(body).hexdigest()
   if index==915:assert digest==BODY915_SHA and len(body)==20852
   identities.append(dict(index=index,signature=texts[index][0].strip(),wat_line=line,wat_start=a,wat_end=b,wat_sha256=hashlib.sha256(raw).hexdigest(),
    body_start=bodya,body_end=bodyb,body_bytes=len(body),body_sha256=digest,
    direct_callers=[r[0]for r in conn.execute('SELECT DISTINCT caller FROM calls WHERE callee=? ORDER BY caller',(index,))],
    direct_callees=[r[0]for r in conn.execute('SELECT DISTINCT callee FROM calls WHERE caller=? ORDER BY callee',(index,))]))
 inv=control_inventory(texts[915]);assert len(texts[915])==9666 and inv['counts']['br_table']==10
 (out/'915-control-inventory.json').write_text(json.dumps(inv,indent=2)+'\n')
 direct_callee_ids=sorted({c['index']for c in inv['calls_lexical']});callee_identity=[]
 with WAT.open('rb')as wat,SOURCE.open('rb')as binary:
  for index in direct_callee_ids:
   a,b,line,bodya,bodyb=conn.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end FROM functions WHERE idx=?',(index,)).fetchone()
   wat.seek(a);signature=wat.readline().decode().strip();binary.seek(bodya);body=binary.read(bodyb-bodya)
   callee_identity.append(dict(index=index,signature=signature,body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),
    call_lines=[c['line']for c in inv['calls_lexical']if c['index']==index]))
 #Broad lexical scan is deliberately a candidate list, not a claim that every
 #large memarg denotes the game G. Other structs use the same numeric offsets.
 rows=conn.execute('SELECT idx,wat_line FROM functions ORDER BY wat_line').fetchall();starts=[r[1]for r in rows]
 pattern='offset=(1808|1812|1816|1820|1824|1828|2364)( |$)|i32.const (1808|1820)( |$)'
 result=subprocess.run(['rg','-n',pattern,str(WAT)],capture_output=True,text=True,check=True)
 candidates=defaultdict(list)
 for row in result.stdout.splitlines():
  line,text=row.split(':',1);line=int(line);index,start=rows[bisect.bisect_right(starts,line)-1]
  candidates[index].append(dict(global_wat_line=line,function_line=line-start,instruction=text.strip()))
 (out/'offset-scan-candidates.json').write_text(json.dumps(dict(note='Lexical candidates only; G provenance must be checked separately',functions=candidates),indent=2)+'\n')
 dinv=control_inventory(texts[910]);switch=next(b for b in dinv['branches']if b['line']==365)
 cases=[]
 for k,end in enumerate(switch['target_end_lines'][:-1],1):
  rawtags=[raw for raw in range(256)if(29 if raw<=2 else(raw-3)&255)==k]
  cases.append(dict(normalized_tag=k,raw_descriptor37_tags=rawtags,entry_line=end+1))
 sites=[]
 wanted={'call 63687','call 34693','f32.store offset=2364','i32.store offset=1816'}
 for i,line in enumerate(texts[910]):
  if clean(line)in wanted:
   entry=max((c['entry_line']for c in cases if c['entry_line']<=i),default=None)
   sites.append(dict(line=i,instruction=line.strip(),nearest_lexical_switch_entry=entry,
    candidate_normalized_tags=[c['normalized_tag']for c in cases if c['entry_line']==entry],
    candidate_raw_descriptor37_tags=[t for c in cases if c['entry_line']==entry for t in c['raw_descriptor37_tags']],
    window=[dict(line=j,text=texts[910][j].strip())for j in range(max(0,i-20),min(len(texts[910]),i+3))]))
 producer=dict(function=910,switch_line=365,normalization='rawDescriptor37<=2 ?29 :((rawDescriptor37-3)&255)',
  cases=cases,producer_sites=sites,scope_note='Nearest lexical case entry is a navigation hint, not a proof of all control guards or dynamic reachability',
  true_edges={'910':[63687,34693],'63687':'G1820/1824/1828 push56','34693':'G1808/1812/1816 push120','921':'dynamic44B NPC action queue→910','915':'due56 default→910'},
  exact_clock_site=dict(raw_descriptor37_tag=34,normalized_tag=31,line=1371),
  delayed_special_tags=[dict(raw_producer_tag=7,normalized=4,scheduled_tag49=35,push_line=5759),
   dict(raw_producer_tag=20,normalized=17,scheduled_tag49=36,push_line=3985),dict(raw_producer_tag=23,normalized=20,scheduled_tag49=37,push_line=2952)])
 (out/'910-producer-inventory.json').write_text(json.dumps(producer,indent=2)+'\n')
 report=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,full_wat_sha256=WAT_SHA,
  script_sha256=sha(Path(__file__)),functions=identities,direct_callee_identity=callee_identity,
  complete915=dict(lines=len(texts[915]),body_bytes=20852,body_sha256=BODY915_SHA,control_counts=inv['counts'],
   branches=len(inv['branches']),control_nodes=len(inv['control_nodes']),calls=len(inv['calls_lexical']),distinct_callees=len(direct_callee_ids),
   inventory='915-control-inventory.json',all_control_targets_resolved=True),
  global_inputs={'clock2352':'read at entry','2364':'positive due deadline→clear0,1644++,54811 message',
   '1820/1824/1828':'cap/pointer/length stride56 pending target/action records',
   '1808/1812/1816':'cap/pointer/length stride120 effect/projectile/geometry records',
   '1784/1788/1792':'ordinary424B entity vector','2348':'world height/navigation','1880/1884/1888':'16B physical message queue',
   '1892/1896/1900':'12B owned serialized payload/string queue','2582':'mode/owner routing with2528',
   '2587':'phase guard','387/2568':'incoming damage scaling/protection-related gates','1416/1420/1424':'playerXYZ',
   '2496/1428/1648/2500':'movement flags/heading/speed/previous-input clock prediction','1644':'player movement/action sequence',
   '2412':'unit movement sequence; delayed35 may increment','416..436':'player position/action state written by delayed36'},
  phases=[dict(lines=[0,73],name='positive-due2364',guard='2364>0 &&2364<=now',behavior='clear2364, increment1644,54811,append16B message'),
   dict(lines=[74,1246],name='pending56',guard='G1828>0',behavior='ordered due/owner test, delete56 via memory.copy;tag255 skip;tag35 movement;36 phase1 player relocation;37 aura removal;default910'),
   dict(lines=[1247,9655],name='effects120-entire-region',guard='G1816!=0 (br1252 targets block1248 end9655)',behavior='large whole region skipped only when actual120vector is empty'),
   dict(lines=[1253,1791],name='player-world-prediction-and-temporaries',guard='nonempty120',behavior='height/nav lookup, movement2496/heading/trig prediction and temporary vectors'),
   dict(lines=[1800,4475],name='record120-source-follow/shape/type',guard='nonempty120 per record',behavior='resolve sourceGUID24;mode-owner filtering;116 follow-unit;104+117 homing;40 shape/8 type collision;aggregate incoming or enqueue spawn/outgoing/aux effects'),
   dict(lines=[4476,5112],name='temporary-index/intersection-resolution',guard='temporary records',behavior='geometry overlap/shape tests and index selection; large formatting/allocation helpers also occur'),
   dict(lines=[5113,7369],name='visual-initialization-and-serialization',guard='record visualGUID32 sentinel-1 and temp updates',behavior='maycall2825,updates32,builds serialized current effect descriptors;all branches inventoried'),
   dict(lines=[7370,8553],name='ordered-expiry/delete-and-payload-emission',guard='temp removal indices/serialized output',behavior='reverse selected120 removals/memory.copy,170despawn plus12B serialized payload queue'),
   dict(lines=[8554,8595],name='incoming1073',guard='accumulatedlocal30>0',behavior='wave/protection-relatedfactor then1073;not cosmetic'),
   dict(lines=[8596,8856],name='player-action-message',guard='phase2587==1 &&local19',behavior='increment1644 andemit action/movement packet'),
   dict(lines=[8857,8924],name='deferred-spawn5736',guard='temporary16B descriptors',behavior='callsactual5736;may create entities andconsumeRNG'),
   dict(lines=[8925,9419],name='deferred-outgoing914',guard='temporary24B descriptors',behavior='spatial collect IDs→914 damage with literal school2,critical0/context0;death may consume RNG'),
   dict(lines=[9420,9630],name='deferred-per-unit-aux24296',guard='temporary16B descriptors',behavior='unit lookup/message and24296;semantic continuation stillunknown'),
   dict(lines=[9631,9665],name='temporary-free-and-return',guard='allocation flags',behavior='free owned temporary buffers;restore stack;allocationfailuretrap retained')],
  record56={'0':'targetGUID u64','8':'due=now+delay f32','12..51':'40B copied action descriptor','49':'descriptor+37 rawtag byte','52..55':'unwritten tail from63687'},
  record120={'0':'variant/tag u32','4..7':'unwritten by34693','8..23':'four-word type/state payload copied by34693','24':'sourceGUID u64','32':'visualGUID u64,maystart-1',
   '40/44/48':'shape tag and2geometry floats','52':'G2356-generated identifier','56/60/64':'XYZ','68':'angle','72':'starttime','76':'deadline','80':'player-attach window',
   '84':'spell/action id','88':'damage/magnitude','92/96/100':'aux deadlines/magnitudes;full variants not restored','104':'movement speed','108/112':'aux state/previous radius',
   '116/117/118':'independent gating bytes;names not yet established','119':'unwritten by34693'},
  constructor_proof=dict(function=1560,copy_line=2752,source_base='scratch+88',copied_bytes=2592,
   stores=[dict(line=858,scratch=1904,G=1816,value=0),dict(line=873,scratch=1896,G=1808,low_cap=0,high_ptr=8),
    dict(line=879,scratch=2452,G=2364,value=0),dict(line=882,scratch=1908,G=1820,low_cap=0,high_ptr=8),dict(line=885,scratch=1916,G=1828,value=0)],
   meaning='Initial empty vectors/deadline are explicit constructor writes, not an assumption about malloc. Their later persistence is NOT observed by current same-G projection.'),
  eight_seed_scope=dict(player='Mage/human fireball/perception;new flamestrike/blizzard/pyroblast per original unchangedpolicy',
   established_static='Complete922 has no910 edge; known common/racial/area player producers use other vectors.910 direct callers are only921,915,self.',
   expected_but_unproved='124 known melee definitions have prefix tag0; root AI validator limits current units, suggesting NPC action queue may stay empty. Existing receipts do NOT read1828/1816/2364, so actual persistence cannot be claimed.',
   next_required='Retain8actual seeds/actions. Add full915 between3757and921; capture actual2364andbothvectors before/afterevery producer and915, includingraw56/raw120/backing as applicable;no external zero/absence overwrite.'),
  status='static reconnaissance only; no executable915productionmodel or fresh915oracle coverage',original_executed=False,
  host_called=False,application_start_called=False,network_used=False,user_saves_accessed=False)
 (out/'effect-system135-static.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(directory=str(out),branches=len(inv['branches']),controls=len(inv['control_nodes']),calls=len(inv['calls_lexical']),
  distinct_callees=len(direct_callee_ids),scan_candidate_functions=len(candidates),report_sha256=sha(out/'effect-system135-static.json'))))


if __name__=='__main__':main()
