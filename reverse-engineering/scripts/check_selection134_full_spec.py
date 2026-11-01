#!/usr/bin/env python3
"""Validate migrated80B ability updates against complete original0.134.0 1073.

Current field offsets are recovered separately, not transferred by a uniform
shift. Only compared fields and explicitly chosen empty auxiliary-state domain
are accepted; the production model's postprocessing remains pending.
"""
import hashlib
import itertools
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from build_full134_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.ability_state import (AbilityRecord,AbilityDefinition,UpgradeCard,
                                    apply_upgrade_card,initialize_ability,neutral_additional_bytes)


def corpus():
    definition=AbilityDefinition(5463472,b'cleave',5);record=AbilityRecord(definition.pointer)
    result=[]
    def add(kinds=(),tier=0,phase=2,index=0,variant='upgrade',group='ordered_upgrade'):
        i=len(result);accepted=phase==2
        if variant=='new':expected=initialize_ability(definition,additional=neutral_additional_bytes())
        elif accepted and index==0:expected=apply_upgrade_card(record,UpgradeCard(index,tuple(kinds),tier),definition)
        else:expected=record
        result.append({'id':i,'group':group,'variant':variant,'phase':phase,'kinds':list(kinds),'tier':tier,
                       'owned_index':index,'input_hex':record.to_bytes().hex(),
                       'expected':{'id':i,'record_hex':expected.to_bytes().hex(),'owned_count':1,
                                   'phase2579':1,'selection_kind2577':255 if accepted else 0,
                                   'pending2368':0 if accepted else 1,'candidate_count1904':0 if accepted else 1}})
    for length in (1,2,3):
        for kinds in itertools.product(range(5),repeat=length):
            for tier in range(5):add(kinds,tier)
    add((0,1),2,phase=1,group='phase_guard')
    add((),999,group='empty_kinds_does_not_read_tier')
    add((0,1),2,index=1,group='owned_index_out_of_range_still_finishes')
    add(variant='new',group='new_tier0_empty_modifiers')
    return result


def main():
    out,manifest=build(['select_ability','recalculate_stats','finish_selection'])
    cases=corpus();casefile=out/'selection134-cases.jsonl'
    casefile.write_text(''.join(json.dumps(c,allow_nan=False)+'\n' for c in cases))
    runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    if sha(runtime)!='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0':raise ValueError('Fixed Node identity differs')
    command=[str(runtime),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_selection134_full_oracle.mjs'),str(out),str(casefile)]
    resultfile=out/'selection134-original-results.jsonl'
    with resultfile.open('w') as stdout,(out/'selection134-stderr.log').open('w') as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise SystemExit('Owned new-version function oracle exceeded60s')
    if code:raise SystemExit(f'Original0.134 selection failed; inspect {out}')
    rows=[json.loads(x) for x in resultfile.read_text().splitlines()]
    if len(rows)!=len(cases) or [x['id'] for x in rows]!=list(range(len(cases))):raise ValueError('Persisted result IDs differ')
    mismatch=[{'input':c,'original':a} for c,a in zip(cases,rows) if c['expected']!=a]
    (out/'selection134-mismatches.json').write_text(json.dumps(mismatch,indent=2,allow_nan=False)+'\n')
    files=('scripts/build_full134_oracle.py','scripts/full134_host.mjs','scripts/run_selection134_full_oracle.mjs',
           'scripts/check_selection134_full_spec.py','scripts/build_upgrade134_oracle.py',
           'reconstruction/core_spec/ability_state.py','reconstruction/core_spec/upgrade_values.py','reconstruction/core_spec/binary32.py')
    receipt={'version':'0.134.0','build':'983346a7','original_wasm_sha256':SOURCE_SHA,
             'module_sha256':manifest['module_sha256'],'original_function':1073,'original_full_function_executed':True,
             'case_count':len(cases),'mismatch_count':len(mismatch),'fields_compared':['complete80B owned record','owned_count1660','phase2579','selection_kind2577','pending2368','candidate_count1904'],
             'only_changed_source_section':7,'dependency_shims':[],
             'runtime':json.loads((out/'selection134-runtime.json').read_text()),
             'source_sha256':{f:sha(ROOT/f) for f in files},
             'artifact_sha256':{p.name:sha(p) for p in (casefile,resultfile,out/'selection134-mismatches.json')},
             'limitations':['Synthetic warrior/human level1 cleave, empty modifiers/equipment/loot, pending2368=1.',
                            'Production model postprocessing remains explicit pending; full original tail actually executes here.',
                            'Nonzero new-ability tier, next candidate generation, other pending queues and whole game are unverified.']}
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Original changed during test')
    (out/'selection134-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'run':str(out),'version':'0.134.0','complete_original1073':True,'cases':len(cases),'mismatches':len(mismatch)}))
    if mismatch:raise SystemExit('Current-version selection differs from migrated model')


if __name__=='__main__':main()
