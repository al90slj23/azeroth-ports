#!/usr/bin/env python3
"""Independent read-only audit of one whole-original-App observation."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,hashlib,json,math,mmap,os,sqlite3,struct,sys
sys.dont_write_bytecode=True
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries
from build_upgrade134_oracle import Reader,source_memory

BATCH=ROOT/'evidence/full-app0135-probe-20261101T122659.584362Z'
RECEIPT_SHA='8a8bc535e373eacf31e33433e63e1e8f1930d7a2c1389582df2609f0ce0e95d8'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'

def sha(path):
 with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
def u64bits(value):return int.from_bytes(struct.pack('<d',value),'little')

def header(buffer,App):
 d=lambda p:struct.unpack_from('<I',buffer,p)[0]
 q=lambda p:struct.unpack_from('<Q',buffer,p)[0]
 marker=q(App)
 return dict(App=App,Rc=App-16,strong=d(App-16),weak=d(App-12),borrow=buffer[App-8],borrow_padding_hex=buffer[App-7:App-4].hex(),marker_u64=str(marker),previous_bits_u64=str(q(App+8)),clock_previous_active=marker==1,previous_seconds=struct.unpack_from('<d',buffer,App+8)[0]if marker==1 else None,game_tag_u64=str(q(App+16)),second_tag=d(App+2608),profile_tag=d(App+3376),transport_pointer=d(App+4768),transport_vtable=d(App+4772),world_cache=d(App+5116),memory_bytes=len(buffer))

def main():
 own=Path(__file__);own_sha=sha(own);rp=BATCH/'receipt.json';assert sha(rp)==RECEIPT_SHA
 receipt=load(rp);config=load(BATCH/'config.json');runtime=load(BATCH/'runtime.json');result=runtime['result']
 assert receipt['runtime']==runtime and receipt['status']==runtime['status']=='observed_original_app_and_complete_idle_tick'
 assert sha(BATCH/'config.json')==receipt['config_sha256']=='37dde85ff8bf643b039639321a6e20e36c66236e35e18634f46386ea89060548'
 before=receipt['source_sha256_before'];assert before==receipt['source_sha256_after']==config['source_sha256'] and len(before)==10
 for name,h in before.items():
  assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
  if name.endswith('.py'):ast.parse((ROOT/name).read_text())
 # Independently inspect local script imports rather than trust the declared list.
 closure=set();todo=[ROOT/'scripts/probe_full_app135.py',ROOT/'scripts/probe_entry_world135.py',ROOT/'reconstruction/resource_spec/mpq.py',ROOT/'reconstruction/resource_spec/__init__.py']
 while todo:
  path=todo.pop();key=str(path.relative_to(ROOT))
  if key in closure:continue
  closure.add(key)
  for node in ast.walk(ast.parse(path.read_text())):
   names=[x.name for x in node.names]if isinstance(node,ast.Import)else[node.module]if isinstance(node,ast.ImportFrom)and node.module else[]
   for name in names:
    candidate=ROOT/'scripts'/((name.split('.')[0])+'.py')
    if candidate.is_file():todo.append(candidate)
 assert closure|{'scripts/run_full_app135.mjs','scripts/browser_full_app135.mjs'}==set(before)
 for key,digest_key in(('node_path','node_sha256'),('chrome_path','chrome_sha256'),('aux_path','aux_sha256'),('name_index_path','name_index_sha256')):assert sha(Path(config[key]))==config[digest_key]
 package=Path(config['playwright_path'])/'package.json';assert sha(package)==config['playwright_package_sha256'] and load(package)['version']==config['playwright_version']=='1.64.1'
 glue=Path(config['glue_path']).read_bytes();official=ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js';official_bytes=official.read_bytes()
 assert sha(official)==config['official_glue_sha256'] and glue[:config['glue_prefix_bytes']]==official_bytes
 assert hashlib.sha256(glue).hexdigest()==receipt['bridge_sha256']==config['glue_sha256']
 append=glue[config['glue_prefix_bytes']:].decode()
 assert 'Reflect.apply(fn,this,args)'in append and 'return __wbg_finalize_init(instance,module)'in append and "observe('original_finalizer_entry'"in append
 browser_text=(ROOT/'scripts/browser_full_app135.mjs').read_text();host_text=(ROOT/'scripts/run_full_app135.mjs').read_text()
 assert 'hostEvents>1000000'not in browser_text and 'if(imports.length<20000)'in browser_text
 assert 'new Uint8Array(buffer).slice()'in browser_text and 'header(x.App,frozen.buffer)'in browser_text and 'body:frozen.subarray('in browser_text
 assert 'frame.before.borrow===0&&frame.returned===true&&frame.after.borrow===0'in browser_text
 assert "connect-src 'self'"in host_text and "server.on('upgrade'"in host_text and 'MAP * ~NOTFOUND'in host_text
 assert "new URL(route.request().url()).origin!==origin"in host_text and "server:'http://127.0.0.1:9'"in host_text and "serviceWorkers:'block'"in host_text
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA==receipt['original_sha256']==config['original_sha256']
 types,imports,decl,bodies,segments=parse_source(raw);sections=section_list(raw);exports,_=export_entries(raw,next(x for x in sections if x[0]==7))
 assert len(imports)==878 and all(x[0]!=8 for x in sections)
 assert dict((name,index)for name,kind,index in exports if kind==0)['__wbindgen_start']==176107
 assert imports[517][1]=='__wbg_setInterval_ae27514ca815a798' and imports[867][1]=='__wbindgen_cast_0000000000000010'
 assert imports[681][1]=='__wbg_now_f565250295e2d180'
 assert types[imports[517][2]]==(bytes.fromhex('6f6f7f'),bytes.fromhex('7f')) and types[imports[867][2]]==(bytes.fromhex('7f7f'),bytes.fromhex('6f'))
 assert ('wasm_bindgen_98522a9d8f8d72e2___convert__closures_____invoke_______true_',0,104471)in exports
 vtable,offset,segment=source_memory(raw,segments,5305816,24);words=struct.unpack('<6I',vtable)
 element=next(x for x in sections if x[0]==9);reader=Reader(raw,element[2],element[3]);assert reader.uint()==1 and reader.uint()==0 and reader.byte()==0x41
 base=reader.sint();assert reader.byte()==0x0b;entries=[reader.uint()for _ in range(reader.uint())];reader.finished();assert entries[words[4]-base]==83825
 db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;static=[];texts={}
 with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  for idx in(176107,4253,122123,104471,83825,174119,880):
   row=dict(db.execute('select *from functions where idx=?',(idx,)).fetchone());wat.seek(row['wat_start']);text=wat.read(row['wat_end']-row['wat_start']);texts[idx]='\n'.join(x.strip()for x in text.decode().splitlines());static.append(dict(index=idx,**row,wat_sha256=hashlib.sha256(text).hexdigest(),body_sha256=hashlib.sha256(raw[slice(*bodies[idx])]).hexdigest()))
 assert 'call 4253'in texts[176107] and 'call 867'in texts[122123]
 assert 'i32.const 5305816\ncall 122123'in texts[4253] and 'i32.const 25\ncall 517'in texts[4253]
 assert 'i32.load offset=16\ncall_indirect (type 3)'in texts[104471]
 assert 'i32.load8_u offset=8'in texts[83825] and 'f64.div\ncall 880'in texts[83825] and 'call 681'in texts[174119]
 assert result['adapterInfo']=={'vendor':'apple','architecture':'metal-3'} and result['confirmed_complete880_returns']==result['callback_returns']==8
 assert result['original_finalizer_entered'] and result['original_appstart_called'] and result['initializationReturned']
 assert result['wasm_memory_written_by_research']is False and result['original_function_bodies_changed']is False
 assert result['independent_model_cases']==result['new_independent_mainloop_frames']==receipt['new_independent_cases']==receipt['new_independent_mainloop_frames']==0
 assert len(result['imports'])==20000 and result['hostEvents']==result['hostCalls']*2 and result['import_details_truncated']
 contexts=result['contexts'];assert len(contexts)==len(result['timers'])==1;context=contexts[0];App=context['App'];Rc=context['Rc'];env=context['env']
 assert struct.unpack_from('<I',bytes.fromhex(context['closure_env12_hex']),8)[0]==Rc and App==Rc+16
 assert result['timers'][0]['env']==env and result['timers'][0]['vtable']==5305816 and result['timers'][0]['interval_ms']==25 and result['timers'][0]['returns']==8
 cast=bytes.fromhex(context['app5168_hex_at_cast']);assert len(cast)==5168
 assert struct.unpack_from('<Q',cast)[0]==0 and struct.unpack_from('<Q',cast,16)[0]==2 and struct.unpack_from('<I',cast,3376)[0]==2
 frames=result['frames'];assert len(frames)==8
 for i,frame in enumerate(frames):
  assert frame['index']==i and frame['App']==App and frame['returned'] and frame['confirmed_complete880_return']
  assert frame['before']['borrow']==frame['after']['borrow']==0 and frame['borrow_gate_status']=='eligible_and_restored'
  assert frame['before']['game_tag_u64']==frame['after']['game_tag_u64']=='2'
  assert len(frame['original_now_values_ms'])==1
  now=frame['original_now_values_ms'][0];assert math.isfinite(now) and int(frame['after']['previous_bits_u64'])==u64bits(now/1000)
  assert frame['after']['marker_u64']=='1'
  if i:assert frame['before']['previous_bits_u64']==frames[i-1]['after']['previous_bits_u64']
  else:assert frame['before']['marker_u64']=='0'
 capture=BATCH/'original_app.memory';assert capture.stat().st_size==result['capture']['bytes']==419692544
 assert sha(capture)==result['capture']['sha256']=='17be706e1fc91beb8851389ba56e8cbeb340f9b7ec419c7e0ace44c6ef3f8781'
 assert result['capture']['complete'] and result['capture_synchronously_copied_unshared_memory'] and result['final_header_from_same_frozen_copy']
 with capture.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as memory:
  assert header(memory,App)==context['final']
  assert struct.unpack_from('<I',memory,env+8)[0]==Rc and context['final']['previous_bits_u64']==frames[-1]['after']['previous_bits_u64']
  assert context['final']['game_tag_u64']=='2' and context['final']['world_cache']==0
 assert result['memory_bytes']==476643328>capture.stat().st_size and result['memory_bytes']<=config['memory_cap_bytes']==536870912
 requests=runtime['requests'];assert len(requests)==999 and all(row['status']==200 for row in requests)
 methods=Counter(row['method']for row in requests);assert methods=={'GET':598,'POST':401}
 assert all(row['path']=='/capture/original_app.memory'for row in requests if row['method']=='POST')
 assert methods['POST']==math.ceil(capture.stat().st_size/config['capture_chunk_bytes'])
 assert runtime['errors']==runtime['blocked']==[]
 presence=[x for x in runtime['logs']if 'https://wow.aethus.pl/presence'in x['text']]
 assert presence and all('Content Security Policy'in x['text']and 'blocked'in x['text']for x in presence)
 assert not any('presence'in x['path']for x in requests)
 assert result['renderer_observation_status']=='no_renderer_error_reported_not_visual_acceptance'
 inventory=load(BATCH/'actual-assets-inventory.json');assert len(inventory['requests'])==535 and inventory['decoded_bytes']==53898024
 assert inventory['decoded_bytes']<=config['asset_decoded_byte_budget']==268435456 and len(inventory['requests'])<=config['asset_file_budget']==1024
 archives=ROOT/'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data';asset_audit=[]
 for asset in inventory['requests']:
  assert asset['status']==200;file=Path(asset['file']);assert file.is_relative_to(BATCH/'actual-assets')
  payload=file.read_bytes();assert len(payload)==asset['bytes'] and hashlib.sha256(payload).hexdigest()==asset['sha256']
  block=asset['block'];assert block['flags']==0x80000000 and block['compressed_size']==block['size']==len(payload)
  with(archives/asset['archive']).open('rb')as stream:stream.seek(block['offset']);assert stream.read(len(payload))==payload
  asset_audit.append(dict(chain=asset['chain'],bytes=len(payload),sha256=asset['sha256'],archive=asset['archive'],offset=block['offset']))
 font=Path(config['font_path']);font_bytes=font.read_bytes();assert sha(font)==config['font_sha256']=='5499291b696324c10c3e7f2d3d89a5c490897319a629141ea5b40c85e62e6224' and len(font_bytes)==config['font_bytes']==1225412
 assert config['font_origin_url']=='https://wow.aethus.pl/data/fonts/azs_sc.ttf'
 font_receipt=load(font.parent/'receipt.json');assert font_receipt['sha256']==sha(font) and font_receipt['url']==config['font_origin_url']
 exe=ROOT/'originals/official-acquisition-20261101T030310.926207Z/windows-0.135.1/AzerothSurvivors.exe';assert sha(exe)=='71e5f1767279db4bd428d1cd9c5d50d37759b72295386a69f9e3f6e70bc59249'
 with exe.open('rb')as stream:stream.seek(120912388);assert stream.read(len(font_bytes))==font_bytes
 font_requests=[x for x in requests if x['path']=='/data/fonts/azs_sc.ttf'];assert len(font_requests)==1 and font_requests[0]['status']==200 and 'asset'not in font_requests[0]
 term=receipt['process']['terminal'];assert term['all_owned_terminal'] and all(term['owned_pids'].values())and all(term['owned_pgids'].values())
 for pid in term['owned_pids']:assert missing(int(pid))
 for group in term['owned_pgids']:assert missing(int(group),True)
 assert receipt['process']['exit_code']==0 and receipt['process']['seconds']<=120
 starts={x['label']:x for x in runtime['events']if x['label'].endswith('_started')};assert starts['worker_started']['pgid']==receipt['process']['pgid'] and starts['browser_started']['pgid']==starts['browser_started']['pid']
 args=starts['browser_started']['spawnargs'];assert '--use-angle=metal'in args and '--proxy-server=http://127.0.0.1:9'in args and any('user-data-dir='+str(BATCH/'tmp')in x for x in args)
 history=[]
 for name,h,diagnosis_sha in[('120144.289175','fd5dba35d0aeacffe822ce070fd5bc218da8352a5b725e48c166df289b91c726','c10ee16f2d568c9cfcff91c5f95bb236593271202a77ece0a261458902c57998'),('121656.691420','3bc5f80d9d791194bf0257d9b8dbfd3271b36a1720c12abee14a065b5ffb7512','edac4248ae00ebf9d4ad669916b170e8a5ccdee22b9dc6186188322af6319148')]:
  old=ROOT/f'evidence/full-app0135-probe-20261101T{name}Z';assert sha(old/'receipt.json')==h and sha(old/'post-exit-diagnosis.json')==diagnosis_sha
  r=load(old/'runtime.json');rec=load(old/'receipt.json');assert rec['process']['terminal']['all_owned_terminal']
  if name.startswith('120144'):assert any('createBuffer'in x['text']and('failed'in x['text']or'Failure'in x['text'])for x in r['logs']) and any('unreachable'in x for x in r['errors'])
  else:
   assert any('Declared import observation budget'in x for x in r['errors'])
   failed=[x for x in r['requests']if x.get('status')==404];assert len(failed)==3 and all(x['path']=='/data/fonts/azs_sc.ttf'for x in failed)
   old_text=(old/'source-snapshot/scripts/browser_full_app135.mjs').read_text();assert "if(hostEvents>1000000)throw Error('Declared import observation budget')"in old_text
  history.append(dict(directory=str(old.relative_to(ROOT)),receipt_sha256=h,post_exit_diagnosis_sha256=diagnosis_sha,counters_not_added=True))
 for name,h in before.items():assert sha(ROOT/name)==h
 assert sha(own)==own_sha and sha(rp)==RECEIPT_SHA
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('full-app0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 (out/'static-callback-chain.json').write_text(json.dumps(dict(vtable5305816_hex=vtable.hex(),table_slot_at16=words[4],original_target=83825,functions=static),indent=2)+'\n')
 (out/'asset-payload-audit.json').write_text(json.dumps(asset_audit,indent=2)+'\n')
 review=dict(status='passed_scoped_independent_read_only_review',reviewer_sha256=own_sha,receipt=str(rp.relative_to(ROOT)),receipt_sha256=RECEIPT_SHA,source_closure=10,current_and_frozen_sources_verified=True,original_wasm_whole_identity_verified=True,official_glue_prefix_byte_identical=True,
  actual_adapter=result['adapterInfo'],observed_original_App_contexts=1,eligible_original_complete_idle880_returns=8,Game_tag2_no_run_world=True,callback_identity_static_chain_verified=True,clock_ms_to_seconds_exact_f64_bits=True,
  frozen_capture_bytes=capture.stat().st_size,frozen_capture_sha256=sha(capture),live_memory_bytes_after_upload=result['memory_bytes'],header_from_same_frozen_capture_verified=True,mpq_assets_raw_payloads_rechecked=535,mpq_decoded_bytes=53898024,official_non_MPQ_font_bytes=len(font_bytes),official_non_MPQ_font_sha256=sha(font),font_native_static_offset=120912388,font_native_static_full_bytes_equal=True,
  HTTP_requests=999,HTTP_all200=True,page_errors=0,CSP_blocked_presence_attempts=len(presence),actual_presence_HTTP_request_observed=False,network_intent_present=True,live_multiplayer_validated=False,all_owned_processes_and_groups_terminal=True,old_runs=history,screenshot_sha256=sha(BATCH/'original-app.png'),
  screenshot_visual_check='Reviewer viewed actual original Chinese character/class/region selection UI; this is original rendering, not reconstructed UI or gameplay acceptance.',original_program_reexecuted_by_reviewer=False,new_independent_cases=0,new_independent_mainloop_frames=0,complete_game=False,
  limitations=['Complete original App construction and8 idle880 returns only; Game remainsNone tag2 and no world/run is entered.','Real browser/API/GPU domain is distinct from pureNode878deny/32MiB component oracles.','Presence networking intent was explicitly blocked by CSP; no co-op/server/protocol acceptance.','Import details truncate at20000; counters record12,133,225 before calls and24,266,450 total events; not all import arguments retained.','Native font inclusion is static evidence only; Windows program was not executed.','One screenshot and absence of reported renderer errors do not validate all UI/render/audio/performance/game behavior.'],evidence_files={p.name:sha(p)for p in out.iterdir()})
 target=out/'review.json';target.write_text(json.dumps(review,indent=2)+'\n');report=ROOT/'reports/2026-11-01-full-app0135-independent-review.json';report.write_text(json.dumps({**review,'review_path':str(target.relative_to(ROOT)),'review_sha256':sha(target)},indent=2)+'\n')
 report.with_suffix('.md').write_text(f'''# 完整原App初始化与idle880观察独立复核

限定原件观察独审通过：[最终收据](../{rp.relative_to(ROOT)})及10源、原WASM90MB身份、官方JS187,006B前缀和append delegate桥均核实。[独审证据](../{target.relative_to(ROOT)}) SHA `{sha(target)}`。本复核未重跑原件。

真实Apple／metal-3上观察1个原4253构造App，实际cast867／vtable5305816／env+8 Rc+16 App、517注册25ms、104471动态转83825再进完整880的原body／表项均重新静态核对。8次before borrow0、正常返回、after borrow0；每次真实now毫秒除1000后的f64 bits与App时钟逐字一致。Game始终tag2，worldcache0，仍是原角色选择页idle域。

同步冻结419,692,544B内存SHA `{sha(capture)}`，直接解析同份frozen bytes得到完全一致的final App/Rc header。上传后live内存已增长到476,643,328B，不能把逐块live读取误当一致snapshot。999个本地HTTP全200，535份MPQ资源53,898,024B独立raw payload重读；官方中文字体1,225,412B单列非MPQ来源，其完整字节与固定Windows EXE offset120912388一致，未执行EXE。Node／browser／worker PID和已归属PGID均已结束。

截图已独立查看，显示原件中文职业／角色／区域选择页，不能称重建UI或完整游戏。console明确记录向官方`/presence`连接的意图，被CSP阻断，未出现在实际HTTP请求中；`blocked=[]`不代表没有联网意图，也不证明联机可用。

旧SwiftShader批真实GPU createBuffer panic、旧Metal批研究observer1M事件throw及3个字体404分别保留原收据／事后诊断。最终去掉observer主动throw、补真实字体后，pageerror为空；各批次数不叠加。当前记录前20,000条import详情，总计数仍持续；没有用研究异常冒充原GPU缺陷。

新增独立模型案例／主循环帧0；原件8次idle入口不等于独立880实现。真实App所有字段／所有权、完整进场与战斗、渲染音频性能、存档／联机及独立完整一局仍待继续验证。
''')
 print(json.dumps(dict(directory=str(out),review_sha256=sha(target),status=review['status'],original_idle_returns=8,new_independent_mainloop_frames=0)))

if __name__=='__main__':main()
