#!/usr/bin/env python3
"""Expected-first real2123/922 deaths -> full925, no corpse injection."""
from pathlib import Path
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_enemy_ai_dead139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import projection,load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA,missing
from check_player_autocast139 import combat_projection
from check_healing139_v3 import heal_projection
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.autocast_dead_source139 import prepare_autocast_dead_source139
from core_spec.enemy_ai_dead139 import PhysicalNPCVector139,update_enemy_ai_dead139
from core_spec.enemy_ai139 import position_xyz139
from core_spec.default_damage139 import cast_cleave_default139
from core_spec.player_autocast139 import _adopt
from core_spec.healing139 import DefaultHealingSources139
from core_spec.cast139 import CleaveDefinition139
from core_spec.candidates139_data import DEFINITIONS139
from core_spec.death139 import word139,guid139
from core_spec.incoming_history139 import projection as history_projection

ENGLISH={5830904:'Kobold Vermin'}


def closure():
    names=set(production_sources135(ROOT,'core_spec.enemy_ai_dead139','core_spec.autocast_dead_source139'))|set('scripts/'+n for n in['check_enemy_ai_dead139.py','build_enemy_ai_dead139_oracle.py','run_enemy_ai_dead139_oracle.mjs','check_player_update139.py','check_player_autocast139.py','check_healing139_v3.py','production_closure135.py','source_closure137.py'])
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def ai_projection(ai,units):
    path=ai.distance_map
    return dict(capacity=units.capacity,count=units.count,records432_cells=[list(r)for r in units.storage],history=history_projection(ai.history),path=None if path is None else dict(capacity=len(path.values_u16),count=len(path.values_u16),start_index=path.start_index,field24=path.field24,u16le_sha256=hashlib.sha256(struct.pack('<'+'H'*len(path.values_u16),*path.values_u16)).hexdigest()),path_clock2372_bits=ai.distance_clock2372_bits,incoming992_hex=struct.pack('>d',ai.incoming.incoming992).hex(),last_hit1652_bits=ai.incoming.last_hit1652_bits,categories={k:struct.pack('>d',v).hex()for k,v in ai.incoming.category1112},movement_sequence2412=ai.movement_sequence2412)


def adopt_ai(actor,ai):
    g=replace(actor.player.growth,units432_cells=ai.records432,current_hp_bits=ai.incoming.hp1440_bits,player_fields=dict(ai.player_fields),now_bits=ai.now_bits)
    p=replace(actor.player,growth=g,player_xyz=ai.player_xyz,last_hit1652_bits=ai.incoming.last_hit1652_bits)
    return replace(actor,player=p,damage=replace(actor.damage,records432=ai.records432,player_hp1440_bits=ai.incoming.hp1440_bits,now_bits=ai.now_bits,movement_sequence2412=ai.movement_sequence2412))


def prepare(world,dead_count):
    source=prepare_autocast_dead_source139(world);actor=source.actor;ai=source.ai;casts=[];diagnostics=[]
    raw=bytes.fromhex(DEFINITIONS139['cleave'][1]);definition=CleaveDefinition139(5882740,b'cleave',raw)
    while sum(word139(r,0)==1 for r in actor.damage.records432)<dead_count:
        index=next(i for i,r in enumerate(actor.damage.records432)if word139(r,0)==0)
        xyz=position_xyz139(actor.damage.records432[index],actor.damage.now_bits);height=world.height(*xyz[:2]);assert height.found;player=(*xyz[:2],height.value_bits)
        actor=replace(actor,player=replace(actor.player,player_xyz=player));g=actor.player.growth
        result=cast_cleave_default139(actor.damage,player,{str(k):v for k,v in g.derived_bits.items()},definition,g.owned_records80[0],actor.player.spell_sets,world,healing=actor.ledger,healing_sources=DefaultHealingSources139(1,g.source_counts),inherited_context908=0,source_id=0,heal_on_kill1600_bits=g.derived_bits[1600])
        casts.append(dict(anchor_index=index,anchor_guid=str(guid139(actor.damage.records432[index])),now_bits=actor.damage.now_bits,player_xyz=list(player)));actor=_adopt(actor,result)
        diagnostics.append(dict(player=projection(actor.player),combat=combat_projection(actor),healing=heal_projection(actor.ledger),known_packets=[list(p)for p in result.known_packets],selected_ids=list(map(str,result.selected_ids))))
        if len(casts)>12:raise RuntimeError('Bounded actual922 producer did not reach corpse count')
    assert sum(word139(r,0)==1 for r in actor.damage.records432)==dead_count
    g=actor.player.growth;incoming=replace(ai.incoming,now_bits=g.now_bits,records432=g.units432_cells,hp1440_bits=g.current_hp_bits,player_xy=actor.player.player_xyz[:2],last_hit1652_bits=actor.player.last_hit1652_bits)
    ai=replace(ai,records432=g.units432_cells,incoming=incoming,now_bits=g.now_bits,player_xyz=actor.player.player_xyz,player_fields=tuple(sorted(g.player_fields.items())),movement_sequence2412=actor.damage.movement_sequence2412)
    return source,actor,ai,PhysicalNPCVector139(tuple(actor.damage.records432),len(actor.damage.records432)),casts,diagnostics


