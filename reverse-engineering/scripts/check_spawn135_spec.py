#!/usr/bin/env python3
"""Predict135 weighted choices, exp decay and complete normal spawn records."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
SOURCE_FILES=('scripts/check_spawn135_spec.py','scripts/run_spawn135_oracle.mjs','scripts/build_full135_oracle.py',
    'scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py','reconstruction/core_spec/spawn135.py',
    'reconstruction/core_spec/spawn135_data.py','reconstruction/core_spec/spawn_math135.py',
    'reconstruction/core_spec/binary32.py','reconstruction/core_spec/binary32_sqrt.py',
    'reconstruction/core_spec/rng.py','reconstruction/core_spec/enemy_scaling.py','reconstruction/core_spec/progression134.py')
IMPORT_HASHES={name:sha(ROOT/name)for name in SOURCE_FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.spawn135 import SpawnInput,spawn_normal,choose_spawn,eligible_normals
from core_spec.spawn135_data import ZONES,NORMALS
from core_spec.spawn_math135 import exp_bits
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
FLOAT_FIELDS=(288,292,296,300,304,308,312,316,320,324,328,332,336,340,344,348,352,396)


def corpus(pilot=False):
    cases=[]
    def normal(group,zone=0,index=0,**kw):
        raw={'zone':zone,'definition_index':index,'now_bits':f.from_float(120),'zone_multiplier_bits':f.from_float(1),
             'difficulty':1,'mode':0,'members':1,'victory_field400':0,'endless_flag':0,'endless_start_bits':0,
             'existing_states':[],'rng_words':[1,2,3,4],'counter':0,'position_bits':[f.from_float(-9396),f.from_float(-633),0],
             'resolved_owner':0,'initial_slot_hex':bytes((17*j+31)%256 for j in range(424)).hex()}
        raw.update(kw);s=SpawnInput(**raw);result=spawn_normal(s)
        expected={'success':result.success,'guid':str(result.guid),'counter':result.counter,'rng_words':list(result.rng_words),
                  'count':len(raw['existing_states'])+int(result.success),'record_hex':result.record_hex}
        cases.append(dict(id=len(cases),kind='normal',group=group,zone_id=ZONES[zone][0],input=raw,expected=expected,
                          model_draws=result.draws,model_cap=result.cap))
    def choice(group,zone=0,candidates=(0,1,2),minutes=0,words=(1,2,3,4)):
        result=choose_spawn(zone,candidates,minutes,words)
        cases.append(dict(id=len(cases),kind='choice',group=group,zone_id=ZONES[zone][0],
            input=dict(zone=zone,candidates=list(candidates),minutes_bits=minutes,rng_words=list(words)),
            expected=dict(index=result.index,rng_words=list(result.rng_words)),model_draws=result.draws,
            model_weights=list(result.weight_bits),model_sum=result.total_bits))
    normal('pilot-normal');normal('pilot-elite',index=11);normal('pilot-coop',mode=1,members=4)
    for e in (.25,.5,1,2,4,20):normal('pilot-endless',victory_field400=1,endless_flag=1,now_bits=f.from_float(e*60))
    choice('pilot-choice',minutes=f.from_float(10));choice('pilot-choice-inf',zone=11,candidates=tuple(range(16)),minutes=0x7f800000)
    for x in (0,-.01,-1,-10,-90,1,80):
        bits=f.from_float(x);cases.append(dict(id=len(cases),kind='decay',group='pilot-decay',input=dict(bits=bits),expected=dict(bits=exp_bits(bits))))
    if pilot:return cases
    words=((1,2,3,4),(0,0,0,0),(0xffffffff,0x80000000,0x12345678,0xabcdef01),(123456789,362436069,521288629,88675123))
    for z,defs in enumerate(NORMALS):
        for i in range(len(defs)):
            normal('every-normal-definition',zone=z,index=i)
            for mode in (0,1):
                normal('every-definition-endless',zone=z,index=i,mode=mode,members=4,
                       victory_field400=1,endless_flag=1,now_bits=f.from_float(16*60),endless_start_bits=f.from_float(3.25*60),
                       rng_words=list(words[(z+i)%len(words)]),difficulty=(i%5)+1)
        for t in (0,.5,1,3.5,10,20,100):
            selected=eligible_normals(z,f.from_float(t))
            for w in words:choice('eligible-world-pool',z,selected,f.from_float(t),w)
        for t in (0,0x80000000,0x7f800000,0xff800000,0x7fc00001):
            for w in words:choice('all-definition-special-time',z,tuple(range(len(defs))),t,w)
    for difficulty in range(256):normal('every-difficulty-byte',difficulty=difficulty,index=11)
    for mode in (0,1,2,7,255):
        for members in (0,1,2,4,255,0xffffffff):
            for z in (0,2,3,11):normal('mode-member-region',zone=z,mode=mode,members=members)
    for count in (0,1,48,49,50,51,54):
        for marker in (0,1,2,0xffffffff):normal('alive-cap-xor',existing_states=[marker]*count)
    for index in (0xffffffff,0xfffffffe,99):normal('definition-clamp',index=index)
    for counter in (0xfffffe,0xffffff,0x1000000,0xfffffffe,0xffffffff):normal('counter-guid-wrap',counter=counter)
    for exponent in (-1,0,.01,.1,.25,.3,.5,1,1.25,2,3,4,10,20,40,60,100,200,500,1000):
        for z in (0,6,11):normal('endless-power-and-clock',zone=z,index=3,victory_field400=1,endless_flag=1,now_bits=f.from_float(600+max(exponent,0)*60),endless_start_bits=f.from_float(600))
    rng=random.Random(0xa2e05736)
    for _ in range(300):
        z=rng.randrange(12);now=rng.uniform(0,3600)
        normal('mixed-ordered',zone=z,index=rng.randrange(len(NORMALS[z])),now_bits=f.from_float(now),
               zone_multiplier_bits=f.from_float(rng.choice((.5,.8,1,1.25,2))),difficulty=rng.randrange(8),
               mode=rng.choice((0,1,2)),members=rng.randrange(1,9),victory_field400=1,
               endless_flag=rng.randrange(2),endless_start_bits=f.from_float(rng.uniform(0,now)),
               counter=rng.getrandbits(32),rng_words=[rng.getrandbits(32)for _ in range(4)])
    for x in (0,0x80000000,1,0x80000001,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00001):
        cases.append(dict(id=len(cases),kind='decay',group='decay-special-bits',input=dict(bits=x),expected=dict(bits=exp_bits(x))))
    values=[f.from_float(x/100)for x in range(-10400,9001,17)]
    for boundary in (956301312,1051816472,1065686418,1118743632,1118925335,1120924084):
        values.extend((boundary+d)|sign for d in (-2,-1,0,1,2)for sign in (0,f.SIGN))
    values.extend(rng.getrandbits(32)for _ in range(1000))
    for x in values:
        cases.append(dict(id=len(cases),kind='decay',group='decay-range-and-thresholds',input=dict(bits=x),expected=dict(bits=exp_bits(x))))
    return cases


def equal_bits(a,b):return a==b or f.is_nan(a) and f.is_nan(b)


def compare(cases,rows):
    failures=[]
    if len(rows)!=len(cases) or [r['id']for r in rows]!=list(range(len(cases))):raise ValueError('Result coverage/order/IDs')
    for c,row in zip(cases,rows):
        a,b=c['expected'],row['result']
        if c['kind']=='decay':
            if not equal_bits(a['bits'],b['bits']):failures.append(dict(id=c['id'],group=c['group'],field='decay',expected=a,actual=b))
        elif c['kind']=='choice':
            if a!=b:failures.append(dict(id=c['id'],group=c['group'],field='choice',expected=a,actual=b))
        else:
            for key in ('success','guid','counter','rng_words','count'):
                if a[key]!=b[key]:failures.append(dict(id=c['id'],group=c['group'],field=key,expected=a[key],actual=b[key]))
            if a['record_hex'] is None:
                if b['record_hex'] is not None:failures.append(dict(id=c['id'],field='unexpected record'))
            elif b['record_hex'] is None:failures.append(dict(id=c['id'],field='missing record'))
            else:
                import struct
                x=bytes.fromhex(a['record_hex']);y=bytes.fromhex(b['record_hex'])
                for k in range(106):
                    u,v=struct.unpack_from('<I',x,k*4)[0],struct.unpack_from('<I',y,k*4)[0]
                    if u!=v and not(k*4 in FLOAT_FIELDS and equal_bits(u,v)):
                        failures.append(dict(id=c['id'],group=c['group'],field=f'unit+{k*4}',expected=hex(u),actual=hex(v)))
    return failures


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');a=p.parse_args()
    before={name:sha(ROOT/name)for name in SOURCE_FILES};assert before==IMPORT_HASHES
    out,manifest=build(['choose_spawn','spawn_normal','spawn_decay'])
    snapshots=out/'source-snapshot';snapshots.mkdir()
    for name in SOURCE_FILES:
        dest=snapshots/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    cases=corpus(a.phase=='pilot');file=out/'spawn135-fixtures.json';file.write_text(json.dumps(cases,allow_nan=False)+'\n')
    assert json.loads(file.read_text())==cases
    assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_spawn135_oracle.mjs'),str(out),str(file)]
    results=out/'spawn135-results.jsonl';stderr=out/'spawn135-stderr.log';start=time.monotonic()
    with results.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned original spawn runner exceeded60s')
    if code:raise RuntimeError(f'Original spawn runner failed: {out}')
    rows=[json.loads(x)for x in results.read_text().splitlines()];failures=compare(cases,rows)
    (out/'spawn135-mismatches.json').write_text(json.dumps(failures,indent=2,allow_nan=False)+'\n')
    after={name:sha(ROOT/name)for name in SOURCE_FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    receipt=dict(version='0.135.1',build='0898d5e3',phase=a.phase,cases=len(cases),groups=dict(Counter(c['group']for c in cases)),
        kind_counts=dict(Counter(c['kind']for c in cases)),mismatch_fields=len(failures),mismatch_cases=len({x['id']for x in failures}),
        original_functions=[20272,5736,26361],original_internal_callees_unchanged=True,only_changed_section=7,
        original_wasm_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],source_sha256_before=before,source_sha256_after=after,
        artifact_sha256={q.name:sha(q)for q in(file,results,stderr,out/'spawn135-mismatches.json',out/'spawn135-runtime.json')},
        runtime=json.loads((out/'spawn135-runtime.json').read_text()),process=dict(command=command,exit_code=code,deadline_seconds=60,seconds=round(time.monotonic()-start,3)),
        expected_generated_before_original=True,original_application_start_called=False,installed_apps_or_saves_modified=False,
        limitations=['Explicit supplied position and resolved owner; world sampling8751 and complete scheduler947/boss2785 still pending.',
            'Entire424B destination slot is explicit before append; unwritten bytes must be preserved, not assumed initialized.',
            'Object creation1525/queues execute but their bytes/accounting are not independently compared.',
            'Only actual normal/elite definitions, no successful empty-candidate panic comparison; NaN float fields compare classification only.'])
    (out/'spawn135-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_fields=len(failures),failures=failures[:15]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
