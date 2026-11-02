#!/usr/bin/env python3
"""Expected-first actual damage/deaths to complete952; no input owner patching."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from dataclasses import replace
import argparse,json,os,signal,subprocess,sys,time,struct
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from build_spawn_combat139_oracle import build
from check_player_update139 import projection,load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA,missing
from check_player_autocast139 import combat_projection
from check_healing139_v3 import heal_projection
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.spawn_combat_source139 import prepare_spawn_combat_source139,kill_live_normals139,PhysicalNPCVector139,prepare_spawn_moving_source139
from core_spec.spawn_schedule139_v4 import update_spawn_schedule139,projection139,thread_spawn_result139,from_combat139,f

def closure():
 names=set(production_sources135(ROOT,'core_spec.spawn_combat_source139','core_spec.spawn_schedule139_v4'))|set('scripts/'+n for n in['check_spawn_combat139.py','build_spawn_combat139_oracle.py','run_spawn_combat139_oracle.mjs','check_asset_world139.py','check_player_update139.py','check_player_autocast139.py','check_healing139_v3.py','production_closure135.py','source_closure137.py'])
 while True:
  try:return sorted(names),verify_local_source_closure(sorted(names))
  except AssertionError as e:
   pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])

def corpus(world,phase):
 rows=[]
 for deaths,boost in([(4,True)]if phase=='pilot'else[(1,False),(2,False),(4,False),(4,True)]):
  source=prepare_spawn_combat_source139(world,deaths);s=source.scheduler;actor=source.actor;updates=[];stages=[];now=s.now_bits
  for index in range(2 if phase=='pilot'else 4):
   actions=[]
   if boost and index==1:
    actor,actions,_=kill_live_normals139(actor,world);physical=PhysicalNPCVector139(actor.damage.records432+s.records432[s.count:],s.count);s=from_combat139(source.opening,actor,physical,previous=s,distance_map=source.cold_source.ai.distance_map)
   beforeplayer=projection(actor.player)
   now=f.add(now,0x3dcccccd);result=update_spawn_schedule139(s,now,0x3dcccccd,world);s=result.state;actor=thread_spawn_result139(actor,result);updates.append(dict(actions_before=list(actions),now_bits=now,dt_bits=0x3dcccccd));stages.append(dict(before_player=beforeplayer,player=projection(actor.player),spawn=projection139(s),new_packets=[list(p)for p in result.packets],diagnostics=list(result.diagnostics),new_NPCs=[list(v)for v in result.new_NPCs]))
  case=dict(id=len(rows),app_seed_u64='11',amount=5,select_index=0,prefix_updates=[dict(now_bits=r.state.player.growth.now_bits,dt_bits=0x3dcccccd)for r in source.cold_source.steps],controlled_player_xyz=list(source.cold_source.controlled_player_xyz),extra_casts=list(source.extra_controls),updates=updates)
  path=source.cold_source.ai.distance_map
  rows.append(dict(id=case['id'],group='actualdead'+str(deaths)+('_boost'if boost else'')+'_952',input=case,source_player=projection(source.actor.player),source_combat=combat_projection(source.actor),source_healing=heal_projection(source.actor.ledger),source_path=dict(capacity=len(path.values_u16),count=len(path.values_u16),start_index=path.start_index,field24=path.field24,u16le_sha256=__import__('hashlib').sha256(struct.pack('<'+'H'*len(path.values_u16),*path.values_u16)).hexdigest()),stages=stages))
 if phase=='full':
  for source_id in(0,1):
   source=prepare_spawn_moving_source139(world,source_id);probe=source.probe;actor=source.actor;s=source.scheduler;now,dt=probe.target_now_bits,probe.target_dt_bits;result=update_spawn_schedule139(s,now,dt,world);after=thread_spawn_result139(actor,result);beforecombat=combat_projection(actor);beforecombat['records432_cells']=[list(r)for r in source.units.storage];path=probe.target_ai.distance_map
   case=dict(id=len(rows),cooccur_probe=True,source_case_id=source_id,app_seed_u64='11',amount=5,select_index=0,placement=probe.placement,target_index=probe.target_step_index,timestamps64=list(map(str,probe.timestamps64)),updates=[dict(actions_before=[],now_bits=now,dt_bits=dt)])
   rows.append(dict(id=case['id'],group='actual_moving_source'+str(source_id)+'_952',input=case,source_player=projection(actor.player),source_combat=beforecombat,source_healing=heal_projection(actor.ledger),source_path=dict(capacity=len(path.values_u16),count=len(path.values_u16),start_index=path.start_index,field24=path.field24,u16le_sha256=__import__('hashlib').sha256(struct.pack('<'+'H'*len(path.values_u16),*path.values_u16)).hexdigest()),stages=[dict(before_player=projection(actor.player),player=projection(after.player),spawn=projection139(result.state),new_packets=[list(p)for p in result.packets],diagnostics=list(result.diagnostics),new_NPCs=[list(v)for v in result.new_NPCs])]))
 return json.loads(json.dumps(rows))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['pilot','full'],default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('spawn-combat139-'+args.phase+'-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out);opened=[];forbidden=[];model_phase=True
 def audit(event,values):
  if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
   if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original denied during expectation')
 sys.addaudithook(audit)
 try:world,*_=load_world139(WORLD);rows=corpus(world,args.phase)
 finally:model_phase=False
 assert not forbidden and sources=={n:sha(ROOT/n)for n in files}
 for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
 for p,h in[(SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA),(WORLD/'receipt.json',WORLD_SHA)]:assert sha(p)==h
 save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696));frozen={n:sha(out/n)for n in['inputs.json','expected.json','manifest.json',m['module_file'],'config.json','expectation-read-audit.json']};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,actual_damage_producer=True,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA))
 argv=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_spawn_combat139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
 with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
  p=subprocess.Popen(argv,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=p.pid,pgid=p.pid,command=argv,deadline_seconds=120))
  try:code=p.wait(timeout=120)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code=p.returncode
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'owned-terminal.json',terminal);actual=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diff=[]
 def eq(cid,label,want,got):
  counts['assertions']+=1
  if want!=got:
   counts['differences']+=1
   if len(diff)<100:diff.append(dict(case=cid,field=label,expected=want,actual=got))
 def cells(cid,label,rows,hxs):
  eq(cid,label+'.length',len(rows),len(hxs))
  for row,hx in zip(rows,hxs):
   raw=bytes.fromhex(hx);eq(cid,label+'.stride',len(row),len(raw))
   for k,(a,b)in enumerate(zip(row,raw)):
    if a is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
    else:eq(cid,label+'+'+str(k),a,b);counts[label+'_known']+=1
 def player(cid,label,want,got):
  eq(cid,label+'.growth',want['growth'],got['capture']['projection'])
  for k in('scalar','racial80_hex','source_flags','spell_sets'):eq(cid,label+'.'+k,want[k],got[k])
  for k in('live','aura'):
   for n in('capacity','count')+(('flag2569',)if k=='aura'else()):eq(cid,label+'.'+k+'.'+n,want[k][n],got[k][n])
   cells(cid,label+'.'+k,want[k]['storage'],got[k]['storage'])
 for E,A in zip(rows,actual):
  cid=E['id'];eq(cid,'id',cid,A['id']);eq(cid,'newGame',False,A['new_Game_pointer']==A['old_snapshot_Game_not_target']);player(cid,'producer',E['source_player'],A['after_producer']);eq(cid,'sourcepath',E['source_path'],A['after_producer_ai']['path'])
  for k,v in E['source_combat'].items():
   if k=='records432_cells':cells(cid,'producer_NPC',v,A['after_producer_combat']['records432_hex'])
   elif k=='pickups56_cells':cells(cid,'producer_pickup',v,A['after_producer_combat']['pickups56_hex'])
   else:eq(cid,'producer_combat.'+k,v,A['after_producer_combat'][k])
  for k,v in E['source_healing'].items():eq(cid,'producer_healing.'+k,v,A['after_producer_healing'][k])
  previous=A['after_producer']
  for j,(stage,obs,step)in enumerate(zip(E['stages'],A['frames'],E['input']['updates'])):
   e=stage['spawn'];before=obs['before'];after=obs['after'];expectedpre=stage['before_player'];expectedpre['scalar']['2352']=step['now_bits'];player(cid,f'{j}.beforeActualSource',expectedpre,before);player(cid,f'{j}.player',stage['player'],after)
   inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);struct.pack_into('<I',inherited,2352,step['now_bits']);eq(cid,f'{j}.beforeInherited',inherited.hex(),before['capture']['raw_game2592_hex'])if not step['actions_before']and not E['input'].get('cooccur_probe')else None;counts['input_Game2592_inherited']+=2592 if not step['actions_before']and not E['input'].get('cooccur_probe')else 0
   for k,v in obs['spawn'].items():eq(cid,f'{j}.spawn.'+k,e[k],v)
   bg=after['capture']['background'];cells(cid,'NPC',e['records432_cells'],bg['units']['storage']);cells(cid,'pickup',e['pickups']['storage'],bg['pickups']['storage']);eq(cid,f'{j}.packets',stage['new_packets'],obs['new_packets']);counts['known_new_packets']+=len(stage['new_packets']);counts['known_new_packet_bytes']+=sum(len(h)//2 for t,h in stage['new_packets'])
   for k in('pickups','special','windows','boundaries','auxiliary','claims','movement_sequence2412'):eq(cid,f'{j}.background.'+k,before['capture']['background'][k],bg[k])
   eq(cid,f'{j}.AIretained',obs['before_ai'],obs['ai'])
   old=before['capture']['background']['units'];new=bg['units']
   for i in range(old['count']):eq(cid,f'{j}.existingNPC{i}',old['storage'][i],new['storage'][i]);counts['existing_NPC_full432_conserved']+=432
   allowed=set()
   for at,n in((1720,24),(1784,12),(1880,12),(2352,4),(2408,4),(2416,24),(1868,12),(2444,8),(2586,1)):allowed.update(range(at,at+n))
   for at,(a,b)in enumerate(zip(bytes.fromhex(before['capture']['raw_game2592_hex']),bytes.fromhex(after['capture']['raw_game2592_hex']))):
    if at not in allowed:eq(cid,f'{j}.Game{at}',a,b);counts['Game_nonowned_conserved']+=1
   counts['targets952']+=1;counts['positive_killcost_decay']+=e['kill_cost2420_bits']!=0;counts['densityNPC']+=sum(v[3]=='density'for v in stage['new_NPCs']);counts['newNPC']+=len(stage['new_NPCs']);previous=after
  assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]
 runtime=load(out/'runtime.json')if(out/'runtime.json').exists()else None
 if runtime:
  assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None
  assert runtime['full_calls']['952']==sum(len(r['stages'])for r in rows)and all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])
  assert all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
 for n,h in sources.items():assert sha(ROOT/n)==h
 for n,h in frozen.items():assert sha(out/n)==h
 save(out/'differences.json',diff);artifacts={n:sha(out/n)for n in['actual.jsonl','stderr.log','runtime.json','owned-start.json','owned-terminal.json','prepared.json','differences.json']if(out/n).exists()};comparison=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,scope='Real stationary2123/922 deaths→complete952; explicitXP5/selectedThunder prefix, nofullframe/AIafterprefix/collection/naturalupgrade')
 save(out/'comparison.json',comparison);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),differences=counts['differences'],first_fields=[v['field']for v in diff[:8]],counts=dict(counts),process=terminal)),flush=True)
 if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)
load=lambda p:json.loads(Path(p).read_text())
if __name__=='__main__':main()
