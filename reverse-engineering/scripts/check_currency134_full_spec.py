#!/usr/bin/env python3
"""Independent currency134 predictions versus complete original2862 kind1.

Only collect_pickups is exported. Original tree insertion, vector growth,
ordered deletion and despawn creation execute unchanged. Expected numeric
awards, queues and player fields are produced before launch by currency134.py.
"""
from collections import Counter
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import signal
import struct
import subprocess
import sys
import time

from build_full134_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha

SOURCE_FILES=('scripts/check_currency134_full_spec.py','scripts/run_currency134_full_oracle.mjs',
    'scripts/build_full134_oracle.py','scripts/build_upgrade134_oracle.py','scripts/full134_host.mjs',
    'reconstruction/core_spec/currency134.py','reconstruction/core_spec/binary32.py',
    'reconstruction/core_spec/progression134.py')
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
RECORD_PATH=ROOT/'evidence/currency0134-chain-20261101T022005.805413Z/prior-original-case0-kind1-record.bin'
RECORD_SHA='5a9ce3d687c7a0ce1972779f91857ee42b30efee0d6d9a07bd112470fb1a638b'
SEED=0xa2e02871


def source_hashes():
    return {p:sha(ROOT/p) for p in SOURCE_FILES}


IMPORT_HASHES=source_hashes()
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.currency134 import CurrencyState, apply_currency


