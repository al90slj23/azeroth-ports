#!/usr/bin/env python3
"""Real1560→true49037 observational input/side-effect capture, no learned oracle."""
import argparse,json,os,signal,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
FILES=('scripts/probe_terminal_transition135.py','scripts/run_terminal_transition135_oracle.mjs','scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py')
def main():
 before={n:sha(ROOT/n)for n in FILES};out,manifest=build(['initial_game','terminal_tick'])
 for n,h in before.items():
  p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
 cases=[]
 for cls,race,zone,name,hero in[(8,1,0,'elwynn','Hero'),(1,2,1,'duskwood','中文英雄'),(11,8,11,'naxx','A"\\B\n')]:
  cases.append(dict(id=len(cases),input=dict(class_byte=cls,race_byte=race,region_index=zone,object_id_u64='42',seed_u64='1',flat_height_bits=0),region_id=name,hero=hero,flat_height_enabled=True,words={'400':1,'2352':0x41480000,'1644':17,'2412':31},bytes={'2587':1,'2568':0},doubles={},units=[],auxiliary=[],claims=[],counts=dict(units=0,auxiliary=0,claims=0),repeat=2))
 fixture=out/'terminal-transition135-fixtures.json';fixture.write_text(json.dumps(cases,ensure_ascii=False)+'\n');assert json.loads(fixture.read_text())==cases
 runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node';assert sha(runtime)=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
 cmd=[str(runtime),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_terminal_transition135_oracle.mjs'),str(out),str(fixture)];results=out/'terminal-transition135-results.jsonl';err=out/'terminal-transition135-stderr.log';start=time.monotonic()
 with results.open('w')as stream,err.open('w')as errors:
  child=subprocess.Popen(cmd,stdout=stream,stderr=errors,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned terminal probe deadline')
 after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
 receipt=dict(kind='observational_true_terminal_entry_not_independent_model_acceptance',version='0.135.1',build='0898d5e3',cases=len(cases),source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,artifacts={p.name:sha(p)for p in(fixture,results,err,out/'manifest.json',out/manifest['module_file'])},process=dict(pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-start),application_start_called=False,network_used=False,user_saves_accessed=False)
 (out/'terminal-transition135-probe-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),exit_code=code)))
 if code:raise SystemExit(code)
if __name__=='__main__':main()
