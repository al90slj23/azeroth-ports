#!/usr/bin/env python3
"""Independent read-only raw451→fatal model-composition review;0 target/model runs.

Reads captured independent summaries and model expectations only. Does not
import author runner/bridge/production,open original code/memory/results,or
execute their models. Its own file-open audit is explicit; no retrospective
OS-level audit of the author's already completed run is claimed.
"""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import ast,gzip,hashlib,json,struct,sys,time
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/raw-fatal921-owned-20261102T015451.868431Z';MODEL=RUN/'model921'
REPORT=ROOT/'reports/2026-11-02-raw-fatal0135.json'
ORACLE=ROOT/'evidence/opening-combat0135-oracle-20261102T012524.271526Z'
SHA_REPORT='71bd7b45b5ec58c1b92559c4448b18d00ca185bac160e8f30c0aa8939234fbe1'
SHA_RECEIPT='ad418c9435bc4e8b246ec153b1224eb33d904f594d84fc332f859eec070b957d'
SHA_BRIDGE='e34af2038593f9ab9c5e408db462714a4eacb5a9fdb3f34d336a0452b8e3a7a5'
SHA_ORACLE='430e764bfc0b556bf33489796ed04e96da8e1f4f0aedbcc4bee8217b67967160'
reads=set();denied=[]

def audit(event,args):
 if event!='open'or not isinstance(args[0],(str,bytes)):return
 p=Path(args[0]).resolve();mode=args[1];flags=args[2];isread=isinstance(mode,str)and('r'in mode or'+'in mode)or isinstance(flags,int)and flags&3==0
 if not isread:return
 forbidden=p.suffix.lower()in('.wasm','.exe','.memory','.wat')or 'original-results'in p.name or '/capture-cas/'in str(p)or '/originals/'in str(p)or(p.name in('terrain-query.bin','navigation.bin','secondary-height.u32le')and p.parent!=MODEL)
 if forbidden:denied.append(str(p));raise PermissionError('Independent review forbidden read: '+str(p))
 reads.add(str(p))
sys.addaudithook(audit)

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_text())
def owner(rows,count):
 h=hashlib.sha256();unknown=0
 for row in rows:
  assert isinstance(row,list)and all(v is None or type(v)is int and 0<=v<=255 for v in row);unknown+=row.count(None);h.update(json.dumps(row,separators=(',',':')).encode()+b'\n')
 return dict(count=count,capacity=len(rows),backing_sha256=h.hexdigest(),unknown_backing_cells=unknown)
def cells(row):return list(bytes.fromhex(row))if isinstance(row,str)else row

def stage_summary_check(summary,expected):
 p=expected['projection'];v=expected['vectors'];checked={}
 scalars=['phase2587','now_bits','rng_words','spawn_counter','message_sequence','kill_cost_bits','budget_bits','gold','earned','current_hp_bits','progression','outgoing_total_hex','incoming_total_hex','distance_map_updated_at_bits']
 checked['scalars']=all(summary[k]==p[k]for k in scalars)
 for name,label in [('units','units424'),('areas','areas88'),('pickups','pickups56'),('companions','companions88'),('special','special40'),('windows','windows8'),('boundaries','boundaries8'),('live32','live32'),('aura48','aura48')]:checked['owner.'+name]=owner(v[name]['storage'],v[name]['count'])==summary['owners'][label]
 ledger=p['run_ledger'];history=ledger['incoming_history'];header=history['header'];aux=p['auxiliary_motion'];source=summary['physical_player_sources']
 checked['owner.incoming48']=owner(history['storage'],header['count'])==summary['owners']['incoming48']
 checked['owner.auxiliary112']=owner(aux['storage112'],aux['count664'])==summary['owners']['auxiliary112']
 checked['run_ledger']=summary['run_ledger']==dict(counters=ledger['counters'],hero=ledger['hero'],lives1632=ledger['lives1632'],left2567=ledger['left2567'],incoming_history_header=header)
 checked['auxiliary_header']=summary['auxiliary_motion']=={k:aux[k]for k in ['capacity656','pointer660','count664']}
 for key in ['paused408','paused412_bits','terminal_notifications','fatal_stop_packets']:checked[key]=summary[key]==p[key]
 checked['opaque_live_origins']=[dict(slot=i,source=x)for i,x in enumerate(source['auxiliary_origins'])if x is not None]==expected['unresolved_live_auxiliary_origins']
 checked['Aura_and_App']=source['initialized2569']==p['aura_initialized2569']and source['notification_next_id14340336']==p['notification_next_id14340336']and source['rune_notifications']==p['rune_notifications']
 checked['known_motion']={k:x for k,x in summary['motion_words'].items()if x is not None}==p['motion_scalar_words']
 path=p['distance_map'];checked['distance_map']=summary['distance_map']==(None if path is None else dict(start_index=path['start_index'],reachable=path['field24'],values_sha256=path['values_sha256']))
 checked['alive_units']=summary['alive_units']==sum(row[:4]==[0,0,0,0]for row in v['units']['storage'][:v['units']['count']])
 return checked

