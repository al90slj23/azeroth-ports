#!/usr/bin/env python3
"""Expected-first1395719(None) sequential natural-position component."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,random,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_natural_npc139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save,missing
from load_world_position139_inputs import load_world139_canonical
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.natural_npc139 import NaturalNPCInput139,create_four_natural_normals139
from core_spec.world_position139_v2 import DistanceMap139V2
from core_spec.initial_state139 import seed_rng_words139
from core_spec.world_position139_data import ZONE_GEOMETRY139
CANONICAL=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model';CANONICAL_SHA='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
SNAPSHOT=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_world6786.memory';SNAPSHOT_SHA='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
SEED_WAT=ROOT/'evidence/opening139-context-static-20261102T022955.014560Z/6786.wat'
def closure():
 files=set(('scripts/check_natural_npc139.py','scripts/build_natural_npc139_oracle.py','scripts/run_natural_npc139_oracle.mjs','scripts/load_world_position139_inputs.py','scripts/production_closure135.py','scripts/source_closure137.py'))|set(production_sources135(ROOT,'core_spec.natural_npc139','core_spec.initial_state139','resource_spec.world_query135'))
 while True:
  try:edges=verify_local_source_closure(sorted(files));return sorted(files),edges
  except AssertionError as e:
   pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in files;files.add(pair[1])
def corpus(world,pilot):
 cx,cy=ZONE_GEOMETRY139[0][:2];height=world.height(cx,cy);assert height.found;player=(cx,cy,height.value_bits);rows=[]
 def add(group,words,counter=10,backing=False,velocity=(0,0),xyz=player,path=None,preserve=False):
  n=len(rows);raw=tuple(bytes((17*n+29*j+13*k)&255 for k in range(432)).hex()for j in range(4))if backing else()
  p=None if path is None else DistanceMap139V2(None if path['fill_u16']is None else(path['fill_u16'],)*path['count'],path['field24'])
  state=NaturalNPCInput139(tuple(words),counter,tuple(xyz),tuple(velocity),raw,p);expected=create_four_natural_normals139(state,world)
  inp=dict(id=n,rng_words=list(words),counter=counter,player_xyz=list(xyz),velocity_xy=list(velocity),initial_backing=list(raw),distance_map=path,preserve_constructor_rng=preserve)
  rows.append(dict(id=n,group=group,input=inp,expected=expected['answers'],model_diagnostic=expected['model_diagnostic']))
 # App seed0 controlled by original6786fixture, one actualLCG then1600seed.
 constructor_seed=(0*6364136223846793005+1442695040888963407)&((1<<64)-1)
 add('preserved_true_constructor_rng',seed_rng_words139(constructor_seed),preserve=True)
 add('explicit_rng_nonaxis_callerbacking',(1,2,3,4),backing=True,velocity=(f.from_float(-5),f.from_float(4)))
 if pilot:return json.loads(json.dumps(rows))
 rnd=random.Random(0x13957198740);states=[((0,0,0,0),0),((0xffffffff,0x80000000,123,999),0xffffffff)]+[(tuple(rnd.getrandbits(32)for _ in range(4)),n)for n in(0xfffffe,0xffffff,0x1000000,0xfffffffe,0x12345678,10)]
 for words,counter in states:
  for backing in(False,True):add('natural_four_matrix',words,counter,backing,velocity=(f.from_float(3),f.from_float(-8))if backing else(0,0))
 for path in(dict(field24=400,fill_u16=None,count=None),dict(field24=401,fill_u16=0,count=world.nav.width**2),dict(field24=401,fill_u16=65535,count=world.nav.width**2)):
  add('controlled_pathview',states[3][0],path=path)
 add('forced16plus13563_fallback',states[4][0],xyz=(cx,cy,f.from_float(9999)))
 return json.loads(json.dumps(rows))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files}
 assert sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
 seedtext=SEED_WAT.read_text();assert 'i64.const 6364136223846793005'in seedtext and 'i64.const 1442695040888963407'in seedtext and 'i64.store offset=4928'in seedtext and 'i64.store offset=3128'in seedtext
 audit=[];forbidden=[];live=True
 def hook(event,values):
  if event!='open'or not live or not isinstance(values[0],(str,bytes,os.PathLike)):return
  p=Path(os.fsdecode(values[0])).resolve();mode=values[1];flags=values[2];reading=(isinstance(mode,str)and'r'in mode)or(mode is None and isinstance(flags,int)and flags&3==os.O_RDONLY)
  if reading:
   allowed=p.suffix.lower()not in('.memory','.wasm','.wat','.exe');audit.append(dict(path=str(p),allowed=allowed))
   if not allowed:forbidden.append(str(p));raise RuntimeError('Originalinputdeniedduringindependentexpectations')
 sys.addaudithook(hook)
 try:world,provenance=load_world139_canonical(CANONICAL,CANONICAL_SHA);rows=corpus(world,args.phase=='pilot')
 finally:live=False
 assert not forbidden and before=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('natural-npc139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
 for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 expected=out/'expected.json';inputs=out/'inputs.json';save(expected,rows);save(inputs,[r['input']for r in rows]);config=out/'config.json';save(config,dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,game_pointer=14685248,app_pointer=14680072,input_path=str(inputs),input_sha256=sha(inputs)))
 save(out/'expectation-read-audit.json',dict(kind='Pythonopen_audit_notOSsyscallaudit',events=audit,forbidden=forbidden,originalmemoryonlyhashedbeforeaudit_neverparsedbyexpectationmodel=True));frozen={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/manifest['module_file'])}
 command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_natural_npc139_oracle.mjs'),str(out),str(config)];save(out/'prepared.json',dict(source_before=before,source_import_edges=edges,frozen=frozen,world_provenance=provenance,expected_before_original=True,original_inputs_contain_expected=False,seed_proof_source=str(SEED_WAT),seed_proof_sha256=sha(SEED_WAT),deadline_seconds=60))
 began=time.monotonic()
 with(out/'stdout.jsonl').open('wb')as so,(out/'stderr.log').open('wb')as se:
  p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=60))
  try:p.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-began,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'process-terminal.json',terminal)
 actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];diff=[];known=unknown=unknown_nonzero=0
 for e,a in zip(rows,actual):
  assert e['id']==a['id']and len(e['expected'])==len(a['answers'])==4
  for step,(ep,ob)in enumerate(zip(e['expected'],a['answers'])):
   for key in(set(ep)|set(ob))-{'records432_cells','records432_hex'}:
    if ep.get(key)!=ob.get(key):diff.append(dict(id=e['id'],step=step,field=key,expected=ep.get(key),actual=ob.get(key)))
   for ri,(cells,hx)in enumerate(zip(ep['records432_cells'],ob['records432_hex'])):
    raw=bytes.fromhex(hx);assert len(cells)==len(raw)==432
    for offset,v in enumerate(cells):
     if v is None:unknown+=1;unknown_nonzero+=raw[offset]!=0
     else:
      known+=1
      if raw[offset]!=v:diff.append(dict(id=e['id'],step=step,field='known_record_byte',record_index=ri,offset=offset,expected=v,actual=raw[offset]))
 assert before=={n:sha(ROOT/n)for n in files}and frozen=={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/manifest['module_file'])};save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
 report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed=len(actual),differences=len(diff),source_before=before,source_after=before,source_import_edges=edges,world_provenance=provenance,expected_before_original=True,expectation_python_reads_forbidden=forbidden,process=terminal,runtime=runtime,snapshot_sha256=SNAPSHOT_SHA,healthy_v2_context=True,old_bad5d940snapshot_loaded=False,record_comparison=dict(known_bytes=known,unknown_bytes=unknown,observed_nonzero_unknown_bytes=unknown_nonzero,unknowns_not_filled=True),full5719_calls=None if runtime is None else runtime['full5719_calls'],internal8740_notdirectlyinstrumented=True,model_diagnostics_notoriginalcounters=True,constructor_rng_preserved_firstcase=True,constructor_otherGamefields_notclaimed_independent=True,naturalpathMapproducer_recovered=False,independent_world_Rc_owner=False,native_executions=0,complete_games=0,scope='Four sequential full1395719 with realNone8740→5719yaw/jitter interleaving; healthyv2Rc; expectedraw139world; defaultElwynnNPC; controlledfiniteposition/velocity/path/RNG/backing; notfull1108',artifacts={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/'stdout.jsonl',out/'stderr.log',out/'differences.json',out/'process-terminal.json',out/'expectation-read-audit.json')})
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=len(diff),first=diff[:4],process=terminal)),flush=True)
 if p.returncode or len(actual)!=len(rows)or diff:raise SystemExit(1)
if __name__=='__main__':main()
