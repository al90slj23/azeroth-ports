#!/usr/bin/env python3
"""Expected-first physical live backing922/4600/1072; no headless dependency."""
from pathlib import Path
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_live_owner135_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.derived_stats135 import StatsInput,recalculate
from core_spec.level_cycle135 import from_dict
from core_spec.candidates135 import Candidate
from core_spec.cast135 import CastState,SpatialUnit
from core_spec.combat135 import CombatState,UnitState
from core_spec.battle_shout135 import BattleShoutDefinition135,cast_battle_shout135
from core_spec.racial_cast135 import RacialDefinition135,cast_self_buff
from core_spec.cast_catalogue135 import RAW_BY_POINTER
from core_spec.live_owner135 import (LiveVector135,live_semantics135,live_active_view135,resume_live1020_135,append_live135,retain_live135,ScratchAuxiliaryWord135)
from core_spec.currency134 import CurrencyState
from core_spec.selection_cycle135 import SelectionCycleState,select_card
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def raw_level(owner,mode,caster):
 semantic=live_semantics135(owner,allowed_kinds=(0,8,12));base=StatsInput(class_byte=1,race_byte=8 if caster=='berserking'else 1,level=1,now_bits=f.from_float(10),live_effects=list(semantic));initial=recalculate(base);d=initial['derived_bits'];hp=f.mul(d['1536'],f.from_float(.3))
 return dict(progression=dict(level=1,xp=0,pending_upgrades=1 if mode=='select'else 0),stats=dict(class_byte=1,race_byte=8 if caster=='berserking'else 1,old_max_hp_bits=d['1536'],current_hp_bits=hp,now_bits=f.from_float(10),previous_speed_bits=initial['speed_bits'],conditional268_bits=0,flag2574=0,pool1532_bits=0,pool1536_bits=0,conditional1344_id=0,conditional1348_bits=0,pool768_bits=0),sources=dict(passives=[],adjustments=[],item_modifiers=[],owned_skills=[],timed_records=[],definitions=[],live_effects=[asdict(x)for x in semantic]),derived_bits=d,player_fields={},rng_words=[1,2,3,4],choice_inputs=dict(owned=[dict(ability_id=caster,record_hex=AbilityRecord(5477196 if caster=='berserking'else 5467956).to_bytes().hex())]if mode=='cast'else[],blocked_ids=[],banished_keys=[],flag275=0,flag2581=1),phase2587=1 if mode=='cast'else 2,selection_kind2585=0 if mode=='select'else 255,generation_counter2400=0,flags2576=0,gate2572=0,flags2573=0,heal_gate387=0,pool756_bits=0)

def row(kind,spell,*,owner=0,nullable=False,stamp=0):
 words=[owner&f.MASK,owner>>32,kind,f.from_float(.2)if kind==8 else 0x4a12abcd^stamp,0x5aa5a55a^stamp,spell,f.from_float(20),0];b=list(struct.pack('<8I',*words))
 if nullable:
  b[16:20]=[None]*4
  if kind in(0,12):b[12:16]=[None]*4
 return tuple(b)
def prediction(c):
 owner=LiveVector135(tuple(tuple(x)for x in c['physical_live']['storage']),c['physical_live']['count']);level=from_dict(c['level']);basic=c['basic_hex'];owned=[];success=None
 if c['mode']=='cast':
  d=dict(level.derived_bits);units=(UnitState(target_id=1,hp_bits=f.from_float(100),max_hp_bits=f.from_float(100)),)if c['target_present']else();spatial=tuple(SpatialUnit(u,(f.from_float(1),0),(f.from_float(1),0))for u in units)
  cast=CastState(CombatState(units,now_bits=level.stats.now_bits,phase_2579=level.phase2587),spatial,(0,0),level.rng_words,d[1540],d[1536],d[1548],d[1552],d[1580],d[1544],d[1592],42,1,0,())
  active,marks=live_active_view135(owner)
  scratch={'scratch_word16_source':ScratchAuxiliaryWord135(None)}if c.get('scratch_source_unresolved')else{'scratch_word16_bits':c['scratch_word16_bits']}
  if c['caster']=='battle_shout':result=cast_battle_shout135(cast,level,BattleShoutDefinition135(),AbilityRecord.from_bytes(bytes.fromhex(c['cast_owned_hex'])),live_records=active,unspecified_live_words=marks,explicit_other_sources_absent=True,physical_live=owner,**scratch)
  else:result=cast_self_buff(cast,level,RacialDefinition135(5477196,b'berserking',RAW_BY_POINTER[5477196]),AbilityRecord.from_bytes(bytes.fromhex(c['cast_owned_hex'])),live_records=active,unspecified_live_words=marks,physical_live=owner,**scratch)
  owner,level,success=result.physical_live,result.level,result.success;owned=[c['cast_owned_hex']]
 elif c['mode']=='resume':
  owner=resume_live1020_135(owner,level.stats.now_bits,resumption_explicit=True);level=replace(level,phase2587=1,selection_kind2585=255,flags2573=0,sources=replace(level.sources,live_effects=live_semantics135(owner,allowed_kinds=(0,8,12))))
 else:
  level=replace(level,candidates=(Candidate('new',1,'cleave'),));currency=CurrencyState(7,9,dict(level.derived_bits)[1588],0,0,0,0,(),0,())
  result=select_card(SelectionCycleState(level,0,0,(),0,0,currency,0,(),0),0,additional_modifiers=());assert result.accepted and result.status=='running';level=result.state.level;owner=resume_live1020_135(owner,level.stats.now_bits,resumption_explicit=True);assert live_semantics135(owner,allowed_kinds=(0,8,12))==level.sources.live_effects;owned=[x.record.to_bytes().hex()for x in level.choice_inputs.owned]
 keys={22,28,34,716,717,1109,1176}
 return dict(success=success,physical_live=dict(capacity=owner.capacity,count=owner.count,storage=owner.storage),derived_bits=dict(level.derived_bits),current_hp_bits=level.stats.current_hp_bits,speed_bits=level.stats.previous_speed_bits,player_fields={k:v for k,v in level.player_fields if k in keys},rng_words=level.rng_words,phase2587=level.phase2587,selection_kind2585=level.selection_kind2585,generation_counter2400=level.generation_counter2400,owned_records_hex=owned,cast_owned_hex=c['cast_owned_hex'],basic_hex=basic,action_sequence1644=9,message_sequence2412=19)

