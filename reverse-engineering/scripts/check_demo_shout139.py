#!/usr/bin/env python3
"""Expected-first complete1160 cast and real925 weakness/Aura continuation."""
from pathlib import Path
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
import argparse,json,os,signal,subprocess,sys,time,struct,hashlib
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from build_demo_shout139_oracle import build
from check_player_update139 import projection,load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA,missing
from check_player_autocast139 import combat_projection
from check_healing139_v3 import heal_projection
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.demo_world139 import prepare_demo_world139
from core_spec.demo_shout139 import cast_demo_actor139,merge_demo_debuff21553
from core_spec.demo_enemy_ai139 import EnemyAIState139,update_demo_enemy_ai139
from core_spec.incoming139 import IncomingState139,Buff139
from core_spec.incoming_history139 import IncomingHistory139,projection as history_projection
from core_spec.death139 import word139,position3_139
from core_spec import binary32 as f


def closure():
 names=set(production_sources135(ROOT,'core_spec.demo_world139','core_spec.demo_shout139','core_spec.demo_enemy_ai139'))|set('scripts/'+n for n in['check_demo_shout139.py','build_demo_shout139_oracle.py','run_demo_shout139_oracle.mjs','check_player_update139.py','check_player_autocast139.py','check_healing139_v3.py','check_asset_world139.py','production_closure135.py','source_closure137.py'])
 while True:
  try:return sorted(names),verify_local_source_closure(sorted(names))
  except AssertionError as e:
   pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])

def ai_projection(ai):
 path=ai.distance_map
 return dict(history=history_projection(ai.history),path=None if path is None else dict(capacity=len(path.values_u16),count=len(path.values_u16),start_index=path.start_index,field24=path.field24,u16le_sha256=hashlib.sha256(struct.pack('<'+'H'*len(path.values_u16),*path.values_u16)).hexdigest()),categories={k:struct.pack('>d',v).hex()for k,v in ai.incoming.category1112},path_clock2372_bits=ai.distance_clock2372_bits,incoming992_hex=struct.pack('>d',ai.incoming.incoming992).hex(),last_hit1652_bits=ai.incoming.last_hit1652_bits)

