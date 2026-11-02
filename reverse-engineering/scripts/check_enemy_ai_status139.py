#!/usr/bin/env python3
"""Expected-first real922 slow -> full925 current139 controlled continuity."""
from pathlib import Path
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_enemy_ai_status139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import projection,load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA,missing
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.thunder_clap_world139 import prepare_thunder_world139
from core_spec.thunder_clap139 import ThunderClapDefinition139,cast_thunder_clap139
from core_spec.death139 import OrdinaryDamageState139,DefaultDeathSources139,word139
from core_spec.death_pickups139 import PickupVector139
from core_spec.hit_events139 import produce_default_cleave_hit_sources139,prove_owned_execution11_absent139
from core_spec.candidates139_data import DEFINITIONS139
from core_spec.incoming_history139 import projection as history_projection
from core_spec.enemy_ai_status139 import from_thunder_slow139,update_enemy_ai_status139

ENGLISH={5830904:'Kobold Vermin'}
load=lambda p:json.loads(Path(p).read_text())


def closure():
    names=set(production_sources135(ROOT,'core_spec.enemy_ai_status139','core_spec.thunder_clap_world139','core_spec.thunder_clap139','core_spec.opening139','core_spec.player_update139'))|set('scripts/'+n for n in['check_enemy_ai_status139.py','build_enemy_ai_status139_oracle.py','run_enemy_ai_status139_oracle.mjs','check_player_update139.py','check_asset_world139.py','production_closure135.py','source_closure137.py'])
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def ai_projection(state):
    ai=state.ai;path=ai.distance_map
    return dict(records432_cells=[list(r)for r in ai.records432],history=history_projection(ai.history),path=None if path is None else dict(capacity=len(path.values_u16),count=len(path.values_u16),start_index=path.start_index,field24=path.field24,u16le_sha256=hashlib.sha256(struct.pack('<'+'H'*len(path.values_u16),*path.values_u16)).hexdigest()),path_clock2372_bits=ai.distance_clock2372_bits,incoming992_hex=struct.pack('>d',ai.incoming.incoming992).hex(),last_hit1652_bits=ai.incoming.last_hit1652_bits,categories={k:struct.pack('>d',v).hex()for k,v in ai.incoming.category1112},movement_sequence2412=ai.movement_sequence2412)


