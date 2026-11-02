#!/usr/bin/env python3
"""New model expectations against frozen56 original captures; no original runs.

Reads fixture INPUT only, freezes both expectations, then opens historical
stdout. This ordering is not a claim that the author was blind to old results.
Unknown queue headers are never borrowed from the historical actual capture.
"""
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from core_spec.world_motion_stop135 import WorldMotionStopInput135,stop_world_motion135,UnknownWorldMotionStop135
from resource_spec.world_query135 import decode_world_snapshot

HISTORY=ROOT/'evidence/world-motion-stop135-oracle-20261102T000919.144127Z'
SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
WORLD_RC=26204808
OLD_MODEL_SHA='709afc4d28df4b170d2dfb62bfcc367a5d006e01a852bf9052233f75cc7e4bed'
PINNED={
 'inputs.json':'0cb8885a758d04abe1745bedcdbb5bb3370645015ed153768fa81c0381253143',
 'stdout.jsonl':'16df5d5973097199c2d00e2e48002451725c3f0b685079109a93dbe599f419d2',
 'comparison.json':'8a49cd52bcaaf2b8fbd803ab0476f1dce459e7c837a57ac6b4c16bb83a983e99',
 'world-summary.json':'69714c603c42ed43eef6930b22b80ec5c591c002282c2055471b3e9a2ca29c6e',
}
STRIDES={'units':424,'auxiliary':112,'claims':88}
def sha(path):
 h=hashlib.sha256()
 with path.open('rb')as stream:
  while block:=stream.read(4<<20):h.update(block)
 return h.hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def sources():
 names=set(production_sources135(ROOT,'core_spec.world_motion_stop135','resource_spec.world_query135'))
 names.update('scripts/'+v for v in('check_world_motion_stop135_header_projection.py','production_closure135.py','source_closure137.py'))
 while True:
  try:return sorted(names),verify_local_source_closure(sorted(names))
  except AssertionError as error:
   pair=error.args[0]
   if not isinstance(pair,tuple)or len(pair)!=2 or not(ROOT/pair[1]).is_file()or pair[1]in names:raise
   names.add(pair[1])
def state(case,known):
 return WorldMotionStopInput135(case['now_bits'],case['sequence'],*(v for name in STRIDES for v in(tuple(case['storage'][name]),case['counts'][name])),case['packet_capacity']if known else None,len(case['prefix'])if known else None)
def projection(result):
 return dict(sequence=result.state.movement_sequence2412,
  packet_capacity=result.state.packet_capacity,packet_count=result.state.packet_count,
  packet_header_known=result.packet_header_known,complete=result.complete,pending=list(result.pending),
  vectors={name:dict(count=getattr(result.state,name+'_count'),storage=list(getattr(result.state,name+'_storage')))for name in STRIDES},
  new_packets=[dict(opcode=p[0],capacity=p[1],payload_hex=p[2])for p in result.packets],
  stopped_guids=[str(v)for v in result.stopped_guids],heights=[asdict(v)for v in result.heights])
