#!/usr/bin/env python3
"""Complete922 six-racial self-buff differential; actual G1256 owned record."""
from collections import Counter
from dataclasses import asdict,replace
import argparse,json,os,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
from check_level_cycle135 import make_input,empty_sources,SOURCE_FILES as LEVEL_FILES,RUNTIME,RUNTIME_SHA
from check_cast135_full_spec import inputs,unit,state_from_input,SOURCE_FILES as CAST_FILES
FILES=tuple(dict.fromkeys((*LEVEL_FILES,*CAST_FILES,'scripts/check_racial_cast135.py','scripts/run_racial_cast135_oracle.mjs',
 'reconstruction/core_spec/racial_cast135.py','reconstruction/core_spec/__init__.py','reports/2026-11-01-catalogue0135.json','scripts/trace_racial_cast135.py')))
IMPORT_HASH={n:sha(ROOT/n)for n in FILES}
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.level_cycle135 import from_dict
from core_spec.racial_cast135 import RacialDefinition135,RACIALS,cast_self_buff


def definitions():
 x=json.loads((ROOT/'reports/2026-11-01-catalogue0135.json').read_text());rows={r['identifier']:r for r in x['abilities']}
 return {aid:RacialDefinition135(pointer,aid,rows[aid.decode()]['record_raw_hex'])for aid,(pointer,tag,spell)in RACIALS.items()}


def corpus(pilot=False):
 cases=[];b=f.from_float
 def add(aid,group='base-six-racials',hp=.3,cls=1,race=1,live=(),owned_changes=None,busy=0,context=0,sources=None,enemy_distance=1):
  definition=definitions()[aid];raw_records=tuple(struct.pack('<8I',*r).hex()for r in live);src=empty_sources()if sources is None else sources
  src=dict(src,live_effects=[dict(kind=r[2],value_bits=0 if r[2]==12 else r[3],spell_id=r[5],expires_bits=r[6])for r in live])
  raw=make_input(class_byte=cls,race_byte=race,level=1,phase=1,mode=0,hp_fraction=hp,sources=src,owned=())
  level=from_dict(raw);d=dict(level.derived_bits);s=inputs([]if enemy_distance is None else[unit(2,enemy_distance)],source_id='1',now_bits=level.stats.now_bits,rng_words=list(level.rng_words),context908=context,
   max_hp_bits=d[1536],current_hp_bits=level.stats.current_hp_bits,damage_multiplier_bits=d[1540],cooldown_multiplier_bits=d[1544],
   critical_chance_bits=d[1548],critical_multiplier_bits=d[1552],area_multiplier_bits=d[1580],extra_targets=d[1592])
  cast=state_from_input(s);owned=AbilityRecord(definition.pointer)
  if owned_changes:owned=replace(owned,**owned_changes)
  result=cast_self_buff(cast,level,definition,owned,live_records=raw_records,busy488=busy,attempted_spell_sets=((),(),()))
  l=result.level;expected=dict(success=result.success,live_records=result.live_records,derived_bits=dict(l.derived_bits),current_hp_bits=l.stats.current_hp_bits,
   auxiliary_bits={1444:l.stats.pool1532_bits,1448:l.stats.pool1536_bits,1348:l.stats.conditional1348_bits,768:l.stats.pool768_bits,756:l.pool756_bits},
   shield_source=l.stats.conditional1344_id,speed_bits=l.stats.previous_speed_bits,player_fields={k:v for k,v in l.player_fields if k in(22,28,1109)},
   rng_words=result.cast.rng_words,owned_hex=owned.to_bytes().hex(),attempted_spell_sets=result.attempted_spell_sets)
  dd=asdict(definition);dd['ability_id']=aid.decode();cases.append(dict(id=len(cases),group=group,input=raw,cast=s,definition=dd,owned_hex=owned.to_bytes().hex(),busy488=busy,
   live_records=raw_records,expected=expected,unspecified_live_words=result.unspecified_live_words,callbacks=result.callbacks))
 for aid in RACIALS:add(aid)
 if pilot:return json.loads(json.dumps(cases,allow_nan=False))
 for aid,(pointer,tag,spell)in RACIALS.items():
  for hp in(0,.3499999,.35,.3500001,.8,1):add(aid,'hp-activation-boundaries',hp=hp)
  for cls in(1,2,3,4,5,7,8,9,11):
   for race in(1,2,3,4,5,6,7,8):add(aid,'class-race-stat-rebuild',cls=cls,race=race)
  for busy,context in((1,0),(0,1),(0,2),(0,3)):add(aid,'entry-gates',busy=busy,context=context)
  for expiry in(9,10,11):
   for owner in(0,123):
    row=(owner,0,tag,b(.5),0x12345678,spell,b(expiry),0xabcdef01)
    other=(0,0,8,b(.1),0,999,b(30),0)
    add(aid,'same-spell-owner-expiry-order',live=(row,other,row))
  for expiry in(9,10,11):add(aid,'existing-protection12',live=((0,0,12,0xa5a5a5a5,0x5a5a5a5a,1020,b(expiry),0),))
  for duration in(-1,0,.001,.5,2):
   for magnitude in(-.2,0,.5,2):add(aid,'owned-duration-magnitude',owned_changes=dict(duration_bits=b(duration),additional_duration_bits=b(.7),field76_bits=b(magnitude),damage_bits=b(1.7),additional_damage_bits=b(1.2)))
  for cd in(0,.5,10):add(aid,'direct922-does-not-own-cooldown',owned_changes=dict(remaining_cooldown_bits=b(cd)))
  for distance in(None,29.999,30,30.001,50):add(aid,'target30-activation-guard',enemy_distance=distance)
 return json.loads(json.dumps(cases,allow_nan=False))


