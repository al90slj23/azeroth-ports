#!/usr/bin/env python3
"""Different-author readonly current2372 default first Guardian source."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
 if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen')or event=='import'and str(args[0]).startswith(('core_spec','resource_spec')):
  AUDIT['forbidden_execution']+=1;raise RuntimeError(event)
sys.addaudithook(audit)
import review_ordinary_family139 as F
C=F.C;U=F.U;G=F.G;O=F.O;D=F.D;AI=F.AI;Spawn=F.Spawn;Npc=F.S.N
ROOT=F.ROOT;SOURCE=F.SOURCE;PROFILE=F.PROFILE;WASM=F.WASM
sha=F.sha;parse_module=F.parse_module;local_closure=F.local_closure;fp=F.fp;bits=F.bits
BATCH=ROOT/'evidence/special-world139-full-20261102T162951.190698Z'
HAND='167a065e2964e7696a40408c9b37074e05eaac16f3eeae7cc3b24a3cc089276b'
COMP='5b0382d7d7c1c2959208a9a2190e0ba699d77436342a0acde32e702a2b7c35db'
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
q=lambda b,o=0:struct.unpack_from('<Q',b,o)[0]
def load(p):
 assert Path(p).name!='expected.json';return json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def scalars(now,definition,ctx):
 minute=C.div(now,bits(60.));assert 0<=C.rational(minute)<=3
 a,b=ctx['milestone'];milestone=C.mul(C.add(C.div(C.mul(minute,0x3ecccccd),a),0x3f19999a),b)
 curve=C.add(C.add(C.mul(minute,0x3df5c28f),C.ONE),C.mul(minute,C.mul(minute,0x3c1374bc)))
 base=C.mul(C.mul(C.mul(ctx['zone136'],curve),u(definition,40)),bits(2.5));floor=C.mul(ctx['zone136'],C.mul(milestone,0x3f19999a));hp=C.mul(base if C.rational(base)>C.rational(floor)else floor,bits(3.))
 for _ in range(4):hp=C.mul(hp,C.ONE)
 curve=C.add(C.add(C.mul(minute,0x3da3d70a),C.ONE),C.mul(minute,C.mul(minute,0x3b83126f)));attack=C.mul(u(definition,44),C.mul(curve,AI.sqrt32(ctx['zone136'])));attack=C.mul(attack,0x3fb33333)
 for _ in range(3):attack=C.mul(attack,C.ONE)
 return hp,attack

def birth(index,slot,record,p,s,physical,count,now,ctx,counts):
 d=ctx['definitions'][index];header,abilities,records=ctx['guardian'][index];xyz=tuple(D.read(record,k)for k in[16,20,24]);hp,attack=scalars(now,d,ctx);scale=C.mul(u(d,32),0x3faccccd);s['counter']=(s['counter']+1)&C.M;entry=u(d,24);guid=0xf130000000000000|((entry&0xffffff)<<24)|(s['counter']&0xffffff)
 fields={0:guid&C.M,1:guid>>32,2:9,3:entry,4:scale,16:0,17:0,22:math.ceil(C.rational(hp)),28:math.ceil(C.rational(hp)),34:min(p['g']['level']+3,63),35:14,36:256,46:0,126:2000,127:2000,129:C.mul(scale,0x3f000000),130:C.mul(scale,0x3fc00000),131:u(d,28),132:u(d,28),134:bits(5.),135:bits(10.),145:C.ONE}
 masks=[sum(1<<(k%32)for k in fields if k//32==j)for j in range(5)];values=bytes([5])+struct.pack('<5I',*masks)+struct.pack('<'+'I'*len(fields),*(fields[k]for k in sorted(fields)))
 heading=Npc.heading_ref(fp(C.sub(p['player'][1],xyz[1])),fp(C.sub(p['player'][0],xyz[0])),ctx['heading']);movement=bytes([3,112])+struct.pack('<2I',0,0)+struct.pack('<4I',*xyz,bits(heading))+struct.pack('<I6II',0,*ctx['speeds'],1);packet=[169,(struct.pack('<IBB',1,0,3)+C.packguid(guid)+movement+values).hex()]
 random=G.Sampler(s['words']);yaw=random.uniform(0x40c90fdb);s['words']=list(random.words);counts['uniform_yaw_draws']+=random.draws
 for _ in range(10000):
  v,s['words']=C.nextword(s['words']);counts['variant_draws']+=1
  if v&0x02000000==0:break
 else:raise AssertionError('Bounded variant RNG')
 raw=bytearray(432)
 def put(o,v):struct.pack_into('<I',raw,o,v)
 for o in[40,244]:put(o,C.M)
 for o,v in{64:3,72:3,76:abilities,80:3,84:abilities,88:3,92:slot,96:header,280:0,284:5830904+72*index,288:hp,292:hp,296:attack,300:u(d,52),304:u(d,48),308:C.add(C.mul(scale,0x3f99999a),0x400ccccd),312:scale,340:now,344:0,348:now,352:C.mul(u(d,48),0x3f000000),404:C.add(yaw,0)}.items():put(o,v)
 struct.pack_into('<Q',raw,112,guid);struct.pack_into('<Q',raw,236,4)
 for off in[316,328]:struct.pack_into('<3I',raw,off,*xyz)
 raw[424]=d[68]
 if count==len(physical):physical.extend([[None]*432 for _ in range(max(4,2*count)-count)]);counts['NPC_vec_growth']+=1
 row=physical[count]
 for off,n in[(0,4),(8,4),(16,4),(40,4),(64,4),(72,37),(112,136),(280,147)]:row[off:off+n]=raw[off:off+n]
 row[68:72]=[None]*4
 timer=dict(unit_slot=count,guid=str(guid),capacity=3,count=3,timers_bits=[C.mul(u(r,40),0x3f000000)for r in records],header_pointer=header,ability_pointer=abilities)
 counts['Guardian_creates']+=1;counts['logical_timers']+=3
 return packet,timer,guid

def update(p,s,physical,count,special,state,now,ctx,counts):
 packets=[]
 for slot,row in enumerate(special):
  if D.read(row,0,8)or C.rational(now)<C.rational(D.read(row,32)):continue
  assert now==bits(20.),'Only first exact due20 constructor domain'
  index=D.read(row,28);packet,timer,guid=birth(index,slot,row,p,s,physical,count,now,ctx,counts);packets.append(packet);state['timers'].append(timer);count+=1;row[:16]=struct.pack('<QQ',1,guid);state['selected392']=0
 active=[j for j,row in enumerate(special)if D.read(row,0,8)]
 if active:
  target=min(active,key=lambda j:(C.totalkey(AI.distance([D.read(special[j],k)for k in[16,20]],p['player'][:2])),j))
 else:target=min(range(len(special)),key=lambda j:(C.totalkey(D.read(special[j],32)),j))
 if not(state['selected392']and state['target396']==target and state['announced2565']and C.rational(C.sub(now,state['stamp2392_bits']))<=300):
  row=special[target];name=ctx['names'][D.read(row,28)];text=name+(' (Guardian)'if D.read(row,0,8)else"'s lair (empty)");payload=struct.pack('<5I',99,D.read(row,16),D.read(row,20),6,0)+text.encode()+bytes(1);packets.append([548,payload.hex()]);state.update(selected392=1,target396=target,announced2565=1,stamp2392_bits=now);counts['notifications548']+=1
  length=20+len(text.encode());capacity=max(64,length)if length>32 else 32
  if length==capacity:capacity*=2
  assert capacity==64
 state['navigation2564']=1;state['protection2576']=0;s['rows']=copy.deepcopy(physical[:count]);p['NPC']=copy.deepcopy(s['rows']);p['g']['rng_words']=list(s['words']);counts['full2372']+=1
 return physical,count,special,state,packets


def main():
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(SOURCE)==WASM and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
 hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');rt=load(BATCH/'runtime.json');authors=hand['author_files'];assert len(authors)==8
 for n,h in authors.items():assert sha(ROOT/n)==h
 sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==95 and sum(n.startswith('reconstruction/')for n in sources)==80
 for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
 edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==360
 for table in[comp['frozen'],prep['frozen']]:
  for n,h in table.items():assert sha(BATCH/n)==h
 assert comp['cases']==comp['completed_cases']==3 and comp['differences']==0 and comp['expected_before_original']and not comp['original_input_contains_expected']and not comp['forbidden_model_reads']and not load(BATCH/'expectation-read-audit.json')['forbidden']
 oldref=ROOT/'evidence/ordinary-family139-independent-owned-20261102T162445.590649Z/review/review.json';assert sha(oldref)=='cd478dda3b9bb4c943c1f97a746ea15f7a698b9dcaf3b5447299c8d51a1d114d';helpers=load(oldref)['helper_sha256'];helpers['scripts/review_ordinary_family139.py']='aebfd5bafa00be2fe3253e42f6d6013ff2d1cf109f13267fa56ef44da2419f93'
 for n,h in helpers.items():assert sha(ROOT/n)==h
 assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
 ctx=Spawn.load_context();data=ctx['data'];raw=ctx['raw'];module=ctx['module'];zone=data(5871348,152);ctx.update(definitions=[data(5830904+72*j,72)for j in range(12)],zone136=u(zone,136),milestone=struct.unpack_from('<2I',data(u(zone,72),72),48),names={},guardian={})
 assert u(zone,72)==5833692 and ctx['milestone']==(bits(3.),bits(3600.))and ctx['zone136']==1062333317
 for index,header in[(9,5899360),(10,5899388),(11,5899416)]:
  d=ctx['definitions'][index];p,n=struct.unpack_from('<2I',d,16);ctx['names'][index]=data(p,n).decode();h=data(header,28);ability,n=struct.unpack_from('<2I',h);assert n==3 and u(h,12)==0 and u(h,24)==u(d,24);ctx['guardian'][index]=(header,ability,[data(ability+44*j,44)for j in range(n)])
 private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
 for a,b in zip(module['sections'],private['sections'],strict=True):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
 assert private['exports']==module['exports']+[tuple(v)for v in m['added_exports']]and len(module['imports'])==882 and[(x['module'],x['name'],x['type_index'])for x in module['imports']]==[(x['module'],x['name'],x['type_index'])for x in m['original_imports']]
 bindings={};texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as f:
  for idx,claim in m['functions'].items():
   a,z=module['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();f.seek(lo);wat=f.read(hi-lo);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());assert all(proof[k]==claim[k]for k in proof)and wat==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=proof;texts[int(idx)]=wat.decode();(out/f'{idx}.wat').write_bytes(wat)
 assert len(bindings)==28 and bindings=={k:{z:v[z]for z in['body_sha256','WAT_sha256']}for k,v in m['special_trace']['functions'].items()}
 for key,claim in m['special_trace']['static_reads'].items():
  address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==claim['sha256']
 for d in m['special_trace']['declarations']:
  index,p,rawhex,name,header,hx,ability,records=d;assert p==5830904+72*index and data(p,72).hex()==rawhex and ctx['names'][index]==name and data(header,28).hex()==hx and ability==ctx['guardian'][index][1]and [r.hex()for r in ctx['guardian'][index][2]]==records
 assert all(v in texts[2372]for v in['call 16381','call 42922','call 1586','call 33347','i32.store offset=392','i32.store offset=396','i32.store8 offset=2565','i32.const 548','i64.store offset=112','i32.store offset=68'])
 assert all(v in texts[16381]for v in['i32.load offset=1092','i32.load8_u offset=387','f32.const 0x1.26e978p-7','f32.const 0x1.8p+1'])and all(v in texts[42922]for v in['f32.sqrt','f32.const 0x1.666666p+0','i32.load8_u offset=387'])
 assert 'i64.const 0\n                  i64.store offset=2811 align=1'in texts[1600]and'i64.load offset=2812 align=1\n                  i64.store offset=1177 align=1'in texts[1600]and'i32.const 104\n                  i32.add\n                  local.get 1\n                  i32.const 376\n                  memory.copy'in texts[1600]
 for h in[5899360,5899388,5899416]:assert'i32.const '+str(h)in texts[33347]
 counts=Counter();traces=[]
 def cells(label,want,hx):
  seen=bytes.fromhex(hx);assert len(want)==len(seen)
  for j,(v,b)in enumerate(zip(want,seen,strict=True)):
   if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
   else:assert v==b,(label,j,v,b);counts[label+'_known']+=1
 def player(obs,p,flag,label):
  want=U.project(p);assert obs['capture']['projection']==want['growth'],(label,'growth');assert G.tree_fields(obs['capture'],bytes.fromhex(obs['capture']['raw_game2592_hex']))==want['growth']['player_fields']
  for k in['racial80_hex','scalar','source_flags','spell_sets']:assert obs[k]==want[k],(label,k)
  for k in['live','aura']:
   for f in['capacity','count']:assert obs[k][f]==want[k][f]
   if k=='aura':assert obs[k]['flag2569']==(flag if want[k]['flag2569']is None else want[k]['flag2569'])
   for row,hx in zip(want[k]['storage'],obs[k]['storage'],strict=True):cells(k,row,hx)
  game=bytes.fromhex(obs['capture']['raw_game2592_hex']);assert game[387]==0 and u(game,1092)==0 and u(game,2516)==C.ONE and u(game,400)==0 and game[2568]==game[2582]==game[2576]==0
 def special_view(obs,state,before=False):
  for k,v in state.items():
   if v is not None:assert obs[k]==v,('special',k,v,obs[k])
 def combat(obs,p,s,physical):
  values=dict(rng_words=list(s['words']),accounted_total_bits='0',spell_sets=p['sets'],owned80_hex=p['g']['owned_records80_hex'][0],player_xyz=list(p['player']),phase2587=1,spell_totals64=[],kills1084=0,elites1088=0,counter2408=s['counter'],movement_sequence2412=1,killcost2420_bits=0,player_hp1440_bits=p['g']['current_hp_bits'],maximum1536_bits=p['g']['derived_bits']['1536'],xp1436=0,pickup_capacity=len(s['pickups']),pickup_count=2)
  for k,v in values.items():assert obs[k]==v,(k,v,obs[k])
  for row,hx in zip(physical,obs['records432_hex'],strict=True):cells('NPC',row,hx)
  for row,hx in zip(s['pickups'],obs['pickups56_hex'],strict=True):cells('pickup',row,hx)
 cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==3 and[c['app_seed_u64']for c in cases]==['0','1','5']
 for case,A in zip(cases,actual,strict=True):
  full,p,s,ai,L,physical,count=F.initial_reference(case,ctx);op=full['projection'];special=copy.deepcopy(op['special']['storage']);state=dict(selected392=0,target396=None,announced2565=0,stamp2392_bits=0,navigation2564=1,protection2576=0,timers=[]);flag=A['initial']['aura']['flag2569'];player(A['initial'],p,flag,'initial');cells('openingGame',full['known_Game2592'],A['opening']['raw_game2592_hex']);assert A['opening']['packets']==op['packets']and A['initial']['capture']==A['opening']and A['stack_after']==1048576 and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248
  previous=A['initial'];stages=[];assert len(case['steps'])==len(A['stages'])==5
  for j,(control,obs)in enumerate(zip(case['steps'],A['stages'],strict=True)):
   now=control['now_bits'];assert now==bits([.1,19.9,20.,20.1,30.1][j]);assert control['follow_special_index']==(1 if j==4 else None);xyz=[D.read(special[1],k)for k in[16,20,24]]if j==4 else op['player_xyz'];assert control['player_xyz']==xyz
   p['player']=tuple(xyz);p['g']['now_bits']=now;p['scalar']['2352']=now;prior=bytearray.fromhex(previous['capture']['raw_game2592_hex']);struct.pack_into('<3I',prior,1416,*xyz);U.put(prior,2352,now);assert prior.hex()==obs['before']['capture']['raw_game2592_hex'];counts['Game_input_inheritance_bytes']+=2592;player(obs['before'],p,flag,'before');special_view(obs['before_special'],state)
   oldrows=copy.deepcopy(physical);oldcount=count;physical,count,special,state,packets=update(p,s,physical,count,special,state,now,ctx,counts);player(obs['after'],p,flag,'after');special_view(obs['special'],state);combat(obs['combat'],p,s,physical);assert packets==obs['new_packets'];counts['complete_packets']+=len(packets);counts['complete_packet_bytes']+=sum(len(h)//2 for k,h in packets)
   units=obs['after']['capture']['background']['units'];assert units['capacity']==len(physical)and units['count']==count
   oldraw=obs['before']['capture']['background']['units']['storage']
   for k,(row,hx)in enumerate(zip(physical,units['storage'],strict=True)):
    cells('physicalNPC',row,hx)
    if k<len(oldraw):
     replay=bytearray.fromhex(oldraw[k])
     for off,v in enumerate(row):
      if v is not None:replay[off]=v
     assert replay.hex()==hx;counts['NPC_fullphysical_replay_bytes']+=432
   assert units['storage'][:4]==A['opening']['background']['units']['storage'];counts['original4NPC_preserved_bytes']+=1728
   for row,hx,oldhx in zip(special,obs['after']['capture']['background']['special']['storage'],obs['before']['capture']['background']['special']['storage'],strict=True):
    cells('special40',row,hx);replay=bytearray.fromhex(oldhx)
    for off,v in enumerate(row):
     if v is not None:replay[off]=v
    assert replay.hex()==hx;counts['special_fullphysical_replay_bytes']+=40
   for k in['pickups','windows','boundaries','auxiliary','claims']:assert obs['after']['capture']['background'][k]==A['opening']['background'][k]
   beforegame=bytes.fromhex(obs['before']['capture']['raw_game2592_hex']);aftergame=bytes.fromhex(obs['after']['capture']['raw_game2592_hex']);allowed=set()
   for off,n in[(392,8),(1720,16),(1784,12),(1880,12),(2392,4),(2408,4),(2565,1)]:allowed.update(range(off,off+n))
   assert all(a==b for k,(a,b)in enumerate(zip(beforegame,aftergame,strict=True))if k not in allowed);counts['Game_output_nonowned_preserved_bytes']+=2592-len(allowed)
   for packet,detail in zip(packets,obs['packet_details'],strict=True):
    assert detail['opcode']==packet[0]and detail['length']==len(packet[1])//2 and detail['capacity']>=detail['length']
    if packet[0]==548:assert detail['capacity']==64
   for timer in state['timers']:
    row=bytes.fromhex(units['storage'][timer['unit_slot']]);assert u(row,64)==u(row,72)==3 and u(row,76)==timer['ability_pointer']and u(row,96)==timer['header_pointer']and u(row,68)>0
   stages.append(dict(now_bits=now,special=copy.deepcopy(state),packets=packets,count=count,rng_words=list(s['words'])));previous=obs['after']
  assert[state['target396']for state in[s['special']for s in stages]]==[0,0,2,2,1]
  assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]
  assert len(A['timer_pointer_observations'])==20 and all(v['observed_only']for v in A['timer_pointer_observations']);counts['observed_only_timer_pointer_snapshots']+=20;traces.append(dict(seed=case['app_seed_u64'],stages=stages));counts['cases']+=1
 assert counts['cases']==3 and counts['full2372']==15 and counts['Guardian_creates']==12 and counts['logical_timers']==36 and counts['notifications548']==9 and counts['complete_packets']==21 and counts['complete_packet_bytes']==2571
 assert rt==comp['runtime']and rt['fresh_instances']==3 and rt['full_calls']['2372']==15 and sum(rt['full_calls'].values())==24 and rt['full_calls']['2945']==rt['full_calls']['1600']==rt['full_calls']['1108']==3 and rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None
 assert len(rt['target_and_setup_returns'])==24 and all(v['returned']and v['before']==v['after']==1048576 for v in rt['target_and_setup_returns'])and len(rt['world_source_checks'])==21 and all(v['ranges']==2318 and v['unchanged']for v in rt['world_source_checks'])and rt['stack_checks']==39 and rt['allocator_calls']==15 and rt['output_bytes']==(BATCH/'actual.jsonl').stat().st_size
 assert rt['peak_memory_bytes']==177078272<=rt['memory_cap_bytes']==268435456 and not any(rt[k]for k in['old_Game_used_as_target','App_or_world_Rc_producer_executed','NPC_definition_HP_position_status_or_storage_writes','HP_RNG_readiness_source_or_flag_injections'])and rt['native_executions']==rt['full_mainloop_frames']==rt['complete_games']==0
 term=load(BATCH/'owned-terminal.json');assert term==hand['process']==comp['process']and term['exit_code']==0 and term['pid_missing']and term['pgid_missing']
 for table in[authors,sources,helpers]:
  for n,h in table.items():assert sha(ROOT/n)==h
 assert not AUDIT
 result=dict(accepted=True,scope='current1392372 defaultfirst20s Guardian creation/selection/notify only',author_handoff_sha256=HAND,comparison_sha256=COMP,reviewer_sha256=sha(Path(__file__)),source_sha256=WASM,author_files=authors,helper_sha256=helpers,current_body_bindings=bindings,source_counts=dict(files=95,production=80,edges=360,bodies=28),formal_counts=dict(fresh_instances=3,full2372=15,target_entries=15,setup2945_1600_1108=9,direct_entries=24,author_program_executions=0,original_executions=0),counts=dict(counts),traces=traces,original_process=term,author_expected_values_read=False,full884_frames=0,complete_games=0,seconds=time.monotonic()-start,limits=['Explicitclock.1/19.9/20/20.1/30.1 andplayerfollowactualspecial1;notnatural30seconds/full884.', 'TwelveGuardian9/10/11/9 initialspawns andnearesttarget0→2→1/three548perseed only;noGuardianAI/abilityexecution/due>21respawn150.', 'Pointer68andpacket169capacity179 observedonly;36logicaltimers independentlyderivedfromcurrent44Babilityrecordsandallknowndeclared432bytes checked;newallocationNone notfilled.', 'Complete21packetpayloads2571B and548capacity64 predicted;notallpacketallocation/heapaddresses.', 'G387=profile371withinreal376copyandG1092=zero-scratchunpackedaggregate sourcebound;defaultG2516/field400/endless/mode only,noalternative scaling.', 'Currentresource-onlycontext notindependentApp/worldbootstrap;World hash/booleaninstrumentation notrawpairs.', 'Existing4NPC/twoRunes/windows/special/bounds andwholeGameoutsideownedwrite-ranges preserved;independentUI/save/network/nativeWindows/completegame remainPending.'])
 save(out/'review.json',result);print(json.dumps(dict(accepted=True,counts=dict(counts),formal_counts=result['formal_counts'],seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
