#!/usr/bin/env python3
"""Compare prefix-model scalar fields with full1063 on nonfatal empty state.

The production model deliberately stops at named pending stages. This corpus
only accepts its core-HP stage or real entry guards, then checks selected fields
against actual final full-original fields on this explicitly restricted domain.
It does not turn the prefix model into a complete incoming-damage replacement.
"""
from dataclasses import asdict
import itertools
import json
import os
import signal
import struct
import subprocess
import sys
from build_full134_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.incoming134 import IncomingState,resolve_incoming_prefix

FIELDS=('armor_1392_bits','hp_1528_bits','shield_1532_bits','barrier_1536_bits',
        'shield_source_1344','shield_source_remaining_1348_bits','reserve_768_bits',
        'absorbed_740_bits','maximum_shield_744_bits','last_hit_1648_bits')


def corpus():
    b=f.from_float;cases=[]
    def add(group,amount=10,armor=0,shield=0,barrier=0,mode=0,wave=1,map_id='',phase=1,protection=0):
        state=IncomingState(phase_2579=phase,protection_2568=protection,mode_2574=mode,map_id=map_id.encode(),
            wave_2532=wave,now_bits=b(10),armor_1392_bits=b(armor),hp_1528_bits=b(1000),
            shield_1532_bits=b(shield),barrier_1536_bits=b(barrier))
        result=resolve_incoming_prefix(state,b(amount),source_guid=0)
        if result.status!='returned'and result.stage!='core_hp_write_L1793':
            raise ValueError('Fixture reached an unimplemented pre-HP callback')
        if not f.to_float(result.state.hp_1528_bits)>0:
            raise ValueError('Corpus must remain nonfatal')
        expected={name:getattr(result.state,name)for name in FIELDS}
        expected['incoming_total_992_bits']=struct.pack('>d',result.state.incoming_total_992).hex()
        expected['phase2579']=phase
        record=asdict(state);record['map_id']=map_id
        cases.append({'id':len(cases),'group':group,'state':record,'map_id':map_id,'max_hp_bits':b(1000),
                      'amount_bits':b(amount),'model_stage':result.stage,'expected':expected})
    for amount,armor,pair in itertools.product((0,.25,1,10,30),(0,.1,.5,1),((0,0),(50,30),(50,0))):
        add('armor_and_nonexhausting_shield',amount,armor,*pair)
    for map_id,wave,amount,armor,shield in itertools.product(('elwynn','ungoro','unknown'),(1,2,10),(1,10),(0,.25),(0,100)):
        add('mode_map_wave_scaling',amount,armor,shield,30 if shield else 0,mode=1,wave=wave,map_id=map_id)
    for phase in (0,2,3,255):add('phase_guard',phase=phase)
    for protection in (1,3,255):add('protection_guard',protection=protection)
    return cases


def main():
    cases=corpus();out,manifest=build(['incoming_damage'])
    casefile=out/'incoming134-cases.json';casefile.write_text(json.dumps(cases,indent=2,allow_nan=False)+'\n')
    runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    if sha(runtime)!='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0':raise ValueError('Node pin differs')
    command=[str(runtime),'--max-old-space-size=512','--wasm-max-mem-pages=512',
             str(ROOT/'scripts/run_incoming134_full_oracle.mjs'),str(out),str(casefile)]
    resultfile=out/'incoming134-original-results.jsonl'
    with resultfile.open('w')as stdout,(out/'incoming134-stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise SystemExit('Owned full1063 comparison exceeded60s')
    if code:raise SystemExit(f'Full1063 run failed; inspect {out}')
    rows=[json.loads(x)for x in resultfile.read_text().splitlines()]
    if len(rows)!=len(cases)or [x['id']for x in rows]!=list(range(len(cases))):raise ValueError('Output coverage/order differs')
    mismatch=[{'id':c['id'],'group':c['group'],'difference':{k:[v,a[k]]for k,v in c['expected'].items()if v!=a[k]}}
              for c,a in zip(cases,rows)if any(v!=a[k]for k,v in c['expected'].items())]
    mismatchfile=out/'incoming134-mismatches.json';mismatchfile.write_text(json.dumps(mismatch,indent=2,allow_nan=False)+'\n')
    runtimefile=out/'incoming134-runtime.json'
    files=('scripts/build_full134_oracle.py','scripts/full134_host.mjs','scripts/build_upgrade134_oracle.py',
        'scripts/check_incoming134_nonfatal_spec.py','scripts/run_incoming134_full_oracle.mjs',
        'reconstruction/core_spec/incoming134.py','reconstruction/core_spec/binary32.py')
    receipt={'version':'0.134.0','build':'983346a7','original_wasm_sha256':SOURCE_SHA,
        'module_sha256':manifest['module_sha256'],'original_function':1063,'original_full_function_executed':True,
        'case_count':len(cases),'mismatch_count':len(mismatch),'fields_compared':list(cases[0]['expected']),
        'groups':{g:sum(c['group']==g for c in cases)for g in sorted({c['group']for c in cases})},
        'production_model_kind':'explicitly_partial_scalar_prefix_with_pending_stages',
        'runtime':json.loads(runtimefile.read_text()),'only_changed_source_section':7,'dependency_shims':[],
        'source_sha256':{p:sha(ROOT/p)for p in files},
        'artifact_sha256':{p.name:sha(p)for p in (casefile,resultfile,mismatchfile,runtimefile)},
        'limitations':['Nonfatal HP1000/maxHP1000, sourceGUID0, empty units/items/buffs/modifiers, reserve0/sourceSpell0; finite nonnegative amounts.',
            'Shield cases do not exhaust total shield; cleanup1202/reserve callbacks and revival/death not independently implemented.',
            'Comparison accepts selected final scalar fields only on this domain; prefix-model pending stages remain pending.',
            'Nearby unit reductions, rawtag54, activebuff12 and cast922 barrier replacement are static/model-only, not this runtime corpus.',
            'Full original internal callees run if reached; independent statistics/history/events/packets and complete incoming behavior remain missing.']}
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Original source changed')
    (out/'incoming134-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'run':str(out),'original1063_executed':True,'cases':len(cases),'mismatches':len(mismatch)}))
    if mismatch:raise SystemExit('Selected nonfatal incoming fields differ')


if __name__=='__main__':main()
