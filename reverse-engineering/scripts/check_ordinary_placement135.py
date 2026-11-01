#!/usr/bin/env python3
"""Full1417/914 flat-world placement differential, no synthetic placements."""
from collections import Counter
from dataclasses import asdict
import argparse,json,os,random,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build,parse_source
from build_upgrade134_oracle import sha,source_memory
FILES=('scripts/check_ordinary_placement135.py','scripts/run_ordinary_placement135_oracle.mjs','scripts/build_full135_oracle.py',
 'scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py')+tuple('reconstruction/core_spec/'+n+'.py'for n in(
 'ordinary_placement135','pickups134','pickup_entity134','death_loot134','spawn_geometry135','spawn_position135_data','spawn135_data',
 'binary32','binary32_sqrt','rng','progression134','spawn135','enemy_scaling','spawn_math135','__init__','upgrade_values'))
IMPORT_HASH={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ordinary_placement135 import project_from_record,clamp_pickup_position
from core_spec.pickups134 import PickupState,append_xp,append_idle_currency,encode_record56
from core_spec.pickup_entity134 import project_kind1_entity
from core_spec.death_loot134 import OrdinaryDefinition,RewardSource,project_ordinary_rewards
from core_spec.spawn135 import SpawnInput,spawn_normal
from core_spec.spawn135_data import ZONES,NORMALS
from core_spec.spawn_position135_data import ZONE_GEOMETRY
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def corpus(pilot=False):
 cases=[];b=f.from_float
 def add(z,xy,kind,group,seed=(1,2,3,4),height=0,moving=False,clock=10,start=9,duration=2,flat=True):
  cx,cy,rad=ZONE_GEOMETRY[z];xyz=(f.add(cx,b(xy[0])),f.add(cy,b(xy[1])),b(7));now=b(clock)
  s=dict(zone=z,now_bits=now,flat_height_bits=b(height),flat_height_enabled=int(flat),counter=11,message_sequence=19,kill_cost_bits=b(2.5),
    rng_words=seed,player_xyz=(cx,cy,0));p=PickupState((),64,11,19,now);rng=seed;kill=b(2.5);movement=False;unit=None
  if kind=='direct':
   s.update(xyz_bits=xyz,pickup_kind=(len(cases)//2)%2,amount=7)
   placement=clamp_pickup_position(z,xyz,b(height),terrain_grid_absent=True,navigation_absent=True)
   if s['pickup_kind']==0:p=append_xp(p,7,placement).state
   else:
    entity=project_kind1_entity(rng,p.spawn_counter);rng=entity.rng_state;p=append_idle_currency(p,7,placement,guid=entity.guid,counter_after=entity.counter2400).state
  else:
   index=next(i for i,d in enumerate(NORMALS[z])if d[-1]==0);row=NORMALS[z][index]
   raw=bytearray.fromhex(spawn_normal(SpawnInput(z,index,now,b(1),0,0,1,0,0,0,(),seed,0,xyz,0,bytes(424).hex())).record_hex)
   struct.pack_into('<Q',raw,112,1);struct.pack_into('<I',raw,288,b(.25));struct.pack_into('<I',raw,292,b(100))
   origin=(f.add(xyz[0],b(-7)),f.add(xyz[1],b(-3)),b(-5))if moving else xyz
   target=(f.add(xyz[0],b(9)),f.add(xyz[1],b(5)),b(11))if moving else xyz
   for j,v in enumerate(origin):struct.pack_into('<I',raw,316+4*j,v)
   for j,v in enumerate(target):struct.pack_into('<I',raw,328+4*j,v)
   struct.pack_into('<I',raw,340,b(start));struct.pack_into('<I',raw,344,b(duration)if moving else 0);s['record_hex']=raw.hex()
   placement=project_from_record(z,now,raw.hex(),b(height),terrain_grid_absent=True,navigation_absent=True);movement=placement.movement_message
   reward=project_ordinary_rewards(OrdinaryDefinition(row[11],row[12],row[14]),rng,source=RewardSource(f.MASK,0,f.MASK,row[1]),accumulator_bits=kill)
   if reward.xp.amount:p=append_xp(p,reward.xp.amount,placement.xp_placement).state
   rng=reward.direct_rng_state;kill=reward.accumulator2412_bits
   if reward.currency.chance_passed:
    entity=project_kind1_entity(rng,p.spawn_counter);rng=entity.rng_state;p=append_idle_currency(p,reward.currency.amount,placement.currency_placement,guid=entity.guid,counter_after=entity.counter2400).state
   unit=dict(marker=1,duration_bits=0,movement_time_bits=now,from_xyz=placement.death_xyz,to_xyz=placement.death_xyz)
  expected=dict(count=len(p.records),pickup_hex=[encode_record56(r,uninitialized_arrival_bits=0xa5a5a5a5).hex()if r.arrival_bits is None else encode_record56(r).hex()for r in p.records],
    counter=p.spawn_counter,message_sequence=(p.message_sequence+int(movement))&f.MASK,rng_words=rng,kill_cost_bits=kill)
  if unit is not None:expected['unit']=unit
  cases.append(dict(id=len(cases),kind=kind,group=group,zone_id=ZONES[z][0],input=s,expected=expected))
 for z in((0,7,11)if pilot else range(12)):
  radius=f.to_float(ZONE_GEOMETRY[z][2])
  for xy in((0,0),(radius-2,0),(radius+10,0),(.8*radius,.8*radius)):
   for kind in('direct','death'):add(z,xy,kind,'zone-center-boundary-outside')
  add(z,(radius,0),'death','moving-boundary',moving=True,height=3,seed=(123456789,362436069,521288629,88675123))
 if not pilot:
  for z in range(12):
   radius=f.to_float(ZONE_GEOMETRY[z][2])
   for height in(-7,13):
    for kind in('direct','death'):add(z,(radius+8,0),kind,'nonzero-base-height-fallback',height=height,flat=False)
   for epsilon in(-.001,0,.001):
    for xy in((radius-2+epsilon,0),(0,-radius+2+epsilon),(.6*(radius-2+epsilon),.8*(radius-2+epsilon))):
     for height in(-20,0,11):add(z,xy,'direct','clamp-threshold-height',height=height,flat=height!=0)
   for clock in(8,9,9.5,10,11,12):
    for duration in(-1,0,2):add(z,(radius-3,radius/5),'death','moving-clock-clamp',moving=True,clock=clock,duration=duration,height=-2)
   for seed in((0,0,0,0),(123456789,362436069,521288629,88675123),(0xffffffff,0x80000000,0x12345678,0xabcdef01)):
    for xy in((-2*radius,0),(radius,radius),(0,0)):add(z,xy,'death','currency-offset-before-clamp',seed=seed,height=4)
  rng=random.Random(0x13514171821)
  for _ in range(120):
   z=rng.randrange(12);rad=f.to_float(ZONE_GEOMETRY[z][2]);add(z,(rng.uniform(-3,3)*rad,rng.uniform(-3,3)*rad),'death','seeded-spatial-mixed',
    seed=tuple(rng.getrandbits(32)for _ in range(4)),height=rng.uniform(-30,30),moving=True,clock=rng.uniform(0,20),start=rng.uniform(0,10),duration=rng.uniform(.1,7))
 return json.loads(json.dumps(cases,allow_nan=False))


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_HASH
 original=SOURCE.read_bytes();assert sha(SOURCE)==SOURCE_SHA;segments=parse_source(original)[4];geometry=[]
 for z,(cx,cy,rad)in enumerate(ZONE_GEOMETRY):
  address=5456016+z*152;raw,off,seg=source_memory(original,segments,address+104,20);assert struct.unpack_from('<2I',raw)==(cx,cy)and struct.unpack_from('<I',raw,16)[0]==rad
  geometry.append(dict(zone=z,address=address+104,file_offset=off,data_segment=seg,raw_hex=raw.hex()))
 cases=corpus(args.phase=='pilot');out,manifest=build(['damage','spawn_pickup']);snap=out/'source-snapshot';snap.mkdir()
 for n,h in before.items():
  target=snap/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
 fixture=out/'ordinary-placement135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
 (out/'ordinary-placement135-geometry.json').write_text(json.dumps(geometry,indent=2)+'\n');results=out/'ordinary-placement135-results.jsonl';stderr=out/'ordinary-placement135-stderr.log';assert sha(RUNTIME)==RUNTIME_SHA
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_ordinary_placement135_oracle.mjs'),str(out),str(fixture)];started=time.monotonic()
 with results.open('w')as stdout,stderr.open('w')as err:
  child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned placement deadline')
 if code:raise RuntimeError(f'Original placement failed: {out}')
 rows=[json.loads(x)for x in results.read_text().splitlines()];assert [r['id']for r in rows]==list(range(len(cases)));failures=[dict(id=c['id'],expected=c['expected'],actual=r['result'])for c,r in zip(cases,rows)if c['expected']!=r['result']]
 (out/'ordinary-placement135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n');after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),kinds=dict(Counter(c['kind']for c in cases)),groups=dict(Counter(c['group']for c in cases)),mismatch_cases=len(failures),
  source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
  artifacts={p.name:sha(p)for p in(fixture,results,stderr,out/'ordinary-placement135-mismatches.json',out/'ordinary-placement135-runtime.json',out/'ordinary-placement135-geometry.json')},
  expected_before_original=True,only_changed_section=7,original_internal_callees_unchanged=True,runtime=json.loads((out/'ordinary-placement135-runtime.json').read_text()),
  process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-started),
  limitations=['Flat/base V116 height, absent terrain/grid/navigation only; real world mesh/height fields remain pending.',
   'Unflagged ordinary death source and empty existing pickup/proc vectors; existing merge/cap logic is reused but not newly validated here.',
   'Placement consumes no RNG; full1417 kind1 and full914 reward/entity RNG are compared through pre-existing independent arithmetic.'])
 (out/'ordinary-placement135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_cases=len(failures),first_failures=failures[:3]),indent=2))
 if failures:raise SystemExit(1)


if __name__=='__main__':main()
