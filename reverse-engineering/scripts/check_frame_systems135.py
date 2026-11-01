#!/usr/bin/env python3
"""Expected-first complete main-tail entry tests, with explicit partial scope."""
from collections import Counter
from dataclasses import asdict
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build,parse_source
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
sys.dont_write_bytecode=True
FILES=('scripts/check_frame_systems135.py','scripts/run_frame_systems135_oracle.mjs','scripts/source_closure135.py','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/full135_host.mjs')+core_sources(ROOT,'frame_systems135.py')
IMPORT_SHA={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.frame_systems135 import guard_owned_execution975,tick_scheduled_spells38007,tick_secondary_areas2602,guard_claim_tick2573,guard_terminal_tick49037,UnresolvedFrameSystem135
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
ROLES=('owned_effect_tick','deadline_tick','secondary_hits','claim_tick','terminal_tick')
BODY={975:('7f7d','11ffc7a65f7f5703fa3bacca09f3a4e2614b610f74bc387e5e28ad6c3a6cdb7c'),38007:('7f','970c6290bedabc686aa99221938e0fecb504442cb304bc808f9fad371808cd2b'),2602:('7f','badd383731d42ec76e01ba1d5b28e1da341a8a253767126101dec27b50d76b11'),2573:('7f','1d896b573277b55fa03a9fbeef1ae5e61c3e3997aea5fca6fc836abaaab89139'),49037:('7f','e972d7925d7cdeb7b3fa81cae73ff0ace5e819bb7c0277259669bcae9062efc7')}


def bodies_guard():
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;types,imports,decl,bodies,_=parse_source(raw);out=[]
 for idx,(params,expected)in BODY.items():
  a,b=bodies[idx];p,r=types[decl[idx-len(imports)]];assert(p.hex(),r.hex(),hashlib.sha256(raw[a:b]).hexdigest())==(params,'',expected)
  out.append(dict(index=idx,parameters_hex=params,results_hex='',body_sha256=expected,body_start=a,body_end=b))
 return out


def record(stride,guid=1,expiry=10,tick=20,interval=1,definition=0xa5debabe,tail=0xa5):
 raw=bytearray([tail]*stride)
 if stride==32:
  struct.pack_into('<QII3I',raw,0,guid&0xffffffffffffffff,f.from_float(expiry),0x12345678,0x80000000,0x7fc01234,0x41480000)
 elif stride==112:
  struct.pack_into('<I',raw,0,definition);struct.pack_into('<Q',raw,80,guid)
  struct.pack_into('<III',raw,100,f.from_float(expiry),f.from_float(tick),f.from_float(interval))
 return raw.hex()


def expected(c):
 storage=tuple(c['storage']);count=c['count'];packet_count=0;stages=[]
 for op in c['ops']:
  packets=();trap=False;changes=[];old_count=count
  if c['kind']=='owned':assert guard_owned_execution975(tuple(c['owned']),{int(k):v for k,v in c['definitions'].items()},op['dt_bits'])==tuple(c['owned'])
  elif c['kind']=='deadline':
   result=tick_scheduled_spells38007(storage,count,op['now_bits']);storage,count,packets=result.storage,result.count,result.packets
  elif c['kind']=='secondary':
   result=tick_secondary_areas2602(storage,count,op['now_bits']);storage,count,packets=result.storage,result.count,result.packets
   assert result.status in('secondary_expiry_idle_complete','trap_null_secondary_definition_after_pop')
   trap=result.status.startswith('trap_')
  elif c['kind']=='claim':
   result=guard_claim_tick2573(storage,count,c['phase']);storage,count=result.storage,result.count
  elif c['kind']=='terminal':assert guard_terminal_tick49037(c['field400'],c['phase'],c['endless'])==c['phase']
  else:raise AssertionError(c['kind'])
  if count!=old_count:changes.append([1840 if c['kind']=='deadline'else 1864 if c['kind']=='secondary'else 2116,count])
  if packets:packet_count+=len(packets);changes.append([1888,packet_count])
  stages.append(dict(count=count,storage=list(storage),owned=c['owned'],packets=[list(x)for x in packets],game_changes=sorted(changes),entry_trap=trap))
  if trap:break
 return stages


def corpus(pilot=False):
 rows=[];b=f.from_float
 def add(kind,group,records=(),count=None,ops=None,phase=1,endless=0,field400=0,owned=(),definitions=None,stride=None):
  stride=stride or(32 if kind in('owned','deadline','terminal')else 112 if kind=='secondary'else 88)
  storage=tuple(records)+((bytes([0x5a])*stride).hex(),)*(16-len(records));assert len(storage)==16
  c=dict(id=len(rows),kind=kind,group=group,stride=stride,storage=list(storage),count=len(records)if count is None else count,phase=phase,endless=endless,field400=field400,owned=list(owned),definitions=definitions or{},ops=ops or[dict(now_bits=b(n),dt_bits=b(.1))for n in(9.9,10,11,15)])
  c['expected']=expected(c);rows.append(c)
 add('deadline','pilot-one-fullpayload',[record(32,guid=0x123456789abcdef0)])
 add('secondary','pilot-last-expiry-170',[record(112)])
 add('secondary','pilot-null-after-pop-trap',[record(112,definition=0)])
 add('owned','pilot-empty-owned');add('claim','pilot-empty-claims');add('terminal','pilot-field400zero')
 if pilot:return rows
 for tag in range(256):
  if tag==11:continue
  definition=bytearray([0xa5]*88);definition[84]=tag;owned=bytearray([0x3c]*80);struct.pack_into('<I',owned,0,0x11110000+tag)
  add('owned','all255-nonexecution11-byte-tags',owned=(owned.hex(),),definitions={str(0x11110000+tag):definition.hex()},ops=[dict(now_bits=0x7fc01234,dt_bits=0x7fc01234)])
 for size in(0,1,2,7,16):
  for guid in(0,1,0x100,0x102030405060708,0xffffffffffffffff):
   add('deadline','full-guid-and-stable-compaction',tuple(record(32,guid+j,expiry=9+j%3,tail=17+j)for j in range(size)))
 for due in(-float('inf'),-1,0,9.9,10,10.0001,11,float('inf'),float('nan')):
  for now in(9.9,10,11,float('nan')):
   add('deadline','ordered-NaN-infinite-due', (record(32,expiry=due),),ops=[dict(now_bits=b(now),dt_bits=0)])
 for expiry in(-float('inf'),0,9.9,10,10.0001,11,float('inf'),float('nan')):
  for guid in(0,1,0xffffffffffffffff):
   for definition in(0,1,0xffffffff):
    add('secondary','expiry-guid-null-definition-before-packet',(record(112,guid=guid,expiry=expiry,tick=float('inf'),definition=definition),),ops=[dict(now_bits=b(n),dt_bits=0)for n in(10,11)])
 for count in(2,3,7,16):
  add('secondary','successive-expiry-full112-backing',tuple(record(112,guid=j+1,expiry=10 if j%2==0 else 12,tail=33+j)for j in range(count)))
  add('secondary','null-in-middle-post-compaction-trap',tuple(record(112,guid=j+1,expiry=10,definition=0 if j==count//2 else 1,tail=65+j)for j in range(count)))
 for due in(11,float('inf'),float('nan')):
  add('secondary','nonempty-live-not-due',(record(112,expiry=100,tick=due),),ops=[dict(now_bits=b(n),dt_bits=0)for n in(9,10)])
 for phase in(0,1,2,3,4,5,255):
  for count in(0,1,7):
   if phase==1 and count:continue
   add('claim','claim-phase-and-empty-gates',tuple((bytes([11+j])*88).hex()for j in range(count)),phase=phase)
 for field400 in(0,1,0xffffffff):
  for phase in(0,1,2,3,4,5,255):
   for endless in(0,1,2,3,255):
    if field400 and phase==1 and not endless&1:continue
    add('terminal','terminal-field-phase-and-bit0-gates',phase=phase,endless=endless,field400=field400,ops=[dict(now_bits=b(10),dt_bits=0)])
 rng=random.Random(0x975380072602)
 for k in range(48):
  records=[]
  for j in range(rng.randrange(0,16)):
   raw=bytearray(rng.randbytes(32));struct.pack_into('<Q',raw,0,rng.getrandbits(64));struct.pack_into('<I',raw,8,b(rng.choice((9,10,11,float('nan')))));records.append(raw.hex())
  add('deadline','seeded-opaque32-row-preservation',records)
 return json.loads(json.dumps(rows,allow_nan=False))


def negatives():
 baddef=bytearray(88);baddef[84]=11;owned=bytearray(80);struct.pack_into('<I',owned,0,7);rows=[]
 for name,call in(
  ('execution11',lambda:guard_owned_execution975((owned.hex(),),{7:baddef.hex()},0)),
  ('unknown-definition',lambda:guard_owned_execution975((owned.hex(),),{},0)),
  ('unknown-owned-vector',lambda:guard_owned_execution975(None,{},0)),
  ('unknown32backing',lambda:tick_scheduled_spells38007(None,0,0)),
  ('unknown112backing',lambda:tick_secondary_areas2602(None,0,0)),
  ('active-prefix-overflow',lambda:tick_scheduled_spells38007((),1,0)),
  ('short-physical32',lambda:tick_scheduled_spells38007(('00',),1,0)),
  ('running-nonempty-claims',lambda:guard_claim_tick2573(((bytes(88)).hex(),),1,1)),
  ('unknown-claims',lambda:guard_claim_tick2573(None,0,1)),
  ('terminal-true-path',lambda:guard_terminal_tick49037(1,1,0)),
  ('unknown-terminal-scalar',lambda:guard_terminal_tick49037(None,1,0))):
  try:call()
  except(ValueError,TypeError,UnresolvedFrameSystem135)as e:rows.append(dict(case=name,rejected=True,reason=str(e)))
  else:raise AssertionError(name)
 r=tick_secondary_areas2602((record(112,expiry=100,tick=10,interval=2),),1,f.from_float(10))
 assert r.status=='pending_secondary_due_effect'and struct.unpack_from('<I',bytes.fromhex(r.storage[0]),104)[0]==f.from_float(12)
 rows.append(dict(case='secondary-active-due',rejected_as_complete=True,status=r.status,preserved_partial104=f.from_float(12)))
 return rows


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_SHA
 identities=bodies_guard();rejected=negatives();cases=corpus(args.phase=='pilot');out,manifest=build(ROLES);snap=out/'source-snapshot'
 for n,h in before.items():
  q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
 fixture=out/'frame-systems135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
 assert sha(RUNTIME)==RUNTIME_SHA;fixed={q.name:sha(q)for q in(fixture,out/'manifest.json',out/manifest['module_file'])}
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_frame_systems135_oracle.mjs'),str(out),str(fixture)];start=time.monotonic();results=out/'frame-systems135-results.jsonl';stderr=out/'frame-systems135-stderr.log'
 with results.open('w')as stdout,stderr.open('w')as err:
  child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned frame system deadline')
 if code:raise RuntimeError(f'Original frame systems failed:{out}')
 actual=[json.loads(x)for x in results.read_text().splitlines()];assert[x['id']for x in actual]==list(range(len(cases)));failures=[]
 for c,a in zip(cases,actual):
  if c['expected']!=a['stages']:failures.append(dict(case=c['id'],group=c['group'],expected=c['expected'],actual=a['stages']))
 after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and fixed=={q.name:sha(q)for q in(fixture,out/'manifest.json',out/manifest['module_file'])}
 for name,value in(('frame-systems135-mismatches.json',failures),('frame-systems135-rejections.json',rejected)):(out/name).write_text(json.dumps(value,indent=2)+'\n')
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),stages=sum(len(c['expected'])for c in cases),groups=dict(Counter(c['group']for c in cases)),kinds=dict(Counter(c['kind']for c in cases)),mismatch_cases=len(failures),source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),body_guards=identities,expected_before_original=True,production_freeze_before_import=True,rejections=len(rejected),artifacts={q.name:sha(q)for q in(fixture,results,stderr,out/'frame-systems135-mismatches.json',out/'frame-systems135-rejections.json',out/'frame-systems135-runtime.json')},runtime=json.loads((out/'frame-systems135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),limitations=['Complete38007 arbitrary raw32 queue and10529 packet306 payload/capacity; opaque+28 physical byte preservation.','2602 expiry/idle plus expectednull-definition trap only; active due effect104+=108 returns explicit partial pending, not completedfunction.','975 allnon11 definitionbyte gates,2573 nonrunning/emptyclaim gates and49037 falseguard only; execution11/liveclaims/true-terminal remain explicit unknowns.','All2592B gameword changes and complete queuebackings/owned80 bytes compared; controlled definition pointers normalized to explicitfixtureID only.','This does not construct actual1089 entry, terrain or full880 front/multiplayer scheduler.'])
 (out/'frame-systems135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),stages=receipt['stages'],mismatch_cases=len(failures),first_failures=failures[:1]),indent=2))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
