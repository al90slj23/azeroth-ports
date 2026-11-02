#!/usr/bin/env python3
"""Expected-first fresh complete952 before40s, genuine full1108 owners."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,ast,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from check_growth_world139 import ROOT,SOURCE,SOURCE_SHA,NODE,NODE_SHA,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,missing
from incoming139_tools import sha,save
from build_spawn_schedule139_oracle import build
from check_asset_world139 import load_world139
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.opening139 import DefaultOpeningInput139,initialize_default_opening139,opening_projection139
from core_spec.opening_profile139 import EmptyAccountSources139
from core_spec.spawn_schedule139 import from_opening139,update_spawn_schedule139,projection139

def closure():
    names=set(production_sources135(ROOT,'core_spec.spawn_schedule139','core_spec.opening139'))|set('scripts/'+n for n in('check_spawn_schedule139.py','build_spawn_schedule139_oracle.py','run_spawn_schedule139_oracle.mjs','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])

def expected(case,world):
    opening=initialize_default_opening139(DefaultOpeningInput139(int(case['app_seed_u64']),EmptyAccountSources139(0,0,0,0),tuple([165]*40)),world)
    state=from_opening139(opening);frames=[];timeline=[];produced=[];now=0
    for j in range(case['frames']):
        now=f.add(now,case['dt_bits']);result=update_spawn_schedule139(state,now,case['dt_bits'],world);state=result.state;v=projection139(state)
        timeline.append(dict(frame=j,**{k:w for k,w in v.items()if k not in('records432_cells','packets')},packet_count=len(v['packets'])))
        produced.extend([dict(frame=j,slot=x[0],definition_index=x[1],guid=x[2],origin=x[3])for x in result.new_NPCs])
        if j in case['checkpoints']or j==case['frames']-1:frames.append(dict(frame=j,projection=v))
    return dict(opening=opening_projection139(opening),frames=frames,timeline=timeline,produced=produced)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args()
    files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    assert all(sha(p)==s for p,s in((SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(WORLD/'receipt.json',WORLD_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA)))
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('spawn-schedule139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    specs=[(0,8)]if args.phase=='pilot'else[(0,600),(1,320),(42,160)]
    cases=[]
    for j,(seed,n)in enumerate(specs):cases.append(dict(id=j,app_seed_u64=str(seed),dt_bits=f.from_float(.0625),frames=n,checkpoints=sorted(set(x for x in(0,1,7,15,31,63,127,255,479,n-1)if x<n))))
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original input denied during expectation')
    sys.addaudithook(audit)
    try:
        world,_,_=load_world139(WORLD);rows=[dict(id=c['id'],expected=expected(c,world))for c in cases]
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files}
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',cases);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden,layer='Python open audit'))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',manifest['module_file'],'expectation-read-audit.json')}
    save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,all_background_owners_retained=True,only_clock2352_written_by_runner=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_spawn_schedule139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=120))
        try:code=p.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code=p.returncode
    terminal=dict(pid=p.pid,pgid=p.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(line)for line in(out/'actual.jsonl').read_text().splitlines()];diff=[];counts=Counter()
    def eq(case,field,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(case=case,field=field,expected=want,actual=got))
    for row,a in zip(rows,actual):
        case=row['id'];want=row['expected'];eq(case,'id',case,a['id']);eq(case,'newGame',False,a['new_Game_pointer']==a['old_snapshot_Game_not_target']);eq(case,'opening-packets',want['opening']['packets'],a['opening']['packets']);eq(case,'framecount',len(want['frames']),len(a['frames']));eq(case,'timeline',want['timeline'],a['timeline'])
        previous=a['before']
        for frame,got in zip(want['frames'],a['frames']):
            j=frame['frame'];e=frame['projection'];v=got['view'];bg=v['background'];eq(case,f'f{j}.frame',j,got['frame'])
            for key in('capacity','count'):eq(case,f'f{j}.NPC.{key}',e[key],bg['units'][key])
            for index,(desired,hx)in enumerate(zip(e['records432_cells'],bg['units']['storage'])):
                for off,(expectedbyte,actualbyte)in enumerate(zip(desired,bytes.fromhex(hx))):
                    if expectedbyte is None:counts['NPC_None']+=1;counts['NPC_nonzero_None']+=bool(actualbyte)
                    else:eq(case,f'f{j}.NPC{index}+{off}',expectedbyte,actualbyte);counts['NPC_known']+=1
                if index<len(previous['background']['units']['storage']):
                    old=bytes.fromhex(previous['background']['units']['storage'][index]);new=bytes.fromhex(hx)
                    for off,value in enumerate(desired):
                        if value is None:eq(case,f'f{j}.unknownNPC{index}+{off}',old[off],new[off]);counts['NPC_None_physically_conserved']+=1
            eq(case,f'f{j}.packets',e['packets'],v['packets']);counts['known_packet_snapshots']+=len(e['packets'])
            for key in('rng_words',):eq(case,f'f{j}.{key}',e[key],v['projection'][key])
            for key in('pickups','special','windows','boundaries','auxiliary','claims','movement_sequence2412'):eq(case,f'f{j}.background.{key}',a['before']['background'][key],bg[key]);counts['background_owners_conserved']+=1
            eq(case,f'f{j}.counter',e['counter2408'],bg['counter2408'])
            for key in('level','xp','pending','phase2587','current_hp_bits','derived_bits','player_fields','owned_records80_hex','candidates','selection_kind2585','generation_counter2400','flag2581','flags2573'):eq(case,f'f{j}.unchanged.{key}',a['before']['projection'][key],v['projection'][key])
            eq(case,f'f{j}.live',a['before']['live32_hex'],v['live32_hex'])
            allowed=set()
            for off,n in((1720,24),(1784,12),(1880,12),(2352,4),(2408,4),(2416,24)):allowed.update(range(off,off+n))
            for off,(old,new)in enumerate(zip(bytes.fromhex(previous['raw_game2592_hex']),bytes.fromhex(v['raw_game2592_hex']))):
                if off not in allowed:eq(case,f'f{j}.Game{off}',old,new);counts['inherited_Game2592_bytes']+=1
            counts['full_checkpoints']+=1;previous=v
        counts['full952_calls']+=len(want['timeline']);counts['new_NPCs']+=len(want['produced']);counts['unlocked_definition1_spawns']+=sum(v['definition_index']==1 for v in want['produced']);counts['new_NPC_packet169']+=len(want['produced'])
        assert a['account368_before_hex']==a['account368_after_hex']and a['profile376_before_hex']==a['profile376_after_hex']and a['selection_canaries']==['c3'*16,'d7'*16]
    for n,h in sources.items():assert sha(ROOT/n)==h
    for n,h in frozen.items():assert sha(out/n)==h
    save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    if runtime is not None:
        assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None
        assert runtime['full_calls']=={'2945':len(cases),'1600':len(cases),'1108':len(cases),'952':sum(c['frames']for c in cases)}
        assert runtime['fresh_instances']==len(cases)and runtime['memory_cap_bytes']==268435456 and runtime['peak_memory_bytes']==177078272
        assert all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])
        assert all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
        assert all(runtime[k]is False for k in('NPC_positions_written_by_driver','NPC_states_or_timers_written_by_driver','velocity_or_path_headers_written_by_driver','RNG_or_budget_written_by_driver','old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','App_or_world_Rc_producer_executed','externref_restored'))
        assert runtime['real_initial_budget3']and runtime['active_initial_NPCs_retained']and runtime['full952_body_unchanged']
        assert runtime['native_executions']==runtime['full_mainloop_frames']==runtime['complete_games']==0
    artifacts={n:sha(out/n)for n in('actual.jsonl','stderr.log','runtime.json','owned-start.json','owned-terminal.json','prepared.json','differences.json')if(out/n).exists()}
    comparison=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(cases),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,scope='Actualcomplete952 on default fullopening before40s; noAI/player/mainframe; later timers Pending',limits=['Full1108 retains4NPC/2Rune/windows/special/bounds; genuine initialbudget3 andtimer values, noNPC/timer/RNG/velocity/path injection.','Clock2352/delta are explicit finite normalcomponent inputs .0625<=.1; no884 frame invoked.','Static139 tables and952/5719/20357/8740/1586/97427 are authority; no135 runtime transfer.','Nonordinary40s/60s/240s/Boss gates,farNPC/movement/death/pool/multiplayer/nondefault remainPending.','KnownNone bytes remainunknown andretain actualphysicalsource whereprovided.','Canonicalworld is independent input; originalresource-onlyv2snapshot is originalcontext, not independentApp/WorldRc producer.'])
    save(out/'comparison.json',comparison);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(cases),completed=len(actual),differences=counts['differences'],first_fields=[x['field']for x in diff[:6]],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(cases)or counts['differences']:raise SystemExit(1)
if __name__=='__main__':main()
