#!/usr/bin/env python3
"""New counter spec against immutable moving460 evidence; no model/target runs.

Death expectations are independently accumulated from a separately frozen model
event trace. Level/earned expectations come from historical independent owners.
Boss/guardian/chest projections remain explicitly unvalidated running owners.
Every CAS logical record/blob occurrence is finished before reporting results.
"""
from pathlib import Path
from collections import Counter
import ast,hashlib,importlib.util,json,os,sqlite3,struct,sys,time,zlib
sys.dont_write_bytecode=True
from review_stats138 import digest,function_ids,process_missing
from review_opening_combat135 import JsonlReader
ROOT=Path(__file__).resolve().parents[1]
CAPTURE=ROOT/'evidence/opening-combat0135-oracle-20261101T232156.684647Z'
TRACE=ROOT/'evidence/run-summary135-model-events-20261102T001522.269306Z/trace.json'
STATIC=ROOT/'evidence/fatal-dependencies135-static-20261102T001521.877775Z/proof.json'
CAPTURE_SHA='521db52b9d97637212460083a7ea88b9038d63871536d6635edc21645e0bd622'
TRACE_SHA='703e0069f2c835a00e7f8c0569fe41e1990a156df5f10d7ec48ab8b4682ce0ad'
STATIC_SHA='b237777fcf3098aefe496a38f11b9694c6682c4926533bcad1c21e5811a4ceb1'
COUNTERS=(1432,1084,1088,1092,1096,1100,1104)
UNRESTORED=(1092,1096,1104)
def load(path):return json.loads(Path(path).read_text())
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def word(raw,o):return struct.unpack_from('<I',raw,o)[0]
def unit_record(snapshot,guid):
 v=snapshot['vectors']['units']
 for text in v['storage'][:v['count']]:
  if int.from_bytes(bytes.fromhex(text[224:240]),'little')==guid:return bytes.fromhex(text)
 raise AssertionError(('Event target missing from original source',guid))
