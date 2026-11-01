#!/usr/bin/env python3
"""Read-only static Aura-origin audit plus explicitly historical observations.

No original/model/checker/trace producer is executed. A direct-call subgraph is
not a resolution of call_indirect or an alias-complete proof of ID nonwriters.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,static_reader,missing
from review_combat137 import exports
from review_resource_consumer137 import identities

ROOT=Path(__file__).resolve().parents[1]
TRACE=ROOT/'evidence/player-aura-origin0135-static-20261101T220416.107301Z'
CORRECTED=ROOT/'evidence/player-aura-origin0135-static-20261101T220724.149178Z'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
PROBE=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def clean(line):return line.split(';;',1)[0].strip()

def structure(text):
    stack=[];blocks={};inside={}
    for number,line in enumerate(text.splitlines(),1):
        instruction=clean(line);inside[number]=tuple(stack)
        if re.match(r'^(block|loop|if)(\s|$)',instruction):
            blocks[number]=dict(kind=instruction.split()[0],start=number,end=None,else_line=None);stack.append(number)
        elif instruction=='else':
            assert stack and blocks[stack[-1]]['kind']=='if';blocks[stack[-1]]['else_line']=number
        elif instruction.startswith('end'):
            assert stack;blocks[stack.pop()]['end']=number
    assert not stack
    return blocks,inside

def line_of(lines,needle):
    found=[i for i,line in enumerate(lines,1)if clean(line)==needle]
    assert len(found)==1,(needle,found);return found[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve();out.mkdir();began=time.monotonic();trace=load(TRACE/'trace.json')
    assert sha(TRACE/'trace.json')=='4207c163c4d5ed12aaae6c31f5d2fecf36126b2255e3a9a5e73b30a952dbaf37'
    assert trace['producer_sha256']=='8b72e813a58a67282452af4ff8752f392723a3c8c543d3d636d09627c329a934'
    corrected=load(CORRECTED/'trace.json');assert sha(CORRECTED/'trace.json')=='38254937fd50ca7aa6c440ed9fc4aa32d25c8d1cb1862499737779be744c7474'
    assert sha(ROOT/'scripts/trace_player_aura_origin135.py')==corrected['producer_sha256']=='ca6810fd59c74ced7be46d4aa343ded688614b65987a7b14bbda30f1511e2c1c'
    for key in('functions','windows','direct_call_closures','constructor_rules','default_opening_requirements'):
        assert trace[key]==corrected[key]
    assert all(corrected['default_opening_rules'][key]for key in('final_Aura_state_not_proven_by_direct_graph','App14340336_history_not_proven_by_direct_graph','controller_notification_input_remains_explicit','indirect_call_edges_not_resolved'))
    assert not trace['original_executed']and not trace['models_executed']and trace['new_original_cases']==0
    original=ORIGINAL.read_bytes();assert hashlib.sha256(original).hexdigest()==trace['original_sha256']=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
    targets={1202,23581,42920,44447};ids=sorted({n for c in trace['direct_call_closures']for n in c['functions']}|targets|{1512})
    binary=identities(original,ids);texts={};calls={};indirect=[];proofs=[];total=0
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.execute('pragma query_only=on');meta={k:json.loads(v)for k,v in db.execute('select key,value from meta')}
        assert meta['original_sha256']==trace['original_sha256']
        for idx in ids:
            lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(idx,)).fetchone()
            assert(bs,be)==(binary[idx]['body_start'],binary[idx]['body_end'])and 0<hi-lo<524288
            stream.seek(lo);raw=stream.read(hi-lo);total+=len(raw);text=raw.decode();texts[idx]=text
            direct=sorted(set(int(match.group(1))for match in re.finditer(r'^\s*(?:return_call|call)\s+(\d+)\)*\s*$',text,re.M)))
            indexed=[row[0]for row in db.execute('select distinct callee from calls where caller=?order by callee',(idx,))]
            assert direct==indexed,(idx,direct,indexed);calls[idx]=direct
            for number,line in enumerate(text.splitlines(),1):
                if 'call_indirect'in line:indirect.append(dict(function=idx,line=number,instruction=clean(line)))
            proofs.append(dict(**binary[idx],wat_start=lo,wat_end=hi,wat_sha256=hashlib.sha256(raw).hexdigest()))
        literal_refs=db.execute('select function_idx,value,wat_line,operation from iconsts where value=?order by function_idx,wat_line',(14340336,)).fetchall()
    for item in trace['functions']:
        idx=item['index'];assert sha(TRACE/(str(idx)+'.wat'))==item['WAT_sha256']
        assert texts[idx]==(TRACE/(str(idx)+'.wat')).read_text()and binary[idx]['body_sha256']==item['body_sha256']
    for window in trace['windows']:
        start,end=window['lines'];assert texts[window['index']].splitlines()[start-1:end]==window['instructions']
    f=texts[1560];lines=f.splitlines()
    assert f.count('local.tee 3\n')==1 and 'local.set 3\n'not in f
    assert 'i32.const 2976\n    i32.sub\n    local.tee 3'in f
    assert 'local.get 3\n                  i64.const 17179869184\n                  i64.store offset=2088'in f
    assert 'local.get 3\n                  i64.const 0\n                  i64.store offset=2096'in f
    assert 'local.get 3\n                  i32.const 0\n                  i32.store16 offset=2657 align=1'in f
    assert 'i32.const 88\n                  i32.add\n                  local.tee 1\n                  call 1512'in f
    assert 'local.get 0\n                  local.get 1\n                  i32.const 2592\n                  memory.copy'in f
    assert len(re.findall(r'^\s*call 1512\s*$',f,re.M))==1 and 1202 not in calls[1560]
    assert (2088-88,2096-88,2657-88)==(2000,2008,2569)
    assert struct.unpack('<II',struct.pack('<Q',17179869184))==(0,4)
    beginning=texts[1089].splitlines();blocks,inside=structure(texts[1089])
    first_if=16;assert clean(beginning[first_if-2])=='i32.load8_u offset=2576'and blocks[first_if]['kind']=='if'
    boss=[i for i,line in enumerate(beginning,1)if clean(line)=='call 2785'];assert len(boss)==5
    assert all(first_if in inside[line]for line in boss)and blocks[first_if]['else_line']is None
    branch=1890;assert clean(beginning[branch-1]).startswith('br_if 1')
    assert clean(beginning[branch-3])=='i32.load8_u offset=2576'and clean(beginning[branch-2])=='i32.eqz'
    target=blocks[inside[branch][-2]]
    late=[i for i,line in enumerate(beginning,1)if clean(line)=='call 5745'];assert len(late)==1
    assert target['start']<branch<late[0]<target['end']
    definition=texts[10146].splitlines();assert sum(clean(line)=='call 5745'for line in definition)==1
    assert 'i32.load offset=2056'in texts[10146]and'i32.const 36\n      i32.mul'in texts[10146]
    assert 'local.get 3\n          i32.eqz\n          br_if 1'in texts[10146]
    # Verify only the claimed conditional direct graph. Unknown indirect
    # targets stay unresolved, never silently omitted from the scope label.
    closures=[]
    for declared in trace['direct_call_closures']:
        skipped={(x['caller'],x['callee'])for x in declared['excluded_edges']};seen=set();todo=[declared['entry']];edges=[]
        while todo:
            idx=todo.pop()
            if idx<878 or idx in seen:continue
            seen.add(idx)
            for callee in calls[idx]:
                if(idx,callee)in skipped:continue
                edges.append([idx,callee]);todo.append(callee)
        assert sorted(seen)==declared['functions']and sorted(edges)==declared['direct_edges']and not seen&targets
        sites=[item for item in indirect if item['function']in seen]
        closures.append(dict(entry=declared['entry'],functions=len(seen),direct_edges=len(edges),excluded_edges=declared['excluded_edges'],
                             no_known_target_in_conditional_direct_graph=True,unresolved_indirect_sites=sites,
                             indirect_or_alias_complete_no_writer_proof=False))
    assert sorted({row[0]for row in literal_refs})==[23581,42920,44447]
    writers=[]
    for idx in(23581,42920,44447):
        text=texts[idx];loc=text.index('i32.const 14340336');excerpt=text[loc:loc+400]
        assert 'i32.load'in excerpt and'i32.store'in excerpt and'i32.const 1'in excerpt and'i32.add'in excerpt
        writers.append(dict(function=idx,body_sha256=binary[idx]['body_sha256'],literal_load_increment_store_excerpt=excerpt))
    static=static_reader(original);assert static(14340336,4)==b'\1\0\0\0'
    # Existing historical observation, not a fresh oracle or universal input
    # producer. Preserve its object0/class1/race1/seed0/profile identity.
    receipt=load(PROBE/'entry-world135-probe-receipt.json');config=load(PROBE/'entry-world135-config.json');runtime=load(PROBE/'entry-world135-runtime.json');observed=load(PROBE/'observations.json')
    assert sha(PROBE/'entry-world135-probe-receipt.json')=='530f079d322365691ce897120ac0014be0da416eb048861b4d42ab988160556c'
    assert observed['receipt_sha256']==sha(PROBE/'entry-world135-probe-receipt.json')and receipt['runtime']==runtime
    for name,digest in receipt['artifacts'].items():assert sha(PROBE/name)==digest
    assert receipt['source_before']==receipt['source_after']
    for name,digest in receipt['source_before'].items():assert sha(PROBE/'source-snapshot'/name)==digest
    profile=config['selected_profile_input']
    assert(profile['region_id'],profile['class_byte'],profile['race_byte'],profile['object_id_u64'],profile['app_lcg_seed_u64'])==('elwynn',1,1,'0','0')
    assert profile['live_bytes']==372 and profile['allocation_bytes']==376
    assert runtime['status']=='original_entry_returned'and runtime['error']is None and not runtime['external_network_permitted']and not runtime['user_profile_used']
    assert receipt['process']['exit_code']==0 and receipt['process']['pid']==54944 and missing(54944)
    module=(PROBE/'entry-world135.wasm').read_bytes();before,after=sections(original),sections(module)
    assert[x[0]for x in before]==[x[0]for x in after]and all(original[a:b]==module[c:d]for(k,a,_,b),(_,c,_,d)in zip(before,after)if k!=7)
    assert exports(module)[:len(exports(original))]==exports(original)
    snapshots=[]
    for state in observed['states']:
        if state['label']not in('after_real_world6730','after_real_begin1089'):continue
        artifact=state['memory'];path=PROBE/artifact['file'];assert sha(path)==artifact['sha256']and path.stat().st_size==artifact['bytes']and artifact['complete']
        assert artifact in runtime['captures']
        with path.open('rb')as stream:
            stream.seek(state['G']);game=stream.read(2592);stream.seek(14340336);notification=struct.unpack('<I',stream.read(4))[0]
        assert game.hex()==state['game2592_hex']
        aura=struct.unpack_from('<3I',game,2000);assert aura==(0,4,0)and game[2569]==game[2576]==0 and struct.unpack_from('<I',game,2056)[0]==0 and notification==1
        snapshots.append(dict(label=state['label'],path=str(path),bytes=artifact['bytes'],sha256=artifact['sha256'],Game=state['G'],Aura2000_2004_2008=list(aura),initialized2569=game[2569],flags2576=game[2576],definitions2056=0,App14340336=notification))
    assert len(snapshots)==2
    save(out/'body-and-gate-proofs.json',dict(functions=proofs,primary_windows=trace['windows'],conditional_direct_closures=closures,
        first_debug_if=blocks[first_if],boss_call_lines=boss,second_debug_exit_branch=branch,second_debug_exit_target=target,late5745_lines=late,
        literal_ID_reference_rows=literal_refs,literal_ID_increment_writers=writers,all_unresolved_indirect_sites=indirect,original_static_reads=static.proofs))
    result=dict(status='passed_local_static_and_historical_observation_review_with_unresolved_indirect_boundary',
        version='0.135.1',actual_build='90898d5e3',trace=str(TRACE/'trace.json'),trace_sha256=sha(TRACE/'trace.json'),producer_sha256=trace['producer_sha256'],
        corrected_trace=str(CORRECTED/'trace.json'),corrected_trace_sha256=sha(CORRECTED/'trace.json'),current_producer_sha256=corrected['producer_sha256'],
        old_trace_source_snapshot_available=False,
        reviewer_script_sha256=sha(Path(__file__)),original_sha256=trace['original_sha256'],bounded_WAT_functions=len(ids),bounded_WAT_bytes_read=total,
        constructor_frame_offset=88,constructor_local_writes=dict(aura_header=[0,4,0],initialized2569=0,output_copy_bytes=2592,direct1512=True,direct1202=False),
        conditional_direct_closures=closures,unresolved_indirect_site_count=len(indirect),global_indirect_no1202_or_noIDwriter_proven=False,
        known_literal14340336_writer_functions=[23581,42920,44447],arbitrary_computed_pointer_ID_alias_analysis_complete=False,
        historical_observation=dict(receipt=str(PROBE/'entry-world135-probe-receipt.json'),receipt_sha256=sha(PROBE/'entry-world135-probe-receipt.json'),
            config_sha256=sha(PROBE/'entry-world135-config.json'),runtime_sha256=sha(PROBE/'entry-world135-runtime.json'),observations_sha256=sha(PROBE/'observations.json'),
            selected_profile_input=profile,snapshots=snapshots,kind='Existing controlled original observation, not new differential cases or a complete menu producer.'),
        correction='Do not promote the conditional direct graph to complete indirect reachability. Historical object0 evidence supports only its stated input. Current object42 natural AppID producer needs corresponding captured evidence; controller may supply explicit typed1 input.',
        body_proofs_sha256=sha(out/'body-and-gate-proofs.json'),new_original_executions=0,new_model_or_checker_executions=0,new_original_cases=0,new_mainloop_frames=0,
        current_object42_natural_producer_verified=False,complete_profile_menu_producer=False,full_WAT_read=False,elapsed_seconds=time.monotonic()-began)
    assert result['elapsed_seconds']<60
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],unresolved_indirect=len(indirect),WAT_bytes=total)),flush=True)

if __name__=='__main__':main()
