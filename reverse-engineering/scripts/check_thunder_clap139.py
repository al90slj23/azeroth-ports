#!/usr/bin/env python3
"""Expected-first139fullopening/selectedThunder/complete922 differential."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_thunder_clap139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import (prepare,projection,load_world139,WORLD,WORLD_SHA,
    CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA)
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.thunder_clap139 import ThunderClapDefinition139,cast_thunder_clap139
from core_spec.death139 import (OrdinaryDamageState139,DefaultDeathSources139,word139)
from core_spec.death_pickups139 import PickupVector139
from core_spec.hit_events139 import produce_default_cleave_hit_sources139,prove_owned_execution11_absent139
from core_spec.candidates139_data import DEFINITIONS139


def closure():
    names=set(production_sources135(ROOT,'core_spec.thunder_clap139','core_spec.opening139','core_spec.growth_world139','core_spec.player_update139','core_spec.player_effects139','resource_spec.world_query135'))|set('scripts/'+n for n in('check_thunder_clap139.py','run_thunder_clap139_oracle.mjs','build_thunder_clap139_oracle.py','check_player_update139.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def corpus(world,phase):
    opening,gain,selected,initial=prepare(world)
    profile=[None]*376
    for o in(160,*range(260,336,4)):profile[o:o+4]=bytes(4)
    profile[344]=profile[345]=1
    owned=initial.growth.owned_records80
    hit=produce_default_cleave_hit_sources139(tuple(profile),(owned[0],),initial.growth.racial_record80)
    declarations=tuple((DEFINITIONS139[k][0],bytes.fromhex(DEFINITIONS139[k][1]))for k in('cleave','thunder_clap'))
    hit=replace(hit,owned_execution_scan=prove_owned_execution11_absent139(owned,declarations))
    sources=DefaultDeathSources139(hit,(),(),(),(),())
    definition=ThunderClapDefinition139(*declarations[1]);derived={str(k):v for k,v in initial.growth.derived_bits.items()};rows=[]
    layouts=[('far_no_target',0,100.,1),('near_first_nonlethal',0,0.,2),('first_through_death_then_no_target',0,0.,8)]
    if phase=='full':
        layouts += [('each_natural_NPC_through_death',i,0.,8)for i in(1,2,3)]
        layouts += [('radius10_X_inclusive_neighbor',i,x,1)for i in range(4)for x in(9.9990234375,10.,10.0009765625)]
    for group,index,offset,repeats in layouts:
        row=initial.growth.units432_cells[index]
        player=(f.add(word139(row,316),f.from_float(offset)),word139(row,320),word139(row,324))
        state=OrdinaryDamageState139(initial.growth.units432_cells,initial.growth.rng_words,0,1,0,(),0,0,opening.counter,1,0,initial.growth.current_hp_bits,derived['1536'],PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),sources)
        sets=((),(),());stages=[];diagnostics=[];times=tuple(f.from_float(j/8)for j in range(repeats))
        for now in times:
            state=replace(state,now_bits=now)
            result=cast_thunder_clap139(state,player,derived,definition,owned[1],sets,world)
            state,sets=result.state,result.spell_sets
            stages.append(dict(records432_cells=[list(r)for r in state.records432],rng_words=list(state.rng_words),accounted_total_bits=str(state.accounted_total_bits),spell_sets=[list(x)for x in sets],owned80_hex=owned[1].hex(),player_xyz=list(player),phase2587=state.phase2587,spell_totals64=[[k,str(v)]for k,v in state.spell_totals64],kills1084=state.kills1084,elites1088=state.elites1088,counter2408=state.counter2408,movement_sequence2412=state.movement_sequence2412,killcost2420_bits=state.killcost2420_bits,player_hp1440_bits=state.player_hp1440_bits,maximum1536_bits=state.maximum1536_bits,xp1436=initial.growth.xp,pickup_capacity=state.pickups.capacity,pickup_count=state.pickups.count,pickups56_cells=[list(r)for r in state.pickups.storage],success=result.success))
            diagnostics.append(dict(selected_ids=[str(v)for v in result.selected_ids],base_damage_bits=result.base_damage_bits,radius_bits=result.radius_bits,effect_writes=[[str(g),o,b]for g,o,b in result.effect_writes],hits=[dict(target=str(g),amount_bits=a,critical=c,dead=r.dead,applied=r.applied,direct_reward_draws=r.direct_reward_draws,rewards=r.reward_events)for g,a,c,r in result.hits],known_packets=[list(p)for p in result.known_packets],enqueued_hits=[],enqueued_areas=[]))
        case=dict(id=len(rows),app_seed_u64='0',amount=5,dead_mask=0,select_index=0,action=dict(npc_index=index,offset_x_bits=f.from_float(offset),offset_y_bits=0),casts=times)
        rows.append(dict(id=case['id'],group=group,input=case,initial=projection(initial),player_xyz=list(player),stages=stages,diagnostics=diagnostics))
    return json.loads(json.dumps(rows))


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA and sha(CONTEXT)==CONTEXT_SHA and sha(GATE)==GATE_SHA and sha(RANGES)==RANGES_SHA and sha(WORLD/'receipt.json')==WORLD_SHA
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original input denied during expectation')
    sys.addaudithook(audit)
    try:world,*_=load_world139(WORLD);rows=corpus(world,args.phase)
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('thunder-clap139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    assert m['thunder_clap88_hex']==DEFINITIONS139['thunder_clap'][1]
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit_notOSaudit',opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,full_world_owners_retained=True,controlled_player_placement=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_thunder_clap139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=120))
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(s)for s in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();differences=[]
    def eq(cid,field,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(differences)<100:differences.append(dict(id=cid,field=field,expected=want,actual=got))
    def cells(cid,label,want,got,width):
        eq(cid,label+'.physical_rows',len(want),len(got))
        for j,(row,hx)in enumerate(zip(want,got,strict=False)):
            raw=bytes.fromhex(hx);assert len(raw)==len(row)==width
            for k,(v,b)in enumerate(zip(row,raw,strict=True)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
                else:eq(cid,f'{label}[{j}]+{k}',v,b);counts[label+'_known']+=1
    for row,a in zip(rows,actual,strict=False):
        cid=row['id'];eq(cid,'id',cid,a['id']);eq(cid,'playerplacement',row['player_xyz'],a['cast_stages'][0]['before_combat']['player_xyz']);previous=a['controlled_before'];initial=a['player_before']
        controlled=bytearray.fromhex(initial['capture']['raw_game2592_hex'])
        for k,v in enumerate(row['player_xyz']):controlled[1416+4*k:1420+4*k]=int(v).to_bytes(4,'little')
        eq(cid,'controlled_playerXYZ_only_Game_write',controlled.hex(),previous['capture']['raw_game2592_hex'])
        for key,width in(('live',32),('aura',16)):
            for field in('capacity','count')+(('flag2569',)if key=='aura'else()):eq(cid,'initial.'+key+'.'+field,row['initial'][key][field],initial[key][field])
            cells(cid,'initial_'+key,row['initial'][key]['storage'],initial[key]['storage'],width)
        for key in('racial80_hex','scalar','source_flags'):eq(cid,'initial.'+key,row['initial'][key],initial[key])
        for j,(want,got,diag)in enumerate(zip(row['stages'],a['cast_stages'],row['diagnostics'],strict=True)):
            pre,post=got['before'],got['after'];inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);inherited[2352:2356]=int(row['input']['casts'][j]).to_bytes(4,'little');eq(cid,'sameGame_clock_only'+str(j),inherited.hex(),pre['capture']['raw_game2592_hex']);counts['inherited_Game2592_bytes']+=2592
            c=got['combat']
            for n,(cells_after,before_hex,after_hex)in enumerate(zip(want['records432_cells'],got['before_combat']['records432_hex'],c['records432_hex'],strict=True)):
                before_raw,after_raw=bytes.fromhex(before_hex),bytes.fromhex(after_hex)
                for k,v in enumerate(cells_after):
                    if v is None:eq(cid,f'NPC_unknown_conserved[{n}]+{k}',before_raw[k],after_raw[k]);counts['NPC_unknown_physically_conserved']+=1
            for key,value in want.items():
                if key=='records432_cells':cells(cid,'NPC',value,c['records432_hex'],432)
                elif key=='pickups56_cells':cells(cid,'pickup',value,c['pickups56_hex'],56)
                else:eq(cid,'cast'+str(j)+'.'+key,value,c.get(key))
            for key in('live','aura','racial80_hex'):eq(cid,'preserve_'+key+str(j),initial[key],post[key])
            for key,value in row['initial']['growth'].items():
                if key!='rng_words':eq(cid,'growth_'+key+str(j),value,post['capture']['projection'].get(key))
            eq(cid,'complete72_player_keys'+str(j),row['initial']['growth']['player_fields'],post['capture']['projection']['player_fields'])
            position=0
            for p in diag['known_packets']:
                found=next((k for k in range(position,len(got['new_packets']))if got['new_packets'][k]==p),None);eq(cid,'packet'+str(j),True,found is not None)
                if found is not None:position=found+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(p[1])//2
            eq(cid,'no_pending_hit'+str(j),0,got['pending_after']['hits']['count']);eq(cid,'no_area'+str(j),0,got['pending_after']['areas']['count']);eq(cid,'empty_consumers_Game_conservation'+str(j),True,got['empty_consumers_Game2592_unchanged'])
            counts['full922']+=1;counts['successful_casts']+=want['success'];counts['damage_calls']+=len(diag['hits']);counts['deaths']+=sum(v['dead']for v in diag['hits']);counts['slow_write_operations']+=len(diag['effect_writes']);previous=post
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',differences)
    artifacts={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json','prepared.json','actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','expectation-read-audit.json','stderr.log','differences.json')if(out/n).exists()}
    report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],sources_before=sources,sources_after=sources,source_import_edges=edges,expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,artifacts=artifacts,frozen=frozen,runtime=runtime,process=terminal,counts=dict(counts),independent_world_receipt_sha256=WORLD_SHA,resource_context_snapshot_sha256=CONTEXT_SHA,resource_context_gate_sha256=GATE_SHA,fullworld_objects_retained=True,limitations=['Actualfullopening/XP5/newthunder with2owned/live1020 retained;controlledplayerplacement/clock,notinput/AI/main884.','No1775/3755enqueue inexec2;only their actualempty consumers tested.','Known/None nevercompleted;otherlive/skill/proc/effect49/slow376 owners pending.','OrdinaryNPCnonlethal/death/reward composed; full592/HP169/UI/heap streams incomplete.','Single-natural-target vicinity;multi-target area/order needs later dynamic validation.','Windows/native/network/save/completegame0.'])
    save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=counts['differences'],first=differences[:4],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