def corpus(world,phase):
 rows=[];specs=[(3,1,'tier2_near',0.,1,[])]
 if phase=='full':
  specs=[]
  for seed,index in[(2,0),(3,1)]:
   specs.extend((seed,index,label,offset,n,[])for label,offset,n in [('far',100.,1),('near_repeat',0.,2),('edge_inside',13.9990234375,1),('edge_equal',14.,1),('edge_outside',14.0009765625,1),('through_actual_death',0.,32)])
  specs.append((3,1,'multi_midpoint',None,1,[]))
  specs.append((3,1,'weakness_active_contact',0.,1,[dict(now_bits=f.from_float(2.),dt_bits=f.from_float(1.))]))
  specs.append((3,1,'expiry_equal_sameframe_contact',0.,1,[dict(now_bits=f.from_float(6.),dt_bits=f.from_float(1.))]))
  specs.append((3,1,'normal_cadence_expiry',0.,1,[dict(now_bits=f.from_float((i+1)/8),dt_bits=f.from_float(.125))for i in range(64)]))
 for seed,select_index,label,offset,n,aiupdates in specs:
  opening,gain,selected,actor=prepare_demo_world139(seed,select_index,world);initial=actor;anchor=position3_139(actor.damage.records432[0],0)
  if offset is None:
   pair=min(((i,j)for i in range(4)for j in range(i+1,4)),key=lambda ij:sum((f.to_float(word139(actor.damage.records432[ij[0]],k))-f.to_float(word139(actor.damage.records432[ij[1]],k)))**2 for k in(316,320)))
   aa,bb=[position3_139(actor.damage.records432[k],0)for k in pair];xy=tuple(f.mul(f.add(a,b),0x3f000000)for a,b in zip(aa[:2],bb[:2]));offsets=tuple(f.sub(a,b)for a,b in zip(xy,anchor[:2]))
  else:offsets=(f.from_float(offset),0);xy=(f.add(anchor[0],offsets[0]),anchor[1])
  height=world.height(*xy);assert height.found;xyz=(*xy,height.value_bits);actor=replace(actor,player=replace(actor.player,player_xyz=xyz));stages=[];diags=[];times=[f.from_float(i/8)for i in range(n)]
  for now in times:
   actor=replace(actor,player=replace(actor.player,growth=replace(actor.player.growth,now_bits=now)),damage=replace(actor.damage,now_bits=now));actor,result=cast_demo_actor139(actor,1,world);stages.append(dict(player=projection(actor.player),combat=combat_projection(actor),healing=heal_projection(actor.ledger),success=result.success));diags.append(dict(selected_ids=list(map(str,result.selected_ids)),base_damage_bits=result.base_damage_bits,radius_bits=result.radius_bits,strength_bits=result.strength_bits,duration_bits=result.duration_bits,effect_writes=[[str(g),o,b]for g,o,b in result.effect_writes],known_packets=[list(p)for p in result.known_packets],heal_events=[dict(reason_id=v.reason_id,amount_bits=v.amount_bits,event_id=str(v.event_id))for v in result.heal_events],hits=[dict(target=str(guid),amount_bits=amount,critical=critical,dead=value.dead)for guid,amount,critical,value in result.hits],cooldown_if_success_bits=result.cooldown_if_success_bits))
  aistages=[]
  if aiupdates:
   p=actor.player;g=p.growth;incoming=IncomingState139(1,g.now_bits,0,0,g.current_hp_bits,g.derived_bits[1536],g.derived_bits[1568],g.derived_bits[1572],last_hit1652_bits=p.last_hit1652_bits,player_xy=p.player_xyz[:2],records432=g.units432_cells,live32=tuple(Buff139(word139(r,8),None if word139(r,8)==12 else word139(r,12),word139(r,20),word139(r,24))for r in p.live.active),items8=())
   ai=EnemyAIState139(g.units432_cells,g.now_bits,0,p.player_xyz,incoming,IncomingHistory139(0,0,0,(),(),()),tuple(g.player_fields.items()),actor.damage.movement_sequence2412)
   for step in aiupdates:
    ai=replace(ai,now_bits=step['now_bits'],dt_bits=step['dt_bits']);value=update_demo_enemy_ai139(ai,world,english_names={5830904:'Kobold Vermin'});ai=value.state;p=actor.player;g=replace(p.growth,now_bits=ai.now_bits,units432_cells=ai.records432,current_hp_bits=ai.incoming.hp1440_bits,player_fields=dict(ai.player_fields));actor=replace(actor,player=replace(p,growth=g,last_hit1652_bits=ai.incoming.last_hit1652_bits),damage=replace(actor.damage,records432=ai.records432,now_bits=ai.now_bits,player_hp1440_bits=ai.incoming.hp1440_bits,movement_sequence2412=ai.movement_sequence2412));aistages.append(dict(player=projection(actor.player),ai=ai_projection(ai),packets=[list(p)for p in value.packets],attacks=list(value.attacks),motions=list(value.motions),records432_cells=[list(r)for r in ai.records432]))
  case=dict(id=len(rows),app_seed_u64=str(seed),amount=5,dead_mask=0,select_index=select_index,action=dict(npc_index=0,offset_x_bits=offsets[0],offset_y_bits=offsets[1],height_bits=height.value_bits),casts=times,ai_updates=aiupdates)
  rows.append(dict(id=case['id'],group=label,input=case,actual_tier=gain.state.candidates[select_index].tier,initial=projection(initial.player),player_xyz=list(xyz),stages=stages,diagnostics=diags,ai_stages=aistages))
 return json.loads(json.dumps(rows))


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['pilot','full'],default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('demo-shout139-'+args.phase+'-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out);opened=[];forbidden=[];model_phase=True
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
 save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696));frozen={n:sha(out/n)for n in['inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json']};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA))
 argv=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_demo_shout139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
 with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
  p=subprocess.Popen(argv,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=p.pid,pgid=p.pid,command=argv,deadline_seconds=120))
  try:code=p.wait(timeout=120)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code=p.returncode
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'owned-terminal.json',terminal);actual=[json.loads(v)for v in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diff=[]
 def eq(cid,label,want,got):
  counts['assertions']+=1
  if want!=got:
   counts['differences']+=1
   if len(diff)<100:diff.append(dict(case=cid,field=label,expected=want,actual=got))
 def cells(cid,label,rows,hxs):
  eq(cid,label+'.length',len(rows),len(hxs))
  for row,hx in zip(rows,hxs):
   raw=bytes.fromhex(hx);assert len(row)==len(raw)
   for k,(a,b)in enumerate(zip(row,raw)):
    if a is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
    else:eq(cid,label+'+'+str(k),a,b);counts[label+'_known']+=1
 def player(cid,label,want,got):
  eq(cid,label+'.growth',want['growth'],got['capture']['projection'])
  for k in('racial80_hex','scalar','source_flags','spell_sets'):eq(cid,label+'.'+k,want[k],got[k])
  for k in('live','aura'):
   for n in('capacity','count')+(('flag2569',)if k=='aura'else()):eq(cid,label+'.'+k+'.'+n,want[k][n],got[k][n])
   cells(cid,label+'.'+k,want[k]['storage'],got[k]['storage'])
 for E,A in zip(rows,actual):
  cid=E['id'];eq(cid,'id',cid,A['id']);player(cid,'initial',E['initial'],A['player_before']);eq(cid,'actual-tier',E['actual_tier'],A['gain']['projection']['candidates'][E['input']['select_index']]['tier']);eq(cid,'controlled-player',E['player_xyz'],A['cast_stages'][0]['before_combat']['player_xyz']);previous=A['controlled_before']
  for j,(want,obs,diag)in enumerate(zip(E['stages'],A['cast_stages'],E['diagnostics'],strict=True)):
   player(cid,'cast'+str(j),want['player'],obs['after']);eq(cid,'success'+str(j),want['success'],obs['combat']['success'])
   for k,v in want['combat'].items():
    if k=='records432_cells':cells(cid,'NPC',v,obs['combat']['records432_hex'])
    elif k=='pickups56_cells':cells(cid,'pickup',v,obs['combat']['pickups56_hex'])
    else:eq(cid,'combat.'+k,v,obs['combat'].get(k))
   for k,v in want['healing'].items():eq(cid,'healing.'+k,v,obs['healing'][k])
   cursor=0
   for packet in diag['known_packets']:
    at=next((i for i in range(cursor,len(obs['new_packets']))if obs['new_packets'][i]==packet),None);eq(cid,'packet_subset',True,at is not None)
    if at is not None:cursor=at+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2
   for k in('live','aura','racial80_hex'):eq(cid,'preserved'+k,A['player_before'][k],obs['after'][k])
   counts['full922']+=1;counts['success']+=want['success'];counts['hits']+=len(diag['hits']);counts['crit']+=sum(v['critical']for v in diag['hits']);counts['death']+=sum(v['dead']for v in diag['hits']);counts['max_targets']=max(counts['max_targets'],len(diag['hits']));previous=obs['after']
  for want,obs in zip(E['ai_stages'],A['ai_stages'],strict=True):
   player(cid,'AI',want['player'],obs['after']);cells(cid,'AI_NPC',want['records432_cells'],obs['after']['capture']['background']['units']['storage']);eq(cid,'AI_packets',want['packets'],obs['new_packets'])
   for k in('path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories'):eq(cid,'AI_'+k,want['ai'][k],obs['ai'][k])
   for k in('header','active'):eq(cid,'AI_history_'+k,want['ai']['history'][k],obs['ai']['history'][k])
   cells(cid,'history',want['ai']['history']['storage'],obs['ai']['history']['storage']);counts['full925']+=1;counts['AI_attacks']+=len(want['attacks']);counts['AI_packets']+=len(want['packets']);counts['Aura_expiry_packet169']+=sum(k==169 for k,v in want['packets'])
  assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]
 runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
 if runtime:
  assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None
  assert all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])and all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
 for n,h in sources.items():assert sha(ROOT/n)==h
 for n,h in frozen.items():assert sha(out/n)==h
 save(out/'differences.json',diff);artifacts={n:sha(out/n)for n in['actual.jsonl','stderr.log','runtime.json','owned-start.json','owned-terminal.json','prepared.json','differences.json']if(out/n).exists()};comp=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,artifacts=artifacts,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,scope='DirectDemo922/Tier0+2 andfinite925weakness/Aura; explicitXP5/selectedrecord;no1238/naturalfullframe/game')
 save(out/'comparison.json',comp);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),differences=counts['differences'],first_fields=[v['field']for v in diff[:10]],counts=dict(counts),process=terminal)),flush=True)
 if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)
if __name__=='__main__':main()
