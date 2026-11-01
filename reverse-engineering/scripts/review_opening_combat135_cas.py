#!/usr/bin/env python3
"""Read-only400-frame CAS review; transport dependency is explicitly declared.
No original, production model or checker executes. Default transport is the
frozen root decoder; a private copy may change only the string quoting fastpath.
"""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import argparse,ast,hashlib,importlib.util,json,struct,sys,time,zlib
sys.dont_write_bytecode=True
import review_opening_combat135 as semantic
from review_combat137 import exports
from review_battle_shout135 import F,B,sub,mul,add,word
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'evidence/opening-combat0135-oracle-20261101T173256.931310Z'
DECODER_SHA='16ca91ea52fdb107988d2f9c0c7b8d3b069d21df13f5a1b6091dd8ddb1199049'
FAST_OLD="return json.dumps(value, ensure_ascii=False, separators=(',', ':'))"
FAST_NEW='return json.encoder.encode_basestring(value)'
STAGES=semantic.STAGES

def sha(p):return semantic.sha(p)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',nargs='?',type=Path,default=DEFAULT);parser.add_argument('--private-fast-decoder',type=Path);args=parser.parse_args()
    began=time.monotonic();directory=args.directory.resolve();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-combat135-cas-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    report=json.loads((directory/'comparison.json').read_text());fixtures=json.loads((directory/'fixtures.json').read_text());runtime=report['runtime'];source=directory/'source-snapshot'
    assert report['status']=='matched_requested_budget'and report['differences']==0 and report['independent_frames']==400 and report['independent_selections']==4 and report['compared_stages']==5604 and report['capture_format']=='cas'
    assert report['source_sha256_before']==report['source_sha256_after']and len(report['source_sha256_before'])==98
    for name,digest in report['source_sha256_before'].items():assert sha(source/name)==digest==sha(ROOT/name),name
    production=sorted(n for n in report['source_sha256_before']if n.startswith('reconstruction/'));assert production==semantic.frozen_closure(source)and len(production)==85
    for name in production:
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                f=node.func;fn=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else''
                assert fn not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'),(name,fn)
    decoder_source=source/'scripts/opening_combat135_cas.py';assert sha(decoder_source)==DECODER_SHA
    decoder_path=args.private_fast_decoder.resolve()if args.private_fast_decoder else decoder_source
    if args.private_fast_decoder:assert decoder_path.read_text()==decoder_source.read_text().replace(FAST_OLD,FAST_NEW)and decoder_source.read_text().count(FAST_OLD)==1
    spec=importlib.util.spec_from_file_location('declared_CAS_transport',decoder_path);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    decoder=transport.CaptureCAS135(directory)
    codec_review=ROOT/'evidence/opening-cas-codec135-review-20261101T173151.174099Z/review.json';assert sha(codec_review)=='5e27cf0fd619a8a5c315ac00bb4e8d803ba17c89ca8e5ba9af19c42a7b543839'
    inputs=json.loads((directory/'inputs.json').read_text());assert inputs==[{k:fixtures[k]for k in('id','input','actions')}]
    for file,key in(('fixtures.json','fixtures_sha256'),('inputs.json','inputs_sha256'),('stage-expectations.jsonl.gz','expectations_sha256'),('results.cas.jsonl.gz','original_results_sha256')):assert sha(directory/file)==report[key]
    assert report['model_expected_before_original']and report['original_input_contains_no_expectations']
    checker=(source/'scripts/check_opening_combat135.py').read_text();assert checker.index('row=corpus(')<checker.index('child=subprocess.Popen(')and'child.wait(timeout=60)'in checker
    original=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes();manifest=json.loads((directory/'manifest.json').read_text());module=(directory/manifest['module_file']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==report['original_sha256']and hashlib.sha256(module).hexdigest()==manifest['module_sha256']
    a,b=semantic.sections(original),semantic.sections(module);assert[x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]
    assert all(original[x:y]==module[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    added=[['research_opening_combat135_'+x['role'],0,x['index']]for x in manifest['roles']]+[['research_opening_combat135_stack',3,0]]
    assert exports(module)==exports(original)+added
    read_static=semantic.static_reader(original);battle_definition=read_static(5467956,88);del original,module
    assert word(battle_definition,0)==8 and word(battle_definition,44)==6673 and battle_definition[84]==9
    context=report['original_context'];assert sha(Path(context['snapshot_path']))==context['snapshot_sha256']=='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
    expected_reader=semantic.JsonlReader(directory/'stage-expectations.jsonl.gz',True,1073741824);expected=iter(expected_reader);opening=next(expected);assert opening['record_kind']=='opening';opening=opening['expected']
    distance=semantic.independent_distance_sha(opening,report)
    order=[('case_start',None,None,0),('constructor',None,None,0),('opening',None,None,0)];frame=0
    for index,action in enumerate(fixtures['actions']):
        if action['kind']=='select':order.append(('stage',index,'select',frame))
        else:assert action['kind']=='controlled_tail_frame';order.append(('clock_control',index,None,frame));order.extend(('stage',index,kind,frame)for kind in STAGES);frame+=1
    order.append(('case_end',None,None,frame));assert frame==400 and len(order)==6008 and len(fixtures['actions'])<=600
    compressed=(directory/'results.cas.jsonl.gz').read_bytes();assert len(compressed)<=268435456
    inflate=zlib.decompressobj(31);index_raw=inflate.decompress(compressed,33554433);assert len(index_raw)<=33554432 and inflate.eof and not inflate.unused_data and not inflate.unconsumed_tail
    counts=Counter();maximum=defaultdict(int);records=Counter();clock=0;stage_index=0;previous=None;last=None;locale=None;selections=[];guardian_owners={};guardian_captures=0;guardian_payloads=0;packet_max=0;first_guardian=None;first_battle=None;battle_tick_count=0;fourth_select=None;battle_countdowns=[];previous_packets=[];previous_notifications=[];negative=[]
    for line_index,line in enumerate(index_raw.splitlines(keepends=True)):
        assert time.monotonic()-began<120,'Read-only review120s budget';raw=decoder.decode_line(line);kind,action_index,stage_kind,frame_index=order[line_index]
        records[raw['record_kind']]+=1;assert raw['record_kind']==kind and raw['id']==0
        if action_index is not None:assert raw['action_index']==action_index and raw['frame']==frame_index
        if stage_kind is not None:assert raw['kind']==stage_kind
        if kind=='case_start':locale=raw['locale_prestate'];assert locale['effective_index']==0 and locale['once_flag']==3
        if kind=='clock_control':
            action=fixtures['actions'][action_index];assert raw['old_bits']==clock and raw['dt_bits']==action['dt_bits'];clock=B(F(clock)+F(action['dt_bits']))
            assert raw['new_bits']==clock and raw['original880_called']is False and raw['only_external_game_write_offset']==2352
        if kind in('constructor','opening','stage'):
            want=opening if kind=='opening'else None
            if kind=='stage':
                item=next(expected);assert item['record_kind']=='stage'and item['stage_index']==stage_index and item['action_index']==action_index and item['kind']==stage_kind;want=item['expected'];counts['stage_identity_leaves']+=2
            guardians=semantic.check_snapshot(raw,want,counts,maximum,read_static);packet_max=max(packet_max,raw['packets']['count'])
            for queue,field,old in(('packets','new_packets',previous_packets),('notifications','new_notifications',previous_notifications)):
                current=[{'opcode':x['opcode'],'payload_hex':x['payload_hex']}for x in raw[queue]['active']]if queue=='packets'else[x['payload_hex']for x in raw[queue]['active']]
                prefix=len(old)<=len(current)and current[:len(old)]==old;delta=raw[field]
                assert delta['prefix_preserved']==prefix and delta['previous_count']==len(old)and delta['current_count']==len(current)and delta['appended']==(current[len(old):]if prefix else[])
                if not prefix:assert delta['full_current']==current
                if queue=='packets':previous_packets=current
                else:previous_notifications=current
            if guardians:
                guardian_captures+=1;guardian_payloads+=len(guardians)
                if first_guardian is None:first_guardian=dict(frame=frame_index,stage_index=stage_index,count=len(guardians));negative=semantic.owner_negative_checks(raw,want,read_static)
                for owner in guardians:
                    identity=(owner['ability_pointer'],owner['header_pointer']);assert guardian_owners.get(owner['guid'],identity)==identity;guardian_owners[owner['guid']]=identity
            if kind=='stage':
                assert raw['stage_index']==stage_index and raw['projection']['now_bits']==clock
                assert raw['entry_index']==(1072 if stage_kind=='select'else semantic.ENTRIES[STAGES.index(stage_kind)])
                if stage_kind=='select':
                    selected=fixtures['actions'][action_index]['index'];cards=previous['projection']['candidates'];assert previous['projection']['phase2587']==2 and raw['input_index']==selected
                    selection=dict(frame=frame_index,action_index=action_index,index=selected,card=cards[selected],phase_after=raw['projection']['phase2587']);selections.append(selection)
                    if len(selections)==4:
                        assert selection['card']['ability_id']=='battle_shout'and selected==0 and frame_index==379 and raw['projection']['phase2587']==1;fourth_select=selection
                        battle=next(bytes.fromhex(x)for x in raw['projection']['owned_records_hex']if word(bytes.fromhex(x),0)==5467956)
                        assert word(battle,8)==0x3f000000 and raw['vectors']['owned80']['count']==3
                if stage_kind=='player'and fourth_select:
                    prior=[bytes.fromhex(x)for x in previous['projection']['owned_records_hex']];current=[bytes.fromhex(x)for x in raw['projection']['owned_records_hex']]
                    bi=next(i for i,x in enumerate(prior)if word(x,0)==5467956);before,after=prior[bi],current[bi];remaining=sub(word(before,8),fixtures['actions'][action_index]['dt_bits']);battle_tick_count+=1
                    assert before[:8]+before[12:]==after[:8]+after[12:]
                    if F(remaining)>0:assert word(after,8)==remaining
                    else:
                        cooldown=mul(mul(mul(mul(word(battle_definition,52),0x3fb33333),word(before,16)),word(before,56)),raw['projection']['derived_bits']['1544'])
                        cooldown=cooldown if F(cooldown)>.25 else 0x3e800000;assert word(after,8)==cooldown
                        duration=mul(mul(mul(word(battle_definition,68),0x3fb33333),word(before,28)),word(before,68));duration=duration if F(duration)>.1 else 0x3dcccccd
                        active=[bytes.fromhex(x)for x in raw['vectors']['live32']['storage'][:raw['vectors']['live32']['count']]]
                        buff=next(x for x in active if word(x,8)==8 and word(x,20)==6673)
                        assert buff[:8]==bytes(8)and word(buff,12)==mul(word(before,76),word(battle_definition,4))and word(buff,24)==add(clock,duration)and word(buff,28)==0
                        if first_battle is None:first_battle=dict(frame=frame_index,stage_index=stage_index,player_ticks_since_selection=battle_tick_count,clock_bits=clock,remaining_cooldown_bits=word(after,8),live_record_hex=buff.hex(),damage_multiplier_bits=raw['projection']['derived_bits']['1540'])
                    battle_countdowns.append(dict(frame=frame_index,remaining_bits=word(after,8)))
                path=raw['projection']['distance_map']
                if path is not None:
                    for key,value in distance.items():assert path[key]==value
                stage_index+=1
            previous=raw;last=raw
        if kind=='case_end':
            assert raw['boundary']is None and raw['host_calls']==[]and raw['stage_count']==5604 and raw['locale_writes']==0 and raw['locale_after']==locale
            for call in raw['calls']:assert call['stack_after']==1048576
            calls=[x for x in raw['calls']if x['role']!='original_allocator'];assert len(calls)==5606 and all(x['returned']for x in calls)
        if(line_index+1)%100==0:
            progress=dict(records=line_index+1,stages=stage_index,seconds=time.monotonic()-began);(out/'progress.json').write_text(json.dumps(progress)+'\n');print(json.dumps(progress),flush=True)
    assert decoder.record_index==6008 and stage_index==5604 and len(selections)==4 and next(expected,None)is None
    cas=decoder.finish(runtime['capture_cas']);assert cas['logical_bytes']==1662490742 and cas['logical_sha256']=='814cdb65300a5bd66d80e3801efda5b1f8cf97c260f1e92124b5e6a03712fb8f'
    assert expected_reader.bytes==fixtures['expected_uncompressed_bytes']==report['expected_uncompressed_bytes']and expected_reader.file_digest.hexdigest()==report['expectations_sha256']
    assert runtime['schema_version']==5 and runtime['output_protocol']=='bounded_stage_cas_jsonl_gzip'and runtime['budgets']==runtime['capture_cas']['limits']
    limits=runtime['budgets'];assert limits['logical_record_bytes']==2097152 and limits['logical_output_bytes']==8589934592 and limits['unique_blob_bytes']==536870912 and limits['blob_bytes']==16777216 and limits['blob_files']==65536 and limits['compressed_output_bytes']==268435456 and limits['owned_deadline_seconds']==60
    assert runtime['capture_cas']['compressed_bytes']==len(compressed)and runtime['capture_cas']['compressed_sha256']==hashlib.sha256(compressed).hexdigest()and runtime['memory_page_cap']==4096 and runtime['peak_memory_bytes']<=268435456 and runtime['js_heap_cap_mib']==512 and runtime['denied_imports']==878 and runtime['host_imports_throw']is True
    assert all(maximum[x]==0 for x in semantic.EMPTY_DOMAINS)and first_battle['player_ticks_since_selection']==6
    reconciled=sum(counts[k]for k in('strict_record_bytes','projection_leaves','vector_shape_fields','stage_identity_leaves'))
    assert reconciled==report['comparison']['compared_leaves']and counts['unknown_cells']==report['comparison']['declared_unknown_cells']and counts['unwritten_pickup_arrival_words']==report['comparison']['unwritten_pickup_arrivals']
    terminal=json.loads((directory/'process-terminal.json').read_text());owned=json.loads((directory/'owned-process.json').read_text());assert terminal['exit_code']==0 and terminal['deadline_exceeded']is False and owned['deadline_seconds']==60
    assert semantic.missing(terminal['pid'])and semantic.missing(terminal['pgid'],True)and(directory/'stderr.log').stat().st_size==0 and json.loads((directory/'differences.json').read_text())==[]
    for name,digest in report['source_sha256_before'].items():assert sha(source/name)==digest==sha(ROOT/name),name
    result=dict(status='passed_scoped_read_only_review',comparison=str(directory/'comparison.json'),comparison_sha256=sha(directory/'comparison.json'),source_files=98,production_files=85,current_and_frozen_sources_verified=True,reviewer_script_sha256=sha(Path(__file__)),transport=dict(source= str(decoder_path),sha256=sha(decoder_path),frozen_root_decoder_sha256=DECODER_SHA,private_fast_only_one_string_quoting_line_changed=bool(args.private_fast_decoder),independent_26negative_review_sha256=sha(codec_review),each_logical_SHA_and_all_occurrences_verified=True,full_finish=cas,one_complete_gzip_member=True),
        stream_record_counts=dict(records),expected_stream=expected_reader.receipt(),comparison_counts=dict(counts),reconciled_known_leaves=reconciled,nonexport_sections_identical=True,full_declared_projection_recompared=True,omitted_payload_max_counts={x:maximum[x]for x in semantic.EMPTY_DOMAINS},observed_vector_max_counts=dict(maximum),first_guardian=first_guardian,guardian_distinct_GUIDs=sorted(guardian_owners),guardian_owner_captures=guardian_captures,guardian_payload_comparisons=guardian_payloads,guardian_corruption_checks=negative,
        selections=selections,battle_first_actual_buff=first_battle,battle_player_countdown=battle_countdowns,Battle_effect8_owner0_payload_and_CD_independently_checked=True,independent_Dijkstra=distance,final_progression=last['projection']['progression'],final_gold=last['projection']['gold'],observed_packet_max=packet_max,packets_payload_semantics_claimed_compared=False,
        original_process_terminal=terminal,original_wait60s_did_not_timeout=True,parent_process_seconds_including_recomparison=report['process']['seconds'],actual_Node_seconds_not_inferred_from_parent_total=True,original_or_model_or_checker_executed_by_reviewer=False,new_original_cases=0,new_full880_frames=0,scope='One human warrior seed0/navFalse stationary400 controlled14-tail frames, realphase1/ownedcapacity/None; independent preparsedworld/originalsnapshot/externalclock, not full880/native/wholegame.',elapsed_seconds=time.monotonic()-began)
    (out/'static-image-reads.json').write_text(json.dumps(read_static.proofs,indent=2)+'\n');result['static_image_reads_sha256']=sha(out/'static-image-reads.json')
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],battle_first=first_battle)),flush=True)
if __name__=='__main__':main()
