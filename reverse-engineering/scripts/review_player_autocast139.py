#!/usr/bin/env python3
"""Different-author readonly full1238/2123 default positive-target review."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import ast,copy,hashlib,json,math,os,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_healing_hurtactor139_v3 as H
import review_enemy_ai139 as AI
from review_combat139 import sha,parse_module,local_closure
C=H.C;U=H.U;D=H.D;T=H.T;G=H.G;W=H.W;O=H.O
load_world=H.load_world;initial_record=H.initial_record;WASM=H.WASM;fp=H.fp
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
BATCH=ROOT/'evidence/player-autocast139-oracle-20261102T125128.084675Z'
HAND='6d8ea6c9bdb1322d43d4875c16e9e10723fc7136b16f7ba16b2b69ad3e1d73dc'
COMP='6932653ea3c74f45cbf8cf9276a223a055d310b794a07e107724bde243b3bdc4'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]

def targets(rows,player,now,radius):
 square=C.mul(radius,radius);selected=[]
 for i,row in enumerate(rows):
  marker=D.read(row,0);assert marker in(0,1)
  if marker==0 and C.le(C.distance(T.position(row,now),player),square):selected.append(i)
 selected=D.stable(selected,lambda i:C.totalkey(C.distance(T.position(rows[i],now),player)));buckets=[[],[],[],[]]
 for i in selected:buckets[3 if C.rational(now)<C.rational(D.read(rows[i],380))else 2-rows[i][424]].append(i)
 if buckets[2]:
  anchor=T.position(rows[buckets[2][0]],now);near=[];far=[]
  for i in buckets[2]:(near if C.rational(C.distance(T.position(rows[i],now),anchor))<=36 else far).append(i)
  buckets[2]=D.stable(near,lambda i:C.totalkey(D.read(rows[i],288)))+far
 return[i for group in buckets for i in group]

def resolve_hit(p,s,L,index,amount,critical,spell,school,now,world,scalars,speeds,normal,counts):
 row=s['rows'][index];target=D.read(row,112,8);assert D.read(row,0)==0
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

def cooldown(spell,remaining):
 milliseconds=int(C.rational(C.mul(remaining,0x447a0000)));return[[308,struct.pack('<QII',0,spell,milliseconds).hex()],[309,struct.pack('<IQ',spell,0).hex()]]

def scheduler(p,s,L,now,dt,world,scalars,speeds,normal,definitions,perception,classes,races,counts):
 g=p['g'];packets=[];events=[];heals=[];timer=C.sub(p['scalar']['1628'],dt)
 if C.rational(timer)<=0:
  chosen=targets(s['rows'],p['player'],now,0x40c00000)
  if chosen:
   index=chosen[0];target=D.read(s['rows'][index],112,8);roll,s['words']=D.uniform24(s['words']);critical=int(C.rational(g['derived_bits']['1548'])>C.rational(roll));base=C.mul(C.mul(C.mul(0x41dc0000,0x3fc00000),C.ONE),g['derived_bits']['1540']);amount=C.mul(base,g['derived_bits']['1552'])if critical else base
   shown=max(0,min(C.M,int(C.rational(amount))));packets.append([330,(struct.pack('<I',130 if critical else 2)+C.packguid(0)+C.packguid(target)+struct.pack('<I',shown)+bytes([1])+struct.pack('<IfI6I',0,float(shown),shown,0,0,1,0,0,0)+b'Melee\0melee\0').hex()])
   a,b=resolve_hit(p,s,L,index,amount,critical,0,0,now,world,scalars,speeds,normal,counts);packets.extend(a);heals.extend(b)
   timer=C.mul(C.mul(0x3fcccccd,0x3f99999a),AI.sqrt32(g['derived_bits']['1544']));events.append(['basic_success',target,amount,critical,timer,1]);counts['basic']+=1;counts['basic_crit']+=critical
  else:timer=0x3e19999a;events.append(['basic_no_target',timer])
 p['scalar']['1628']=timer
 for index,hx in enumerate(g['owned_records80_hex']):
  row=bytearray.fromhex(hx);remaining=C.sub(u(row,8),dt);U.put(row,8,remaining);g['owned_records80_hex'][index]=row.hex()
  if C.rational(remaining)>0:continue
  name='cleave'if u(row)==5882740 else'thunder_clap';definition=definitions[name][1];spell=u(definition,44);U.attempt(p,spell)
  if name=='cleave':
   radius=u(definition,56);chosen=targets(s['rows'],p['player'],now,radius);limit=u(definition,64);limit=max(1,(limit+u(row,20)+u(row,60)+g['derived_bits']['1592'])&C.M)if limit else 1;chosen=chosen[:limit];coefficient=C.ONE
  else:
   radius=C.mul(g['derived_bits']['1580'],C.mul(u(definition,60),C.mul(u(row,24),u(row,64))));assert C.rational(radius)<=70;square=C.mul(radius,radius);chosen=[i for i,r in enumerate(s['rows'])if D.read(r,0)==0 and C.le(C.distance(T.position(r,now),p['player']),square)];chosen=D.stable(chosen,lambda i:C.totalkey(C.distance(T.position(s['rows'][i],now),p['player'])));coefficient=0x3f000000
  ids=[D.read(s['rows'][i],112,8)for i in chosen];value=C.mul(C.mul(C.mul(C.mul(u(definition,48),0x3fb33333),u(row,12)),u(row,52)),coefficient);life=C.mul(g['derived_bits']['1536'],u(row,72))if C.rational(u(definition,48))>0 else 0;base=C.mul(g['derived_bits']['1540'],C.add(value,life))
  if ids:packets.append([306,C.launch(0,845,ids)if name=='cleave'else T.launch(ids)])
  for targetindex in chosen:
   roll,s['words']=D.uniform24(s['words']);critical=int(C.rational(g['derived_bits']['1548'])>C.rational(roll));amount=C.mul(base,g['derived_bits']['1552'])if critical else base
   a,b=resolve_hit(p,s,L,targetindex,amount,critical,spell,definition[85],now,world,scalars,speeds,normal,counts);packets.extend(a);heals.extend(b)
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

def main():
    start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(SOURCE)==WASM and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
    hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json')
    authors=hand['author_files'];assert len(authors)==7
    for n,h in authors.items():assert sha(ROOT/n)==h
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==87 and len([n for n in sources if n.startswith('reconstruction/')])==73
    assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(comp['source_import_edges'])==333
    for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
    for table in(comp['frozen'],comp['artifacts'],prep['frozen']):
        for n,h in table.items():assert sha(BATCH/n)==h
    assert comp['differences']==0 and comp['cases']==comp['completed_cases']==4 and prep['expected_before_original']and not prep['original_input_contains_expected']and comp['forbidden_model_reads']==[]
    helper_names=['review_healing_hurtactor139_v3.py','review_enemy_ai139.py','review_player_update139.py','review_thunder_clap139.py','review_death139.py','review_cast139.py','review_combat139.py'];helpers={n:sha(ROOT/'scripts'/n)for n in helper_names}
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
    assert len(m['functions'])==40 and len(original['sections'])==len(private['sections'])and len(original['imports'])==882
    for a,b in zip(original['sections'],private['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
    assert private['exports']==original['exports']+[tuple(x)for x in m['added_exports']]
    texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx,claim in m['functions'].items():
            a,z=original['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();stream.seek(lo);b=stream.read(hi-lo)
            proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(b).hexdigest());assert all(proof[k]==claim[k]for k in proof)and b==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=proof;texts[int(idx)]=b.decode();(out/f'{idx}.wat').write_bytes(b)
    for key,proof in m['static_reads'].items():
        address,n=map(int,key.split(':'));assert hashlib.sha256(data(address,n)).hexdigest()==proof['sha256']
    assert original['types'][original['decl'][913-882]]==('7f7e7d7f7f7f7f','')
    assert 'local.get 41\n        local.get 33\n        i32.const 0\n        i32.const 0\n        local.get 10\n        i32.const 1\n        call 913' in texts[1238]
    assert 'call 13833'in texts[1238]and 'call 9541'in texts[913]and 'i32.load8_u offset=908'in texts[913]
    assert data(1592776,5)==b'Melee'and data(1596339,5)==b'melee'
    assert [u(cls,k)for k in(0,4,8,12)]==[1,0x41dc0000,0x3fcccccd,0x40c00000]
    assert 'f32.sqrt'in texts[1238]and'call 8673'in texts[1238]and'call 23328'in texts[1238]
    assert 'local.get 57\n          i32.const 1\n          i32.const 0\n          local.get 2\n          call 1076'in texts[925]
    neighbors=list(struct.iter_unpack('<ii',data(5408444,64)));assert neighbors==[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
    assert sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(cfg['range_file']))==2318 and cfg['world_rc']==20544696
    cases=load(BATCH/'inputs.json');expected=load(BATCH/'expected.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==4
    for case,E,A in zip(cases,expected,actual,strict=True):
        breakdown_seen.clear();assert case==E['input']and case['id']==E['id']==A['id']
        op,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,heading,normal,spawn_speeds,classes,races,zones,eligible,minutes);opening=op['projection'];initial,_=G.reference(dict(id=case['id'],seed_u64=op['constructor_seed_u64'],amount=0,select_index=None),classes,races,zones,kit,defs,cooldown,damage);before=initial['before'];before['rng_words']=opening['rng_words'];gain,index,selected,_=W.grow(before,case,classes,races,kit,defs,cooldown,damage,W.inactive(opening['units']['storage']));assert index==0 and gain['candidates'][0]['ability_id']=='thunder_clap'and gain['candidates'][0]['tier']==E['actual_card_tier']
        assert A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['opening']['packets']==opening['packets']
        p=dict(g=copy.deepcopy(selected['projection']),live=copy.deepcopy(selected['live32_cells'])+[[None]*32 for _ in range(3)],count=1,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]],NPC=copy.deepcopy(opening['units']['storage']),player=opening['player_xyz']);p['g']['now_bits']=0;U.sync_aura(p);player(A['player_before'],p,'initial');assert U.project(p)==E['initial'];L=H.ledger();accounting(A['initial_healing'],L,'initial',A['player_before'])
        actual_game=bytes.fromhex(A['player_before']['capture']['raw_game2592_hex']);assert actual_game[360:362]==bytes([1,1])and struct.unpack_from('<Q',actual_game,1336)[0]==0 and u(actual_game,1432)==2 and u(actual_game,1664)==2
        if case['warmup']:
            p,_=U.tick(p,0x3f800000,0x3f800000,classes,races,defs,perception);player(A['warmup'],p,'warmup');assert U.project(p)==E['warmup'];counts['setup2123']+=1
        else:assert A['warmup']is E['warmup']is None
        sequence=1;path=None
        if case['moving_setup']:
            ai=dict(rows=copy.deepcopy(p['NPC']),now=C.sub(p['g']['now_bits'],0x3dcccccd),frame=0,player=p['player'],path=None,path_values=None,path_clock=0,sequence=1,hp=p['g']['current_hp_bits'],last=p['scalar']['1652'],incoming=0.,category=0.,has_category=False,derived=p['g']['derived_bits'],guards={o:0 for o in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(p['g']['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=[])
            ai,answer=AI.tick(ai,0x3dcccccd,world,nav,neighbors,{5830904:'Kobold Vermin'},{'Melee':'Melee'},counts);assert not answer['attacks'];p['NPC']=copy.deepcopy(ai['rows']);sequence=ai['sequence'];player(A['ai_setup']['after'],p,'actual925 setup')
            for want,hx in zip(ai['rows'],A['ai_setup']['after']['capture']['background']['units']['storage'],strict=True):cells('AI_NPC',want,hx)
            path={k:v for k,v in ai['path'].items()};path['clock2372_bits']=ai['path_clock'];assert path==A['ai_setup']['path'];counts['setup925']+=1
        else:assert A['ai_setup']is E['ai_setup']is None
        if case['warmup']:
            ic=case['incoming_control'];assert ic==dict(contact_flag=1,category=0,spell_id=0);control=dict(ic,source_guid=str(D.read(p['NPC'][0],112,8)));assert control==A['incoming_control_observed']==E['incoming_control_expected']
            g=p['g'];incoming=C.mul(case['hurt_amount_bits'],C.sub(C.ONE,g['derived_bits']['1568']));g['current_hp_bits']=C.sub(g['current_hp_bits'],incoming);p['scalar']['1652']=g['now_bits'];g['player_fields'].update({'22':math.ceil(C.rational(g['current_hp_bits'])),'28':math.ceil(C.rational(g['derived_bits']['1536']))});player(A['hurt'],p,'incoming1/0/0');assert U.project(p)==E['hurt'];counts['setup1076']+=1
            assert struct.unpack_from('<d',bytes.fromhex(A['hurt']['capture']['raw_game2592_hex']),992)[0]==float(C.rational(incoming))
        else:assert A['hurt']is A['incoming_control_observed']is E['incoming_control_expected']is None
        player(A['before_control'],p,'before controlledXYZ');assert U.project(p)==E['before_control'];assert p['g']['now_bits']==(0x3f800000 if case['warmup']else 0)
        pos=T.position(p['NPC'][0],case['action']['anchor_now_bits']);xy=(C.add(pos[0],case['action']['xoffset_bits']),pos[1]);height=world.height(*xy);assert height==case['action']['height_bits'];p['player']=(*xy,height);assert list(p['player'])==E['player_xyz']
        s=dict(rows=copy.deepcopy(p['NPC']),words=list(p['g']['rng_words']),sets=copy.deepcopy(p['sets']),total=0,spelltotals={},kills=0,elites=0,counter=opening['counter'],sequence=sequence,cost=0,pickups=copy.deepcopy(opening['pickups']['storage']),pickup_count=opening['pickups']['count']);previous=A['controlled_before'];player(previous,p,'controlledXYZ')
        stages=[]
        for j,(step,obs)in enumerate(zip(case['updates'],A['stages'],strict=True)):
            now,dt=step['now_bits'],step['dt_bits'];assert dt==0x3dcccccd and now==C.add(p['g']['now_bits'],dt)
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(inherited,2352,now);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['Game_inherited_bytes']+=2592
            p['g']['now_bits']=now;p['scalar']['2352']=now;expired=[];regen_request=regen_amount=0;heal_events=[]
            if case['mode']=='2123':
                keep=[i for i in range(p['count'])if C.rational(now)<C.rational(U.read(p['live'][i],24))];expired=[U.read(p['live'][i],20)for i in range(p['count'])if i not in keep]
                if expired:
                    old=copy.deepcopy(p['live'])
                    for k,i in enumerate(keep):p['live'][k]=old[i]
                    p['count']=len(keep);U.recalculate(p,classes,races);U.sync_aura(p);counts['expiry']+=len(expired)
                regen_request,regen_amount,heal_events=H.regen(p,L,now,dt);counts['Regen']+=len(heal_events);counts['full2123']+=1
            else:counts['full1238']+=1
            p['NPC']=copy.deepcopy(s['rows']);packets,events,cast_heals=scheduler(p,s,L,now,dt,world,scalars,speeds,normal,defs,perception,classes,races,counts);heal_events+=cast_heals
            if expired:events.insert(0,['expiry',expired])
            expected_player=U.project(p);assert expected_player==E['stages'][j]['player'];player(obs['after'],p,('after',case['id'],j));accounting(obs['healing'],L,('ledger',case['id'],j),obs['after']);assert L==E['stages'][j]['healing']
            combat=dict(records432_cells=copy.deepcopy(s['rows']),rng_words=list(s['words']),accounted_total_bits=str(s['total']),spell_sets=copy.deepcopy(p['sets']),player_xyz=list(p['player']),phase2587=1,spell_totals64=[[k,str(v)]for k,v in sorted(s['spelltotals'].items())],kills1084=s['kills'],elites1088=s['elites'],counter2408=s['counter'],movement_sequence2412=s['sequence'],killcost2420_bits=s['cost'],player_hp1440_bits=p['g']['current_hp_bits'],maximum1536_bits=p['g']['derived_bits']['1536'],xp1436=p['g']['xp'],pickup_capacity=len(s['pickups']),pickup_count=s['pickup_count'],pickups56_cells=copy.deepcopy(s['pickups']))
            assert combat==E['stages'][j]['combat'],('combat_expected',case['id'],j)
            for key,v in combat.items():
                if key not in('records432_cells','pickups56_cells'):assert obs['combat'][key]==v,(case['id'],j,key)
            for label,desired,got in [('NPC',combat['records432_cells'],obs['combat']['records432_hex']),('pickup',combat['pickups56_cells'],obs['combat']['pickups56_hex'])]:
                for row,hx in zip(desired,got,strict=True):cells(label,row,hx)
            for row,hx,oldhx in zip(s['rows'],obs['combat']['records432_hex'],obs['before_combat']['records432_hex'],strict=True):
                a,b=bytes.fromhex(hx),bytes.fromhex(oldhx)
                for k,value in enumerate(row):
                    if value is None:assert a[k]==b[k];counts['NPC_None_conserved']+=1
            assert events==E['diagnostics'][j]['events'],('events',case['id'],j,events,E['diagnostics'][j]['events'])
            assert packets==E['diagnostics'][j]['known_packets'],('packets',case['id'],j,[(k,a,b)for k,(a,b)in enumerate(zip(packets,E['diagnostics'][j]['known_packets']))if a!=b],len(packets),len(E['diagnostics'][j]['known_packets']))
            assert expired==E['diagnostics'][j]['expired_spells'],('expiry',case['id'],j)
            assert regen_request==E['diagnostics'][j]['regen_request_bits']and regen_amount==E['diagnostics'][j]['regen_accounted_bits']
            assert [{k:e[k]for k in('reason_id','amount_bits','event_id')}for e in heal_events]==E['diagnostics'][j]['heal_events']
            cursor=0
            for packet in packets:
                k=next(k for k in range(cursor,len(obs['new_packets']))if obs['new_packets'][k]==packet);cursor=k+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2
            counts['all_packet_observations']+=len(obs['new_packets']);counts['all_packet_observation_bytes']+=sum(len(packet[1])//2 for packet in obs['new_packets'])
            for key in('windows','special','boundaries','auxiliary','claims'):assert obs['after']['capture']['background'][key]==A['controlled_before']['capture']['background'][key];counts['background_vectors']+=1
            assert obs['after']['capture']['background']['pickups']['storage'][:2]==A['controlled_before']['capture']['background']['pickups']['storage'][:2]
            assert obs['path']==path and all(v==0 for v in obs['source_headers'].values())and obs['pending_after']['hits']['count']==obs['pending_after']['areas']['count']==0
            stages.append(dict(player=expected_player,combat=combat,healing=copy.deepcopy(L)));previous=obs['after']
        reference.append(dict(id=case['id'],stages=stages))
        assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]
    rt=load(BATCH/'runtime.json');term=load(BATCH/'owned-terminal.json');assert rt==comp['runtime']and term==comp['process']
    assert rt['full_calls']=={'2945':4,'1600':4,'1108':4,'4677':4,'1093':4,'922':0,'1775':0,'3755':0,'2123':51,'1076':3,'1238':48,'925':3}and len(rt['target_and_setup_returns'])==125
    assert rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None and rt['fresh_instances']==4 and rt['peak_memory_bytes']==177078272
    assert all(v['returned']and v['before']==v['after']==1048576 for v in rt['target_and_setup_returns'])and all(v['unchanged']and v['ranges']==2318 for v in rt['world_source_checks'])
    assert not any(rt[k]for k in('old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','App_or_world_Rc_producer_executed','externref_restored','native_executions','full_mainloop_frames','complete_games','basic_or_racial_disabled','NPC_positions_or_HP_written_by_harness'))
    assert term['exit_code']==0 and term['pid_missing']and term['pgid_missing']and H.missing(term['pid'])and H.missing(term['pgid'],True)
    assert counts['full1238']==counts['full2123']==48 and counts['damage']==13 and counts['basic']==4 and counts['basic_crit']==3 and counts['cleave']==4 and counts['thunder_clap']==3 and counts['racial']==1 and counts['Leech']==10 and counts['Regen']==24 and counts['deaths']==5 and counts['moving_deaths']==3
    assert counts['known_packets']==37 and counts['known_packet_bytes']==1587 and counts['all_packet_observations']==64 and counts['all_packet_observation_bytes']==2593
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    for n,h in authors.items():assert sha(ROOT/n)==h
    for n,h in helpers.items():assert sha(ROOT/'scripts'/n)==h
    save(out/'independent-reference.json',reference)
    result=dict(status='pass_current139_default_player_autocast96targets_readonly_independent_review',author='/root/growth139_review',reviewer='/root/growth139_world',author_handoff_sha256=HAND,comparison_sha256=COMP,reviewer_source_sha256=sha(__file__),frozen_author7=authors,independent_helper_sha256=helpers,source_files=87,production_files=73,import_edges=333,current_body_bindings=bindings,counts=dict(counts),author_owned_terminal=term,original_executions=0,author_production_checker_builder_runner_executions=0,independent_reference_sha256=sha(out/'independent-reference.json'),seconds=time.monotonic()-start,limits=['DefaultHumanWarrior/actualcleave+firstnewThunder only; controlledplayerXYZ andexplicitclock; nofullApp/884/game.','96targets=48full1238+48full2123;3moving925setup+3warmup2123+3full1076+20prefix=125direct,not125targetcases.','Basicspell0/packetflag1 vsownednonzero/flag0 andinheritedGame9080 arestaticbounddistinctcontrols; flags/metadata not dynamically sampled inside913.','13damage sharedG960/G1016/reasonf64/Vec48projection only; full2077physical96keys/catalog/bucket/history remainPending.','37knownpackets1587B are orderedsubset of64observedpackets2593B; completepacket/UI/statecallbackstream notaccepted.','Literal3flags/sourceGUID/type andincoming1/0/0 verified sourcefaithfully; incominghistory/category/callback stilloutside scopedprojection.'])
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
