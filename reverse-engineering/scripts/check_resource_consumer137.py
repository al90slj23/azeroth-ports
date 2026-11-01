#!/usr/bin/env python3
"""Expected-first full13710291 effect projection; no original callee bypass."""
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,os,re,signal,struct,subprocess,sys,time

sys.dont_write_bytecode=True
from build_resource_consumer137_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.derived_stats135 import StatsInput,recalculate
from core_spec.resource_consumer137 import (LiveVector137,ResourceConsumerState137,consume_resource137,
    ResourceCollectionInput137,collect_resources137,PendingResourceConsumer137)
from core_spec.opening_npc_pickups135 import OpeningVector135

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def live_vector(spells=(),capacity=0,unknown=True):
    capacity=max(capacity,len(spells));rows=[]
    for i in range(capacity):
        row=list(bytes((i*31+j*17+37)&255 for j in range(32)))
        if i<len(spells):
            spell,expiry=spells[i]
            for offset,value in((0,123 if i&1 else 0),(4,42 if i&1 else 0),(8,0),(20,spell),(24,f.from_float(expiry)),(28,0)):
                row[offset:offset+4]=struct.pack('<I',value)
        if unknown:row[12:20]=[None,row[13],None,row[15],row[16],None,row[18],None]
        rows.append(tuple(row))
    return LiveVector137(tuple(rows),len(spells))


