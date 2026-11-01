#!/usr/bin/env python3
"""Independent kind0 selection/stat/sweep/continuation versus full1072."""
import argparse
from collections import Counter
from dataclasses import replace
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
from check_level_cycle135 import make_input,empty_sources,mixed_sources
SOURCE_FILES=('scripts/check_selection_cycle135.py','scripts/run_selection_cycle135_oracle.mjs',
 'scripts/check_level_cycle135.py','scripts/build_full135_oracle.py','scripts/full135_host.mjs',
 'scripts/build_upgrade134_oracle.py','reconstruction/core_spec/selection_cycle135.py',
 'reconstruction/core_spec/level_cycle135.py','reconstruction/core_spec/ability_state135.py',
 'reconstruction/core_spec/ability_upgrade135.py','reconstruction/core_spec/candidates135.py',
 'reconstruction/core_spec/derived_stats135.py','reconstruction/core_spec/derived_stats134.py',
 'reconstruction/core_spec/ability_state.py','reconstruction/core_spec/currency134.py',
 'reconstruction/core_spec/pickups134.py','reconstruction/core_spec/progression134.py',
 'reconstruction/core_spec/progression.py','reconstruction/core_spec/binary32.py',
 'reconstruction/core_spec/binary32_sqrt.py','reconstruction/core_spec/rng.py','reconstruction/core_spec/upgrade_values.py')
def source_hashes():return {n:sha(ROOT/n)for n in SOURCE_FILES}
IMPORT_SOURCES=source_hashes()
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state135 import AbilityModifier135,DEFINITIONS
from core_spec.candidates135 import Candidate
from core_spec.currency134 import CurrencyState
from core_spec.level_cycle135 import from_dict
from core_spec.pickups134 import PickupRecord,decode_record56,encode_record56
from core_spec.selection_cycle135 import SelectionCycleState,select_card,projection


def fixture(group,name='cleave',variant='new',tier=0,kinds=(0,),owned=(),pending=1,level=1,
            picks=(),mode=0,members=1,gate=0,flag=0,sources=None,steps=1,class_byte=1,race=1,mods=()):
    raw=make_input(class_byte=class_byte,race_byte=race,level=level,phase=2,mode=mode,pending=pending,
        gate2572=gate,flags2573=flag,sources=empty_sources()if sources is None else sources,owned=owned)
    raw['selection_kind2585']=0
    card=dict(variant=variant,tier=tier,ability_id=name if variant!='gold'else'',owned_index=0,kinds=list(kinds)if variant=='upgrade'else[],gold=25 if variant=='gold' else 0)
    currency=dict(gold=0xffffffff-10,earned=20,multiplier_bits=raw['derived_bits']['1588'],mode=mode,local_peer=42,
        member_count=members,region_index=0,queue=[],queue_capacity=0,player_fields=[])
    control=dict(pending_kind1=0,pending_kind2=0,player_x_bits=0,player_y_bits=0,game_tag=0,
        currency=currency,region_id='elwynn',xp_queue=[],xp_queue_capacity=0,
        pickup_hex=[encode_record56(p).hex()for p in picks],definition_pointer=DEFINITIONS[name.encode()].pointer,
        modifiers=[dict(kind=m.kind,value_bits=m.value_bits,filter_tag=m.filter_tag,filter_value=m.filter_value,
            ability_id_hex=m.ability_id.hex(),ability_ids_hex=[x.hex()for x in m.ability_ids])for m in mods])
    return dict(group=group,input=raw,control=control,card=card,choice_indices=[0]*steps)