def corpus():
    if sha(RECORD_PATH)!=RECORD_SHA:
        raise ValueError('Prior actual original kind1 record differs')
    original=RECORD_PATH.read_bytes()
    original_words=struct.unpack('<14I',original)
    if (original_words[0],original_words[2],original_words[3],original_words[9])!=(0,1,4,9004):
        raise ValueError('Unexpected prior original record')
    b=f.from_float;player=(b(-9396),b(-633));cases=[]
    def record(amount=4,marker=0,arrival=None,dx=None,dy=None,guid_delta=0):
        raw=bytearray(original);struct.pack_into('<I',raw,0,marker);struct.pack_into('<I',raw,12,amount)
        if arrival is not None:struct.pack_into('<I',raw,4,arrival)
        if dx is not None:struct.pack_into('<I',raw,40,f.add(player[0],b(dx)))
        if dy is not None:struct.pack_into('<I',raw,44,f.add(player[1],b(dy)))
        guid=struct.unpack_from('<Q',raw,16)[0]
        struct.pack_into('<Q',raw,16,(guid+guid_delta)&0xffffffffffffffff)
        return bytes(raw)
    def guid(raw):return f'{struct.unpack_from("<Q",raw,16)[0]:016x}'
    def snapshot(state,remaining,capacity,messages,phase):
        return {'gold':state.gold,'earned':state.earned,'queue_capacity':state.queue_capacity,
            'queue_count':len(state.queue),'queue_entries':[list(row)for row in state.queue],
            'player_fields':[list(row)for row in state.player_fields],
            'tree_present':bool(state.player_fields),'pickup_capacity':capacity,
            'pickup_count':len(remaining),'record_hex':[raw.hex()for raw in remaining],
            'rng':[1,2,3,4],'messages':list(messages),'phase':phase}
    def add(group,records=None,eligible=None,scale=0x3f800000,mode=0,members=1,
            region=('',0),gold=0,earned=0,warmup=False,queue=(),queue_capacity=None,
            radius=0x41100000,phase=1):
        records=[original] if records is None else list(records)
        eligible=list(range(len(records))) if eligible is None else list(eligible)
        if eligible!=sorted(set(eligible)) or any(i<0 or i>=len(records)for i in eligible):
            raise ValueError('Bad explicit fixture eligible indices')
        if queue_capacity is None:queue_capacity=len(queue)
        state=CurrencyState(gold=gold,earned=earned,multiplier_bits=scale,mode=mode,
            local_peer=42,member_count=members,region_index=region[1],queue=tuple(queue),
            queue_capacity=queue_capacity)
        initial=json.loads(json.dumps(asdict(state)));messages=[];expected={};capacity=max(1,len(records))
        warmup_raw=record(0) if warmup else None
        if warmup:
            result=apply_currency(state,0)
            if result.status!='core_projection':raise ValueError('Warmup outside model domain')
            state=result.state;messages.append({'opcode':170,'length':8,'guid_hex':guid(warmup_raw)})
            expected['after_warmup']=snapshot(state,[],capacity,messages,phase)
        expected['before_target_tree_present']=bool(state.player_fields)
        awards=[];indices=[]
        for index in reversed(eligible):
            amount=struct.unpack_from('<I',records[index],12)[0]
            result=apply_currency(state,amount)
            if result.status!='core_projection':raise ValueError('Fixture outside currency model domain')
            state=result.state;awards.append(result.award);indices.append(index)
            messages.append({'opcode':170,'length':8,'guid_hex':guid(records[index])})
        remaining=[raw for index,raw in enumerate(records)if index not in eligible]
        expected['after_collection']=snapshot(state,remaining,capacity,messages,phase)
        cases.append({'id':len(cases),'group':group,'currency':initial,'region_id':region[0],
            'radius_bits':radius,'player_xy':list(player),'now_bits':b(10),'phase':phase,
            'rng':[1,2,3,4],'pickup_capacity':capacity,'record_hex':[raw.hex()for raw in records],
            'warmup_record_hex':warmup_raw.hex()if warmup_raw else None,
            'explicit_fixture_eligible_indices':eligible,'expected_dispatch_indices':indices,
            'model_awards':awards,'expected':expected,
            'record_provenance':{'original_record_sha256':RECORD_SHA,
                'unaltered_baseline':records==[original],
                'variants':'Declared amount/marker/arrival/xy/GUID mutations of prior actual original record'}})
    add('unaltered_original_record_radius9')
    add('unaltered_original_record_radius0_retained',eligible=[],radius=0)
    for marker in (0,1):
        for arrival in (b(10)-1,b(10),b(10)+1,0x7fc00001,0x7f800000,0xff800000):
            r=record(marker=marker,arrival=arrival)
            eligible=[0] if marker==1 and arrival in (b(10)-1,b(10),0xff800000) else []
            add('outside_radius_marker_arrival_guard',[r],eligible,radius=0)
            add('inside_radius_ignores_marker_arrival',[r],radius=b(9))
    for radius in (b(5)-1,b(5),b(5)+1):
        add('exact_3_4_5_radius_boundary',[record(dx=3,dy=4)],
            [0]if radius>=b(5)else [],radius=radius)
    for radius in (0x7fc00001,0x7f800000,0xff800000,b(-1)):
        add('nonfinite_radius_guard',[record()], [0]if radius==0x7f800000 else [],radius=radius)
    # Every currency expected value is produced by the production module.
    scales=[0,0x80000000,1,0x007fffff,0x3effffff,0x3f000000,0x3f000001,
        b(1),b(1.2),b(1.5),b(-1),b(10000),0x7f7fffff,0xff7fffff,
        0x7f800000,0xff800000,0x7fc00001,0xffc12345]
    amounts=[0,1,2,3,4,15,0x7fffffff,0xfffffffe,0xffffffff]
    for mode in (0,2,255):
        for scale in scales:
            for amount in amounts:
                add('round_nonfinite_saturation',[record(amount)],scale=scale,mode=mode,
                    gold=0xfffffffd,earned=0xfffffffe,warmup=bool(amount&1))
    for region in (('',0),('elwynn',0),('wsg',2),('ungoro',3),('naxx',11)):
        for members in (0,1,2,255,0xffffffff):
            for amount in (0,1,4,15,0xffffffff):
                add('mode1_region_member_divisor',[record(amount)],mode=1,members=members,
                    region=region,scale=b(1.2),warmup=bool(amount&1))
    queue_states=[((),0),((),4),(((90,100),),1),
        (((90,100),(91,200),(92,300),(93,400)),4),(((90,100),(91,200)),8)]
    for mode in (0,1,2,7,255):
        for old_queue,capacity in queue_states:
            for warmup in (False,True):
                rs=[record(amount,guid_delta=i)for i,amount in enumerate((1,2,4,15))]
                add('queue_reverse_order_growth_existing_tree',rs,mode=mode,members=2,
                    region=('ungoro',3),queue=old_queue,queue_capacity=capacity,warmup=warmup)
    for gold in (0,0xffff,0x10000,0x7fffffff,0xfffffffe,0xffffffff):
        for earned in (0,0xfffffffe,0xffffffff):
            for amount in (0,1,4,0xffffffff):
                add('gold_tally_and_copper_wrap',[record(amount)],gold=gold,earned=earned,warmup=True)
    for phase in (0,1,2,3,255):
        add('no_phase_entry_guard',[original],phase=phase)
    # Some records stay idle between removals; the original vector must retain order.
    for mode in (0,1,2):
        rs=[record(i+1,marker=i%2,arrival=b(9)if i in(1,5)else b(11),guid_delta=i)for i in range(7)]
        add('mixed_eligible_indices_preserve_remaining_order',rs,[1,5],radius=0,mode=mode,
            members=2,region=('wsg',2),warmup=True)
    rng=random.Random(SEED)
    for _ in range(256):
        mode=rng.choice((0,1,2,255));region=rng.choice((('',0),('wsg',2),('ungoro',3),('naxx',11)))
        rs=[record(rng.getrandbits(32),guid_delta=i)for i in range(rng.randrange(1,9))]
        old,cap=rng.choice(queue_states)
        add('seeded_numeric_and_reverse_vectors',rs,scale=rng.getrandbits(32),mode=mode,
            members=rng.choice((0,1,2,0xffffffff)),region=region,gold=rng.getrandbits(32),
            earned=rng.getrandbits(32),warmup=bool(rng.randrange(2)),queue=old,queue_capacity=cap)
    return cases


