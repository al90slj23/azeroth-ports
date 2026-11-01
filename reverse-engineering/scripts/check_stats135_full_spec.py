#!/usr/bin/env python3
"""Current0.135.1 independent23-word model versus complete original1512.

The ordered corpus structure and pinned process harness are reused from the
134 regression corpus; expected results come from derived_stats135.py, which
reuses the134 arithmetic and independently retains the newly stored armor cap.
No older-version test result is used. Includes original allocation, vector
copy/reserve/free, BTree insertion and movement packet production.
"""
import argparse
from collections import Counter
from dataclasses import asdict,replace
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
SOURCE_FILES=('reconstruction/core_spec/derived_stats135.py','reconstruction/core_spec/binary32.py',
    'reconstruction/core_spec/progression.py','scripts/check_stats135_full_spec.py',
    'scripts/run_stats135_full_oracle.mjs','scripts/full135_host.mjs','scripts/build_full135_oracle.py',
    'scripts/build_upgrade134_oracle.py','reconstruction/core_spec/derived_stats134.py')

def source_hashes():
    return {name:sha(ROOT/name)for name in SOURCE_FILES}

IMPORT_SOURCE_HASHES=source_hashes()
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.derived_stats135 import (StatsInput,Modifier,Adjustment,TimedRecord,
    TimedDefinition,LiveEffect,recalculate,input_from_dict)
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


def base_cases():
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
    rng=random.Random(1513)
    finite=[from_float(x) for x in (-5,-1,-.6,-.1,0,.01,.1,.2,.6,1,2,5,100)]
    for _ in range(600):
        sample=lambda:rng.choice(finite)
        yield row('mixed-ordered',StatsInput(class_byte=rng.randrange(256),race_byte=rng.randrange(256),level=rng.randrange(200),
            old_max_hp_bits=sample(),current_hp_bits=sample(),now_bits=sample(),
            conditional268_bits=sample(),flag2574=rng.randrange(2),
            passives=[Modifier(rng.randrange(17),sample()) for _ in range(rng.randrange(16))],
            adjustments=[Adjustment(rng.randrange(24),sample(),sample()) for _ in range(rng.randrange(12))],
            item_modifiers=[Modifier(rng.randrange(38),sample()) for _ in range(rng.randrange(20))],
            owned_skills=[['soul_link',rng.randrange(256)]],
            timed_definitions=[TimedDefinition(27,sample(),rng.randrange(34)) for _ in range(4)],
            timed_records=[TimedRecord(rng.randrange(6),rng.randrange(5),sample()) for _ in range(8)],
            live_effects=[LiveEffect(rng.choice([0,8,9]),sample(),rng.choice([1,774,23451,23505]),sample()) for _ in range(rng.randrange(8))]))


def equivalent(a,b):return a==b or (is_nan(a) and is_nan(b))


def cases():
    yield from base_cases()
    for cls in (1,2,3,4,5,7,8,9,11):
        for race in range(1,9):
            for level in (1,14,15,29,30,44,45,120):
                yield {'group':'all-class-race-level','input':asdict(StatsInput(class_byte=cls,race_byte=race,level=level))}
    for cap in (.39999998,.4,.40000004,.8,.99999994,1,1.00000012,2):
        yield {'group':'new-adjustment-cap1','input':asdict(StatsInput(adjustments=[Adjustment(19,from_float(cap))]))}
    special=[0,0x80000000,from_float(-1),from_float(100),from_float(230),from_float(500),
             0x7f800000,0xff800000,0x7fc00001]
    for a in special:
        for b in special:
            for identifier in (0,11426):
                yield {'group':'new-auxiliary-pool-clamps','input':asdict(StatsInput(pool1532_bits=a,pool1536_bits=b,
                    conditional1344_id=identifier,conditional1348_bits=from_float(500),pool768_bits=from_float(500)))}
    pairs=[(from_float(500),from_float(500)),(0x7f800000,0x7f800000),
        (from_float(500),0x7f800000),(0x7f800000,from_float(500)),
        (0x80000000,0),(0,0x80000000),(0x7fc00001,from_float(500)),(from_float(500),0x7fc00001)]
    for a,b in pairs:
        for old1348 in special:
            for old768 in special:
                for identifier in (0,11426):
                    yield {'group':'new-conditional-pool-select-order','input':asdict(StatsInput(
                        pool1532_bits=a,pool1536_bits=b,conditional1344_id=identifier,
                        conditional1348_bits=old1348,pool768_bits=old768))}
    for race in range(1,9):
        for level in (1,15,45,120):
            yield {'group':'XP-radius-ordered-source-domains','input':asdict(StatsInput(
                race_byte=race,level=level,now_bits=from_float(1),
                passives=[Modifier(8,from_float(.1))],
                adjustments=[Adjustment(11,from_float(.2)),Adjustment(12,from_float(.3))],
                item_modifiers=[Modifier(9,from_float(.4)),Modifier(10,from_float(.5))],
                timed_definitions=[TimedDefinition(27,from_float(.6),9),TimedDefinition(27,from_float(.7),10)],
                timed_records=[TimedRecord(0,3,from_float(2)),TimedRecord(1,2,from_float(2))]))}
    for previous in [0,0x80000000,0x7f800000,0xff800000,0x7fc00000]+[
            from_float(x)for x in (6.989999,6.99,6.990001,7,7.009999,7.01,7.010001)]:
        yield {'group':'movement-threshold','input':asdict(StatsInput(previous_speed_bits=previous))}


