#!/usr/bin/env python3
"""New exact atan/atan2 and arbitrary-motion8751/947 differential.

Old accepted1580 fixtures and8pending are reused as inputs, never as original
results. New expected positions/records come from the new independent modules.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import json
import os
import random
import signal
import subprocess
import sys
import time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build,parse_source
from build_upgrade134_oracle import sha,source_memory
import hashlib
import struct
from source_closure135 import core_sources
PRE_PRODUCTION = core_sources(ROOT,'spawn_frame_motion135.py','spawn_heading135.py')
PRE_HASHES = {p:sha(ROOT/p) for p in PRE_PRODUCTION}
from check_spawn_frame135 import SOURCE_FILES as BASE_SOURCES,FLOAT_FIELDS

SOURCE_FILES=tuple(dict.fromkeys((*BASE_SOURCES,'scripts/check_spawn_frame135.py',
 'scripts/check_spawn_motion135.py','scripts/run_spawn_motion135_oracle.mjs',
 'reconstruction/core_spec/spawn_heading135.py',
 'reconstruction/core_spec/spawn_position_motion135.py',
 'reconstruction/core_spec/spawn_frame_motion135.py','scripts/source_closure135.py',*PRE_PRODUCTION)))
IMPORT_HASHES={p:sha(ROOT/p)for p in SOURCE_FILES}
assert all(IMPORT_HASHES[p]==h for p,h in PRE_HASHES.items())
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.spawn_heading135 import atan_bits,atan2_bits,HI,LO,INF_QUADRANTS,XINF_QUADRANTS
from core_spec.spawn_position135 import PositionInput
from core_spec.spawn_position_motion135 import sample_position
from core_spec.spawn_frame_motion135 import step_ordinary_frame
from core_spec.spawn_schedule135 import FrameInput
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from core_spec.spawn135_data import ZONES
from check_spawn_frame135 import corpus as old_corpus,compare as old_compare
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def corpus(pilot=False):
    cases=[];pending=[];b=f.from_float
    def add(row):row['id']=len(cases);cases.append(row)
    def position(raw,group):
        result=sample_position(PositionInput(**raw))
        if result.status!='resolved_flat':pending.append(dict(group=group,input=raw,status=result.status));return
        add(dict(kind='position',group=group,input=raw,zone_id=ZONES[raw['zone']][0],
                 expected=dict(position_bits=list(result.position_bits),rng_words=list(result.rng_words))))
    def frame(raw,group):
        result=step_ordinary_frame(FrameInput(**raw))
        if result.status!='ordinary_projection':pending.append(dict(group=group,input=raw,status=result.status));return
        inp=dict(zone=raw['zone'],player_xyz=raw['player_xyz'],velocity_xy=raw['velocity_xy'],
                 low_radius_bits=b(26),high_radius_bits=b(36),bias_probability_bits=b(.5),
                 flat_height_bits=raw['flat_height_bits'],obstacle_grid_absent=True,pathfinding_absent=True,rng_words=raw['rng_words'])
        add(dict(kind='tick',group=group,input=inp,frame_input=raw,zone_id=ZONES[raw['zone']][0],
          expected=dict(budget_bits=result.budget_bits,kill_cost_bits=result.kill_cost_bits,
             count=len(result.unit_records),counter=result.counter,rng_words=list(result.rng_words),
             record_hex=list(result.unit_records),velocity_xy=list(result.velocity_xy)),
          **{k:raw[k]for k in('now_bits','dt_bits','budget_bits','kill_cost_bits','mode','members','difficulty',
               'zone_multiplier_bits','victory_field400','endless_flag','endless_start_bits','counter','unit_records','previous_player_xyz')}))
    special=[0,f.SIGN,1,f.SIGN|1,0x007fffff,0x00800000,0x3f000000,0xbf000000,
             0x3f800000,0xbf800000,0x40000000,0xc0000000,0x7f7fffff,0xff7fffff,
             f.INF,f.INF|f.SIGN,0x7fc00001,0xffc01234]
    for bits in special:
        add(dict(kind='atan',group='atan-special',input=dict(bits=bits),expected=dict(bits=atan_bits(bits))))
    for x in special:
        for y in special:
            add(dict(kind='atan2',group='atan2-special-grid',input=dict(y=y,x=x),expected=dict(bits=atan2_bits(y,x))))
    if not pilot:
        for edge in(8388608,964689920,1054867456,1060110336,1066926080,1075576832,1283457023):
            for off in range(-5,6):
                for sign in(0,f.SIGN):
                    bits=(edge+off)|sign
                    add(dict(kind='atan',group='atan-threshold-neighbors',input=dict(bits=bits),expected=dict(bits=atan_bits(bits))))
        rng=random.Random(0xa2e42475)
        for _ in range(1800):
            x,y=rng.getrandbits(32),rng.getrandbits(32)
            add(dict(kind='atan2',group='atan2-seeded-allwords',input=dict(y=y,x=x),expected=dict(bits=atan2_bits(y,x))))
        for _ in range(800):
            bits=rng.getrandbits(32)
            add(dict(kind='atan',group='atan-seeded-allwords',input=dict(bits=bits),expected=dict(bits=atan_bits(bits))))
    old,old_pending=old_corpus(pilot)
    for row in old:
        if row['kind']=='position':position(row['input'],'prior-'+row['group'])
        else:frame(row['frame_input'],'prior-'+row['group'])
    for row in old_pending:position(row['input'],'previously-pending-nonaxis')
    motions=((3,4),(-3,4),(3,-4),(-3,-4),(.0001,5),(5,.0001),(1e10,2e10),(2.1,-.1))
    for z in ((0,6,11)if pilot else range(12)):
        for velocity in motions:
            cx,cy,_=ZONE_GEOMETRY[z];xyz=[cx,cy,0]
            for seed in((1,2,3,4),(123456789,362436069,521288629,88675123)):
                position(dict(zone=z,player_xyz=xyz,velocity_xy=[b(v)for v in velocity],
                    low_radius_bits=b(26),high_radius_bits=b(36),bias_probability_bits=b(1),flat_height_bits=0,
                    obstacle_grid_absent=True,pathfinding_absent=True,rng_words=list(seed)), 'nonaxis-forced-bias')
                frame(dict(zone=z,now_bits=b(180),dt_bits=0,budget_bits=b(10),kill_cost_bits=0,mode=0,members=1,
                    difficulty=2,zone_multiplier_bits=b(1),victory_field400=0,endless_flag=0,endless_start_bits=0,
                    player_xyz=xyz,previous_player_xyz=xyz,velocity_xy=[b(v)for v in velocity],flat_height_bits=0,
                    rng_words=list(seed),counter=0,unit_records=[],other_event_timers_future=True),'nonaxis-natural-frame')
    return json.loads(json.dumps(cases,allow_nan=False)),json.loads(json.dumps(pending,allow_nan=False))


def compare(cases,rows):
    assert len(cases)==len(rows)and[x['id']for x in rows]==list(range(len(cases)))
    failures=[];word_count=0
    for case,row in zip(cases,rows):
        if case['kind']in('atan','atan2'):
            x,y=case['expected']['bits'],row['result']['bits'];word_count+=1
            if x!=y and not(f.is_nan(x)and f.is_nan(y)):failures.append((case['id'],x,y))
        else:
            c=dict(case,id=0);r=dict(row,id=0);diffs,n=old_compare([c],[r]);word_count+=n
            failures.extend((case['id'],d)for d in diffs)
    return failures,word_count


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in SOURCE_FILES};assert before==IMPORT_HASHES
    binary=SOURCE.read_bytes();assert hashlib.sha256(binary).hexdigest()==SOURCE_SHA
    parsed=parse_source(binary);tables=[]
    for address,wanted in((14335568,HI),(14335584,LO),(14335600,INF_QUADRANTS),(14335616,XINF_QUADRANTS)):
        raw,file_offset,segment=source_memory(binary,parsed[4],address,16)
        assert struct.unpack('<4I',raw)==wanted
        tables.append(dict(address=address,file_offset=file_offset,data_segment=segment,raw_hex=raw.hex()))
    cases,pending=corpus(args.phase=='pilot');out,manifest=build(['spawn_position','spawn_tick','atan_heading','atan2_heading'])
    (out/'spawn-heading135-tables.json').write_text(json.dumps(tables,indent=2)+'\n')
    snap=out/'source-snapshot';snap.mkdir()
    for n,value in before.items():
        p=snap/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==value
    file=out/'spawn-motion135-fixtures.json';file.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(file.read_text())==cases
    (out/'spawn-motion135-pending.json').write_text(json.dumps(pending,allow_nan=False)+'\n')
    results=out/'spawn-motion135-results.jsonl';stderr=out/'spawn-motion135-stderr.log'
    assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_spawn_motion135_oracle.mjs'),str(out),str(file)]
    started=time.monotonic()
    with results.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned spawn heading/frame deadline')
    if code:raise RuntimeError(f'Original failed: {out}')
    rows=[json.loads(s)for s in results.read_text().splitlines()];failures,words=compare(cases,rows)
    (out/'spawn-motion135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in SOURCE_FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),
        kinds=dict(Counter(c['kind']for c in cases)),groups=dict(Counter(c['group']for c in cases)),
        mismatch_fields=len(failures),compared_words=words,pending_not_counted=len(pending),
        source_sha256_before=before,source_sha256_after=after,module_sha256=manifest['module_sha256'],
        original_wasm_sha256=SOURCE_SHA,original_functions=[34787,42475,8751,947],only_changed_section=7,
        expected_before_original=True,original_callees_unchanged=True,
        artifact_sha256={p.name:sha(p)for p in(file,results,stderr,out/'spawn-motion135-pending.json',out/'spawn-motion135-mismatches.json',out/'spawn-motion135-runtime.json')},
        runtime=json.loads((out/'spawn-motion135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-started),
        limitations=['Flat-height/absentgrid/pathfinding only; fallback and other timed947 events remain pending.',
                    'No application start, native EXE, network, user save or installed-app write.'])
    (out/'spawn-motion135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),pending=len(pending),mismatch_fields=len(failures),first_failures=failures[:8]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