def semantic(p):return {name:p[name]for name in('sequence','vectors','new_packets','stopped_guids','heights')}
def selfchecks(cases,world):
 base=state(cases[0],True);checks=[];calls=0
 for capacity,count in((None,0),(0,None),(-1,0),(0,1),(1<<32,0),(4,False)):
  try:replace(base,packet_capacity=capacity,packet_count=count)
  except ValueError:checks.append(dict(case='reject-invalid-header',capacity=capacity,count=count))
  else:raise AssertionError('Invalid or half-unknown metadata accepted')
 for capacity,count in((8192,5000),(4096,4096)):
  result=stop_world_motion135(replace(base,packet_capacity=capacity,packet_count=count),world);calls+=1
  assert result.complete and result.packet_header_known and not result.pending
  assert result.state.packet_count==count+len(result.packets)
  assert result.state.packet_capacity==(capacity if capacity>count else capacity*2)
  checks.append(dict(case='known-header-above-old-fixture-budget-model-only',capacity=capacity,count=count,after_capacity=result.state.packet_capacity,after_count=result.state.packet_count))
 try:stop_world_motion135(replace(base,packet_capacity=0x80000000,packet_count=0x80000000),world);calls+=1
 except UnknownWorldMotionStop135:calls+=1;checks.append(dict(case='unrepresented-growth-refuses-model-only'))
 else:raise AssertionError('Overflowing metadata projection accepted')
 inactive=state(cases[2],False);result=stop_world_motion135(inactive,None);calls+=1
 assert not result.packets and result.state.packet_capacity is None and result.state.packet_count is None
 assert not result.complete and not result.packet_header_known and result.pending
 checks.append(dict(case='inactive-unknown-header-and-world-stay-unresolved-model-only'))
 return checks,calls
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',required=True,type=Path);args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 files,edges=sources();before={name:sha(ROOT/name)for name in files}
 for name,hash_value in before.items():
  path=out/'source-snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes());assert sha(path)==hash_value
 assert sha(HISTORY/'inputs.json')==PINNED['inputs.json']
 assert sha(HISTORY/'source-snapshot/reconstruction/core_spec/world_motion_stop135.py')==OLD_MODEL_SHA
 assert sha(SNAPSHOT)==SNAPSHOT_SHA
 # No historical stdout is opened until the entire new expectation file exists.
 inputs=json.loads((HISTORY/'inputs.json').read_text());assert inputs['snapshot_sha256']==SNAPSHOT_SHA and inputs['world_rc']==WORLD_RC
 memory=SNAPSHOT.read_bytes();world=decode_world_snapshot(memory,WORLD_RC)
 ranges=sorted(set((p,n)for _,p,n in world.source_ranges));h=hashlib.sha256()
 for p,n in ranges:h.update(struct.pack('<2I',p,n));h.update(memory[p:p+n])
 assert h.hexdigest()==inputs['expected_world_digest'] and ranges==[tuple(v)for v in inputs['world_ranges']]
 assert world.primary is None and world.flat_height_bits is None and len(world.tiles)==9
 del memory
 cases=inputs['cases'];predictions=[]
 for case in cases:
  known=projection(stop_world_motion135(state(case,True),world));unknown=projection(stop_world_motion135(state(case,False),world))
  assert known['complete']and known['packet_header_known']and not known['pending']
  assert not unknown['complete']and not unknown['packet_header_known']and unknown['pending']
  assert unknown['packet_capacity']is None and unknown['packet_count']is None
  assert semantic(known)==semantic(unknown)
  predictions.append(dict(id=case['id'],known=known,unknown_header=unknown))
 (out/'fixture-inputs.json').write_bytes((HISTORY/'inputs.json').read_bytes())
 save(out/'expectations.json',predictions);expected_sha=sha(out/'expectations.json')
 checks,check_calls=selfchecks(cases,world);save(out/'model-only-checks.json',checks)
 prepared=dict(new_expectations_before_historical_stdout_read=True,author_blinded_to_historical_results=False,
  expected_sha256=expected_sha,fixture_input_sha256=PINNED['inputs.json'],source_sha256=before,
  original_calls=0,new_original_frames=0,model_comparison_calls=2*len(cases),model_only_calls=check_calls,
  unknown_header_not_filled_from_actual=True)
 save(out/'prepared.json',prepared)
 # Historical captures begin here. They do not supply any model inputs.
 for name,hash_value in PINNED.items():assert sha(HISTORY/name)==hash_value
 actual=[json.loads(line)for line in(HISTORY/'stdout.jsonl').read_text().splitlines()]
 assert len(actual)==len(cases)==56
 counts=Counter();differences=[];rows=[]
 def compare(case_id,mode,field,expected,observed):
  if expected!=observed:differences.append(dict(id=case_id,mode=mode,field=field,expected=expected,actual=observed))
 for case,predicted,observed in zip(cases,predictions,actual,strict=True):
  assert case['id']==predicted['id']==observed['id'];after=observed['after'];raw=bytes.fromhex(after['raw_game2592_hex']);oldraw=bytes.fromhex(observed['before']['raw_game2592_hex'])
  actual_sequence=struct.unpack_from('<I',raw,2412)[0];actual_packets=after['queue']['packets'][len(case['prefix']):]
  assert observed['before']['queue']['packets']==case['prefix'] and after['queue']['packets'][:len(case['prefix'])]==case['prefix']
  assert observed['before']['vectors']=={name:dict(count=case['counts'][name],storage=case['storage'][name])for name in STRIDES}
  for mode in('known','unknown_header'):
   p=predicted[mode]
   for field,value in(('sequence',actual_sequence),('vectors',after['vectors']),('new_packets',actual_packets)):compare(case['id'],mode,field,p[field],value)
   counts[mode+'_cases']+=1;counts[mode+'_full_source_bytes_compared']+=sum(len(bytes.fromhex(v))for entries in after['vectors'].values()for v in entries['storage']);counts[mode+'_new221_packets_compared']+=len(actual_packets)
  known=predicted['known']
  for field,key in(('packet_capacity','capacity'),('packet_count','count')):compare(case['id'],'known',field,known[field],after['queue'][key]);counts['known_header_words_compared']+=1
  wanted=bytearray(oldraw)
  for offset,value in((2412,known['sequence']),(1880,known['packet_capacity']),(1888,known['packet_count'])):struct.pack_into('<I',wanted,offset,value)
  pointer_observed=observed['before']['queue']['capacity']!=after['queue']['capacity']
  if pointer_observed:wanted[1884:1888]=raw[1884:1888]
  compare(case['id'],'known','all_Game2592_except_observed_reallocation_pointer',wanted.hex(),raw.hex())
  counts['known_Game_bytes_compared']+=len(raw);counts['known_reallocation_pointer_words_observed_not_predicted']+=int(pointer_observed)
  assert observed['before']['world']==after['world']==dict(sha256=inputs['expected_world_digest'],bytes=sum(n for _,n in ranges))
  assert observed['full17119']and observed['host_calls']==0 and observed['stack_after']==1048576
  rows.append(dict(id=case['id'],new221=len(actual_packets),known_header_comparison=True,unknown_header_comparison=False,unknown_complete=False,unknown_pending=predicted['unknown_header']['pending']))
 assert expected_sha==sha(out/'expectations.json') and before=={name:sha(ROOT/name)for name in files} and sha(SNAPSHOT)==SNAPSHOT_SHA
 save(out/'case-comparisons.json',rows)
 report=dict(status='historical_projection_comparison_passed'if not differences else'differences',version='0.135.1',build='90898d5e3',
  historical_cases=len(cases),new_original_calls=0,new_original_frames=0,model_comparison_calls=2*len(cases),model_only_calls=check_calls,
  differences=len(differences),difference_rows=differences[:100],counts=dict(counts),
  history=str(HISTORY.relative_to(ROOT)),historical_files=PINNED,historical_model_sha256=OLD_MODEL_SHA,
  source_sha256_before=before,source_sha256_after=before,source_files=len(files),source_import_edges=edges,
  projection_api=dict(packet_header_input='paired explicit unsigned integers or paired None; mixed None rejected',
   known='complete=True within declared projection, pending=(); no allocation pointer prediction',
   unknown='complete=False, pending capacity/count + allocation/copy/panic + complete physical17119 return; header remains None',
   old_4096_limit='removed from core metadata validation; was fixture-only budget'),
  prepared=prepared,world=dict(snapshot_sha256=SNAPSHOT_SHA,world_rc=WORLD_RC,query_source_ranges=len(ranges),query_bytes=sum(n for _,n in ranges),query_sha256=inputs['expected_world_digest'],primary_present=False),
  artifacts={name:sha(out/name)for name in('fixture-inputs.json','expectations.json','prepared.json','model-only-checks.json','case-comparisons.json')},
  limitations=[
   'This is a new model against historical56 original captures, not new original calls or frames; author had access to historical results.',
   'Both expectation modes use only frozen fixture inputs and genuine borrowed after1089 Elwynn world input before replay reads historical actuals.',
   'Unknown-header output is conditional semantic records/sequence/new221 only. It does not prove physical queue allocation/copy/panic behavior or successful complete17119 return.',
   'Capacity/count comparisons and full Game invariant are known-header only; reallocated pointer words are observed, never independently predicted.',
   'Known metadata above4096 and growth refusal are model-only interface checks, with no new original validation of large queues or allocation validity.',
   'Primary23181 world is absent in this historical corpus. No new native runtime, constructor, AI/fatal same-state or full game acceptance.'
  ])
 save(out/'comparison.json',report)
 print(json.dumps(dict(status=report['status'],out=str(out.relative_to(ROOT)),sha256=sha(out/'comparison.json'),differences=len(differences),counts=dict(counts),sources=len(files),edges=len(edges),model_only_checks=len(checks))))
 if differences:raise SystemExit(1)
if __name__=='__main__':main()
