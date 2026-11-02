#!/usr/bin/env python3
"""Expected-first actual Native513B emulation and intact WASM25511 comparison."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time,zipfile
sys.dont_write_bytecode=True
from build_native_upgrade139_oracle import ROOT,SOURCE,SOURCE_SHA,NATIVE,NATIVE_SHA,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.native_upgrade139 import upgrade_scalar139,classification

TOOL=ROOT/'.toolchain/unicorn139-2.1.4'
PYTHON=TOOL/'venv/bin/python'
WHEEL=TOOL/'wheels/unicorn-2.1.4-cp37-abi3-macosx_11_0_arm64.whl'
WHEEL_SHA='d6c93e0f60328d8f4a1792af3f834137a28050fcc2305f2ec01efe8558a9844e'
SITE=TOOL/'venv/lib/python3.14/site-packages/unicorn'
LIB=SITE/'lib/libunicorn.2.dylib'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def closure():
    names=set(production_sources135(ROOT,'core_spec.native_upgrade139'))|set('scripts/'+n for n in['check_native_upgrade139.py','build_native_upgrade139_oracle.py','run_native_upgrade139_unicorn.py','run_native_upgrade139_wasm.mjs','production_closure135.py','source_closure137.py'])
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def corpus(manifest,full):
    definitions=manifest['definitions'];default=next(d['index']for d in definitions if d['slug']=='cleave');cases=[];seen=set()
    def add(kind,tier,index,word,label):
        key=(kind,tier,index,word)
        if key not in seen:seen.add(key);cases.append(dict(id=len(cases),kind=kind,tier=tier,definition_index=index,input_word=word,label=label))
    defaults=[0,0x3f800000,0,0x3f800000,0x3f800000]
    for kind in range(5):
        for tier in(range(5)if full else[2]):add(kind,tier,default,defaults[kind],'five_original_variants')
    specials=[d for d in definitions if d['execution']==11 and d['slug']in('seal_fate','soul_fire','lightwell','faerie_fire')];assert len(specials)==4
    for d in specials:add(2,4,d['index'],1,'actual_exec11_special_name_cap2')
    other=next(d for d in definitions if d['execution']==11 and d not in specials);add(2,3,other['index'],1,'actual_exec11_other_cap0')
    add(0,4,default,0xffffffff,'counter_uint32_max');add(1,3,default,0x7fc00001,'NaN_input_MAXSS_selects_zero');add(4,4,default,0xff800000,'negative_infinity_duration')
    if full:
        for counter in[0,1,2,3,0x00ffffff,0x01000000,0x01000001,0x7fffffff,0x80000000,0xffffffff]:
            for tier in range(5):add(0,tier,default,counter,'counter_conversion_boundary')
        floats=[0xff7fffff,0xff800000,0xbf800000,0x80000000,0,1,0x3e4ccccc,0x3e4ccccd,0x3e4cccce,0x3f800000,0x409fffff,0x40a00000,0x40a00001,0x40bfffff,0x40c00000,0x40c00001,0x7f7fffff,0x7f800000,0x7fc00001,0xffc000a5,0x7f800001,0xff800001]
        for kind in[1,3,4]:
            for tier in range(5):
                for word in floats:add(kind,tier,default,word,'float32_thresholds_NaN_Inf_signedzero')
        for d in definitions:
            for tier in range(5):
                for count in[0,1,2]:add(2,tier,d['index'],count,'all114_actual_definitions_count0_1_2')
        for tier in range(5):
            for count in[11,12,13,0xffffffff]:add(2,tier,default,count,'ordinary_count_cap12_boundary')
            for d in specials:
                for count in[3,0xffffffff]:add(2,tier,d['index'],count,'actual_special_cap_saturation')
    return cases


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0);return False
    except ProcessLookupError:return True


def execute(out,argv,label,env,deadline=120):
    started=time.monotonic()
    with(out/(label+'-actual.jsonl')).open('w')as so,(out/(label+'-stderr.log')).open('w')as se:
        child=subprocess.Popen(argv,env=env,stdout=so,stderr=se,start_new_session=True);save(out/(label+'-owned-start.json'),dict(pid=child.pid,pgid=child.pid,command=argv,deadline_seconds=deadline))
        try:code=child.wait(timeout=deadline)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-started,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/(label+'-owned-terminal.json'),terminal);return terminal


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['pilot','full'],default='pilot');args=ap.parse_args();names,edges=closure();sources={n:sha(ROOT/n)for n in names};assert sha(WHEEL)==WHEEL_SHA and sha(NODE)==NODE_SHA
    with zipfile.ZipFile(WHEEL)as wheel:
        for name in wheel.namelist():
            if name.startswith('unicorn/')and Path(name).suffix in('.py','.dylib'):assert hashlib.sha256(wheel.read(name)).hexdigest()==sha(SITE/name[len('unicorn/'):])
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('native-upgrade139-'+args.phase+'-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out);cases=corpus(manifest,args.phase=='full');opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.exe','.wasm','.bin','.wat')or'/originals/'in str(p)or'-actual.jsonl'in str(p):forbidden.append(str(p));raise RuntimeError('Original or output read during independent expectation')
    sys.addaudithook(audit)
    try:
        expected=[]
        for c in cases:
            definition=manifest['definitions'][c['definition_index']];value=upgrade_scalar139(c['kind'],c['tier'],c['input_word'],definition['execution'],definition['slug'],manifest['tables']);expected.append(dict(id=c['id'],result_bits=value,result_class=classification(value)))
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in names}
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',cases);save(out/'expected.json',expected);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden,static_manifest_data_supplied=True,no_runtime_output_supplied=True))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),unicorn_library=str(LIB),unicorn_library_sha256=sha(LIB),wheel_sha256=WHEEL_SHA))
    guards=[dict(id=i,kind=k,tier=t,definition_index=cases[0]['definition_index'],input_word=0,label=p,guard_probe=p)for i,(p,k,t)in enumerate([('uninitialized_owner',0,2),('invalid_variant',5,2),('out_of_range_tier',0,5)])];guard_expected=['Uninitialized_or_out_of_whitelist_read','Uninitialized_or_out_of_whitelist_read','Forbidden_call_syscall_or_trap'];save(out/'guard-inputs.json',guards);save(out/'guard-expected.json',guard_expected);save(out/'guard-config.json',dict(input_file=str(out/'guard-inputs.json'),input_sha256=sha(out/'guard-inputs.json'),unicorn_library=str(LIB),unicorn_library_sha256=sha(LIB),wheel_sha256=WHEEL_SHA,guard_mode=True))
    frozen={n:sha(out/n)for n in['inputs.json','expected.json','expectation-read-audit.json','config.json','guard-inputs.json','guard-expected.json','guard-config.json','manifest.json','native513.bin',manifest['wasm_module_file']]};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_both_original_engines=True,original_inputs_contain_expected=False,Unicorn_wheel=str(WHEEL),Unicorn_wheel_sha256=WHEEL_SHA,Unicorn_library_sha256=sha(LIB),Windows_application_executions=0))
    env={**os.environ,'TMPDIR':str(TOOL/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','LIBUNICORN_PATH':str(LIB.parent)}
    native_terminal=execute(out,[str(PYTHON),str(ROOT/'scripts/run_native_upgrade139_unicorn.py'),str(out),str(out/'config.json')],'native',env)
    wasm_terminal=execute(out,[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=1024',str(ROOT/'scripts/run_native_upgrade139_wasm.mjs'),str(out),str(out/'config.json')],'wasm',env)
    guard_terminal=execute(out,[str(PYTHON),str(ROOT/'scripts/run_native_upgrade139_unicorn.py'),str(out),str(out/'guard-config.json')],'native-guards',env)
    native=[json.loads(s)for s in(out/'native-actual.jsonl').read_text().splitlines()];wasm=[json.loads(s)for s in(out/'wasm-actual.jsonl').read_text().splitlines()];counts=Counter();diff=[]
    def eq(cid,label,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(id=cid,label=label,expected=want,actual=got))
    for engine,rows in [('native',native),('WASM',wasm)]:
        for c,w,a in zip(cases,expected,rows):
            eq(c['id'],'id_'+engine,c['id'],a['id'])
            nan_input=c['kind']in(1,3,4)and classification(c['input_word'])=='nan'
            if w['result_class']=='nan'or nan_input:
                eq(c['id'],engine+'_classification',w['result_class'],classification(a['result_bits'])if a['result_bits']is not None else None);counts[engine+'_NaN_input_or_output_classification_only']+=1
            else:eq(c['id'],engine+'_bits',w['result_bits'],a['result_bits'])
            if engine=='native':
                eq(c['id'],'native_returned',True,a['returned']);eq(c['id'],'native_no_violation',[],a['violations']);eq(c['id'],'native_no_guest_writes',[],a['guest_writes']);eq(c['id'],'native_readonly_PE',True,a['all_PE_pages_unchanged']);eq(c['id'],'native_owned_unknown_not_consumed',True,all(a['owner64_known_or_None'][r['address']-0x100000100+j]is not None for r in a['reads']if r['source'].startswith('owned_')for j in range(r['size'])))
                counts['native_instruction_emulation_calls']+=1;counts['native_instructions']+=a['instructions'];counts['native_data_reads']+=len(a['reads']);counts['native_owner_None_cells']+=sum(v is None for v in a['owner64_known_or_None'])
            else:
                eq(c['id'],'WASM_ownerpage_unchanged',True,a['owner_page_unchanged']);eq(c['id'],'WASM_stack_before',1048576,a['stack_before']);eq(c['id'],'WASM_stack_after',1048576,a['stack_after']);counts['full_WASM25511_calls']+=1
    for c,n,a in zip(cases,native,wasm):
        if c['kind']in(1,3,4)and classification(c['input_word'])=='nan':counts['NaN_input_or_output_classification_only']+=1
        else:eq(c['id'],'two_originals_same_bits',n['result_bits'],a['result_bits'])
        counts['kind'+str(c['kind'])]+=1;counts['input_NaN_cases']+=c['kind']in(1,3,4)and classification(c['input_word'])=='nan'
    eq(-1,'native_completed',len(cases),len(native));eq(-1,'WASM_completed',len(cases),len(wasm));eq(-1,'native_exit',0,native_terminal['exit_code']);eq(-1,'WASM_exit',0,wasm_terminal['exit_code'])
    guard_actual=[json.loads(s)for s in(out/'native-guards-actual.jsonl').read_text().splitlines()];eq(-1,'guard_completed',3,len(guard_actual));eq(-1,'guard_exit',0,guard_terminal['exit_code'])
    for g,w,a in zip(guards,guard_expected,guard_actual):
        eq(g['id'],'guard_id',g['id'],a['id']);eq(g['id'],'guard_refused_return',False,a['returned']);eq(g['id'],'guard_reason',[w],[v['reason']for v in a['violations']]);eq(g['id'],'guard_guest_writes',[],a['guest_writes']);eq(g['id'],'guard_result_unknown',None,a['result_bits']);counts['harness_negative_guard_probes']+=1
    runtimes={label:json.loads((out/(label+'-runtime.json')).read_text())if(out/(label+'-runtime.json')).exists()else None for label in['native','wasm']}
    assert sources=={n:sha(ROOT/n)for n in names}and frozen=={n:sha(out/n)for n in frozen}and sha(NATIVE)==NATIVE_SHA and sha(SOURCE)==SOURCE_SHA;save(out/'differences.json',diff)
    artifacts={n:sha(out/n)for n in['native-actual.jsonl','wasm-actual.jsonl','native-runtime.json','wasm-runtime.json','native-guards-runtime.json','native-guards-actual.jsonl','native-guards-owned-start.json','native-guards-owned-terminal.json','native-guards-stderr.log','native-owned-start.json','wasm-owned-start.json','native-owned-terminal.json','wasm-owned-terminal.json','prepared.json','differences.json','native-stderr.log','wasm-stderr.log']if(out/n).exists()}
    comp=dict(kind='two_original_scalar_functions_unicorn_native_instruction_emulation_and_intact_WASM',version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(cases),native_completed=len(native),wasm_completed=len(wasm),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtimes=runtimes,native_process=native_terminal,wasm_process=wasm_terminal,guard_process=guard_terminal,expected_before_both_originals=True,Windows_application_executions=0,native_full_Game_Unit_ABI_restored=False,limits=['Actual original513B emulated at originalVAs, not Windows OS/application execution.','Only five kinds/tiers and actually consumed partial owner fields; other bytesUnknown and reads denied.','Intact25511 export-only WASM with static actual definitions; not App/gameplay/mainloop.','NaN payload equality not claimed; NativeMAXSS/WASMselect clear floatNaN inputs tozero.','Negative guard probes are refused harness attempts, not valid original-function behavioral fixtures.'])
    save(out/'comparison.json',comp);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(cases),counts=dict(counts),native_process=native_terminal,wasm_process=wasm_terminal,first_differences=diff[:6])),flush=True)
    if counts['differences']or native_terminal['exit_code']or wasm_terminal['exit_code']:raise SystemExit(1)


if __name__=='__main__':main()