def corpus(world,phase):
    specs=[(1,0)]if phase=='pilot'else[(n,b)for n in(1,2,4)for b in(-1,0,1)];rows=[]
    for dead_count,neighbor in specs:
        source,actor,ai,units,casts,cast_diags=prepare(world,dead_count);initial_actor=actor;initial_ai=ai;initial_units=units;death_times={word139(r,4)for r in units.active if word139(r,0)};assert len(death_times)==1
        death=next(iter(death_times));boundary=f.add(death,0x3f99999a);assert f.sub(boundary,death)==0x3f99999a
        updates=[];now=ai.now_bits
        for _ in range(11):now=f.add(now,0x3dcccccd);updates.append(dict(now_bits=now,dt_bits=0x3dcccccd))
        last=boundary+neighbor;updates.append(dict(now_bits=last,dt_bits=f.sub(last,now)));now=last
        for _ in range(4):now=f.add(now,0x3dcccccd);updates.append(dict(now_bits=now,dt_bits=0x3dcccccd))
        assert all(f.to_float(c['dt_bits'])>0 and f.to_float(c['dt_bits'])<=f.to_float(0x3dcccccd)for c in updates)
        stages=[];diags=[]
        for c in updates:
            ai=replace(ai,now_bits=c['now_bits'],dt_bits=c['dt_bits']);result=update_enemy_ai_dead139(ai,units,world,english_names=ENGLISH);ai,units=result.ai,result.units;actor=adopt_ai(actor,ai)
            stages.append(dict(player=projection(actor.player),ai=ai_projection(ai,units),new_packets=[list(p)for p in result.packets]))
            diags.append(dict(removed_guids=list(map(str,result.removed_guids)),before_removal=[list(r)for r in result.before_removal],lifetime_proofs=[list(p)for p in result.lifetime_proofs],attacks=[list(p)for p in result.attacks],motions=[list(p)for p in result.motions],path_recomputed=result.path_recomputed,routing=[list(p)for p in result.routing]))
        case=dict(id=len(rows),app_seed_u64='11',amount=5,select_index=0,prefix_updates=[dict(now_bits=r.state.player.growth.now_bits,dt_bits=0x3dcccccd)for r in source.steps],controlled_player_xyz=list(source.controlled_player_xyz),extra_casts=casts,updates=updates)
        rows.append(dict(id=case['id'],group=f'actual_dead{dead_count}_boundary{neighbor:+}',input=case,source_setup_ai_records=[list(r)for r in source.setup_ai_result.state.records432],source_setup_ai_packets=[list(p)for p in source.setup_ai_result.packets],prefix=[dict(player=projection(r.state.player),combat=combat_projection(r.state),healing=heal_projection(r.state.ledger),known_packets=[list(p)for p in r.packets])for r in source.steps],extra_casts=cast_diags,after_producer=dict(player=projection(initial_actor.player),ai=ai_projection(initial_ai,initial_units),combat=combat_projection(initial_actor),healing=heal_projection(initial_actor.ledger)),stages=stages,diagnostics=diags))
    return json.loads(json.dumps(rows))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['study','pilot','full'],default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('enemy-ai-dead139-'+args.phase+'-%Y%m%dT%H%M%S.%fZ');out.mkdir();opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original denied during expectation')
    sys.addaudithook(audit)
    try:world,*_=load_world139(WORLD);rows=corpus(world,'full'if args.phase=='study'else args.phase)
    except BaseException as e:
        save(out/'model-failure.json',dict(error=repr(e),original_executions=0,sources=sources));raise
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files}
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    if args.phase=='study':
        save(out/'model-study.json',dict(original_executions=0,rows=rows,sources=sources,source_import_edges=edges));print(json.dumps(dict(directory=str(out),summaries=[dict(group=r['group'],prefix_marker=[word139(row,0)for row in r['after_producer']['ai']['records432_cells']],extra922=len(r['extra_casts']),removals=[len(d['removed_guids'])for d in r['diagnostics']],attacks=sum(len(d['attacks'])for d in r['diagnostics']))for r in rows])),flush=True);return
    assert all(sha(p)==h for p,h in[(SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA),(WORLD/'receipt.json',WORLD_SHA)])
    m=build(out);save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in['inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json']};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,controlled_clock_and_player_only=True,actual_death_producers=True,physical_capacity_staleTail_retained=True,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA))
    argv=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_enemy_ai_dead139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(argv,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=argv,deadline_seconds=120))
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diff=[]
    def eq(cid,k,w,a):
        counts['assertions']+=1
        if w!=a:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(id=cid,field=k,expected=w,actual=a))
    def cells(cid,k,wanted,hxs):
        eq(cid,k+'.rows',len(wanted),len(hxs))
        for i,(row,hx)in enumerate(zip(wanted,hxs)):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)
            for off,(v,b)in enumerate(zip(row,raw)):
                if v is None:counts[k+'_None']+=1;counts[k+'_nonzero_None']+=bool(b)
                else:eq(cid,f'{k}[{i}]+{off}',v,b);counts[k+'_known']+=1
    def player(cid,k,w,g):
        eq(cid,k+'.growth',w['growth'],g['capture']['projection'])
        for key in['scalar','racial80_hex','spell_sets','source_flags']:eq(cid,k+'.'+key,w[key],g[key])
        for key in['live','aura']:
            for field in['capacity','count']+(['flag2569']if key=='aura'else[]):eq(cid,k+'.'+key+'.'+field,w[key][field],g[key][field])
            cells(cid,key,w[key]['storage'],g[key]['storage'])
    def subset(cid,k,w,g):
        cursor=0
        for packet in w:
            at=next((j for j in range(cursor,len(g))if g[j]==packet),None);eq(cid,k,True,at is not None)
            if at is not None:cursor=at+1;counts['prefix_known_packets']+=1
    def ai(cid,k,w,g,p):
        bg=p['capture']['background']['units'];eq(cid,k+'.count',w['count'],bg['count']);eq(cid,k+'.capacity',w['capacity'],bg['capacity']);cells(cid,'NPC',w['records432_cells'],bg['storage'])
        for key in['path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories']:eq(cid,k+'.'+key,w[key],g[key])
        for key in['header','active']:eq(cid,k+'.history.'+key,w['history'][key],g['history'][key])
        cells(cid,'history',w['history']['storage'],g['history']['storage']);eq(cid,k+'.sequence',w['movement_sequence2412'],p['capture']['background']['movement_sequence2412'])
    def combat(cid,k,w,g):
        for key,value in w.items():
            if key=='records432_cells':cells(cid,k+'_NPC',value,g['records432_hex'])
            elif key=='pickups56_cells':cells(cid,k+'_pickup',value,g['pickups56_hex'])
            else:eq(cid,k+'.'+key,value,g.get(key))
    def healing(cid,k,w,g):
        for key,value in w.items():eq(cid,k+'.'+key,value,g[key])
    allowed=set()
    for off,n in[(968,16),(992,8),(1112,12),(1440,4),(1652,4),(1792,4),(1880,12),(2368,8),(2412,4),(2476,12)]:allowed.update(range(off,off+n))
    for wanted,a in zip(rows,actual):
        cid=wanted['id'];eq(cid,'id',cid,a['id']);eq(cid,'newGame',False,a['new_Game_pointer']==a['old_snapshot_Game_not_target']);cells(cid,'initial_moving',wanted['source_setup_ai_records'],a['ai_setup']['after']['capture']['background']['units']['storage']);eq(cid,'prefix6',6,len(a['prefix']))
        eq(cid,'setup925_packets',wanted['source_setup_ai_packets'],a['ai_setup']['new_packets']);eq(cid,'extra922_count',len(wanted['extra_casts']),len(a['extra_casts']));eq(cid,'full925_frame_count',len(wanted['stages']),len(a['frames']))
        controlled=bytearray.fromhex(a['ai_setup']['after']['capture']['raw_game2592_hex'])
        for i,v in enumerate(wanted['input']['controlled_player_xyz']):struct.pack_into('<I',controlled,1416+4*i,v)
        eq(cid,'prefix_only_actual_playerXYZ_control',controlled.hex(),a['controlled_before']['capture']['raw_game2592_hex']);previous_prefix=a['controlled_before']
        for j,(w,g)in enumerate(zip(wanted['prefix'],a['prefix'])):
            inherited=bytearray.fromhex(previous_prefix['capture']['raw_game2592_hex']);struct.pack_into('<I',inherited,2352,wanted['input']['prefix_updates'][j]['now_bits']);eq(cid,'prefix_clock_only'+str(j),inherited.hex(),g['before']['capture']['raw_game2592_hex'])
            player(cid,'prefix'+str(j),w['player'],g['after']);combat(cid,'prefix'+str(j),w['combat'],g['combat']);healing(cid,'prefix'+str(j),w['healing'],g['healing']);subset(cid,'prefix_packets',w['known_packets'],g['new_packets']);previous_prefix=g['after']
        for j,(w,g)in enumerate(zip(wanted['extra_casts'],a['extra_casts'])):
            inherited=bytearray.fromhex(previous_prefix['capture']['raw_game2592_hex'])
            for i,v in enumerate(wanted['input']['extra_casts'][j]['player_xyz']):struct.pack_into('<I',inherited,1416+4*i,v)
            eq(cid,'extra922_playerXYZ_only'+str(j),inherited.hex(),g['before']['capture']['raw_game2592_hex'])
            player(cid,'extra922'+str(j),w['player'],g['after']);combat(cid,'extra922'+str(j),w['combat'],g['combat']);healing(cid,'extra922'+str(j),w['healing'],g['healing']);subset(cid,'extra922_packets',w['known_packets'],g['new_packets']);previous_prefix=g['after']
        w=wanted['after_producer'];player(cid,'after_producer',w['player'],a['after_producer']);ai(cid,'after_producer',w['ai'],a['after_producer_ai'],a['after_producer']);combat(cid,'after_producer',w['combat'],a['after_producer_combat']);healing(cid,'after_producer',w['healing'],a['after_producer_healing']);eq(cid,'producer_end_exactSameGame',previous_prefix['capture']['raw_game2592_hex'],a['after_producer']['capture']['raw_game2592_hex'])
        previous=a['after_producer']
        for j,(w,g,control,d)in enumerate(zip(wanted['stages'],a['frames'],wanted['input']['updates'],wanted['diagnostics'])):
            tag='frame'+str(j);player(cid,tag,w['player'],g['after']);ai(cid,tag,w['ai'],g['ai'],g['after']);eq(cid,tag+'.packets',w['new_packets'],g['new_packets'])
            counts['full925_complete_packets']+=len(w['new_packets']);counts['full925_complete_packet_bytes']+=sum(len(p[1])//2 for p in w['new_packets'])
            before=bytearray.fromhex(previous['capture']['raw_game2592_hex']);struct.pack_into('<I',before,2352,control['now_bits']);eq(cid,tag+'.clock_only_control',before.hex(),g['before']['capture']['raw_game2592_hex']);counts['Game_input_inherited_bytes']+=2592
            physical=[bytearray.fromhex(hx)for hx in g['before']['capture']['background']['units']['storage']];count=g['before']['capture']['background']['units']['count']
            for row,known in zip(physical,d['before_removal'],strict=True):
                for off,value in enumerate(known):
                    if value is not None:row[off]=value
            for guid in d['removed_guids']:
                at=next(i for i in range(count)if str(int.from_bytes(physical[i][112:120],'little'))==guid)
                for k in range(at,count-1):physical[k]=bytearray(physical[k+1])
                count-=1
            eq(cid,tag+'.full432_stable_copy_and_staleTail',[r.hex()for r in physical],g['after']['capture']['background']['units']['storage']);counts['physical_NPC_replay_bytes']+=432*len(physical)
            for key in['live','aura','racial80_hex']:eq(cid,tag+'.inherited_'+key,a['after_producer'][key],g['after'][key])
            for key in['pickups','special','windows','boundaries','auxiliary','claims','counter2408']:eq(cid,tag+'.inherited_'+key,a['after_producer']['capture']['background'][key],g['after']['capture']['background'][key])
            before=bytes.fromhex(g['before']['capture']['raw_game2592_hex']);after=bytes.fromhex(g['after']['capture']['raw_game2592_hex'])
            for off,(old,new)in enumerate(zip(before,after,strict=True)):
                if off not in allowed:eq(cid,tag+'.nonownedGame'+str(off),old,new);counts['Game_nonowned_after_bytes']+=1
            counts['full925_targets']+=1;counts['corpse_removals']+=len(d['removed_guids']);counts['real_attacks']+=len(d['attacks']);counts['motion221']+=len(d['motions']);counts['path_rebuilds']+=d['path_recomputed'];counts['lifetime_predicates']+=len(d['lifetime_proofs']);previous=g['after']
    eq(-1,'completed_cases',len(rows),len(actual));runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    if code==0 and runtime is not None:
        n=len(rows);targets=sum(len(r['stages'])for r in rows);extra=sum(len(r['extra_casts'])for r in rows)
        assert runtime['full_calls']=={'2945':n,'1600':n,'1108':n,'4677':n,'1093':n,'925':n+targets,'2123':6*n,'922':extra,'1775':0,'3755':0,'1076':0,'1238':0}
        assert runtime['fresh_instances']==n and runtime['allocator_calls']==5*n and runtime['stack_checks']==17*n+targets+extra
        assert len(runtime['target_and_setup_returns'])==12*n+targets+extra and all(r['returned']and r['before']==r['after']==1048576 for r in runtime['target_and_setup_returns'])
        assert len(runtime['world_source_checks'])==12*n+targets+extra and all(r['unchanged']and r['ranges']==2318 for r in runtime['world_source_checks'])
        assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['peak_memory_bytes']==177078272 and runtime['memory_cap_bytes']==268435456 and runtime['error']is None
        assert all(runtime[k]is False for k in['old_Game_used_as_target','readiness_flags_injected','NPC_dead_or_HP_or_position_writes','NPC_records_removed_by_driver','physical_capacity_or_staleTail_cleared','source_headers_cleared','live_racial_CD_cleared','HP_filled_or_reset','App_or_world_Rc_producer_executed','externref_restored'])
        assert runtime['native_executions']==runtime['full_mainloop_frames']==runtime['complete_games']==0 and terminal['pid_missing']and terminal['pgid_missing']
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',diff);artifacts={n:sha(out/n)for n in['actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','prepared.json','stderr.log','differences.json']if(out/n).exists()}
    comp=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,limits=['Actualmarker1 produced by fresh6full2123/optional922;no corpse writes or removal bydriver.','Complete925 standalone with explicit clocks;oldlive12/perception/racial/owned/Aura remain physically retained without2123reschedule.','PhysicalVec capacity/staleTail complete;default empty destructor owners only;other families/duplicateGUID/resourcesPending.','No fullmain884/nativeWindows/fullgame or network/save acceptance.'])
    save(out/'comparison.json',comp);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),counts=dict(counts),process=terminal,first_differences=diff[:4])),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