def state(*,cls=1,race=1,level=1,now=10,hp_fraction=.25,heal_gate=0,live=None):
    stats=StatsInput(class_byte=cls,race_byte=race,level=level,now_bits=f.from_float(now))
    initial=recalculate(stats);derived={int(k):v for k,v in initial['derived_bits'].items()};maximum=derived[1536]
    current=f.mul(maximum,f.from_float(hp_fraction))
    stats=replace(stats,old_max_hp_bits=maximum,current_hp_bits=current,previous_speed_bits=initial['speed_bits'])
    fields={22:max(0,int(-(-f.to_float(current)//1))),28:max(0,int(-(-f.to_float(maximum)//1))),1109:initial['object_fields']['1109']}
    return ResourceConsumerState137(stats,tuple(sorted(derived.items())),tuple(sorted(fields.items())),
        live or live_vector(),heal_gate,(1,2,3,4),85,123,9)


def known(s,pickups=None,destroy=()):
    t=s.stats
    pickups=pickups if pickups is not None else OpeningVector135(56,())
    return dict(live=dict(capacity=s.live.capacity,count=s.live.count,storage=s.live.storage),
        pickups=dict(capacity=pickups.capacity,count=pickups.count,storage=pickups.storage),destroy170_hex=destroy,
        derived_bits={str(k):v for k,v in s.derived_bits},current_hp_bits=t.current_hp_bits,speed_bits=t.previous_speed_bits,
        auxiliary_bits={'1444':t.pool1532_bits,'1448':t.pool1536_bits,'1348':t.conditional1348_bits,'764':t.pool768_bits},
        player_fields={str(k):v for k,v in s.player_fields if k in(22,28,1109)},rng_words=s.rng_words,counter2408=s.counter2408,
        message_sequence2412=s.message_sequence2412,action_sequence1644=s.action_sequence1644)


def corpus(full):
    rows,expected,labels=[],[],[]
    def add(group,s,kinds):
        original=s;ops=[];answers=[];metadata=[]
        for j,kind in enumerate(kinds):
            now=f.add(original.stats.now_bits,f.from_float(j*.25));s=replace(s,stats=replace(s.stats,now_bits=now))
            result=consume_resource137(s,kind);s=result.state;ops.append(dict(operation='effect',kind=kind,now_bits=now));answers.append(known(s))
            metadata.append(dict(kind=kind,spell=result.spell_id,removed=result.removed_live_count,heal_request_bits=result.heal_request_bits,heal_delta_bits=result.heal_delta_bits,pending=result.pending))
        i=len(rows);rows.append(dict(id=i,state=asdict(original),operations=ops,player_guid='42',unknown_poison=(0xa5,0x5a)[i&1]));expected.append(dict(id=i,stages=answers));labels.append(dict(id=i,group=group,operations=metadata))
    def add_collect(group,s,specs,*,repeat=1):
        original=s;storage=[]
        for i,spec in enumerate(specs):
            kind,marker,x,z,amount=spec;visual={3:9006,4:9007,5:9008}.get(kind,9005)
            guid=0xf110000000000000|(visual<<24)|(200+i)
            row=[None]*56
            for offset,value in((0,marker),(8,kind),(12,amount),(24,0),(28,8),(32,0),(36,visual),(40,f.from_float(x)),(44,0),(48,f.from_float(z)),(52,f.from_float(1))):
                row[offset:offset+4]=struct.pack('<I',value)
            row[16:24]=struct.pack('<Q',guid);row[5]=77;row[7]=88;storage.append(tuple(row))
        count=len(storage);storage.extend(tuple((i*11+j*19+37)&255 for j in range(56))for i in range(2))
        initial=OpeningVector135(56,tuple(storage),count);pickups=initial;destroy=();ops=[];answers=[];meta=[]
        for j in range(repeat):
            now=f.add(original.stats.now_bits,f.from_float(j*.25));s=replace(s,stats=replace(s.stats,now_bits=now))
            result=collect_resources137(ResourceCollectionInput137(s,pickups,(0,0,0),True));s,pickups=result.state,result.pickups;destroy+=result.destroy170_hex
            ops.append(dict(operation='collect',now_bits=now));answers.append(known(s,pickups,destroy));meta.append(dict(consumed=result.consumed,destroy170_hex=result.destroy170_hex,pending=result.pending))
        i=len(rows);rows.append(dict(id=i,state=asdict(original),operations=ops,player_guid='42',unknown_poison=(0xa5,0x5a)[i&1],
            player_xyz_bits=[0,0,0],pickups=dict(count=initial.count,storage=initial.storage)))
        expected.append(dict(id=i,stages=answers));labels.append(dict(id=i,group=group,operations=meta))
    for kind in(3,4,5):add('pilot-real-full10291-resource'+str(kind),state(),(kind,))
    for kind in(3,4,5):add_collect('pilot-full2862-near-resource'+str(kind),state(),((kind,0,0,0,0xdeadbeef),))
    if full:
        for cls in(1,2,3,4,5,7,8,9,11):
            for race in(1,2,3,4,5,6,7,8):add('class-race-empty-source-stat-consumer',state(cls=cls,race=race,level=1+(cls+race)%20),((cls+race)%2+3,))
        for kind,spell in((3,23451),(4,23505)):
            for spells in((),((spell,50),),((42,50),(spell,5),(23505 if kind==3 else 23451,50),(spell,50)),
                    ((spell,50),(spell,50),(42,50)),((42,50),(43,8))):
                for spare in(0,2):add('stable-remove-all-owners-and-preserve-full-backing',state(live=live_vector(spells,len(spells)+spare)),(kind,kind))
        for gate in(0,4,5,255):
            for hp in(0,.25,.75,1):add('half-max-heal-cap-and-gate387',state(heal_gate=gate,hp_fraction=hp),(5,5))
        for capacity in(0,1,3,4):
            spells=tuple((42+i,50)for i in range(capacity));add('capacity-growth-repeated-all-three',state(live=live_vector(spells,capacity)),(3,4,3,5,4,5))
        for kind in(3,4,5):
            for marker in(0,1):
                for distance in(0,2.9999998,3,3.0000002,4,100):
                    add_collect('resource-XY3-geometry-marker-and-destroy',state(),((kind,marker,distance,1000000,0xffffffff),),repeat=2)
        add_collect('mixed-kind-reverse-order-full56B-compaction',state(),((3,0,0,0,0),(2,0,100,0,777),(4,1,3,0,1),(5,0,2,0,0xffffffff)),repeat=2)
        add_collect('same-spell-reverse-refresh-valid-live-markers',state(live=live_vector(((23451,30),(42,40)),4)),((3,0,0,0,1),(4,1,2,0,2),(3,1,1,0,3)),repeat=2)
    return rows,expected,labels


def refusal_checks():
    row=[0]*56
    for offset,value in((0,2),(8,3),(24,0),(28,8),(32,0)):
        row[offset:offset+4]=struct.pack('<I',value)
    value=ResourceCollectionInput137(state(),OpeningVector135(56,(tuple(row),),1),(0,0,0),True)
    result=[]
    try:collect_resources137(value)
    except PendingResourceConsumer137:result.append('marker2-refused-with-preserved-original31727-panic-counterexample')
    else:raise AssertionError('Known invalid marker2 accepted as ordinary successful collection')
    try:collect_resources137(replace(value,claims_empty=False))
    except PendingResourceConsumer137:result.append('nonempty-claims-remain-pending')
    else:raise AssertionError('Unknown claims accepted')
    return result


def compare(expected,actual):
    errors=[];counts=Counter()
    def walk(want,got,path):
        if want is None:
            assert re.fullmatch(r'case\d+\.stage\d+\.(live|pickups)\.storage\[\d+\]\[\d+\]',path),path
            assert type(got)is int and 0<=got<=255;counts['explicit_unknown_physical_bytes']+=1
        elif isinstance(want,dict):
            if not isinstance(got,dict)or set(want)!=set(got):errors.append(dict(path=path,expected_keys=list(want),actual_keys=list(got)));return
            for k in want:walk(want[k],got[k],path+'.'+k)
        elif isinstance(want,(list,tuple)):
            if not isinstance(got,(list,tuple))or len(want)!=len(got):errors.append(dict(path=path,expected_length=len(want),actual_length=len(got)));return
            for i,(a,b)in enumerate(zip(want,got)):walk(a,b,path+'['+str(i)+']')
        else:
            counts['known_values']+=1
            if type(want)is not type(got)or want!=got:errors.append(dict(path=path,expected=want,actual=got))
    assert len(expected)==len(actual)
    for want,row in zip(expected,actual):
        assert want['id']==row['id']and len(want['stages'])==len(row['stages'])
        for j,(a,raw)in enumerate(zip(want['stages'],row['stages'])):
            b=raw['known'];b['live']['storage']=[list(bytes.fromhex(h))for h in b['live']['storage']]
            b['pickups']['storage']=[list(bytes.fromhex(h))for h in b['pickups']['storage']]
            walk(a,b,'case'+str(want['id'])+'.stage'+str(j));counts['stages']+=1
            counts['observed_packets']+=raw['raw_packets']['count'];counts['observed_notifications']+=raw['raw_notifications']['count']
    return errors,counts


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=('pilot','full'),default='pilot');parser.add_argument('--case-index',type=int);args=parser.parse_args()
    scripts=('check_resource_consumer137.py','build_resource_consumer137_oracle.py','run_resource_consumer137_oracle.mjs','source_closure137.py',
        'production_closure135.py','build_combat137_oracle.py','wasm137_profile.py','wasm134_profile.py','wasm_index.py')
    files=tuple('scripts/'+n for n in scripts)+production_sources135(ROOT,'core_spec.resource_consumer137')
    edges=verify_local_source_closure(files);before={n:sha(ROOT/n)for n in files};rows,expected,labels=corpus(args.phase=='full');refused=refusal_checks()
    if args.case_index is not None:
        if not 0<=args.case_index<len(rows):parser.error('case-index outside generated corpus')
        rows,expected,labels=[rows[args.case_index]],[expected[args.case_index]],[labels[args.case_index]]
        for row in(rows[0],expected[0],labels[0]):row['id']=0
        labels[0]['original_case_index']=args.case_index
    assert before=={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('resource-consumer0137-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for n,digest in before.items():
        p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==digest
    for n,v in(('input.json',rows),('expected.json',expected),('labels.json',labels),('refusals.json',refused)):save(out/n,v)
    assert all((out/n).stat().st_size<=4194304 for n in('input.json','expected.json'))
    artifacts={n:sha(out/n)for n in('input.json','expected.json','labels.json','refusals.json','manifest.json',manifest['module_file'],'10291.wat')}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_resource_consumer137_oracle.mjs'),str(out),str(out/'input.json')]
    save(out/'prepared.json',dict(source_sha256=before,artifacts=artifacts,cases=len(rows),operations=sum(len(r['operations'])for r in rows),command=command,expected_before_original=True,deadline_seconds=60,local_source_import_edges=edges))
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    began=time.monotonic();error=None
    def interrupted(sig,frame):raise KeyboardInterrupt('Owned137 resource consumer signal '+str(sig))
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
        assert(out/'stdout.jsonl').stat().st_size<=32*1024*1024
        actual=[json.loads(line)for line in(out/'stdout.jsonl').read_text().splitlines()];errors,counts=compare(expected,actual)
        runtime=json.loads((out/'resource-consumer137-runtime.json').read_text());assert runtime['fresh_instances']==len(rows)and runtime['actual_host_calls']==0 and runtime['stack_all_restored']
    save(out/'differences.json',errors);after={n:sha(ROOT/n)for n in files}
    report=dict(version='0.137.0',actual_build='d171b8f9f',original_sha256=SOURCE_SHA,cases=len(rows),operations=sum(len(r['operations'])for r in rows),differences=len(errors),comparison=dict(counts),groups=dict(Counter(r['group']for r in labels)),
        expected_before_original=True,source_files=len(files),source_sha256_before=before,source_sha256_after=after,source_unchanged=before==after,local_source_import_edges=edges,
        frozen_artifacts=artifacts,artifacts_unchanged=all(sha(out/n)==h for n,h in artifacts.items()),process=terminal,runtime=runtime,pure_model_refusals=refused,
        scope='Full10291 and2862 original calls; independently predicted effect345/live32/physical56B compaction/destroy170/HP/23derived/3keyed/aux/RNG/counter/sequence in empty external source domain',
        input_limitations=['Manual Game8192/empty source vectors/initial BTree/live backing fixtures, not original constructor','Shared135 independent stats numerical rules freshly checked only in declared137 consumer domain'],
        observations_not_predictions=['Complete raw aura48x16 vector and all keyed-tree fields','All raw packet/notification payloads and locale state','Full8192B Game after each call'],
        full2862_calls=sum(op['operation']=='collect'for row in rows for op in row['operations']),full880_frames=0,native_windows_execution=False,complete_games=0,
        pending=['Non-resource nearby2862 consumers, XP/coins and claims/auxiliary ownership','Full aura/wire/localized notification independent semantics','Nonempty item/talent/timed/other live source domains','137 full world/boot/game/UI/network'],
        artifacts={n:sha(out/n)for n in('stdout.jsonl','stderr.log','differences.json','prepared.json')})
    save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),cases=len(rows),operations=report['operations'],differences=len(errors),first_errors=errors[:12],process=terminal,receipt_sha256=sha(out/'comparison.json'))))
    if child.returncode or error or errors or not terminal['pid_missing']or not terminal['pgid_missing']or not report['source_unchanged']or not report['artifacts_unchanged']:raise SystemExit(1)


if __name__=='__main__':main()
