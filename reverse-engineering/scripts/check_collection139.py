#!/usr/bin/env python3
"""Expected-first sameGame death→collection→true current1394677 XP2."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,os,signal,struct,subprocess,sys,time
from dataclasses import replace
sys.dont_write_bytecode=True
from build_collection139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from load_world_position139_inputs import load_world139_canonical
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.collection_handoff139 import prepare_default_collection139
from core_spec.collection139 import collect_pickups139,MIN_DELAY139,ClaimSource139,ForwardQueue139
from core_spec.death_pickups139 import vector139
from core_spec import binary32 as f
from core_spec.growth139 import gain_xp139,projection139 as growth_projection139
from core_spec.cast139 import CleaveDefinition139
CANONICAL=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model';CANONICAL_SHA='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
SNAPSHOT=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_world6786.memory';SNAPSHOT_SHA='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
DEFINITION88='0000000000000000000000003aa5590006000000ccb5590006000000d2b5590016000000e8b55900030000004d03000000003c420000c03f0000e04000000000030000000000000000000000000000000000000005000000'
GROWTH_FROZEN={'reconstruction/core_spec/growth139.py':'046d30aacfc3775bfdb2c022e61e3f1b655e858ebfdf865cee6e8e9419ea2169','reconstruction/core_spec/candidates139.py':'4ff5b2c3706247a9bb0f733bda6b7b2a9d46bbb19ab46b4d7f418b8e3ee70954','reconstruction/core_spec/candidates139_data.py':'efb653784d0fe24bdc35cf65437a5226eff64888252f33826a8341645eaf8343'}
def closure():
 files=set(('scripts/check_collection139.py','scripts/build_collection139_oracle.py','scripts/run_collection139_oracle.mjs','scripts/load_world_position139_inputs.py','scripts/production_closure135.py','scripts/source_closure137.py'))|set(production_sources135(ROOT,'core_spec.collection139','core_spec.collection_handoff139','resource_spec.world_query135'))
 while True:
  try:return sorted(files),verify_local_source_closure(sorted(files))
  except AssertionError as e:
   pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in files;files.add(pair[1])
def projection(state):
 g=state.growth
 return dict(pickup_capacity=state.pickups.capacity,pickup_count=state.pickups.count,pickups56_cells=[list(row)for row in state.pickups.storage],movement_sequence2412=state.movement_sequence2412,gold1456=state.gold1456,earned1100=state.earned1100,level1432=g.level,xp1436=g.xp,pending2376=g.pending,phase2587=g.phase2587,selection_kind2585=g.selection_kind2585,generation2400=g.generation_counter2400,rng_words=list(g.rng_words),hp1440_bits=g.current_hp_bits,derived_bits={str(k):v for k,v in g.derived_bits.items()},known_player_fields={str(k):v for k,v in g.player_fields.items()},xp_queue2144=dict(capacity=state.xp_queue2144.capacity,entries=[list(v)for v in state.xp_queue2144.entries]),coin_queue2156=dict(capacity=state.coin_queue2156.capacity,entries=[list(v)for v in state.coin_queue2156.entries]))
def corpus(world,phase):
 definition=CleaveDefinition139(5882740,b'cleave',bytes.fromhex(DEFINITION88));rows=[]
 def add(*,words=None,counter=10,backing=(),action='near_first',component=None,times=(0,MIN_DELAY139-1,MIN_DELAY139),group='sameGameXP2'):
  h=prepare_default_collection139(world,definition,rng_words=words,counter=counter,backing=backing,action=action);state=h['state'];stages=[];diagnostics=[]
  if component is not None:
   g=state.growth;derived=dict(g.derived_bits);derived.update({1560:component['radius'],1564:component['xp_multiplier'],1588:component['coin_multiplier']});g=replace(g,mode2582=component['mode'],derived_bits=derived)
   claims=ClaimSource139(tuple(tuple(bytes.fromhex(v))for v in component['claims88']),component['claims_count'],len(component['claims88']),None)
   state=replace(state,growth=g,pickups=vector139(tuple(component['pickups56']),component['pickup_count']),claims=claims,player_xyz=tuple(component['player_xyz']),movement_sequence2412=component['sequence'],gold1456=component['gold'],earned1100=component['earned'],mode2582=component['mode'],peer2528=component['peer'],member_count2540=component['member_count'])
  pre=projection(state)
  for now in times:
   result=collect_pickups139(state,now,gain_xp139=gain_xp139);state=result.state;ep=projection(state);ep['now_bits']=now;ep['new_packets']=[list(v)for v in result.packets];stages.append(ep);diagnostics.append(dict(attractions=result.attraction_events,consumption=result.consumption_events,growth_events=[x.events for x in result.growth_results],levels_gained=sum(x.levels_gained for x in result.growth_results),claims=result.claimed_pickup_guids))
  inp=dict(id=len(rows),rng_words=None if words is None else list(words),counter=counter,action=action,repeats=2,gentle_owned_multiplier=False,initial_backing=list(backing),collect_times=list(times),component=component);rows.append(dict(id=len(rows),group=group,input=inp,expected=stages,model_diagnostic=diagnostics,precollection=pre,real_nonempty_world_owners_retained=True))
 add()
 if phase=='pilot':return json.loads(json.dumps(rows))
 for words,counter,action in[((1,2,3,4),10,'near_first'),((0xffffffff,0x80000000,123,999),0xffffffff,'near_second'),((4161993919,3471457705,2142121393,152833613),0xffffff,'near_first'),((198257393,821540657,4290565505,1862768078),0,'near_first'),((2600322798,992965990,1885547156,3874692653),0xffffff,'near_first'),((2878749276,4098555950,4288030436,3462912780),0xffffffff,'near_second')]:add(words=words,counter=counter,action=action)
 base=prepare_default_collection139(world,definition)['state'];player=base.player_xyz
 def row(guid,kind,amount,dx=0,dy=0,marker=0,arrival=0x5a5a5a5a,spawn=0):
  return struct.pack('<4IQ4I4I',marker,arrival,kind,amount,guid,0,8,0,9001 if kind==0 else 9004,f.add(player[0],f.from_float(dx)),f.add(player[1],f.from_float(dy)),player[2],spawn).hex()
 def component(records,claims=(),*,mode=0,members=1,peer=0,gold=0,earned=0,sequence=1,radius=9,xpm=1.2,coinm=1.2):
  return dict(pickups56=list(records),pickup_count=len(records),claims88=list(claims),claims_count=len(claims),player_xyz=list(player),radius=f.from_float(radius),xp_multiplier=f.from_float(xpm),coin_multiplier=f.from_float(coinm),mode=mode,member_count=members,peer=peer,gold=gold,earned=earned,sequence=sequence)
 # Reverse removal of interleaved0/1, all four XPmin1 stay below level1cost5.
 records=[row(100+i,i%2,1 if i%2==0 else 3,dx=(i%3)*.2)for i in range(7)];add(component=component(records),group='reverse_interleaved56_tail')
 add(component=component([row(200,1,3),row(201,1,0xffffffff),row(202,1,0)],gold=0xfffffffe,earned=0xffffffff),group='coins_wrapping_gold_key')
 add(component=component([row(300,0,0),row(301,1,4)],mode=1,members=3,peer=7),group='mode1_forward_rawamount')
 add(component=component([row(310,0,1),row(311,1,4)],mode=2,members=0,peer=0xffffffff),group='mode2_forward_no_scaling')
 # Far arrived coin and far marker0coin followdistinctlazyarrival branches.
 add(component=component([row(400,1,2,dx=40,marker=1,arrival=0),row(401,1,3,dx=40),row(402,1,3,marker=0,arrival=0)]),times=(0,),group='coin_arrival_laziness_canonicalmarker')
 add(component=component([row(410,0,1,dx=40,marker=1,arrival=0)]),times=(0,),group='XP_far_arrived_marker1')
 add(component=component([row(420,0,1,dx=9),row(421,0,1,dx=9.0009765625)]),times=(0,0x3ec00000),group='radius_inclusive_and_far')
 # Claims suppress only age acceleration; far claimed XP stays while unclaimed flies.
 claim=bytearray([0xa5]*88);struct.pack_into('<I',claim,0,1);struct.pack_into('<Q',claim,8,500)
 inactive=bytearray([0x5a]*88);struct.pack_into('<I',inactive,0,0)
 six=0x40c00000;above=six+1;arrival=f.add(above,0x3fa00000)
 add(component=component([row(500,0,1,dx=40),row(501,0,1,dx=40)],(claim.hex(),inactive.hex())),times=(six,above,arrival),group='age6_claimed_vs_unclaimed')
 # Claim does not suppress near-radius attract even afterage6.
 add(component=component([row(500,0,1)],(claim.hex(),)),times=(above,f.add(above,MIN_DELAY139)),group='near_claim_still_attracts')
 add(component=component([row(600,0,1)],sequence=0xffffffff),group='movement_sequence_wrap')
 add(component=component([row(700,0,0),row(701,1,3)],xpm=float('nan'),coinm=-1),group='XPmin1_coin_negative_round')
 return json.loads(json.dumps(rows))
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files}
 for n,h in GROWTH_FROZEN.items():assert before[n]==h
 assert sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
 audit=[];forbidden=[];live=True
 def hook(event,args):
  if event!='open'or not live or not isinstance(args[0],(str,bytes,os.PathLike)):return
  p=Path(os.fsdecode(args[0])).resolve();mode=args[1];flags=args[2];reading=(isinstance(mode,str)and'r'in mode)or(mode is None and isinstance(flags,int)and flags&3==os.O_RDONLY)
  if reading:
   allowed=p.suffix.lower()not in('.memory','.wasm','.wat','.exe');audit.append(dict(path=str(p),allowed=allowed))
   if not allowed:forbidden.append(str(p));raise RuntimeError('Originalinputdeniedduringindependentexpectations')
 sys.addaudithook(hook)
 try:world,provenance=load_world139_canonical(CANONICAL,CANONICAL_SHA);rows=corpus(world,args.phase)
 finally:live=False
 assert not forbidden and before=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('collection139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out);assert m['definition']['raw88_hex']==DEFINITION88
 for n,h in before.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
 save(out/'expected.json',rows);save(out/'inputs.json',[r['input']for r in rows]);save(out/'config.json',dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,game_pointer=14685248,app_pointer=14680072,input_path=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json')));save(out/'expectation-read-audit.json',dict(kind='Pythonopenaudit_notOSsyscall',events=audit,forbidden=forbidden));frozen={n:sha(out/n)for n in('expected.json','inputs.json','config.json','manifest.json',m['module_file'])};save(out/'prepared.json',dict(source_before=before,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_inputs_contain_expected=False,world_provenance=provenance,nonempty_NPC_owner_retained=True,cross_threshold_source_pending_not_bypassed=True))
 command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_collection139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
 with(out/'stdout.jsonl').open('wb')as so,(out/'stderr.log').open('wb')as se:
  p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=60))
  try:p.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-start,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'process-terminal.json',terminal);actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];diff=[];known=unknown=nonzero=0;packets=0;knownfields=0
 for e,a in zip(rows,actual):
  assert e['id']==a['id']and len(e['expected'])==len(a['collection_stages'])
  for stage,(ep,ob)in enumerate(zip(e['expected'],a['collection_stages'])):
   for key in set(ep)-{'pickups56_cells','known_player_fields'}:
    if ep[key]!=ob.get(key):diff.append(dict(id=e['id'],stage=stage,field=key,expected=ep[key],actual=ob.get(key)))
   fields=dict(ob['player_fields'])
   for key,v in ep['known_player_fields'].items():
    knownfields+=1
    if fields.get(int(key))!=v:diff.append(dict(id=e['id'],stage=stage,field='known_player_field',key=key,expected=v,actual=fields.get(int(key))))
   for row,hx in zip(ep['pickups56_cells'],ob['pickups56_hex'],strict=True):
    raw=bytes.fromhex(hx);assert len(row)==len(raw)==56
    for offset,v in enumerate(row):
     if v is None:unknown+=1;nonzero+=raw[offset]!=0
     else:
      known+=1
      if raw[offset]!=v:diff.append(dict(id=e['id'],stage=stage,field='pickup56',offset=offset,expected=v,actual=raw[offset]))
   packets+=len(ep['new_packets'])
 assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None;names=['expected.json','inputs.json','config.json','manifest.json','stdout.jsonl','stderr.log','process-terminal.json','owned-process.json','expectation-read-audit.json','differences.json']+(['runtime.json']if runtime else[])
 runtime_ok=bool(runtime)and runtime['cases']==len(rows)and runtime['full5719_calls']==4*len(rows)and runtime['full922_calls']==2*len(rows)and runtime['full2890_calls']==sum(len(r['input']['collect_times'])for r in rows)and runtime['snapshot_restores']==len(rows)and runtime['denied_imports']==882 and runtime['actual_host_calls']==0 and runtime['stack_checks']==runtime['allocator_calls']+runtime['full5719_calls']+runtime['full922_calls']+runtime['full2890_calls']and runtime['peak_memory_bytes']<=268435456
 process_ok=p.returncode==0 and len(actual)==len(rows)and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<60
 report=dict(status='scoped_original_differential_passed'if runtime_ok and process_ok and not diff else'differences_or_runtime_failure_preserved',version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed=len(actual),differences=len(diff),source_before=before,source_after=before,source_import_edges=edges,world_provenance=provenance,expected_before_original=True,expectation_reads_forbidden=forbidden,process=terminal,runtime=runtime,runtime_contract_checked=runtime_ok,process_contract_checked=process_ok,comparison=dict(known56bytes=known,unknown56bytes=unknown,observed_nonzero_unknown56=nonzero,complete_collector_packets=packets,known_player_fields=knownfields),real_nonempty_world_owners_retained=True,cross_threshold_current_typed_pending=True,scope='18or1sameGame4NPC→two922death;default7and11explicitcollectorinputfixtures retainNPCowner;full2890attract/arrival/remove/full4677belowthresholdXP,typedrealgrowth;mode0andlocalmode1/2forward,claims88,lazyarrival,reverse56,coins. Notnetworktransport/fullopening/mainloop/fullgame.',native_executions=0,complete_games=0,artifacts={n:sha(out/n)for n in names})
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=len(diff),first=diff[:4],process=terminal)),flush=True)
 if not process_ok or not runtime_ok or diff:raise SystemExit(1)
if __name__=='__main__':main()