def prepare(world,boundary,cid,initial_offset=0x41000000):
    opening,gain,selected,initial=prepare_thunder_world139(0,world);rows=initial.growth.units432_cells;anchor=rows[0]
    positions=[]
    for dx in(initial_offset,0xc1000000):
        x,y=f.add(word139(anchor,316),dx),word139(anchor,320);height=world.height(x,y)
        if not height.found:raise RuntimeError('Canonical legal player position unresolved')
        positions.append((x,y,height.value_bits))
    profile=[None]*376
    for o in(160,*range(260,336,4)):profile[o:o+4]=bytes(4)
    profile[344]=profile[345]=1;owned=initial.growth.owned_records80
    declarations=tuple((DEFINITIONS139[k][0],bytes.fromhex(DEFINITIONS139[k][1]))for k in('cleave','thunder_clap'))
    hit=produce_default_cleave_hit_sources139(tuple(profile),(owned[0],),initial.growth.racial_record80);hit=replace(hit,owned_execution_scan=prove_owned_execution11_absent139(owned,declarations));sources=DefaultDeathSources139(hit,(),(),(),(),())
    g=initial.growth;death=OrdinaryDamageState139(g.units432_cells,g.rng_words,0,1,0,(),0,0,opening.counter,1,0,g.current_hp_bits,g.derived_bits[1536],PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),sources)
    cast=cast_thunder_clap139(death,positions[0],{str(k):v for k,v in g.derived_bits.items()},ThunderClapDefinition139(*declarations[1]),owned[1],initial.spell_sets,world)
    state=from_thunder_slow139(initial,cast,positions[0]);times=[f.from_float(j/8)for j in range(1,24)]+[boundary]+[f.from_float(j/8)for j in range(25,37)];updates=[];previous=0
    for j,now in enumerate(times):updates.append(dict(now_bits=now,dt_bits=f.sub(now,previous),retarget=j>=23));previous=now
    case=dict(id=cid,app_seed_u64='0',amount=5,select_index=0,action=dict(npc_index=0,initial_offset_x_bits=initial_offset,retarget_offset_x_bits=0xc1000000,initial_height_bits=positions[0][2],retarget_height_bits=positions[1][2]),updates=updates)
    stages=[];diagnostics=[];post_cast=projection(state.player);after_cast_ai=ai_projection(state)
    for control in updates:
        player=positions[int(control['retarget'])];result=update_enemy_ai_status139(state,control['now_bits'],control['dt_bits'],player,world,english_names=ENGLISH);state=result.state
        stages.append(dict(player=projection(state.player),ai=ai_projection(state),new_packets=[list(p)for p in result.packets]))
        diagnostics.append(dict(attacks=[list(x)for x in result.attacks],motions=[list(x)for x in result.motions],routing=[list(x)for x in result.routing],path_recomputed=result.path_recomputed,motion_speed_proofs=[list(x)for x in result.motion_speed_proofs],active_guard12=result.active_guard12))
    outgoing=dict(accounted_total_bits=str(cast.state.accounted_total_bits),spell_totals64=[[k,str(v)]for k,v in cast.state.spell_totals64],kills1084=cast.state.kills1084,elites1088=cast.state.elites1088,counter2408=cast.state.counter2408,movement_sequence2412=cast.state.movement_sequence2412,killcost2420_bits=cast.state.killcost2420_bits,pickup_count=cast.state.pickups.count)
    return dict(id=cid,group='real_guard12_contact_then_expiry'if initial_offset==0 else{0x403fffff:'expiry_below_neighbor',0x40400000:'expiry_equal',0x40400001:'expiry_above_neighbor'}[boundary],input=case,opening=opening,initial=projection(initial),post_cast_player=post_cast,post_cast_ai=after_cast_ai,cast_outgoing=outgoing,cast_known_packets=[list(p)for p in cast.known_packets],cast_selected_ids=list(map(str,cast.selected_ids)),cast_effect_writes=[list(x)for x in cast.effect_writes],slowed_guids=list(map(str,state.slowed_guids)),player_positions=[list(x)for x in positions],stages=stages,diagnostics=diagnostics)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['study','pilot','full'],default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original denied in model expectation')
    sys.addaudithook(audit)
    try:
        world,*_=load_world139(WORLD);boundaries=[0x40400000]if args.phase=='pilot'else[0x40400000,0x403fffff,0x40400001];rows=[prepare(world,b,i)for i,b in enumerate(boundaries)]
        if args.phase!='pilot':rows.append(prepare(world,0x40400000,len(rows),0))
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('enemy-ai-status139-'+args.phase+'-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    if args.phase=='study':
        summaries=[]
        for row in rows:
            target=int(row['slowed_guids'][0]);speeds=[dict(frame=i,now_bits=row['input']['updates'][i]['now_bits'],proof=p)for i,d in enumerate(row['diagnostics'])for p in d['motion_speed_proofs']if p[0]==target]
            summaries.append(dict(id=row['id'],group=row['group'],slowed_guids=row['slowed_guids'],target_motion_speeds=speeds,contact_attempts=sum(len(d['attacks'])for d in row['diagnostics']),guard12_contact_attempts=sum(len(d['attacks'])for d in row['diagnostics']if d['active_guard12']),routing=sorted(set(x[1]for d in row['diagnostics']for x in d['routing'])),final_hp_bits=row['stages'][-1]['player']['growth']['current_hp_bits']))
        save(out/'study.json',dict(original_executions=0,source_hashes=sources,source_edges=edges,summary=summaries));print(json.dumps(dict(directory=str(out),summary=summaries)),flush=True);return
    assert all(sha(p)==h for p,h in[(SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA),(WORLD/'receipt.json',WORLD_SHA)])
    m=build(out)
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);expected=[]
    from core_spec.opening139 import opening_projection139
    for row in rows:copyrow=dict(row);copyrow['opening']=opening_projection139(row['opening']);expected.append(copyrow)
    save(out/'expected.json',expected);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in['inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json']};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,controlled_player_position_only=True,all_source_owners_retained=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_enemy_ai_status139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=120))
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal)
    observations=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diff=[]
    def eq(cid,key,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(id=cid,field=key,expected=want,actual=got))
    def cells(cid,label,want,physical):
        eq(cid,label+'.rows',len(want),len(physical))
        for j,(row,hx)in enumerate(zip(want,physical)):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)
            for k,(v,b)in enumerate(zip(row,raw)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
                else:eq(cid,f'{label}[{j}]+{k}',v,b);counts[label+'_known']+=1
    def player(cid,label,want,got):
        for k in['racial80_hex','scalar','source_flags','spell_sets']:eq(cid,label+'.'+k,want[k],got[k])
        eq(cid,label+'.growth',want['growth'],got['capture']['projection'])
        for key in['live','aura']:
            for fkey in['capacity','count']+(['flag2569']if key=='aura'else[]):eq(cid,label+'.'+key+'.'+fkey,want[key][fkey],got[key][fkey])
            cells(cid,key,want[key]['storage'],got[key]['storage'])
    def ai(cid,label,want,got,ps):
        for k in['path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories']:eq(cid,label+'.'+k,want[k],got[k])
        eq(cid,label+'.historyheader',want['history']['header'],got['history']['header']);eq(cid,label+'.historyactive',want['history']['active'],got['history']['active']);cells(cid,'history',want['history']['storage'],got['history']['storage']);cells(cid,'NPC',want['records432_cells'],ps['capture']['background']['units']['storage']);eq(cid,label+'.sequence',want['movement_sequence2412'],ps['capture']['background']['movement_sequence2412'])
    for row,a in zip(expected,observations):
        cid=row['id'];eq(cid,'id',cid,a['id']);eq(cid,'opening_packets',row['opening']['packets'],a['opening']['packets']);player(cid,'initial',row['initial'],a['player_before']);player(cid,'after_real_thunder',row['post_cast_player'],a['after_thunder']);ai(cid,'after_real_thunder',row['post_cast_ai'],a['after_thunder_ai'],a['after_thunder'])
        for k,v in row['cast_outgoing'].items():eq(cid,'real922_outgoing.'+k,v,a['after_thunder_combat'][k])
        cursor=0
        for p in row['cast_known_packets']:
            at=next((j for j in range(cursor,len(a['thunder_new_packets']))if a['thunder_new_packets'][j]==p),None);eq(cid,'thunder_known_packet',True,at is not None);cursor=at+1 if at is not None else cursor
        previous=a['after_thunder']
        for j,(want,got,control,diag)in enumerate(zip(row['stages'],a['frames'],row['input']['updates'],row['diagnostics'])):
            tag='frame'+str(j);player(cid,tag,want['player'],got['after']);ai(cid,tag,want['ai'],got['ai'],got['after']);eq(cid,tag+'.packets',want['new_packets'],got['new_packets'])
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);struct.pack_into('<I',inherited,2352,control['now_bits']);position=row['player_positions'][int(control['retarget'])]
            for k,v in enumerate(position):struct.pack_into('<I',inherited,1416+4*k,v)
            eq(cid,tag+'.only_clock_XYZ_controls',inherited.hex(),got['before']['capture']['raw_game2592_hex']);counts['inherited_Game2592_bytes']+=2592
            for cells_after,oldhx,newhx in zip(want['ai']['records432_cells'],got['before']['capture']['background']['units']['storage'],got['after']['capture']['background']['units']['storage'],strict=True):
                physical=bytearray.fromhex(oldhx)
                for k,v in enumerate(cells_after):
                    if v is not None:physical[k]=v
                eq(cid,tag+'.fullNPCphysical',physical.hex(),newhx);counts['NPC_full_physical_replay_bytes']+=432
            for key in['live','aura','racial80_hex']:eq(cid,tag+'.unchanged_'+key,a['player_before'][key],got['after'][key])
            for key in['pickups','special','windows','boundaries','auxiliary','claims','counter2408']:eq(cid,tag+'.preserved_'+key,a['after_thunder']['capture']['background'][key],got['after']['capture']['background'][key])
            counts['full925']+=1;counts['contact_attempts']+=len(diag['attacks']);counts['guard12_contact_attempts']+=len(diag['attacks'])if diag['active_guard12']else 0;counts['active_guard12_frames']+=diag['active_guard12'];counts['motion221']+=len(diag['motions']);counts['path_rebuilds']+=diag['path_recomputed'];counts['slow_motion_proofs']+=sum(p[3]for p in diag['motion_speed_proofs']);counts['unslow_motion_proofs']+=sum(not p[3]for p in diag['motion_speed_proofs']);previous=got['after']
    eq(-1,'completed_cases',len(expected),len(observations));runtime=load(out/'runtime.json')if(out/'runtime.json').exists()else None
    n=len(expected);frames=sum(len(r['stages'])for r in expected)
    if code==0 and runtime is not None:
        assert runtime['full_calls']=={'2945':n,'1600':n,'1108':n,'4677':n,'1093':n,'922':n,'925':frames}and runtime['fresh_instances']==n and runtime['allocator_calls']==5*n and runtime['stack_checks']==11*n+frames
        assert len(runtime['target_and_setup_returns'])==6*n+frames and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['target_and_setup_returns'])
        assert len(runtime['world_source_checks'])==6*n+frames and all(x['unchanged']and x['ranges']==2318 for x in runtime['world_source_checks'])
        assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['peak_memory_bytes']==177078272 and runtime['error']is None and terminal['pid_missing']and terminal['pgid_missing']
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',diff);artifacts={n:sha(out/n)for n in['actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','prepared.json','stderr.log','differences.json']if(out/n).exists()}
    comp=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(expected),completed_cases=len(observations),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,limits=['RealThunder slow producer then standalonefull925, not2123/1238/main884 schedule.','No NPC/source/CD/racial/live clearing; live1020 physically retained beyond its read-only expiry predicate.','Only default nonfatal ordinary sources; naturalApp/worldRc/externref/native/fullgame remainPending.'])
    save(out/'comparison.json',comp);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),counts=dict(counts),process=terminal,first_differences=diff[:4])),flush=True)
    if code or len(observations)!=len(expected)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
