#!/usr/bin/env python3
"""Execute independent stats model against isolated original1573 numeric stores.

Synthetic cases cover selector/level boundaries, separate tag domains, ordered
mixed records, soul_link append, timed expiry and 32B dominance/special-ID paths.
NaN payloads are compared by classification; all non-NaN bits must match exactly.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

from build_stats_oracle import build
from wasm_index import sha

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.derived_stats import (StatsInput,Modifier,Adjustment,TimedRecord,TimedDefinition,
                                     LiveEffect,recalculate,input_from_dict)
from core_spec.binary32 import from_float,is_nan,mul

RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_VERSION='v22.23.4'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
RUNTIME_FLAGS=('--max-old-space-size=512','--wasm-max-mem-pages=512')


def run_fixed_oracle(script,arguments,output_file,stderr_file):
    """Run only the project-pinned Node, with owned process and memory limits."""
    before=sha(RUNTIME)
    version=subprocess.check_output([str(RUNTIME),'--version'],text=True,timeout=10).strip()
    if before!=RUNTIME_SHA or version!=RUNTIME_VERSION:
        raise ValueError('Pinned project Node identity differs')
    command=[str(RUNTIME),*RUNTIME_FLAGS,str(script),*[str(a) for a in arguments]]
    start=time.monotonic()
    with output_file.open('w') as stream,stderr_file.open('w') as err:
        child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise RuntimeError('Owned stats oracle exceeded60s and was stopped')
    duration=time.monotonic()-start
    if sha(RUNTIME)!=before:raise ValueError('Pinned Node changed during execution')
    if code:raise RuntimeError(f'Stats oracle failed with exit{code}; inspect {stderr_file}')
    return {'runtime_path':str(RUNTIME),'runtime_version':version,'runtime_sha256':before,
            'runtime_flags':list(RUNTIME_FLAGS),'exit_code':code,'runner_seconds':round(duration,3),
            'subprocess_deadline_seconds':60,'stderr_file':stderr_file.name,
            'stderr_bytes':stderr_file.stat().st_size,'stderr_sha256':sha(stderr_file)}


def checked_result_rows(result_file,fixture_file,expected_fixtures):
    """Validate persisted fixture/result identity, coverage, uniqueness and order."""
    persisted=[json.loads(line) for line in fixture_file.read_text().splitlines()]
    rows=[json.loads(line) for line in result_file.read_text().splitlines()]
    wanted=list(range(len(expected_fixtures)))
    if persisted!=expected_fixtures:raise ValueError('Persisted fixture content differs')
    for label,values in (('fixture',persisted),('result',rows)):
        ids=[row.get('id') for row in values]
        if (any(type(i) is not int for i in ids) or ids!=wanted
                or len(set(ids))!=len(wanted)):
            raise ValueError(f'Persisted {label} IDs/coverage/order/uniqueness differ')
    return rows


def cases():
    def row(group,state):return {'group':group,'input':asdict(state)}
    for c in range(256):yield row('class-selector',StatsInput(class_byte=c))
    for r in range(256):yield row('race-selector',StatsInput(race_byte=r))
    levels=list(range(100))+[127,255,65535,0xffffff,0x1000000,0x1000001,0x7fffffff,0xfffffffe,0xffffffff]
    for level in levels:
        for cls in (1,2,3,4,5,7,8,9,11):
            yield row('class-level',StatsInput(class_byte=cls,level=level,race_byte=(level%8)+1))
    special=[0,0x80000000,1,0x80000001,0x3dcccccd,0xbdcccccd,0x3f800000,
             0xbf800000,0x3fc00000,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,
             0x7fc00000,0xffc00001]
    for tag in list(range(20))+[255,256,0xffffffff]:
        for value in special:yield row('passive-tag',StatsInput(passives=[Modifier(tag,value)]))
    for tag in list(range(24))+[255,256,0xffffffff]:
        for value in special:
            for auxiliary in (0x3dcccccd,0x7fc00000):
                yield row('adjustment-tag',StatsInput(adjustments=[Adjustment(tag,value,auxiliary)]))
    for tag in list(range(40))+[255,256,0xffffffff]:
        for value in special:yield row('item-tag',StatsInput(item_modifiers=[Modifier(tag,value)]))
    for oldmax in special:
        for hp in special:yield row('hp-select',StatsInput(old_max_hp_bits=oldmax,current_hp_bits=hp))
    for ranks in ([],[['soul_link',0]],[['soul_link',1]],[['soul_link',255]],
                  [['not_soul_link',1],['soul_link',17]],[['soul_link',0],['soul_link',3]],
                  [['soul_link',3],['soul_link',0]]):
        for tag32 in special:
            for count in (1,3,4,5,8):
                yield row('owned-soul-link',StatsInput(owned_skills=ranks,item_modifiers=[Modifier(32,tag32)]*count))
    for now in (0,0x3f800000,0x7f800000,0x7fc00000):
        for expiry in special:
            for count in (0,1,0xffffffff):
                yield row('timed-expiry',StatsInput(now_bits=now,
                    timed_definitions=[TimedDefinition(27,0x3dcccccd,5),TimedDefinition(26,0x3f800000,2)],
                    timed_records=[TimedRecord(0,count,expiry),TimedRecord(1,1,expiry),TimedRecord(2,1,expiry)]))
    # Type8/9 share a dominance comparison; other types supply zero comparands.
    values=[0xbf800000,0x80000000,0,0x3f000000,0x3f800000,0x7fc00000]
    for first_type in (0,7,8,9,10):
        for second_type in (0,7,8,9,10):
            for a in values:
                for b in values:
                    for spell in (1,774,23451,23505):
                        yield row('live-dominance',StatsInput(live_effects=[
                            LiveEffect(first_type,a,spell,0x41200000),LiveEffect(second_type,b,spell,0x41200000)]))
    for now in (0,0x3f800000,0x7f800000,0x7fc00000):
        for expiry in special:
            yield row('live-expiry',StatsInput(now_bits=now,live_effects=[
                LiveEffect(8,0x3dcccccd,1,expiry),LiveEffect(9,0x3e4ccccd,1,0x41200000)]))
    rng=random.Random(1573)
    finite=[from_float(x) for x in (-5,-1,-.6,-.1,0,.01,.1,.2,.6,1,2,5,100)]
    for _ in range(600):
        sample=lambda:rng.choice(finite)
        yield row('mixed-ordered',StatsInput(class_byte=rng.randrange(256),race_byte=rng.randrange(256),level=rng.randrange(200),
            old_max_hp_bits=sample(),current_hp_bits=sample(),now_bits=sample(),
            conditional268_bits=sample(),flag2294=rng.randrange(2),
            passives=[Modifier(rng.randrange(17),sample()) for _ in range(rng.randrange(16))],
            adjustments=[Adjustment(rng.randrange(24),sample(),sample()) for _ in range(rng.randrange(12))],
            item_modifiers=[Modifier(rng.randrange(38),sample()) for _ in range(rng.randrange(20))],
            owned_skills=[['soul_link',rng.randrange(256)]],
            timed_definitions=[TimedDefinition(27,sample(),rng.randrange(34)) for _ in range(4)],
            timed_records=[TimedRecord(rng.randrange(6),rng.randrange(5),sample()) for _ in range(8)],
            live_effects=[LiveEffect(rng.choice([0,8,9]),sample(),rng.choice([1,774,23451,23505]),sample()) for _ in range(rng.randrange(8))]))


def equivalent(a,b):return a==b or (is_nan(a) and is_nan(b))


def spec_source_hashes():
    names=('reconstruction/core_spec/derived_stats.py','reconstruction/core_spec/binary32.py',
           'reconstruction/core_spec/progression.py','scripts/build_stats_oracle.py',
           'scripts/check_stats_spec.py','scripts/run_stats_oracle.mjs',
           'scripts/check_stats_full_spec.py','scripts/run_stats_full_oracle.mjs')
    return {name:sha(ROOT/name) for name in names}


def check(oracle_dir=None):
    if oracle_dir is None:oracle_dir,_=build()
    oracle_dir=Path(oracle_dir).resolve()
    manifest=json.loads((oracle_dir/'manifest.json').read_text())
    wasm=oracle_dir/manifest['module_file']
    if sha(wasm)!=manifest['module_sha256']:raise ValueError('Oracle module identity differs')
    fixtures=[];expected={};groups=Counter()
    for i,c in enumerate(cases()):
        state=input_from_dict(c['input']);result=recalculate(state)
        c.update({'id':i,'oracle_speed_bits':mul(result['derived_bits']['1196'],0x40e00000)})
        fixtures.append(c);expected[i]=result;groups[c['group']]+=1
    casefile=oracle_dir/'fixtures.jsonl';casefile.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in fixtures))
    outfile=oracle_dir/'oracle-results.jsonl'
    runtime=run_fixed_oracle(ROOT/'scripts/run_stats_oracle.mjs',[wasm,casefile],outfile,
                             oracle_dir/'micro-oracle-stderr.log')
    failures=[];count=0;allocations=reserves=frees=0
    for got in checked_result_rows(outfile,casefile,fixtures):
        i=got['id'];want=expected[i];count+=1
        for domain in ('derived_bits','object_fields'):
            for key,value in want[domain].items():
                actual=got[domain][key]
                # Integer stores must not use NaN-classification equivalence.
                integer=(domain=='object_fields' and key!='1109') or (domain=='derived_bits' and key in ('1228','1244'))
                if not (value==actual if integer else equivalent(value,actual)):
                    failures.append({'id':i,'group':fixtures[i]['group'],'field':domain+'.'+key,
                                     'expected':f'{value:08x}','actual':f'{actual:08x}'})
        if not equivalent(want['current_hp_bits'],got['current_hp_bits']):
            failures.append({'id':i,'group':fixtures[i]['group'],'field':'current_hp_bits',
                             'expected':f"{want['current_hp_bits']:08x}",'actual':f"{got['current_hp_bits']:08x}"})
        if got['speed_bits']!=fixtures[i]['oracle_speed_bits']:raise ValueError('Unexpected speed path mutation')
        allocations+=got['allocation_calls'];reserves+=got['reserve_calls'];frees+=got['free_calls']
    if count!=len(fixtures):raise ValueError('Oracle result count differs')
    output={'cases':count,'case_groups':dict(groups),'passed':count-len({x['id'] for x in failures}),
            'mismatch_fields':len(failures),'failures':failures[:100],
            'nan_comparison':'classification only; every non-NaN result requires exact bits',
            'allocation_shim_calls':allocations,'vector_reserve_shim_calls':reserves,'free_shim_calls':frees,
            'fixture_sha256':sha(casefile),'results_sha256':sha(outfile),
            'persisted_fixture_ids_unique_and_ordered':True,'result_ids_unique_and_ordered':True,
            'runtime':runtime,
            'scope':'original1573 numeric body under substituted allocators; speed-message and BTree-insert paths bypassed',
            'oracle_directory':str(oracle_dir.relative_to(ROOT)),
            'source_sha256':spec_source_hashes(),
            'original_body_sha256':manifest['original_body_sha256'],'oracle_module_sha256':manifest['module_sha256']}
    (oracle_dir/'comparison.json').write_text(json.dumps(output,indent=2)+'\n')
    if failures:print(json.dumps(output,indent=2));raise SystemExit(1)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--oracle-directory',type=Path);args=parser.parse_args()
    print(json.dumps(check(args.oracle_directory),indent=2))
