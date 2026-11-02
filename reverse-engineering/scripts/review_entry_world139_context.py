#!/usr/bin/env python3
"""Independent read-only139 research world/opening context observation review.
No author observer/acquirer/production/original is executed. Captures are read
as data and compared with their stored observations;not independent predictions.
"""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import ast,hashlib,json,mmap,re,sqlite3,struct,time
from urllib.parse import unquote,urlsplit
from review_combat139 import parse_module,local_closure,Reader
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent
CASE=ROOT/'evidence/entry-world139-probe-20261102T023815.931445Z'
RECEIPT_SHA='5d940f9d00f0428327791132f5b9f60df7787348d6fd5a1d50ad840aea1a2964'
HANDOFF_SHA='6913c249e92c155eede510eb83c0041c927c51990d2c4e7b4ed574a697a58507'
OBSERVER=ROOT/'evidence/entry-world139-inspection-20261102T024328.416207Z/observations.json'
OBS_SHA='92367b368fc46666ae75e7e4ffd156209704b4967c1e9732d1688a027b6600db'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm';SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
ALLOW_IDS={0,337,338,343,498,520,522,640,642,643,644,657,658,659,734,772,773,804,831,839,849,852,855,881}
LAYOUT={'NPC':(1784,1788,1792,432),'companions':(2108,2112,2116,88),'pickups':(1868,1872,1876,56),'special':(1916,1920,1924,40),'windows':(1964,1968,1972,8),'boundaries':(2120,2124,2128,8)}

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_text())
def path(value):
 p=Path(value);return p if p.is_absolute()else REPO/p

