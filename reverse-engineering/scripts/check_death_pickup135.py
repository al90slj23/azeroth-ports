#!/usr/bin/env python3
"""Independent cast -> ordinary death -> mixed pickup -> XP/choice differential."""
from collections import Counter
from dataclasses import asdict,replace
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
from pathlib import Path
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
from check_level_cycle135 import make_input,empty_sources
from check_cast135_full_spec import definition_catalogue,inputs,unit,state_from_input
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.cast135 import cast_ability,process_hits,position
from core_spec.level_cycle135 import from_dict,projection
from core_spec.currency134 import CurrencyState
from core_spec.death_loot134 import OrdinaryDefinition
from core_spec.pickups134 import PickupRecord,Placement,encode_record56,decode_record56
from core_spec.death_pickup135 import (DeathContext135,OrdinaryDeathBinding135,OrdinaryDeathConsumer135,
 CollectionState135,collect_pickups,apply_damage_lifesteal)

FILES=['scripts/check_death_pickup135.py','scripts/run_death_pickup135_oracle.mjs',
 'scripts/check_level_cycle135.py','scripts/check_cast135_full_spec.py','scripts/build_full135_oracle.py',
 'scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py']
# All production transitive imports are frozen, including reused arithmetic codecs.
for n in ('death_pickup135','death_loot134','pickups134','pickup_entity134','pickup_entity','currency134',
 'cast135','combat135','combat134','level_cycle135','derived_stats135','derived_stats134','progression134',
 'progression','candidates135','ability_state','upgrade_values','binary32','binary32_sqrt','radius','rng'):
 p='reconstruction/core_spec/'+n+'.py'
 if (ROOT/p).exists():FILES.append(p)
SOURCE_FILES=tuple(FILES)
IMPORT_HASH={n:sha(ROOT/n) for n in SOURCE_FILES}
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
STATIC=ROOT/'evidence/spawn0135-static-20261101T034427.162905Z/spawn-data.json'


def words(record):
 raw=encode_record56(record,uninitialized_arrival_bits=0) if record.arrival_bits is None else encode_record56(record)
 v=list(struct.unpack('<14I',raw))
 if record.arrival_bits is None:v[1]=None
 return v


def snapshot(cast,collection,rawunits,dead_xyz):
 v=projection(collection.level)
 v.update(rng_words=list(cast.rng_words),units=[],accounted_total_hex=struct.pack('>d',cast.combat.accounted_total).hex(),
  pickup_words=[words(x) for x in collection.death.records],capacity=collection.death.capacity,
  spawn_counter=collection.death.spawn_counter,message_sequence=collection.death.message_sequence,
  kill_cost_bits=collection.death.kill_cost_bits,gold=collection.currency.gold,earned=collection.currency.earned,
  currency_queue=list(collection.currency.queue),currency_queue_capacity=collection.currency.queue_capacity,
  xp_queue=list(collection.xp_queue),xp_queue_capacity=collection.xp_queue_capacity,
  queued=[dict(asdict(h),target_id=str(h.target_id),source_id=str(h.source_id)) for h in cast.queued])
 for sp,raw in zip(cast.spatial,rawunits):
  u=sp.unit;xyz=dead_xyz.get(u.target_id)
  v['units'].append(dict(hp_bits=u.hp_bits,marker=u.marker,duration_bits=u.movement_duration_344_bits,
   movement_time_bits=u.movement_time_340_bits,death_time_bits=u.death_time_4_bits,afflicted=u.afflicted_240,
   from_xyz=list(xyz) if xyz else list(sp.from_xy)+[raw['from_xyz'][2]],
   to_xyz=list(xyz) if xyz else list(sp.to_xy)+[raw['to_xyz'][2]]))
 return json.loads(json.dumps(v))


