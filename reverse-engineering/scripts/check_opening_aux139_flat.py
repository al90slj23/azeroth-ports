#!/usr/bin/env python3
"""Expected-first139 actor1886 and13563→1446 kind2 on typedflat query input."""
from collections import Counter
from datetime import datetime,timezone
import argparse,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from build_opening_aux139_oracle import build
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.opening_actor139 import(OpeningVector139,vector_from_hex139,create_world_actor139,append_kind2_pickup139)
from core_spec.opening_aux139_data import CENTER_XY_BITS,FALLBACK_BITS
from core_spec.opening_profile139 import EmptyAccountSources139,absent_companion_selection139,advance_app_seed139
from core_spec.initial_state139 import ConstructorInput139,initialize_empty_profile139,canonical_game_cells139
from core_spec.world_position139_v2 import WorldPositionInput139V2,sample_random_position
from resource_spec.world_query135 import WorldQueries135
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def closure():
    names=set(production_sources135(ROOT,'core_spec.opening_actor139','core_spec.opening_profile139','core_spec.initial_state139','resource_spec.world_query135'))|set('scripts/'+n for n in('check_opening_aux139_flat.py','run_opening_aux139_flat_oracle.mjs','build_opening_aux139_oracle.py','production_closure135.py','source_closure137.py'))
    while True:
        try:edges=verify_local_source_closure(sorted(names));return sorted(names),edges
        except AssertionError as error:
            pair=error.args[0]
            if not isinstance(pair,tuple)or len(pair)!=2 or pair[1]in names:raise
            names.add(pair[1])

def corpus(pilot):
    rows=[];b=f.from_float;cx,cy=map(f.to_float,CENTER_XY_BITS)
    def add(kind,group,seed=0,height=0,counter=None,rng=None,backing=False,**changes):
        c=dict(id=len(rows),kind=kind,group=group,constructor_seed_u64=str(advance_app_seed139(seed)),flat_height_bits=b(height),now_bits=0,counter_override=counter,rng_override=rng,pickup_backing=[bytes([0x30+j])*56 for j in range(4)]if backing else[])
        c['pickup_backing']=[row.hex()for row in c['pickup_backing']];c.update(changes);rows.append(c)
    add('actor','boundary-actor-default',descriptor=[9013,4831,b(1)],xyz_bits=[b(cx),b(cy),0],kind21=5,flags9=16)
    add('pickup','two-kind2-provided-points',backing=True,ops=[dict(xyz_bits=[b(cx+10),b(cy+20),b(999)],amount=2,now_bits=0),dict(xyz_bits=[b(cx-10),b(cy-20),b(-999)],amount=1,now_bits=b(.5))])
    add('runes','two13563-to1446-from-constructor')
    if not pilot:
        for seed in(1,2,42,(1<<64)-1):
            for entry,display,scale,kind,flags in((9005,259,.5,3,0),(9013,4831,1,5,16),(0x12345678,0xffff,1.25,2,0xffffffff)):
                add('actor','actor-seed-descriptor-matrix',seed=seed,descriptor=[entry,display,b(scale)],xyz_bits=[b(cx+13.25),b(cy-14.5),b(-2)],kind21=kind,flags9=flags)
        for rng in((0,0,0,0),(1,2,3,4),(0xffffffff,)*4):add('actor','typed-RNG-bits',rng=list(rng),counter=0xffffffff,descriptor=[9013,4831,b(1)],xyz_bits=[b(cx),b(cy),b(2)],kind21=5,flags9=16)
        for distance in(0,117.99,118,118.01,130,1000):
            add('pickup','kind2-hypot-radius118-clamp',height=4.25,backing=distance==118,ops=[dict(xyz_bits=[b(cx+distance),b(cy),b(99)],amount=2,now_bits=b(20))])
        for seed in(0,1,2,42,(1<<64)-1):
            for backing in(False,True):add('runes','rune-chain-seed-and-known-backing',seed=seed,height=-10 if backing else 0,backing=backing)
        add('runes','rune-counter-u32-wrap',counter=0xfffffffe)
        add('runes','rune-typed-RNG-zeros',rng=[0,0,0,0])
    return rows

