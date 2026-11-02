#!/usr/bin/env python3
"""Independent139 naturalNPC→two922→full913 death/XP knownness projection."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,os,random,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_death139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from load_world_position139_inputs import load_world139_canonical
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.initial_state139 import ConstructorInput139,initialize_empty_profile139
from core_spec.natural_npc139 import NaturalNPCInput139,create_four_natural_normals139
from core_spec.death139 import OrdinaryDamageState139,DefaultDeathSources139,cast_cleave_with_ordinary_death139
from core_spec.death_pickups139 import PickupVector139
from core_spec.hit_events139 import produce_default_cleave_hit_sources139
from core_spec.cast139 import CleaveDefinition139
from core_spec.world_position139_data import ZONE_GEOMETRY139
from core_spec import binary32 as f
CANONICAL=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model';CANONICAL_SHA='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
SNAPSHOT=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_world6786.memory';SNAPSHOT_SHA='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
DEFINITION88='0000000000000000000000003aa5590006000000ccb5590006000000d2b5590016000000e8b55900030000004d03000000003c420000c03f0000e04000000000030000000000000000000000000000000000000005000000'

def closure():
 files=set(('scripts/check_death139.py','scripts/build_death139_oracle.py','scripts/run_death139_oracle.mjs','scripts/load_world_position139_inputs.py','scripts/production_closure135.py','scripts/source_closure137.py'))|set(production_sources135(ROOT,'core_spec.death139','core_spec.initial_state139','core_spec.natural_npc139','resource_spec.world_query135'))
 while True:
  try:return sorted(files),verify_local_source_closure(sorted(files))
  except AssertionError as e:
   pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in files;files.add(pair[1])
def corpus(world,pilot):
 cx,cy=ZONE_GEOMETRY139[0][:2];ground=world.height(cx,cy);assert ground.found
 initial=initialize_empty_profile139(ConstructorInput139(1,1,0,1442695040888963407,0,ground.value_bits));owned=bytes.fromhex(initial.owned_records_hex[0]);derived=initial.stats_result['derived_bits'];definition=CleaveDefinition139(5882740,b'cleave',bytes.fromhex(DEFINITION88))
 profile=[None]*376
 for o in(160,*range(260,336,4)):profile[o:o+4]=bytes(4)
 profile[344]=profile[345]=1
 hit=produce_default_cleave_hit_sources139(tuple(profile),(owned,),bytes.fromhex(initial.racial_record_hex));sources=DefaultDeathSources139(hit,(),(),(),(),());rows=[]
 def add(group,words=None,counter=10,backing=(),action='near_first'):
  actual_words=initial.rng_words if words is None else words;npc=create_four_natural_normals139(NaturalNPCInput139(tuple(actual_words),counter,initial.player_xyz,(0,0),tuple(backing),None),world);last=npc['answers'][-1];records=tuple(tuple(row)for row in last['records432_cells']);selected=records[0 if action=='near_first'else 1];player=tuple(struct.unpack('<I',bytes(selected[o:o+4]))[0]for o in(316,320,324));state=OrdinaryDamageState139(records,tuple(last['rng_words']),0,1,0,(),0,0,last['counter'],1,0,derived['1536'],derived['1536'],PickupVector139(()),sources);sets=((),(),());stages=[];events=[]
  for stage in range(2):
   r=cast_cleave_with_ordinary_death139(state,player,derived,definition,owned,sets,world);state,sets=r.state,r.spell_sets
   stages.append(dict(success=r.success,records432_cells=[list(x)for x in state.records432],rng_words=list(state.rng_words),accounted_total_bits=str(state.accounted_total_bits),spell_sets=[list(x)for x in sets],owned80_hex=owned.hex(),launch306_packets=[]if r.launch306_hex is None else[[306,r.launch306_hex]],player_xyz=list(player),phase2587=1,spell_totals64=[[key,str(value)]for key,value in state.spell_totals64],kills1084=state.kills1084,elites1088=state.elites1088,counter2408=state.counter2408,movement_sequence2412=state.movement_sequence2412,killcost2420_bits=state.killcost2420_bits,player_hp1440_bits=state.player_hp1440_bits,maximum1536_bits=state.maximum1536_bits,xp1436=0,pickup_capacity=state.pickups.capacity,pickup_count=state.pickups.count,pickups56_cells=[list(x)for x in state.pickups.storage],known_packets=[list(x)for x in r.known_packets]))
   events.append(dict(selected_ids=[str(x)for x in r.selected_ids],hits=[dict(guid=str(g),damage_bits=amount,critical=critical,dead=h.dead,reward_events=h.reward_events,direct_reward_draws=h.direct_reward_draws,event_calls994=None if h.event_tail_plan is None else h.event_tail_plan.calls994)for g,amount,critical,h in r.hits],private_selection_selfchecks=r.private_selection_checks))
  inp=dict(id=len(rows),rng_words=None if words is None else list(words),counter=counter,action=action,repeats=2,gentle_owned_multiplier=False,initial_backing=list(backing))
  actor=dict(derived_bits=derived,owned80_hex=owned.hex(),initial_rng=list(initial.rng_words),player_xyz=list(initial.player_xyz),phase2587=0,source_id='0')
  rows.append(dict(id=len(rows),group=group,input=inp,actor_before=actor,expected=stages,model_diagnostic=events,natural_producer_expected=npc['answers'],profile_knowncells_input=profile))
 add('default_constructor_rng_secondcleave_death')
 add('explicit_rng_secondcleave_death',(1,2,3,4),backing=tuple(bytes((17*j+13*k)&255 for k in range(432)).hex()for j in range(4)))
 if not pilot:
  rnd=random.Random(0x139913)
  for j,words in enumerate([(0,0,0,0),(0xffffffff,0x80000000,123,999)]+[tuple(rnd.getrandbits(32)for _ in range(4))for _ in range(10)]):
   add('death_reward_rng_matrix',words,counter=(0,0xffffffff,0xffffff,0x1000000)[j%4],action='near_second'if j%2 else'near_first')
 return json.loads(json.dumps(rows))
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files};assert sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
 events=[];forbidden=[];live=True
 def audit(event,args):
  if event!='open'or not live or not isinstance(args[0],(str,bytes,os.PathLike)):return
  p=Path(os.fsdecode(args[0])).resolve();mode=args[1];flags=args[2];read=(isinstance(mode,str)and'r'in mode)or(mode is None and isinstance(flags,int)and flags&3==os.O_RDONLY)
  if read:
   okay=p.suffix.lower()not in('.memory','.wasm','.wat','.exe');events.append(dict(path=str(p),allowed=okay))
   if not okay:forbidden.append(str(p));raise RuntimeError('Originalinputdeniedduringindependentexpectation')
 sys.addaudithook(audit)
 try:world,provenance=load_world139_canonical(CANONICAL,CANONICAL_SHA);rows=corpus(world,args.phase=='pilot')
 finally:live=False
 assert not forbidden and before=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('death139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out);assert m['definition']['raw88_hex']==DEFINITION88
 for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 save(out/'expected.json',rows);save(out/'inputs.json',[r['input']for r in rows]);save(out/'config.json',dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,game_pointer=14685248,app_pointer=14680072,input_path=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json')));save(out/'expectation-read-audit.json',dict(kind='Pythonopenaudit_notOSsyscall',events=events,forbidden=forbidden));frozen={n:sha(out/n)for n in('expected.json','inputs.json','config.json','manifest.json',m['module_file'])};save(out/'prepared.json',dict(source_before=before,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_inputs_contain_expected=False,world_provenance=provenance,profile_source='explicitcomponentknownemptyprofilefields;notnaturalApp'))
 command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_death139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
 with(out/'stdout.jsonl').open('wb')as so,(out/'stderr.log').open('wb')as se:
  p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=60))
  try:p.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-start,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'process-terminal.json',terminal);actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];diff=[];known=unknown=nonzero=0;known56=unknown56=nonzero56=0;knownpackets=0
 for e,a in zip(rows,actual):
  assert e['id']==a['id']and len(a['cast_stages'])==len(e['expected'])==2
  if e['actor_before']!=a['actor_before']:diff.append(dict(id=e['id'],field='actor_before',expected=e['actor_before'],actual=a['actor_before']))
  for stage,(ep,ob)in enumerate(zip(e['expected'],a['cast_stages'])):
   for key in(set(ep)|set(ob))-{'records432_cells','records432_hex','pickups56_cells','pickups56_hex','known_packets','new_packets'}:
    if ep.get(key)!=ob.get(key):diff.append(dict(id=e['id'],stage=stage,field=key,expected=ep.get(key),actual=ob.get(key)))
   for cells,hx in zip(ep['records432_cells'],ob['records432_hex'],strict=True):
    raw=bytes.fromhex(hx);assert len(cells)==len(raw)==432
    for offset,v in enumerate(cells):
     if v is None:unknown+=1;nonzero+=raw[offset]!=0
     else:
      known+=1
      if v!=raw[offset]:diff.append(dict(id=e['id'],stage=stage,field='record432',offset=offset,expected=v,actual=raw[offset]))
   for cells,hx in zip(ep['pickups56_cells'],ob['pickups56_hex'],strict=True):
    raw=bytes.fromhex(hx);assert len(cells)==len(raw)==56
    for offset,v in enumerate(cells):
     if v is None:unknown56+=1;nonzero56+=raw[offset]!=0
     else:
      known56+=1
      if v!=raw[offset]:diff.append(dict(id=e['id'],stage=stage,field='pickup56',offset=offset,expected=v,actual=raw[offset]))
   cursor=0
   for packet in ep['known_packets']:
    match=next((j for j in range(cursor,len(ob['new_packets']))if ob['new_packets'][j]==packet),None)
    if match is None:diff.append(dict(id=e['id'],stage=stage,field='known_packet_ordered_subsequence',expected=packet,actual=ob['new_packets']))
    else:cursor=match+1;knownpackets+=1
 assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',diff);runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None;names=('expected.json','inputs.json','config.json','manifest.json','stdout.jsonl','stderr.log','process-terminal.json','owned-process.json','expectation-read-audit.json','differences.json')+(('runtime.json',)if runtime else())
 report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed=len(actual),differences=len(diff),source_before=before,source_after=before,source_import_edges=edges,world_provenance=provenance,expected_before_original=True,expectation_reads_forbidden=forbidden,process=terminal,runtime=runtime,comparison=dict(known432bytes=known,unknown432bytes=unknown,observed_nonzero_unknown432=nonzero,known56bytes=known56,unknown56bytes=unknown56,observed_nonzero_unknown56=nonzero56,ordered_known_packets=knownpackets),full913_internal_calls_notdirectlyinstrumented=True,known_packet_subsequence_not_full_stream=True,scope='FulloriginalsameGame5719x4→two922/913ordinarydeath→XP/currencyrecords;controlledphase/playeraction/defaultfullHPactor/emptyconstructorsources/healthyv2world;notnaturalApp/full1108/game',native_executions=0,complete_games=0,artifacts={n:sha(out/n)for n in names})
 save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=len(diff),first=diff[:4],process=terminal)),flush=True)
 if p.returncode or len(actual)!=len(rows)or diff:raise SystemExit(1)
if __name__=='__main__':main()