def main():
 began=time.monotonic();assert len(sys.argv)==2 and os.getpid()==os.getpgrp(),'Owned reviewer launcher required';out=Path(sys.argv[1]).resolve();assert out.parent==ROOT/'evidence'and out.name.startswith('run-summary135-historical-review-')and out.is_dir()
 report=load(CAPTURE/'comparison.json');trace=load(TRACE);static=load(STATIC)
 assert digest(CAPTURE/'comparison.json')==CAPTURE_SHA and digest(TRACE)==TRACE_SHA and digest(STATIC)==STATIC_SHA
 assert report['differences']==0 and report['independent_frames']==460 and report['compared_stages']==6488 and report['capture_format']=='cas'
 assert report['source_sha256_before']==report['source_sha256_after']and len(report['source_sha256_before'])==117
 old_sources=report['source_sha256_before'];old=CAPTURE/'source-snapshot'
 for name,h in old_sources.items():assert digest(old/name)==h,name
 assert 'reconstruction/core_spec/run_summary135.py'not in old_sources
 assert trace['kind']=='pure_model_event_trace_not_original_differential'and trace['original_calls']==trace['native_executions']==0 and trace['completed_frames']==920 and trace['failing_frame']==921 and trace['source_unchanged']and trace['frozen_model_was_not_fed_new_owners']
 common=set(old_sources)&set(trace['source_sha256']);assert len(common)==102 and all(old_sources[n]==trace['source_sha256'][n]for n in common)
 drift={};trace_provenance={}
 for name,h in trace['source_sha256'].items():
  historical=old/name;current=ROOT/name
  candidate=historical if historical.is_file()and digest(historical)==h else current
  assert candidate.is_file()and digest(candidate)==h,('Missing exact trace source',name)
  if current.is_file()and digest(current)!=h:drift[name]=dict(trace_sha256=h,current_sha256=digest(current))
  target=out/'trace-source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(candidate.read_bytes());trace_provenance[name]=dict(sha256=h,source='moving460_frozen_source'if candidate==historical else'current_exact_trace_source')
 assert trace['source_sha256']['reconstruction/core_spec/run_summary135.py']=='71ee8897fa52669193dacd14de08bb53f2fbf987a9470516a4a455e27419f0d2'
 # New source is read as data only. Its running counters are not imported.
 owner=(out/'trace-source-snapshot/reconstruction/core_spec/run_summary135.py').read_text();probe=(out/'trace-source-snapshot/scripts/probe_run_summary135.py').read_text()
 assert 'rank & 1'in owner and 'return old_death(cast, damage, context, binding)'in probe and 'opening-combat0135-oracle'not in probe
 assert '(target.kind_40, target.kind_64, target.elite_244) != (-1, -1, -1)'in owner
 raw=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes();assert hashlib.sha256(raw).hexdigest()==report['original_sha256']=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
 targets={1560,914,20660,28796};ids=function_ids(raw,targets)
 profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';extra={}
 with sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
  db.row_factory=sqlite3.Row
  with(profile/'official-0.135.1-full.wat').open('rb')as wat:
   for i in targets:
    entry=static['functions'][str(i)];assert entry['body_sha256']==ids[i]['body_sha256']
    row=dict(db.execute('select * from functions where idx=?',(i,)).fetchone());assert row['body_start']==ids[i]['body_start']and row['body_end']==ids[i]['body_end'];wat.seek(row['wat_start']);text=wat.read(row['wat_end']-row['wat_start']);assert hashlib.sha256(text).hexdigest()==entry['wat_sha256'];lines=[x.strip()for x in text.decode().splitlines()]
    for window in entry['windows'].values():assert all(lines[x['line']-1]==x['instruction']for x in window)
    if i==914:
     extra['914_kills_elites']=lines[5730:5747];extra['914_boss_gate']=lines[6819:6823];extra['914_guardian_gate']=lines[7257:7263]
   for i in(2862,38321):
    row=dict(db.execute('select * from functions where idx=?',(i,)).fetchone());wat.seek(row['wat_start']);text=wat.read(row['wat_end']-row['wat_start']);lines=[x.strip()for x in text.decode().splitlines()]
    at=next(j for j,x in enumerate(lines)if x=='call 20660');extra[str(i)+'_chest_call_window']=lines[max(0,at-24):at+8]
  assert {r[0]for r in db.execute('select caller from calls where callee=20660')}=={2862,38321}
 dump(out/'counter-static-provenance.json',dict(original_identities=ids,source_static_proof=str(STATIC.relative_to(ROOT)),source_static_sha256=STATIC_SHA,extra_windows=extra,contract={'1084':'914 every accepted new death increments, including special branches','1088':'same death increments iff rawU416 lowbit','1096':'later914 boss-definition pointer branch (U244 active, U256 pointer);not ordinary adapter','1092':'later914 U64 guardian-kind branch;not ordinary adapter','1100':'28796 adds awarded collected gold, separate from available1456','1104':'20660 successful u32 available1456>=cost2452 spend increments; also2380 pending chest selection; not counted from pickup/entity population','20660_callers':['2862 nearbykind2 and2571 guard','38321 interaction distance<=10 path']}))
 del raw
 for name,key in(('inputs.json','inputs_sha256'),('fixtures.json','fixtures_sha256'),('stage-expectations.jsonl.gz','expectations_sha256'),('results.cas.jsonl.gz','original_results_sha256')):assert digest(CAPTURE/name)==report[key]
 fixture=load(CAPTURE/'fixtures.json');inputs=load(CAPTURE/'inputs.json');assert inputs==[{k:fixture[k]for k in('id','input','actions')}]
 declared_input=inputs[0]['input'];assert declared_input['class_byte']==trace['input']['class_byte']==1 and declared_input['race_byte']==trace['input']['race_byte']==1 and declared_input['region_index']==trace['input']['region_index']==0 and int(declared_input['app_lcg_seed_u64'])==trace['input']['app_lcg_seed_u64']==0 and int(declared_input['object_id_u64'])==trace['input']['object_id_u64']==42
 assert Counter(a['kind']for a in fixture['actions'])==dict(controlled_tail_frame=460,motion=44,select=4)
 codec=old/'scripts/opening_combat135_cas.py';assert digest(codec)==old_sources['scripts/opening_combat135_cas.py'];private=out/'frozen_capture_transport.py';private.write_bytes(codec.read_bytes());spec=importlib.util.spec_from_file_location('frozen_counter_audit_transport',private);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);decoder=transport.CaptureCAS135(CAPTURE)
 compressed=(CAPTURE/'results.cas.jsonl.gz').read_bytes();inflate=zlib.decompressobj(31);index=inflate.decompress(compressed,33554433);assert inflate.eof and not inflate.unused_data and not inflate.unconsumed_tail and len(index)<=33554432
 expected_reader=JsonlReader(CAPTURE/'stage-expectations.jsonl.gz',True,1073741824);expected=iter(expected_reader);opening=next(expected);assert opening['record_kind']=='opening'
 events=trace['accepted_death_events'];assert len(events)==109 and all(e['stage']=='owned'and e['applied']and e['dead']for e in events)
 event_groups={};total_kills=total_elites=0
 for event in events:
  total_kills=(total_kills+1)&0xffffffff;total_elites=(total_elites+(event['rawU416']&1))&0xffffffff
  assert event['counter_after']==dict(kills1084=total_kills,elites1088=total_elites,guardians1092=0,bosses1096=0,chests1104=0)
  if event['frame']<=460:event_groups.setdefault((event['frame']-1,'player'),[]).append(event)
 assert sum(map(len,event_groups.values()))==38 and total_kills==trace['run_summary']['kills1084']==109
 counts=Counter();changes=[];differences=[];unrestored_nonzero=[];rows_path=out/'stage-counter-comparison.jsonl';previous=None;previous_observed=None;kills=elites=0;consumed=0;last_projection=None;observed_sets={o:set()for o in COUNTERS};stage_index=0
 with rows_path.open('w')as rows:
  for n,line in enumerate(index.splitlines(keepends=True)):
   entry=decoder.decode_line(line);kind=entry['record_kind'];assert entry['id']==0
   if kind not in('constructor','opening','stage'):continue
   if kind=='stage':
    want=next(expected);assert want['record_kind']=='stage'and want['stage_index']==entry['stage_index']==stage_index and want['kind']==entry['kind']and want['action_index']==entry['action_index'];projection=want['expected']['projection'];stage_index+=1
   elif kind=='opening':projection=opening['expected']['projection']
   else:projection=dict(progression=dict(level=1),earned=0)
   game=bytes.fromhex(entry['raw_game2592_hex']);assert len(game)==2592;observed={str(o):word(game,o)for o in COUNTERS};counts['raw_Game_bytes_bound']+=len(game)
   added=event_groups.get((entry.get('frame'),entry.get('kind')),[])if kind=='stage'else[]
   for event in added:
    assert previous is not None and event['now_bits']==word(game,2352);guid=int(event['guid']);before=unit_record(previous,guid);after=unit_record(entry,guid)
    assert word(before,0)==0 and word(after,0)==1 and all(word(before,o)==word(after,o)==0xffffffff for o in(40,64,244))and after[416]==before[416]==event['rawU416']and word(after,284)==event['definition_pointer']
    kills=(kills+1)&0xffffffff;elites=(elites+(event['rawU416']&1))&0xffffffff;consumed+=1;counts['original_marker_and_classification_event_matches']+=1
   declared={'1432':projection['progression']['level'],'1084':kills,'1088':elites,'1100':projection['earned']}
   for key,value in declared.items():
    if observed[key]!=value:differences.append(dict(stage_index=entry.get('stage_index'),frame=entry.get('frame'),kind=entry.get('kind',kind),offset=int(key),expected=value,actual=observed[key]))
    counts['declared_counter_values_compared']+=1
   if kind=='constructor':assert observed=={'1432':1,'1084':0,'1088':0,'1092':0,'1096':0,'1100':0,'1104':0};counts['constructor_counter_values_verified']+=7
   for offset in COUNTERS:observed_sets[offset].add(observed[str(offset)])
   if previous_observed is not None:
    delta={key:[previous_observed[key],value]for key,value in observed.items()if previous_observed[key]!=value}
    if delta:changes.append(dict(record_index=n,stage_index=entry.get('stage_index'),frame=entry.get('frame'),kind=entry.get('kind',kind),changes=delta))
   for offset in UNRESTORED:
    if observed[str(offset)]!=0:unrestored_nonzero.append(dict(stage_index=entry.get('stage_index'),frame=entry.get('frame'),kind=entry.get('kind',kind),offset=offset,observed=observed[str(offset)],ordinary_only_owner=0))
   row=dict(record_kind=kind,stage_index=entry.get('stage_index'),controller_frame=entry.get('frame'),stage=entry.get('kind',kind),declared_expected=declared,original_observed=observed,unrestored_running_owners=[1092,1096,1104],ordinary_slice_projection={'1092':0,'1096':0,'1104':0},model_death_events_applied=len(added));rows.write(json.dumps(row,separators=(',',':'))+'\n')
   previous=entry;previous_observed=observed;last_projection=projection;counts['counter_snapshots']+=1
   if n%500==0:print(json.dumps(dict(progress_records=n,compared_stages=stage_index,seconds=round(time.monotonic()-began,2))),flush=True)
 assert stage_index==6488 and consumed==38 and kills==38 and next(expected,None)is None
 cas=decoder.finish(report['runtime']['capture_cas']);assert cas['records']==6952 and cas['logical_bytes']==2139516743 and cas['logical_sha256']=='8e9e568814f20cb00a6f48f8a954b8745cd2b021a9373e368c300a8dca8f04f5'
 assert expected_reader.bytes==report['expected_uncompressed_bytes']and expected_reader.file_digest.hexdigest()==report['expectations_sha256']
 dump(out/'counter-changes.json',changes);dump(out/'declared-differences.json',differences);dump(out/'unrestored-counter-nonzero-observations.json',unrestored_nonzero);dump(out/'trace-source-provenance.json',trace_provenance)
 terminal=load(CAPTURE/'process-terminal.json');assert terminal['exit_code']==0 and process_missing(terminal['pid'])and process_missing(terminal['pgid'],True)
 result=dict(status='declared_historical_counter_spec_matches'if not differences else'declared_historical_counter_spec_differences',capture=str((CAPTURE/'comparison.json').relative_to(ROOT)),capture_sha256=CAPTURE_SHA,model_trace=str(TRACE.relative_to(ROOT)),model_trace_sha256=TRACE_SHA,static_proof_sha256=STATIC_SHA,original_version='0.135.1',actual_build='90898d5e3',historical_controlled_frames=460,new_original_calls=0,new_original_frames=0,new_model_executions=0,new_full880_frames=0,source_common_sha_equal=102,historical_source_files=117,model_trace_source_files=len(trace['source_sha256']),current_source_drift=drift,summary_not_in_historical_model=True,new_summary_source_sha256=trace['source_sha256']['reconstruction/core_spec/run_summary135.py'],counts=dict(counts),declared_differences=len(differences),declared_difference_rows=differences[:100],all_seven_counters_observed_by_stage=True,declared_running_counter_offsets=[1432,1084,1088,1100],unrestored_running_counter_offsets=[1092,1096,1104],unrestored_nonzero_observations=len(unrestored_nonzero),original_observed_value_sets={str(k):sorted(v)for k,v in observed_sets.items()},counter_change_stages=len(changes),final_declared_counter_values=dict(level=last_projection['progression']['level'],kills=kills,elites=elites,earned=last_projection['earned']),all109_model_deaths_recomputed=True,model920_count109_original_parity_claimed=False,model_events_first460=38,expected_level_gold_source='Historical independent progression/currency stage expectations, generated before original',expected_kill_elite_source='Separate model on_death events; independent accumulator; original counters never fed into model',static_counter_contract_sha256=digest(out/'counter-static-provenance.json'),counter_rows_sha256=digest(rows_path),counter_changes_sha256=digest(out/'counter-changes.json'),trace_source_provenance_sha256=digest(out/'trace-source-provenance.json'),transport=dict(source=str(codec.relative_to(ROOT)),sha256=digest(codec),private_source_identical=True,CAS_full_finish=cas,expected_stream=expected_reader.receipt()),auditor_sha256=digest(Path(__file__)),owned_audit_process=dict(pid=os.getpid(),pgid=os.getpgrp(),expected_terminal='owned-terminal.json'),elapsed_seconds=round(time.monotonic()-began,3),findings=['914 accepted deaths always increment1084 before special branches;rawU416 lowbit increments1088.Ordinary adapter is a guarded subset.','Boss1096 andguardian1092 have separate later914 producers;ordinary on_death does not establish their globalabsence.','Chest1104 is a separate20660 successful-spend producer, with2862near-kind2/2571 and38321distance call paths;no chest owner is restored in run_summary135.','Existing resource consumer explicitly rejects nearbykind2 and retains far ones;this guard must remain rather than incrementing orzeroing counts from pickup population.','Only four running counter owners are declared comparable here;the other three raw columns are observations,not verified knownzero.'],limitations=['Read-only comparison reuses immutable historical original data;does not increase original/frame acceptance counts.','New summary module was absent from the old460 frozen model;102common sources match and the new trace is separately pinned.','The trace records109ordinarydeaths through920 but only its first38events have this historical460comparison.','Source/proc/wholecounter producers,same-statefatal/full880 andcompletegame remain incomplete.'])
 dump(out/'review.json',result);tracked=ROOT/'reports/2026-11-02-run-summary0135-historical-review.json';dump(tracked,result|dict(evidence=str(out.relative_to(ROOT)),review_sha256=digest(out/'review.json')))
 md=ROOT/'reports/2026-11-02-run-summary0135-historical-review.md';md.write_text('# Run counter135 historical comparison\n\nThe new ordinary counter spec was compared read-only against the frozen moving460 capture. No original or model was executed. CAS was fully finished for6952records/2.139GBlogicalbytes.\n\n- Independently replayed38 accepted ordinary death events at the original player stages, including multiple events in one stage; original marker0→1, GUID, rawU416 and ordinary tags matched.\n- Compared currentlevel1432, kills1084, elites1088 and lifetimeearned1100 against originalrawGame at every recorded stage. Level/earned came from historical independent owners; kill/elite from the separate model event trace.\n- All seven original columns are saved stage by stage. Boss1096/guardian1092/chest1104 remain unresolved running owners; observedzero is not declared a restoredproducer.\n-914special branches produce boss/guardian counts;20660successfulspend produces chest1104 through2862kind2/2571 or38321interaction. Nearbykind2 remains guarded in the current consumer.\n\nThe new summary module was absent from historicalsource117;102shared sources match the separately pinned eventtrace. No original counter observation was fed into expected values.109model deaths through920 do not become originalparity claims.\n\nEvidence: `'+str(out.relative_to(ROOT))+'`; reviewSHA256 `'+digest(out/'review.json')+'`. Declared differences: '+str(len(differences))+'. Unrestored nonzero observations: '+str(len(unrestored_nonzero))+'.\n')
 print(json.dumps(dict(status=result['status'],evidence=str(out.relative_to(ROOT)),review_sha256=digest(out/'review.json'),report_json_sha256=digest(tracked),report_md_sha256=digest(md),declared_differences=len(differences),unrestored_nonzero_observations=len(unrestored_nonzero),final=result['final_declared_counter_values'],counts=dict(counts),seconds=result['elapsed_seconds'])),flush=True)
if __name__=='__main__':main()
