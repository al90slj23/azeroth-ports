#!/usr/bin/env python3
"""Expected-first complete2862 mixed XP/coin/resource differential."""
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
from itertools import permutations
from pathlib import Path
import argparse,json,os,re,signal,struct,subprocess,sys,time

sys.dont_write_bytecode=True
from build_mixed_pickup135_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.candidates135 import DEFINITIONS
from core_spec.currency134 import CurrencyState
from core_spec.derived_stats135 import StatsInput,recalculate
from core_spec.level_cycle135 import from_dict,projection
from core_spec.pickups134 import PickupRecord
from core_spec.opening_npc_pickups135 import OpeningVector135
from core_spec.resource_consumer135 import LiveVector135
from core_spec.resource_aura135 import ResourceAuraState135
from core_spec.mixed_resource135 import MixedResourceContext135,project_mixed_pickup_storage135
from core_spec.death_pickup135 import DeathContext135,CollectionState135,collect_pickups
from core_spec.opaque_pickup135 import OpaqueKind2Pickup135,PickupAmountAddress135

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def level_input(*,level=1,phase=1,protection=0,mode=0,owned=(),hp=.2,radius=None,heal_gate=0):
    s=StatsInput(class_byte=1,race_byte=1,level=level,now_bits=f.from_float(10))
    initial=recalculate(s)
    scalar=dict(class_byte=1,race_byte=1,old_max_hp_bits=initial['derived_bits']['1536'],
        current_hp_bits=f.mul(initial['derived_bits']['1536'],f.from_float(hp)),now_bits=s.now_bits,
        previous_speed_bits=initial['speed_bits'],conditional268_bits=0,flag2574=mode,
        pool1532_bits=0,pool1536_bits=0,conditional1344_id=0,conditional1348_bits=0,pool768_bits=0)
    derived=dict(initial['derived_bits'])
    if radius is not None:derived['1560']=f.from_float(radius)
    return dict(progression=dict(level=level,xp=0,pending_upgrades=0),stats=scalar,
        sources=dict(passives=[],adjustments=[],item_modifiers=[],owned_skills=[],timed_records=[],definitions=[],live_effects=[]),
        derived_bits=derived,player_fields={},rng_words=[1,2,3,4],
        choice_inputs=dict(owned=[dict(ability_id=name,record_hex=AbilityRecord(DEFINITIONS[name].pointer).to_bytes().hex())for name in owned],
            blocked_ids=[],banished_keys=[],flag275=0,flag2581=1),
        phase2587=phase,selection_kind2585=255,generation_counter2400=0xffffffff,
        flags2576=protection,gate2572=0,flags2573=0,heal_gate387=heal_gate,pool756_bits=0)


def record(kind,index,*,amount=None,marker=None,arrival=None,x=0,z=0,spawn=0,opaque=False):
    if amount is None:amount={0:5,1:7}.get(kind,0xdeadbeef)
    if marker is None:marker=1 if kind==0 else 0
    if arrival is None and marker==1:arrival=f.from_float(9)
    visual={0:9001,1:9004,2:9005,3:9006,4:9007,5:9008}[kind]
    guid=0xf110000000000000|(visual<<24)|(700+index)
    values=(marker,arrival,kind,amount,guid,0,8,0,visual,f.from_float(x),0,f.from_float(z),f.from_float(spawn))
    if opaque:
        values=values[:3]+(None,)+values[4:]
        return OpaqueKind2Pickup135(*values,amount_origin=PickupAmountAddress135(guid,1872,176))
    return PickupRecord(*values)


def physical(records):
    rows=[]
    fields=((0,'marker'),(4,'arrival_bits'),(8,'kind'),(12,'amount'),(24,'aux_capacity'),(28,'aux_pointer'),
        (32,'aux_count'),(36,'visual_id'),(40,'x_bits'),(44,'y_bits'),(48,'height_bits'),(52,'spawn_time_bits'))
    for r in records:
        row=[None]*56
        for offset,name in fields:
            value=getattr(r,name)
            if value is not None:row[offset:offset+4]=struct.pack('<I',value)
        row[16:24]=struct.pack('<Q',r.guid);rows.append(tuple(row))
    rows.extend(tuple((j*19+i*31+37)&255 for j in range(56))for i in range(2))
    return OpeningVector135(56,tuple(rows),len(records))


def expected_projection(state,pickups,packets,notifications):
    c=state.resource_context
    return dict(level=projection(state.level),pickups=dict(capacity=pickups.capacity,count=pickups.count,storage=pickups.storage),
        live=dict(capacity=c.live.capacity,count=c.live.count,storage=c.live.storage),
        aura=dict(capacity=c.aura.capacity,count=c.aura.count,storage=c.aura.storage,initialized2569=c.aura.initialized2569),
        gold=state.currency.gold,earned=state.currency.earned,currency_queue=state.currency.queue,currency_queue_capacity=state.currency.queue_capacity,
        xp_queue=state.xp_queue,xp_queue_capacity=state.xp_queue_capacity,spawn_counter=state.death.spawn_counter,
        message_sequence=state.death.message_sequence,action_sequence1644=c.action_sequence1644,
        notification_next_id14340336=c.notification_next_id14340336,
        packets=[dict(opcode=op,payload_hex=data)for op,data in packets],notifications=notifications)


