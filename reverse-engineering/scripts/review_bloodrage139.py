#!/usr/bin/env python3
"""Different-author read-only Bloodrage current139 reference.

Only independent reviewer helpers execute. Frozen original observations and
current source bodies are read; author expected JSON values never are parsed.
"""
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
import review_natural_demo139 as B
C=B.C;G=B.G;U=B.U;Pause=B.Pause;K=B.K;Chain=B.Chain;Spawn=B.Spawn;AI=B.AI;D=B.D;H=B.H;T=B.T;Demo=B.Demo;R=B.R;targets=B.targets;cooldown=B.cooldown
ROOT=B.ROOT;SOURCE=B.SOURCE;PROFILE=B.PROFILE;WASM=B.WASM
sha=B.sha;parse_module=B.parse_module;local_closure=B.local_closure;bits=B.bits;u=B.u
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def load(p):
 assert Path(p).name!='expected.json','Author expected values forbidden'
 return json.loads(Path(p).read_text())
AUTHOR=ROOT/'evidence/natural-bloodrage139-oracle-20261102T170631.797698Z/task-handoff.json'
AUTHOR_SHA='057815a57df6040a77d6ab35eb8b121f441fb4dcda2b3359af7c058a994b9d3b'
BATCHES=[dict(kind='natural_five_stage',evidence='evidence/natural-bloodrage139-oracle-20261102T170631.797698Z',comparison='7ef6a9c097a21195371d3dc803f974f613956c954747c4b7058be9660f8ab81f',steps=190,sources=118,production=102,edges=554,bodies=91,component=0),dict(kind='controlled_component',evidence='evidence/bloodrage-component139-oracle-20261102T170638.369369Z',comparison='9ec819c5fc2adb94ef1b7ac20d05b245491ba130b9b5f958744ff2a7f7eeccae',steps=107,sources=120,production=102,edges=574,bodies=91,component=434)]

def resource_initial():
 return dict(rage868_bits=0,reservoir872_bits=0,last_hit876_bits=0,cooldown_registry=[],display_tag784=0,display_key788=None,display_value792=None,other983_counts=[0]*5)

def interval(p):
 r=bytes.fromhex(p['g']['owned_records80_hex'][2]);d=DEFINITION
 assert u(r)==5883620 and d[84]==11
 value=C.mul(C.mul(C.mul(C.mul(u(d,52),0x3fb33333),u(r,16)),u(r,56)),p['g']['derived_bits']['1544'])
 return C.div(max(bits(8.),max(bits(.25),value,key=C.rational),key=C.rational),max(bits(.1),u(r,76),key=C.rational))

def release(p,s,L,now,ctx,counts):
 r=p['bloodrage'];g=p['g']
 if C.rational(r['rage868_bits'])<100:return [],[]
 due=next((deadline for name,deadline in r['cooldown_registry']if name=='bloodrage'),0xff7fffff)
 if C.rational(due)>C.rational(now):counts['release_blocked_deadline']+=1;return [],[]
 assert len(g['owned_records80_hex'])==3
 row=bytes.fromhex(g['owned_records80_hex'][2]);radius=C.mul(g['derived_bits']['1580'],C.mul(u(DEFINITION,60),C.mul(u(row,24),u(row,64))));assert 0<C.rational(radius)<=70
 square=C.mul(radius,radius);chosen=[j for j,v in enumerate(s['rows'])if D.read(v,0)==0 and C.le(C.distance(T.position(v,now),p['player']),square)]
 chosen=D.stable(chosen,lambda j:C.totalkey(C.distance(T.position(s['rows'][j],now),p['player'])))
 if not chosen:counts['full_rage_no_target_preserved']+=1;return [],[]
 ids=[D.read(s['rows'][j],112,8)for j in chosen];cd=interval(p);deadline=C.add(now,cd);r.update(rage868_bits=0,cooldown_registry=[['bloodrage',deadline]])
 owned=bytearray(row);U.put(owned,8,cd);g['owned_records80_hex'][2]=owned.hex()
 packets=B.cooldown(2687,cd)+[[306,(bytes(2)+struct.pack('<IHB',5246,256,len(ids))+b''.join(struct.pack('<Q',v)for v in ids)+bytes(3)).hex()]];heals=[]
 value=C.mul(C.mul(u(row,12),C.mul(u(DEFINITION,48),0x3fb33333)),u(row,52));life=C.mul(g['derived_bits']['1536'],u(row,72))if C.rational(u(DEFINITION,48))>0 else 0;base=C.mul(g['derived_bits']['1540'],C.add(value,life))
 for index in chosen:
  roll,s['words']=D.uniform24(s['words']);critical=int(C.rational(g['derived_bits']['1548'])>C.rational(roll));amount=C.mul(base,g['derived_bits']['1552'])if critical else base
  pk,hs=damage(p,s,L,index,amount,critical,2687,DEFINITION[85],now,ctx['world'],ctx['scalars'],ctx['speeds'],ctx['family_definitions'],counts,mode=3);packets.extend(pk);heals.extend(hs);counts['release_targets']+=1;counts['release_deaths']+=D.read(s['rows'][index],0)==1
 counts['full_rage_releases']+=1;counts['release_max_targets']=max(counts['release_max_targets'],len(ids));p['NPC']=copy.deepcopy(s['rows']);g['rng_words']=list(s['words']);return packets,heals

def damage_tail(p,s,L,now,ctx,counts,mode):
 if len(p['g']['owned_records80_hex'])<3:return [],[]
 if mode:counts['mode3_resource_recursion_skipped']+=1;return [],[]
 r=p['bloodrage'];spent=max(0,min(bits(2.),r['reservoir872_bits'],key=C.rational),key=C.rational)
 r.update(last_hit876_bits=now,reservoir872_bits=C.sub(r['reservoir872_bits'],spent),rage868_bits=min(bits(100.),C.add(r['rage868_bits'],spent),key=C.rational));counts['nonproc_resource_damage_tails']+=1;counts['positive_resource_transfers']+=C.rational(spent)>0
 return release(p,s,L,now,ctx,counts)

