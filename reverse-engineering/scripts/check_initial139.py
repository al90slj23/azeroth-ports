#!/usr/bin/env python3
"""Fresh1600 expected-first independent139 default constructor differential."""
from collections import Counter
from dataclasses import asdict
from datetime import datetime,timezone
import argparse,json,os,random,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_initial139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure

sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.initial_state139 import ConstructorInput139,initialize_empty_profile139,projection139,canonical_game_cells139
from core_spec.initial_state139_data import CLASS_STARTERS,RACIAL_ABILITIES,ZONE_ENTRIES

STATIC=ROOT/'evidence/initial139-static-20261102T020924.042153Z/initial-data.json'
STATIC_SHA='7e2e3ab1693723fa8972fc541b919d0ee5ac4c2db90226fadd171b0ee5063060'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def closure():
    declared=set(tuple('scripts/'+n for n in('check_initial139.py','build_initial139_oracle.py','run_initial139_oracle.mjs',
        'trace_initial139.py','production_closure135.py','source_closure137.py'))+
        production_sources135(ROOT,'core_spec.initial_state139'))
    while True:
        try:edges=verify_local_source_closure(sorted(declared));break
        except AssertionError as error:
            pair=error.args[0]
            if not isinstance(pair,tuple)or len(pair)!=2 or pair[1]in declared or not(ROOT/pair[1]).is_file():raise
            declared.add(pair[1])
    assert not any('headless'in n or'player_motion'in n or'player_correction'in n for n in declared)
    return sorted(declared),edges


def data_guard():
    assert sha(STATIC)==STATIC_SHA
    data=json.loads(STATIC.read_text());assert data['original_wasm_sha256']==SOURCE_SHA and data['script_sha256']==sha(ROOT/'scripts/trace_initial139.py')
    fresh=data['fresh'];assert data['target_executions']==0 and data['model_executions']==0 and data['old_acceptance_transferred']is False
    assert data['functions']['1600']['body_sha256']=='17f2335fc31fe91be1509ffcabe89e56662b61cc2c684f862c54c681eb69b8b1'
    assert data['physical_layout']['Game_bytes']==2592 and data['physical_layout']['selected_profile_bytes']==376
    assert {x['class_byte']:(x['starter_id'],x['definition_pointer'],x['hp_bits'])for x in fresh['classes']}==CLASS_STARTERS
    assert {x['race_byte']:(x['racial_id'],x['definition_pointer'],x['execution_kind'],x['effect_tag'])for x in fresh['races']}==RACIAL_ABILITIES
    assert tuple((x['identifier'],x['x_bits'],x['y_bits'],x['field116_bits'])for x in fresh['zones'])==ZONE_ENTRIES
    assert sha(ROOT/data['output_production_data_module'])==data['production_data_sha256']
    stats=ROOT/'evidence/stats0139-oracle-20261102T020320.478498Z/comparison.json'
    assert sha(stats)=='9f667e74d304eed1b36dd56e06c1d17e941ab87e29e558e0dd6b3fec4c316de8'
    assert sha(ROOT/'reconstruction/core_spec/derived_stats139.py')=='1e8edc3ae73fa895438a7a725d235da6d03ea941ad979072479b8d54145acfc7'
    return dict(path=str(STATIC),sha256=STATIC_SHA,fresh139_declaration_rows=len(fresh['classes'])+len(fresh['races'])+len(fresh['zones']),
        own139_stats_validation=str(stats.relative_to(ROOT)),own139_stats_validation_sha256=sha(stats),
        native_executed=False,new139_pointer_data_checked=True,old_function_acceptance_transferred=False)


def corpus(pilot):
    rows=[]
    def add(group,cls,race,zone,seed,guid,height):
        value=ConstructorInput139(cls,race,zone,seed,guid,height);state=initialize_empty_profile139(value);inp=asdict(value)
        inp['seed_u64']=str(seed);inp['object_id_u64']=str(guid)
        rows.append(dict(id=len(rows),group=group,input=inp,region_id=ZONE_ENTRIES[zone][0],
            expected=dict(projection=projection139(state),canonical_cells=canonical_game_cells139(state))))
    add('pilot-class8-human',8,1,0,1,42,0);add('pilot-class1-orc',1,2,0,0,1,0);add('pilot-class4-gnome',4,7,0,(1<<64)-1,999,0)
    if not pilot:
        for cls in(1,2,3,4,5,7,8,9,11):
            for race in range(1,9):add('nineclass-eightrace-empty-profile',cls,race,0,0x123456789abcdef,42,0)
        for zone in range(12):
            for seed in(0,1,(1<<64)-1):add('twelve-zone-flat-entry',8,1,zone,seed,0xffffffff,0x41200000)
        rng=random.Random(0x1391600)
        for j in range(40):add('seed-guid-matrix',8,1 if j%2==0 else 4,0,rng.getrandbits(64),rng.getrandbits(64),0)
        for guid in(0,1,0x100,0x10000,0x1000000,0x100000000,0x10000000000,0x1000000000000,0x100000000000000,0x8000000000000000,0xffffffffffffffff):
            add('constructor-speed-packet-guid-masks',8,4,0,1,guid,0)
    return json.loads(json.dumps(rows))


