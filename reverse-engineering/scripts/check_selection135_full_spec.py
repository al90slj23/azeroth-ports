#!/usr/bin/env python3
"""Validate ordered135 upgrade records through unchanged complete selector1072."""
import argparse
from collections import Counter
from dataclasses import replace
import itertools
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
SOURCE_FILES=('scripts/check_selection135_full_spec.py','scripts/run_selection135_full_oracle.mjs',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/full135_host.mjs',
 'reconstruction/core_spec/ability_upgrade135.py','reconstruction/core_spec/ability_state135.py',
 'reconstruction/core_spec/ability_state.py','reconstruction/core_spec/upgrade_values.py',
 'reconstruction/core_spec/binary32.py')
def source_hashes():return {p:sha(ROOT/p)for p in SOURCE_FILES}
IMPORT_SOURCES=source_hashes()
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.ability_upgrade135 import AbilityRecord,UpgradeCard,apply_upgrade_card
from core_spec.ability_state135 import DEFINITIONS,initialize_ability


def corpus(phase):
    result=[]
    def add(name=b'cleave',kinds=(),tier=0,phase=2,index=0,variant='upgrade',group='ordered_upgrade'):
        definition=DEFINITIONS[name];record=AbilityRecord(definition.pointer)
        accepted=phase==2
        if variant=='new':expected=initialize_ability(definition,tier=tier,modifiers=())
        elif accepted and index==0:expected=apply_upgrade_card(record,UpgradeCard(index,tuple(kinds),tier),definition)
        else:expected=record
        i=len(result)
        result.append(dict(id=i,group=group,ability_id=name.decode(),definition_pointer=definition.pointer,
            execution_kind=definition.execution_kind,variant=variant,phase=phase,kinds=list(kinds),tier=tier,
            owned_index=index,input_hex=record.to_bytes().hex(),expected=dict(id=i,record_hex=expected.to_bytes().hex(),
            owned_count=1,phase2587=1,selection_kind2585=255 if accepted else 0,
            pending2376=0 if accepted else 1,candidate_count1912=0 if accepted else 1)))
    if phase=='pilot':
        for name in (b'cleave',b'battle_shout',b'arcane_power',b'stormstrike',b'rockbiter'):
            for kind in range(5):add(name,(kind,),4,group='pilot-real-execution-and-ID')
    else:
        for length in (1,2,3):
            for kinds in itertools.product(range(5),repeat=length):
                for tier in range(5):add(kinds=kinds,tier=tier)
        for name in DEFINITIONS:
            for kind in range(5):
                for tier in range(5):add(name,(kind,),tier,group='all114-declarations-all5kinds-tiers')
    add(kinds=(0,1),tier=2,phase=1,group='phase_guard')
    add(kinds=(),tier=999,group='empty_kinds_does_not_read_tier')
    add(kinds=(0,1),tier=2,index=1,group='owned_index_out_of_range_still_finishes')
    add(variant='new',group='new_tier0_known_empty_modifiers')
    return result


def check(phase):
    sources=source_hashes()
    if sources!=IMPORT_SOURCES or sha(SOURCE)!=SOURCE_SHA:raise ValueError('Sources changed before generation')
    cases=corpus(phase);out,manifest=build(['select_ability'])
    for name,expected in sources.items():
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
        if sha(p)!=expected:raise ValueError('Source snapshot differs')
    casefile=out/'selection135-cases.jsonl';casefile.write_text(''.join(json.dumps(c,allow_nan=False)+'\n'for c in cases))
    frozen_artifacts={p.name:sha(p)for p in (casefile,out/'manifest.json',out/manifest['module_file'])}
    runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    runtime_sha='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    if sha(runtime)!=runtime_sha:raise ValueError('Pinned runtime differs')
    if subprocess.check_output([str(runtime),'--version'],text=True,timeout=10).strip()!='v22.23.4':raise ValueError('Runtime version differs')
    command=[str(runtime),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_selection135_full_oracle.mjs'),str(out),str(casefile)]
    resultfile=out/'selection135-original-results.jsonl';stderrfile=out/'selection135-stderr.log';started=time.monotonic()
    with resultfile.open('w')as stdout,stderrfile.open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        pid=child.pid
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned original1072 timed out')
    process=dict(command=command,pid=pid,pgid=pid,deadline_seconds=60,seconds=time.monotonic()-started,exit_code=code,runtime_sha256=runtime_sha)
    (out/'process.json').write_text(json.dumps(process,indent=2)+'\n')
    if code:raise RuntimeError('Original1072 failed; evidence '+str(out))
    persisted=[json.loads(x)for x in casefile.read_text().splitlines()];rows=[json.loads(x)for x in resultfile.read_text().splitlines()]
    if persisted!=cases or [x.get('id')for x in rows]!=list(range(len(cases))):raise ValueError('Persisted corpus/result coverage differs')
    mismatch=[dict(case=c,original=a)for c,a in zip(cases,rows)if c['expected']!=a]
    mismatchfile=out/'selection135-mismatches.json';mismatchfile.write_text(json.dumps(mismatch,indent=2)+'\n')
    if source_hashes()!=sources or sha(SOURCE)!=SOURCE_SHA or sha(runtime)!=runtime_sha:raise ValueError('Source/runtime changed')
    if any(sha(out/n)!=v for n,v in frozen_artifacts.items()):raise ValueError('Frozen artifact changed')
    report=dict(version='0.135.1',build='0898d5e3',phase=phase,status='passed'if not mismatch else'failed',
        original_wasm_sha256=SOURCE_SHA,original_full_function=1072,original_internal_callees_unchanged=True,
        only_changed_source_section=7,cases=len(cases),mismatches=len(mismatch),groups=dict(Counter(c['group']for c in cases)),
        compared_fields=['full80B owned record','owned count1664','phase2587','selection kind2585','pending2376','candidate count1912'],
        source_sha256_before=sources,source_sha256_after=source_hashes(),source_snapshots=True,
        module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
        artifact_sha256={p.name:sha(p)for p in(casefile,resultfile,mismatchfile,stderrfile,out/'selection135-runtime.json')},
        process=process,runtime=json.loads((out/'selection135-runtime.json').read_text()),evidence_directory=str(out.relative_to(ROOT)),
        limitations=['Each owned record starts at level1/counts0 and known neutral numeric fields; all114 synthetic definitions/all5kind bytes do not prove all kinds naturally eligible.',
        'Ordered1..3-kind loops use cleave; separate114*5*5 covers execution/ID definitions and tiers.',
        'Shared tail actually executes, but production API only returns record mutation; real producers/talent/world/messages/stats/choice scheduling remain pending.'],
        application_start_called=False,full_game_started=False,user_saves_accessed=False)
    (out/'selection135-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    if phase=='full':(ROOT/'reports/2026-11-01-selection0135-spec.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),mismatches=len(mismatch))))
    if mismatch:raise SystemExit(1)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();check(args.phase)