def damage(p,s,L,index,amount,critical,spell,school,now,world,scalars,speeds,definitions,counts,mode=0):
 row=s['rows'][index];normal=definitions[D.read(row,284)];target=D.read(row,112,8);assert D.read(row,0)==0
 mult=C.ONE
 if C.rational(now)<C.rational(D.read(row,148)):mult=C.add(mult,D.read(row,144))
 term=D.read(row,152)if C.rational(now)<C.rational(D.read(row,156))else D.read(row,160)if C.rational(now)<C.rational(D.read(row,164))else 0
 mult=C.add(C.add(C.add(mult,term),D.read(row,368)),0);schoolterm=0x3dcccccd if school&254==2 and C.rational(now)<C.rational(D.read(row,372))else 0
 damage=C.mul(C.mul(amount,C.add(mult,schoolterm)),C.ONE);damage=damage if C.rational(damage)>1 else C.ONE
 old=D.read(row,288);hp=C.sub(old,damage);account=min(max(C.rational(old),0),C.rational(damage))
 s['total']=C.bits64(C.f64(s['total'])+float(account));s['spelltotals'][spell]=C.bits64(C.f64(s['spelltotals'].get(spell,0))+float(account));D.put(row,288,hp)
 reason={0:'melee',845:'ability:cleave:r1',6343:'ability:thunder_clap:r1',1160:'ability:demo_shout:r1',2687:'ability:bloodrage:r1'}[spell];H.account(L,reason,C.rounded(account),now,[],damage=True)
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
 ctx=dict(world=world,scalars=scalars,speeds=speeds,family_definitions=definitions)
 pk,hs=damage_tail(p,s,L,now,ctx,counts,mode);packets.extend(pk);heals.extend(hs);p['NPC']=copy.deepcopy(s['rows']);g['rng_words']=list(s['words'])
 return packets,heals

def scheduler_reference(p,s,L,now,dt,world,scalars,speeds,normal,definitions,perception,classes,races,counts):
 g=p['g'];packets=[];events=[];heals=[];timer=C.sub(p['scalar']['1628'],dt)
 if C.rational(timer)<=0:
  chosen=targets(s['rows'],p['player'],now,0x40c00000)
  if chosen:
   index=chosen[0];target=D.read(s['rows'][index],112,8);roll,s['words']=D.uniform24(s['words']);critical=int(C.rational(g['derived_bits']['1548'])>C.rational(roll));base=C.mul(C.mul(C.mul(0x41dc0000,0x3fc00000),C.ONE),g['derived_bits']['1540']);amount=C.mul(base,g['derived_bits']['1552'])if critical else base
   shown=max(0,min(C.M,int(C.rational(amount))));packets.append([330,(struct.pack('<I',130 if critical else 2)+C.packguid(0)+C.packguid(target)+struct.pack('<I',shown)+bytes([1])+struct.pack('<IfI6I',0,float(shown),shown,0,0,1,0,0,0)+b'Melee\0melee\0').hex()])
   a,b=Demo.damage_demo(p,s,L,index,amount,critical,0,0,now,world,scalars,speeds,normal,counts);packets.extend(a);heals.extend(b)
   timer=C.mul(C.mul(0x3fcccccd,0x3f99999a),AI.sqrt32(g['derived_bits']['1544']));events.append(['basic_success',target,amount,critical,timer,1]);counts['basic']+=1;counts['basic_crit']+=critical
  else:timer=0x3e19999a;events.append(['basic_no_target',timer])
 p['scalar']['1628']=timer
 for index,hx in enumerate(g['owned_records80_hex']):
  row=bytearray.fromhex(hx);remaining=C.sub(u(row,8),dt);U.put(row,8,remaining);g['owned_records80_hex'][index]=row.hex()
  if C.rational(remaining)>0:continue
  if u(row)==5883620:
   remaining=max(0,remaining,key=C.rational);U.put(row,8,remaining);g['owned_records80_hex'][index]=row.hex();events.append(['owned_exec11_skip1238',index,'bloodrage',remaining]);counts['exec11_skipped_normal922']+=1;continue
  name={5882740:'cleave',5883180:'demo_shout'}[u(row)];definition=definitions[name][1];spell=u(definition,44);U.attempt(p,spell)
  if name=='demo_shout':
   ctx0=dict(world=world,scalars=scalars,speeds=speeds,family_definitions=normal,defs=definitions)
   ps,diag=Demo.cast(p,s,L,now,ctx0,counts);packets.extend(ps);counts['full922']-=1;counts['internal_Demo922_attempts']+=1
   counts['Demo_success']+=bool(diag['selected_ids']);counts['Demo_targets']+=len(diag['selected_ids']);counts['Demo_max_targets']=max(counts['Demo_max_targets'],len(diag['selected_ids']))
   if diag['selected_ids']:
    remaining=C.mul(C.mul(C.mul(C.mul(u(definition,52),0x3fb33333),u(row,16)),u(row,56)),g['derived_bits']['1544']);remaining=remaining if C.rational(remaining)>.25 else 0x3e800000;packets.extend(R.cooldown(spell,remaining))
   else:remaining=0x3e4ccccd
   U.put(row,8,remaining);g['owned_records80_hex'][index]=row.hex();events.append(['owned',index,name,int(bool(diag['selected_ids'])),list(map(int,diag['selected_ids'])),remaining]);continue
  if name=='cleave':
   radius=u(definition,56);chosen=targets(s['rows'],p['player'],now,radius);limit=u(definition,64);limit=max(1,(limit+u(row,20)+u(row,60)+g['derived_bits']['1592'])&C.M)if limit else 1;chosen=chosen[:limit];coefficient=C.ONE
  else:
   radius=C.mul(g['derived_bits']['1580'],C.mul(u(definition,60),C.mul(u(row,24),u(row,64))));assert C.rational(radius)<=70;square=C.mul(radius,radius);chosen=[i for i,r in enumerate(s['rows'])if D.read(r,0)==0 and C.le(C.distance(T.position(r,now),p['player']),square)];chosen=D.stable(chosen,lambda i:C.totalkey(C.distance(T.position(s['rows'][i],now),p['player'])));coefficient=0x3f000000
  ids=[D.read(s['rows'][i],112,8)for i in chosen];value=C.mul(C.mul(C.mul(C.mul(u(definition,48),0x3fb33333),u(row,12)),u(row,52)),coefficient);life=C.mul(g['derived_bits']['1536'],u(row,72))if C.rational(u(definition,48))>0 else 0;base=C.mul(g['derived_bits']['1540'],C.add(value,life))
  if ids:packets.append([306,C.launch(0,845,ids)if name=='cleave'else T.launch(ids)])
  for targetindex in chosen:
   roll,s['words']=D.uniform24(s['words']);critical=int(C.rational(g['derived_bits']['1548'])>C.rational(roll));amount=C.mul(base,g['derived_bits']['1552'])if critical else base
   a,b=Demo.damage_demo(p,s,L,targetindex,amount,critical,spell,definition[85],now,world,scalars,speeds,normal,counts);packets.extend(a);heals.extend(b)
   if name=='thunder_clap'and D.read(s['rows'][targetindex],0)!=1:
    effect=C.add(now,C.mul(u(definition,8),u(row,68)))
    for off,v in[(124,effect),(120,u(definition,4)),(376,0)]:D.put(s['rows'][targetindex],off,v)
    counts['slow_writes']+=3
  if ids:
   remaining=C.mul(C.mul(C.mul(C.mul(u(definition,52),0x3fb33333),u(row,16)),u(row,56)),g['derived_bits']['1544']);remaining=remaining if C.rational(remaining)>.25 else 0x3e800000;packets.extend(cooldown(spell,remaining));counts[name]+=1
  else:remaining=0x3e4ccccd
  U.put(row,8,remaining);g['owned_records80_hex'][index]=row.hex();events.append(['owned',index,name,int(bool(ids)),ids,remaining])
 remaining=C.sub(U.read(p['racial'],8),dt);U.put(p['racial'],8,remaining)
 if C.rational(remaining)<=0:
  U.attempt(p,20600);near=[r for r in s['rows']if D.read(r,0)==0 and C.rational(C.distance(T.position(r,now),p['player']))<=900]
  success=int(bool(near))
  if success:
   packets.append([306,(bytes(2)+struct.pack('<IHBQBH',20600,256,1,0,0,0)).hex()]);duration=C.mul(C.mul(C.mul(u(perception,68),0x3fb33333),U.read(p['racial'],28)),U.read(p['racial'],68));duration=duration if C.rational(duration)>C.rational(0x3dcccccd)else 0x3dcccccd;value=C.mul(U.read(p['racial'],76),u(perception,4));expiry=C.add(now,duration)
   keep=[i for i in range(p['count'])if not(U.read(p['live'][i],20)==20600 and U.read(p['live'][i],0,8)==0)];old=copy.deepcopy(p['live'])
   for j,i in enumerate(keep):p['live'][j]=old[i]
   p['count']=len(keep)
   if p['count']==len(p['live']):p['live'].extend([[None]*32 for _ in range(max(4,2*len(p['live']))-len(p['live']))])
   row=list(p['live'][p['count']]);row[:16]=struct.pack('<QII',0,8,value);row[16:20]=[None]*4;row[20:32]=struct.pack('<III',20600,expiry,0);p['live'][p['count']]=row;p['count']+=1;U.recalculate(p,classes,races);U.sync_aura(p)
   remaining=C.mul(C.mul(C.mul(C.mul(u(perception,52),0x3fb33333),U.read(p['racial'],16)),U.read(p['racial'],56)),g['derived_bits']['1544']);remaining=remaining if C.rational(remaining)>.25 else 0x3e800000;packets.extend(cooldown(20600,remaining));counts['racial']+=1
  else:remaining=0x3f000000
  U.put(p['racial'],8,remaining);events.append(['racial',success,remaining])
 g['rng_words']=list(s['words']);p['NPC']=copy.deepcopy(s['rows']);s['sets']=copy.deepcopy(p['sets'])
 return packets,events,heals

