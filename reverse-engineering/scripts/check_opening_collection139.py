#!/usr/bin/env python3
"""Expected-first full1108→actualdeaths/XP→firstcard→directcontinuation."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
from collections import Counter
import argparse,json,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from build_opening_collection139_oracle import build
from check_asset_world139 import load_world139
from check_opening139 import compare as compare_opening,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA,WORLD,WORLD_SHA
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.opening_collection139 import OpeningCombatCounters139,OpeningCollectionInput139,compose_firstlevel_opening_collection139
from core_spec.cast139 import CleaveDefinition139
DEFINITION='0000000000000000000000003aa5590006000000ccb5590006000000d2b5590016000000e8b55900030000004d03000000003c420000c03f0000e04000000000030000000000000000000000000000000000000005000000'


def closure():
    names=set(production_sources135(ROOT,'core_spec.opening_collection139','resource_spec.world_query135'))|{
        'scripts/check_opening_collection139.py','scripts/run_opening_collection139_oracle.mjs',
        'scripts/build_opening_collection139_oracle.py','scripts/check_asset_world139.py',
        'scripts/production_closure135.py','scripts/source_closure137.py'}
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def corpus(world,pilot):
    rows=[];definition=CleaveDefinition139(5882740,b'cleave',bytes.fromhex(DEFINITION))
    for seed in [0]if pilot else[0,1,42]:
        c=OpeningCombatCounters139(0,(),0,0,1,0,0,0)
        answer=compose_firstlevel_opening_collection139(OpeningCollectionInput139(seed,c,'near_first',(0,)),world,definition)
        counters=asdict(c);counters['accounted_total_bits']=str(counters['accounted_total_bits'])
        rounds=[dict(target_index=r['target_index'],now_bits=r['now_bits'],collect_times=r['collect_times'])for r in answer['rounds']]
        follow=answer['continuation']
        inp=dict(id=len(rows),app_seed_u64=str(seed),initial_counters=counters,rounds=rounds,
            select_index=answer['selection']['index'],followup_index=None if follow is None else follow['target_index'])
        rows.append(dict(id=len(rows),input=inp,expected=answer))
    return json.loads(json.dumps(rows,default=asdict))


def compare(case,actual,counts,diff):
    def eq(field,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(id=case['id'],field=field,expected=want,actual=got))
    e=case['expected'];compare_opening(dict(id=case['id'],expected=e['opening_expected']),actual,counts,diff)
    def cells(label,wants,observed):
        eq(label+'.rows',len(wants),len(observed))
        for j,(want,hx)in enumerate(zip(wants,observed,strict=True)):
            raw=bytes.fromhex(hx);eq(label+'.width',len(want),len(raw))
            for i,(v,b)in enumerate(zip(want,raw,strict=True)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
                else:eq(f'{label}[{j}]+{i}',v,b);counts[label+'_known']+=1
    def packets(label,want,got):
        cursor=0
        for packet in want:
            found=next((i for i in range(cursor,len(got))if got[i]==packet),None)
            eq(label+'.packet-present',True,found is not None)
            if found is not None:cursor=found+1
            counts[label+'_known_packets']+=1;counts[label+'_known_packet_bytes']+=len(packet[1])//2
    def cast(label,ep,got):
        cells('castNPC',ep['records432_cells'],got['records432_hex']);cells('castPickup',ep['pickups56_cells'],got['pickups56_hex'])
        for k in set(ep)-{'records432_cells','pickups56_cells','known_packets'}:eq(label+'.'+k,ep[k],got.get(k))
        packets('cast',ep['known_packets'],got['new_packets'])
    def growth(label,ep,got):
        for k,v in ep.items():
            if k=='player_fields':
                for field,value in v.items():eq(label+'.field'+field,value,got[k].get(field));counts['known_growth_fields']+=1
            else:eq(label+'.'+k,v,got.get(k))
    previous=actual['after']['raw_Game2592_hex']
    eq('rounds',len(e['rounds']),len(actual['rounds']))
    for roundno,(er,ar)in enumerate(zip(e['rounds'],actual['rounds'],strict=True)):
        eq('round.before-control',previous,ar['before_control_hex'])
        action=bytearray.fromhex(previous);action[2352:2356]=er['now_bits'].to_bytes(4,'little')
        for j,v in enumerate(er['player_xyz']):action[1416+4*j:1420+4*j]=v.to_bytes(4,'little')
        eq('round.controlonlyXYZandclock',action.hex(),ar['action_before']['raw_Game2592_hex']);previous=action.hex()
        for j,(ep,got,raw)in enumerate(zip(er['cast_stages'],ar['cast_stages'],ar['cast_raw_games'],strict=True)):
            eq('cast.fullGameinputinherited',previous,raw['before_hex']);cast(f'round{roundno}.cast{j}',ep,got);previous=raw['after_hex'];counts['complete922_returns']+=1
        for j,(ep,got)in enumerate(zip(er['collection_stages'],ar['collection_stages'],strict=True)):
            cells('collectPickup',ep['pickups56_cells'],got['pickups56_hex'])
            for k in set(ep)-{'pickups56_cells','known_player_fields','new_packets','growth_projection'}:eq(f'collect{roundno}.{j}.'+k,ep[k],got.get(k))
            fields=dict(got['player_fields'])
            for k,v in ep['known_player_fields'].items():eq(f'collect{roundno}.{j}.field'+k,v,fields.get(int(k)));counts['known_player_fields']+=1
            growth(f'growth{roundno}.{j}',ep['growth_projection'],got['growth']['projection'])
            packets('collect',ep['new_packets'],got['new_packets'])
            before=bytearray.fromhex(previous);before[2352:2356]=ep['now_bits'].to_bytes(4,'little')
            eq('collect.fullGameinputinherited',before.hex(),got['raw_game_before_hex']);previous=got['raw_game_after_hex']
            eq('collect.NPCconserved',got['units_before_hex'],got['units_after_hex']);counts['NPC_source_conserved_bytes']+=len(bytes.fromhex(got['units_before_hex']));counts['complete2890_returns']+=1
    selection=actual['selection'];eq('select.fullGameinputinherited',previous,selection['before_game_hex'])
    growth('selection',e['selection']['projection'],selection['projection']);cells('selectedLive',e['selection']['live32_cells'],selection['live32_hex']);previous=selection['after_game_hex'];counts['complete1093_returns']+=1
    eq('selection.actualowned2source',e['postselection_hit_sources'],selection['postselection_hit_sources'])
    eq('selection.inactiveNPCconserved',selection['units_before_hex'],selection['units_after_hex']);counts['selected_NPC_source_conserved_bytes']+=len(bytes.fromhex(selection['units_before_hex']))
    eq('selection.emptyhitsources-before',[0]*7,selection['hit_source_words_before']);eq('selection.emptyhitsources-after',[0]*7,selection['hit_source_words_after'])
    if e['continuation']is None:eq('continuation',None,actual['continuation'])
    else:
        ep=e['continuation'];got=actual['continuation'];eq('follow.beforecontrol',previous,got['before_control_hex']);action=bytearray.fromhex(previous)
        for j,v in enumerate(ep['player_xyz']):action[1416+4*j:1420+4*j]=v.to_bytes(4,'little')
        eq('follow.controlonlyXYZ',action.hex(),got['before_game_hex']);cast('continuation',ep['state'],got['state'])
        eq('follow.actualowned2scan',ep['actual_owned_scan'],got['actual_owned_scan']);cells('followLive',ep['live32_cells_preserved'],got['live32_after_hex']);eq('follow.actualLiveconserved',got['live32_before_hex'],got['live32_after_hex']);counts['postselection_live_preserved_cleave_returns']+=1
    for key in ['companions','windows','special','boundaries']:eq('background.'+key,actual['after'][key],actual['terminal_view'][key])
    eq('Runephysicalprefix',actual['after']['pickups']['storage'][:2],actual['terminal_view']['pickups']['storage'][:2]);eq('background-flag',True,actual['background_unchanged'])
    eq('initialcountercontract',case['input']['initial_counters'],actual['initial_counters_observed'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args()
    files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    assert sha(SOURCE)==SOURCE_SHA and sha(CONTEXT)==CONTEXT_SHA and sha(RANGES)==RANGES_SHA and sha(GATE)==GATE_SHA and sha(NODE)==NODE_SHA
    opened=[];auditing=True
    def audit(event,params):
        if auditing and event=='open'and isinstance(params[0],(str,bytes,os.PathLike)):
            p=str(params[0]);opened.append(p)
            if p.endswith(('.memory','.wasm','.wat','.exe'))or'/originals/'in p:raise AssertionError(('Originalforbiddenduringexpectations',p))
    sys.addaudithook(audit)
    try:world,_,_=load_world139(WORLD);rows=corpus(world,args.phase=='pilot')
    finally:auditing=False
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-collection139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out);assert m['definition']['raw88_hex']==DEFINITION
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'expected.json',rows);save(out/'inputs.json',[r['input']for r in rows]);save(out/'expectation-read-audit.json',dict(kind='Pythonopen_audit_notOSaudit',opened=opened,forbidden=False,world_receipt_sha256=WORLD_SHA))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in ['expected.json','inputs.json','manifest.json','config.json',m['module_file'],'expectation-read-audit.json']}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_opening_collection139_oracle.mjs'),str(out),str(out/'config.json')]
    save(out/'prepared.json',dict(source_before=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_inputs_contain_expected=False,resource_context_gate_sha256=GATE_SHA,world_receipt_sha256=WORLD_SHA,command=command));started=time.monotonic()
    with(out/'stdout.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=60))
        try:p.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    def missing(group=False):
        try:(os.killpg if group else os.kill)(p.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-started,pid_missing=missing(),pgid_missing=missing(True));save(out/'process-terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];counts=Counter();diff=[]
    for c,a in zip(rows,actual):assert c['id']==a['id'];compare(c,a,counts,diff)
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    total_rounds=sum(len(r['input']['rounds'])for r in rows);follows=sum(r['input']['followup_index']is not None for r in rows);expected_calls={'2945':len(rows),'1600':len(rows),'1108':len(rows),'922':2*total_rounds+follows,'2890':2*total_rounds,'1093':len(rows)}
    runtime_ok=bool(runtime)and runtime['full_calls']==expected_calls and runtime['host_calls']==0 and runtime['denied_imports']==882 and runtime['fresh_instances']==len(rows)and len(runtime['world_source_checks'])==4*len(rows)+4*total_rounds+follows and runtime['error']is None and len(runtime['target_and_setup_returns'])==sum(expected_calls.values())and all(r['returned']and r['before']==r['after']==1048576 for r in runtime['target_and_setup_returns'])and runtime['stack_guards']==runtime['allocator_calls']+sum(expected_calls.values())
    process_ok=p.returncode==0 and len(actual)==len(rows)and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<60
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}and sha(SOURCE)==SOURCE_SHA
    save(out/'differences.json',diff);artifacts={n:sha(out/n)for n in ['expected.json','inputs.json','config.json','manifest.json','prepared.json','stdout.jsonl','stderr.log','process-terminal.json','owned-process.json','differences.json','expectation-read-audit.json']+(['runtime.json']if runtime else[])}
    receipt=dict(status='scoped_original_composition_passed'if runtime_ok and process_ok and not diff else'failure_preserved',version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed=len(actual),differences=counts['differences'],counts=dict(counts),source_before=sources,source_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,runtime_contract_checked=runtime_ok,process_contract_checked=process_ok,expected_before_original=True,original_inputs_contain_expected=False,resource_context_sha256=CONTEXT_SHA,resource_context_gate_sha256=GATE_SHA,world_receipt_sha256=WORLD_SHA,full_mainloop_frames=0,native_windows_executions=0,complete_games=0)
    save(out/'comparison.json',receipt);print(json.dumps(dict(out=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=counts['differences'],first=diff[:3],process=terminal)),flush=True)
    if not process_ok or not runtime_ok or diff:raise SystemExit(1)


if __name__=='__main__':main()
