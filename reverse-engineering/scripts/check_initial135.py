#!/usr/bin/env python3
"""Full1560 differential from explicit unearned/untalented selected profiles."""
from dataclasses import asdict
from collections import Counter
import argparse,json,os,signal,subprocess,sys,time,random
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
SOURCE_FILES=tuple(['scripts/check_initial135.py','scripts/run_initial135_oracle.mjs','scripts/trace_initial135.py',
 'scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py']+['reconstruction/core_spec/'+n+'.py'for n in('__init__','initial_state135','initial_state135_data','ability_state','candidates135','derived_stats135','derived_stats134','level_cycle135','progression134','progression','upgrade_values','rng','binary32')])
IMPORT_HASH={n:sha(ROOT/n)for n in SOURCE_FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.initial_state135 import ConstructorInput135,initialize_empty_profile,projection
from core_spec.initial_state135_data import ZONE_ENTRIES
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def corpus(phase):
 rows=[]
 def add(group,cls,race,region,seed,object_id,height):
  value=ConstructorInput135(cls,race,region,seed,object_id,height);s=asdict(value);s['seed_u64']=str(seed);s['object_id_u64']=str(object_id)
  rows.append(json.loads(json.dumps(dict(id=len(rows),group=group,input=s,region_id=ZONE_ENTRIES[region][0],expected=projection(initialize_empty_profile(value))))))
 add('pilot-class8-human-real-starters',8,1,0,1,42,0)
 add('pilot-class1-orc',1,2,0,0,1,0)
 add('pilot-class4-gnome',4,7,0,(1<<64)-1,999,0)
 if phase=='pilot':return rows
 for cls in (1,2,3,4,5,7,8,9,11):
  for race in range(1,9):add('all-class-race-constructor-domain',cls,race,0,0x123456789abcdef,42,0)
 for region in range(12):
  for seed in (0,1,(1<<64)-1):add('all-zone-flat-entry-seeded',8,1,region,seed,0xffffffff,0x41200000)
 rng=random.Random(0x1351560)
 for i in range(40):add('seed-matrix',8,1,0,rng.getrandbits(64),rng.getrandbits(64),0)
 return rows


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in SOURCE_FILES};assert before==IMPORT_HASH
 rows=corpus(args.phase);out,manifest=build(['initial_game']);snap=out/'source-snapshot';snap.mkdir()
 for n in SOURCE_FILES:
  p=snap/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==before[n]
 fixture=out/'initial135-fixtures.jsonl';fixture.write_text(''.join(json.dumps(c,separators=(',',':'))+'\n'for c in rows));assert[json.loads(s)for s in fixture.read_text().splitlines()]==rows
 frozen={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])};assert sha(RUNTIME)==RUNTIME_SHA;assert subprocess.check_output([str(RUNTIME),'--version'],text=True).strip()=='v22.23.4'
 cmd=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_initial135_oracle.mjs'),str(out),str(fixture)];result=out/'initial135-original-results.jsonl';err=out/'initial135-stderr.log';started=time.monotonic()
 with result.open('w')as stream,err.open('w')as errors:
  child=subprocess.Popen(cmd,stdout=stream,stderr=errors,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned initial135 constructor oracle deadline60s')
 duration=time.monotonic()-started
 if code:raise RuntimeError(f'Original failed exit{code}; inspect {out}')
 actual=[json.loads(s)for s in result.read_text().splitlines()];assert[x['id']for x in actual]==list(range(len(rows)))
 failures=[dict(id=c['id'],group=c['group'],expected=c['expected'],actual=a['projection'])for c,a in zip(rows,actual)if c['expected']!=a['projection']];mismatch=out/'initial135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
 after={n:sha(ROOT/n)for n in SOURCE_FILES};assert before==after;assert sha(SOURCE)==SOURCE_SHA;assert sha(RUNTIME)==RUNTIME_SHA;assert frozen=={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(rows),mismatch_cases=len(failures),groups=dict(Counter(c['group']for c in rows)),source_sha256_before=before,source_sha256_after=after,wasm_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),artifacts={p.name:sha(p)for p in(fixture,result,err,mismatch,out/'initial135-runtime.json')},runtime=json.loads((out/'initial135-runtime.json').read_text()),process=dict(command=cmd,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=round(duration,3)),independent_expected_before_original=True,source_snapshots=True,only_changed_section=7,limitations=['Whole original1560 executes, but comparison projects numeric/record fields; raw2592B output preserved separately, including unknown physical pointers.','Input is a declared empty selected-profile376; upstream account/character48/profile producer and real asset registration remain incomplete.','Class/race matrix is constructor domain coverage, not proof all pairs are selectable in original UI.','No phase1 world entry or racial execution/effect behavior is claimed.'])
 (out/'initial135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(rows),mismatch_cases=len(failures),first_ids=[x['id']for x in failures[:12]],seconds=duration)))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
