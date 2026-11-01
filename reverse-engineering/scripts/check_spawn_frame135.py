#!/usr/bin/env python3
"""Compare actual8751 placement and947 ordinary natural-spawn composition."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
import math
import os
import random
import signal
import struct
import subprocess
import sys
import time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
SOURCE_FILES=('scripts/check_spawn_frame135.py','scripts/run_spawn_position135_oracle.mjs',
 'scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py',
 'reconstruction/core_spec/spawn_schedule135.py','reconstruction/core_spec/spawn_schedule135_data.py',
 'reconstruction/core_spec/spawn_position135.py','reconstruction/core_spec/spawn_position135_data.py',
 'reconstruction/core_spec/spawn_geometry135.py','reconstruction/core_spec/spawn135.py',
 'reconstruction/core_spec/spawn135_data.py','reconstruction/core_spec/spawn_math135.py',
 'reconstruction/core_spec/binary32.py','reconstruction/core_spec/binary32_sqrt.py',
 'reconstruction/core_spec/rng.py','reconstruction/core_spec/progression134.py','reconstruction/core_spec/enemy_scaling.py')
IMPORT_HASHES={p:sha(ROOT/p)for p in SOURCE_FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.spawn_position135 import PositionInput,sample_position
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from core_spec.spawn_schedule135 import FrameInput,step_ordinary_frame
from core_spec.spawn135 import SpawnInput,spawn_normal
from core_spec.spawn135_data import ZONES
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
FLOAT_FIELDS=(288,292,296,300,304,308,312,316,320,324,328,332,336,340,344,348,352,396)


def corpus(pilot=False):
    cases=[];pending=[];b=f.from_float
    words=((1,2,3,4),(123456789,362436069,521288629,88675123),(0xffffffff,0x80000000,0x12345678,0xabcdef01))
    def position(group,zone=0,offset=0,velocity=(0,0),prob=.5,seed=words[0],lo=26,hi=36):
        cx,cy,_=ZONE_GEOMETRY[zone]
        raw=dict(zone=zone,player_xyz=[f.add(cx,b(offset)),cy,0],velocity_xy=[b(v)for v in velocity],
            low_radius_bits=b(lo),high_radius_bits=b(hi),bias_probability_bits=b(prob),flat_height_bits=0,
            obstacle_grid_absent=True,pathfinding_absent=True,rng_words=list(seed))
        r=sample_position(PositionInput(**raw))
        if r.status!='resolved_flat':pending.append(dict(kind='position',group=group,input=raw,status=r.status));return
        cases.append(dict(id=len(cases),kind='position',group=group,zone_id=ZONES[zone][0],input=raw,
            expected=dict(position_bits=list(r.position_bits),rng_words=list(r.rng_words)),model_draws=r.draws,
            model_attempts=r.attempts,model_radius_shrinks=r.radius_shrinks))
    cache={}
    def existing(zone,count):
        key=(zone,count)
        if key not in cache:
            records=[];rng=words[0]
            for i in range(count):
                xyz=(*ZONE_GEOMETRY[zone][:2],0)
                s=SpawnInput(zone,0,0,b(1),0,0,1,0,0,0,tuple([0]*i),rng,i,xyz,0,bytes(424).hex())
                r=spawn_normal(s)
                if not r.success:raise ValueError('Existing fixture cap')
                records.append(r.record_hex);rng=r.rng_words
            cache[key]=records
        return cache[key]
    def frame(group,zone=0,budget=2,now=0,dt=.1,mode=0,members=1,difficulty=0,kills=0,
              endless=0,victory=0,start=0,velocity=(0,0),seed=words[0],count=0,scale=1,counter=None):
        xyz=[*ZONE_GEOMETRY[zone][:2],0];units=existing(zone,count)
        raw=dict(zone=zone,now_bits=b(now),dt_bits=b(dt),budget_bits=b(budget),kill_cost_bits=b(kills),mode=mode,members=members,
            difficulty=difficulty,zone_multiplier_bits=b(scale),victory_field400=victory,endless_flag=endless,endless_start_bits=b(start),
            player_xyz=xyz,previous_player_xyz=xyz,velocity_xy=[b(v)for v in velocity],flat_height_bits=0,
            rng_words=list(seed),counter=count if counter is None else counter,unit_records=units,other_event_timers_future=True)
        r=step_ordinary_frame(FrameInput(**raw))
        if r.status!='ordinary_projection':pending.append(dict(kind='tick',group=group,input=raw,status=r.status));return
        position_input=dict(zone=zone,player_xyz=xyz,velocity_xy=raw['velocity_xy'],low_radius_bits=b(26),high_radius_bits=b(36),
            bias_probability_bits=b(.5),flat_height_bits=0,obstacle_grid_absent=True,pathfinding_absent=True,rng_words=list(seed))
        expected=dict(budget_bits=r.budget_bits,kill_cost_bits=r.kill_cost_bits,count=len(r.unit_records),counter=r.counter,
            rng_words=list(r.rng_words),record_hex=list(r.unit_records),velocity_xy=list(r.velocity_xy))
        cases.append(dict(id=len(cases),kind='tick',group=group,zone_id=ZONES[zone][0],input=position_input,frame_input=raw,
            expected=expected,model_requests=list(r.requests),model_draws=r.draws,
            **{k:raw[k]for k in('now_bits','dt_bits','budget_bits','kill_cost_bits','mode','members','difficulty',
               'zone_multiplier_bits','victory_field400','endless_flag','endless_start_bits','counter','unit_records','previous_player_xyz')}))
    for zone in(0,6,11):
        position('pilot-flat',zone)
        for budget in(0,2,20):frame('pilot-natural',zone,budget)
    for velocity in((5,0),(-5,0),(0,5),(0,-5)):
        position('pilot-axis',velocity=velocity,seed=words[1]);frame('pilot-moving',velocity=velocity,seed=words[1],dt=0)
    if pilot:return cases,pending
    for zone in range(12):
        radius=f.to_float(ZONE_GEOMETRY[zone][2])
        for seed in words:
            for offset in(0,radius-5,radius+10,radius+25):
                position('zone-boundary-retry',zone,offset,seed=seed)
            for now in(0,180,600,1200):
                for budget in(0,1,2,8,30):frame('all-zones-clock-budget',zone,budget,now,seed=seed)
    for velocity in((0,0),(1.9999999,0),(2,0),(2.0000002,0),(5,0),(-5,0),(0,5),(0,-5),(3,4)):
        for prob in(-.1,0,.5,1,1.1,float('nan')):
            for seed in words:position('motion-threshold-and-bias',velocity=velocity,prob=prob,seed=seed)
    for mode in(0,1,2,7,255):
        for members in(0,1,2,4,255,0xffffffff):
            for zone in(0,3,11):frame('mode-and-member-normal-frame',zone,budget=20,now=240,mode=mode,members=members,kills=100)
    for difficulty in range(256):frame('all-difficulty-natural',difficulty=difficulty,now=600,budget=12)
    for count in(1,3,10,35,36,48,49,50):
        for budget in(0,.5,1,8,100):frame('prior-units-density-cap',count=count,budget=budget,now=60,kills=20)
    for flag in(0,1,2,255):
        for now in(60,600,1200):
            for start in(0,now/2,now+60):frame('endless-guard-and-powers',now=now,start=start,endless=flag,victory=1,budget=20,kills=100,zone=11)
    rng=random.Random(0xa2e00947)
    for _ in range(120):
        z=rng.randrange(12);now=rng.uniform(0,1200)
        frame('seeded-natural-mixed',z,now=now,dt=rng.choice((0,.001,.016,.1,.5)),budget=rng.uniform(0,100),
            mode=rng.randrange(3),members=rng.randrange(1,8),difficulty=rng.randrange(8),kills=rng.uniform(0,200),
            endless=rng.randrange(2),victory=1,start=rng.uniform(0,now),scale=rng.choice((.5,1,2)),
            velocity=rng.choice(((0,0),(5,0),(-5,0),(0,5),(0,-5))),seed=tuple(rng.getrandbits(32)for _ in range(4)))
    return cases,pending


def compare(cases,rows):
    if len(rows)!=len(cases)or[r['id']for r in rows]!=list(range(len(cases))):raise ValueError('Unique complete result order')
    fail=[];leaves=0
    def eq(a,b,path):
        nonlocal leaves
        if type(a)is not type(b):fail.append((path,'type',a,b));return
        if isinstance(a,list):
            if len(a)!=len(b):fail.append((path,'length',len(a),len(b)));return
            for i,(x,y)in enumerate(zip(a,b)):eq(x,y,path+(i,))
        elif isinstance(a,dict):
            if a.keys()!=b.keys():fail.append((path,'keys'));return
            for k in a:eq(a[k],b[k],path+(k,))
        elif path[-2:-1]==('record_hex',):
            x,y=bytes.fromhex(a),bytes.fromhex(b)
            if len(x)!=424 or len(y)!=424:fail.append((path,'record bytes'));return
            for o in range(0,424,4):
                u,v=struct.unpack_from('<I',x,o)[0],struct.unpack_from('<I',y,o)[0];leaves+=1
                if u!=v and not(o in FLOAT_FIELDS and f.is_nan(u)and f.is_nan(v)):fail.append((path+(o,),hex(u),hex(v)))
        else:
            leaves+=1
            floating=any(k in path for k in('position_bits','velocity_xy'))or path[-1]in('budget_bits','kill_cost_bits')
            if a!=b and not(floating and type(a)is int and f.is_nan(a)and f.is_nan(b)):fail.append((path,a,b))
    for c,r in zip(cases,rows):eq(c['expected'],r['result'],(c['id'],))
    return fail,leaves


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    before={p:sha(ROOT/p)for p in SOURCE_FILES};assert before==IMPORT_HASHES
    out,manifest=build(['spawn_position','spawn_tick']);snap=out/'source-snapshot';snap.mkdir()
    for name,digest in before.items():
        p=snap/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==digest
    cases,pending=corpus(args.phase=='pilot');file=out/'spawn-frame135-fixtures.json';file.write_text(json.dumps(cases,allow_nan=False)+'\n')
    assert json.loads(file.read_text())==cases
    (out/'spawn-frame135-pending.json').write_text(json.dumps(pending,allow_nan=False)+'\n')
    results=out/'spawn-frame135-results.jsonl';errors=out/'spawn-frame135-stderr.log'
    assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_spawn_position135_oracle.mjs'),str(out),str(file)]
    start=time.monotonic()
    with results.open('w')as stdout,errors.open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned original947/8751 deadline')
    if code:raise RuntimeError(f'Original process failed, inspect {out}')
    rows=[json.loads(x)for x in results.read_text().splitlines()];failures,leaves=compare(cases,rows)
    (out/'spawn-frame135-mismatches.json').write_text(json.dumps(failures,indent=2,allow_nan=False)+'\n')
    after={p:sha(ROOT/p)for p in SOURCE_FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),kind_counts=dict(Counter(c['kind']for c in cases)),
        groups=dict(Counter(c['group']for c in cases)),pending_model_inputs_not_counted=len(pending),mismatch_fields=len(failures),
        compared_scalar_or_record_words=leaves,naturally_created_units=sum(len(c.get('model_requests',[]))for c in cases),
        source_sha256_before=before,source_sha256_after=after,original_wasm_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],
        manifest_sha256=sha(out/'manifest.json'),original_functions=[947,8751],unchanged_original_callees=True,changed_original_sections=[7],
        artifact_sha256={p.name:sha(p)for p in(file,results,errors,out/'spawn-frame135-pending.json',out/'spawn-frame135-mismatches.json',out/'spawn-position135-runtime.json')},
        runtime=json.loads((out/'spawn-position135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=round(time.monotonic()-start,3)),
        expected_before_original_launch=True,complete947_reconstruction=False,application_start_called=False,
        limitations=['Other elite/event/Boss timers explicitly future, associated vectors empty; ordinary budget/density only.',
            'Original8751 samples real positions using flat29631 guard and absentgrid/pathfinding; terrain andfallback13516 remain pending.',
            'Nonaxis atan2 heading is unresolved if motion-biased branch selected; pending model inputs are separately retained and not accepted comparisons.',
            'Object/message callees execute unchanged; physical message/object structures and full AI/rendering are not compared.'])
    (out/'spawn-frame135-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),pending=len(pending),mismatch_fields=len(failures),first_failures=failures[:12]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