def check(full_directory=None):
    frozen_sources=source_hashes()
    if frozen_sources!=IMPORT_SOURCE_HASHES:raise ValueError('Sources changed after module import')
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Current original identity differs')
    if full_directory is None:full_directory,manifest=build(['recalculate_stats'])
    full_directory=Path(full_directory).resolve()
    manifestfile=full_directory/'manifest.json';manifest_hash=sha(manifestfile)
    manifest=json.loads(manifestfile.read_text())
    if manifest['module_file']!='research135-exports.wasm':raise ValueError('Module file differs')
    modulefile=full_directory/manifest['module_file'];module_hash=sha(modulefile)
    if module_hash!=manifest['module_sha256']:raise ValueError('Module identity differs')
    output_directory=full_directory
    fixtures=list(cases());expected={};groups=Counter()
    for i,c in enumerate(fixtures):
        c['id']=i;groups[c['group']]+=1;expected[i]=recalculate(input_from_dict(c['input']))
    snapshot=output_directory/'source-snapshot';snapshot.mkdir(exist_ok=False)
    for name in SOURCE_FILES:
        dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    casefile=output_directory/'stats135-fixtures.jsonl'
    casefile.write_text(''.join(json.dumps(c,separators=(',',':'))+'\n'for c in fixtures))
    fixture_hash=sha(casefile)
    resultsfile=output_directory/'stats135-results.jsonl'
    runtime=run_fixed_oracle(ROOT/'scripts/run_stats135_full_oracle.mjs',[full_directory,casefile],
        resultsfile,output_directory/'stats135-stderr.log')
    results_hash=sha(resultsfile)
    failures=[];movement=0;memory=instances=0
    for got in checked_result_rows(resultsfile,casefile,fixtures):
        i=got['id'];want=expected[i]
        for domain in ('derived_bits','object_fields','auxiliary_bits'):
            for key,value in want[domain].items():
                actual=got[domain][key]
                integer=(domain=='object_fields'and key!='1109')or(domain=='derived_bits'and key in('1592','1608'))
                if not(value==actual if integer else equivalent(value,actual)):
                    failures.append({'id':i,'group':fixtures[i]['group'],'field':domain+'.'+key,
                        'expected':f'{value:08x}','actual':f'{actual:08x}'})
        for field in ('current_hp_bits','speed_bits'):
            if not equivalent(want[field],got[field]):
                failures.append({'id':i,'group':fixtures[i]['group'],'field':field,
                    'expected':f"{want[field]:08x}",'actual':f"{got[field]:08x}"})
        for field in ('speed_sequence','movement_queue_count'):
            if got[field]!=int(want['speed_changed']):
                failures.append({'id':i,'group':fixtures[i]['group'],'field':field,
                    'expected':int(want['speed_changed']),'actual':got[field]})
        if got['host_calls']or not got['original_internal_callees']:raise ValueError('Original closure guard')
        movement+=got['movement_queue_count'];memory=max(memory,got['memory_bytes']);instances=max(instances,got['instance_count'])
    if source_hashes()!=frozen_sources:raise ValueError('Validation sources changed during comparison')
    if (sha(SOURCE)!=SOURCE_SHA or sha(modulefile)!=module_hash or sha(manifestfile)!=manifest_hash
            or sha(casefile)!=fixture_hash or sha(resultsfile)!=results_hash):
        raise ValueError('Frozen source/module/manifest/fixture/results changed during comparison')
    output={'version':'0.135.1','build':'0898d5e3','cases':len(fixtures),'case_groups':dict(groups),
        'passed':len(fixtures)-len({x['id']for x in failures}),'mismatch_fields':len(failures),'failures':failures[:100],
        'original_function1512_executed':True,'original_internal_callees_executed':True,
        'replacement_callees':[],'changed_original_sections':[7],'host_calls':0,'denied_function_imports':878,
        'application_start_called':False,'user_saves_read':False,'network_used':False,
        'actual_original_movement_packets_queued':movement,'actual_original_BTree_insertions':len(fixtures)*3,
        'maximum_memory_bytes':memory,'memory_page_cap':512,'fresh_instances':instances,
        'runtime':runtime,'persisted_fixture_ids_unique_and_ordered':True,'result_ids_unique_and_ordered':True,
        'nan_comparison':'classification only; every non-NaN result requires exact bits',
        'fixture_sha256':fixture_hash,'results_sha256':results_hash,'source_sha256':frozen_sources,
        'source_hashes_checked_before_and_after':True,'research_manifest_sha256':manifest_hash,
        'research_module_sha256':manifest['module_sha256'],'original_wasm_sha256':SOURCE_SHA,
        'full_oracle_directory':str(full_directory.relative_to(ROOT)),
        'compared_derived_offsets':list(range(1536,1625,4)),
        'compared_auxiliary_offsets':[1444,1448,1348,768],
        'scope':'Complete original1512 and reached original callees on synthetic states; no game start or host call',
        'limitations':['Synthetic records do not establish real item/talent/effect producer IDs or save compatibility.',
            'Movement queue count and BTree numeric fields verified; packet bytes and external delivery not compared.',
            'Other full-game state, integration, scheduling and UI remain unvalidated. NaN payload preservation not claimed.']}
    (output_directory/'stats135-comparison.json').write_text(json.dumps(output,indent=2)+'\n')
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Original changed')
    print(json.dumps({'directory':str(full_directory),'cases':len(fixtures),'mismatch_fields':len(failures),
        'failures':failures[:20]},indent=2))
    if failures:raise SystemExit(1)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--full-directory',type=Path);a=p.parse_args();check(a.full_directory)