def inputs(phase):
    rows=[fixture('new-return-running'),fixture('upgrade-return-running',variant='upgrade',owned=('cleave',),kinds=(0,1),tier=4),
          fixture('gold-return-running',variant='gold'),fixture('next-choice-kind0',pending=3,steps=4,mode=1),
          fixture('sweep-multilevel-marker',picks=(PickupRecord(marker=1,arrival_bits=f.from_float(999),amount=1000,x_bits=f.from_float(100)),),steps=6,mode=1)]
    if phase=='pilot':return rows
    for name in DEFINITIONS:
        for tier in (0,4):rows.append(fixture('all114-new-stat-finish',name=name.decode(),tier=tier,mode=1))
    for cls in(1,2,3,4,5,7,8,9,11):
        for race in range(1,9):
            for variant in('new','upgrade','gold'):
                rows.append(fixture('class-race-mixed-sources',variant=variant,owned=('cleave',)if variant=='upgrade'else(),
                    kinds=(0,1,2),tier=3,class_byte=cls,race=race,sources=mixed_sources(),mode=1))
    for pending in(0,1,2,4,0xffffffff):
        for gate in(0,1,2,255):
            for flag in(0,1,2,255):rows.append(fixture('pending-gate-control',pending=pending,gate=gate,flag=flag,mode=1,steps=3))
    for marker in(0,1):
        for x in(0,8.999999,9,9.000001,100):
            for amount in(0,1,200,0xffffffff):
                rows.append(fixture('sweep-marker-radius-amount',mode=1,level=1,steps=3,picks=(
                    PickupRecord(marker=marker,arrival_bits=f.from_float(999),amount=amount,x_bits=f.from_float(x),guid=123),
                    PickupRecord(marker=0,arrival_bits=0,kind=1,amount=10,x_bits=0,guid=456))))
    for mode in(0,1,2,7,255):
        for members in(0,1,2,255,0xffffffff):
            for amount in(1,100,1000):rows.append(fixture('party-xp-and-gold',variant='gold',mode=mode,members=members,steps=3,
                picks=(PickupRecord(marker=1,arrival_bits=0,amount=amount,guid=11),)))
    for seed in range(16):
        mods=tuple(AbilityModifier135(k,f.from_float(.1*(k+1)))for k in range(7))
        rows.append(fixture('explicit-additional-modifiers',name='fireball',mode=1,mods=mods,tier=seed%5,pending=2,steps=3))
    return rows


def state_for(c):
    level=from_dict(c['input']);card=dict(c['card']);card['kinds']=tuple(card['kinds']);level=replace(level,candidates=(Candidate(**card),))
    control=c['control'];currency=CurrencyState(**control['currency'])
    return SelectionCycleState(level,control['pending_kind1'],control['pending_kind2'],
        tuple(decode_record56(bytes.fromhex(x))for x in control['pickup_hex']),control['player_x_bits'],control['player_y_bits'],
        currency,control['game_tag'],tuple(tuple(x)for x in control['xp_queue']),control['xp_queue_capacity'])


def modifiers(c):
    return tuple(AbilityModifier135(m['kind'],m['value_bits'],m['filter_tag'],m['filter_value'],bytes.fromhex(m['ability_id_hex']),tuple(bytes.fromhex(x)for x in m['ability_ids_hex']))for m in c['control']['modifiers'])


def corpus(phase):
    result=[]
    for i,c in enumerate(inputs(phase)):
        c['id']=i;state=state_for(c);expected=[];statuses=[]
        for index in c['choice_indices']:
            answer=select_card(state,index,additional_modifiers=modifiers(c));state=answer.state
            expected.append(projection(state));statuses.append(dict(status=answer.status,accepted=answer.accepted,swept_base_xp=answer.swept_base_xp,awarded_xp=answer.awarded_xp))
        c['expected']=expected;c['model_events']=statuses;result.append(c)
    return json.loads(json.dumps(result,allow_nan=False))


def differences(want,got,path=()):
    if isinstance(want,dict):
        if set(want)!=set(got):return[(path,'keys',list(want),list(got))]
        out=[]
        for key,value in want.items():out+=differences(value,got[key],path+(key,))
        return out
    if isinstance(want,list):
        if not isinstance(got,list)or len(want)!=len(got):return[(path,'length',len(want),len(got))]
        out=[]
        for i,(a,b)in enumerate(zip(want,got)):
            if path==('live_effects',)and a['kind']==12 and a['spell_id']==1020:
                b=dict(b);b['value_bits']=a['value_bits'] # Original4600 leaves this inactive union word unwritten.
            out+=differences(a,b,path+(i,))
        return out
    if want==got and type(want)is type(got):return[]
    integer_derived='derived_bits'in path and str(path[-1])in('1592','1608')
    is_float=(path and not integer_derived and(path[-1]in('current_hp_bits','speed_bits','value_bits','expires_bits')or'derived_bits'in path or'auxiliary_bits'in path))
    if is_float and type(want)is int and type(got)is int and f.is_nan(want)and f.is_nan(got):return[]
    return[(path,'value',want,got)]


