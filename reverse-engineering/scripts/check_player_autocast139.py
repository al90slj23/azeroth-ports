#!/usr/bin/env python3
"""Expected-first defaultWarrior full1238/2123 success components, not884."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,math,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_player_autocast139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
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


def closure():
    names=set(production_sources135(ROOT,'core_spec.player_autocast139','core_spec.default_damage139',
        'core_spec.thunder_clap_world139','core_spec.enemy_ai139','core_spec.player_regeneration139',
        'core_spec.incoming139','resource_spec.world_query135'))
    names.update('scripts/'+n for n in('check_player_autocast139.py','run_player_autocast139_oracle.mjs',
        'build_player_autocast139_oracle.py','check_healing139_v3.py','check_player_update139.py',
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


def corpus(world,phase):
    layouts=[('warm_moving_basic_cleave',11,'1238',True,True,0.)]
    if phase=='full':layouts.extend([
        ('warm_moving_thunder_regen',11,'2123',True,True,8.),
        ('cold_moving_expiry_racial',11,'2123',False,True,8.),
        ('warm_stationary_tier4',69,'1238',True,False,0.)])
    rows=[];control=dict(contact_flag=1,category=0,spell_id=0)
    declarations=tuple((DEFINITIONS139[k][0],bytes.fromhex(DEFINITIONS139[k][1]))for k in('cleave','thunder_clap'))
    for group,seed,mode,warmup,moving,offset in layouts:
        opening,gain,selected,p=prepare_thunder_world139(seed,world)
        initial=projection(p);ledger=DefaultOutgoingLedger139(0,0,())
        warm_projection=None
        if warmup:
            result=update_player_regeneration139(p,ledger,0x3f800000,0x3f800000,
                sync_aura139=sync_aura139,cast_perception139=cast_perception139)
            p,ledger=result.state,result.healing;warm_projection=projection(p)
        ai_projection=None;ai_clock=0;seq=1
        if moving:
            ai=EnemyAIState139(p.growth.units432_cells,p.growth.now_bits,0x3dcccccd,p.player_xyz,
                incoming_owner(p),IncomingHistory139(0,0,0,(),(),()),
                tuple(p.growth.player_fields.items()),1)
            value=update_enemy_ai139(ai,world,english_names={5830904:'Kobold Vermin'})
            assert not value.attacks
            seq=value.state.movement_sequence2412;ai_clock=value.state.distance_clock2372_bits
            p=replace(p,growth=replace(p.growth,units432_cells=value.state.records432))
            ai_projection=dict(records432_cells=[list(r)for r in value.state.records432],
                movement_sequence2412=seq,distance_clock2372_bits=ai_clock,
                distance_map_cells=list(value.state.distance_map.values_u16),
                distance_seed=value.state.distance_map.start_index,packets=value.packets)
        source=guid139(p.growth.units432_cells[0]);incoming_projection=None
        if warmup:
            incoming=incoming_owner(p);hurt=resolve_prefix139(incoming,f.from_float(20.),
                source_guid=source,contact_flag=control['contact_flag'])
            fields=dict(p.growth.player_fields);fields[22]=math.ceil(f.to_float(hurt.state.hp1440_bits));fields[28]=math.ceil(f.to_float(p.growth.derived_bits[1536]))
            p=replace(p,growth=replace(p.growth,current_hp_bits=hurt.state.hp1440_bits,
                player_fields=fields),last_hit1652_bits=hurt.state.last_hit1652_bits)
            incoming_projection=projection(p)
        before_control=projection(p);now=f.add(p.growth.now_bits,0x3dcccccd)
        pos=position_xyz139(p.growth.units432_cells[0],now)
        xy=(f.add(pos[0],f.from_float(offset)),pos[1]);height=world.height(*xy)
        assert height.found
        player=(*xy,height.value_bits);p=replace(p,player_xyz=player)
        profile=[None]*376
        for o in(160,*range(260,336,4)):profile[o:o+4]=bytes(4)
        profile[344]=profile[345]=1
        hit=produce_default_cleave_hit_sources139(tuple(profile),(p.growth.owned_records80[0],),p.growth.racial_record80)
        hit=replace(hit,owned_execution_scan=prove_owned_execution11_absent139(p.growth.owned_records80,declarations))
        sources=DefaultDeathSources139(hit,(),(),(),(),())
        d=OrdinaryDamageState139(p.growth.units432_cells,p.growth.rng_words,p.growth.now_bits,1,0,(),0,0,
            opening.counter,seq,0,p.growth.current_hp_bits,p.growth.derived_bits[1536],
            PickupVector139(opening.pickups.vector.storage,opening.pickups.vector.count),sources)
        state=PlayerAutocastState139(p,d,ledger,0,0);stages=[];updates=[];diags=[]
        count=12 if phase=='pilot' else 24
        for _ in range(count):
            now=f.add(state.player.growth.now_bits,0x3dcccccd);dt=0x3dcccccd
            updates.append(dict(now_bits=now,dt_bits=dt))
            if mode=='2123':r=update_player_autocast139(state,now,dt,world)
            else:
                state=replace(state,player=replace(state.player,growth=replace(state.player.growth,now_bits=now)),
                    damage=replace(state.damage,now_bits=now))
                r=tick_default_autocast139(state,dt,world)
            state=r.state
            stages.append(dict(player=projection(state.player),combat=combat_projection(state),healing=heal_projection(state.ledger)))
            diags.append(dict(events=r.events,known_packets=r.packets,
                heal_events=[dict(reason_id=e.reason_id,amount_bits=e.amount_bits,event_id=e.event_id)for e in r.heal_events],
                expired_spells=r.expired_spells,regen_request_bits=r.regen_request_bits,
                regen_accounted_bits=r.regen_accounted_bits))
        case=dict(id=len(rows),app_seed_u64=str(seed),amount=5,dead_mask=0,select_index=0,
            mode=mode,warmup=warmup,moving_setup=moving,hurt_amount_bits=f.from_float(20.)if warmup else None,
            incoming_control=control,action=dict(anchor_index=0,anchor_now_bits=updates[0]['now_bits'],
                xoffset_bits=f.from_float(offset),height_bits=height.value_bits),updates=updates)
        rows.append(dict(id=case['id'],group=group,input=case,initial=initial,warmup=warm_projection,
            ai_setup=ai_projection,hurt=incoming_projection,before_control=before_control,
            player_xyz=list(player),actual_card_tier=gain.state.candidates[0].tier,
            incoming_control_expected=dict(control,source_guid=str(source))if warmup else None,
            stages=stages,diagnostics=diags))
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
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('player-autocast139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit_notOSaudit',opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,full_world_owners_retained=True,controlled_player_placement=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_player_autocast139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
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
    def packets_eq(cid,label,want,got):
        position=0
        for p in want:
            found=next((k for k in range(position,len(got))if got[k]==p),None)
            eq(cid,label,True,found is not None)
            if found is not None:position=found+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(p[1])//2
    for row,a in zip(rows,actual,strict=False):
        cid=row['id'];eq(cid,'id',cid,a['id']);player_eq(cid,'initial',row['initial'],a['player_before'])
        if row['warmup'] is not None:player_eq(cid,'warmup',row['warmup'],a['warmup'])
        eq(cid,'incoming_parameter_fidelity',row['incoming_control_expected'],a['incoming_control_observed'])
        if row['hurt'] is not None:player_eq(cid,'hurt',row['hurt'],a['hurt'])
        player_eq(cid,'before_control',row['before_control'],a['before_control'])
        if row['ai_setup'] is not None:
            import struct,hashlib
            ai=row['ai_setup'];got=a['ai_setup'];cells(cid,'AI_setup_NPC',ai['records432_cells'],got['after']['capture']['background']['units']['storage'],432)
            eq(cid,'AI_setup_movement_sequence',ai['movement_sequence2412'],got['after']['capture']['background']['movement_sequence2412'])
            eq(cid,'AI_setup_path_clock',ai['distance_clock2372_bits'],got['path']['clock2372_bits'])
            eq(cid,'AI_setup_path_seed',ai['distance_seed'],got['path']['start_index'])
            eq(cid,'AI_setup_BFS78400',hashlib.sha256(struct.pack('<78400H',*ai['distance_map_cells'])).hexdigest(),got['path']['u16le_sha256'])
            counts['actual925_setup_BFS_cells']+=78400
        controlled=bytearray.fromhex(a['before_control']['capture']['raw_game2592_hex'])
        for k,v in enumerate(row['player_xyz']):controlled[1416+4*k:1420+4*k]=int(v).to_bytes(4,'little')
        eq(cid,'controlled_playerXYZ_only_Game_write',controlled.hex(),a['controlled_before']['capture']['raw_game2592_hex'])
        eq(cid,'controlled_playerXYZ',row['player_xyz'],a['stages'][0]['combat']['player_xyz'])
        previous=a['controlled_before']
        for j,(want,got,diag)in enumerate(zip(row['stages'],a['stages'],row['diagnostics'],strict=True)):
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);inherited[2352:2356]=int(row['input']['updates'][j]['now_bits']).to_bytes(4,'little')
            eq(cid,'sameGame_clock_only'+str(j),inherited.hex(),got['before']['capture']['raw_game2592_hex']);counts['inherited_Game2592_bytes']+=2592
            player_eq(cid,'frame'+str(j),want['player'],got['after'])
            for key,value in want['combat'].items():
                if key=='records432_cells':cells(cid,'NPC',value,got['combat']['records432_hex'],432)
                elif key=='pickups56_cells':cells(cid,'pickup',value,got['combat']['pickups56_hex'],56)
                else:eq(cid,'combat'+str(j)+'.'+key,value,got['combat'].get(key))
            for n,(model,before_hex,after_hex)in enumerate(zip(want['combat']['records432_cells'],got['before_combat']['records432_hex'],got['combat']['records432_hex'],strict=True)):
                old,new=bytes.fromhex(before_hex),bytes.fromhex(after_hex)
                for k,v in enumerate(model):
                    if v is None:eq(cid,f'NPC_unknown_conserved[{n}]+{k}',old[k],new[k]);counts['NPC_unknown_physically_conserved']+=1
            for key,value in want['healing'].items():eq(cid,'healing'+str(j)+'.'+key,value,got['healing'][key])
            names={'regen':('Regeneration','Spell_Nature_Rejuvenation'),'leech':('Leech','Spell_Shadow_LifeDrain02')}
            breakdown=[dict(name=names[k][0],icon=names[k][1],total64=v,owns=0,nested_count=0)for k,v in want['healing']['reason_totals64'].items()if k in names]
            eq(cid,'heal_breakdown'+str(j),breakdown,[{k:r[k]for k in('name','icon','total64','owns','nested_count')}for r in got['healing']['breakdown']])
            packets_eq(cid,'packet'+str(j),diag['known_packets'],got['new_packets'])
            counts['full'+row['input']['mode']]+=1;counts['positive_heal_events']+=len(diag['heal_events'])
            counts['expiry_events']+=len(diag['expired_spells'])
            counts['basic_success']+=sum(e[0]=='basic_success'for e in diag['events'])
            counts['basic_natural_crit']+=sum(e[0]=='basic_success'and e[3]for e in diag['events'])
            for name in('cleave','thunder_clap'):
                counts[name+'_success']+=sum(e[0]=='owned'and e[2]==name and e[3]for e in diag['events'])
            counts['racial_success']+=sum(e[0]=='racial'and e[1]for e in diag['events'])
            previous=got['after']
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',differences)
    artifacts={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json','prepared.json','actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','expectation-read-audit.json','stderr.log','differences.json')if(out/n).exists()}
    report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),
        differences=counts['differences'],sources_before=sources,sources_after=sources,source_import_edges=edges,
        expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,
        artifacts=artifacts,frozen=frozen,runtime=runtime,process=terminal,counts=dict(counts),
        independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,
        limitations=['Full1238/2123 components after controlled player placement, not884/fullmain or completegame.',
        'Optionalactual925 setup produces real movingNPC without clearingowners; continuous925 interleaving still pending.',
        'Known packets are ordered subset; full2077 physicalcontainer/key/catalog/deque and incominghistory/callback projection pending.',
        'Only actual2owned(rank1cleave/Thunder)/Humanracial/defaultWarrior emptyprocowners; otherabilities/upgrades/positiveheal_on_kill stop.',
        'All fourNPC/twoRunes/windows/special/69bounds retained; explicitknown/None payloads.'])
    save(out/'comparison.json',report)
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),
        differences=counts['differences'],first=differences[:4],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
