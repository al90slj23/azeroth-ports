#!/usr/bin/env python3
"""Independent read-only current139 naturalDemo + two-owned secondcards.
No author programs or original functions execute; author expected values unread.
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
import review_natural_growth139_v2 as N
import review_demo_shout139 as Demo
targets=Demo.R.targets;cooldown=Demo.R.cooldown
C=N.C;G=N.G;U=N.U;Pause=N.Pause;K=N.K;Chain=N.Chain;Spawn=N.Spawn;AI=N.AI;D=N.D;R=Demo.R;H=Demo.H;T=Demo.T
ROOT=N.ROOT;SOURCE=N.SOURCE;PROFILE=N.PROFILE;WASM=N.WASM
sha=N.sha;parse_module=N.parse_module;local_closure=N.local_closure;fp=N.fp;bits=N.bits
def load(p):
 assert Path(p).name!='expected.json','Author expected values forbidden'
 return json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]
load_context=N.load_context;initial_reference=N.initial_reference;level_heal_reference=N.level_heal_reference

def gain_reference(player,ledger,amount,classes,races,kit):
    p=copy.deepcopy(player);L=copy.deepcopy(ledger);g=p['g'];g['xp']=(g['xp']+amount)&0xffffffff;levels=[]
    while g['level']<=119 and g['xp']>=G.threshold(g['level']):
        p,L,event=level_heal_reference(p,L,classes,races);g=p['g'];levels.append(event)
    g['player_fields'].update({'716':g['xp'],'717':G.threshold(g['level'])})
    if g['pending']and g['phase2587']==1:
        cards,words,draws=candidates_reference(g,kit);g.update(candidates=cards,rng_words=words,phase2587=2,selection_kind2585=0,generation_counter2400=g['generation_counter2400']+1)
    else:draws=0
    return p,L,dict(levels=levels,card_draws=draws,phase2_stop_pending=g['phase2587']==2)

def collect_reference(player,combat,ledger,now,ctx):
    """Current2890 default XP/coin path, preserving2Rune/capacity/stale tail.

    Exact sqrt/attraction helpers were independently reviewed below level5;
    this variant supplies new level-heal/card callback instead of its old guard.
    """
    p=copy.deepcopy(player);s=copy.deepcopy(combat);L=copy.deepcopy(ledger);g=p['g'];rows=s['pickups'];n=s['pickup_count'];packets=[];attractions=[];eligible=[]
    for i,old in enumerate(rows[:n]):
        if K.read(old,8)!=0 or K.read(old,0)!=0:continue
        distance=K.distance(old,p['player']);aged=C.rational(C.sub(now,K.read(old,52)))>6
        if not aged and C.rational(distance)>C.rational(g['derived_bits']['1560']):continue
        delay=C.div(distance,0x42000000 if aged else 0x41c00000);delay=delay if C.rational(delay)>C.rational(0x3df5c28f)else 0x3df5c28f
        row=copy.deepcopy(old);K.put(row,0,1);K.put(row,4,C.add(now,delay));rows[i]=row;s['sequence']=(s['sequence']+1)&0xffffffff;xyz=[K.read(old,k)for k in[40,44,48]]
        packet=C.packguid(K.read(old,16,8))+struct.pack('<4I',*xyz,s['sequence'])+bytes(1)+struct.pack('<3I3I',256,max(1,K.truncsat(C.mul(delay,0x447a0000))),1,*p['player']);packets.append([221,packet.hex()]);attractions.append(dict(index=i,delay_bits=delay,aged=aged))
    for i,row in enumerate(rows[:n]):
        kind=K.read(row,8);marker=K.read(row,0)
        if kind==0:take=marker!=0 and C.rational(K.read(row,4))<=C.rational(now)
        elif kind==1:take=C.rational(K.distance(row,p['player']))<=C.rational(g['derived_bits']['1560'])or marker==1 and C.rational(K.read(row,4))<=C.rational(now)
        else:assert C.rational(K.distance(row,p['player']))>3,'Near Rune/resource unknown';take=False
        if take:eligible.append(i)
    before_shift=copy.deepcopy(rows);events=[];growth=[]
    for i in reversed(eligible):
        row=copy.deepcopy(rows[i]);kind=K.read(row,8);amount=K.read(row,12);guid=K.read(row,16,8);assert K.read(row,0)!=2 and K.read(row,32)==0
        for j in range(i,n-1):rows[j]=copy.deepcopy(rows[j+1])
        n-=1;packets.append([170,struct.pack('<Q',guid).hex()]);multiplier=g['derived_bits']['1564'if kind==0 else'1588'];value=K.rounded86979(C.mul(multiplier,C.rounded(K.Fraction(amount))))
        if kind==0:
            award=max(1,K.truncsat(value));p,L,grew=gain_reference(p,L,award,ctx['classes'],ctx['races'],ctx['kit']);g=p['g'];growth.append(grew)
            if grew['card_draws']:
                owners=dict(units=dict(count=len(s['rows']),storage=s['rows']),auxiliary=dict(count=0,storage=[]),claims=dict(count=0,storage=[]));stop=Pause.emit_reference(owners,now,s['sequence'],0,0,ctx['world'],resume=False);s['sequence']=stop['sequence'];packets.extend([[a,hx]for a,cap,hx in stop['packets']])
        else:
            award=K.truncsat(value);s['gold']=(s.get('gold',0)+award)&0xffffffff;s['earned']=(s.get('earned',0)+award)&0xffffffff;g['player_fields']['1176']=(s['gold']*10000)&0xffffffff
        events.append(dict(index=i,kind=kind,guid=str(guid),amount=amount,award=award))
    s.update(pickups=rows,pickup_count=n,words=list(g['rng_words']));return p,s,L,dict(known_packets=packets,attractions=attractions,events=events,precompaction=before_shift,growth=growth)

def select_choice_reference(player,combat,ledger,index,physical,count,ctx):
    p=copy.deepcopy(player);s=copy.deepcopy(combat);L=copy.deepcopy(ledger);g=p['g'];card=g['candidates'][index];assert card['variant']=='new'and card['ability_id']=='demo_shout'and g['pending']==1 and g['phase2587']==2
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

def enemy_with_live(p,s,ai,storage,count,now,dt,ctx,counts):
 storage=copy.deepcopy(s['rows'])+copy.deepcopy(storage[count:]);alive=[];remove=[]
 for index,row in enumerate(storage[:count]):
  marker=D.read(row,0);assert marker in(0,1)
  if marker==0:alive.append(index)
  else:
   assert all(D.read(row,k)==0xffffffff for k in(40,64,244))and D.read(row,232)==0 and D.read(row,284)in ctx['names'] and row[424]==0
   if C.rational(C.sub(now,D.read(row,4)))>C.rational(0x3f99999a):remove.append(str(D.read(row,112,8)))
 ai=copy.deepcopy(ai);ai.update(rows=[copy.deepcopy(storage[k])for k in alive],now=C.sub(now,dt),player=p['player'],hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],derived=p['g']['derived_bits'],fields=copy.deepcopy(p['g']['player_fields']),sequence=s['sequence'],packets=[])
 if ai['path']is not None and AI.probe(ctx['nav'],p['player'][:2])[1]!=ai['path']['start_index']:
  assert C.rational(C.sub(now,ai['path_clock']))>=C.rational(0x3e4ccccd),'Changed-cell young map domain pending'
  ai['path'],ai['path_values']=AI.breadth_first(ctx['nav'],p['player'],ctx['neighbors']);ai['path_clock']=now;counts['path_refreshes']+=1
 ai,answer=Demo.tick_demo(ai,dt,ctx['world'],ctx['nav'],ctx['neighbors'],ctx['names'],{'Melee':'Melee'},counts,p['live'][:p['count']])
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

def player_stage(p,s,L,now,dt,ctx,counts):
 p['g']['now_bits']=now;p['scalar']['2352']=now
 keep=[i for i in range(p['count'])if C.rational(now)<C.rational(U.read(p['live'][i],24))];expired=[U.read(p['live'][i],20)for i in range(p['count'])if i not in keep]
 if expired:
  old=copy.deepcopy(p['live'])
  for j,i in enumerate(keep):p['live'][j]=old[i]
  p['count']=len(keep);U.recalculate(p,ctx['classes'],ctx['races']);U.sync_aura(p)
 _,_,heals=H.regen(p,L,now,dt);counts['positive_Regen']+=len(heals)
 packets,events,castheals=scheduler_reference(p,s,L,now,dt,ctx['world'],ctx['scalars'],ctx['speeds'],ctx['family_definitions'],ctx['defs'],ctx['perception'],ctx['classes'],ctx['races'],counts)
 if expired:events.insert(0,['expiry',expired])
 return packets,events,heals+castheals,expired


def upgrade_score(owned,kind,tier,tables):
 if kind==0:return C.div(tables[0][tier],C.add(C.mul(C.rounded(Fraction(u(owned,32))),0x3f000000),C.ONE))
 if kind==2:return C.rounded(Fraction(min(max(0,12-u(owned,20)),tables[2][tier])))
 x=u(owned,{1:16,3:24,4:28}[kind]);factor=C.div(C.add(x,0xbe4ccccd),0x3f4ccccd)if kind==1 else C.mul(C.sub(bits(5.),x),0x3e800000)if kind==3 else C.div(C.sub(bits(6.),x),bits(5.))
 return C.mul(factor if C.rational(factor)>0 else 0,tables[kind][tier])

def candidates_reference(g,kit):
 if len(g['owned_records80_hex'])==1:return G.candidates(g['rng_words'],kit,g['level'])
 assert len(g['owned_records80_hex'])==2
 owned=[bytes.fromhex(h)for h in g['owned_records80_hex']];names=['cleave','demo_shout'];assert[u(x)for x in owned]==[5882740,5883180]and g['derived_bits']['1544']==C.ONE and g['derived_bits']['1584']==0
 for name,row in zip(names,owned,strict=True):
  assert u(row,4)==1 and all(u(row,k)==0 for k in[20,32,36,40,44,48,60,72])and all(u(row,k)==C.ONE for k in[16,24,28,52,56,64,68,76])and u(row,12)==(C.ONE if name=='cleave'else 0x3fa00000)
  assert CANDIDATE_DEFS[name][2]==((0,1,2)if name=='cleave'else(1,3))and CANDIDATE_DEFS[name][1][84]in(5,2)
 # Current30022/27572 enumerate declaration order and call25511 at tier4
 # before appending each eligible upgrade pool entry. Other sources rejected.
 eligible={name:[k for k in CANDIDATE_DEFS[name][2]if C.rational(upgrade_score(row,k,4,CANDIDATE_TABLES))>=C.rational(0x3ba3d70a)]for name,row in zip(names,owned,strict=True)}
 assert eligible=={'cleave':[0,1,2],'demo_shout':[1,3]}
 pool=[(0x3fcccccd,'new',name,0)for name in kit if name not in names]+[(0x3fa66666,'upgrade',name,j)for j,name in enumerate(names)if eligible[name]];random=G.Sampler(g['rng_words']);chosen=[]
 for _ in range(3):
  total=0x80000000
  for weight,_,_,_ in pool:total=C.add(total,weight)
  remainder=random.uniform(total);index=len(pool)-1
  for j,(weight,_,_,_)in enumerate(pool):
   if C.rational(remainder)<C.rational(weight):index=j;break
   remainder=C.sub(remainder,weight)
  chosen.append(pool.pop(index))
 factor=C.add(C.ONE,min(C.mul(bits(float(g['level'])),0x3c23d70a),0x3e99999a));square=C.mul(factor,factor);weights=[bits(60.),C.mul(factor,bits(25.)),C.mul(square,bits(10.)),C.mul(C.mul(factor,square),bits(4.)),C.mul(square,square)];high=weights[0]
 for weight in weights[1:]:high=C.add(high,weight)
 cards=[]
 for _,variant,name,index in chosen:
  remainder=random.uniform(high);tier=0
  for j,weight in enumerate(weights):
   if C.rational(remainder)<C.rational(weight):tier=j;break
   remainder=C.sub(remainder,weight)
  kinds=[]
  if variant=='upgrade':
   kinds=[k for k in eligible[name]if C.rational(upgrade_score(owned[index],k,tier,CANDIDATE_TABLES))>=C.rational(0x3ba3d70a)];random.shuffle(kinds);kinds=kinds[:2 if tier==4 else 1]
  cards.append(dict(variant=variant,tier=tier,ability_id=name,owned_index=index,kinds=kinds,gold=0))
 return cards,list(random.words),random.draws

BATCHES=[dict(evidence='evidence/natural-demo139-oracle-20261102T162640.693635Z',handoff_sha256='36bd1554f3c4c51195de2968e5b73d54f2ad3e3a9547c4b60fe9db93877e017e',comparison_sha256='1bd45570537180f68862fe24675172d89afe73939b0f9221d79c8091ed10ffbb',steps=106,authors=11,sources=110,production=96,edges=493,bodies=81,policy='default_index0'),dict(evidence='evidence/natural-demo-second139-oracle-20261102T163422.291343Z',handoff_sha256='902910b59b4fb40a1cc465a74927627f48304ffc9bed701b4ae2188a402ac495',comparison_sha256='c5974b23b007acb7195bc9388d79f97618ad668fa1ce78b078d21922bc776828',steps=107,authors=9,sources=113,production=98,edges=506,bodies=84,policy='first_default0_stop_second')]

def review_batch(out,joint,entry,with_spawn):
    global BATCH,COMP
    BATCH=ROOT/entry['evidence'];COMP=entry['comparison_sha256'];start=time.monotonic();out.mkdir();assert sha(BATCH/'comparison.json')==COMP
    hand=joint;comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');rt=load(BATCH/'runtime.json');authors=hand['author_files'];assert len(authors)==entry['authors']
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
    ctx=load_context();ctx.update(family_definitions={x:ctx['data'](x,72)for x in[5830904,5830976]},names={5830904:'Kobold Vermin',5830976:'Young Wolf'});raw,module,data=ctx['raw'],ctx['module'],ctx['data'];private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
    for a,b in zip(module['sections'],private['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
    assert private['exports']==module['exports']+[tuple(x)for x in m['added_exports']]and len(module['imports'])==882 and[(x['module'],x['name'],x['type_index'])for x in module['imports']]==[(x['module'],x['name'],x['type_index'])for x in m['original_imports']]
    bindings={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx,claim in m['functions'].items():
            a,z=module['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();stream.seek(lo);wat=stream.read(hi-lo);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());assert all(proof[k]==claim[k]for k in proof)and wat==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=proof;texts[int(idx)]=wat.decode();(out/f'{idx}.wat').write_bytes(wat)
    assert len(bindings)==entry['bodies'];guard='\n'.join(texts[1076].splitlines()[58:101]);assert 'i32.const 12'in guard and'f32.gt'in guard and'br 2'in guard;prior=load(N.STATIC/'binding.json')
    for idx,proof in prior['bodies'].items():
        if idx in bindings:assert proof==bindings[idx]
    for key,claim in m['static_reads'].items():
        address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==claim['sha256']
    assert data(1593648,44).hex()==m['levelup44_hex']and data(1593604,8)==b'level_up'and data(1593618,8)==b'Level Up'and data(1593626,19)==b'Spell_Holy_HolyBolt'
    global CANDIDATE_DEFS,CANDIDATE_TABLES
    CANDIDATE_DEFS=ctx['defs'];CANDIDATE_TABLES=[struct.unpack('<5I',data(a,20))for a in[5405004,5405040,5405076,5405112,5405148]]
    if entry['steps']==107:
        assert 'call 30022'in texts[2181]and 'call 27572'in texts[30022]and 'call 30628'in texts[27572]and 'call 25511'in texts[27572]and 'i64.const 5362837094'in texts[2181]
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
        game=bytes.fromhex(capture['raw_game2592_hex']);assert game[275]==0 and u(game,2092)==u(game,2104)==0;assert G.tree_fields(capture,game)==want['growth']['player_fields']and u(game,1440)==p['g']['current_hp_bits']
        for card,hx in zip(want['growth']['candidates'],capture['raw_candidates80_hex'],strict=True):
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
        for off in[176,600,648,1984,2032,2044,2056]:assert u(game,off)==0
        assert game[387]==0;counts['player_views']+=1
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
        game=bytes.fromhex(playerobs['capture']['raw_game2592_hex']);aggregate=bytes.fromhex(obs['accounting_struct68_hex']);assert struct.unpack_from('<Q',game,960)[0]==int(L['event_counter960'])and game[1000:1068]==aggregate and struct.unpack_from('<Q',aggregate,16)[0]==int(L['accepted_count1016'])
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
        player(obs['player'],p,'choice',flag);combat(obs['combat'],p,s);accounting(obs['healing'],L,obs['player'],'choice');ai_check(obs['ai'],ai,storage,count)
        assert obs['gold1456']==s.get('gold',0)and obs['earned1100']==s.get('earned',0)
    cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==1 and [(c['app_seed_u64'],len(c['timestamps64']),c['selection_policy'])for c in cases]==[('111',entry['steps'],entry['policy'])]
    for case,A in zip(cases,actual,strict=True):
        assert case['id']==A['id']and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['stack_after']==1048576 and case['clock_initial']==dict(tag=1,previous64='0')
        opening,p,s,ai,L,storage,count=initial_reference(case,ctx);op=opening['projection'];initial_flag=A['initial']['aura']['flag2569'];player(A['initial'],p,'initial',initial_flag);accounting(A['initial_healing'],L,A['initial'],'initial');ai_check(A['initial_ai'],ai,storage,count)
        cells('openingGame',opening['known_Game2592'],A['opening']['raw_game2592_hex']);assert A['opening']['packets']==op['packets']and A['initial']['capture']==A['opening']
        for key in['units','pickups','special','windows','boundaries']:
            for row,hx in zip(op[key]['storage'],A['opening']['background'][key]['storage'],strict=True):cells('opening_'+key,row,hx)
        previous=A['initial'];prior_stamp=Fraction(0);steps=[];choice=None;choices=[];chosen_first=False;scheduler=dict(budget2416_bits=bits(3.),previous_player_xyz=[0,0,0],velocity_xy=[0,0],timer_fields={'2424':bits(60.),'2440':bits(240.),'2444':bits(40.),'2448':bits(60.),'2452':20,'2456':0})
        for j,(stampstr,obs)in enumerate(zip(case['timestamps64'],A['stages'],strict=True)):
            stamp=Fraction(C.f64(int(stampstr)));dt=C.rounded(min(Fraction(.1),max(Fraction(0),stamp-prior_stamp)));prior_stamp=stamp;now=C.add(p['g']['now_bits'],dt)
            assert stamp==Fraction(j+1,8)and obs['clock']==dict(tag=1,previous64=stampstr,dt_bits=dt,now_bits=now)
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(inherited,2352,now);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['Game_clock_input_inheritance_bytes']+=2592
            oldstorage=[bytearray.fromhex(hx)for hx in obs['before_combat']['records432_hex']];oldcount=count
            pk,events,heals,expired=player_stage(p,s,L,now,dt,ctx,counts);player(obs['after_player'],p,('player',case['id'],j),initial_flag)
            logical=copy.deepcopy(s['rows'])+copy.deepcopy(storage[count:]);physical=[row[:]for row in oldstorage]
            for i,row in enumerate(logical):
                for k,v in enumerate(row):
                    if v is not None:physical[i][k]=v
            assert [r.hex()for r in physical]==obs['after_player']['capture']['background']['units']['storage'];counts['player_NPC_physical_replay_bytes']+=432*len(physical)
            ai,storage,count,pa,br,removed=enemy_with_live(p,s,ai,storage,count,now,dt,ctx,counts);player(obs['after_ai'],p,('AI',case['id'],j),initial_flag)
            for i,row in enumerate(br):
                for k,v in enumerate(row):
                    if v is not None:physical[i][k]=v
            physical_count=oldcount
            for guid in removed:
                retained=[row[:]for row in physical[:physical_count]if str(int.from_bytes(row[112:120],'little'))!=guid]
                for i,row in enumerate(retained):physical[i]=row
                physical_count=len(retained)
            assert physical_count==count and[r.hex()for r in physical]==obs['after_ai']['capture']['background']['units']['storage'];counts['AI_NPC_physical_replay_bytes']+=432*len(physical)
            beforecollection=copy.deepcopy(s['pickups']);p,s,L,collected=collect_reference(p,s,L,now,ctx);player(obs['after_collection'],p,('collect',case['id'],j),initial_flag);packets=pk+pa+collected['known_packets']
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
                if not chosen_first:
                    assert p['g']['candidates'][0]['variant']=='new'and p['g']['candidates'][0]['ability_id']=='demo_shout'and obs['selection_index']==0
                    p,s,L,selection=select_choice_reference(p,s,L,0,storage,count,ctx);chosen_first=True;packets.extend(selection['known_packets']);choice['selection']=selection;counts['default0_selections']+=1;counts['selection_pickups']+=len(selection['consumed']);counts['selection_raw_XP']+=selection['raw_XP'];counts['selection_award']+=selection['award']
                else:assert obs['selection_index']is None and j==106 and j==len(A['stages'])-1 and entry['steps']==107 and p['g']['candidates']==[dict(variant='new',tier=0,ability_id=name,owned_index=0,kinds=[],gold=0)for name in['bloodrage','execute','shield_slam']]
                choices.append(choice)
            else:assert obs['before_choice']is None and obs['selection_index']is None
            player(obs['after'],p,('final',case['id'],j),initial_flag);combat(obs['combat'],p,s);accounting(obs['healing'],L,obs['after'],('ledger',case['id'],j));ai_check(obs['ai'],ai,storage,count)
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
    assert counts['natural_steps']==entry['steps'] and counts['default0_selections']==1 and counts['phase2_choices']==(1 if entry['steps']==106 else 2) and counts['selection_pickups']==1 and counts['selection_raw_XP']==counts['selection_award']==2 and counts['Demo_max_targets']==5 and counts['post_select_Demo']==1 and counts['Demo_success_step91']==1 and counts['expiry169']==0 and counts['Wolf_born']==0
    assert reference[0]['choices'][0]['step']==85 and reference[0]['choices'][0]['cards'][0]==dict(variant='new',tier=2,ability_id='demo_shout',owned_index=0,kinds=[],gold=0)
    assert counts['known_packets']==(173 if entry['steps']==106 else 178)and counts['known_packet_bytes']==(9147 if entry['steps']==106 else 9256)
    assert rt==comp['runtime']and rt['fresh_instances']==1 and rt['full_calls']=={'922':0,'925':entry['steps'],'952':entry['steps'],'1076':0,'1093':1,'1108':1,'1238':0,'1600':1,'1775':0,'2123':entry['steps'],'2890':entry['steps'],'2945':1,'3755':0,'4677':0}and rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None
    assert len(rt['target_and_setup_returns'])==4*entry['steps']+4 and all(v['before']==v['after']==1048576 and v['returned']for v in rt['target_and_setup_returns'])and len(rt['world_source_checks'])==entry['steps']+2 and all(v['ranges']==2318 and v['unchanged']for v in rt['world_source_checks'])and rt['stack_checks']==4*entry['steps']+9 and rt['allocator_calls']==5 and rt['output_bytes']==(BATCH/'actual.jsonl').stat().st_size
    assert rt['explicit_XP_gain_calls']==0 and rt['actual2123then925then2890then952']and not rt['XP_HP_card_RNG_CD_status_timers_NPC_positions_written_by_driver']and not rt['basic_or_racial_disabled']and not rt['old_Game_used_as_target']and rt['peak_memory_bytes']==177078272<=rt['memory_cap_bytes']==268435456 and rt['native_executions']==rt['full_mainloop_frames']==rt['complete_games']==0
    term=load(BATCH/'owned-terminal.json');assert term==comp['process']==hand['process']and term['exit_code']==0 and term['pid_missing']and term['pgid_missing']
    for name,h in authors.items():assert sha(ROOT/name)==h
    for name,h in sources.items():assert sha(ROOT/name)==h
    assert not AUDIT and not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    result=dict(accepted=True,batch=str(BATCH.relative_to(ROOT)),with_spawn=with_spawn,source_sha256=WASM,comparison_sha256=COMP,counts=dict(counts),source_files=sources,source_edges=edges,body_bindings=bindings,choices=[r['choices']for r in reference],original_process=term,reviewer_author_original_executions=0)
    save(out/'review.json',result);save(out/'independent-reference.json',reference);print(json.dumps(dict(batch=result['batch'],accepted=True,counts=dict(counts),seconds=time.monotonic()-start)),flush=True);return result

def main():
 global HELPERS
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
 chainhand=ROOT/'evidence/player-enemy139-v2-readonly-review-20261102T141221.354196Z/task-handoff.json';assert sha(chainhand)=='be34cae870f5dda6e7296461972cca20c64106f24f8d96509714bbcc4f491ed9'and load(chainhand)['files']['scripts/review_player_enemy139_v2.py']=='c30da653210f7b81d311c5a8af0e2b6ab6ede3fe93b0807d87cf4b75da03208f'and sha(ROOT/'scripts/review_player_enemy139_v2.py')=='c30da653210f7b81d311c5a8af0e2b6ab6ede3fe93b0807d87cf4b75da03208f'
 assert sha(ROOT/'scripts/review_natural_growth139_v2.py')=='94159b53391a89ef002f01093ded4a5f15db92825dba20b79d681816ff2feab6'and sha(ROOT/'scripts/review_demo_shout139.py')=='fc1662b9218c4e1326e6fed45c627cf7a60f1936580957d479a6f0e1724388d7'
 prior=load(ROOT/'evidence/demo-shout139-independent-owned-20261102T163745.038764Z/review/review.json');assert prior['reviewer_sha256']==sha(ROOT/'scripts/review_demo_shout139.py');HELPERS={**prior['helper_sha256'],**N.HELPERS,'scripts/review_natural_growth139_v2.py':'94159b53391a89ef002f01093ded4a5f15db92825dba20b79d681816ff2feab6','scripts/review_demo_shout139.py':'fc1662b9218c4e1326e6fed45c627cf7a60f1936580957d479a6f0e1724388d7','scripts/review_player_enemy139_v2.py':'c30da653210f7b81d311c5a8af0e2b6ab6ede3fe93b0807d87cf4b75da03208f'}
 observed_helpers={str(Path(v.__file__).relative_to(ROOT)):sha(v.__file__)for v in list(sys.modules.values())if getattr(v,'__file__',None)and str(v.__file__).startswith(str(ROOT/'scripts'))and Path(v.__file__).name!=Path(__file__).name}
 for n,h in HELPERS.items():assert observed_helpers[n]==h
 results=[];authors={}
 for j,entry in enumerate(BATCHES):
  batch=ROOT/entry['evidence'];assert sha(batch/'task-handoff.json')==entry['handoff_sha256'];hand=load(batch/'task-handoff.json')
  for n,h in hand['author_files'].items():assert n not in authors or authors[n]==h;authors[n]=h
  results.append(review_batch(out/('batch'+str(j)),hand,entry,True))
 counts=Counter();sources={};edges=set();bodies={}
 for r in results:
  counts.update(r['counts'])
  for n,h in r['source_files'].items():assert n not in sources or sources[n]==h;sources[n]=h
  edges.update(tuple(v)for v in r['source_edges'])
  for idx,proof in r['body_bindings'].items():assert idx not in bodies or bodies[idx]==proof;bodies[idx]=proof
 counts['Demo_max_targets']=max(r['counts']['Demo_max_targets']for r in results);counts['max_targets']=max(r['counts']['max_targets']for r in results)
 assert counts['natural_steps']==213 and counts['Demo_targets']==10 and counts['Demo_max_targets']==5 and counts['phase2_choices']==3 and counts['default0_selections']==2 and counts['selection_raw_XP']==counts['selection_award']==4 and counts['known_packets']==351 and counts['known_packet_bytes']==18403
 # Maxima aggregate by max; event/target counts aggregate by sum.
 extra={};raw=SOURCE.read_bytes();module=parse_module(raw)
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
  lo,hi=db.execute('select wat_start,wat_end from functions where idx=983').fetchone();stream.seek(lo);wat=stream.read(hi-lo);a,z=module['bodies'][983];extra['983']=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest(),direct_full_entry_calls=0);(out/'983.wat').write_bytes(wat)
 assert 'i32.load8_u offset=84\n          i32.const 11'in wat.decode()
 for table in[authors,sources,observed_helpers]:
  for n,h in table.items():assert sha(ROOT/n)==h
 assert not AUDIT and not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
 result=dict(accepted=True,scope='two fresh current139 same-seed natural Demo and second-candidate component schedules',reviewer_sha256=sha(Path(__file__)),source_sha256=WASM,author_files=authors,source_files=sources,source_import_edges=sorted(edges),source_counts=dict(files=len(sources),production=sum(n.startswith('reconstruction/')for n in sources),edges=len(edges),bodies=len(bodies)),current_body_bindings=bodies,static_only_983_guard=extra,helper_sha256=observed_helpers,batches=[dict(evidence=e['evidence'],handoff_sha256=e['handoff_sha256'],comparison_sha256=e['comparison_sha256'],process=r['original_process'],choices=r['choices'],counts=r['counts'])for e,r in zip(BATCHES,results,strict=True)],formal_counts=dict(fresh_instances=2,unique_app_seeds=1,component_steps=213,full2123=213,full925=213,full2890=213,full952=213,full1093=2,four_stage_entries=852,target_entries_with_1093=854,setup2945_1600_1108=6,direct_entries=860,reviewer_author_program_executions=0,reviewer_original_executions=0),counts=dict(counts),actual_max_Demo_targets=5,author_expected_values_read=False,complete_games=0,full884_frames=0,late14_scheduler_executions=0,seconds=time.monotonic()-start,limits=['Twofresh captures ofsameAppseed111;106+107steps share106-step input prefix. They are not two unique trajectories.', 'Real cleave-only/noXP start,firstdefault0Demo tier2 atindex85;one natural5-target Demo perbatch atindex91. Oldcomponentmax1 is not counted asmultitarget evidence.', 'Secondcapture reachesphase2atindex106 withactualBloodrage0/Execute0/ShieldSlam0. Second1093notexecuted;theseabilities are metadataonly,not restored mechanics.', 'Currenttwo-owned pool/weights/tier/RNG/eligibility reconstructed;all3secondcards arenew,so upgradedselectedkindshuffle andactualupgradeselection remainPending.', 'Knownpackets areorderedsubsets;fullnetwork/UI/presentation streams not rebuilt. Check numericcounts perbatch, not a completepacketclaim.', 'Fourcomponents2123→925→2890→952 plusfirst1093at externalclock;no full884/later14 stages or983 execution. Guardabsenceofexec11 isstatic sourcequalification only.', 'InitialRune/special/window/boundary owners persist;20sGuardian stage not reached. Wolf handlerdeclared butactualWolf births0;no positiveWolf runtime transferredfromordinaryfixtures. Demo6s expiry deadline not reached here;componentexpiry proof remains separate.', 'NewallocationNone staysunknown;physicalNPCinheritedbytes/stabledeletion/staleTail replayed separately. Semanticf64/Vec48accountingdoesnotestablishall2077physicalcontainers.', 'Resource-onlyoriginalcontext notindependentApp/worldbootstrap. No UI/save/nativeWindows/co-op/completegame acceptance.'])
 save(out/'review.json',result);print(json.dumps(dict(accepted=True,counts=dict(counts),source_counts=result['source_counts'],formal_counts=result['formal_counts'],seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