def compare(cases,rows):
 assert [r['id']for r in rows]==list(range(len(cases)));failures=[]
 for c,r in zip(cases,rows):
  e=c['expected'];a=r['result'];assert e.keys()==a.keys()
  for k,v in e.items():
   if k=='live_records':
    if len(v)!=len(a[k]):failures.append((c['id'],k,len(v),len(a[k])));continue
    unknown=set(tuple(x)for x in c['unspecified_live_words'])
    for j,(left,right)in enumerate(zip(v,a[k])):
     for n,(x,y)in enumerate(zip(struct.unpack('<8I',bytes.fromhex(left)),struct.unpack('<8I',bytes.fromhex(right)))):
      if (j,n*4)not in unknown and x!=y:failures.append((c['id'],f'live{j}+{n*4}',x,y))
   elif v!=a[k]:failures.append((c['id'],k,v,a[k]))
 return failures


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_HASH
 cases=corpus(args.phase=='pilot');out,manifest=build(['cast']);snap=out/'source-snapshot';snap.mkdir()
 for n,h in before.items():
  target=snap/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
 fixture=out/'racial-cast135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
 results=out/'racial-cast135-results.jsonl';stderr=out/'racial-cast135-stderr.log';assert sha(RUNTIME)==RUNTIME_SHA
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_racial_cast135_oracle.mjs'),str(out),str(fixture)];started=time.monotonic()
 with results.open('w')as stdout,stderr.open('w')as err:
  child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned racial deadline')
 if code:raise RuntimeError(f'Original racial failed: {out}')
 rows=[json.loads(x)for x in results.read_text().splitlines()];failures=compare(cases,rows);(out/'racial-cast135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
 after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),groups=dict(Counter(c['group']for c in cases)),successful=sum(c['expected']['success']for c in cases),mismatch_fields=len(failures),
  source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
  artifacts={p.name:sha(p)for p in(fixture,results,stderr,out/'racial-cast135-mismatches.json',out/'racial-cast135-runtime.json')},expected_before_original=True,only_changed_section=7,
  runtime=json.loads((out/'racial-cast135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-started),
  unknown_words='Only newly appended effect7/8/9 +16 from unwritten stack scratch; retained old words strict. Type12 value12/aux16 are explicitly copied from definition.',
  limitations=['Six fixedracial kind9 definitions and explicitly resolved source snapshots only.','Stat keys22/28/1109 and numeric derived/HP/pools are compared;1202 aura/display keyed fields and packet payloads remain pending.','Direct922 ignores cooldown; actualG1256 initialization/8157 scheduling belongs to separate producer validation.'])
 (out/'racial-cast135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_fields=len(failures),first_failures=failures[:12]),indent=2))
 if failures:raise SystemExit(1)


if __name__=='__main__':main()
