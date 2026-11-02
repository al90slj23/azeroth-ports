#!/usr/bin/env python3
"""Different-author current139 Demo1160 cast/weakness/AI reference.

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
import review_ordinary_family139 as F
from review_combat139 import sha,parse_module,local_closure,fp,bits,f32
from review_world_position139 import load_world
from review_initial139 import reference as constructor_reference,record as initial_record
C=R.C;U=R.U;G=R.G;O=R.O;D=R.D;T=R.T;H=R.H
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]
def tick_demo(state,dt,world,nav,neighbors,names,english,counts,live):
    state=copy.deepcopy(state);now=C.add(state['now'],dt);state['now']=now;player=state['player']
    if state['path']is None:
        state['path'],values=AI.breadth_first(nav,player,neighbors);state['path_values']=values;state['path_clock']=now;recomputed=True;counts['path_rebuilds']+=1;counts['BFS_values']+=len(values)
    else:
        assert AI.probe(nav,player[:2])[1]==state['path']['start_index'];recomputed=False
    motions=[];attacks=[];routing=[];expired=[]
    for row in state['rows']:
        if AI.word(row,0)==0 and AI.word(row,360):
            assert AI.word(row,360)==1160
            expiry=AI.word(row,132)if AI.lt(now,AI.word(row,132))else AI.word(row,140)
            if AI.le(expiry,now):expired.append(AI.word(row,112,8));AI.put(row,360,0)
    for row in state['rows']:
        assert all(AI.word(row,p)==0xffffffff for p in(40,64,244))and AI.word(row,284)in names and row[424]==0
        assert all(AI.word(row,p)==0 for p in(0,8,16,240,380,388,396,416,420))
        assert AI.word(row,360)in(0,1160)
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
        # Current1076 guards active kind12 before HP/history;925alreadyemitted330.
        if any(U.read(r,8)==12 and C.rational(U.read(r,24))>C.rational(now)for r in live):
            counts['active_live12_guarded_contacts']+=1;continue
        assert all(state['guards'][p]==0 for p in state['guards'])and C.rational(state['hp'])>C.rational(damage)
        state['hp']=C.sub(state['hp'],damage);state['last']=now;state['incoming']+=fp(damage);state['category']+=fp(damage);state['has_category']=True
        source=next(row for row in state['rows']if AI.word(row,112,8)==target);assert AI.word(source,284)in names and source[424]==0
        AI.I.append_ring(state['history'],now,fp(damage),0.,fp(state['hp']),state['derived']['1536'],(names[AI.word(source,284)],english['Melee'],'INV_Sword_04'),0,0)
        state['fields'].update({'22':math.ceil(fp(state['hp'])),'28':math.ceil(fp(state['derived']['1536']))});counts['contacts']+=1
    for target in expired:
        row=next(r for r in state['rows']if AI.word(r,112,8)==target)
        aura(row,target,1160,False,packets,counts);counts['expiry169']+=1
    state['packets'].extend(packets)
    answer=dict(frame=state['frame'],records=copy.deepcopy(state['rows']),hp1440_bits=state['hp'],last_hit1652_bits=state['last'],incoming992_hex=struct.pack('>d',state['incoming']).hex(),categories={'mob melee':struct.pack('>d',state['category']).hex()}if state['has_category']else{},fields=copy.deepcopy(state['fields']),history=AI.I.ring_projection(state['history']),path=copy.deepcopy(state['path']),path_clock2372_bits=state['path_clock'],movement_sequence2412=state['sequence'],packets=copy.deepcopy(state['packets']),attacks=attacks,routing=routing,path_recomputed=recomputed)
    state['frame']+=1;counts['frames']+=1;counts['movement221']+=len(motions);return state,answer

def damage_demo(p,s,L,index,amount,critical,spell,school,now,world,scalars,speeds,definitions,counts):
 row=s['rows'][index];normal=definitions[D.read(row,284)];target=D.read(row,112,8);assert D.read(row,0)==0
 mult=C.ONE
 if C.rational(now)<C.rational(D.read(row,148)):mult=C.add(mult,D.read(row,144))
 term=D.read(row,152)if C.rational(now)<C.rational(D.read(row,156))else D.read(row,160)if C.rational(now)<C.rational(D.read(row,164))else 0
 mult=C.add(C.add(C.add(mult,term),D.read(row,368)),0);schoolterm=0x3dcccccd if school&254==2 and C.rational(now)<C.rational(D.read(row,372))else 0
 damage=C.mul(C.mul(amount,C.add(mult,schoolterm)),C.ONE);damage=damage if C.rational(damage)>1 else C.ONE
 old=D.read(row,288);hp=C.sub(old,damage);account=min(max(C.rational(old),0),C.rational(damage))
 s['total']=C.bits64(C.f64(s['total'])+float(account));s['spelltotals'][spell]=C.bits64(C.f64(s['spelltotals'].get(spell,0))+float(account));D.put(row,288,hp)
 reason={0:'melee',845:'ability:cleave:r1',6343:'ability:thunder_clap:r1',1160:'ability:demo_shout:r1'}[spell];H.account(L,reason,C.rounded(account),now,[],damage=True)
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

BATCH=ROOT/'evidence/demo-shout139-full-20261102T161613.361873Z'
HAND='1bc0a32cf30a2acf12ef0543565c64b3c189ebe39c7612e5c260a964de306a4b'
COMP='40976feb20905b34e7fb8a6a76cb5257cc251914551ae8da8a9c668dc55522a1'

def aura(row,target,spell,adding,packets,counts):
 assert D.read(row,0)==0 and D.read(row,240)==0
 slots=[D.read(row,168+4*i)for i in range(16)]
 if adding:
  if spell in slots or 0 not in slots:return
  slot=slots.index(0);slots[slot]=spell
 else:
  if spell not in slots:return
  slot=slots.index(spell);slots[slot]=0
 D.put(row,168+4*slot,slots[slot]);group=slot//8
 fields={79+slot:slots[slot],99+group:sum(2<<(4*i)for i,v in enumerate(slots[group*8:group*8+8])if v),121+slot//4:0}
 count=max(fields)//32+1;masks=[sum(1<<(k%32)for k in fields if k//32==j)for j in range(count)]
 payload=struct.pack('<IB',1,0)+bytes(1)+C.packguid(target)+bytes([count])+struct.pack('<'+'I'*count,*masks)+struct.pack('<'+'I'*len(fields),*(fields[k]for k in sorted(fields)))
 packets.append([169,payload.hex()]);counts['Aura169']+=1

def merge(words,strength,deadline,now):
 a,ae,b,be=words
 if C.le(ae,now):a,ae=(b,be)if not C.le(be,now)else(0,0);b,be=0,0
 if C.le(ae,now)or not C.le(strength,a)or strength==a and not C.le(deadline,ae):other=(a,ae);a,ae=strength,deadline
 else:other=strength,deadline
 chosen=None
 for v,e in[(b,be),other]:
  if C.le(v,0)or C.le(e,now)or C.le(e,ae):continue
  if chosen is None or not C.le(v,chosen[0])or v==chosen[0]and not C.le(e,chosen[1]):chosen=v,e
 return a,ae,*(chosen or(0,0))

def cast(p,s,L,now,ctx,counts):
 g=p['g'];d=ctx['defs']['demo_shout'][1];owned=bytes.fromhex(g['owned_records80_hex'][1]);derived=g['derived_bits'];radius=C.mul(derived['1580'],C.mul(u(d,60),C.mul(u(owned,24),u(owned,64))));assert 0<C.rational(radius)<=70
 square=C.mul(radius,radius);chosen=[i for i,row in enumerate(s['rows'])if D.read(row,0)==0 and C.le(C.distance(T.position(row,now),p['player']),square)];chosen=D.stable(chosen,lambda i:C.totalkey(C.distance(T.position(s['rows'][i],now),p['player'])))
 ids=[D.read(s['rows'][i],112,8)for i in chosen]
 for words in p['sets']:
  if 1160 not in words:words.append(1160)
 s['sets']=copy.deepcopy(p['sets'])
 value=C.mul(C.mul(C.mul(C.mul(u(d,48),0x3fb33333),u(owned,12)),u(owned,52)),0x3f000000);life=C.mul(derived['1536'],u(owned,72))if C.rational(u(d,48))>0 else 0;base=C.mul(derived['1540'],C.add(value,life));duration=C.mul(u(d,8),u(owned,68));strength=C.mul(u(d,4),u(owned,76));strength=strength if C.rational(strength)<C.rational(0x3f666666)else 0x3f666666
 packets=[[306,(bytes(2)+struct.pack('<IHB',1160,256,len(ids))+b''.join(struct.pack('<Q',x)for x in ids)+bytes(3)).hex()]]if ids else[];heals=[];hits=[]
 for index in chosen:
  roll,s['words']=D.uniform24(s['words']);critical=int(C.rational(derived['1548'])>C.rational(roll));amount=C.mul(base,derived['1552'])if critical else base
  pk,hs=damage_demo(p,s,L,index,amount,critical,1160,0,now,ctx['world'],ctx['scalars'],ctx['speeds'],ctx['family_definitions'],counts);packets.extend(pk);heals.extend(hs);row=s['rows'][index];dead=D.read(row,0)==1;hits.append(dict(target=str(D.read(row,112,8)),amount_bits=amount,critical=critical,dead=dead))
  if dead:counts['killing_effect_skipped']+=1;continue
  deadline=C.add(now,duration);words=merge(tuple(D.read(row,k)for k in[128,132,136,140]),strength,deadline,now)
  for off,w in zip([128,132,136,140],words,strict=True):D.put(row,off,w)
  if words[:2]==(strength,deadline):D.put(row,364,duration)
  previous=D.read(row,360)
  if previous!=1160:
   assert previous==0;D.put(row,360,1160);aura(row,D.read(row,112,8),1160,True,packets,counts)
  counts['effect_applications']+=1
 p['NPC']=copy.deepcopy(s['rows']);g['rng_words']=list(s['words']);counts['full922']+=1;counts['success']+=bool(ids);counts['max_targets']=max(counts['max_targets'],len(ids));counts['hits']+=len(ids)
 return packets,dict(selected_ids=list(map(str,ids)),radius_bits=radius,base_damage_bits=base,strength_bits=strength,duration_bits=duration,hits=hits)

def setup(case,ctx):
 full,p,s,ai,L,physical,count=F.initial_reference(case,ctx);g=p['g'];before=copy.deepcopy(g);before.pop('now_bits');assert case['amount']==5 and case['dead_mask']==0
 g['xp']=5;g['xp']-=G.threshold(1);g['level']=2;g['pending']=1;G.recalculate(g,ctx['classes'],ctx['races']);g['current_hp_bits']=g['derived_bits']['1536'];g['player_fields'].update({'22':math.ceil(fp(g['current_hp_bits'])),'28':math.ceil(fp(g['derived_bits']['1536'])),'34':2,'716':0,'717':G.threshold(2)})
 cards,words,draws=G.candidates(g['rng_words'],ctx['kit'],2);g.update(candidates=cards,rng_words=words,phase2587=2,selection_kind2585=0,generation_counter2400=1);gain=copy.deepcopy(g);gain.pop('now_bits');card=cards[case['select_index']];assert card['variant']=='new'and card['ability_id']=='demo_shout'and card['tier']==(0 if case['app_seed_u64']=='2'else 2)
 g['owned_records80_hex'].append(G.selected_record('demo_shout',card['tier'],ctx['defs'],ctx['cooldown'],ctx['damage']));G.recalculate(g,ctx['classes'],ctx['races']);g.update(candidates=[],phase2587=1,pending=0,selection_kind2585=255,flag2581=1,flags2573=0)
 live=[None]*32;live[:8]=bytes(8);live[8:12]=struct.pack('<I',12);live[20:32]=struct.pack('<III',1020,C.ONE,0);p['live']=[live]+[[None]*32 for _ in range(3)];p['count']=1;U.sync_aura(p)
 s.update(words=list(words),sets=copy.deepcopy(p['sets']));ai.update(derived=g['derived_bits'],hp=g['current_hp_bits'],fields=copy.deepcopy(g['player_fields']))
 return full,p,s,ai,L,before,gain,card['tier']

def main():
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(SOURCE)==WASM and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
 hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');rt=load(BATCH/'runtime.json');authors=hand['author_files'];assert len(authors)==9
 for n,h in authors.items():assert sha(ROOT/n)==h
 sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==94 and sum(n.startswith('reconstruction/')for n in sources)==77
 for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
 edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==393
 for table in[comp['frozen'],comp['artifacts'],prep['frozen']]:
  for n,h in table.items():assert sha(BATCH/n)==h
 assert comp['cases']==comp['completed_cases']==16 and comp['differences']==0 and comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']and not load(BATCH/'expectation-read-audit.json')['forbidden']
 assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
 oldref=ROOT/'evidence/ordinary-family139-independent-owned-20261102T162445.590649Z/review/review.json';assert sha(oldref)=='cd478dda3b9bb4c943c1f97a746ea15f7a698b9dcaf3b5447299c8d51a1d114d';helpers=load(oldref)['helper_sha256'];helpers['scripts/review_ordinary_family139.py']='aebfd5bafa00be2fe3253e42f6d6013ff2d1cf109f13267fa56ef44da2419f93'
 for n,h in helpers.items():assert sha(ROOT/n)==h
 ctx=Spawn.load_context();data=ctx['data'];raw=ctx['raw'];module=ctx['module'];ctx.update(family_definitions={5830904:data(5830904,72)},names={5830904:'Kobold Vermin'})
 wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';assert sha(wp)=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'and sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
 private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
 for a,b in zip(module['sections'],private['sections'],strict=True):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
 assert private['exports']==module['exports']+[tuple(v)for v in m['added_exports']]and len(module['imports'])==882 and[(x['module'],x['name'],x['type_index'])for x in module['imports']]==[(x['module'],x['name'],x['type_index'])for x in m['original_imports']]
 bindings={};texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as f:
  for idx,claim in m['functions'].items():
   a,z=module['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();f.seek(lo);wat=f.read(hi-lo);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());assert all(proof[k]==claim[k]for k in proof)and wat==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=proof;texts[int(idx)]=wat.decode();(out/f'{idx}.wat').write_bytes(wat)
 assert len(bindings)==36
 for key,claim in m['static_reads'].items():
  address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==claim['sha256']
 definition=data(5883180,88);assert definition==ctx['defs']['demo_shout'][1]and definition.hex()==m['demo_shout88_hex']and u(definition)==11 and definition[84:86]==bytes([2,0])and u(definition,44)==1160 and u(definition,8)==bits(6.)and u(definition,60)==bits(14.)
 assert all(s in texts[922]for s in['call 27754','call 10490','call 913','f32.const 0x1.ccccccp-1','f32.const 0x1.666666p+0'])and 'call 21553'in texts[2189]and 'f32.store offset=12'in texts[21553]and 'call 4593'in texts[925]
 assert texts[925].index('i32.const 221')<texts[925].index('call 1076')<texts[925].index('call 4593')and 'i32.store offset=360'in texts[925]
 guard='\n'.join(texts[1076].splitlines()[58:101]);assert 'i32.const 12'in guard and 'f32.gt'in guard and 'br 2'in guard
 effect=texts[2189];assert effect.index('i32.const 128')<effect.index('call 21553')<effect.index('i32.const 364')<effect.index('i32.const 360')
 counts=Counter();traces=[]
 def cells(label,want,hx):
  seen=bytes.fromhex(hx);assert len(want)==len(seen)
  for index,(v,b)in enumerate(zip(want,seen,strict=True)):
   if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
   else:assert v==b,(label,index,v,b);counts[label+'_known']+=1
 def player(obs,p,label):
  want=U.project(p);assert obs['capture']['projection']==want['growth'],(label,'growth',[(k,v,obs['capture']['projection'].get(k))for k,v in want['growth'].items()if v!=obs['capture']['projection'].get(k)])
  for key in['racial80_hex','scalar','source_flags','spell_sets']:assert obs[key]==want[key],(label,key)
  game=bytes.fromhex(obs['capture']['raw_game2592_hex']);assert G.tree_fields(obs['capture'],game)==want['growth']['player_fields']
  for key in['live','aura']:
   for field in['capacity','count']:assert obs[key][field]==want[key][field]
   if key=='aura':assert obs[key]['flag2569']==want[key]['flag2569']
   for row,hx in zip(want[key]['storage'],obs[key]['storage'],strict=True):cells(key,row,hx)
 def background(obs,initial):
  for key in['live','aura','racial80_hex']:assert obs[key]==initial[key]
  assert obs['capture']['background']['units']['capacity']==obs['capture']['background']['units']['count']==4
  for key in['auxiliary','claims','special','windows','boundaries']:assert obs['capture']['background'][key]==initial['capture']['background'][key]
  assert obs['capture']['background']['pickups']['storage'][:2]==initial['capture']['background']['pickups']['storage'][:2]
 def physical(old,new,rows):
  assert len(old)==len(new)==len(rows)
  for oldhx,newhx,row in zip(old,new,rows,strict=True):
   replay=bytearray.fromhex(oldhx)
   for k,v in enumerate(row):
    if v is not None:replay[k]=v
   assert replay.hex()==newhx;counts['NPC_fullphysical_replay_bytes']+=len(replay)
 def healing(obs,L):
  for k,v in L.items():assert obs[k]==v,('healing',k,v,obs[k])
  decoded={}
  for r in obs['stats_keys']:
   raw96=bytes.fromhex(r['raw96']);assert obs['stats']['storage'][r['index']]==r['raw96']and struct.unpack_from('<Q',raw96,8)[0]==int(r['total64']);decoded[r['reason']]=C.bits64(C.f64(decoded.get(r['reason'],0))+C.f64(int(r['total64'])))
  assert{k:str(v)for k,v in decoded.items()}==L['reason_totals64'];assert not obs['source_registry']['count']and not obs['saved_history']['count']
  assert[{k:r[k]for k in['name','icon','total64','owns','nested_count']}for r in obs['breakdown']]==[dict(name='Leech',icon='Spell_Shadow_LifeDrain02',total64=v,owns=0,nested_count=0)for k,v in L['reason_totals64'].items()if k=='leech']
 def combat(obs,p,s,success=None):
  values=dict(rng_words=list(s['words']),accounted_total_bits=str(s['total']),spell_sets=p['sets'],owned80_hex=p['g']['owned_records80_hex'][1],player_xyz=list(p['player']),phase2587=1,spell_totals64=[[k,str(v)]for k,v in sorted(s['spelltotals'].items())],kills1084=s['kills'],elites1088=s['elites'],counter2408=s['counter'],movement_sequence2412=s['sequence'],killcost2420_bits=s['cost'],player_hp1440_bits=p['g']['current_hp_bits'],maximum1536_bits=p['g']['derived_bits']['1536'],xp1436=0,pickup_capacity=len(s['pickups']),pickup_count=s['pickup_count'])
  if success is not None:values['success']=success
  for k,v in values.items():assert obs[k]==v,('combat',k,v,obs[k])
  for row,hx in zip(s['rows'],obs['records432_hex'],strict=True):cells('NPC',row,hx)
  for row,hx in zip(s['pickups'],obs['pickups56_hex'],strict=True):cells('pickup',row,hx)
 def match(want,got,complete,label):
  if complete:assert want==got,(label,want,got)
  else:
   cursor=0
   for pkt in want:cursor=next(k for k in range(cursor,len(got))if got[k]==pkt)+1
  counts[label+'_known_packets']+=len(want);counts[label+'_known_bytes']+=sum(len(h)//2 for op,h in want);counts[label+'_observed_packets']+=len(got);counts[label+'_observed_bytes']+=sum(len(h)//2 for op,h in got)
 cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==16
 for case,A in zip(cases,actual,strict=True):
  assert case['id']==cases.index(case)and case['amount']==5 and case['dead_mask']==0
  if case['id']<12:
   k=case['id']%6;n=[1,2,1,1,1,32][k];assert case['app_seed_u64']==('2'if case['id']<6 else'3')and case['select_index']==(0 if case['id']<6 else 1)and case['casts']==[bits(j/8)for j in range(n)]and case['ai_updates']==[]
   assert case['action']['offset_x_bits']==bits([100.,0.,13.9990234375,14.,14.0009765625,0.][k])and case['action']['offset_y_bits']==0
  else:
   assert case['app_seed_u64']=='3'and case['select_index']==1 and case['casts']==[0]
   assert case['ai_updates']==([]if case['id']==12 else[dict(now_bits=bits(2. if case['id']==13 else 6.),dt_bits=C.ONE)]if case['id']<15 else[dict(now_bits=bits((j+1)/8),dt_bits=bits(.125))for j in range(64)])
  assert case['id']==A['id']and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['stack_after']==1048576
  full,p,s,ai,L,before,gain,tier=setup(case,ctx);op=full['projection'];assert A['constructor_seed_u64']==full['constructor_seed_u64']and A['opening']['packets']==op['packets'];cells('openingGame',full['known_Game2592'],A['opening']['raw_game2592_hex']);assert A['before']['projection']==before and A['gain']['projection']==gain;player(A['player_before'],p,'initial')
  for stage in['opening','before','gain','selection']:assert A[stage]['background']==A['opening']['background']
  anchor=T.position(s['rows'][case['action']['npc_index']],0);a=case['action'];xy=(C.add(anchor[0],a['offset_x_bits']),C.add(anchor[1],a['offset_y_bits']));assert ctx['world'].height(*xy)==a['height_bits'];p['player']=(*xy,a['height_bits']);player(A['controlled_before'],p,'controlled');prior=bytearray.fromhex(A['player_before']['capture']['raw_game2592_hex']);struct.pack_into('<3I',prior,1416,*p['player']);assert prior.hex()==A['controlled_before']['capture']['raw_game2592_hex'];counts['controlledGame_exact_bytes']+=2592
  previous=A['controlled_before'];stages=[]
  for j,(now,obs)in enumerate(zip(case['casts'],A['cast_stages'],strict=True)):
   p['g']['now_bits']=now;p['scalar']['2352']=now;prior=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(prior,2352,now);assert prior.hex()==obs['before']['capture']['raw_game2592_hex'];player(obs['before'],p,'castbefore');combat(obs['before_combat'],p,s)
   packets,diag=cast(p,s,L,now,ctx,counts);player(obs['after'],p,'castafter');combat(obs['combat'],p,s,int(bool(diag['selected_ids'])));healing(obs['healing'],L);assert obs['after']==obs['after_cast']
   physical(obs['before']['capture']['background']['units']['storage'],obs['after']['capture']['background']['units']['storage'],s['rows']);background(obs['after'],A['controlled_before']);match(packets,obs['new_packets'],False,'cast')
   for q in['hits','areas']:assert obs['pending_before'][q]==obs['pending_after'][q]and obs['pending_after'][q]['count']==0
   assert obs['source_headers']=={str(k):0 for k in[176,600,648,1984,2032,2044,2056]}and obs['empty_consumers_not_executed'];counts['Game_input_inheritance_bytes']+=2592;stages.append(dict(now_bits=now,**diag,known_packets=packets));previous=obs['after']
  ai.update(rows=copy.deepcopy(s['rows']),hp=p['g']['current_hp_bits'],derived=p['g']['derived_bits'],fields=copy.deepcopy(p['g']['player_fields']),player=p['player'],sequence=s['sequence'],last=p['scalar']['1652'])
  for control,obs in zip(case['ai_updates'],A['ai_stages'],strict=True):
   now=control['now_bits'];dt=control['dt_bits'];p['g']['now_bits']=now;p['scalar']['2352']=now;prior=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(prior,2352,now);assert prior.hex()==obs['before']['capture']['raw_game2592_hex'];player(obs['before'],p,'AIbefore')
   ai.update(now=C.sub(now,dt),packets=[]);ai,answer=tick_demo(ai,dt,ctx['world'],ctx['nav'],ctx['neighbors'],ctx['names'],{'Melee':'Melee'},counts,p['live'][:p['count']]);assert ai['now']==now
   s['rows']=copy.deepcopy(ai['rows']);s['sequence']=ai['sequence'];p['NPC']=copy.deepcopy(s['rows']);p['g']['current_hp_bits']=ai['hp'];p['g']['player_fields']=copy.deepcopy(ai['fields']);p['scalar']['1652']=ai['last'];player(obs['after'],p,'AIafter');physical(obs['before']['capture']['background']['units']['storage'],obs['after']['capture']['background']['units']['storage'],s['rows']);background(obs['after'],A['controlled_before']);match(answer['packets'],obs['new_packets'],True,'AI')
   for k,v in dict(path=ai['path'],path_clock2372_bits=ai['path_clock'],incoming992_hex=struct.pack('>d',ai['incoming']).hex(),last_hit1652_bits=ai['last'],categories={'mob melee':struct.pack('>d',ai['category']).hex()}if ai['has_category']else{}).items():assert obs['ai'][k]==v,('AI',k,v,obs['ai'][k])
   hist=AI.I.ring_projection(ai['history']);assert obs['ai']['history']['header']==hist['header']and obs['ai']['history']['active']==hist['active']
   for row,hx in zip(hist['storage'],obs['ai']['history']['storage'],strict=True):cells('history',row,hx)
   counts['full925']+=1;counts['AI_attacks']+=len(answer['attacks']);counts['Game_input_inheritance_bytes']+=2592;previous=obs['after']
  assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16];counts['cases']+=1;traces.append(dict(id=case['id'],seed=case['app_seed_u64'],tier=tier,action=case['action'],stages=stages))
 assert counts['cases']==16 and counts['full922']==80 and counts['full925']==66 and counts['hits']==41 and counts['critical']==1 and counts['deaths']==2 and counts['max_targets']==1 and counts['AI_attacks']==9 and counts['expiry169']==2 and counts['active_live12_guarded_contacts']==1
 assert(counts['cast_known_packets'],counts['cast_known_bytes'],counts['cast_observed_packets'],counts['cast_observed_bytes'])==(55,1668,139,5703)and(counts['AI_known_packets'],counts['AI_known_bytes'])==(48,2297)
 assert rt==comp['runtime']and rt['full_calls']=={'922':80,'925':66,'1093':16,'1108':16,'1600':16,'1775':0,'2945':16,'3755':0,'4677':16}and rt['fresh_instances']==16 and rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None
 assert len(rt['target_and_setup_returns'])==226 and all(r['before']==r['after']==1048576 and r['returned']for r in rt['target_and_setup_returns'])and len(rt['world_source_checks'])==226 and all(r['ranges']==2318 and r['unchanged']for r in rt['world_source_checks'])and rt['stack_checks']==306 and rt['allocator_calls']==80
 assert rt['peak_memory_bytes']==177078272<=rt['memory_cap_bytes']==268435456 and rt['output_bytes']==(BATCH/'actual.jsonl').stat().st_size and not any(rt[k]for k in['old_Game_used_as_target','App_or_world_Rc_producer_executed','readiness_flags_injected','NPC_HP_or_records_or_CD_or_RNG_written_by_driver','explicit_dead_marker_fixtures','empty1775_3755_executions'])and rt['native_executions']==rt['full_mainloop_frames']==rt['complete_games']==0
 term=load(BATCH/'owned-terminal.json');assert term==comp['process']==hand['process']and term['exit_code']==0 and term['pid_missing']and term['pgid_missing']
 for table in[authors,sources,helpers]:
  for n,h in table.items():assert sha(ROOT/n)==h
 assert not AUDIT
 result=dict(accepted=True,scope='current139 controlled directDemo1160/weakness and AI925 only',author_handoff_sha256=HAND,comparison_sha256=COMP,source_sha256=WASM,reviewer_sha256=sha(Path(__file__)),author_files=authors,helper_sha256=helpers,source_counts=dict(files=94,production=77,edges=393,bodies=36),current_body_bindings=bindings,formal_counts=dict(fixtures=16,full922=80,full925=66,target_entries=146,setup2945_1600_1108_4677_1093=80,direct_entries=226,reviewer_author_program_executions=0,reviewer_original_executions=0),counts=dict(counts),definition88_hex=definition.hex(),traces=traces,original_process=term,first_reference_domain_failure='evidence/demo-shout139-independent-owned-20261102T163540.652505Z',author_expected_values_read=False,full884_frames=0,complete_games=0,seconds=time.monotonic()-start,limits=['Controlled direct922 casts after actualXP5 and choosing realDemo tier0/2; no1238 cooldown scheduler coverage.', 'maxTargets1; nearest-pair midpoint has zero actual targets, multi-target acceptance0. Separate naturalDemo batch not inherited.', 'Tier0/2, finite same-strength repeated primary refresh only; generic two-slot otherstrength/NaN/saturation/fullAura replacement remainPending.', '55knowncastpackets1668B orderedsubset of139observed5703B; all48AIpackets2297B exact; unmodeled84castpackets4035B remainPending.', 'No1775/3755executions/jobs; empty headers observed only. No proxy pending-drain claim.', '925 movement/BFS/nonfatal incoming9/6sAura expiry checked; expired live1020 physically retained because2123not scheduled; activekind12earlyguard also checked;fatal/otherstatus/corpsecontinuation not accepted.', 'All4NPC/currentHP/23derived/owned/racial/spellsets/RNG/ledger/rewardpickups/background retained; logicalNone not completed, fullNPCphysical replay separately verified.', 'Resource world checks are runner boolean/hash instrumentation, not independent raw2MBbefore/afterpairs; resource snapshot is notnewApp/Rcproducer.', 'External clock/component order; complete884/14-stage integration/native/client/UI/save/network/completegame remainPending.'])
 save(out/'review.json',result);print(json.dumps(dict(accepted=True,formal_counts=result['formal_counts'],counts=dict(counts),seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