def corpus(full):
 cases=[];wanted=[];labels=[]
 def add(mode,pattern,slack,nullable=False,target=True,caster='battle_shout',opaque=False):
  active=[row(x[0],x[1],owner=x[2]if len(x)==3 else 0,nullable=nullable,stamp=j)for j,x in enumerate(pattern)];storage=active+[tuple((j*17+k*31+73)&255 for j in range(32))for k in range(slack)];owner=LiveVector135(tuple(storage),len(active));c=dict(id=len(cases),mode=mode,group=mode+'-'+('nullable'if nullable else'known')+'-'+str(len(active))+'-slack'+str(slack),physical_live=asdict(owner),level=raw_level(owner,mode,caster),caster=caster,cast_definition_pointer=5477196 if caster=='berserking'else 5467956,cast_definition88_hex=RAW_BY_POINTER[5477196 if caster=='berserking'else 5467956],cast_owned_hex=AbilityRecord(5477196 if caster=='berserking'else 5467956).to_bytes().hex(),basic_hex=AbilityRecord(5476580).to_bytes().hex(),target_present=target,unknown_poison=(0xa5,0x5a)[len(cases)&1],scratch_word16_bits=(0,0xa5a5a5a5,0x5a5a5a5a,0x4289add5)[len(cases)&3],scratch_source_unresolved=opaque);w=prediction(c);material=json.loads(json.dumps(c));material['physical_live']['storage']=[[c['unknown_poison']if x is None else x for x in row]for row in material['physical_live']['storage']];material['scratch_source_unresolved']=False;concrete=prediction(material)['physical_live'];cases.append(c);wanted.append(dict(id=c['id'],result=w,materialized_physical_live=concrete));labels.append(dict(id=c['id'],mode=mode,group=c['group'],initial_count=owner.count,initial_capacity=owner.capacity,initial_active_kinds=[x[0]for x in pattern],predicate='owner0+spell6673'if mode=='cast'else'all spell1020',target_present=target,scratch_word16_bits=c['scratch_word16_bits'],scratch_origin='Explicit controlled922 entry frame+48 input; natural caller producer pending'))
 mixed=((12,1020),(0,23451),(12,1020),(8,6673))
 add('cast',(),0);add('cast',mixed,2,True);add('resume',mixed,2,True);add('select',mixed,2,True);add('cast',mixed,2,True,caster='berserking')
 if full:
  patterns=((),((8,6673),),((0,23505),(12,1020)),mixed,((8,6673),(0,23451),(8,6673),(12,1020)),((0,23451),(8,6673),(0,23505),(12,1020)),((12,1020),(12,1020),(12,1020)),((8,6673,42),(0,23505),(12,1020)))
  for mode in('cast','resume','select'):
   for pattern in patterns:
    for slack in(0,2):
     for nullable in(False,True):add(mode,pattern,slack,nullable)
  for slack in(0,2):add('cast',mixed,slack,True,False)
  for slack in(0,2):add('cast',mixed,slack,False,caster='berserking')
  for caster in('battle_shout','berserking'):
   for slack in(0,2):add('cast',mixed,slack,False,caster=caster,opaque=True)
 #JSON interchange must be frozen before original execution.
 return json.loads(json.dumps(cases)),json.loads(json.dumps(wanted)),json.loads(json.dumps(labels))

