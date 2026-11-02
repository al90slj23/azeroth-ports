#!/usr/bin/env python3
"""Independent frozen163-case ordinary source1073 review; no target/model runs."""
from pathlib import Path
from collections import Counter
import ast,hashlib,json,os,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_stats138 import digest,sections,exports,function_ids,static_image_reader,local_edges,process_missing
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/full0135-oracle-20261101T235458.632785Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
CAPTURE_SHA='84accac68189bdf3bb55dc41118e67fff3c36c6437512373ec31d2c3182459e9'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
OFFSETS={'armor_1392_bits':1568,'armor_cap_1572_bits':1572,'nearby_reduction_1444_bits':1624,'hp_1528_bits':1440,'shield_1532_bits':1444,'barrier_1536_bits':1448,'shield_source_1344':1344,'shield_source_remaining_1348_bits':1348,'reserve_768_bits':768,'absorbed_740_bits':740,'maximum_shield_744_bits':744,'last_hit_1648_bits':1652}
def load(path):return json.loads(Path(path).read_text())
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def u(raw,offset):return struct.unpack_from('<I',raw,offset)[0]
def f(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def b(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def literal(path,name):return ast.literal_eval(next(n.value for n in ast.parse(path.read_text()).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)))

def main():
 began=time.monotonic();assert len(sys.argv)==2 and os.getpid()==os.getpgrp(),'Owned audit launcher required';out=Path(sys.argv[1]).resolve();assert out.parent==ROOT/'evidence'and out.name.startswith('incoming-source135-independent-review-')and out.is_dir()
 receipt=load(RUN/'incoming-source135-comparison.json');manifest=load(RUN/'manifest.json');assert digest(RUN/'incoming-source135-comparison.json')==CAPTURE_SHA
 files=receipt['source_sha256_before'];assert files==receipt['source_sha256_after']and len(files)==20;source=RUN/'source-snapshot'
 for name,h in files.items():assert digest(ROOT/name)==h==digest(source/name),name
 edges=local_edges(source,files);production={n for n in files if n.startswith('reconstruction/')};assert len(production)==9
 todo=['reconstruction/core_spec/incoming_source135.py','reconstruction/core_spec/incoming135.py','reconstruction/core_spec/incoming_history135.py'];closure=set()
 while todo:
  name=todo.pop()
  if name in closure:continue
  closure.add(name)
  if name.startswith('reconstruction/')and not name.endswith('/__init__.py'):todo.append(str(Path(name).parent/'__init__.py'))
  todo.extend(b for a,b in edges if a==name)
 assert closure==production
 for name,h in receipt['artifacts'].items():assert digest(RUN/name)==h,name
 original=ORIGINAL.read_bytes();module=(RUN/manifest['module_file']).read_bytes();assert len(original)==90959080 and hashlib.sha256(original).hexdigest()==SOURCE_SHA
 assert hashlib.sha256(module).hexdigest()==manifest['module_sha256'];a,z=sections(original),sections(module);assert [x[0]for x in a]==[x[0]for x in z]and not any(x[0]==8 for x in a)
 assert all(original[x:y]==module[p:q]for(k,x,_,y),(_,p,_,q)in zip(a,z)if k!=7)
 assert exports(module)==exports(original)+[['research135_incoming_damage',0,1073]]and['__wbindgen_malloc',0,91941]in exports(original)
 identities=function_ids(original,{1073,58162});role=manifest['roles'][0];assert len(manifest['roles'])==1 and role['index']==1073
 assert identities[1073]['signature']==['7f7d7e7f7f7f','']and identities[1073]['body_sha256']==role['body_sha256']=='ae8055c998f7dad212a404de8cee67a5375c9f4f94750f1e69fd5119f4f9e076'
 static=ROOT/'evidence/player-death135-static-20261101T234954.522203Z/proof.json';proof=load(static);assert digest(static)=='80c938514cd1a347edfb97a3e50e74f67595fb9e73226776edb48bf62cc8c6e6'
 for i in (1073,58162):assert proof['functions'][str(i)]['body_sha256']==identities[i]['body_sha256']
 # Independently reread indexedWAT windows; the previous diagnostic is not
 # trusted as substitute for the pinned original/index binding.
 profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';wat_bindings={}
 with sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
  db.row_factory=sqlite3.Row
  with(profile/'official-0.135.1-full.wat').open('rb')as wat:
   for i in(1073,58162):
    row=dict(db.execute('select * from functions where idx=?',(i,)).fetchone());assert row['body_start']==identities[i]['body_start']and row['body_end']==identities[i]['body_end'];wat.seek(row['wat_start']);raw=wat.read(row['wat_end']-row['wat_start']);assert hashlib.sha256(raw).hexdigest()==proof['functions'][str(i)]['wat_sha256'];wat_bindings[str(i)]={'WAT_bytes':len(raw),'WAT_sha256':hashlib.sha256(raw).hexdigest()}
 tree=ast.parse((source/'reconstruction/core_spec/incoming_source135.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='resolve_incoming_source135')
 assert not any(isinstance(n,ast.Subscript)and isinstance(n.ctx,ast.Store)for n in ast.walk(fn))
 calls=[(n.lineno,n.func.id,[getattr(v,'value',None)for v in n.args])for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id in('u32','u64')];calls.sort()
 assert [(name,args[1])for _,name,args in calls]==[('u64',112),('u32',244),('u32',40),('u32',284)]
 reader=static_image_reader(original);fields=literal(source/'reconstruction/core_spec/spawn135_data.py','NORMAL_FIELDS');definitions=literal(source/'reconstruction/core_spec/spawn135_data.py','NORMALS');catalog={}
 for zone in definitions:
  for values in zone:
   entry=dict(zip(fields,values));ptr=entry['pointer'];name_ptr,name_len=struct.unpack('<2I',reader(ptr+16,8));actual_name=reader(name_ptr,name_len).decode('utf8');assert entry['name']==actual_name
   if ptr in catalog:assert catalog[ptr]==actual_name
   catalog[ptr]=actual_name
 assert len(catalog)==148;dump(out/'static-fallback-names.json',{'names':catalog,'provenance':reader.proofs,'identities':identities,'WAT_bindings':wat_bindings})
 fixtures=load(RUN/'incoming-source135-fixtures.json');inputs=load(RUN/'incoming-source135-inputs.json');actual=[json.loads(x)for x in(RUN/'incoming-source135-results.jsonl').read_text().splitlines()];assert len(fixtures)==len(inputs)==len(actual)==163
 counts=Counter();groups=Counter();pointer_tags=set();ranks=set()
 for i,(c,inp,row)in enumerate(zip(fixtures,inputs,actual,strict=True)):
  assert c['id']==inp['id']==row['id']==i and inp=={k:v for k,v in c.items()if k not in('expected',)}and len(c['ops'])==len(c['expected'])==len(row['stages'])==1
  assert set(inp)=={'capacity','count','group','head','id','input','ops','source_records','storage'}and c['capacity']==c['head']==c['count']==0 and c['storage']==[]
  s=c['input'];op=c['ops'][0];got=row['stages'][0];want=c['expected'][0];groups[c['group']]+=1
  assert s['phase_2579']in(1,4)and s['protection_2568']==s['mode_2574']==s['minimum_one_2578']==0 and all(not s[k]for k in('units','buffs','modifiers'))
  assert s['armor_1392_bits']==s['nearby_reduction_1444_bits']==s['shield_1532_bits']==s['barrier_1536_bits']==s['shield_source_1344']==s['shield_source_remaining_1348_bits']==s['reserve_768_bits']==0
  assert op['category']==0 and op['critical']in(0,1)and f(s['hp_1528_bits'])==1000 and f(s['max_hp_bits'])==1000 and f(op['amount_bits'])==7.5 and f(op['now_bits'])==20
  guarded=s['phase_2579']!=1;label='';rank=4;matched=None;guid=int(op['source_guid'])
  records=[bytes.fromhex(x)for x in c['source_records']];assert all(len(x)==424 for x in records)
  if not guarded:
   for j,unit in enumerate(records):
    if struct.unpack_from('<Q',unit,112)[0]!=guid:continue
    assert u(unit,244)==u(unit,40)==0xffffffff;ptr=u(unit,284);label=catalog[ptr]if ptr else '';rank=unit[416];matched=j;pointer_tags.add(ptr);ranks.add(rank);break
  scalar={key:s[key]for key in OFFSETS}
  if not guarded:scalar['hp_1528_bits']=b(f(s['hp_1528_bits'])-f(op['amount_bits']));scalar['last_hit_1648_bits']=op['now_bits']
  scalar['incoming_total_992_bits']=struct.pack('>d',s['incoming_total_992']+(0 if guarded else f(op['amount_bits']))).hex();scalar['phase_2579']=s['phase_2579'];assert scalar==want['scalar']==got['scalar']
  counts['scalar_values']+=len(scalar)
  expected_cap=0 if guarded else 4;expected_count=0 if guarded else 1;assert got['header']==want['header']==dict(capacity=expected_cap,head=0,count=expected_count)
  game=bytes.fromhex(got['raw_game2592_hex']);assert len(game)==2592;counts['raw_Game_bytes_bound']+=len(game)
  for key,offset in OFFSETS.items():assert u(game,offset)==got['scalar'][key]
  assert struct.unpack_from('<Q',game,992)[0]==int(scalar['incoming_total_992_bits'],16)and game[2587]==scalar['phase_2579']
  assert list(struct.unpack_from('<4I',game,968))==[expected_cap,got['history_pointer'],0,expected_count]
  cap,ptr,n=struct.unpack_from('<3I',game,1784);assert cap==n==len(records)and ptr+n*424<=receipt['runtime']['max_memory_bytes']
  assert got['source_records_after']==c['source_records'];counts['source_record_bytes_exact']+=sum(map(len,records))
  for offset,value in got['game_changes']:assert u(game,offset)==value
  assert got['packets']==got['notifications']==[]and u(game,1888)==u(game,1900)==0
  assert len(bytes.fromhex(got['message_metadata_backing_hex']))==u(game,1880)*16==2048 and set(bytes.fromhex(got['message_metadata_backing_hex']))=={0}
  assert got['notification_metadata_backing_hex']==''and u(game,1892)==0
  if guarded:
   assert got['storage']==got['active']==[]and want['storage']==want['active']==want['provenance']==[];counts['phase_guard_returns']+=1;continue
  assert len(got['active'])==1 and len(got['storage'])==len(want['storage'])==len(want['provenance'])==4
  strings=[label,'Melee','INV_Sword_04'];assert got['active'][0]['slot']==0 and got['active'][0]['strings']==strings and want['active']==[dict(slot=0,strings=strings)]
  expected_row=[None]*48;origins=['allocator_unwritten']*48
  for offset,text in zip((0,8,16),strings):expected_row[offset+4:offset+8]=list(struct.pack('<I',len(text.encode('utf8'))));origins[offset:offset+4]=['resource_pointer']*4;origins[offset+4:offset+8]=['semantic']*4
  expected_row[24:44]=list(struct.pack('<5I',op['now_bits'],op['amount_bits'],0,scalar['hp_1528_bits'],s['max_hp_bits']));origins[24:44]=['semantic']*20;expected_row[44:46]=[rank,0];origins[44:46]=['semantic']*2
  assert want['storage']==[expected_row]+[[None]*48 for _ in range(3)]and want['provenance']==[origins]+[['allocator_unwritten']*48 for _ in range(3)]
  assert got['active'][0]['raw_hex']==got['storage'][0]
  for slot,raw_hex in enumerate(got['storage']):
   raw=bytes.fromhex(raw_hex);assert len(raw)==48
   for j,value in enumerate(want['storage'][slot]):
    if value is None:
     tag=want['provenance'][slot][j];assert tag in('resource_pointer','allocator_unwritten');counts[tag+'_observations']+=1;counts[tag+'_nonzero_observations']+=raw[j]!=0
    else:assert raw[j]==value;counts['strict_backing_bytes']+=1
  for offset,text in zip((0,8,16),strings):
   raw=bytes.fromhex(got['storage'][0]);p,n=struct.unpack_from('<2I',raw,offset);assert n==len(text.encode('utf8'))and p+n<=receipt['runtime']['max_memory_bytes']
  counts['active_rows']+=1;counts['matched_source_rows']+=matched is not None;counts['unmatched_source_rows']+=matched is None
 assert dict(groups)==receipt['groups']and len(pointer_tags-{0})==148
 for key in('resource_pointer_observations','resource_pointer_nonzero_observations','strict_backing_bytes','allocator_unwritten_observations','allocator_unwritten_nonzero_observations','active_rows'):assert counts[key]==receipt['comparison'][key],key
 runtime=load(RUN/'incoming-source135-runtime.json');terminal=load(RUN/'process-terminal.json');assert runtime==receipt['runtime']and terminal==receipt['process']
 assert runtime['calls']==runtime['cases']==163 and runtime['fresh_instances']==21 and runtime['host_calls']==0 and runtime['denied_imports']==878 and runtime['max_memory_bytes']<=33554432 and runtime['memory_pages']==512
 assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and not terminal['timed_out']and process_missing(terminal['pid'])and process_missing(terminal['pgid'],True)
 assert (RUN/'stderr.log').stat().st_size==0 and receipt['differences']==0 and receipt['independent_expected_before_original']and not receipt['original_input_contains_expected']
 runner=(source/'scripts/run_incoming_source135_oracle.mjs').read_text();assert 'source_records_after:sourceAfter'in runner and "const sourceAfter=units.map((_,j)=>slice(U+j*424,424))"in runner
 checker=(source/'scripts/check_incoming_source135.py').read_text();assert checker.index('cases = corpus(')<checker.index('subprocess.Popen(')
 for name,h in files.items():assert digest(ROOT/name)==h==digest(source/name)
 summary=dict(status='scoped_frozen163_incoming_source_history_scalar_independent_review_passed',version='0.135.1',actual_build='90898d5e3',comparison=str((RUN/'incoming-source135-comparison.json').relative_to(ROOT)),comparison_sha256=CAPTURE_SHA,cases=163,frozen_original1073_calls=163,new_original_executions=0,new_production_model_checker_builder_executions=0,differences=0,counts=dict(counts),groups=dict(groups),source_files=20,production_files=9,independent_local_import_edges=len(edges),source_snapshot_current_equal=True,source_import_edges=edges,all148_English_fallback_names_reextracted=True,observed_rank_bytes=sorted(ranks),source_record_bytes_saved_and_independently_compared=True,first_match_including_dead_entry_static_verified=True,unmatched_does_not_consume_inactive_source_fields_static_verified=True,only_export_section_changed=True,complete_original1073_callees_preserved=True,identities=identities,static_names_provenance_sha256=digest(out/'static-fallback-names.json'),runtime=runtime,process=terminal,source_sha256=files,auditor_sha256=digest(Path(__file__)),auditor_utilities={'scripts/review_stats138.py':digest(ROOT/'scripts/review_stats138.py')},owned_audit_process=dict(pid=os.getpid(),pgid=os.getpgrp(),expected_terminal_file='owned-terminal.json'),full880_frames=0,complete_games=0,native_executions=0,elapsed_seconds=round(time.monotonic()-began,3),limitations=['Only original English fallback labels; translation-map producer remains unverified.','Raw classification bytes include7/255; this does not extend1367 recap acceptance beyond its own rank domain.','G1112 source-statistics registry/other keyed heap layout,retaliation/proc and fatal/revival outputs remain unmodeled.','Only declared scalar/history/source-record outputs compared; rawGame retained and bound fieldwise,not wholeGame equality.','Older163 capture and separate pilots are not added.','No current138/native/full-game/880 acceptance follows from this fixed135 component.'])
 dump(out/'review.json',summary);report=ROOT/'reports/2026-11-02-incoming-source0135-independent-review.json';dump(report,summary|dict(evidence=str(out.relative_to(ROOT)),review_sha256=digest(out/'review.json')))
 md=ROOT/'reports/2026-11-02-incoming-source0135-independent-review.md';md.write_text('# Ordinary NPC incoming source135 independent review\n\nRead-only audit passed for163 frozen full1073 calls. No original, production model, checker or builder executed during review.\n\n- Reextracted148 English fallback names directly from pinned original static definition bytes. Independently followed first matching U112 GUID, U244/U40 ordinary guards, U284 name lookup and raw U416 rank.\n- Independently recomputed source strings/rank, nonfatal scalars and all known48B history bytes; retained resource-pointer and allocator-unwritten provenance.\n- Rechecked all persisted source-record bytes from actual WASM reads, full source closure20 files/9 production and'+str(len(edges))+' local import edges, original1073 signature/body and unchanged complete callees.\n- Raw classifications7/255 are accepted only as metadata here; downstream recap rank guards remain intact.\n\nG1112 registry, localized-map production, proc/retaliation, fatal/revival and complete game remain unverified. This is a fieldwise component audit. Older163/pilots are not added.\n\nEvidence: `'+str(out.relative_to(ROOT))+'`; review SHA256 `'+digest(out/'review.json')+'`. Owned terminal receipt is stored alongside the review.\n')
 print(json.dumps(dict(status=summary['status'],evidence=str(out.relative_to(ROOT)),review_sha256=digest(out/'review.json'),report_json_sha256=digest(report),report_md_sha256=digest(md),auditor_sha256=digest(Path(__file__)),counts=dict(counts),edges=len(edges),seconds=summary['elapsed_seconds'])))
if __name__=='__main__':main()
