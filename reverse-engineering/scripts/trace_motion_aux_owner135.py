#!/usr/bin/env python3
"""Static135 auxiliary owner plus new model/historical460 header comparison.

No original, native, checker or builder executes. Static bytes and historical
captures are read only. New expected headers are frozen before capture replay.
"""
from collections import Counter
from dataclasses import replace
from pathlib import Path
import ast,hashlib,importlib.util,json,os,re,sqlite3,struct,sys,time,zlib
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from review_stats138 import digest,function_ids,static_image_reader
from review_opening_combat135 import JsonlReader
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from core_spec.initial_state135 import ConstructorInput135,initialize_empty_profile
from core_spec.motion_aux_owner135 import (MotionAuxOwner135,MotionAuxAdmission135,
 from_empty_profile1560_aux135,inherit_motion_aux135,UnknownMotionAuxOwner135,
 ADMITTED_DEFINITIONS135,EMPTY_SOURCE_COUNTS135,TAIL_EVENTS135,FATAL_TAIL_EVENTS135)
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
CAPTURE=ROOT/'evidence/opening-combat0135-oracle-20261101T232156.684647Z'
CAPTURE_SHA='521db52b9d97637212460083a7ea88b9038d63871536d6635edc21645e0bd622'
FUNCTIONS=(1560,1089,10146,5745,1680,984,1072,1076,922,2244,914,1073,2088,1512,1202,
 916,975,1754,3757,915,38007,2602,921,2862,2573,947,2376,49037,17119,17217,16340,65336,36294,968,2328,4600)
COUNT_NAMES={604:'timed12',652:'active84',1804:'areas',1852:'hits112',1816:'effects120',1828:'delayed56',2116:'companions'}
STAGE_TARGETS=dict(player=2088,extra=916,owned_effects=975,hits=1754,area=3757,effects=915,deadline=38007,secondary=2602,ai=921,collect=2862,claims=2573,spawn=947,special=2376,terminal=49037,select=1072,motion=2328)
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def load(path):return json.loads(path.read_text())
def source_files():
 names=set(production_sources135(ROOT,'core_spec.motion_aux_owner135'))
 names.update('scripts/'+s for s in('trace_motion_aux_owner135.py','review_stats138.py','review_opening_combat135.py','production_closure135.py','source_closure137.py'))
 while True:
  try:return sorted(names),verify_local_source_closure(sorted(names))
  except AssertionError as error:
   pair=error.args[0]
   if not isinstance(pair,tuple)or len(pair)!=2 or not(ROOT/pair[1]).is_file()or pair[1]in names:raise
   names.add(pair[1])
