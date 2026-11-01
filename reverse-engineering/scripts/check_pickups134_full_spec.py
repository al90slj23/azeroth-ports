#!/usr/bin/env python3
"""Compare kind0 pickup model with complete current1417 and2862.

Original region0/flat-world placement is controlled to match explicitly
resolved model coordinates. Unwritten append+4 is compared to the known prior
slot when retained, and masked only after unknown allocation growth.
"""
from dataclasses import asdict,replace
import itertools
import json
import os
import random
import signal
import struct
import subprocess
import sys
from build_full134_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.pickups134 import (PickupRecord,PickupState,Placement,append_xp,append_idle_currency,step_pickups,encode_record56)
from core_spec.pickup_entity134 import project_kind1_entity
from core_spec.progression134 import ProgressionState,apply_xp

SEED=0xa2e02862
SLOT_WORD=0xa5a5a5a5
OLD_ARRIVAL=0x4faabbcc


def corpus():
    b=f.from_float;cases=[]
    def record(i,x=0,y=0,**kw):
        return PickupRecord(guid=0xf130002329000000+i+1,amount=i+1,x_bits=b(-9396+x),y_bits=b(-633+y),spawn_time_bits=b(9),**kw)
    def add(operation,group,records=(),capacity=None,amount=7,placement=None,level=120,xp=0,pending=0,phase=1,**kw):
        if capacity is None:capacity=len(records)
        options={'spawn_counter':200,'now_bits':b(10),'player_x_bits':b(-9396),
                 'player_y_bits':b(-633),'radius_bits':b(4)}
        options.update(kw)
        state=PickupState(records=records,capacity=capacity,**options)
        placement=placement or Placement(b(-9396),b(-633),0)
        rng=[1,2,3,4]
        if operation=='append':result=append_xp(state,amount,placement)
        elif operation=='currency':
            entity=project_kind1_entity(rng,state.spawn_counter)
            result=append_idle_currency(state,amount,placement,guid=entity.guid,counter_after=entity.counter2400)
            rng=list(entity.rng_state)
        else:result=step_pickups(state)
        if result.status!='core_projection':raise ValueError('Corpus outside model domain: '+str(result))
        growth=result.capacity_growth is not None
        old_arrival={r.guid:r.arrival_bits if r.arrival_bits is not None else OLD_ARRIVAL for r in records}
        words=[]
        for r in result.state.records:
            raw=encode_record56(r,uninitialized_arrival_bits=old_arrival.get(r.guid,SLOT_WORD)if r.arrival_bits is None else None)
            row=list(struct.unpack('<14I',raw))
            if r.guid not in old_arrival and r.arrival_bits is None and growth:row[1]=None
            words.append(row)
        progress=ProgressionState(level,xp,pending)
        for award in result.xp_awards:progress=apply_xp(progress,award).state
        expected={'capacity':result.state.capacity,'count':len(words),'spawn_counter':result.state.spawn_counter,
            'message_sequence':result.state.message_sequence,'level':progress.level,'xp':progress.xp,
            'pending':progress.pending_upgrades,'phase':phase,'rng':rng,'records_words':words}
        scalar=asdict(state);scalar.pop('records')
        cases.append({'id':len(cases),'operation':operation,'group':group,'state':scalar,
            'record_hex':[encode_record56(r,uninitialized_arrival_bits=OLD_ARRIVAL if r.arrival_bits is None else None).hex()for r in records],
            'placement':[placement.x_bits,placement.y_bits,placement.height_bits],'amount':amount,'level':level,'xp':xp,
            'pending':pending,'phase':phase,'rng':[1,2,3,4],'expected':expected,'expected_xp_awards':list(result.xp_awards)})
    for count in (0,1,4,43,44,45,46,60):
        for spare in (0,3):
            for amount in (0,1,0xffffffff):
                rs=tuple(record(i,x=(i%11)-5,y=(i//11)-2)for i in range(count))
                add('append','idle_count_growth_merge',rs,capacity=count+spare,amount=amount)
    for marker_count in (1,2,20,44):
        rs=tuple(record(i,marker=int(i<marker_count),arrival_bits=b(20)if i<marker_count else None)for i in range(45))
        add('append','attracting_records_do_not_count_as_idle',rs,capacity=46)
    # Two equidistant nearest idle records must retain the first under strict>.
    tie=tuple(replace(record(i,x=-1 if i==0 else 1 if i==1 else 20),amount=0xffffffff if i==0 else 1)for i in range(45))
    add('append','nearest_first_tie_and_amount_wrap',tie,capacity=45,amount=2)
    for counter in (0xffffff,0x1000000,0xffffffff):
        add('append','spawn_counter_wrap_and_guid_low24',capacity=1,spawn_counter=counter)
    for marker in (0,1):
        for x,y in ((0,0),(3,4),(4,0),(4.0009765625,0),(24,0),(40,0)):
            for radius in (0,4,5,100):
                r=record(0,x,y,marker=marker,arrival_bits=b(10)if marker else None)
                add('step','distance_radius_and_due_markers',(r,),radius_bits=b(radius))
    for age in (5.999999,6,6.000001,7):
        add('step','age6_strict_boundary',(replace(record(0,x=24),spawn_time_bits=f.sub(b(10),b(age))),),radius_bits=0)
    for arrival in (b(10)-1,b(10),b(10)+1,0x7fc00001,0x7f800000,0xff800000):
        add('step','stored_arrival_boundary',(record(0,marker=1,arrival_bits=arrival),))
    for multiplier,amount in itertools.product((0,-1,.5,1,1.5,float('inf'),float('nan')),(0,1,3,0xffffffff)):
        add('step','XP_round_min_sat',(replace(record(0,marker=1,arrival_bits=b(10)),amount=amount),),xp_multiplier_bits=b(multiplier))
    # Asymmetric u32 wrap+threshold makes reverse dispatch observable in final fields.
    reverse=(replace(record(0,marker=1,arrival_bits=b(10)),amount=0xffffffff),
             replace(record(1,marker=1,arrival_bits=b(10)),amount=5))
    add('step','reverse_dispatch_observable_via_wrap',reverse,level=119,phase=3)
    for now in (2**24,2**26):
        add('step','same_invocation_arrival_rounds_to_now',(record(0),),now_bits=b(now))
    rng=random.Random(SEED)
    for _ in range(200):
        count=rng.randrange(0,12);rs=[]
        for i in range(count):
            marker=rng.randrange(2)
            rs.append(replace(record(i,x=rng.randrange(-20,21),y=rng.randrange(-20,21),marker=marker,
                arrival_bits=b(rng.choice((9,10,11)))if marker else None),amount=rng.getrandbits(32)))
        add('step','seeded_records',tuple(rs),radius_bits=b(rng.randrange(0,25)),xp=rng.getrandbits(32))
    for count in (0,1,4,44,45):
        for spare in (0,2):
            for amount in (0,4,0xffffffff):
                add('currency','kind1_entity_counter_rng_append',tuple(record(i)for i in range(count)),capacity=count+spare,amount=amount)
    for counter in (0xffffff,0xffffffff):add('currency','kind1_guid_counter_wrap',capacity=1,spawn_counter=counter)
    for foreign_kind,distance in ((1,10),(1,4.0009765625),(2,4),(6,10),(99,10)):
        foreign=record(1,x=distance,kind=foreign_kind)
        add('step','idle_foreign_outside_collect_guard',(record(0),foreign))
    return cases


def compare(want,got):
    difference={}
    for key,value in want.items():
        if key=='records_words':
            if len(value)!=len(got[key]):difference[key]=[value,got[key]];continue
            bad=[{'record':i,'word':j,'expected':x,'actual':got[key][i][j]}for i,row in enumerate(value)
                 for j,x in enumerate(row)if x is not None and x!=got[key][i][j]]
            if bad:difference[key]=bad
        elif value!=got[key]:difference[key]=[value,got[key]]
    return difference


def main():
    cases=corpus();out,manifest=build(['spawn_pickup','collect_pickups'])
    casefile=out/'pickups134-cases.json';casefile.write_text(json.dumps(cases,indent=2,allow_nan=False)+'\n')
    node=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    if sha(node)!='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0':raise ValueError('Node identity')
    resultfile=out/'pickups134-original-results.jsonl'
    with resultfile.open('w')as stdout,(out/'pickups134-stderr.log').open('w')as stderr:
        child=subprocess.Popen([str(node),'--max-old-space-size=512','--wasm-max-mem-pages=512',
            str(ROOT/'scripts/run_pickups134_full_oracle.mjs'),str(out),str(casefile)],stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise
    if code:raise SystemExit(f'Original pickup run failed: {out}')
    rows=[json.loads(x)for x in resultfile.read_text().splitlines()]
    if len(rows)!=len(cases)or [x['id']for x in rows]!=list(range(len(cases))):raise ValueError('Result coverage/order')
    mismatches=[{'id':c['id'],'group':c['group'],'difference':d}for c,a in zip(cases,rows)if (d:=compare(c['expected'],a))]
    mismatchfile=out/'pickups134-mismatches.json';mismatchfile.write_text(json.dumps(mismatches,indent=2,allow_nan=False)+'\n')
    runtimefile=out/'pickups134-runtime.json'
    files=('scripts/build_full134_oracle.py','scripts/full134_host.mjs','scripts/check_pickups134_full_spec.py','scripts/run_pickups134_full_oracle.mjs',
        'reconstruction/core_spec/pickups134.py','reconstruction/core_spec/pickup_entity134.py','reconstruction/core_spec/rng.py',
        'reconstruction/core_spec/binary32_sqrt.py','reconstruction/core_spec/binary32.py','reconstruction/core_spec/progression134.py')
    receipt={'version':'0.134.0','build':'983346a7','original_wasm_sha256':SOURCE_SHA,'module_sha256':manifest['module_sha256'],
        'original_full_functions':[1417,2862],'case_count':len(cases),'mismatch_count':len(mismatches),
        'operation_cases':{op:sum(c['operation']==op for c in cases)for op in ('append','currency','step')},
        'groups':{g:sum(c['group']==g for c in cases)for g in sorted({c['group']for c in cases})},
        'fields_compared':list(cases[0]['expected']),'unwritten_arrival_policy':'Known old/prior slot words exact; only newly allocated unknown append arrival masked.',
        'runtime':json.loads(runtimefile.read_text()),'source_sha256':{p:sha(ROOT/p)for p in files},
        'artifact_sha256':{p.name:sha(p)for p in (casefile,resultfile,mismatchfile,runtimefile)},
        'limitations':['Kind0 and idle foreign records outside collect guards; kind1 append;mode0,empty claims/XP aux,resolved region0 flat placement.',
            'All complete original internal callees retained. Other state/message/visual fields not compared.',
            'World clamp/full terrain,foreign pickup callbacks,noncanonical marker,mode/claims and full scheduling remain pending.',
            'Model pending serialization/physical allocation/4630 full side effects remain pending.']}
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Source changed')
    (out/'pickups134-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'run':str(out),'cases':len(cases),'mismatches':len(mismatches)}))
    if mismatches:raise SystemExit('Pickup projection differs')


if __name__=='__main__':main()
