#!/usr/bin/env python3
"""Independent1391446 XP/currency expectations before bounded full original."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,os,random,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_death_pickups139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from load_world_position139_inputs import load_world139_canonical
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.death_pickups139 import vector139,append_death_pickup139
from core_spec.world_position139_data import ZONE_GEOMETRY139
CANONICAL=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model';CANONICAL_SHA='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
SNAPSHOT=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_world6786.memory';SNAPSHOT_SHA='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def closure():
 files=set(('scripts/check_death_pickups139.py','scripts/build_death_pickups139_oracle.py','scripts/run_death_pickups139_oracle.mjs','scripts/load_world_position139_inputs.py','scripts/production_closure135.py','scripts/source_closure137.py'))|set(production_sources135(ROOT,'core_spec.death_pickups139','resource_spec.world_query135'))
 while True:
  try:return sorted(files),verify_local_source_closure(sorted(files))
  except AssertionError as e:
   pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in files;files.add(pair[1])
def corpus(world,pilot):
 rows=[];cx,cy=ZONE_GEOMETRY139[0][:2];z=world.height(cx,cy).value_bits;centre=(cx,cy,z)
 def add(group,kind,amount,words=(1,2,3,4),counter=14,backing=(),count=0,xyz=centre):
  vec=vector139(tuple(backing),count);r=append_death_pickup139(kind,amount,tuple(xyz),world,tuple(words),counter,0,vector=vec)
  inp=dict(id=len(rows),kind=kind,amount=amount,rng_words=list(words),counter=counter,initial_backing=list(backing),initial_count=count,xyz=list(xyz),now_bits=0)
  expected=dict(capacity=r.vector.capacity,count=r.vector.count,storage56_cells=[list(x)for x in r.vector.storage],counter=r.counter,rng_words=list(r.rng_words),packets=[list(x)for x in r.packets])
  rows.append(dict(id=len(rows),group=group,input=inp,expected=expected,model_diagnostic=dict(position_bits=r.position_bits,guid=None if r.guid is None else str(r.guid),merged_index=r.merged_index,draws=r.draws)))
 raw=tuple(bytes((13*k+17*j)&255 for k in range(56)).hex()for j in range(4))
 add('pilotXP2',0,2);add('pilotcurrency3',1,3,backing=raw)
 if pilot:return json.loads(json.dumps(rows))
 rnd=random.Random(0x1391446);states=[(0,0,0,0),(0xffffffff,0x80000000,123,999)]+[tuple(rnd.getrandbits(32)for _ in range(4))for _ in range(6)]
 for j,words in enumerate(states):
  for kind in(0,1):
   for backing in((),raw):add('XPcurrencymatrix',kind,(0,1,2,3,4,19,20,0xffffffff)[j],words,counter=(0,0xffffffff,0xffffff,0x1000000,14,99,0xfffffffe,0x12345678)[j],backing=backing)
 def row(i,marker=0,kind=0):
  b=bytearray((7*i+13*j)&255 for j in range(56));struct.pack_into('<4I',b,0,marker,0xa5a5a5a5,kind,0xffffffff if i==9 else i+1);struct.pack_into('<3I',b,40,f.add(cx,f.from_float((i%9-4)*.2)),f.add(cy,f.from_float((i//9-2)*.2)),z);return b.hex()
 for n in(44,45,46):add('idle45merge-boundary',0,7,backing=tuple(row(i)for i in range(n)),count=n)
 mixed=tuple(row(i,marker=1 if i%11==0 else 0,kind=1 if i%13==0 else 0)for i in range(52));add('mixed-marker-kind-idlecount',0,0xffffffff,backing=mixed,count=52)
 # Closest idleindex9 hasamountMASK andmustwraponmerge.
 merge=[row(i)for i in range(45)];b=bytearray.fromhex(merge[9]);struct.pack_into('<3I',b,40,*centre);merge[9]=b.hex();add('nearestmerge-wrapping',0,2,backing=tuple(merge),count=45)
 for kind in(0,1):
  for dx,dy in((160,0),(4900,4900)):
   xyz=(f.add(cx,f.from_float(dx)),f.add(cy,f.from_float(dy)),0x461c3c00);add('radialclamp-realworld',kind,4,states[3],xyz=xyz)
 return json.loads(json.dumps(rows))
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files};assert sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
 audit=[];forbidden=[];live=True
 def hook(event,values):
  if event!='open'or not live or not isinstance(values[0],(str,bytes,os.PathLike)):return
  p=Path(os.fsdecode(values[0])).resolve();mode=values[1];flags=values[2];reading=(isinstance(mode,str)and'r'in mode)or(mode is None and isinstance(flags,int)and flags&3==os.O_RDONLY)
  if reading:
   allowed=p.suffix.lower()not in('.memory','.wasm','.wat','.exe');audit.append(dict(path=str(p),allowed=allowed))
   if not allowed:forbidden.append(str(p));raise RuntimeError('Originalinputdeniedduringexpectation')
 sys.addaudithook(hook)
 try:world,provenance=load_world139_canonical(CANONICAL,CANONICAL_SHA);rows=corpus(world,args.phase=='pilot')
 finally:live=False
 assert not forbidden and before=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('death-pickups139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
 for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 expected=out/'expected.json';inputs=out/'inputs.json';save(expected,rows);save(inputs,[r['input']for r in rows]);config=out/'config.json';save(config,dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,game_pointer=14685248,app_pointer=14680072,input_path=str(inputs),input_sha256=sha(inputs)));save(out/'expectation-read-audit.json',dict(kind='Pythonopenaudit_notOSsyscalls',events=audit,forbidden=forbidden));frozen={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/m['module_file'])};save(out/'prepared.json',dict(source_before=before,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_inputs_contain_expected=False,world_provenance=provenance))
 command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_death_pickups139_oracle.mjs'),str(out),str(config)];began=time.monotonic()
 with(out/'stdout.jsonl').open('wb')as so,(out/'stderr.log').open('wb')as se:
  p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=60))
  try:p.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-began,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'process-terminal.json',terminal);actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];diff=[];known=unknown=nonzero=0
 for e,a in zip(rows,actual):
  assert e['id']==a['id'];ep,ob=e['expected'],a['projection']
  for key in(set(ep)|set(ob))-{'storage56_cells','storage56_hex'}:
   if ep.get(key)!=ob.get(key):diff.append(dict(id=e['id'],field=key,expected=ep.get(key),actual=ob.get(key)))
  assert len(ep['storage56_cells'])==len(ob['storage56_hex'])
  for i,(cells,hx)in enumerate(zip(ep['storage56_cells'],ob['storage56_hex'])):
   raw=bytes.fromhex(hx);assert len(raw)==len(cells)==56
   for offset,v in enumerate(cells):
    if v is None:unknown+=1;nonzero+=raw[offset]!=0
    else:
     known+=1
     if raw[offset]!=v:diff.append(dict(id=e['id'],field='record56',index=i,offset=offset,expected=v,actual=raw[offset]))
 assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
 report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed=len(actual),differences=len(diff),source_before=before,source_after=before,source_import_edges=edges,world_provenance=provenance,expected_before_original=True,expectation_reads_forbidden=forbidden,process=terminal,runtime=runtime,comparison=dict(known56_bytes=known,unknown56_bytes=unknown,observed_nonzero_unknown=nonzero,None_not_filled=True),snapshot_sha256=SNAPSHOT_SHA,healthy_v2_context=True,old_badcontext_loaded=False,scope='Full1446 kind0XP andkind1currency,realElwynngeometry/45idlemerge/new56record+169; nofull913deathyet',native_executions=0,complete_games=0,artifacts={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json','stdout.jsonl','stderr.log','process-terminal.json','expectation-read-audit.json')})
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=len(diff),first=diff[:3],process=terminal)),flush=True)
 if p.returncode or len(rows)!=len(actual)or diff:raise SystemExit(1)
if __name__=='__main__':main()