def comparator_contracts():
    # These are pure comparator contracts, not additional original cases.
    for key in('1592','1608'):
        if not differences({'derived_bits':{key:0x7fc00001}},{'derived_bits':{key:0xffc00002}}):
            raise AssertionError('Integer derived words must not use NaN equivalence: '+key)
    if differences({'derived_bits':{'1536':0x7fc00001}},{'derived_bits':{'1536':0xffc00002}}):
        raise AssertionError('Declared floating NaNs retain classification policy')
    return dict(integer_nan_style_pairs_rejected=2,declared_float_nan_classification_pair_accepted=1,original_WASM_cases=0)


def main(phase):
    sources=source_hashes()
    if sources!=IMPORT_SOURCES:raise ValueError('Sources changed after import')
    contracts=comparator_contracts()
    cases=corpus(phase);out,manifest=build(['select_ability'])
    for n,h in sources.items():
        p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
        if sha(p)!=h:raise ValueError('Snapshot changed')
    casefile=out/'selection-cycle135-cases.json';casefile.write_text(json.dumps(cases,separators=(',',':'))+'\n')
    # Runner expects JSONL; persist an independent single-case per line interchange.
    casefile.write_text(''.join(json.dumps(c,separators=(',',':'))+'\n'for c in cases))
    frozen={p.name:sha(p)for p in(casefile,out/'manifest.json',out/manifest['module_file'])}
    runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    if sha(runtime)!='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0':raise ValueError('Pinned runtime differs')
    command=[str(runtime),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_selection_cycle135_oracle.mjs'),str(out),str(casefile)]
    resultfile=out/'selection-cycle135-original-results.jsonl';stderrfile=out/'selection-cycle135-stderr.log';start=time.monotonic()
    with resultfile.open('w')as stdout,stderrfile.open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned1072 deadline')
    process=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60,command=command)
    (out/'process.json').write_text(json.dumps(process,indent=2)+'\n')
    if code:raise RuntimeError('Original1072 failed; evidence '+str(out))
    persisted=[json.loads(x)for x in casefile.read_text().splitlines()]
    if persisted!=cases:raise ValueError('Fixture readback differs')
    rows=[json.loads(x)for x in resultfile.read_text().splitlines()];ids=[(c['id'],i)for c in cases for i in range(len(c['expected']))]
    if[(r['id'],r['step'])for r in rows]!=ids:raise ValueError('Result order/count/uniqueness differs')
    failures=[]
    for row in rows:failures += [dict(id=row['id'],step=row['step'],path=list(p),kind=k,expected=a,actual=b)for p,k,a,b in differences(cases[row['id']]['expected'][row['step']],row['projection'])]
    (out/'mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
    if source_hashes()!=sources or sha(SOURCE)!=SOURCE_SHA or any(sha(out/n)!=h for n,h in frozen.items()):raise ValueError('Source/artifact drift')
    report=dict(version='0.135.1',build='0898d5e3',phase=phase,cases=len(cases),entry_calls=len(rows),mismatch_fields=len(failures),groups=dict(Counter(c['group']for c in cases)),
        source_sha256_before=sources,source_sha256_after=source_hashes(),module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
        process=process,runtime=json.loads((out/'selection-cycle135-runtime.json').read_text()),evidence_directory=str(out.relative_to(ROOT)),
        artifact_sha256={p.name:sha(p)for p in(casefile,resultfile,out/'mismatches.json',stderrfile)},
        comparison_scope='Complete declared selection/stat/XP/phase/candidate projection; freshkind12/spell1020 inactive union value word excluded, all other declared scalar fields compared',
        uninitialized_union_field_policy='4600 does not write freshkind12+12, so value_bits is semantically canonical0 and explicitly not a raw heap prediction',
        comparator_contracts=contracts,integer_derived_offsets_compared_strictly=[1592,1608],
        pending=['Real producers/world/messages/physical tree and queue allocation','kind1/2 metadata generation','Full frame/gameplay scheduling'],full_game_started=False)
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    if phase=='full'and not failures:(ROOT/'reports/2026-11-01-selection-cycle0135.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),entry_calls=len(rows),mismatches=len(failures),failures=failures[:12]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');a=p.parse_args();main(a.phase)