def select_choice_reference(player,combat,ledger,index,physical,count,ctx):
    p=copy.deepcopy(player);s=copy.deepcopy(combat);L=copy.deepcopy(ledger);g=p['g'];card=g['candidates'][index];assert card['variant']=='new'and card['ability_id']in('demo_shout','bloodrage')and g['pending']==1 and g['phase2587']==2
    g['owned_records80_hex'].append(G.selected_record(card['ability_id'],card['tier'],ctx['defs'],ctx['cooldown'],ctx['damage']));U.recalculate(p,ctx['classes'],ctx['races']);g.update(pending=0,flag2581=1,candidates=[])
    #4603 has not restoredphase1 at this point. All near/attracted XP is
    #removed forward and summed before a single4677, including early flight.
    rows=s['pickups'];n=s['pickup_count'];i=0;raw=0;consumed=[];packets=[]
    while i<n:
        row=rows[i]
        if K.read(row,8)!=0:i+=1;continue
        marker=K.read(row,0)
        if marker==0 and C.rational(K.distance(row,p['player']))>C.rational(g['derived_bits']['1560']):i+=1;continue
        assert marker in(0,1)and K.read(row,32)==0
        guid=K.read(row,16,8);amount=K.read(row,12);raw=(raw+amount)&0xffffffff;consumed.append(dict(index=i,guid=str(guid),raw_amount=amount,marker=marker))
        for j in range(i,n-1):rows[j]=copy.deepcopy(rows[j+1])
        n-=1;packets.append([170,struct.pack('<Q',guid).hex()])
    s['pickup_count']=n;award=0;growth=None
    if raw:
        rounded=K.rounded86979(C.mul(g['derived_bits']['1564'],C.rounded(Fraction(raw))));award=max(1,K.truncsat(rounded));p,L,growth=gain_reference(p,L,award,ctx['classes'],ctx['races'],ctx['kit']);g=p['g'];assert g['phase2587']==2,'No early resume before aggregate gain'
    if g['pending']:raise NotImplementedError('Actual4603 pending causes another choice; not admitted by thismatrix')
    g.update(phase2587=1,selection_kind2585=255,flags2573=0)
    owners=dict(units=dict(count=count,storage=physical),auxiliary=dict(count=0,storage=[]),claims=dict(count=0,storage=[]));resume=Pause.emit_reference(owners,g['now_bits'],s['sequence'],0,0,ctx['world'],resume=True);s['sequence']=resume['sequence'];packets.extend([[op,hx]for op,cap,hx in resume['packets']])
    old=copy.deepcopy(p['live']);retained=[i for i in range(p['count'])if U.read(old[i],20)!=1020]
    for j,i in enumerate(retained):p['live'][j]=copy.deepcopy(old[i])
    index=len(retained)
    if index==len(p['live']):p['live'].extend([[None]*32 for _ in range(max(4,2*index)-index)])
    row=p['live'][index];row[:8]=bytes(8);U.put(row,8,12);U.put(row,20,1020);U.put(row,24,C.add(g['now_bits'],C.ONE));U.put(row,28,0);p['count']=index+1;U.sync_aura(p);s['words']=list(g['rng_words'])
    return p,s,L,dict(consumed=consumed,raw_XP=raw,award=award,known_packets=packets,growth=growth,retained_live_indices=retained,new1020_index=index)