def corpus(full):
    rows=[];expected=[];labels=[]
    def add(group,kinds,*,raw=None,records=None,times=(10,),members=0):
        raw=raw or level_input();level=from_dict(raw)
        records=tuple(records or(record(kind,j)for j,kind in enumerate(kinds)))
        vector=physical(records);death=DeathContext135(records,vector.capacity,85,19,f.from_float(2.5))
        currency=CurrencyState(7,9,dict(level.derived_bits)[1588],level.stats.flag2574,42,members,0,(),0,())
        resource=MixedResourceContext135(LiveVector135((),0),ResourceAuraState135((),0),42,9,1,'en',True)
        state=CollectionState135(level,death,currency,(0,0,0),(),0,True,resource)
        inputs=dict(id=len(rows),group=group,level=raw,control=dict(currency=asdict(currency),player_xyz=[0,0,0],
            spawn_counter=85,message_sequence=19,kill_cost_bits=death.kill_cost_bits,xp_queue=[],xp_queue_capacity=0),
            resource_context=asdict(resource),pickups=dict(storage=vector.storage,count=vector.count),
            times_bits=[f.from_float(t)for t in times],unknown_poison=(0xa5,0x5a)[len(rows)&1])
        answers=[];metadata=[];packets=();notifications=()
        for now in inputs['times_bits']:
            before=state
            result=collect_pickups(state,now);assert result.status=='core_projection',result
            vector=project_mixed_pickup_storage135(vector,before.death.records,result);state=result.state
            for effect in result.ordered_effects:
                if effect.stage=='despawn':packets+=((170,struct.pack('<Q',effect.guid).hex()),)
                packets+=effect.packets
                notifications+=tuple(dict(kind='rune_raw',payload_hex=data)for data in effect.notifications)
                if effect.stage=='choice_notification_pending':
                    notifications+=(dict(kind='choices_known',**dict(effect.metadata)['known_envelope']),)
            answers.append(expected_projection(state,vector,packets,notifications))
            metadata.append(dict(consumption_order=result.consumption_order,xp_awards=result.xp_awards,coin_awards=result.coin_awards,
                growth_events=result.growth_events,ordered_effects=[asdict(e)for e in result.ordered_effects],pending=result.pending))
        rows.append(inputs);expected.append(dict(id=inputs['id'],stages=answers));labels.append(dict(id=inputs['id'],group=group,operations=metadata))
    add('pilot-resource-before-XP-growth',(0,1,4))
    add('pilot-XP-before-resource-growth',(4,1,0))
    add('pilot-paused-choice-still-finishes-selected-resources',(5,0,4),raw=level_input(owned=('cleave',)))
    add('pilot-attraction-arrival-and-resource',(0,3,1),raw=level_input(protection=1),records=(
        record(0,0,marker=0,x=1,spawn=0),record(3,1,x=2),record(1,2,x=.5)),times=(10,10.25))
    add('pilot-level15-DOT-with-resource',(0,4,1),raw=level_input(level=14,owned=('rend',)),records=(
        record(0,0,amount=200),record(4,1),record(1,2)))
    add('pilot-XP-coin-only-compatibility',(0,1),raw=level_input(protection=1))
    if full:
        for kind in(3,4,5):
            for order in permutations((0,1,kind)):
                for protection in(0,1):add('all-resource-XP-coin-order-and-pause',order,raw=level_input(protection=protection))
        for gate in(0,5,255):
            for hp in(0,.75,1):add('mixed-heal-gate-and-cap',(0,5,1,4),raw=level_input(protection=1,hp=hp,heal_gate=gate))
        add('multiple-XP-resource-interleaving-single-choice',(0,4,0,1,3),records=(
            record(0,0,amount=5),record(4,1),record(0,2,amount=100),record(1,3),record(3,4)))
        for kind in(3,4,5):
            add('entry-radius-cached-before-level-recalculation',(1,0,kind),raw=level_input(radius=8),records=(
                record(1,0,x=4),record(0,1),record(kind,2,x=2.5)))
            add('far-opaque-kind2-full56-preserved',(0,kind,2),records=(
                record(0,0),record(kind,1),record(2,2,x=100,opaque=True)))
        for mode in(0,1):
            add('forwarding-queues-and-paused-phase-boundary',(0,1,4,0),raw=level_input(mode=mode),members=2,
                records=(record(0,0,amount=40),record(1,1,amount=100),record(4,2),record(0,3,amount=5)))
    return json.loads(json.dumps(rows,allow_nan=False)),json.loads(json.dumps(expected,allow_nan=False)),json.loads(json.dumps(labels,allow_nan=False))


