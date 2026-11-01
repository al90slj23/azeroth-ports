#!/usr/bin/env python3
"""Differential XP/stats/heal/choice composition against full original4630.

No rewritten original callee or application start. Cases are generated from
independent production models before launching the pinned Node process.
"""
import argparse
from collections import Counter
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
SOURCE_FILES = ('scripts/check_level_cycle135.py','scripts/run_level_cycle135_oracle.mjs',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/full135_host.mjs',
 'reconstruction/core_spec/level_cycle135.py','reconstruction/core_spec/derived_stats135.py',
 'reconstruction/core_spec/progression134.py','reconstruction/core_spec/progression.py',
 'reconstruction/core_spec/candidates135.py','reconstruction/core_spec/ability_state.py',
 'reconstruction/core_spec/upgrade_values.py','reconstruction/core_spec/rng.py',
 'reconstruction/core_spec/binary32.py','reconstruction/core_spec/derived_stats134.py')
IMPORT_SOURCE_HASHES = {name:sha(ROOT/name) for name in SOURCE_FILES}
sys.path.insert(0, str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.candidates135 import DEFINITIONS, CLASS_KITS, CLASS_BYTE
from core_spec.derived_stats135 import StatsInput, input_from_dict, recalculate
from core_spec.level_cycle135 import from_dict, gain_xp, projection
from core_spec.progression134 import xp_threshold


RUNTIME = ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
CLASSES = (1,2,3,4,5,7,8,9,11)
SEED = 0xa2e046301513


def empty_sources():
    # This is a declared controlled snapshot, not a producer default.
    return dict(passives=[],adjustments=[],item_modifiers=[],owned_skills=[],
                timed_records=[],definitions=[],live_effects=[])


def mixed_sources():
    return dict(passives=[dict(tag=2,value_bits=f.from_float(50)),dict(tag=3,value_bits=f.from_float(.1))],
      adjustments=[dict(tag=2,value_bits=f.from_float(.2),definition32_bits=0),
                   dict(tag=12,value_bits=f.from_float(.3),definition32_bits=0)],
      item_modifiers=[dict(tag=10,value_bits=f.from_float(.4)),dict(tag=32,value_bits=f.from_float(1))],
      owned_skills=[['soul_link',3]],timed_records=[dict(definition_index=0,stack_count=2,expires_bits=f.from_float(20))],
      definitions=[dict(kind=27,value4_bits=0,value20_bits=f.from_float(.1),modifier_tag=0,summon_state41=0),
                   dict(kind=32,value4_bits=f.from_float(.5),value20_bits=0,modifier_tag=0,summon_state41=0),
                   dict(kind=33,value4_bits=0,value20_bits=0,modifier_tag=0,summon_state41=0),
                   dict(kind=42,value4_bits=0,value20_bits=0,modifier_tag=0,summon_state41=4)],
      live_effects=[dict(kind=8,value_bits=f.from_float(.3),spell_id=23451,expires_bits=f.from_float(30)),
                    dict(kind=9,value_bits=f.from_float(.2),spell_id=774,expires_bits=f.from_float(5))])


def make_input(*,class_byte=1,race_byte=1,level=1,phase=3,mode=0,heal_gate=0,
               hp_fraction=.2,pending=0,flag275=0,flag2581=1,flags2576=0,gate2572=0,flags2573=0,
               sources=None,rng_words=(1,2,3,4),owned=(),blocked=(),banished=(),luck=0):
    if sources is None:
        sources=empty_sources()
    # All source vectors are explicitly present in the interchange. Initial
    # derived words are independent fixture preparation, not a claimed game init.
    defs=[dict(kind=d['kind'],value20_bits=d['value20_bits'],modifier_tag=d['modifier_tag'])
          for d in sources['definitions']]
    stat_input=dict(class_byte=class_byte,race_byte=race_byte,level=level,old_max_hp_bits=0,
      current_hp_bits=0,now_bits=f.from_float(10),previous_speed_bits=f.from_float(7),
      conditional268_bits=f.from_float(luck),flag2574=mode,pool1532_bits=f.from_float(500),
      pool1536_bits=f.from_float(400),conditional1344_id=11426,conditional1348_bits=f.from_float(350),
      pool768_bits=f.from_float(450),passives=sources['passives'],adjustments=sources['adjustments'],
      item_modifiers=sources['item_modifiers'],owned_skills=sources['owned_skills'],
      timed_records=sources['timed_records'],timed_definitions=defs,live_effects=sources['live_effects'])
    initial=recalculate(input_from_dict(stat_input))
    scalar={k:v for k,v in stat_input.items() if k in {
      'class_byte','race_byte','old_max_hp_bits','current_hp_bits','now_bits','previous_speed_bits',
      'conditional268_bits','flag2574','pool1532_bits','pool1536_bits','conditional1344_id',
      'conditional1348_bits','pool768_bits'}}
    scalar.update(old_max_hp_bits=initial['derived_bits']['1536'],
                  current_hp_bits=f.mul(initial['derived_bits']['1536'],f.from_float(hp_fraction)),
                  previous_speed_bits=initial['speed_bits'])
    # Deliberately retain caller-given auxiliary pools; first1512 must clamp them.
    choice_owned=[dict(ability_id=n,record_hex=AbilityRecord(DEFINITIONS[n].pointer).to_bytes().hex())for n in owned]
    return dict(progression=dict(level=level,xp=0,pending_upgrades=pending),stats=scalar,
      sources=sources,derived_bits=initial['derived_bits'],player_fields={},rng_words=list(rng_words),
      choice_inputs=dict(owned=choice_owned,blocked_ids=list(blocked),banished_keys=list(banished),
                         flag275=flag275,flag2581=flag2581),
      phase2587=phase,selection_kind2585=255,generation_counter2400=0xffffffff,
      flags2576=flags2576,gate2572=gate2572,flags2573=flags2573,heal_gate387=heal_gate,
      pool756_bits=f.from_float(123.5))


def corpus(phase):
    rows=[]
    def add(group,raw,amounts):
        state=from_dict(raw);expected=[];events=[];draws=0
        for amount in amounts:
            r=gain_xp(state,amount)
            if r.status!='core_projection':raise ValueError('Fixture reached unresolved model boundary')
            state=r.state;expected.append(projection(state));events.extend(r.level_events);draws+=r.rng_draws
        # Normalize interchange tuple/list and numeric-key representations before original launch.
        rows.append(json.loads(json.dumps(dict(id=len(rows),group=group,input=raw,amounts=amounts,
          expected=expected,independent_level_events=events,predicted_rng_draws=draws),allow_nan=False)))
    for mode,phase_byte in ((0,3),(1,1)):
        for gate in (0,4,5,255):
            add('pilot-level-sequence',make_input(mode=mode,phase=phase_byte,heal_gate=gate),[4,1,50,100])
    for hp in (0,1,-.5,2):
        add('pilot-kind32-33-preserved-level-up-cause0',make_input(sources=mixed_sources(),hp_fraction=hp),[5,25])
    for flags in (0,1,2,255):
        add('pilot-actual-choice-inhibit-bit0',make_input(mode=1,phase=1,flags2576=flags),[5,100])
    for rawhp in (0x7fc00001,0x7f800000,0xff800000,0x80000000):
        r=make_input();r['stats']['current_hp_bits']=rawhp
        add('pilot-heal-NaN-infinity-and-zero',r,[5])
    if phase=='pilot':return rows
    for cls in CLASSES:
      for race in range(1,9):
       for level in (0,1,14,29,118,119,120):
        needed=xp_threshold(level)
        raw=make_input(class_byte=cls,race_byte=race,level=level,mode=1,phase=1,
          heal_gate=(cls+race)%8,hp_fraction=.1*(race%5),flag275=cls&1,flag2581=race&1,
          sources=mixed_sources() if race%2 else empty_sources(),luck=3 if race%3 else 100,
          rng_words=(cls,race,level+1,0x9e3779b9))
        add('all-class-race-level-stateful-choice',raw,[max(needed-1,0),1,min(f.MASK,needed*4),0])
    for gate in range(256):
        raw=make_input(class_byte=8,race_byte=8,heal_gate=gate,hp_fraction=-.1 if gate%3==0 else .2,
                       sources=mixed_sources())
        add('all-heal387-bytes-multilevel',raw,[sum(xp_threshold(n)for n in range(1,7)),5])
    for pending in (0,1,0xfffffffe,0xffffffff):
     for flags2576 in (0,1,2,128,255):
      for gate2572 in (0,1,2):
       for flags2573 in (0,1,2):
        add('pending-wrap-and-choice-guards',make_input(mode=1,phase=1,pending=pending,
          flags2576=flags2576,gate2572=gate2572,flags2573=flags2573),[5,100])
    for cls in CLASSES:
        kit=CLASS_KITS[CLASS_BYTE.get(cls,'warrior')]
        for count in range(7):
            add('owned-pool-derived-cooldown-choice',make_input(class_byte=cls,mode=1,phase=1,
                owned=kit[:count],sources=mixed_sources(),luck=3),[5,200])
    rng=random.Random(SEED)
    for _ in range(128):
        level=rng.randrange(0,120);cls=rng.choice(CLASSES);kit=CLASS_KITS[CLASS_BYTE.get(cls,'warrior')]
        raw=make_input(class_byte=cls,race_byte=rng.randrange(1,9),level=level,mode=1,phase=1,
          heal_gate=rng.randrange(256),sources=mixed_sources(),pending=rng.getrandbits(32),
          rng_words=tuple(rng.getrandbits(32)for _ in range(4)),owned=kit[:rng.randrange(7)],
          hp_fraction=rng.choice((0,.1,.5,1,2,-1)),luck=rng.choice((0,3,10,100)))
        add('seeded-complete-level-choice-sequences',raw,[rng.randrange(50000),rng.getrandbits(32),0])
    return rows


def differences(expected,actual,path=()):
    if isinstance(expected,dict):
        if not isinstance(actual,dict)or expected.keys()!=actual.keys():return [(path,'keys',expected,actual)]
        return [d for k,v in expected.items()for d in differences(v,actual[k],path+(k,))]
    if isinstance(expected,list):
        if not isinstance(actual,list)or len(expected)!=len(actual):return [(path,'length',expected,actual)]
        return [d for i,(a,b)in enumerate(zip(expected,actual))for d in differences(a,b,path+(i,))]
    if type(expected) is not type(actual):return [(path,'type',expected,actual)]
    float_word=(path[-1]in ('current_hp_bits','speed_bits') or 'auxiliary_bits'in path
                or ('derived_bits'in path and path[-1]not in ('1592','1608'))
                or ('player_fields'in path and path[-1]=='1109'))
    if expected!=actual and not(float_word and type(expected)is int and type(actual)is int and f.is_nan(expected)and f.is_nan(actual)):
        return [(path,'bits',expected,actual)]
    return []


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in SOURCE_FILES}
    if before!=IMPORT_SOURCE_HASHES:raise ValueError('Sources changed after import')
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Original source identity differs')
    cases=corpus(args.phase);out,manifest=build(['gain_experience'])
    module_file=out/manifest['module_file']; module_sha=sha(module_file); manifest_sha=sha(out/'manifest.json')
    snapshot=out/'source-snapshot';snapshot.mkdir()
    for name,value in before.items():
        target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
        if sha(target)!=value:raise ValueError('Source drift during snapshot')
    casefile=out/'level-cycle135-cases.jsonl'
    casefile.write_text(''.join(json.dumps(c,allow_nan=False)+'\n'for c in cases))
    fixture_sha=sha(casefile)
    if [json.loads(line) for line in casefile.read_text().splitlines()]!=cases:raise ValueError('Fixture readback differs')
    (out/'level-cycle135-source-before.json').write_text(json.dumps(before,indent=2)+'\n')
    if sha(RUNTIME)!=RUNTIME_SHA:raise ValueError('Pinned runtime differs')
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',
             str(ROOT/'scripts/run_level_cycle135_oracle.mjs'),str(out),str(casefile)]
    resultfile=out/'level-cycle135-original-results.jsonl';stderr=out/'level-cycle135-stderr.log'
    started=time.monotonic()
    with resultfile.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:exitcode=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise SystemExit('Owned original4630 process exceeded60s')
    if exitcode:raise SystemExit(f'Full original run exit{exitcode}; inspect {out}')
    actual=[json.loads(line)for line in resultfile.read_text().splitlines()]
    expected_ids=[(c['id'],j)for c in cases for j in range(len(c['amounts']))]
    if [(x['id'],x['step'])for x in actual]!=expected_ids:raise ValueError('Result IDs/order/count differ')
    mismatches=[]
    for row in actual:
        c=cases[row['id']];diff=differences(c['expected'][row['step']],row['projection'])
        if diff:mismatches.append(dict(id=row['id'],step=row['step'],group=c['group'],differences=diff))
    after={n:sha(ROOT/n)for n in SOURCE_FILES}
    if before!=after or sha(SOURCE)!=SOURCE_SHA:raise ValueError('Participating source drift')
    if sha(module_file)!=module_sha or sha(out/'manifest.json')!=manifest_sha or sha(casefile)!=fixture_sha:raise ValueError('Module/manifest/fixture drift')
    (out/'level-cycle135-source-after.json').write_text(json.dumps(after,indent=2)+'\n')
    mfile=out/'level-cycle135-mismatches.json';mfile.write_text(json.dumps(mismatches,indent=2,allow_nan=False)+'\n')
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,original_wasm_sha256=SOURCE_SHA,
      original_full_entry=4630,original_internal_callees_unchanged=True,only_changed_section=7,
      cases=len(cases),entry_calls=len(actual),mismatch_cases=len(mismatches),mismatch_fields=sum(len(x['differences'])for x in mismatches),
      groups=dict(Counter(c['group']for c in cases)),independent_level_iterations=sum(len(c['independent_level_events'])for c in cases),
      expected_generated_before_original_launch=True,source_sha256_before=before,source_sha256_after=after,
      module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
      runtime=json.loads((out/'level-cycle135-runtime.json').read_text()),
      process=dict(command=command,pid=child.pid,pgid=child.pid,owned_process_group=True,deadline_seconds=60,
                   exit_code=exitcode,elapsed_seconds=time.monotonic()-started,runtime_sha256=RUNTIME_SHA),
      artifact_sha256={x.name:sha(x)for x in (casefile,resultfile,mfile,stderr,out/'level-cycle135-runtime.json')},
      evidence_directory=str(out),limitations=[
        'Explicit synthetic original-allocator state; no original game startup or scheduler.',
        'Full4630 executes1512,10847,1453 and eligible2159; relevant projected state compared after every entry call, not instrumented inside each level.',
        'Every source vector explicitly supplied; original equipment/talent/modifier producers remain unrecovered.',
        'Level-up cause27960 firstword0 skips10847 special overheal branch even with kind32/33 definitions; general nonzero-cause healing is not implemented.',
        'Mode1 and flag2566=0 omit world/notification choices through original guards; candidate display payload, allocation, packet bytes and account-heal logs pending.',
        'All23 derived words, HP/aux/speed, six-key logical player tree, progression, RNG, candidate metadata and phase/control compared; not whole-game equivalence.',
        'Fixed0.135.1 numerical/choice projection; no whole-game or native-Windows equivalence claim.'])
    (out/'level-cycle135-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(run=str(out),cases=len(cases),entry_calls=len(actual),mismatch_cases=len(mismatches),mismatch_fields=receipt['mismatch_fields'])))
    if mismatches:raise SystemExit('Independent level composition differs from original')


if __name__=='__main__':main()