def expected(c):
    initial=initialize_empty_profile139(ConstructorInput139(1,1,0,int(c['constructor_seed_u64']),0,c['flat_height_bits']));world=WorldQueries135((),None,None,None,FALLBACK_BITS,c['flat_height_bits'])
    words=tuple(c['rng_override'])if c['rng_override']is not None else initial.rng_words;counter=c['counter_override']if c['counter_override']is not None else 10
    vector=vector_from_hex139(56,c['pickup_backing'],0)if c['pickup_backing']else OpeningVector139(56,());packets=[];stages=[];cap=0
    def state():return dict(counter=counter,rng_words=list(words),pickup_capacity=vector.capacity,pickup_count=vector.count,storage=[list(row)for row in vector.storage],packet_capacity=cap,packets=list(packets),phase2587=0)
    def emit(actor):
        nonlocal cap
        if len(packets)==cap:cap=max(4,cap*2)
        packets.append([169,actor.payload169.hex()])
    if c['kind']=='actor':
        result=create_world_actor139(*c['descriptor'],tuple(c['xyz_bits']),c['kind21'],c['flags9'],counter,words);counter,words=result.counter,result.rng_words;emit(result.create);stages.append(dict(role=1886,returned_guid=str(result.create.guid),state=state()))
    elif c['kind']=='pickup':
        for op in c['ops']:
            result=append_kind2_pickup139(tuple(op['xyz_bits']),op['amount'],world,words,counter,now_bits=op['now_bits'],vector=vector);counter,words,vector=result.counter,result.rng_words,result.vector
            for actor in result.creates:emit(actor)
            stages.append(dict(role=1446,state=state()))
    else:
        for amount in(2,1):
            position=sample_random_position(WorldPositionInput139V2(0,initial.player_xyz,(0,0),0x41900000,0x42480000,0,words,None),world);words=tuple(position.rng_words);stages.append(dict(role=13563,position_bits=list(position.position_bits),state=state()))
            result=append_kind2_pickup139(position.position_bits,amount,world,words,counter,now_bits=c['now_bits'],vector=vector);counter,words,vector=result.counter,result.rng_words,result.vector
            for actor in result.creates:emit(actor)
            stages.append(dict(role=1446,state=state()))
    return dict(constructor_cells=list(canonical_game_cells139(initial)),constructor_rng_words=list(initial.rng_words),constructor_counter=10,selected40_hex=bytes(absent_companion_selection139(EmptyAccountSources139(0,0,0,0),bytes([0xa5])*40)).hex(),stages=stages)