def compare(w,a,path,counts,errors):
 if w is None:
  if path==('success',):
   assert a is None;counts['structural_null_success']+=1;return
  assert path[-4:-2]==('physical_live','storage')and type(a)is int and 0<=a<256;counts['explicit_unknown_bytes']+=1;return
 if type(w)is not type(a):errors.append(dict(path=path,expected=w,actual=a));return
 if isinstance(w,dict):
  if set(w)!=set(a):errors.append(dict(path=path,expected_keys=list(w),actual_keys=list(a)));return
  for k in w:compare(w[k],a[k],path+(k,),counts,errors)
 elif isinstance(w,list):
  if len(w)!=len(a):errors.append(dict(path=path,expected_length=len(w),actual_length=len(a)));return
  for j,(x,y)in enumerate(zip(w,a)):compare(x,y,path+(j,),counts,errors)
 else:
  counts['known_values']+=1
  if w!=a:errors.append(dict(path=path,expected=w,actual=a))

def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();scripts=('check_live_owner135.py','build_live_owner135_oracle.py','run_live_owner135_oracle.mjs','wasm135_profile.py','wasm134_profile.py','wasm_index.py','production_closure135.py','source_closure137.py');files=tuple('scripts/'+x for x in scripts)+production_sources135(ROOT,'core_spec.live_owner135','core_spec.battle_shout135','core_spec.selection_cycle135','core_spec.cast_catalogue135');assert not any('headless'in n for n in files);edges=verify_local_source_closure(files);before={n:sha(ROOT/n)for n in files};rows,wanted,labels=corpus(args.phase=='full');assert before=={n:sha(ROOT/n)for n in files}
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('live-owner135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
 for n,h in before.items():dest=out/'source-snapshot'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes());assert sha(dest)==h
 for n,v in(('input.json',rows),('expected.json',wanted),('labels.json',labels)):save(out/n,v)
 frozen={n:sha(out/n)for n in('input.json','expected.json','labels.json','manifest.json',m['module_file'],*(str(x)+'.wat'for x in(922,1072,4600,65320,1073,2088)))};assert all((out/n).stat().st_size<=4194304 for n in('input.json','expected.json'));command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_live_owner135_oracle.mjs'),str(out),str(out/'input.json')];save(out/'prepared.json',dict(source_before=before,artifacts=frozen,expected_before_original=True,command=command,deadline_seconds=60));assert sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA;began=time.monotonic();error=None
 with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'));save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
  try:child.wait(timeout=60)
  except BaseException as e:error=repr(e)
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 def missing(group=False):
  try:(os.killpg if group else os.kill)(child.pid,0)
  except ProcessLookupError:return True
  return False
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,error=error);save(out/'process-terminal.json',terminal);errors=[];counts=Counter();runtime=load(out/'runtime.json')if(out/'runtime.json').exists()else None
 if child.returncode==0:
  actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];assert len(actual)==len(wanted)
  for w,a in zip(wanted,actual):
   assert w['id']==a['id'];v=a['result'];v['physical_live']['storage']=[list(bytes.fromhex(x))for x in v['physical_live']['storage']];compare(w['result'],v,(),counts,errors);concrete_counts=Counter();compare(w['materialized_physical_live'],v['physical_live'],('physical_live',),concrete_counts,errors)
 after={n:sha(ROOT/n)for n in files};assert before==after and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',errors);r=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,cases=len(rows),full_calls=len(rows),entry_counts=dict(Counter(x['mode']for x in rows)),comparison_complete=child.returncode==0,differences=len(errors)if child.returncode==0 else None,counts=dict(counts),source_files=len(files),source_before=before,source_after=after,source_unchanged=True,local_source_import_edges=edges,frozen_artifacts=frozen,expected_before_original=True,process=terminal,runtime=runtime,scope='Controlled full live32 capacity/backing and known numeric projection; caster8/9 with explicit entry scratch+48 u32 or exacttyped unresolved origin,4600/1072 resumption. Unresolved-origin+16 is not a predicted byte; controlledpoison companion comparison is separate. No natural scratch caller/headless/App/native',pending=['Physical1202 Aura and all wire are raw observations in this component, not new independent predictions','Caster variants7/12 physical append and1073 physical incoming cleanup remain separate','No prior original count transferred; no750 source/checker changed'])
 save(out/'comparison.json',r);print(json.dumps(dict(directory=str(out),cases=len(rows),differences=r['differences'],first=errors[:5],process=terminal,comparison_sha256=sha(out/'comparison.json'))),flush=True)
 if child.returncode or error or errors or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)
 assert runtime['actual_host_calls']==0 and runtime['stack_all_restored']and runtime['peak_memory_bytes']<=33554432

def load(p):return json.loads(p.read_text())
if __name__=='__main__':main()
