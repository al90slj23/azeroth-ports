#!/usr/bin/env python3
"""Different-author current139 two ordinary families: read-only reference.

Independent source reference precedes frozen author capture review. No author
or original function executes; no expected JSON values are read.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
 if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen')or event=='import'and str(args[0]).startswith(('core_spec','resource_spec')):
  AUDIT['forbidden_author_original_execution']+=1;raise RuntimeError('Read-only reviewer refuses '+event)
sys.addaudithook(audit)
import review_enemy_ai139 as AI
import review_player_autocast139 as R
import review_spawn_schedule139_v3 as S
import review_spawn_combat139 as Spawn
from review_combat139 import sha,parse_module,local_closure,fp,bits,f32
from review_world_position139 import load_world
from review_initial139 import reference as constructor_reference,record as initial_record
C=R.C;U=R.U;G=R.G;O=R.O;D=R.D;T=R.T;H=R.H
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
STATIC=ROOT/'evidence/ordinary-family139-independent-preparation-20261102T161651.907861Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]
def tick_family(state,dt,world,nav,neighbors,names,english,counts):
    state=copy.deepcopy(state);now=C.add(state['now'],dt);state['now']=now;player=state['player']
    if state['path']is None:
        state['path'],values=AI.breadth_first(nav,player,neighbors);state['path_values']=values;state['path_clock']=now;recomputed=True;counts['path_rebuilds']+=1;counts['BFS_values']+=len(values)
    else:
        assert AI.probe(nav,player[:2])[1]==state['path']['start_index'];recomputed=False
    motions=[];attacks=[];routing=[]
    for row in state['rows']:
        assert all(AI.word(row,p)==0xffffffff for p in(40,64,244))and AI.word(row,284)in names and row[424]==0
        assert all(AI.word(row,p)==0 for p in(0,8,16,240,360,380,388,396,416,420))
        if AI.lt(now,AI.word(row,408)):continue
        pos=AI.position(row,now);timer=C.sub(AI.word(row,352),dt);AI.put(row,352,timer);target=AI.word(row,112,8)
        if AI.le(AI.distance(pos,player),AI.word(row,308)):
            if AI.lt(0,AI.word(row,344))and AI.lt(now,C.add(AI.word(row,340),AI.word(row,344))):
                for k,v in enumerate(pos):AI.put(row,316+4*k,v);AI.put(row,328+4*k,v)
                AI.put(row,340,now);AI.put(row,344,0);motions.append((target,pos,pos,0))
            if AI.le(timer,0)and AI.le(AI.word(row,412),now):
                AI.put(row,352,AI.word(row,304));weak=AI.word(row,128)if AI.lt(now,AI.word(row,132))else AI.word(row,136)if AI.lt(now,AI.word(row,140))else 0
                attacks.append([target,C.mul(AI.word(row,296),C.sub(C.ONE,weak))])
            continue
        if AI.lt(now,AI.word(row,348)):continue
        angle=C.add(AI.word(row,404),0x3e19999a);AI.put(row,404,angle);sine,cosine=AI.trig(angle)
        radius=AI.maximum(C.mul(AI.word(row,308),0x3f4ccccd),0x3fc00000)
        dest=(C.add(player[0],C.mul(radius,cosine)),C.add(player[1],C.mul(radius,sine)),player[2]);length=AI.distance(pos,dest)
        if AI.lt(0x41600000,length):
            factor=C.div(0x41600000,length);dest=(C.add(pos[0],C.mul(C.sub(dest[0],pos[0]),factor)),C.add(pos[1],C.mul(C.sub(dest[1],pos[1]),factor)),pos[2]);counts['clamped14_motions']+=1
        assert AI.segment(nav,pos,dest,counts)==C.ONE,'Blocked-flow branch remains Pending; do not reuse old acceptance'
        routing.append([target,'direct_clear']);counts['direct_clear_routes']+=1
        speed=AI.word(row,300)
        if AI.lt(now,AI.word(row,124)):speed=C.mul(speed,C.sub(C.ONE,AI.word(row,120)))
        if AI.lt(now,AI.word(row,412)):speed=C.mul(speed,0x3faccccd)
        duration=C.div(AI.distance(pos,dest),AI.maximum(speed,0x3f000000))
        for k,v in enumerate(pos):AI.put(row,316+4*k,v)
        for k,v in enumerate(dest):AI.put(row,328+4*k,v)
        AI.put(row,340,now);AI.put(row,344,duration);AI.put(row,348,C.add(now,AI.minimum(AI.maximum(duration,0x3e800000),0x3f333333)));motions.append((target,pos,dest,duration))
    packets=[]
    for target,start,end,duration in motions:
        state['sequence']=(state['sequence']+1)&0xffffffff;packets.append(AI.packet221(world,target,start,end,duration,state['sequence'],counts))
    for target,amount in attacks:
        damage=C.mul(amount,C.sub(C.ONE,state['derived']['1568']));shown=max(1,int(C.rational(damage)))
        packets.append([330,(struct.pack('<I',2)+C.packguid(target)+C.packguid(0)+struct.pack('<I',shown)+b'\1'+struct.pack('<IfI6I',0,float(shown),shown,0,0,1,0,0,0)).hex()])
        assert all(state['guards'][p]==0 for p in state['guards'])and C.rational(state['hp'])>C.rational(damage)
        state['hp']=C.sub(state['hp'],damage);state['last']=now;state['incoming']+=fp(damage);state['category']+=fp(damage);state['has_category']=True
        source=next(row for row in state['rows']if AI.word(row,112,8)==target);assert AI.word(source,284)in names and source[424]==0
        AI.I.append_ring(state['history'],now,fp(damage),0.,fp(state['hp']),state['derived']['1536'],(names[AI.word(source,284)],english['Melee'],'INV_Sword_04'),0,0)
        state['fields'].update({'22':math.ceil(fp(state['hp'])),'28':math.ceil(fp(state['derived']['1536']))});counts['contacts']+=1
    state['packets'].extend(packets)
    answer=dict(frame=state['frame'],records=copy.deepcopy(state['rows']),hp1440_bits=state['hp'],last_hit1652_bits=state['last'],incoming992_hex=struct.pack('>d',state['incoming']).hex(),categories={'mob melee':struct.pack('>d',state['category']).hex()}if state['has_category']else{},fields=copy.deepcopy(state['fields']),history=AI.I.ring_projection(state['history']),path=copy.deepcopy(state['path']),path_clock2372_bits=state['path_clock'],movement_sequence2412=state['sequence'],packets=copy.deepcopy(state['packets']),attacks=attacks,routing=routing,path_recomputed=recomputed)
    state['frame']+=1;counts['frames']+=1;counts['movement221']+=len(motions);return state,answer



def damage_family(p,s,L,index,amount,critical,spell,school,now,world,scalars,speeds,definitions,counts):
 row=s['rows'][index];normal=definitions[D.read(row,284)];target=D.read(row,112,8);assert D.read(row,0)==0
 mult=C.ONE
 if C.rational(now)<C.rational(D.read(row,148)):mult=C.add(mult,D.read(row,144))
 term=D.read(row,152)if C.rational(now)<C.rational(D.read(row,156))else D.read(row,160)if C.rational(now)<C.rational(D.read(row,164))else 0
 mult=C.add(C.add(C.add(mult,term),D.read(row,368)),0);schoolterm=0x3dcccccd if school&254==2 and C.rational(now)<C.rational(D.read(row,372))else 0
 damage=C.mul(C.mul(amount,C.add(mult,schoolterm)),C.ONE);damage=damage if C.rational(damage)>1 else C.ONE
 old=D.read(row,288);hp=C.sub(old,damage);account=min(max(C.rational(old),0),C.rational(damage))
 s['total']=C.bits64(C.f64(s['total'])+float(account));s['spelltotals'][spell]=C.bits64(C.f64(s['spelltotals'].get(spell,0))+float(account));D.put(row,288,hp)
 reason={0:'melee',845:'ability:cleave:r1',6343:'ability:thunder_clap:r1'}[spell];H.account(L,reason,C.rounded(account),now,[],damage=True)
 g=p['g'];new,delta=H.heal_number(g['current_hp_bits'],g['derived_bits']['1536'],C.mul(C.mul(damage,0x3c75c28f),C.ONE));g['current_hp_bits']=new;g['player_fields'].update({'22':math.ceil(C.rational(new)),'28':math.ceil(C.rational(g['derived_bits']['1536']))});heals=[];H.account(L,'leech',delta,now,heals)
 packets=[];dead=C.rational(hp)<=0;counts['damage']+=1;counts['critical']+=critical
 if dead:
  xyz=T.position(row,now);duration=D.read(row,344)
  if C.rational(duration)>0 and C.rational(now)<C.rational(C.add(D.read(row,340),duration)):
   s['sequence']=(s['sequence']+1)&C.M;height=world.height(xyz[0],xyz[1]);stopxyz=(xyz[0],xyz[1],xyz[2]if height is None else height)
   packets.append([221,(C.packguid(target)+struct.pack('<4I',*stopxyz,s['sequence'])+bytes([1])).hex()]);counts['moving_deaths']+=1
  D.put(row,0,1);D.put(row,4,now);D.put(row,240,0)
  for off in(316,328):row[off:off+12]=struct.pack('<3I',*xyz)
  D.put(row,340,now);D.put(row,344,0);s['kills']=(s['kills']+1)&C.M;s['elites']=(s['elites']+(row[424]&1))&C.M;s['cost']=C.add(u(normal,60),s['cost']);counts['deaths']+=1
  random,s['words']=D.uniform24(s['words']);scaled=C.mul(C.rounded(Fraction(u(normal,56))),0x3fd33333);whole=int(C.rational(scaled));xp=whole+int(C.rational(C.sub(scaled,C.rounded(Fraction(whole))))>C.rational(random))
  if xp:
   packet,_=D.pickup(0,xp,xyz,world,scalars,speeds,s);D.put(s['pickups'][s['pickup_count']-1],52,now);packets.append(packet)
  random,s['words']=D.uniform24(s['words'])
  if C.rational(random)<C.rational(0x3e28f5c3):
   for _ in range(10000):
    w,s['words']=C.nextword(s['words']);product=w*3
    if product&C.M<=0xbfffffff:break
   else:raise AssertionError('Bounded currency RNG')
   coin=[C.add(xyz[0],0x3f4ccccd),C.add(xyz[1],0x3f4ccccd),xyz[2]];packet,_=D.pickup(1,(product>>32)+2,coin,world,scalars,speeds,s);D.put(s['pickups'][s['pickup_count']-1],52,now);packets.append(packet)
 counts['Leech']+=len(heals)
 return packets,heals


BATCH=ROOT/'evidence/ordinary-family139-full-20261102T154148.091148Z'
HAND='7483df1cd8157bd863dc91646f6d96373e3a0b869f95024f47bbd47d4444ce5a'
COMP='d13f38570b09a89258d46cad3a73cc1b93e61db9af205997c0a46e9422b62be6'


def initial_reference(case,ctx):
 full,_=O.reference(case,ctx['world'],ctx['nav'],ctx['scalars'],ctx['heading'],ctx['normal'],ctx['spawn_speeds'],ctx['classes'],ctx['races'],ctx['zones'],ctx['eligible'],ctx['minutes']);op=full['projection']
 ctor,_=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=full['constructor_seed_u64'],object_id_u64='0',flat_height_bits=ctx['world'].height(*ctx['scalars']['center_xy_bits'])),ctx['classes'],ctx['races'],ctx['zones'])
 g=dict(level=1,xp=0,pending=0,phase2587=1,current_hp_bits=ctor['current_hp_bits'],derived_bits=ctor['derived_bits'],player_fields=ctor['player_fields'],rng_words=op['rng_words'],candidates=[],selection_kind2585=255,generation_counter2400=0,owned_records80_hex=ctor['owned_records_hex'],flag2581=0,flags2573=0,now_bits=0)
 p=dict(g=g,live=[],count=0,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]],NPC=copy.deepcopy(op['units']['storage']),player=op['player_xyz'])
 s=dict(rows=copy.deepcopy(op['units']['storage']),words=list(op['rng_words']),sets=[[],[],[]],total=0,spelltotals={},kills=0,elites=0,counter=op['counter'],sequence=1,cost=0,pickups=copy.deepcopy(op['pickups']['storage']),pickup_count=op['pickups']['count'],gold=0,earned=0)
 ai=dict(rows=copy.deepcopy(s['rows']),now=0,frame=0,player=p['player'],path=None,path_values=None,path_clock=0,sequence=1,hp=g['current_hp_bits'],last=p['scalar']['1652'],incoming=0.,category=0.,has_category=False,derived=g['derived_bits'],guards={o:0 for o in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(g['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=[])
 return full,p,s,ai,H.ledger(),copy.deepcopy(s['rows']),4


def enemy_step(p,s,ai,physical,count,now,dt,ctx,counts):
 physical=copy.deepcopy(s['rows'])+copy.deepcopy(physical[count:]);alive=[];removed=[]
 for i,row in enumerate(physical[:count]):
  marker=D.read(row,0);assert marker in(0,1)and D.read(row,284)in ctx['names']
  if not marker:alive.append(i)
  else:
   assert all(D.read(row,k)==0xffffffff for k in[40,64,244])and D.read(row,232)==0 and row[424]==0
   if C.rational(C.sub(now,D.read(row,4)))>C.rational(0x3f99999a):removed.append(str(D.read(row,112,8)))
 ai=copy.deepcopy(ai);ai.update(rows=[copy.deepcopy(physical[i])for i in alive],now=C.sub(now,dt),player=p['player'],hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],derived=p['g']['derived_bits'],fields=copy.deepcopy(p['g']['player_fields']),sequence=s['sequence'],packets=[])
 if ai['path']is not None and AI.probe(ctx['nav'],p['player'][:2])[1]!=ai['path']['start_index']:
  assert C.rational(C.sub(now,ai['path_clock']))>=C.rational(0x3e4ccccd)
  ai['path'],ai['path_values']=AI.breadth_first(ctx['nav'],p['player'],ctx['neighbors']);ai['path_clock']=now;counts['path_refreshes']+=1
 ai,answer=tick_family(ai,dt,ctx['world'],ctx['nav'],ctx['neighbors'],ctx['names'],{'Melee':'Melee'},counts);assert ai['now']==now
 for i,row in zip(alive,ai['rows'],strict=True):physical[i]=row
 before=copy.deepcopy(physical)
 for guid in removed:
  kept=[copy.deepcopy(row)for row in physical[:count]if str(D.read(row,112,8))!=guid]
  for j,row in enumerate(kept):physical[j]=row
  count=len(kept)
 s['rows']=copy.deepcopy(physical[:count]);s['sequence']=ai['sequence'];p['NPC']=copy.deepcopy(s['rows']);p['g']['current_hp_bits']=ai['hp'];p['g']['player_fields']=copy.deepcopy(ai['fields']);p['scalar']['1652']=ai['last'];p['g']['now_bits']=now;p['scalar']['2352']=now
 counts['removed_corpses']+=len(removed);return ai,physical,count,[[170,int(g).to_bytes(8,'little').hex()]for g in removed]+answer['packets'],before,removed,answer


def main():
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(SOURCE)==WASM and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
 hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');rt=load(BATCH/'runtime.json');authors=hand['author_files'];assert len(authors)==9
 for n,h in authors.items():assert sha(ROOT/n)==h
 sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==103 and sum(n.startswith('reconstruction/')for n in sources)==87
 for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
 edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==418
 for table in[comp['frozen'],prep['frozen']]:
  for n,h in table.items():assert sha(BATCH/n)==h
 assert comp['cases']==comp['completed_cases']==4 and comp['differences']==0 and comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']and not comp['forbidden_model_reads']and not load(BATCH/'expectation-read-audit.json')['forbidden']
 assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
 helpers={**S.HELPERS,**AI.HELPERS,'scripts/review_spawn_schedule139_v3.py':'264b675f93b9e74b271dc1cfa80892407bff088b6f6143e6b2fc7bd1e7268c6e','scripts/review_spawn_combat139.py':'79878046c39d39431622093bc706b6e42dcf17980a8c007bd78f627ec7db0ace'}
 oldref=ROOT/'evidence/spawn-combat139-independent-owned-20261102T152712.290110Z/review/review.json';assert sha(oldref)=='d82c990d5f042fb1ded0f6e32d90c4b126069650927d67d1c2ccfbba4b529213'
 for n,h in load(oldref)['helper_source_sha256'].items():
  if n in [str(Path(v.__file__).relative_to(ROOT))for v in list(sys.modules.values())if getattr(v,'__file__',None)and str(v.__file__).startswith(str(ROOT/'scripts'))]:helpers[n]=h
 for n,h in helpers.items():assert sha(ROOT/n)==h
 ctx=Spawn.load_context();data=ctx['data'];raw=ctx['raw'];module=ctx['module'];ctx.update(zone=data(5871348,152),definitions=[data(5830904+72*i,72)for i in range(12)],family_definitions={p:data(p,72)for p in[5830904,5830976]},names={5830904:'Kobold Vermin',5830976:'Young Wolf'})
 wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';assert sha(wp)=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'and sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
 private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
 for a,b in zip(module['sections'],private['sections'],strict=True):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
 assert private['exports']==module['exports']+[tuple(v)for v in m['added_exports']]and len(module['imports'])==882 and[(x['module'],x['name'],x['type_index'])for x in module['imports']]==[(x['module'],x['name'],x['type_index'])for x in m['original_imports']]
 trace=m['ordinary_family_trace'];claims={**m['functions'],**trace['functions']};bindings={};texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as f:
  for idx,claim in claims.items():
   a,z=module['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();f.seek(lo);wat=f.read(hi-lo);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());assert all(proof[k]==claim[k]for k in proof)and wat==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=proof;texts[int(idx)]=wat.decode();(out/f'{idx}.wat').write_bytes(wat)
 assert len(bindings)==169 and trace['original_calls']==0 and not trace['import_callees']
 prior=load(STATIC/'binding.json')
 for idx,proof in prior['bodies'].items():assert bindings[idx]==proof
 for group in[m['static_reads'],trace['static_reads']]:
  for key,claim in group.items():
   address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==claim['sha256']
 for rec in trace['definitions']:
  ptr=rec['pointer'];d=data(ptr,72);assert d==ctx['family_definitions'][ptr]and d.hex()==rec['raw72_hex']and hashlib.sha256(d).hexdigest()==rec['raw72_sha256']and data(u(d,16),u(d,20)).decode()==ctx['names'][ptr]==rec['fallback']==rec['english_name']and u(d,56)==rec['XP56']==1 and u(d,60)==rec['cost60_bits']==C.ONE and d[68]==rec['classification68']==0
 engp,engn=struct.unpack('<II',data(5401532,8));english=json.loads(data(engp,engn))
 for ptr,name in ctx['names'].items():assert english['enemy.'+str(u(ctx['family_definitions'][ptr],24))]==name
 assert {r['pointer']:r['english']for r in prior['definitions']}==ctx['names']
 assert texts[925].index('call 40215')<texts[925].index('i32.const 170')<texts[925].index('i32.const 221')<texts[925].index('call 1076')and'i32.const 284'in texts[913]and'f32.load offset=60'in texts[913]and'i32.const 56'in texts[913]
 counts=Counter();traces=[]
 def cells(label,want,hx):
  seen=bytes.fromhex(hx);assert len(want)==len(seen)
  for index,(v,b)in enumerate(zip(want,seen,strict=True)):
   if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
   else:assert v==b,(label,index,v,b);counts[label+'_known']+=1
 def player(obs,p,label,initial_flag):
  want=U.project(p);assert obs['capture']['projection']==want['growth'],(label,'growth',[(k,v,obs['capture']['projection'].get(k))for k,v in want['growth'].items()if v!=obs['capture']['projection'].get(k)])
  for key in['racial80_hex','scalar','source_flags','spell_sets']:assert obs[key]==want[key],(label,key)
  game=bytes.fromhex(obs['capture']['raw_game2592_hex']);assert G.tree_fields(obs['capture'],game)==want['growth']['player_fields']
  for key in['live','aura']:
   for field in['capacity','count']:assert obs[key][field]==want[key][field]
   if key=='aura':assert obs[key]['flag2569']==(initial_flag if want[key]['flag2569']is None else want[key]['flag2569'])
   for row,hx in zip(want[key]['storage'],obs[key]['storage'],strict=True):cells(key,row,hx)
 def view(obs,p,s,ai,L,physical,count,initial_flag,label):
  player(obs['player'],p,label,initial_flag)
  wanted=dict(records432_cells=s['rows'],rng_words=list(s['words']),accounted_total_bits=str(s['total']),spell_sets=p['sets'],player_xyz=list(p['player']),phase2587=p['g']['phase2587'],spell_totals64=[[k,str(v)]for k,v in sorted(s['spelltotals'].items())],kills1084=s['kills'],elites1088=s['elites'],counter2408=s['counter'],movement_sequence2412=s['sequence'],killcost2420_bits=s['cost'],player_hp1440_bits=p['g']['current_hp_bits'],maximum1536_bits=p['g']['derived_bits']['1536'],xp1436=p['g']['xp'],pickup_capacity=len(s['pickups']),pickup_count=s['pickup_count'],pickups56_cells=s['pickups'])
  for k,v in wanted.items():
   if k=='records432_cells':
    for row,hx in zip(v,obs['combat']['records432_hex'][:count],strict=True):cells('NPCactive',row,hx)
   elif k=='pickups56_cells':
    for row,hx in zip(v,obs['combat']['pickups56_hex'],strict=True):cells('pickup',row,hx)
   else:assert obs['combat'][k]==v,(label,k,v,obs['combat'][k])
  units=obs['player']['capture']['background']['units'];assert units['capacity']==len(physical)and units['count']==count
  for row,hx in zip(physical,units['storage'],strict=True):cells('NPCphysical',row,hx)
  for k,v in L.items():assert obs['healing'][k]==v,(label,k,v,obs['healing'][k])
  aggregate=bytes.fromhex(obs['healing']['accounting_struct68_hex']);game=bytes.fromhex(obs['player']['capture']['raw_game2592_hex']);assert struct.unpack_from('<Q',game,960)[0]==int(L['event_counter960'])and game[1000:1068]==aggregate and struct.unpack_from('<Q',aggregate,16)[0]==int(L['accepted_count1016'])
  decoded={}
  for r in obs['healing']['stats_keys']:
   raw96=bytes.fromhex(r['raw96']);assert obs['healing']['stats']['storage'][r['index']]==r['raw96']and struct.unpack_from('<Q',raw96,8)[0]==int(r['total64']);decoded[r['reason']]=C.bits64(C.f64(decoded.get(r['reason'],0))+C.f64(int(r['total64'])))
  assert{k:str(v)for k,v in decoded.items()}==L['reason_totals64']
  expected_breakdown=[dict(name='Leech',icon='Spell_Shadow_LifeDrain02',total64=v,owns=0,nested_count=0)for k,v in L['reason_totals64'].items()if k=='leech'];assert[{k:r[k]for k in['name','icon','total64','owns','nested_count']}for r in obs['healing']['breakdown']]==expected_breakdown
  for k in['source_registry','saved_history']:assert[obs['healing'][k][z]for z in['capacity','pointer','count']]==[0,8,0]
  for k,v in dict(path=ai['path'],path_clock2372_bits=ai['path_clock'],incoming992_hex=struct.pack('>d',ai['incoming']).hex(),last_hit1652_bits=ai['last'],categories={'mob melee':struct.pack('>d',ai['category']).hex()}if ai['has_category']else{}).items():assert obs['ai'][k]==v,(label,'AI',k)
  hist=AI.I.ring_projection(ai['history']);assert obs['ai']['history']['header']==hist['header']and obs['ai']['history']['active']==hist['active']
  for row,hx in zip(hist['storage'],obs['ai']['history']['storage'],strict=True):cells('history',row,hx)
  assert obs['gold1456']==obs['earned1100']==0
  for q in['xp_queue','coin_queue']:assert[obs[q][z]for z in['capacity','pointer','count']]==[0,4,0]
 def match_packets(want,got,complete):
  if complete:assert want==got,('completepackets',want,got)
  else:
   cursor=0
   for pkt in want:cursor=next(k for k in range(cursor,len(got))if got[k]==pkt)+1
  counts['known_packets']+=len(want);counts['known_packet_bytes']+=sum(len(h)//2 for op,h in want);counts['observed_packets']+=len(got);counts['observed_packet_bytes']+=sum(len(h)//2 for op,h in got)
 cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==4
 assert[(x['app_seed_u64'],x['hits'][0]['spell_id'],x['hits'][0]['critical'])for x in cases]==[('0',0,0),('1',845,1),('5',845,0),('8',0,1)]
 for case,A in zip(cases,actual,strict=True):
  assert case['id']==A['id']and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['stack_after']==1048576
  full,p,s,ai,L,physical,count=initial_reference(case,ctx);flag=A['initial']['player']['aura']['flag2569'];view(A['initial'],p,s,ai,L,physical,count,flag,'initial');op=full['projection'];assert A['opening']['packets']==op['packets'];cells('openingGame',full['known_Game2592'],A['opening']['raw_game2592_hex'])
  now=bits(30.1);dt=0x3dcccccd;assert case['spawn']==dict(now_bits=now,dt_bits=dt)
  sched=dict(budget2416_bits=bits(3.),previous_player_xyz=[0,0,0],velocity_xy=[0,0],timer_fields={'2424':bits(60.),'2440':bits(240.),'2444':bits(40.),'2448':bits(60.),'2452':20,'2456':0});sc=Counter();sched,p,s,physical,count,packets,born,diagnostic=Spawn.spawn(sched,p,s,ai,physical,count,now,dt,ctx,sc);assert A['spawn']=={k:sched[k]for k in A['spawn']};view(A['after_spawn'],p,s,ai,L,physical,count,flag,'spawn');match_packets(packets,A['spawn_packets'],True);counts['full952']+=1;counts['spawn_births']+=len(born)
  assert A['initial']['player']['capture']['background']['units']['storage']==A['after_spawn']['player']['capture']['background']['units']['storage'][:4];counts['initialNPC_raw_preserved']+=1728
  wolves=[D.read(r,112,8)for r in s['rows']if D.read(r,284)==5830976];target=wolves[0]if wolves else D.read(s['rows'][0],112,8);definition=D.read(next(r for r in s['rows']if D.read(r,112,8)==target),284);assert A['wolf_count']==len(wolves)and A['target_definition']==definition
  previous=A['after_spawn'];steps=[]
  for group in['frames','hits','cleanup']:
   assert len(case[group])==len(A[group])==(8 if group=='frames'else 3 if group=='hits'else 2)
   for j,(control,obs)in enumerate(zip(case[group],A[group],strict=True)):
    now=control['now_bits']
    if group=='frames':
     assert str(target)==control['follow_guid'];row=next(r for r in s['rows']if D.read(r,112,8)==target);p['player']=T.position(row,now);assert list(p['player'])==control['player_xyz']
    elif group=='cleanup':assert tuple(control['player_xyz'])==tuple(p['player'])
    p['g']['now_bits']=now;p['scalar']['2352']=now;inherited=bytearray.fromhex(previous['player']['capture']['raw_game2592_hex']);U.put(inherited,2352,now)
    if 'player_xyz'in control:struct.pack_into('<3I',inherited,1416,*control['player_xyz'])
    assert inherited.hex()==obs['before']['player']['capture']['raw_game2592_hex'];counts['Game_input_inheritance_bytes']+=2592;view(obs['before'],p,s,ai,L,physical,count,flag,group+'before')
    oldraw=obs['before']['player']['capture']['background']['units']['storage'];oldcount=count
    if group=='hits':
     assert control['target_guid']==str(target)and control['amount_bits']==[C.ONE,bits(250.),C.ONE][j]and control['suppress_flag']==(1 if control['spell_id']==0 else 0)
     index=next(k for k,row in enumerate(s['rows'])if D.read(row,112,8)==target);applied=D.read(s['rows'][index],0)==0
     if applied:packets,heals=damage_family(p,s,L,index,control['amount_bits'],control['critical'],control['spell_id'],control['school'],now,ctx['world'],ctx['scalars'],ctx['speeds'],ctx['family_definitions'],counts)
     else:packets=[];heals=[]
     physical=copy.deepcopy(s['rows'])+physical[count:];p['g']['rng_words']=list(s['words']);p['NPC']=copy.deepcopy(s['rows']);counts['full913']+=1;counts['accepted_hits']+=applied;counts['positive_Leech']+=len(heals);match_packets(packets,obs['new_packets'],False)
     if not applied:assert obs['before']==obs['after']and not obs['new_packets']
     before_removal=physical;removed=[]
    else:
     ai,physical,count,packets,before_removal,removed,answer=enemy_step(p,s,ai,physical,count,now,control['dt_bits'],ctx,counts);match_packets(packets,obs['new_packets'],True);counts['full925']+=1;counts['AI_attacks']+=len(answer['attacks'])
    view(obs['after'],p,s,ai,L,physical,count,flag,group+'after')
    replay=[bytearray.fromhex(hx)for hx in oldraw]
    for k,row in enumerate(before_removal):
     for off,v in enumerate(row):
      if v is not None:replay[k][off]=v
    n=oldcount
    for guid in removed:
     retained=[r[:]for r in replay[:n]if str(int.from_bytes(r[112:120],'little'))!=guid]
     for k,row in enumerate(retained):replay[k]=row
     n=len(retained)
    assert n==count and[r.hex()for r in replay]==obs['after']['player']['capture']['background']['units']['storage'];counts['NPC_physical_replay_bytes']+=432*len(replay)
    for key in['special','windows','boundaries','auxiliary','claims']:assert obs['after']['player']['capture']['background'][key]==A['initial']['player']['capture']['background'][key]
    assert obs['after']['player']['capture']['background']['pickups']['storage'][:2]==A['initial']['player']['capture']['background']['pickups']['storage'][:2]
    steps.append(dict(group=group,index=j,now_bits=now,target_definition=definition,known_packets=packets,removed=removed,ledger=copy.deepcopy(L),hp=p['g']['current_hp_bits']));previous=obs['after']
  assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]
  counts['cases']+=1;counts['Wolf_cases']+=bool(wolves);traces.append(dict(seed=case['app_seed_u64'],wolf_count=len(wolves),target_definition=definition,born=born,steps=steps))
 assert counts['cases']==4 and counts['Wolf_cases']==2 and counts['full952']==4 and counts['full925']==40 and counts['full913']==12 and counts['accepted_hits']==8 and counts['deaths']==4 and counts['positive_Leech']==8 and counts['AI_attacks']==23 and counts['removed_corpses']==4 and counts['known_packets']==154 and counts['known_packet_bytes']==9277 and counts['observed_packets']==170 and counts['observed_packet_bytes']==9801
 assert rt==comp['runtime']and rt['full_calls']=={'913':12,'922':0,'925':40,'952':4,'1076':0,'1093':0,'1108':4,'1238':0,'1600':4,'1775':0,'2123':0,'2890':0,'2945':4,'3755':0,'4677':0}and rt['fresh_instances']==4 and rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None
 assert len(rt['target_and_setup_returns'])==68 and all(r['before']==r['after']==1048576 and r['returned']for r in rt['target_and_setup_returns'])and len(rt['world_source_checks'])==64 and all(r['ranges']==2318 and r['unchanged']for r in rt['world_source_checks'])and rt['stack_checks']==88 and rt['allocator_calls']==20
 assert rt['peak_memory_bytes']==177078272<=rt['memory_cap_bytes']==268435456 and rt['output_bytes']==(BATCH/'actual.jsonl').stat().st_size and not any(rt[k]for k in['old_Game_used_as_target','App_or_world_Rc_producer_executed','NPC_definition_HP_position_status_or_storage_writes','HP_or_RNG_reset','live_racial_or_owned_disabled'])and rt['native_executions']==rt['full_mainloop_frames']==rt['complete_games']==0
 term=load(BATCH/'owned-terminal.json');assert term==comp['process']==hand['process']and term['exit_code']==0 and term['pid_missing']and term['pgid_missing']
 for n,h in authors.items():assert sha(ROOT/n)==h
 for n,h in sources.items():assert sha(ROOT/n)==h
 for n,h in helpers.items():assert sha(ROOT/n)==h
 assert not AUDIT
 result=dict(accepted=True,scope='current139 two ordinary families controlled full952/925/913 only',author_handoff_sha256=HAND,comparison_sha256=COMP,source_sha256=WASM,reviewer_sha256=sha(Path(__file__)),author_files=authors,helper_sha256=helpers,source_counts=dict(files=103,production=87,edges=418,bodies=169),current_body_bindings=bindings,formal_counts=dict(fixtures=4,full952=4,full925=40,full913=12,target_entries=56,setup2945_1600_1108=12,direct_entries=68,reviewer_author_program_executions=0,reviewer_original_executions=0),counts=dict(counts),definitions=prior['definitions'],traces=traces,original_process=term,author_expected_values_read=False,full884_frames=0,complete_games=0,seconds=time.monotonic()-start,limits=['Current139KoboldVermin/YoungWolf only; twoWolfcases plus twoKoboldcontrols, not everyordinaryfamily.', 'Full952 at controlledclock30.1 produces real7NPCs; playerfollows actualtarget positions, no NPCfilter/HP/RNG/CD/statusclearing. This is not natural30seconds orfullmainframe.', 'Complete925packetstream plus fullspawn169; direct913onlyknown orderedsubset.154known9277B of170observed9801B; unknown16/524B not rebuilt.', 'Direct913basicspell0/flag1 andownedcleave845/flag0; inputcritical flag doesnotdouble suppliedamount. Thunder/Demo staticidentityfields confer0dynamicacceptance.', 'AIEnglishnames/genericmelee/class0 source/history/currentHP/f64categories andrealBFS verified; nonfatalnofatal/shield/modifier/blockedflowonly.', 'Stable432corpseremoval/count/staleTail/no unknownfilling; allsourceactors retained. FullGameclock/playercontrolinput inherited, outputGameownerprojectiononly/wholeheapnotpredicted.', 'SemanticG960/G1016/reasonf64/Vec48 only; physical2077containers/UI/network/native/bootstrap remainsPending.', '7pre-runsources+2postcapturereports frozen; originaldoubleLFpreserved, noformatrewrite. Pilotsnotcounted, oldacceptance nottransferred.'])
 save(out/'review.json',result);print(json.dumps(dict(accepted=True,formal_counts=result['formal_counts'],counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
