#!/usr/bin/env python3
"""Expected-first complete915 guardedclock/delayed56 differential."""
from collections import Counter
from dataclasses import asdict,replace
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
FILES=('scripts/check_effect_system135.py','scripts/run_effect_system135_oracle.mjs','scripts/source_closure135.py',
 'scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py')+core_sources(ROOT,'effect_system135.py','spawn135_data.py')
IMPORT_HASH={n:sha(ROOT/n)for n in FILES}
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.effect_system135 import EffectSystemState135,PendingEffectSystem135,step_effect_system
from core_spec.spawn135_data import ZONES
from core_spec.spawn_position135_data import ZONE_GEOMETRY


def unit(guid=1,xyz=(0,0,2),origin=None,start=9,duration=0,marker=0,owner=0,reach=2,auras=()):
 raw=bytearray(424);w=lambda o,v:struct.pack_into('<I',raw,o,v&f.MASK)
 w(0,marker);struct.pack_into('<Q',raw,112,guid);w(280,owner);w(308,f.from_float(reach));w(340,f.from_float(start));w(344,f.from_float(duration));w(352,f.from_float(.3))
 for off,coords in((316,origin or xyz),(328,xyz)):
  for j,x in enumerate(coords):w(off+4*j,f.from_float(x))
 for j,x in enumerate(auras):w(168+4*j,x)
 return raw.hex()


def record(tag=255,guid=1,due=10,payload=(0,0,0),spell=1234,tail=0xa5):
 raw=bytearray([tail]*56);struct.pack_into('<Q',raw,0,guid);struct.pack_into('<I',raw,8,f.from_float(due))
 if tag==35:struct.pack_into('<3I',raw,12,*(f.from_float(x)for x in payload))
 if tag==37:struct.pack_into('<I',raw,12,spell)
 raw[49]=tag;return raw.hex()


def state(records=(),units=None,*,zone=0,clock=0,phase=1,mode=0,peer=0,height=0,flat=True,player=None,sequence=17,movement=31):
 cx,cy,_=ZONE_GEOMETRY[zone];player=(cx,cy,f.from_float(5))if player is None else tuple(f.from_float(x)for x in player)
 return EffectSystemState135(f.from_float(10),tuple(records),tuple(records)+((bytes([0x5a])*56).hex(),)*(32-len(records)),(),
  (unit(xyz=(f.to_float(cx)+1,f.to_float(cy)+2,2)),)if units is None else tuple(units),f.from_float(clock),sequence,movement,player,
  (0,0x12345678,0x87654321,0xabcddcba,13,0x76543210),0x123456789abcdef0,phase,mode,peer,zone,f.from_float(height),flat,True,True,True,(1,2,3,4),123)


def projection(s,codes):
 return dict(delayed_records=list(s.delayed_records),delayed_storage=list(s.delayed_storage),
  delayed_storage_sha256=hashlib.sha256(b''.join(bytes.fromhex(x)for x in s.delayed_storage)).hexdigest(),
  units=list(s.units),clock2364_bits=s.clock2364_bits,action_sequence1644=s.action_sequence1644,movement_sequence2412=s.movement_sequence2412,
  player_xyz_bits=list(s.player_xyz_bits),player_action_words=list(s.player_action_words),rng_words=list(s.rng_words),spawn_counter2408=s.spawn_counter2408,
  effect120_count=0,message_opcodes=list(codes))


def expected(s,ops):
 stages=[];codes=[];events=[]
 for op in ops:
  s=replace(s,now_bits=op['now_bits'],**op.get('changes',{}));r=step_effect_system(s,op['dt_bits'])
  assert r.status in('delayed_prefix_projection','trap_invalid255_after_pop');s=r.state;codes.extend(e[1]for e in r.events);events.append(r.events)
  stages.append(dict(projection(s,codes),entry_trap=r.status=='trap_invalid255_after_pop'))
  if r.status=='trap_invalid255_after_pop':break
 return stages,events


