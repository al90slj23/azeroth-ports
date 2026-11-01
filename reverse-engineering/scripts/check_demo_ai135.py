#!/usr/bin/env python3
"""Expected-first full921 demo weakness/expiry over controlled query worlds."""
from pathlib import Path
from dataclasses import asdict,replace
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_demo_ai135_oracle import ROOT,SOURCE,SOURCE_SHA,build_demo_ai135,sha
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ai135 import AiFrame135
from core_spec.ai_world135 import update_world_ordinary_units135
from core_spec.demo_ai135 import PendingDemoAi135
from core_spec.demo_shout135 import DemoDebuff135
from core_spec.incoming135 import input_from_dict
from core_spec.record_cells135 import cells135,u32,u64,put_u32,put_u64,encode_row
from ai_world135_inputs import controlled_world135
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
BASE=ROOT/'evidence/full0135-oracle-20261101T044817.224194Z/ai135-fixtures.jsonl'
FIELDS=('armor_1392_bits','armor_cap_1572_bits','nearby_reduction_1444_bits','hp_1528_bits','shield_1532_bits','barrier_1536_bits','shield_source_1344','shield_source_remaining_1348_bits','reserve_768_bits','absorbed_740_bits','maximum_shield_744_bits','last_hit_1648_bits')

def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def declaration(raw):
 return DemoDebuff135(u64(raw,112),u32(raw,0),tuple(u32(raw,o)for o in(128,132,136,140)),u32(raw,360),u32(raw,364),tuple(u32(raw,168+4*i)for i in range(16)),u32(raw,240))

