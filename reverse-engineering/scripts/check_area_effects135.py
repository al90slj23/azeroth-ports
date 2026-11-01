#!/usr/bin/env python3
"""Independent expected-first complete922/3757 area differential."""
from collections import Counter
from dataclasses import asdict, replace
import argparse, json, os, random, signal, struct, subprocess, sys, time
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha

NAMES=('__init__','ability_state','area_effects135','binary32','binary32_sqrt','candidates135','cast135','cast_events135',
 'combat134','combat135','currency134','death_loot134','death_pickup135','derived_stats134','derived_stats135',
 'level_cycle135','ordinary_placement135','pickup_entity134','pickups134','progression','progression134','radius','rng',
 'spawn135_data','spawn_geometry135','spawn_position135_data','unit_records135','upgrade_values')
FILES=tuple('reconstruction/core_spec/'+n+'.py'for n in NAMES)+(
 'scripts/check_area_effects135.py','scripts/run_area_effects135_oracle.mjs',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/full135_host.mjs',
 'reports/2026-11-01-catalogue0135.json')
IMPORT_HASH={n:sha(ROOT/n)for n in FILES}
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.combat135 import CombatState
from core_spec.cast135 import CastState
from core_spec.unit_records135 import decode_spatial,patch_units,FLOAT_FIELDS
from core_spec.area_effects135 import AREAS,AreaDefinition135,AreaState135,produce_area,tick_areas
from core_spec.death_pickup135 import DeathContext135,OrdinaryDeathBinding135,consume_ordinary_death
from core_spec.death_loot134 import OrdinaryDefinition
from core_spec.ordinary_placement135 import project_from_record
from core_spec.pickups134 import encode_record56
from core_spec.spawn135_data import ZONES,NORMALS
from core_spec.spawn_position135_data import ZONE_GEOMETRY

UNIT_OFFSETS=tuple(sorted({0,4,40,64,120,124,144,148,152,156,160,164,240,244,288,292,316,320,324,328,332,336,340,344,356,368,372,380,388,408,412,416}))


def definitions():
 rows={r['identifier']:r for r in json.loads((ROOT/'reports/2026-11-01-catalogue0135.json').read_text())['abilities']}
 return {aid:AreaDefinition135(pointer,aid,rows[aid.decode()]['record_raw_hex'])for aid,(pointer,tag,spell)in AREAS.items()}


def unit(guid,x,y=0,*,marker=0,start=None,duration=0,time=0):
 raw=bytearray(424);w=lambda o,v:struct.pack_into('<I',raw,o,v&f.MASK)
 w(0,marker)
 for o in(40,64,244):w(o,f.MASK)
 struct.pack_into('<Q',raw,112,guid);w(284,5415572);w(288,f.from_float(1000000));w(292,f.from_float(1000000))
 for off,xyz in((316,start or(x,y,0)),(328,(x,y,0))):
  for j,v in enumerate(xyz):w(off+4*j,f.from_float(v))
 w(340,f.from_float(time));w(344,f.from_float(duration));return bytes(raw).hex()


def input_state(records,*,now=10,player=(0,0),seed=(1,2,3,4),crit=.3,critmult=2,damage=1,area=1,height=0,counter=0,context=0,busy=0):
 return dict(unit_hex=list(records),now_bits=f.from_float(now),player_xy=[f.from_float(x)for x in player],rng_words=list(seed),
  critical_chance_bits=f.from_float(crit),critical_multiplier_bits=f.from_float(critmult),damage_multiplier_bits=f.from_float(damage),
  area_multiplier_bits=f.from_float(area),max_hp_bits=f.from_float(500),current_hp_bits=f.from_float(500),height_bits=f.from_float(height),counter=counter,
  source_id='999',context908=context,busy488=busy)


def state_from_input(s):
 spatial=tuple(decode_spatial(bytes.fromhex(h))for h in s['unit_hex'])
 return CastState(CombatState(tuple(u.unit for u in spatial),now_bits=s['now_bits']),spatial,tuple(s['player_xy']),tuple(s['rng_words']),
  s['damage_multiplier_bits'],s['max_hp_bits'],s['critical_chance_bits'],s['critical_multiplier_bits'],s['area_multiplier_bits'],0x3f800000,0,int(s['source_id']),0,s['context908'],())


