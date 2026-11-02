#!/usr/bin/env python3
"""Expected-first complete1391108 in a new1600Game with v2 resource context."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from build_opening_aux139_oracle import build
from trace_opening139 import trace_opening139
from check_asset_world139 import load_world139
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.opening139 import DefaultOpeningInput139,initialize_default_opening139,opening_projection139,opening_known_game139
from core_spec.opening_profile139 import EmptyAccountSources139
from core_spec.initial_state139 import canonical_game_cells139

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
EXPECTED_PHASE=False
EXPECTED_READS=[]

def audit(event,args):
    if EXPECTED_PHASE and event=='open'and isinstance(args[0],(str,bytes,Path)):
        path=str(args[0]);EXPECTED_READS.append(path)
        if path.endswith(('.memory','.wasm'))or'/originals/'in path:raise AssertionError(('Original input forbidden during expectation',path))
sys.addaudithook(audit)

def closure():
    names=set(production_sources135(ROOT,'core_spec.opening139','resource_spec.world_query135'))|set('scripts/'+n for n in('check_opening139.py','run_opening139_oracle.mjs','build_opening_aux139_oracle.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as error:
            pair=error.args[0]
            if not isinstance(pair,tuple)or len(pair)!=2 or pair[1]in names:raise
            names.add(pair[1])

def expected(seed,world):
    state=initialize_default_opening139(DefaultOpeningInput139(seed,EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
    return dict(projection=opening_projection139(state),known_Game2592=list(opening_known_game139(state)),constructor_cells=list(canonical_game_cells139(state.constructor)),constructor_seed_u64=str(state.constructor_seed_u64),selected40_cells=list(state.selected40_cells),diagnostic=dict(window_count_draws=state.windows.count_draws,window_uniform_draws=state.windows.window_draws,boundary_actor_draws=state.boundaries.draws),pending=list(state.pending))

def compare(c,a,counts,diffs):
    def eq(field,w,g):
        counts['assertions']+=1
        if w!=g:
            counts['differences']+=1
            if len(diffs)<120:diffs.append(dict(id=c['id'],field=field,expected=w,actual=g))
    e=c['expected'];p=e['projection'];g=a['after'];eq('constructor_seed_u64',e['constructor_seed_u64'],a['constructor_seed_u64'])
    eq('source-conservation',True,a['account_unchanged']and a['profile_unchanged']);eq('selection-canaries',['c3'*16,'d7'*16],a['selection_canaries'])
    for name,cells,raw in(('selected40',e['selected40_cells'],bytes.fromhex(a['selected40_hex'])),('constructor',e['constructor_cells'],bytes.fromhex(a['constructor']['raw_Game2592_hex'])),('afterGame',e['known_Game2592'],bytes.fromhex(g['raw_Game2592_hex']))):
        for i,(want,got)in enumerate(zip(cells,raw,strict=True)):
            if want is None:counts[name+'_unknown_bytes_observed']+=1;counts[name+'_nonzero_unknown_bytes_observed']+=bool(got)
            else:eq(name+'+'+str(i),want,got);counts[name+'_known_bytes']+=1
    for k in('phase2587','counter','rng_words','player_xyz'):eq(k,p[k],g[k])
    for k in('companions','units','pickups','special','windows','boundaries'):
        eq(k+'.capacity',p[k]['capacity'],g[k]['capacity']);eq(k+'.count',p[k]['count'],g[k]['count']);eq(k+'.physical-slots',len(p[k]['storage']),len(g[k]['storage']))
        for j,(row,actual)in enumerate(zip(p[k]['storage'],g[k]['storage'])):
            for i,(want,got)in enumerate(zip(row,bytes.fromhex(actual),strict=True)):
                if want is None:counts[k+'_unknown_bytes_observed']+=1;counts[k+'_nonzero_unknown_bytes_observed']+=bool(got)
                else:eq(f'{k}[{j}]+{i}',want,got);counts[k+'_known_bytes']+=1
    eq('packets.capacity',p['packet_capacity'],g['packets']['capacity']);eq('packets.count',len(p['packets']),g['packets']['count']);eq('packets.complete-ordered',p['packets'],[[q['opcode'],q['payload_hex']]for q in g['packets']['active']])
    eq('notifications.capacity',p['notification_capacity'],g['notifications']['capacity']);eq('notifications.count',len(p['notifications']),g['notifications']['count']);eq('notifications.complete-ordered',p['notifications'],[q['payload_hex']for q in g['notifications']['active']]);counts['complete_packets']+=len(p['packets']);counts['complete_notifications']+=len(p['notifications'])
    eq('before-typed-velocity-path',[0,0,0],[a['before']['profile_controls'][k]for k in('velocity1736','velocity1740','path2368')]);eq('constructor-phase',0,a['constructor']['phase2587']);eq('constructor-counter',10,a['constructor']['counter'])
    # Controlled same-input conservation: expected known writes are overlaid
    # on the actual input bytes. Seven newly allocated pointer words remain
    # observed relocations, never independent allocator output predictions.
    relative=bytearray.fromhex(a['before']['raw_Game2592_hex']);after=bytes.fromhex(g['raw_Game2592_hex'])
    for i,want in enumerate(e['known_Game2592']):
        if want is not None:relative[i]=want
    for key,offset in(('units',1788),('pickups',1872),('special',1920),('windows',1968),('boundaries',2124),('packets',1884),('notifications',1896)):
        if g[key]['capacity']!=a['before'][key]['capacity']:relative[offset:offset+4]=after[offset:offset+4];counts['observed_new_allocation_pointer_words']+=1
    eq('relativeGame2592-except-explicit-observed-relocations',relative.hex(),after.hex());counts['relativeGame_bytes']+=2592

def main():
    global EXPECTED_PHASE
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest,trace=build(out);trace_opening139(out/'whole-opening-static')
    for name,h in sources.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
    assert sha(WORLD/'receipt.json')==WORLD_SHA and sha(GATE)==GATE_SHA and sha(RANGES)==RANGES_SHA and sha(CONTEXT)==CONTEXT_SHA and CONTEXT.stat().st_size==177078272
    EXPECTED_PHASE=True
    try:
        world,world_receipt,payloads=load_world139(WORLD);seeds=[0]if args.phase=='pilot'else[0,1,2,3,4,5,7,8,9,10,16,31,42,255,1<<63,(1<<64)-1];rows=[dict(id=j,app_seed_u64=str(seed),expected=expected(seed,world))for j,seed in enumerate(seeds)]
    finally:EXPECTED_PHASE=False
    save(out/'fixtures.json',rows);save(out/'inputs.json',[dict(id=c['id'],app_seed_u64=c['app_seed_u64'])for c in rows]);save(out/'expected.json',[dict(id=c['id'],expected=c['expected'])for c in rows]);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit;notOSaudit',opened=EXPECTED_READS,original_WASM_or_memory_read=False,world_model_receipt_sha256=WORLD_SHA))
    config=dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696);save(out/'config.json',config)
    frozen={n:sha(out/n)for n in('fixtures.json','inputs.json','expected.json','config.json','manifest.json',manifest['module_file'],'expectation-read-audit.json')};assert sources=={n:sha(ROOT/n)for n in files}and sha(NODE)==NODE_SHA
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_opening139_oracle.mjs'),str(out),str(out/'config.json')];save(out/'prepared.json',dict(expected_before_original=True,sources=sources,source_import_edges=edges,artifacts=frozen,command=command,deadline_seconds=120,original_input_contains_expected=False,resource_context=dict(snapshot_sha256=CONTEXT_SHA,gate_sha256=GATE_SHA,role='Original-side only;newactual1600Game;notoldGameinputtoindependentmodel'),independent_world_receipt_sha256=WORLD_SHA));started=time.monotonic()
    with(out/'actual.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=120))
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-started,deadline_seconds=120,pid_missing=missing(),pgid_missing=missing(True));save(out/'owned-terminal.json',terminal);actual=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diffs=[]
    if code or len(actual)!=len(rows):save(out/'failure.json',dict(process=terminal,completed=len(actual),expected=len(rows)));print(json.dumps(dict(out=str(out.relative_to(ROOT)),status='failed_preserved',process=terminal,stderr=(out/'stderr.log').read_text()[-2500:])));raise SystemExit(1)
    for c,a in zip(rows,actual,strict=True):assert c['id']==a['id'];compare(c,a,counts,diffs)
    runtime=json.loads((out/'runtime.json').read_text());assert runtime['host_calls']==0 and runtime['full_calls']=={str(i):len(rows)for i in(2945,1600,1108)}and runtime['fresh_instances']==len(rows)and len(runtime['world_source_checks'])==3*len(rows)and all(r['returned']and r['after']==r['before']==1048576 for r in runtime['target_and_setup_returns']);assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}and sha(SOURCE)==SOURCE_SHA
    save(out/'differences.json',diffs);receipt=dict(status='scoped_original_differential_passed'if not diffs else'differences_preserved',version='0.139.0',actual_build='f79c5e2b4',phase=args.phase,cases=len(rows),full1108_calls=len(rows),setup2945_calls=len(rows),setup1600_calls=len(rows),differences=counts['differences'],counts=dict(counts),source_sha256_before=sources,source_sha256_after=sources,source_import_edges=edges,expected_before_original=True,original_input_contains_expected=False,original_sha256=SOURCE_SHA,frozen_artifacts=frozen,artifacts={n:sha(out/n)for n in('actual.jsonl','runtime.json','stderr.log','prepared.json','owned-terminal.json','differences.json','static/trace.json')},runtime=runtime,process=terminal,independent_world_receipt_sha256=WORLD_SHA,resource_context_snapshot_sha256=CONTEXT_SHA,resource_context_gate_sha256=GATE_SHA,limitations=['Current defaultElwynn humanWarrior/GUID0/mode0/level1,explicit empty-account counts and selectedprofile;otherdebug/companion/rank/event modes rejected.','Original consumes healthyv2 initializedlocale/SpellDB/world resource snapshot;newtargetGamefromfresh1600.NotfreshApp/Rc/bootstrap/externref reconstruction.','Independent model consumes onlycurrent139raw-derivedcanonicalworld;nooriginalmemory/WASMread duringexpectationPythonopenaudit;notOSaudit.','Appseed→constructorseed formula is controlled6786LCG arithmetic;full6786notexecuted.','Velocity0/pathNone are explicit typed component inputs;navigationowner remains separate.','Allocator-unwritten cells remainNone;physicalbacking retained.FullGame knownprojectiononly;unmodeledbytes/pointer/payloadcapacity observationsnotclaimed.','Setup2945/1600 are separatelycounted,notnewcomponentacceptance.Mainloop/native/network/completegame0.'])
    save(out/'comparison.json',receipt);print(json.dumps(dict(out=str(out.relative_to(ROOT)),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),differences=counts['differences'],first_differences=diffs[:12],counts=dict(counts),process=terminal)))
    if diffs:raise SystemExit(1)
if __name__=='__main__':main()
