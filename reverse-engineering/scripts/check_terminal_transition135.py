#!/usr/bin/env python3
"""Expected-first true49037 from real1560, including complete packets/notification."""
from collections import Counter
from dataclasses import asdict,replace
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build,parse_source
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
sys.dont_write_bytecode=True
FILES=('scripts/check_terminal_transition135.py','scripts/run_terminal_transition135_oracle.mjs','scripts/source_closure135.py','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/full135_host.mjs')+core_sources(ROOT,'terminal_transition135.py','initial_state135.py')
IMPORT_SHA={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.terminal_transition135 import TerminalInput135,UnknownTerminalTransition135,transition_terminal,speed_packet226,COUNTER_KEYS,CLASSES,RACES,ZONES
from core_spec.initial_state135 import ConstructorInput135,initialize_empty_profile
from core_spec.initial_state135_data import ZONE_ENTRIES
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
FUNCTIONS=(1560,49037,17119,17217,16340,54810,1938,11735,52241,44448,15916,45845,28732,54802,19964,29631,23181,1512,48066)


def identities():
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;types,imports,decl,bodies,_=parse_source(raw);rows=[]
 for idx in FUNCTIONS:
  a,b=bodies[idx];p,r=types[decl[idx-len(imports)]];rows.append(dict(index=idx,parameters_hex=p.hex(),results_hex=r.hex(),body_sha256=hashlib.sha256(raw[a:b]).hexdigest(),body_start=a,body_end=b))
 assert next(r for r in rows if r['index']==49037)['body_sha256']=='e972d7925d7cdeb7b3fa81cae73ff0ace5e819bb7c0277259669bcae9062efc7'
 return rows


def f64bits(value):return struct.unpack('<Q',struct.pack('<d',value))[0]
def row(kind,guid=1,marker=0,start=9,duration=2,origin=(1,2,3),destination=(5,8,11),tail=0xa5):
 stride,go,ao,bo,so,do=(424,112,316,328,340,344)if kind=='units'else(112,16,32,44,56,60)if kind=='auxiliary'else(88,24,44,56,68,72)
 raw=bytearray([tail]*stride)
 if kind=='units':struct.pack_into('<I',raw,0,marker)
 struct.pack_into('<Q',raw,go,guid)
 for offset,xyz in((ao,origin),(bo,destination)):
  struct.pack_into('<3I',raw,offset,*(f.from_float(x)for x in xyz))
 struct.pack_into('<2I',raw,so,f.from_float(start),f.from_float(duration))
 return raw.hex()


def model_state(c):
 x=dict(c['model_input'])
 for key in('units_storage','auxiliary_storage','claims_storage'):x[key]=tuple(x[key])
 x['counters']=tuple(tuple(v)for v in x['counters'])
 for key in('source_id','damage984_f64_bits','taken992_f64_bits'):x[key]=int(x[key])
 return TerminalInput135(**x)


def delta(old,new):
 out=[]
 for offset,a,b in((1644,old.action_sequence1644,new.action_sequence1644),(2412,old.movement_sequence2412,new.movement_sequence2412),(1880,old.packet_capacity,new.packet_capacity),(1888,old.packet_count,new.packet_count),(1892,old.notification_vector_capacity,new.notification_vector_capacity),(1900,old.notification_count,new.notification_count)):
  aa=struct.pack('<I',a);bb=struct.pack('<I',b)
  out.extend([offset+j,bb[j]]for j in range(4)if aa[j]!=bb[j])
 if old.phase2587!=new.phase2587:out.append([2587,new.phase2587])
 if old.packet_capacity!=new.packet_capacity:out.append([1884,'heap_pointer'])
 if old.notification_vector_capacity!=new.notification_vector_capacity:out.append([1896,'heap_pointer'])
 return sorted(out)


def expected(c):
 s=model_state(c);initial=initialize_empty_profile(ConstructorInput135(**{k:int(v)if k in('seed_u64','object_id_u64')else v for k,v in c['input'].items()}));packets=list(c['constructor_expected']['packets']);notifications=[];stages=[]
 for _ in range(c['repeat']):
  old=s;r=transition_terminal(s);s=r.state;packets.extend(dict(opcode=p[0],capacity=p[1],payload_hex=p[2])for p in r.packets);notifications.extend(dict(capacity=n[0],payload_hex=n[1])for n in r.notifications)
  stages.append(dict(phase=s.phase2587,action_sequence=s.action_sequence1644,movement_sequence=s.movement_sequence2412,vectors={name:dict(count=getattr(s,name+'_count'),storage=list(getattr(s,name+'_storage')))for name in('units','auxiliary','claims')},packets=list(packets),notifications=list(notifications),rng_words=list(initial.level.rng_words),spawn_counter=initial.spawn_counter,game_changed_bytes=delta(old,s)))
 return stages


def corpus(pilot=False):
 rows=[];b=f.from_float
 def add(group,cls=8,race=1,zone=0,hero='Hero',units=(),auxiliary=(),claims=(),now=10,height=7,flat=True,source=42,action=17,movement=31,field400=1,phase=1,endless=0,left=0,counters=None,damage=0,taken=0,repeat=2):
  vals={o:0 for o,_ in COUNTER_KEYS};vals[1432]=1;vals.update(counters or{})
  def backing(records,stride):return tuple(records)+((bytes([0x5a])*stride).hex(),)*(16-len(records))if records else()
  initial=initialize_empty_profile(ConstructorInput135(cls,race,zone,1,source,b(height)));speed=initial.level.stats.previous_speed_bits
  prefix=[]
  if f.to_float(f.sub(speed,0x40e00000)&0x7fffffff)>f.to_float(0x3c23d70a):
   packet=speed_packet226(source,1,speed);prefix=[dict(opcode=packet[0],capacity=packet[1],payload_hex=packet[2])]
  s=TerminalInput135(field400,phase,endless,b(now),action,movement,source,backing(units,424),len(units),backing(auxiliary,112),len(auxiliary),backing(claims,88),len(claims),4 if prefix else 0,len(prefix),0,0,tuple(vals.items()),f64bits(damage),f64bits(taken),cls,race,zone,hero,left,b(height),flat,True,True,'english_fallback')
  raw=asdict(s)
  for key in('source_id','damage984_f64_bits','taken992_f64_bits'):raw[key]=str(raw[key])
  c=dict(id=len(rows),group=group,input=dict(class_byte=cls,race_byte=race,region_index=zone,object_id_u64=str(source),seed_u64='1',flat_height_bits=b(height)),region_id=ZONE_ENTRIES[zone][0],hero=hero,flat_height_enabled=flat,
   words={str(k):v for k,v in {400:field400,2352:b(now),1644:action,2412:movement,**vals}.items()},bytes={'2587':phase,'2568':endless,'2567':left},doubles={'984':str(f64bits(damage)),'992':str(f64bits(taken))},
   units=list(s.units_storage),auxiliary=list(s.auxiliary_storage),claims=list(s.claims_storage),counts=dict(units=len(units),auxiliary=len(auxiliary),claims=len(claims)),repeat=repeat,model_input=raw,constructor_expected=dict(packet_capacity=s.packet_capacity,packet_count=s.packet_count,packets=prefix))
  c['expected']=expected(c);rows.append(c)
 add('pilot-real-constructor-empty-terminal',now=12.5)
 add('pilot-three-producers-order-and-unwritten-bytes',units=(row('units',3),),auxiliary=(row('auxiliary',5),),claims=(row('claims',7),))
 add('pilot-nonflat-fallback-and-control-UTF8',cls=11,race=8,zone=11,hero='中文"\\\n\t\r\x00😀',flat=False,units=(row('units'),),action=0xffffffff,movement=0xffffffff)
 if pilot:return json.loads(json.dumps(rows,ensure_ascii=False,allow_nan=False))
 for cls in CLASSES:
  for race in RACES:add('all-class-race-labels',cls=cls,race=race,hero='勇者',left=race%2,now=12.5)
 for zone in range(12):add('all-real-zone-labels',zone=zone,now=1.5,units=(row('units',zone+1),))
 for kind in('units','auxiliary','claims'):
  for start in(8,9,10,11):
   for duration in(-1,0,.1,1,2):
    for flat in(False,True):
     add('three-source-stop-predicates-and-height',flat=flat,**{kind:(row(kind,start=start,duration=duration),)})
 for marker in(0,1,2,3,0xffffffff):add('NPC-exact-marker-zero',units=(row('units',marker=marker),),flat=False)
 for guid in(0,1,1<<8,1<<56,0xffffffffffffffff):
  add('packed-GUID-zero-endian-allbytes',units=(row('units',guid),),auxiliary=(row('auxiliary',guid),),claims=(row('claims',guid),),source=guid,movement=0xfffffffe,action=0xffffffff)
 for size in(2,3,4,7,15):
  add('stable-stop-order-duplicates-and-vector-growth',units=tuple(row('units',j%2,start=9,duration=2,tail=17+j)for j in range(size)),auxiliary=tuple(row('auxiliary',j%2,tail=33+j)for j in range(size)),claims=tuple(row('claims',j%2,tail=65+j)for j in range(size)))
 for text in('','中文','😀','"\\\n\t\r\b\f\x00\x01\x1f','a'*1024,'x\u2028\u2029z'):
  add('full-UTF8-and-control-escaping-capacity',hero=text)
 for n in(-float('inf'),-1.5,-0.0,.0005,.0015,.0625,.125,.9999,12.5,1234.5678,1e15,1e20,float('inf'),float('nan')):
  add('number52241-integer-threshold-fixed3-nonfinite',now=n,damage=n,taken=-n,left=2)
 for n in(0,1,255,256,0xffffffff):add('unsigned32-complete-stat-counters',counters={o:n for o,_ in COUNTER_KEYS},damage=n+.25,taken=-(n+.5))
 for f400 in(0,1,0xffffffff):
  for ph in(0,1,2,3,4,5,255):
   for end in(0,1,2,3,255):add('false-and-true-terminal-predicate',field400=f400,phase=ph,endless=end,repeat=2)
 rng=random.Random(0x4903717119)
 for k in range(64):
  def rs(kind):return tuple(row(kind,rng.getrandbits(64),marker=rng.choice((0,0,1,2)),start=rng.choice((8,9,10,11)),duration=rng.choice((-1,0,.5,1,2)),origin=tuple(rng.uniform(-20,20)for _ in range(3)),destination=tuple(rng.uniform(-20,20)for _ in range(3)),tail=rng.randrange(256))for _ in range(rng.randrange(0,8)))
  add('seeded-mixed-producer-order',cls=rng.choice(tuple(CLASSES)),race=rng.choice(tuple(RACES)),zone=rng.randrange(12),hero='角色'+str(k),units=rs('units'),auxiliary=rs('auxiliary'),claims=rs('claims'),now=rng.choice((9.9,10,11)),flat=bool(k%2),height=rng.uniform(-10,10),action=rng.getrandbits(32),movement=rng.getrandbits(32),source=rng.getrandbits(64),left=rng.randrange(256),counters={o:rng.randrange(1000)for o,_ in COUNTER_KEYS},damage=rng.uniform(-100,100),taken=rng.uniform(-100,100))
 return json.loads(json.dumps(rows,ensure_ascii=False,allow_nan=False))


def negatives():
 c=corpus(True)[1];s=model_state(c);out=[]
 for name,change in(('missing-localization',dict(localization_profile=None)),('unknown-localization',dict(localization_profile='zh')),('terrain-not-proven-absent',dict(terrain_grid_absent=False)),('collision-not-proven-absent',dict(collision_grid_absent=False))):
  try:transition_terminal(replace(s,**change))
  except UnknownTerminalTransition135 as e:out.append(dict(case=name,rejected=True,reason=str(e)))
  else:raise AssertionError(name)
 raw=bytearray.fromhex(s.claims_storage[0]);struct.pack_into('<I',raw,72,0x7fc01234)
 try:transition_terminal(replace(s,claims_storage=(raw.hex(),)+s.claims_storage[1:]))
 except UnknownTerminalTransition135 as e:out.append(dict(case='processed-NaN-duration',rejected=True,reason=str(e)))
 else:raise AssertionError('Nonfinite processed motion accepted')
 return out


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_SHA
 body=identities();rejected=negatives();cases=corpus(args.phase=='pilot');out,manifest=build(['initial_game','terminal_tick'])
 for name,h in before.items():
  p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 fixture=out/'terminal-transition135-fixtures.json';fixture.write_text(json.dumps(cases,ensure_ascii=False,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
 assert sha(RUNTIME)==RUNTIME_SHA;fixed={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])};results=out/'terminal-transition135-results.jsonl';err=out/'terminal-transition135-stderr.log';cmd=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_terminal_transition135_oracle.mjs'),str(out),str(fixture)];started=time.monotonic()
 with results.open('w')as stream,err.open('w')as errors:
  child=subprocess.Popen(cmd,stdout=stream,stderr=errors,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned terminal transition deadline')
 if code:raise RuntimeError(f'Terminal original failed:{out}')
 actual=[json.loads(x)for x in results.read_text().splitlines()];assert[x['id']for x in actual]==list(range(len(cases)));failures=[]
 for c,a in zip(cases,actual):
  reduced=[{k:v for k,v in stage.items()if k!='raw_g2592_hex'}for stage in a['stages']]
  if reduced!=c['expected']:failures.append(dict(case=c['id'],group=c['group'],expected=c['expected'],actual=reduced))
 after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and fixed=={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
 for name,value in(('terminal-transition135-mismatches.json',failures),('terminal-transition135-rejections.json',rejected)):(out/name).write_text(json.dumps(value,indent=2)+'\n')
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),stages=sum(c['repeat']for c in cases),mismatch_cases=len(failures),source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,manifest_sha256=sha(out/'manifest.json'),module_sha256=manifest['module_sha256'],body_guards=body,groups=dict(Counter(c['group']for c in cases)),expected_before_original=True,production_freeze_before_import=True,rejected_cases=len(rejected),artifacts={p.name:sha(p)for p in(fixture,results,err,out/'terminal-transition135-runtime.json',out/'terminal-transition135-mismatches.json',out/'terminal-transition135-rejections.json')},runtime=json.loads((out/'terminal-transition135-runtime.json').read_text()),process=dict(command=cmd,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-started),limitations=['True49037 with full three movement-stop consumers,complete221/232 payloads/capacities and1938victory notification including exactcapacity; default Englishfallback labels only.','Actual1560 constructs state; only declared control,summaryandvector fixtures are patched; original empty sourcecounts are assertedbeforepatch and never supplied asunverifiedabsence.','Processed moving geometry requires explicit absentterrain/collision and finite words; genuine terrainadapter andlocalized notifications remainunknown.','All2592 gamebytes compared aschanges, only knownpacket/notification heapaddresswords normalized; physicalraw preserved.','No appstart,account/world producer,1089 orfull880 completion isclaimed.'])
 (out/'terminal-transition135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_cases=len(failures),first_ids=[x['case']for x in failures[:12]])))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