def corpus(phase):
 rows=[];byid={d.ability_id:(d,h) for d,h in definition_catalogue()}
 norms=[n for n in json.loads(STATIC.read_text())['zones'][0]['normals'] if n['elite']==0]
 def add(group,*,mode=1,seed=(1,2,3,4),count=1,name=b'whirlwind',moving=False,records=(),radius=None,xp_mult=None,initial_xp=0,member_count=1,collect_only=False,class_byte=None,sources=None,heal_gate=0,hp_fraction=.3,nonlethal=False):
  n=norms[(len(rows)//4)%len(norms)];definition=OrdinaryDefinition.from_bytes(bytes.fromhex(n['raw72_hex']))
  # Empty stat/proc sources are explicit fixture snapshots; all levels remain ordinary1.
  raw=make_input(class_byte=class_byte if class_byte is not None else (8 if name==b'fireball' else 1),race_byte=1,level=1,phase=1,mode=mode,
   hp_fraction=hp_fraction,rng_words=seed,owned=() if collect_only else (name.decode(),),sources=sources,heal_gate=heal_gate)
  raw['progression']['xp']=initial_xp
  if radius is not None:raw['derived_bits']['1560']=f.from_float(radius)
  if xp_mult is not None:raw['derived_bits']['1564']=f.from_float(xp_mult)
  d,hexdata=byid[name];owned=AbilityRecord(d.pointer)
  units=[]
  for j in range(0 if collect_only else count):
   x=-9396+(j*.4);y=-633+(j%2)*.25
   u=unit(j+1,x,y,hp_bits=f.from_float(1000000 if nonlethal else .1),max_hp_bits=f.from_float(1000000 if nonlethal else 100))
   u.update(definition_pointer=n['pointer'],from_xyz=u['from_xy']+[0],to_xyz=u['to_xy']+[0])
   if moving:
    u.update(from_xy=[f.from_float(x-1),f.from_float(y-.5)],to_xy=[f.from_float(x+1),f.from_float(y+.5)],
     from_xyz=[f.from_float(x-1),f.from_float(y-.5),f.from_float(-1)],to_xyz=[f.from_float(x+1),f.from_float(y+.5),f.from_float(1)],duration_bits=f.from_float(2),movement_time_bits=f.from_float(9))
   units.append(u)
  s=inputs(units,now_bits=f.from_float(10),player_xy=[f.from_float(-9396),f.from_float(-633)],rng_words=list(seed),
   max_hp_bits=raw['stats']['old_max_hp_bits'],current_hp_bits=raw['stats']['current_hp_bits'],
   damage_multiplier_bits=raw['derived_bits']['1540'],cooldown_multiplier_bits=raw['derived_bits']['1544'],
   critical_chance_bits=raw['derived_bits']['1548'],critical_multiplier_bits=raw['derived_bits']['1552'],
   area_multiplier_bits=raw['derived_bits']['1580'],extra_targets=raw['derived_bits']['1592'])
  cast=state_from_input(s);original_spatial={sp.unit.target_id:sp for sp in cast.spatial};dead_xyz={}
  death=DeathContext135(tuple(records),max(0,len(records)),0xffffffff if len(rows)%7==0 else 11,19,f.from_float(2.5))
  currency=CurrencyState(7,9,raw['derived_bits']['1588'],mode,42,member_count,0,(),0,())
  col=CollectionState135(from_dict(raw),death,currency,tuple(s['player_xy'])+(0,),(),0,True)
  ops=[];expected=[];events=[]
  def on_death(state,damage):
   nonlocal col
   col=replace(col,level=apply_damage_lifesteal(replace(col.level,stats=replace(col.level.stats,now_bits=state.combat.now_bits)),damage.damage_bits))
   orig=original_spatial[damage.target.target_id];xy=position(orig,state.combat.now_bits)
   dur=orig.unit.movement_duration_344_bits
   if f.to_float(dur)<=0:z=units[damage.target.target_id-1]['to_xyz'][2]
   else:
    t=f.div(f.sub(state.combat.now_bits,orig.unit.movement_time_340_bits),dur)
    if f.to_float(t)<0:t=0
    if f.to_float(t)>1:t=f.from_float(1)
    uz=units[damage.target.target_id-1];z=f.add(uz['from_xyz'][2],f.mul(f.sub(uz['to_xyz'][2],uz['from_xyz'][2]),t))
   xyz=xy+(z,);dead_xyz[damage.target.target_id]=xyz
   # Flat height0 explicit; all these positions lie strictly within zone0 radius120.
   binding=OrdinaryDeathBinding135(definition,n['pointer'],Placement(*xy,0),Placement(f.add(xy[0],f.from_float(.8)),f.add(xy[1],f.from_float(.8)),0),xyz,
    f.to_float(dur)>0 and f.to_float(state.combat.now_bits)<f.to_float(f.add(orig.unit.movement_time_340_bits,dur)))
   from core_spec.death_pickup135 import consume_ordinary_death
   r=consume_ordinary_death(state,damage,consumer.context,binding);consumer.context=r.context;events.append(dict(guid=damage.target.target_id,draws=r.draws,death_xyz=list(xyz)));return r.cast
  consumer=OrdinaryDeathConsumer135(death,{})
  def record(kind,now):
   nonlocal cast,col
   ops.append(dict(kind=kind,now_bits=now))
   if kind=='cast':
    result=cast_ability(cast,d,owned,after_death=on_death);cast=result.state
    if nonlethal and d.execution_kind==2:
     for hit in result.hits:col=replace(col,level=apply_damage_lifesteal(col.level,hit[1]))
   elif kind=='process':
    queue=cast.queued;cast,applied=process_hits(cast,now,after_death=on_death)
    if nonlethal:
     accepted={guid for guid,hp in applied}
     for hit in queue:
      if hit.target_id in accepted and f.to_float(hit.due_bits)<=f.to_float(now):
       col=replace(col,level=apply_damage_lifesteal(replace(col.level,stats=replace(col.level.stats,now_bits=now)),hit.damage_bits))
   else:
    col=replace(col,level=replace(col.level,rng_words=cast.rng_words),death=consumer.context)
    out=collect_pickups(col,now)
    if out.status!='core_projection':raise RuntimeError(out)
    col=out.state;consumer.context=col.death;cast=replace(cast,rng_words=col.level.rng_words)
   col=replace(col,death=consumer.context)
   expected.append(snapshot(cast,col,units,dead_xyz))
  if not collect_only:
   record('cast',s['now_bits'])
   if cast.queued:
    due=max(h.due_bits for h in cast.queued);record('process',due)
  now=ops[-1]['now_bits'] if ops else s['now_bits']
  record('collect',now)
  record('collect',f.add(now,f.from_float(.119)))
  record('collect',f.add(now,f.from_float(1)))
  control=dict(player_xyz=list(col.player_xyz),currency=asdict(currency),xp_queue=[],xp_queue_capacity=0,
   pickup_hex=[encode_record56(r).hex() for r in records],capacity=death.capacity,spawn_counter=death.spawn_counter,message_sequence=death.message_sequence,kill_cost_bits=death.kill_cost_bits)
  dd=asdict(d);dd['ability_id']=d.ability_id.decode()
  rows.append(json.loads(json.dumps(dict(id=len(rows),mode='collect' if collect_only else 'cast',group=group,level=raw,cast=s,control=control,definition=dd,definition_hex=hexdata,owned_hex=owned.to_bytes().hex(),ops=ops,expected=expected,independent_deaths=events),allow_nan=False)))
 for mode in (0,1):
  for name in (b'whirlwind',b'fireball'):
   add('pilot-real-cast-death-XP-choice',mode=mode,name=name,count=3,initial_xp=4)
 add('pilot-moving-death-freezes-endpoints',moving=True,count=3,initial_xp=4)
 add('pilot-projectile-moving-death-freezes-endpoints',moving=True,count=1,name=b'fireball',initial_xp=4)
 if phase=='pilot':return rows
 rng=random.Random(0x13519141417)
 for mode in (0,1):
  for name in (b'whirlwind',b'fireball'):
   for count in (1,2,4,7):
    for j in range(8):
     seed=tuple(rng.getrandbits(32) for _ in range(4))
     add('real-cast-multiple-deaths-RNG-continuation',mode=mode,name=name,count=count,seed=seed,moving=j%3==0,initial_xp=j%5,member_count=(1,2,4)[j%3])
 for mode in (0,1):
  for mult in (.25,1,3):
   # Reverse dispatch XP changes later multipliers but never recomputes entry-selected indices.
   for seed in ((1,2,3,4),(193,19,11,16)):
    x,y=f.from_float(-9396),f.from_float(-633)
    rs=(PickupRecord(marker=0,arrival_bits=0,kind=1,amount=7,guid=801,visual_id=9004,x_bits=f.add(x,f.from_float(2)),y_bits=y,spawn_time_bits=f.from_float(10)),
        PickupRecord(marker=1,arrival_bits=f.from_float(9),amount=9,guid=802,x_bits=x,y_bits=y,spawn_time_bits=0),
        PickupRecord(marker=1,arrival_bits=f.from_float(9),kind=1,amount=11,guid=803,visual_id=9004,x_bits=x,y_bits=y,spawn_time_bits=0),
        PickupRecord(marker=1,arrival_bits=f.from_float(9),amount=6,guid=804,x_bits=x,y_bits=y,spawn_time_bits=0))
    add('mixed-entry-selection-latest-multiplier-reverse-awards',mode=mode,seed=seed,collect_only=True,records=rs,radius=.1,xp_mult=mult,member_count=3)
 for cls in (0,1,2,3,4,5,6,7,8,9,10,11,255):
  for gate in (0,5):
   add('all-class-base-lifesteal-and-half-gate',class_byte=cls,heal_gate=gate,count=2,initial_xp=4)
 for family in ('timed','item','adjustment','mixed','negative','NaN'):
  for cls in (1,7,8):
   for gate in (0,5):
    src=empty_sources()
    if family in ('timed','mixed'):
     src['definitions']=[dict(kind=27,value4_bits=0,value20_bits=f.from_float(.07),modifier_tag=14,summon_state41=0)]
     src['timed_records']=[dict(definition_index=0,stack_count=3,expires_bits=f.from_float(11)),dict(definition_index=0,stack_count=1,expires_bits=f.from_float(10)),dict(definition_index=9,stack_count=8,expires_bits=f.from_float(11))]
    if family in ('item','mixed','negative','NaN'):
     value=f.from_float(-1 if family=='negative' else .03) if family!='NaN' else 0x7fc00001
     src['item_modifiers']=[dict(tag=14,value_bits=value),dict(tag=14,value_bits=f.from_float(.01))]
    if family in ('adjustment','mixed'):
     src['adjustments']=[dict(tag=18,value_bits=f.from_float(.02),definition32_bits=0),dict(tag=18,value_bits=f.from_float(.01),definition32_bits=0)]
    add('nonlethal-lifesteal-source-order-'+family,class_byte=cls,heal_gate=gate,sources=src,count=3,initial_xp=4,nonlethal=True)
 for fraction in (0,1,2,float('nan')):
  for gate in (0,5):
   add('lifesteal-HP-clamp-and-NaN',hp_fraction=fraction,heal_gate=gate,count=3,initial_xp=4)
 if phase=='pending-effects':
  selected=[r for r in rows if r['group'] in ('nonlethal-lifesteal-source-order-timed','nonlethal-lifesteal-source-order-mixed')]
 else:
  selected=[r for r in rows if r['group'] not in ('nonlethal-lifesteal-source-order-timed','nonlethal-lifesteal-source-order-mixed')]
 for i,row in enumerate(selected):row['id']=i
 return selected


def equal(w,a,path=''):
 if w is None and '.pickup_words[' in path and path.endswith('[1]'):return True
 if type(w)!=type(a):return False
 if isinstance(w,dict):return set(w)==set(a) and all(equal(v,a[k],path+'.'+k) for k,v in w.items())
 if isinstance(w,list):return len(w)==len(a) and all(equal(v,x,path+f'[{j}]') for j,(v,x) in enumerate(zip(w,a)))
 return w==a


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full','pending-effects'),default='pilot');args=p.parse_args()
 before={n:sha(ROOT/n) for n in SOURCE_FILES};assert before==IMPORT_HASH
 rows=corpus(args.phase);out,manifest=build(['cast','process_hits','collect_pickups']);snap=out/'source-snapshot';snap.mkdir()
 for n in SOURCE_FILES:
  path=snap/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/n).read_bytes());assert sha(path)==before[n]
 fixtures=out/'death-pickup135-fixtures.jsonl';fixtures.write_text(''.join(json.dumps(c,separators=(',',':'),allow_nan=False)+'\n' for c in rows));assert [json.loads(x)for x in fixtures.read_text().splitlines()]==rows
 frozen={p.name:sha(p)for p in (fixtures,out/'manifest.json',out/manifest['module_file'])}
 assert sha(RUNTIME)==RUNTIME_SHA;assert subprocess.check_output([str(RUNTIME),'--version'],text=True).strip()=='v22.23.4'
 cmd=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_death_pickup135_oracle.mjs'),str(out),str(fixtures)]
 result=out/'death-pickup135-original-results.jsonl';err=out/'death-pickup135-stderr.log';start=time.monotonic()
 with result.open('w')as stream,err.open('w')as errors:
  child=subprocess.Popen(cmd,stdout=stream,stderr=errors,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned death/pickup135 original exceeded60s')
 duration=time.monotonic()-start
 if code:raise RuntimeError(f'Original failed exit{code}; inspect {out}')
 actual=[json.loads(x)for x in result.read_text().splitlines()];assert [x['id']for x in actual]==list(range(len(rows)))
 failures=[dict(id=c['id'],group=c['group'],expected=c['expected'],actual=a['stages'])for c,a in zip(rows,actual)if not equal(c['expected'],a['stages'])]
 mismatch=out/'death-pickup135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
 after={n:sha(ROOT/n)for n in SOURCE_FILES};assert before==after;assert sha(SOURCE)==SOURCE_SHA;assert sha(RUNTIME)==RUNTIME_SHA;assert frozen=={p.name:sha(p)for p in (fixtures,out/'manifest.json',out/manifest['module_file'])}
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(rows),stages=sum(len(c['ops'])for c in rows),mismatch_cases=len(failures),groups=dict(Counter(c['group']for c in rows)),source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),artifacts={p.name:sha(p)for p in (fixtures,result,err,mismatch,out/'death-pickup135-runtime.json')},runtime=json.loads((out/'death-pickup135-runtime.json').read_text()),process=dict(command=cmd,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=round(duration,3)),independent_expected_before_original=True,source_snapshots=True,only_changed_section=7,limitations=['Explicit empty item/proc/claim state; ordinary unflagged definition only; flat resolved placement within zone0.','Uninitialized new pickup+4 words alone permit unspecified comparison until first write.','Physical ECS/visual/wire bytes and full game scheduler remain pending; mode0 movement stop35514 pending.','Nonempty definitions dispatch984 and mutate timed sources/trigger1512 after each hit; pending-effects suite retains12 known-unresolved cases and is excluded from passing full coverage.','18353 timed-source coefficient is statically reconstructed but its interaction with984 is not independently complete.'])
 (out/'comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(rows),mismatch_cases=len(failures),first_ids=[x['id']for x in failures[:12]],seconds=duration)))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
