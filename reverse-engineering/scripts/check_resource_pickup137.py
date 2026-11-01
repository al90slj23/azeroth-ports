#!/usr/bin/env python3
"""Expected-first137 full1420 resource appends and complete169 payloads."""
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,ast,hashlib,json,os,random,re,signal,struct,subprocess,sys,time

sys.dont_write_bytecode=True
from build_resource_pickup137_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from production_closure135 import production_sources135
from ai_world135_inputs import ASSET_WORLD,HASHES,load_asset_world135,asset_world_description135,controlled_world135
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.opening_npc_pickups135 import OpeningVector135
from core_spec.initial_state135_data import ZONE_ENTRIES
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from core_spec.resource_pickup137 import ResourcePickupInput137,produce_resource_pickup137,PendingResourcePickup137

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def verify_local_source_closure(files):
    """Require every explicit local Python/JS import, including fixture data.

    The production closure alone does not include checker-only corpus inputs.
    Reject an incomplete declared closure before generating any expectations.
    """
    declared=set(files);edges=set()
    for name in files:
        path=ROOT/name
        if path.suffix=='.mjs':
            for relative in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",path.read_text()):
                dependency=str((path.parent/relative).resolve().relative_to(ROOT))
                assert dependency in declared,(name,dependency)
                edges.add((name,dependency))
            continue
        if path.suffix!='.py':continue
        parts=Path(name).with_suffix('').parts
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[]
            if isinstance(node,ast.Import):modules=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    assert parts[0]=='reconstruction','Unhandled relative script import'
                    prefix=list(parts[1:-node.level]);module='.'.join(prefix+([node.module]if node.module else[]))
                else:module=node.module or''
                modules=[module]+[module+'.'+a.name if module else a.name for a in node.names]
            for module in modules:
                if not module:continue
                rel=Path(*module.split('.'))
                for folder in('scripts','reconstruction'):
                    source=ROOT/folder/rel.with_suffix('.py');package=ROOT/folder/rel/'__init__.py'
                    dependency=source if source.is_file()else package if package.is_file()else None
                    if dependency is None:continue
                    key=str(dependency.relative_to(ROOT));assert key in declared,(name,key)
                    edges.add((name,key))
                    for parent in dependency.parents:
                        if parent==ROOT/folder:break
                        initializer=parent/'__init__.py'
                        if initializer.is_file():
                            key=str(initializer.relative_to(ROOT));assert key in declared,(name,key)
                            edges.add((name,key))
    return [list(row)for row in sorted(edges)]


def vector(variant):
    count,capacity=((0,0),(3,3),(1,4),(0,4),(4,4),(1,1))[variant%6]
    rows=[]
    for i in range(capacity):
        row=list(bytes((i*31+j*17+37)&255 for j in range(56)))
        if i<count:
            row[:4]=struct.pack('<I',99 if i&1 else 0)
            row[8:12]=struct.pack('<I',(3,4,5,2)[i%4])
        if variant&1:row[4:8]=[None,row[5],None,row[7]]
        rows.append(tuple(row))
    return OpeningVector135(56,tuple(rows),count)


def controlled(flat=42,primary=None):
    return dict(kind='controlled_query_world',nav=None,primary=primary,
        fallback_height_bits=f.from_float(-17),flat_height_bits=None if flat is None else f.from_float(flat))


