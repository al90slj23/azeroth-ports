#!/usr/bin/env python3
"""Compare current120-level XP projection against complete original0.134 4630.

Phase3 uses the original final guard to omit2159 choice generation. Actual
attribute/heal/message callees reached during level-up remain unchanged; only
level/XP/pending and phase are independently compared by this harness.
"""
from dataclasses import asdict
import json
import os
import random
import signal
import subprocess
import sys

from build_full134_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.progression134 import ProgressionState,apply_xp,xp_threshold

SEED=0xa2e04630


def corpus():
    result=[]
    def add(group,level,xp,pending,amount):
        state=ProgressionState(level,xp,pending)
        result.append({'id':len(result),'group':group,'state':asdict(state),'amount':amount,
                       'expected':{'state':asdict(apply_xp(state,amount).state),'phase2579':3}})
    for level in range(128):
        needed=xp_threshold(level)
        for delta in (-1,0,1):
            add('threshold_neighbors',level,0,0,needed+delta)
            add('held_XP_amount0_pending_wrap',level,needed+delta,0xffffffff,0)
    for level in (0,1,2,50,98,99,100,118,119,120,121,0xffffffff):
        for xp,amount in ((0xffffffff,1),(0xffffffff,2),(0xfffffffe,1),(0xfffffffe,2),(0,0xffffffff),(1,0xffffffff)):
            add('XP_wrap_and_cap_boundaries',level,xp,0xffffffff,amount)
    total=0
    for level in range(1,120):
        total+=xp_threshold(level)
        for delta in (-1,0,1):add('multilevel_cumulative_boundaries',1,0,0,total+delta)
    rng=random.Random(SEED)
    for _ in range(1000):
        add('seeded_balances_levels_pending',rng.randrange(125),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32))
    return result


def main():
    cases=corpus();out,manifest=build(['gain_experience'])
    casefile=out/'progression134-cases.jsonl'
    casefile.write_text(''.join(json.dumps(c,allow_nan=False)+'\n'for c in cases))
    runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    if sha(runtime)!='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0':
        raise ValueError('Pinned Node identity differs')
    command=[str(runtime),'--max-old-space-size=512','--wasm-max-mem-pages=512',
             str(ROOT/'scripts/run_progression134_full_oracle.mjs'),str(out),str(casefile)]
    resultfile=out/'progression134-original-results.jsonl'
    with resultfile.open('w')as stdout,(out/'progression134-stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise SystemExit('Owned full4630 comparison exceeded60s')
    if code:raise SystemExit(f'Full current4630 run failed; inspect {out}')
    rows=[json.loads(line)for line in resultfile.read_text().splitlines()]
    if len(rows)!=len(cases)or [r['id']for r in rows]!=list(range(len(cases))):
        raise ValueError('Persisted original coverage/order differs')
    mismatch=[{'id':c['id'],'input':c,'original':a}for c,a in zip(cases,rows)
              if c['expected']!={k:a[k]for k in ('state','phase2579')}]
    mismatchfile=out/'progression134-mismatches.json'
    mismatchfile.write_text(json.dumps(mismatch,indent=2,allow_nan=False)+'\n')
    runtimefile=out/'progression134-runtime.json'
    files=('scripts/build_full134_oracle.py','scripts/full134_host.mjs','scripts/build_upgrade134_oracle.py',
           'scripts/run_progression134_full_oracle.mjs','scripts/check_progression134_full_spec.py',
           'reconstruction/core_spec/progression134.py','reconstruction/core_spec/binary32.py')
    receipt={'version':'0.134.0','build':'983346a7','original_wasm_sha256':SOURCE_SHA,
        'module_sha256':manifest['module_sha256'],'original_function':4630,'original_full_function_executed':True,
        'case_count':len(cases),'mismatch_count':len(mismatch),'level_cap':120,
        'fields_compared':['u32 level1520','u32 XP1524','u32 pending2368','phase2579'],
        'groups':{g:sum(c['group']==g for c in cases)for g in sorted({c['group']for c in cases})},
        'seed':hex(SEED),'runtime':json.loads(runtimefile.read_text()),'only_changed_source_section':7,'dependency_shims':[],
        'source_sha256':{p:sha(ROOT/p)for p in files},
        'artifact_sha256':{p.name:sha(p)for p in (casefile,resultfile,mismatchfile,runtimefile)},
        'limitations':['Synthetic warrior/human phase3, empty auxiliary state, original allocator91940-owned5000B game state.',
            'Original1513/10847/1453 and reached message/tree helpers execute if reached; only4 reported fields compared.',
            'Independent attribute/healing/message side effects and original2159 next-choice generation are not implemented by this model.',
            'Other phases, card-eligibility true branch, networking, UI and complete game not accepted by this corpus.']}
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Official source changed')
    (out/'progression134-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'run':str(out),'original4630_executed':True,'cases':len(cases),'mismatches':len(mismatch),'level_cap':120}))
    if mismatch:raise SystemExit('Independent current progression differs from full original4630')


if __name__=='__main__':main()
