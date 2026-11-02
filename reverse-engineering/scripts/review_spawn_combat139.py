#!/usr/bin/env python3
"""Different-author current139 combat-source/full952 read-only reference."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
 if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen')or event=='import'and str(args[0]).startswith(('core_spec','resource_spec')):
  AUDIT['forbidden']+=1;raise RuntimeError('Read-only review refuses '+event)
sys.addaudithook(audit)
import review_cast139 as C
import review_player_update139 as U
import review_growth139 as G
import review_player_enemy139_v2 as Chain
import review_enemy_ai_dead139_v2 as Life
import review_spawn_schedule139_v3 as S
import review_world_position139 as P
from review_combat139 import sha,parse_module,local_closure,fp,bits,f32
from review_initial139 import record as initial_record
from review_world_position139 import load_world
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
BATCH=ROOT/'evidence/spawn-combat139-full-20261102T145803.233915Z'
HAND='2f80063669147ee4bd4104e196b0e096ed81bc34e2a047aecbced71183983a01'
COMP='51814f71c5f6812b75541ebd5a2bfa8a2be5630b1ab42b8f8dc83de9673cc898'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]
H=Chain.H;W=Chain.W;O=Chain.O;T=Chain.T;D=Chain.D;AI=Chain.AI
def load_context():
    raw=SOURCE.read_bytes();module=parse_module(raw)
    def data(address,size):
     out=bytearray(size)
     for at,pos,n in module['data_segments']:
      if at is None:continue
      lo,hi=max(address,at),min(address+size,at+n)
      if lo<hi:out[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
     return bytes(out)
    text=lambda p,n:data(p,n).decode();abilities={}
    for i in range(114):
     p=5882740+88*i;b=data(p,88);abilities[text(u(b,12),u(b,16))]=(p,b,tuple(data(u(b,36),u(b,40))))
    cls=data(5877920,108);kit=[text(p,n)for p,n in struct.iter_unpack('<II',data(u(cls,32),8*u(cls,36)))];defs={k:abilities[k]for k in kit};classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)};race=data(5874636,44);races={1:dict(ability_pointer=abilities[text(u(race,24),u(race,28))][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    zone=data(5871348,152);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];heading=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));spawn_speeds=list(speeds);spawn_speeds[1]=1088421888;normal=data(5830904,72);eligible=[j for j in range(12)if u(data(5830904+72*j,72),68)==1 and math.isfinite(fp(u(data(5830904+72*j,72),64)))];minutes=u(data(u(zone,72)+336,4));perception=data(5891892,88);cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20))
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=json.loads(wp.read_text());world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));scalars['heading_bits']=u(zone,116);neighbors=list(struct.iter_unpack('<ii',data(5408444,64)))
    ctx=dict(world=world,nav=nav,scalars=scalars,speeds=speeds,normal=normal,defs=defs,perception=perception,classes=classes,races=races,kit=kit,neighbors=neighbors)
    ctx.update(heading=heading,spawn_speeds=spawn_speeds,zones=zones,eligible=eligible,minutes=minutes,cooldown=cooldown,damage=damage,data=data,module=module,raw=raw)
    return ctx


def exp_small(x):
 assert x&0x7fffffff<=1051816472
 if x&0x7fffffff<=956301312:return C.add(x,C.ONE)
 square=C.mul(x,x);correction=C.sub(x,C.mul(square,C.add(bits(float.fromhex('0x1.55551ep-3')),C.mul(square,bits(float.fromhex('-0x1.6aa42ap-9'))))))
 return C.add(C.add(x,C.sub(C.div(C.mul(x,correction),C.sub(bits(2.),correction)),0)),C.ONE)

class PathPosition(P.Reference):
    def spawn(self):
        vx,vy=map(fp,self.s['velocity_xy']);moving=f32(f32(vx*vx)+f32(vy*vy))>4.
        heading=heading_ref(vy,vx,self.tables) if moving else 0.;cx,cy=map(fp,self.scalars['center_xy_bits']);limit=fp(self.scalars['radius_bits']);px,py,pz=map(fp,self.s['player_xyz'])
        for _ in range(16):
            self.count['spawn_trials']+=1;biased=False
            if moving:
                out,self.words=next_rng(self.words);self.count['rng_draws']+=1
                biased=f32(float(out>>8)*2.**-24)<fp(self.s['bias_probability_bits'])
            angle=f32(heading+self.uniform(0xbf99999a,0x3f99999a)) if biased else f32(self.uniform(0,0x40c90fdb)+0.)
            radius=self.uniform(self.s['low_radius_bits'],self.s['high_radius_bits'])
            while radius>=12.:
                x,y=self.xy(angle,radius);distance=hypot_ref(f32(x-cx),f32(y-cy));z=None
                if distance<=f32(limit+18.):z=self.height(x,y)
                if z is not None and abs(f32(z-pz))<=(8. if distance>limit else 25.):
                    value,idx=self.probe(x,y);path=self.s['distance_map'];allowed=False
                    if path is None:allowed=value!=1
                    elif not value:
                        if path['field24']<401:allowed=True;self.count['path_lazy_branch']+=1
                        elif idx is not None:
                            assert idx<len(path['values_u16']);cost=path['values_u16'][idx];self.count['path_cost_reads']+=1
                            allowed=cost!=65535 and cost<=f32(f32(hypot_ref(f32(x-px),f32(y-py))*1.5)+12.)
                    if allowed:return [bits(x),bits(y),bits(z)]
                radius=f32(radius-2.);self.count['radius_shrinks']+=1
        self.count['fallback13563']+=1;return self.random()


def packet169_level(guid, entry, display, scale, hp, position, heading, speeds, level):
    fields = {0: guid & 0xffffffff, 1: guid >> 32, 2: 9, 3: entry,
              4: bits(scale), 16: 0, 17: 0, 22: math.ceil(hp), 28: math.ceil(hp),
              34: level, 35: 14, 36: 256, 46: 0, 126: 2000, 127: 2000,
              129: bits(f32(scale * .5)), 130: bits(f32(scale * 1.5)),
              131: display, 132: display, 134: bits(5.), 135: bits(10.), 145: bits(1.)}
    masks = [sum(1 << (key % 32) for key in fields if key // 32 == group) for group in range(5)]
    values = bytes([5]) + struct.pack('<5I', *masks) + struct.pack('<' + 'I' * len(fields), *(fields[key] for key in sorted(fields)))
    movement = bytes([3, 112]) + struct.pack('<2I', 0, 0) + struct.pack('<4I', *position, bits(heading))
    movement += struct.pack('<I6II', 0, *speeds, 1)
    return [169, (struct.pack('<IBB', 1, 0, 3) + S.N.packed_guid(guid) + movement + values).hex()]


def birth(index,now,position,player,words,counter,prior,definitions,zone,tables,speeds,counts,level):
    d=definitions[index];assert d[68]==0 and u(zone,140)==0
    minute=C.div(now,bits(60.));scale=u(zone,136)
    curve=C.add(C.mul(minute,0x3dcccccd),C.ONE)
    curve=C.add(curve,C.mul(minute,C.mul(minute,0x3d1374bc)))
    curve=C.add(curve,C.mul(minute,C.mul(minute,C.mul(minute,0x3be6afcd))))
    hp=C.mul(C.mul(0x409e6666,u(d,40)),C.mul(scale,curve))
    clamp=C.div(minute,bits(20.));clamp=0 if C.rational(clamp)<0 else C.ONE if C.rational(clamp)>1 else clamp
    hp=C.mul(hp,C.add(C.mul(clamp,C.mul(clamp,u(zone,140))),C.ONE))
    curve=C.add(C.mul(minute,0x3d8f5c29),C.ONE)
    curve=C.add(curve,C.mul(minute,C.mul(minute,0x3c75c28f)))
    curve=C.add(curve,C.mul(minute,C.mul(minute,C.mul(minute,0x3951b717))))
    attack=C.mul(C.mul(bits(1.25),u(d,44)),C.mul(curve,bits(S.N.rounded_sqrt(fp(scale)))))
    counter=(counter+1)&0xffffffff;entry=u(d,24);guid=0xf130000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
    yaw,words,yaw_draws=S.N.rng_sample(words,fp(0x40c90fdb));jitter,words,jitter_draws=S.N.rng_sample(words,fp(0x3e99999a));counts['NPC_yaw_jitter_draws']+=yaw_draws+jitter_draws
    buf=bytearray(432)
    def put(o,v):struct.pack_into('<I',buf,o,v)
    for o in(40,64,244):put(o,0xffffffff)
    struct.pack_into('<Q',buf,112,guid);struct.pack_into('<Q',buf,236,4)
    s=u(d,32);speed=u(d,48)
    fields={280:0,284:5830904+72*index,288:hp,292:hp,296:attack,300:C.mul(u(d,52),0x3f866666),304:speed,308:C.add(C.mul(s,0x3f99999a),0x400ccccd),312:s,340:now,348:C.add(now,C.add(bits(jitter),0)),352:C.mul(speed,bits(.5)),404:C.add(bits(yaw),0)}
    for o,v in fields.items():put(o,v)
    for o in(316,328):struct.pack_into('<3I',buf,o,*position)
    cells=list(prior)
    for o,n in S.N.WRITES:cells[o:o+n]=buf[o:o+n]
    dy,dx=(fp(C.sub(player[i],position[i]))for i in(1,0));heading=S.N.heading_ref(dy,dx,tables)
    packet=packet169_level(guid,entry,u(d,28),fp(s),fp(hp),position,heading,speeds,level)
    return cells,words,counter,packet




def prepare(case,ctx,observed,checkplayer,checkcombat,counts):
 world,nav,scalars=ctx['world'],ctx['nav'],ctx['scalars'];classes,races,zones=ctx['classes'],ctx['races'],ctx['zones'];kit,defs=ctx['kit'],ctx['defs']
 full,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,ctx['heading'],ctx['normal'],ctx['spawn_speeds'],classes,races,zones,ctx['eligible'],ctx['minutes']);opening=full['projection']
 initial,_=G.reference(dict(id=case['id'],seed_u64=full['constructor_seed_u64'],amount=0,select_index=None),classes,races,zones,kit,defs,ctx['cooldown'],ctx['damage']);before=initial['before'];before['rng_words']=opening['rng_words'];gain,index,selected,_=W.grow(before,case,classes,races,kit,defs,ctx['cooldown'],ctx['damage'],W.inactive(opening['units']['storage']));assert index==0 and gain['candidates'][0]['ability_id']=='thunder_clap'
 p=dict(g=copy.deepcopy(selected['projection']),live=copy.deepcopy(selected['live32_cells'])+[[None]*32 for _ in range(3)],count=1,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]],NPC=copy.deepcopy(opening['units']['storage']),player=opening['player_xyz']);p['g']['now_bits']=0;U.sync_aura(p);L=H.ledger();checkplayer(observed['player_before'],p,'initial')
 s=dict(rows=copy.deepcopy(p['NPC']),words=list(p['g']['rng_words']),sets=copy.deepcopy(p['sets']),total=0,spelltotals={},kills=0,elites=0,counter=opening['counter'],sequence=1,cost=0,pickups=copy.deepcopy(opening['pickups']['storage']),pickup_count=opening['pickups']['count'])
 ai=dict(rows=copy.deepcopy(s['rows']),now=0,frame=0,player=p['player'],path=None,path_values=None,path_clock=0,sequence=1,hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],incoming=0.,category=0.,has_category=False,derived=p['g']['derived_bits'],guards={o:0 for o in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(p['g']['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=[])
 storage=copy.deepcopy(s['rows']);count=4
 if case.get('cooccur_probe'):
  if case['placement']is not None:
   assert case['placement']['anchor_index']==0;xyz=T.position(s['rows'][0],0);height=world.height(*xyz[:2]);assert height==case['placement']['height_bits'];p['player']=(*xyz[:2],height)
  checkplayer(observed['controlled_before'],p,'controlled');assert len(observed['preceding'])==case['target_index']
  for j,obs in enumerate(observed['preceding']):
   assert C.f64(int(case['timestamps64'][j]))==(j+1)*.125;dt=0x3dcccccd;now=C.add(p['g']['now_bits'],dt);Life.player_step(p,s,L,now,dt,ctx,counts);checkplayer(obs['after_player'],p,'preceding2123');ai,storage,count,pk,br,removed=Life.enemy_step(p,s,ai,storage,count,now,dt,ctx,counts);checkplayer(obs['after'],p,'preceding925');checkcombat(obs['combat'],p,s,storage);counts['source_preceding_pairs']+=1
  target=case['updates'][0];Life.player_step(p,s,L,target['now_bits'],target['dt_bits'],ctx,counts);storage=copy.deepcopy(s['rows'])+storage[count:];ai.update(hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],fields=copy.deepcopy(p['g']['player_fields']),sequence=s['sequence']);counts['source_final2123']+=1
 else:
  ai,storage,count,pk,br,removed=Life.enemy_step(p,s,ai,storage,count,0,0x3dcccccd,ctx,counts);assert not removed;checkplayer(observed['ai_setup']['after'],p,'initial925')
  xyz=T.position(s['rows'][0],0x3dcccccd);xy=[C.add(xyz[0],0x41000000),xyz[1]];p['player']=(*xy,world.height(*xy));assert list(p['player'])==case['controlled_player_xyz'];checkplayer(observed['controlled_before'],p,'controlled')
  for step,obs in zip(case['prefix_updates'],observed['prefix'],strict=True):
   Life.player_step(p,s,L,step['now_bits'],step['dt_bits'],ctx,counts);checkplayer(obs['after'],p,'cold2123');checkcombat(obs['combat'],p,s);counts['source_cold2123']+=1
  for control,obs in zip(case['extra_casts'],observed['extra_casts'],strict=True):
   extra_cast(p,s,L,control,ctx,counts);checkplayer(obs['after'],p,'extra922');checkcombat(obs['combat'],p,s)
  storage=copy.deepcopy(s['rows']);count=len(storage);ai.update(hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],fields=copy.deepcopy(p['g']['player_fields']),sequence=s['sequence'])
 checkplayer(observed['after_producer'],p,'producer');checkcombat(observed['after_producer_combat'],p,s,storage);assert all(observed['after_producer_healing'][k]==v for k,v in L.items());assert observed['after_producer_ai']['path']==ai['path']
 return full,p,s,ai,L,storage,count

def extra_cast(p,s,L,control,ctx,counts):
 i=control['anchor_index'];assert str(D.read(s['rows'][i],112,8))==control['anchor_guid']and D.read(s['rows'][i],0)==0;xyz=T.position(s['rows'][i],p['g']['now_bits']);p['player']=(*xyz[:2],ctx['world'].height(*xyz[:2]));assert list(p['player'])==control['player_xyz'];Life.cleave(p,s,L,control['now_bits'],ctx,counts);counts['source_extra922']+=1


def spawn(state,p,s,ai,physical,count,now,dt,ctx,counts):
 player=p['player'];level=p['g']['level'];rows=copy.deepcopy(physical);words=tuple(s['words']);counter=s['counter'];packets=[];born=[]
 delta=[C.div(C.sub(player[i],state['previous_player_xyz'][i]),dt)for i in range(2)];velocity=state['velocity_xy'][:];speed=bits(P.hypot_ref(*map(fp,delta)))
 if C.rational(speed)<40:
  smoothing=C.sub(C.ONE,exp_small(dt^0x80000000));velocity=[C.add(v,C.mul(smoothing,C.sub(d,v)))for d,v in zip(delta,velocity)];counts['velocity_smoothing_branch']+=1
 else:counts['velocity_jump_filtered']+=1
 for row in rows[:count]:
  marker=S.read(row,0);assert marker in(0,1)
  if marker:counts['dead_rows_skipped']+=1;continue
  assert S.read(row,244)==0xffffffff
  if S.read(row,284)==0 or S.read(row,64)!=0xffffffff or S.read(row,16):continue
  xyz=T.position(row,now);assert C.rational(C.distance(xyz[:2],player[:2]))<=3025;counts['far55_predicates_not_taken']+=1;counts['moving_far_guard_predicates']+=S.read(row,344)!=0
 minute=C.div(now,bits(60.));rate=C.mul(C.add(C.add(C.mul(minute,0x3ea3d70a),0x3f666666),C.mul(minute,C.mul(minute,0x3ccccccd))),0x3f19999a);decay=exp_small(C.div(dt,0xc1400000));cost=C.mul(s['cost'],decay);catchup=max(C.ONE,min(bits(3.),C.div(C.mul(C.div(cost,bits(12.)),bits(1.25)),max(0x3a83126f,rate,key=C.rational)),key=C.rational),key=C.rational);rate=C.mul(rate,catchup);budget=C.add(state['budget2416_bits'],C.mul(dt,rate));counts['positive_decay']+=1;counts['positive_catchup']+=C.rational(catchup)>1
 definitions=ctx['definitions'];eligible=[i for i,d in enumerate(definitions)if not d[68]and C.rational(u(d,64))<=C.rational(minute)]
 def attempt(index,origin):
  nonlocal count,words,counter
  alive=sum(S.read(r,0)^1 for r in rows[:count]);assert alive<50
  path=None if ai['path']is None else dict(field24=ai['path']['field24'],values_u16=ai['path_values'])
  loc=PathPosition(dict(player_xyz=player,velocity_xy=velocity,low_radius_bits=bits(26.),high_radius_bits=bits(36.),bias_probability_bits=bits(.5),rng_words=words,distance_map=path),ctx['world'],ctx['nav'],ctx['scalars'],ctx['heading']);xyz=loc.spawn();words=loc.words
  if count==len(rows):rows.extend([[None]*432 for _ in range(max(4,2*len(rows))-len(rows))])
  row,words,counter,packet=birth(index,now,xyz,player,words,counter,rows[count],definitions,ctx['zone'],ctx['heading'],ctx['spawn_speeds'],counts,level);rows[count]=row;packets.append(packet);born.append(dict(slot=count,definition_index=index,guid=str(D.read(row,112,8)),origin=origin,position_bits=xyz,path_queries=loc.count['path_cost_reads']));counts['newNPC']+=1;counts['densityNPC']+=origin=='density';counts['path_cost_queries']+=loc.count['path_cost_reads'];count+=1
 if C.rational(budget)>=1:
  for _ in range(8):
   index,words=S.choose(eligible,minute,words,definitions,counts);unitcost=u(definitions[index],60)
   if C.rational(unitcost)>C.rational(budget):break
   attempt(index,'budget');budget=C.sub(budget,unitcost)
   if C.rational(budget)<1:break
 target=int(min(Fraction(36),C.rational(C.add(C.mul(minute,0x3fcccccd),bits(4.)))));alive=sum(S.read(r,0)==0 and S.read(r,284)!=0 and definitions[(S.read(r,284)-5830904)//72][68]==0 for r in rows[:count]);density=min(3,max(0,target-alive))
 for _ in range(density):index,words=S.choose(eligible,minute,words,definitions,counts);attempt(index,'density')
 assert all(C.rational(now)<C.rational(v)for v in state['timer_fields'].values()if v not in(0,20))and C.rational(now)<40
 state=copy.deepcopy(state);state.update(player_level1432=level,last_wave2586=255,count=count,capacity=len(rows),rng_words=list(words),counter2408=counter,now_bits=now,budget2416_bits=budget,kill_cost2420_bits=cost,previous_player_xyz=list(player),velocity_xy=velocity)
 s.update(rows=copy.deepcopy(rows[:count]),words=list(words),counter=counter,cost=cost);p['g'].update(rng_words=list(words),now_bits=now);p['scalar']['2352']=now;p['NPC']=copy.deepcopy(s['rows'])
 return state,p,s,rows,count,packets,born,dict(decay_bits=decay,catchup_bits=catchup,rate_bits=rate)

heading_ref=P.heading_ref
hypot_ref=P.hypot_ref

def main():
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(SOURCE)==WASM and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
 hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');rt=load(BATCH/'runtime.json');authors=hand['author_files'];assert len(authors)==8
 for n,h in authors.items():assert sha(ROOT/n)==h
 sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==104 and sum(n.startswith('reconstruction/')for n in sources)==86
 for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
 edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==445
 for table in[comp['artifacts'],comp['frozen'],prep['frozen']]:
  for n,h in table.items():assert sha(BATCH/n)==h
 assert comp['cases']==comp['completed_cases']==6 and comp['differences']==0 and comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']and not load(BATCH/'expectation-read-audit.json')['forbidden']
 assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
 assert prep['resource_context_gate_sha256']==sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
 wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';assert sha(wp)==prep['independent_world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
 required_helpers={**S.HELPERS,**AI.HELPERS,'scripts/review_spawn_schedule139_v3.py':'264b675f93b9e74b271dc1cfa80892407bff088b6f6143e6b2fc7bd1e7268c6e'}
 for n,h in required_helpers.items():assert sha(ROOT/n)==h
 ctx=load_context();raw,module,data=ctx['raw'],ctx['module'],ctx['data'];ctx.update(zone=data(5871348,152),definitions=[data(5830904+72*i,72)for i in range(12)])
 private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
 for a,b in zip(module['sections'],private['sections'],strict=True):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
 assert private['exports']==module['exports']+[tuple(v)for v in m['added_exports']]and len(module['imports'])==882 and[(r['module'],r['name'],r['type_index'])for r in module['imports']]==[(r['module'],r['name'],r['type_index'])for r in m['original_imports']]
 bindings={};texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as f:
  for idx,claim in m['functions'].items():
   a,z=module['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();f.seek(lo);wat=f.read(hi-lo);record=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());assert all(record[k]==claim[k]for k in record)and wat==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=record;texts[int(idx)]=wat.decode();(out/f'{idx}.wat').write_bytes(wat)
 assert len(bindings)==78 and 'call 26521'in texts[952]and'f32.const -0x1.8p+3 (;=-12;)'in texts[952]and'f32.const 0x1.4p+0 (;=1.25;)'in texts[952]
 assert 'f32.const 0x1.55551ep-3'in texts[26521]and'f32.const -0x1.6aa42ap-9'in texts[26521]and'i32.const 1051816472'in texts[26521]
 for key,claim in m['static_reads'].items():
  address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==claim['sha256']
 cases=load(BATCH/'inputs.json');actual=[json.loads(v)for v in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==6
 counts=Counter();traces=[]
 def cells(label,want,hx):
  observed=bytes.fromhex(hx);assert len(want)==len(observed)
  for j,(v,b)in enumerate(zip(want,observed,strict=True)):
   if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
   else:assert v==b,(label,j,v,b);counts[label+'_known']+=1
 def player(obs,p,label):
  want=U.project(p);assert obs['capture']['projection']==want['growth'],(label,'growth',[(k,str(v)[:90],str(obs['capture']['projection'].get(k))[:90])for k,v in want['growth'].items()if v!=obs['capture']['projection'].get(k)])
  for key in['racial80_hex','scalar','source_flags','spell_sets']:assert obs[key]==want[key],(label,key)
  for key,width in[('live',32),('aura',16)]:
   for field in['capacity','count']+(['flag2569']if key=='aura'else[]):assert obs[key][field]==want[key][field],(label,key,field)
   for row,hx in zip(want[key]['storage'],obs[key]['storage'],strict=True):cells(key,row,hx)
  game=bytes.fromhex(obs['capture']['raw_game2592_hex']);assert G.tree_fields(obs['capture'],game)==want['growth']['player_fields']
 def combat(obs,p,s,physical=None):
  want=Life.combat(p,s,physical)
  for key,v in want.items():
   if key=='records432_cells':
    for row,hx in zip(v,obs['records432_hex'],strict=True):cells('producerNPC',row,hx)
   elif key=='pickups56_cells':
    for row,hx in zip(v,obs['pickups56_hex'],strict=True):cells('producerPickup',row,hx)
   else:assert v==obs[key],('combat',key,v,obs.get(key))
 for case,A in zip(cases,actual,strict=True):
  assert case['id']==A['id']and case['app_seed_u64']=='11'and case['amount']==5 and case['select_index']==0 and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['stack_after']==1048576
  full,p,s,ai,L,physical,count=prepare(case,ctx,A,player,combat,counts);op=full['projection'];assert A['opening']['packets']==op['packets'];cells('openingGame',full['known_Game2592'],A['opening']['raw_game2592_hex'])
  assert A['after_producer_ai']['path']==ai['path']and A['after_producer_healing']['event_counter960']==L['event_counter960'];state=dict(budget2416_bits=bits(3.),previous_player_xyz=[0,0,0],velocity_xy=[0,0],timer_fields={'2424':bits(60.),'2440':bits(240.),'2444':bits(40.),'2448':bits(60.),'2452':20,'2456':0});previous=A['after_producer'];frames=[]
  for j,(control,obs)in enumerate(zip(case['updates'],A['frames'],strict=True)):
   assert len(control['actions_before'])==len(obs['interleaved_casts'])
   for action,seen in zip(control['actions_before'],obs['interleaved_casts'],strict=True):
    extra_cast(p,s,L,action,ctx,counts);player(seen['after'],p,'interleaved922');combat(seen['combat'],p,s)
   if control['actions_before']:physical=copy.deepcopy(s['rows'])+physical[count:]
   now,dt=control['now_bits'],control['dt_bits'];assert dt==0x3dcccccd;p['scalar']['2352']=now
   player(obs['before'],p,'pre952')
   if not case.get('cooccur_probe')and not control['actions_before']:
    inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);struct.pack_into('<I',inherited,2352,now);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['Game_input_inheritance_bytes']+=2592
   oldcount=count;oldphysical=copy.deepcopy(physical);state,p,s,physical,count,packets,born,diag=spawn(state,p,s,ai,physical,count,now,dt,ctx,counts)
   assert obs['spawn']=={k:state[k]for k in obs['spawn']},('spawn',case['id'],j,[(k,state.get(k),v)for k,v in obs['spawn'].items()if state.get(k)!=v])
   player(obs['after'],p,'after952');assert obs['new_packets']==packets;counts['known_target_packets']+=len(packets);counts['known_target_packet_bytes']+=sum(len(hx)//2 for op,hx in packets)
   bg=obs['after']['capture']['background'];old=obs['before']['capture']['background'];assert(bg['units']['capacity'],bg['units']['count'])==(len(physical),count)
   for row,hx in zip(physical,bg['units']['storage'],strict=True):cells('targetNPC',row,hx)
   assert old['units']['storage'][:oldcount]==bg['units']['storage'][:oldcount];counts['existingNPC_full432_conserved']+=432*oldcount
   for key in['pickups','special','windows','boundaries','auxiliary','claims','movement_sequence2412']:assert bg[key]==old[key]
   assert obs['before_ai']==obs['ai']
   beforegame=bytes.fromhex(obs['before']['capture']['raw_game2592_hex']);aftergame=bytes.fromhex(obs['after']['capture']['raw_game2592_hex']);wanted=bytearray(beforegame)
   for off,value in[(1720+4*k,v)for k,v in enumerate(state['rng_words'])]+[(1736,state['velocity_xy'][0]),(1740,state['velocity_xy'][1]),(1784,state['capacity']),(1792,state['count']),(2408,state['counter2408']),(2416,state['budget2416_bits']),(2420,state['kill_cost2420_bits']),*[(2428+4*k,v)for k,v in enumerate(state['previous_player_xyz'])]]:struct.pack_into('<I',wanted,off,value)
   pc=u(beforegame,1888)+len(packets);cap=u(beforegame,1880)
   while pc>cap:cap=max(4,cap*2)
   struct.pack_into('<I',wanted,1880,cap);struct.pack_into('<I',wanted,1888,pc)
   for capoff,ptroff in[(1784,1788),(1880,1884)]:
    if u(wanted,capoff)!=u(beforegame,capoff):assert u(aftergame,ptroff)>0;wanted[ptroff:ptroff+4]=aftergame[ptroff:ptroff+4];counts['reallocated_pointer_observations']+=1
   assert bytes(wanted)==aftergame,(case['id'],j,'wholeGame',[(i,x,y)for i,(x,y)in enumerate(zip(wanted,aftergame))if x!=y][:8]);counts['fullGame2592_bytes']+=2592;counts['targets952']+=1;frames.append(dict(spawn=copy.deepcopy(state),born=born,diagnostic=diag));previous=obs['after']
  assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16];traces.append(dict(id=case['id'],cooccur=case.get('cooccur_probe',False),frames=frames))
 assert counts['targets952']==18 and counts['newNPC']==24 and counts['densityNPC']==6 and counts['known_target_packets']==24 and counts['known_target_packet_bytes']==4296 and counts['source_preceding_pairs']==120 and counts['positive_catchup']>0
 assert rt==comp['runtime']and rt['fresh_instances']==6 and rt['full_calls']=={'922':19,'925':124,'952':18,'1076':0,'1093':6,'1108':6,'1238':0,'1600':6,'1775':0,'2123':146,'2945':6,'3755':0,'4677':6}and rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None
 assert len(rt['target_and_setup_returns'])==337 and all(v['before']==v['after']==1048576 and v['returned']for v in rt['target_and_setup_returns'])and len(rt['world_source_checks'])==337 and all(v['ranges']==2318 and v['unchanged']for v in rt['world_source_checks'])and rt['stack_checks']==367 and rt['allocator_calls']==30
 for key in['old_Game_used_as_target','readiness_flags_injected','NPC_dead_or_HP_or_position_writes','NPC_records_removed_by_driver','physical_capacity_or_staleTail_cleared','source_headers_cleared','live_racial_CD_cleared','HP_filled_or_reset','NPC_HP_killcost_budget_RNG_timers_written_by_driver','App_or_world_Rc_producer_executed','externref_restored']:assert not rt[key]
 assert rt['native_executions']==rt['full_mainloop_frames']==rt['complete_games']==0 and rt['peak_memory_bytes']==177078272<=rt['memory_cap_bytes']==268435456 and rt['output_bytes']==(BATCH/'actual.jsonl').stat().st_size
 term=load(BATCH/'owned-terminal.json');assert term==comp['process']==hand['original_process']and term['exit_code']==0 and term['pid_missing']and term['pgid_missing']
 for n,h in authors.items():assert sha(ROOT/n)==h
 for n,h in sources.items():assert sha(ROOT/n)==h
 for n,h in required_helpers.items():assert sha(ROOT/n)==h
 assert not AUDIT
 helpers={str(Path(v.__file__).relative_to(ROOT)):sha(v.__file__)for v in list(sys.modules.values())if getattr(v,'__file__',None)and str(v.__file__).startswith(str(ROOT/'scripts'))and Path(v.__file__).name!=Path(__file__).name}
 result=dict(accepted=True,scope='current139 combat-source controlled18full952 only',author_handoff_sha256=HAND,comparison_sha256=COMP,reviewer_sha256=sha(Path(__file__)),author_files=authors,helper_source_sha256=helpers,current_body_bindings=bindings,source_files=104,production_files=86,source_edges=445,formal_counts=dict(fixtures=6,target_full952=18,source_setup_entries=319,direct_entries=337,source_preceding_pairs_numeric_only=120,reviewer_author_program_executions=0,reviewer_original_executions=0),counts=dict(counts),traces=traces,original_process=term,author_expected_values_read=False,full884_frames=0,complete_games=0,seconds=time.monotonic()-start,limits=['Six explicit actual-damage component sources: XP5/firstThunder/controlledplayerpositions are setup, not natural level progression or fullmain.', '18targets952 replace925 at two final moving/nonfullHPsource steps; preceding120pairs are numeric source only, no newly accepted packet/fullmain ordering.', 'Nonzero killcost decay/catchup,6positive density births,level2/realBFS andmoving NPCposition predicates restored; existingdead rows retained and not counted alive; no50cap saturation runtime claim.', 'Current26521 finite-small arguments only, Fraction ordered polynomial; other exp ranges/nonfinite/endless are not validated.', '24complete ordered1694296B; sourceprefix packet/UI streams are not newfullpacket acceptance.', 'All18wholeGame2592 overlays/50544B existingNPC432 plus knownNone logical storage/background preserved; allocator addresses observed only at predicted capacity growth.', 'New scheduler sources not a fresh60s wave regression; v3 old4096 runtime never transferred to newv4.', 'World/query/resource-onlyv2context and previously frozen pure references explicit; no App/WorldRc/externref producer/native/fullgame.'])
 save(out/'review.json',result);print(json.dumps(dict(accepted=True,formal_counts=result['formal_counts'],counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