def corpus(pilot=False):
 rows=[];b=f.from_float
 def add(group,s,ops=None):
  ops=ops or[dict(now_bits=b(n),dt_bits=b(.1))for n in(9.9,10,10,11,13)]
  e,ev=expected(s,ops);raw=asdict(s);raw['source_id']=str(s.source_id)
  rows.append(dict(id=len(rows),group=group,input=raw,zone_id=ZONES[s.zone][0],ops=ops,expected=e,predicted_events=ev))
 for tag in(35,36,37,255):add('pilot-four-special-tags',state((record(tag,payload=(-9390,-630,3)),),clock=10))
 if pilot:return json.loads(json.dumps(rows,allow_nan=False))
 for clock in(-float('inf'),-1,0,.001,9.999,10,10.001,11,float('inf'),float('nan')):
  for seq in(0,0xffffffff):add('clock-positive-exact-one-shot-wrap',state(clock=clock,sequence=seq))
 for due in(-float('inf'),9.9,10,10.0001,11,float('inf'),float('nan')):
  for tag in(35,36,37,255):add('due-comparison-including-NaN',state((record(tag,due=due,payload=(-9395,-630,4)),)))
 for z in range(12):
  cx,cy,radius=map(f.to_float,ZONE_GEOMETRY[z])
  for flat in(False,True):
   for moving in(False,True):
    units=[unit(xyz=(cx+radius+5,cy+4,7),origin=(cx+radius-3,cy-2,-3)if moving else None,duration=2 if moving else 0)]
    for tag in(35,36):add('all-zones-movement-clamp-and-flat-enabled',state((record(tag,payload=(cx-2,cy+2,11)),),units,zone=z,height=-7 if flat else 13,flat=flat))
 for phase in(0,1,2,3,255):
  for marker in(0,1,2,3):
   for tag in(35,36,37,255):add('phase-marker-lowbit-and255-before-target',state((record(tag,payload=(1,2,3)),),(unit(marker=marker,auras=(1234,1234)),),phase=phase,player=(4,6,1)))
 for mode in(0,1,2):
  for owner in(0,7):
   for peer in(0,7):
    for tag in(35,36,37,255):add('owner-first-GUID-route',state((record(tag,payload=(3,5,7)),),(unit(owner=owner,auras=(1234,)),),mode=mode,peer=peer,player=(1,1,1)))
 for tag in(35,36,37,255):
  for peer in(0,7):add('missing-target-owner-fallback0',state((record(tag,guid=999),),(),mode=1,peer=peer))
 for slot in range(16):
  auras=[500+j for j in range(16)];auras[slot]=1234
  add('aura-first-slot-removal-full424',state((record(37),record(37)),(unit(auras=auras),)))
 for spell in(0,1234,99999):add('aura-zero-existing-duplicates-and-absent',state((record(37,spell=spell),),(unit(auras=(0,1234,1234)),)))
 for marker in(1,3):
  add('duplicate-GUID-owner-and4543-independent-lookup',state((record(37),),(unit(marker=marker,owner=7,auras=(1234,)),unit(marker=0,owner=0,auras=(1234,))),mode=1,peer=7))
 for distance in(0,.0001,5.9999,6,6.0001,100):
  add('forced-duration-15percent-floor-and-cooldownmax',state((record(35,payload=(distance,0,9)),),(unit(xyz=(0,0,2)),),player=(3,4,5),movement=0xffffffff))
 for value in(0x7fc01234,0x7f800000,0xff800000,0x80000000):
  raw=bytearray.fromhex(unit());struct.pack_into('<I',raw,352,value)
  add('cooldown-NaN-Infinity-signedzero-maxnum',state((record(35,payload=(3,4,5)),),(raw.hex(),)))
  add('clock-raw-payload-preservation',replace(state(),clock2364_bits=value))
 for dt in(0x7fc01234,0x7f800000,0xff800000):
  add('dt-unused-with-empty120',state((record(35,payload=(3,4,5)),record(36)),player=(3,4,5)),[dict(now_bits=b(10),dt_bits=dt)])
 for duration in(-1,0,2):
  for start in(8,9,10,11):add('moving-source-ratio-clamp',state((record(35,payload=(4,5,6)),record(36)),(unit(xyz=(5,9,3),origin=(-2,-4,-1),start=start,duration=duration),),player=(2,1,0),flat=False))
 #Sequence tests deliberately mutate route/phase between915 entries; no queue
 #or unmodeled effect state is overwritten to force progress.
 add('retained-owner-unblocks-on-real-peer-change',state((record(255),record(37)),(unit(owner=7,auras=(1234,)),),mode=1,peer=0),
  [dict(now_bits=b(10),dt_bits=b(.1)),dict(now_bits=b(10),dt_bits=b(.1),changes=dict(local_peer2528=7))])
 for count in(2,3,7,24):
  rows56=tuple(record(37,guid=999,tail=17+j)for j in range(count-1))+(record(37,tail=0xef),)
  add('successive-compaction-retains-full-tail',state(rows56,(unit(auras=(1234,)),)))
 add('mixed-special-dispatch-and-movement-order',state((record(37,guid=999),record(35,payload=(3,4,5)),record(37),record(36),record(35,payload=(-5,7,-3))),
  (unit(xyz=(1,2,3),auras=(1234,1234)),),player=(7,8,9),clock=10))
 rng=random.Random(0x13591556)
 for k in range(160):
  z=rng.randrange(12);cx,cy,rad=map(f.to_float,ZONE_GEOMETRY[z]);tag=rng.choice((35,36,37,255));count=rng.randrange(1,5)
  us=tuple(unit(j+1,xyz=(cx+rng.uniform(-rad*1.2,rad*1.2),cy+rng.uniform(-rad,rad),rng.uniform(-5,5)),
   origin=(cx+rng.uniform(-rad,rad),cy+rng.uniform(-rad,rad),rng.uniform(-5,5)),duration=rng.choice((0,2,9)),start=rng.choice((8,9,11)),
   marker=rng.choice((0,0,0,1,2)),owner=rng.choice((0,7)),reach=rng.choice((0,1,2,5)),auras=(1234,1234))for j in range(count))
  records=tuple(record(rng.choice((35,36,37,255)),guid=rng.randrange(1,count+2),due=rng.choice((9.9,10,11)),payload=(cx+rng.uniform(-rad,rad),cy+rng.uniform(-rad,rad),rng.uniform(-5,5)),tail=rng.randrange(256))for _ in range(rng.randrange(1,9)))
  add('seeded-mixed-due-owner-phase-specials',state(records,us,zone=z,clock=rng.choice((0,10,11)),phase=rng.choice((0,1,1,2)),mode=rng.choice((0,1)),peer=rng.choice((0,7)),
   flat=bool(k%2),height=rng.choice((-9,0,13)),player=(cx+3,cy-2,7)))
 return json.loads(json.dumps(rows,allow_nan=False))


