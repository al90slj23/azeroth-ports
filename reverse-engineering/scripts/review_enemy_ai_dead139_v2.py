#!/usr/bin/env python3
"""Independent read-only current925 lifetime/order review; never runs author/original."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import copy,json,struct,math,time,sys,sqlite3,hashlib,os
sys.dont_write_bytecode=True
import review_player_autocast139 as R
from review_combat139 import sha,parse_module,local_closure
H=R.H;AI=R.AI;C=R.C;U=R.U;D=R.D;T=R.T;G=R.G;W=R.W;O=R.O
fp=R.fp;load_world=R.load_world;initial_record=R.initial_record;WASM=R.WASM
ROOT=Path(__file__).resolve().parents[1]
SOURCE=R.SOURCE;PROFILE=R.PROFILE
BATCH=ROOT/'evidence/enemy-ai-dead139-v2-full-20261102T134523.549072Z'
HAND='bd52f7ff7583ff937963342cc188e7b04d43d2811fcfcdf9e4af765501e9fd49'
COMP='ebd66ceb975472a40d290c5468a66a884f0faef3742a0ece34717dea2b75ce23'
load=R.load;save=R.save;u=R.u


def player_step(p,s,L,now,dt,ctx,counts):
 p['g']['now_bits']=now;p['scalar']['2352']=now
 keep=[i for i in range(p['count'])if C.rational(now)<C.rational(U.read(p['live'][i],24))]
 if len(keep)!=p['count']:
  old=copy.deepcopy(p['live'])
  for j,i in enumerate(keep):p['live'][j]=old[i]
  p['count']=len(keep);U.recalculate(p,ctx['classes'],ctx['races']);U.sync_aura(p)
 H.regen(p,L,now,dt)
 packets,events,heals=R.scheduler(p,s,L,now,dt,ctx['world'],ctx['scalars'],ctx['speeds'],ctx['normal'],ctx['defs'],ctx['perception'],ctx['classes'],ctx['races'],counts)
 return packets


def cleave(p,s,L,now,ctx,counts):
 row=bytes.fromhex(p['g']['owned_records80_hex'][0]);definition=ctx['defs']['cleave'][1]
 chosen=R.targets(s['rows'],p['player'],now,u(definition,56));limit=u(definition,64)
 chosen=chosen[:max(1,(limit+u(row,20)+u(row,60)+p['g']['derived_bits']['1592'])&C.M)if limit else 1]
 ids=[D.read(s['rows'][i],112,8)for i in chosen]
 value=C.mul(C.mul(C.mul(C.mul(u(definition,48),0x3fb33333),u(row,12)),u(row,52)),C.ONE)
 base=C.mul(p['g']['derived_bits']['1540'],C.add(value,0))
 packets=[[306,C.launch(0,845,ids)]]if ids else[]
 for i in chosen:
  random,s['words']=D.uniform24(s['words']);critical=int(C.rational(p['g']['derived_bits']['1548'])>C.rational(random));amount=C.mul(base,p['g']['derived_bits']['1552'])if critical else base
  a,b=R.resolve_hit(p,s,L,i,amount,critical,845,definition[85],now,ctx['world'],ctx['scalars'],ctx['speeds'],ctx['normal'],counts);packets.extend(a)
 p['g']['rng_words']=list(s['words']);p['NPC']=copy.deepcopy(s['rows'])
 return packets,ids


def ai_projection(ai,storage,count):
 return dict(capacity=len(storage),count=count,records432_cells=copy.deepcopy(storage),history=AI.I.ring_projection(ai['history']),path=copy.deepcopy(ai['path']),path_clock2372_bits=ai['path_clock'],incoming992_hex=struct.pack('>d',ai['incoming']).hex(),last_hit1652_bits=ai['last'],categories={'mob melee':struct.pack('>d',ai['category']).hex()}if ai['has_category']else{},movement_sequence2412=ai['sequence'])


def enemy_step(p,s,ai,storage,count,now,dt,ctx,counts):
 storage=copy.deepcopy(s['rows'])+copy.deepcopy(storage[count:]);alive=[];remove=[]
 for index,row in enumerate(storage[:count]):
  marker=D.read(row,0);assert marker in(0,1)
  if marker==0:alive.append(index)
  else:
   assert all(D.read(row,k)==0xffffffff for k in(40,64,244))and D.read(row,232)==0 and D.read(row,284)==5830904 and row[424]==0
   if C.rational(C.sub(now,D.read(row,4)))>C.rational(0x3f99999a):remove.append(str(D.read(row,112,8)))
 ai=copy.deepcopy(ai);ai.update(rows=[copy.deepcopy(storage[k])for k in alive],now=C.sub(now,dt),player=p['player'],hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],derived=p['g']['derived_bits'],fields=copy.deepcopy(p['g']['player_fields']),sequence=s['sequence'],packets=[])
 if ai['path']is not None and AI.probe(ctx['nav'],p['player'][:2])[1]!=ai['path']['start_index']:
  assert C.rational(C.sub(now,ai['path_clock']))>=C.rational(0x3e4ccccd),'Changed-cell young map domain pending'
  ai['path'],ai['path_values']=AI.breadth_first(ctx['nav'],p['player'],ctx['neighbors']);ai['path_clock']=now;counts['path_refreshes']+=1
 ai,answer=AI.tick(ai,dt,ctx['world'],ctx['nav'],ctx['neighbors'],{5830904:'Kobold Vermin'},{'Melee':'Melee'},counts)
 assert ai['now']==now
 for index,row in zip(alive,ai['rows'],strict=True):storage[index]=row
 before=copy.deepcopy(storage)
 # Full432 forward stable compaction with stale physical tail retained.
 for guid in remove:
  retained=[copy.deepcopy(row)for row in storage[:count]if str(D.read(row,112,8))!=guid]
  for k,row in enumerate(retained):storage[k]=row
  count=len(retained)
 s['rows']=copy.deepcopy(storage[:count]);s['sequence']=ai['sequence'];p['NPC']=copy.deepcopy(s['rows']);p['g']['current_hp_bits']=ai['hp'];p['g']['player_fields']=copy.deepcopy(ai['fields']);p['scalar']['1652']=ai['last'];p['g']['now_bits']=now;p['scalar']['2352']=now
 packets=[[170,int(guid).to_bytes(8,'little').hex()]for guid in remove]+answer['packets'];counts['removals']+=len(remove)
 return ai,storage,count,packets,before,remove


def combat(p,s,physical=None):
 return dict(records432_cells=copy.deepcopy(s['rows']if physical is None else physical),rng_words=list(s['words']),accounted_total_bits=str(s['total']),spell_sets=copy.deepcopy(p['sets']),player_xyz=list(p['player']),phase2587=1,spell_totals64=[[k,str(v)]for k,v in sorted(s['spelltotals'].items())],kills1084=s['kills'],elites1088=s['elites'],counter2408=s['counter'],movement_sequence2412=s['sequence'],killcost2420_bits=s['cost'],player_hp1440_bits=p['g']['current_hp_bits'],maximum1536_bits=p['g']['derived_bits']['1536'],xp1436=p['g']['xp'],pickup_capacity=len(s['pickups']),pickup_count=s['pickup_count'],pickups56_cells=copy.deepcopy(s['pickups']))


def main():
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
 assert sha(SOURCE)==WASM and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
 hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json')
 authors=hand.get('author_files',hand.get('frozen_author_files'));assert len(authors)==6
 for n,h in authors.items():assert sha(ROOT/n)==h
 sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==96 and sum(n.startswith('reconstruction/')for n in sources)==79
 assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(comp['source_import_edges'])==399
 for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
 for table in(comp['frozen'],comp['artifacts'],prep['frozen']):
  for n,h in table.items():assert sha(BATCH/n)==h
 assert comp['differences']==0 and comp['cases']==comp['completed_cases']==11 and prep['expected_before_original']and not prep['original_input_contains_expected']
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
 assert len(bindings)==55
 for key,proof in m['static_reads'].items():
  address,n=map(int,key.split(':'));assert hashlib.sha256(data(address,n)).hexdigest()==proof['sha256']
 assert original['types'][original['decl'][925-882]]==('7f7d','')
 # The expired scan retains equality; original queued removals emit before motions.
 assert texts[925].index('call 40215')<texts[925].index('i32.const 221',texts[925].index('call 40215'))
 assert 'f32.const 0x1.333334p+0 (;=1.2;)'in texts[925]and 'f32.gt'in texts[925]
 assert 'memory.copy'in texts[40215]and'i32.const 432'in texts[40215]and'i32.const 112'in texts[40215]
 assert 'f32.load offset=2372'in texts[925]and'f32.const 0x1.99999ap-3 (;=0.2;)'in texts[925]
 neighbors=list(struct.iter_unpack('<ii',data(5408444,64)));ctx=dict(world=world,nav=nav,scalars=scalars,speeds=speeds,normal=normal,defs=defs,perception=perception,classes=classes,races=races,neighbors=neighbors)
 cases=load(BATCH/'inputs.json');expected=load(BATCH/'expected.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==11
 def comparecombat(obs,want,label):
  for k,v in want.items():
   if k=='records432_cells':
    for row,hx in zip(v,obs['records432_hex'],strict=True):cells('combatNPC',row,hx)
   elif k=='pickups56_cells':
    for row,hx in zip(v,obs['pickups56_hex'],strict=True):cells('combatPickup',row,hx)
   else:assert obs[k]==v,(label,k)
 def compareai(obs,want,label):
  for k in('path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories'):assert obs[k]==want[k],(label,k)
  assert obs['history']['header']==want['history']['header']and obs['history']['active']==want['history']['active']
  for row,hx in zip(want['history']['storage'],obs['history']['storage'],strict=True):cells('history',row,hx)
 def checkstate(obs,p,Eplayer,label):
  assert U.project(p)==Eplayer,(label,'independentplayer');player(obs,p,label)
 def compareexpectedai(want,e,label):
  assert want==e,(label,[(i,k,a,b)for i,(aa,bb)in enumerate(zip(want['records432_cells'],e['records432_cells']))for k,(a,b)in enumerate(zip(aa,bb))if a!=b][:12],'independentAI',[(k,str(want[k])[:160],str(e[k])[:160])for k in want if want[k]!=e[k]])
 def aiproj(ai,storage,count):return ai_projection(ai,storage,count)
 for case,E,A in zip(cases,expected,actual,strict=True):
  breakdown_seen.clear();assert case==E['input']and case['id']==E['id']==A['id'];probe=case.get('cooccur_probe',False)
  op,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,heading,normal,spawn_speeds,classes,races,zones,eligible,minutes);opening=op['projection'];initial,_=G.reference(dict(id=case['id'],seed_u64=op['constructor_seed_u64'],amount=0,select_index=None),classes,races,zones,kit,defs,cooldown,damage);before=initial['before'];before['rng_words']=opening['rng_words'];gain,index,selected,_=W.grow(before,case,classes,races,kit,defs,cooldown,damage,W.inactive(opening['units']['storage']));assert index==0 and gain['candidates'][0]['ability_id']=='thunder_clap'
  p=dict(g=copy.deepcopy(selected['projection']),live=copy.deepcopy(selected['live32_cells'])+[[None]*32 for _ in range(3)],count=1,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]],NPC=copy.deepcopy(opening['units']['storage']),player=opening['player_xyz']);p['g']['now_bits']=0;U.sync_aura(p);player(A['player_before'],p,'initial');L=H.ledger()
  assert A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['opening']['packets']==opening['packets']and A['stack_after']==1048576
  for name in('units','pickups','windows','special','boundaries'):
   v=A['opening']['background'][name];w=opening[name];assert(v['capacity'],v['count'])==(w['capacity'],w['count'])
   for row,hx in zip(w['storage'],v['storage'],strict=True):cells('opening'+name,row,hx)
  s=dict(rows=copy.deepcopy(p['NPC']),words=list(p['g']['rng_words']),sets=copy.deepcopy(p['sets']),total=0,spelltotals={},kills=0,elites=0,counter=opening['counter'],sequence=1,cost=0,pickups=copy.deepcopy(opening['pickups']['storage']),pickup_count=opening['pickups']['count'])
  ai=dict(rows=copy.deepcopy(s['rows']),now=0,frame=0,player=p['player'],path=None,path_values=None,path_clock=0,sequence=1,hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],incoming=0.,category=0.,has_category=False,derived=p['g']['derived_bits'],guards={o:0 for o in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(p['g']['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=[])
  storage=copy.deepcopy(s['rows']);count=4
  if probe:
   if case['placement']is not None:
    assert case['placement']['anchor_index']==0;xyz=T.position(s['rows'][0],0);height=world.height(*xyz[:2]);assert height==case['placement']['height_bits'];p['player']=(*xyz[:2],height)
   previous=A['controlled_before'];player(previous,p,'controlled')
   assert len(A['preceding'])==case['target_index']==len(E['preceding'])
   for j,(obs,expectedpreceding)in enumerate(zip(A['preceding'],E['preceding'],strict=True)):
    stamp=C.f64(int(case['timestamps64'][j]));assert stamp==(j+1)*.125
    dt=0x3dcccccd;now=C.add(p['g']['now_bits'],dt)
    player_step(p,s,L,now,dt,ctx,counts);assert U.project(p)==expectedpreceding['after_player'];player(obs['after_player'],p,'preAI');counts['preceding2123']+=1
    ai,storage,count,pk,br,removed=enemy_step(p,s,ai,storage,count,now,dt,ctx,counts)
    checkstate(obs['after'],p,expectedpreceding['player'],'preceding');want=combat(p,s,storage);assert want==expectedpreceding['combat'],(case['id'],j,[(ii,kk,aa,bb)for ii,(a,b)in enumerate(zip(want['records432_cells'],expectedpreceding['combat']['records432_cells']))for kk,(aa,bb)in enumerate(zip(a,b))if aa!=bb][:16],[(k,str(v)[:100],str(expectedpreceding['combat'].get(k))[:100])for k,v in want.items()if v!=expectedpreceding['combat'].get(k)]);comparecombat(obs['combat'],want,'preceding');accounting(obs['healing'],L,'preceding',obs['after']);assert L==expectedpreceding['healing'];wantai=aiproj(ai,storage,count);assert wantai==expectedpreceding['ai'];compareai(obs['ai'],wantai,'preceding');assert storage==expectedpreceding['physical'];counts['preceding925']+=1
   targetstep=case['updates'][0];player_step(p,s,L,targetstep['now_bits'],targetstep['dt_bits'],ctx,counts);counts['target_setup2123']+=1;storage=copy.deepcopy(s['rows'])+storage[count:];ai.update(hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],fields=copy.deepcopy(p['g']['player_fields']),sequence=s['sequence'])
   checkstate(A['after_producer'],p,E['after_producer']['player'],'producer');comparecombat(A['after_producer_combat'],combat(p,s,storage),'producer');assert combat(p,s,storage)==E['after_producer']['combat'];accounting(A['after_producer_healing'],L,'producer',A['after_producer']);assert L==E['after_producer']['healing'];compareexpectedai(aiproj(ai,storage,count),E['after_producer']['ai'],'producer');compareai(A['after_producer_ai'],aiproj(ai,storage,count),'producer')
  else:
   ai,storage,count,pk,br,removed=enemy_step(p,s,ai,storage,count,0,0x3dcccccd,ctx,counts);assert not removed;assert s['rows']==E['source_setup_ai_records']and pk==E['source_setup_ai_packets'];player(A['ai_setup']['after'],p,'setup925');counts['initial925']+=1
   xyz=T.position(s['rows'][0],0x3dcccccd);xy=(C.add(xyz[0],0x41000000),xyz[1]);p['player']=(*xy,world.height(*xy));assert list(p['player'])==case['controlled_player_xyz'];player(A['controlled_before'],p,'controlled')
   for j,(step,obs,ep)in enumerate(zip(case['prefix_updates'],A['prefix'],E['prefix'],strict=True)):
    pk=player_step(p,s,L,step['now_bits'],step['dt_bits'],ctx,counts);checkstate(obs['after'],p,ep['player'],'prefix');assert combat(p,s)==ep['combat'];comparecombat(obs['combat'],combat(p,s),'prefix');accounting(obs['healing'],L,'prefix',obs['after']);assert L==ep['healing'];assert pk==ep['known_packets'];counts['coldprefix2123']+=1
   for control,obs,ep in zip(case['extra_casts'],A['extra_casts'],E['extra_casts'],strict=True):
    i=control['anchor_index'];assert str(D.read(s['rows'][i],112,8))==control['anchor_guid']and D.read(s['rows'][i],0)==0;xyz=T.position(s['rows'][i],p['g']['now_bits']);p['player']=(*xyz[:2],world.height(*xyz[:2]));assert list(p['player'])==control['player_xyz'];pk,ids=cleave(p,s,L,control['now_bits'],ctx,counts);checkstate(obs['after'],p,ep['player'],'extra');assert combat(p,s)==ep['combat'];comparecombat(obs['combat'],combat(p,s),'extra');accounting(obs['healing'],L,'extra',obs['after']);assert L==ep['healing'];assert pk==ep['known_packets']and list(map(str,ids))==ep['selected_ids'];counts['extra922']+=1
   storage=copy.deepcopy(s['rows']);count=len(storage);ai.update(hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],fields=copy.deepcopy(p['g']['player_fields']),sequence=s['sequence']);checkstate(A['after_producer'],p,E['after_producer']['player'],'producer');assert combat(p,s)==E['after_producer']['combat'];comparecombat(A['after_producer_combat'],combat(p,s),'producer');accounting(A['after_producer_healing'],L,'producer',A['after_producer']);compareexpectedai(aiproj(ai,storage,count),E['after_producer']['ai'],'producer');compareai(A['after_producer_ai'],aiproj(ai,storage,count),'producer')
  frames=[]
  for j,(step,obs,es,diag)in enumerate(zip(case['updates'],A['frames'],E['stages'],E['diagnostics'],strict=True)):
   now,dt=step['now_bits'],step['dt_bits'];beforeobs=obs['before'];oldraw=copy.deepcopy(beforeobs['capture']['background']['units']['storage']);oldcount=count
   if probe:
    assert C.f64(int(case['timestamps64'][-1]))==(case['target_index']+1)*.125 and obs['clock']==dict(timestamp64=case['timestamps64'][-1],dt_bits=dt,now_bits=now)
    assert now==p['g']['now_bits'];player(obs['after_player'],p,'targetplayer')
    # Physical replay starts after the authentic player prefix.
    oldraw=copy.deepcopy(obs['after_player']['capture']['background']['units']['storage'])
   ai,storage,count,pk,br,removed=enemy_step(p,s,ai,storage,count,now,dt,ctx,counts)
   checkstate(obs['after'],p,es['player'],('target',case['id'],j));wantai=aiproj(ai,storage,count);compareexpectedai(wantai,es['ai'],('target',case['id'],j));compareai(obs['ai'],wantai,'target')
   assert pk==es['new_packets']==obs['new_packets'],('packetorder',case['id'],j)
   assert br==diag['before_removal']and removed==diag['removed_guids']
   vec=obs['after']['capture']['background']['units'];assert vec['capacity']==len(storage)and vec['count']==count
   physical=[bytearray.fromhex(hx)for hx in oldraw]
   for i,row in enumerate(br):
    for k,v in enumerate(row):
     if v is not None:physical[i][k]=v
   physicalcount=oldcount
   for guid in removed:
    retained=[physical[i][:]for i in range(physicalcount)if str(int.from_bytes(physical[i][112:120],'little'))!=guid]
    for i,row in enumerate(retained):physical[i]=row
    physicalcount=len(retained)
   assert physicalcount==count
   assert [x.hex()for x in physical]==vec['storage'];counts['target_physical_replay_bytes']+=432*len(storage)
   for row,hx in zip(storage,vec['storage'],strict=True):cells('targetNPC',row,hx)
   for key in('windows','special','boundaries','auxiliary','claims'):assert obs['after']['capture']['background'][key]==A['opening']['background'][key];counts['background_owners']+=1
   beforegame=bytes.fromhex((obs['after_player']if probe else beforeobs)['capture']['raw_game2592_hex']);aftergame=bytes.fromhex(obs['after']['capture']['raw_game2592_hex'])
   allowed=set()
   for startoff,n in((968,16),(992,8),(1112,12),(1440,4),(1652,4),(1784,12),(1880,12),(2352,4),(2368,8),(2412,4),(2476,12)):allowed.update(range(startoff,startoff+n))
   assert all(x==y for k,(x,y)in enumerate(zip(beforegame,aftergame))if k not in allowed),('nonownedGame',case['id'],j)
   counts['target_Game_nonowned_bytes']+=2592-len(allowed);counts['targets']+=1;counts['target_packets']+=len(pk);counts['target_packet_bytes']+=sum(len(v)//2 for _,v in pk)
   if probe:assert [x[0]for x in pk]==([170,330]if case['source_case_id']==0 else[170,221]);counts['sameframe_probes']+=1
   frames.append(dict(player=U.project(p),ai=wantai,packets=pk,removed=removed))
  reference.append(dict(id=case['id'],frames=frames))
  assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]
 rt=load(BATCH/'runtime.json');term=load(BATCH/'owned-terminal.json');assert rt==comp['runtime']and term==comp['process']
 assert rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None and rt['fresh_instances']==11
 assert all(v['returned']and v['before']==v['after']==1048576 for v in rt['target_and_setup_returns'])and len(rt['target_and_setup_returns'])==524
 assert term['exit_code']==0 and term['pid_missing']and term['pgid_missing']and H.missing(term['pid'])and H.missing(term['pgid'],True)
 assert counts['targets']==146 and counts['target_packets']==73 and counts['target_packet_bytes']==2578 and counts['sameframe_probes']==2 and counts['preceding925']==counts['preceding2123']==120
 assert counts['target_physical_replay_bytes']==252288
 assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
 for n,h in authors.items():assert sha(ROOT/n)==h
 helpers={str(Path(v.__file__).relative_to(ROOT)):sha(v.__file__)for v in list(sys.modules.values())if getattr(v,'__file__',None)and str(v.__file__).startswith(str(ROOT/'scripts'))and Path(v.__file__).name!=Path(__file__).name}
 save(out/'independent-reference.json',reference)
 result=dict(status='pass_current139_dead_lifetime146_and_two_sameframe_orders_readonly',reviewer='/root/growth139_world',author='/root/collection139_finish',handoff_sha256=HAND,comparison_sha256=COMP,reviewer_source_sha256=sha(__file__),author6=authors,helpers=helpers,current_body_bindings=bindings,source_files=96,production_files=79,source_edges=399,counts=dict(counts),author_terminal=term,author_executions=0,original_executions=0,reference_sha256=sha(out/'independent-reference.json'),seconds=time.monotonic()-start,limitations=['146target925;120preceding2123/925 pairs numeric/physical/history/ledger source setup only, not formal corrected packet target coverage.','v1 isolated144 and failed360 order counterexamples remain preserved; no v1 wide pass.','Actual normal uniqueGUID corpses; default empty destructor owners; duplicateGUID/status/boss/projectile blocked-flow branches remain Pending.','Entire target925 packet stream matches this scope; player2123 packet observations in source prefixes remain scoped known subsets.','Explicit XP5/selectedThunder/playerplacement, resourceonly context; no complete884/bootstrap/nativeApp/fullgame.','None bytes are never treated as0; target physical storage replay uses actual inherited owner bytes and full432B stable compaction/stale tails.'])
 save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
