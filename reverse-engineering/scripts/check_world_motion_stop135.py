#!/usr/bin/env python3
"""Expected-first complete17119 over genuine after1089 world snapshot input."""
from dataclasses import asdict,replace
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,math,os,random,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_world_motion_stop135_oracle import build,ROOT,SOURCE,SOURCE_SHA
from build_upgrade134_oracle import sha
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.world_motion_stop135 import WorldMotionStopInput135,stop_world_motion135,UnknownWorldMotionStop135
from core_spec.record_cells135 import cells135,UnknownRecordRead135
from resource_spec.world_query135 import decode_world_snapshot
SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf';WORLD_RC=26204808
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
STRIDES={'units':424,'auxiliary':112,'claims':88}
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def ranges_digest(memory,ranges):
 h=hashlib.sha256()
 for p,n in ranges:h.update(struct.pack('<2I',p,n));h.update(memory[p:p+n])
 return h.hexdigest()
def source_files():
 files=set('scripts/'+n for n in('check_world_motion_stop135.py','build_world_motion_stop135_oracle.py','run_world_motion_stop135_oracle.mjs','build_full135_oracle.py','build_upgrade134_oracle.py','production_closure135.py','source_closure137.py'))
 files.update(production_sources135(ROOT,'core_spec.world_motion_stop135','resource_spec.world_query135'))
 while True:
  try:edges=verify_local_source_closure(sorted(files));return sorted(files),edges
  except AssertionError as error:
   pair=error.args[0]
   if not isinstance(pair,tuple)or len(pair)!=2 or not(ROOT/pair[1]).is_file()or pair[1]in files:raise
   files.add(pair[1])
def row(kind,point,guid,*,start=9,duration=2,dead=False,pattern=0xa5):
 stride,go,ao,bo,so,do=(424,112,316,328,340,344)if kind=='units'else(112,16,32,44,56,60)if kind=='auxiliary'else(88,24,44,56,68,72)
 raw=bytearray([pattern]*stride)
 if kind=='units':struct.pack_into('<I',raw,0,int(dead))
 struct.pack_into('<Q',raw,go,guid)
 x,y=point;origin=(x-2,y-4,17);end=(x+2,y+4,25)
 for offset,values in((ao,origin),(bo,end)):struct.pack_into('<3I',raw,offset,*(f.from_float(v)for v in values))
 struct.pack_into('<2I',raw,so,f.from_float(start),f.from_float(duration));return raw.hex()
def state(c):
 return WorldMotionStopInput135(c['now_bits'],c['sequence'],*(v for name in('units','auxiliary','claims')for v in(tuple(c['storage'][name]),c['counts'][name])),c['packet_capacity'],len(c['prefix']))