def from_input(raw):
 x=dict(raw);x['source_id']=int(x['source_id'])
 for k in('delayed_records','delayed_storage','effect_records120','units','player_xyz_bits','player_action_words','rng_words'):x[k]=tuple(x[k])
 return EffectSystemState135(**x)


def guards():
 s=state((record(0),),(unit(),));results=[]
 result=step_effect_system(s,f.from_float(.1));assert result.status=='pending_910_dispatch'and result.pending_record56==s.delayed_records[0]and not result.state.delayed_records
 results.append(dict(name='ordinary910-explicit-pop-boundary',status=result.status))
 x=replace(s,effect_records120=(bytes(120).hex(),))
 try:step_effect_system(x,f.from_float(.1))
 except PendingEffectSystem135 as e:assert e.state==x;results.append(dict(name='nonempty120-preserved-before-entry',rejected=True))
 else:raise AssertionError('Nonempty120 accepted')
 for flag in('terrain_grid_absent','navigation_absent','collision_grid_absent'):
  x=replace(state((record(36),)),**{flag:False});out=step_effect_system(x,f.from_float(.1));assert out.status=='pending_world_geometry'and out.pending_record56
  results.append(dict(name=flag,status=out.status))
 return results


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_HASH
 cases=corpus(args.phase=='pilot');negative=guards();out,manifest=build(['effect_tick']);snap=out/'source-snapshot';snap.mkdir()
 for n,h in before.items():
  target=snap/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
 fixture=out/'effect-system135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
 guardfile=out/'effect-system135-guards.json';guardfile.write_text(json.dumps(negative,indent=2)+'\n');frozen={p.name:sha(p)for p in(fixture,guardfile,out/'manifest.json',out/manifest['module_file'])}
 result=out/'effect-system135-results.jsonl';stderr=out/'effect-system135-stderr.log';assert sha(RUNTIME)==RUNTIME_SHA
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_effect_system135_oracle.mjs'),str(out),str(fixture)];start=time.monotonic()
 with result.open('w')as stream,stderr.open('w')as err:
  child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned915 deadline')
 if code:raise RuntimeError(f'Original915 failed:{out}')
 rows=[json.loads(x)for x in result.read_text().splitlines()];assert[r['id']for r in rows]==list(range(len(cases)))
 failures=[dict(id=c['id'],group=c['group'],expected=c['expected'],actual=r['stages'])for c,r in zip(cases,rows)if c['expected']!=r['stages']]
 mismatch=out/'effect-system135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n');after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
 assert frozen=={p.name:sha(p)for p in(fixture,guardfile,out/'manifest.json',out/manifest['module_file'])}
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),stages=sum(len(c['expected'])for c in cases),expected_trap_cases=sum(any(s['entry_trap']for s in c['expected'])for c in cases),mismatch_cases=len(failures),guards=len(negative),groups=dict(Counter(c['group']for c in cases)),
  source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),artifacts={p.name:sha(p)for p in(fixture,guardfile,result,stderr,mismatch,out/'effect-system135-runtime.json')},
  expected_before_original=True,source_snapshots=True,only_changed_section=7,runtime=json.loads((out/'effect-system135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),
  limitations=['Full915 with effect120 empty actualfixture snapshot;120 nonempty neverdeleted/zeroed byproduction;ordinary910 due dispatch explicitpartial boundary.',
   'Special35/36 movement finite and flat terrain/collision/navigation absent;clock/dueNaN comparisons explicit and no NaN bit equivalence;255 is an expected actualunreachable afterpop, counted separately.',
   'Complete56B queue/backing and424B units/player action state strict;physical payload bytes retained in originalsidecar but onlyopcode order compared, wire encoding remainspending.',
   'Controlled state fixtures prove consumers;actual8seed producer/three-domain observation is a separate root run.'])
 (out/'effect-system135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_cases=len(failures),first_ids=[x['id']for x in failures[:12]])))
 if failures:raise SystemExit(1)


if __name__=='__main__':main()
