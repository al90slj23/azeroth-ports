#!/usr/bin/env python3
"""Read-only mixed2862 audit; never executes target/model/checker/builder."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import ast,copy,hashlib,json,math,os,signal,sqlite3,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,static_reader,missing
from review_combat137 import exports
from review_resource_consumer137 import source_edges,identities
from review_resource_consumer135 import reference_stats,reference_aura,spellgo,packed,strict,u,put,minimum
from review_level_banner135 import threshold,fixed,packet
from review_resource_spawn135 import advance,uniform
from review_battle_shout135 import F,B,add,sub,mul
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'evidence/mixed-pickup0135-oracle-20261101T210401.228175Z';PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z';ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm';MASK=0xffffffff

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def div(a,b):return B(F(a)/F(b))
def rounded(w):
 r=add(w,(w&0x80000000)|0x3effffff);e=(r>>23)&255
 if e<=149:r&=0x80000000 if e<127 else((-8388608)>>((e-127)&31))&MASK
 return max(0,min(MASK,int(F(r))))
def distance(row,xyz):
 x,y=sub(u(row,40),xyz[0]),sub(u(row,44),xyz[1]);return B(math.sqrt(F(add(mul(x,x),mul(y,y)))))
def owner(row):return int.from_bytes(bytes(row[16:24]),'little')
def match_abstract(w,a):
 if w is None:assert type(a)is int and 0<=a<256;return
 if isinstance(w,list):
  assert len(w)==len(a)
  for x,y in zip(w,a):match_abstract(x,y)
 else:assert w==a,(w,a)

def reference_choices(words,level,owned,luck,read):
 # Finite positive corpus: class1,0/1 default cleave/rend owner, all selected
 # variants new. No production candidate generator is imported or executed.
 kit=[]
 for i in range(11):
  pointer=5467428+88*i;np,n=struct.unpack('<2I',read(pointer+12,8));kit.append(read(np,n).decode())
 assert kit==['cleave','whirlwind','thunder_clap','mortal_strike','execute','demo_shout','battle_shout','bloodthirst','rend','shield_slam','bloodrage']and len(owned)<=1
 owned_ids=[]
 for o in owned:
  row=struct.unpack('<20I',bytes.fromhex(o['record_hex']));assert o['ability_id']in('cleave','rend')and row[1:]==(1,1056964608,1065353216,1065353216,0,1065353216,1065353216,0,0,0,0,0,1065353216,1065353216,0,1065353216,1065353216,0,1065353216);owned_ids.append(o['ability_id'])
 pool=[(0x3fcccccd,'new',name)for name in kit if name not in owned_ids]+[(0x3fa66666,'upgrade',name)for name in owned_ids]
 selected=[];draws=0;state=tuple(words)
 for _ in range(3):
  total=0x80000000
  for weight,_,_ in pool:total=add(total,weight)
  pick,state,n=uniform(state,total);draws+=n;index=len(pool)-1
  for i,(weight,_,_)in enumerate(pool):
   if F(pick)<F(weight):index=i;break
   pick=sub(pick,weight)
  selected.append(pool.pop(index))
 step=mul(B(float(level)),0x3c23d70a);step=step if F(step)<F(0x3e99999a)else 0x3e99999a;factor=add(add(luck,B(1)),step);square=mul(factor,factor);weights=[B(60),mul(factor,B(25)),mul(square,B(10)),mul(mul(factor,square),B(4)),mul(square,square)];total=weights[0]
 for weight in weights[1:]:total=add(total,weight)
 cards=[]
 for _,variant,name in selected:
  assert variant=='new','This finite audit does not infer upgrade-kind/shuffle continuations'
  pick,state,n=uniform(state,total);draws+=n;tier=0
  for i,weight in enumerate(weights):
   if F(pick)<F(weight):tier=i;break
   pick=sub(pick,weight)
  cards.append(dict(variant='new',tier=tier,ability_id=name,owned_index=0,kinds=[],gold=0))
 return cards,list(state),draws

def one_case(c,w,a,label,read,names,templates,counts,sem):
 assert c['id']==w['id']==a['id']==label['id'];s=c['level'];t=dict(s['stats']);t['level']=s['progression']['level'];assert all(not v for v in s['sources'].values())and not s['player_fields']
 assert c['resource_context']['notification_next_id14340336']==1 and c['resource_context']['locale_code']=='en'and c['resource_context']['aura_external_sources_absent']
 assert c['resource_context']['live']=={'storage':[],'count':0}and c['resource_context']['aura']=={'storage':[],'initialized2569':0}
 back=copy.deepcopy(c['pickups']['storage']);pc=c['pickups']['count'];assert all(len(r)==56 for r in back)
 # Parallel physically declared bytes prove that inherited None cells are not
 # zero-materialized during attraction/memmove. New live/aura allocations keep
 # their separately inferred producer write masks rather than guessed values.
 physical=[[c['unknown_poison']if x is None else x for x in row]for row in back]
 live=[];lc=0;aura=[];initialized=0;derived=dict(s['derived_bits']);hp=t['current_hp_bits'];speed=t['previous_speed_bits'];oldmax=t['old_max_hp_bits'];fields={};progress=dict(s['progression']);rng=list(s['rng_words']);phase=s['phase2587'];selection=s['selection_kind2585'];generation=s['generation_counter2400'];rc=c['resource_context'];nextid=rc['notification_next_id14340336'];action=rc['action_sequence1644'];guid=rc['player_guid'];cs=c['control'];cur=cs['currency'];gold=cur['gold'];earned=cur['earned'];cq=copy.deepcopy(cur['queue']);cc=cur['queue_capacity'];xq=copy.deepcopy(cs['xp_queue']);xc=cs['xp_queue_capacity'];sequence=cs['message_sequence'];wire=[];notices=[];previous_raw_packets=[];previous_raw_notices=[]
 executions=[]
 for owned in s['choice_inputs']['owned']:
  row=bytes.fromhex(owned['record_hex']);ptr=u(row,0);nptr,n=struct.unpack('<2I',read(ptr+12,8));assert read(nptr,n).decode()==owned['ability_id'];executions.append(read(ptr+84,1)[0])
 candidates=[]
 def recalc(now):
  nonlocal derived,hp,speed,oldmax
  t['level']=progress['level'];new=reference_stats(t,live,lc,now,read);delta=sub(new['1536'],oldmax);hp=minimum(add(hp,delta)if F(delta)>0 else hp,new['1536']);oldmax=new['1536'];derived=new
  ns=mul(derived['1556'],B(7));changed=F(sub(ns,speed)&0x7fffffff)>F(0x3c23d70a)
  if changed:speed=ns
  fields.update({'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(oldmax))),'1109':mul(derived['1548'],B(100))});return changed
 def effect(kind,now):
  nonlocal lc,live,aura,initialized,hp,action,nextid
  start=len(wire);spell={3:23451,4:23505,5:23493}[kind];wire.append({'opcode':306,'payload_hex':spellgo(guid,spell)})
  if kind==5:
   request=mul(derived['1536'],B(.5));request=mul(request,B(.5)if s['heal_gate387']>4 else B(1));hp=minimum(add(hp,request),derived['1536']);fields.update({'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(derived['1536'])))})
  else:
   at=0
   for j in range(lc):
    if u(live[j],20)==spell:continue
    if at!=j:live[at]=live[j].copy()
    at+=1
   if at==len(live):live.extend([[None]*32 for _ in range(max(4,len(live)*2)-len(live))])
   for o,v in((0,0),(4,0),(8,0),(20,spell),(24,add(now,B(10 if kind==3 else 15))),(28,0)):put(live[at],o,v)
   lc=at+1
   if recalc(now):wire.append({'opcode':226,'payload_hex':(packed(guid)+struct.pack('<II',action,speed)).hex()});action=(action+1)&MASK
   aura,initialized=reference_aura(live,lc,now,aura,initialized,fields,sem)
  name=names[kind];text=name+'!';notice=dict(type='banner',id=nextid,kind='rune',text=text,name=name,boss=False);hexjson=json.dumps(notice,ensure_ascii=False,separators=(',',':')).encode().hex();notices.append(dict(kind='rune_raw',payload_hex=hexjson));chat=('AZSBANNER\tid='+str(nextid)+';kind=rune;boss=0;name='+name+';text='+text).encode();wire.append(dict(opcode=150,payload_hex=(struct.pack('<BIQI',6,MASK,guid,len(chat)+1)+chat+b'\0\0').hex()));nextid=(nextid+1)&MASK;sem['resource_'+str(kind)]+=1;return wire[start:],hexjson
 assert len(c['times_bits'])==len(w['stages'])==len(a['stages'])==len(label['operations'])
 for op,(now,want,raw,meta)in enumerate(zip(c['times_bits'],w['stages'],a['stages'],label['operations'])):
  t['now_bits']=now;radius=derived['1560'];stages=[];before=bytes.fromhex(raw['raw_Game_before8192_hex']);assert len(before)==8192 and u(before,1432)==progress['level']and u(before,1440)==hp and u(before,1456)==gold
  # Attraction first, and all selection tests use this entry radius.
  for j,row in enumerate(back[:pc]):
   if u(row,8)or u(row,0):continue
   d=distance(row,cs['player_xyz']);aged=F(sub(now,u(row,52)))>6
   if not aged and F(d)>F(radius):continue
   delay=div(d,B(32 if aged else 24));delay=delay if F(delay)>F(0x3df5c28f)else 0x3df5c28f;arrival=add(now,delay)
   put(back[j],0,1);put(back[j],4,arrival);put(physical[j],0,1);put(physical[j],4,arrival);sequence=(sequence+1)&MASK;stages.append(('xp_attract',j));sem['attraction_writes']+=1
  selected=[]
  for j,row in enumerate(back[:pc]):
   kind=u(row,8);marker=u(row,0)
   eligible=bool(marker and F(u(row,4))<=F(now))if kind==0 else(F(distance(row,cs['player_xyz']))<=F(radius)or marker==1 and F(u(row,4))<=F(now))if kind==1 else F(distance(row,cs['player_xyz']))<=3 if kind in(3,4,5)else False
   if eligible:selected.append(j)
  order=[];xpaw=[];coinaw=[];growth=[];effects=iter(meta['ordered_effects'])
  for name,j in stages:assert next(effects)['stage']==name
  for j in reversed(selected):
   row=back[j].copy();kind=u(row,8);pid=owner(row);order.append([j,kind,pid]);wire.append(dict(opcode=170,payload_hex=struct.pack('<Q',pid).hex()));e=next(effects);assert(e['stage'],e['index'],e['pickup_kind'],e['guid'])==('despawn',j,kind,pid)
   for k in range(j,pc-1):back[k]=back[k+1].copy();physical[k]=physical[k+1].copy()
   pc-=1;sem['consumed_'+str(kind)]+=1;e=next(effects);assert(e['stage'],e['index'],e['pickup_kind'],e['guid'])==({0:'xp',1:'coin'}.get(kind,'resource'),j,kind,pid)
   amount=u(row,12);factor=B(1)
   if cur['mode']==1:factor=div(B(1),add(mul(mul(B(.7)if cur['region_index']<3 else B(1),B(float((cur['member_count']-1)&MASK))),0x3e9fbe77),B(1)))
   if kind==0:
    if cur['mode']:
     if len(xq)==xc:xc=max(4,xc*2)
     xq.append([cur['local_peer'],amount])
    award=max(1,rounded(mul(factor,mul(derived['1564'],B(float(amount))))));xpaw.append(award);assert dict(e['metadata'])==dict(base_amount=amount,award=award);progress['xp']=(progress['xp']+award)&MASK;start=len(wire);newgrowth=[]
    while progress['level']<120 and progress['xp']>=threshold(progress['level']):
     spent=threshold(progress['level']);oldlevel=progress['level'];old=dict(derived);progress['level']+=1;progress['xp']=(progress['xp']-spent)&MASK;progress['pending_upgrades']=(progress['pending_upgrades']+1)&MASK;fields['34']=progress['level'];recalc(now)
     ev=dict(level_before=oldlevel,level_after=progress['level'],derived_before=[[int(k),v]for k,v in sorted(old.items(),key=lambda x:int(x[0]))],derived_after=[[int(k),v]for k,v in sorted(derived.items(),key=lambda x:int(x[0]))]);newgrowth.append(ev);growth.append(ev);sem['growth_events']+=1
     damage=mul(sub(derived['1540'],old['1540']),B(100));health=sub(derived['1536'],old['1536']);regen=sub(derived['1576'],old['1576']);text=templates[0].replace('{damage}',fixed(damage,0)).replace('{health}',fixed(health,0)).replace('{regen}',fixed(regen,2));wire.append(packet(text))
     if 6 in executions and derived['1608']>old['1608']:wire.append(packet(templates[1].replace('{n}',str(min(derived['1608'],3)+1))));sem['DOT_events']+=1
     request=mul(derived['1536'],0x3e4ccccd);request=mul(request,B(.5)if s['heal_gate387']>4 else B(1));hp=minimum(add(hp,request),derived['1536']);fields.update({'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(oldmax)))})
    assert e['growth_events']==newgrowth and e['owned_definition84']==executions and e['packets']==[[p['opcode'],p['payload_hex']]for p in wire[start:]]
    fields.update({'716':progress['xp'],'717':threshold(progress['level'])})
    eligible=progress['pending_upgrades']and phase==1 and not(s['flags2576']&1)and(s['gate2572']!=1 or s['flags2573']&1)
    if eligible:
     if not cur['mode']:assert next(effects)['stage']=='choice_pause';sem['choice_pause_events']+=1
     choice=next(effects);assert choice['stage']=='choice_notification_pending';md=dict(choice['metadata']);phase=2;selection=0;generation=(generation+1)&MASK;cards=md['candidate_metadata'];envelope=dict(type='choices',offer=generation,why='levelup',level=progress['level'],gold=gold,candidate_kinds=[x['variant']for x in cards],candidate_tiers=[x['tier']for x in cards]);assert md['known_envelope']==envelope and md['presentation_pending']is True and choice['owned_definition84']==executions
     assert cards==want['level']['candidates'];candidates=cards;notices.append(dict(kind='choices_known',**envelope));sem['choice_events']+=1
     independently_selected,newrng,draws=reference_choices(rng,progress['level'],s['choice_inputs']['owned'],derived['1584'],read);assert independently_selected==cards and newrng==want['level']['rng_words'];sem['choice_RNG_steps']+=draws;sem['independently_rebuilt_new_candidate_metadata']+=len(independently_selected);rng=newrng
   elif kind==1:
    if cur['mode']:
     if len(cq)==cc:cc=max(4,cc*2)
     cq.append([cur['local_peer'],amount])
    award=rounded(mul(factor,mul(derived['1588'],B(float(amount)))));coinaw.append(award);gold=(gold+award)&MASK;earned=(earned+award)&MASK;fields['1176']=(gold*10000)&MASK;assert dict(e['metadata'])==dict(base_amount=amount,award=award)
   else:
    p,h=effect(kind,now);assert e['packets']==[[x['opcode'],x['payload_hex']]for x in p]and e['notifications']==[h]
  assert next(effects,None)is None and meta['consumption_order']==order and meta['xp_awards']==xpaw and meta['coin_awards']==coinaw and meta['growth_events']==growth
  predlevel=dict(progression=progress,derived_bits=derived,current_hp_bits=hp,auxiliary_bits={str(o):0 for o in(1444,1448,1348,768,756)},speed_bits=speed,player_fields=fields,rng_words=rng,candidates=candidates,phase2587=phase,selection_kind2585=selection,generation_counter2400=generation)
  pred=dict(level=predlevel,pickups=dict(capacity=len(back),count=pc,storage=back),live=dict(capacity=len(live),count=lc,storage=live),aura=dict(capacity=len(aura),count=len(aura),storage=aura,initialized2569=initialized),gold=gold,earned=earned,currency_queue=cq,currency_queue_capacity=cc,xp_queue=xq,xp_queue_capacity=xc,spawn_counter=cs['spawn_counter'],message_sequence=sequence,action_sequence1644=action,notification_next_id14340336=nextid,packets=wire,notifications=notices)
  assert pred==want,(c['id'],op,[k for k in pred if pred[k]!=want[k]][:3]);observed=copy.deepcopy(raw['known'])
  for name in('pickups','live','aura'):observed[name]['storage']=[list(bytes.fromhex(h))for h in observed[name]['storage']]
  strict(want,observed,(),counts);counts['stages']+=1;assert observed['pickups']['storage']==physical
  game=bytes.fromhex(raw['raw_Game_after8192_hex']);assert len(game)==8192 and observed['level']['derived_bits']=={str(o):u(game,o)for o in range(1536,1628,4)}and u(game,1440)==hp and u(game,1456)==gold and u(game,1100)==earned and u(game,1644)==action and u(game,1648)==speed and u(game,2408)==cs['spawn_counter']and u(game,2412)==sequence and list(struct.unpack_from('<4I',game,1720))==rng
  assert game[2587]==phase and game[2585]==selection and u(game,2400)==generation and u(game,1432)==progress['level']and u(game,1436)==progress['xp']and u(game,2376)==progress['pending_upgrades']
  for name,off,stride in(('pickups',1868,56),('live',1704,32),('aura',2000,16)):
   cap,p,count=struct.unpack_from('<3I',game,off);v=observed[name];assert(cap,count)==(v['capacity'],v['count'])and len(v['storage'])==cap and count<=cap<=4096 and p+cap*stride<=33554432;sem['physical_'+name+'_bytes']+=cap*stride
  for name,base,stride in(('raw_packets',1880,16),('raw_notifications',1892,12)):
   q=raw[name];assert(q['capacity'],q['count'])==(u(game,base),u(game,base+8))and len(q['active'])==q['count']<=q['capacity'];assert u(game,base+4)+q['count']*stride<=33554432
  rp=raw['raw_packets']['active'];rn=raw['raw_notifications']['active'];assert rp[:len(previous_raw_packets)]==previous_raw_packets and rn[:len(previous_raw_notices)]==previous_raw_notices;previous_raw_packets=rp;previous_raw_notices=rn
  assert observed['packets']==[p for p in rp if p['opcode']in(170,306,226,150)]
  tagged=[]
  for n in rn:
   text=json.loads(bytes.fromhex(n['payload_hex']).decode())
   if text['type']=='banner':tagged.append(dict(kind='rune_raw',payload_hex=n['payload_hex']))
   else:
    assert text['type']=='choices';tagged.append(dict(kind='choices_known',**{k:text[k]for k in('type','offer','why','level','gold')},candidate_kinds=[x['kind']for x in text['choices']],candidate_tiers=[x['rarity']for x in text['choices']]))
  assert tagged==notices;sem['actual_known_wire_new']+=len(wire)-(sem.get('_prior_wire_case',0)if op else 0);sem['_prior_wire_case']=len(wire)
  for p in wire[(0 if op==0 else priorwire):]:sem['new_packet_'+str(p['opcode'])]+=1;sem['new_packet_bytes_'+str(p['opcode'])]+=len(bytes.fromhex(p['payload_hex']))
  priorwire=len(wire)
 sem.pop('_prior_wire_case',None)

def worker(out):
 began=time.monotonic();r=load(RUN/'comparison.json');assert sha(RUN/'comparison.json')=='19e28a54b2dc6a306dca5fd6d3bd17f16e24524f858ccb1e9265829128e48e3e'and r['comparison_complete']and r['differences']==0 and r['source_sha256_before']==r['source_sha256_after'];source=RUN/'source-snapshot';files=r['source_sha256_before'];assert len(files)==52
 for n,h in files.items():assert sha(ROOT/n)==h==sha(source/n)
 assert source_edges(source,list(files))==r['local_source_import_edges']and len(r['local_source_import_edges'])==189
 for n in files:
  if not n.startswith('reconstruction/'):continue
  for node in ast.walk(ast.parse((source/n).read_text())):
   if isinstance(node,ast.Call):
    f=node.func;name=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else'';assert name not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__')
 for n,h in r['frozen_artifacts'].items():assert sha(RUN/n)==h
 raw=ORIGINAL.read_bytes();m=load(RUN/'manifest.json');changed=(RUN/m['module_file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['original_sha256']==m['original_sha256']and hashlib.sha256(changed).hexdigest()==m['module_sha256'];aa,bb=sections(raw),sections(changed);assert[k for k,*_ in aa]==[k for k,*_ in bb]and 8 not in[k for k,*_ in aa]and all(raw[a:b]==changed[c:d]for(k,a,_,b),(_,c,_,d)in zip(aa,bb)if k!=7)
 assert exports(changed)==exports(raw)+[['research135_resource_effect10298',0,10298],['research135_resource_collect2862',0,2862],['research135_resource_consumer_stack0',3,0]]
 static=load(RUN/'mixed-static.json');entries=m['functions']+static['functions'];ids=identities(raw,sorted({x['idx']for x in entries}));assert ids[2862]['signature']==['7f',''];proofs=[]
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  db.execute('pragma query_only=on')
  for e in entries:
   i=e['idx'];assert ids[i]['body_sha256']==e['body_sha256'];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(i,)).fetchone();assert(lo,hi)==(e['wat_start'],e['wat_end'])and hi-lo<=524288;wat.seek(lo);data=wat.read(hi-lo);name=str(i)+'.wat'if e in m['functions']else'mixed-'+str(i)+'.wat';assert data==(RUN/name).read_bytes()and hashlib.sha256(data).hexdigest()==e['WAT_sha256'];proofs.append(dict(index=i,body_sha256=ids[i]['body_sha256'],WAT_sha256=e['WAT_sha256']))
  accesses=[dict(zip(('function_idx','value','wat_line','wat_offset'),x))for x in db.execute('select function_idx,value,wat_line,wat_offset from iconsts where value=14340336 order by function_idx,wat_line')];assert accesses==static['notification_literal_accesses']and {x['function_idx']for x in accesses}=={23581,42920,44447}
 writer_proofs={}
 for index,name in((23581,'mixed-23581.wat'),(42920,'42920.wat'),(44447,'mixed-44447.wat')):
  lines=(RUN/name).read_text().splitlines();at=next(i for i,line in enumerate(lines)if'i32.const 14340336'in line);window=lines[at:at+7];assert all(s in '\n'.join(window)for s in('i32.load','local.tee','i32.const 1','i32.add','i32.store'));writer_proofs[str(index)]=dict(start_line=at+1,lines=window)
 save(out/'notification-writer-proofs.json',writer_proofs)
 assert m['denied_imports']==878 and m['validator']['exit_code']==0 and m['validator']['seconds']<45 and missing(m['validator']['pid'])and missing(m['validator']['pgid'],True)
 read=static_reader(raw);assert read(14340336,4)==b'\1\0\0\0';names={e['visual']-9003:e['English']for e in m['English_resource_labels']}
 for e in m['English_resource_labels']:assert read(e['pointer'],e['bytes']).decode()==e['English']
 templates=(read(1587933,88).decode(),read(1588041,62).decode());rows=load(RUN/'input.json');wanted=load(RUN/'expected.json');actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];labels=load(RUN/'labels.json');assert len(rows)==len(wanted)==len(actual)==len(labels)==60;counts=Counter();sem=Counter()
 for c,w,a,l in zip(rows,wanted,actual,labels):assert time.monotonic()-began<60;one_case(c,w,a,l,read,names,templates,counts,sem)
 assert {k:counts[k]for k in r['comparison']}==r['comparison'];assert{str(k):sem['consumed_'+str(k)]for k in(0,1,3,4,5)}=={'0':63,'1':56,'3':16,'4':30,'5':24};assert sem['growth_events']==70 and sem['choice_events']==31 and{str(k):sem['new_packet_'+str(k)]for k in(170,306,226,150)}=={'170':189,'306':70,'226':16,'150':141}
 runtime=load(RUN/'mixed-pickup135-runtime.json');assert runtime==r['runtime']and runtime['actual_host_calls']==0 and runtime['full2862_calls']==61 and runtime['fresh_instances']==runtime['completed_cases']==60 and runtime['max_memory_bytes']<=33554432 and runtime['error']is None and not runtime['notification_counter_written_by_fixture']and not runtime['locale_Once_injected'];assert len(runtime['stack_checks'])==243 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])
 terminal=load(RUN/'process-terminal.json');assert terminal==r['process']and terminal['exit_code']==0 and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True);prep=load(RUN/'prepared.json');assert prep['expected_before_original']and prep['deadline_seconds']==60 and all(x in prep['command']for x in('--max-old-space-size=512','--wasm-max-mem-pages=512'));assert all((RUN/n).stat().st_size<=4194304 for n in('input.json','expected.json'))and(RUN/'stdout.jsonl').stat().st_size<=16777216 and all(len(x)<=2097152 for x in(RUN/'stdout.jsonl').read_bytes().splitlines())and load(RUN/'differences.json')==[]
 runner=(source/'scripts/run_mixed_pickup135_oracle.mjs').read_text();assert "if(r(14340336)!==rc.notification_next_id14340336)"in runner and 'w(14340336'not in runner and 'setUint32(14340336'not in runner
 for n,h in files.items():assert sha(ROOT/n)==h
 save(out/'static-image-proof.json',read.proofs);helpers=['review_mixed_pickup135.py','review_opening_combat135.py','review_combat137.py','review_resource_consumer137.py','review_resource_consumer135.py','review_level_banner135.py','review_resource_spawn135.py','review_battle_shout135.py'];reviewers={f'scripts/{n}':sha(ROOT/'scripts'/n)for n in helpers}
 for n,h in reviewers.items():p=out/'reviewer-source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
 save(out/'review.json',dict(status='passed_scoped_read_only_review',version='0.135.1',actual_build='90898d5e3',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),cases=60,full2862_calls=61,new_original_cases=0,model_original_checker_builder_executed=False,source_files=52,production_files=sum(n.startswith('reconstruction/')for n in files),source_edges=189,current_and_frozen_sources_match=True,only_export_section_changed=True,all_original_bodies_and_callees_preserved=True,static_functions=proofs,strict_comparison=dict(counts),independent_ordered_semantics=dict(sem),notification_owner=dict(pointer=14340336,cold_initial=1,known_writer_functions=[23581,42920,44447],writer_proof_sha256=sha(out/'notification-writer-proofs.json'),fixture_does_not_write=True,retained_across_operations=True,unknown_App_prehistory_pending=True),candidate_scope='93 new candidate metadata independently rebuilt with finite class1/default0-or1 cleave/rend pool, weighted selection and tier f32 sampling;186 RNG steps exact. Other upgrade/shuffle/gold branches and complete presentation JSON not accepted by this review.',physical_unknown_scope='Exact independently inferred None mask for full56/live/aura backing; all inherited56B None bytes separately proven equal input nonzero poison after attraction and stable memmove. No None-to0 conversion.',runtime={k:v for k,v in runtime.items()if k!='stack_checks'},stack_checks=243,original_terminal=terminal,static_image_proof_sha256=sha(out/'static-image-proof.json'),reviewer_sources=reviewers,observed_artifact_sha256={n:sha(RUN/n)for n in('stdout.jsonl','stderr.log','differences.json','prepared.json','process-terminal.json','mixed-pickup135-runtime.json','owned-process.json','validator-owned.json')},artifact_scope='Frozen original receipt seals input/expected/module; output/runtime/terminal hashes additionally bound at review time, not backdated',limitations=r['pending']+r['observations_not_predictions'],headless_resource_integration='Not accepted by this component review or by unrelated static ContextNone750 trajectory',seconds=time.monotonic()-began))

def main():
 if len(sys.argv)==3 and sys.argv[1]=='--worker':worker(Path(sys.argv[2]));return
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('mixed-pickup135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();began=time.monotonic();command=[sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(out)];error=None
 with(out/'stdout.log').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
  try:child.wait(timeout=60)
  except BaseException as e:error=repr(e)
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True),seconds=time.monotonic()-began,deadline_seconds=60,error=error);save(out/'process-terminal.json',terminal)
 if child.returncode or error:print(json.dumps(dict(directory=str(out),process=terminal,error_log=(out/'stderr.log').read_text()[-3500:])));raise SystemExit(1)
 r=load(out/'review.json');r['review_owned_terminal']=terminal;save(out/'review.json',r);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=r['status'],counts=r['independent_ordered_semantics'],process=terminal)))
if __name__=='__main__':main()