def corpus(world,pilot):
 cases=[]
 def add(group,point=(-9396,-633),*,now=10,start=9,duration=2,active=True,include_inactive=True,prefix=(),capacity=0,sequence=31,dead=False,kinds=('units','auxiliary','claims'),copies=1,zero_guid=False):
  storage={};counts={}
  for j,name in enumerate(STRIDES):
   rows=[]
   if name in kinds:
    for i in range(copies):rows.append(row(name,point,0 if zero_guid else (1<<56)+((i%2)*3+j),start=start,duration=duration if active else 0,dead=dead,pattern=0xa5-i))
    if include_inactive:
     rows.append(row(name,point,999+j,start=8,duration=1,dead=True,pattern=0x5a))
   counts[name]=len(rows)
   if rows:rows.append((bytes([0x37])*STRIDES[name]).hex()) # complete unused backing, not an active record
   storage[name]=rows
  inp=dict(id=len(cases),now_bits=f.from_float(now),sequence=sequence,storage=storage,counts=counts,packet_capacity=capacity,prefix=list(prefix));result=stop_world_motion135(state(inp),world)
  expected=dict(sequence=result.state.movement_sequence2412,packet_capacity=result.state.packet_capacity,packet_count=result.state.packet_count,packets=list(prefix)+[dict(opcode=p[0],capacity=p[1],payload_hex=p[2])for p in result.packets],vectors={name:dict(count=getattr(result.state,name+'_count'),storage=list(getattr(result.state,name+'_storage')))for name in STRIDES},heights=[asdict(h)for h in result.heights],stopped_guids=[str(v)for v in result.stopped_guids])
  cases.append(dict(id=len(cases),group=group,input=inp,expected=expected))
 add('real-nonflat-Elwynn-three-domains');add('true-world-miss-preserves-interpolatedZ',(100000,100000));add('all-inactive-real-world-not-consumed',active=False,include_inactive=False)
 add('claim-zero-duration-future-start-only-destination',start=11,duration=0,kinds=('claims',),include_inactive=False)
 if pilot:return cases
 prefix=(dict(opcode=199,capacity=32,payload_hex='0011000000'),dict(opcode=42,capacity=16,payload_hex='12345678'))
 add('prefix-all-metadata-and-wrapping-sequence',prefix=prefix,capacity=2,sequence=0xffffffff,zero_guid=True)
 add('dead-NPC-does-not-stop-aux-claims-still-stop',dead=True)
 add('negative-ratio-clamps-before-actual-world-query',start=11,duration=2)
 add('exact-end-all-three-predicates-inactive',start=9,duration=1,include_inactive=False)
 rng=random.Random(0x1711917217)
 for _ in range(16):add('real-nonflat-local-Elwynn-height',point=(rng.uniform(-9536,-9256),rng.uniform(-773,-493)))
 for _ in range(8):add('actual-nine-tile-geometry',point=(rng.uniform(-10200,-8450),rng.uniform(-1650,50)),include_inactive=False)
 secondary=world.secondary;assert secondary is not None
 finite=[i for i,v in enumerate(secondary.values_bits)if not f.is_nan(v)]
 for i in finite[::max(1,len(finite)//8)][:8]:
  x=f.to_float(secondary.origin_xy_bits[0])+(i%secondary.width+.5)*.5;y=f.to_float(secondary.origin_xy_bits[1])+(i//secondary.width+.5)*.5
  add('actual-secondary-height-cache-nonflat',point=(x,y),include_inactive=False)
 for tile in world.tiles[:2]:
  a,b,c,d=map(f.to_float,tile.bounds_bits)
  for point in((a,(b+d)/2),(c,(b+d)/2),((a+c)/2,b),((a+c)/2,d)):
   add('actual-terrain-tile-exact-boundaries',point=point,include_inactive=False)
 a=min(f.to_float(t.bounds_bits[0])for t in world.tiles);b=min(f.to_float(t.bounds_bits[1])for t in world.tiles);c=max(f.to_float(t.bounds_bits[2])for t in world.tiles);d=max(f.to_float(t.bounds_bits[3])for t in world.tiles)
 for point in((a-1,(b+d)/2),(c+1,(b+d)/2),((a+c)/2,b-1),((a+c)/2,d+1)):add('outside-true-world-boundary-miss',point=point,include_inactive=False)
 for name in STRIDES:add('single-source-exact-order-'+name,kinds=(name,),sequence=0xfffffffe)
 add('duplicate-GUID-stable-order-and-vector-growth',copies=5,include_inactive=False,capacity=1,prefix=prefix[:1],sequence=0xfffffff8)
 return json.loads(json.dumps(cases,ensure_ascii=False))
def partial_projection(c,world):
 full=state(c['input']);changes={}
 for name,stride in STRIDES.items():
  projected=[]
  for index,value in enumerate(getattr(full,name+'_storage')):
   raw=bytes.fromhex(value);known=[]
   if index<getattr(full,name+'_count'):
    word=lambda o:struct.unpack_from('<I',raw,o)[0];now=f.to_float(full.now_bits)
    if name=='units':
     known=[(0,4)]
     if word(0)==0:
      known.append((344,348))
      if f.to_float(word(344))>0:
       known.append((340,344))
       if now<f.to_float(f.add(word(344),word(340))):known.extend(((112,120),(316,340)))
    elif name=='auxiliary':
     known=[(60,64)]
     if f.to_float(word(60))>0:
      known.append((56,60))
      if now<f.to_float(f.add(word(60),word(56))):known.extend(((16,24),(32,56)))
    else:
     known=[(68,76)]
     if not now>=f.to_float(f.add(word(68),word(72))):
      known.extend(((24,32),(56,68)))
      if not f.to_float(word(72))<=0:known.append((44,56))
   projected.append(tuple(v if any(a<=j<b for a,b in known)else None for j,v in enumerate(raw)))
  changes[name+'_storage']=tuple(projected)
 partial=replace(full,**changes);result=stop_world_motion135(partial,world);full_result=stop_world_motion135(full,world);assert result.packets==full_result.packets and result.heights==full_result.heights
 known=preserved=0;vectors={}
 for name,stride in STRIDES.items():
  rows=[]
  for before,after,physical in zip(getattr(partial,name+'_storage'),getattr(result.state,name+'_storage'),getattr(full_result.state,name+'_storage'),strict=True):
   values=cells135(after,stride);actual=bytes.fromhex(physical)
   for j,value in enumerate(values):
    if value is None:assert before[j]is None;preserved+=1
    else:assert value==actual[j];known+=1
   rows.append(values)
  vectors[name]=rows
 return dict(case_id=c['id'],known_bytes=known,unknown_cells_preserved=preserved,vectors=vectors)
def negatives(c,world):
 s=state(c['input']);rows=[]
 try:stop_world_motion135(s,None)
 except UnknownWorldMotionStop135 as error:rows.append(dict(case='active-world-unknown',error=str(error)))
 else:raise AssertionError('Missing world silently accepted')
 unit=list(bytes.fromhex(s.units_storage[0]));unit[0]=None
 try:stop_world_motion135(replace(s,units_storage=(tuple(unit),)+s.units_storage[1:]),world)
 except UnknownRecordRead135 as error:rows.append(dict(case='consumed-marker-unknown',error=str(error)))
 else:raise AssertionError('Unknown marker silently accepted')
 return rows
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();files,edges=source_files();before={n:sha(ROOT/n)for n in files}
 assert sha(SNAPSHOT)==SNAPSHOT_SHA and sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
 memory=SNAPSHOT.read_bytes();world=decode_world_snapshot(memory,WORLD_RC);assert world.flat_height_bits is None and world.primary is None and world.secondary is not None and len(world.tiles)==9
 ranges=sorted(set((p,n)for _,p,n in world.source_ranges));world_digest=ranges_digest(memory,ranges);summary=dict(tiles=len(world.tiles),primary_present=world.primary is not None,secondary_width=world.secondary.width,flat_height_enabled=False,source_ranges=len(ranges),source_bytes=sum(n for _,n in ranges),expected_world_digest=world_digest,snapshot_sha256=SNAPSHOT_SHA,snapshot_bytes=len(memory),world_rc=WORLD_RC);del memory
 cases=corpus(world,args.phase=='pilot');partials=[partial_projection(cases[i],world)for i in(0,2,3)];rejected=negatives(cases[0],world)
 # The entire inactive branch is valid even when no world input is resolved.
 assert not stop_world_motion135(state(cases[2]['input']),None).packets
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-motion-stop135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
 for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 save(out/'fixtures.json',cases);save(out/'expected.json',[dict(id=c['id'],expected=c['expected'])for c in cases]);save(out/'world-summary.json',summary);save(out/'partial-projections.json',partials);save(out/'rejections.json',rejected)
 inputs=dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,world_rc=WORLD_RC,world_ranges=ranges,expected_world_digest=world_digest,cases=[c['input']for c in cases]);save(out/'inputs.json',inputs)
 frozen={p.name:sha(p)for p in(out/'fixtures.json',out/'expected.json',out/'inputs.json',out/'world-summary.json',out/'partial-projections.json',out/'rejections.json',out/'manifest.json',out/manifest['module_file'])}
 assert before=={n:sha(ROOT/n)for n in files}
 cmd=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_world_motion_stop135_oracle.mjs'),str(out),str(out/'inputs.json')];save(out/'prepared.json',dict(expected_before_original=True,source_sha256=before,source_import_edges=edges,artifacts=frozen,command=cmd,deadline_seconds=60));began=time.monotonic()
 with(out/'stdout.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
  child=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=cmd,deadline_seconds=60))
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
 def missing(group=False):
  try:(os.killpg if group else os.kill)(child.pid,0)
  except ProcessLookupError:return True
  return False
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-began,deadline_seconds=60,pid_missing=missing(),pgid_missing=missing(True));save(out/'owned-terminal.json',terminal)
 actual=[json.loads(v)for v in(out/'stdout.jsonl').read_text().splitlines()];counts=Counter();differences=[]
 if code or len(actual)!=len(cases):save(out/'failure.json',dict(terminal=terminal,cases=len(cases),completed=len(actual)));print(json.dumps(dict(status='original_failed',out=str(out.relative_to(ROOT)),terminal=terminal,stderr=(out/'stderr.log').read_text()[-2000:])));raise SystemExit(1)
 for c,a in zip(cases,actual,strict=True):
  assert c['id']==a['id'];e=c['expected'];before_raw=bytes.fromhex(a['before']['raw_game2592_hex']);raw=bytes.fromhex(a['after']['raw_game2592_hex']);after=a['after'];queue=after['queue']
  for name,value in(('sequence',struct.unpack_from('<I',raw,2412)[0]),('packet_capacity',queue['capacity']),('packet_count',queue['count']),('packets',queue['packets']),('vectors',after['vectors'])):
   if value!=e[name]:differences.append(dict(id=c['id'],field=name,expected=e[name],actual=value))
  assert a['before']['vectors']=={name:dict(count=c['input']['counts'][name],storage=c['input']['storage'][name])for name in STRIDES}
  assert a['before']['queue']['packets']==c['input']['prefix'];assert queue['active_metadata_hex'][:len(c['input']['prefix'])*32]==a['before']['queue']['active_metadata_hex'];counts['prefix_metadata_bytes_exact']+=len(c['input']['prefix'])*16
  wanted=bytearray(before_raw)
  for offset,value in((2412,e['sequence']),(1880,e['packet_capacity']),(1888,e['packet_count'])):struct.pack_into('<I',wanted,offset,value)
  if a['before']['queue']['capacity']!=queue['capacity']:wanted[1884:1888]=raw[1884:1888];counts['observed_new_packet_vector_pointer_words']+=1
  if bytes(wanted)!=raw:differences.append(dict(id=c['id'],field='all_Game2592_invariant',offsets=[j for j,(x,y)in enumerate(zip(wanted,raw))if x!=y]))
  assert a['before']['world']==a['after']['world']==dict(sha256=world_digest,bytes=summary['source_bytes'])and a['world_rc']==WORLD_RC
  assert a['full17119']and a['stack_after']==1048576 and a['host_calls']==0 and a['snapshot_bytes']==summary['snapshot_bytes']
  counts['all_Game_bytes_compared']+=len(raw);counts['full_physical_source_bytes_compared']+=sum(len(bytes.fromhex(v))for entries in e['vectors'].values()for v in entries['storage']);counts['new221_packets']+=len(e['packets'])-len(c['input']['prefix']);counts['cases']+=1
  for p in partials:
   if p['case_id']!=c['id']:continue
   for name,rows in p['vectors'].items():
    for projected,physical in zip(rows,after['vectors'][name]['storage'],strict=True):
     values=bytes.fromhex(physical)
     for j,value in enumerate(projected):
      if value is not None:assert values[j]==value;counts['partial_known_bytes_original_compared']+=1
   counts['partial_None_preserved_model_only']+=p['unknown_cells_preserved']
 assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}and sha(SNAPSHOT)==SNAPSHOT_SHA
 runtime=json.loads((out/'runtime.json').read_text());receipt=dict(status='scoped_original_differential_passed'if not differences else'differences',version='0.135.1',actual_build='90898d5e3',phase=args.phase,cases=len(cases),full_original17119_calls=len(actual),differences=len(differences),difference_rows=differences[:100],counts=dict(counts),groups=dict(Counter(c['group']for c in cases)),model_height_sources=dict(Counter(h['source']for c in cases for h in c['expected']['heights'])),height_sources_instrumented=False,source_sha256_before=before,source_sha256_after=before,source_import_edges=edges,source_files=len(files),expected_before_original=True,input_contains_expected=False,world=summary,world_input_is_snapshot=True,fresh_world_producer=False,externref_table_restored=False,only_changed_section=7,original_sha256=SOURCE_SHA,manifest_sha256=sha(out/'manifest.json'),module_sha256=manifest['module_sha256'],frozen_artifacts=frozen,artifacts={n:sha(out/n)for n in('stdout.jsonl','stderr.log','runtime.json','owned-terminal.json','prepared.json')},runtime=runtime,process=terminal,limitations=['Fresh original instances restore genuine after1089 snapshot world/allocator bytes; no world boot/constructor or externref VM restoration is claimed.','All complete17119/17217/16340 bodies/callees unchanged; actual17119 calls counted, internal callee counts are not instrumented.','Elwynn snapshot primaryRc56 is absent: actual29631 nonflat hits and real misses compared; nearest23181 Z-only fallback is static/interface support, not a new actual primary producer experiment.','Partial-cell known bytes are checked against the same original cases; preservation of None and missing-world/unknown-marker refusal are model checks, not extra original cases.','Game2592 invariant checked using physical prestate with only newly allocated packet-vector pointer observed; source backing and all packet payload/capacity bytes compared.','World source digest covers exactly independently parsed query input ranges and is persisted before/after each case.','No actualAI/incoming/fatal/same-state full-game integration, native runtime, 880 or freshworld producer.'])
 save(out/'comparison.json',receipt);print(json.dumps(dict(status=receipt['status'],out=str(out.relative_to(ROOT)),comparison_sha256=sha(out/'comparison.json'),cases=len(cases),differences=len(differences),first_differences=differences[:3],counts=dict(counts),model_height_sources=receipt['model_height_sources'],process=terminal)))
 if differences:raise SystemExit(1)
if __name__=='__main__':main()
