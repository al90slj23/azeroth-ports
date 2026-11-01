#!/usr/bin/env python3
"""Compare independent135 effective armor/incoming scalars to complete originals."""
from dataclasses import asdict,replace
from collections import Counter
import argparse
import json
import os
import random
import signal
import struct
import subprocess
import sys
import time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha

SOURCE_FILES=('scripts/check_incoming135_spec.py','scripts/run_incoming135_oracle.mjs',
 'scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py',
 'reconstruction/core_spec/incoming135.py','reconstruction/core_spec/incoming134.py',
 'reconstruction/core_spec/binary32.py')
IMPORT_SHA={name:sha(ROOT/name)for name in SOURCE_FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.incoming135 import (IncomingState135,UnitPosition,BuffRecord,ModifierRecord,
                                  effective_armor_bits,resolve_incoming_prefix)
FIELDS=('armor_1392_bits','armor_cap_1572_bits','nearby_reduction_1444_bits','hp_1528_bits',
 'shield_1532_bits','barrier_1536_bits','shield_source_1344','shield_source_remaining_1348_bits',
 'reserve_768_bits','absorbed_740_bits','maximum_shield_744_bits','last_hit_1648_bits')
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def state(**changes):
    value=dict(now_bits=f.from_float(10),hp_1528_bits=f.from_float(1000))
    value.update(changes)
    return IncomingState135(**value)


def unit(x=0,y=0,**changes):
    value=dict(start_x_bits=f.from_float(x),start_y_bits=f.from_float(y),
               end_x_bits=f.from_float(x),end_y_bits=f.from_float(y))
    value.update(changes)
    return UnitPosition(**value)


def corpus(pilot=False):
    rows=[];bits=f.from_float
    def add(group,s,kind='incoming',amount=bits(10),source=0,attack=0):
        raw=asdict(s);raw['map_id']=s.map_id.decode('ascii')
        if kind=='armor':expected={'effective_armor_bits':effective_armor_bits(s)}
        else:
            result=resolve_incoming_prefix(s,amount,source)
            if result.stage not in('scalar_nonfatal_projection','phase_guard','protection_guard','active_raw_buff12_guard'):
                raise ValueError('Corpus reached unresolved model boundary: '+result.stage)
            expected={name:getattr(result.state,name)for name in FIELDS}
            expected.update(incoming_total_992_bits=struct.pack('>d',result.state.incoming_total_992).hex(),phase2579=result.state.phase_2579)
        rows.append(dict(id=len(rows),group=group,kind=kind,input=raw,max_hp_bits=bits(1000),
                         amount_bits=amount,source_guid=str(source),attack_kind=attack,expected=dict(id=len(rows),**expected)))
    for rank in(0,1,30,255):
        for cap in(.1,.6):
            s=state(armor_1392_bits=bits(.2),armor_cap_1572_bits=bits(cap),units=(unit(1),),modifiers=(ModifierRecord(54,1,rank),))
            add('pilot-actual54cap',s,'armor');add('pilot-actual54incoming',s)
    for shield in(0,5,50):add('pilot-shield',state(shield_1532_bits=bits(shield),barrier_1536_bits=bits(shield)))
    for source in(0,1):add('pilot-source-registry',state(units=(unit(1),)),source=source,attack=1)
    if pilot:return rows
    for rank in range(256):
        for armor in(0,.55,.9):
            for cap in(.1,.6):add('all-ranks-armor-cap',state(armor_1392_bits=bits(armor),armor_cap_1572_bits=bits(cap),units=(unit(1),),modifiers=(ModifierRecord(54,1,rank),)),'armor')
    for flag in range(256):
        add('first54variant-byte',state(units=(unit(1),),modifiers=(ModifierRecord(54,flag,100),ModifierRecord(54,1,3))),'armor')
    special=(0,0x80000000,0x3e4ccccd,0xbf800000,0x7f800000,0xff800000,0x7fc00001)
    for a in special:
        for cap in special:add('armor-select-nonfinite',state(armor_1392_bits=a,armor_cap_1572_bits=cap,units=(unit(),),modifiers=(ModifierRecord(54,1,30),)),'armor')
    for position in(6.999999,7,7.000001,8,20):
        for marker in(0,1,0xffffffff):
            for t in(-1,0,.5,1,2):
                u=unit(position,marker=marker,start_x_bits=bits(-position),movement_time_bits=bits(10-t),movement_duration_bits=bits(1))
                add('moving-nearby-armor-guard',state(units=(u,),modifiers=(ModifierRecord(54,1,7),)),'armor')
    for amount in(0,.25,1,10,30):
        for armor in(0,.1,.5,1):
            for shield,barrier in((0,0),(50,30),(50,0),(5,5)):
                add('armor-shield-exhaustion',state(armor_1392_bits=bits(armor),shield_1532_bits=bits(shield),barrier_1536_bits=bits(barrier)),amount=bits(amount))
    for mapid in(b'elwynn',b'duskwood',b'wsg',b'ungoro',b'naxx',b'unknown'):
        for members in(0,1,2,10,0xffffffff):
            add('party-map-member-wrap',state(mode_2574=1,map_id=mapid,wave_2532=members,minimum_one_2578=1),amount=bits(10))
    for n in range(7):
        for rank in(0,1,30,255):
            s=state(armor_1392_bits=bits(.2),nearby_reduction_1444_bits=bits(.3),units=tuple(unit(1,target_id=j+1)for j in range(n)),modifiers=(ModifierRecord(54,1,rank),))
            add('nearby-five-and54',s,source=1 if n else 0,attack=1)
    for spell in(0,11426):
        for remaining in(0,3,50):
            for amount in(1,10,50):
                s=state(shield_1532_bits=bits(30),barrier_1536_bits=bits(20),shield_source_1344=spell,shield_source_remaining_1348_bits=bits(remaining),buffs=(BuffRecord(7,spell,bits(1),bits(20)),))
                add('source-shield-cleanup',s,amount=bits(amount))
    for phase in(0,2,3,255):add('phase-guard',state(phase_2579=phase))
    for protection in(1,3,255):add('protection-guard',state(protection_2568=protection))
    for expiry in(9,10,11):add('active12-guard',state(buffs=(BuffRecord(12,expires24_bits=bits(expiry)),)))
    for minimum in(0,1,2,255):add('minimum-one-flag',state(minimum_one_2578=minimum),amount=bits(2000)if minimum else bits(10))
    return rows


def equal(expected,actual,key):
    if type(expected)is not type(actual):return False
    if expected==actual:return True
    if key.endswith('_bits')and isinstance(expected,int):return f.is_nan(expected)and f.is_nan(actual)
    return False


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={name:sha(ROOT/name)for name in SOURCE_FILES};assert before==IMPORT_SHA
    cases=corpus(args.phase=='pilot');out,manifest=build(['effective_armor','incoming_damage'])
    snap=out/'source-snapshot';snap.mkdir()
    for name,value in before.items():
        dest=snap/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes());assert sha(dest)==value
    fixture=out/'incoming135-fixtures.jsonl';fixture.write_text(''.join(json.dumps(c,allow_nan=False)+'\n'for c in cases))
    assert [json.loads(s)for s in fixture.read_text().splitlines()]==json.loads(json.dumps(cases))
    frozen={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
    assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_incoming135_oracle.mjs'),str(out),str(fixture)]
    result=out/'incoming135-results.jsonl';stderr=out/'incoming135-stderr.log';start=time.monotonic()
    with result.open('w')as stream,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned incoming oracle exceeded60s')
    if code:raise RuntimeError(f'Original incoming run failed: {out}')
    rows=[json.loads(s)for s in result.read_text().splitlines()];assert [x['id']for x in rows]==list(range(len(cases)))
    failures=[]
    for c,a in zip(cases,rows):
        assert c['expected'].keys()==a.keys()
        for key,value in c['expected'].items():
            if not equal(value,a[key],key):failures.append(dict(id=c['id'],field=key,expected=value,actual=a[key]))
    after={name:sha(ROOT/name)for name in SOURCE_FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    assert frozen=={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
    (out/'incoming135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),kinds=dict(Counter(c['kind']for c in cases)),mismatch_fields=len(failures),groups=dict(Counter(c['group']for c in cases)),source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),artifacts={p.name:sha(p)for p in(fixture,result,stderr,out/'incoming135-mismatches.json',out/'incoming135-runtime.json')},runtime=json.loads((out/'incoming135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),independent_expected_before_original=True,only_changed_section=7,limitations=['Incoming is a scalar projection with explicit pending registry/events/aura metadata, nonfatal or minimum-one protected state only.','Empty proc/event producers; reserve spill callbacks and death/revival not accepted.','Unit position interpolation and armor54 near<=7 are real full27375 comparisons; world terrain and unit AI are separate.'])
    (out/'incoming135-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_fields=len(failures),failures=failures[:12])))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
