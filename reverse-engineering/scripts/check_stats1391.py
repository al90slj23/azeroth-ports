#!/usr/bin/env python3
"""Expected-first1391_1542 against self-contained139numeric implementation.

Only the historical frozen controlled input JSONL is reused; no historical
expected or original output is read. Every expected result and139original call
is newly generated, with explicit seven source snapshots and139body/tableproof.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,hashlib,json,os,re,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_stats1391_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.derived_stats139 import recalculate,input_from_dict,CLASS_HP_ARMOR,RACE_MODIFIERS
from core_spec.binary32 import is_nan
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def closure():
    initial=['scripts/'+name for name in ('check_stats1391.py','build_stats1391_oracle.py','run_stats1391_oracle.mjs','production_closure135.py','source_closure137.py')]
    initial+=list(production_sources135(ROOT,'core_spec.derived_stats139','core_spec.derived_stats139'))
    declared=set(initial)
    while True:
        try:edges=verify_local_source_closure(sorted(declared));break
        except AssertionError as error:
            pair=error.args[0]
            if not isinstance(pair,tuple)or len(pair)!=2:raise
            name=pair[1]
            if name in declared or not(ROOT/name).is_file():raise
            declared.add(name)
    assert not any('headless'in n or'player_motion'in n for n in declared)
    return sorted(declared),edges


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    files,edges=closure();before={n:sha(ROOT/n)for n in files}
    template=ROOT/'evidence/stats0138-oracle-20261101T231303.006206Z/fixtures.jsonl'
    template_sha='362dd58da9b1b201535c9e0334b212ddc0bc03f84887cac2a039c9188ccb2c09'
    assert sha(template)==template_sha
    rows=[json.loads(x)for x in template.read_text().splitlines()]
    assert all(set(row)=={'id','group','input'}for row in rows)
    assert len(rows)==10569
    if args.phase=='pilot':
        #One selector plus actual source-domain examples, including new timed
        #pointer/count and reserve764. Keep each group separate in labels.
        groups=['class-selector','race-selector','class-level','passive-tag','adjustment-tag','item-tag','owned-soul-link','timed-expiry','live-dominance','new-auxiliary-pool-clamps','new-conditional-pool-select-order','mixed-ordered']
        selected=[]
        for group in groups:
            matches=[x for x in rows if x['group']==group]
            selected.append(matches[len(matches)//2])
        rows=selected
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):
                forbidden.append(str(p));raise RuntimeError('Original denied during expectation')
    sys.addaudithook(audit)
    expected=[]
    try:
        for i,row in enumerate(rows):row['id']=i;expected.append(dict(id=i,result=recalculate(input_from_dict(row['input']))))
    finally:model_phase=False
    assert not forbidden
    assert before=={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('stats01391-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    assert {int(k):tuple(v)for k,v in manifest['classes'].items()}==CLASS_HP_ARMOR
    assert {int(k):tuple(tuple(v)for v in vs)for k,vs in manifest['races'].items()}==RACE_MODIFIERS
    save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden,layer='Python open audit'))
    for n,h in before.items():
        p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    fixture=out/'fixtures.jsonl';fixture.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n'for x in rows));save(out/'expected.json',expected)
    frozen={n:sha(out/n)for n in('fixtures.jsonl','expected.json','manifest.json',manifest['module_file'],'1542.wat','expectation-read-audit.json')}
    assert fixture.stat().st_size<=33554432 and(out/'expected.json').stat().st_size<=33554432
    assert sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_stats1391_oracle.mjs'),str(out),str(fixture)]
    save(out/'prepared.json',dict(phase=args.phase,template_controlled_input_path=str(template.relative_to(ROOT)),template_controlled_input_sha256=template_sha,historical_expected_or_actual_read=False,source_sha256=before,source_import_edges=edges,artifacts=frozen,expected_before_original=True,command=command,deadline_seconds=60))
    began=time.monotonic();error=None
    def interrupted(sig,frame):raise KeyboardInterrupt('Owned139stats signal '+str(sig))
    previous=signal.signal(signal.SIGTERM,interrupted)
    with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        p=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=60))
        try:p.wait(timeout=60)
        except BaseException as e:error=repr(e)
        finally:
            if p.poll()is None:
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
            signal.signal(signal.SIGTERM,previous)
    def missing(group=False):
        try:(os.killpg if group else os.kill)(p.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,error=error)
    save(out/'process-terminal.json',terminal);failures=[];counts=Counter();got=[]
    if p.returncode==0:
        assert(out/'stdout.jsonl').stat().st_size<=134217728
        got=[json.loads(line)for line in(out/'stdout.jsonl').read_text().splitlines()]
        assert len(got)==len(rows)
        for wanted,actual in zip(expected,got):
            assert wanted['id']==actual['id'];idx=actual['id'];w=wanted['result'];raw=bytes.fromhex(actual['raw_game2592_hex']);assert len(raw)==2592
            def check(field,value,observed,integer=False):
                counts['compared_values']+=1
                if value!=observed and not(not integer and is_nan(value)and is_nan(observed)):
                    failures.append(dict(id=idx,group=rows[idx]['group'],field=field,expected=value,actual=observed))
            for domain in('derived_bits','object_fields','auxiliary_bits'):
                assert set(w[domain])==set(actual[domain])
                for key,value in w[domain].items():
                    integer=(domain=='object_fields'and key!='1109')or(domain=='derived_bits'and key in('1592','1608'))
                    check(domain+'.'+key,value,actual[domain][key],integer)
                    if domain!='object_fields':assert struct.unpack_from('<I',raw,int(key))[0]==actual[domain][key]
            for key,offset in [('current_hp_bits',1440),('speed_bits',1648)]:check(key,w[key],actual[key]);assert struct.unpack_from('<I',raw,offset)[0]==actual[key]
            for key in('speed_sequence','movement_queue_count'):check(key,int(w['speed_changed']),actual[key],True)
            assert struct.unpack_from('<I',raw,1644)[0]==actual['speed_sequence']
            assert struct.unpack_from('<I',raw,1888)[0]==actual['movement_queue_count']
            counts['actual_movement_packets']+=actual['movement_queue_count']
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    after={n:sha(ROOT/n)for n in files};assert before==after and frozen=={n:sha(out/n)for n in frozen}
    assert sha(template)==template_sha
    save(out/'differences.json',failures)
    result=dict(version='0.139.1',actual_build='b89633f9b',original_sha256=SOURCE_SHA,phase=args.phase,cases=len(rows),original1542_calls=len(got),differences=len(failures)if p.returncode==0 else None,counts=dict(counts),groups=dict(Counter(x['group']for x in rows)),source_files=len(files),production_files=sum(n.startswith('reconstruction/')for n in files),source_sha256_before=before,source_sha256_after=after,source_unchanged=before==after,source_import_edges=edges,frozen_artifacts=frozen,artifacts_unchanged=True,expected_before_original=True,controlled_template_sha256=template_sha,historical_outputs_used=False,process=terminal,runtime=runtime,old_results_transferred=False,
        scope='Freshcomplete1391_1542/callees, syntheticGame8192 and explicit orderedstat source vectors.23derived+HP+4aux+3objectkeys+speeddecision/queuecount. Timed596/600,reserve764 are explicit139 physicalABI; all seven input source producers remain caller controlled; purederived_stats139 reused as rules hypothesis, fresh1391 execution only.',
        NaN='Classification only forfloat output; all other numeric words exact,integer fields strict.',pending=['Naturalconstructor/profile/talent/equipment producer','FullBTree physical layout/movementpacketbytes','FullGame/880/continuousflow','NativeWindows runtime'],full880_frames=0,native_executions=0,complete_games=0,output_sha256=sha(out/'stdout.jsonl'),stderr_sha256=sha(out/'stderr.log'),runtime_sha256=sha(out/'runtime.json')if runtime else None)
    save(out/'comparison.json',result);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),original1542_calls=len(got),differences=result['differences'],first=failures[:5],process=terminal)))
    if p.returncode or error or failures or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)
    assert runtime['actual_host_calls']==0 and runtime['full1542_calls']==len(rows)and runtime['stack_all_restored']
if __name__=='__main__':main()
