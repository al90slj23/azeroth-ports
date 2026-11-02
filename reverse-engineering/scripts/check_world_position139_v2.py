#!/usr/bin/env python3
"""1398740/13563 expected from independentraw139canonical; target healthyv2."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
from collections import Counter
import argparse,hashlib,json,os,random,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_world_position139_v2_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save,missing
from load_world_position139_inputs import load_world139_canonical
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.world_position139_v2 import WorldPositionInput139V2 as WorldPositionInput139,DistanceMap139V2 as DistanceMap139,sample_spawn_position,sample_random_position
from core_spec.world_position139_data import ZONE_GEOMETRY139
STATIC=ROOT/'evidence/world-position139-static-20261102T033613.062984Z/proof.json'
STATIC_SHA='52d2f0cb1afec1ae720337740fac07fab73efc1bbd27a1e8ddcd9498a9852d0d'
CANONICAL=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model'
CANONICAL_RECEIPT_SHA='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
SNAPSHOT=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_world6786.memory'
SNAPSHOT_SHA='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def closure():
 files=set(('scripts/check_world_position139_v2.py','scripts/build_world_position139_v2_oracle.py','scripts/run_world_position139_v2_oracle.mjs','scripts/load_world_position139_inputs.py','scripts/trace_world_position139.py','scripts/production_closure135.py','scripts/source_closure137.py'))|set(production_sources135(ROOT,'core_spec.world_position139_v2','resource_spec.world_query135'))
 while True:
  try:edges=verify_local_source_closure(sorted(files));return sorted(files),edges
  except AssertionError as e:
   pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in files;files.add(pair[1])

PEER_COUNTER=ROOT/'evidence/world-position139-review-work/counterexample.json'
PEER_SHA='cbc42c1bdc0bf26ca72b390bc3b7273d63e3e1241ec3ff3af5526f4411d591ad'
OWN_COUNTER=ROOT/'evidence/position139-rounding-gap-20261102T041910.058498Z/candidate-inputs.json'
OWN_SHA='4518b92340111a0d631b2030ec193638db9fd492f36349264d655e671490a8e2'
OLD_INPUTS=ROOT/'evidence/world-position139-oracle-20261102T035151.444640Z/inputs.json'

def append_clamp_inputs(rows,world,pilot):
 assert sha(PEER_COUNTER)==PEER_SHA and sha(OWN_COUNTER)==OWN_SHA
 candidates=[json.loads(PEER_COUNTER.read_text())['case_input']['input']]+[x['input']for x in json.loads(OWN_COUNTER.read_text())['candidates']]
 if pilot:candidates=candidates[:2]
 for j,raw in enumerate(candidates):
  value=dict(raw)
  for key in('player_xyz','velocity_xy','rng_words'):value[key]=tuple(value[key])
  assert value['distance_map']is None;state=WorldPositionInput139(**value);result=sample_random_position(state,world)
  rows.append(dict(id=len(rows),group='real139-firsttrial-clamp-f32norm-'+str(j),kind='random',input=dict(raw),expected=dict(position_bits=result.position_bits,rng_words=result.rng_words),model_diagnostic=asdict(result)))
 return rows

def corpus(world,pilot):
 rows=[];cx,cy,_=ZONE_GEOMETRY139[0];centre=world.height(cx,cy);assert centre.found;player=(cx,cy,centre.value_bits)
 def add(group,kind='spawn',*,rng=(1,2,3,4),xyz=player,velocity=(0,0),low=26,high=36,bias=.5,path=None):
  p=None if path is None else DistanceMap139(None if path['fill_u16']is None else(path['fill_u16'],)*path['count'],path['field24'])
  state=WorldPositionInput139(0,tuple(xyz),tuple(velocity),f.from_float(low),f.from_float(high),f.from_float(bias),tuple(rng),p)
  result=(sample_spawn_position if kind=='spawn'else sample_random_position)(state,world);inp=asdict(state);inp['distance_map']=path
  rows.append(dict(id=len(rows),group=group,kind=kind,input=inp,expected=dict(position_bits=result.position_bits,rng_words=result.rng_words),model_diagnostic=asdict(result)))
 add('real139world-still')
 add('real139world-nonaxis-bias',velocity=(f.from_float(-5),f.from_float(4)),bias=1)
 add('real139world-forced16then13',xyz=(cx,cy,f.from_float(9999)),low=3,high=8)
 add('real139world-random13-worldfallback','random',rng=(12,34,56,78),xyz=(cx,cy,f.from_float(9999)),low=4900,high=5100)
 if pilot:return json.loads(json.dumps(append_clamp_inputs(rows,world,True)))
 rnd=random.Random(0x1398740)
 states=[(0,0,0,0),(0xffffffff,0x80000000,123,999)]+[tuple(rnd.getrandbits(32)for _ in range(4))for _ in range(6)]
 for words in states:
  add('real139world-still-matrix',rng=words)
  add('real139world-random-matrix','random',rng=words,low=18,high=50)
  for vx,vy in((7,0),(-5,4),(3,-8)):
   add('real139world-moving-matrix',rng=words,velocity=(f.from_float(vx),f.from_float(vy)))
 for dx,dy in((-110,0),(110,0),(0,-100),(0,110)):
  x,y=f.add(cx,f.from_float(dx)),f.add(cy,f.from_float(dy));sample=world.height(x,y)
  if not sample.found:raise NotImplementedError('Declared edgeplayerheight inputunresolved')
  for words in(states[0],states[3]):
   add('real139world-edge',rng=words,xyz=(x,y,sample.value_bits))
   add('real139world-edge-random','random',rng=words,xyz=(x,y,sample.value_bits),low=18,high=50)
 for field,fill in((400,None),(400,0),(401,0),(401,65535),(401,500),(0xffffffff,0)):
  path=dict(field24=field,fill_u16=fill,count=None if fill is None else world.nav.width**2)
  for words in(states[2],states[5]):add('explicitdistance-map400lazy'if fill is None else'explicitdistance-map-cost',rng=words,path=path)
 # Invert one xoshiro transition so the radius draw hasoutput0xffffffff.
 # This forces the finiteupper-exclusive rejection at26..36 afteroneangle.
 desired=(0,1,2,0xffffffff);A,B,C,D=desired;T=((D>>11)|(D<<21))&f.MASK;a=A^T;v=C^B;b=(v^(v<<9)^(v<<18)^(v<<27))&f.MASK;inverse=(a,b,B^a^b,T^b)
 from core_spec.rng import next_u32_words
 _,after=next_u32_words(inverse);out,_=next_u32_words(after);assert tuple(after)==desired and out==f.MASK
 add('radius-upper-exclusive-rejection',rng=inverse)
 add('narrowradius-upper-exclusive-rejection',rng=inverse,low=26,high=f.to_float(0x41d00001))
 for velocity in((f.from_float(2),0),(0x40000001,0),(f.from_float(-5),f.from_float(4))):
  for bias in(0,1):add('velocitythreshold-andbias',rng=states[4],velocity=velocity,bias=bias)
 rows=json.loads(json.dumps(rows));assert[{k:x[k]for k in('id','kind','input')}for x in rows]==json.loads(OLD_INPUTS.read_text())
 return json.loads(json.dumps(append_clamp_inputs(rows,world,False)))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files}
 assert sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA and sha(STATIC)==STATIC_SHA
 static=json.loads(STATIC.read_text());assert static['script_sha256']==sha(ROOT/'scripts/trace_world_position139.py')and sha(ROOT/static['production_data_module'])==static['production_data_sha256']
 audit=[];forbidden=[];live=True
 def hook(event,values):
  if event!='open'or not live or not isinstance(values[0],(str,bytes,os.PathLike)):return
  p=Path(os.fsdecode(values[0])).resolve();mode=values[1];flags=values[2];reading=(isinstance(mode,str)and'r'in mode)or(mode is None and isinstance(flags,int)and flags&3==os.O_RDONLY)
  if reading:
   allowed=p.suffix.lower()not in('.memory','.wasm','.wat','.exe');audit.append(dict(path=str(p),allowed=allowed))
   if not allowed:forbidden.append(str(p));raise RuntimeError('Originalinputdeniedduringindependentexpectations')
 sys.addaudithook(hook)
 try:world,provenance=load_world139_canonical(CANONICAL,CANONICAL_RECEIPT_SHA);rows=corpus(world,args.phase=='pilot')
 finally:live=False
 assert not forbidden and before=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-position139-v2-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
 for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 expected=out/'expected.json';inputs=out/'inputs.json';save(expected,rows);save(inputs,[{k:c[k]for k in('id','kind','input')}for c in rows]);config=out/'config.json';save(config,dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,game_pointer=14685248,app_pointer=14680072,input_path=str(inputs),input_sha256=sha(inputs)))
 save(out/'expectation-read-audit.json',dict(kind='Pythonopen_audit_notOSsyscallaudit',events=audit,forbidden=forbidden,originalmemoryonlyhashedbeforeaudit_neverparsedbyexpectationmodel=True));frozen={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/manifest['module_file'])}
 command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_world_position139_v2_oracle.mjs'),str(out),str(config)];save(out/'prepared.json',dict(source_before=before,source_import_edges=edges,frozen=frozen,world_provenance=provenance,expected_before_original=True,original_input_contains_expected=False,deadline_seconds=60))
 began=time.monotonic()
 with(out/'stdout.jsonl').open('wb')as so,(out/'stderr.log').open('wb')as se:
  p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=60))
  try:p.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-began,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'process-terminal.json',terminal)
 actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];diff=[]
 for e,a in zip(rows,actual):
  assert e['id']==a['id']
  if e['expected']!=a['projection']:diff.append(dict(id=e['id'],group=e['group'],expected=e['expected'],actual=a['projection'],model_diagnostic=e['model_diagnostic']))
 assert before=={n:sha(ROOT/n)for n in files}and frozen=={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/manifest['module_file'])};save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
 report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),actual_cases=len(actual),differences=len(diff),groups=dict(Counter(x['group']for x in rows)),source_before=before,source_after=before,source_import_edges=edges,world_provenance=provenance,
  supersedes_v1_rule_defect=dict(old_receipt='evidence/world-position139-oracle-20261102T035151.444640Z/comparison.json',old_receipt_sha256='eb52328da53d1f90ccba3957f649cd3d52314e20287096e23cac2c46794bb931',rule='13563first12inlinef32sumSquaresThenSqrt; oldmodelincorrectlyused50441f64sumhypot',oldsource_kept=True),
  clamp_input_sources=[dict(path=str(PEER_COUNTER),sha256=PEER_SHA),dict(path=str(OWN_COUNTER),sha256=OWN_SHA)],old80_input_regression=args.phase=='full',source_wasm_sha256=SOURCE_SHA,static_proof_sha256=STATIC_SHA,expected_before_original=True,expectations_from_originalmemory=False,expectation_python_reads_forbidden=forbidden,model_diagnostics_notdirectoriginalcounters=True,
  process=terminal,runtime=runtime,snapshot_sha256=SNAPSHOT_SHA,healthy_v2_context=True,old_bad5d940snapshot_loaded=False,naturalpathMapproducer_recovered=False,independent_world_owner=False,native_executions=0,complete_games=0,
  scope='Full1398740/13563 overhealthyv2realElwynn; expectedquerydata fromindependentraw139canonical; explicitplayer/RNG/pathview inputs; notfull1108/game',
  artifacts={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/'stdout.jsonl',out/'stderr.log',out/'differences.json',out/'process-terminal.json',out/'expectation-read-audit.json')})
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),actual_cases=len(actual),differences=len(diff),first=diff[:2],process=terminal)),flush=True)
 if p.returncode or len(actual)!=len(rows)or diff:raise SystemExit(1)
if __name__=='__main__':main()
