#!/usr/bin/env python3
"""Second-author frozen ACK199 audit; never imports or executes production.

This auditor reads original bytes/indexed WAT and the saved88-case capture.
Setup is observed component input. Queue payloads/world-range hashes were not
persisted; their invariance remains a runner assertion plus static mode0 proof.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,hashlib,json,mmap,os,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
# Read-only auditor utilities only; no production/model/checker/builder import.
from review_stats138 import sections,exports,function_ids,local_edges,digest,process_missing
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/player-motion135-oracle-20261101T232552.862423Z'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
STATIC=ROOT/'evidence/player-correction135-static-20261101T232136.971209Z/proof.json'
CAPTURE_SHA='463deadc49cb34222e92854de1a17116fbf16a78d0952d3f49ad0e14456415ea'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
def load(path):return json.loads(Path(path).read_text())
def u(raw,offset):return int.from_bytes(raw[offset:offset+4],'little')
def put(raw,offset,value):raw[offset:offset+4]=value.to_bytes(4,'little')
def decode(payload):
    assert type(payload)is bytes and payload,'Exact packedGUID+u32 ACK required'
    slots=[j for j in range(8) if payload[0]&(1<<j)]
    assert len(payload)==len(slots)+5,'Malformed length outside admitted domain'
    expanded=bytearray(8)
    for j,value in zip(slots,payload[1:1+len(slots)],strict=True):expanded[j]=value
    ack=int.from_bytes(payload[-4:],'little');return int.from_bytes(expanded,'little'),ack
def consume(cells,ack,reads=None):
    """Independent read-tracked interpretation of original local968 ACK block."""
    out=list(cells)
    def read(offset):
        if reads is not None:reads.append(offset)
        selected=out[offset:offset+4]
        if any(x is None for x in selected):raise LookupError('Unknown consumed u32')
        return int.from_bytes(bytes(selected),'little')
    clear=False
    if read(416)==1:
        pending=read(432)
        if ack>=pending:out[416:420]=[0]*4;clear=True
    return out,clear
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    began=time.monotonic();assert len(sys.argv)==2 and os.getpid()==os.getpgrp(),'Run under owned start_new_session launcher'
    out=Path(sys.argv[1]).resolve();assert out.parent==ROOT/'evidence' and out.name.startswith('player-correction135-independent-review-') and out.is_dir()
    capture=load(RUN/'correction-comparison.json');manifest=load(RUN/'manifest.json');context=load(RUN/'setup-context.json');cases_config=load(RUN/'cases-config.json');setup_config=load(RUN/'setup-config.json')
    assert digest(RUN/'correction-comparison.json')==CAPTURE_SHA
    assert capture['source_sha256_before']==capture['source_sha256_after'];files=capture['source_sha256_before'];assert len(files)==17
    frozen=RUN/'source-snapshot'
    for name,h in files.items():assert digest(ROOT/name)==h==digest(frozen/name),name
    edges=local_edges(frozen,files);assert edges==capture['complete_static_local_import_edges'] and len(edges)==31
    production={n for n in files if n.startswith('reconstruction/')};assert len(production)==9
    reachable=set();todo=['reconstruction/core_spec/player_correction135.py','reconstruction/resource_spec/world_query135.py']
    # Imports are independently resolved against the current tree, including all
    # package initializers, before closure equality is asserted.
    while todo:
        name=todo.pop()
        if name in reachable:continue
        reachable.add(name)
        if name.startswith('reconstruction/') and not name.endswith('/__init__.py'):todo.append(str(Path(name).parent/'__init__.py'))
        todo.extend(b for a,b in edges if a==name)
    assert reachable==production
    for name,h in capture['artifacts'].items():assert digest(RUN/name)==h,name
    assert digest(RUN/'setup-context.json')==cases_config['context_sha256']==capture['setup_context_sha256']
    assert digest(RUN/'inputs.json')==cases_config['input_sha256']
    assert cases_config['snapshot_sha256']==setup_config['snapshot_sha256']==capture['snapshot_sha256']
    snapshot=Path(cases_config['snapshot_path']);assert digest(snapshot)==capture['snapshot_sha256'] and snapshot.stat().st_size==166395904
    original=ORIGINAL.read_bytes();module=(RUN/manifest['module_file']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==SOURCE_SHA==manifest['original_wasm_sha256'] and len(original)==90959080
    assert hashlib.sha256(module).hexdigest()==manifest['module_sha256'] and len(module)==manifest['module_bytes']==90959289
    a,b=sections(original),sections(module);assert [x[0] for x in a]==[x[0] for x in b] and not any(x[0]==8 for x in a)
    assert all(original[x:y]==module[z:w] for (k,x,_,y),(_,z,_,w) in zip(a,b) if k!=7)
    prior=exports(original);assert prior==manifest['original_exports']
    added=[[x['export'],0,x['index']] for x in manifest['roles']]+[[manifest['stack_export'],3,0]]+[[x['export'],0,x['index']] for x in manifest['additional_setup_roles']]
    assert exports(module)==prior+added and ['__wbindgen_malloc',0,91941] in prior
    identities=function_ids(original,{968,2328,6730,1089,17726})
    for role in manifest['roles']+manifest['additional_setup_roles']:
        identity=identities[role['index']];assert identity['signature']==[role['parameters_hex'],role['results_hex']] and identity['body_sha256']==role['body_sha256']
    assert identities[968]['body_sha256']=='ae8aedaaa5ca805c5a4e35009e03bbe542fa23c5294f9ab8dadfe4b7e3b7aa97'
    slices={};index={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        with (PROFILE/'official-0.135.1-full.wat').open('rb') as wat:
            for entry in (968,17726):
                item=dict(db.execute('select * from functions where idx=?',(entry,)).fetchone());index[entry]=item
                for k in ('body_start','body_end','body_bytes'):assert item[k]==identities[entry][k]
                wat.seek(item['wat_start']);slices[entry]=wat.read(item['wat_end']-item['wat_start'])
    proof=load(STATIC);assert digest(STATIC)=='f24e914980a47a426801cb4922ead41952853606901ac36daf4dca3af2d12cf1'
    lines=[x.strip() for x in slices[968].decode().splitlines()];windows={}
    for name,window in proof['functions']['968']['windows'].items():
        assert all(lines[row['line']-1]==row['instruction'] for row in window),name;windows[name]=window
    assert hashlib.sha256(slices[968]).hexdigest()==proof['functions']['968']['wat_sha256']
    guard=[x.strip() for x in slices[17726].decode().splitlines()]
    assert guard[8:13]==['local.get 0','i32.load8_u offset=2582','i32.const 1','i32.ne','br_if 0 (;@1;)']
    assert guard[-5:]==['end','local.get 4','i32.const 32','i32.add','global.set 0)']
    # Only Game416 is written in the local ACK block. No GUID comparison is
    # performed there.17726's mode0 branch exits its entire mutation block.
    assert [x for x in lines[9643:9661] if '.store' in x]==['i32.store offset=416']
    assert lines[9653]=='i32.lt_u' and lines[9660]=='call 17726'
    dump(out/'static-windows.json',dict(original_sha256=SOURCE_SHA,identities=identities,profile_index=index,windows=windows,mode17726_guard=guard[:14],mode17726_exit=guard[-5:],WAT_read_bytes=sum(map(len,slices.values())),full_WAT_read=False))
    author=ast.parse((frozen/'reconstruction/core_spec/player_correction135.py').read_text());fn=next(n for n in author.body if isinstance(n,ast.FunctionDef) and n.name=='consume_player_correction_ack135')
    clear=next(n.value for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cleared' for t in n.targets))
    assert ast.dump(clear,include_attributes=False)==ast.dump(ast.parse('word(416)==1 and ack.sequence>=word(432)',mode='eval').body,include_attributes=False)
    checker=(frozen/'scripts/check_player_correction135.py').read_text();runner=(frozen/'scripts/run_player_correction135_oracle.mjs').read_text()
    assert checker.index('rows,canonical=corpus(')<checker.index("terminal=execute(out,config,'cases')")
    assert "JSON.stringify(prefix.rows)!==JSON.stringify(final.rows.slice(0,prefix.count))" in runner
    assert "config.world_ranges.some(([p,n],j)=>hash(b().subarray(p,p+n))!==arrayHashes[j])" in runner
    assert 'prefix.rows' not in next(x for x in runner.splitlines() if 'process.stdout.write' in x)
    assert context['kind']==capture['setup_context_kind']=='original-setup-observation-explicit-input-not-independent-constructor'
    assert context['App']==14549000 and context['G']==14549016 and context['world_pointer']==26204808
    assert context['full_setup_functions']==[6730,1089] and context['setup_target968_calls']==context['original_host_calls']==0
    assert context['completeApp_producer'] is False and capture['independent_constructor_validation'] is False
    base=bytes.fromhex(context['game2592_hex']);app=bytes.fromhex(context['app5168_hex']);world=bytes.fromhex(context['world124_hex'])
    assert len(base)==2592 and len(app)==5168 and len(world)==124 and app[16:2608]==base
    assert base[2582]==0 and base[2587]==1 and int.from_bytes(app[2608:2616],'little')==2 and int.from_bytes(app[16:24],'little')!=2
    with snapshot.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as memory:
        assert bytes.fromhex(context['app_original5168_hex'])==memory[context['App']:context['App']+5168]
        assert u(memory,context['world_pointer'])==context['old_world_refcount']==2 and u(world,0)==context['world_refcount']==3
    assert u(base,2348)==context['world_pointer'] and u(app,5116)==context['world_pointer']
    ranges=cases_config['world_ranges'];assert ranges==setup_config['world_ranges'] and len(set(map(tuple,ranges)))==len(ranges)
    assert all(type(p)is int and type(n)is int and 0<p and 0<n<=4194304 and p+n<=snapshot.stat().st_size for p,n in ranges)
    fixtures=load(RUN/'fixtures.json');inputs=load(RUN/'inputs.json');actual=[json.loads(x) for x in (RUN/'cases-results.jsonl').read_text().splitlines()]
    assert len(fixtures)==len(inputs)==len(actual)==capture['cases']==capture['actual_cases']==88
    counts=Counter();groups=Counter();queue=dict(zip(('capacity','pointer','count'),struct.unpack_from('<3I',base,1880)));assert queue==dict(capacity=128,pointer=31488256,count=78)
    for i,(c,entry,row) in enumerate(zip(fixtures,inputs,actual,strict=True)):
        assert c['id']==entry['id']==row['id']==i and c['input']==entry and set(entry)=={'id','opcode','payload_hex','patch_words'} and entry['opcode']==199
        groups[c['group']]+=1;payload=bytes.fromhex(entry['payload_hex']);guid,ack=decode(payload)
        before=bytearray(base);assert [p for p,_ in entry['patch_words']]==[416,420,424,428,432,436]
        for offset,value in entry['patch_words']:assert type(value)is int and 0<=value<1<<32;put(before,offset,value)
        after,cleared=consume(before,ack);after=bytes(after);pending=u(before,432);tag=u(before,416)
        diag=c['diagnostic'];assert diag['tag']==tag and diag['pending_sequence']==pending and diag['ack_sequence']==ack and int(diag['ack_guid'])==guid and int(diag['player_guid'])==int.from_bytes(base[1336:1344],'little')
        assert diag['cleared']==cleared and diag['writes']==([[416,0]] if cleared else [])
        app_before=bytearray(app);app_before[16:2608]=before;app_after=bytearray(app_before);app_after[16:2608]=after
        wanted=dict(game_before_hex=before.hex(),game_after_hex=after.hex(),app_before_hex=app_before.hex(),app_after_hex=app_after.hex(),packets=[])
        assert c['expected']==wanted
        for key,value in wanted.items():assert row[key]==value,(i,key)
        for key in ('game_before_hex','game_after_hex','app_before_hex','app_after_hex'):counts['compared_raw_Game_App_bytes']+=len(bytes.fromhex(row[key]))
        assert row['world_before_hex']==row['world_after_hex']==context['world124_hex'];counts['compared_world_record_bytes']+=248
        assert row['queue_before']==row['queue_after']==queue and row['packets']==[];counts['queue_header_values']+=6
        assert row['stack_after']==1048576 and row['host_calls']==0 and row['full_target_function']==968 and row['setup_functions']==[6730,1089] and row['same_inline_G']==context['G'] and row['route']==[0,0] and row['partialApp_fixture'] is True
        counts['clear' if cleared else 'retain']+=1;counts['different_GUID_clear']+=cleared and guid!=int.from_bytes(base[1336:1344],'little')
        signed=lambda x:x-(1<<32) if x&(1<<31) else x
        counts['unsigned_vs_signed_different_decision']+=tag==1 and (ack>=pending)!=(signed(ack)>=signed(pending))
        counts['nonzero_GUID_cases']+=guid!=0;counts['packed_GUID_payload_bytes']+=len(payload);counts['decoded_GUID_bytes']+=8;counts['decoded_u32_ACKs']+=1
        cells=[None]*2592;cells[416:420]=tag.to_bytes(4,'little')
        if tag==1:cells[432:436]=pending.to_bytes(4,'little')
        reads=[];partial,partial_cleared=consume(cells,ack,reads);assert partial_cleared==cleared and reads==([416,432] if tag==1 else [416])
        for j,value in enumerate(partial):
            if value is None:assert cells[j] is None;counts['independent_unknown_cells_preserved']+=1
            else:assert value==after[j]
    assert dict(groups)==capture['groups'] and counts['clear']==28 and counts['retain']==60 and counts['different_GUID_clear']==15
    assert counts['independent_unknown_cells_preserved']==capture['canonical_cells']['unknown_bytes_preserved']==227592
    assert counts['unsigned_vs_signed_different_decision']>0
    try:consume([None]*2592,0)
    except LookupError:counts['unknown416_refused_independently']+=1
    else:raise AssertionError('Unknown416 consumed')
    for payload in (b'',b'\xff',b'\x00',b'\x00'+bytes(8)):
        try:decode(payload)
        except AssertionError:counts['malformed_length_refused_independently']+=1
        else:raise AssertionError('Outside-domain payload admitted')
    runtime=load(RUN/'cases-runtime.json');setup_runtime=load(RUN/'setup-runtime.json');assert runtime==capture['runtime'] and setup_runtime==capture['setup_runtime']
    assert runtime['full968_calls']==runtime['full6730_calls']==runtime['full1089_calls']==88 and setup_runtime['full968_calls']==0 and setup_runtime['full6730_calls']==setup_runtime['full1089_calls']==1
    for r in (runtime,setup_runtime):
        assert r['host_calls']==0 and r['denied_imports']==878 and r['max_memory_bytes']==166395904<=r['memory_page_cap']*65536==268435456
        for name in ('worldRc_forged','externref_forged','completeApp_producer','natural1371Game_install','app_entry_called','user_saves_accessed','network_used','original_bodies_modified'):assert r[name] is False
    for phase,key in (('setup','setup_process'),('cases','target_process')):
        terminal=load(RUN/f'{phase}-terminal.json');assert terminal==capture[key] and terminal['exit_code']==0 and terminal['deadline_seconds']==60 and terminal['pid_missing'] and terminal['pgid_missing']
        assert process_missing(terminal['pid']) and process_missing(terminal['pgid'],True)
        assert (RUN/f'{phase}-stderr.log').stat().st_size==0
    assert (RUN/'setup-results.jsonl').stat().st_size==0
    for name,h in files.items():assert digest(ROOT/name)==h==digest(frozen/name)
    artifacts={name:digest(RUN/name) for name in ('correction-comparison.json','fixtures.json','inputs.json','setup-context.json','setup-config.json','cases-config.json','manifest.json','setup-runtime.json','cases-runtime.json','setup-terminal.json','cases-terminal.json','cases-results.jsonl','setup-stderr.log','cases-stderr.log')}
    summary=dict(status='scoped_frozen_ACK199_full968_Game_App_independent_review_passed',version='0.135.1',build='90898d5e3',capture=str((RUN/'correction-comparison.json').relative_to(ROOT)),capture_sha256=CAPTURE_SHA,original_sha256=SOURCE_SHA,cases=88,frozen_full_original968_calls=88,new_original_executions=0,new_model_checker_builder_executions=0,differences=0,counts=dict(counts),groups=dict(groups),source_files=17,production_files=9,local_import_edges=31,source_snapshot_current_equal=True,only_exports_changed=True,complete_original_callees_preserved=True,source_sha256=files,identities=identities,static_windows_sha256=digest(out/'static-windows.json'),setup_kind=context['kind'],setup_is_independent_constructor_validation=False,raw_Game_App_independent_recompute=True,queue_prefix=dict(count=78,raw_rows_persisted=False,raw_payloads_independently_compared=False,evidence='frozen runner asserted invariant; original local968 plus mode0 full17726 static no-write path'),world_record_raw_before_after_compared=True,world_ranges=dict(count=len(ranges),declared_bytes=sum(n for _,n in ranges),hashes_persisted=False,evidence='runner asserted invariant only; configured bounds and source-binding verified'),canonical_None_domain=dict(author_guard_AST_verified_short_circuit=True,original_None_cells_exist=False,independent_reference_preservation=True,not_added_to_original_cases=True),runtime=runtime,setup_runtime=setup_runtime,artifacts_sha256=artifacts,auditor_source=str(Path(__file__).relative_to(ROOT)),auditor_sha256=digest(Path(__file__)),auditor_utilities={'scripts/review_stats138.py':digest(ROOT/'scripts/review_stats138.py')},owned_audit_process=dict(pid=os.getpid(),pgid=os.getpgrp(),expected_terminal_file='owned-terminal.json'),full880_frames=0,complete_games=0,native_executions=0,elapsed_seconds=round(time.monotonic()-began,3),limitations=['Observed6730/1089 setup prestate is input, not independent constructor acceptance.','Only local ownerRoute0 peer0 mode0 phase1 exact packedGUID+u32 ACK domain.','GUID bytes are consumed but local scalar branch does not authenticate/compare GUID.','No persisted prefix raw rows/payloads or world-range before/after hashes; those remain runner asserted invariants plus static path evidence.','None unknown-cell preservation and four malformed rejections are independent model/static checks, not new original differential cases.','Remote route1,mode1 forwarding,truncated/defaulting parser behavior,wraparound sequence policy and sameGame915 continuation remain outside this capture.'])
    dump(out/'review.json',summary);report=ROOT/'reports/2026-11-02-player-correction0135-independent-review.json';dump(report,summary|dict(evidence=str(out.relative_to(ROOT)),review_sha256=digest(out/'review.json')))
    md=ROOT/'reports/2026-11-02-player-correction0135-independent-review.md'
    md.write_text('# Fixed135 ACK199 independent review\n\nScoped review passed for88 frozen full968 calls. The auditor executed no original, production module, checker or builder.\n\n- Independently decoded packedGUID and unsigned u32 ACK; independently reconstructed all2592 Game and5168 App bytes before/after.28 clears and60 retains matched;15 different-GUID clears.\n- Reverified17 current/frozen source hashes,9 production files,31 local import edges. Original bodies/callees unchanged; only private exports added.\n- Confirmed original968 local block clears only G416 when tag1 and unsigned ACK>=G432; full17726 returns without queue writes inmode0.\n-227592 None cells preserved by independent reference; author AST uses a short-circuit guard, so inactive tag0/2 does not read unknown G432. This is model/static evidence.\n- Queue count78, pointer, capacity and zero appended packets match the raw Game/App capture. Existing prefix payloads and world-range hashes were not persisted: preservation is a frozen-runner assertion plus static mode0 path evidence, not independent raw prefix/world-range comparison.\n- Full6730/1089 setup is an observed explicit prestate; no independent constructor or naturalApp acceptance.\n\nRemote route1,mode1 forwarding,truncated parsing,sameGame915 continuation,native runtime and complete games remain unverified.\n\nEvidence: `'+str(out.relative_to(ROOT))+'`; review SHA256 `'+digest(out/'review.json')+'`. Owned terminal receipt is stored alongside the review by the launcher.\n')
    print(json.dumps(dict(status=summary['status'],evidence=str(out.relative_to(ROOT)),review_sha256=digest(out/'review.json'),report_json_sha256=digest(report),report_md_sha256=digest(md),auditor_sha256=digest(Path(__file__)),counts=dict(counts),seconds=summary['elapsed_seconds'])))
if __name__=='__main__':main()