def static(out):
 assert digest(SOURCE)==SOURCE_SHA;binary=SOURCE.read_bytes();functions=function_ids(binary,FUNCTIONS);read=static_image_reader(binary);texts={};raw_defs={};total=0
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  for index in FUNCTIONS:
   row=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone();a,b,bs,be=row;assert(bs,be)==(functions[index]['body_start'],functions[index]['body_end'])
   wat.seek(a);raw=wat.read(b-a);total+=len(raw);p=out/'static'/f'{index}.wat';p.parent.mkdir(exist_ok=True);p.write_bytes(raw);lines=[line.strip()for line in raw.decode().splitlines()];texts[index]=lines
   functions[index].update(wat_start=a,wat_end=b,wat_sha256=hashlib.sha256(raw).hexdigest(),function_lines=len(lines),direct_callees=sorted({v[0]for v in db.execute('select callee from calls where caller=?',(index,))}))
  callers={str(index):[row[0]for row in db.execute('select distinct caller from calls where callee=? order by caller',(index,))]for index in(1680,5745,10146)}
 assert callers=={'1680':[984,5745,10146],'5745':[916,984,1089,10146],'10146':[1089]}
 for pointer,(name,execution,effect,h)in ADMITTED_DEFINITIONS135.items():
  raw=read(pointer,88);assert len(raw)==88 and hashlib.sha256(raw).hexdigest()==h and raw[84]==execution and int.from_bytes(raw[:4],'little')==effect
  p,n=struct.unpack_from('<2I',raw,12);assert read(p,n).decode()==name;raw_defs[pointer]=raw.hex()
 def window(index,a,b):return [dict(line=n,instruction=texts[index][n-1])for n in range(a,b+1)]
 assert texts[1560][1362]=='i64.store offset=748 align=4'and texts[1560][1365]=='i64.store offset=740 align=4'
 assert texts[1560][2742]=='i32.add'and texts[1560][2743]=='local.tee 1'and texts[1560][2752]=='memory.copy'
 assert texts[1680][1986]=='call 65336'and texts[1680][2068]=='i32.store offset=664'
 assert texts[984][8]=='i32.load offset=2056'and texts[984][22].startswith('br_if 2 ')
 assert all(not re.search(r'offset=(656|660|664)(?:\s|$)',s)for s in texts[1072])
 assert all(not re.search(r'offset=(656|660|664)(?:\s|$)',s)for s in texts[4600])
 assert not any(re.search(r'\bload\S* offset=416(?:\s|$)',s)for s in texts[915])
 # These bodies have no direct accesses to this header; callees retain their
 # own explicit predicates below. This is not a generic alias-analysis claim.
 no_direct={str(i):True for i in STAGE_TARGETS.values()if all(not re.search(r'offset=(656|660|664)(?:\s|$)',s)for s in texts[i])}
 rules=[
  dict(event='constructor1560',condition='independent empty-profile1560',write_set='scratch740 i64=0 covers G652 and G656; scratch748 i64=8 sets G660ptr8/G664count0; Game copied from scratch+88'),
  dict(event='opening1089',condition='flag2576=0, item2032count=0',write_set='direct5745 summon path is skipped by flag2576;10146 first output and second loop are item-count gated; header inherited'),
  dict(event='player2088/1076/922',condition='exact declared cleave exec5/effect0;thunder exec2/effect1;demo exec2/effect11;battle/perception exec9/effect8;empty modifiers/items',write_set='immediate914 and2244 or live32/1512/1202 paths; no selected summon dispatch;984 returns at emptyG2056'),
  dict(event='extra916',condition='G604timed12=0,G652active84=0,and auxiliaryG664=0',write_set='timed loop/expiry,active84 block,and all auxiliary loops skipped;5745 cannot execute'),
  dict(event='owned_effects975',condition='all actual owned definition byte84 in2,5,9 rather than11',write_set='975 full early return before class resource work'),
  dict(event='hits1754/area3757/effects915/deadline38007/secondary2602/claims2573',condition='hits1852/areas1804/effects1816/delayed1828/deadline1840/secondary1864/claims2116 all0',write_set='idle queue branches no auxiliary spawn; secondaryG1856 is separate storage.915 has no416 load; currentheadless4160 restriction is a separate composition boundary, not an originalaux producer predicate'),
  dict(event='ai921/collect2862/spawn947/special2376/terminal49037',condition='only already admitted ordinary/guardian AI, XP/coin/resource consumers, ordinary/special unit424 and pickup56 producers;emptyitems/modifiers;no generic network or unknown ability events',write_set='restored units/pickups/live/stats/notifications and terminal movement consumers;984 emptyproc gate excludes1680. Unsupported producer remains boundary'),
  dict(event='selection1072',condition='actualkind0 skill/gold,selected/current definitions remain the five fixed admitted declarations;items/modifiers still empty',write_set='owned80/stat/XP/resume-live1020 and shared existing consumers;1072 and4600 have no direct aux header access or direct1680/5745/10146. Existingemptyowner is inherited; no claim1072 directly calls17119'),
  dict(event='localmotion2328/correction199',condition='admitted local default968 route;exclude2080remote switch/mode1forward',write_set='player scalar/correction state and packets;no directauxheaderaccess; no1680/5745/10146 calls'),
  dict(event='fatal same-frame remaining tail',condition='before=afterphase4 only collect/claims/spawn/special/terminal;same guarded sources',write_set='2573 exits unlessphase1;49037 requiresphase1;2862/947/2376 admitted producers retainaux and do not restart921planning. No dynamicphase4case in historical460'),
 ]
 windows={'1560_constructor_aux':window(1560,1358,1369),'1560_Game_copy_from_scratch88':window(1560,2740,2753),'1680_append_aux':window(1680,1974,2069),'984_empty_modifiers':window(984,8,25),'916_source_gates':window(916,8,25)+window(916,212,224),'10146_items_first':window(10146,8,16),'10146_items_second':window(10146,441,449),'1089_flag_skip_direct_summon':window(1089,1885,1897)+window(1089,2471,2491),'975_owned_execution11_gate':window(975,1,100),'2573_phase1_only':window(2573,8,18),'49037_phase1_only':window(49037,8,22)}
 proof=dict(original_sha256=SOURCE_SHA,index_seek_only=True,full_WAT_read=False,wat_read_bytes=total,original_executions=0,functions={str(k):v for k,v in functions.items()},summon_direct_callers=callers,
  constructor=dict(Game_base='scratch+88',capacity656=0,pointer660=8,count664=0,pointer_is_aligned_dangling_sentinel=True),
  selected_definitions={str(p):dict(name=d[0],execution=d[1],effect=d[2],raw88_sha256=d[3],raw88_hex=raw_defs[p])for p,d in ADMITTED_DEFINITIONS135.items()},
  stage_targets=STAGE_TARGETS,no_direct_header_access=no_direct,admitted_write_contracts=rules,windows=windows,
  limitations=['Summon1680 and all indexed direct callers are explicit. This is bounded admitted-path reasoning, not a complete program-wide alias/network-deserialization proof.','Empty constructor and no-admitted-producer reasoning establish expectations; original snapshot zero is never a model input.','Nonempty auxiliary producers, modifier proc sources, item summons, active timed/extra casting and unsupported declarations remain unknown.'])
 save(out/'static-proof.json',proof);return raw_defs,proof
