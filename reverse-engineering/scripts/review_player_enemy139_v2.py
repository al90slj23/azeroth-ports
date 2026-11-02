#!/usr/bin/env python3
"""Independent read-only current925 lifetime/order review; never runs author/original."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import copy,json,struct,math,time,sys,sqlite3,hashlib,os
sys.dont_write_bytecode=True
import review_player_autocast139 as R
import review_enemy_ai_dead139_v2 as LIFE
from review_combat139 import sha,parse_module,local_closure
H=R.H;AI=R.AI;C=R.C;U=R.U;D=R.D;T=R.T;G=R.G;W=R.W;O=R.O
fp=R.fp;load_world=R.load_world;initial_record=R.initial_record;WASM=R.WASM
ROOT=Path(__file__).resolve().parents[1]
SOURCE=R.SOURCE;PROFILE=R.PROFILE
BATCH=ROOT/'evidence/player-enemy139-v2-oracle-20261102T135124.692057Z'
HAND='153f9f8f6696bbcc2b418535a89c1178555b2aecbef679fb834b64f942bde5d6'
COMP='c062cf804b1f9bf9a21d654ead648b407fdd9c863fe7ad4c14023862194d03c6'
load=R.load;save=R.save;u=R.u


player_step=LIFE.player_step
enemy_step=LIFE.enemy_step
combat=LIFE.combat
ai_projection=LIFE.ai_projection

def player_stage(p,s,L,now,dt,ctx,counts):
 p['g']['now_bits']=now;p['scalar']['2352']=now
 keep=[i for i in range(p['count'])if C.rational(now)<C.rational(U.read(p['live'][i],24))];expired=[U.read(p['live'][i],20)for i in range(p['count'])if i not in keep]
 if expired:
  old=copy.deepcopy(p['live'])
  for j,i in enumerate(keep):p['live'][j]=old[i]
  p['count']=len(keep);U.recalculate(p,ctx['classes'],ctx['races']);U.sync_aura(p)
 _,_,heals=H.regen(p,L,now,dt);counts['positive_Regen']+=len(heals)
 packets,events,castheals=R.scheduler(p,s,L,now,dt,ctx['world'],ctx['scalars'],ctx['speeds'],ctx['normal'],ctx['defs'],ctx['perception'],ctx['classes'],ctx['races'],counts)
 if expired:events.insert(0,['expiry',expired])
 return packets,events,heals+castheals,expired

def main():
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
 assert sha(SOURCE)==WASM and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
 hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json')
 authors=hand.get('author_files',hand.get('frozen_author_files'));assert len(authors)==6
 for n,h in authors.items():assert sha(ROOT/n)==h
 sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==91 and sum(n.startswith('reconstruction/')for n in sources)==77
 assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(comp['source_import_edges'])==351
 for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
 for table in(comp['frozen'],comp['artifacts'],prep['frozen']):
  for n,h in table.items():assert sha(BATCH/n)==h
 assert comp['differences']==0 and comp['cases']==comp['completed_cases']==3 and prep['expected_before_original']and not prep['original_input_contains_expected']
 raw=SOURCE.read_bytes();original=parse_module(raw)
 def data(address,size):
     result=bytearray(size)
     for at,pos,n in original['data_segments']:
         if at is None:continue
         lo,hi=max(address,at),min(address+size,at+n)
         if lo<hi:result[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
     return bytes(result)
 text=lambda p,n:data(p,n).decode();word=lambda p:u(data(p,4));abilities={}
 for i in range(114):
     p=5882740+88*i;b=data(p,88);abilities[text(u(b,12),u(b,16))]=(p,b,tuple(data(u(b,36),u(b,40))))
 cls=data(5877920,108);assert u(cls,80)==0x3c75c28f
 classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)};kit=[text(p,n)for p,n in struct.iter_unpack('<II',data(u(cls,32),8*u(cls,36)))];defs={k:abilities[k]for k in kit}
 race=data(5874636,44);racial_name=text(u(race,24),u(race,28));races={1:dict(ability_pointer=abilities[racial_name][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
 zone=data(5871348,152);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];heading=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));spawn_speeds=list(speeds);spawn_speeds[1]=1088421888;normal=data(5830904,72);eligible=[j for j in range(12)if word(5830904+72*j+68)==1 and math.isfinite(fp(word(5830904+72*j+64)))];minutes=word(u(zone,72)+336);cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20));definition=data(5882916,88);perception=data(5891892,88)
 wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));scalars['heading_bits']=u(zone,116)
 literal={}
 for p in(1592624,1591852):
     b=data(p,44);literal['regen'if p==1592624 else'leech']={str(k):text(u(b,k),u(b,k+4))for k in(0,8,16,24,32)}
 assert literal['regen']['0']=='regen'and literal['leech']['0']=='leech'

 counts=Counter();bindings={};reference=[];breakdown_seen={}
 def cells(label,want,hx):
     seen=bytes.fromhex(hx);assert len(want)==len(seen)
     for v,w in zip(want,seen):
         if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(w)
         else:assert v==w,(label,v,w);counts[label+'_known']+=1
 def player(obs,state,label):
     want=U.project(state);cap=obs['capture'];assert cap['projection']==want['growth'],(label,'growth');assert G.tree_fields(cap,bytes.fromhex(cap['raw_game2592_hex']))==want['growth']['player_fields']
     for k in('racial80_hex','scalar','source_flags','spell_sets'):assert obs[k]==want[k],(label,k)
     for k,width in(('live',32),('aura',16)):
         for field in('capacity','count')+(('flag2569',)if k=='aura'else()):assert want[k][field]==obs[k][field],(label,k,field)
         for row,hx in zip(want[k]['storage'],obs[k]['storage'],strict=True):assert len(row)==width;cells(k,row,hx)
     game=bytes.fromhex(cap['raw_game2592_hex']);assert u(game,1440)==state['g']['current_hp_bits']and u(game,1652)==state['scalar']['1652'];assert game[387]==0
     assert all(u(game,p)==0 for p in(1676,1700,2032,176,600,2056,2044,648,660,2116)),'Actualdefaultsourceownersnotempty'
     counts['logical_player_maps']+=1
 def accounting(obs,L,label,player_obs=None):
     for k,v in L.items():assert obs[k]==v,(label,k,v,obs[k])
     aggregate=bytes.fromhex(obs['accounting_struct68_hex']);assert len(aggregate)==68 and struct.unpack_from('<Q',aggregate,16)[0]==int(L['accepted_count1016'])
     if player_obs is not None:
         game=bytes.fromhex(player_obs['capture']['raw_game2592_hex']);assert struct.unpack_from('<Q',game,960)[0]==int(L['event_counter960'])and game[1000:1068]==aggregate
     decoded={}
     for row in obs['stats_keys']:
         raw96=bytes.fromhex(row['raw96']);assert len(raw96)==96 and row['raw96']==obs['stats']['storage'][row['index']]
         assert struct.unpack_from('<Q',raw96,8)[0]==int(row['total64']);reason=row['reason'];decoded[reason]=C.bits64(C.f64(decoded.get(reason,0))+C.f64(int(row['total64'])))
     assert {k:str(v)for k,v in decoded.items()}==L['reason_totals64']
     expected=[dict(name=literal[k]['24'],icon=literal[k]['32'],total64=v,owns=0,nested_count=0)for k,v in L['reason_totals64'].items()if k in literal]
     assert [{k:r[k]for k in expected[0]}for r in obs['breakdown']]==expected if expected else obs['breakdown']==[]
     for row in obs['breakdown']:
         raw48=bytes.fromhex(row['raw48']);assert len(raw48)==48 and struct.unpack_from('<Q',raw48,8)[0]==int(row['total64'])and u(raw48,4)==len(row['icon'].encode())and u(raw48,36)==len(row['name'].encode())and u(raw48,24)==0 and raw48[40]==0 and u(raw48,28)==0xffffffff
         if row['name']in breakdown_seen:
             old=breakdown_seen[row['name']];assert old[:8]+old[16:]==raw48[:8]+raw48[16:];counts['inherited_Vec48_nonvalue_bytes']+=40
         breakdown_seen[row['name']]=raw48
     for name in('source_registry','saved_history'):assert[obs[name][k]for k in('capacity','pointer','count')]==[0,8,0]
     counts['semantic_ledger_snapshots']+=1;counts['Vec48_rows']+=len(expected)

 private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
 assert len(original['sections'])==len(private['sections'])and len(original['imports'])==882
 for a,b in zip(original['sections'],private['sections']):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
 assert private['exports']==original['exports']+[tuple(x)for x in m['added_exports']]
 texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
  for idx,claim in m['functions'].items():
   a,z=original['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();stream.seek(lo);b=stream.read(hi-lo)
   proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(b).hexdigest());assert all(proof[k]==claim[k]for k in proof)and b==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=proof;texts[int(idx)]=b.decode()
 assert len(bindings)==42
 for key,proof in m['static_reads'].items():
  address,n=map(int,key.split(':'));assert hashlib.sha256(data(address,n)).hexdigest()==proof['sha256']
 assert original['types'][original['decl'][925-882]]==('7f7d','')
 # The expired scan retains equality; original queued removals emit before motions.
 assert texts[925].index('call 40215')<texts[925].index('i32.const 221',texts[925].index('call 40215'))
 assert 'f32.const 0x1.333334p+0 (;=1.2;)'in texts[925]and 'f32.gt'in texts[925]
 assert 'memory.copy'in texts[40215]and'i32.const 432'in texts[40215]and'i32.const 112'in texts[40215]
 assert 'f32.load offset=2372'in texts[925]and'f32.const 0x1.99999ap-3 (;=0.2;)'in texts[925]
 neighbors=list(struct.iter_unpack('<ii',data(5408444,64)));ctx=dict(world=world,nav=nav,scalars=scalars,speeds=speeds,normal=normal,defs=defs,perception=perception,classes=classes,races=races,neighbors=neighbors)
 cases=load(BATCH/'inputs.json');expected=load(BATCH/'expected.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==3
 for case,E,A in zip(cases,expected,actual,strict=True):
  breakdown_seen.clear();assert case==E['input']and case['id']==E['id']==A['id']and case['dead_mask']==0
  op,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,heading,normal,spawn_speeds,classes,races,zones,eligible,minutes);opening=op['projection'];initial,_=G.reference(dict(id=case['id'],seed_u64=op['constructor_seed_u64'],amount=0,select_index=None),classes,races,zones,kit,defs,cooldown,damage);before=initial['before'];before['rng_words']=opening['rng_words'];gain,index,selected,_=W.grow(before,case,classes,races,kit,defs,cooldown,damage,W.inactive(opening['units']['storage']));assert index==0 and gain['candidates'][0]['ability_id']=='thunder_clap'
  p=dict(g=copy.deepcopy(selected['projection']),live=copy.deepcopy(selected['live32_cells'])+[[None]*32 for _ in range(3)],count=1,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]],NPC=copy.deepcopy(opening['units']['storage']),player=opening['player_xyz']);p['g']['now_bits']=0;U.sync_aura(p);player(A['player_before'],p,'initial');L=H.ledger();accounting(A['initial_healing'],L,'initial',A['player_before']);assert U.project(p)==E['initial']
  assert A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['opening']['packets']==opening['packets']and A['stack_after']==1048576
  for name in('units','pickups','windows','special','boundaries'):
   v=A['opening']['background'][name];w=opening[name];assert(v['capacity'],v['count'])==(w['capacity'],w['count'])
   for row,hx in zip(w['storage'],v['storage'],strict=True):cells('opening'+name,row,hx)
  if case['placement']is not None:
   assert case['placement']['anchor_index']==0;xyz=T.position(p['NPC'][0],0);height=world.height(*xyz[:2]);assert height==case['placement']['height_bits'];p['player']=(*xyz[:2],height)
  assert list(p['player'])==E['player_xyz'];player(A['controlled_before'],p,'controlled')
  s=dict(rows=copy.deepcopy(p['NPC']),words=list(p['g']['rng_words']),sets=copy.deepcopy(p['sets']),total=0,spelltotals={},kills=0,elites=0,counter=opening['counter'],sequence=1,cost=0,pickups=copy.deepcopy(opening['pickups']['storage']),pickup_count=opening['pickups']['count'])
  ai=dict(rows=copy.deepcopy(s['rows']),now=0,frame=0,player=p['player'],path=None,path_values=None,path_clock=0,sequence=1,hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],incoming=0.,category=0.,has_category=False,derived=p['g']['derived_bits'],guards={o:0 for o in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(p['g']['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=[])
  assert case['clock_initial']==dict(tag=1,previous64='0')
  storage=copy.deepcopy(s['rows']);count=4;previous=A['controlled_before'];frames=[];prior_stamp=Fraction(0)
  assert len(case['timestamps64'])==len(A['stages'])==len(E['stages'])
  for j,(stampstr,obs,es,diag)in enumerate(zip(case['timestamps64'],A['stages'],E['stages'],E['diagnostics'],strict=True)):
   stamp=Fraction(C.f64(int(stampstr)));elapsed=stamp-prior_stamp;prior_stamp=stamp;dt=C.rounded(min(Fraction(.1),max(Fraction(0),elapsed)));now=C.add(p['g']['now_bits'],dt)
   assert obs['clock']==dict(tag=1,previous64=stampstr,dt_bits=dt,now_bits=now)and diag['now_bits']==now and diag['dt_bits']==dt and diag['clock_tag']==1 and diag['clock_previous64']==stampstr
   inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(inherited,2352,now);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['Game_input_inheritance_bytes']+=2592
   oldraw=obs['before']['capture']['background']['units']['storage'];pkplayer,events,heals,expired=player_stage(p,s,L,now,dt,ctx,counts);storage=copy.deepcopy(s['rows'])+storage[count:]
   assert U.project(p)==es['after_player']['player'],('afterplayer',case['id'],j,[(k,str(v)[:160],str(es['after_player']['player'].get(k))[:160])for k,v in U.project(p).items()if v!=es['after_player']['player'].get(k)]);player(obs['after_player'],p,('player',case['id'],j))
   assert combat(p,s)==es['after_player']['combat']
   wantplayercombat=combat(p,s,storage)
   for key,v in wantplayercombat.items():
    if key=='records432_cells':
     for row,hx in zip(v,obs['after_player_combat']['records432_hex'],strict=True):cells('afterplayerNPC',row,hx)
    elif key=='pickups56_cells':
     for row,hx in zip(v,obs['after_player_combat']['pickups56_hex'],strict=True):cells('afterplayerPickup',row,hx)
    else:assert obs['after_player_combat'][key]==v,('afterplayercombat',case['id'],j,key)
   for beforehx,row,afterhx in zip(oldraw,storage,obs['after_player']['capture']['background']['units']['storage'],strict=True):
    physical=bytearray.fromhex(beforehx)
    for k,v in enumerate(row):
     if v is not None:physical[k]=v
    assert physical.hex()==afterhx;counts['player_NPC_physical_replay_bytes']+=432
   aiinputraw=obs['after_player']['capture']['background']['units']['storage'];oldcount=count
   ai,storage,count,pkai,br,removed=enemy_step(p,s,ai,storage,count,now,dt,ctx,counts)
   assert U.project(p)==es['player'];player(obs['after'],p,('AI',case['id'],j));assert storage==es['physical_NPC_storage']and count==es['physical_NPC_count']
   want=combat(p,s);assert want==es['combat'],('combat',case['id'],j)
   for key,v in want.items():
    if key=='records432_cells':
     for row,hx in zip(storage,obs['combat']['records432_hex'],strict=True):cells('afterAINPC',row,hx)
    elif key=='pickups56_cells':
     for row,hx in zip(v,obs['combat']['pickups56_hex'],strict=True):cells('afterAIPickup',row,hx)
    else:assert obs['combat'][key]==v,('combat',case['id'],j,key)
   accounting(obs['healing'],L,('ledger',case['id'],j),obs['after']);assert L==es['healing']
   wantai=ai_projection(ai,storage,count)
   for k in('path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories'):assert wantai[k]==es['ai'][k]==obs['ai'][k],('AI',case['id'],j,k)
   assert wantai['history']==es['ai']['history'];assert wantai['history']['header']==obs['ai']['history']['header']and wantai['history']['active']==obs['ai']['history']['active']
   for row,hx in zip(wantai['history']['storage'],obs['ai']['history']['storage'],strict=True):cells('history',row,hx)
   physical=[bytearray.fromhex(x)for x in aiinputraw]
   for i,row in enumerate(br):
    for k,v in enumerate(row):
     if v is not None:physical[i][k]=v
   physicalcount=oldcount
   for guid in removed:
    retained=[physical[i][:]for i in range(physicalcount)if str(int.from_bytes(physical[i][112:120],'little'))!=guid]
    for i,row in enumerate(retained):physical[i]=row
    physicalcount=len(retained)
   assert physicalcount==count and [x.hex()for x in physical]==obs['after']['capture']['background']['units']['storage'];counts['AI_NPC_physical_replay_bytes']+=432*len(storage)
   packets=pkplayer+pkai;assert packets==diag['known_packets']and events==diag['events']and expired==diag['expired_spells']and removed==diag['removed_guids'];assert [{k:e[k]for k in('reason_id','amount_bits','event_id')}for e in heals]==diag['heal_events']
   cursor=0
   for packet in packets:
    k=next(k for k in range(cursor,len(obs['new_packets']))if obs['new_packets'][k]==packet);cursor=k+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2
   if pkai:assert obs['new_packets'][-len(pkai):]==pkai
   counts['observed_packets']+=len(obs['new_packets']);counts['observed_packet_bytes']+=sum(len(x[1])//2 for x in obs['new_packets'])
   for key in('windows','special','boundaries','auxiliary','claims'):assert obs['after']['capture']['background'][key]==A['opening']['background'][key];counts['background_owners']+=1
   for key in('live','aura','racial80_hex'):assert obs['after'][key]==obs['after_player'][key]
   beforegame=bytes.fromhex(obs['after_player']['capture']['raw_game2592_hex']);aftergame=bytes.fromhex(obs['after']['capture']['raw_game2592_hex']);allowed=set()
   for startoff,n in((968,16),(992,8),(1112,12),(1440,4),(1652,4),(1784,12),(1880,12),(2352,4),(2368,8),(2412,4),(2476,12)):allowed.update(range(startoff,startoff+n))
   assert all(x==y for k,(x,y)in enumerate(zip(beforegame,aftergame))if k not in allowed);counts['AI_Game_nonowned_bytes']+=2592-len(allowed)
   assert all(x==0 for x in obs['source_headers'].values())and obs['pending_after']['hits']['count']==obs['pending_after']['areas']['count']==0
   counts['component_steps']+=1;previous=obs['after'];frames.append(dict(player=U.project(p),combat=want,ai=wantai,known_packets=packets,removed=removed,healing=copy.deepcopy(L)))
  reference.append(dict(id=case['id'],frames=frames));assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]
 rt=load(BATCH/'runtime.json');term=load(BATCH/'owned-terminal.json');assert rt==comp['runtime']and term==comp['process']
 assert rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None and rt['fresh_instances']==3
 assert rt['full_calls']=={'922':0,'925':360,'1076':0,'1093':3,'1108':3,'1238':0,'1600':3,'1775':0,'2123':360,'2945':3,'3755':0,'4677':3}
 assert len(rt['target_and_setup_returns'])==735 and all(v['returned']and v['before']==v['after']==1048576 for v in rt['target_and_setup_returns'])and all(v['unchanged']and v['ranges']==2318 for v in rt['world_source_checks'])
 assert term['exit_code']==0 and term['pid_missing']and term['pgid_missing']and H.missing(term['pid'])and H.missing(term['pgid'],True)
 assert counts['component_steps']==360 and counts['damage']==25 and counts['contacts']==9 and counts['positive_Regen']==103 and counts['Leech']==10 and counts['deaths']==counts['removals']==12 and counts['basic']==7 and counts['cleave']==9 and counts['thunder_clap']==counts['racial']==3
 assert counts['known_packets']==168 and counts['known_packet_bytes']==7571 and counts['observed_packets']==223 and counts['observed_packet_bytes']==9572
 assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
 for n,h in authors.items():assert sha(ROOT/n)==h
 helpers={str(Path(v.__file__).relative_to(ROOT)):sha(v.__file__)for v in list(sys.modules.values())if getattr(v,'__file__',None)and str(v.__file__).startswith(str(ROOT/'scripts'))and Path(v.__file__).name!=Path(__file__).name}
 save(out/'independent-reference.json',reference)
 result=dict(status='pass_current139_consecutive2123_925_360steps_readonly',reviewer='/root/growth139_world',author='/root/growth139_review',handoff_sha256=HAND,comparison_sha256=COMP,reviewer_source_sha256=sha(__file__),author6=authors,helpers=helpers,current_body_bindings=bindings,source_files=91,production_files=77,source_edges=351,counts=dict(counts),author_terminal=term,author_executions=0,original_executions=0,reference_sha256=sha(out/'independent-reference.json'),seconds=time.monotonic()-start,limitations=['360consecutive component steps=360full2123+360full925;15prefixsetup separate,735direct.','Explicit XP5/firstnewThunder, optionalcontrolledplayerplacement, explicitclock;2890collection/952spawn andother884stages notexecuted.','168knownpackets7571B orderedsubset of223observed9572B; AI suffix complete in domain, player callbacks/UI packet stream stillPending.','v1failed360 order counterexamples and oldsources remain unchanged; no v1 pass transfer.','Fullknown/None physical capacity/tail anddefaultordinary no-blockedpath only; nofullmain/App/bootstrap/native/fullgame.'])
 save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