def corpus(full):
    cases,expected,labels=[],[],[]
    world=load_asset_world135();world_desc=asset_world_description135()
    def add(group,zone,kind,xyz,vec,description,provider,*,amount=1,counter=85):
        i=len(cases);rng=random.Random(0x1371420+i)
        words=(0,0,0,0)if i%17==0 else tuple(rng.getrandbits(32)for _ in range(4))
        value=ResourcePickupInput137(zone,kind,amount,xyz,f.from_float(40.0+i/8),words,counter,vec)
        result=produce_resource_pickup137(value,provider)
        state=asdict(value);state['pickups']=dict(count=vec.count,storage=vec.storage)
        cases.append(dict(id=i,input=state,map_id_utf8=ZONE_ENTRIES[zone][0],world=description,
            unknown_poison=(0xa5,0x5a)[i&1],message_sequence=(0xffffffff if i%11==0 else 1)))
        expected.append(dict(id=i,result=dict(pickups=dict(capacity=result.pickups.capacity,count=result.pickups.count,storage=result.pickups.storage),
            rng_words=result.rng_words,counter=result.counter,message_sequence=cases[-1]['message_sequence'],
            packets=[dict(opcode=169,payload_hex=x.payload169_hex)for x in result.creates],notifications_count=0)))
        labels.append(dict(id=i,group=group,zone=zone,kind=kind,clamped=result.clamped,draws=result.draws,
            final_position_bits=result.position_bits,input_capacity=vec.capacity,output_capacity=result.pickups.capacity,
            source_world_identity='135 independent query artifacts supplied as137 controlled function input'if provider is world else'explicit synthetic query fixture'))
    for zone in range(12 if full else 1):
        cx,cy,radius=ZONE_GEOMETRY[zone]
        desc=controlled(42-zone);provider=controlled_world135(desc)
        for kind in (3,4,5):
            for outside in ((False,True)if full else(False,)):
                xyz=(f.add(cx,f.from_float(1200))if outside else cx,
                    f.add(cy,f.from_float(-900))if outside else cy,f.from_float(1234))
                i=len(cases);add('all12-zones-flat-world-outside-clamp'if outside else'all12-zones-flat-world-centre',zone,kind,xyz,vector(i),desc,provider,
                    amount=(0,1,0xffffffff,0xdeadbeef)[i%4],counter=(0xffffffff if i%13==0 else 85+i))
    # These are explicit reusable query inputs, not a claim of137 resource boot.
    cx,cy,_=ZONE_GEOMETRY[0]
    actual_positions=((f.from_float(-8949.95),f.from_float(-132.49),0),
        (cx,cy,0),(f.add(cx,f.from_float(1200)),f.add(cy,f.from_float(-900)),0),
        (f.add(cx,f.from_float(40)),f.add(cy,f.from_float(25)),0))
    for j in range(12 if full else 3):
        add('independent451-query-world-input',0,3+j%3,actual_positions[j%4],vector(j),world_desc,world,
            amount=(0,1,0xffffffff,0xdeadbeef)[j%4],counter=0xffffffff if j==5 else 200+j)
    if full:
        origin=(f.sub(cx,f.from_float(2)),f.sub(cy,f.from_float(2)))
        for nearest in (False,True):
            heights=[f.from_float(63)]*64 if not nearest else[0x7fc00000]*64
            if nearest:heights[3+3*8]=f.from_float(67)
            desc=controlled(None,dict(values_bits=heights,origin_xy_bits=list(origin),width=8));provider=controlled_world135(desc)
            for kind in (3,4,5):
                add('explicit-primary-nearest-success'if nearest else'explicit-primary-direct-height',0,kind,(cx,cy,0),vector(kind),desc,provider,amount=0x89abcdef,counter=300+kind)
    return cases,expected,labels


