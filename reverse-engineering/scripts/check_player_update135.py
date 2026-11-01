#!/usr/bin/env python3
"""Full2088 empty-periodic expiry/regen plus full921 corpse cleanup differential."""
import argparse,json,os,signal,struct,subprocess,time,sys,ast
from collections import Counter
from dataclasses import replace
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
LEVEL_FILES=ast.literal_eval(next(n.value for n in ast.parse((ROOT/'scripts/check_level_cycle135.py').read_text()).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SOURCE_FILES'for t in n.targets)))
FILES=tuple(dict.fromkeys((*LEVEL_FILES,'reconstruction/core_spec/__init__.py','reconstruction/core_spec/player_update135.py','reconstruction/core_spec/ai_lifecycle135.py','scripts/check_player_update135.py','scripts/run_player_update135_oracle.mjs')))
IMPORT_HASH={n:sha(ROOT/n)for n in FILES}
from check_level_cycle135 import make_input,empty_sources,RUNTIME,RUNTIME_SHA,differences
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.level_cycle135 import from_dict
from core_spec.player_update135 import prepare_player_update,UnresolvedPlayerUpdate135
from core_spec.ai_lifecycle135 import cleanup_ordinary_corpses


def projection(result):
 l=result.level
 return dict(live_records=result.live_records,derived_bits=dict(l.derived_bits),current_hp_bits=l.stats.current_hp_bits,
  auxiliary_bits={1444:l.stats.pool1532_bits,1448:l.stats.pool1536_bits,1348:l.stats.conditional1348_bits,768:l.stats.pool768_bits,756:l.pool756_bits},
  shield_source=l.stats.conditional1344_id,speed_bits=l.stats.previous_speed_bits,player_fields={k:v for k,v in l.player_fields if k in(22,28,1109)},rng_words=l.rng_words)


def corpus(pilot):
 rows=[];b=f.from_float
 def player(group='baseline',cls=8,race=1,hp=.3,gate=0,live=(),steps=((10,.1),),last=0,shield=0,source=0,remaining=0,barrier=0,derived=None,hp_word=None):
  sources=empty_sources();sources['live_effects']=[dict(kind=r[2],value_bits=0 if r[2]==12 else r[3],spell_id=r[5],expires_bits=r[6])for r in live]
  raw=make_input(class_byte=cls,race_byte=race,phase=1,mode=0,heal_gate=gate,hp_fraction=hp,sources=sources)
  raw['stats'].update(conditional1344_id=source,conditional1348_bits=b(remaining),pool1532_bits=b(shield),pool1536_bits=b(barrier),pool768_bits=0)
  if hp_word is not None:raw['stats']['current_hp_bits']=hp_word
  if derived:
   for k,v in derived.items():raw['derived_bits'][str(k)]=v
  l=from_dict(raw);records=tuple(struct.pack('<8I',*r).hex()for r in live);expected=[];trace=[]
  for now,dt in steps:
   now=now if type(now)is tuple else(b(now),);dt=dt if type(dt)is tuple else(b(dt),)
   q=prepare_player_update(l,records,(),now[0],dt[0],b(last),explicit_other_sources_absent=True,periodic_input=())
   l=q.level;records=q.live_records;expected.append(projection(q));trace.append(dict(now_bits=now[0],dt_bits=dt[0]))
  # Genuine racial80, not a dummy basic. Infinite remaining and melee prelude
  # timer isolate2088 prefix while every real1076 callee stays unchanged.
  owned=replace(AbilityRecord(5476580),remaining_cooldown_bits=0x7f800000)
  rows.append(dict(id=len(rows),kind='player',group=group,input=raw,live_records=[struct.pack('<8I',*r).hex()for r in live],last_hit_bits=b(last),steps=trace,owned_hex=owned.to_bytes().hex(),expected=expected))
 def corpse(group,markers,times,owners,now=10,mode=0,peer=0,guids=None):
  records=[]
  for i,(mark,t,owner)in enumerate(zip(markers,times,owners)):
   z=bytearray(424)
   for off,val in((0,mark),(4,b(t)),(40,f.MASK),(64,f.MASK),(244,f.MASK),(280,owner),(400,b(1000))):struct.pack_into('<I',z,off,val)
   struct.pack_into('<Q',z,112,guids[i]if guids else i+1);records.append(z.hex())
  q=cleanup_ordinary_corpses(tuple(records),b(now),mode=mode,local_peer=peer,explicit_other_sources_absent=True)
  rows.append(dict(id=len(rows),kind='corpse',group=group,records=records,now_bits=b(now),mode=mode,peer=peer,expected=dict(records=q.records,packet_count=q.packet_count,removed_guids=[str(x)for x in q.removed_guids],rng_words=[1,2,3,4],sequence=123)))
 player();player('perception-14second-expiry',live=((0,0,8,b(.3),0,20600,b(14),0),),steps=((13.999,.1),(14,.1),(14.1,.1),(15,.1)))
 player('source-shield-expiry',live=((0,0,7,b(.2),0,20594,b(10),0),),source=20594,remaining=7,shield=10,barrier=8)
 corpse('corpse-basic',[1,1,1],[8,9,10],[0,0,0])
 if pilot:return json.loads(json.dumps(rows))
 for cls in(1,2,3,4,5,7,8,9,11):
  for race in range(1,9):
   player('class-race-expiry',cls=cls,race=race,live=((0,0,8,b(.3),0,20600,b(14),0),(0,0,9,b(.2),0,26297,b(20),0)),steps=((13.9,.1),(14,.1),(20,.1)))
 for hp in(-1,0,.3,.999,1,2):
  for gate in(0,4,5,255):
   for dt in(0,.001,.1,1,20,-.1):player('regen-hp-gate-dt',hp=hp,gate=gate,steps=((10,dt),))
 for since in(2.999999,3,3.000001):
  for gate in(0,5):player('last-hit-three-second',gate=gate,last=10-since,derived={1576:b(2),1620:b(.03)})
 for tag in(7,8,9,12):
  for expiry in(9.999,10,10.001):
   player('live-tags-exact-expiry',live=((0,0,tag,b(.3),0x12345678,20594 if tag==7 else 20600,b(expiry),0),),steps=((10,.1),(10.001,.1)))
 for live in(((0,0,8,b(.3),0,20600,0x7fc00001,0),),((0,0,8,b(.3),0,20600,0x7fc00001,0),(0,0,9,b(.2),0,26297,b(10),0)),((0,0,8,b(.3),0,20600,b(20),0),(0,0,9,b(.2),0,26297,b(10),0),(0,0,8,b(.2),0,1,b(30),0))):player('stable-filter-NaN-coexpiry',live=live)
 for shield,remaining,barrier in((10,7,8),(2,7,8),(0,0,8),(10,7,1)):
  player('shield-source-pool-expiry',live=((0,0,7,b(.2),0,20594,b(10),0),),source=20594,remaining=remaining,shield=shield,barrier=barrier)
 for word in(0x7fc00001,0xffc00001,0x7f800000,0xff800000,0x80000000):
  player('NaN-infinite-HP',hp_word=word)
 player('NaN-now',steps=(((0x7fc00001,),.1),))
 for age in(1.199999,1.2,1.200001,2):
  for mode in(0,1,2,255):
   for peer in(0,7):corpse('corpse-age-owner',[1,1,1],[10-age]*3,[0,7,8],mode=mode,peer=peer)
 corpse('stable-all-same-guid-removal',[1,1,1,1],[8,10,8,10],[0]*4,guids=[99,2,99,3])
 corpse('corpse-NaN-clock',[1],[float('nan')],[0])
 return json.loads(json.dumps(rows))


def compare(cases,results):
 assert [r['id']for r in results]==list(range(len(cases)));diff=[]
 for c,r in zip(cases,results):
  e=c['expected'];a=r['result']
  if c['kind']=='corpse':
   if e!=a:diff.append((c['id'],'corpse',e,a))
  else:
   diff.extend((c['id'],*x)for x in differences(e,a))
 return diff


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_HASH
 cases=corpus(args.phase=='pilot');guards=[]
 baseline=from_dict(cases[0]['input'])
 for name,call in [('default-source-guard',lambda:prepare_player_update(baseline,(),(),f.from_float(10),f.from_float(.1),0)),('nonfinite-dt',lambda:prepare_player_update(baseline,(),(),f.from_float(10),0x7fc00001,0,explicit_other_sources_absent=True)),('periodic-source',lambda:prepare_player_update(baseline,(),(),f.from_float(10),f.from_float(.1),0,explicit_other_sources_absent=True,periodic_input=(1,))),('corpse-default-source-guard',lambda:cleanup_ordinary_corpses((),0,mode=0,local_peer=0)),('missing-periodic-snapshot',lambda:prepare_player_update(baseline,(),(),f.from_float(10),f.from_float(.1),0,explicit_other_sources_absent=True))]:
  try:call()
  except(UnresolvedPlayerUpdate135,ValueError)as exc:guards.append(dict(name=name,error=str(exc)))
  else:raise AssertionError('Unknown accepted:'+name)
 out,manifest=build(['player_tick','update_units']);snap=out/'source-snapshot';snap.mkdir()
 for n,h in before.items():
  target=snap/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
 fixture=out/'player-update135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
 results=out/'player-update135-results.jsonl';stderr=out/'player-update135-stderr.log';assert sha(RUNTIME)==RUNTIME_SHA
 fixed={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_player_update135_oracle.mjs'),str(out),str(fixture)];started=time.monotonic()
 with results.open('w')as stdout,stderr.open('w')as err:
  child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned player update deadline')
 if code:raise RuntimeError(f'Original player failed: {out}')
 actual=[json.loads(x)for x in results.read_text().splitlines()];failures=compare(cases,actual);(out/'player-update135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
 after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and fixed=={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),rejection_guards=guards,groups=dict(Counter(c['group']for c in cases)),steps=sum(len(c.get('steps',[0]))for c in cases),mismatch_fields=len(failures),source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),artifacts={p.name:sha(p)for p in(fixture,results,stderr,out/'player-update135-mismatches.json',out/'player-update135-runtime.json')},expected_before_original=True,only_changed_section=7,runtime=json.loads((out/'player-update135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-started),limitations=['Explicit empty non-live sources; finite dt; no periodic budget; live7/8/9/12 only; special11426 rejected.','Full2088 invokes real1076 with genuine racial80 infinity remaining and empty learned80; this isolates prefix, not opening schedule.','Raw live32 and corpse424 compared without masks; numeric derived/HP/pools/keys22,28,1109/RNG/sequence compared; physical message/account payload pending.'])
 (out/'player-update135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_fields=len(failures),first_failures=failures[:8]),indent=2))
 if failures:raise SystemExit(1)

if __name__=='__main__':main()
