#!/usr/bin/env python3
"""Expected-first helper21455/full2244/full922/full1076 demo differential."""
from pathlib import Path
from dataclasses import asdict,replace
from collections import Counter
import argparse,ast,hashlib,json,math,os,random,re,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 with Path(p).open('rb')as s:return hashlib.file_digest(s,'sha256').hexdigest()
def files():
 bases=(ROOT/'scripts',ROOT/'reconstruction');pending=[Path(__file__).resolve(),ROOT/'scripts/run_demo_shout135_oracle.mjs'];seen=set()
 def resolve(module):
  for base in bases:
   p=base/Path(*module.split('.'))
   for child in(p.with_suffix('.py'),p/'__init__.py'):
    if child.is_file():return child
 while pending:
  p=pending.pop();name=str(p.relative_to(ROOT))
  if name in seen:continue
  seen.add(name);base=next(b for b in bases if p.is_relative_to(b));parts=list(p.relative_to(base).with_suffix('').parts[:-1]);targets=[]
  if p.suffix=='.mjs':targets=[(p.parent/n).resolve()for n in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",p.read_text())]
  else:
   for node in ast.walk(ast.parse(p.read_text())):
    modules=[]
    if isinstance(node,ast.Import):modules=[a.name for a in node.names]
    elif isinstance(node,ast.ImportFrom):
     prefix='.'.join(parts[:len(parts)-node.level+1])if node.level else'';module='.'.join(v for v in(prefix,node.module or'')if v);modules=[module]+[module+'.'+a.name for a in node.names]
    targets.extend(child for m in modules if m and(child:=resolve(m))is not None)
  for child in targets:
   pending.append(child);base=next(b for b in bases if child.is_relative_to(b))
   for parent in child.parents:
    if parent==base:break
    if(parent/'__init__.py').is_file():pending.append(parent/'__init__.py')
 return sorted(seen)
FILES=files();BEFORE={n:sha(ROOT/n)for n in FILES}
from build_demo_shout135_oracle import build_demo,source_definition,missing,save
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.combat135 import UnitState,CombatState
from core_spec.cast135 import CastDefinition,CastState,SpatialUnit,UnresolvedCast
from core_spec.owned_cast135 import OwnedEntry135,OwnedSources135
from core_spec.demo_shout135 import (DemoDebuff135,DemoShoutOwnedEntry135,merge_demo_debuff21455,
    apply_demo_effect135,cast_demo_shout135,tick_owned_demo_shout135)
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
MODEL665=ROOT/'evidence/opening-event135-model-boundary-20261101T201809.896133Z'
def bits(x):return f.from_float(x)
def put(row,o,v):row[o:o+4]=struct.pack('<I',v&f.MASK)
def read(row,o):return int.from_bytes(bytes(row[o:o+4]),'little')
def definition(d):return CastDefinition(**{**{k:v for k,v in d.items()if k!='definition_hex'},'ability_id':d['ability_id'].encode()})
def unit(guid=1,x=1,y=0,*,marker=0,words=(0,0,0,0),spell=0,duration=0,auras=(0,)*16,phase_until=0,moving=False):
 row=list(bytes(424))
 for o,v in((0,marker),(40,f.MASK),(64,f.MASK),(244,f.MASK),(284,5415572),(288,bits(1000000)),(292,bits(1000000)),(316,bits(x-3)if moving else bits(x)),(320,bits(y)),(328,bits(x)),(332,bits(y)),(340,bits(5)),(344,bits(10)if moving else 0),(360,spell),(364,duration),(408,phase_until),(416,0),(236,4),(240,0)):put(row,o,v)
 row[112:120]=struct.pack('<Q',guid)
 for j,v in enumerate(words):put(row,128+j*4,v)
 for j,v in enumerate(auras):put(row,168+j*4,v)
 for lo,hi in((4,8),(32,40),(68,109)):row[lo:hi]=[None]*(hi-lo)
 return row
def debuffs(rows):
 return tuple(DemoDebuff135(int.from_bytes(bytes(r[112:120]),'little'),read(r,0),tuple(read(r,128+j*4)for j in range(4)),read(r,360),read(r,364),tuple(read(r,168+j*4)for j in range(16)),read(r,240))for r in rows)
def state(s,rows):
 units=[];spatial=[]
 for row in rows:
  u=UnitState(int.from_bytes(bytes(row[112:120]),'little'),read(row,288),read(row,292),marker=read(row,0),kind_40=-1,linked_id_32=None,kind_64=-1,elite_244=-1,elite_416=read(row,416),phase_until_408_bits=read(row,408),phase_until_412_bits=read(row,412),movement_duration_344_bits=read(row,344),movement_time_340_bits=read(row,340),death_time_4_bits=None)
  units.append(u);spatial.append(SpatialUnit(u,(read(row,316),read(row,320)),(read(row,328),read(row,332)),read(row,372)))
 return CastState(CombatState(tuple(units),now_bits=s['now_bits'],phase_2579=s['phase']),tuple(spatial),tuple(s['player_xy']),tuple(s['rng_words']),s['damage_multiplier_bits'],s['max_hp_bits'],s['critical_chance_bits'],s['critical_multiplier_bits'],s['area_multiplier_bits'],s['cooldown_multiplier_bits'],s['extra_targets'],int(s['source_id']),int(s['current_target_id']),s['context908'],())
def corpus(full):
 defs=source_definition();demo=definition(defs['demo_shout']);basic=definition(defs['fireball']);cases=[];expected=[];labels=[];rng=random.Random(0x135116021455)
 def merge(group,words,ops):
  current=tuple(words);want=[]
  for op in ops:current=merge_demo_debuff21455(current,**op);want.append(dict(words=list(current)))
  cases.append(dict(id=len(cases),mode='merge',words=list(words),ops=ops));expected.append(want);labels.append(dict(id=len(labels),group=group))
 def op(s=.35,e=16,t=10):return dict(strength_bits=bits(s),deadline_bits=bits(e),now_bits=bits(t))
 merge('expired_promote_and_stronger_shorter_fallback',tuple(map(bits,(.5,5,.2,30))),[op(.35,16),op(.1,40),op(.4,20,17)])
 merge('weaker_longer_then_equal_extend_tie',tuple(map(bits,(.5,20,.2,30))),[op(.35,40),op(.35,45),op(.35,45)])
 if full:
  states=[(0,0,0,0),(.5,20,.2,30),(.5,5,.2,30),(.2,20,.5,40),(-.1,20,.3,40),(.5,10,.2,10)]
  for words in states:
   for j,strength in enumerate((-.1,0,.2,.35,.5,.9,1,2)):merge('primary_backup_candidate_strict_ties',tuple(map(bits,words)),[op(strength,(5,10,15,20,30,40,45,50)[j])])
  for j in range(64):
   words=[bits(rng.choice((-.1,0,.1,.35,.5,.9,1,2)))if k%2==0 else bits(rng.choice((-5,0,5,10,15,20,30,40)))for k in range(4)]
   merge('random_nonmonotonic_expiry_strength_pairs',words,[op(rng.choice((-.1,0,.1,.35,.5,.9,1,2)),rng.choice((-5,0,5,10,15,20,30,40)),rng.choice((0,10,20)))])
  for j,v in enumerate((0x80000000,f.INF,0xff800000,0x7fc00000)):
   for pos in range(4):
    words=list(map(bits,(.5,20,.2,30)));words[pos]=v;merge('ordered_compare_signed0_infinity_NaN',words,[op(.35,40)])
 def add(group,*,mode='cast',rows=None,ops=None,record=None,overrides=None,class_byte=1,timer=f.INF):
  rows=[unit(j+1,1+j*3)for j in range(3)]if rows is None else rows;s=dict(now_bits=bits(10),phase=1,player_xy=[0,0],rng_words=[1,2,3,4],damage_multiplier_bits=bits(1),max_hp_bits=bits(300),current_hp_bits=bits(50),critical_chance_bits=bits(.2),critical_multiplier_bits=bits(2),area_multiplier_bits=bits(1),cooldown_multiplier_bits=bits(1),extra_targets=0,source_id='42',current_target_id='0',context908=0);s.update(overrides or{})
  owned=record or AbilityRecord(demo.pointer,remaining_cooldown_bits=0);base=AbilityRecord(basic.pointer,remaining_cooldown_bits=f.INF);entry=DemoShoutOwnedEntry135(demo,owned);basicentry=OwnedEntry135(basic,base);st=state(s,rows);owners=debuffs(rows);packets=[];want=[];physical=[r.copy()for r in rows];details=[];now=s['now_bits'];countdown=timer
  player_hp=s['current_hp_bits'];player_fields={}
  def after_hit(cast,damage):
   nonlocal player_hp
   coefficient=defs['class_leech_bits'][str(class_byte)]
   if f.to_float(coefficient)>0:
    total=f.add(player_hp,f.mul(damage.damage_bits,coefficient));maximum=s['max_hp_bits'];first=maximum if f.is_nan(total)else total;second=first if f.is_nan(maximum)else maximum
    player_hp=first if f.to_float(second)>f.to_float(first)else second
    player_fields.update({'22':max(0,math.ceil(f.to_float(player_hp))),'28':max(0,math.ceil(f.to_float(maximum)))})
   return cast
  if ops is None:ops=[dict(kind=mode,now_bits=bits(10))]
  for operation in ops:
   operation=dict(operation);now=operation['now_bits'];st=replace(st,combat=replace(st.combat,now_bits=now));success=None;writes=();actions=();newpackets=()
   if operation['kind']=='effect':
    result=apply_demo_effect135(owners,int(operation['target_guid']),operation['strength_bits'],operation['duration_bits'],now,operation['spell_id']);owners=result.debuffs;writes=result.writes;actions=result.aura_actions;newpackets=result.aura_packets
   elif operation['kind']=='cast':
    result=cast_demo_shout135(st,demo,entry.record,debuffs=owners,after_hit=after_hit);st=result.state;owners=result.debuffs;writes=result.effect_writes;actions=result.aura_actions;newpackets=result.aura_packets;success=result.success
   elif operation['kind']=='owned':
    result=tick_owned_demo_shout135(st,(entry,),basicentry,operation['dt_bits'],debuffs=owners,sources=OwnedSources135((),(),True),class_byte=class_byte,timer1628_bits=countdown,after_hit=after_hit);st=result.owned_tick.state;entry=result.owned_tick.entries[0];basicentry=result.owned_tick.basic;countdown=result.owned_tick.prelude.timer1628_bits;owners=result.debuffs;writes=result.effect_writes;actions=result.aura_actions;newpackets=result.aura_packets
   else:raise ValueError('Operation')
   for j,u in enumerate(st.combat.units):put(physical[j],288,u.hp_bits);put(physical[j],0,u.marker)
   for index,guid,offset,value in writes:assert owners[index].guid==guid;put(physical[index],offset,value)
   packets.extend(dict(opcode=code,payload_hex=data)for code,data in newpackets)
   ownerdict=[{**asdict(row),'guid':str(row.guid),'words128_140':list(row.words128_140),'aura_slots168':list(row.aura_slots168)}for row in owners]
   projection=dict(hp_bits=[u.hp_bits for u in st.combat.units],markers=[u.marker for u in st.combat.units],rng_words=list(st.rng_words),accounted_total_hex=struct.pack('>d',st.combat.accounted_total).hex(),attempted_spell_sets=[list(st.attempted_spell_ids)]*3,owned_words=list(entry.record.words()),basic_words=list(basicentry.record.words()),current_hp_bits=player_hp,player_fields=dict(player_fields),timer1628_bits=countdown,debuffs=ownerdict,aura_packets=list(packets))
   want.append(dict(kind=operation['kind'],**({}if success is None else dict(success=success)),projection=projection,unit_cells=[r.copy()for r in physical]));details.append(dict(writes=writes,aura_actions=actions,selected=getattr(result,'selected_ids',()),numeric_effect_only_AI_not_run=True))
  cases.append(dict(id=len(cases),mode=mode,input=s,units424=rows,class_byte=class_byte,timer1628_bits=timer,unknown_poison=(0xa5,0x5a)[len(cases)%2],definition=defs['demo_shout'],basic_definition=defs['fireball'],owned_hex=owned.to_bytes().hex(),basic_hex=base.to_bytes().hex(),ops=ops));expected.append(want);labels.append(dict(id=len(labels),group=group,operations=details))
 def eff(t=10,s=.35,d=6,guid=1,spell=1160):return dict(kind='effect',now_bits=bits(t),strength_bits=bits(s),duration_bits=bits(d),target_guid=str(guid),spell_id=spell)
 add('first_Aura_and_same_spell_refresh',mode='effect',rows=[unit()],ops=[eff(),eff(t=11)])
 add('empty_target_full922',rows=[])
 add('full922_damage_then_21455_then_Aura',ops=[dict(kind='cast',now_bits=bits(10)),dict(kind='cast',now_bits=bits(11))])
 add('full1076_held_warrior_prelude_and_retry',mode='owned',ops=[dict(kind='owned',now_bits=bits(t),dt_bits=bits(dt))for t,dt in((10.1,.1),(10.5,.4),(25,14.5))])
 if full:
  add('first_live_duplicate_GUID_not_dead_first',mode='effect',rows=[unit(marker=1),unit()],ops=[eff()])
  add('missing_GUID_and_marker2_2244_is_not_31732',mode='effect',rows=[unit(marker=2)],ops=[eff(guid=99),eff()])
  for spell,slots in((777,(777,)+(0,)*15),(777,(777,1160)+(0,)*14),(0,tuple(range(100,116))),(777,(777,777)+(0,)*14),(1160,(0,)*16)):
   add('Aura_remove_add_existing_and_full16',mode='effect',rows=[unit(spell=spell,auras=slots)],ops=[eff()])
  add('spell0_does_not_touch_Aura_or_spell360',mode='effect',rows=[unit(spell=777,auras=(777,)+(0,)*15)],ops=[eff(spell=0)])
  for words in((.5,20,.2,30),(.2,20,.5,40),(.5,5,.2,30)):
   add('2244_primary_acceptance_controls_duration364',mode='effect',rows=[unit(words=tuple(map(bits,words)),duration=bits(99))],ops=[eff(s=.35,d=6),eff(t=12,s=.1,d=40),eff(t=30,s=.5,d=10)])
  for n in(1,8,16):add('full922_target_count',rows=[unit(j+1,(j%7)-3,j//7)for j in range(n)])
  for x in(0x415fffff,0x41600000,0x41600001,0xc1600000):
   row=unit();put(row,316,x);put(row,328,x);add('radius14_exact_boundary',rows=[row])
  for phase in(0,2,3):add('effect_even_when914_phase_rejects_damage',overrides=dict(phase=phase))
  for strength in(-1,0,.5,1,2,5):add('owned76_effect_strength_and_point9_cap',record=replace(AbilityRecord(demo.pointer),field76_bits=bits(strength)))
  for duration in(-1,0,.5,2,5):add('owned68_duration_and_unread_owned28',record=replace(AbilityRecord(demo.pointer),additional_duration_bits=bits(duration),duration_bits=0x7fc00000))
  for j in range(8):add('moving_targets_and_shared_crit_rng',rows=[unit(k+1,rng.uniform(-16,16),rng.uniform(-5,5),moving=True)for k in range(1+j%6)],overrides=dict(rng_words=[rng.getrandbits(32)for _ in range(4)],critical_chance_bits=bits((0,.3,1)[j%3])),record=replace(AbilityRecord(demo.pointer),area_bits=bits((.5,1,3)[j%3]),additional_duration_bits=bits((.5,1,2)[j%3])))
  for cooldown in(0,bits(.5),f.INF,0x7fc00000):add('1076_cooldown_finite_infinite_NaN',mode='owned',record=replace(AbilityRecord(demo.pointer),remaining_cooldown_bits=cooldown),ops=[dict(kind='owned',now_bits=bits(t),dt_bits=bits(dt))for t,dt in((10.1,.1),(10.5,.4),(25,14.5))])
  add('1076_no_target_retry_point2',mode='owned',rows=[],ops=[dict(kind='owned',now_bits=bits(t),dt_bits=bits(.1))for t in(10.1,10.2,10.3)])
  model=json.loads((MODEL665/'final-state.json').read_text());receipt=json.loads((MODEL665/'receipt.json').read_text());assert sha(MODEL665/'final-state.json')==receipt['final_state_sha256']=='127bcb3ed7f2b2e6996fd961a599162f5a75caaa94b6e52763173f4d5aed1449'and receipt['frames']==665 and receipt['selections']==6 and receipt['new_original_cases']==0 and not receipt['original_wasm_executed'];copied=AbilityRecord.from_bytes(bytes.fromhex(model['owned_records_hex'][-1]));assert copied.definition_pointer==demo.pointer and copied.level==1;d=model['derived_bits'];now=model['now_bits']
  add('independent665_selected_demo_numeric_fragment_controlled_NPCs',mode='owned',record=copied,overrides=dict(now_bits=now,max_hp_bits=d['1536'],current_hp_bits=model['current_hp_bits'],damage_multiplier_bits=d['1540'],critical_chance_bits=d['1548'],critical_multiplier_bits=d['1552'],area_multiplier_bits=d['1580'],cooldown_multiplier_bits=d['1544'],extra_targets=d['1592'],rng_words=model['rng_words'],fixture_derived23=d),ops=[dict(kind='owned',now_bits=f.add(now,bits(offset)),dt_bits=bits(dt))for offset,dt in((.1,.1),(.5,.4),(15,14.5))])
  cases[-1]['independent_model_fragment']=dict(final_state=str(MODEL665/'final-state.json'),final_state_sha256=sha(MODEL665/'final-state.json'),receipt=str(MODEL665/'receipt.json'),receipt_sha256=sha(MODEL665/'receipt.json'),copied=['selected_demo_owned80','23derived','playerHP','RNG','now'],not_copied=['records424/None','world','otherlearnedskills','racial','liveeffects','playerworldcoordinates'],controlled_remap='Three manual ordinary NPCs near localXY0,mode1,emptyother/proc sources,heldinfinityclassprelude; no natural665original claim')
 assert len(cases)<=256
 return json.loads(json.dumps(cases,allow_nan=False)),json.loads(json.dumps(expected,allow_nan=False)),json.loads(json.dumps(labels,allow_nan=False))
def compare(expected,actual):
 errors=[];counts=Counter()
 def walk(a,b,path):
  if a is None:assert '.unit_cells['in path and type(b)is int and 0<=b<=255;counts['unknown_physical_bytes']+=1;counts['nonzero_unknown_original_bytes']+=bool(b);return
  if type(a)is not type(b):errors.append(dict(path=path,expected=a,actual=b));return
  if isinstance(a,dict):
   if set(a)!=set(b):errors.append(dict(path=path,expected_keys=sorted(a),actual_keys=sorted(b)));return
   for k in a:walk(a[k],b[k],path+'.'+k)
  elif isinstance(a,list):
   if len(a)!=len(b):errors.append(dict(path=path,expected_length=len(a),actual_length=len(b)));return
   for j,(x,y)in enumerate(zip(a,b)):walk(x,y,path+'['+str(j)+']')
  else:
   counts['known_values']+=1
   if a!=b and not('.words['in path and type(a)is int and f.is_nan(a)and f.is_nan(b)):errors.append(dict(path=path,expected=a,actual=b))
 for i,(want,got)in enumerate(zip(expected,actual)):
  assert got['id']==i and len(want)==len(got['stages'])
  for j,(w,a)in enumerate(zip(want,got['stages'])):
   if 'words'in w:converted=dict(words=a['words'])
   else:converted={key:a[key]for key in w if key!='unit_cells'};converted['unit_cells']=[list(bytes.fromhex(x))for x in a['raw_units424_hex']]
   walk(w,converted,'case'+str(i)+'.stage'+str(j))
 return errors,counts
def main():
 args=argparse.ArgumentParser();args.add_argument('--phase',choices=('pilot','full'),default='pilot');args.add_argument('--prepare-only',action='store_true');opt=args.parse_args();assert BEFORE=={n:sha(ROOT/n)for n in FILES};cases,expected,labels=corpus(opt.phase=='full');out,manifest=build_demo();refusals=[];defs=manifest['definitions'];demo=definition(defs['demo_shout'])
 try:OwnedEntry135(demo,AbilityRecord(demo.pointer))
 except UnresolvedCast:refusals.append('shared_old_owned_gate_still_rejects_demo')
 else:raise AssertionError('Shared gate changed')
 row=replace(debuffs([unit()])[0],ability_count240=1)
 try:apply_demo_effect135((row,),1,bits(.35),bits(6),bits(10),1160)
 except UnresolvedCast:refusals.append('nonempty44B_NPC_15511_owner_pending')
 else:raise AssertionError('Unknown NPC owner accepted')
 try:merge_demo_debuff21455((None,0,0,0),bits(.35),bits(16),bits(10))
 except ValueError:refusals.append('unknown_debuff_read_not_zero_filled')
 else:raise AssertionError('Unknown primary read accepted')
 for name,h in BEFORE.items():
  p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 inputfile=out/'input.jsonl';inputfile.write_text(''.join(json.dumps(c,ensure_ascii=False,allow_nan=False)+'\n'for c in cases));save(out/'expected.json',expected);save(out/'labels.json',labels);save(out/'pure-refusals.json',refusals);assert inputfile.stat().st_size<4194304 and(out/'expected.json').stat().st_size<4194304
 artifacts={n:sha(out/n)for n in('input.jsonl','expected.json','labels.json','pure-refusals.json','manifest.json',manifest['module_file'])};external={str(p):sha(p)for p in(MODEL665/'final-state.json',MODEL665/'receipt.json')}if opt.phase=='full'else{};command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_demo_shout135_oracle.mjs'),str(out),str(inputfile)];save(out/'prepared.json',dict(source_sha256=BEFORE,artifacts=artifacts,external_independent_model_fragments=external,expected_before_original=True,command=command,cases=len(cases),deadline_seconds=60));assert sha(NODE)==NODE_SHA and BEFORE=={n:sha(ROOT/n)for n in FILES}
 if opt.prepare_only:print(json.dumps(dict(directory=str(out),cases=len(cases),original_executed=False)));return
 started=time.monotonic();error=None
 with(out/'results.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'));save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
  try:child.wait(timeout=60)
  except Exception as exc:error=repr(exc)
  finally:
   try:os.killpg(child.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:child.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,error=error,seconds=time.monotonic()-started,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'process-terminal.json',terminal);actual=[json.loads(x)for x in(out/'results.jsonl').read_text().splitlines()];runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None;complete=child.returncode==0 and len(actual)==len(cases);errors,counts=compare(expected,actual)if complete else([],{});save(out/'differences.json',errors);after={n:sha(ROOT/n)for n in FILES}
 report=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',status='compared'if complete else'original_failed_or_incomplete',cases=len(cases),stages=sum(map(len,expected)),comparison_complete=complete,differences=len(errors)if complete else None,comparison=dict(counts),groups=dict(Counter(l['group']for l in labels)),source_files=len(FILES),source_sha256_before=BEFORE,source_sha256_after=after,source_unchanged=BEFORE==after,artifacts=artifacts,artifacts_unchanged=all(sha(out/n)==h for n,h in artifacts.items()),external_independent_model_fragments=external,external_fragments_unchanged=all(sha(Path(p))==h for p,h in external.items()),pure_model_refusals=refusals,runtime=runtime,process=terminal,original_snapshot_inputs=False,full880_frames=0,natural665_frame_runs=0,scope='Helper21455/full2244/full922/full1076 numeric+emptyU240 Aura169 component; controlled Game8192/424B owners, noAI/boot/world/game constructor',pending=['AI360 expiry/Aura cleanup/attack scheduling integration','Nonempty44B NPC ability15511 owner/count semantics','922 nonempty effect49/proc/death continuation','All nonAura wire/accounting and fullGame ownership','Natural665+mainloop/full880/native/fullgame'])
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),receipt_sha256=sha(out/'comparison.json'),cases=len(cases),stages=report['stages'],differences=report['differences'],first_errors=errors[:6],process=terminal)),flush=True)
 if not complete or errors or error or not terminal['pid_missing']or not terminal['pgid_missing']or BEFORE!=after or not report['artifacts_unchanged']or not report['external_fragments_unchanged']:raise SystemExit(1)
 assert runtime['actual_host_calls']==0 and runtime['stack_all_restored']and runtime['completed_cases']==len(cases)
if __name__=='__main__':main()