def model_negative_guards():
    baseline=dict(class_byte=8,race_byte=1,region_index=0,seed_u64=1,object_id_u64=42,flat_height_bits=0)
    variants=(('unsupported-class',dict(class_byte=6)),('unsupported-race',dict(race_byte=0)),
        ('region-out-of-domain',dict(region_index=12)),('negative-seed',dict(seed_u64=-1)),
        ('GUID-u64-overflow',dict(object_id_u64=1<<64)),('height-NaN',dict(flat_height_bits=0x7fc00000)),
        ('height-infinity',dict(flat_height_bits=0x7f800000)),('bool-not-u8',dict(class_byte=True)))
    result=[]
    for name,change in variants:
        try:ConstructorInput139(**(baseline|change))
        except ValueError:result.append(dict(name=name,rejected=True,target_executed=False))
        else:raise AssertionError('Missing model input guard '+name)
    return result


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    files,edges=closure();before={n:sha(ROOT/n)for n in files};guard=data_guard();assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    negative_guards=model_negative_guards();rows=corpus(args.phase=='pilot');assert before=={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('initial139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for name,h in before.items():
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
    expected=out/'expected.json';save(expected,rows)
    inputs=out/'inputs.json';save(inputs,[{k:c[k]for k in('id','input','region_id')}for c in rows])
    config=out/'config.json';save(config,dict(input_path=str(inputs),input_sha256=sha(inputs)))
    frozen={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/manifest['module_file'],out/'1600.wat')}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_initial139_oracle.mjs'),str(out),str(config)]
    save(out/'prepared.json',dict(source_sha256=before,source_import_edges=edges,frozen_artifacts=frozen,expected_before_original=True,
        original_input_contains_expected=False,deadline_seconds=60,command=command,data=guard))
    start=time.monotonic()
    with(out/'stdout.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60,
        pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'process-terminal.json',terminal)
    actual=[json.loads(line)for line in(out/'stdout.jsonl').read_text().splitlines()];differences=[];known=unknown=nonzero_unknown=0
    for c,a in zip(rows,actual):
        assert c['id']==a['id']
        if c['expected']['projection']!=a['projection']:
            for key in set(c['expected']['projection'])|set(a['projection']):
                if c['expected']['projection'].get(key)!=a['projection'].get(key):
                    differences.append(dict(id=c['id'],group=c['group'],field=key,expected=c['expected']['projection'].get(key),actual=a['projection'].get(key)))
        raw=bytes.fromhex(a['raw_game2592_hex']);assert len(raw)==2592
        cells=c['expected']['canonical_cells'];assert len(cells)==2592
        for i,v in enumerate(cells):
            if v is None:unknown+=1;nonzero_unknown+=raw[i]!=0
            else:
                known+=1
                if v!=raw[i]:differences.append(dict(id=c['id'],group=c['group'],field='known_Game_byte',offset=i,expected=v,actual=raw[i]))
    assert before=={n:sha(ROOT/n)for n in files} and frozen=={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/manifest['module_file'],out/'1600.wat')}
    save(out/'differences.json',differences)
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    report=dict(version='0.139.0',actual_build='f79c5e2b4',phase=args.phase,cases=len(rows),actual_cases=len(actual),original1600_calls=0 if runtime is None else runtime['full1600_calls'],
        differences=len(differences),groups=dict(Counter(c['group']for c in rows)),source_files=len(files),source_sha256_before=before,source_sha256_after=before,source_import_edges=edges,
        source_closure_verified_before_expectations=True,expected_before_original=True,input_contains_expected=False,data=guard,
        original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],process=terminal,runtime=runtime,
        physical_comparison=dict(known_bytes=known,unknown_bytes=unknown,observed_nonzero_unknown_bytes=nonzero_unknown,
            inactive_payload_not_filled=True,full_raw2592_preserved=True),
        artifacts={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/'stdout.jsonl',out/'stderr.log',out/'differences.json',out/'process-terminal.json')},
        scope='Fresh full1600/callees with declared emptyselected376 andborrowedflatqueryview;numeric/owned80/racial80 andpartialknown2592Gamebytes',
        model_negative_guards=negative_guards,model_negative_guards_are_original_cases=False,old_acceptance_transferred=False,old_snapshot_loaded=False,complete_App=False,world_Rc_producer=False,phase1=False,native_executions=0,complete_games=0,
        pending=['Naturalaccount/profile376 producer','CompletephysicalGame/heap/BTree/vectorproducer','Realworld/cache6786 lifetime/bootstrap','Opening1108 andcontinuous139flow','NativeWindowsbehavior'])
    save(out/'comparison.json',report)
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),actual_cases=len(actual),differences=len(differences),first=differences[:8],process=terminal)))
    if code or len(actual)!=len(rows)or differences or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)


if __name__=='__main__':main()