def corpus(full):
 with BASE.open()as stream:line=stream.readline(2097153)
 assert len(line)<=2097152;baseline=json.loads(line);template=baseline['input']['records'][0];world_description=dict(kind='controlled_query_world',nav=None,primary=None,fallback_height_bits=0,flat_height_bits=0);world=controlled_world135(world_description);rows=[];expected=[];labels=[]
 def add(group,words,*,steps=((10,.1),),slot=0,aura=True,freeze=0,phase=1,chase=False,multiple=False):
  initial=[]
  for index in range(2 if multiple else 1):
   raw=cells135(template);put_u64(raw,112,(u64(raw,112)+index)&((1<<64)-1));put_u32(raw,360,1160);put_u32(raw,364,f.from_float(6))
   for offset,value in zip((128,132,136,140),words):put_u32(raw,offset,f.from_float(value))
   if index:put_u32(raw,132,f.from_float(9));put_u32(raw,140,f.from_float(9))
   for i in range(16):put_u32(raw,168+i*4,1160 if aura and i==slot else 0)
   for offset in(316,328):
    for j,value in enumerate((15 if chase else .5+index*.1,0,0)):put_u32(raw,offset+j*4,f.from_float(value))
   for offset,value in((340,0),(344,0),(348,0),(352,f.from_float(.05)),(396,0),(400,f.from_float(freeze))):put_u32(raw,offset,value)
   initial.append(encode_row(raw))
  records=tuple(initial);incoming_raw=dict(baseline['input']['incoming']);incoming_raw.update(phase_2579=phase,mode_2574=0,map_id='elwynn');incoming=input_from_dict(incoming_raw);states=tuple(declaration(cells135(raw))for raw in records);sequence=123;packets=0;answers=[];trace=[];details=[]
  for now,dt in steps:
   frame=AiFrame135(records,f.from_float(now),f.from_float(dt),(0,0,0),incoming,other_incoming_sources_absent=True,known_demo_statuses=states)
   result=update_world_ordinary_units135(frame,world);records,incoming,states=result.records,result.incoming,result.demo_statuses
   sequence=(sequence+len(result.movements))&f.MASK;packets+=len(result.movements)+len(result.attacks)+len(result.demo_aura_packets169)
   answers.append(dict(records=list(records),**{key:getattr(incoming,key)for key in FIELDS},incoming_total_992_bits=struct.pack('>d',incoming.incoming_total_992).hex(),sequence=sequence,packet_count=packets,rng_words=[1,2,3,4],new_aura_packets169=[dict(opcode=op,payload_hex=payload)for op,payload in result.demo_aura_packets169],new_non169_packet_count=len(result.movements)+len(result.attacks),aura_after_non169=True))
   trace.append(dict(now_bits=f.from_float(now),dt_bits=f.from_float(dt),player_xyz_bits=[0,0,0]));details.append(dict(attacks=[(str(guid),value)for guid,value in result.attacks],expirations=[(str(guid),spell)for guid,spell in result.demo_expirations],fields=[(str(guid),keys)for guid,keys in result.demo_aura_fields],known_demo_after=[asdict(x)for x in states],movements=len(result.movements)))
  index=len(rows);rows.append(dict(id=index,group=group,world=world_description,records=initial,incoming=incoming_raw,max_hp_bits=f.from_float(10000),sequence=123,steps=trace));expected.append(dict(id=index,stages=answers));labels.append(dict(id=index,group=group,stages=details))
 add('pilot-primary-active-contact',(.35,20,.1,30))
 add('pilot-backup-active-at-primary-equality',(.35,10,.1,20))
 add('pilot-expired-contact-and-late169',(.35,9,.1,9))
 if full:
  for primary in(9,10,f.to_float(f.from_float(10)+1),20):
   for backup in(0,9,10,f.to_float(f.from_float(10)+1),30):
    for strength in(.35,.9):add('primary-backup-ordered-boundaries',(strength,primary,.1,backup))
  add('expiry-before-U400-freeze',(.35,9,.1,9),freeze=20)
  add('expiry-missing-Aura-emits-no-packet',(.35,9,.1,9),aura=False)
  for slot in(3,4,7,8,11,12,15):add('Aura-slot-field-mask-groups',(.35,9,.1,9),slot=slot)
  add('phase2-local-cleanup-and-incoming-guard',(.35,9,.1,9),phase=2)
  add('movement-before-late-Aura-remove',(.35,9,.1,9),chase=True)
  add('two-unit-independent-owner-late-remove',(.35,20,.1,30),multiple=True)
  add('continuous-primary-fallback-expiry',(.35,10,.1,12),steps=((9.8,.1),(10,.2),(11.4,1.4),(12.8,1.4),(14.2,1.4)))
  add('live-primary-ignores-earlier-backup',(.35,20,.1,10),steps=((10,.1),(11.4,1.4),(20,8.6)))
  add('post-expiry-continuation-no-repeated169',(.35,9,.1,9),steps=((10,.1),(11.4,1.4),(12.8,1.4)))
 return json.loads(json.dumps(rows)),json.loads(json.dumps(expected)),json.loads(json.dumps(labels))

