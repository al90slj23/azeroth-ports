#!/usr/bin/env python3
"""Expected-first narrow1395719 full original pilot with Some XYZ inputs."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
import hashlib,json,os,random,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_npc_spawn139_fresh_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save,missing,binary_identity
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.npc_spawn139 import InitialNPCInput139,initial_normal139,initial_four_normals139,DEFINITION72_HEX,DEFINITION_POINTER,ZONE_SCALING_BITS
from core_spec.initial_state139_data import ZONE_ENTRIES
from core_spec import binary32 as f
SNAPSHOT_SHA='f2cc1e0e1b336e9e923e4cda4401853a380a2c3ad769a3b73805e153a2114b8c'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def closure():
 files=set(('scripts/check_npc_spawn139_fresh.py','scripts/build_npc_spawn139_fresh_oracle.py','scripts/run_npc_spawn139_fresh_oracle.mjs','scripts/production_closure135.py','scripts/source_closure137.py'))|set(production_sources135(ROOT,'core_spec.npc_spawn139'))
 while True:
  try:edges=verify_local_source_closure(sorted(files));return sorted(files),edges
  except AssertionError as e:
   pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in files;files.add(pair[1])

def guard_data():
 import struct
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;identity,_=binary_identity(raw);segments=[s for s in identity['data_segments']if s['address']is not None];mem=bytearray(max(s['address']+s['bytes']for s in segments))
 for s in segments:mem[s['address']:s['address']+s['bytes']]=raw[s['file_offset']:s['file_offset']+s['bytes']]
 assert bytes(mem[DEFINITION_POINTER:DEFINITION_POINTER+72]).hex()==DEFINITION72_HEX
 assert struct.unpack_from('<I',mem,5871348+64)[0]==DEFINITION_POINTER and struct.unpack_from('<I',mem,5871348+136)[0]==ZONE_SCALING_BITS
 assert struct.unpack_from('<I',mem,5871348+140)[0]==0
 return dict(source_sha256=SOURCE_SHA,definition_pointer=DEFINITION_POINTER,raw72_hex=DEFINITION72_HEX,zone5871348_normal64=DEFINITION_POINTER,zone136_scaling_bits=ZONE_SCALING_BITS,zone140_late_bits=0,original_executed=False)

def main():
 files,edges=closure();before={n:sha(ROOT/n)for n in files};data=guard_data();assert sha(NODE)==NODE_SHA
 xy=ZONE_ENTRIES[0][1:3];rows=[];rng=random.Random(0x1395719)
 states=[((1,2,3,4),10),((0,0,0,0),0),((0xffffffff,0x80000000,123,999),0xffffffff)]
 states += [(tuple(rng.getrandbits(32)for _ in range(4)),counter)for counter in(0xfffffe,0xffffff,0x1000000,0xfffffffe,0x12345678)]
 for state_index,(words,counter)in enumerate(states):
  for mode in('preallocated','real-reserve-empty'):
   axes=(((-10,0),(10,0),(0,10),(0,-10)),((-11,-7),(11,-7),(11,7),(-11,7)),((0,0),(-12,.5),(.5,-12),(12,.5)),((-1,7),(-1,-7),(7,-1),(-7,-1)))
   offsets=axes[state_index]if state_index<len(axes)else tuple((rng.uniform(-50,50),rng.uniform(-50,50))for _ in range(4))
   positions=tuple((f.add(xy[0],f.from_float(dx)),f.add(xy[1],f.from_float(dy)),(0,0x41200000,0x3f000000,0xbf800000)[j])for j,(dx,dy)in enumerate(offsets))
   backing=tuple(bytes(((17*state_index+29*j+13*k)&255)for k in range(432)).hex()for j in range(4))if mode=='preallocated'else()
   result=initial_four_normals139(words,counter,positions,backing)
   rows.append(dict(id=len(rows),mode=mode,input=dict(id=len(rows),rng_words=words,counter=counter,positions=positions,initial_backing=backing,player_xy=xy),expected=result['answers'],model_rng_draws=result['model_rng_draws']))
 rows=json.loads(json.dumps(rows))
 assert before=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('npc-spawn139-fresh-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
 for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 expected=out/'expected.json';inputs=out/'inputs.json';save(expected,rows);save(inputs,[r['input']for r in rows]);config=out/'config.json';save(config,dict(inputs=str(inputs),inputs_sha256=sha(inputs)))
 frozen={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/manifest['module_file'])};command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_npc_spawn139_fresh_oracle.mjs'),str(out),str(config)]
 save(out/'prepared.json',dict(source_before=before,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_inputs_contain_expected=False,data=data,deadline_seconds=60))
 began=time.monotonic()
 with(out/'stdout.jsonl').open('wb')as so,(out/'stderr.log').open('wb')as se:
  p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=60))
  try:p.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-began,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'process-terminal.json',terminal)
 actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];diff=[];known=unknown=unknown_nonzero=0
 for e,a in zip(rows,actual):
  assert e['id']==a['id']and len(e['expected'])==len(a['answers'])==4
  for step,(eproj,observed)in enumerate(zip(e['expected'],a['answers'])):
   for key in set(eproj)|set(observed):
    if key in('records432_cells','records432_hex'):continue
    if eproj.get(key)!=observed.get(key):diff.append(dict(id=e['id'],step=step,field=key,expected=eproj.get(key),actual=observed.get(key)))
   for record_index,(cells,raw_hex)in enumerate(zip(eproj['records432_cells'],observed['records432_hex'])):
    raw=bytes.fromhex(raw_hex);assert len(cells)==len(raw)==432
    for offset,v in enumerate(cells):
     if v is None:unknown+=1;unknown_nonzero+=raw[offset]!=0
     else:
      known+=1
      if raw[offset]!=v:diff.append(dict(id=e['id'],step=step,field='known_record_byte',record_index=record_index,offset=offset,expected=v,actual=raw[offset]))
 assert before=={n:sha(ROOT/n)for n in files}and frozen=={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/manifest['module_file'])}
 save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
 report=dict(version='0.139.0',build='f79c5e2b4',cases=len(rows),completed=len(actual),differences=len(diff),source_before=before,source_after=before,source_import_edges=edges,data=data,expected_before_original=True,
  process=terminal,runtime=runtime,snapshot_sha256=None,snapshot_restores=0,constructor1600_true_producer=True,old_snapshot_loaded=False,model_rng_draws_observed_independently=False,
  record_comparison=dict(known_bytes=known,unknown_bytes=unknown,observed_nonzero_unknown_bytes=unknown_nonzero,unknowns_not_filled=True),
  full5719_calls=None if runtime is None else runtime['full5719_calls'],allocation_modes=['preallocated4','actual66565reserve0to4'],
  scope='Full5719/naturalcallees foursequential time0/defaultElwynnNPC SomeXYZ/axes-quadrants-nonaxis-finiteheading; caller432backing orunknownnewpadding; notnaturalplacement/full1108',native_executions=0,complete_games=0,
  artifacts={p.name:sha(p)for p in(expected,inputs,config,out/'manifest.json',out/'stdout.jsonl',out/'stderr.log',out/'differences.json',out/'process-terminal.json')})
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),completed=len(actual),differences=len(diff),first_fields=[x['field']for x in diff[:8]],process=terminal)),flush=True)
 if p.returncode or len(actual)!=len(rows)or diff:raise SystemExit(1)
if __name__=='__main__':main()
