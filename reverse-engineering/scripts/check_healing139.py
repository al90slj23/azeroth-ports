#!/usr/bin/env python3
"""Expected-first positive1392123 regeneration after actual1076 hurt."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_healing139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_asset_world139 import load_world139
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.opening139 import DefaultOpeningInput139,initialize_default_opening139,opening_projection139
from core_spec.opening_profile139 import EmptyAccountSources139
from core_spec.growth139 import from_constructor139,projection139
from core_spec.growth_world139 import gain_xp_world139,select_card_world139
from core_spec.player_update139 import PlayerUpdateState139,LiveVector139
from core_spec.player_regeneration139 import update_player_regeneration139
from core_spec.healing139 import HealingLedger139
from core_spec.incoming139 import IncomingState139,Buff139,resolve_prefix139
from core_spec.death139 import guid139,word139
from core_spec.player_effects139 import AuraSnapshot139,sync_aura139,cast_perception139

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
WORLD=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model'
WORLD_SHA='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
CONTEXT=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_begin1108.memory'
CONTEXT_SHA='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
RANGES=ROOT/'evidence/asset-world139-observation-check-20261102T032808.223945Z/source-ranges.json'
RANGES_SHA='ddfbd9aa7c80d54a25446f33955f474feeebaf3305d416cfffd216b7d065ae02'
GATE=ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json'
GATE_SHA='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'


def closure():
    names=set(production_sources135(ROOT,'core_spec.opening139','core_spec.growth_world139','core_spec.player_update139','core_spec.player_effects139','core_spec.player_regeneration139','core_spec.incoming139','resource_spec.world_query135'))|set('scripts/'+n for n in('check_healing139.py','run_healing139_oracle.mjs','build_healing139_oracle.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def projection(state):
    aura=state.aura_state
    return dict(growth=projection139(state.growth),racial80_hex=state.growth.racial_record80.hex(),live=dict(capacity=state.live.capacity,count=state.live.count,storage=[list(r)for r in state.live.storage]),aura=dict(capacity=aura.capacity,count=aura.count,flag2569=aura.flag2569,storage=[list(r)for r in aura.storage]),scalar={str(k):v for k,v in [(2352,state.growth.now_bits),(1628,state.timer1628_bits),(1444,state.pool1444_bits),(1448,state.pool1448_bits),(1344,state.conditional1344),(1348,state.conditional1348_bits),(764,state.pool764_bits),(1648,state.previous_speed1648_bits),(1652,state.last_hit1652_bits)]},source_flags={str(k):0 for k in[387,548,768,770,772,908]},spell_sets=[list(v)for v in state.spell_sets])


def prepare(world):
    opening=initialize_default_opening139(DefaultOpeningInput139(0,EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
    growth=replace(from_constructor139(opening.constructor,phase2587=1),rng_words=opening.rng_words,units432_cells=tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells']))
    gain=gain_xp_world139(growth,5);selected=select_card_world139(gain.state,0)
    assert selected.accepted and gain.state.candidates[0].ability_id=='thunder_clap'
    rows=selected.state.live32_cells+tuple((None,)*32 for _ in range(4-len(selected.state.live32_cells)))
    state=PlayerUpdateState139(selected.state,LiveVector139(rows,1),tuple(opening.constructor.player_xyz),((),(),()),0,AuraSnapshot139.empty_constructor139())
    value=sync_aura139(dict(player_state=state,growth=state.growth,live=state.live,spell_sets=state.spell_sets,aura=state.aura_state,racial80=state.growth.racial_record80,player_xyz=state.player_xyz))
    state=replace(state,growth=value['growth'],live=value['live'],spell_sets=value['spell_sets'],aura_state=value['aura'])
    return opening,gain,selected,state


def heal_projection(ledger):
    return dict(event_counter960=str(ledger.event_counter960),accepted_count1016=str(ledger.accepted_count1016),reason_totals64={k:str(v)for k,v in ledger.reason_totals64})


def corpus(world,phase):
    opening,gain,selected,initial=prepare(world);layouts=[('actual_hurt_partial_regen',20.,tuple([.125]*8))]
    if phase=='full':layouts += [('actual_hurt_clips_at_maximum',1.,(.125,1.,.125)),('actual_large_nonfatal_hurt',200.,tuple([.125]*8)),('actual_small_hurt_zero_dt_and_cap',.03125,(0.,.1,.5,.125)),('actual_hurt_float_cadence_and_long_delta',10.,(.1,.125,.5,2.,4.,8.))]
    rows=[]
    for group,amount,deltas in layouts:
        ledger=HealingLedger139(0,0,());warm=update_player_regeneration139(initial,ledger,0x3f800000,0x3f800000,sync_aura139=sync_aura139,cast_perception139=cast_perception139);state,ledger=warm.state,warm.healing;g=state.growth
        live=tuple(Buff139(word139(r,8),0 if word139(r,8)==12 else word139(r,12),word139(r,20),word139(r,24))for r in state.live.active)
        incoming=IncomingState139(1,0,0,g.now_bits,g.current_hp_bits,g.derived_bits[1536],g.derived_bits[1568],g.derived_bits[1572],last_hit1652_bits=state.last_hit1652_bits,player_xy=state.player_xyz[:2],records432=g.units432_cells,live32=live,items8=())
        hurt=resolve_prefix139(incoming,f.from_float(amount),source_guid=guid139(g.units432_cells[0]),contact_flag=1)
        assert hurt.callbacks_complete and hurt.history_required and f.to_float(hurt.state.hp1440_bits)>0
        fields=dict(g.player_fields);fields[22]=min(f.MASK,max(0,__import__('math').ceil(f.to_float(hurt.state.hp1440_bits))));fields[28]=min(f.MASK,max(0,__import__('math').ceil(f.to_float(g.derived_bits[1536]))))
        state=replace(state,growth=replace(g,current_hp_bits=hurt.state.hp1440_bits,player_fields=fields),last_hit1652_bits=hurt.state.last_hit1652_bits);hurt_projection=projection(state)
        previous=0x3f800000;updates=[];stages=[];diagnostics=[];heals=[]
        for delta in deltas:
            dt=f.from_float(delta);now=f.add(previous,dt);updates.append(dict(now_bits=now,dt_bits=dt));result=update_player_regeneration139(state,ledger,now,dt,sync_aura139=sync_aura139,cast_perception139=cast_perception139);state,ledger=result.state,result.healing
            stages.append(projection(state));heals.append(heal_projection(ledger));diagnostics.append(dict(expired_spells=result.expired_spells,retained_source_indices=result.retained_source_indices,expiry_recalculate1542_called=result.expiry_recalculate1542_called,expiry_sync1173_called=result.expiry_sync1173_called,regen_request_bits=result.regen_request_bits,regen_accounted_bits=result.regen_accounted_bits,known_packets=result.packets,heal_events=[dict(reason_id=e.reason_id,amount_bits=e.amount_bits,now_bits=e.now_bits,event_id=e.event_id,resolved_spell_id_or_zero=e.resolved_spell_id_or_zero,arg3_descriptor_head=e.arg3_descriptor_head,arg4_descriptor_head=e.arg4_descriptor_head)for e in result.heal_events],events=result.events));previous=now
        case=dict(id=len(rows),app_seed_u64='0',amount=5,dead_mask=0,select_index=0,hurt_amount_bits=f.from_float(amount),updates=updates)
        rows.append(dict(id=case['id'],group=group,input=case,initial=projection(initial),warmup=projection(warm.state),warmup_healing=heal_projection(warm.healing),hurt=hurt_projection,hurt_healing=heal_projection(warm.healing),stages=stages,healing=heals,diagnostics=diagnostics))
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
    try:world,wr,payloads=load_world139(WORLD);rows=corpus(world,args.phase)
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('healing139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit_notOSaudit',opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,full_world_owners_retained=True,external_clock_components=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_healing139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
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
    def compare(cid,label,want,got):
        capture=got['capture'];g=capture['projection']
        for key,value in want['growth'].items():
            if key=='player_fields':
                for k,v in value.items():eq(cid,label+'.key'+k,v,g[key].get(k));counts['known_player_fields']+=1
            else:eq(cid,label+'.'+key,value,g.get(key))
        eq(cid,label+'.complete_logical_player_fields',want['growth']['player_fields'],g['player_fields'])
        for key in('racial80_hex','scalar','source_flags','spell_sets'):eq(cid,label+'.'+key,want[key],got[key])
        for key,width in(('live',32),('aura',16)):
            w,a=want[key],got[key]
            for field in('capacity','count')+ (('flag2569',)if key=='aura'else()):eq(cid,label+'.'+key+'.'+field,w[field],a[field])
            for j,(row,hx)in enumerate(zip(w['storage'],a['storage'],strict=True)):
                raw=bytes.fromhex(hx);assert len(row)==len(raw)==width
                for k,(v,b)in enumerate(zip(row,raw,strict=True)):
                    if v is None:counts[key+'_None']+=1;counts[key+'_nonzero_None']+=bool(b)
                    else:eq(cid,f'{label}.{key}[{j}]+{k}',v,b);counts[key+'_known']+=1
    for row,a in zip(rows,actual,strict=False):
        cid=row['id'];eq(cid,'id',cid,a['id']);compare(cid,'initial',row['initial'],a['player_before']);compare(cid,'warmup',row['warmup'],a['warmup']);compare(cid,'hurt',row['hurt'],a['hurt']);cursor=len(a['hurt']['capture']['packets']);previous=a['hurt']
        for label in('warmup','hurt'):
            for key,value in row[label+'_healing'].items():eq(cid,label+'.heal.'+key,value,a[label+'_healing'][key])

        eq(cid,'account',a['account368_before_hex'],a['account368_after_hex']);eq(cid,'profile',a['profile376_before_hex'],a['profile376_after_hex']);eq(cid,'selection_canaries',['c3'*16,'d7'*16],a['selection_canaries'])
        for j,(want,got,diagnostic)in enumerate(zip(row['stages'],a['player_stages'],row['diagnostics'],strict=True)):
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);inherited[2352:2356]=int(row['input']['updates'][j]['now_bits']).to_bytes(4,'little');eq(cid,'sameGame_inherited_clock_only'+str(j),inherited.hex(),got['before']['capture']['raw_game2592_hex']);counts['inherited_Game2592_bytes']+=2592
            for name in('live','aura','racial80_hex','spell_sets'):eq(cid,'inherited_'+name+str(j),previous[name],got['before'][name])
            for key,value in row['healing'][j].items():eq(cid,'heal.'+key+str(j),value,got['healing'][key])
            names={'regen':('Regeneration','Spell_Nature_Rejuvenation'),'leech':('Leech','Spell_Shadow_LifeDrain02')}
            wanted_breakdown=[dict(name=names[k][0],icon=names[k][1],total64=v,owns=0,nested_count=0)for k,v in row['healing'][j]['reason_totals64'].items()]
            eq(cid,'semantic_breakdown48'+str(j),wanted_breakdown,[{k:r[k]for k in('name','icon','total64','owns','nested_count')}for r in got['healing']['breakdown']]);counts['breakdown_rows_compared']+=len(wanted_breakdown)
            eq(cid,'heal registry remains realempty'+str(j),[0,8,0],[got['healing']['source_registry'][k]for k in('capacity','pointer','count')]);eq(cid,'no invented saved448history'+str(j),[0,8,0],[got['healing']['saved_history'][k]for k in('capacity','pointer','count')]);counts['positive_heal_events']+=len(diagnostic['heal_events']);counts['zero_heal_steps']+=not diagnostic['heal_events']
            compare(cid,'stage'+str(j),want,got['after']);eq(cid,'background'+str(j),a['player_before']['capture']['background'],got['after']['capture']['background']);packets=got['after']['capture']['packets'];new=packets[cursor:];cursor=len(packets);position=0
            for p in diagnostic['known_packets']:
                found=next((k for k in range(position,len(new))if new[k]==p),None);eq(cid,'known_packet'+str(j),True,found is not None)
                if found is not None:position=found+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(p[1])//2
            counts['full2123_calls']+=1;counts['expiry1542_1173_paths']+=diagnostic['expiry_recalculate1542_called'];counts['expired_live_events']+=len(diagnostic['expired_spells'])
            previous=got['after']
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',differences)
    artifacts={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json','prepared.json','actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','expectation-read-audit.json','stderr.log','differences.json')if(out/n).exists()}
    report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],sources_before=sources,sources_after=sources,source_import_edges=edges,expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,artifacts=artifacts,frozen=frozen,runtime=runtime,process=terminal,counts=dict(counts),independent_world_receipt_sha256=WORLD_SHA,resource_context_snapshot_sha256=CONTEXT_SHA,resource_context_gate_sha256=GATE_SHA,fullworld_objects_retained=True,limitations=['Actualfullopening/XP5/newthunder→full2123warmup1sexpires1020/realracial→actualnonfatal1076→positive2123regen;notnaturalAI/main884.','Full2123includesreal1238/currentHumanperception9/effect8;quietcenterNPC4remain26..36away,noAI/motion/full884frames.','Clock/deltaareexplicitcomponentinputs;noCD/racialdisabling/NPCclearing/livepayloadcompletion.','PositivehurtHP/regenactualcap,key22/28 and1466reasonsemantictotals/counters;physical2077catalog/buckets/completekeys andotherhealsourcespending.','Knownpacketsareorderedsubsequence;physicalqueuecapacity/BTreeallocation/UIpresentationstreamsnotfullyprojected.','NativeWindows/network/save/fullgame0.'])
    save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=counts['differences'],first=differences[:4],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
