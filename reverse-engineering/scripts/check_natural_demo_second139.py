#!/usr/bin/env python3
"""Expected-first actual natural2123/925/2890/952, not a complete884 frame."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,math,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_natural_demo_second139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import (projection,load_world139,WORLD,WORLD_SHA,
    CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA)
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.natural_demo_v2_139 import prepare_natural_demo139,advance_natural_demo139,choose_natural_demo_spawn_card139
from core_spec.spawn_schedule139_v4 import projection139 as spawn_projection139
from core_spec.player_update139 import word139
from core_spec.world_pause139 import update_world_pause139
from core_spec.incoming_history139 import projection as history_projection
from core_spec.frame_clock139 import FrameClock139,sample_frame_clock139,bits64,advance_game_clock139
from core_spec.death139 import guid139

import struct,hashlib


def closure():
    names=set(production_sources135(ROOT,'core_spec.natural_demo_v2_139','core_spec.natural_run139','core_spec.natural_growth139','core_spec.natural_autocast139','core_spec.natural_damage139','core_spec.natural_collection139','core_spec.world_pause139','core_spec.frame_clock139',
        'core_spec.thunder_clap_world139','core_spec.enemy_ai139','core_spec.player_regeneration139',
        'core_spec.incoming139','resource_spec.world_query135'))
    names.update('scripts/'+n for n in('check_natural_demo_second139.py','run_natural_demo_second139_oracle.mjs',
        'build_natural_demo_second139_oracle.py','check_player_update139.py',
        'check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def heal_projection(ledger):
    return dict(event_counter960=str(ledger.event_counter960),accepted_count1016=str(ledger.accepted_count1016),reason_totals64={k:str(v)for k,v in ledger.reason_totals64})


def combat_projection(s):
    d=s.damage
    return dict(records432_cells=[list(r)for r in d.records432],rng_words=list(d.rng_words),
        accounted_total_bits=str(d.accounted_total_bits),spell_sets=[list(v)for v in s.player.spell_sets],
        player_xyz=list(s.player.player_xyz),phase2587=d.phase2587,
        spell_totals64=[[k,str(v)]for k,v in sorted(d.spell_totals64)],kills1084=d.kills1084,
        elites1088=d.elites1088,counter2408=d.counter2408,movement_sequence2412=d.movement_sequence2412,
        killcost2420_bits=d.killcost2420_bits,player_hp1440_bits=d.player_hp1440_bits,
        maximum1536_bits=d.maximum1536_bits,xp1436=s.player.growth.xp,
        pickup_capacity=d.pickups.capacity,pickup_count=d.pickups.count,
        pickups56_cells=[list(r)for r in d.pickups.storage])


def ai_projection(state):
    path=state.distance_map
    return dict(history=history_projection(state.history),
        path=None if path is None else dict(capacity=len(path.values_u16),count=len(path.values_u16),
            start_index=path.start_index,field24=path.field24,
            u16le_sha256=hashlib.sha256(struct.pack('<'+'H'*len(path.values_u16),*path.values_u16)).hexdigest()),
        path_clock2372_bits=state.distance_clock2372_bits,
        incoming992_hex=struct.pack('>d',state.incoming.incoming992).hex(),
        categories={k:struct.pack('>d',v).hex()for k,v in state.incoming.category1112},
        last_hit1652_bits=state.incoming.last_hit1652_bits)


def stage_projection(composition):
    state=composition.run
    scheduler={k:v for k,v in spawn_projection139(composition.scheduler).items()if k not in('windows','records432_cells','packets','pickups')}
    return dict(scheduler=scheduler,player=projection(state.actor.player),combat=combat_projection(state.actor),
        physical_NPC_storage=[list(r)for r in state.units.storage],physical_NPC_count=state.units.count,
        healing=heal_projection(state.actor.ledger),ai=ai_projection(state),gold1456=state.gold1456,earned1100=state.earned1100,
        xp_queue=dict(capacity=state.xp_queue.capacity,entries=state.xp_queue.entries),
        coin_queue=dict(capacity=state.coin_queue.capacity,entries=state.coin_queue.entries))


def corpus(world,phase):
    layouts=[('natural_demo_seed111_default0',111,107,'first_default0_stop_second')]
    rows=[]
    for group,seed,count,policy in layouts:
        state=prepare_natural_demo139(seed,world);initial=stage_projection(state)
        clock=FrameClock139(1,bits64(0.));stages=[];stamps=[];diags=[];choice_made=False
        for index in range(count):
            stamp=bits64((index+1)*.125);stamps.append(str(stamp));sample=sample_frame_clock139(clock,stamp);clock=sample.state
            now=advance_game_clock139(state.run.actor.player.growth.now_bits,sample.dt_bits,phase2587=1)
            composed=advance_natural_demo139(state,now,sample.dt_bits,world,pause_world=update_world_pause139);state=composed.state;value=composed.natural
            before_choice=None;selection=None;packets=composed.packets;heals=list(value.heal_events)
            if state.run.actor.player.growth.phase2587==2:
                before_choice=stage_projection(state)
                if policy=='first_default0_stop_second'and not choice_made:
                    if choice_made:raise AssertionError('Secondlevel is outside firstloop corpus')
                    cards=state.run.actor.player.growth.candidates
                    assert cards[0].variant=='new'and cards[0].ability_id=='demo_shout'
                    state,selection=choose_natural_demo_spawn_card139(state,0,world,resume_world=update_world_pause139)
                    assert selection.accepted;packets+=selection.packets;choice_made=True
            stages.append(dict(final=stage_projection(state),before_choice=before_choice))
            diags.append(dict(now_bits=now,dt_bits=sample.dt_bits,clock_tag=clock.tag_u64,clock_previous64=str(clock.previous_timestamp_bits),
                player_events=value.player_result.events,known_packets=packets,spawn_new=composed.spawn.new_NPCs,spawn_diagnostics=composed.spawn.diagnostics,
                heal_events=[dict(reason_id=e.reason_id,amount_bits=e.amount_bits,event_id=e.event_id)for e in heals],
                expired_spells=value.player_result.expired_spells,AI_attacks=value.ai_result.attacks,AI_motions=value.ai_result.motions,
                removed_guids=[str(g)for g in value.ai_result.removed_guids],path_recomputed=value.ai_result.path_recomputed,
                attractions=value.collection_result.attraction_events,consumption=value.collection_result.consumption_events,
                growth_events=[r.events for r in value.collection_result.growth_results],selection_index=0 if selection else None,
                selection_pickups=selection.consumed if selection else(),selection_raw_XP_sum=selection.raw_XP_sum if selection else 0,selection_scaled_XP_award=selection.scaled_XP_award if selection else 0,
                live_at_choice=[word139(r,20)for r in state.run.actor.player.live.active]if selection else()))
            if before_choice is not None and selection is None:break
        case=dict(id=len(rows),app_seed_u64=str(seed),selection_policy=policy,timestamps64=stamps,clock_initial=dict(tag=1,previous64=str(bits64(0.))))
        rows.append(dict(id=case['id'],group=group,input=case,initial=initial,stages=stages,diagnostics=diags))
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
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('natural-demo-second139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit_notOSaudit',opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,full_world_owners_retained=True,controlled_player_placement=False))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_natural_demo_second139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=120))
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(s)for s in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();differences=[]
    def eq(cid,label,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(differences)<100:differences.append(dict(id=cid,field=label,expected=want,actual=got))
    def cells(cid,label,want,got,width):
        eq(cid,label+'.physical_rows',len(want),len(got))
        for index,(row,hx)in enumerate(zip(want,got,strict=False)):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)==width
            for offset,(value,byte)in enumerate(zip(row,raw,strict=True)):
                if value is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(byte)
                else:eq(cid,f'{label}[{index}]+{offset}',value,byte);counts[label+'_known']+=1
    def player_eq(cid,label,want,got,initial_flag):
        for key,value in want['growth'].items():eq(cid,label+'.growth.'+key,value,got['capture']['projection'].get(key))
        for key in('racial80_hex','scalar','source_flags','spell_sets'):eq(cid,label+'.'+key,want[key],got[key])
        for key,width in(('live',32),('aura',16)):
            for name in('capacity','count'):eq(cid,label+'.'+key+'.'+name,want[key][name],got[key][name])
            cells(cid,key,want[key]['storage'],got[key]['storage'],width)
            if key=='aura':
                if want[key]['flag2569']is None:eq(cid,label+'.unwritten_AuraFlag_physically_conserved',initial_flag,got[key]['flag2569'])
                else:eq(cid,label+'.AuraFlag',want[key]['flag2569'],got[key]['flag2569'])
    def combat_eq(cid,label,want,got):
        for key,value in want.items():
            if key=='records432_cells':cells(cid,'activeNPC',value,got['records432_hex'][:len(value)],432)
            elif key=='pickups56_cells':cells(cid,'pickups',value,got['pickups56_hex'],56)
            else:eq(cid,label+'.'+key,value,got.get(key))
    def stage_eq(cid,label,want,got,initial_flag):
        for key,value in want['scheduler'].items():eq(cid,label+'.scheduler.'+key,value,got['scheduler'].get(key))
        player_eq(cid,label,want['player'],got['player'],initial_flag);combat_eq(cid,label,want['combat'],got['combat'])
        for key,value in want['healing'].items():eq(cid,label+'.healing.'+key,value,got['healing'][key])
        for key in('path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories'):eq(cid,label+'.AI.'+key,want['ai'][key],got['ai'][key])
        for key in('header','active'):eq(cid,label+'.history.'+key,want['ai']['history'][key],got['ai']['history'][key])
        cells(cid,'history',want['ai']['history']['storage'],got['ai']['history']['storage'],48)
        for key in('gold1456','earned1100'):eq(cid,label+'.'+key,want[key],got[key])
        for key in('xp_queue','coin_queue'):
            eq(cid,label+'.'+key+'.capacity',want[key]['capacity'],got[key]['capacity'])
            observed=[list(struct.unpack('<II',bytes.fromhex(hx)))for hx in got[key]['storage'][:got[key]['count']]]
            eq(cid,label+'.'+key+'.entries',want[key]['entries'],observed)
    def view_stage(got):
        return dict(scheduler=got['scheduler'],player=got['after'],combat=got['combat'],healing=got['healing'],ai=got['ai'],gold1456=got['gold1456'],earned1100=got['earned1100'],xp_queue=got['xp_queue'],coin_queue=got['coin_queue'])
    for row,got in zip(rows,actual,strict=False):
        cid=row['id'];eq(cid,'id',cid,got['id']);initial_flag=got['initial']['aura']['flag2569']
        player_eq(cid,'initial',row['initial']['player'],got['initial'],initial_flag)
        eq(cid,'natural_initial_level1_singleowned',1,len(got['initial']['capture']['projection']['owned_records80_hex']))
        eq(cid,'natural_initial_XP0',0,got['initial']['capture']['projection']['xp'])
        previous=got['initial']
        for index,(want,stage,diag)in enumerate(zip(row['stages'],got['stages'],row['diagnostics'],strict=True)):
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);inherited[2352:2356]=int(diag['now_bits']).to_bytes(4,'little')
            eq(cid,'sameGame_clock_only'+str(index),inherited.hex(),stage['before']['capture']['raw_game2592_hex']);counts['inherited_Game2592_bytes']+=2592
            eq(cid,'derived_clock'+str(index),dict(tag=diag['clock_tag'],previous64=diag['clock_previous64'],dt_bits=diag['dt_bits'],now_bits=diag['now_bits']),stage['clock'])
            stage_eq(cid,'step'+str(index),want['final'],view_stage(stage),initial_flag)
            units=stage['after']['capture']['background']['units'];eq(cid,'NPC_count'+str(index),want['final']['physical_NPC_count'],units['count'])
            cells(cid,'physicalNPC',want['final']['physical_NPC_storage'],units['storage'],432)
            old_by_guid={int.from_bytes(bytes.fromhex(hx)[112:120],'little'):bytes.fromhex(hx)for hx in stage['before_combat']['records432_hex']}
            for slot,(model,hx)in enumerate(zip(want['final']['physical_NPC_storage'],units['storage'],strict=True)):
                key=None if None in model[112:120]else guid139(tuple(model))
                if key in old_by_guid:old=old_by_guid[key]
                elif slot<stage['before_spawn']['capacity']:old=bytes.fromhex(stage['before_spawn']['storage'][slot])
                else:
                    counts['new_allocation_unknown_NPC_bytes']+=sum(v is None for v in model);continue
                new=bytes.fromhex(hx)
                for offset,value in enumerate(model):
                    if value is None:eq(cid,f'NPC_unknown_copy[{slot}]+{offset}',old[offset],new[offset]);counts['NPC_unknown_physical_copy']+=1
            if want['before_choice']is None:eq(cid,'choice_not_inserted'+str(index),None,stage['before_choice'])
            else:
                eq(cid,'actual_first3cards',3,len(stage['before_choice']['player']['capture']['projection']['candidates']))
                stage_eq(cid,'before_choice'+str(index),want['before_choice'],stage['before_choice'],initial_flag)
                counts['actual_phase2_choices']+=1
            eq(cid,'actual_selection_index'+str(index),diag['selection_index'],stage['selection_index'])
            if diag['selection_index']is not None:counts['actual_default0_selections']+=1
            names={'regen':('Regeneration','Spell_Nature_Rejuvenation'),'leech':('Leech','Spell_Shadow_LifeDrain02'),'level_up':('Level Up','Spell_Holy_HolyBolt')}
            breakdown=[dict(name=names[key][0],icon=names[key][1],total64=value,owns=0,nested_count=0)for key,value in want['final']['healing']['reason_totals64'].items()if key in names]
            eq(cid,'heal_breakdown'+str(index),breakdown,[{key:r[key]for key in('name','icon','total64','owns','nested_count')}for r in stage['healing']['breakdown']])
            position=0
            for packet in diag['known_packets']:
                found=next((k for k in range(position,len(stage['new_packets']))if stage['new_packets'][k]==packet),None)
                eq(cid,'ordered_packet'+str(index),True,found is not None)
                if found is not None:position=found+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2
            counts['selection_pickups']+=len(diag['selection_pickups']);counts['selection_raw_XP_sum']+=diag['selection_raw_XP_sum'];counts['selection_scaled_XP_award']+=diag['selection_scaled_XP_award'];counts['spawn_NPCs']+=len(diag['spawn_new']);counts['positive_spawn_cost_steps']+=bool(diag['spawn_diagnostics']and diag['spawn_diagnostics'][0]['old_bits']);counts['natural_steps']+=1;counts['AI_attacks']+=len(diag['AI_attacks']);counts['removals']+=len(diag['removed_guids']);counts['collections']+=len(diag['consumption']);counts['attractions']+=len(diag['attractions'])
            counts['XP_awarded']+=sum(event[4]for event in diag['consumption']if event[1]==0)
            for event in diag['heal_events']:counts[event['reason_id']+'_positive_events']+=1
            counts['level_transitions']+=sum(event['kind']=='level_up'for events in diag['growth_events']for event in events)
            if row['input']['selection_policy']=='first_default0_stop_second'and any(s['selection_index']is not None for s in got['stages'][:index]):
                counts['post_select_basic_success']+=sum(event[0]=='basic_success'for event in diag['player_events'])
                counts['post_select_demo_success']+=sum(event[0]=='owned'and event[2]=='demo_shout'and event[3]for event in diag['player_events'])
            previous=stage['after']
    runtime=load_runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert sources=={name:sha(ROOT/name)for name in files}and frozen=={name:sha(out/name)for name in frozen}
    save(out/'differences.json',differences)
    artifacts={name:sha(out/name)for name in('inputs.json','expected.json','config.json','manifest.json','prepared.json','actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','expectation-read-audit.json','stderr.log','differences.json')if(out/name).exists()}
    report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],
        sources_before=sources,sources_after=sources,source_import_edges=edges,expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,
        artifacts=artifacts,frozen=frozen,runtime=runtime,process=terminal,counts=dict(counts),
        source_seed_search='evidence/natural-demo139-model-prefix-20261102T162305.361584Z/result.json',
        limits=['NaturalXP only:initialsinglecleave/noXP,actual2123/925/2890 pickups andhurtactor levelheal/live/candidates/default0selection;noHP/RNG/card/CD/timer edits.',
        '884-compatible externalclock;otherlate884stages notexecuted;952executedfromfirstsliceafter2890withoutphase2skip. ControlledUIchoice atsameGameclock;notfullApp/mainframe/completegame.',
        'Same seed111 natural Demo2 then second2181 candidate offer atindex106; secondUIchoice remainsunsupported andisnotselected. No otherseed/redraw.',
        'Knownmessageorderedsubset/fullnumeric/physicalNPC andpickup knownNone/incominghistory/sharedsemanticledger;full2077 physicalcontainers/wholeheap/UI/network/nativeWindows stillPending.',
        'WorldPause is a separatelysource-bound dependency. NoNPC/live clearing;originalworldmotions retained.'])
    save(out/'comparison.json',report)
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),completed=len(actual),differences=counts['differences'],first=differences[:4],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
