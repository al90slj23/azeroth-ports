#!/usr/bin/env python3
"""Read-only independent browser-receipt/bridge review; no browser/WASM execution."""
from pathlib import Path
from datetime import datetime,timezone
import collections,hashlib,importlib.util,json,os,sqlite3,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from review_terrain_effect_geometry135 import sha,digest,load,norm,strict,save,uint,sections,exports,identity,closure,checker
BATCH=ROOT/'evidence/full0135-oracle-20261101T083300.201197Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
GLUE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js'
ALLOWED=(0,521,523,643,644,645,658,659,660,735,804,827,835,845,848,851,877)
FIELDS={'armor_1392_bits':1568,'armor_cap_1572_bits':1572,'nearby_reduction_1444_bits':1624,'hp_1528_bits':1440,'shield_1532_bits':1444,'barrier_1536_bits':1448,'shield_source_1344':1344,'shield_source_remaining_1348_bits':1348,'reserve_768_bits':768,'absorbed_740_bits':740,'maximum_shield_744_bits':744,'last_hit_1648_bits':1652}
def word(raw,o):return struct.unpack_from('<I',raw,o)[0]
def main():
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('browser-resources0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();(out/'reviewer-source.py').write_bytes(Path(__file__).read_bytes());(out/'reviewer-helper.py').write_bytes((ROOT/'scripts/review_terrain_effect_geometry135.py').read_bytes())
 receipt_path=BATCH/'browser-resource135-comparison.json';receipt=load(receipt_path);assert sha(receipt_path)=='e9affcc1707f381334c8f007eec207ae52014ebbe926539a623909056c6563f7'
 hashes=receipt['source_before'];assert hashes==receipt['source_after']and len(hashes)==33;snap=BATCH/'source-snapshot'
 for name,h in hashes.items():assert sha(snap/name)==h==sha(ROOT/name),name
 for name,h in receipt['artifacts'].items():assert sha(BATCH/name)==h,name
 config=load(BATCH/'browser-resource135-config.json');runtime=load(BATCH/'browser-resource135-runtime.json');assert strict(runtime,receipt['runtime']);res=runtime['result'];assert runtime['status']=='passed'and runtime['error']is None and res['failures']==[]
 manifest=identity(BATCH,dict(effect_tick=915,npc_action=910,spawn_boss=2785));assert sha(BATCH/'manifest.json')==config['base_manifest_sha256']
 core=closure(snap,['reconstruction/core_spec/effect_geometry135.py','reconstruction/core_spec/spawn_boss135.py','reconstruction/resource_spec/dbc.py']);assert set(core)<=hashes.keys()
 author=checker(snap,'check_browser_resources135.py');fixtures=load(BATCH/'browser-resource135-fixtures.json');regen=[c for c in author.corpus(True)if c['id']in(0,3,6)];assert strict(fixtures,regen)
 assert [c['id']for c in fixtures]==[r['case_id']for r in res['results']]==[0,3,6]
 assert sha(GLUE)==config['official_glue_sha256']=='636bcd5acba01a31c4b40234969243e964cc8e7e7610adf0817e3494d92c9945'
 original_glue=GLUE.read_bytes();bridge=(BATCH/'official-resource-bridge135.mjs').read_bytes();assert bridge==original_glue+author.BRIDGE_APPEND.encode()and len(original_glue)==config['official_glue_prefix_bytes']and digest(bridge)==config['glue_sha256']
 suffix=bridge[len(original_glue):].decode();assert all(x not in suffix for x in('__wbg_finalize_init','initSync','__wbindgen_start','start(','fetch(','import('))
 raw=ORIGINAL.read_bytes();assert digest(raw)==receipt['original_sha256']==config['original_sha256'];before=sections(raw);browser=(BATCH/'browser-resource135.wasm').read_bytes();after=sections(browser);assert digest(browser)==config['wasm_sha256']
 assert [(k,v)for k,v,*_ in before if k!=7]==[(k,v)for k,v,*_ in after if k!=7]and not any(k==8 for k,*_ in before)
 original_exports=exports(raw,next(x for x in before if x[0]==7));browser_exports=exports(browser,next(x for x in after if x[0]==7));base_exports=exports((BATCH/'research135-exports.wasm').read_bytes(),next(x for x in sections((BATCH/'research135-exports.wasm').read_bytes())if x[0]==7))
 assert browser_exports==base_exports+[('resource135_spell_record',0,4546)]and browser_exports[:len(original_exports)]==original_exports
 types,imports,decl,bodies,_=author.parse_source(raw);assert types[decl[4546-len(imports)]]==(b'\x7f',b'\x7f');a,b=bodies[4546];assert digest(raw[a:b])==config['extra_export']['body_sha256']=='073d44f43e2a1a3ebb31ad697f20516f07128a866eb8c7c40c2eb1fbcca2e00f'
 assert [(i['module'],i['name'],i['type_index'])for i in config['imports']]==imports and [i['id']for i in config['imports']if i['allowed']]==list(ALLOWED)and len(imports)==878
 assert len(runtime['allowed_resource_imports'])==17 and runtime['denied_other_import_count']==861
 assert all(row['allowed']is True and row['id']in ALLOWED and row['name']==config['imports'][row['id']]['name']for row in res['imports'])
 # Pin every real served asset, including the legacy auxiliary module explicitly.
 assets={};asset_root=Path(config['asset_root'])
 for name,h in config['assets'].items():
  p=asset_root/name;assert sha(p)==h;assets[name]=p.read_bytes()
 assert len(assets)==3 and sha(Path(config['auxiliary_module']['path']))==config['auxiliary_module']['sha256']=='a6d8b6cbe3ade99211ad4f01a4712c9996044e402975fc3d72e7f7b6d043f85b'
 from resource_spec.dbc import DBC
 dbc=DBC.parse(assets['dbfilesclient/spell.dbc']);expected_names={}
 for sid in(5568,28783,28308):expected_names[str(sid)]=dbc.string(dbc.word(next(j for j in range(dbc.rows)if dbc.word(j,0)==sid),120)).decode()
 assert expected_names==config['names']
 http_origin=next(x['origin']for x in runtime['lifecycle']if x['event']=='http_listening');request_counts=collections.Counter()
 for request in runtime['requests']:
  assert request['method']=='GET'and request['url'].startswith(http_origin+'/')and request['status']==200
  if request['path'].startswith('/data/'):
   name=request['path'][6:];assert name in assets and request['bytes']==len(assets[name])and request['sha256']==digest(assets[name]);request_counts[name]+=1
  elif request['path']=='/case.mjs':assert request['sha256']==hashes['scripts/browser_resource_case135.mjs']
  elif request['path']=='/bridge.mjs':assert request['sha256']==digest(bridge)
 assert dict(request_counts)=={n:3 for n in assets}and not runtime['blocked_requests']and not runtime['browser_errors']
 # The old pending model is unchanged; compare all known projections ourselves,
 # retaining actual extra1073-tail messages as explicitly unmodeled suffixes.
 totals=collections.Counter();extra_packets=collections.Counter();extra_json=collections.Counter();raw_changes=[]
 for c,actual in zip(fixtures,res['results']):
  assert len(actual['stages'])==len(actual['physical'])==len(c['expected'])==5
  oldpackets=[];oldjson=[]
  for si,(expected,stage,physical,masks)in enumerate(zip(c['expected'],actual['stages'],actual['physical'],c['unspecified_storage_bytes'])):
   assert stage['actual_entry_returned']is True and stage['model_status']==expected['entry_status']
   for key,value in expected.items():
    if key=='entry_status':continue
    if key=='storage':
     assert len(value)==len(stage[key])==len(masks)==64
     for x,y,mask in zip(value,stage[key],masks):
      assert mask in([],[20,21,22,23]);xx=bytes.fromhex(x);yy=bytes.fromhex(y);assert len(xx)==len(yy)==120
      for j,(u,v)in enumerate(zip(xx,yy)):
       if j in mask:totals['explicit_unknown_scratch_bytes']+=1
       else:assert u==v;totals['strict_effect_bytes']+=1
    elif key in('new_packet_opcodes','new_effect_json_events')and expected['entry_status']=='pending_original_spell_database':
     assert strict(stage[key][:len(value)],value)
     suffix=stage[key][len(value):]
     if key=='new_packet_opcodes':extra_packets.update(suffix)
     else:extra_json.update(x['type']for x in suffix)
    else:assert strict(stage[key],value),(c['id'],si,key)
   game=bytes.fromhex(physical['raw_G2592_hex']);unit_storage=bytes.fromhex(physical['unit_full_backing_hex']);effect_storage=bytes.fromhex(physical['full_storage_hex']);timers=bytes.fromhex(physical['timer_full_backing_hex']);mm=bytes.fromhex(physical['message_metadata_full_backing_hex']);nm=bytes.fromhex(physical['notification_metadata_full_backing_hex'])
   assert len(game)==2592 and len(unit_storage)==128*424 and len(effect_storage)==64*120
   assert effect_storage==b''.join(bytes.fromhex(x)for x in stage['storage'])
   unit=bytearray(unit_storage[:424]);assert word(unit,248)==physical['unit248_pointer'];struct.pack_into('<I',unit,248,0);assert unit.hex()==stage['units'][0]and unit_storage[424:]==bytes(127*424)
   assert list(struct.unpack('<'+'I'*(len(timers)//4),timers))==stage['timers_bits']and len(timers)==word(unit,244)*4
   assert len(mm)==word(game,1880)*16 and len(nm)==word(game,1892)*12
   for j,pkt in enumerate(physical['packets']):
    assert word(mm,j*16+8)==len(bytes.fromhex(pkt['payload_hex']))and struct.unpack_from('<H',mm,j*16+12)[0]==pkt['opcode'];assert word(mm,j*16)>=word(mm,j*16+8)
   for j,text in enumerate(physical['effect_json']):assert word(nm,j*12+8)==len(text.encode('utf8'))and word(nm,j*12)>=len(text.encode('utf8'))
   assert len(physical['packets'])==word(game,1888)and len(physical['effect_json'])==word(game,1900)
   assert physical['packets'][:len(oldpackets)]==oldpackets and physical['effect_json'][:len(oldjson)]==oldjson;oldpackets=physical['packets'];oldjson=physical['effect_json']
   for key,off in FIELDS.items():assert stage[key]==word(game,off)
   assert stage['phase2587']==game[2587]and stage['effect_counter2356']==word(game,2356)and stage['movement_sequence2412']==word(game,2412)
   if si:prior=bytes.fromhex(actual['physical'][si-1]['raw_G2592_hex']);raw_changes.append(dict(case_id=c['id'],stage=si,word_delta=[[off,word(prior,off),word(game,off)]for off in range(0,2592,4)if word(prior,off)!=word(game,off)]))
   totals.update(stages=1,raw_game_observation_bytes=len(game),unit_backing_observation_bytes=len(unit_storage),effect_backing_observation_bytes=len(effect_storage),timer_observation_bytes=len(timers),metadata_observation_bytes=len(mm)+len(nm))
  assert c['expected'][-1]['entry_status']=='pending_original_spell_database'
 # Entry log and Once transitions, including two genuinely cold hit paths.
 entries=res['entry_calls'];assert len(entries)==42 and [x['sequence']for x in entries]==list(range(42));permitted={'resource135_spell_record','__wbindgen_malloc','research135_spawn_boss','research135_npc_action','research135_effect_tick'}
 assert all(e['name']in permitted and e['returned']is True for e in entries)
 for probe in res['resource_probes']:
  cid=probe['case_id'];assert probe['before_once']==0 and probe['after_once']==3 and len(probe['records'])==3
  assert{str(p['spell_id']):p['name']for p in probe['records']}==expected_names
  for record in probe['records']:assert len(bytes.fromhex(record['record24_hex']))==24
  if cid==0:assert probe['before_hit_once']==3 and probe['probe_when']=='before_game_hit'
  else:
   assert probe['before_hit_once']==0 and probe['probe_when']=='after_cold_game_hit';warm=[e for e in entries if e['case_id']==cid and e['name']=='research135_effect_tick'and e['once_before']==0 and e['once_after']==3];assert len(warm)==1
   seq=warm[0]['sequence'];native=[i for i in res['imports']if i['case_id']==cid and i['entry_sequence']==seq];assert native and all(i['entry_name']=='research135_effect_tick'for i in native)and any(i['id']==827 for i in native)
 assert totals['stages']==15 and len(res['imports'])==111 and len({i['id']for i in res['imports']})==14
 assert res['cap_verified']is True and res['wasm_page_cap']==2048 and config['memory_cap_bytes']==128*1024*1024 and res['max_memory_bytes']==92143616 and max(e['memory_after']for e in entries)==92143616
 assert res['native_self']is True and res['native_xhr']is True and res['local_storage_keys']==[]and res['indexeddb_databases']==[]
 assert receipt['process']['exit_code']==0 and runtime['process_pid']==receipt['process']['pid']==79922
 browser=next(x for x in runtime['lifecycle']if x['event']=='browser_started');final=next(x for x in runtime['lifecycle']if x['event']=='browser_process_final');assert browser['pid']==final['pid']==runtime['browser_pid']==79938 and browser['parent_pid']==runtime['process_pid']and final['exit_code']==0 and final['signal_code']is None
 assert any(x['event']=='context_closed'for x in runtime['lifecycle'])and any(x['event']=='http_server_closed'for x in runtime['lifecycle'])
 args=browser['spawnargs'];assert '--js-flags=--wasm-max-mem-pages=2048 --max-old-space-size=512'in args and any(x.startswith('--user-data-dir='+str(BATCH/'browser-tmp')+'/')for x in args)and '--proxy-server=http://127.0.0.1:9'in args
 profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';assert sha(profile/'index.sqlite')=='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
 graph=sqlite3.connect(f'file:{profile / "index.sqlite"}?mode=ro',uri=True);graph.row_factory=sqlite3.Row;assert[tuple(x)for x in graph.execute('select caller,count(*) from calls where callee=4253 group by caller')]==[(176107,1)]and not list(graph.execute('select caller from calls where callee=176107'))
 row=graph.execute('select wat_start,wat_end from functions where idx=176107').fetchone()
 with(profile/'official-0.135.1-full.wat').open('rb')as stream:stream.seek(row['wat_start']);start_wat=stream.read(row['wat_end']-row['wat_start']).decode()
 assert start_wat=='  (func (;176107;) (type 9)\n    call 851\n    call 4253)\n'and ('start',0,4253)in original_exports and ('__wbindgen_start',0,176107)in original_exports
 process_check=[]
 for pid in(79922,79938):
  try:os.kill(pid,0)
  except ProcessLookupError:process_check.append(dict(pid=pid,present=False,method='signal0 presence query, no signal sent'))
  else:raise AssertionError('Owned process still exists')
 save(out/'observed-game-word-deltas.json',raw_changes)
 result=dict(status='passed_scoped_real_browser_embedding_review',receipt=str(receipt_path.relative_to(ROOT)),receipt_sha256=sha(receipt_path),sources=33,production_closure=core,official_glue_sha256=sha(GLUE),bridge_prefix_bytes=len(original_glue),wasm_only_export_change=True,added_exports=browser_exports[len(original_exports):],approved_import_ids=list(ALLOWED),allowed_imports=17,denied_imports=861,actual_import_calls=111,actual_distinct_imports=14,asset_hashes=config['assets'],data_request_counts=dict(request_counts),dbc_name_records=expected_names,cases=3,known_stages=15,explicit_entry_calls=len(entries),once_probes=res['resource_probes'],totals=dict(totals),unmodeled_extra_packet_opcodes=dict(extra_packets),unmodeled_extra_JSON_types=dict(extra_json),max_memory_bytes=res['max_memory_bytes'],engine_page_cap=2048,cap2049_negative_checked=True,closed_node_pid=79922,closed_browser_pid=79938,process_check=process_check,reviewer_sha256=sha(Path(__file__)),helper_sha256=sha(ROOT/'scripts/review_terrain_effect_geometry135.py'),original_or_browser_reexecuted=False,author_sources_modified=False,
 appstart_evidence=['Original module hasno implicitstartsection8.','Explicit JS callallowlist andall42entrylogs contain nostart/__wbindgen_start.','Officialglue prefix exact;appendonly BindOnly nevercallsinitSync/default/finalizer.','Original176107 directbody calls851then4253;4253 directcallindex only176107.'],
 limitations=['Appstart false flags are harness declarations;explicitJS/static evidence isnot an exhaustive proof against every possible internalcall_indirect.','No externalrequest observed;exactloopback route/CSP/proxy/DNS policy andfreshprofile were audited,not packetlevelOSnetworktracing.','3normal originalentry returns and15knownprojections do not independently reconstruct resource-success history/registry/procs/keyedcontainer tails.','rawG2592/full128unit/effect/timer/metadata/payload sidecars include unknown state,not allindependent expected;known4scratchbytes+unit248address normalization remain explicit.','Three Spell names are independentlychecked;24Brecord pointers/icons andthe completeDBschema are not therebyreconstructed.','The17allowedresource-import/128MiB browser experiment isseparate from878-denied/32MiB Node mathbatches;old390pendingmodel notchanged.','Legacylocal assets/snippet are genuine readbytes,not complete latest135 assetequivalence orreal1089/world/app completion.'])
 save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),cases=3,known_stages=15)),flush=True)
if __name__=='__main__':main()
