#!/usr/bin/env python3
"""Different-author read-only1391_1542 audit; no author or original executes.

The frozen independent139 semantic arithmetic is reused only as a reference,
not its old outputs. Current1391 ABI/data/fullbody/imports are rebound here.
"""
import review_stats139 as independent139
from review_stats139 import *
HELPER_SHA='175667eded3461b118ddc2b7e47ee29517434b0bee7dfe77d4e388a9cc327473'
assert digest(Path(independent139.__file__))==HELPER_SHA
RUN=ROOT/'evidence/stats01391-oracle-20261102T151522.075107Z'
PROFILE=ROOT/'evidence/wasm01391-profile-20261102T133454.115329Z'
ORIGINAL=ROOT/'originals/official-release-v2-20261102T133059.984802Z/latest-wenilla_bg.wasm'
TRACE=ROOT/'evidence/stats1391-static-20261102T150813.349501Z/trace.json'
SHA='8831b4a21314cefd0b9f56dcb5681ac822a9ee30770ab1acae473f9e8f2aec71'
COMPARISON_SHA='5383d72da72fb4e9263ff737a8fb7f18e1e839360b378332f3ac7ff27ae828bb'


def current_static_contract(original,manifest,out):
    trace=load(TRACE);assert digest(TRACE)=='0dc7b86c448c3f52834cc2db0c4533800e3592a7ba398dea138e46a72b81a6fb'and trace['source_sha256']==SHA
    wanted={x['index']for x in trace['functions']}|{93365};ids=function_ids(original,wanted)
    wat,proof=bind_wat(PROFILE,'official-0.139.1-full.wat',ids,out)
    for record in trace['functions']:
        row=proof[record['index']]
        assert row['signature']==[record['params_hex'],record['results_hex']]
        for key in('body_start','body_end','body_bytes','body_sha256','wat_sha256'):assert row[key]==record[key]
    assert ids[1542]['signature']==['7f','']and ids[1542]['body_bytes']==4745
    assert ids[1542]['body_sha256']=='97ec7ef75ba04560c5235f0892cce1e9da30ced32c5aad5120f97e9d080d6df8'
    assert ids[93365]['signature']==['7f7f','7f']and manifest['allocator_type_index']==6
    assert wat[1542].encode()==(RUN/'1542.wat').read_bytes()
    text=wat[1542];lines=[x.strip()for x in text.splitlines()]
    calls=Counter(int(x.split()[1])for x in lines if re.fullmatch(r'call \d+',x))
    expected=Counter({48981:1,52417:3,66549:1,66554:2,73040:1,81910:1,108382:1,109334:1})
    assert calls==expected==Counter({x['callee']:x['sites']for x in manifest['full_direct_callees']})
    assert calls==Counter({x['callee']:x['sites']for x in trace['direct_callees']})
    for guard in trace['guards']:
        seq=guard['instructions'];sites=[i+1 for i in range(len(lines)-len(seq)+1)if lines[i:i+len(seq)]==seq]
        assert sites==guard['sites']
    headers=dict(passives=[1692,1696,1700,8],adjustments=[1668,1672,1676,16],items=[2024,2028,2032,8],owned=[168,172,176,8],timed_definitions=[2048,2052,2056,36],timed_records=[592,596,600,12],live=[1704,1708,1712,32])
    assert manifest['source_headers']==trace['seven_source_headers']==headers
    for cap,ptr,n,stride in headers.values():assert f'i32.load offset={ptr}'in lines and f'i32.load offset={n}'in lines
    assert all(x in text for x in('f32.load offset=764','f32.store offset=764','f32.store offset=1572','f32.store offset=1648','call 48981'))
    assert all(x not in text for x in('f32.load offset=768','f32.store offset=768','i32.load offset=604'))
    # Static numeric equivalence only. No139 old expected/actual results read.
    oldpath=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
    oldraw=oldpath.read_bytes();assert hashlib.sha256(oldraw).hexdigest()=='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
    oldids=function_ids(oldraw,{1542});oldout=out/'historical-static-only';oldout.mkdir();oldwat,oldproof=bind_wat(ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z','official-0.139.0-full.wat',oldids,oldout)
    left,lp=numeric_prefix(oldwat[1542],static_bounds(oldraw));right,rp=numeric_prefix(text,static_bounds(original))
    assert left==right and len(right)==1959
    prefix=dict(current_instructions=len(right),normalized_sha256=hashlib.sha256('\n'.join(right).encode()).hexdigest(),old_alpha=lp,current_alpha=rp,old_static_body=oldproof[1542],historical_runtime_results_read=False)
    pair=['local.get 4','local.get 2','i32.store offset=24','local.get 4','i32.const 0','i32.store offset=20']
    pairs=[i+1 for i in range(len(lines)-len(pair)+1)if lines[i:i+len(pair)]==pair];assert len(pairs)==3
    assert all(f'i32.const {key}'in lines for key in(22,28,1109))and'f32.ceil'in lines and'i32.trunc_sat_f32_u'in lines
    read=static_image_reader(original);classes={};races={};declarations=[]
    for selector in range(256):
        delta=(selector-2)&255;cp=word(read(1601176+4*delta,4),0)if delta<=9 else 5874384
        classes[selector]=struct.unpack('<2I',read(cp+72,8))
        rp0=word(read(1601016+4*delta,4),0)if delta<=6 else 5871100
        ptr,n=struct.unpack('<2I',read(rp0+16,8));assert n<=16
        races[selector]=list(struct.iter_unpack('<2I',read(ptr,n*8)))if n else[]
        if selector in(1,2,3,4,5,7,8,9,11):declarations.append(dict(domain='class',selector=selector,pointer=cp,hp_bits=classes[selector][0],armor_bits=classes[selector][1],scalar8_hex=read(cp+72,8).hex()))
        if 1<=selector<=8:declarations.append(dict(domain='race',selector=selector,pointer=rp0,modifier_pointer=ptr,modifier_count=n,raw_modifiers8_hex=read(ptr,n*8).hex()if n else'',modifiers=[list(x)for x in races[selector]]))
    assert sorted(declarations,key=lambda x:(x['domain'],x['selector']))==sorted(trace['declarations'],key=lambda x:(x['domain'],x['selector']))
    assert {int(k):tuple(v)for k,v in manifest['classes'].items()}=={k:classes[k]for k in(1,2,3,4,5,7,8,9,11)}
    assert {int(k):[list(x)for x in vs]for k,vs in manifest['races'].items()}=={k:[list(x)for x in races[k]]for k in range(1,9)}
    hp=literal(RUN/'source-snapshot/reconstruction/core_spec/derived_stats139.py','CLASS_HP_ARMOR');racial=literal(RUN/'source-snapshot/reconstruction/core_spec/derived_stats139.py','RACE_MODIFIERS')
    assert hp=={k:classes[k]for k in hp}and racial=={k:tuple(races[k])for k in racial}
    assert sum(len(races[k])for k in range(1,9))==14
    for name,h in trace['source_files'].items():assert digest(ROOT/name)==digest(TRACE.parent/'source-snapshot'/name)==h
    result=dict(functions=proof,current_source_headers=headers,current_data=declarations,current_data_read_proofs=read.proofs,numeric_prefix=prefix,current_BTree_two_word_sites=pairs,current1391_full_direct_callees=manifest['full_direct_callees'],native_execution=False)
    save(out/'static-proof.json',result);return classes,races,result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve())and not out.is_relative_to(RUN);out.mkdir();began=time.monotonic()
    auditor=digest(Path(__file__));(out/'auditor.py').write_bytes(Path(__file__).read_bytes())
    c=load(RUN/'comparison.json');m=load(RUN/'manifest.json');p=load(RUN/'prepared.json');runtime=load(RUN/'runtime.json');terminal=load(RUN/'process-terminal.json');handoff=load(RUN/'task-handoff.json')
    assert digest(RUN/'comparison.json')==COMPARISON_SHA and digest(RUN/'task-handoff.json')=='20ec16e4dc258f3ef18b190220000e688bdefb031453d3482b5b510ab572b073'
    files=c['source_sha256_before'];source=RUN/'source-snapshot';assert files==c['source_sha256_after']==p['source_sha256']and len(files)==13
    for n,h in files.items():assert digest(source/n)==digest(ROOT/n)==h,n
    edges=local_edges(source,files);assert edges==c['source_import_edges']==p['source_import_edges']and len(edges)==19
    production={n for n in files if n.startswith('reconstruction/')};seen=set();todo=['reconstruction/core_spec/derived_stats139.py']
    while todo:
        name=todo.pop()
        if name in seen:continue
        seen.add(name);todo.extend(b for a,b in edges if a==name)
    assert seen==production and len(production)==5
    for name in production:
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                fn=node.func;label=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else''
                assert label not in('open','read_text','read_bytes','write_text','write_bytes','Popen','eval','exec','__import__','import_module'),(name,label)
    for name,h in handoff['frozen_author_files'].items():assert digest(ROOT/name)==h
    assert len(handoff['frozen_author_files'])==6
    assert c['frozen_artifacts']==p['artifacts']
    for name,h in c['frozen_artifacts'].items():assert digest(RUN/name)==h
    artifacts={n:digest(RUN/n)for n in('comparison.json','manifest.json','prepared.json','runtime.json','process-terminal.json','owned-process.json','validator-terminal.json','validation.stdout','validation.stderr','stdout.jsonl','stderr.log','expected.json','fixtures.jsonl','1542.wat','stats1391-original-exports.wasm','task-handoff.json','differences.json')}
    assert artifacts['stdout.jsonl']==c['output_sha256']and artifacts['stderr.log']==c['stderr_sha256']and artifacts['runtime.json']==c['runtime_sha256']
    original=ORIGINAL.read_bytes();changed=(RUN/m['module_file']).read_bytes();assert len(original)==92537579 and hashlib.sha256(original).hexdigest()==m['original_sha256']==SHA and digest(RUN/m['module_file'])==m['module_sha256']
    old,new=sections(original),sections(changed);assert[x[0]for x in old]==[x[0]for x in new]and not any(x[0]==8 for x in old)
    assert all(original[a:b]==changed[u:v]for(k,a,_,b),(_,u,_,v)in zip(old,new)if k!=7)
    assert exports(original)==m['original_exports']and exports(changed)==exports(original)+[['research1391_stats1542',0,1542],['research1391_stats_stack0',3,0]]and ['__wbindgen_malloc',0,93365]in exports(original)
    imported=imports_of(original);assert imported==m['original_imports'];surface=[dict(module=x['module'],name=x['name'],kind='function')for x in imported]
    assert surface==runtime['denied_import_surface']and hashlib.sha256(json.dumps(surface,separators=(',',':')).encode()).hexdigest()==runtime['denied_import_surface_sha256']
    audit=load(RUN/'expectation-read-audit.json');assert audit==dict(opened=[],forbidden=[],layer='Python open audit')
    assert digest(RUN/'prepared.json')==handoff['prepared_sha256']
    assert handoff['original_source_sha256']==SHA and handoff['formal_cases']==handoff['formal_full1542_entries']==10569
    assert c['phase']=='full'and c['full880_frames']==c['native_executions']==c['complete_games']==0
    assert m['entry']['body_sha256']=='97ec7ef75ba04560c5235f0892cce1e9da30ced32c5aad5120f97e9d080d6df8'and not m['original_executed_by_builder']
    classes,races,static=current_static_contract(original,m,out);del original,changed
    checker=(source/'scripts/check_stats1391.py').read_text();runner=(source/'scripts/run_stats1391_oracle.mjs').read_text()
    assert checker.index("save(out/'expected.json',expected)")<checker.index('subprocess.Popen(')and c['expected_before_original']and not c['historical_outputs_used']and not c['old_results_transferred']
    assert p['historical_expected_or_actual_read']is False and p['template_controlled_input_sha256']==c['controlled_template_sha256']==artifacts['fixtures.jsonl']=='362dd58da9b1b201535c9e0334b212ddc0bc03f84887cac2a039c9188ccb2c09'
    assert 'call(1542,e.research1391_stats1542,G)'in runner and 'calls%32===0'in runner and 'bytes().fill(0,p,p+n)'in runner
    assert runtime==c['runtime']and terminal==c['process']and terminal['exit_code']==0 and terminal['error']is None and terminal['pid_missing']and terminal['pgid_missing']and process_missing(terminal['pid'])and process_missing(terminal['pgid'],True)
    facts=dict(version='0.139.1',actual_build='b89633f9b',cases=10569,completed_cases=10569,full1542_calls=10569,fresh_instances=331,actual_host_calls=0,denied_imports=882,memory_cap_bytes=33554432,heap_cap_mib=512,stack_guards=101736,stack_all_restored=True,original_function_bodies_unchanged=True,network_used=False,user_saves_accessed=False,original_snapshot_loaded=False,error=None)
    for key,value in facts.items():assert runtime[key]==value,(key,runtime[key],value)
    assert runtime['peak_memory_bytes']==14942208 and runtime['output_bytes']==(RUN/'stdout.jsonl').stat().st_size and(RUN/'stderr.log').stat().st_size==0
    assert runtime['stats_stack_returns']==[dict(case=i,before=1048576,after=1048576,returned=True)for i in range(10569)]
    expected=load(RUN/'expected.json');assert len(expected)==10569;counts=Counter();semantic=Counter();groups=Counter();stack_guards=0;headers=Counter()
    with(RUN/'fixtures.jsonl').open('rb')as fixtures,(RUN/'stdout.jsonl').open('rb')as actuals:
        for index,(left,right)in enumerate(zip(fixtures,actuals,strict=True)):
            assert len(left)<=32768 and len(right)<=16384 and left.endswith(b'\n')and right.endswith(b'\n')and time.monotonic()-began<180
            fixture=json.loads(left);actual=json.loads(right);want=expected[index];assert fixture['id']==actual['id']==want['id']==index;groups[fixture['group']]+=1;s=fixture['input']
            prediction=reference(s,classes,races,semantic);model=want['result'];assert set(prediction)==set(model)
            temp=Counter()
            for name in('derived_bits','auxiliary_bits','object_fields'):
                assert set(prediction[name])==set(model[name])==set(actual[name])
                for key,value in prediction[name].items():
                    integer=name=='object_fields'and key in('22','28')or name=='derived_bits'and key in('1592','1608')
                    scalar_equal(value,model[name][key],integer,(index,'expected',name,key),temp);scalar_equal(value,actual[name][key],integer,(index,'original',name,key),counts)
            for key in('current_hp_bits','speed_bits'):
                scalar_equal(prediction[key],model[key],False,(index,'expected',key),temp);scalar_equal(prediction[key],actual[key],False,(index,'original',key),counts)
            assert prediction['speed_changed']==model['speed_changed']and prediction['accepted_live_indices']==model['accepted_live_indices']
            changed=int(prediction['speed_changed']);assert actual['speed_sequence']==actual['movement_queue_count']==changed
            counts['compared_values']+=2;counts['strict_integer_values']+=2;counts['movement_queue_entries']+=changed;counts['cases']+=1
            game=bytes.fromhex(actual['raw_game2592_hex']);assert len(game)==2592;counts['raw_Game_bytes_field_bound']+=len(game)
            for name in('derived_bits','auxiliary_bits'):
                for offset,value in actual[name].items():assert word(game,int(offset))==value
            for key,offset in(('current_hp_bits',1440),('speed_bits',1648),('speed_sequence',1644),('movement_queue_count',1888)):assert word(game,offset)==actual[key]
            assert game[360]==s['class_byte']&255 and game[361]==s['race_byte']&255 and game[2582]==s['flag2574']&255
            for key,offset in(('level',1432),('now_bits',2352),('conditional268_bits',268),('conditional1344_id',1344)):assert word(game,offset)==s[key]
            assert int.from_bytes(game[1336:1344],'little')==1 and word(game,2476)>0 and word(game,2480)==0
            for key,offset in(('passives',1692),('adjustments',1668),('item_modifiers',2024),('owned_skills',168),('timed_definitions',2048),('timed_records',592),('live_effects',1704)):
                cap,ptr,n=struct.unpack_from('<3I',game,offset);assert cap==n==len(s[key])and ptr>0;counts['source_vector_headers']+=1
            capacity,pointer,n=struct.unpack_from('<3I',game,1880);assert n==changed and n<=capacity and pointer>0
            if not changed:assert(capacity,pointer,n)==(0,4,0)
            headers[str(capacity)]+=1
            stack_guards+=9+len(s['adjustments'])+2*len(s['owned_skills'])
    assert dict(groups)==c['groups']and counts['cases']==c['cases']==c['original1542_calls']==10569
    assert counts['compared_values']==c['counts']['compared_values']==359346 and counts['movement_queue_entries']==c['counts']['actual_movement_packets']==1537
    assert counts['source_vector_headers']==73983 and counts['raw_Game_bytes_field_bound']==27394848 and stack_guards==runtime['stack_guards']==101736
    assert counts['nan_category_comparisons']>0 and counts['signed_negative_zero_values']>0 and c['differences']==0
    for n,h in files.items():assert digest(ROOT/n)==digest(source/n)==h
    for name,h in handoff['frozen_author_files'].items():assert digest(ROOT/name)==h
    for n,h in artifacts.items():assert digest(RUN/n)==h
    assert digest(Path(__file__))==auditor
    result=dict(status='scoped_fresh1391_full1542_independent_read_only_review_passed',version='0.139.1',actual_build='b89633f9b',original_sha256=SHA,comparison=str((RUN/'comparison.json').relative_to(ROOT)),comparison_sha256=COMPARISON_SHA,cases=10569,full1542_calls_in_frozen_batch=10569,new_original_calls=0,production_imports=0,production_executions=0,checker_builder_tracer_executions=0,differences=0,source_count=13,production_sources=5,local_import_edges=19,sources=files,handoff_files=6,handoff_sha256=artifacts['task-handoff.json'],auditor_source='scripts/review_stats1391.py',independent_helper_source='scripts/review_stats139.py',independent_helper_sha256=HELPER_SHA,auditor_sha256=auditor,counts=dict(counts),semantic_counts=dict(semantic),groups=dict(groups),movement_queue_capacity_observations=dict(headers),stack_guards_independently_counted=stack_guards,static_function_proof=static['functions'],numeric_prefix_proof=static['numeric_prefix'],static_proof_sha256=digest(out/'static-proof.json'),current1391_class_race_data_reextracted=True,current_class_records=9,current_race_records=8,current_race_modifier_entries=14,seven_explicit_source_headers=static['current_source_headers'],only_export7_changed=True,all_eight_actual_callees_preserved=True,allocator=93365,entry=1542,physical_timed_pointer_count=[596,600],reserve_offset=764,armor_cap1572_single_ordered_accumulator=True,old_runtime_acceptance_transferred=False,pilot12_added=False,runtime={k:v for k,v in runtime.items()if k not in('stats_stack_returns','denied_import_surface')},process=terminal,artifacts=artifacts,seconds=time.monotonic()-began,full884_frames=0,native_executions=0,complete_games=0,limitations=['All10569 current1391 original calls were already recorded; this review replays immutable evidence without executing original/production/checker/builder/tracer.','Semantic accumulator reference code is reused,not historical expected/actual/pass status. Current1391 full1959-instruction numeric prefix is independently re-normalized and every1391 class/race lookup is newly extracted before recalculation.','NaN float outputs match by classification only; finite/infinite values,signed zeros and integer fields match exact words.','Raw Game2592 is bound fieldwise,including73983 seven-source headers; no whole image or source backing/heap/BTree layout equality claim.','1537 counts actual movement queue entries only; payload bytes,physical backing and network delivery were not captured or independently recovered.','Explicit seven source snapshots are synthetic controlled inputs; natural profile/equipment/talent/live producers and constructor1391/full flow remain separate work.','The12-case pilot is not added; fixed135/138 acceptance and native Windows execution/layout receive no transferred runtime credit.'])
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=digest(out/'review.json'),cases=10569,counts=dict(counts),seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
