#!/usr/bin/env python3
"""Read-only fixed135 resource/aura/wire audit; no production or original runs."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,hashlib,json,math,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,static_reader,missing
from review_combat137 import exports
from review_battle_shout135 import F,B,add,sub,mul
from review_resource_consumer137 import source_edges,identities
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/resource-consumer0135-oracle-20261101T203315.893397Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
MASK=0xffffffff

def sha(path):
 with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def u(row,offset=0):
 value=row[offset:offset+4];assert len(value)==4 and all(type(v)is int and 0<=v<=255 for v in value);return int.from_bytes(bytes(value),'little')
def put(row,offset,value):row[offset:offset+4]=struct.pack('<I',value)
def div(a,b):return B(F(a)/F(b))
def minimum(a,b):return a if F(a)<F(b)else b
def maximum(a,b):return a if F(a)>F(b)else b

def closure(source,edges):
 pending=['reconstruction/core_spec/resource_consumer135.py'];seen=set()
 while pending:
  n=pending.pop()
  if n in seen:continue
  seen.add(n);pending.extend(b for a,b in edges if a==n and b.startswith('reconstruction/'))
 return sorted(seen)

def strict(want,got,path,counts):
 if want is None:
  assert len(path)>=4 and path[-4]in('live','pickups','aura')and path[-3]=='storage'
  assert type(got)is int and 0<=got<=255;counts['explicit_unknown_physical_bytes']+=1;counts['unknown_original_nonzero_bytes']+=bool(got);return
 assert type(want)is type(got),(path,type(want),type(got))
 if isinstance(want,dict):
  assert set(want)==set(got),(path,set(want),set(got))
  for k,v in want.items():strict(v,got[k],path+(k,),counts)
 elif isinstance(want,list):
  assert len(want)==len(got),(path,len(want),len(got))
  for index,(a,b)in enumerate(zip(want,got)):strict(a,b,path+(index,),counts)
 else:assert want==got,(path,want,got);counts['known_values']+=1

def selected_lives(live,count,now):
 accepted=[]
 for index,row in enumerate(live[:count]):
  if not F(u(row,24))>F(now):continue
  kind,spell=u(row,8),u(row,20);assert kind in(0,8)
  value=u(row,12)if kind==8 else 0
  if kind==8:assert math.isfinite(F(value))and F(value)>=0
  if spell!=774 and any(s==spell for _,s,_,_ in accepted):
   assert kind==0 and all(k==0 for k,s,_,_ in accepted if s==spell),'Duplicate kind8 outside admitted domain';continue
  accepted.append((kind,spell,u(row,24),value))
 return accepted

def reference_stats(t,live,count,now,read):
 """Static class/race sources and ordered admitted1512 binary32 arithmetic."""
 cls,race=t['class_byte'],t['race_byte'];cp=u(read(1595888+4*((cls-2)&255),4))if((cls-2)&255)<=9 else 5462608;rp=u(read(1595728+4*((race-2)&255),4))if((race-2)&255)<=6 else 5459304
 hp,armor=struct.unpack('<2I',read(cp+72,8));rpv,nr=struct.unpack('<2I',read(rp+16,8));assert nr<=16
 n=sub(B(float(t['level'])),B(1));v={0:B(1),1:add(mul(n,0x3cf5c28f),B(1)),2:0,3:B(1),4:0x3d4ccccd,5:armor,6:add(mul(n,0x3da3d70a),0x3f4ccccd),7:B(9),8:B(1),9:B(1),10:0,11:0}
 for j in range(nr):
  tag,value=struct.unpack('<2I',read(rpv+j*8,8));assert tag in v
  if tag==7:v[7]=mul(v[7],add(value,B(1)))
  else:v[tag]=add(v[tag],value)
 for kind,spell,expiry,value in selected_lives(live,count,now):
  if kind==8:v[1]=add(v[1],mul(B(1),value))
  if spell==23451:v[3]=add(v[3],0x3f19999a)
  elif spell==23505:v[1]=add(v[1],0x3f000000)
 base=add(hp,mul(n,B(9)));maxhp=mul(add(base,0),v[0]);armor=minimum(v[5],0x3f19999a);speed=minimum(v[3],0x400ccccd)
 result={1536:maxhp,1540:add(add(div(mul(0,armor),B(10)),mul(0,maximum(sub(v[5],0x3f19999a),0))),v[1]),1544:div(B(1),add(v[2],B(1))),1548:B(1)if F(v[4])>1 else v[4],1552:add(B(2),add(v[4],B(-1)))if F(v[4])>1 else B(2),1556:speed,1560:v[7],1564:v[8],1568:armor,1572:0x3f19999a,1576:add(mul(0,maxhp),v[6]),1580:B(1),1584:add(v[10],t['conditional268_bits'])if t['flag2574']else v[10],1588:v[9],1592:0,1596:0,1600:v[11],1604:0,1608:min(t['level']//15,3),1612:0,1616:add(div(maxhp,maximum(base,B(1))),B(-1)),1620:0,1624:0}
 return{str(k):value for k,value in result.items()}

def reference_aura(live,count,now,previous,initialized,fields,sem):
 selected=selected_lives(live,count,now);order=[];grouped={}
 for kind,spell,expiry,value in selected:
  if spell not in grouped:grouped[spell]=[expiry,1];order.append(spell)
  else:
   assert spell==774;grouped[spell][0]=maximum(grouped[spell][0],expiry);grouped[spell][1]=(grouped[spell][1]+1)&MASK;sem['spell774_stack_aggregations']+=1
 rows=[[0]*4+[None]*12 for _ in range(48)]
 for row,spell in zip(rows,order[:32]):row[:]=list(struct.pack('<4I',1,spell,*grouped[spell]))
 def spell(row):return u(row,4)if u(row)else 0
 def flags(data,group):return sum((9 if i<32 else 8)<<(4*(i%8))for i in range(group*8,group*8+8)if u(data[i])==1)
 def apps(data,group):return sum((min(u(data[i],12),255)-1)<<(8*(i%4))for i in range(group*4,group*4+4)if u(data[i])==1 and u(data[i],12)>0)
 valid=len(previous)==48 and bool(initialized&1);writes=[]
 for i,row in enumerate(rows):
  value=spell(row)
  if not valid or value!=spell(previous[i]):writes.append((47+i,value))
 for j in range(6):
  value=flags(rows,j)
  if not valid or value!=flags(previous,j):writes.append((95+j,value))
 for j in range(12):
  value=apps(rows,j)
  if not valid or value!=apps(previous,j):writes.append((113+j,value))
 assert len(writes)<=66 and not any(101<=key<=112 for key,_ in writes)
 sem['aura_rebuilds']+=1;sem['aura_key_writes']+=len(writes);sem['aura_forced66_initializations']+=not valid;sem['aura_valid_old48_comparisons']+=valid
 fields.update((str(key),value)for key,value in writes)
 return rows,1

def packed(guid):
 data=guid.to_bytes(8,'little');mask=sum(1<<i for i,b in enumerate(data)if b);return bytes((mask,))+bytes(b for b in data if b)
def spellgo(guid,spell):return(packed(guid)*2+struct.pack('<IHBQBH',spell,256,1,guid,0,0)).hex()

def revalidate_raw(raw,runtime):
 game=bytes.fromhex(raw['raw_game8192_hex']);assert len(game)==8192;q=raw['known'];read=lambda o:struct.unpack_from('<I',game,o)[0]
 assert q['derived_bits']=={str(o):read(o)for o in range(1536,1628,4)}
 for key,o in(('current_hp_bits',1440),('speed_bits',1648),('counter2408',2408),('message_sequence2412',2412),('action_sequence1644',1644)):assert q[key]==read(o)
 assert q['rng_words']==list(struct.unpack_from('<4I',game,1720))and q['auxiliary_bits']=={str(o):read(o)for o in(1444,1448,1348,768)}
 assert q['player_fields']==raw['raw_keyed_fields']
 for name,offset,stride in(('live',1704,32),('pickups',1868,56),('aura',2000,16)):
  cap,p,count=struct.unpack_from('<3I',game,offset);v=q[name];assert(v['capacity'],v['count'])==(cap,count)and count<=cap<=4096 and len(v['storage'])==cap and p+cap*stride<=runtime['max_memory_bytes'];assert all(len(bytes.fromhex(x))==stride for x in v['storage'])
 assert q['aura']['initialized2569']==game[2569]
 aura=raw['raw_aura16'];cap,p,n=struct.unpack_from('<3I',game,2000);assert(aura['capacity'],aura['count'])==(cap,n)and ''.join(q['aura']['storage'])==aura['storage_hex']
 for name,offset,stride in(('raw_packets',1880,16),('raw_notifications',1892,12)):
  cap,p,n=struct.unpack_from('<3I',game,offset);queue=raw[name];assert(queue['capacity'],queue['count'])==(cap,n)and n<=cap<=512 and p+n*stride<=runtime['max_memory_bytes']and len(queue['active'])==n;metadata=bytes.fromhex(queue['raw_hex']);assert len(metadata)==n*stride
  for index,item in enumerate(queue['active']):
   size,ptr,length=struct.unpack_from('<3I',metadata,index*stride);assert length<=size<=1048576 and ptr+length<=runtime['max_memory_bytes']and len(bytes.fromhex(item['payload_hex']))==length
   if name=='raw_packets':assert item['opcode']==struct.unpack_from('<H',metadata,index*stride+12)[0]
 assert q['packets_known']==raw['raw_packets']['active']and q['notifications_hex']==[x['payload_hex']for x in raw['raw_notifications']['active']]
 assert q['destroy170_hex']==[x['payload_hex']for x in raw['raw_packets']['active']if x['opcode']==170]
 return q

def review_case(c,w,a,label,counts,sem,read,names):
 assert c['id']==w['id']==a['id']==label['id']and len(c['operations'])==len(w['stages'])==len(a['stages'])
 state=c['state'];t=state['stats'];assert t['flag2574']==0 and state['aura_external_sources_absent']is True and state['locale_code']=='en'
 assert all(not t[k]for k in('passives','adjustments','item_modifiers','owned_skills','timed_records','timed_definitions'))
 assert all(t[k]==0 for k in('pool1532_bits','pool1536_bits','conditional1344_id','conditional1348_bits','pool768_bits','conditional268_bits'))
 live=[list(x)for x in state['live']['storage']];lc=state['live']['count'];derived={str(k):v for k,v in state['derived_bits']};assert derived==reference_stats(t,live,lc,t['now_bits'],read)
 hp=t['current_hp_bits'];speed=t['previous_speed_bits'];sequence=state['action_sequence1644'];fields={str(k):v for k,v in state['player_fields']};aura=[list(x)for x in state['aura']['storage']];initialized=state['aura']['initialized2569'];next_id=state['notification_next_id14340336'];guid=int(c['player_guid']);assert guid==state['player_guid']
 pickup=c.get('pickups',dict(storage=[],count=0));backing=[list(x)for x in pickup['storage']];pc=pickup['count'];destroys=[];wire=[];notifications=[];locale_initialized=False
 def effect(kind,now):
  nonlocal live,lc,derived,hp,speed,sequence,aura,initialized,next_id,locale_initialized
  spell={3:23451,4:23505,5:23493}[kind];wire.append(dict(opcode=306,payload_hex=spellgo(guid,spell)));sem['actual_effects_including_nested']+=1;sem['effect_kind'+str(kind)]+=1
  if kind==5:
   request=mul(derived['1536'],0x3f000000);request=mul(request,0x3f000000 if state['heal_gate387']>4 else B(1));hp=minimum(add(hp,request),derived['1536']);fields.update({'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(derived['1536'])))})
   sem['half_heal_gate_calls']+=state['heal_gate387']>4;sem['capped_heal_calls']+=hp==derived['1536']
  else:
   write=0
   for index in range(lc):
    if u(live[index],20)==spell:sem['all_owner_same_spell_removed']+=1;continue
    if write!=index:live[write]=live[index].copy()
    write+=1
   if write==len(live):live.extend([[None]*32 for _ in range(max(4,2*len(live))-len(live))]);sem['live_capacity_growths']+=1
   for offset,value in((0,0),(4,0),(8,0),(20,spell),(24,add(now,B(10 if kind==3 else 15))),(28,0)):put(live[write],offset,value)
   lc=write+1;derived=reference_stats(t,live,lc,now,read);hp=minimum(hp,derived['1536']);fields.update({'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(derived['1536']))),'1109':mul(derived['1548'],B(100))})
   new_speed=mul(derived['1556'],B(7))
   if F(sub(new_speed,speed)&0x7fffffff)>F(0x3c23d70a):
    speed=new_speed;wire.append(dict(opcode=226,payload_hex=(packed(guid)+struct.pack('<II',sequence,speed)).hex()));sequence=(sequence+1)&MASK;sem['speed226_events']+=1
   aura,initialized=reference_aura(live,lc,now,aura,initialized,fields,sem)
  name=names[kind];text=name+'!';notice=dict(type='banner',id=next_id,kind='rune',text=text,name=name,boss=False)
  notifications.append(json.dumps(notice,ensure_ascii=False,separators=(',',':')).encode().hex());chat=('AZSBANNER\tid='+str(next_id)+';kind=rune;boss=0;name='+name+';text='+text).encode()
  wire.append(dict(opcode=150,payload_hex=(struct.pack('<BIQI',6,MASK,guid,len(chat)+1)+chat+b'\0\0').hex()));next_id=(next_id+1)&MASK;locale_initialized=True;sem['type6_150_and_JSON_events']+=1
  if next_id==0:sem['notification_u32_wraps']+=1
 for op,want,raw,meta in zip(c['operations'],w['stages'],a['stages'],label['operations']):
  now=op['now_bits']
  if op['operation']=='effect':sem['direct10298']+=1;effect(op['kind'],now)
  else:
   assert op['operation']=='collect';sem['complete2862']+=1;selected=[];xyz=c['player_xyz_bits']
   for index,row in enumerate(backing[:pc]):
    kind=u(row,8);assert kind>=2 and u(row)in(0,1);dx,dy=sub(u(row,40),xyz[0]),sub(u(row,44),xyz[1]);distance=B(math.sqrt(F(add(mul(dx,dx),mul(dy,dy)))))
    if F(distance)<=3:assert kind in(3,4,5)and u(row,24)==u(row,32)==0;selected.append(index)
   consumed=[]
   for index in reversed(selected):
    row=backing[index].copy();kind=u(row,8);owner=int.from_bytes(bytes(row[16:24]),'little');destroy=struct.pack('<Q',owner).hex();destroys.append(destroy);wire.append(dict(opcode=170,payload_hex=destroy));consumed.append([index,kind,owner,{3:23451,4:23505,5:23493}[kind]])
    for j in range(index,pc-1):backing[j]=backing[j+1].copy()
    pc-=1;effect(kind,now);sem['nested_consumed_resources']+=1
   assert consumed==meta['consumed']
   if not selected:sem['empty_collect_stages']+=1
  prediction=dict(aura=dict(capacity=len(aura),count=len(aura),storage=aura,initialized2569=initialized),packets_known=wire,notifications_hex=notifications,notification_next_id14340336=next_id,live=dict(capacity=len(live),count=lc,storage=live),pickups=dict(capacity=len(backing),count=pc,storage=backing),destroy170_hex=destroys,derived_bits=derived,current_hp_bits=hp,speed_bits=speed,auxiliary_bits={'1444':0,'1448':0,'1348':0,'768':0},player_fields=fields,rng_words=state['rng_words'],counter2408=state['counter2408'],message_sequence2412=state['message_sequence2412'],action_sequence1644=sequence)
  assert prediction==want,(c['id'],op,'Independent reconstruction differs from frozen expected',[(k,prediction[k],want[k])for k in prediction if prediction[k]!=want[k]][:1])
  observed=dict(raw['known'])
  for name in('live','pickups','aura'):observed[name]={**observed[name],'storage':[list(bytes.fromhex(x))for x in observed[name]['storage']]}
  strict(want,observed,(),counts);counts['stages']+=1;counts['observed_packets']+=raw['raw_packets']['count'];counts['observed_notifications']+=raw['raw_notifications']['count']
  locale=struct.unpack('<7I',bytes.fromhex(raw['locale_state_hex']));assert locale[6]==(3 if locale_initialized else 0)
  if locale_initialized:assert(locale[1]if locale[0]else locale[2])==0 and locale[3]==locale[5]==14
 sem['initialized_locale_cases'if locale_initialized else'untouched_locale_cases']+=1

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args();began=time.monotonic();out=args.output.resolve()if args.output else ROOT/'evidence'/datetime.now(timezone.utc).strftime('resource-consumer135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 report=json.loads((RUN/'comparison.json').read_text());assert sha(RUN/'comparison.json')=='970e32ef5af326ffd665b488a43f949eb8bd9e3192d6ffd7e2c121b78636c963'and report['comparison_complete']and report['differences']==0 and report['source_sha256_before']==report['source_sha256_after'];source=RUN/'source-snapshot';files=report['source_sha256_before'];assert len(files)==31
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 edges=source_edges(source,files);assert edges==report['local_source_import_edges'];production=sorted(n for n in files if n.startswith('reconstruction/'));assert production==closure(source,edges)and len(production)==24
 for n in production:
  for node in ast.walk(ast.parse((source/n).read_text())):
   if isinstance(node,ast.Call):
    fn=node.func;name=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else'';assert name not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__')
 for n,h in(report['frozen_artifacts']|report['artifacts']).items():assert sha(RUN/n)==h,n
 original=ORIGINAL.read_bytes();manifest=json.loads((RUN/'manifest.json').read_text());changed=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(original).hexdigest()==report['original_sha256']==manifest['original_sha256']=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'and hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
 a,b=sections(original),sections(changed);assert[x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]and all(original[x:y]==changed[v:z]for(k,x,_,y),(_,v,_,z)in zip(a,b)if k!=7)
 assert exports(changed)==exports(original)+[['research135_resource_effect10298',0,10298],['research135_resource_collect2862',0,2862],['research135_resource_consumer_stack0',3,0]]
 ids=identities(original,[x['idx']for x in manifest['functions']]+[29629,30834,23583,19964,82070]);assert ids[10298]['signature']==['7f7f','']and ids[2862]['signature']==['7f',''];static=[];texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  db.execute('pragma query_only=on')
  for index,row in ids.items():
   lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone();assert(bs,be)==(row['body_start'],row['body_end'])and hi-lo<=524288;wat.seek(lo);text=wat.read(hi-lo);texts[index]=text.decode();static.append(dict(**row,wat_start=lo,wat_end=hi,wat_sha256=hashlib.sha256(text).hexdigest()))
   if index in[x['idx']for x in manifest['functions']]:
    assert text==(RUN/(str(index)+'.wat')).read_bytes();entry=next(x for x in manifest['functions']if x['idx']==index);assert entry['body_sha256']==row['body_sha256']and entry['WAT_sha256']==hashlib.sha256(text).hexdigest()
  assert db.execute('select count(*)from calls where caller=19964 and callee=82070').fetchone()[0]>0
 read=static_reader(original);assert read(14340336,4)==b'\x01\x00\x00\x00';names={}
 for row in manifest['English_resource_labels']:
  visual=row['visual'];i=visual-9004;ptr=u(read(5505544+4*i,4));length=u(read(5505504+4*i,4));name=read(ptr,length).decode();assert(ptr,length,name)==(row['pointer'],row['bytes'],row['English']);names[visual-9003]=name
 assert names=={3:'Speed Rune',4:'Berserker Rune',5:'Restoration Rune'}
 assert read(1376537,4).hex()==manifest['notification_text_format4_hex']and read(1054294,40).hex()==manifest['banner_field_format_hex']
 assert texts[10298].index('call 1512')<texts[10298].index('call 1202')<texts[10298].index('call 42920')and texts[2862].index('call 31732')<texts[2862].index('call 10298')
 assert 'i32.const 14340336'in texts[42920]and texts[42920].index('call 10434')<texts[42920].index('call 15915')<texts[42920].index('call 22747')and'i32.const 150'in texts[22747]
 assert 'i32.load offset=2000'in texts[1202]and'i32.store offset=2000'in texts[1202]and'i32.store8 offset=2569'in texts[1202]and'i32.const 48'in texts[1202]
 assert 'f32.load offset=768'in texts[1512]or'f32.store offset=768'in texts[1512]
 del original,changed
 inputs=json.loads((RUN/'input.json').read_text());wanted=json.loads((RUN/'expected.json').read_text());actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];labels=json.loads((RUN/'labels.json').read_text());assert len(inputs)==len(wanted)==len(actual)==len(labels)==130
 runtime=report['runtime'];assert runtime==json.loads((RUN/'resource-consumer135-runtime.json').read_text());counts=Counter();sem=Counter()
 for c,w,a,label in zip(inputs,wanted,actual,labels):
  assert time.monotonic()-began<60
  for raw in a['stages']:revalidate_raw(raw,runtime)
  review_case(c,w,a,label,counts,sem,read,names)
 assert{k:counts[k]for k in report['comparison']}==report['comparison']and sem['direct10298']==163 and sem['complete2862']==81
 assert runtime['full_original_calls']=={'10298':163,'2862':81}and runtime['cases']==runtime['fresh_instances']==runtime['completed_cases']==130 and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['stack_all_restored']and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])and runtime['max_memory_bytes']<=runtime['memory_cap_bytes']==33554432
 assert all(runtime[k]is False for k in('application_start_called','full_game_started','network_used','user_saves_accessed','original_memory_snapshot_read','once_or_locale_state_injected'))and runtime['error']is None
 for row in runtime['locales']:assert bytes.fromhex(row['before_hex'])==bytes(28)and row['first_call_bootstrap_untouched']
 checker=(source/'scripts/check_resource_consumer135.py').read_text();runner=(source/'scripts/run_resource_consumer135_oracle.mjs').read_text();prepared=json.loads((RUN/'prepared.json').read_text());assert checker.index('rows,expected,labels=corpus(')<checker.index('child=subprocess.Popen(')and'child.wait(timeout=60)'in checker and prepared['expected_before_original']and prepared['source_sha256']==files and prepared['artifacts']==report['frozen_artifacts']
 assert 'w(14340336,s.notification_next_id14340336)'in runner and 'notification_next_id14340336:r(14340336)'in runner and 'once_or_locale_state_injected:false'in runner
 terminal=report['process'];assert terminal==json.loads((RUN/'process-terminal.json').read_text())and terminal['exit_code']==0 and terminal['error']is None and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
 assert sha(Path(prepared['command'][0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'and '--wasm-max-mem-pages=512'in prepared['command']and '--max-old-space-size=512'in prepared['command']
 assert not(RUN/'stderr.log').stat().st_size and json.loads((RUN/'differences.json').read_text())==[]and(RUN/'stdout.jsonl').stat().st_size==runtime['output_bytes']<=16777216 and max(len(x)for x in(RUN/'stdout.jsonl').read_bytes().splitlines(keepends=True))<=2097152
 proof=dict(functions=static,static_memory_intervals=read.proofs,local_source_import_edges=edges,consumer_order='2862 reverse31732 removal then10298; buff10529/306 ->1512 ->1202 ->42920 notification/type6-150; heal10847 then10529 without1512/1202.',notification_id_owner=dict(pointer=14340336,static_initial=1,typed_per_case_seed='1,0 orFFFFFFFF; fixed input, not inferred from unseenApp',wrap='u32+1'),aura_domain='Live-only positive kind0/unique nonnegativekind8, no ownedkind12/definition38/negative/control producers; 48x16,66logicalkeys, no101..112 writes.')
 (out/'static-proofs.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 result=dict(status='passed_scoped_read_only_review',version='0.135.1',actual_build='90898d5e3',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),reviewer_script_sha256=sha(Path(__file__)),source_files=31,production_files=24,local_dependency_edges=len(edges),current_and_frozen_sources_verified=True,nonexport_sections_and_all_callees_unchanged=True,static_proofs_sha256=sha(out/'static-proofs.json'),cases=130,stages=244,external_original_calls=runtime['full_original_calls'],comparison_counts=dict(counts),independent_semantic_checks=dict(sem),full23_derived_from_original_static_class_race_and_live_sources_recomputed=True,full48x16_aura_and_all66_key_write_rules_independently_rebuilt=True,stable_all_owner_live_filter_and_reverse_full56_compaction_preserved=True,all170_306_226_type6_150_and_notificationJSON_payloads_and_order_compared=True,notification_global_owner_and_wrapping_typed_input_verified=True,physical_auxiliary_pool_offset=768,unpredicted_observations='Physical BTree/malloc identity, full8192 Game nonprojected words and locale cache allocation bytes.',process=terminal,host_calls=0,stack_all_restored=True,model_or_original_or_checker_executed_by_reviewer=False,new_original_cases=0,full880_frames=0,native_Windows_execution=False,scope=report['scope'],input_limitations=report['input_limitations'],pending=report['pending'],elapsed_seconds=time.monotonic()-began)
 assert result['elapsed_seconds']<60
 (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],semantics=dict(sem))),flush=True)
if __name__=='__main__':main()