def stage983(p,s,L,now,dt,ctx,counts):
 if len(p['g']['owned_records80_hex'])<3:return [],[]
 assert [u(bytes.fromhex(v))for v in p['g']['owned_records80_hex']]==[5882740,5883180,5883620]
 r=p['bloodrage'];rate=C.div(bits(100.),interval(p));cap=max(bits(2.),C.mul(rate,bits(.5)),key=C.rational);r['reservoir872_bits']=min(cap,C.add(r['reservoir872_bits'],C.mul(dt,rate)),key=C.rational)
 elapsed=C.sub(now,r['last_hit876_bits'])
 if C.rational(elapsed)>3:
  old=r['rage868_bits'];r['rage868_bits']=max(0,C.add(old,C.mul(dt,bits(-15.))),key=C.rational);counts['idle_strict_gt3_branch']+=1;counts['positive_idle_decay']+=C.rational(r['rage868_bits'])<C.rational(old)
 elif C.rational(elapsed)==3:counts['idle_exact3_preserved']+=1
 pk,hs=release(p,s,L,now,ctx,counts);shown=max(0,min(C.M,int(C.rational(C.mul(r['rage868_bits'],bits(10.))))));r.update(display_tag784=1,display_key788=24,display_value792=shown);p['g']['player_fields']['24']=shown;p['NPC']=copy.deepcopy(s['rows']);p['g']['rng_words']=list(s['words']);counts['active983']+=1
 return pk,hs

B.scheduler_reference=scheduler_reference
B.Demo.damage_demo=damage

gain_reference=B.gain_reference

