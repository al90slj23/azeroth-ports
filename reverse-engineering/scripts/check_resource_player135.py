#!/usr/bin/env python3
"""Expected-first unchanged complete2088 resource expiry/regen differential."""
from pathlib import Path
from collections import Counter
from dataclasses import asdict,fields,replace
from datetime import datetime,timezone
from itertools import permutations
import argparse,json,os,re,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_resource_player135_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.derived_stats135 import StatsInput,recalculate
from core_spec.level_cycle135 import StatScalars,from_dict
from core_spec.resource_consumer135 import LiveVector135,_semantics
from core_spec.resource_aura135 import ResourceAuraState135,rebuild_resource_aura135
from core_spec.mixed_resource135 import MixedResourceContext135
from core_spec.resource_player_update135 import prepare_resource_player_update135,PendingResourcePlayerUpdate135
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def live_vector(definitions,capacity=5):
    rows=[]
    for i in range(max(capacity,len(definitions))):
        row=list(bytes((i*37+j*19+43)&255 for j in range(32)))
        if i<len(definitions):
            kind,spell,expiry,magnitude=definitions[i]
            for offset,value in((0,i*123),(4,i*99),(8,kind),(20,spell),(24,expiry),(28,0)):
                row[offset:offset+4]=struct.pack('<I',value)
            row[12:20]=[None]*8
            if kind==8:row[12:16]=struct.pack('<I',magnitude)
        rows.append(tuple(row))
    return LiveVector135(tuple(rows),len(definitions))

