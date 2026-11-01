#!/usr/bin/env python3
"""Expected-first1744/1821 components over a genuine restored world snapshot."""
from pathlib import Path
from dataclasses import asdict
from collections import Counter
import argparse,json,os,signal,struct,subprocess,sys,time
from build_world_snapshot135_oracle import build_snapshot135,ROOT,SOURCE,SOURCE_SHA
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
sys.dont_write_bytecode=True
FILES=tuple(dict.fromkeys(('scripts/check_opening_entities135.py','scripts/run_opening_entities135_oracle.mjs',
 'scripts/build_world_snapshot135_oracle.py','scripts/world_snapshot135_host.mjs','scripts/build_full135_oracle.py',
 'scripts/build_upgrade134_oracle.py','scripts/source_closure135.py')+core_sources(ROOT,'opening_entities135.py')+
 tuple('reconstruction/resource_spec/'+x+'.py'for x in('__init__','world_query135','terrain135','entry_resources135','dbc'))))
IMPORTED={p:sha(ROOT/p)for p in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.opening_entities135 import(CompanionSlot135,create_companions,create_world_actor,vector_from_hex)
from resource_spec.world_query135 import decode_world_snapshot
SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_world6730.memory'
SNAPSHOT_SHA='f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
G=14554176;WORLD=26204808
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
INPUT_KEYS=('id','kind','input','ops')


def expected(case,world):
    s=case['input'];counter=s['counter'];words=tuple(s['rng_words']);packets=[];returns=[];stages=[]
    vector=vector_from_hex(88,s.get('prior_storage',[]),s.get('prior_count',0))
    for op in case['ops']:
        if case['kind']=='companions':
            slots=tuple(CompanionSlot135(p['token'],tag,p['entry'],p['display'],p['scale_bits'])for p,tag in zip(s['prototypes'],op['tags']))
            value=create_companions(slots,tuple(op['player_xyz']),op['heading'],op['now_bits'],op['stat1556_bits'],op['rank273'],counter,world,vector,s['protection2576'])
            vector,counter=value.vector,value.counter;packets.extend(dict(opcode=169,payload_hex=x.payload169_hex)for x in value.creates)
            stages.append(dict(counter=counter,rng_words=list(words),companion_count=vector.count,companion_capacity=vector.capacity,
                companion_storage=[list(row)for row in vector.storage],packets=list(packets)))
        else:
            value=create_world_actor(op['entry'],op['display'],op['scale_bits'],tuple(op['xyz']),op['kind21'],op['flags9'],counter,words)
            counter,words=value.counter,value.rng_words;returns.append(str(value.create.guid));packets.append(dict(opcode=169,payload_hex=value.create.payload169_hex))
            stages.append(dict(counter=counter,rng_words=list(words),return_guids=list(returns),packets=list(packets)))
    return stages


def corpus(world,pilot):
    b=f.from_float;rows=[];origin=(3323121664,3290316800,1116212265);rng=(3713081075,3463651554,2696601855,1334331845)
    null=dict(token=0,entry=0,display=0,scale_bits=0)
    proto=(dict(token=0x10000000,entry=42,display=26,scale_bits=b(.8)),dict(token=0x10000001,entry=9001,display=4831,scale_bits=b(1.3)))
    def add(kind,s,ops):
        c=dict(id=len(rows),kind=kind,input=s,ops=ops);c['expected']=expected(c,world);rows.append(c)
    def companions(tags=(0,0),custom=False,capacity=0,count=0,counter=10,protection=0,rank=0,stat=1,heading=.4,repeats=1):
        storage=[bytes([17+j%229])*88 for j in range(capacity)]
        s=dict(counter=counter,rng_words=rng,prior_storage=[x.hex()for x in storage],prior_count=count,prototypes=proto if custom else(null,null),protection2576=protection)
        ops=[dict(tags=tags,player_xyz=origin,heading=b(heading),now_bits=b(i*.5),rank273=rank,stat1556_bits=b(stat))for i in range(repeats)]
        add('companions',s,ops)
    def actor(entry=9013,display=4831,scale=1,counter=18,words=rng,kind=5,flags=16,repeats=1):
        s=dict(counter=counter,rng_words=words)
        add('world_actor',s,[dict(entry=entry,display=display,scale_bits=b(scale),xyz=(b(-9396+i),b(-633+i/2),b(68+i/8)),kind21=kind,flags9=flags)for i in range(repeats)])
    companions();companions(custom=True,capacity=4,count=3,rank=7);actor();actor(counter=0xfffffffe,repeats=3)
    if not pilot:
        for tags in((255,255),(0,255),(255,0),(254,1)):companions(tags,custom=True)
        for capacity,count in((1,0),(1,1),(3,3),(4,0),(4,2),(4,4),(8,7)):companions(custom=True,capacity=capacity,count=count,repeats=2)
        for rank,stat in((0,.3),(1,1),(255,2.5)):companions(custom=True,rank=rank,stat=stat,heading=7.0)
        companions(custom=True,protection=1,capacity=4,count=2);companions(custom=True,counter=0xffffffff)
        for entry,display,scale in((0,0,0),(9005,259,.7),(0xffffffff,0xffffffff,3)):actor(entry,display,scale,repeats=2)
        for words in((0,0,0,0),(1,2,3,4),(0xffffffff,)*4):actor(words=words,kind=0,flags=0,repeats=4)
        actor(repeats=69)
    return json.loads(json.dumps(rows,allow_nan=False))


def compare(want,actual,counters,failures,path):
    for key,value in want.items():
        if key=='companion_storage':
            assert len(value)==len(actual[key])
            for j,(row,rawhex)in enumerate(zip(value,actual[key])):
                raw=bytes.fromhex(rawhex);assert len(raw)==88
                for o,(w,a)in enumerate(zip(row,raw)):
                    if w is None:
                        counters['unknown_unwritten_bytes']+=1;counters['unknown_nonzero_bytes']+=bool(a)
                    else:
                        counters['strict_record_bytes']+=1
                        if w!=a:failures.append(dict(field=f'{path}.row{j}+{o}',want=w,actual=a))
        elif value!=actual[key]:failures.append(dict(field=path+'.'+key,want=value,actual=actual[key]))
    counters['stages']+=1;counters['packet_observation_bytes']+=sum(len(p['payload_hex'])//2 for p in actual['packets'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in FILES};assert before==IMPORTED
    assert sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
    world=decode_world_snapshot(SNAPSHOT.read_bytes(),WORLD);cases=corpus(world,args.phase=='pilot')
    out,manifest=build_snapshot135(['companions','world_actor']);snap=out/'source-snapshot'
    for name,digest in before.items():q=snap/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/name).read_bytes());assert sha(q)==digest
    fixture=out/'opening-entities135-fixtures.json';fixture.write_text(json.dumps(cases,separators=(',',':'))+'\n')
    inputs=out/'opening-entities135-inputs.json';inputs.write_text(json.dumps([{k:c[k]for k in INPUT_KEYS}for c in cases],separators=(',',':'))+'\n')
    config=out/'opening-entities135-config.json';config.write_text(json.dumps(dict(snapshot=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,G=G,inputs=str(inputs)),indent=2)+'\n')
    frozen={q.name:sha(q)for q in(fixture,inputs,config,out/'manifest.json',out/manifest['module_file'])}
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_opening_entities135_oracle.mjs'),str(out),str(config)]
    results=out/'opening-entities135-results.jsonl';err=out/'opening-entities135-stderr.log';started=time.monotonic()
    with results.open('w')as stream,err.open('w')as errors:
        child=subprocess.Popen(command,stdout=stream,stderr=errors,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError(f'Owned60s deadline:{out}')
    if code:raise RuntimeError(f'Original exit{code}:{out}')
    counters=Counter();failures=[]
    with results.open()as stream:
        for case in cases:
            actual=json.loads(next(stream));assert actual['id']==case['id']and len(actual['stages'])==len(case['expected'])
            for j,(w,a)in enumerate(zip(case['expected'],actual['stages'])):compare(w,a,counters,failures,f'case{case["id"]}.stage{j}')
        assert not stream.read().strip()
    mismatches=out/'opening-entities135-mismatches.json';mismatches.write_text(json.dumps(failures,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA
    assert frozen=={q.name:sha(q)for q in(fixture,inputs,config,out/'manifest.json',out/manifest['module_file'])}
    runtime=out/'opening-entities135-runtime.json'
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,kind='snapshot-derived-full1744-1821-component-differential',cases=len(cases),stages=counters['stages'],differences=len(failures),comparison=dict(counters),
        snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,snapshot_bytes=SNAPSHOT.stat().st_size,source_sha256_before=before,source_sha256_after=after,
        expected_before_original=True,input_contains_expected=False,original_input_keys=list(INPUT_KEYS),source_snapshots=True,
        process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-started),
        runtime=json.loads(runtime.read_text()),artifacts={q.name:sha(q)for q in(fixture,inputs,config,results,err,mismatches,runtime,out/'manifest.json',out/manifest['module_file'])},
        limitations=['Full1744 and1821 only;inline1089 special40/windows8/boundary geometry require completeopening differential separately.',
            'Snapshot-derived realworld consumer;not independentworld producer/freshbootstrap.Originalfullmemory restored, no Once/Rc state forged.',
            'Companion definition pointer normalization onlyfor explicitfixture prototypes, fullrawbacking/maps retained;unwritten11Bpernew88slot preserved orunknown.',
            'All169 activepayload bytes compared;metadata physicalallocation/retainedfullG are observations,not wholeGame equivalence.',
            'Defaultmode/explicitprofile/realworldpositiondomain;realmenu,sourceproducer,multiplayer,full880/fullgame remainincomplete.'])
    target=out/'opening-entities135-comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),receipt_sha256=sha(target),cases=len(cases),stages=counters['stages'],differences=len(failures),failures=failures[:3]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