def refusal_checks():
 rows,_,_=corpus(False);c=rows[0];raw=cells135(c['records'][0]);incoming=input_from_dict(c['incoming']);world=controlled_world135(c['world']);status=declaration(raw);results=[]
 def run(record,declared):return update_world_ordinary_units135(AiFrame135((encode_row(record),),f.from_float(10),f.from_float(.1),(0,0,0),incoming,other_incoming_sources_absent=True,known_demo_statuses=declared),world)
 attempts=[('legacy-unbound360-remains-rejected',raw,()),('wrong-word-declaration',raw,(replace(status,words128_140=(0,*status.words128_140[1:])),)),('unsupported-spell',raw,(replace(status,spell360=123),)),('duplicate-GUID-declaration',raw,(status,status))]
 other=raw.copy();put_u32(other,172,123);attempts.append(('unowned-other-Aura-pending',other,(declaration(other),)))
 duplicate=raw.copy();put_u32(duplicate,172,1160);attempts.append(('duplicate-Aura-needs-earlier-cleanup',duplicate,(declaration(duplicate),)))
 for name,record,declared in attempts:
  try:run(record,declared)
  except(PendingDemoAi135,ValueError):results.append(name)
  else:raise AssertionError('Unknown demo source accepted: '+name)
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
 scripts=('check_demo_ai135.py','build_demo_ai135_oracle.py','run_demo_ai135_oracle.mjs','demo_ai135_host.mjs','ai_world135_packing.mjs','build_distance_map135_oracle.py','build_full135_oracle.py','build_upgrade134_oracle.py','production_closure135.py','source_closure137.py','ai_world135_inputs.py')
 files=tuple('scripts/'+x for x in scripts)+production_sources135(ROOT,'core_spec.ai_world135','core_spec.ai_motion135')
 edges=verify_local_source_closure(files);before={x:sha(ROOT/x)for x in files};rows,wanted,labels=corpus(args.phase=='full');refusals=refusal_checks();out,manifest=build_demo_ai135()
 for n,h in before.items():
  dest=out/'source-snapshot'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes());assert sha(dest)==h
 for name,v in(('input.json',rows),('expected.json',wanted),('labels.json',labels),('refusals.json',refusals)):save(out/name,v)
 artifacts={name:sha(out/name)for name in('input.json','expected.json','labels.json','refusals.json','manifest.json',manifest['module_file'],*(f'demo-ai-{x}.wat'for x in(921,4543,15511,13814,1073,27375)))};source_input=dict(path=str(BASE),sha256=sha(BASE),scope='Only first typed fixture input row/incoming read; no old original result is consumed')
 assert sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA;command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_demo_ai135_oracle.mjs'),str(out),str(out/'input.json')];save(out/'prepared.json',dict(source_sha256=before,artifacts=artifacts,expected_before_original=True,command=command,deadline_seconds=60,fixture_input=source_input))
 began=time.monotonic();error=None
 with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'));save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
  try:child.wait(timeout=60)
  except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as exc:error=repr(exc)
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=2)
 def missing(group=False):
  try:(os.killpg if group else os.kill)(child.pid,0)
  except ProcessLookupError:return True
  return False
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,error=error);save(out/'process-terminal.json',terminal);errors=[];compared=0;runtime=None
 if child.returncode==0:
  actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];assert len(actual)==len(wanted)
  for want,got in zip(wanted,actual):
   assert want['id']==got['id']and len(want['stages'])==len(got['stages'])
   for index,(w,a)in enumerate(zip(want['stages'],got['stages'])):
    observed=a['known'];compared+=1
    for key,value in w.items():
     if observed[key]!=value:errors.append(dict(case_id=want['id'],stage=index,field=key,expected=value,actual=observed[key]))
  runtime=json.loads((out/'demo-ai135-runtime.json').read_text());assert runtime['actual_host_calls']==0 and runtime['stack_all_restored']and runtime['max_memory_bytes']<=33554432
 save(out/'differences.json',errors);after={x:sha(ROOT/x)for x in files};assert before==after and artifacts=={n:sha(out/n)for n in artifacts}and sha(BASE)==source_input['sha256']
 report=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,cases=len(rows),stages=sum(len(x['steps'])for x in rows),compared_stages=compared,differences=len(errors)if child.returncode==0 else None,comparison_complete=child.returncode==0,groups=dict(Counter(x['group']for x in labels)),source_files=len(files),source_sha256_before=before,source_sha256_after=after,local_source_import_edges=edges,frozen_artifacts=artifacts,expected_before_original=True,fixture_input=source_input,pure_model_refusals=refusals,process=terminal,runtime=runtime,scope='Fresh complete921 ordinary local-mode weakness/expiry/contact over explicit controlled flat world; physical424B/HP/incoming/late169 complete aura slots, fixed135 only',pending=['Original constructor/world resource ownership/full880 not executed','Other or duplicate NPC aura entries, nonempty44B NPC abilities, remote-party modes and other status/CC producers remain pending','Full movement and incoming-hit packet payloads observed; this scope predicts exact lateAura169, total packet count and order only'],full880_frames=0,native_executions=0,complete_games=0,artifacts={n:sha(out/n)for n in('stdout.jsonl','stderr.log','differences.json','prepared.json')})
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),cases=len(rows),stages=report['stages'],differences=report['differences'],first_errors=errors[:3],process=terminal,comparison_sha256=sha(out/'comparison.json'))),flush=True)
 if child.returncode or error or errors or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)
if __name__=='__main__':main()
