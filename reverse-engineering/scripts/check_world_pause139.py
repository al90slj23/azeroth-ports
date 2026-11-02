#!/usr/bin/env python3
"""Expected-first26364/35988/25613 over actual fresh moving opening owners."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_world_pause139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.world_pause139 import WorldMotionOwners139,gather_world_motion139,update_world_pause139
from core_spec.opening139 import DefaultOpeningInput139,initialize_default_opening139
from core_spec.opening_profile139 import EmptyAccountSources139
from core_spec.growth139 import from_constructor139
from core_spec.enemy_ai139 import EnemyAIState139,update_enemy_ai139
from core_spec.incoming139 import IncomingState139
from core_spec.incoming_history139 import IncomingHistory139


def closure():
    names=set(production_sources135(ROOT,'core_spec.world_pause139','core_spec.opening139','core_spec.enemy_ai139'))
    names.update('scripts/'+n for n in('check_world_pause139.py','build_world_pause139_oracle.py','run_world_pause139_oracle.mjs','check_player_update139.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as error:
            pair=error.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def moving_source(seed,world):
    opening=initialize_default_opening139(DefaultOpeningInput139(seed,EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
    growth=from_constructor139(opening.constructor,phase2587=1)
    records=tuple(tuple(row)for row in opening.units['answers'][-1]['records432_cells'])
    incoming=IncomingState139(1,0,0,0x3f800000,growth.current_hp_bits,growth.derived_bits[1536],growth.derived_bits[1568],growth.derived_bits[1572],items8=(),last_hit1652_bits=0xc1200000)
    ai=update_enemy_ai139(EnemyAIState139(records,0x3f800000,0x3dcccccd,opening.constructor.player_xyz,incoming,IncomingHistory139(0,0,0,(),(),()),tuple(growth.player_fields.items()),1),world,english_names={5830904:'Kobold Vermin'})
    assert not ai.attacks
    packets=tuple(opening.packets)+tuple(ai.packets);capacity=opening.packet_capacity
    for count in range(len(opening.packets),len(packets)):
        if count==capacity:capacity=max(4,capacity*2)
    return opening,ai,packets,capacity


def fixtures(family,xyz,count,*,start=1,duration=2,spare=1):
    stride,guid_off,origin,end,so,do=(112,16,32,44,56,60)if family=='auxiliary'else(88,24,44,56,68,72)
    rows=[]
    for j in range(count):
        row=bytearray([0x5a]*stride);struct.pack_into('<Q',row,guid_off,(0x0102030405060708 if j==0 else 0x1000000000000000+j)+(0x10000 if family=='companion'else 0))
        a=tuple(f.add(v,f.from_float(j*.125 if k<2 else 0))for k,v in enumerate(xyz))
        b=(f.add(a[0],f.from_float(1)),f.add(a[1],f.from_float(2)),f.add(a[2],f.from_float(3)))
        struct.pack_into('<3I',row,origin,*a);struct.pack_into('<3I',row,end,*b)
        struct.pack_into('<II',row,so,f.from_float(start),f.from_float(duration));rows.append(tuple(row))
    rows.extend([tuple([0xa5]*stride)]*spare)
    return tuple(rows)


def corpus(world,full):
    cases=[]
    layouts=[('real4moving',0,0,0,1,2),('three_family_order',0,1,1,1,2)]
    if full:layouts.extend([('seed11_endtime_boundaries',11,0,0,1,2),('seed69_before_motion_start',69,0,0,1,2),('merge_cap9_then18',0,5,9,1,2),('only_auxiliary_selected_cap5',11,5,0,100,2),('only_companions_selected_cap9',69,0,9,100,2),('expired_controlled_owners',0,3,3,-2,1)])
    for label,seed,na,nc,start,duration in layouts:
        opening,ai,prefix,packet_cap=moving_source(seed,world);xyz=opening.constructor.player_xyz
        aux=fixtures('auxiliary',xyz,na,start=start,duration=duration)if na else()
        comp=fixtures('companion',xyz,nc,start=start,duration=duration)if nc else()
        owners=WorldMotionOwners139(ai.state.records432,4,aux,na,comp,nc)
        now=f.from_float(100.25 if start==100 else .5 if 'before_motion'in label else 1.25)
        times=[now]
        if 'boundaries'in label:
            row=owners.units432_storage[0];u=lambda off:int.from_bytes(bytes(row[off:off+4]),'little')
            end=f.add(u(340),u(344));times=[end-1,end,end+1]
        if label=='real4moving'and full:times=[f.from_float(.5),now,f.from_float(100)]
        updates=[]
        for t in times:
            updates.extend([dict(action='gather',now_bits=t,phase=1),dict(action='pause',now_bits=t,phase=2),dict(action='resume',now_bits=t,phase=1)])
        # A repeated pair must not change the original motion records.
        if label=='three_family_order':updates.extend([dict(action='pause',now_bits=now,phase=2),dict(action='resume',now_bits=now,phase=1)]*3)
        stages=[];sequence=ai.state.movement_sequence2412;pc=len(prefix)
        for update in updates:
            gathered=gather_world_motion139(owners,update['now_bits']);packets=()
            if update['action']!='gather':
                result=update_world_pause139(owners,update['now_bits'],sequence,world,resume=update['action']=='resume');sequence=result.movement_sequence2412;packets=result.packets;assert result.owners==owners
            for _ in packets:
                if pc==packet_cap:packet_cap=max(4,2*packet_cap)
                pc+=1
            stages.append(dict(action=update['action'],sequence=sequence,packet_capacity=packet_cap,packet_count=pc,packets=[list(p)for p in packets],gathered=dict(capacity=gathered.capacity,count=gathered.count,storage=[list(row)for row in gathered.storage40])if update['action']=='gather'else None,gathered_families=[v.source_family for v in gathered.motions]))
        control=dict(id=len(cases),seed=seed,fixtures=dict(auxiliary=dict(count=na,storage=[bytes(row).hex()for row in aux]),companions=dict(count=nc,storage=[bytes(row).hex()for row in comp])),updates=updates)
        cases.append(dict(id=control['id'],label=label,input=control,source_units=[list(row)for row in ai.state.records432],source_sequence=ai.state.movement_sequence2412,prefix_packets=[list(p)for p in prefix],owners=dict(units=[list(row)for row in owners.units432_storage],auxiliary=[list(row)for row in aux],companions=[list(row)for row in comp]),stages=stages))
    return cases


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args()
    files,edges=closure();sources={name:sha(ROOT/name)for name in files}
    for path,digest in((SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA),(WORLD/'receipt.json',WORLD_SHA)):assert sha(path)==digest
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-pause139-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original forbidden during expectation')
    sys.addaudithook(audit)
    try:world,*_=load_world139(WORLD);rows=corpus(world,args.phase=='full')
    finally:model_phase=False
    assert not forbidden and sources=={name:sha(ROOT/name)for name in files}
    for name,digest in sources.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==digest
    save(out/'inputs.json',[row['input']for row in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden,layer='Pythonopenaudit'))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={name:sha(out/name)for name in('inputs.json','expected.json','config.json','manifest.json',manifest['module_file'],'expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_sha256=WORLD_SHA,resource_gate_sha256=GATE_SHA))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_world_pause139_oracle.mjs'),str(out),str(out/'config.json')];started=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-started,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(line)for line in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diff=[]
    def eq(cid,label,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(id=cid,field=label,expected=want,actual=got))
    def cells(cid,label,want,observed,stride):
        eq(cid,label+'.length',len(want),len(observed))
        for j,(row,hx)in enumerate(zip(want,observed)):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)==stride
            for k,value in enumerate(row):
                if value is None:counts['None_observed']+=1
                else:eq(cid,f'{label}[{j}]+{k}',value,raw[k]);counts['known_cells_compared']+=1
    for row,a in zip(rows,actual):
        cid=row['id'];eq(cid,'id',cid,a['id']);eq(cid,'source_sequence',row['source_sequence'],a['before']['sequence'])
        eq(cid,'complete_prefix_packets',row['prefix_packets'],[[p[0],p[2]]for p in a['before']['packets']])
        for name,width in(('units',432),('auxiliary',112),('companions',88)):cells(cid,'source_'+name,row['owners'][name],a['before']['owners'][name]['storage'],width)
        eq(cid,'stage_count',len(row['stages']),len(a['stages']));previous=a['before']
        for j,(control,want,got)in enumerate(zip(row['input']['updates'],row['stages'],a['stages'])):
            key='step'+str(j)+'.'
            for field in('action','sequence','packet_capacity','packet_count'):eq(cid,key+field,want[field],got[field])
            eq(cid,key+'complete_new_packets',want['packets'],got['new_packets'])
            eq(cid,key+'existing_packet_prefix',previous['packets'],got['packets'][:previous['packet_count']])
            if want['gathered']is not None:
                g=want['gathered'];eq(cid,key+'gather_capacity',g['capacity'],got['gathered']['capacity']);eq(cid,key+'gather_count',g['count'],got['gathered']['count']);cells(cid,key+'gather40',g['storage'],got['gathered']['storage'],40)
            else:eq(cid,key+'no_direct_gather_observation',None,got['gathered'])
            input_game=bytes.fromhex(got['input_game2592_hex']);anticipated=bytearray.fromhex(previous['raw_game2592_hex']);struct.pack_into('<I',anticipated,2352,control['now_bits']);anticipated[2587]=control['phase'];eq(cid,key+'only_declared_clock_phase_driver_patches',bytes(anticipated).hex(),input_game.hex())
            expected_game=bytearray(input_game);struct.pack_into('<I',expected_game,2412,want['sequence']);struct.pack_into('<I',expected_game,1880,want['packet_capacity']);struct.pack_into('<I',expected_game,1888,want['packet_count']);output=bytes.fromhex(got['raw_game2592_hex'])
            if previous['packet_capacity']!=want['packet_capacity']:expected_game[1884:1888]=output[1884:1888];counts['observed_reallocated_packet_pointer_words']+=1
            eq(cid,key+'all_Game2592_bytes',bytes(expected_game).hex(),output.hex());eq(cid,key+'all_actor_and_background_owners_unchanged',previous['owners'],got['owners']);eq(cid,key+'RNG_unchanged',previous['rng_words'],got['rng_words'])
            counts['formal_'+control['action']]+=1;counts['complete221_packets']+=len(want['packets']);counts['packet_payload_bytes']+=sum(len(p[2])//2 for p in want['packets']);counts['Game2592_bytes_compared']+=2592;counts['all_actor_backing_bytes_conserved']+=sum(v['capacity']*v['stride']for v in got['owners'].values());previous=got
        eq(cid,'stack',1048576,a['stack_after']);eq(cid,'profile_unchanged',a['profile_before'],a['profile_after']);eq(cid,'account_unchanged',a['account_before'],a['account_after'])
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    if runtime:
        eq('runtime','fresh_instances',len(rows),runtime['fresh_instances']);eq('runtime','host',0,runtime['actual_host_calls'])
        for action,idx in(('gather','26364'),('pause','35988'),('resume','25613')):eq('runtime',idx,counts['formal_'+action],runtime['calls'][idx])
        for returned in runtime['returns']:eq('runtime','intact_return_'+str(returned['role']),[1048576,True],[returned['after'],returned['returned']])
    assert sources=={name:sha(ROOT/name)for name in files}and frozen=={name:sha(out/name)for name in frozen};save(out/'differences.json',diff)
    artifacts={name:sha(out/name)for name in('prepared.json','actual.jsonl','runtime.json','stderr.log','owned-start.json','owned-terminal.json','differences.json')if(out/name).exists()}
    result=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,expectation_before_original=True,full_main884_frames=0,complete_games=0,limits=['Fresh2945/1600/1108/925prefixusesresource-onlyv2snapshot;independentexpectationusespreviousraw-producedcanonicalworld,notrawproductionrerun.', 'NPCactorsareactualfull925movingoutputs;auxiliary/companionfixturesareexplicitseparatecontrolledownerinputs.', 'Callerphase/clockpatchesexplicit;26364/35988/25613donotimplement2181/1093orcompletechoice.', 'Activefinitecoordinates/times/no-primaryworld;NaNprocessedmovementandprimaryfallbackremainunvalidated.', 'CompleteGame2592change-and-all-actorphysicalconservation,fullnew221payload/capacity;wholeheapallocationnotpredicted.', 'Directgather40tail4andspareallocatedcellsremainUnknown;cleanup73034iscountedseparatelyasnon-target.', 'Pilotnotcounted;noWindowsapplicationexecutionorcompletegame.'])
    save(out/'comparison.json',result);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=counts['differences'],first=diff[:3],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']or not runtime:raise SystemExit(1)


if __name__=='__main__':main()
