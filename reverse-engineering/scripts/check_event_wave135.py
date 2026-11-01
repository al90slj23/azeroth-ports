#!/usr/bin/env python3
"""Expected-first complete original947 G2424 event-wave component check."""
from pathlib import Path
from dataclasses import asdict,replace
from collections import Counter
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'reconstruction'))
from build_full135_oracle import SOURCE,SOURCE_SHA
from build_event_wave135_oracle import build_event_wave135
from trace_event_wave135 import trace_event_wave135
from production_closure135 import production_sources135
from ai_world135_inputs import load_asset_world135,asset_world_description135,HASHES,ASSET_WORLD
from core_spec import binary32 as f
from core_spec.event_wave135 import EventWaveInput135,EventWaveLocale135,step_event_wave135,PendingEventWave135,MESSAGES135
from core_spec.spawn135_data import NORMALS
from prepare_event_wave135_prefix import prepare_default_event_prefix135
from core_spec.opening135 import EmptyOpeningInput135
from core_spec.opening_handoff135 import initialize_absent_companion_handoff
from core_spec.profile_companions135 import EmptyCompanionProfile135
from core_spec.opening_npc_pickups135 import OpeningVector135,npc_create_fields
from core_spec.spawn_frame_motion135 import step_ordinary_frame
from core_spec.spawn_schedule135 import FrameInput
from core_spec.spawn135 import definition
from core_spec.spawn_heading135 import atan2_bits
from core_spec.opening_entities135 import BASE_SPEEDS,unit_create169
from core_spec.record_cells135 import cells135,u32
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory';SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
def sha(p):
 with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def physical(v):return dict(capacity=v.capacity,count=v.count,storage=v.storage)