def projection(cast,areas,records,ledgers,death=None):
 result=dict(area_records=list(areas.records),counter=areas.spawn_counter,
  unit_words=[[struct.unpack_from('<I',raw,o)[0]for o in UNIT_OFFSETS]for raw in records],
  rng_words=list(cast.rng_words),accounted_total_hex=struct.pack('>d',cast.combat.accounted_total).hex(),
  player_hp_bits=f.from_float(500),attempted_spell_sets=[list(x)for x in ledgers])
 if death is not None:result.update(pickup_hex=[encode_record56(r,uninitialized_arrival_bits=0xa5a5a5a5).hex()if r.arrival_bits is None else encode_record56(r).hex()for r in death.records],message_sequence=death.message_sequence,kill_cost_bits=death.kill_cost_bits)
 return result


def expected_case(s,ops,initial_areas=()):
 cast=state_from_input(s);areas=AreaState135(tuple(initial_areas),s['counter']);ledgers=((),(),());records=tuple(bytes.fromhex(x)for x in s['unit_hex']);stages=[]
 death=DeathContext135((),128,s['counter'],19,f.from_float(2.5))if'death_zone'in s else None
 dead_xyz={}
 for op in ops:
  cast=replace(cast,combat=replace(cast.combat,now_bits=op['now_bits']))
  if op.get('cast_changes'):cast=replace(cast,**op['cast_changes'])
  if op['kind']=='cast':
   d=AreaDefinition135(op['definition']['pointer'],op['definition']['ability_id'].encode(),op['definition']['raw88_hex'])
   result=produce_area(cast,areas,d,AbilityRecord.from_bytes(bytes.fromhex(op['owned_hex'])),s['height_bits'],append_slot_hex=op['slot_hex'],
    terrain_grid_absent=True,navigation_absent=True,busy488=s['busy488'],attempted_spell_sets=ledgers,area_modifiers_absent=True)
   cast,areas,ledgers=result.cast,result.areas,result.attempted_spell_sets;success=result.success
   if death is not None:death=replace(death,spawn_counter=areas.spawn_counter)
  else:
   # All positive fixtures are nonlethal and player's HP already equals max;
   # explicit accepted-hit consumer models the clamped self-heal empty-source domain.
   def after_hit(state,damage):
    if damage.dead and death is None:raise AssertionError('Nonlethal fixture escaped its declared domain')
    return state
   def after_death(state,damage):
    nonlocal death
    z=s['death_zone'];index=next(j for j,u in enumerate(state.combat.units)if u.target_id==damage.target.target_id)
    raw=records[index];pointer=struct.unpack_from('<I',raw,284)[0];row=next(n for n in NORMALS[z]if n[1]==pointer)
    p=project_from_record(z,op['now_bits'],raw.hex(),s['height_bits'],terrain_grid_absent=True,navigation_absent=True)
    binding=OrdinaryDeathBinding135(OrdinaryDefinition(row[11],row[12],row[14]),pointer,p.xp_placement,p.currency_placement,p.death_xyz,p.movement_message)
    r=consume_ordinary_death(state,damage,death,binding);death=r.context;dead_xyz[damage.target.target_id]=p.death_xyz
    return r.cast
   result=tick_areas(cast,areas,op['now_bits'],after_hit=after_hit,after_death=after_death if death is not None else None,area_modifiers_absent=True)
   cast,areas=result.cast,result.areas;success=None
   if death is not None:areas=replace(areas,spawn_counter=death.spawn_counter)
   records=patch_units(records,cast.combat.units)
   mutable=[bytearray(x)for x in records]
   for guid,offset,bits in result.effect_writes:
    index=next(j for j,u in enumerate(cast.combat.units)if u.target_id==guid)
    struct.pack_into('<I',mutable[index],offset,bits)
   for index,u in enumerate(cast.combat.units):
    if u.target_id in dead_xyz:
     for off in(316,328):struct.pack_into('<3I',mutable[index],off,*dead_xyz[u.target_id])
   records=tuple(bytes(x)for x in mutable)
  stages.append(dict(success=success,snapshot=projection(cast,areas,records,ledgers,death)))
 return stages


