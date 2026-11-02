#!/usr/bin/env python3
"""Expected-first actual2372→full925 genuineCharge queue→laterfull38553."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import replace
from collections import Counter
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_guardian_charge139_oracle import ROOT,SOURCE,SOURCE_SHA,sha,save,build
from check_player_update139 import load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA
from check_natural_run139 import ai_projection
from check_special_world139 import special_projection
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.natural_run139 import prepare_natural_run139,_incoming
from core_spec.enemy_ai139 import EnemyAIState139
from core_spec.enemy_ai_dead139 import PhysicalNPCVector139
from core_spec.guardian_ai139 import GuardianAIContext139,update_guardian_ai139
from core_spec.guardian_ai139_data import GUARDIAN_PHASES139,ENGAGE_TEXT139
from core_spec.guardian_charge139 import EffectVector120139,DeferredGuardianVector56139
from core_spec.frame_systems139 import ScheduledSpellVector139,tick_scheduled_spells139
from core_spec.special_world139 import from_opening_special139,update_special_world139,word


def closure():
    files=set(production_sources135(ROOT,'core_spec.guardian_ai139','core_spec.guardian_charge139','core_spec.natural_run139'))
    files.update('scripts/'+n for n in('check_guardian_charge139.py','build_guardian_charge139_oracle.py','run_guardian_charge139_oracle.mjs','trace_guardian_charge139.py','check_special_world139.py','check_natural_run139.py','check_player_update139.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(files),verify_local_source_closure(sorted(files))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in files;files.add(pair[1])


def context_projection(ctx):
    a=ctx.ai;fields=dict(a.player_fields)
    return dict(ai=ai_projection(a),hp1440_bits=a.incoming.hp1440_bits,player_fields=fields,movement_sequence2412=a.movement_sequence2412,
        units432_storage=[list(r)for r in ctx.special.units432_storage],units_count=ctx.special.units_count,special=special_projection(ctx.special),
        effects=dict(capacity=len(ctx.effects.storage),count=ctx.effects.count,storage=[list(r)for r in ctx.effects.storage]),
        deferred=dict(capacity=len(ctx.deferred.storage),count=ctx.deferred.count,storage=[list(r)for r in ctx.deferred.storage]),
        scheduled=dict(capacity=len(ctx.scheduled.storage),count=ctx.scheduled.count,storage=[list(r)for r in ctx.scheduled.storage]),counter2356=ctx.counter2356)


def corpus(world,phase):
    layout=[(0,0,46)]if phase=='pilot'else[(0,0,46),(1,3,46),(5,None,4)]
    cases=[]
    for seed,home_index,count in layout:
        opening,run=prepare_natural_run139(seed,world);s=replace(from_opening_special139(opening),now_bits=f.from_float(20))
        opening_special=update_special_world139(s);s=opening_special.state
        xyz=run.actor.player.player_xyz
        if home_index is not None:
            h=s.special40_storage[home_index];xyz=(f.add(word(h,16),f.from_float(15)),word(h,20),word(h,24))
        p=replace(run.actor.player,player_xyz=xyz,growth=replace(run.actor.player.growth,now_bits=s.now_bits,units432_cells=s.units432_storage[:s.units_count],rng_words=s.rng_words))
        units=PhysicalNPCVector139(s.units432_storage,s.units_count)
        incoming=_incoming(run.incoming,p,units)
        ai=EnemyAIState139(units.active,s.now_bits,f.from_float(.1),xyz,incoming,run.history,tuple(p.growth.player_fields.items()),run.actor.damage.movement_sequence2412)
        ctx=GuardianAIContext139(ai,s,EffectVector120139((),0),DeferredGuardianVector56139((),0),ScheduledSpellVector139((),0),0)
        steps=[];frames=[]
        for index in range(count):
            now=f.add(ctx.ai.now_bits,f.from_float(.1));ctx=replace(ctx,ai=replace(ctx.ai,now_bits=now,player_xyz=xyz,dt_bits=f.from_float(.1)))
            before=context_projection(ctx);result=update_guardian_ai139(ctx,world);ctx=result.context
            steps.append(dict(now_bits=now,dt_bits=f.from_float(.1),player_xyz=xyz))
            frames.append(dict(before=before,after=context_projection(ctx),packets=result.packets,actions=[dict(unit_index=a.unit_index,ability_index=a.ability_index,ability_pointer=a.ability_pointer,raw40_hex=a.raw40.hex())for a in result.queued_actions],aggro_guids=[str(g)for g in result.aggro_guids],attacks=result.attacks,path_recomputed=result.path_recomputed))
        now=f.add(ctx.ai.now_bits,f.from_float(.1));ctx=replace(ctx,ai=replace(ctx.ai,now_bits=now));before=context_projection(ctx)
        consumed=tick_scheduled_spells139(ctx.scheduled,now);ctx=replace(ctx,scheduled=consumed.vector)
        cases.append(dict(id=len(cases),input=dict(id=len(cases),app_seed_u64=str(seed),home_index=home_index,spawn_now_bits=s.now_bits,steps=steps,consume_now_bits=now),spawn_packets=opening_special.packets,after_spawn=special_projection(s),frames=frames,consumer=dict(before=before,after=context_projection(ctx),packets=consumed.packets,removed_indices=consumed.removed_indices)))
    return json.loads(json.dumps(cases))


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    opened=[];forbidden=[];active=True
    def audit(event,values):
        if active and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original reads denied during independent expectation')
    sys.addaudithook(audit)
    try:world,*_=load_world139(WORLD);rows=corpus(world,args.phase)
    finally:active=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('guardian-charge139-'+args.phase+'-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    assert json.loads(json.dumps(GUARDIAN_PHASES139))==json.loads(json.dumps(manifest['guardian_trace']['phases']))and ENGAGE_TEXT139==manifest['guardian_trace']['engage_english']
    for p,h in((SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA),(WORLD/'receipt.json',WORLD_SHA)):assert sha(p)==h
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','manifest.json',manifest['module_file'],'config.json','expectation-read-audit.json')}
    save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False))
    argv=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_guardian_charge139_oracle.mjs'),str(out),str(out/'config.json')];started=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(argv,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=argv,deadline_seconds=180))
        try:code=child.wait(timeout=180)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-started,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diff=[]
    def eq(cid,key,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(id=cid,field=key,expected=want,actual=got))
    def cells(cid,label,want,got):
        eq(cid,label+'.capacity',len(want),len(got))
        for i,(row,hx)in enumerate(zip(want,got)):
            raw=bytes.fromhex(hx);eq(cid,label+'.width',len(row),len(raw))
            for o,(v,b)in enumerate(zip(row,raw)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
                else:eq(cid,f'{label}[{i}]+{o}',v,b);counts[label+'_known']+=1
    def specialview(cid,label,W,O):
        cells(cid,'special40',W['special40_storage'],[bytes(r).hex()for r in O['special40_storage']])
        for key,value in W.items():
            if key!='special40_storage'and value is not None:eq(cid,label+'.'+key,value,O[key])
    def view(cid,label,W,O):
        for key in('hp1440_bits','player_fields','movement_sequence2412','counter2356'):eq(cid,label+'.'+key,W[key],O[key])
        eq(cid,label+'.NPC_count',W['units_count'],O['units']['count']);cells(cid,'NPC432',W['units432_storage'],O['units']['storage'])
        specialview(cid,label+'.special',W['special'],O['special'])
        for kind in('effects','deferred','scheduled'):
            for key in('count','capacity'):eq(cid,label+'.'+kind+'.'+key,W[kind][key],O[kind][key])
            cells(cid,kind,W[kind]['storage'],O[kind]['storage'])
        for key in('path','path_clock2372_bits','incoming992_hex','categories','last_hit1652_bits'):eq(cid,label+'.ai.'+key,W['ai'][key],O['ai'][key])
        for key in('header','active'):eq(cid,label+'.history.'+key,W['ai']['history'][key],O['ai']['history'][key])
        cells(cid,'history',W['ai']['history']['storage'],O['ai']['history']['storage'])
    unowned=set(range(2592))
    for at,n in((968,16),(992,8),(1112,12),(1440,4),(1652,4),(1808,36),(1880,12),(2356,4),(2368,8),(2412,4),(2476,12)):unowned.difference_update(range(at,at+n))
    for W,O in zip(rows,actual):
        cid=W['id'];eq(cid,'id',cid,O['id']);eq(cid,'spawn_packets',[[op,hx]for op,cap,hx in W['spawn_packets']],O['spawn_packets']);specialview(cid,'after_spawn_special',W['after_spawn'],O['after_spawn']['special']);eq(cid,'framecount',len(W['frames']),len(O['frames']))
        previous=O['after_spawn']
        for index,(A,B)in enumerate(zip(W['frames'],O['frames'])):
            tag=str(index);view(cid,tag+'.before',A['before'],B['before']);view(cid,tag+'.after',A['after'],B['after'])
            eq(cid,tag+'.full_packets',A['packets'],B['packets']);counts['full925']+=1;counts['internal916_actions']+=len(A['actions']);counts['aggro']+=len(A['aggro_guids']);counts['incoming_contacts']+=len(A['attacks'])
            counts['known_packets']+=len(A['packets']);counts['known_packet_bytes']+=sum(len(hx)//2 for op,hx in A['packets'])
            raw=bytearray.fromhex(previous['raw_game2592_hex']);struct.pack_into('<I',raw,2352,W['input']['steps'][index]['now_bits']);struct.pack_into('<3I',raw,1416,*W['input']['steps'][index]['player_xyz']);eq(cid,tag+'.only_input_controls',raw.hex(),B['before']['raw_game2592_hex'])
            for key in('pickups','windows','boundaries','auxiliary','claims'):eq(cid,tag+'.background.'+key,B['before']['background'][key],B['after']['background'][key])
            for key in('rng_words','derived_bits','owned_records80_hex','phase2587','candidates','xp','level','pending'):eq(cid,tag+'.player_preserved.'+key,B['before']['growth'][key],B['after']['growth'][key])
            eq(cid,tag+'.live_preserved',B['before']['live'],B['after']['live']);eq(cid,tag+'.Aura_preserved',B['before']['aura'],B['after']['aura'])
            for j,(model,hx)in enumerate(zip(A['after']['units432_storage'],B['after']['units']['storage'])):
                prior=bytes.fromhex(B['before']['units']['storage'][j]);new=bytes.fromhex(hx)
                for k,v in enumerate(model):
                    if v is None:eq(cid,tag+'.NPC_unwritten',prior[k],new[k]);counts['NPC_unknown_copy']+=1
            eq(cid,tag+'.special_raw_unchanged',B['before']['special']['special40_storage'],B['after']['special']['special40_storage'])
            first=bytes.fromhex(B['before']['raw_game2592_hex']);last=bytes.fromhex(B['after']['raw_game2592_hex'])
            for at in unowned:eq(cid,tag+'.unowned_Game'+str(at),first[at],last[at]);counts['unowned_Game_bytes']+=1
            cap=struct.unpack_from('<I',first,1880)[0];required=struct.unpack_from('<I',last,1888)[0]
            while cap<required:cap=max(4,cap*2)
            eq(cid,tag+'.packet_vector_capacity',cap,struct.unpack_from('<I',last,1880)[0])
            for p,detail in zip(A['packets'],B['packet_details']):
                n=len(p[1])//2;cap=32
                while cap<n:cap*=2
                eq(cid,tag+'.packet_payload_capacity',dict(opcode=p[0],capacity=cap,length=n),detail)
            previous=B['after']
        A=W['consumer'];B=O['consumer'];view(cid,'consumer.before',A['before'],B['before']);view(cid,'consumer.after',A['after'],B['after']);eq(cid,'consumer.full_packets',[[op,hx]for op,cap,hx in A['packets']],B['packets']);counts['full38553']+=1
        eq(cid,'consumer.effects_untouched',B['before']['effects'],B['after']['effects']);eq(cid,'consumer.deferred_untouched',B['before']['deferred'],B['after']['deferred']);eq(cid,'consumer.NPC_untouched',B['before']['units'],B['after']['units'])
        counts['scheduled_launched']+=len(A['packets']);counts['effect120_produced']+=A['after']['effects']['count'];counts['deferred56_produced']+=A['after']['deferred']['count'];counts['all_NPC_retained']+=A['after']['units_count']
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}
    save(out/'differences.json',diff);report=dict(phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,full_mainloop_frames=0,complete_games=0,passing_pilot_excluded=dict(directory='evidence/guardian-charge139-pilot-20261102T172120.974272Z',comparison_sha256='02417e7cf124ead6cc33de39e5593ddf0ba21a381b2017771cc5f201032862fd',full925=46,new_formal_targets_replayed=True),rejected_prior_pilot=dict(directory='evidence/guardian-charge139-pilot-20261102T171552.736844Z',comparison_sha256='257eb5e88a0b341fa04da21645a704a71d4ffd5c573b50b2c3126c8e6ec6fabb',differences=97,cause='rawtag7normalized4selector3 was mistaken for selector4; source switch subtraction omitted',not_counted=True),limits=['Explicit20sclock+playerposition and .1dt full925components;notnatural20s/full884.','All4openingordinary+4real2372Guardiansretained;oneTaskmasterengaged,otherGuardianabilities/phase/leashPending.','Actualrawtag7useshardcodedChargegeometry/duration/damage;declarationparamzerosarenotread.','120Beffectand56Bdeferredactionproduced;full920/deferredconsumerPending,38553isactualemptycontrol.','Logicalhistory/category/keyedHPverified;allocatorpointersobserved,full1076callbacks/fullheapnotrestored.'])
    save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),differences=counts['differences'],counts=dict(counts),first=diff[:3],process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
