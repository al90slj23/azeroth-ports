#!/usr/bin/env python3
"""Expected-first fresh1392945 empty sources and18062 resolved start packet."""
from collections import Counter
from datetime import datetime,timezone
import argparse,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from build_opening_profile139_oracle import build
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.opening_profile139 import EmptyAccountSources139,absent_companion_selection139,advance_app_seed139,start_banner139
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def closure():
    names=set(production_sources135(ROOT,'core_spec.opening_profile139'))|set('scripts/'+n for n in('check_opening_profile139.py','build_opening_profile139_oracle.py','run_opening_profile139_oracle.mjs','trace_opening_aux139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:edges=verify_local_source_closure(sorted(names));return sorted(names),edges
        except AssertionError as error:
            pair=error.args[0]
            if not isinstance(pair,tuple)or len(pair)!=2 or pair[1]in names:raise
            names.add(pair[1])

def corpus(pilot,static):
    rows=[]
    def select(account_poison,poison):
        raw=bytearray([account_poison]*368)
        for o in(196,244,256,268):struct.pack_into('<I',raw,o,0)
        rows.append(dict(id=len(rows),group='four-empty-sources-inactive-account-poison',kind='selection',account_hex=raw.hex(),poison=poison))
    def banner(title,subtitle,group='resolved-UTF8-start150'):
        rows.append(dict(id=len(rows),group=group,kind='banner',title=title,subtitle=subtitle))
    select(0,0xa5);select(0xa5,0xff);banner(static['English']['title'],static['English']['subtitle']);banner('角色😀','中文界面「说明」\n下一行');banner('a'*23,'b'*19,'capacity-edge')
    if not pilot:
        for ap in(0,0x5a,0xa5,0xff):
            for p in(0,0x5a,0xa5,0xff):select(ap,p)
        for title,subtitle in(('', ''),('a','b'),('"\\\n','x\x00y'),('界'*30,'😀'*30),('Azeroth Survivors','')):banner(title,subtitle)
        for n in(0,7,8,15,16,17,22,23,24,30,31,32,33,48,63,64,65,127,128,129,300):
            for m in(0,19,300):banner('x'*n,'y'*m,'capacity-reservation-boundaries')
    return rows

def expected(case):
    if case['kind']=='selection':
        raw=bytes.fromhex(case['account_hex']);counts=[struct.unpack_from('<I',raw,o)[0]for o in(196,244,256,268)];sources=EmptyAccountSources139(*counts);prior=bytes([case['poison']])*40;out=absent_companion_selection139(sources,prior)
        return dict(id=case['id'],kind='selection',prior40_hex=prior.hex(),output40_hex=bytes(out).hex(),account_unchanged=True,canaries=['c3'*16,'d7'*16])
    packet=start_banner139(case['title'].encode(),case['subtitle'].encode())
    return dict(id=case['id'],kind='banner',capacity=packet.capacity,length=len(packet.payload),opcode=packet.opcode,payload_hex=packet.payload.hex(),strings_unchanged=True,canaries=['c3'*16,'d7'*16])

def model_checks():
    result=[]
    for changes in((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1),(False,0,0,0)):
        try:EmptyAccountSources139(*changes)
        except NotImplementedError:result.append(dict(kind='nonempty_or_bool_source_rejected',input=list(changes)))
        else:raise AssertionError(changes)
    out=absent_companion_selection139(EmptyAccountSources139(0,0,0,0));assert sum(x is None for x in out)==10 and sum(x is not None for x in out)==30
    return dict(original_calls=0,kind='model_only_unknown_and_seed_selfchecks',rejected=result,uninitialized40_known_cells=30,uninitialized40_unknown_cells=10,seed_examples=[dict(input=str(v),output=str(advance_app_seed139(v)))for v in(0,1,(1<<64)-1)],seed_rule='Static6786 provenance only;not a new runtime6786 differential.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-profile139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest,static=build(out)
    for name,digest in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==digest
    rows=corpus(args.phase=='pilot',static);answers=[expected(c)for c in rows];save(out/'inputs.json',rows);save(out/'expected.json',answers);checks=model_checks();save(out/'model-checks.json',checks)
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','model-checks.json','manifest.json',manifest['module_file'])};assert before=={n:sha(ROOT/n)for n in files}and sha(NODE)==NODE_SHA
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_opening_profile139_oracle.mjs'),str(out),str(out/'inputs.json')];save(out/'prepared.json',dict(sources=before,source_import_edges=edges,expected_before_original=True,artifacts=frozen,command=command,deadline_seconds=60));start=time.monotonic()
    with(out/'actual.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=60,command=command))
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60,pid_missing=missing(),pgid_missing=missing(True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];diffs=[];counts=Counter()
    if code or len(actual)!=len(rows):save(out/'failure.json',dict(process=terminal,completed=len(actual),expected=len(rows)));print(json.dumps(dict(out=str(out.relative_to(ROOT)),status='original_or_capture_failed_preserved',process=terminal,stderr=(out/'stderr.log').read_text()[-2000:])));raise SystemExit(1)
    for c,e,a in zip(rows,answers,actual,strict=True):
        if c['kind']=='selection':got=a;counts['full2945']+=1;counts['exact40_output_bytes']+=40
        else:
            descriptor=bytes.fromhex(a['raw_descriptor16_hex']);assert len(descriptor)==16
            assert struct.unpack_from('<I',descriptor,0)[0]==a['capacity']and struct.unpack_from('<I',descriptor,8)[0]==a['length']and struct.unpack_from('<H',descriptor,12)[0]==150
            got={k:v for k,v in a.items()if k!='raw_descriptor16_hex'};counts['full18062']+=1;counts['exact_packet_payload_bytes']+=len(bytes.fromhex(a['payload_hex']));counts['observed_physical_pointer_bytes']+=4;counts['unwritten_stack_descriptor_padding_observed_bytes']+=2
        if got!=e:diffs.append(dict(id=c['id'],group=c['group'],expected=e,actual=got))
    runtime=json.load(open(out/'runtime.json'));assert runtime['host_calls']==0 and runtime['full2945_calls']==counts['full2945']and runtime['full18062_calls']==counts['full18062']
    assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}and sha(SOURCE)==SOURCE_SHA
    save(out/'differences.json',diffs);report=dict(status='scoped_original_differential_passed'if not diffs else'differences_preserved',version='0.139.0',actual_build='f79c5e2b4',phase=args.phase,cases=len(rows),differences=len(diffs),counts=dict(counts),source_sha256_before=before,source_sha256_after=before,source_import_edges=edges,original_sha256=SOURCE_SHA,expected_before_original=True,original_input_contains_expected=False,frozen_artifacts=frozen,artifacts={n:sha(out/n)for n in('actual.jsonl','runtime.json','stderr.log','owned-terminal.json','prepared.json','differences.json','static/trace.json')},runtime=runtime,process=terminal,static1108_whole_function_covered=True,full1108_calls=0,full6786_calls=0,scope='Full actual2945 with four explicit empty account sources and legal40-byte output/outer canaries; full18062 resolvedUTF8 payload/capacity/opcode,all882 hosts denied.',limitations=['2945 input is an explicit368B account component,not a natural App/2917Storage producer.','Thirty output2945 bytes are actually written;caller padding and tail40 are preserved or unknown,not assumed zero.','18062 resource pointer and stack-unwritten descriptor padding retained as observations;no allocator reimplementation.','English/currentzone/banner source is freshly extracted static data;full1108 localization/resource bootstrap not accepted by these calls.','6786 LCG is statically recovered and model-selfchecked only.','NaturalNPC/13563v2/pickups1446/windows/special/boundaries/full1108 remain next composition work.','No old135/138/139 runtime cases are transferred.'])
    save(out/'comparison.json',report);print(json.dumps(dict(out=str(out.relative_to(ROOT)),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),differences=len(diffs),counts=dict(counts),first_differences=diffs[:3],process=terminal)))
    if diffs:raise SystemExit(1)
if __name__=='__main__':main()
