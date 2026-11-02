#!/usr/bin/env python3
"""Pre-freeze independent current139 natural level/choice reference.

Author model/checker/expected and original functions are never executed.
This WIP is static preparation, not acceptance of an unfrozen natural batch.
"""
from pathlib import Path
from collections import Counter
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
from fractions import Fraction
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
    if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen')or event=='import'and str(args[0]).startswith('core_spec'):
        AUDIT['forbidden_author_or_original_execution']+=1;raise RuntimeError('Read-only reviewer refuses '+event)
sys.addaudithook(audit)
import review_cast139 as C
import review_growth139 as G
import review_player_update139 as U
import review_world_pause139 as Pause
import review_collection139 as K
import review_player_enemy139_v2 as Chain
import review_spawn_combat139 as Spawn
from review_world_position139 import load_world
from review_initial139 import reference as constructor_reference,record as initial_record
from review_combat139 import sha,parse_module,local_closure,fp,bits

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
STATIC=ROOT/'evidence/natural-growth139-independent-preparation-20261102T144755.416614Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS={'scripts/review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b','scripts/review_growth139.py':'db6246b4dc0da5aa902ef87e629ce4d460c04e2e41acad4c7b63fba2a2e9d243','scripts/review_player_update139.py':'4123e0715620c0d050bfad0c1c060b0fc5b426c36d0789c95a0c7801d52c8bde','scripts/review_world_pause139.py':'363fbe4c48e650641df248d2cc9f162df0230120748a47ab3510509e936af873'}
#player_update's exact SHA is resolved against its frozen handoff before formal review.


def level_heal_reference(player,ledger,classes,races):
    """One genuine4677 level increment, with inherited nonempty live/Aura.

    player is the independent U state, not a production dataclass. ledger
    is the previously reviewed semantic G960/1016/reason-f64 view only.
    """
    p=copy.deepcopy(player);L=copy.deepcopy(ledger);g=p['g'];before_live=copy.deepcopy(p['live']);before_aura=copy.deepcopy(p['aura']);before_hp=g['current_hp_bits'];before_max=g['derived_bits']['1536']
    old_level=g['level'];spent=G.threshold(old_level);assert 0<=old_level<=119 and g['xp']>=spent
    g['level']=(old_level+1)&0xffffffff;g['xp']=(g['xp']-spent)&0xffffffff;g['pending']=(g['pending']+1)&0xffffffff
    U.recalculate(p,classes,races);g['player_fields']['34']=g['level'];recalculated_hp=g['current_hp_bits'];maximum=g['derived_bits']['1536'];request=C.mul(maximum,0x3e4ccccd)
    candidate=C.add(recalculated_hp,request);healed=maximum if C.rational(candidate)>C.rational(maximum)else candidate;delta=C.sub(healed,recalculated_hp);g['current_hp_bits']=healed
    #11033 updatesHP before1466; default rank387<=4 admits full request.
    #The 1542 positive maxHP delta is not attributed as healing.
    events=[]
    if C.rational(delta)>0:
        L['event_counter960']=str((int(L['event_counter960'])+1)&((1<<64)-1));L['accepted_count1016']=str((int(L['accepted_count1016'])+1)&((1<<64)-1))
        prior=C.f64(int(L['reason_totals64'].get('level_up','0')));L['reason_totals64']['level_up']=str(C.bits64(prior+float(C.rational(delta))))
        events.append(dict(reason_id='level_up',amount_bits=delta,now_bits=g['now_bits'],event_id=int(L['event_counter960']),resolved_spell_id_or_zero=0,arg3_descriptor_head=-1,arg4_descriptor_head=0))
    g['player_fields']['22']=max(0,math.ceil(C.rational(healed)));g['player_fields']['28']=max(0,math.ceil(C.rational(maximum)))
    assert p['live']==before_live and p['aura']==before_aura
    return p,L,dict(before_level=old_level,after_level=g['level'],threshold_spent=spent,old_max_hp_bits=before_max,old_hp_bits=before_hp,after1542_hp_bits=recalculated_hp,new_max_hp_bits=maximum,heal_request_bits=request,heal_actual_delta_bits=delta,heal_events=events)