def corpus(pilot=False,death_only=False):
 rows=[];defs=definitions();b=f.from_float
 def add(group,aid,s=None,owned=None,ticks=None,initial_areas=(),casts=1):
  d=defs[aid];s=input_state([unit(1,1),unit(2,3),unit(3,12)])if s is None else s;a=owned or AbilityRecord(d.pointer)
  dd=asdict(d);dd['ability_id']=aid.decode();ops=[]
  for j in range(casts):ops.append(dict(kind='cast',now_bits=s['now_bits'],definition=dd,owned_hex=a.to_bytes().hex(),slot_hex=(bytes([0xa5 if j%2==0 else 0x5a])*88).hex()))
  for now in ([10.249,10.25,10.25,11,13,16,20]if ticks is None else ticks):ops.append(dict(kind='tick',now_bits=b(now)))
  rows.append(dict(id=len(rows),group=group,input=s,initial_areas=list(initial_areas),ops=ops,expected=expected_case(s,ops,initial_areas)))
 if death_only:
  for z in range(12):
   cx,cy,rad=ZONE_GEOMETRY[z];x,y=f.to_float(cx),f.to_float(cy);normal=next(r for r in NORMALS[z]if r[-1]==0)
   for aid in defs:
    for moving in(False,True):
     us=[]
     for j in range(3):
      raw=bytearray.fromhex(unit(j+1,x+j*.7,y+j*.3,start=(x-1,y-.5,-1)if moving else None,duration=2 if moving else 0,time=9))
      struct.pack_into('<I',raw,284,normal[1]);struct.pack_into('<I',raw,288,b(.1));struct.pack_into('<I',raw,292,b(100));us.append(raw.hex())
     s=input_state(us,player=(x,y),seed=(1,2,3,4)if not moving else(123456789,362436069,521288629,88675123),counter=0xffffffff if z%3==0 else 11,height=3 if moving else 0)
     s['death_zone']=z;s['zone_id']=ZONES[z][0]
     add('ordinary-area-death-shared-counter-RNG-placement',aid,s,ticks=[10.25,10.25,11,20],casts=2)
  return json.loads(json.dumps(rows,allow_nan=False))
 for aid in defs:add('all-seven-real-definitions',aid)
 if pilot:return rows
 for aid,d in defs.items():
  for n in(0,1,2,7,24,25,40):
   s=input_state([unit(j+1,(j%6)*4-10,(j//6)*3-8,marker=int(j%11==0))for j in range(n)])
   add('query-size-dead-and-density',aid,s)
  for dur in(-1,0,.01,.1,.5,1,2,7):
   add('duration-round-tick-count-and-expiration',aid,owned=replace(AbilityRecord(d.pointer),duration_bits=b(dur),additional_duration_bits=b(.7)))
  for area in(0,.01,.5,1,3,10,100):
   add('radius-compression-and-zero',aid,input_state([unit(j+1,j*9-15,j%3)for j in range(8)],area=area),replace(AbilityRecord(d.pointer),area_bits=b(1.7),additional_area_bits=b(.8)))
  for count in(2,3):add('overlapping-area-order-same-time',aid,casts=count)
  for counter in(0xffffff,0xffffffff):add('full32-counter-wrap-guid',aid,input_state([unit(1,1)],counter=counter))
  for context,busy in((1,0),(2,0),(3,0),(0,1)):add('three-attempt-ledger-gates',aid,input_state([unit(1,1)],context=context,busy=busy))
  for height in(-12,3.5):add('explicit-flat-height',aid,input_state([unit(1,1)],height=height))
 for aid in(b'flamestrike',b'blizzard'):
  for reverse in(False,True):
   # Equal density and distance tie; later candidate wins. A unit beyond cast
   # range still contributes density around the candidate inside range.
   points=[unit(1,-10),unit(2,10),unit(3,35),unit(4,29)]
   add('later-density-ties-and-beyond-range-neighbours',aid,input_state(points[::-1]if reverse else points))
  points=[unit(j+1,j+1)for j in range(24)]+[unit(30,29)]+[unit(31+j,31+j*.01)for j in range(7)]
  add('only-first24-candidate-cap',aid,input_state(points))
 rng=random.Random(0x1353757922)
 for k in range(280):
  aid=rng.choice(tuple(defs));d=defs[aid];n=rng.randrange(1,36)
  us=[unit(j+1,rng.uniform(-40,40),rng.uniform(-40,40),marker=int(rng.randrange(13)==0),
   start=(rng.uniform(-40,40),rng.uniform(-40,40),rng.uniform(-3,3)),duration=rng.choice((0,2,9)),time=rng.choice((0,8,12)))for j in range(n)]
  s=input_state(us,seed=tuple(rng.getrandbits(32)for _ in range(4)),crit=rng.choice((0,.3,1)),critmult=rng.choice((1,1.7,3)),damage=rng.choice((0,.2,1,3)),area=rng.choice((.1,1,3)),height=rng.choice((0,-7,2.5)))
  a=replace(AbilityRecord(d.pointer),damage_bits=b(rng.uniform(.2,4)),additional_damage_bits=b(rng.uniform(.5,2)),
   duration_bits=b(rng.choice((.1,.5,1,2,5))),additional_duration_bits=b(rng.choice((.3,1,1.7))),
   area_bits=b(rng.choice((.5,1,2))),additional_area_bits=b(rng.choice((.7,1,2))),life_damage_bits=b(rng.choice((0,.01,.1))))
  add('random-moving-density-RNG-and-upgrades',aid,s,a,casts=1+k%3)
 # Explicit temporal paths: no target due tick still decrements, repeated same
 # clock drains only one tick per call, expiry wins over due tick.
 for aid in(b'flamestrike',b'blizzard'):
  add('single-tick-no-catchup-repeated-same-time',aid,ticks=[15,15,15,15,15,15,15,15,19])
  add('moving-target-leaves-before-first-tick',aid,input_state([unit(1,200,start=(1,0,0),duration=1,time=10)]),ticks=[10.25,11,11,20])
 d=defs[b'flamestrike'];s=input_state([unit(1,1),unit(2,4)])
 row=produce_area(state_from_input(s),AreaState135(),d,AbilityRecord(d.pointer),0,append_slot_hex=(b'\xa5'*88).hex(),terrain_grid_absent=True,navigation_absent=True,area_modifiers_absent=True).areas.records[0]
 def changed(**kw):
  raw=bytearray.fromhex(row)
  for off,value in kw.items():struct.pack_into('<I',raw,int(off),value)
  return raw.hex()
 for interval in(0,-.5,2):
  records=(changed(**{'80':b(10.25)}),changed(**{'80':b(10.249)}),changed(**{'68':b(interval),'80':b(30)}),changed(**{'72':0,'80':b(15)}))
  add('expiry-equals-due-compaction-and-empty-remaining',b'flamestrike',s,ticks=[10.249,10.25,10.25,15,30],initial_areas=records,casts=0)
 add('stored-damage-current-critical-profile',b'flamestrike',s,ticks=[10.25,11,13,14,20])
 c=rows[-1]
 for j,op in enumerate(c['ops'][1:]):op['cast_changes']=dict(damage_multiplier_bits=b(100+j),critical_chance_bits=b(1 if j%2 else 0),critical_multiplier_bits=b(3 if j%2 else 1),area_multiplier_bits=b(100))
 c['expected']=expected_case(c['input'],c['ops'])
 return json.loads(json.dumps(rows,allow_nan=False))


def guard_cases():
 d=definitions()[b'flamestrike'];s=input_state([unit(1,1)]);cast=state_from_input(s);a=AbilityRecord(d.pointer)
 opts=dict(append_slot_hex=bytes(88).hex(),terrain_grid_absent=True,navigation_absent=True,area_modifiers_absent=True)
 def prod(**kw):
  args=dict(opts);args.update(kw);return produce_area(cast,AreaState135(),d,a,0,**args)
 row=prod().areas.records[0]
 bad=bytearray.fromhex(row);struct.pack_into('<Q',bad,0,1)
 badspell=bytearray.fromhex(row);struct.pack_into('<I',badspell,60,999999)
 tests=[('missing-area-sources',lambda:prod(area_modifiers_absent=False)),('real-terrain',lambda:prod(terrain_grid_absent=False)),
  ('real-navigation',lambda:prod(navigation_absent=False)),('short-slot',lambda:prod(append_slot_hex='00')),
  ('unknown-area-variant',lambda:AreaState135((bad.hex(),))),('unknown-spell',lambda:AreaState135((badspell.hex(),))),
  ('unknown-tick-sources',lambda:tick_areas(cast,AreaState135((row,)),f.from_float(10.25))),
  ('missing-accepted-hit-consumer',lambda:tick_areas(cast,AreaState135((row,)),f.from_float(10.25),area_modifiers_absent=True)),
  ('wrong-owned-pointer',lambda:produce_area(cast,AreaState135(),d,AbilityRecord(5467428),0,**opts)),
  ('nonfinite-owned-duration',lambda:produce_area(cast,AreaState135(),d,replace(a,duration_bits=f.INF),0,**opts)),
  ('nonfinite-height',lambda:produce_area(cast,AreaState135(),d,a,f.NAN,**opts)),
  ('missing-gated-ledgers',lambda:produce_area(replace(cast,context908=1),AreaState135(),d,a,0,**opts)),
  ('duplicate-GUID',lambda:produce_area(state_from_input(input_state([unit(1,1),unit(1,2)])),AreaState135(),d,a,0,**opts))]
 frozen=json.dumps(asdict(cast),sort_keys=True);results=[]
 for name,call in tests:
  try:call()
  except (ValueError,NotImplementedError)as e:results.append(dict(name=name,rejected=True,exception=type(e).__name__,reason=str(e)))
  else:raise AssertionError('Unknown area source accepted: '+name)
 assert frozen==json.dumps(asdict(cast),sort_keys=True)
 return results


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full','death'),default='pilot');a=p.parse_args()
 before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_HASH
 cases=corpus(a.phase=='pilot',a.phase=='death');guards=guard_cases();out,manifest=build(['cast','area_tick']);snap=out/'source-snapshot';snap.mkdir()
 for n,h in before.items():
  target=snap/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
 fixture=out/'area-effects135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
 guardfile=out/'area-effects135-guards.json';guardfile.write_text(json.dumps(guards,indent=2)+'\n')
 frozen={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
 results=out/'area-effects135-results.jsonl';err=out/'area-effects135-stderr.log';assert sha(RUNTIME)==RUNTIME_SHA
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_area_effects135_oracle.mjs'),str(out),str(fixture)]
 start=time.monotonic()
 with results.open('w')as stdout,err.open('w')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned area deadline')
 if code:raise RuntimeError(f'Original area failed: {out}')
 rows=[json.loads(x)for x in results.read_text().splitlines()];assert[c['id']for c in rows]==list(range(len(cases)))
 failures=[dict(id=c['id'],group=c['group'],expected=c['expected'],actual=r['stages'])for c,r in zip(cases,rows)if c['expected']!=r['stages']]
 mismatch=out/'area-effects135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
 after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and frozen=={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
 receipt=dict(version='0.135.1',build='0898d5e3',phase=a.phase,cases=len(cases),stages=sum(len(c['ops'])for c in cases),mismatch_cases=len(failures),groups=dict(Counter(c['group']for c in cases)),
  source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
  artifacts={p.name:sha(p)for p in(fixture,results,err,mismatch,guardfile,out/'area-effects135-runtime.json')},guards_rejected=len(guards),expected_before_original=True,source_snapshots=True,only_changed_section=7,
  runtime=json.loads((out/'area-effects135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),
  limitations=['Seven fixed kind3/effect0 or1 definitions; effect2/follow36/override49 and non-flat terrain rejected.',
   'Full88B area records strict; caller supplies explicit preallocated append-slot bytes, including unwritten8..23/85..87; zero masks.',
   'Empty proc/item sources; capped playerHP; death suite explicitly threads ordinary914 loot/placement sharedcounter and RNG; physical packet/ECS bytes and full-game schedule remain pending.',
   'Integer and float words strict; no NaN equivalence used in this finite corpus.'])
 (out/'area-effects135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_cases=len(failures),first_ids=[x['id']for x in failures[:12]])))
 if failures:raise SystemExit(1)


if __name__=='__main__':main()
