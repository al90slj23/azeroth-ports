#!/usr/bin/env python3
"""Fresh135 full target/cast/auto/delayed-hit differential; no game start."""
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
from pathlib import Path
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build,parse_source
from build_upgrade134_oracle import sha
SOURCE_FILES=('scripts/check_cast135_full_spec.py','scripts/run_cast135_full_oracle.mjs',
 'scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py',
 'reconstruction/core_spec/cast135.py','reconstruction/core_spec/combat135.py','reconstruction/core_spec/combat134.py',
 'reconstruction/core_spec/ability_state.py','reconstruction/core_spec/upgrade_values.py',
 'reconstruction/core_spec/binary32.py','reconstruction/core_spec/binary32_sqrt.py',
 'reconstruction/core_spec/radius.py','reconstruction/core_spec/rng.py')
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
IMPORT_SHA={n:sha(ROOT/n) for n in SOURCE_FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.combat135 import UnitState,CombatState
from core_spec.cast135 import (CastDefinition,SpatialUnit,CastState,query_targets,cast_ability,auto_cast,auto_cast_many,process_hits)


def definition_catalogue():
 binary=SOURCE.read_bytes();assert hashlib.sha256(binary).hexdigest()==SOURCE_SHA
 segments=parse_source(binary)[4];size=max(s['address']+s['length'] for s in segments if s['address'] is not None)
 memory=bytearray(size)
 for s in segments:
  if s['address'] is not None:memory[s['address']:s['address']+s['length']]=binary[s['file_offset']:s['file_offset']+s['length']]
 result=[]
 for j in range(114):
  pointer=5467428+j*88;raw=bytes(memory[pointer:pointer+88]);w=struct.unpack('<22I',raw);aid=bytes(memory[w[3]:w[3]+w[4]])
  if raw[84] in (0,2) and w[0]==0:
   d=CastDefinition(pointer,aid,raw[84],w[0],w[11],raw[85],w[12],w[13],w[14],w[15],w[16])
   result.append((d,raw.hex()))
 assert len({d.ability_id for d,_ in result})==len(result)
 return result


def unit(guid,x,y=0,**kw):
 v=dict(guid=str(guid),hp_bits=f.from_float(1000000),max_hp_bits=f.from_float(1000000),marker=0,
 kind_40=-1,kind_64=-1,elite_244=-1,elite_416=0,linked_id='0',priority_until372_bits=0,
 phase_until408_bits=0,phase_until412_bits=0,from_xy=[f.from_float(x),f.from_float(y)],
 to_xy=[f.from_float(x),f.from_float(y)],duration_bits=0,movement_time_bits=0)
 v.update(kw);return v


def inputs(units=None,**kw):
 v=dict(units=[unit(1,1),unit(2,3),unit(3,12)] if units is None else units,
 now_bits=f.from_float(10),player_xy=[0,0],phase=1,rng_words=[1,2,3,4],
 damage_multiplier_bits=f.from_float(1),max_hp_bits=f.from_float(500),current_hp_bits=f.from_float(500),
 critical_chance_bits=f.from_float(.3),critical_multiplier_bits=f.from_float(2),
 area_multiplier_bits=f.from_float(1),cooldown_multiplier_bits=f.from_float(1),extra_targets=0,
 source_id='999',current_target_id='0',context908=0,override_bits=0)
 v.update(kw);return v


def state_from_input(s):
 spatial=[]
 for x in s['units']:
  u=UnitState(int(x['guid']),x['hp_bits'],x['max_hp_bits'],marker=x['marker'],kind_40=x['kind_40'],
    kind_64=x['kind_64'],elite_244=x['elite_244'],elite_416=x['elite_416'],linked_id_32=int(x['linked_id']),
    movement_duration_344_bits=x['duration_bits'],movement_time_340_bits=x['movement_time_bits'],
    phase_until_408_bits=x['phase_until408_bits'],phase_until_412_bits=x['phase_until412_bits'])
  spatial.append(SpatialUnit(u,tuple(x['from_xy']),tuple(x['to_xy']),x['priority_until372_bits']))
 combat=CombatState(tuple(x.unit for x in spatial),now_bits=s['now_bits'],phase_2579=s['phase'])
 return CastState(combat,tuple(spatial),tuple(s['player_xy']),tuple(s['rng_words']),
  s['damage_multiplier_bits'],s['max_hp_bits'],s['critical_chance_bits'],s['critical_multiplier_bits'],
  s['area_multiplier_bits'],s['cooldown_multiplier_bits'],s['extra_targets'],int(s['source_id']),
  int(s['current_target_id']),s['context908'],())


def projection(state,remaining=None):
 hits=[]
 for h in state.queued:
  v=asdict(h);v['target_id']=str(v['target_id']);v['source_id']=str(v['source_id']);hits.append(v)
 return dict(hp_bits=[u.hp_bits for u in state.combat.units],markers=[u.marker for u in state.combat.units],
  rng_words=list(state.rng_words),accounted_total_hex=struct.pack('>d',state.combat.accounted_total).hex(),
  queued=hits,attempted_spell_sets=[list(state.attempted_spell_ids)]*3,active_remaining_bits=remaining)


def corpus(phase='full'):
 defs=definition_catalogue();byid={d.ability_id:(d,h) for d,h in defs};rows=[]
 def add_query(group,s,radius,excluded=()):
  s=dict(s,query_radius_bits=radius,excluded=list(map(str,excluded)))
  state=state_from_input(s);want={'targets':list(map(str,query_targets(state.spatial,state.player_xy,radius,s['now_bits'],tuple(excluded))))}
  rows.append(dict(id=len(rows),mode='query',group=group,input=s,expected=want))
 def add_cast(group,name,s=None,owned=None,dt=None,delayed=True):
  d,hexdata=byid[name];s=inputs() if s is None else s;owned=owned or AbilityRecord(d.pointer,remaining_cooldown_bits=0)
  mode='auto' if dt is not None else 'cast';state=state_from_input(s);stages=[];remaining=owned.remaining_cooldown_bits
  if dt is not None:
   for bits in dt:
    state,remaining,result=auto_cast(state,d,owned,remaining,bits,s['override_bits'])
    stages.append(dict(kind='auto',snapshot=projection(state,remaining)))
  else:
   result=cast_ability(state,d,owned);state=result.state;stages.append(dict(kind='cast',success=result.success,snapshot=projection(state)))
  at=[]
  if delayed and state.queued:
   dues=[h.due_bits for h in state.queued]
   finite=[x for x in dues if f.to_float(x)>=0 and x<0x7f800000]
   if finite:at=[max(0,min(finite)-1),min(finite),max(finite)]
   for now in at:
    state,_=process_hits(state,now);stages.append(dict(kind='process',snapshot=projection(state,remaining if mode=='auto' else None)))
  dd=asdict(d);dd['ability_id']=d.ability_id.decode()
  rows.append(dict(id=len(rows),mode=mode,group=group,input=s,definition=dd,definition_hex=hexdata,
   owned_hex=owned.to_bytes().hex(),dt_bits=dt or [],process_at_bits=at,expected={'stages':stages}))
 add_query('pilot-query',inputs(),f.from_float(8))
 add_cast('pilot-area',b'whirlwind');add_cast('pilot-projectile',b'fireball')
 add_cast('pilot-auto',b'whirlwind',owned=replace(AbilityRecord(byid[b'whirlwind'][0].pointer),level=4),dt=[f.from_float(.1),f.from_float(.5),f.from_float(8)])
 add_cast('pilot-empty-retry',b'fireball',s=inputs([]),dt=[f.from_float(.1),f.from_float(.5),f.from_float(.4)])
 if phase=='pilot':return rows
 for d,_ in defs:
  for n in (0,1,3,7):
   s=inputs([unit(j+1,j*2+1,hp_bits=f.from_float(1000000-j*1000)) for j in range(n)])
   for rank in (1,4,19):
    a=replace(AbilityRecord(d.pointer,remaining_cooldown_bits=0),level=rank,damage_bits=f.from_float(1+rank*.17),
      cooldown_bits=f.from_float(1/(1+rank*.05)),extra_targets=rank%3,area_bits=f.from_float(1+rank*.05),life_damage_bits=f.from_float(.002*rank))
    add_cast('all-supported-definitions-ranked',d.ability_id,s,a)
 for radius in (0,0x80000000,f.from_float(5),f.from_float(-5),f.from_float(70),0x7f800000,0xff800000,0x7fc00001):
  for n in (0,1,2,5,20,21,32,65):
   s=inputs([unit(j+1,(j%5)-2,(j//5)-2,marker=j%7==0) for j in range(n)])
   add_query('query-size-sort-and-radius',s,radius,tuple(j+1 for j in range(n) if j%9==0))
 rng=random.Random(0xa2e0922)
 for k in range(360):
  n=rng.randrange(67);us=[]
  for j in range(n):
   a=[f.from_float(rng.uniform(-50,50)) for _ in range(2)];b=[f.from_float(rng.uniform(-50,50)) for _ in range(2)]
   us.append(unit(j+1,0,from_xy=a,to_xy=b,duration_bits=rng.choice([0,f.from_float(-1),f.from_float(5),0x7fc00001]),
      movement_time_bits=f.from_float(rng.choice([0,5,10,20])),marker=rng.randrange(5)==0))
  add_query('query-random-motion-exclusion',inputs(us),f.from_float(rng.uniform(-80,80)),tuple(j+1 for j in range(n) if j%13==0))
 for k in range(400):
  d,_=rng.choice(defs);n=rng.randrange(1,9);us=[]
  for j in range(n):
   us.append(unit(j+1,rng.uniform(-18,18),rng.uniform(-18,18),hp_bits=f.from_float(rng.uniform(10000000,100000000)),
     duration_bits=f.from_float(rng.choice([0,0,5])),movement_time_bits=f.from_float(5),
     from_xy=[f.from_float(rng.uniform(-20,20)),f.from_float(rng.uniform(-20,20))]))
  s=inputs(us,critical_chance_bits=f.from_float(rng.choice([-.1,0,.05,.3,1,1.1])),
   critical_multiplier_bits=f.from_float(rng.choice([.5,1,1.5,2,3])),area_multiplier_bits=f.from_float(rng.choice([.5,1,2,9,25])),
   cooldown_multiplier_bits=f.from_float(rng.choice([0,.3,1,2])),damage_multiplier_bits=f.from_float(rng.choice([-.2,0,.1,1,3])),
   rng_words=[rng.getrandbits(32) for _ in range(4)],extra_targets=rng.randrange(3),current_target_id=str(rng.randrange(n+2)))
  a=replace(AbilityRecord(d.pointer,remaining_cooldown_bits=f.from_float(rng.choice([-.1,0,.3,1]))),level=rng.randrange(1,30),
   damage_bits=f.from_float(rng.uniform(.1,3)),additional_damage_bits=f.from_float(rng.uniform(.2,2)),
   cooldown_bits=f.from_float(rng.uniform(.1,2)),additional_cooldown_bits=f.from_float(rng.uniform(.1,2)),
   extra_targets=rng.randrange(3),additional_targets=rng.randrange(3),area_bits=f.from_float(rng.uniform(.2,3)),
   additional_area_bits=f.from_float(rng.uniform(.2,2)),life_damage_bits=f.from_float(rng.choice([0,.02,.1])))
  if k%2:add_cast('mixed-auto-rank-multipliers',d.ability_id,s,a,dt=[f.from_float(x) for x in (.1,.5,8)])
  else:add_cast('mixed-cast-rank-multipliers',d.ability_id,s,a)
 for k in range(72):
  count=1+k%6; chosen=[defs[(k+j*3)%len(defs)] for j in range(count)]
  snapshot=inputs([unit(j+1,j*2-4,hp_bits=f.from_float(10000000-j*500000)) for j in range(k%8)],
   rng_words=[rng.getrandbits(32) for _ in range(4)],critical_chance_bits=f.from_float(rng.choice([0,.3,1])))
  state=state_from_input(snapshot);records=[];entry=[];definitions=[];hexlist=[];overrides=[]
  for j,(d,dh) in enumerate(chosen):
   a=replace(AbilityRecord(d.pointer),level=2+j,remaining_cooldown_bits=f.from_float([0,.2,1][j%3]),
    damage_bits=f.from_float(1+j*.13),cooldown_bits=f.from_float(1/(1+j*.1)),extra_targets=j%3)
   records.append(a);entry.append((d,a,a.remaining_cooldown_bits,f.from_float(.1) if j%4==3 else 0))
   dd=asdict(d);dd['ability_id']=d.ability_id.decode();definitions.append(dd);hexlist.append(dh);overrides.append(entry[-1][3])
  stages=[];dts=[f.from_float(x) for x in (.1,.4,10)]
  for dt in dts:
   state,remaining,_=auto_cast_many(state,entry,dt)
   entry=[(d,a,b,o) for (d,a,_,o),b in zip(entry,remaining)]
   stages.append(dict(kind='auto',snapshot=projection(state,list(remaining))))
  at=[]
  if state.queued:
   finite=[h.due_bits for h in state.queued if 0<=f.to_float(h.due_bits)<float('inf')]
   if finite:at=[max(0,min(finite)-1),min(finite),max(finite)]
   for now in at:
    state,_=process_hits(state,now);stages.append(dict(kind='process',snapshot=projection(state,list(remaining))))
  rows.append(dict(id=len(rows),mode='auto-many',group='multiple-active-forward-HP-RNG-order',input=snapshot,
   definitions=definitions,definition_hex_list=hexlist,owned_hex_list=[a.to_bytes().hex() for a in records],
   override_bits_list=overrides,dt_bits=dts,process_at_bits=at,expected={'stages':stages}))
 for name in (b'whirlwind',b'fireball',b'hellfire'):
  for phasebyte in (0,1,2,3,4,5,128,255):
   for override in (0,f.from_float(.01),f.from_float(1),0x7fc00001):
    s=inputs(phase=phasebyte,override_bits=override)
    add_cast('phase-and-override-cooldown',name,s,dt=[0,f.from_float(.4),f.from_float(20)])
 for d,_ in defs:
  if d.execution_kind==0:
   s=inputs([unit(1,1,hp_bits=f.from_float(800000)),unit(2,2,hp_bits=f.from_float(200000)),unit(3,9,hp_bits=f.from_float(100000)),unit(4,15,hp_bits=f.from_float(100000))])
   add_cast('nearby-hp-priority-and-target-count-clamp',d.ability_id,s,replace(AbilityRecord(d.pointer),extra_targets=4,additional_targets=2))
 return rows


def equal(w,a,path=''):
 if type(w)!=type(a):return False
 if isinstance(w,dict):return set(w)==set(a) and all(equal(v,a[k],path+'.'+k) for k,v in w.items())
 if isinstance(w,list):return len(w)==len(a) and all(equal(v,x,path+f'[{j}]') for j,(v,x) in enumerate(zip(w,a)))
 floating=('.hp_bits[' in path or path.endswith('.active_remaining_bits') or
           ('.queued[' in path and path.endswith(('.due_bits','.damage_bits'))))
 return w==a or (floating and isinstance(w,int) and f.is_nan(w) and f.is_nan(a))


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
 before={n:sha(ROOT/n) for n in SOURCE_FILES};assert before==IMPORT_SHA
 rows=corpus(args.phase);out,manifest=build(['cast','auto_cast','process_hits','query_targets'])
 snap=out/'source-snapshot';snap.mkdir()
 for n in SOURCE_FILES:
  p=snap/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==before[n]
 fixtures=out/'cast135-fixtures.jsonl';fixtures.write_text(''.join(json.dumps(c,allow_nan=False,separators=(',',':'))+'\n' for c in rows))
 assert [json.loads(x) for x in fixtures.read_text().splitlines()]==rows
 frozen_hashes={p.name:sha(p) for p in (fixtures,out/'manifest.json',out/manifest['module_file'])}
 assert sha(RUNTIME)==RUNTIME_SHA;version=subprocess.check_output([str(RUNTIME),'--version'],text=True).strip();assert version=='v22.23.4'
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_cast135_full_oracle.mjs'),str(out),str(fixtures)]
 result=out/'cast135-original-results.jsonl';stderr=out/'cast135-stderr.log';start=time.monotonic()
 with result.open('w') as stream,stderr.open('w') as err:
  child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned cast135 oracle exceeded60s')
 duration=time.monotonic()-start
 if code:raise RuntimeError(f'Original failed exit{code}; inspect {out}')
 result_sha=sha(result)
 actual=[json.loads(x) for x in result.read_text().splitlines()]
 assert [x['id'] for x in actual]==list(range(len(rows)))
 assert [x['id'] for x in map(json.loads,fixtures.read_text().splitlines())]==list(range(len(rows)))
 failures=[]
 for c,a in zip(rows,actual):
  target={k:v for k,v in a.items() if k!='id'}
  if not equal(c['expected'],target):failures.append({'id':c['id'],'group':c['group'],'expected':c['expected'],'actual':target})
 (out/'cast135-mismatches.json').write_text(json.dumps(failures,indent=2,allow_nan=False)+'\n')
 after={n:sha(ROOT/n) for n in SOURCE_FILES};assert after==before;assert sha(SOURCE)==SOURCE_SHA;assert sha(RUNTIME)==RUNTIME_SHA
 assert result_sha==sha(result)
 assert frozen_hashes=={p.name:sha(p) for p in (fixtures,out/'manifest.json',out/manifest['module_file'])}
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(rows),mismatch_cases=len(failures),
  groups=dict(Counter(x['group'] for x in rows)),modes=dict(Counter(x['mode'] for x in rows)),
  source_sha256_before=before,source_sha256_after=after,original_wasm_sha256=SOURCE_SHA,
  module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
  artifacts={p.name:sha(p) for p in (fixtures,result,stderr,out/'cast135-mismatches.json',out/'cast135-runtime.json')},
  runtime=json.loads((out/'cast135-runtime.json').read_text()),process=dict(command=command,exit_code=code,deadline_seconds=60,seconds=round(duration,3),pid=child.pid,pgid=child.pid),
  independent_expected_before_original=True,source_snapshots=True,only_changed_section=7,original_internal_callees_preserved=True,
  limitations=['All original profiles use known-empty auxiliary/proc/item state, canonical unique ordinary GUIDs and nonlethal hits.',
   'Production dispatcher rejects nonzero effect tags, other execution kinds and unresolved death continuation.',
   'Physical packet/presentation bytes, procs/death loot, complete active/timed-system scheduler and full game remain pending.',
   'Only declared float outputs permit NaN classification equality; integers are strict.'])
 (out/'comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'directory':str(out),'cases':len(rows),'mismatch_cases':len(failures),'first_ids':[x['id'] for x in failures[:12]],'seconds':duration}))
 if failures:raise SystemExit(1)

if __name__=='__main__':main()