def review_batch(out,joint,entry,with_spawn):
    global BATCH,COMP
    BATCH=ROOT/entry['evidence'];COMP=entry['comparison'];start=time.monotonic();out.mkdir();print(json.dumps(dict(phase='identity_hashes',batch=entry['kind'])),flush=True);assert sha(BATCH/'comparison.json')==COMP
    hand=joint;comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');rt=load(BATCH/'runtime.json');authors=hand['author_files'];assert len(authors)==16
    for name,h in authors.items():assert sha(ROOT/name)==h
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==entry['sources'] and sum(n.startswith('reconstruction/')for n in sources)==entry['production']
    for name,h in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==entry['edges']
    for table in[comp['artifacts'],comp['frozen'],prep['frozen']]:
        for name,h in table.items():assert sha(BATCH/name)==h
    assert comp['differences']==0 and comp['cases']==comp['completed_cases']==1 and comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']and not comp['forbidden_model_reads']
    assert not load(BATCH/'expectation-read-audit.json')['forbidden']
    assert sha(SOURCE)==WASM and sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
    assert prep['resource_context_gate_sha256']==sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    assert prep['independent_world_receipt_sha256']==sha(ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json')=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    ctx=B.load_context();ctx.update(family_definitions={x:ctx['data'](x,72)for x in[5830904,5830976]},names={5830904:'Kobold Vermin',5830976:'Young Wolf'});raw,module,data=ctx['raw'],ctx['module'],ctx['data'];private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
    for a,b in zip(module['sections'],private['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
    assert private['exports']==module['exports']+[tuple(x)for x in m['added_exports']]and len(module['imports'])==882 and[(x['module'],x['name'],x['type_index'])for x in module['imports']]==[(x['module'],x['name'],x['type_index'])for x in m['original_imports']]
    bindings={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx,claim in m['functions'].items():
            a,z=module['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();stream.seek(lo);wat=stream.read(hi-lo);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());assert all(proof[k]==claim[k]for k in proof)and wat==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=proof;texts[int(idx)]=wat.decode();(out/f'{idx}.wat').write_bytes(wat)
    assert len(bindings)==entry['bodies'];guard='\n'.join(texts[1076].splitlines()[58:101]);assert 'i32.const 12'in guard and'f32.gt'in guard and'br 2'in guard;prior=load(B.N.STATIC/'binding.json')
    for idx,proof in prior['bodies'].items():
        if idx in bindings:assert proof==bindings[idx]
    for key,claim in m['static_reads'].items():
        address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==claim['sha256']
    assert data(1593648,44).hex()==m['levelup44_hex']and data(1593604,8)==b'level_up'and data(1593618,8)==b'Level Up'and data(1593626,19)==b'Spell_Holy_HolyBolt'
    global DEFINITION
    B.CANDIDATE_DEFS=ctx['defs'];B.CANDIDATE_TABLES=[struct.unpack('<5I',data(a,20))for a in[5405004,5405040,5405076,5405112,5405148]]
    DEFINITION=ctx['data'](5883620,88)
    assert DEFINITION.hex()==m['bloodrage88_hex']and DEFINITION[84]==11 and ctx['data'](u(DEFINITION,12),u(DEFINITION,16))==b'bloodrage'
    assert 'call 10285'in texts[983]and 'call 33222'in texts[983]and 'f32.store offset=872'in texts[983]and 'f32.const 0x1.8p+1 (;=3;)'in texts[983]
    assert 'call 50267'in texts[33222]and 'f32.const 0x1.99999ap-4'in texts[33222]and 'f32.const 0x1p+3'in texts[50267]
    assert 'i32.const 5246'in texts[10285]and 'i32.const 3\n          i32.store8 offset=770'in texts[10285]and 'call 22428'in texts[10285]and 'call 913'in texts[10285]
    assert 'f32.store offset=876'in texts[913]and 'call 10285'in texts[913]
    #1600 staged temporary is initialized before copy to T956=G868.
    assert texts[1600].index('i64.store offset=2912')<texts[1600].index('i64.load offset=2912')and 'i64.store offset=956 align=4'in texts[1600]and 'i64.store offset=964 align=4'in texts[1600]
    if entry['steps']==107:
        assert 'call 30022'in texts[2181]and 'call 27572'in texts[30022]and 'call 30628'in texts[27572]and 'call 25511'in texts[27572]and 'i64.const 5362837094'in texts[2181]
    print(json.dumps(dict(phase='bound_current_bodies',batch=entry['kind'],bodies=len(bindings))),flush=True)
    counts=Counter();reference=[];helper_SHA={str(Path(v.__file__).relative_to(ROOT)):sha(v.__file__)for v in list(sys.modules.values())if getattr(v,'__file__',None)and str(v.__file__).startswith(str(ROOT/'scripts'))and Path(v.__file__).name!=Path(__file__).name}
    for name,h in HELPERS.items():assert helper_SHA[name]==h
    assert texts[925].index('i32.const 221')<texts[925].index('call 1076')<texts[925].index('call 4593')and 'call 21553'in texts[2189]
    assert 'i32.const 128'in texts[2189]and 'i32.const 360'in texts[2189]and 'i32.const 364'in texts[2189]
    def cells(label,want,hx):
        seen=bytes.fromhex(hx);assert len(want)==len(seen)
        for i,(v,b)in enumerate(zip(want,seen,strict=True)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
            else:assert v==b,(label,i,v,b);counts[label+'_known']+=1
    def player(obs,p,label,initial_flag):
        want=U.project(p);capture=obs['capture'];assert capture['projection']==want['growth'],(label,'growth',[(k,v,capture['projection'].get(k))for k,v in want['growth'].items()if v!=capture['projection'].get(k)])
        game=bytes.fromhex(capture['raw_game2592_hex'])if 'raw_game2592_hex'in capture else None
        if game is not None:
            assert game[275]==0 and u(game,2092)==u(game,2104)==0;assert G.tree_fields(capture,game)==want['growth']['player_fields']and u(game,1440)==p['g']['current_hp_bits']
            for key,off in[('rage868_bits',868),('reservoir872_bits',872),('last_hit876_bits',876)]:assert u(game,off)==p['bloodrage'][key],(label,key,u(game,off),p['bloodrage'][key])
        for card,hx in zip(want['growth']['candidates'],capture.get('raw_candidates80_hex',[]),strict=True):
            row=bytes.fromhex(hx);assert len(row)==80 and u(row,76)==card['tier'];tag=u(row,60)
            if card['variant']=='new':
                d=ctx['defs'][card['ability_id']][1];assert tag==0x80000000 and u(row,64)==u(d,12)and u(row,68)==u(d,16)and data(u(row,64),u(row,68)).decode()==card['ability_id']
            else:assert card['variant']=='upgrade'and(tag==0x80000001 or tag<0x80000000)and u(row,72)==card['owned_index']
            counts['raw_candidate_metadata80']+=1
        for key in['racial80_hex','scalar','source_flags','spell_sets']:assert obs[key]==want[key],(label,key)
        for key,width in[('live',32),('aura',16)]:
            for field in['capacity','count']:assert obs[key][field]==want[key][field],(label,key,field)
            if key=='aura':assert obs[key]['flag2569']==(initial_flag if want[key]['flag2569']is None else want[key]['flag2569'])
            for row,hx in zip(want[key]['storage'],obs[key]['storage'],strict=True):cells(key,row,hx)
        if game is not None:
            for off in[176,600,648,1984,2032,2044,2056]:assert u(game,off)==0
            assert game[387]==0
        counts['player_views']+=1
    def combat(obs,p,s,physical=None):
        want=Chain.combat(p,s,physical);want['phase2587']=p['g']['phase2587']
        for key,v in want.items():
            if key=='records432_cells':
                for row,hx in zip(v,obs['records432_hex'][:len(v)],strict=True):cells('NPC',row,hx)
            elif key=='pickups56_cells':
                for row,hx in zip(v,obs['pickups56_hex'],strict=True):cells('pickup',row,hx)
            else:assert obs[key]==v,('combat',key,v,obs.get(key))
    def accounting(obs,L,playerobs,label):
        for key,v in L.items():assert obs[key]==v,(label,key,v,obs.get(key))
        game=bytes.fromhex(playerobs['capture']['raw_game2592_hex'])if 'raw_game2592_hex'in playerobs['capture']else None;aggregate=bytes.fromhex(obs['accounting_struct68_hex']);assert struct.unpack_from('<Q',aggregate,16)[0]==int(L['accepted_count1016'])
        if game is not None:assert struct.unpack_from('<Q',game,960)[0]==int(L['event_counter960'])and game[1000:1068]==aggregate
        decoded={}
        for row in obs['stats_keys']:
            raw96=bytes.fromhex(row['raw96']);assert row['raw96']==obs['stats']['storage'][row['index']]and len(raw96)==96 and struct.unpack_from('<Q',raw96,8)[0]==int(row['total64']);decoded[row['reason']]=C.bits64(C.f64(decoded.get(row['reason'],0))+C.f64(int(row['total64'])))
        assert{k:str(v)for k,v in decoded.items()}==L['reason_totals64']
        names={}
        for reason,address in[('regen',1592624),('leech',1591852),('level_up',1593648)]:
            desc=data(address,44);names[reason]=[data(u(desc,k),u(desc,k+4)).decode()for k in[24,32]]
        wanted=[dict(name=names[k][0],icon=names[k][1],total64=v,owns=0,nested_count=0)for k,v in L['reason_totals64'].items()if k in names]
        assert [{k:r[k]for k in['name','icon','total64','owns','nested_count']}for r in obs['breakdown']]==wanted
        for row in obs['breakdown']:
            r=bytes.fromhex(row['raw48']);assert len(r)==48 and struct.unpack_from('<Q',r,8)[0]==int(row['total64'])and u(r,4)==len(row['icon'].encode())and u(r,36)==len(row['name'].encode())and u(r,24)==0 and r[40]==0 and u(r,28)==0xffffffff
        for key in['source_registry','saved_history']:assert[obs[key][k]for k in['capacity','pointer','count']]==[0,8,0]
        counts['semantic_ledger_snapshots']+=1
    def ai_check(obs,ai,storage,count):
        want=Chain.ai_projection(ai,storage,count)
        for key in['path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories']:assert obs[key]==want[key],('AI',key,want[key],obs[key])
        for key in['header','active']:assert obs['history'][key]==want['history'][key]
        for row,hx in zip(want['history']['storage'],obs['history']['storage'],strict=True):cells('history',row,hx)
    def stage_view(obs,p,s,L,ai,storage,count,flag):
        resource(obs['bloodrage'],p);player(obs['player'],p,'choice',flag);combat(obs['combat'],p,s);accounting(obs['healing'],L,obs['player'],'choice');ai_check(obs['ai'],ai,storage,count)
        assert obs['gold1456']==s.get('gold',0)and obs['earned1100']==s.get('earned',0)
    def resource(obs,p):
        want=p['bloodrage']
        for key,v in want.items():
            if v is not None:assert obs[key]==v,('resource',key,v,obs[key]);counts['resource_fields']+=1
        registry=obs['registry'];assert registry['stride']==12 and registry['count']==len(want['cooldown_registry'])and registry['capacity']==(4 if registry['count']else 0)
        for (name,deadline),hx in zip(want['cooldown_registry'],registry['storage'][:registry['count']],strict=True):
            row=bytes.fromhex(hx);assert len(row)==12 and struct.unpack('<III',row)==(u(DEFINITION,12),u(DEFINITION,16),deadline);counts['registry_entry12_bytes']+=12
        counts['registry_unknown_tail_observed_only']+=12*(registry['capacity']-registry['count'])
    cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==1 and [(c['app_seed_u64'],len(c['timestamps64']),c['selection_policy'])for c in cases]==[('111',entry['steps'],'first_two_default0_stop_third')]
    print(json.dumps(dict(phase='independent_numerical_replay',batch=entry['kind'],steps=entry['steps'])),flush=True)
    for case,A in zip(cases,actual,strict=True):
        assert case['id']==A['id']and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['stack_after']==1048576 and case['clock_initial']==dict(tag=1,previous64='0')
        opening,p,s,ai,L,storage,count=B.initial_reference(case,ctx);p['bloodrage']=resource_initial();op=opening['projection'];initial_flag=A['initial']['aura']['flag2569'];player(A['initial'],p,'initial',initial_flag);accounting(A['initial_healing'],L,A['initial'],'initial');ai_check(A['initial_ai'],ai,storage,count)
        cells('openingGame',opening['known_Game2592'],A['opening']['raw_game2592_hex']);assert A['opening']['packets']==op['packets']and A['initial']['capture']==A['opening']
        for key in['units','pickups','special','windows','boundaries']:
            for row,hx in zip(op[key]['storage'],A['opening']['background'][key]['storage'],strict=True):cells('opening_'+key,row,hx)
        previous=A['initial'];prior_stamp=Fraction(0);steps=[];choice=None;choices=[];chosen_count=0;scheduler=dict(budget2416_bits=bits(3.),previous_player_xyz=[0,0,0],velocity_xy=[0,0],timer_fields={'2424':bits(60.),'2440':bits(240.),'2444':bits(40.),'2448':bits(60.),'2452':20,'2456':0})
        for j,(stampstr,obs)in enumerate(zip(case['timestamps64'],A['stages'],strict=True)):
            stamp=Fraction(C.f64(int(stampstr)));dt=C.rounded(min(Fraction(.1),max(Fraction(0),stamp-prior_stamp)));prior_stamp=stamp;now=C.add(p['g']['now_bits'],dt)
            assert stamp==Fraction(j+1,8)and obs['clock']==dict(tag=1,previous64=stampstr,dt_bits=dt,now_bits=now)
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(inherited,2352,now);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['Game_clock_input_inheritance_bytes']+=2592
            oldstorage=[bytearray.fromhex(hx)for hx in obs['before_combat']['records432_hex']];oldcount=count
            pk,events,heals,expired=B.player_stage(p,s,L,now,dt,ctx,counts);player(obs['after_player'],p,('player',case['id'],j),initial_flag)
            logical=copy.deepcopy(s['rows'])+copy.deepcopy(storage[count:]);physical=[row[:]for row in oldstorage]
            for i,row in enumerate(logical):
                for k,v in enumerate(row):
                    if v is not None:physical[i][k]=v
            assert [r.hex()for r in physical]==obs['after_player']['capture']['background']['units']['storage'];counts['player_NPC_physical_replay_bytes']+=432*len(physical)
            po,ho=stage983(p,s,L,now,dt,ctx,counts);player(obs['after_owned_effects'],p,('983',case['id'],j),initial_flag)
            logical=copy.deepcopy(s['rows'])+copy.deepcopy(storage[count:])
            for i,row in enumerate(logical):
                for k,v in enumerate(row):
                    if v is not None:physical[i][k]=v
            assert [r.hex()for r in physical]==obs['after_owned_effects']['capture']['background']['units']['storage'];counts['983_NPC_physical_replay_bytes']+=432*len(physical)
            ai,storage,count,pa,br,removed=B.enemy_with_live(p,s,ai,storage,count,now,dt,ctx,counts);player(obs['after_ai'],p,('AI',case['id'],j),initial_flag)
            for i,row in enumerate(br):
                for k,v in enumerate(row):
                    if v is not None:physical[i][k]=v
            physical_count=oldcount
            for guid in removed:
                retained=[row[:]for row in physical[:physical_count]if str(int.from_bytes(row[112:120],'little'))!=guid]
                for i,row in enumerate(retained):physical[i]=row
                physical_count=len(retained)
            assert physical_count==count and[r.hex()for r in physical]==obs['after_ai']['capture']['background']['units']['storage'];counts['AI_NPC_physical_replay_bytes']+=432*len(physical)
            beforecollection=copy.deepcopy(s['pickups']);p,s,L,collected=B.collect_reference(p,s,L,now,ctx);player(obs['after_collection'],p,('collect',case['id'],j),initial_flag);packets=pk+po+pa+collected['known_packets']
            assert obs['after_collection']['capture']['background']['units']==obs['after_ai']['capture']['background']['units']
            counts['attractions']+=len(collected['attractions']);counts['collections']+=len(collected['events']);counts['XP_awarded']+=sum(e['award']for e in collected['events']if e['kind']==0)
            counts['Demo_success_step91']+=sum(e[0]=='owned'and e[2]=='demo_shout'and e[3]and len(e[4])==5 and j==91 for e in events)
            for grew in collected['growth']:
                counts['level_transitions']+=len(grew['levels']);counts['level_up_positive_events']+=sum(bool(e['heal_events'])for e in grew['levels'])
            if with_spawn:
                assert obs['before_spawn']==obs['after_collection']['capture']['background']['units'];ctx['zone']=ctx['data'](5871348,152);ctx['definitions']=[ctx['data'](5830904+72*i,72)for i in range(12)]
                spawn_counts=Counter();scheduler,p,s,storage,count,spawn_packets,born,spawn_diag=Spawn.spawn(scheduler,p,s,ai,storage,count,now,dt,ctx,spawn_counts);packets.extend(spawn_packets);player(obs['after_spawn'],p,('spawn',case['id'],j),initial_flag)
                assert obs['scheduler']=={k:scheduler[k]for k in obs['scheduler']};counts['spawn_steps']+=1;counts['spawn_NPCs']+=len(born);counts['Wolf_born']+=sum(D.read(r,284)==5830976 for r in s['rows'][-len(born):])if born else 0;counts['positive_spawn_cost_steps']+=scheduler['kill_cost2420_bits']!=0
                for key,value in spawn_counts.items():counts['spawn_'+('exp_evaluations'if key=='positive_decay'else key)]+=value
                for row,hx in zip(storage,obs['after_spawn']['capture']['background']['units']['storage'],strict=True):cells('spawnNPC',row,hx)
                oldbg=obs['before_spawn'];newbg=obs['after_spawn']['capture']['background']['units'];assert oldbg['storage'][:oldbg['count']]==newbg['storage'][:oldbg['count']]
            if p['g']['phase2587']==2:
                assert obs['before_choice']is not None;stage_view(obs['before_choice'],p,s,L,ai,storage,count,initial_flag);counts['phase2_choices']+=1;choice=dict(step=j,now_bits=now,cards=copy.deepcopy(p['g']['candidates']),active_live_before=copy.deepcopy(p['live'][:p['count']]),growth=collected['growth'])
                assert chosen_count<2 and p['g']['candidates'][0]['variant']=='new'and p['g']['candidates'][0]['ability_id']==('demo_shout'if chosen_count==0 else'bloodrage')and obs['selection_index']==0
                p,s,L,selection=select_choice_reference(p,s,L,0,storage,count,ctx);chosen_count+=1;packets.extend(selection['known_packets']);choice['selection']=selection;counts['default0_selections']+=1;counts['selection_pickups']+=len(selection['consumed']);counts['selection_raw_XP']+=selection['raw_XP'];counts['selection_award']+=selection['award']
                choices.append(choice)
            else:assert obs['before_choice']is None and obs['selection_index']is None
            resource(obs['bloodrage'],p);player(obs['after'],p,('final',case['id'],j),initial_flag);combat(obs['combat'],p,s);accounting(obs['healing'],L,obs['after'],('ledger',case['id'],j));ai_check(obs['ai'],ai,storage,count)
            for row,hx in zip(storage,obs['after']['capture']['background']['units']['storage'],strict=True):cells('physicalNPC',row,hx)
            assert obs['gold1456']==s.get('gold',0)and obs['earned1100']==s.get('earned',0)
            for queue in['xp_queue','coin_queue']:assert[obs[queue][k]for k in['capacity','pointer','count']]==[0,4,0]and not obs[queue]['storage']
            assert not any(obs['source_headers'].values())and all(obs['pending_after'][q]['count']==0 for q in['hits','areas','deadlines'])
            for key in['special','windows','boundaries','auxiliary','claims']:assert obs['after']['capture']['background'][key]==A['opening']['background'][key]
            assert obs['after']['capture']['background']['pickups']['storage'][:2]==A['opening']['background']['pickups']['storage'][:2]
            cursor=0
            for packet in packets:
                cursor=next(k for k in range(cursor,len(obs['new_packets']))if obs['new_packets'][k]==packet)+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2
            counts['observed_packets']+=len(obs['new_packets']);counts['observed_packet_bytes']+=sum(len(v[1])//2 for v in obs['new_packets']);counts['natural_steps']+=1;counts['AI_attacks']+=len(pa)and sum(v[0]==330 for v in pa);counts['formal_removals']+=len(removed)
            if choice is not None and j>choice['step']:
                counts['post_select_basic']+=sum(e[0]=='basic_success'for e in events);counts['post_select_Demo']+=sum(e[0]=='owned'and e[2]=='demo_shout'and e[3]for e in events)
            steps.append(dict(now_bits=now,events=events,removed=removed,known_packets=packets,level=p['g']['level'],xp=p['g']['xp'],phase=p['g']['phase2587'],healing=copy.deepcopy(L),collected=collected['events'],growth=collected['growth']));previous=obs['after']
        assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16];reference.append(dict(seed=case['app_seed_u64'],steps=steps,choice=choice,choices=choices))
        # Full983 and913 components inherit the genuine107-step prefix. Only
        # clock/player and input damage amount are externally controlled.
        operations=case.get('operations',[]);components=A.get('components',[])
        assert len(operations)==len(components)==entry['component']
        for index,(op,obs)in enumerate(zip(operations,components,strict=True)):
            now,dt=op['now_bits'],op['dt_bits'];p['g']['now_bits']=now;p['scalar']['2352']=now;p['player']=op['player_xyz'][:]
            before=[bytearray.fromhex(v)for v in obs['before_NPC_storage']];assert len(before)==len(storage)
            if op['kind']=='tick983':pk,hs=stage983(p,s,L,now,dt,ctx,counts);counts['component_full983']+=1
            else:
                assert op['kind']=='hit913'and op['amount_bits']==C.ONE and op['spell_id']==op['school']==op['critical']==op['source_mode770']==0 and op['suppress_spell_damage_packet']==1
                target=next(i for i,row in enumerate(s['rows'])if str(D.read(row,112,8))==op['target_guid'])
                pk,hs=damage(p,s,L,target,op['amount_bits'],0,0,0,now,ctx['world'],ctx['scalars'],ctx['speeds'],ctx['family_definitions'],counts);counts['component_full913_controlled_amount1']+=1
            storage=copy.deepcopy(s['rows'])+copy.deepcopy(storage[count:]);scheduler.update(player_level1432=p['g']['level'],count=count,capacity=len(storage),rng_words=list(s['words']),counter2408=s['counter'],now_bits=now,kill_cost2420_bits=s['cost'])
            assert obs['final']['scheduler']==scheduler,('componentScheduler',index)
            stage_view(obs['final'],p,s,L,ai,storage,count,initial_flag)
            for i,row in enumerate(storage):
                cells('componentNPC',row,obs['physical_NPC_storage'][i])
                for k,v in enumerate(row):
                    if v is not None:before[i][k]=v
                    else:counts['component_None_physical_copy']+=1
            assert [v.hex()for v in before]==obs['physical_NPC_storage'];counts['component_NPC_physical_replay_bytes']+=432*len(before)
            cursor=0
            for packet in pk:
                cursor=next(k for k in range(cursor,len(obs['new_packets']))if obs['new_packets'][k]==packet)+1;counts['component_known_packets']+=1;counts['component_known_packet_bytes']+=len(packet[1])//2
            counts['component_observed_packets']+=len(obs['new_packets']);counts['component_observed_packet_bytes']+=sum(len(v[1])//2 for v in obs['new_packets']);counts['component_targets']+=1
            reference[0].setdefault('components',[]).append(dict(index=index,operation=op,resource=copy.deepcopy(p['bloodrage']),packets=pk,healing=copy.deepcopy(L)))
    assert counts['natural_steps']==entry['steps']and counts['default0_selections']==2 and counts['phase2_choices']==2 and counts['selection_pickups']==1 and counts['selection_raw_XP']==counts['selection_award']==2 and counts['Demo_max_targets']==5 and counts['Demo_success_step91']==1 and counts['Wolf_born']==0
    assert reference[0]['choices'][0]['step']==85 and reference[0]['choices'][1]['step']==106 and reference[0]['choices'][1]['cards']==[dict(variant='new',tier=0,ability_id=name,owned_index=0,kinds=[],gold=0)for name in['bloodrage','execute','shield_slam']]
    expected_calls=Counter({'2945':1,'1600':1,'1108':1,'1093':2})
    for role in('2123','983','925','2890','952'):expected_calls[role]+=entry['steps']
    expected_calls['983']+=counts['component_full983'];expected_calls['913']+=counts['component_full913_controlled_amount1']
    assert rt==comp['runtime']and rt['fresh_instances']==1 and all(value==expected_calls[role]for role,value in rt['full_calls'].items())and rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None
    returned=Counter(str(v['role'])for v in rt['target_and_setup_returns']if v['returned']);assert returned==+expected_calls and len(rt['target_and_setup_returns'])==sum(expected_calls.values())and all(v['before']==v['after']==1048576 and v['returned']for v in rt['target_and_setup_returns'])
    assert len(rt['world_source_checks'])==entry['steps']+2 and all(v['ranges']==2318 and v['unchanged']for v in rt['world_source_checks'])and rt['stack_checks']==sum(expected_calls.values())+5 and rt['allocator_calls']==5 and rt['output_bytes']==(BATCH/'actual.jsonl').stat().st_size
    assert rt['explicit_XP_gain_calls']==0 and rt['actual2123then983then925then2890then952']and not rt['XP_HP_card_RNG_CD_status_timers_NPC_positions_written_by_driver']and not rt['basic_or_racial_disabled']and not rt['old_Game_used_as_target']and rt['peak_memory_bytes']==177078272<=rt['memory_cap_bytes']==268435456 and rt['native_executions']==rt['full_mainloop_frames']==rt['complete_games']==0
    term=load(BATCH/'owned-terminal.json');assert term==comp['process']and term in hand['processes']and term['exit_code']==0 and term['pid_missing']and term['pgid_missing']
    for name,h in authors.items():assert sha(ROOT/name)==h
    for name,h in sources.items():assert sha(ROOT/name)==h
    assert not AUDIT and not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    result=dict(accepted=True,batch=str(BATCH.relative_to(ROOT)),source_sha256=WASM,comparison_sha256=COMP,counts=dict(counts),source_files=sources,source_edges=edges,body_bindings=bindings,choices=[r['choices']for r in reference],original_process=term,reviewer_author_original_executions=0)
    save(out/'review.json',result);save(out/'independent-reference.json',reference);print(json.dumps(dict(batch=result['batch'],accepted=True,counts=dict(counts),seconds=time.monotonic()-start)),flush=True);return result


def main():
 global HELPERS
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
 assert sha(AUTHOR)==AUTHOR_SHA;hand=load(AUTHOR)
 prior=load(ROOT/'evidence/natural-demo139-independent-owned-20261102T165141.958858Z/review/review.json')
 assert sha(ROOT/'scripts/review_natural_demo139.py')==prior['reviewer_sha256']=='91642b4d8354ad372ea46cf9e1c8ca04ca90e316c133c3584ae2a7634b30d4c9'
 HELPERS={**prior['helper_sha256'],'scripts/review_natural_demo139.py':prior['reviewer_sha256']}
 helpers={str(Path(v.__file__).relative_to(ROOT)):sha(v.__file__)for v in list(sys.modules.values())if getattr(v,'__file__',None)and str(v.__file__).startswith(str(ROOT/'scripts'))and Path(v.__file__).name!=Path(__file__).name}
 for name,h in HELPERS.items():assert helpers[name]==h
 results=[review_batch(out/('batch'+str(i)),hand,entry,True)for i,entry in enumerate(BATCHES)]
 counts=Counter();sources={};edges=set();bodies={}
 for result in results:
  counts.update(result['counts'])
  for name,h in result['source_files'].items():assert name not in sources or sources[name]==h;sources[name]=h
  edges.update(tuple(e)for e in result['source_edges'])
  for idx,proof in result['body_bindings'].items():assert idx not in bodies or bodies[idx]==proof;bodies[idx]=proof
 for key in('Demo_max_targets','max_targets','release_max_targets'):counts[key]=max(r['counts'].get(key,0)for r in results)
 assert counts['natural_steps']==297 and counts['default0_selections']==4 and counts['component_targets']==434 and counts['component_full983']==373 and counts['component_full913_controlled_amount1']==61
 assert counts['release_targets']==counts['release_deaths']==counts['mode3_resource_recursion_skipped']==5 and counts['full_rage_releases']==1 and counts['release_max_targets']==5 and counts['positive_idle_decay']>0 and counts['idle_exact3_preserved']==1 and counts['full_rage_no_target_preserved']>0
 for table in(hand['author_files'],sources,helpers):
  for name,h in table.items():assert sha(ROOT/name)==h
 assert not AUDIT and not any(name.startswith(('core_spec','resource_spec'))for name in sys.modules)
 result=dict(accepted=True,scope='current139 natural five-component progression and actual Bloodrage owned/damage source components',version='0.139.0',build='f79c5e2b4',source_sha256=WASM,reviewer_sha256=sha(Path(__file__)),author_handoff=str(AUTHOR.relative_to(ROOT)),author_handoff_sha256=AUTHOR_SHA,author_files=hand['author_files'],source_files=sources,source_import_edges=sorted(edges),source_counts=dict(files=len(sources),production=sum(n.startswith('reconstruction/')for n in sources),edges=len(edges),bodies=len(bodies)),current_body_bindings=bodies,helper_sha256=helpers,batches=[dict(kind=e['kind'],evidence=e['evidence'],comparison_sha256=e['comparison'],process=r['original_process'],choices=r['choices'],counts=r['counts'])for e,r in zip(BATCHES,results,strict=True)],formal_counts=dict(fresh_original_instances=2,natural_unique_progression_steps=190,natural_five_component_entries=950,controlled_component_entries=434,controlled_full983=373,controlled_full913=61,component_shared107prefix_setup_entries=535,opening_setup=6,UI1093_setup=4,total_direct_entries=1929,reviewer_author_program_executions=0,reviewer_original_executions=0),counts=dict(counts),author_expected_values_read=False,complete_games=0,full884_frames=0,native_windows_app_executions=0,seconds=time.monotonic()-start,limits=['The second batch repeats the first107-step input prefix as explicit setup;297 observed prefix steps are not297 unique naturalprogression steps.', 'Full2123→983→925→2890→952 are externally driven component schedules, with current884 relative order. Otherlate14 stages and884/App not executed.', 'Two actualdefault0 choices are Demo tier2 thenBloodrage tier0, atindices85/106. No XP/HP/RNG/CD/resource injection in natural progression. At19s no2372/20sGuardian integration.', '61 component normal913 amount1 calls andclock/playercontrols are explicit component inputs, not automatic/naturalattacks. They produce61 genuine resource transfers;controlledfullrage 5-targetrelease is notnaturalburst acceptance.', 'Numeric/stat/knownNPC/pickup/live/Aura/history/candidates/ledger andorderedknownpackets checked with independentreviewer references. Allunknownbytes remainNone;physical inheritedNPC bytes checked separately. Allocator-tail/heap pointers not predicted.', 'NamedVec12 entry bytes andcapacity checked;uninitialized registrytail is observationonly. Cacheinactive payload notfilled fromactual.', 'Sharedsemantic2077 counters andf64 reason attribution checked;all2077heap/catalogphysicalownership,completeUI/network packets andallskills stillincomplete.', 'Originalcontrolledfunctions borrowv2 resource-only memory context;model/referenceworldusesindependentrawpipelineoutput. NoWindowsapplication/main884/fullgame acceptance.'])
 save(out/'review.json',result);print(json.dumps(dict(accepted=True,counts=dict(counts),source_counts=result['source_counts'],formal_counts=result['formal_counts'],seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