def compare(expected,actual):
    counts=Counter();errors=[]
    def walk(want,got,path):
        if want is None:
            assert re.fullmatch(r'case\d+\.pickups\.storage\[\d+\]\[\d+\]',path),path
            assert type(got)is int and 0<=got<=255;counts['explicit_unknown_cells']+=1
        elif isinstance(want,dict):
            if not isinstance(got,dict)or set(want)!=set(got):errors.append(dict(path=path,expected_keys=list(want),actual_keys=list(got)));return
            for key in want:walk(want[key],got[key],path+'.'+key)
        elif isinstance(want,(tuple,list)):
            if not isinstance(got,(tuple,list))or len(want)!=len(got):errors.append(dict(path=path,expected_length=len(want),actual_length=len(got)));return
            for i,(a,b)in enumerate(zip(want,got)):walk(a,b,path+'['+str(i)+']')
        else:
            counts['compared_known_values']+=1
            if type(want)is not type(got)or want!=got:errors.append(dict(path=path,expected=want,actual=got))
    assert len(expected)==len(actual)
    for want,raw in zip(expected,actual):
        assert raw['id']==want['id'];result=raw['result']
        result['pickups']['storage']=[list(bytes.fromhex(row))for row in result['pickups']['storage']]
        walk(want['result'],result,'case'+str(want['id']))
        before=bytes.fromhex(raw['game_before8192_hex']);after=bytes.fromhex(raw['game_after8192_hex']);assert len(before)==len(after)==8192
        admitted=set(range(1720,1736))|set(range(1868,1892))|set(range(2408,2412))
        changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b]
        unexpected=[i for i in changed if i not in admitted]
        if unexpected:errors.append(dict(path='case'+str(want['id'])+'.game_outside_admitted_ranges',offsets=unexpected))
        counts['unchanged_game_bytes_outside_admitted_ranges']+=8192-len(admitted)
        counts['observed_changed_game_bytes']+=len(changed)
        counts['packets']+=len(want['result']['packets']);counts['packet_bytes']+=sum(len(p['payload_hex'])//2 for p in want['result']['packets'])
    return errors,counts


def refusals(cases):
    c=cases[0];s=c['input'];value=ResourcePickupInput137(**{**s,'pickups':OpeningVector135(56,tuple(tuple(r)for r in s['pickups']['storage']),s['pickups']['count'])})
    provider=controlled_world135(c['world']);answers=[]
    for name,v,w in(('unsupported-kind',replace(value,kind=2),provider),('absent-world',value,None)):
        try:produce_resource_pickup137(v,w)
        except PendingResourcePickup137:answers.append(name)
        else:raise AssertionError(name)
    cx,cy,_=ZONE_GEOMETRY[0];desc=controlled(None,dict(values_bits=[0x7fc00000]*4,origin_xy_bits=[cx,cy],width=2))
    try:produce_resource_pickup137(replace(value,position_bits=(cx,cy,0)),controlled_world135(desc))
    except PendingResourcePickup137:answers.append('primary-present-nearest-miss-remains-pending')
    else:raise AssertionError('Unrecovered low-address read accepted')
    return answers


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    files=tuple('scripts/'+s for s in ('check_resource_pickup137.py','build_resource_pickup137_oracle.py','run_resource_pickup137_oracle.mjs',
        'ai_world135_inputs.py','ai_world135_packing.mjs','production_closure135.py','build_combat137_oracle.py','wasm137_profile.py','wasm134_profile.py','wasm_index.py'))+production_sources135(ROOT,'core_spec.resource_pickup137','resource_spec.world_query135','core_spec.initial_state135_data')
    local_import_edges=verify_local_source_closure(files)
    before={n:sha(ROOT/n)for n in files}
    world_inputs={str(ASSET_WORLD/n):h for n,h in HASHES.items()}
    world_inputs[str(ASSET_WORLD/'receipt.json')]=sha(ASSET_WORLD/'receipt.json')
    cases,expected,labels=corpus(args.phase=='full');refused=refusals(cases)
    assert before=={n:sha(ROOT/n)for n in files}
    assert all(sha(Path(n))==h for n,h in world_inputs.items())
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('resource-pickup0137-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    assert manifest['zone_geometry137']==[list(r)for r in ZONE_GEOMETRY]
    for n,digest in before.items():
        p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==digest
    for n,v in(('input.json',cases),('expected.json',expected),('labels.json',labels),('refusals.json',refused)):save(out/n,v)
    assert all((out/n).stat().st_size<=4194304 for n in('input.json','expected.json'))
    artifacts={n:sha(out/n)for n in('input.json','expected.json','labels.json','refusals.json','manifest.json',manifest['module_file'],'1420.wat')}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_resource_pickup137_oracle.mjs'),str(out),str(out/'input.json')]
    save(out/'prepared.json',dict(source_sha256=before,artifacts=artifacts,world_inputs=world_inputs,cases=len(cases),command=command,expected_before_original=True,deadline_seconds=60,local_source_import_edges=local_import_edges))
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    began=time.monotonic();error=None
    def interrupted(sig,frame):raise KeyboardInterrupt('Owned137 resource signal '+str(sig))
    previous=signal.signal(signal.SIGTERM,interrupted)
    with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as e:error=repr(e)
        finally:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM,previous)
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,error=error)
    save(out/'process-terminal.json',terminal);errors=[];counts=Counter();runtime=None
    if child.returncode==0:
        assert(out/'stdout.jsonl').stat().st_size<=8*1024*1024
        actual=[json.loads(line)for line in(out/'stdout.jsonl').read_text().splitlines()];errors,counts=compare(expected,actual)
        runtime=json.loads((out/'resource-pickup137-runtime.json').read_text());assert runtime['fresh_instances']==len(cases)and runtime['actual_host_calls']==0 and runtime['stack_all_restored']
    save(out/'differences.json',errors);after={n:sha(ROOT/n)for n in files}
    report=dict(version='0.137.0',actual_build='d171b8f9f',original_sha256=SOURCE_SHA,cases=len(cases),differences=len(errors),comparison=dict(counts),groups=dict(Counter(r['group']for r in labels)),
        expected_before_original=True,source_files=len(files),source_sha256_before=before,source_sha256_after=after,source_unchanged=before==after,local_source_import_edges=local_import_edges,
        frozen_artifacts=artifacts,artifacts_unchanged=all(sha(out/n)==h for n,h in artifacts.items()),world_inputs=world_inputs,world_unchanged=all(sha(Path(n))==h for n,h in world_inputs.items()),
        pure_model_refusals=refused,process=terminal,runtime=runtime,
        scope='Full1420 kinds3..5 append, complete56B backing, shared RNG/counter, exact169 packets; explicit independent or synthetic query fixtures',
        game_preservation='All8192 fixture Game bytes outside RNG1720:1736, pickup-vector1868:1880, output-packet-vector1880:1892, counter2408:2412 unchanged',
        input_limitations=['Synthetic Game8192 fixture, not original Game constructor','World124 manually packed query-equivalent fixture, not original World constructor',
            '451 asset query artifacts retain135 provenance; supplied as137 controlled inputs, not latest137 asset boot'],
        full947_calls=0,full880_frames=0,native_windows_execution=False,complete_games=0,
        pending=['Resource947 scheduler/ordinary432 domain integration','Resource collection/effects','Primary-present nearest-miss low-address read','137 full world/boot/game/UI/network'],
        artifacts={n:sha(out/n)for n in('stdout.jsonl','stderr.log','differences.json','prepared.json')})
    save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),cases=len(cases),differences=len(errors),first_errors=errors[:8],process=terminal,receipt_sha256=sha(out/'comparison.json'))))
    if child.returncode or error or errors or not terminal['pid_missing']or not terminal['pgid_missing']or not report['source_unchanged']or not report['artifacts_unchanged']or not report['world_unchanged']:raise SystemExit(1)


if __name__=='__main__':main()