def context(expected,event,raw_defs,selected_kind=None):
 p=expected['projection'];v=expected['vectors'];pointers=[int.from_bytes(bytes.fromhex(h)[:4],'little')for h in p['owned_records_hex']]
 pointers.append(int.from_bytes(bytes.fromhex(p['racial_record_hex'])[:4],'little'))
 # 2032/2056 have empty constructor owners and skill-only1072 transitions.
 # 1840/1864 have empty constructor owners and no selected producer. They
 # are not looked up in actualGame, including when oldprojection omitted them.
 counts=tuple((offset,v[name]['count']if(offset in COUNT_NAMES and(name:=COUNT_NAMES[offset]))else 0)for offset in EMPTY_SOURCE_COUNTS135)
 return MotionAuxAdmission135(event,p['phase2587'],p['mode2582'],p['tail_flags']['protection2576'],1,1,tuple((pointer,raw_defs[pointer])for pointer in pointers),counts,selected_kind)
def main():
 assert len(sys.argv)==2 and os.getpid()==os.getpgrp(),'Owned bounded launcher required';out=Path(sys.argv[1]).resolve();assert out.parent==ROOT/'evidence'and out.name.startswith('motion-aux-owner135-')and out.is_dir();began=time.monotonic()
 files,edges=source_files();before={n:digest(ROOT/n)for n in files}
 for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert digest(p)==h
 report=load(CAPTURE/'comparison.json');fixture=load(CAPTURE/'fixtures.json');assert digest(CAPTURE/'comparison.json')==CAPTURE_SHA and digest(CAPTURE/'fixtures.json')==report['fixtures_sha256']
 assert fixture['input']['class_byte']==fixture['input']['race_byte']==1 and fixture['input']['region_index']==0 and fixture['input']['app_lcg_seed_u64']=='0'
 raw_defs,proof=static(out)
 initial=initialize_empty_profile(ConstructorInput135(1,1,0,0,42,0));owner=from_empty_profile1560_aux135(initial);assert(owner.capacity656,owner.pointer660,owner.count664)==(0,8,0)
 expected_reader=JsonlReader(CAPTURE/'stage-expectations.jsonl.gz',True,1073741824);iterator=iter(expected_reader);opening=next(iterator);assert opening['record_kind']=='opening';old=opening['expected'];opening_before=replace(context(old,'opening1089',raw_defs),phase2587=0);assert inherit_motion_aux135(owner,opening_before,context(old,'opening1089',raw_defs))is owner
 predictions=[dict(record_kind='constructor',kind='constructor',header=[0,8,0],source_counts=dict.fromkeys(EMPTY_SOURCE_COUNTS135,0)),dict(record_kind='opening',kind='opening',header=[0,8,0],source_counts=dict(context(old,'opening1089',raw_defs).source_counts))];events=Counter(opening1089=1);stage_index=0;skills=set();phase_counts=Counter();model_transitions=1
 for row in iterator:
  assert row['record_kind']=='stage'and row['stage_index']==stage_index;new=row['expected'];kind=row['kind'];event='selection1072'if kind=='select'else'motion2328'if kind=='motion'else kind
  selected=old['projection']['selection_kind2585']if kind=='select'else None
  pre=context(old,event,raw_defs,selected);post=context(new,event,raw_defs,selected);assert inherit_motion_aux135(owner,pre,post)is owner
  for pointer,_ in post.definitions88:skills.add(ADMITTED_DEFINITIONS135[pointer][0])
  predictions.append(dict(record_kind='stage',stage_index=stage_index,action_index=row['action_index'],kind=kind,header=[owner.capacity656,owner.pointer660,owner.count664],event=event,source_counts=dict(post.source_counts),phase2587=post.phase2587));events[event]+=1;phase_counts[post.phase2587]+=1;stage_index+=1;model_transitions+=1;old=new
 assert stage_index==6488 and expected_reader.file_digest.hexdigest()==report['expectations_sha256'] and expected_reader.bytes==report['expected_uncompressed_bytes']
 save(out/'new-expectations.json',predictions);expected_sha=digest(out/'new-expectations.json');save(out/'prepared.json',dict(new_model_expectations_before_historical_CAS_read=True,author_blinded=False,original_calls=0,new_original_frames=0,expectations_sha256=expected_sha,model_transitions=model_transitions,constructor_model_calls=1,context_unprojected_counts='2032/2056 inherited empty constructor plus skill-only selection;1840/1864 empty constructor plus no admitted producer;never actual Game read'))
 # Negative properties are separate model checks, not extra original cases.
 rejected=[];base=context(opening['expected'],'player',raw_defs)
 for offset in EMPTY_SOURCE_COUNTS135:
  try:replace(base,source_counts=tuple((o,1 if o==offset else n)for o,n in base.source_counts))
  except UnknownMotionAuxOwner135:rejected.append('source_'+str(offset))
  else:raise AssertionError('Nonempty source admitted')
 try:inherit_motion_aux135(MotionAuxOwner135(1,None,(tuple([None]*112),),1),base,base)
 except UnknownMotionAuxOwner135:rejected.append('nonempty_auxiliary_owner')
 else:raise AssertionError('Nonempty auxiliary owner erased')
 try:inherit_motion_aux135(None,base,base)
 except TypeError:rejected.append('missing_owner')
 else:raise AssertionError('Missing owner invented')
 for event in FATAL_TAIL_EVENTS135:
  phase4=replace(base,event=event,phase2587=4);assert inherit_motion_aux135(owner,phase4,phase4)is owner
 for event in('player','ai','extra','effects','motion2328'):
  phase4=replace(base,event=event,phase2587=4)
  try:inherit_motion_aux135(owner,phase4,phase4)
  except UnknownMotionAuxOwner135:rejected.append('reject_phase4_replanning_'+event)
  else:raise AssertionError('Fatal phase restarted earlier scheduling')
 try:replace(base,phase2587=True)
 except ValueError:rejected.append('reject_bool_phase')
 else:raise AssertionError('Boolean phase admitted')
 save(out/'model-only-rejections.json',rejected)
 # Replay all original logical CAS records; no original data feeds the model.
 codec=CAPTURE/'source-snapshot/scripts/opening_combat135_cas.py';assert digest(codec)==report['source_sha256_before']['scripts/opening_combat135_cas.py'];private=out/'frozen_capture_transport.py';private.write_bytes(codec.read_bytes());spec=importlib.util.spec_from_file_location('aux_owner_frozen_capture_transport',private);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);decoder=transport.CaptureCAS135(CAPTURE)
 compressed=(CAPTURE/'results.cas.jsonl.gz').read_bytes();inflate=zlib.decompressobj(31);index=inflate.decompress(compressed,33554433);assert inflate.eof and not inflate.unused_data and not inflate.unconsumed_tail and len(index)<=33554432
 expected=iter(predictions);counts=Counter();differences=[];observed_headers=Counter();header_rows=out/'header-comparisons.jsonl'
 with header_rows.open('w')as stream:
  for n,line in enumerate(index.splitlines(keepends=True)):
   entry=decoder.decode_line(line);kind=entry['record_kind']
   if kind not in('constructor','opening','stage'):continue
   prediction=next(expected);assert kind==prediction['record_kind']
   if kind=='stage':assert entry['stage_index']==prediction['stage_index']and entry['kind']==prediction['kind']and entry['action_index']==prediction['action_index']
   raw=bytes.fromhex(entry['raw_game2592_hex']);actual=list(struct.unpack_from('<3I',raw,656));observed_headers[tuple(actual)]+=1
   if actual!=prediction['header']:differences.append(dict(record=n,kind=kind,stage_index=entry.get('stage_index'),expected=prediction['header'],actual=actual))
   for offset,value in prediction['source_counts'].items():
    observed_count=struct.unpack_from('<I',raw,int(offset))[0]
    if observed_count!=value:differences.append(dict(record=n,kind=kind,stage_index=entry.get('stage_index'),source_count=int(offset),expected=value,actual=observed_count))
    counts['source_count_guard_words_compared']+=1
   stream.write(json.dumps(dict(record_kind=kind,stage_index=entry.get('stage_index'),kind=entry.get('kind',kind),expected=prediction['header'],actual=actual),separators=(',',':'))+'\n');counts['header_snapshots']+=1;counts['header_words_compared']+=3;counts['header_bytes_compared']+=12
   if n%1000==0:print(json.dumps(dict(progress_records=n,compared=counts['header_snapshots'],seconds=round(time.monotonic()-began,2))),flush=True)
 assert next(expected,None)is None and counts['header_snapshots']==6490
 cas=decoder.finish(report['runtime']['capture_cas']);assert cas['records']==6952 and cas['logical_bytes']==2139516743
 assert expected_sha==digest(out/'new-expectations.json')and before=={n:digest(ROOT/n)for n in files}and digest(SOURCE)==SOURCE_SHA
 result=dict(status='scoped_auxiliary_owner_historical_match'if not differences else'differences',version='0.135.1',actual_build='90898d5e3',new_original_calls=0,new_original_frames=0,new_model_transitions=model_transitions,new_constructor_model_calls=1,
  historical_controlled_frames=460,historical_stage_records=6488,differences=len(differences),difference_rows=differences[:100],counts=dict(counts),observed_headers=[dict(header=list(h),snapshots=n)for h,n in sorted(observed_headers.items())],
  events=dict(events),observed_admitted_skills=sorted(skills),all_five_static_admitted_declarations=True,phase_counts=dict(phase_counts),
  static_proof_sha256=digest(out/'static-proof.json'),constructor_owner_expected=[0,8,0],same_owner_identity_retained=True,nonempty_aux_producer_restored=False,
  source_sha256_before=before,source_sha256_after=before,source_files=len(files),source_import_edges=edges,
  capture=str(CAPTURE.relative_to(ROOT)),capture_sha256=CAPTURE_SHA,original_sha256=SOURCE_SHA,auxiliary_owner_module_absent_historical_model=True,
  expected_reader=expected_reader.receipt(),capture_CAS_full_finish=cas,negative_model_checks=len(rejected),fatal_phase4_inheritance_model_only_checks=len(FATAL_TAIL_EVENTS135),
  artifact_sha256={n:digest(out/n)for n in('new-expectations.json','prepared.json','static-proof.json','model-only-rejections.json','header-comparisons.jsonl','frozen_capture_transport.py')},
  elapsed_seconds=round(time.monotonic()-began,3),limitations=[
   'New auxiliary owner module was absent from the historical117-source model; this is a new spec/model compared to historical controlled460 raw Game, not new original calls/frames.',
   'The original headers are observations used only after model predictions were frozen; zero headers are never model inputs or proof of a constructor.',
   'Historical460 selects only the declarations seen in observed_admitted_skills. All five declarations and their producer exclusion are static; unseen skill configurations are not added original cases.',
   'Phase4 continuation inheritance has static rules plus model-only checks for five remaining tail events. Historical460 contains only phases1/2 and adds no originalfatal acceptance.',
   '2032/2056/1840/1864 empty count witnesses use explicit constructor/no-admitted-producer reasoning because old stage projection omitted those owners; they are not copied from actual.',
   'Nonempty summon1680/item/modifier/timed/extra sources, remote/network replacement, unsupported abilities and general alias analysis remain unresolved. Nonempty data is refused rather than cleared.',
   'This owner does not replace G1856 secondary areas or complete gameplay/fatal integration. The empty constructor plus admitted source closure is the declared scope.'
  ])
 save(out/'comparison.json',result);print(json.dumps(dict(status=result['status'],evidence=str(out.relative_to(ROOT)),comparison_sha256=digest(out/'comparison.json'),differences=len(differences),counts=dict(counts),events=dict(events),sources=len(files),edges=len(edges),skills=sorted(skills),seconds=result['elapsed_seconds'])),flush=True)
 if differences:raise SystemExit(1)
if __name__=='__main__':main()
