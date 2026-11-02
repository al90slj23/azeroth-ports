#!/usr/bin/env python3
"""Expected-first defaultWarrior full1238/2123 success components, not884."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,math,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_player_enemy139_v2_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import (projection,load_world139,WORLD,WORLD_SHA,
    CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA)
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.player_autocast139 import (PlayerAutocastState139,
    tick_default_autocast139,update_player_autocast139)
from core_spec.player_regeneration139 import update_player_regeneration139
from core_spec.healing139 import HealingLedger139
from core_spec.default_damage139 import DefaultOutgoingLedger139
from core_spec.player_effects139 import sync_aura139,cast_perception139
from core_spec.incoming139 import IncomingState139,Buff139,resolve_prefix139
from core_spec.incoming_history139 import IncomingHistory139
from core_spec.enemy_ai139 import EnemyAIState139,update_enemy_ai139,position_xyz139
from core_spec.death139 import (guid139,OrdinaryDamageState139,DefaultDeathSources139,word139)
from core_spec.death_pickups139 import PickupVector139
from core_spec.hit_events139 import produce_default_cleave_hit_sources139,prove_owned_execution11_absent139
from core_spec.candidates139_data import DEFINITIONS139
from core_spec.thunder_clap_world139 import prepare_thunder_world139
from check_healing139_v3 import heal_projection
from core_spec.player_enemy139_v2 import PlayerEnemyState139,NPCVector139,update_player_enemy139
from core_spec.frame_clock139 import FrameClock139,sample_frame_clock139,bits64,advance_game_clock139
from core_spec.incoming_history139 import projection as history_projection
import struct,hashlib


def closure():
    names=set(production_sources135(ROOT,'core_spec.player_enemy139_v2','core_spec.frame_clock139','core_spec.player_autocast139','core_spec.default_damage139',
        'core_spec.thunder_clap_world139','core_spec.enemy_ai139','core_spec.player_regeneration139',
        'core_spec.incoming139','resource_spec.world_query135'))
    names.update('scripts/'+n for n in('check_player_enemy139_v2.py','run_player_enemy139_v2_oracle.mjs',
        'build_player_enemy139_v2_oracle.py','check_healing139_v3.py','check_player_update139.py',
        'check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def incoming_owner(p):
    g=p.growth
    live=tuple(Buff139(word139(r,8),None if word139(r,8)==12 else word139(r,12),
        word139(r,20),word139(r,24))for r in p.live.active)
    return IncomingState139(1,0,0,g.now_bits,g.current_hp_bits,g.derived_bits[1536],
        g.derived_bits[1568],g.derived_bits[1572],last_hit1652_bits=p.last_hit1652_bits,
        player_xy=p.player_xyz[:2],records432=g.units432_cells,live32=live,items8=())


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


def corpus(world,phase):
    layouts=[('natural_center_seed11',11,None,72 if phase=='pilot'else 160)]
    if phase=='full':layouts.extend([
        ('controlled_player_near_actualNPC_seed11',11,0,100),
        ('natural_center_tier4_seed69',69,None,100)])
    declarations=tuple((DEFINITIONS139[k][0],bytes.fromhex(DEFINITIONS139[k][1]))for k in('cleave','thunder_clap'))
    rows=[]
    for group,seed,placement,count in layouts:
        opening,gain,selected,p=prepare_thunder_world139(seed,world);initial=projection(p)
        action=None
        if placement is not None:
            xyz=position_xyz139(p.growth.units432_cells[placement],0)
            height=world.height(*xyz[:2]);assert height.found
            p=replace(p,player_xyz=(*xyz[:2],height.value_bits))
            action=dict(anchor_index=placement,height_bits=height.value_bits)
        profile=[None]*376
        for o in(160,*range(260,336,4)):profile[o:o+4]=bytes(4)
        profile[344]=profile[345]=1
        hit=produce_default_cleave_hit_sources139(tuple(profile),(p.growth.owned_records80[0],),p.growth.racial_record80)
        hit=replace(hit,owned_execution_scan=prove_owned_execution11_absent139(p.growth.owned_records80,declarations))
        d=OrdinaryDamageState139(p.growth.units432_cells,p.growth.rng_words,0,1,0,(),0,0,opening.counter,1,0,
            p.growth.current_hp_bits,p.growth.derived_bits[1536],
            PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),DefaultDeathSources139(hit,(),(),(),(),()))
        actor=PlayerAutocastState139(p,d,DefaultOutgoingLedger139(0,0,()),0,0)
        state=PlayerEnemyState139(actor,NPCVector139(d.records432,len(d.records432)),incoming_owner(p),
            IncomingHistory139(0,0,0,(),(),()),None,0)
        clock=FrameClock139(1,bits64(0.));stages=[];timestamps=[];diags=[]
        for index in range(count):
            stamp=bits64((index+1)*.125);timestamps.append(str(stamp))
            sampled=sample_frame_clock139(clock,stamp);clock=sampled.state
            now=advance_game_clock139(state.actor.player.growth.now_bits,sampled.dt_bits,phase2587=1)
            result=update_player_enemy139(state,now,sampled.dt_bits,world);state=result.state
            stages.append(dict(player=projection(state.actor.player),combat=combat_projection(state.actor),
                after_player=dict(player=projection(result.player_result.state.player),combat=combat_projection(result.player_result.state)),
                physical_NPC_storage=[list(r)for r in state.units.storage],physical_NPC_count=state.units.count,
                healing=heal_projection(state.actor.ledger),ai=ai_projection(state)))
            diags.append(dict(now_bits=now,dt_bits=sampled.dt_bits,
                clock_tag=clock.tag_u64,clock_previous64=str(clock.previous_timestamp_bits),
                events=result.player_result.events,known_packets=result.packets,
                heal_events=[dict(reason_id=e.reason_id,amount_bits=e.amount_bits,event_id=e.event_id)for e in result.player_result.heal_events],
                expired_spells=result.player_result.expired_spells,AI_attacks=result.ai_result.attacks,
                AI_motions=result.ai_result.motions,removed_guids=[str(g)for g in result.removed_guids],
                path_recomputed=result.ai_result.path_recomputed))
        case=dict(id=len(rows),app_seed_u64=str(seed),amount=5,dead_mask=0,select_index=0,
            placement=action,timestamps64=timestamps,clock_initial=dict(tag=1,previous64=str(bits64(0.))))
        rows.append(dict(id=case['id'],group=group,input=case,initial=initial,player_xyz=list(p.player_xyz),
            actual_card_tier=gain.state.candidates[0].tier,stages=stages,diagnostics=diags))
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
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('player-enemy139-v2-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit_notOSaudit',opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,full_world_owners_retained=True,controlled_player_placement=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_player_enemy139_v2_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
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
    def player_eq(cid,label,want,got):
        for key,value in want['growth'].items():eq(cid,label+'.growth.'+key,value,got['capture']['projection'].get(key))
        for key in('racial80_hex','scalar','source_flags','spell_sets'):eq(cid,label+'.'+key,want[key],got[key])
        for key,width in(('live',32),('aura',16)):
            for field in('capacity','count')+(('flag2569',)if key=='aura'else()):eq(cid,label+'.'+key+'.'+field,want[key][field],got[key][field])
            cells(cid,label+'_'+key,want[key]['storage'],got[key]['storage'],width)
    def combat_eq(cid,label,want,got):
        for key,value in want.items():
            if key=='records432_cells':cells(cid,label+'_active_NPC',value,got['records432_hex'][:len(value)],432)
            elif key=='pickups56_cells':cells(cid,label+'_pickup',value,got['pickups56_hex'],56)
            else:eq(cid,label+'.'+key,value,got.get(key))
    def packets_eq(cid,label,want,got):
        position=0
        for p in want:
            found=next((k for k in range(position,len(got))if got[k]==p),None)
            eq(cid,label,True,found is not None)
            if found is not None:position=found+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(p[1])//2
    for row,a in zip(rows,actual,strict=False):
        cid=row['id'];eq(cid,'id',cid,a['id']);player_eq(cid,'initial',row['initial'],a['player_before'])
        controlled=bytearray.fromhex(a['before_control']['capture']['raw_game2592_hex'])
        for k,v in enumerate(row['player_xyz']):controlled[1416+4*k:1420+4*k]=int(v).to_bytes(4,'little')
        eq(cid,'controlled_playerXYZ_only_Game_write',controlled.hex(),a['controlled_before']['capture']['raw_game2592_hex'])
        previous=a['controlled_before'];previous_path=None
        for j,(want,got,diag)in enumerate(zip(row['stages'],a['stages'],row['diagnostics'],strict=True)):
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);inherited[2352:2356]=int(diag['now_bits']).to_bytes(4,'little')
            eq(cid,'sameGame_clock_only'+str(j),inherited.hex(),got['before']['capture']['raw_game2592_hex']);counts['inherited_Game2592_bytes']+=2592
            eq(cid,'clock'+str(j),dict(tag=diag['clock_tag'],previous64=diag['clock_previous64'],dt_bits=diag['dt_bits'],now_bits=diag['now_bits']),got['clock'])
            player_eq(cid,'after2123_'+str(j),want['after_player']['player'],got['after_player'])
            combat_eq(cid,'after2123_'+str(j),want['after_player']['combat'],got['after_player_combat'])
            player_eq(cid,'after925_'+str(j),want['player'],got['after']);combat_eq(cid,'after925_'+str(j),want['combat'],got['combat'])
            units=got['after']['capture']['background']['units'];eq(cid,'NPCcapacity'+str(j),len(want['physical_NPC_storage']),units['capacity']);eq(cid,'NPCcount'+str(j),want['physical_NPC_count'],units['count'])
            cells(cid,'NPC_fullphysical',want['physical_NPC_storage'],units['storage'],432)
            # Every unwritten byte follows the real full432 copy source. This
            # also verifies stale tail after40215; no None is completed with0.
            before_by_guid={int.from_bytes(bytes.fromhex(hx)[112:120],'little'):bytes.fromhex(hx)for hx in got['before_combat']['records432_hex']}
            for index,(model,hx)in enumerate(zip(want['physical_NPC_storage'],units['storage'],strict=True)):
                target=guid139(tuple(model));raw=bytes.fromhex(hx);source=before_by_guid[target]
                for k,v in enumerate(model):
                    if v is None:eq(cid,f'physicalNPC_copyunknown[{index}]+{k}',source[k],raw[k]);counts['NPC_unknown_copy_or_retained']+=1
            for key,value in want['healing'].items():eq(cid,'healing'+str(j)+'.'+key,value,got['healing'][key])
            for key in('path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories'):eq(cid,'AI_'+key+str(j),want['ai'][key],got['ai'][key])
            history=want['ai']['history'];actual_history=got['ai']['history']
            eq(cid,'incoming_history_header'+str(j),history['header'],actual_history['header']);eq(cid,'incoming_history_active'+str(j),history['active'],actual_history['active'])
            cells(cid,'incoming_history',history['storage'],actual_history['storage'],48)
            if diag['path_recomputed']:counts['BFS_compared_u16_values']+=78400
            packets_eq(cid,'packet'+str(j),diag['known_packets'],got['new_packets'])
            counts['component_steps']+=1;counts['positive_heal_events']+=len(diag['heal_events'])
            for event in diag['heal_events']:counts[event['reason_id']+'_events']+=1
            counts['expiry_events']+=len(diag['expired_spells']);counts['AI_attacks']+=len(diag['AI_attacks']);counts['AI_motions']+=len(diag['AI_motions']);counts['corpse_removals']+=len(diag['removed_guids'])
            counts['basic_success']+=sum(e[0]=='basic_success'for e in diag['events']);counts['basic_natural_crit']+=sum(e[0]=='basic_success'and e[3]for e in diag['events'])
            for name in('cleave','thunder_clap'):counts[name+'_success']+=sum(e[0]=='owned'and e[2]==name and e[3]for e in diag['events'])
            counts['racial_success']+=sum(e[0]=='racial'and e[1]for e in diag['events']);previous=got['after']
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',differences)
    artifacts={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json','prepared.json','actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','expectation-read-audit.json','stderr.log','differences.json')if(out/n).exists()}
    report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),
        differences=counts['differences'],sources_before=sources,sources_after=sources,source_import_edges=edges,
        expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,
        artifacts=artifacts,frozen=frozen,runtime=runtime,process=terminal,counts=dict(counts),
        independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,
        limitations=['Full2123then925 consecutive components with external884-compatible clock arithmetic; not884/fullmain or completegame.',
        'Other actual main stages924/983/1775/3755/920/38553/2621/2890/2584/952/2372/49961 not executed or replaced here.',
        '2 natural-center cases and1 controlled initial player placement; no NPC position/HP/source clearing or cooldown/racial disabling.',
        'Known packet ordered subset and semantic outgoing ledger; full2077 physicalcontainer/key/catalog/deque pending.',
        'NPC deathmarker producer, strict1.2 expiry, full432stablecompaction/count/capacity/staleTail verified; nonempty destructor owners stop.',
        'All incoming hurt produced by actual925, no standalone1076 fixture; its category0 internal param5 queueindex remains source-proven unread, not modeled as zero.',
        'Only actual2owned(rank1cleave/Thunder)/Humanracial/defaultWarrior emptyprocowners; otherabilities/upgrades/positiveheal_on_kill stop.'])
    save(out/'comparison.json',report)
    summary_keys=('assertions','component_steps','positive_heal_events','regen_events','leech_events',
        'expiry_events','AI_attacks','AI_motions','corpse_removals','basic_success','basic_natural_crit',
        'cleave_success','thunder_clap_success','racial_success','known_packets','known_packet_bytes',
        'NPC_unknown_copy_or_retained','BFS_compared_u16_values')
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),
        differences=counts['differences'],first=differences[:4],counts={k:counts[k]for k in summary_keys},process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
