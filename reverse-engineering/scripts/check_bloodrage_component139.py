#!/usr/bin/env python3
"""Expected-first actual natural2123/925/2890/952, not a complete884 frame."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,math,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_bloodrage_component139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import (projection,load_world139,WORLD,WORLD_SHA,
    CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA)
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.natural_bloodrage139 import prepare_natural_bloodrage139,advance_natural_bloodrage139,choose_natural_bloodrage_spawn_card139
from core_spec.spawn_schedule139_v4 import projection139 as spawn_projection139
from core_spec.player_update139 import word139
from core_spec.world_pause139 import update_world_pause139
from core_spec.incoming_history139 import projection as history_projection
from core_spec.frame_clock139 import FrameClock139,sample_frame_clock139,bits64,advance_game_clock139
from core_spec.death139 import guid139

import struct,hashlib


def closure():
    names=set(production_sources135(ROOT,'core_spec.natural_bloodrage139','core_spec.natural_run139','core_spec.natural_growth139','core_spec.natural_autocast139','core_spec.natural_damage139','core_spec.natural_collection139','core_spec.world_pause139','core_spec.frame_clock139',
        'core_spec.thunder_clap_world139','core_spec.enemy_ai139','core_spec.player_regeneration139',
        'core_spec.incoming139','resource_spec.world_query135'))
    names.update('scripts/'+n for n in('check_bloodrage_component139.py','run_bloodrage_component139_oracle.mjs',
        'build_bloodrage_component139_oracle.py','check_natural_bloodrage139.py','build_natural_bloodrage139_oracle.py','check_player_update139.py',
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
    from core_spec.bloodrage139 import resource_projection139
    return dict(bloodrage=resource_projection139(state.actor.damage.bloodrage),scheduler=scheduler,player=projection(state.actor.player),combat=combat_projection(state.actor),
        physical_NPC_storage=[list(r)for r in state.units.storage],physical_NPC_count=state.units.count,
        healing=heal_projection(state.actor.ledger),ai=ai_projection(state),gold1456=state.gold1456,earned1100=state.earned1100,
        xp_queue=dict(capacity=state.xp_queue.capacity,entries=state.xp_queue.entries),
        coin_queue=dict(capacity=state.coin_queue.capacity,entries=state.coin_queue.entries))


def corpus(world,phase):
    from check_natural_bloodrage139 import corpus as natural_corpus
    from core_spec.bloodrage139 import update_owned_effects983_139,attach_bloodrage_state139
    from core_spec.bloodrage_damage139 import resolve_bloodrage_damage139
    from core_spec.bloodrage_autocast139 import _adopt
    from core_spec.healing139 import DefaultHealingSources139
    from core_spec.enemy_ai_dead139_v2 import PhysicalNPCVector139
    from core_spec.death139 import position3_139
    rows=natural_corpus(world,'pilot')
    for row in rows:
        row['stages']=row['stages'][:107];row['diagnostics']=row['diagnostics'][:107];row['input']['timestamps64']=row['input']['timestamps64'][:107]
        s=prepare_natural_bloodrage139(111,world)
        for j in range(107):
            s=advance_natural_bloodrage139(s,f.add(s.run.actor.player.growth.now_bits,0x3dcccccd),0x3dcccccd,world,pause_world=update_world_pause139).state
            if s.run.actor.player.growth.phase2587==2:s,_=choose_natural_bloodrage_spawn_card139(s,0,world,resume_world=update_world_pause139)
        initial=s;ops=[];results=[];now=s.run.actor.player.growth.now_bits
        xyz=s.run.actor.player.player_xyz;far=(f.add(xyz[0],0x43fa0000),xyz[1],xyz[2])
        target=next(r for r in s.run.actor.damage.records432 if word139(r,0)==0 and f.to_float(word139(r,288))>80)
        guid=guid139(target)
        def perform(kind,dt=0,*,time_bits=None,player=None,target_guid=None):
            nonlocal s,now
            if time_bits is not None:now=time_bits
            elif kind=='tick983':now=f.add(now,dt)
            a=s.run.actor;p=replace(a.player,player_xyz=player or a.player.player_xyz,growth=replace(a.player.growth,now_bits=now))
            d=replace(attach_bloodrage_state139(a.damage,p),now_bits=now);a=replace(a,player=p,damage=d)
            inputs=dict(kind=kind,dt_bits=dt,now_bits=now,player_xyz=list(p.player_xyz))
            if kind=='tick983':
                value=update_owned_effects983_139(a,dt,world,healing_sources=DefaultHealingSources139(1,p.growth.source_counts));a=value.state;packets=value.packets;events=value.events
            else:
                inputs.update(target_guid=str(target_guid),amount_bits=0x3f800000,spell_id=0,school=0,critical=0,source_mode770=0,suppress_spell_damage_packet=1)
                value=resolve_bloodrage_damage139(d,target_guid,0x3f800000,world,spell_id=0,school=0,critical=0,inherited_context908=0,healing=a.ledger,healing_sources=DefaultHealingSources139(1,p.growth.source_counts),outgoing_owned80=None,suppress_spell_damage_packet=1)
                a=_adopt(a,value);packets=value.known_packets;events=(('controlled_basic_damage1',target_guid,value.dead),)
            units=PhysicalNPCVector139(tuple(a.damage.records432)+s.run.units.storage[s.run.units.count:],s.run.units.count)
            from core_spec.spawn_schedule139_v4 import from_combat139
            scheduler=from_combat139(s.opening,a,units,previous=s.scheduler,distance_map=s.run.distance_map)
            s=replace(s,run=replace(s.run,actor=a,units=units),scheduler=scheduler);ops.append(inputs);results.append(dict(final=stage_projection(s),known_packets=packets,events=events))
        for j in range(50):
            for k in range(6):perform('tick983',0x3dcccccd,player=far)
            perform('hit913',target_guid=guid)
            if j==10:
                last=s.run.actor.damage.bloodrage.last_hit876_bits
                perform('tick983',0,time_bits=f.add(last,0x40400000))
                perform('tick983',0x3dcccccd,time_bits=(f.add(last,0x40400000)+1))
                perform('tick983',0x3f800000)
                perform('tick983',0x3f800000)
        while f.to_float(s.run.actor.damage.bloodrage.rage868_bits)<100:
            if len(ops)>560:raise AssertionError('Bounded actual resource producer failed to reach100')
            for k in range(6):perform('tick983',0x3dcccccd,player=far)
            perform('hit913',target_guid=guid)
        assert f.to_float(s.run.actor.damage.bloodrage.rage868_bits)==100
        perform('tick983',0x3dcccccd,player=far)
        near=position3_139(next(r for r in s.run.actor.damage.records432 if guid139(r)==guid),now)
        perform('tick983',0,player=near)
        assert s.run.actor.damage.bloodrage.rage868_bits==0 and s.run.actor.damage.bloodrage.cooldown_registry
        perform('tick983',0)
        row['input']['operations']=ops;row['components']=results;row['component_initial']=stage_projection(initial)
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
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('bloodrage-component139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit_notOSaudit',opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,full_world_owners_retained=True,controlled_player_placement=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_bloodrage_component139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
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
        for key,value in want['bloodrage'].items():
            if value is not None:eq(cid,label+'.bloodrage.'+key,value,got['bloodrage'][key])
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
        return dict(bloodrage=got['bloodrage'],scheduler=got['scheduler'],player=got['after'],combat=got['combat'],healing=got['healing'],ai=got['ai'],gold1456=got['gold1456'],earned1100=got['earned1100'],xp_queue=got['xp_queue'],coin_queue=got['coin_queue'])
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
                eq(cid,'actual_three_cards',3,len(stage['before_choice']['player']['capture']['projection']['candidates']))
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
            if row['input']['selection_policy']=='first_two_default0_stop_third'and any(s['selection_index']is not None for s in got['stages'][:index]):
                counts['post_select_basic_success']+=sum(event[0]=='basic_success'for event in diag['player_events'])
                counts['post_select_demo_success']+=sum(event[0]=='owned'and event[2]=='demo_shout'and event[3]for event in diag['player_events'])
            previous=stage['after']
    for row,got in zip(rows,actual,strict=False):
        eq(row['id'],'component_count',len(row['components']),len(got['components']))
        for j,(want,stage)in enumerate(zip(row['components'],got['components'],strict=True)):
            stage_eq(row['id'],'component'+str(j),want['final'],stage['final'],got['initial']['aura']['flag2569'])
            cells(row['id'],'component_physicalNPC',want['final']['physical_NPC_storage'],stage['physical_NPC_storage'],432)
            for slot,(cells_row,oldhex,newhex)in enumerate(zip(want['final']['physical_NPC_storage'],stage['before_NPC_storage'],stage['physical_NPC_storage'],strict=True)):
                before=bytes.fromhex(oldhex);after=bytes.fromhex(newhex)
                for offset,value in enumerate(cells_row):
                    if value is None:eq(row['id'],f'component_None_copy[{slot}]+{offset}',before[offset],after[offset]);counts['component_None_physical_copy']+=1
            position=0
            for packet in want['known_packets']:
                found=next((k for k in range(position,len(stage['new_packets']))if stage['new_packets'][k]==packet),None)
                eq(row['id'],'component_ordered_packet'+str(j),True,found is not None)
                if found is not None:position=found+1;counts['component_known_packets']+=1;counts['component_known_packet_bytes']+=len(packet[1])//2
            counts['component_targets']+=1
    runtime=load_runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    expected_calls=Counter()
    for row in rows:
        expected_calls.update({'2945':1,'1600':1,'1108':1})
        for role in('2123','983','925','2890','952'):expected_calls[role]+=len(row['stages'])
        expected_calls['1093']+=sum(d['selection_index']is not None for d in row['diagnostics'])
        for op in row['input'].get('operations',[]):expected_calls['983'if op['kind']=='tick983'else'913']+=1
    if runtime is not None:
        for role,count in runtime['full_calls'].items():eq('runtime','full_calls.'+role,expected_calls[role],count)
        returned=Counter(str(x['role'])for x in runtime['target_and_setup_returns']if x['returned'])
        for role in set(expected_calls)|set(returned):eq('runtime','entry_return_count.'+role,expected_calls[role],returned[role])
        eq('runtime','allentry_returned_SP_restored',True,all(x['returned']and x['before']==x['after']==1048576 for x in runtime['target_and_setup_returns']))
        eq('runtime','host_calls',0,runtime['actual_host_calls'])
        eq('runtime','deny_imports',882,runtime['denied_imports'])
    else:eq('runtime','receipt_present',True,False)
    assert sources=={name:sha(ROOT/name)for name in files}and frozen=={name:sha(out/name)for name in frozen}
    save(out/'differences.json',differences)
    artifacts={name:sha(out/name)for name in('inputs.json','expected.json','config.json','manifest.json','prepared.json','actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','expectation-read-audit.json','stderr.log','differences.json')if(out/name).exists()}
    report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],
        sources_before=sources,sources_after=sources,source_import_edges=edges,expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,
        artifacts=artifacts,frozen=frozen,runtime=runtime,process=terminal,counts=dict(counts),
        source_seed_search='evidence/natural-demo139-model-prefix-20261102T162305.361584Z/result.json',
        limits=['NaturalXP only:initialsinglecleave/noXP,actual2123/983/925/2890 pickups andhurtactor levelheal/live/candidates/default0selection;noHP/RNG/card/CD/timer edits.',
        '884-compatible externalclock;otherlate884stages notexecuted;952executedfromfirstsliceafter2890withoutphase2skip. ControlledUIchoice atsameGameclock;notfullApp/mainframe/completegame.',
        'Same seed111 genuine first107 five-stage frames and2default selections are setup. Then explicit full983 clock/dt/player controls and full913 amount1/normalmode0 calls produce resources without HP/resource/RNG/owned edits; not natural auto attacks or fullframes.',
        'Knownmessageorderedsubset/fullnumeric/physicalNPC andpickup knownNone/incominghistory/sharedsemanticledger;full2077 physicalcontainers/wholeheap/UI/network/nativeWindows stillPending.',
        'WorldPause is a separatelysource-bound dependency. NoNPC/live clearing;originalworldmotions retained.'])
    save(out/'comparison.json',report)
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),completed=len(actual),differences=counts['differences'],first=differences[:4],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