def compare(expected,actual):
    differences=[];counts=Counter()
    def walk(a,b,path):
        if a is None:
            assert re.fullmatch(r'case\d+\.stage\d+\.(pickups|live|aura)\.storage\[\d+\]\[\d+\]',path),path
            assert type(b)is int and 0<=b<=255;counts['explicit_unknown_physical_bytes']+=1
        elif isinstance(a,dict):
            if type(b)is not dict or a.keys()!=b.keys():differences.append(dict(path=path,reason='keys'));return
            for key in a:walk(a[key],b[key],path+'.'+str(key))
        elif isinstance(a,list):
            if type(b)is not list or len(a)!=len(b):differences.append(dict(path=path,reason='length',expected=len(a),actual=len(b)));return
            for i,(x,y)in enumerate(zip(a,b)):walk(x,y,path+'['+str(i)+']')
        else:
            counts['known_values']+=1
            if type(a)is not type(b)or a!=b:differences.append(dict(path=path,expected=a,actual=b))
    assert len(expected)==len(actual)
    for want,row in zip(expected,actual):
        assert want['id']==row['id']and len(want['stages'])==len(row['stages'])
        for j,(a,b)in enumerate(zip(want['stages'],row['stages'])):
            got=b['known']
            for key in('pickups','live','aura'):got[key]['storage']=[list(bytes.fromhex(h))for h in got[key]['storage']]
            walk(a,got,'case'+str(want['id'])+'.stage'+str(j));counts['stages']+=1
    return differences,counts


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    scripts=('check_mixed_pickup135.py','build_mixed_pickup135_oracle.py','run_mixed_pickup135_oracle.mjs',
        'build_resource_consumer135_oracle.py','build_full135_oracle.py','build_upgrade134_oracle.py','production_closure135.py','source_closure137.py')
    files=tuple('scripts/'+n for n in scripts)+production_sources135(ROOT,'core_spec.death_pickup135','core_spec.mixed_resource135','core_spec.opaque_pickup135')
    edges=verify_local_source_closure(files);before={n:sha(ROOT/n)for n in files}
    rows,expected,labels=corpus(args.phase=='full');assert len(rows)<=128
    assert before=={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('mixed-pickup0135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for n,h in before.items():
        p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    for n,v in(('input.json',rows),('expected.json',expected),('labels.json',labels)):save(out/n,v)
    assert all((out/n).stat().st_size<=4194304 for n in('input.json','expected.json'))
    artifacts={n:sha(out/n)for n in('input.json','expected.json','labels.json','manifest.json','mixed-static.json',manifest['module_file'])}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_mixed_pickup135_oracle.mjs'),str(out),str(out/'input.json')]
    save(out/'prepared.json',dict(source_sha256=before,local_source_import_edges=edges,artifacts=artifacts,expected_before_original=True,command=command,deadline_seconds=60))
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    began=time.monotonic();error=None
    def stop(sig,frame):raise KeyboardInterrupt('Owned mixed pickup stop '+str(sig))
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
        actual=[json.loads(l)for l in(out/'stdout.jsonl').read_text().splitlines()];errors,counts=compare(expected,actual)
    if(out/'mixed-pickup135-runtime.json').exists():runtime=json.loads((out/'mixed-pickup135-runtime.json').read_text())
    after={n:sha(ROOT/n)for n in files};save(out/'differences.json',errors)
    receipt=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,
        cases=len(rows),operations=sum(len(r['times_bits'])for r in rows),comparison_complete=child.returncode==0,differences=len(errors)if child.returncode==0 else None,
        comparison=dict(counts),groups=dict(Counter(row['group']for row in rows)),source_files=len(files),local_source_import_edges=edges,
        source_sha256_before=before,source_sha256_after=after,source_unchanged=before==after,
        frozen_artifacts=artifacts,artifacts_unchanged=all(sha(out/n)==h for n,h in artifacts.items()),expected_before_original=True,process=terminal,runtime=runtime,
        scope='Complete2862 mixed0/1/3/4/5,ordered level/resource state,full56/live/aura backing,all150/306/226/170 and EnglishJSON; explicit empty other producers/no moving NPCs during choice pause.',
        observations_not_predictions=['Other packet families including XP221 movement;2159 choice notification presentation JSON beyond known envelope/candidate metadata','FullGame8192 and allocator/BTree/queue addresses'],
        notification_owner='Explicit cold-module nextID1 checked by Node without writing original global; retained over every operation.',
        full880_frames=0,complete_games=0,native_executions=0,pending=['Nearbykind2/other kinds','Nonempty claims/aux and other external live/stat/aura producers','Moving NPC35514 pause producer must be interleaved by root owner','Non-English labels','CompleteGame/mainloop/native'])
    save(out/'comparison.json',receipt);print(json.dumps(dict(directory=str(out),cases=len(rows),operations=receipt['operations'],differences=receipt['differences'],first_errors=errors[:6],process=terminal,receipt_sha256=sha(out/'comparison.json'))))
    if child.returncode or errors or error or not terminal['pid_missing']or not terminal['pgid_missing']or not receipt['source_unchanged']or not receipt['artifacts_unchanged']:raise SystemExit(1)
    assert runtime['actual_host_calls']==0 and runtime['stack_all_restored']


if __name__=='__main__':main()
