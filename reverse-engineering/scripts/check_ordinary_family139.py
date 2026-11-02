#!/usr/bin/env python3
"""Expected-first genuine952 family production→925/913/corpse components."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import replace
from collections import Counter
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_ordinary_family139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import projection,load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA
from check_natural_run139 import stage_projection,combat_projection,ai_projection,heal_projection
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.natural_run139 import prepare_natural_run139,_incoming,_adopt_player
from core_spec.spawn_schedule139_v4 import from_combat139,update_spawn_schedule139,thread_spawn_result139,projection139 as spawn_projection
from core_spec.enemy_family_ai139 import update_enemy_family139,EnemyAIState139,PhysicalNPCVector139
from core_spec.ordinary_family139_data import ORDINARY_DEFINITIONS139
from core_spec.ordinary_family_damage139 import resolve_family_damage139
from core_spec.death139 import word139,guid139,position3_139
from core_spec.healing139 import DefaultHealingSources139


def closure():
    names=set(production_sources135(ROOT,'core_spec.enemy_family_ai139','core_spec.ordinary_family_damage139','core_spec.natural_run139','core_spec.spawn_schedule139_v4'))
    names.update('scripts/'+n for n in('check_ordinary_family139.py','build_ordinary_family139_oracle.py','run_ordinary_family139_oracle.mjs','trace_ordinary_family139.py','check_natural_run139.py','check_player_update139.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def adopt_ai(state,result):
    a=state.actor;p=a.player;g=replace(p.growth,now_bits=result.ai.now_bits,units432_cells=result.units.active,current_hp_bits=result.ai.incoming.hp1440_bits,player_fields=dict(result.ai.player_fields))
    p=replace(p,growth=g,last_hit1652_bits=result.ai.incoming.last_hit1652_bits)
    actor=_adopt_player(a,p,result.units,sequence=result.ai.movement_sequence2412)
    return replace(state,actor=actor,units=result.units,incoming=result.ai.incoming,history=result.ai.history,distance_map=result.ai.distance_map,distance_clock2372_bits=result.ai.distance_clock2372_bits)


def run_ai(state,now,dt,world,*,follow_guid=None):
    xyz=state.actor.player.player_xyz
    if follow_guid is not None:
        row=next(r for r in state.units.active if guid139(r)==follow_guid);xyz=position3_139(row,now)
    p=replace(state.actor.player,player_xyz=xyz,growth=replace(state.actor.player.growth,now_bits=now))
    actor=_adopt_player(state.actor,p,state.units)
    state=replace(state,actor=actor,incoming=_incoming(state.incoming,p,state.units))
    before=stage_projection(state)
    result=update_enemy_family139(EnemyAIState139(state.units.active,now,dt,xyz,state.incoming,state.history,tuple(p.growth.player_fields.items()),actor.damage.movement_sequence2412,state.distance_map,state.distance_clock2372_bits),state.units,world)
    return adopt_ai(state,result),result,before,xyz


def corpus(world,phase):
    rows=[]
    for seed,spell,critical in([(0,0,0)]if phase=='pilot'else[(0,0,0),(1,845,1),(5,845,0),(8,0,1)]):
        opening,state=prepare_natural_run139(seed,world);initial=stage_projection(state);spawn_now=f.from_float(30.1);dt=f.from_float(.1)
        source=from_combat139(opening,state.actor,state.units);spawn=update_spawn_schedule139(source,spawn_now,dt,world)
        actor=thread_spawn_result139(state.actor,spawn);units=PhysicalNPCVector139(spawn.state.records432,spawn.state.count)
        state=replace(state,actor=actor,units=units,incoming=_incoming(state.incoming,actor.player,units))
        after_spawn=stage_projection(state);wolves=[guid139(r)for r in units.active if word139(r,284)==5830976]
        target=wolves[0]if wolves else guid139(units.active[0]);target_def=word139(next(r for r in units.active if guid139(r)==target),284)
        inputs=[];frames=[];now=spawn_now
        for _ in range(8):
            now=f.add(now,f.from_float(.5));state,result,before,xyz=run_ai(state,now,f.from_float(.5),world,follow_guid=target)
            control=dict(now_bits=now,dt_bits=f.from_float(.5),follow_guid=str(target),player_xyz=xyz)
            inputs.append(control);frames.append(dict(before=before,after=stage_projection(state),packets=result.packets,attacks=result.attacks,motions=result.motions,removed_guids=[str(g)for g in result.removed_guids]))
        hits=[];hit_inputs=[]
        for label,amount in(('nonlethal',f.from_float(1)),('lethal',f.from_float(250)),('already_dead',f.from_float(1))):
            actor=state.actor;before=stage_projection(state)
            result=resolve_family_damage139(actor.damage,target,amount,world,spell_id=spell,school=0,critical=critical,inherited_context908=0,healing=actor.ledger,healing_sources=DefaultHealingSources139(1,(0,)*7),outgoing_owned80=actor.player.growth.owned_records80[0]if spell else None,suppress_spell_damage_packet=0 if spell else 1)
            units=PhysicalNPCVector139(result.state.records432+state.units.storage[state.units.count:],state.units.count)
            fields=dict(actor.player.growth.player_fields);fields.update(result.player_key_writes)
            p=replace(actor.player,growth=replace(actor.player.growth,player_fields=fields,rng_words=result.state.rng_words,units432_cells=units.active,current_hp_bits=result.state.player_hp1440_bits))
            actor=replace(actor,player=p,damage=result.state,ledger=result.healing)
            state=replace(state,actor=actor,units=units,incoming=_incoming(state.incoming,p,units))
            hit_inputs.append(dict(label=label,now_bits=now,target_guid=str(target),amount_bits=amount,spell_id=spell,school=0,critical=critical,suppress_flag=0 if spell else 1))
            hits.append(dict(before=before,after=stage_projection(state),packets=result.known_packets,accepted=result.applied,killed=result.dead,heal_events=[dict(reason=e.reason_id,amount_bits=e.amount_bits,event_id=e.event_id)for e in result.heal_events],reward_events=result.reward_events))
        cleanup=[];cleanup_inputs=[];death=now
        for delta,step in((1.,1.),(1.25,.25)):
            stamp=f.add(death,f.from_float(delta));state,result,before,xyz=run_ai(state,stamp,f.from_float(step),world)
            cleanup_inputs.append(dict(now_bits=stamp,dt_bits=f.from_float(step),player_xyz=xyz))
            cleanup.append(dict(before=before,after=stage_projection(state),packets=result.packets,attacks=result.attacks,motions=result.motions,removed_guids=[str(g)for g in result.removed_guids],lifetime_proofs=result.lifetime_proofs))
        case=dict(id=len(rows),app_seed_u64=str(seed),spawn=dict(now_bits=spawn_now,dt_bits=dt),frames=inputs,hits=hit_inputs,cleanup=cleanup_inputs)
        rows.append(dict(id=case['id'],input=case,initial=initial,after_spawn=after_spawn,spawn={k:v for k,v in spawn_projection(spawn.state).items()if k not in('windows','records432_cells','packets','pickups')},spawn_packets=spawn.packets,wolf_count=len(wolves),target_definition=target_def,frames=frames,hits=hits,cleanup=cleanup))
    return json.loads(json.dumps(rows))


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original input denied in expected model')
    sys.addaudithook(audit)
    try:world,*_=load_world139(WORLD);rows=corpus(world,args.phase)
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('ordinary-family139-'+args.phase+'-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    assert[(d.pointer,d.raw72.hex(),d.english_name)for d in ORDINARY_DEFINITIONS139]==[(d['pointer'],d['raw72_hex'],d['english_name'])for d in m['ordinary_family_trace']['definitions']]
    for p,h in((SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA),(WORLD/'receipt.json',WORLD_SHA)):assert sha(p)==h
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','manifest.json',m['module_file'],'config.json','expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False))
    argv=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_ordinary_family139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(argv,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=argv,deadline_seconds=120))
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(line)for line in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();differences=[]
    def eq(cid,label,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(differences)<100:differences.append(dict(id=cid,field=label,expected=want,actual=got))
    def cells(cid,label,rows,hxs):
        eq(cid,label+'.rows',len(rows),len(hxs))
        for row,hx in zip(rows,hxs):
            raw=bytes.fromhex(hx);eq(cid,label+'.width',len(row),len(raw))
            for o,(v,b)in enumerate(zip(row,raw)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
                else:eq(cid,label+'+'+str(o),v,b);counts[label+'_known']+=1
    def view(cid,label,want,got,initial_flag):
        p=got['player'];w=want['player'];eq(cid,label+'.growth',w['growth'],p['capture']['projection'])
        for key in('racial80_hex','scalar','source_flags','spell_sets'):eq(cid,label+'.'+key,w[key],p[key])
        for key in('live','aura'):
            for attr in('capacity','count'):eq(cid,label+'.'+key+'.'+attr,w[key][attr],p[key][attr])
            cells(cid,key,w[key]['storage'],p[key]['storage'])
            if key=='aura':eq(cid,label+'.AuraFlag',initial_flag if w[key]['flag2569']is None else w[key]['flag2569'],p[key]['flag2569'])
        for key,value in want['combat'].items():
            if key=='records432_cells':cells(cid,'NPCactive',value,got['combat']['records432_hex'][:len(value)])
            elif key=='pickups56_cells':cells(cid,'pickups',value,got['combat']['pickups56_hex'])
            else:eq(cid,label+'.combat.'+key,value,got['combat'][key])
        eq(cid,label+'.NPC_count',want['physical_NPC_count'],p['capture']['background']['units']['count']);cells(cid,'NPCphysical',want['physical_NPC_storage'],p['capture']['background']['units']['storage'])
        for key,value in want['healing'].items():eq(cid,label+'.ledger.'+key,value,got['healing'][key])
        for key in('path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories'):eq(cid,label+'.AI.'+key,want['ai'][key],got['ai'][key])
        for key in('header','active'):eq(cid,label+'.history.'+key,want['ai']['history'][key],got['ai']['history'][key])
        cells(cid,'history',want['ai']['history']['storage'],got['ai']['history']['storage'])
        for key in('gold1456','earned1100'):eq(cid,label+'.'+key,want[key],got[key])
        for key in('xp_queue','coin_queue'):eq(cid,label+'.'+key+'.capacity',want[key]['capacity'],got[key]['capacity']);eq(cid,label+'.'+key+'.count',len(want[key]['entries']),got[key]['count'])
    def packets(cid,label,want,got,complete):
        if complete:eq(cid,label+'.full_packets',want,got)
        else:
            pos=0
            for p in want:
                at=next((i for i in range(pos,len(got))if got[i]==p),None);eq(cid,label+'.ordered_packet',True,at is not None)
                if at is not None:pos=at+1
        counts['known_packets']+=len(want);counts['known_packet_bytes']+=sum(len(p[1])//2 for p in want)
    for E,A in zip(rows,actual):
        cid=E['id'];flag=A['initial']['player']['aura']['flag2569'];eq(cid,'id',cid,A['id']);view(cid,'initial',E['initial'],A['initial'],flag);view(cid,'spawn',E['after_spawn'],A['after_spawn'],flag)
        for k,v in A['spawn'].items():eq(cid,'spawn.'+k,E['spawn'][k],v)
        eq(cid,'spawn_preserves_all_four_original_NPC_records',A['initial']['player']['capture']['background']['units']['storage'],A['after_spawn']['player']['capture']['background']['units']['storage'][:4]);counts['spawn_preserved_original_NPC_bytes']+=1728
        packets(cid,'spawn',E['spawn_packets'],A['spawn_packets'],True);eq(cid,'wolf_count',E['wolf_count'],A['wolf_count']);eq(cid,'target_definition',E['target_definition'],A['target_definition'])
        previous=A['after_spawn']
        for group in('frames','hits','cleanup'):
            eq(cid,group+'.count',len(E[group]),len(A[group]))
            for index,(wanted,got)in enumerate(zip(E[group],A[group])):
                label=group+str(index);view(cid,label+'.before',wanted['before'],got['before'],flag);view(cid,label+'.after',wanted['after'],got['after'],flag)
                control=E['input'][group][index];inherited=bytearray.fromhex(previous['player']['capture']['raw_game2592_hex']);struct.pack_into('<I',inherited,2352,control['now_bits'])
                if 'player_xyz'in control:struct.pack_into('<3I',inherited,1416,*control['player_xyz'])
                eq(cid,label+'.only_clock_and_player_control',inherited.hex(),got['before']['player']['capture']['raw_game2592_hex']);counts['inherited_Game_bytes']+=2592
                oldphysical=got['before']['player']['capture']['background']['units']['storage'];newphysical=got['after']['player']['capture']['background']['units']['storage']
                byguid={int.from_bytes(bytes.fromhex(hx)[112:120],'little'):bytes.fromhex(hx)for hx in oldphysical}
                for slot,(model,hx)in enumerate(zip(wanted['after']['physical_NPC_storage'],newphysical)):
                    key=None if None in model[112:120]else guid139(tuple(model))
                    prior=byguid.get(key,bytes.fromhex(oldphysical[slot]));observed=bytes.fromhex(hx)
                    for at,v in enumerate(model):
                        if v is None:eq(cid,label+'.unknown_NPC_copy'+str(slot)+'+'+str(at),prior[at],observed[at]);counts['NPC_unknown_physical_copy']+=1
                packets(cid,label,wanted['packets'],got['new_packets'],group!='hits')
                if group=='hits':
                    counts['full913']+=1;counts['positive_Leech']+=len(wanted['heal_events']);counts['deaths']+=wanted['killed'];counts['accepted_hits']+=wanted['accepted']
                    if control['label']=='already_dead':eq(cid,'already_dead_no_Game_mutation',got['before']['player']['capture']['raw_game2592_hex'],got['after']['player']['capture']['raw_game2592_hex']);eq(cid,'already_dead_no_NPC_mutation',got['before']['player']['capture']['background']['units'],got['after']['player']['capture']['background']['units']);eq(cid,'already_dead_no_packets',[],got['new_packets'])
                else:counts['full925']+=1;counts['AI_attacks']+=len(wanted['attacks']);counts['removed_corpses']+=len(wanted['removed_guids'])
                previous=got['after']
        counts['cases']+=1;counts['Wolf_cases']+=E['wolf_count']>0;counts['no_Wolf_controls']+=E['wolf_count']==0
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    if runtime:assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}
    save(out/'differences.json',differences);report=dict(phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,fullmain_frames=0,complete_games=0,limits=['Controlledclock jump to30.1s and player follows actualNPC; not natural30seconds, mainframe, renderer or native Windows.','Only Kobold/Wolf ordinary branches and basic0/ownedcleave845 direct913 are covered; Thunder/Demo contexts not dynamically accepted.','Full925 packets and known ordered subset of913, semanticledger plus field/physical knownNone; wholeheap/full2077/UI remains Pending.'])
    save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),counts=dict(counts),differences=counts['differences'],first=differences[:3],process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