def corpus(full):
 world=load_asset_world135();description=asset_world_description135();cases=[];wanted=[];labels=[];locale=EventWaveLocale135(0,tuple((b'enemy.'+str(row[3]).encode(),row[2].encode())for row in NORMALS[0]),tuple((message,message)for message in MESSAGES135))
 for seed in range(12 if full else 1):
  handoff=initialize_absent_companion_handoff(EmptyOpeningInput135(1,1,0,seed,42),world,companion_profile=EmptyCompanionProfile135(()),title_utf8=b'Elwynn Forest',subtitle_utf8=b'')
  for moving in(range(2)if full else(0,)):
   o=handoff.opening;initial=handoff.initial;now=f.from_float(60.1);velocity=(f.from_float(5),f.from_float(2))if moving else(0,0)
   frame=FrameInput(0,now,f.from_float(.1),0,0,0,0,0,0x3f800000,0,0,None,initial.player_xyz,initial.player_xyz,velocity,world.fallback_height_bits,o.initial.level.rng_words,initial.spawn_counter,tuple(o.units.storage[:o.units.count]),True)
   ordinary=step_ordinary_frame(frame,destination_slots=o.units.storage,world=world,distance_map=None,allow_unknown_storage_growth=True);assert ordinary.status=='ordinary_projection'
   rows=list(o.units.storage)
   while len(rows)<len(ordinary.unit_records):rows.extend([(None,)*424]*(max(4,len(rows)*2)-len(rows)))
   for j,row in enumerate(ordinary.unit_records):rows[j]=tuple(cells135(row,424))
   vector=OpeningVector135(424,tuple(rows),len(ordinary.unit_records))
   value=EventWaveInput135(0,now,f.from_float(60),255,initial.player_xyz,ordinary.velocity_xy,ordinary.rng_words,ordinary.counter,initial.message_sequence,vector,initial.source_id,initial.level.progression.level,0x3f800000)
   result=step_event_wave135(value,world,locale=locale);packets=[]
   for request,row in zip(ordinary.requests,ordinary.unit_records[o.units.count:]):
    desc=definition(0,request['index']);xyz=tuple(request['position_bits']);heading=atan2_bits(f.sub(frame.player_xyz[1],xyz[1]),f.sub(frame.player_xyz[0],xyz[0]));fields=npc_create_fields(request['guid'],desc['entry'],desc['display'],desc['scale_bits'],u32(row,288),desc['elite'],initial.source_id,initial.level.progression.level);packets.append(dict(opcode=169,payload_hex=unit_create169(request['guid'],xyz,heading,BASE_SPEEDS,fields).hex()))
   packets.extend(dict(opcode=op,payload_hex=payload)for op,payload in result.packets)
   scalars=dict(initial.initial_scalar_words);scalars[2440]=scalars[2444]=scalars[2448]=f.from_float(1000)
   raw=asdict(value);raw['rng_words']=list(frame.rng_words);raw['counter']=frame.counter;raw['pickups']=dict(count=o.pickups.count,storage=o.pickups.storage);raw.pop('units');raw['velocity_xy']=list(frame.velocity_xy)
   case=dict(id=len(cases),input=raw,frame=asdict(frame),units=dict(count=o.units.count,storage=o.units.storage),world=description,message_sequence=initial.message_sequence,initial_scalars=tuple(scalars.items()),level=initial.level.progression.level,player_guid=str(initial.source_id),locale=dict(language_index=locale.language_index,enemy_names=[(k.decode(),v.decode())for k,v in locale.enemy_names],messages=[(k.decode(),v.decode())for k,v in locale.messages]),distance_map=None,unknown_poison=0xa5 if moving==0 else 0x5a)
   expected=dict(id=case['id'],result=dict(pickups=physical(o.pickups),units=physical(result.units),rng_words=result.rng_words,counter=result.counter,message_sequence=result.message_sequence,packets=packets,notifications_count=0,next_event2424_bits=result.next_event2424_bits,last_event2586=result.last_event2586,budget_bits=ordinary.budget_bits,kill_cost_bits=ordinary.kill_cost_bits,velocity_xy=ordinary.velocity_xy,previous_player_xyz=frame.player_xyz,other_clocks={str(i):scalars[i]for i in(2440,2444,2448,2456,2460)}))
   cases.append(case);wanted.append(expected);labels.append(dict(id=case['id'],seed=seed,moving=moving,status=result.status,event=result.event,definition_index=result.definition_index,requested=result.requested,successful=len(result.creates),ordinary_requests=ordinary.requests,ordinary_draws=ordinary.draws,wave_draws=result.draws,charged_guids=result.charged_guids,initial2586_producer='1560 scratch2674=255;Game copy scratch88',natural_elapsed_frames=0))
 if full:
  prior,pre,frame,ordinary,selections=prepare_default_event_prefix135(world);initial=pre.opening_handoff.initial;o=pre.opening_handoff.opening
  rows=list(pre.unit_storage)
  while len(rows)<len(ordinary.unit_records):rows.extend([(None,)*424]*(max(4,len(rows)*2)-len(rows)))
  for j,row in enumerate(ordinary.unit_records):rows[j]=tuple(cells135(row,424))
  vector=OpeningVector135(424,tuple(rows),len(ordinary.unit_records));scalars=dict(pre.initial_scalars);scalars[2444]=pre.next_resource2444_bits;original2448=scalars[2448];scalars[2448]=f.from_float(1000);level=pre.collection.level;death=pre.collection.death
  value=EventWaveInput135(pre.zone,frame.now_bits,scalars[2424],255,pre.collection.player_xyz,ordinary.velocity_xy,ordinary.rng_words,ordinary.counter,death.message_sequence,vector,pre.source_id,level.progression.level,scalars[2516],distance_map=pre.distance_map)
  result=step_event_wave135(value,world,locale=locale);packets=[]
  for request,row in zip(ordinary.requests,ordinary.unit_records[len(pre.records):]):
   desc=definition(pre.zone,request['index']);xyz=tuple(request['position_bits']);heading=atan2_bits(f.sub(frame.player_xyz[1],xyz[1]),f.sub(frame.player_xyz[0],xyz[0]));fields=npc_create_fields(request['guid'],desc['entry'],desc['display'],desc['scale_bits'],u32(row,288),desc['elite'],pre.source_id,level.progression.level);packets.append(dict(opcode=169,payload_hex=unit_create169(request['guid'],xyz,heading,BASE_SPEEDS,fields).hex()))
  packets.extend(dict(opcode=op,payload_hex=payload)for op,payload in result.packets);pickups=OpeningVector135(56,tuple(tuple(cells135(row,56))for row in pre.pickup_storage56),pre.pickup_active_count)
  raw=asdict(value);raw.pop('units');raw.pop('distance_map');raw['rng_words']=list(frame.rng_words);raw['counter']=frame.counter;raw['velocity_xy']=list(frame.velocity_xy);raw['pickups']=dict(count=pickups.count,storage=pickups.storage)
  guardians=[dict(unit_index=x.unit_index,guid=str(x.guid),capacity=x.capacity,timers_bits=list(x.timers_bits),ability_pointer=x.ability_pointer,header_pointer=x.header_pointer,ability_records44_hex=list(x.ability_records44_hex),header28_hex=x.header28_hex)for x in pre.guardian_cooldowns]
  case=dict(id=len(cases),guardians=guardians,input=raw,frame=asdict(frame),units=dict(count=len(pre.records),storage=tuple(tuple(cells135(row,424))for row in pre.unit_storage)),world=description,message_sequence=death.message_sequence,initial_scalars=tuple(scalars.items()),level=level.progression.level,player_guid=str(pre.source_id),locale=dict(language_index=locale.language_index,enemy_names=[(k.decode(),v.decode())for k,v in locale.enemy_names],messages=[(k.decode(),v.decode())for k,v in locale.messages]),distance_map=asdict(pre.distance_map),unknown_poison=0x5a)
  expected=dict(id=case['id'],result=dict(pickups=physical(pickups),units=physical(result.units),rng_words=result.rng_words,counter=result.counter,message_sequence=result.message_sequence,packets=packets,notifications_count=0,next_event2424_bits=result.next_event2424_bits,last_event2586=result.last_event2586,budget_bits=ordinary.budget_bits,kill_cost_bits=ordinary.kill_cost_bits,velocity_xy=ordinary.velocity_xy,previous_player_xyz=frame.player_xyz,other_clocks={str(i):scalars[i]for i in(2440,2444,2448,2456,2460)}))
  expected['result']['guardian_cooldowns']=guardians
  cases.append(case);wanted.append(expected);labels.append(dict(id=case['id'],kind='actual_independent600_next_frame_prefix',natural_elapsed_frames=600,original_elapsed_frames=0,prior_now_bits=prior.collection.level.stats.now_bits,now_bits=frame.now_bits,selections=selections,pre_ordinary_rng_words=frame.rng_words,post_ordinary_rng_words=ordinary.rng_words,ordinary_draws=ordinary.draws,ordinary_requests=ordinary.requests,status=result.status,event=result.event,definition_index=result.definition_index,requested=result.requested,successful=len(result.creates),wave_draws=result.draws,charged_guids=result.charged_guids,full601_original_validated=False,original_next2448_bits=original2448,isolated_next2448_bits=scalars[2448],later_kind2_replenishment_explicitly_isolated=True))
 for case,want in zip(cases,wanted):case.setdefault('guardians',[]);want['result'].setdefault('guardian_cooldowns',[])
 return cases,wanted,labels

