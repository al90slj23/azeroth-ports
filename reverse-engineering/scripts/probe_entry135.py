#!/usr/bin/env python3
"""Observational full1089/2328 host-throw probe, after real1560. Not an entry model."""
from dataclasses import asdict
from collections import Counter
import json,os,signal,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
FILES=tuple(['scripts/probe_entry135.py','scripts/probe_entry135.mjs','scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py']+['reconstruction/core_spec/'+n+'.py'for n in('__init__','initial_state135','initial_state135_data','ability_state','candidates135','derived_stats135','derived_stats134','level_cycle135','progression134','progression','upgrade_values','rng','binary32')]);BEFORE={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.initial_state135 import ConstructorInput135,initialize_empty_profile,projection
from core_spec import binary32 as f
from core_spec.initial_state135_data import ZONE_ENTRIES
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def main():
 rows=[]
 for operation,offset in(('begin',0),('move',0),('move',.1),('move',1)):
  v=ConstructorInput135(8,1,0,1,42,0);state=initialize_empty_profile(v);s=asdict(v);s['seed_u64']=str(v.seed_u64);s['object_id_u64']=str(v.object_id_u64)
  rows.append(json.loads(json.dumps(dict(id=len(rows),input=s,region_id=ZONE_ENTRIES[0][0],expected_before=projection(state),operation=operation,target_xyz=[f.add(state.player_xyz[0],f.from_float(offset)),state.player_xyz[1],state.player_xyz[2]],facing_bits=ZONE_ENTRIES[0][3],declared_scope='Real constructor, no source patches, unknown entry effects; host import attempts must throw'))))
 out,manifest=build(['initial_game','begin_run','move_player']);snap=out/'source-snapshot';snap.mkdir()
 for n in FILES:
  p=snap/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==BEFORE[n]
 fixture=out/'entry135-probe-fixtures.jsonl';fixture.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n'for x in rows));assert[json.loads(s)for s in fixture.read_text().splitlines()]==rows
 frozen={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])};assert sha(RUNTIME)==RUNTIME_SHA;assert subprocess.check_output([str(RUNTIME),'--version'],text=True).strip()=='v22.23.4'
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/probe_entry135.mjs'),str(out),str(fixture)];result=out/'entry135-probe-results.jsonl';stderr=out/'entry135-probe-stderr.log';start=time.monotonic()
 with result.open('w')as stream,stderr.open('w')as err:
  child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned entry probe deadline60s')
 elapsed=time.monotonic()-start
 if code:raise RuntimeError(f'Probe runner failed exit{code}, inspect {out}')
 actual=[json.loads(s)for s in result.read_text().splitlines()];assert[x['id']for x in actual]==list(range(len(rows)));assert all(c['expected_before']==a['before_projection']for c,a in zip(rows,actual))
 after={n:sha(ROOT/n)for n in FILES};assert after==BEFORE;assert sha(SOURCE)==SOURCE_SHA;assert sha(RUNTIME)==RUNTIME_SHA;assert frozen=={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
 receipt=dict(version='0.135.1',build='0898d5e3',kind='observational_host_throw_probe_not_verified_entry_model',cases=len(rows),outcomes=dict(Counter(x['outcome']for x in actual)),constructor_before_model_matches=len(rows),source_sha256_before=BEFORE,source_sha256_after=after,original_wasm_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),artifacts={p.name:sha(p)for p in(fixture,result,stderr,out/'entry135-probe-runtime.json')},runtime=json.loads((out/'entry135-probe-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=round(elapsed,3)),pending='Original entry side effects are observed, not reconstructed by this probe. Neither success nor partialphase1 alone proves the entry producer is independently implemented.')
 (out/'entry135-probe-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),outcomes=receipt['outcomes'],seconds=elapsed)))
if __name__=='__main__':main()