def compare(c,a,counts,diffs):
    def eq(field,w,g):
        counts['assertions']+=1
        if w!=g:
            counts['differences']+=1
            if len(diffs)<80:diffs.append(dict(id=c['id'],group=c['group'],field=field,expected=w,actual=g))
    e=c['expected'];eq('selected40',e['selected40_hex'],a['selected40_hex']);eq('constructor RNG',e['constructor_rng_words'],a['constructor']['rng_words']);eq('constructor counter',10,a['constructor']['counter']);raw=bytes.fromhex(a['constructor']['raw_Game2592_hex'])
    for j,value in enumerate(e['constructor_cells']):
        if value is None:counts['constructor_unknown_cells_observed']+=1
        else:eq('constructor+'+str(j),value,raw[j]);counts['constructor_known_bytes']+=1
    assert all(a[k]for k in('account_unchanged','profile_unchanged','borrowed_flatquery_unchanged'))and a['selection_canaries']==['c3'*16,'d7'*16]
    previous=a['before'];pickup_op=0
    for i,(want,got)in enumerate(zip(e['stages'],a['stages'],strict=True)):
        label=f'stage{i}';eq(label+'.role',want['role'],got['role']);s=want['state'];g=got['state']
        for k in('returned_guid','position_bits'):
            if k in want:eq(label+'.'+k,want[k],got[k])
        for k in('counter','rng_words','phase2587'):eq(label+'.'+k,s[k],g[k])
        eq(label+'.pickup-cap',s['pickup_capacity'],g['pickups']['capacity']);eq(label+'.pickup-count',s['pickup_count'],g['pickups']['count']);eq(label+'.packet-cap',s['packet_capacity'],g['packets']['capacity']);eq(label+'.packets',s['packets'],[[r['opcode'],r['payload_hex']]for r in g['packets']['active']])
        for j,(row,physical)in enumerate(zip(s['storage'],g['pickups']['storage'],strict=True)):
            for k,(value,actual)in enumerate(zip(row,bytes.fromhex(physical),strict=True)):
                if value is None:counts['allocator_unwritten_pickup_cells_observed']+=1
                else:eq(f'{label}.pickup[{j}]+{k}',value,actual);counts['known_pickup_bytes']+=1
        before=bytearray.fromhex(previous['raw_Game2592_hex']);after=bytes.fromhex(g['raw_Game2592_hex'])
        if c['kind']=='pickup'and got['role']==1446:struct.pack_into('<I',before,2352,c['ops'][pickup_op]['now_bits']);pickup_op+=1
        for j,v in enumerate(s['rng_words']):struct.pack_into('<I',before,1720+4*j,v)
        for offset,value in((2408,s['counter']),(1868,s['pickup_capacity']),(1876,s['pickup_count']),(1880,s['packet_capacity']),(1888,len(s['packets']))):struct.pack_into('<I',before,offset,value)
        for header,ptr in(('pickups',1872),('packets',1884)):
            if g[header]['capacity']!=previous[header]['capacity']:before[ptr:ptr+4]=after[ptr:ptr+4];counts['observed_new_vector_pointer_words']+=1
        eq(label+'.relative-allGame2592',before.hex(),after.hex());counts['relative_Game_bytes']+=2592
        n=previous['packets']['count'];eq(label+'.packet-prefix-metadata',previous['packets']['metadata_backing_hex'][:32*n],g['packets']['metadata_backing_hex'][:32*n]);eq(label+'.packet-prefix-payloads',previous['packets']['active'],g['packets']['active'][:n]);previous=g;counts['stages']+=1;counts['target_'+str(got['role'])]+=1

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-aux139-flat-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest,trace=build(out)
    for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
    rows=corpus(args.phase=='pilot')
    for c in rows:c['expected']=expected(c)
    save(out/'fixtures.json',rows);save(out/'inputs.json',[{k:v for k,v in c.items()if k!='expected'}for c in rows]);save(out/'expected.json',[dict(id=c['id'],expected=c['expected'])for c in rows]);frozen={n:sha(out/n)for n in('fixtures.json','inputs.json','expected.json','manifest.json',manifest['module_file'])}
    assert before=={n:sha(ROOT/n)for n in files}and sha(NODE)==NODE_SHA
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_opening_aux139_flat_oracle.mjs'),str(out),str(out/'inputs.json')];save(out/'prepared.json',dict(expected_before_original=True,sources=before,source_import_edges=edges,artifacts=frozen,command=command,deadline_seconds=90));started=time.monotonic()
    with(out/'actual.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=90))
        try:code=child.wait(timeout=90)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-started,deadline_seconds=90,pid_missing=missing(),pgid_missing=missing(True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diffs=[]
    if code or len(actual)!=len(rows):save(out/'failure.json',dict(process=terminal,completed=len(actual),expected=len(rows)));print(json.dumps(dict(out=str(out.relative_to(ROOT)),status='failed_preserved',process=terminal,stderr=(out/'stderr.log').read_text()[-2000:])));raise SystemExit(1)
    for c,a in zip(rows,actual,strict=True):assert c['id']==a['id'];compare(c,a,counts,diffs)
    runtime=json.load(open(out/'runtime.json'));assert runtime['host_calls']==0 and all(runtime['full_calls'][str(i)]==counts['target_'+str(i)]for i in(1886,13563,1446));assert runtime['full_calls']['2945']==runtime['full_calls']['1600']==len(rows)
    assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}and sha(SOURCE)==SOURCE_SHA;save(out/'differences.json',diffs)
    receipt=dict(status='scoped_original_differential_passed'if not diffs else'differences_preserved',version='0.139.0',actual_build='f79c5e2b4',phase=args.phase,cases=len(rows),differences=counts['differences'],counts=dict(counts),groups=dict(Counter(c['group']for c in rows)),source_sha256_before=before,source_sha256_after=before,source_import_edges=edges,expected_before_original=True,original_input_contains_expected=False,original_sha256=SOURCE_SHA,frozen_artifacts=frozen,artifacts={n:sha(out/n)for n in('actual.jsonl','runtime.json','stderr.log','prepared.json','owned-terminal.json','differences.json','static/trace.json')},runtime=runtime,process=terminal,scope='Fresh2945→1600 setup with typedborrowedflatquery;full1886 actor and actual13563→1446 two-kind2 linked state/RNG/counter/record56/full169 bytes.',limitations=['Typedflatquery is not a natural Rc/world producer;current139 actual nonflat world composition remains separate.','Velocity0/pathNone are explicit inputs;no App/menu/accountStorage producer.','2945/1600 setup is not counted as new independent constructor/profile acceptance.','Mode0 kind2 count<5 only;other pickup kinds/cap replacement/deathcallbacks excluded.','Allocator-unwritten record56 cells stayNone;payload pointer/capacity observations are retained without claiming an allocator reconstruction.','Full1108/windows/special/boundaries and complete gameplay are not exercised here.'])
    save(out/'comparison.json',receipt);print(json.dumps(dict(out=str(out.relative_to(ROOT)),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),differences=counts['differences'],first_differences=diffs[:5],counts=dict(counts),process=terminal)))
    if diffs:raise SystemExit(1)
if __name__=='__main__':main()