def gain_reference(player,ledger,amount,classes,races,kit):
    p=copy.deepcopy(player);L=copy.deepcopy(ledger);g=p['g'];g['xp']=(g['xp']+amount)&0xffffffff;levels=[]
    while g['level']<=119 and g['xp']>=G.threshold(g['level']):
        p,L,event=level_heal_reference(p,L,classes,races);g=p['g'];levels.append(event)
    g['player_fields'].update({'716':g['xp'],'717':G.threshold(g['level'])})
    if g['pending']and g['phase2587']==1:
        assert len(g['owned_records80_hex'])==1,'Only first natural choice domain restored'
        cards,words,draws=G.candidates(g['rng_words'],kit,g['level']);g.update(candidates=cards,rng_words=words,phase2587=2,selection_kind2585=0,generation_counter2400=g['generation_counter2400']+1)
    else:draws=0
    return p,L,dict(levels=levels,card_draws=draws,phase2_stop_pending=g['phase2587']==2)


def select_new_reference(player,index,classes,races,definitions,cooldown,damage):
    """1093 numeric/owned mutation, then4603 preserves other live32.

    Caller separately emits resume25613 before the1020 self packet; this
    helper does not claim complete presentation or physical heap rebuild.
    """
    p=copy.deepcopy(player);g=p['g'];card=g['candidates'][index];assert card['variant']=='new'and g['pending']==1 and g['phase2587']==2
    g['owned_records80_hex'].append(G.selected_record(card['ability_id'],card['tier'],definitions,cooldown,damage));U.recalculate(p,classes,races)
    g.update(pending=0,phase2587=1,selection_kind2585=255,flag2581=1,flags2573=0,candidates=[])
    before=copy.deepcopy(p['live']);retained=[i for i in range(p['count'])if U.read(before[i],20)!=1020]
    for j,i in enumerate(retained):p['live'][j]=copy.deepcopy(before[i])
    count=len(retained)
    if count==len(p['live']):p['live'].extend([[None]*32 for _ in range(max(4,2*count)-count)])
    row=p['live'][count];row[:8]=bytes(8);U.put(row,8,12);U.put(row,20,1020);U.put(row,24,C.add(g['now_bits'],C.ONE));U.put(row,28,0);p['count']=count+1
    fields=U.sync_aura(p)
    return p,dict(retained_source_indices=retained,appended_index=count,appended_spell=1020,appended_kind=12,unknown_unwritten_offsets=[12,20],expiry_bits=U.read(row,24),Aura_field_updates=fields)


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


def static_preparation(out):
    out=Path(out);out.mkdir();assert sha(SOURCE)==WASM;raw=SOURCE.read_bytes();module=parse_module(raw);binding=json.loads((STATIC/'binding.json').read_text())
    for idx,claim in binding['bodies'].items():
        lo,hi=module['bodies'][int(idx)];assert hashlib.sha256(raw[lo:hi]).hexdigest()==claim['body_sha256']and sha(STATIC/(idx+'.wat'))==claim['WAT_sha256']
    texts={int(k):(STATIC/(k+'.wat')).read_text()for k in binding['bodies']}
    assert texts[4677].index('call 1542')<texts[4677].index('call 11033')<texts[4677].index('call 2181')
    assert 'f32.const 0x1.99999ap-3 (;=0.2;)'in texts[4677]and texts[11033].index('f32.store offset=1440')<texts[11033].index('call 1466')and'offset=1440'not in texts[1466]
    assert texts[1466].index('i64.store offset=960')<texts[1466].index('call 2077')and'i32.const 1000'in texts[1466]
    assert texts[2181].index('i32.store8 offset=2587')<texts[2181].index('call 35988')
    assert texts[1093].index('call 1542')<texts[1093].index('call 4603')and texts[4603].index('call 25613')<texts[4603].index('i32.const 1020')<texts[4603].index('call 1173')
    result=dict(scope='Independent pre-author-freeze WIP/static reference only; not a natural-chain pass',source_sha256=WASM,current_body_bindings=binding['bodies'],descriptor_level_up=dict(address=1593648,strings=['level_up','system','known']),order=['4677level++/XPsubtract/pending++','1542recomputeincludingretainedactive20600','maxHPdeltaadjustsHPoutsidehealaccounting','11033requestnewMaxHP*.2/clampHP','1466actualpositivehealdeltaonly/G960then2077','2181phase2/35988stop','1093owned/recalculate1542','4603phase1/25613resume','removeallold1020retainotherfull32/addlive12now+1','1173Aura'],live_source_note='20600kind8value.15affectsdamage;1020kind12doesnotnumericstats;1173rebuildsAurawithinactivepayloadunknown',semantic_ledger_only=True,author_model_or_expected_reads=0,author_original_executions=0,reviewer_source_sha256=sha(Path(__file__)),complete_games=0)
    (out/'preparation.json').write_text(json.dumps(result,indent=2)+'\n');return result



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

