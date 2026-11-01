#!/usr/bin/env python3
"""Expected-first complete opening differential over a genuine resolved world."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
from build_world_snapshot135_oracle import build_snapshot135,ROOT,SOURCE,SOURCE_SHA
from build_upgrade134_oracle import sha
from source_closure135 import core_sources

sys.dont_write_bytecode=True
FILES=tuple(dict.fromkeys(('scripts/check_opening135.py','scripts/run_opening135_oracle.mjs',
 'scripts/build_world_snapshot135_oracle.py','scripts/world_snapshot135_host.mjs',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/source_closure135.py')+
 core_sources(ROOT,'opening135.py')+tuple('reconstruction/resource_spec/'+x+'.py'for x in('__init__','world_query135','terrain135','entry_resources135','dbc'))))
IMPORTED={p:sha(ROOT/p)for p in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.opening135 import EmptyOpeningInput135,initialize_empty_opening,projection
from resource_spec.world_query135 import decode_world_snapshot

SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
MODEL_SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_world6730.memory'
MODEL_SNAPSHOT_SHA='f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
APP,WORLD=14549000,26204808
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
VECTOR_STRIDES={'companions':88,'units':424,'pickups':56,'special':40,'windows':8,'boundaries':8}
UNWRITTEN={'companions':set(range(8,16))|set(range(21,24)),
 'units':set(range(424))-set(range(0,4))-set(range(8,12))-set(range(16,20))-set(range(40,44))-set(range(64,68))-set(range(112,248))-set(range(280,419)),
 'pickups':set(range(4,8)),'special':set(range(8,16))|set(range(36,40)),'windows':set(),'boundaries':set()}
INPUT_KEYS=('id','input')


def corpus(world,pilot):
    rows=[]
    def add(cls,race,seed,guid,group):
        state=EmptyOpeningInput135(cls,race,0,seed,guid)
        result=initialize_empty_opening(state,world,title_utf8=b'Elwynn Forest',subtitle_utf8='The Defias Uprising — survive the onslaught!'.encode())
        value=asdict(state);value['app_lcg_seed_u64']=str(seed);value['object_id_u64']=str(guid)
        rows.append(dict(id=len(rows),input=value,group=group,expected=projection(result),
            diagnostic=dict(constructor_seed_u64=str(result.constructor_seed_u64),position_draws=result.position_draws,actor_draws=result.actor_draws,window_draws=result.window_draws)))
    add(1,1,0,0,'default-eight-seeds');add(8,1,1,42,'class-race-guid-matrix')
    if not pilot:
        for seed in(1,2,3,7,31,255,0x123456789abcdef):add(1,1,seed,0,'default-eight-seeds')
        for args in((2,3,2,0x100000000),(3,4,7,0xffffffffffffffff),(4,5,3,0x100000001),
            (7,6,31,0x123456789abcdef0),(9,8,255,42),(11,7,0x123456789abcdef,0x7fffffffffffffff),(5,2,0,0xffff000000000001)):
            add(*args,'class-race-guid-matrix')
    return json.loads(json.dumps(rows,allow_nan=False))


def compare(case,actual,counters,failures):
    want=case['expected'];observed=actual['projection'];path=f'case{case["id"]}'
    assert set(want)==set(observed)
    for name,stride in VECTOR_STRIDES.items():
        w,a=want[name],observed[name]
        for key in('count','capacity'):
            if w[key]!=a[key]:failures.append(dict(field=f'{path}.{name}.{key}',expected=w[key],actual=a[key]))
        if len(w['storage'])!=len(a['storage']):continue
        for i,(row,rawhex)in enumerate(zip(w['storage'],a['storage'])):
            raw=bytes.fromhex(rawhex);assert len(row)==len(raw)==stride
            for offset,(wb,ab)in enumerate(zip(row,raw)):
                if wb is None:
                    assert i>=w['count']or offset in UNWRITTEN[name],(name,i,offset)
                    label='active_unwritten'if i<w['count']else'inactive_allocator'
                    counters[label+'_bytes']+=1;counters[label+'_nonzero_bytes']+=bool(ab)
                else:
                    counters['strict_backing_bytes']+=1
                    if i<w['count']:counters['strict_active_bytes']+=1
                    if wb!=ab:failures.append(dict(field=f'{path}.{name}.row{i}+{offset}',expected=wb,actual=ab))
    for key in want:
        if key not in VECTOR_STRIDES and want[key]!=observed[key]:
            if key=='packets':
                if len(want[key])!=len(observed[key]):failures.append(dict(field=path+'.packets.count',expected=len(want[key]),actual=len(observed[key])))
                for i,(w,a)in enumerate(zip(want[key],observed[key])):
                    if w!=a:failures.append(dict(field=f'{path}.packet{i}',expected=w,actual=a))
            else:failures.append(dict(field=path+'.'+key,expected=want[key],actual=observed[key]))
    if actual['raw']['final']['app_lcg_seed_u64']!=case['diagnostic']['constructor_seed_u64']:
        failures.append(dict(field=path+'.app_lcg_seed',expected=case['diagnostic']['constructor_seed_u64'],actual=actual['raw']['final']['app_lcg_seed_u64']))
    counters['opening_packets']+=len(observed['packets']);counters['opening_packet_bytes']+=sum(len(x['payload_hex'])//2 for x in observed['packets'])
    counters['notifications']+=len(observed['notifications_utf8_hex']);counters['constructor_prefix_packets']+=len(actual['constructor_prefix']['packets'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORTED
    assert sha(SNAPSHOT)==SNAPSHOT_SHA and sha(MODEL_SNAPSHOT)==MODEL_SNAPSHOT_SHA and sha(NODE)==NODE_SHA
    world=decode_world_snapshot(MODEL_SNAPSHOT.read_bytes(),WORLD);rows=corpus(world,args.phase=='pilot')
    out,manifest=build_snapshot135(['cached_construct','begin_run'])
    fixture=out/'opening135-fixtures.json';fixture.write_text(json.dumps(rows,separators=(',',':'))+'\n')
    inputs=out/'opening135-inputs.json';inputs.write_text(json.dumps([{k:c[k]for k in INPUT_KEYS}for c in rows],separators=(',',':'))+'\n')
    config=out/'opening135-config.json';config.write_text(json.dumps(dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,
        model_snapshot_sha256=MODEL_SNAPSHOT_SHA,app_pointer=APP,world_pointer=WORLD,input_path=str(inputs),input_sha256=sha(inputs)),indent=2)+'\n')
    for name,h in before.items():
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
    frozen={p.name:sha(p)for p in(fixture,inputs,config,out/'manifest.json',out/manifest['module_file'])}
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_opening135_oracle.mjs'),str(out),str(config)]
    results=out/'opening135-results.jsonl';stderr=out/'opening135-stderr.log';started=time.monotonic();timed_out=False
    with results.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(child.pid,signal.SIGKILL);code=child.wait()
    actual=[json.loads(line)for line in results.read_text().splitlines()];failures=[];counters=Counter()
    if code!=0 or timed_out:failures.append(dict(field='original_process',exit_code=code,timed_out=timed_out))
    if len(actual)!=len(rows):failures.append(dict(field='result_case_count',expected=len(rows),actual=len(actual)))
    for case,value in zip(rows,actual):assert case['id']==value['id'];compare(case,value,counters,failures)
    mismatch=out/'opening135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(MODEL_SNAPSHOT)==MODEL_SNAPSHOT_SHA
    assert frozen=={p.name:sha(p)for p in(fixture,inputs,config,out/'manifest.json',out/manifest['module_file'])}
    runtime=out/'opening135-runtime.json'
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,kind='complete-opening-over-resolved-realworld-input',cases=len(rows),completed_cases=len(actual),differences=len(failures),comparison=dict(counters),groups=dict(Counter(c['group']for c in rows)),
        source_sha256_before=before,source_sha256_after=after,source_closure_count=len(before),source_snapshots=True,original_sha256=SOURCE_SHA,
        original_snapshot=dict(path=str(SNAPSHOT),sha256=SNAPSHOT_SHA,bytes=SNAPSHOT.stat().st_size),model_world_snapshot=dict(path=str(MODEL_SNAPSHOT),sha256=MODEL_SNAPSHOT_SHA,bytes=MODEL_SNAPSHOT.stat().st_size),
        expected_before_original=True,expected_in_original_input=False,input_exact_keys=list(INPUT_KEYS),original_input_fields=list(rows[0]['input']),
        artifacts={p.name:sha(p)for p in(fixture,inputs,config,results,stderr,mismatch,out/'manifest.json',out/manifest['module_file'])if p.exists()},
        runtime=json.loads(runtime.read_text())if runtime.exists()else None,
        process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,timed_out=timed_out,deadline_seconds=60,seconds=time.monotonic()-started),
        limitations=['Full6730 cached construction then complete1089 with all callees retained; originalworld already resolved and supplied, not independently produced.',
            'Zero freshbootstraps and zero additional mainloop frames. No full880, saves, UI, multiplayer or independentcompletegame claim.',
            'Emptyselectedprofile/mode0/protection0/Elwynn/English only; other equipment, talents, regions, modes and locales remain separate.',
            'Six vector fullbacking: knownbytes strict; None only statically unwritten active offsets or freshallocator inactive slots; allrawbytes retained.',
            'Constructor queue prefixes retained separately; only appended opening169/150 and start JSON are modeled here.',
            'Rawcomplete2592G/5168App/124worldRc and completequeue metadata/payloadbacking are observations; unprojectedbytes are not asserted cosmetic or equal.'])
    if runtime.exists():receipt['artifacts'][runtime.name]=sha(runtime)
    target=out/'opening135-comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),receipt_sha256=sha(target),cases=len(rows),completed_cases=len(actual),differences=len(failures),source_files=len(before),first_failures=failures[:3]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
