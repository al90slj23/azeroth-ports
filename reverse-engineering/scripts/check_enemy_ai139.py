#!/usr/bin/env python3
"""Expected-first full925 current139 natural fourNPC movement/contact chain."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from check_growth_world139 import ROOT,SOURCE,SOURCE_SHA,NODE,NODE_SHA,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,missing
from incoming139_tools import sha,save
from build_enemy_ai139_oracle import build
from check_asset_world139 import load_world139
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.opening139 import DefaultOpeningInput139,initialize_default_opening139,opening_projection139,opening_known_game139
from core_spec.opening_profile139 import EmptyAccountSources139
from core_spec.growth139 import from_constructor139
from core_spec.enemy_ai139 import EnemyAIState139,update_enemy_ai139
from core_spec.incoming139 import IncomingState139
from core_spec.incoming_history139 import from_raw_storage,projection as history_projection

ENGLISH={5830904:'Kobold Vermin'}
def closure():
    names=set(production_sources135(ROOT,'core_spec.enemy_ai139','core_spec.opening139'))|set('scripts/'+n for n in('check_enemy_ai139.py','build_enemy_ai139_oracle.py','run_enemy_ai139_oracle.mjs','trace_enemy_ai139.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])

def expected(case,world):
    opening=initialize_default_opening139(DefaultOpeningInput139(int(case['app_seed_u64']),EmptyAccountSources139(0,0,0,0),tuple([165]*40)),world)
    growth=from_constructor139(opening.constructor,phase2587=1);rows=tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells'])
    incoming=IncomingState139(1,0,0,0,growth.current_hp_bits,growth.derived_bits[1536],growth.derived_bits[1568],growth.derived_bits[1572],items8=(),last_hit1652_bits=0xc1200000)
    seq=struct.unpack('<I',bytes(opening_known_game139(opening)[2412:2416]))[0]
    state=EnemyAIState139(rows,0,case['dt_bits'],opening.constructor.player_xyz,incoming,from_raw_storage((),0,0),tuple(growth.player_fields.items()),movement_sequence2412=seq)
    packets=list(opening_projection139(opening)['packets']);frames=[]
    for j in range(case['frames']):
        state=replace(state,now_bits=f.add(state.now_bits,case['dt_bits']));result=update_enemy_ai139(state,world,english_names=ENGLISH);state=result.state;packets.extend([list(x)for x in result.packets]);path=state.distance_map
        frames.append(dict(frame=j,records=[list(r)for r in state.records432],hp1440_bits=state.incoming.hp1440_bits,last_hit1652_bits=state.incoming.last_hit1652_bits,incoming992_hex=struct.pack('>d',state.incoming.incoming992).hex(),categories={k:struct.pack('>d',v).hex()for k,v in state.incoming.category1112},fields=dict(state.player_fields),history=history_projection(state.history),path=None if path is None else dict(capacity=len(path.values_u16),count=len(path.values_u16),start_index=path.start_index,field24=path.field24,u16le_sha256=hashlib.sha256(struct.pack('<'+'H'*len(path.values_u16),*path.values_u16)).hexdigest()),path_clock2372_bits=state.distance_clock2372_bits,movement_sequence2412=state.movement_sequence2412,packets=list(packets),attacks=[list(x)for x in result.attacks],routing=[list(x)for x in result.routing],path_recomputed=result.path_recomputed))
    return dict(opening=opening_projection139(opening),frames=frames)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args()
    files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    assert all(sha(p)==s for p,s in((SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(WORLD/'receipt.json',WORLD_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA)))
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('enemy-ai139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    # Static identities/source labels are declared before expectation, not from observations.
    manifest=build(out);trace=json.loads((out/'static/trace.json').read_text());assert{int(k):v for k,v in trace['english_names'].items()}==ENGLISH
    cases=[dict(id=0,app_seed_u64='0',dt_bits=f.from_float(.5),frames=2 if args.phase=='pilot'else 32)]
    if args.phase=='full':cases.extend([dict(id=1,app_seed_u64='1',dt_bits=f.from_float(.25),frames=48),dict(id=2,app_seed_u64='42',dt_bits=f.from_float(1),frames=12)])
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original input denied during expectation')
    sys.addaudithook(audit)
    try:
        world,_,_=load_world139(WORLD);rows=[dict(id=c['id'],expected=expected(c,world))for c in cases]
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files}
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',cases);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden,layer='Python open audit'))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',manifest['module_file'],'expectation-read-audit.json','static/trace.json')}
    save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,all_background_owners_retained=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_enemy_ai139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=120))
        try:code=p.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code=p.returncode
    terminal=dict(pid=p.pid,pgid=p.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(line)for line in(out/'actual.jsonl').read_text().splitlines()];diff=[];counts=Counter()
    def eq(case,field,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(case=case,field=field,expected=want,actual=got))
    for row,a in zip(rows,actual):
        case=row['id'];e=row['expected'];eq(case,'id',case,a['id']);eq(case,'newGame',False,a['new_Game_pointer']==a['old_snapshot_Game_not_target'])
        eq(case,'opening-packets',e['opening']['packets'],a['opening']['packets']);eq(case,'framecount',len(e['frames']),len(a['frames']))
        previous=a['before']
        for want,got in zip(e['frames'],a['frames']):
            tag='f'+str(want['frame']);v=got['view'];ai=got['ai'];eq(case,tag+'.frame',want['frame'],got['frame'])
            for key in('path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories'):eq(case,tag+'.'+key,want[key],ai[key])
            eq(case,tag+'.hp',want['hp1440_bits'],v['projection']['current_hp_bits']);eq(case,tag+'.fields',{str(k):val for k,val in want['fields'].items()},v['projection']['player_fields'])
            eq(case,tag+'.movementSequence',want['movement_sequence2412'],v['background']['movement_sequence2412']);eq(case,tag+'.packets',want['packets'],v['packets'])
            eq(case,tag+'.historyheader',want['history']['header'],ai['history']['header']);eq(case,tag+'.historyactive',want['history']['active'],ai['history']['active'])
            for kind,desired,physical in(('NPC',want['records'],v['background']['units']['storage']),('history',want['history']['storage'],ai['history']['storage'])):
                eq(case,tag+'.'+kind+'cap',len(desired),len(physical))
                for j,(cells,hx)in enumerate(zip(desired,physical)):
                    for k,(expectedbyte,actualbyte)in enumerate(zip(cells,bytes.fromhex(hx))):
                        if expectedbyte is None:counts[kind+'_None_bytes']+=1;counts[kind+'_nonzero_None_bytes']+=bool(actualbyte)
                        else:eq(case,f'{tag}.{kind}[{j}]+{k}',expectedbyte,actualbyte);counts[kind+'_known_bytes']+=1
            for key in('pickups','special','windows','boundaries','auxiliary','claims','counter2408'):eq(case,tag+'.background.'+key,a['before']['background'][key],v['background'][key])
            for key in('rng_words','derived_bits','owned_records80_hex','phase2587'):eq(case,tag+'.unchanged.'+key,a['before']['projection'][key],v['projection'][key])
            eq(case,tag+'.live',a['before']['live32_hex'],v['live32_hex'])
            allowed=set()
            for start,size in((968,16),(992,8),(1112,12),(1440,4),(1652,4),(1880,12),(2352,4),(2368,8),(2412,4),(2476,12)):allowed.update(range(start,start+size))
            oldgame=bytes.fromhex(previous['raw_game2592_hex']);newgame=bytes.fromhex(v['raw_game2592_hex'])
            for j,(beforebyte,afterbyte)in enumerate(zip(oldgame,newgame)):
                if j not in allowed:eq(case,f'{tag}.inheritedGame+{j}',beforebyte,afterbyte);counts['inherited_Game_bytes']+=1
            writable=set(range(316,356))|set(range(404,408))
            for j,(oldhx,newhx)in enumerate(zip(previous['background']['units']['storage'],v['background']['units']['storage'])):
                for k,(beforebyte,afterbyte)in enumerate(zip(bytes.fromhex(oldhx),bytes.fromhex(newhx))):
                    if k not in writable:eq(case,f'{tag}.inheritedNPC{j}+{k}',beforebyte,afterbyte);counts['inherited_NPC_bytes']+=1
            counts['frames']+=1;counts['contacts']+=len(want['attacks']);counts['path_rebuilds']+=want['path_recomputed'];previous=v
        counts['movement_packets']+=sum(p[0]==221 for p in e['frames'][-1]['packets'])-sum(p[0]==221 for p in e['opening']['packets'])
    for n,h in sources.items():assert sha(ROOT/n)==h
    for n,h in frozen.items():assert sha(out/n)==h
    save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    artifacts={n:sha(out/n)for n in('actual.jsonl','stderr.log','runtime.json','owned-start.json','owned-terminal.json','prepared.json','differences.json')if(out/n).exists()}
    comparison=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(cases),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,limits=['Actualfull1108 newGame4NPC/2Rune/windows/special/boundaries preserved;pathNone andvelocity0 explicit setup.','Full925 standalone: no player2123/mainloop883/native execution,perception not disabled or scheduled.','Ordinary default melee only;nonfatal emptycallbacks/no status/ranged/boss/pet/fatal.','Logicalcategory/keyedhistory verified,physicalBTreeallocation addresses not independently modeled.','Sharedpure135nav algorithms rebound to current925/30179/29237;oldruntimeacceptance not reused.'])
    save(out/'comparison.json',comparison);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(cases),completed=len(actual),differences=counts['differences'],first_fields=[x['field']for x in diff[:6]],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(cases)or counts['differences']:raise SystemExit(1)
if __name__=='__main__':main()