def main():
 began=time.monotonic();assert sha(CASE/'receipt.json')==RECEIPT_SHA and sha(CASE/'task-handoff.json')==HANDOFF_SHA and sha(OBSERVER)==OBS_SHA and sha(SOURCE)==SOURCE_SHA
 receipt=load(CASE/'receipt.json');handoff=load(CASE/'task-handoff.json');cfg=load(CASE/'config.json');runtime=load(CASE/'runtime.json');result=runtime['result'];observers=load(OBSERVER)['rows'];report=load(ROOT/'reports/2026-11-02-entry-world0139-context.json')
 for n,h in handoff['owned_files'].items():assert sha(ROOT/n)==h
 assert receipt['source_before']==receipt['source_after']and len(receipt['source_before'])==10
 for n,h in receipt['source_before'].items():assert sha(ROOT/n)==h and sha(CASE/'source-snapshot'/n)==h
 assert local_closure(receipt['source_before'])==sorted(receipt['source_import_edges'])and len(receipt['source_import_edges'])==9
 for n,h in receipt['artifacts'].items():assert sha(CASE/n)==h
 assert receipt['runtime']==runtime and cfg['only_changed_section']==7
 raw=SOURCE.read_bytes();original=parse_module(raw);changedraw=(CASE/'entry-world139.wasm').read_bytes();changed=parse_module(changedraw);assert sha(CASE/'entry-world139.wasm')==cfg['wasm_sha256']
 assert len(original['sections'])==len(changed['sections'])
 for a,b in zip(original['sections'],changed['sections']):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==changedraw[b['start']:b['end']]
 exports=[('entry139_load_account',0,2917),('entry139_companion_selection',0,2945),('entry139_construct_world_game',0,6786),('entry139_begin_run',0,1108),('entry139_stack0',3,0)];assert changed['exports']==original['exports']+exports
 glue=SOURCE.parent/'official-wenilla.js';bridge=CASE/'entry-world139-bridge.mjs';prefix=glue.read_bytes();assert len(prefix)==187604 and sha(glue)=='d08ade052f40bcca1da93b559e9e10397ec240ba4975a467d6089ff5407bf3bd'
 append=None
 for node in ast.parse((ROOT/'scripts/probe_entry_world139.py').read_text()).body:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='APPEND'for t in node.targets):append=ast.literal_eval(node.value)
 assert bridge.read_bytes()==prefix+append.encode()and cfg['official_glue_prefix_bytes']==len(prefix)
 assert len(cfg['imports'])==len(original['imports'])==882 and{m['id']for m in cfg['imports']if m['allowed']}==ALLOW_IDS
 for i,(a,b)in enumerate(zip(cfg['imports'],original['imports'])):assert a['id']==i and a['name']==b['name']and a['module']==b['module']and a['type_index']==b['type_index']
 actualimports=result['imports'];counts=Counter(m['id']for m in actualimports);assert len(actualimports)==3396 and len(counts)==16 and set(counts)<ALLOW_IDS
 for m in actualimports:assert m['allowed']is True and m['name']==cfg['imports'][m['id']]['name']and not m.get('error')
 storage=[m for m in actualimports if m['id']==640];assert len(storage)==1 and storage[0]['storage_key']=='rogue.characters'and storage[0]['storage_has_key']is False
 assert not runtime['blocked']and not runtime['browserErrors']and runtime['external_network_permitted']is False and runtime['user_profile_used']is False
 assert result['status']=='original_entry_returned'and result['error']is None and result['page_cap_negative_checked']and not result['all_storage_keys']and not result['session_keys']and not result['indexeddb_databases']
 assert result['appstart_exports_called']is False and result['finalizer_called']is False and result['independent_model_cases']==0
 entries=result['entries'];assert len(entries)==10 and all(e['sequence']==i and e['returned']and e['stack_before']==e['stack_after']==1048576 for i,e in enumerate(entries))
 components=[e['name']for e in entries if e['name']!='__wbindgen_malloc'];assert components==[x[0]for x in exports[:4]]and sum(e['name']=='__wbindgen_malloc'for e in entries)==6
 snapshots={s['label']:s for s in result['snapshots']};before=snapshots['declared_input_before_account'];App,G=before['App'],before['G'];assert(App,G)==(14680072,14685248)and before['world_cache5116']==0
 initial=bytes.fromhex(before['app5168_hex']);profile=bytearray(376);P=App+3376;np=struct.unpack_from('<I',initial,3376+168)[0];struct.pack_into('<I',profile,156,4);struct.pack_into('<I',profile,168,np);struct.pack_into('<I',profile,172,6);profile[344]=profile[345]=1
 assert bytes(profile)==bytes.fromhex(before['selected376_hex'])==initial[3376:3752]
 declared=bytearray([165])*5168;declared[3376:3752]=profile;struct.pack_into('<Q',declared,4928,0);struct.pack_into('<I',declared,5116,0);struct.pack_into('<Q',declared,4776,0);struct.pack_into('<I',declared,5163,4278255360);declared[4768:4772]=initial[4768:4772];struct.pack_into('<I',declared,4772,1410440);assert bytes(declared)==initial
 account=snapshots['after_real_account2917'];selected=snapshots['after_real_companion_selection2945'];aP=bytes.fromhex(account['app5168_hex'])[3376:3752];sP=bytes.fromhex(selected['app5168_hex'])[3376:3752]
 assert aP==profile;expected=(bytes(4)+bytes([255,165,165,165]))*2
 assert sP[224:240]==expected and sP[:224]==aP[:224]and sP[240:]==aP[240:]
 assert entries[5]['args']==[App+4160]and entries[7]['args'][1]==App+4160 and entries[8]['args']==[G,App]and entries[9]['args']==[G]
 assert account['game2592_hex']==selected['game2592_hex']==bytes([165]*2592).hex()
 assetdir=path(cfg['resource_map_path']).parent;assert sha(assetdir/'resource-map.json')==cfg['resource_map_sha256']==handoff['resource_map_sha256'];assert sha(assetdir/'receipt.json')==cfg['asset_acquisition_receipt_sha256']==handoff['asset_receipt_sha256']
 assetmap=load(assetdir/'resource-map.json');assert len(assetmap)==454 and sum(x['bytes']for x in assetmap.values())==85332479
 acquisitions=[];seen=set()
 def chain(p):
  p=path(p);assert str(p)not in seen;seen.add(str(p));a=load(p);assert a['version']=='0.139.0'and a['stamp']=='f339dd20e0fe'and a['old_resource_bytes_reused']is False and a['target_executions']==0
  previous=a.get('prior_fresh139_receipt')
  if previous:assert sha(path(previous))==a['prior_fresh139_receipt_sha256'];chain(previous)
  acquisitions.append((p,a))
 chain(assetdir/'receipt.json');assert len(acquisitions)==3
 source_rows={};coherence=[]
 for j,(p,a)in enumerate(acquisitions):
  assert(a['status']=='failed_preserved')if j<2 else(a['status']=='fresh_official139_candidate_resource_set_acquired')
  if j<2:assert sha(p.parent/'source-snapshot/acquire_entry_assets139.py')==a['source_sha256_before']==a['source_sha256_after']
  else:assert sha(ROOT/'scripts/acquire_entry_assets139.py')==a['source_sha256_before']==a['source_sha256_after']
  meta=p.parent/'files/metadata-before.json';page=p.parent/'files/metadata-before.html';assert load(meta)['version']=='0.139.0'and'f339dd20e0fe'in page.read_text()
  if j==2:assert meta.read_bytes()==(p.parent/'files/metadata-after.json').read_bytes()and'f339dd20e0fe'in(p.parent/'files/metadata-after.html').read_text()
  coherence.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),status=a['status'],requests=len(a['requests']),decoded_bytes=a['decoded_bytes'],metadata_sha256=sha(meta)))
  for q in a['requests']:
   if q.get('exit_code')==0 and q.get('http_status')==200:source_rows[(q['name'],q['sha256'])]=(p,q)
 for key,a in assetmap.items():
  p=path(a['file']);assert p.stat().st_size==a['bytes']and sha(p)==a['sha256'];assert(key,a['sha256'])in source_rows and a['http_status']==200 and a['exit_code']==0 and a['pid_missing']and a['pgid_missing']
  admitted_receipt,admitted_request=source_rows[(key,a['sha256'])]
  assert p.resolve()==(admitted_receipt.parent/'files'/key).resolve()
  assert urlsplit(a['url']).netloc=='wow.aethus.pl'and urlsplit(a['url']).scheme=='https';assert p.resolve().is_relative_to(ROOT/'originals')and p.parent!=SOURCE.parent
 currentindex=load(path(assetmap['data/__index']['file']));names={s.replace('\\','/').lower()for s in currentindex};assert all(k[5:]in names for k in assetmap if k!='data/__index')
 assert acquisitions[-1][1]['requests']and all(q.get('pid_missing',True)and q.get('pgid_missing',True)for _,a in acquisitions for q in a['requests']if 'pid'in q)
 requests=runtime['requests'];resources=[q for q in requests if q['path'].startswith('/data/')];assert len(resources)==561 and all(q['status']==200 for q in requests)
 for q in resources:
  k='data/'+unquote(q['path'][6:]);a=assetmap[k];assert q['source_sha256']==q['sha256']==a['sha256']and q['bytes']==a['bytes']
 assert len({q['path']for q in resources})==454
 posts=[q for q in requests if q['method']=='POST'];assert len(posts)==276;assert sum(q['bytes']for q in posts)==111804416+177078272
 for cap in runtime['captures']:
  pp=[q for q in posts if q['path']=='/capture/'+cap['file']];assert len(pp)==math_ceil(cap['bytes'],1048576)and all(0<q['bytes']<=1048576 for q in pp)and sum(q['bytes']for q in pp)==cap['bytes']
 def staticread(address,n):
  answer=bytearray(n)
  for a,b,size in original['data_segments']:
   if a is None:continue
   lo,hi=max(a,address),min(a+size,address+n)
   if lo<hi:answer[lo-address:hi-address]=raw[b+lo-a:b+hi-a]
  return bytes(answer)
 vtable=list(struct.unpack('<9I',staticread(1410440,36)));assert vtable==[284,24,8,285,286,287,288,289,290]
 sec=next(q for q in original['sections']if q['kind']==9);er=Reader(raw,sec['payload'],sec['end']);assert er.uint()==1 and er.uint()==0 and er.byte()==0x41;base=er.sint();assert er.byte()==0x0b;elements=[er.uint()for _ in range(er.uint())];er.end();assert elements[290-base]==177894;ba,bb=original['bodies'][177894];assert raw[ba:bb].hex()=='0041000b'
 db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');proof=load(ROOT/'evidence/opening139-context-static-20261102T022955.014560Z/proof.json');assert sha(ROOT/'evidence/opening139-context-static-20261102T022955.014560Z/proof.json')==cfg['static_proof_sha256']
 static_functions={};texts={}
 with(PROFILE/'official-0.139.0-full.wat').open('rb')as w:
  for idx in[2917,2945,6786,1108,4562,20060,83304,48446,66941]:
   loc=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());assert(loc['body_start'],loc['body_end'])==original['bodies'][idx];w.seek(loc['wat_start']);wat=w.read(loc['wat_end']-loc['wat_start']);texts[idx]=wat.decode();h=hashlib.sha256(raw[loc['body_start']:loc['body_end']]).hexdigest();static_functions[idx]=dict(body_sha256=h,wat_sha256=hashlib.sha256(wat).hexdigest(),**loc)
   if str(idx)in proof['selected_functions']:assert h==proof['selected_functions'][str(idx)]['body_sha256']and static_functions[idx]['wat_sha256']==proof['selected_functions'][str(idx)]['wat_sha256']
 for caller,callee in[(2917,48446),(48446,66941),(66941,640),(20060,83304)]:assert db.execute('select count(*) from calls where caller=? and callee=?',(caller,callee)).fetchone()[0]==1
 selection_lines=[x.strip()for x in texts[2945].splitlines()]
 first_rebind=next(i for i,s in enumerate(selection_lines)if s in('local.tee 0','local.set 0'))
 stores=[]
 for i,s in enumerate(selection_lines[:first_rebind]):
  if '.store'in s and 'local.get 0'in selection_lines[max(0,i-5):i]:
   match=re.match(r'([if](?:32|64))\.store(8|16|32)?(?: offset=(\d+))?',s)
   assert match
   stores.append(dict(relative_line=i+1,instruction=s,offset=int(match[3]or 0),width=int(match[2])//8 if match[2]else int(match[1][1:])//8))
 assert first_rebind+1==1204 and len(stores)==12 and not any('.store'in s for s in selection_lines[first_rebind:])
 written={i for s in stores for i in range(s['offset'],s['offset']+s['width'])}
 assert max(written)+1==36 and len(written)==30 and sorted(set(range(36))-written)==[5,6,7,13,14,15]
 output_allocation=entries[6]['args'][0]
 assert output_allocation==16 and entries[6]['name']=='__wbindgen_malloc'
 output_layout_finding=dict(function=2945,required_minimum_output_bytes=36,declared_allocated_bytes=output_allocation,written_bytes=30,first_local0_rebind_line=1204,stores=stores,padding_offsets=[5,6,7,13,14,15],written_outside_declared_allocation=sorted(written-set(range(output_allocation))),observed_first16_hex=expected.hex(),legal_output_allocation=False,physical_heap_corruption_proven=False)
 assert staticread(1758543,16)==b'rogue.characters'and 'i32.const 1758449'in texts[4562]and staticread(1758449,23)==b'DBFilesClient\\Spell.dbc'and staticread(1758472,27)==b'DBFilesClient\\SpellIcon.dbc'
 assert 'i32.const 14476488'in texts[20060]and 'call 83304'in texts[20060]and 'i32.const 14'in texts[83304]and'i32.const 28'in texts[83304]
 #Each declaration is28B:JSONptr,len,reserved,idptr,len,nameptr,len.
 locale=[]
 for j in range(14):
  p=5401532+28*j;jp,jn,tag,ip,il,np,nl=struct.unpack('<7I',staticread(p,28));value=json.loads(staticread(jp,jn));locale.append(dict(id=staticread(ip,il).decode(),name=staticread(np,nl).decode(),JSON_bytes=jn,JSON_sha256=hashlib.sha256(staticread(jp,jn)).hexdigest(),JSON_type=type(value).__name__))
 captures=[]
 for record,obs in zip(runtime['captures'],observers):
  p=CASE/record['file'];assert p.stat().st_size==record['bytes']and sha(p)==record['sha256']==obs['input_sha256'];assert record['complete']and record['bytes']%65536==0
  with p.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as memory:
   def get(p,n):assert 0<=p<=p+n<=len(memory);return memory[p:p+n]
   def u(p):return struct.unpack('<I',get(p,4))[0]
   def q(p):return struct.unpack('<Q',get(p,8))[0]
   def hex(p,n):return get(p,n).hex()
   snap=snapshots['after_real_world6786'if obs['phase2587']==0 else'after_real_begin1108'];assert u(App+5116)==u(G+2348)==snap['world_rc_pointer']==20544640
   assert hex(App,5168)==snap['app5168_hex']==obs['raw_App5168_hex']and hex(G,2592)==snap['game2592_hex']==obs['raw_Game2592_hex']and hex(20544640,124)==snap['world_rc124_hex']==obs['raw_worldRc124_hex']
   assert hex(P,376)==obs['selected376_hex']and hex(App+4160,368)==obs['account368_hex']and get(P+224,16)==bytes(expected)
   assert get(G+2587,1)[0]==obs['phase2587']and u(G+2408)==obs['counter2408']and[u(G+1720+4*j)for j in range(4)]==obs['rng_words']and[u(G+1416+4*j)for j in range(3)]==obs['player_xyz']
   for name,(co,po,no,stride)in LAYOUT.items():
    cap,ptr,count=u(G+co),u(G+po),u(G+no);assert count<=cap<=4096;v=obs['vectors'][name];assert v==dict(capacity=cap,pointer=ptr,count=count,stride=stride,storage_hex=[hex(ptr+j*stride,stride)for j in range(cap)])
   for co,po,no,stride,key in[(1880,1884,1888,16,'packets'),(1892,1896,1900,12,'notifications')]:
    cap,ptr,count=u(G+co),u(G+po),u(G+no);v=obs[key];assert cap==v['capacity']and ptr==v['pointer']and count==v['count']and hex(ptr,cap*stride)==v['metadata_backing_hex']
    for j,e in enumerate(v['entries']):
     ep=ptr+j*stride;size,pp,n=u(ep),u(ep+4),u(ep+8);assert n<=size<=1048576 and(size,pp,n)==(e['capacity'],e['pointer'],e['length'])and hex(pp,n)==e['payload_hex']and hex(ep,stride)==e['metadata_hex']
     if key=='packets':assert struct.unpack('<H',get(ep+12,2))[0]==e['opcode']
   for n in obs['NPC_observations']:
    up=obs['vectors']['NPC']['pointer']+432*n['index'];dp=u(up+284);np,nl=u(dp+16),u(dp+20);assert n==dict(index=n['index'],guid=str(q(up+112)),definition_pointer=dp,definition72_hex=hex(dp,72),definition_name_utf8_hex=hex(np,nl),definition_name=get(np,nl).decode(),entry=u(dp+24),HP288_bits=u(up+288),classification424=get(up+424,1)[0],new416=u(up+416),new420=u(up+420),tail427_431_observed_hex=hex(up+427,5))
   assert get(14476488,1)[0]==3 and u(14476484)==14 and u(14476480)==21017688
   captures.append(dict(file=record['file'],bytes=len(memory),sha256=record['sha256'],phase=obs['phase2587'],counter=obs['counter2408'],counts={k:v['count']for k,v in obs['vectors'].items()},packet_count=obs['packets']['count'],notification_count=obs['notifications']['count'],worldRc=20544640,worldRc_prefix_counts=[u(20544640),u(20544644)],locale_Once=3,locale_count=14,locale_pointer=21017688,spell_Once=get(14476440,1)[0]))
 assert[c['phase']for c in captures]==[0,1]and captures[0]['packet_count']==captures[0]['notification_count']==0 and all(x==0 for x in captures[0]['counts'].values())
 assert captures[1]['counts']==dict(NPC=4,companions=0,pickups=2,special=4,windows=2,boundaries=69)and captures[1]['counter']==85 and captures[1]['packet_count']==76 and captures[1]['notification_count']==1
 assert json.loads(bytes.fromhex(observers[1]['notifications']['entries'][0]['payload_hex']))['type']=='start'
 process=receipt['process'];assert process['exit_code']==0 and process['pid_missing']and process['pgid_missing']and process['seconds']<120;assert receipt['validator']['exit_code']==0 and receipt['validator']['pid_missing']and receipt['validator']['pgid_missing']
 terminal=runtime['lifecycle'][-1];assert terminal['event']=='browser_terminal'and terminal['pid']==85059 and terminal['exit_code']==0 and terminal['signal_code']is None
 assert result['max_memory_bytes']==177078272<268435456 and cfg['memory_page_cap']==4096
 assert receipt['independent_model_cases']==0 and receipt['natural_App_produced']is False and receipt['selected_profile_producer_complete']is False
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('entry-world139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 review=dict(status='not_accepted_as_legal_context_2945_output_underallocated',legal_context_gate_passed=False,observation_byte_audit_completed=True,output2945_allocation_finding=output_layout_finding,author_handoff_sha256=HANDOFF_SHA,receipt_sha256=RECEIPT_SHA,observations_sha256=OBS_SHA,source_wasm_sha256=SOURCE_SHA,
  unchanged_nonexport_sections=True,official_JS187604prefix_byte_identical=True,only_append_research_bindings=True,current_source_closure_files=10,current_source_closure_edges=9,source_snapshots_hashes_unchanged=True,
  allowed_imports=24,actual_import_ids=len(counts),actual_host_calls=3396,actual_import_counts=dict(counts),denied_invocations=0,resource_requests=561,unique_resource_requests=454,resource_non200=0,current_resources_rehashed=454,current_resource_bytes=85332479,fresh139_acquisition_chain=coherence,
  outer_export_entries=10,real_components=components,malloc_entries=6,entry_stacks_all_restored=True,selected376_declared_input_and_absentA5_slots_checked=True,selected_profile_is_natural=False,App_is_natural=False,worldRc_produced_by6786_not_flatV=True,transport_const0_vtable_original=True,
  full_capture_chunk_POSTs=276,capture_bytes_total=sum(c['bytes']for c in captures),captures=captures,all6vectorbacking_andallpacket_notificationbytes_match_inspector=True,static_functions=static_functions,account_call_chain=[2917,48446,66941,640],Spell4562='LiteralDBFilesClientSpell.dbc/SpellIcon.dbcresolver;notlocaleproducer',locale_actual_chain=[20060,83304],locale_static14_JSON_declarations=locale,locale_independent_producer=False,
  author_original_calls=4,reviewer_original_calls=0,reviewer_author_observer_or_acquirer_executions=0,reviewer_model_executions=0,independent_opening_model_cases=0,native_executions=0,author_owned_process=process,browser_terminal=terminal,
  inspector_outputs_are_observations_not_expected_results=True,old_snapshot_loaded=False,old_resource_bytes_reused=False,source_script_sha256=sha(Path(__file__)),pure_review_parser_sha256=sha(ROOT/'scripts/review_combat139.py'),seconds=time.monotonic()-began,
  boundaries=['ResearchApp/profile/transportarenotnaturalApp/menu/producers;selectedabsenttags255comeonlyfromreal2917→2945','InputinactiveA5payloadsremainobservedinputbytes,notindependentknown/defaultzero','ActualnewRcproducedby6786,butindependentworldproducerandRc/JS/externreflifetimearenotrestored','24allowedrealJSimports/3396actualhostcalls;thisisnot882denyallnumericoracle','LocaleOnce3/count14/pointerareobservations;noindependentlanguagechoiceorEnglishproduceraccepted','Onlypoint-in-timeofficial139manifest/stamp/indexandper-resourceHTTP/hashcoherence;noexternalsignedassetmanifestclaim','Noindependent1108/continuousgame/win/save/render/UI/network/nativeacceptance','Previousinitial139zero376fixtureisadifferentprofiledomain;its502knownmaskdidnotpredictcompanioninactive16B','Phase1windowcount1972=2doesnotmeetearlierdamageempty1972admission;donotsilentlypassasempty'])
 (out/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),legal_context_gate_passed=False,captures=len(captures),host_calls=3396,resource_requests=561,seconds=review['seconds'])),flush=True)
def math_ceil(n,d):return(n+d-1)//d
if __name__=='__main__':main()