def compare(want,got,path=''):
    differences=[]
    if isinstance(want,dict):
        for key,value in want.items():
            if key not in got:differences.append({'field':path+key,'missing':True})
            else:differences+=compare(value,got[key],path+key+'.')
    elif want!=got:
        differences.append({'field':path.rstrip('.'),'expected':want,'actual':got})
    return differences


def main():
    frozen=source_hashes()
    if frozen!=IMPORT_HASHES or sha(SOURCE)!=SOURCE_SHA:raise ValueError('Pre-import/source freeze differs')
    if sha(RUNTIME)!=RUNTIME_SHA:raise ValueError('Pinned Node SHA differs')
    version=subprocess.check_output([str(RUNTIME),'--version'],text=True,timeout=10).strip()
    if version!='v22.23.4':raise ValueError('Pinned Node version differs')
    cases=corpus()  # All expectations exist before build or original execution.
    out,manifest=build(['collect_pickups'])
    manifest_hash=sha(out/'manifest.json');module_path=out/manifest['module_file']
    casefile=out/'currency134-cases.json';casefile.write_text(json.dumps(cases,indent=2,allow_nan=False)+'\n')
    case_hash=sha(casefile)
    if source_hashes()!=frozen:raise ValueError('Sources changed before target launch')
    beforefile=out/'currency134-source-freeze-before.json'
    beforefile.write_text(json.dumps({'source_sha256':frozen,'original_wasm_sha256':SOURCE_SHA,
        'module_sha256':manifest['module_sha256'],'builder_manifest_sha256':manifest_hash,
        'corpus_sha256':case_hash,'expected_case_count':len(cases),'runtime_sha256':RUNTIME_SHA,
        'original_results_read':False},indent=2,allow_nan=False)+'\n')
    resultsfile=out/'currency134-original-results.jsonl';stderrfile=out/'currency134-stderr.log'
    start=time.monotonic()
    with resultsfile.open('w')as stdout,stderrfile.open('w')as stderr:
        child=subprocess.Popen([str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',
            str(ROOT/'scripts/run_currency134_full_oracle.mjs'),str(out),str(casefile)],
            stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned oracle stopped at60s')
    duration=time.monotonic()-start
    if code:raise RuntimeError(f'Currency original runner exit{code}: {out}')
    rows=[json.loads(line)for line in resultsfile.read_text().splitlines()]
    if json.loads(casefile.read_text())!=cases or sha(casefile)!=case_hash:
        raise ValueError('Persisted corpus changed')
    if len(rows)!=len(cases)or[row['id']for row in rows]!=list(range(len(cases))):
        raise ValueError('Persisted results coverage/order/uniqueness')
    failures=[{'id':c['id'],'group':c['group'],'differences':d}
        for c,row in zip(cases,rows)if(d:=compare(c['expected'],row))]
    mismatchfile=out/'currency134-mismatches.json';mismatchfile.write_text(json.dumps(failures,indent=2,allow_nan=False)+'\n')
    runtimefile=out/'currency134-runtime.json';runtime=json.loads(runtimefile.read_text())
    after=source_hashes()
    if frozen!=after or sha(SOURCE)!=SOURCE_SHA or sha(RUNTIME)!=RUNTIME_SHA:
        raise ValueError('Final source/runtime freeze changed')
    if sha(out/'manifest.json')!=manifest_hash or sha(module_path)!=manifest['module_sha256']:
        raise ValueError('Final module/manifest identity changed')
    afterfile=out/'currency134-source-freeze-after.json'
    afterfile.write_text(json.dumps({'source_sha256':after,'original_wasm_sha256':sha(SOURCE),
        'module_sha256':sha(module_path),'builder_manifest_sha256':sha(out/'manifest.json'),
        'corpus_sha256':sha(casefile),'runtime_sha256':sha(RUNTIME),'stable':True},
        indent=2,allow_nan=False)+'\n')
    if runtime['actual_host_calls']!=0 or runtime['denied_function_imports']!=878:
        raise ValueError('Host boundary failed')
    receipt={'version':'0.134.0','build':'983346a7','original_wasm_sha256':SOURCE_SHA,
        'module_sha256':manifest['module_sha256'],'original_full_entry':2862,
        'unchanged_original_currency_callees':[31731,28795],'case_count':len(cases),
        'mismatch_count':len(failures),'groups':dict(sorted(Counter(c['group']for c in cases).items())),
        'model_expected_before_original_launch':True,'production_currency_model_used':True,
        'record_provenance':{'path':str(RECORD_PATH.relative_to(ROOT)),'sha256':RECORD_SHA,
            'origin':'prior original full914 case0/after_death/record0; complete56B copied or declared synthetic variants'},
        'fields_compared':list(cases[0]['expected']['after_collection']),
        'warmup_cases':sum(c['warmup_record_hex']is not None for c in cases),
        'missing_tree_target_cases':sum(not c['expected']['before_target_tree_present']for c in cases),
        'existing_tree_target_cases':sum(c['expected']['before_target_tree_present']for c in cases),
        'actual_missing_key_insert_cases':sum(not c['expected']['before_target_tree_present']
            and bool(c['explicit_fixture_eligible_indices'])for c in cases),
        'actual_existing_key_update_cases':sum(c['expected']['before_target_tree_present']
            and bool(c['explicit_fixture_eligible_indices'])for c in cases),
        'normal_original_tree_insert_and_existing_key_update_exercised':
            any(not c['expected']['before_target_tree_present']and c['explicit_fixture_eligible_indices']for c in cases)
            and any(c['expected']['before_target_tree_present']and c['explicit_fixture_eligible_indices']for c in cases),
        'observed_tree_depths':sorted({row['after_collection']['tree_depth']for row in rows}),
        'runtime':runtime,'owned_process':{'runtime_path':str(RUNTIME),'version':version,
            'runtime_sha256':RUNTIME_SHA,'flags':['--max-old-space-size=512','--wasm-max-mem-pages=512'],
            'deadline_seconds':60,'seconds':round(duration,3),'exit_code':code},
        'source_sha256_before':frozen,'source_sha256_after':after,
        'builder_manifest_sha256':manifest_hash,
        'artifact_sha256':{p.name:sha(p)for p in(casefile,resultsfile,mismatchfile,runtimefile,stderrfile,
            beforefile,afterfile)},
        'run_directory':str(out.relative_to(ROOT)),
        'limitations':['Only kind1 records with normal marker0/1,empty claims/aux; no XP or other-kind callback composition.',
            'Original tree insertion and existing key1176 update tested at depth0; deeper/multi-key search remains pending.',
            'Despawn opcode170/length8/GUID queue entries compared; later player-field wire flush and transport are pending.',
            'Producer1820/death914,account transfer/persistence,full game/app start and network not exercised.',
            'Indirect error/panic/allocation-failure callbacks remain unchanged in original but are not deliberately triggered.']}
    receiptfile=out/'currency134-comparison.json';receiptfile.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'run':str(out),'cases':len(cases),'mismatches':len(failures),'receipt_sha256':sha(receiptfile)}))
    if failures:raise SystemExit('Currency model differs; notify root before any model change')


if __name__=='__main__':main()