def initial(live,*,hp=.2,gate=0,cls=1,race=1,cache=0,action=9,pools=(0,0)):
    stats=StatsInput(class_byte=cls,race_byte=race,level=1,now_bits=0,live_effects=_semantics(live))
    result=recalculate(stats);d={int(k):v for k,v in result['derived_bits'].items()};maximum=d[1536]
    stats=replace(stats,old_max_hp_bits=maximum,current_hp_bits=f.mul(maximum,f.from_float(hp)),previous_speed_bits=result['speed_bits'],pool1532_bits=pools[0],pool1536_bits=pools[1])
    scalar={item.name:getattr(stats,item.name)for item in fields(StatScalars)}
    raw=dict(progression=dict(level=1,xp=0,pending_upgrades=0),stats=scalar,
        sources=dict(passives=[],adjustments=[],item_modifiers=[],owned_skills=[],timed_records=[],definitions=[],live_effects=[asdict(e)for e in _semantics(live)]),
        derived_bits={str(k):v for k,v in d.items()},player_fields={'22':max(0,int(-(-f.to_float(stats.current_hp_bits)//1))),'28':max(0,int(-(-f.to_float(maximum)//1))),'1109':result['object_fields']['1109']},rng_words=[1,2,3,4],
        choice_inputs=dict(owned=[],blocked_ids=[],banished_keys=[],flag275=0,flag2581=1),phase2587=1,selection_kind2585=255,generation_counter2400=0xffffffff,flags2576=0,gate2572=0,flags2573=0,heal_gate387=gate,pool756_bits=0)
    level=from_dict(raw);aura=ResourceAuraState135((),0)
    if cache:aura=replace(rebuild_resource_aura135(live.storage,live.count,0,aura,()).aura,initialized2569=cache)
    context=MixedResourceContext135(live,aura,42,action,1,'en',True)
    state=dict(stats=asdict(stats),derived_bits=level.derived_bits,player_fields=level.player_fields,live=asdict(live),heal_gate387=gate,rng_words=level.rng_words,counter2408=85,message_sequence2412=123,action_sequence1644=action,player_guid=42,aura=asdict(aura),aura_external_sources_absent=True,notification_next_id14340336=1,locale_code='en')
    return raw,level,context,state

def known(level,context,packets):
    t=level.stats;c=context
    return dict(aura=dict(capacity=c.aura.capacity,count=c.aura.count,storage=c.aura.storage,initialized2569=c.aura.initialized2569),packets_known=[dict(opcode=op,payload_hex=data)for op,data in packets],notifications_hex=[],notification_next_id14340336=c.notification_next_id14340336,live=dict(capacity=c.live.capacity,count=c.live.count,storage=c.live.storage),pickups=dict(capacity=0,count=0,storage=[]),destroy170_hex=[],derived_bits={str(k):v for k,v in level.derived_bits},current_hp_bits=t.current_hp_bits,speed_bits=t.previous_speed_bits,auxiliary_bits={'1444':t.pool1532_bits,'1448':t.pool1536_bits,'1348':t.conditional1348_bits,'768':t.pool768_bits,'756':level.pool756_bits},player_fields={str(k):v for k,v in level.player_fields},rng_words=level.rng_words,counter2408=85,message_sequence2412=123,action_sequence1644=c.action_sequence1644)

def corpus(full):
    rows=[];expected=[];labels=[];b=f.from_float
    speed=(0,23451,b(10),0);berserk=(0,23505,b(15),0);battle=(8,6673,b(20),b(.2))
    def add(group,live,steps,**kw):
        raw,level,context,state=initial(live_vector(live),**kw);ops=[];answers=[];metadata=[];packets=()
        for step in steps:
            now,dt,last=step;op=dict(now_bits=b(now),dt_bits=b(dt),last_hit_bits=b(last));result=prepare_resource_player_update135(level,context,**op,periodic_input=(),explicit_other_sources_absent=True)
            level,context=result.level,result.context;packets+=result.packets;ops.append(op);answers.append(known(level,context,packets));metadata.append(dict(expired_spell_ids=result.expired_spell_ids,recalculated=result.recalculated,regen_request_bits=result.regen_request_bits,heal_delta_bits=result.heal_delta_bits,events=result.events))
        i=len(rows);basic=replace(AbilityRecord(5467428),remaining_cooldown_bits=0x7f800000)
        rows.append(dict(id=i,state=state,level_input=raw,operations=ops,player_guid='42',unknown_poison=(0xa5,0x5a)[i&1],basic_hex=basic.to_bytes().hex(),pool756_bits=0));expected.append(dict(id=i,stages=answers));labels.append(dict(id=i,group=group,operations=metadata))
    add('speed10-strict-boundary',(speed,),[(9.999,.1,0),(10,.1,0),(10.001,.1,0)])
    add('berserker15-strict-boundary',(berserk,),[(14.999,.1,0),(15,.1,0),(15.001,.1,0)])
    add('ordered-two-resource-expiries',(speed,berserk),[(10,.1,0),(15,.1,0)])
    add('speed-then-positive-Battle',(speed,battle),[(10,.1,0),(20,.1,0)],cache=1)
    add('NaN-alone-no-dirty',((0,23451,0x7fc01234,0),),[(10,.1,0)])
    if not full:return rows,expected,labels
    for order in permutations((speed,(0,23505,b(10),0),battle)):
        add('stable-full32-compaction',order,[(10,.1,0),(20,.1,0)],cache=1)
    add('duplicate-kind0-earliest-aura',((0,23451,b(5),0),(0,23451,b(20),0),berserk),[(5,.1,0),(15,.1,0),(20,.1,0)],cache=1)
    add('NaN-co-remove',((0,23451,0x7fc01234,0),(0,23505,b(10),0)),[(9,.1,0),(10,.1,0)],cache=1)
    add('NaN-kind8-co-remove',(speed,(8,6673,0x7fc01234,b(.2))),[(10,.1,0)],cache=1)
    for hp in(.001,.999,1,1.2):
        for gate in(0,5):add('HP-regen-gate-at-expiry',(speed,),[(10,.1,0)],hp=hp,gate=gate)
    for dt in(0,.001,1,-.1):add('finite-dt-with-expiry',(speed,),[(10,dt,0)])
    for last in(7.001,7,6.999):add('last-hit-three-second',(speed,),[(10,.1,last)])
    for cls in(2,8,9):add('controlled-class-expiry',(speed,berserk),[(10,.1,0),(15,.1,0)],cls=cls)
    for cache in(0,1,2,255):add('aura-cache-initialized-bit',(speed,battle),[(10,.1,0)],cache=cache)
    add('226-action-wrap',(speed,),[(10,.1,0)],action=0xffffffff)
    add('pool-min-no-dirty',(speed,),[(9,.1,0)],pools=(b(10),b(20)))
    return rows,expected,labels

def compare(expected,actual,rows):
    errors=[];counts=Counter()
    def walk(want,got,path,poison):
        if want is None:
            assert re.fullmatch(r'case\d+\.stage\d+\.(live|aura)\.storage\[\d+\]\[\d+\]',path),path
            assert type(got)is int and 0<=got<=255;counts['unknown_physical_bytes']+=1
            if '.live.'in path and got!=poison:errors.append(dict(path=path,expected_preserved_poison=poison,actual=got))
        elif isinstance(want,dict):
            if not isinstance(got,dict)or set(want)!=set(got):errors.append(dict(path=path,expected_keys=list(want),actual_keys=list(got)));return
            for key in want:walk(want[key],got[key],path+'.'+key,poison)
        elif isinstance(want,(list,tuple)):
            if not isinstance(got,(list,tuple))or len(want)!=len(got):errors.append(dict(path=path,expected_length=len(want),actual_length=len(got)));return
            for i,(a,b)in enumerate(zip(want,got)):walk(a,b,path+'['+str(i)+']',poison)
        else:
            counts['known_values']+=1
            if type(want)is not type(got)or want!=got:errors.append(dict(path=path,expected=want,actual=got))
    assert len(expected)==len(actual)==len(rows)
    for want,row,case in zip(expected,actual,rows):
        assert want['id']==row['id']and len(want['stages'])==len(row['stages'])
        for j,(a,raw)in enumerate(zip(want['stages'],row['stages'])):
            actual=raw['known']
            for name in('live','aura','pickups'):actual[name]['storage']=[list(bytes.fromhex(h))for h in actual[name]['storage']]
            walk(a,actual,'case'+str(want['id'])+'.stage'+str(j),case['unknown_poison']);counts['stages']+=1
            counts['raw_packet_observations']+=raw['raw_packets']['count']
    return errors,counts

def refusal_checks():
    b=f.from_float;_,level,context,_=initial(live_vector(((0,23451,b(10),0),)))
    checks=[]
    candidates=[('missing-explicit-sources',lambda:prepare_resource_player_update135(level,context,b(10),b(.1),0)),
        ('missing-periodic-input',lambda:prepare_resource_player_update135(level,context,b(10),b(.1),0,explicit_other_sources_absent=True)),
        ('nonempty-periodic-input',lambda:prepare_resource_player_update135(level,context,b(10),b(.1),0,explicit_other_sources_absent=True,periodic_input=(1,))),
        ('nonfinite-dt',lambda:prepare_resource_player_update135(level,context,b(10),0x7fc00001,0,explicit_other_sources_absent=True,periodic_input=())),
        ('shield-cleanup',lambda:prepare_resource_player_update135(replace(level,stats=replace(level.stats,conditional1344_id=11426)),context,b(10),b(.1),0,explicit_other_sources_absent=True,periodic_input=()))]
    for label,definitions in [('unknown-kind0',((0,123,b(10),0),)),('duplicate-kind8',((8,6673,b(20),b(.2)),(8,6673,b(20),b(.3))))]:
        _,a,c,_=initial(live_vector(definitions));candidates.append((label,lambda a=a,c=c:prepare_resource_player_update135(a,c,b(10),b(.1),0,explicit_other_sources_absent=True,periodic_input=())))
    for label,call in candidates:
        try:call()
        except NotImplementedError as error:checks.append(dict(name=label,error=str(error)))
        else:raise AssertionError('Unknown source accepted: '+label)
    return checks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    scripts=('check_resource_player135.py','build_resource_player135_oracle.py','run_resource_player135_oracle.mjs','build_full135_oracle.py','build_upgrade134_oracle.py','production_closure135.py','source_closure137.py')
    files=tuple('scripts/'+n for n in scripts)+production_sources135(ROOT,'core_spec.resource_player_update135')
    edges=verify_local_source_closure(files);before={n:sha(ROOT/n)for n in files};rows,expected,labels=corpus(args.phase=='full');refusals=refusal_checks()
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('resource-player0135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for n,h in before.items():
        p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    for n,v in(('input.json',rows),('expected.json',expected),('labels.json',labels),('refusals.json',refusals)):save(out/n,v)
    assert all((out/n).stat().st_size<=4194304 for n in('input.json','expected.json'))
    artifacts={n:sha(out/n)for n in('input.json','expected.json','labels.json','refusals.json','manifest.json',manifest['module_file'])}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_resource_player135_oracle.mjs'),str(out),str(out/'input.json')]
    save(out/'prepared.json',dict(source_sha256=before,local_source_import_edges=edges,artifacts=artifacts,expected_before_original=True,command=command,deadline_seconds=60))
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA;began=time.monotonic();error=None
    def stop(sig,frame):raise KeyboardInterrupt('Owned resource player stop '+str(sig))
    old=signal.signal(signal.SIGTERM,stop)
    with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=60))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as exc:error=repr(exc)
        finally:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM,old)
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,error=error)
    save(out/'process-terminal.json',terminal);errors=[];counts=Counter();runtime=None
    if child.returncode==0:
        actual=[json.loads(l)for l in(out/'stdout.jsonl').read_text().splitlines()];errors,counts=compare(expected,actual,rows)
    if(out/'resource-player135-runtime.json').exists():runtime=json.loads((out/'resource-player135-runtime.json').read_text())
    after={n:sha(ROOT/n)for n in files};save(out/'differences.json',errors)
    receipt=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,cases=len(rows),operations=sum(len(r['operations'])for r in rows),comparison_complete=child.returncode==0,differences=len(errors)if child.returncode==0 else None,comparison=dict(counts),pure_model_refusals=refusals,groups=dict(Counter(row['group']for row in labels)),source_files=len(files),local_source_import_edges=edges,source_sha256_before=before,source_sha256_after=after,source_unchanged=before==after,frozen_artifacts=artifacts,artifacts_unchanged=all(sha(out/n)==h for n,h in artifacts.items()),expected_before_original=True,process=terminal,runtime=runtime,scope='Complete2088 with empty owned/future basic; resource kind0 and positive unique8 expiry,full32 backing,None preservation,48Aura cache,keyed fields,HP/regen,226/action/RNG',observations_not_predictions=['1453 account/presentation/statistics payload and all non226 packets','FullGame8192 and allocator/BTree/queue addresses'],full880_frames=0,complete_games=0,native_executions=0,pending=['1076 actual owned/basic/racial scheduling','Other live/periodic/shield/proc/aura source families','Full1453 healaccount logging','CompleteGame/mainloop/native'])
    save(out/'comparison.json',receipt);print(json.dumps(dict(directory=str(out),cases=len(rows),operations=receipt['operations'],differences=receipt['differences'],first_errors=errors[:6],process=terminal,receipt_sha256=sha(out/'comparison.json'))))
    if child.returncode or errors or error or not terminal['pid_missing']or not terminal['pgid_missing']or not receipt['source_unchanged']or not receipt['artifacts_unchanged']:raise SystemExit(1)
    assert runtime['actual_host_calls']==0 and runtime['stack_all_restored']
if __name__=='__main__':main()
