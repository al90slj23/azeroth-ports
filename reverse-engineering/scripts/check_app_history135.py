#!/usr/bin/env python3
"""Expected-first full empty history and scoped real address-entropy experiment."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from trace_app_history135 import ROOT,build
from source_closure135 import core_sources
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.app_history135 import empty_history135,RandomState135,app_hash_maps135

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
 files=('scripts/check_app_history135.py','scripts/run_app_history135_oracle.mjs','scripts/trace_app_history135.py','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/source_closure135.py')+core_sources(ROOT,'app_history135.py')
 before={p:sha(ROOT/p)for p in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('app-history0135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
 for n,h in before.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
 cases=[];expected=[]
 for i in range(24):
  c=dict(id=i,input=dict(offset=i%8,poison=(0,0xa5,0xff)[i//8],warm_bytes=(0,1,4096,65536)[i%4]));cases.append(c)
  data=bytearray([c['input']['poison']]*512);start=64+c['input']['offset'];data[start:start+240]=empty_history135();expected.append(dict(id=i,initialized=data.hex(),dropped=data.hex(),seed_first=1048559,seed_flag=1,entropy_first=1048575,stack=1048576,seed_second=None,entropy_second=None))
 (out/'inputs.json').write_text(json.dumps(cases)+'\n');(out/'expected.json').write_text(json.dumps(expected)+'\n')
 # Inline4253 typed-state replay is separate from new complete-entry counts.
 typed=[]
 for a,b in[(0,0),(1,2),((1<<64)-3,(1<<64)-1)]:
  r=app_hash_maps135(RandomState135(a,b));typed.append(dict(input=[str(a),str(b)],bytes128=r.bytes128.hex(),next_state=[str(r.next_state.first),str(r.next_state.second)]));assert len(r.bytes128)==128 and r.next_state.first==(a+4)&((1<<64)-1)
 (out/'typed-inline-state-replay.json').write_text(json.dumps(typed,indent=2)+'\n')
 frozen={p.name:sha(p)for p in(out/'inputs.json',out/'expected.json',out/'manifest.json',out/manifest['module_file'],out/'typed-inline-state-replay.json')}
 node=ROOT/'.toolchain/runtime/node_modules/node/bin/node';assert sha(node)=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
 cmd=[str(node),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_app_history135_oracle.mjs'),str(out)];start=time.monotonic()
 with(out/'results.jsonl').open('wb')as stream,(out/'stderr.log').open('wb')as err:
  child=subprocess.Popen(cmd,stdout=stream,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
 for fn in(os.kill,os.killpg):
  try:fn(child.pid,0);raise AssertionError('Process/group remains')
  except ProcessLookupError:pass
 after={n:sha(ROOT/n)for n in files};assert before==after and all(sha(out/n)==h for n,h in frozen.items())
 rows=[json.loads(x)for x in(out/'results.jsonl').read_text().splitlines()];errors=[];observed=[]
 if len(rows)!=24:errors.append({'case_count':len(rows)})
 for e,r in zip(expected,rows):
  for k in('id','initialized','dropped','stack'):
   if e[k]!=r[k]:errors.append(dict(id=e['id'],field=k))
  sb=bytes.fromhex(r['seeded']);eb=bytes.fromhex(r['entropy']);sf=int.from_bytes(sb[:8],'little');ef=int.from_bytes(eb[:8],'little');sp=int.from_bytes(sb[8:16],'little');ep=int.from_bytes(eb[8:16],'little')
  if(sf,sb[16],ef)!=(e['seed_first'],e['seed_flag'],e['entropy_first']):errors.append(dict(id=e['id'],field='known_entropy_projection'))
  assert 0<sp<r['memory_bytes'] and 0<ep<r['memory_bytes'] and r['host_calls']==0
  observed.append(dict(id=e['id'],seed_second=sp,entropy_second=ep,seed_first=sf,entropy_first=ef))
 runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
 receipt=dict(version='0.135.1',build='0898d5e3',status='passed'if code==0 and not errors else'failed_preserved',cases=24,original_calls=96,differences=len(errors),errors=errors,source_count=len(before),source_sha256_before=before,source_sha256_after=after,frozen_artifacts=frozen,runtime=runtime,process=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60,pid_and_pgid_missing=True),complete53845_bytes=24*240,empty28797_buffer_invariance_cases=24,entropy_known_bytes=24*(9+8),entropy_opaque_observed_bytes=24*16,address_entropy_observations=observed,seed_or_once_injected=False,typed4253_replay_cases=3,new_original4253_cases=0,new_original_app_or_mainloop_cases=0,limitations=['53845 complete240B and empty28797 only; nonempty history destruction not accepted here.','60416 and81334 known stack/flag projection only; allocator-address second word is opaque, not predicted.','4253 fourmap constructor is static typed-state replay, not full4253 runtime acceptance.','No complete App/history usage/880/ownership/game acceptance.'],artifacts={p.name:sha(p)for p in(out/'results.jsonl',out/'runtime.json',out/'stderr.log')if p.exists()})
 target=out/'comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),receipt_sha256=sha(target),status=receipt['status'],differences=len(errors))))
 if code or errors:raise SystemExit(1)

if __name__=='__main__':main()