def initial_reference(case,ctx):
    world=ctx['world'];scalars=ctx['scalars'];classes=ctx['classes'];races=ctx['races'];zones=ctx['zones']
    opening,_=Chain.O.reference(case,world,ctx['nav'],scalars,ctx['heading'],ctx['normal'],ctx['spawn_speeds'],classes,races,zones,ctx['eligible'],ctx['minutes']);op=opening['projection'];ctor,_=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=opening['constructor_seed_u64'],object_id_u64='0',flat_height_bits=world.height(*scalars['center_xy_bits'])),classes,races,zones)
    g=dict(level=1,xp=0,pending=0,phase2587=1,current_hp_bits=ctor['current_hp_bits'],derived_bits=ctor['derived_bits'],player_fields=ctor['player_fields'],rng_words=op['rng_words'],candidates=[],selection_kind2585=255,generation_counter2400=0,owned_records80_hex=ctor['owned_records_hex'],flag2581=0,flags2573=0,now_bits=0)
    p=dict(g=g,live=[],count=0,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]],NPC=copy.deepcopy(op['units']['storage']),player=op['player_xyz'])
    s=dict(rows=copy.deepcopy(op['units']['storage']),words=list(op['rng_words']),sets=[[],[],[]],total=0,spelltotals={},kills=0,elites=0,counter=op['counter'],sequence=1,cost=0,pickups=copy.deepcopy(op['pickups']['storage']),pickup_count=op['pickups']['count'],gold=0,earned=0)
    ai=dict(rows=copy.deepcopy(s['rows']),now=0,frame=0,player=p['player'],path=None,path_values=None,path_clock=0,sequence=1,hp=g['current_hp_bits'],last=p['scalar']['1652'],incoming=0.,category=0.,has_category=False,derived=g['derived_bits'],guards={o:0 for o in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(g['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=[])
    L=Chain.H.ledger();storage=copy.deepcopy(s['rows']);count=4
    return opening,p,s,ai,L,storage,count

AI=Chain.AI
D=Chain.D

def tick_with_live(state,dt,world,nav,neighbors,names,english,counts,live):
    state=copy.deepcopy(state);now=C.add(state['now'],dt);state['now']=now;player=state['player']
    if state['path']is None:
        state['path'],values=AI.breadth_first(nav,player,neighbors);state['path_values']=values;state['path_clock']=now;recomputed=True;counts['path_rebuilds']+=1;counts['BFS_values']+=len(values)
    else:
        assert AI.probe(nav,player[:2])[1]==state['path']['start_index'];recomputed=False
    motions=[];attacks=[];routing=[]
    for row in state['rows']:
        assert all(AI.word(row,p)==0xffffffff for p in(40,64,244))and AI.word(row,284)==5830904 and row[424]==0
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
        #Current1076 entry guard:Presentation330 was already sent by925.
        if any(U.read(row,8)==12 and C.rational(U.read(row,24))>C.rational(now)for row in live):
            counts['active_live12_guarded_contacts']+=1;continue
        assert all(state['guards'][p]==0 for p in state['guards'])and C.rational(state['hp'])>C.rational(damage)
        state['hp']=C.sub(state['hp'],damage);state['last']=now;state['incoming']+=fp(damage);state['category']+=fp(damage);state['has_category']=True
        source=next(row for row in state['rows']if AI.word(row,112,8)==target);assert AI.word(source,284)in names and source[424]==0
        AI.I.append_ring(state['history'],now,fp(damage),0.,fp(state['hp']),state['derived']['1536'],(names[AI.word(source,284)],english['Melee'],'INV_Sword_04'),0,0)
        state['fields'].update({'22':math.ceil(fp(state['hp'])),'28':math.ceil(fp(state['derived']['1536']))});counts['contacts']+=1
    state['packets'].extend(packets)
    answer=dict(frame=state['frame'],records=copy.deepcopy(state['rows']),hp1440_bits=state['hp'],last_hit1652_bits=state['last'],incoming992_hex=struct.pack('>d',state['incoming']).hex(),categories={'mob melee':struct.pack('>d',state['category']).hex()}if state['has_category']else{},fields=copy.deepcopy(state['fields']),history=AI.I.ring_projection(state['history']),path=copy.deepcopy(state['path']),path_clock2372_bits=state['path_clock'],movement_sequence2412=state['sequence'],packets=copy.deepcopy(state['packets']),attacks=attacks,routing=routing,path_recomputed=recomputed)
    state['frame']+=1;counts['frames']+=1;counts['movement221']+=len(motions);return state,answer



def enemy_with_live(p,s,ai,storage,count,now,dt,ctx,counts):
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
 ai,answer=tick_with_live(ai,dt,ctx['world'],ctx['nav'],ctx['neighbors'],{5830904:'Kobold Vermin'},{'Melee':'Melee'},counts,p['live'][:p['count']])
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



BATCH=ROOT/'evidence/natural-run139-v2-oracle-20261102T151854.097863Z'
HAND='8747945288895de3050a1dc5115519c004664adc05885e26fc17121fea22845c'
COMP='16b4c51032dc150522d9279da7c69ba826e637a912e70853581b22b55c4a518c'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]


JOINT=ROOT/'evidence/natural-run139-v2-joint-20261102T152159.601512Z'


def select_choice_reference(player,combat,ledger,index,physical,count,ctx):
    p=copy.deepcopy(player);s=copy.deepcopy(combat);L=copy.deepcopy(ledger);g=p['g'];card=g['candidates'][index];assert card['variant']=='new'and card['ability_id']=='thunder_clap'and g['pending']==1 and g['phase2587']==2
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
def review_batch(out,joint,entry,with_spawn):
    global BATCH,COMP
    BATCH=ROOT/entry['evidence'];COMP=entry['comparison_sha256'];start=time.monotonic();out.mkdir();assert sha(BATCH/'comparison.json')==COMP
    hand=joint;comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');rt=load(BATCH/'runtime.json');authors=hand['author_files'];assert len(authors)==10
    for name,h in authors.items():assert sha(ROOT/name)==h
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==(102 if with_spawn else 94) and sum(n.startswith('reconstruction/')for n in sources)==(89 if with_spawn else 82)
    for name,h in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==(415 if with_spawn else 367)
    for table in[comp['artifacts'],comp['frozen'],prep['frozen']]:
        for name,h in table.items():assert sha(BATCH/name)==h
    assert comp['differences']==0 and comp['cases']==comp['completed_cases']==3 and comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']and not comp['forbidden_model_reads']
    assert not load(BATCH/'expectation-read-audit.json')['forbidden']
    assert sha(SOURCE)==WASM and sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
    assert prep['resource_context_gate_sha256']==sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    ctx=load_context();raw,module,data=ctx['raw'],ctx['module'],ctx['data'];private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
    for a,b in zip(module['sections'],private['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
    assert private['exports']==module['exports']+[tuple(x)for x in m['added_exports']]and len(module['imports'])==882 and[(x['module'],x['name'],x['type_index'])for x in module['imports']]==[(x['module'],x['name'],x['type_index'])for x in m['original_imports']]
    bindings={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx,claim in m['functions'].items():
            a,z=module['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();stream.seek(lo);wat=stream.read(hi-lo);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());assert all(proof[k]==claim[k]for k in proof)and wat==(BATCH/'static'/f'{idx}.wat').read_bytes();bindings[idx]=proof;texts[int(idx)]=wat.decode();(out/f'{idx}.wat').write_bytes(wat)
    assert len(bindings)==(78 if with_spawn else 49);guard='\n'.join(texts[1076].splitlines()[58:101]);assert 'i32.const 12'in guard and'f32.gt'in guard and'br 2'in guard;prior=load(STATIC/'binding.json')
    for idx,proof in prior['bodies'].items():
        if idx in bindings:assert proof==bindings[idx]
    for key,claim in m['static_reads'].items():
        address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==claim['sha256']
    assert data(1593648,44).hex()==m['levelup44_hex']and data(1593604,8)==b'level_up'and data(1593618,8)==b'Level Up'and data(1593626,19)==b'Spell_Holy_HolyBolt'
    counts=Counter();reference=[];helper_SHA={str(Path(v.__file__).relative_to(ROOT)):sha(v.__file__)for v in list(sys.modules.values())if getattr(v,'__file__',None)and str(v.__file__).startswith(str(ROOT/'scripts'))and Path(v.__file__).name!=Path(__file__).name}
    for name,h in HELPERS.items():assert helper_SHA[name]==h
    def cells(label,want,hx):
        seen=bytes.fromhex(hx);assert len(want)==len(seen)
        for i,(v,b)in enumerate(zip(want,seen,strict=True)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
            else:assert v==b,(label,i,v,b);counts[label+'_known']+=1
    def player(obs,p,label,initial_flag):
        want=U.project(p);capture=obs['capture'];assert capture['projection']==want['growth'],(label,'growth',[(k,v,capture['projection'].get(k))for k,v in want['growth'].items()if v!=capture['projection'].get(k)])
        game=bytes.fromhex(capture['raw_game2592_hex']);assert G.tree_fields(capture,game)==want['growth']['player_fields']and u(game,1440)==p['g']['current_hp_bits']
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
    cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==3 and[(c['app_seed_u64'],len(c['timestamps64']),c['selection_policy'])for c in cases]==([('0',110,'default_index0'),('50',110,'default_index0'),('111',86,'stop_phase2')]if with_spawn else[('111',96,'default_index0'),('10',96,'default_index0'),('0',90,'stop_phase2')])
    for case,A in zip(cases,actual,strict=True):
        assert case['id']==A['id']and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248 and A['stack_after']==1048576 and case['clock_initial']==dict(tag=1,previous64='0')
        opening,p,s,ai,L,storage,count=initial_reference(case,ctx);op=opening['projection'];initial_flag=A['initial']['aura']['flag2569'];player(A['initial'],p,'initial',initial_flag);accounting(A['initial_healing'],L,A['initial'],'initial');ai_check(A['initial_ai'],ai,storage,count)
        cells('openingGame',opening['known_Game2592'],A['opening']['raw_game2592_hex']);assert A['opening']['packets']==op['packets']and A['initial']['capture']==A['opening']
        for key in['units','pickups','special','windows','boundaries']:
            for row,hx in zip(op[key]['storage'],A['opening']['background'][key]['storage'],strict=True):cells('opening_'+key,row,hx)
        previous=A['initial'];prior_stamp=Fraction(0);steps=[];choice=None;scheduler=dict(budget2416_bits=bits(3.),previous_player_xyz=[0,0,0],velocity_xy=[0,0],timer_fields={'2424':bits(60.),'2440':bits(240.),'2444':bits(40.),'2448':bits(60.),'2452':20,'2456':0})
        for j,(stampstr,obs)in enumerate(zip(case['timestamps64'],A['stages'],strict=True)):
            stamp=Fraction(C.f64(int(stampstr)));dt=C.rounded(min(Fraction(.1),max(Fraction(0),stamp-prior_stamp)));prior_stamp=stamp;now=C.add(p['g']['now_bits'],dt)
            assert stamp==Fraction(j+1,8)and obs['clock']==dict(tag=1,previous64=stampstr,dt_bits=dt,now_bits=now)
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);U.put(inherited,2352,now);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['Game_clock_input_inheritance_bytes']+=2592
            oldstorage=[bytearray.fromhex(hx)for hx in obs['before_combat']['records432_hex']];oldcount=count
            pk,events,heals,expired=Chain.player_stage(p,s,L,now,dt,ctx,counts);player(obs['after_player'],p,('player',case['id'],j),initial_flag)
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
            counts['positive_Regen']+=0 #already accumulated by frozen player_stage
            for grew in collected['growth']:
                counts['level_transitions']+=len(grew['levels']);counts['level_up_positive_events']+=sum(bool(e['heal_events'])for e in grew['levels'])
            if with_spawn:
                assert obs['before_spawn']==obs['after_collection']['capture']['background']['units'];ctx['zone']=ctx['data'](5871348,152);ctx['definitions']=[ctx['data'](5830904+72*i,72)for i in range(12)]
                spawn_counts=Counter();scheduler,p,s,storage,count,spawn_packets,born,spawn_diag=Spawn.spawn(scheduler,p,s,ai,storage,count,now,dt,ctx,spawn_counts);packets.extend(spawn_packets);player(obs['after_spawn'],p,('spawn',case['id'],j),initial_flag)
                assert obs['scheduler']=={k:scheduler[k]for k in obs['scheduler']};counts['spawn_steps']+=1;counts['spawn_NPCs']+=len(born);counts['positive_spawn_cost_steps']+=scheduler['kill_cost2420_bits']!=0
                for key,value in spawn_counts.items():counts['spawn_'+('exp_evaluations'if key=='positive_decay'else key)]+=value
                for row,hx in zip(storage,obs['after_spawn']['capture']['background']['units']['storage'],strict=True):cells('spawnNPC',row,hx)
                oldbg=obs['before_spawn'];newbg=obs['after_spawn']['capture']['background']['units'];assert oldbg['storage'][:oldbg['count']]==newbg['storage'][:oldbg['count']]
            if p['g']['phase2587']==2:
                assert obs['before_choice']is not None;stage_view(obs['before_choice'],p,s,L,ai,storage,count,initial_flag);counts['phase2_choices']+=1;choice=dict(step=j,now_bits=now,cards=copy.deepcopy(p['g']['candidates']),active_live_before=copy.deepcopy(p['live'][:p['count']]),growth=collected['growth'])
                if case['selection_policy']=='default_index0':
                    assert p['g']['candidates'][0]['variant']=='new'and p['g']['candidates'][0]['ability_id']=='thunder_clap'and obs['selection_index']==0
                    p,s,L,selection=select_choice_reference(p,s,L,0,storage,count,ctx);packets.extend(selection['known_packets']);choice['selection']=selection;counts['default0_selections']+=1;counts['selection_pickups']+=len(selection['consumed']);counts['selection_raw_XP']+=selection['raw_XP'];counts['selection_award']+=selection['award']
                else:assert obs['selection_index']is None and j==len(A['stages'])-1 and p['g']['candidates'][0]['ability_id']!='thunder_clap'
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
                counts['post_select_basic']+=sum(e[0]=='basic_success'for e in events);counts['post_select_Thunder']+=sum(e[0]=='owned'and e[2]=='thunder_clap'and e[3]for e in events)
            steps.append(dict(now_bits=now,level=p['g']['level'],xp=p['g']['xp'],phase=p['g']['phase2587'],healing=copy.deepcopy(L),collected=collected['events'],growth=collected['growth']));previous=obs['after']
        assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16];reference.append(dict(seed=case['app_seed_u64'],steps=steps,choice=choice))
    assert counts['natural_steps']==(306 if with_spawn else 282) and counts['default0_selections']==2 and counts['phase2_choices']==counts['level_transitions']==counts['level_up_positive_events']==3 and counts['XP_awarded']==(26 if with_spawn else 17)and counts['collections']==(18 if with_spawn else 13)and counts['attractions']==(19 if with_spawn else 12)and counts['removals']==(11 if with_spawn else 9)and counts['AI_attacks']==(49 if with_spawn else 15)and counts['post_select_basic']==counts['post_select_Thunder']==(2 if with_spawn else 1)
    assert counts['known_packets']==(482 if with_spawn else 204)and counts['known_packet_bytes']==(25896 if with_spawn else 9194)and counts['observed_packets']==(595 if with_spawn else 264)and counts['observed_packet_bytes']==(31070 if with_spawn else 12245)
    assert rt==comp['runtime']and rt['fresh_instances']==3 and rt['full_calls']==({'922':0,'925':306,'952':306,'1076':0,'1093':2,'1108':3,'1238':0,'1600':3,'1775':0,'2123':306,'2890':306,'2945':3,'3755':0,'4677':0}if with_spawn else{'922':0,'925':282,'1076':0,'1093':2,'1108':3,'1238':0,'1600':3,'1775':0,'2123':282,'2890':282,'2945':3,'3755':0,'4677':0})and rt['actual_host_calls']==0 and rt['denied_imports']==882 and rt['error']is None
    assert len(rt['target_and_setup_returns'])==(1235 if with_spawn else 857) and all(v['before']==v['after']==1048576 and v['returned']for v in rt['target_and_setup_returns'])and len(rt['world_source_checks'])==(312 if with_spawn else 288) and all(v['ranges']==2318 and v['unchanged']for v in rt['world_source_checks'])and rt['stack_checks']==(1250 if with_spawn else 872) and rt['allocator_calls']==15 and rt['output_bytes']==(BATCH/'actual.jsonl').stat().st_size
    assert rt['explicit_XP_gain_calls']==0 and rt['actual2123then925then2890then952'if with_spawn else'actual2123then925then2890']and not rt['XP_HP_card_RNG_CD_status_timers_NPC_positions_written_by_driver']and not rt['basic_or_racial_disabled']and not rt['old_Game_used_as_target']and rt['peak_memory_bytes']==177078272<=rt['memory_cap_bytes']==268435456 and rt['native_executions']==rt['full_mainloop_frames']==rt['complete_games']==0
    term=load(BATCH/'owned-terminal.json');assert term==comp['process']==entry['process']and term['exit_code']==0 and term['pid_missing']and term['pgid_missing']
    for name,h in authors.items():assert sha(ROOT/name)==h
    for name,h in sources.items():assert sha(ROOT/name)==h
    assert not AUDIT and not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    result=dict(accepted=True,batch=str(BATCH.relative_to(ROOT)),with_spawn=with_spawn,source_sha256=WASM,comparison_sha256=COMP,counts=dict(counts),source_files=sources,source_edges=edges,body_bindings=bindings,choices=[r['choice']for r in reference],original_process=term,reviewer_author_original_executions=0)
    save(out/'review.json',result);save(out/'independent-reference.json',reference);print(json.dumps(dict(batch=result['batch'],accepted=True,counts=dict(counts),seconds=time.monotonic()-start)),flush=True);return result


def main():
    start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(JOINT/'task-handoff.json')==HAND;hand=load(JOINT/'task-handoff.json');assert len(hand['author_files'])==10
    for name,h in hand['author_files'].items():assert sha(ROOT/name)==h
    failure=hand['failure_localization'];assert sha(ROOT/failure['path'])==failure['sha256']=='135b3b59891af9c7a4cd9fb4c93be4379b76f7ea08147fc74f7e5e3da0592c55'
    assert sha(ROOT/'scripts/review_spawn_combat139.py')=='79878046c39d39431622093bc706b6e42dcf17980a8c007bd78f627ec7db0ace'
    entries=hand['formal_batches'];assert len(entries)==2 and entries[0]['comparison_sha256']=='16b4c51032dc150522d9279da7c69ba826e637a912e70853581b22b55c4a518c'and entries[1]['comparison_sha256']=='5cab88ba3b2090e794c41ff23753ecd5aaf1fabb394765ea604cb949e29f3ec9'
    results=[review_batch(out/('batch'+str(i)),hand,entry,bool(i))for i,entry in enumerate(entries)];counts=Counter();sources={};edges=set();bodies={}
    for result in results:
        counts.update(result['counts'])
        for name,h in result['source_files'].items():
            if name in sources:assert sources[name]==h
            sources[name]=h
        edges.update(tuple(x)for x in result['source_edges'])
        for idx,proof in result['body_bindings'].items():
            if idx in bodies:assert bodies[idx]==proof
            bodies[idx]=proof
    assert len(sources)==104 and sum(n.startswith('reconstruction/')for n in sources)==89 and len(edges)==427 and len(bodies)==78
    assert counts['natural_steps']==588 and counts['spawn_steps']==306 and counts['spawn_NPCs']==25 and counts['positive_spawn_cost_steps']==174 and counts['selection_pickups']==3 and counts['selection_raw_XP']==4 and counts['selection_award']==5 and counts['known_packets']==686 and counts['known_packet_bytes']==35090 and counts['observed_packets']==859 and counts['observed_packet_bytes']==43315
    assert counts['phase2_choices']==counts['level_transitions']==counts['level_up_positive_events']==6 and counts['default0_selections']==4 and counts['post_select_basic']==counts['post_select_Thunder']==3
    for name,h in hand['author_files'].items():assert sha(ROOT/name)==h
    assert not AUDIT
    result=dict(accepted=True,scope='current139 first-natural-level sixfixtures/588controlledcomponentsteps only',author_handoff_sha256=HAND,reviewer_sha256=sha(Path(__file__)),author_files=hand['author_files'],sources=sources,source_edges=[list(v)for v in sorted(edges)],current_body_bindings=bodies,source_counts=dict(files=104,production=89,edges=427,bodies=78),batches=[dict(evidence=r['batch'],comparison_sha256=r['comparison_sha256'],original_process=r['original_process'])for r in results],formal_counts=dict(fresh_instances=6,component_steps=588,full2123=588,full925=588,full2890=588,full952=306,full1093=4,target_entries=2074,setup2945_1600_1108=18,direct_entries=2092,reviewer_author_program_executions=0,reviewer_original_executions=0),counts=dict(counts),choices=[r['choices']for r in results],failure_localization=failure,old_v1_not_accepted=True,old_v1_readonly_limited_observation='evidence/natural-growth139-independent-owned-20261102T151357.024358Z/acceptance-withheld.json',first_live12_reference_domain_failure='evidence/natural-growth139-independent-owned-20261102T151100.142371Z',preauthor_independent_preparation='evidence/natural-growth139-independent-reference-preparation-20261102T145117.710582Z/static/preparation.json',preauthor_pure_model_only='evidence/natural-growth139-independent-model-20261102T145424.617485Z/model-study.json',author_expected_values_read=False,full884_frames=0,complete_games=0,seconds=time.monotonic()-start,limits=['Current139/71a44 fixed input; no 1391 migration transfer.', 'Sixfresh defaultHumanWarrior/Elwynn initialsinglecleave/noXP/noHP/CD/RNG/card/position/racialpatches; UIindex0 actualofferedThunder orunsupported cardstopphase2.', 'Two declared schedules2123->925->2890 and2123->925->2890->952 at external884-compatibleclock, including952afterphase2entered; neither actualfull884 scheduling/frame nor completegame.', 'New1093->4603 forwardstable56BXP consumption accepts marker1 withoutarrival/radius; marker0 usespost1542radius; rawu32sum scaled/roundedonce->4677 whilephase2. Additionalpending choice remains explicitPending and was not dynamically admitted.', 'Stats maxHP+9 adjustsHP before11033; onlypositiveclampedhealdelta goes1466/G960/2077/G1016/reasonlevel_up; descriptorheads remainstatic,not sampledarguments.', 'Inherited20600 and1020nonemptylive/Aura retained. Current1076activekind12 guard beforeHP/history recovers the priorreadonlyhelperdomain failure; oldsource/failure retained.', '686 known packets35090B only orderedsubset of859observed43315B; unknown173/8225B includespresentation/UI/callbackstream. No fullnetwork/nativeWindows acceptance.', 'Known/None NPC/pickup/live/Aura/history matched, NPCphysicalknownupdates/stablecompaction/staleTail andinitial2Rune/background preserved; newallocationholes remainUnknown.', 'Sharedledger/f64/Vec48semantic view only; full2077 physical keys/catalog/buckets/history/heapaddresses andentire outputGame not reconstructed. ExactGameinputclockinheritance checked.', 'Current952domain through~11s;25newNPC/positivecost174, no60swave/40spickup/Boss180/elite240/windowdue/wholegame regression implied.', 'Resource-onlyv2context andcanonicalworld remainexplicit dependencies, no independentApp/WorldRc/externref bootstrap.', 'Oldnaturalv1 threefixture observations not acceptedasgeneralchoice composition; initial273differences andcorrected1093/4603localization retained. Freshnewold3 are separately captured and independently replayed.'])
    save(out/'review.json',result);print(json.dumps(dict(accepted=True,formal_counts=result['formal_counts'],counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
