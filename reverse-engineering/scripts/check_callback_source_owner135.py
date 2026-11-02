#!/usr/bin/env python3
"""Expected-first fresh1560 and controlled full1072 source-header component."""
from dataclasses import asdict
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.callback_source_owner135 import (CallbackSourcesProfile135,
    produce_callback_source_owner135,empty_research_callback_sources135,
    retain_callback_sources_after_selection135,UnknownCallbackSourceOwner135)
from core_spec.candidates135 import Candidate
from core_spec.ability_state135 import DEFINITIONS

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def main():
 scripts=('check_callback_source_owner135.py','run_callback_source_owner135_oracle.mjs',
    'full135_host.mjs','build_full135_oracle.py','build_upgrade134_oracle.py',
    'production_closure135.py','source_closure137.py')
 files=tuple('scripts/'+name for name in scripts)+production_sources135(ROOT,
    'core_spec.callback_source_owner135','core_spec.ability_state135')
 edges=verify_local_source_closure(files);before={name:sha(ROOT/name)for name in files}
 rows=[];expected=[]
 for cls in(1,2,3,4,5,7,8,9,11):
  owner=empty_research_callback_sources135();cards=[];stages=[dict(role=1560,headers=dict(owner.constructor_headers),ring968=[0,4,0,0])]
  selected=[Candidate('upgrade',tier=1,owned_index=0,kinds=(i,))for i in range(5)]
  selected+=[Candidate('upgrade',tier=0,owned_index=0,kinds=()),Candidate('gold',gold=17)]
  if cls==1:selected+=[Candidate('new',tier=0,ability_id='cleave')]
  for card in selected:
   owner=retain_callback_sources_after_selection135(owner,card,phase2587=2,selection_kind2585=0)
   raw=asdict(card)
   if card.variant=='new':raw['definition_pointer']=DEFINITIONS[card.ability_id.encode()].pointer
   cards.append(raw);stages.append(dict(role=1072,headers=dict(owner.constructor_headers),phase2587=1))
  rows.append(dict(id=len(rows),class_byte=cls,race_byte=1,region_id='elwynn',seed='0',object_id='42',flat_height_bits=0,selections=cards))
  expected.append(dict(id=len(expected),stages=stages,profileBefore=dict(ranked_count160=0,ranked_flag164=0,equipped19=[0]*19),profileAfter=dict(ranked_count160=0,ranked_flag164=0,equipped19=[0]*19)))
 refusals=[]
 for name,profile in(('unknown-count',CallbackSourcesProfile135(None,0,(0,)*19)),('nonzero-count',CallbackSourcesProfile135(1,0,(0,)*19)),('unknown-flag',CallbackSourcesProfile135(0,None,(0,)*19)),('nonzero-flag',CallbackSourcesProfile135(0,1,(0,)*19)),('gear',CallbackSourcesProfile135(0,0,(100000,)+(0,)*18)),('unknown-gear',CallbackSourcesProfile135(0,0,(None,)+(0,)*18))):
  try:produce_callback_source_owner135(profile)
  except UnknownCallbackSourceOwner135:refusals.append(name)
  else:raise AssertionError('Unknown source admitted')
 for name,kind,variant in(('priority-kind',1,'upgrade'),('equipment-card',0,'item')):
  try:retain_callback_sources_after_selection135(empty_research_callback_sources135(),Candidate(variant),phase2587=2,selection_kind2585=kind)
  except UnknownCallbackSourceOwner135:refusals.append(name)
  else:raise AssertionError('Mutation branch admitted')
 out,manifest=build(['initial_game','select_ability'])
 for name,h in before.items():
  target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes());assert sha(target)==h
 for name,value in(('input.json',rows),('expected.json',expected),('model-refusals.json',refusals)):save(out/name,value)
 artifacts={name:sha(out/name)for name in('input.json','expected.json','model-refusals.json','manifest.json',manifest['module_file'])}
 assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
 command=[str(NODE),'--max-old-space-size=256','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_callback_source_owner135_oracle.mjs'),str(out),str(out/'input.json')]
 save(out/'prepared.json',dict(expected_before_original=True,source_sha256=before,artifacts=artifacts,command=command,deadline_seconds=60))
 began=time.monotonic();error=None
 with(out/'actual.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
  p=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,deadline_seconds=60,command=command))
  try:p.wait(timeout=60)
  except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as exc:error=repr(exc)
  finally:
   if p.poll()is None:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=2)
 def missing(group=False):
  try:(os.killpg if group else os.kill)(p.pid,0)
  except ProcessLookupError:return True
  return False
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,error=error)
 save(out/'process-terminal.json',terminal);diff=[];runtime=None
 if p.returncode==0:
  actual=[json.loads(line)for line in(out/'actual.jsonl').read_text().splitlines()];assert len(actual)==len(expected)
  for want,got in zip(expected,actual):
   # JSON numeric keys are canonical strings in the expected persisted form.
   if json.loads(json.dumps(want))!=got:diff.append(dict(expected=want,actual=got))
  runtime=json.loads((out/'callback-source-owner-runtime.json').read_text());assert runtime['actual_host_calls']==0 and runtime['max_memory_bytes']<=33554432
 save(out/'differences.json',diff);after={name:sha(ROOT/name)for name in files};assert before==after and artifacts=={name:sha(out/name)for name in artifacts}
 report=dict(version='0.135.1',original_sha256=SOURCE_SHA,cases=len(rows),full1560=len(rows),full1072=sum(len(row['selections'])for row in rows),differences=len(diff)if p.returncode==0 else None,expected_before_original=True,source_files=len(files),local_source_import_edges=edges,source_sha256_before=before,source_sha256_after=after,frozen_artifacts=artifacts,runtime=runtime,process=terminal,scope='Fresh actual1560 declared blank376 profile; then explicit controlledphase2/kind0 complete1072 upgrades/gold/onelearn. Sourceheaders andinputprofile slices only; notnaturalApp/selection/gameplay.',limits=['No nonempty ranked-profile/equipment/trait/summon producer restored','No stack-global export or percall stack receipt in this inherited full135 host; normal entry returns and0host observed','No naturalXP/menu card producer or completefatal acceptance','Model refusals are not extraoriginalcases'])
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),cases=len(rows),full1560=report['full1560'],full1072=report['full1072'],differences=report['differences'],comparison_sha256=sha(out/'comparison.json'),process=terminal)),flush=True)
 if p.returncode or error or diff or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)


if __name__=='__main__':main()