def main():
 began=time.monotonic();assert sha(REPORT)==SHA_REPORT and sha(MODEL/'receipt.json')==SHA_RECEIPT and sha(RUN/'stage-terminal-model-bridge.json')==SHA_BRIDGE and sha(ORACLE/'comparison.json')==SHA_ORACLE
 report=load(REPORT);receipt=load(MODEL/'receipt.json');bridge=load(RUN/'stage-terminal-model-bridge.json');oracle=load(ORACLE/'comparison.json');handoff=load(RUN/'task-handoff.json');assert sha(RUN/'task-handoff.json')=='e80812362ffed77c9b440f1c4287e34c0abb32a62e1f2245f6644c0e37f1579c'
 for n,h in handoff['files'].items():assert sha(ROOT/n)==h
 for n,h in report['artifacts'].items():assert sha(ROOT/n)==h
 for name,key in [('inputs.json','inputs_sha256'),('stages.jsonl','stages_sha256'),('final-state.json','final_state_sha256'),('final-ledger-owner.json','final_ledger_owner_sha256'),('opaque-pickup-amount-origins.json','opaque_pickup_amount_origins_sha256')]:assert sha(MODEL/name)==receipt[key]
 assert len(receipt['source_sha256_before'])==121 and receipt['source_sha256_before']==receipt['source_sha256_after']and not receipt['escaped_runtime_sources']and receipt['production_source_unchanged']
 source_io=[]
 for name,h in receipt['source_sha256_before'].items():
  assert sha(ROOT/name)==h and sha(MODEL/'source-snapshot'/name)==h
  tree=ast.parse((MODEL/'source-snapshot'/name).read_text())
  for node in ast.walk(tree):
   if isinstance(node,ast.Call):
    label=node.func.id if isinstance(node.func,ast.Name)else node.func.attr if isinstance(node.func,ast.Attribute)else ''
    if label in('open','read_bytes','read_text','Popen','run','system','exec','eval','CDLL','load_module','instantiate'):source_io.append(dict(file=name,line=node.lineno,call=label))
 assert sum(n.startswith('reconstruction/')for n in receipt['source_sha256_before'])==117
 shared={n:h for n,h in oracle['source_sha256_before'].items()if n.startswith('reconstruction/')};assert len(shared)==113
 for n,h in shared.items():assert receipt['source_sha256_before'].get(n)==h and sha(ORACLE/'source-snapshot'/n)==h
 rawextra=sorted(set(n for n in receipt['source_sha256_before']if n.startswith('reconstruction/'))-set(shared));assert len(rawextra)==4
 inputs=load(MODEL/'inputs.json');assert inputs['world_input']=='raw_assets_only_no_preparsed_world_or_original_memory'and inputs['requested_frames']==1000 and inputs['run_ledger135']and inputs['physical_player_sources']and inputs['explicit_App_notification_counter']==1
 manifest=Path(receipt['asset_manifest']);assert sha(manifest)==receipt['asset_manifest_sha256']==sha(MODEL/'asset-manifest.input.json')
 declared={x['chain']:x for x in inputs['asset_inputs']};loaded=receipt['loaded_assets_sha256_after'];assert len(declared)==453 and len(loaded)==451;assert set(declared)-set(loaded)=={'dbfilesclient\\spell.dbc','dbfilesclient\\spellicon.dbc'}
 assetbytes=0;headers=Counter()
 for name,h in loaded.items():
  a=declared[name];p=Path(a['file']);assert p.resolve().is_relative_to(Path('/Volumes/RuiRui4TB'))and p.stat().st_size==a['bytes'];assert sha(p)==h==a['sha256'];assetbytes+=a['bytes']
  with p.open('rb')as f:headers[f.read(4).hex()]+=1
 assert assetbytes==67281330 and receipt['decoded_asset_bytes']==assetbytes and receipt['assets_unchanged']
 world_expected={Path(n).name:h for n,h in oracle['world_input']['artifacts'].items()};world={}
 for a in receipt['world_artifacts'].values():
  p=MODEL/a['file'];assert sha(p)==a['sha256']==world_expected[p.name]and p.stat().st_size==a['bytes'];world[p.name]=dict(bytes=a['bytes'],sha256=a['sha256'])
 assert len(world)==3
 for name in ['owned-terminal.json','bridge-owned-terminal.json']:
  x=load(RUN/name);assert x['exit_code']==0 and x['pid_missing']and x['pgid_missing']and not x['deadline_exceeded']and x['new_original_cases']==x['original_executions']==0
 assert receipt['oracle_cases']==receipt['new_original_differential_cases']==0 and all(receipt[k]is False for k in ['original_program_executed','original_memory_read','original_wasm_executed','preparsed_world_input_read'])
 assert not bridge['original_stage_comparison']and bridge['new_original_cases']==bridge['original_executions']==0
 expectedfile=ORACLE/'stage-expectations.jsonl.gz';assert sha(expectedfile)==oracle['expectations_sha256'];fixture=load(ORACLE/'fixtures.json');assert sha(ORACLE/'fixtures.json')==oracle['fixtures_sha256']
 kinds=Counter();categories=Counter();failures=[];logical=0;count=0;phase4=[];frames=set();selections=0;actions=set();motions=[];terminal=None;lastsummary=None;maxline=0
 with gzip.open(expectedfile,'rb')as source,(MODEL/'stages.jsonl').open('rb')as summaries:
  while True:
   raw=source.readline(2097153)
   if not raw:break
   assert raw.endswith(b'\n')and len(raw)<=2097152;logical+=len(raw);maxline=max(maxline,len(raw));assert logical<=1073741824
   own=summaries.readline(2097153);assert own.endswith(b'\n')and len(own)<=2097152
   expected=json.loads(raw);row=json.loads(own);kind='opening'if expected['record_kind']=='opening'else expected['kind'];assert row['stage_index']==count and row['kind']==kind and row['action_index']==expected.get('action_index')
   if expected['record_kind']=='stage':assert expected['stage_index']==count-1
   if row['action_index']is not None:actions.add(row['action_index'])
   if kind=='player':frames.add(row['action_index'])
   if kind=='select':selections+=1;assert row['chosen_index']==fixture['actions'][row['action_index']]['index']
   if kind=='motion':motions.append(dict(kind='motion',opcode=row['opcode'],payload24_hex=row['payload24_hex']))
   summary=row['summary'];assert summary['frames']==len(frames)and summary['selections']==selections
   assert summary['seconds']==struct.unpack('<f',struct.pack('<I',summary['now_bits']))[0]
   content={k:v for k,v in summary.items()if k!='summary_sha256'};assert hashlib.sha256(json.dumps(content,sort_keys=True,separators=(',',':')).encode()).hexdigest()==summary['summary_sha256']
   checks=stage_summary_check(summary,expected['expected']);checks['stage_identity']=True
   assert len(checks)==24 and set(checks)==set(bridge['stage_summary_checks'])
   for k,ok in checks.items():
    categories[k]+=1
    if not ok:failures.append(dict(row=count,category=k))
   if summary['phase2587']==4:phase4.append(dict(stage_index=count,kind=kind,HP_bits=summary['current_hp_bits']))
   kinds[kind]+=1;count+=1;terminal=expected;lastsummary=summary
  assert not summaries.read(1)
 assert not failures and count==12946 and logical==1072504103 and oracle['compared_stages']==12945
 assert len(frames)==921 and selections==7 and len(motions)==44 and actions==set(range(972))and motions==[x for x in fixture['actions']if x['kind']=='motion']
 assert receipt['motion_route_events']==fixture['motion_route_events']and receipt['independent_frames']==921 and receipt['independent_selections']==7 and receipt['actions']==972 and receipt['stage_summaries']==12946
 assert receipt['boundary']==dict(kind='not_running',phase='frame',attempted_frame=921,completed_frames=921)
 assert phase4==bridge['phase4_rows']and[k['kind']for k in phase4]==['ai','collect','claims','spawn','special','terminal']and all(k['HP_bits']==0 for k in phase4)
 assert terminal['kind']=='terminal'and terminal['stage_index']==12944 and terminal['action_index']==971
 state=load(MODEL/'final-state.json');summary=load(MODEL/'final-summary.json');ledger=load(MODEL/'final-ledger-owner.json');assert summary==lastsummary
 p=terminal['expected']['projection'];v=terminal['expected']['vectors'];own=state['independent_opening_owner'];player=state['player_source_owner'];direct=[k for k in p if k in state]
 assert len(direct)==36 and direct==bridge['direct_terminal_projection_keys']and all(state[k]==p[k]for k in direct)
 fullowners={
  'units':(own['unit_backing_cells'],len(state['records']),'units424'),
  'areas':(own['area_backing_cells'],len(state['area_records']),'areas88'),
  'pickups':(own['pickup_backing_cells'],own['pickup_active_count'],'pickups56'),
  'windows':(own['window_backing_cells'],own['window_count'],'windows8'),
  'boundaries':(own['boundary_backing_cells'],own['boundary_count'],'boundaries8'),
  'live32':(player['live_backing_cells'],player['live_count'],'live32'),
  'aura48':(player['aura_backing_cells'],player['aura_capacity'],'aura48'),
 }
 finalowners={};totalcells=0;unknown=0
 for name,(rows,n,label)in fullowners.items():
  assert rows==v[name]['storage']and len(rows)==v[name]['capacity']and n==v[name]['count']and owner(rows,n)==summary['owners'][label];totalcells+=sum(len(x)for x in rows);unknown+=sum(x.count(None)for x in rows);finalowners[name]=summary['owners'][label]
 for name,label in [('special','special40'),('companions','claims88')]:
  actual=state['tail_state'][label];rows=[cells(x)for x in actual['records_hex']];vector=v[name]
  assert actual['capacity']==len(rows)==vector['capacity']==vector['count']and rows==vector['storage'];ownerlabel='special40'if name=='special'else'companions88';assert owner(rows,len(rows))==summary['owners'][ownerlabel];totalcells+=sum(len(x)for x in rows);unknown+=sum(x.count(None)for x in rows);finalowners[name]=summary['owners'][ownerlabel]
 history=ledger['incoming_history'];expectedhistory=p['run_ledger']['incoming_history'];assert history['storage']==expectedhistory['storage']and {k:history[k]for k in ['capacity','head','count']}==expectedhistory['header'];assert owner(history['storage'],history['count'])==summary['owners']['incoming48'];totalcells+=sum(len(x)for x in history['storage']);unknown+=sum(x.count(None)for x in history['storage']);finalowners['incoming48']=summary['owners']['incoming48']
 assert ledger['auxiliary_motion']==p['auxiliary_motion']==dict(capacity656=0,pointer660=8,storage112=[],count664=0);finalowners['auxiliary112']=summary['owners']['auxiliary112'];assert finalowners['auxiliary112']==owner([],0)
 assert totalcells==22720 and unknown==8205
 assert ledger['hero']==dict(text='',cloned_capacity200=0,cloned_pointer204=1,cloned_length208=0,utf8_hex='')and ledger['lives1632']==ledger['left2567']==0
 assert ledger['callback_sources']['items8']==dict(stride=8,count=0,storage=[],capacity_word=0)and ledger['callback_sources']['modifiers36']==dict(stride=36,count=0,storage=[],capacity_word=0)
 assert len(ledger['callback_sources']['ordinary_selection_events'])==7 and len(summary['terminal_notifications'])==1 and len(summary['fatal_stop_packets'])==10 and summary['paused408']==1 and summary['paused412_bits']==summary['now_bits']and summary['current_hp_bits']==0 and summary['phase2587']==4
 opcode,payload=summary['terminal_notifications'][0];assert opcode==3748;notification=json.loads(bytes.fromhex(payload));assert{key:notification[key]for key in ['level','kills','elites','guardians','bosses','gold','chests','hero','left']}==dict(level=8,kills=109,elites=0,guardians=0,bosses=0,gold=115,chests=0,hero='',left=False)
 assert state['physical_output_pending']==fixture['physical_output_pending']and load(MODEL/'opaque-pickup-amount-origins.json')==terminal['expected']['opaque_pickup_amount_origins']
 motion=load(MODEL/'final-motion-owner.json');offsets=[416,420,424,428,432,436,440,444,448,452,456,460,464,1428,1744,1748,1752,1756,1760,1764,1768,1772,1776,1780,2496,2500];valid={b for o in offsets for b in range(o,o+4)};known=p['motion_scalar_words'];assert len(motion)==2592 and all(x is None for j,x in enumerate(motion)if j not in valid)
 for o in offsets:assert motion[o:o+4]==[None]*4 if str(o)not in known else None not in motion[o:o+4]and int.from_bytes(bytes(motion[o:o+4]),'little')==known[str(o)]
 failed=ROOT/report['failure_preserved']['owned_directory'];assert not(failed/'model921/receipt.json').exists();ft=load(failed/'owned-terminal.json');assert ft['exit_code']==1 and ft['pid_missing']and ft['pgid_missing']and sha(failed/'owned-terminal.json')==report['failure_preserved']['owned_terminal_sha256'];assert sha(failed/'stderr.log')==report['failure_preserved']['stderr_sha256']and 'Object of type bytes is not JSON serializable'in(failed/'stderr.log').read_text()
 fb=load(failed/'model921/source-before.json');assert all(fb[n]==h for n,h in receipt['source_sha256_before'].items()if n.startswith('reconstruction/'))
 old460=ROOT/'scripts/check_raw_moving_rune135_bridge.py';assert sha(old460)==report['previous_460_bridge_unchanged_sha256']
 source= (ROOT/'scripts/run_asset_combat135.py').read_text();assert "parser.add_argument('--run-ledger',action='store_true'"in source and 'dict(run_ledger=empty_research_run_ledger135())if args.run_ledger else{}'in source
 assert not denied
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('raw-fatal135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 result=dict(status='pass_scoped_raw_model_composition_not_new_original_differential',report_sha256=SHA_REPORT,model_receipt_sha256=SHA_RECEIPT,bridge_sha256=SHA_BRIDGE,controlled_original_experiment_metadata_sha256=SHA_ORACLE,
  author_runner_or_bridge_executions=0,author_production_executions=0,original_executions=0,new_original_cases=0,native_executions=0,raw_assets_independently_rehashed=451,raw_asset_bytes=assetbytes,raw_asset_header_counts=dict(headers),world_artifacts_rehashed=world,
  source_files_current_and_snapshot_hashed=121,production_files=117,shared_gameplay_production_byte_identical=113,raw_only_production_files=rawextra,static_IO_callsite_audit=source_io,
  stage_rows_independently_read=count,expected_logical_bytes=logical,maximum_expected_line_bytes=maxline,stage_kinds=dict(kinds),stage_summary_category_counts=dict(categories),stage_summary_mismatches=failures,additional_summary_hashes_clock_frame_selection_counts_checked=True,
  complete_terminal_direct_projection_keys=direct,terminal_full_rows_known_and_None_owner_details=finalowners,terminal_physical_cells_compared=totalcells,terminal_unknown_None_cells_retained=unknown,
  default_run_ledger_disabled=True,failed_bytes_export_retained=True,failed117production_matches_success=True,phase4_AI_and_five_tail_stages=phase4,author_original_claim_scope='No new original or per-stage raw-asset original differential;two model runs share113gameplay source files',
  read_audit_scope='This reviewer open audit only.Author run has static provider/source/input guards and metadata,but no separately captured OS-level file-open audit',reviewer_read_paths=sorted(reads),reviewer_forbidden_reads=denied,reviewer_static_source_sha256=sha(Path(__file__)),seconds=time.monotonic()-began,
  limits=['Comparison reads only model expected stream and comparison metadata,never original-results/CAS/rawmemory','No independent re-execution/reconstruction of geometry or gameplay rules;raw artifacts and two serialized modeloutputs are independently read/rehashed/compared','24stage categories are declaredsummary subsets;unserializedfields notinvented','Terminalspecial/companions fullrows are direct inthisspecificfinalstate because activecount==capacity;other stages usefullbacking fingerprint','None8205cells remainunknown,notzero;caller-scratch numericproducer remainsunrestored','NaturalApp/deviceinput/full880/win/save/render/audio/UI/network/allmaps/classes/skills andlatest139fullflow remainincomplete'])
 (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),stage_rows=count,categories=len(categories),terminal_cells=totalcells,None_cells=unknown,seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