def compare(wants,observed):
 errors=[];counts=Counter()
 def walk(a,b,path=()):
  if a is None:
   assert len(path)>=4 and path[-4]in('units','pickups')and path[-3]=='storage'and type(b)is int and 0<=b<=255;counts['explicit_unknown_cells']+=1;return
  if isinstance(a,dict):
   if set(a)!=set(b):errors.append(dict(path=path,keys_expected=list(a),keys_actual=list(b)));return
   for k,v in a.items():walk(v,b[k],path+(k,))
  elif isinstance(a,(list,tuple)):
   if len(a)!=len(b):errors.append(dict(path=path,len_expected=len(a),len_actual=len(b)));return
   for i,(x,y)in enumerate(zip(a,b)):walk(x,y,path+(i,))
  elif a!=b:
   if len(errors)<100:errors.append(dict(path=path,expected=a,actual=b))
   counts['differences']+=1
  else:counts['equal_known_values']+=1
 for want,raw in zip(wants,observed):
  for name in('units','pickups'):raw['result'][name]['storage']=[list(bytes.fromhex(row))for row in raw['result'][name]['storage']]
  walk(want,dict(id=raw['id'],result=raw['result']))
  counts['packets']+=len(raw['result']['packets']);counts['packet_bytes']+=sum(len(bytes.fromhex(p['payload_hex']))for p in raw['result']['packets'])
 return errors,dict(counts)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();scripts=('check_event_wave135.py','build_event_wave135_oracle.py','run_event_wave135_oracle.mjs','trace_event_wave135.py','production_closure135.py','ai_world135_inputs.py','ai_world135_packing.mjs','build_full135_oracle.py','build_upgrade134_oracle.py','prepare_event_wave135_prefix.py');files=tuple('scripts/'+n for n in scripts)+production_sources135(ROOT,'core_spec.event_wave135','core_spec.headless135','core_spec.opening_handoff135','core_spec.spawn_frame_motion135','resource_spec.world_query135');before={p:sha(ROOT/p)for p in files};cases,wanted,labels=corpus(args.phase=='full');assert before=={p:sha(ROOT/p)for p in files};out,manifest=build_event_wave135();trace_event_wave135(out)
 for name,digest in before.items():
  target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes());assert sha(target)==digest
 for name,value in(('event-input.json',cases),('event-expected.json',wanted),('event-labels.json',labels)):save(out/name,value)
 frozen={name:sha(out/name)for name in('event-input.json','event-expected.json','event-labels.json','manifest.json',manifest['module_file'],'event-wave135-static.json')};assert (out/'event-input.json').stat().st_size<4194304 and sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA
 command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_event_wave135_oracle.mjs'),str(out),str(out/'event-input.json')];save(out/'event-prepared.json',dict(source_sha256=before,artifacts=frozen,command=command,expected_before_original=True,deadline_seconds=60,context_snapshot_sha256=SNAPSHOT_SHA,typed_Game_and_query_world=True))
 began=time.monotonic();error=None
 with(out/'event-results.jsonl').open('wb')as stdout,(out/'event-stderr.log').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'));save(out/'event-owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
  try:child.wait(timeout=60)
  except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as e:error=str(e)
  finally:
   try:os.killpg(child.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:child.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 def missing(group=False):
  try:(os.killpg if group else os.kill)(child.pid,0)
  except ProcessLookupError:return True
  return False
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,launcher_error=error);save(out/'event-process-terminal.json',terminal);errors=[];counts={};runtime=None
 if child.returncode==0:
  observed=[json.loads(x)for x in(out/'event-results.jsonl').read_text().splitlines()];assert len(observed)==len(wanted);game_guard=[]
  allowed=((1720,24),(1784,12),(1880,12),(2408,4),(2416,12),(2428,12),(2586,1))
  for row in observed:
   a=bytes.fromhex(row['game_before2592_hex']);b=bytes.fromhex(row['game_after2592_hex']);unexpected=[i for i,(x,y)in enumerate(zip(a,b))if x!=y and not any(start<=i<start+n for start,n in allowed)];assert not unexpected,(row['id'],unexpected);game_guard.append(row['id'])
  errors,counts=compare(wanted,observed);runtime=json.loads((out/'event-wave135-runtime.json').read_text())
 after={p:sha(ROOT/p)for p in files};assert all(sha(out/name)==digest for name,digest in frozen.items())and all(sha(ASSET_WORLD/n)==digest for n,digest in HASHES.items());save(out/'event-differences.json',errors);report=dict(version='0.135.1',actual_build='90898d5e3',original_sha256=SOURCE_SHA,cases=len(cases),differences=len(errors),comparison=counts,events=dict(Counter(str(x['event'])for x in labels)),source_sha256_before=before,source_sha256_after=after,source_files=len(files),frozen_artifacts=frozen,all_artifacts_and_world_inputs_unchanged=True,game_unchanged_outside_declared_byte_write_mask=True,world_inputs={str(ASSET_WORLD/n):h for n,h in HASHES.items()},context_snapshot_sha256=SNAPSHOT_SHA,process=terminal,runtime=runtime,expected_before_original=True,full880_frames=0,natural60_second_runs=0,component_scope='Independent opening typed single full947 at explicit60.1s; ordinary once thenG2424; otherdue branches declaredfuture; initializedsnapshot locale; actualqueryworld manuallypacked');save(out/'event-wave135-comparison.json',report);print(json.dumps(dict(directory=str(out),cases=len(cases),differences=len(errors),first_errors=errors[:8],process=terminal,receipt_sha256=sha(out/'event-wave135-comparison.json'))),flush=True)
 if errors or child.returncode or error or before!=after or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)
if __name__=='__main__':main()
