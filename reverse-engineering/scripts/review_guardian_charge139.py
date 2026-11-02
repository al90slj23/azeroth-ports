#!/usr/bin/env python3
"""Different-author current139 Guardian925/Charge readonly recomputation.

Only current raw declarations, canonicalworld and prior independent numeric
references execute. Author production/harness/expected values never execute.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time,re
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
 if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen')or event=='import'and str(args[0]).startswith(('core_spec','resource_spec')):
  AUDIT['forbidden_execution']+=1;raise RuntimeError('Read-only review refuses '+event)
sys.addaudithook(audit)
import review_special_world139 as S
F=S.F;C=S.C;AI=S.AI;D=S.D;U=S.U;G=S.G;O=S.O
ROOT=S.ROOT;SOURCE=S.SOURCE;PROFILE=S.PROFILE;WASM=S.WASM
sha=S.sha;parse_module=S.parse_module;local_closure=S.local_closure;fp=S.fp;bits=S.bits
BATCH=ROOT/'evidence/guardian-charge139-full-20261102T172227.559733Z'
HAND='3e55ed093b3aa8dafa26ccfb1b147e08e956b344a3cd02895e110872f5567315'
COMP='d4624d5d7b96664fdc0c08ab38f70343fd5c420408772697589ada9a074f184d'
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
q=lambda b,o=0:struct.unpack_from('<Q',b,o)[0]
def load(p):
 assert Path(p).name!='expected.json','Author expected values forbidden'
 return json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
put=D.put;read=D.read;lt=AI.lt;le=AI.le;mn=AI.minimum;mx=AI.maximum


def atan_ref(v):
 a=v&0x7fffffff;index=-1;z=v
 if a>=1054867456:
  if a<1066926080:
   if a>=1060110336:z=C.div(C.sub(a,C.ONE),C.add(a,C.ONE));index=1
   else:z=C.div(C.sub(C.add(a,a),C.ONE),C.add(a,0x40000000));index=0
  elif a<1075576832:z=C.div(C.sub(a,0x3fc00000),C.add(C.mul(a,0x3fc00000),C.ONE));index=2
  else:z=C.div(0xbf800000,a);index=3
 elif a<964689920:return v
 s=C.mul(z,z);w=C.mul(s,s)
 p=C.mul(z,C.add(C.mul(w,C.add(C.mul(w,0xbdda1247),0xbe4cca98)),C.mul(s,C.add(C.mul(w,C.add(C.mul(w,0x3d7cac25),0x3e11f50d)),0x3eaaaaa9))))
 if index<0:return C.sub(z,p)
 hi=(0x3eed6338,0x3f490fda,0x3f7b985e,0x3fc90fda);lo=(0x31ac3769,0x33222168,0x33140fb4,0x33a22168)
 return C.sub(hi[index],C.sub(C.sub(p,lo[index]),z))^(v&0x80000000)
def atan2_ref(y,x):
 assert x&0x7fffffff<0x7f800000 and y&0x7fffffff<0x7f800000
 if x==C.ONE:return atan_ref(y)
 quadrant=((x>>30)&2)|(y>>31);ay,ax=y&0x7fffffff,x&0x7fffffff
 if not ay:return (0,0,0x40490fdb,0xc0490fdb)[quadrant]if quadrant&2 else y
 if not ax:return 0x3fc90fdb|(y&0x80000000)
 assert ax+218103808>=ay and (not(x&0x80000000)or ay+218103808>=ax),'Extreme atan2 ratios outside present reference'
 a=atan_ref(C.div(y,x)&0x7fffffff)
 return(a,a^0x80000000,C.sub(0x40490fdb,C.add(a,0x33bbbd2e)),C.add(C.add(a,0x33bbbd2e),0xc0490fdb))[quadrant]


def project(world,xyz,fallback):
 h=world.height(*xyz[:2]);return(*xyz[:2],xyz[2]if h is None and fallback else world.fallback_height_bits if h is None else h)


def route(ctx,ai,start,end,counts):
 nav=ctx['nav']
 if AI.segment(nav,start,end,counts)==C.ONE:return end
 _,index=AI.probe(nav,start[:2])
 if index is None:return end
 values=ai['path_values'];width=nav['width']
 def lower(current):
  yy,xx=divmod(current,width);candidates=[]
  for dx,dy in ctx['neighbors']:
   x,y=xx+dx,yy+dy
   if 0<=x<width and 0<=y<width:
    k=x+y*width
    if values[k]!=65535:candidates.append((values[k],k))
  if not candidates:return None
  cost=min(c[0]for c in candidates);choice=next(k for c,k in candidates if c==cost)
  return choice if values[current]==65535 or cost<values[current]else None
 def centre(k):
  y,x=divmod(k,width);return(C.add(nav['origin_xy_bits'][0],C.add(C.rounded(Fraction(x)),0x3f000000)),C.add(nav['origin_xy_bits'][1],C.add(C.rounded(Fraction(y)),0x3f000000)))
 if values[index]==65535:
  candidate=lower(index)
  if candidate is None:return end
  index=candidate
 selected=centre(index)
 if index!=ai['path']['start_index']:
  candidate=lower(index)
  for _ in range(40):
   if candidate is None:break
   xy=centre(candidate)
   if lt(0x41600000,AI.distance(start[:2],xy))or lt(AI.segment(nav,start,xy,counts),C.ONE):break
   selected=xy
   if candidate==ai['path']['start_index']:break
   candidate=lower(candidate)
 counts['flow_routes']+=1
 return(*selected,start[2])


def reserve(rows,n,width):
 if n==len(rows):rows.extend([[None]*width for _ in range(max(4,2*len(rows))-len(rows))])
 return rows[n]


def charge(ai,action,effects,deferred,counter,ctx,counts):
 i,raw=action;row=ai['rows'][i];now=ai['now'];origin=AI.position(row,now);target=project(ctx['world'],ai['player'],True)
 assert raw[37]==7 and u(raw)==100 and not any(raw[4:37]),'Actual declaration-only Charge source'
 yaw=atan2_ref(C.sub(target[1],origin[1]),C.sub(target[0],origin[0]));sine,cosine=AI.trig(yaw)
 length=C.add(AI.distance(origin,target),0x40c00000)
 planned=(C.add(origin[0],C.mul(cosine,length)),C.add(origin[1],C.mul(sine,length)),target[2])
 fraction=AI.segment(ctx['nav'],origin,planned,counts)
 if lt(fraction,C.ONE):
  t=mx(0,C.sub(fraction,C.div(0x3f000000,mx(0x3f000000,AI.distance(origin,planned)))))
  planned=tuple(C.add(a,C.mul(C.sub(b,a),t))for a,b in zip(origin,planned));counts['charge_clipped']+=1
 endpoint=project(ctx['world'],planned,True);distance=mx(0x40800000,AI.distance(origin,endpoint));duration=C.add(C.div(distance,0x42200000),C.ONE)
 stopped=project(ctx['world'],origin,True)
 put(row,100,mx(read(row,100),C.add(C.add(now,0x3fcccccd),0x3ecccccd)))
 for off in(316,328):row[off:off+12]=struct.pack('<3I',*stopped)
 put(row,340,now);put(row,344,0);until=mx(C.add(now,duration),read(row,408));put(row,408,until);put(row,348,until);put(row,352,mx(read(row,352),C.add(duration,0x3e99999a)))
 guid=read(row,112,8);ai['sequence']=(ai['sequence']+1)&C.M
 packets=[[221,(C.packguid(guid)+struct.pack('<4I',*stopped,ai['sequence'])+b'\4'+struct.pack('<4I3I',yaw,256,1,1,*stopped)).hex()],
          [305,(C.packguid(guid)*2+struct.pack('<IHIH',100,2,1000,0)).hex()]]
 counter=(counter+1)&C.M;n=effects['count'];effect=reserve(effects['storage'],n,120)
 for off,val in((0,0),(8,0),(40,2),(44,distance),(48,mn(mx(C.mul(read(row,312),0x3f99999a),0x40800000),0x40e00000)),(52,counter),(56,origin[0]),(60,origin[1]),(64,project(ctx['world'],origin,False)[2]),(68,yaw),(72,now),(76,C.add(now,C.ONE)),(80,0),(84,0),(88,C.add(read(row,296),read(row,296))),(92,0x7f800000)):put(effect,off,val)
 effect[24:40]=struct.pack('<QQ',guid,0);effect[96:119]=bytes(23);effects['count']+=1
 n=deferred['count'];entry=reserve(deferred['storage'],n,56);entry[:24]=struct.pack('<QI3I',guid,C.add(now,C.ONE),*endpoint);entry[49]=35;deferred['count']+=1
 counts['Charge']+=1;counts['effect120_produced']+=1;counts['deferred56_produced']+=1
 return counter,packets,dict(guid=str(guid),now_bits=now,yaw_bits=yaw,origin=list(origin),endpoint=list(endpoint),distance_bits=distance,stop_duration_bits=duration,raw40_hex=raw.hex())


def tick(ai,dt,special,timers,effects,deferred,counter,ctx,counts):
 now=ai['now'];player=ai['player'];motions=[];attacks=[];queued=[];aggro=[]
 if ai['path']is None:
  ai['path'],ai['path_values']=AI.breadth_first(ctx['nav'],player,ctx['neighbors']);ai['path_clock']=now;counts['BFS_maps']+=1;counts['BFS_values']+=len(ai['path_values'])
 else:assert AI.probe(ctx['nav'],player[:2])[1]==ai['path']['start_index']
 for index,row in enumerate(ai['rows']):
  assert read(row,0)==0 and all(read(row,o)==C.M for o in(40,244))
  if lt(now,read(row,408)):continue
  pos=AI.position(row,now);attackclock=C.sub(read(row,352),dt);put(row,352,attackclock);guid=read(row,112,8)
  if read(row,64)!=C.M:
   assert read(row,64)==3 and row[424]==1
   h=read(row,92);home=tuple(read(special[h],o)for o in(16,20,24))
   if row[108]==0:
    assert read(row,288)==read(row,292)
    if le(AI.distance(pos,home),0x40400000)and le(AI.distance(pos,player),0x41a00000):row[108]=1;aggro.append(index)
    else:
     assert le(AI.distance(pos,home),0x40000000),'This source remains at home'
     continue
   else:assert le(AI.distance(home,player),bits(97.5))
   definition=ctx['definitions'][(read(row,284)-5830904)//72];header,ability,records=ctx['guardian'][(read(row,284)-5830904)//72]
   assert read(row,104)==0
   ratio=C.div(read(row,288),mx(read(row,292),C.ONE))
   for phase in ctx['phases'][header]:assert not lt(ratio,u(phase,8))
   clocks=timers[str(guid)]['timers_bits']
   for j,r in enumerate(records):
    clocks[j]=C.sub(clocks[j],dt)
    if not le(clocks[j],0):continue
    tag=r[37];normalized=29 if tag<=2 else tag-3;concurrent=normalized<=31 and bool((1<<normalized)&0xa0180006)
    if not concurrent and (lt(now,read(row,100))or any(a[0]==index for a in queued)):continue
    clocks[j]=C.mul(u(r,40),0x3f333333 if lt(read(row,288),C.mul(read(row,292),0x3e99999a))else C.ONE)
    assert j==0 and tag==7;queued.append((index,r[:40]))
  if le(AI.distance(pos,player),read(row,308)):
   if lt(0,read(row,344))and lt(now,C.add(read(row,340),read(row,344))):
    for off in(316,328):row[off:off+12]=struct.pack('<3I',*pos)
    put(row,340,now);put(row,344,0);motions.append((guid,pos,pos,0))
   if le(attackclock,0)and le(read(row,412),now):
    put(row,352,read(row,304));weak=read(row,128)if lt(now,read(row,132))else read(row,136)if lt(now,read(row,140))else 0
    attacks.append((index,C.mul(read(row,296),C.sub(C.ONE,weak))))
   continue
  if lt(now,read(row,348)):continue
  angle=C.add(read(row,404),0x3e19999a);put(row,404,angle);sine,cosine=AI.trig(angle);radius=mx(C.mul(read(row,308),0x3f4ccccd),0x3fc00000)
  end=(C.add(player[0],C.mul(radius,cosine)),C.add(player[1],C.mul(radius,sine)),player[2]);distance=AI.distance(pos,end)
  if lt(0x41600000,distance):
   t=C.div(0x41600000,distance);end=(C.add(pos[0],C.mul(C.sub(end[0],pos[0]),t)),C.add(pos[1],C.mul(C.sub(end[1],pos[1]),t)),pos[2])
  end=route(ctx,ai,pos,end,counts);speed=read(row,300)
  if lt(now,read(row,124)):speed=C.mul(speed,C.sub(C.ONE,read(row,120)))
  if lt(now,read(row,412)):speed=C.mul(speed,0x3faccccd)
  duration=C.div(AI.distance(pos,end),mx(speed,0x3f000000))
  for off,xyz in((316,pos),(328,end)):row[off:off+12]=struct.pack('<3I',*xyz)
  put(row,340,now);put(row,344,duration);put(row,348,C.add(now,mn(mx(duration,0x3e800000),0x3f333333)));motions.append((guid,pos,end,duration))
 packets=[];charged=[]
 for guid,start,end,duration in motions:
  ai['sequence']=(ai['sequence']+1)&C.M;packets.append(AI.packet221(ctx['world'],guid,start,end,duration,ai['sequence'],counts))
 for index,amount in attacks:
  row=ai['rows'][index];guid=read(row,112,8);damage=C.mul(amount,C.sub(C.ONE,ai['derived']['1568']));shown=max(1,int(C.rational(damage)))
  packets.append([330,(struct.pack('<I',2)+C.packguid(guid)+C.packguid(0)+struct.pack('<I',shown)+b'\1'+struct.pack('<IfI6I',0,float(shown),shown,0,0,1,0,0,0)).hex()])
  assert C.rational(ai['hp'])>C.rational(damage)and all(ai['guards'][p]==0 for p in ai['guards'])
  ai['hp']=C.sub(ai['hp'],damage);ai['last']=now;ai['incoming']+=fp(damage);category='elite'if row[424]else'mob melee';ai['categories'][category]=ai['categories'].get(category,0.)+fp(damage)
  name=ctx['names'][(read(row,284)-5830904)//72]
  AI.I.append_ring(ai['history'],now,fp(damage),0.,fp(ai['hp']),ai['derived']['1536'],(name,'Melee','INV_Sword_04'),row[424],0)
  ai['fields'].update({'22':math.ceil(C.rational(ai['hp'])),'28':math.ceil(C.rational(ai['derived']['1536']))});counts['contacts']+=1
 for action in queued:
  counter,new,details=charge(ai,action,effects,deferred,counter,ctx,counts);packets.extend(new);charged.append(details)
 for index in aggro:
  row=ai['rows'][index];definition=ctx['definitions'][(read(row,284)-5830904)//72];hp,attack=S.scalars(now,definition,ctx);oldmax=read(row,292)
  if lt(oldmax,hp):put(row,292,hp);put(row,288,C.mul(hp,mn(mx(C.div(read(row,288),oldmax),0),C.ONE)))
  put(row,296,mx(read(row,296),attack));guid=read(row,112,8)
  packets.append([169,(struct.pack('<IBB',1,0,0)+C.packguid(guid)+b'\1'+struct.pack('<III',0x10400000,math.ceil(C.rational(read(row,288))),math.ceil(C.rational(read(row,292))))).hex()])
  name=ctx['names'][(read(row,284)-5830904)//72].encode();text=ctx['english'][ctx['engage']].encode()
  packets.append([150,(b'\x0c'+struct.pack('<IQI',0,guid,len(name)+1)+name+b'\0'+struct.pack('<QI',0,len(text)+1)+text+b'\0\0').hex()]);counts['aggro']+=1
 counts['925']+=1;counts['AI_packets']+=len(packets);counts['AI_packet_bytes']+=sum(len(v)//2 for op,v in packets)
 return counter,packets,charged


def dispatch_source(text):
 stack=[];blocks={};switch=None
 for line,s in enumerate(text.splitlines(),1):
  t=s.strip()
  if t.startswith(('block ','block\t','loop ','if '))or t in('block','loop','if'):stack.append(line)
  elif t=='end':
   if stack:blocks[stack.pop()]=line
  if 'br_table'in t and len(re.findall(r'\(;',t))>=30 and switch is None:
   depths=[int(n)for n in re.findall(r'(\d+) \(;',t)];switch=(line,depths,list(stack))
 assert switch is not None
 line,depths,stack=switch;raw=7;normalized=raw-3;selector=normalized-1;depth=depths[selector];opened=stack[-1-depth];ended=blocks[opened]
 assert(raw,normalized,selector,depth,opened,ended)==(7,4,3,23,235,5539)
 branch='\n'.join(text.splitlines()[ended:5761]);assert 'call 64899'in branch and 'i32.const 35'in branch and 'call 68224'not in branch and 'f32.const 0x1p+0 (;=1;)'in branch
 return dict(raw=raw,normalized=normalized,selector=selector,depth=depth,block_start=opened,block_end=ended,branch_start=ended+1,branch_end=5761)


def main():
 start=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();sys.stderr.write('start\n');sys.stderr.flush();assert sha(SOURCE)==WASM and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
 hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');runtime=load(BATCH/'runtime.json')
 assert len(hand['author_files'])==9 and comp['sources_before']==comp['sources_after']==prep['sources']
 authors=hand['author_files'];sources=comp['sources_before'];assert len(sources)==105 and sum(n.startswith('reconstruction/')for n in sources)==86
 for n,h in authors.items():assert sha(ROOT/n)==h
 for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
 assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(comp['source_import_edges'])==409
 for table in(comp['frozen'],prep['frozen']):
  for n,h in table.items():assert sha(BATCH/n)==h
 assert comp['phase']=='full'and comp['cases']==comp['completed_cases']==3 and comp['differences']==0 and prep['expected_before_original']and not prep['original_input_contains_expected']and not comp['forbidden_model_reads']and not load(BATCH/'expectation-read-audit.json')['forbidden']
 sys.stderr.write('metadata %.3f\n'%(time.monotonic()-start));sys.stderr.flush()
 ctx=S.Spawn.load_context();data=ctx['data'];raw=ctx['raw'];module=ctx['module'];zone=data(5871348,152)
 ctx.update(definitions=[data(5830904+72*j,72)for j in range(12)],zone136=u(zone,136),milestone=struct.unpack_from('<2I',data(u(zone,72),72),48),names={},guardian={},phases={})
 for index,header in((9,5899360),(10,5899388),(11,5899416)):
  definition=ctx['definitions'][index];np,n=struct.unpack_from('<II',definition,16);ctx['names'][index]=data(np,n).decode();h=data(header,28);ability,n=struct.unpack_from('<II',h);ctx['guardian'][index]=(header,ability,[data(ability+44*j,44)for j in range(n)]);p,n=struct.unpack_from('<II',h,16);ctx['phases'][header]=[data(p+52*j,52)for j in range(n)]
 ctx['names'][0]='Kobold Vermin';ep,en=struct.unpack('<II',data(5401532,8));ctx['english']=json.loads(data(ep,en));ctx['engage']=data(1594130,24).decode();assert ctx['english'][ctx['engage']]==ctx['engage']=='Who dares enter my lair?'
 private_raw=(BATCH/m['module_file']).read_bytes();private=parse_module(private_raw)
 for a,b in zip(module['sections'],private['sections'],strict=True):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
 assert private['exports']==module['exports']+[tuple(v)for v in m['added_exports']]and len(module['imports'])==882
 assert [(x['module'],x['name'],x['type_index'])for x in module['imports']]==[(x['module'],x['name'],x['type_index'])for x in m['original_imports']]
 sys.stderr.write('context %.3f\n'%(time.monotonic()-start));sys.stderr.flush()
 texts={};bindings={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as f:
  for idx,claim in m['functions'].items():
   a,z=module['bodies'][int(idx)];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(int(idx),)).fetchone();assert hi-lo<16*1024*1024;f.seek(lo);wat=f.read(hi-lo);binding=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());assert all(binding[k]==claim[k]for k in binding)and wat==(BATCH/'static'/f'{idx}.wat').read_bytes();texts[int(idx)]=wat.decode();bindings[idx]=binding
 assert len(bindings)==162
 sys.stderr.write('binding %.3f\n'%(time.monotonic()-start));sys.stderr.flush()
 proof=dispatch_source(texts[916]);assert all(x in texts[64899]for x in('i32.load offset=1828','i32.const 56','i64.store offset=44 align=4','i32.store offset=1828'))
 reviewer_extra={}
 if 35202 not in texts:
  with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as f:
   lo,hi=db.execute('select wat_start,wat_end from functions where idx=35202').fetchone();assert hi-lo<65536;f.seek(lo);extra=f.read(hi-lo)
  a,z=module['bodies'][35202];reviewer_extra['35202']=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(extra).hexdigest(),source='reviewer independently bounded current original;outsideauthor162directclosure')
  texts[35202]=extra.decode();(out/'35202-reviewer-extra.wat').write_bytes(extra)
 for n in(21112,62654,35067,64899,51773,16627,43076,35202,47161,30179,29237):assert n in texts
 constants={bits(float.fromhex(v))for v in re.findall(r'f32.const ([^ ]+)',texts[35202])if 'nan'not in v and 'inf'not in v}
 assert {0xbdda1247,0xbe4cca98,0x3d7cac25,0x3e11f50d,0x3eaaaaa9}<=constants
 #Bind the reused atan polynomial to actualcurrent35202 literals/tablebits.
 assert 'call 35202'in texts[43076]and 'i32.const 1065353216'in texts[43076]
 assert data(14426512,16)==struct.pack('<4I',0x3eed6338,0x3f490fda,0x3f7b985e,0x3fc90fda)and data(14426528,16)==struct.pack('<4I',0x31ac3769,0x33222168,0x33140fb4,0x33a22168)
 assert re.search(r'i32.const 35\s+i32.store8 offset=469',texts[916])and re.search(r'i32.const 2\s+i32.store offset=484',texts[916])
 for t in(m['guardian_trace'],):
  for key,claim in t['static_reads'].items():
   address,n=map(int,key.split(':'));assert hashlib.sha256(data(address,n)).hexdigest()==claim['sha256']
 assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
 counts=Counter();references=[]
 def cells(label,want,hx):
  b=bytes.fromhex(hx);assert len(want)==len(b)
  for off,(v,actual)in enumerate(zip(want,b,strict=True)):
   if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(actual)
   else:assert v==actual,(label,off,v,actual);counts[label+'_known']+=1
 def view(obs,p,ai,special,state,physical,effects,deferred,counter,label):
  assert obs['hp1440_bits']==ai['hp']and obs['player_fields']==ai['fields']and obs['movement_sequence2412']==ai['sequence']and obs['counter2356']==counter,(label,'numeric')
  assert obs['units']['capacity']==obs['units']['count']==8
  for i,(row,hx)in enumerate(zip(physical,obs['units']['storage'],strict=True)):cells(label+'NPC'+str(i),row,hx)
  for k,v in state.items():
   if v is not None:assert obs['special'][k]==v,(label,'special',k,v,obs['special'][k])
  for row,actual in zip(special,obs['special']['special40_storage'],strict=True):cells(label+'special',row,bytes(actual).hex())
  for key,owner,width in(('effects',effects,120),('deferred',deferred,56),('scheduled',dict(count=0,storage=[]),32)):
   got=obs[key];assert(got['capacity'],got['count'])==(len(owner['storage']),owner['count']),(label,key)
   for row,hx in zip(owner['storage'],got['storage'],strict=True):cells(key,row,hx)
  for key,want in dict(path=ai['path'],path_clock2372_bits=ai['path_clock'],incoming992_hex=struct.pack('>d',ai['incoming']).hex(),last_hit1652_bits=ai['last'],categories={k:struct.pack('>d',v).hex()for k,v in ai['categories'].items()}).items():assert obs['ai'][key]==want,(label,'AI',key,want,obs['ai'][key])
  history=AI.I.ring_projection(ai['history']);assert obs['ai']['history']['header']==history['header']and obs['ai']['history']['active']==history['active']
  for row,hx in zip(history['storage'],obs['ai']['history']['storage'],strict=True):cells('history',row,hx)
  p['g'].update(current_hp_bits=ai['hp'],player_fields=copy.deepcopy(ai['fields']),now_bits=ai['now']);assert obs['growth']==U.project(p)['growth'],(label,'growth')
 cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==3
 for case,A in zip(cases,actual,strict=True):
  sys.stderr.write('case%s init %.3f\n'%(case['id'],time.monotonic()-start));sys.stderr.flush()
  full,p,s,ai,L,physical,count=F.initial_reference(case,ctx);opening=full['projection'];assert A['id']==case['id']and A['opening']['packets']==opening['packets']and A['new_Game_pointer']!=A['old_snapshot_Game_not_target']==14685248
  cells('openingGame',full['known_Game2592'],A['opening']['raw_game2592_hex'])
  special=copy.deepcopy(opening['special']['storage']);state=dict(selected392=0,target396=None,announced2565=0,stamp2392_bits=0,navigation2564=1,protection2576=0,timers=[])
  assert case['spawn_now_bits']==bits(20.)
  physical,count,special,state,spawn_packets=S.update(p,s,physical,count,special,state,bits(20.),ctx,counts);assert spawn_packets==A['spawn_packets']and count==8
  ai.update(rows=physical,now=bits(20.),hp=p['g']['current_hp_bits'],fields=copy.deepcopy(p['g']['player_fields']),categories={});effects=dict(count=0,storage=[]);deferred=dict(count=0,storage=[]);counter=0;p['g']['now_bits']=bits(20.);view(A['after_spawn'],p,ai,special,state,physical,effects,deferred,counter,'after_spawn')
  if case['home_index']is None:xyz=tuple(opening['player_xyz'])
  else:h=special[case['home_index']];xyz=(C.add(read(h,16),bits(15.)),read(h,20),read(h,24))
  timers={t['guid']:t for t in state['timers']};previous=A['after_spawn'];traces=[];prior_now=bits(20.)
  for j,(step,obs)in enumerate(zip(case['steps'],A['frames'],strict=True)):
   if j%10==0:sys.stderr.write('case%s frame%s %.3f\n'%(case['id'],j,time.monotonic()-start));sys.stderr.flush()
   assert step['dt_bits']==0x3dcccccd and step['now_bits']==C.add(prior_now,step['dt_bits'])and step['player_xyz']==list(xyz)
   ai['now']=step['now_bits'];ai['player']=xyz;p['player']=xyz;p['g']['now_bits']=ai['now'];p['scalar']['2352']=ai['now']
   before=bytearray.fromhex(previous['raw_game2592_hex']);put(before,2352,ai['now']);struct.pack_into('<3I',before,1416,*xyz);assert before.hex()==obs['before']['raw_game2592_hex'];counts['inputGame_inheritance_bytes']+=2592
   view(obs['before'],p,ai,special,state,physical,effects,deferred,counter,'before'+str(j));old=copy.deepcopy(physical)
   counter,packets,charged=tick(ai,step['dt_bits'],special,timers,effects,deferred,counter,ctx,counts)
   view(obs['after'],p,ai,special,state,physical,effects,deferred,counter,'after'+str(j));assert packets==obs['packets'],(case['id'],j,'complete packets',packets,obs['packets'])
   for row,hx,oldhx in zip(physical,obs['after']['units']['storage'],obs['before']['units']['storage'],strict=True):
    prior=bytes.fromhex(oldhx);post=bytes.fromhex(hx)
    for k,v in enumerate(row):
     if v is None:assert prior[k]==post[k];counts['NPC_None_copy']+=1
   for key in('pickups','windows','boundaries','auxiliary','claims'):assert obs['before']['background'][key]==obs['after']['background'][key]==A['opening']['background'][key]
   assert obs['before']['live']==obs['after']['live']and obs['before']['aura']==obs['after']['aura']and obs['before']['special']['special40_storage']==obs['after']['special']['special40_storage']
   allowed=set()
   for off,n in((968,16),(992,8),(1112,12),(1440,4),(1652,4),(1808,36),(1880,12),(2356,4),(2368,8),(2412,4),(2476,12)):allowed.update(range(off,off+n))
   prior=bytes.fromhex(obs['before']['raw_game2592_hex']);post=bytes.fromhex(obs['after']['raw_game2592_hex'])
   assert all(a==b for k,(a,b)in enumerate(zip(prior,post,strict=True))if k not in allowed);counts['unowned_Game_bytes']+=2592-len(allowed)
   cap=u(prior,1880);required=u(post,1888)
   while cap<required:cap=max(4,cap*2)
   assert cap==u(post,1880)
   for (opcode,hx),detail in zip(packets,obs['packet_details'],strict=True):
    cap=32
    while cap<len(hx)//2:cap*=2
    assert detail==dict(opcode=opcode,length=len(hx)//2,capacity=cap)
   traces.append(dict(index=j,now_bits=ai['now'],packets=packets,charged=charged));previous=obs['after'];prior_now=ai['now']
  assert case['consume_now_bits']==C.add(prior_now,0x3dcccccd);ai['now']=case['consume_now_bits'];p['g']['now_bits']=ai['now']
  view(A['consumer']['before'],p,ai,special,state,physical,effects,deferred,counter,'consumerbefore');view(A['consumer']['after'],p,ai,special,state,physical,effects,deferred,counter,'consumerafter')
  assert not A['consumer']['packets']and A['consumer']['before']==A['consumer']['after'];counts['empty38553']+=1
  assert A['account368_before_hex']==A['account368_after_hex']and A['profile376_before_hex']==A['profile376_after_hex']and A['selection_canaries']==['c3'*16,'d7'*16]and A['stack_after']==1048576
  assert len(A['timer_pointer_observations'])==(2*len(case['steps'])+3)*4 and all(x['observed_only']for x in A['timer_pointer_observations']);counts['retained_NPC']+=count
  references.append(dict(case=case,frames=traces,effects=effects,deferred=deferred,scheduled_count=0));counts['cases']+=1
 assert counts['cases']==3 and counts['925']==96 and counts['Charge']==2 and counts['contacts']==4 and counts['aggro']==2 and counts['effect120_produced']==counts['deferred56_produced']==2 and counts['AI_packets']==80 and counts['AI_packet_bytes']==3766 and counts['BFS_maps']==3
 assert runtime==comp['runtime']and runtime['fresh_instances']==3 and runtime['full_calls']['925']==96 and runtime['full_calls']['38553']==3 and sum(runtime['full_calls'].values())==111 and all(runtime['full_calls'][n]==3 for n in('2945','1600','1108','2372'))
 assert len(runtime['target_and_setup_returns'])==111 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['target_and_setup_returns'])and runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None
 assert all(x['unchanged']and x['ranges']==2318 for x in runtime['world_source_checks'])and runtime['peak_memory_bytes']<=runtime['memory_cap_bytes']==268435456 and runtime['output_bytes']==(BATCH/'actual.jsonl').stat().st_size
 term=load(BATCH/'owned-terminal.json');assert term==hand['process']==comp['process']and term['exit_code']==0 and term['pid_missing']and term['pgid_missing']
 helpers={str(Path(v.__file__).resolve().relative_to(ROOT)):sha(Path(v.__file__))for v in list(sys.modules.values())if getattr(v,'__file__',None)and Path(v.__file__).resolve().parent==ROOT/'scripts'and Path(v.__file__).name.startswith('review_')}
 assert not AUDIT
 for n,h in authors.items():assert sha(ROOT/n)==h
 for n,h in sources.items():assert sha(ROOT/n)==h
 save(out/'independent-reference.json',references)
 result=dict(accepted=True,scope='current139explicit2372first20ssetup→mixed8NPC full92596/realraw7Charge120+56→threeempty38553',author_handoff_sha256=HAND,comparison_sha256=COMP,author_files=authors,reviewer_script_sha256=sha(Path(__file__)),helper_sha256=helpers,current_body_bindings=bindings,reviewer_extra_body_bindings=reviewer_extra,dispatch_independently_parsed=proof,source_counts=dict(files=105,production=86,edges=409,bodies=162),counts=dict(counts),original_process=term,reference_sha256=sha(out/'independent-reference.json'),original_executions=0,author_program_executions=0,author_expected_values_read=False,author_expected_hash_only=True,read_audit=dict(AUDIT),own_static_aggro_assistance='evidence/guardian-aggro139-static-20261102T171254.378340Z/notes.json',full884_frames=0,complete_games=0,seconds=time.monotonic()-start,limits=['Explicit20sclock2372setup/playeractualhome+15;notnatural20s/full884.', 'Currentraw7→normalized4→selector3/depth23 branch only. Two120and56tag35producers;scheduled32empty and38553controls only. No920/deferredconsumer/Chargearrivaldamage.', 'OtherGuardianskills/HPphase/leash/death andwholeheap/pointerallocation remainPending.', 'Independentpreviousreviewhelpers reusedasnumeric algorithmsandcurrentrawdata rebound;no priorruntime acceptance transferred.','Aggro payloadstaticnoteswereauthoredbythisreviewerbeforethisbatch anddeclaredhere;freshactualwholepacketcomparison independentlyrecomputed,notauthor expected reuse.'])
 save(out/'review.json',result);print(json.dumps(dict(accepted=True,counts=dict(counts),seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
