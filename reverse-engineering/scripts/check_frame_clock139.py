#!/usr/bin/env python3
"""Expected-first current884 clock-prefix micro-module differential only."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,math,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,save,sha
from build_frame_clock139_oracle import build
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.frame_clock139 import FrameClock139,sample_frame_clock139,advance_game_clock139,bits64,classification32,classification64
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
def h(v):return format(bits64(v),'016x')
def closure():
    names=set(production_sources135(ROOT,'core_spec.frame_clock139'))|set('scripts/'+n for n in('check_frame_clock139.py','build_frame_clock139_oracle.py','run_frame_clock139_oracle.mjs','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])
def corpus(full):
    cases=[]
    def add(label,tag,previous,nows):cases.append(dict(id=len(cases),label=label,initial_tag_hex=f'{tag:016x}',initial_previous_hex=previous,now_hexes=nows))
    for tag in(0,2,(1<<32)+1,(1<<64)-1):add('first-tag-not-one',tag,'7ff0000000000001',[h(.125)])
    add('negative-zero-preserved',1,h(0.0),[h(-0.0)])
    add('ordinary-continuous',0,h(99),[h(x)for x in(100,100.05,100.1,100.2,100.19,101)])
    if full:
        vals=[-math.inf,-float.fromhex('0x1.fffffffffffffp1023'),-1.0,-.1,-float.fromhex('0x0.0000000000001p-1022'),-0.0,0.0,float.fromhex('0x0.0000000000001p-1022'),2**-150,2**-149,math.nextafter(.1,0),.1,math.nextafter(.1,math.inf),1.0,float.fromhex('0x1.fffffffffffffp1023'),math.inf]
        specials=[h(v)for v in vals]+['7ff8000000000001','fff80000000000a5','7ff0000000000001']
        for previous in specials:
            for now in specials:add('tag1-f64-cross-product',1,previous,[now])
        for tag in(0,2,1<<32,(1<<32)+1,(1<<63),(1<<64)-1):
            for now in specials:add('first-tag64-ignores-previous',tag,'fff0000000000001',[now])
        add('nan-then-recover',0,h(0),['7ff8000000000001',h(1),h(1.125),h(1.15)])
        add('infinite-then-finite',1,h(0),[h(math.inf),h(math.inf),h(2),h(2.05)])
        add('continuous-boundary-cancellation',1,h(2**52),[h(2**52),h(2**52+1),h(2**52-1),h(0),h(.1),h(.2)])
    return cases
def expected(c):
    tag=int(c['initial_tag_hex'],16);state=FrameClock139(tag,int(c['initial_previous_hex'],16)if tag==1 else None);steps=[]
    for now in c['now_hexes']:
        result=sample_frame_clock139(state,int(now,16));state=result.state
        steps.append(dict(tag_u64=state.tag_u64,timestamp_hex=f'{state.previous_timestamp_bits:016x}',timestamp_class=classification64(state.previous_timestamp_bits),dt_bits=result.dt_bits,dt_class=classification32(result.dt_bits),previous_consumed=result.previous_timestamp_consumed))
    return steps
def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files};cases=corpus(args.phase=='full')
    opened=[];forbidden=[];model_phase=True
    def audit(event,args):
        if model_phase and event=='open'and isinstance(args[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(args[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Originaldeniedduringexpectation')
    sys.addaudithook(audit)
    try:rows=[dict(id=c['id'],steps=expected(c))for c in cases]
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files}
    # Separate model-only arithmetic checks;these are notoriginal mainloopcalls.
    model_checks=[]
    for phase in(0,1,2,4,5):
        for old,dt in((0,0),(f.SIGN,f.SIGN),(f.from_float(5),f.from_float(.1)),(f.INF,0),(f.NAN,0)):
            result=advance_game_clock139(old,dt,phase2587=phase);assert result==(f.add(dt,old)if phase==1 else old);model_checks.append(dict(phase=phase,clock=old,dt=dt,result=result))
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('frame-clock139-micro-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for n,v in sources.items():q=out/'source-snapshot'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==v
    save(out/'inputs.json',cases);save(out/'expected.json',rows);save(out/'model-only-game-clock-checks.json',dict(kind='arithmetic_model_selfcheck_not_original',cases=model_checks,original_calls=0));save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden,layer='Pythonopenaudit'))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json')));frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',manifest['module_file'],'original-local-declaration.bin','original-clock-prefix.bin','instrumentation-tail.bin','expectation-read-audit.json','model-only-game-clock-checks.json')}
    save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original_prefix_micro_execution=True,original_input_contains_expected=False,full884_calls=0))
    cmd=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=64',str(ROOT/'scripts/run_frame_clock139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        p=subprocess.Popen(cmd,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=p.pid,pgid=p.pid,command=cmd,deadline_seconds=60))
        try:code=p.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code=p.returncode
    terminal=dict(pid=p.pid,pgid=p.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(s)for s in(out/'actual.jsonl').read_text().splitlines()];diff=[];counts=Counter()
    def eq(case,field,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<100:diff.append(dict(case=case,field=field,expected=want,actual=got))
    for c,w,a in zip(cases,rows,actual):
        eq(c['id'],'id',c['id'],a['id']);eq(c['id'],'steps',len(w['steps']),len(a['steps']));before=bytes.fromhex(a['before_owner_and_canaries144_hex']);eq(c['id'],'initialtag',int(c['initial_tag_hex'],16),struct.unpack_from('<Q',before,64)[0]);eq(c['id'],'initialtimestamp',int(c['initial_previous_hex'],16),struct.unpack_from('<Q',before,72)[0])
        for i,(want,got)in enumerate(zip(w['steps'],a['steps'])):
            tag,timestamp=struct.unpack('<QQ',bytes.fromhex(got['owner16_hex']));eq(c['id'],f's{i}.tag',want['tag_u64'],tag)
            if want['timestamp_class']=='nan':eq(c['id'],f's{i}.timestampNaN','nan',classification64(timestamp));counts['timestamp_NaN_classifications']+=1
            else:eq(c['id'],f's{i}.timestamp',int(want['timestamp_hex'],16),timestamp)
            if want['dt_class']=='nan':eq(c['id'],f's{i}.dtNaN','nan',classification32(got['dt_bits']));counts['dt_NaN_classifications']+=1
            else:eq(c['id'],f's{i}.dt',want['dt_bits'],got['dt_bits'])
            eq(c['id'],f's{i}.low64',before[:64].hex(),got['low64_hex']);eq(c['id'],f's{i}.high64',before[80:].hex(),got['high64_hex']);eq(c['id'],f's{i}.outsideOwner',True,got['outside_owner_unchanged']);eq(c['id'],f's{i}.SPbefore',1048576-i*10704,got['stack_before']);eq(c['id'],f's{i}.SPafter',1048576-(i+1)*10704,got['stack_after']);counts['micro_calls']+=1;counts['negative_zero_dt']+=got['dt_bits']==f.SIGN;counts['first_timestamp_not_consumed']+=not want['previous_consumed'];counts['canary_bytes']+=128;counts['owner_write_bytes']+=16
    for n,v in sources.items():assert sha(ROOT/n)==v
    for n,v in frozen.items():assert sha(out/n)==v
    save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    artifacts={n:sha(out/n)for n in('actual.jsonl','runtime.json','stderr.log','owned-start.json','owned-terminal.json','prepared.json','differences.json')if(out/n).exists()}
    comparison=dict(kind=manifest['kind'],version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(cases),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,original_prefix_preserved_verbatim=True,full884_calls=0,original_function_entry_calls=0,game2352_original_execution_calls=0,model_game_clock_selfchecks=25,limits=['Micro-modulewithoriginal884full local declaration+unchangedcontiguousopcodesonly;tailaddsget156/end. Notoriginal884entryorfullmainloop.','Stacksubtract10704preservedwithoutrestoration;externalharnessresetonlybetweencases.','NaNonlyclassification,nopayloadpromises.','Game2352phase1additionstaticandmodelselfcheckonly;nooriginal884branch/App/bootstrap/gameacceptance.'])
    save(out/'comparison.json',comparison);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(cases),completed=len(actual),differences=counts['differences'],first=diff[:4],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(cases)or counts['differences']:raise SystemExit(1)
if __name__=='__main__':main()
