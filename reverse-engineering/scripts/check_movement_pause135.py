#!/usr/bin/env python3
"""Full1371 pause/resume →35514/25472→26200 moving NPC sequence differential."""
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time,sqlite3
from collections import Counter
from dataclasses import asdict
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build,parse_source
from build_upgrade134_oracle import sha
FILES=('scripts/check_movement_pause135.py','scripts/run_movement_pause135_oracle.mjs','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/full135_host.mjs','reconstruction/core_spec/__init__.py','reconstruction/core_spec/binary32.py','reconstruction/core_spec/upgrade_values.py','reconstruction/core_spec/loop135.py','reconstruction/core_spec/movement_pause135.py')
IMPORT_SHA={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.movement_pause135 import moving_sequence_delta,UnresolvedMovementPause135
from core_spec.loop135 import apply_pause_command
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
BODY_GUARDS={1371:('7f7f','','fe613365e0c9b6520201f744a7c4c187e07e3d6010b074e65ef57179bef660cd'),35514:('7f','','b63b5546dce15768b153a58d8e87eeb44b18066ce704d6ba8c9f035a18b4d9df'),25472:('7f','','83f9ab98548b78e3cfd9edfc5a802cbf80a974b471ecf7c9a4e676450c7b752b'),26200:('7f7f','','dfd9f441f44d2cb3e1b7ae805d652e7bb688b47684febcf60fc4e05812770f74'),45845:('7f7e7f7f','','c6502e4033836dcb50eb72024a9ae6418ccbd3c93c72270f07da8eb6a35aa947'),27457:('7f7e7f7f7f7f','','d5828588e28f348d87604edfd0bae6afc3717b4b60b48cf0c048844634927f99'),15916:('7e7f','','b616d3b4ee6503812fecd72b255821cce06871a83c48c7dbe08225b0d9147c12'),45628:('7f7f7f','','4a664ae3b391919b5b35998204aa081bf3adbfa02a9c12458c59a3301084893e')}


def bodies_guard():
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;types,imports,decl,bodies,_=parse_source(raw);rows=[]
 for i,(ph,rh,body)in BODY_GUARDS.items():
  a,b=bodies[i];p,r=types[decl[i-len(imports)]];assert(p.hex(),r.hex(),hashlib.sha256(raw[a:b]).hexdigest())==(ph,rh,body)
  rows.append(dict(index=i,parameters_hex=ph,results_hex=rh,body_sha256=body,body_start=a,body_end=b,body_bytes=b-a))
 return rows


def unit(guid=1,marker=0,start=None,duration=None):
 r=bytearray(424);struct.pack_into('<I',r,0,marker);struct.pack_into('<Q',r,112,guid)
 for o,v in((316,1),(320,2),(324,3),(328,4),(332,5),(336,6)):struct.pack_into('<I',r,o,f.from_float(v))
 struct.pack_into('<II',r,340,f.from_float(9)if start is None else start,f.from_float(2)if duration is None else duration)
 return r.hex()


def corpus(pilot):
 rows=[];b=f.from_float
 def add(group,records,steps=None,phase=1,mode=0,discriminant=0,sequence=123):
  steps=steps or[(b(10),1),(b(10),0),(b(11),1),(b(11),0)]
  before=phase;seq=sequence;expected=[];packets=0;notifications=0
  for now,payload in steps:
   transition=apply_pause_command(game_discriminant=discriminant,mode=mode,phase=before,payload_byte=payload);events=[]
   if transition.changed:
    moving=moving_sequence_delta(tuple(records),now,auxiliary_motions=(),claims=())
    for guid in moving.guids:
     seq=(seq+1)&f.MASK;events.append(dict(guid=str(guid),sequence=seq,stop_flag=int(payload!=0)))
    packets+=moving.count;notifications+=1
   before=transition.phase
   expected.append(dict(phase=before,sequence=seq,records=records,rng_words=[1,2,3,4],events=events,packet_count=packets,notifications=notifications,auxiliary_count=0,claims_count=0))
  rows.append(dict(id=len(rows),group=group,records=records,initial_phase=phase,mode=mode,discriminant=str(discriminant),sequence=sequence,steps=[dict(now_bits=n,payload_byte=p)for n,p in steps],expected=expected))
 add('basic-one-moving',[unit()]);add('zero-moving',[]);add('stable-order-duplicate-guids',[unit(5),unit(7,marker=1),unit(5),unit(0),unit(0xffffffffffffffff)],sequence=0xfffffffe)
 if pilot:return json.loads(json.dumps(rows))
 for marker in(0,1,2,0xffffffff):
  for duration in(b(-1),0,0x80000000,1,b(.1),b(1),b(2),0x7f800000,0x7fc00001):
   for start in(b(9),b(10),b(11),0x7fc00001,0xff800000):
    add('predicate-marker-duration-end', [unit(marker=marker,start=start,duration=duration)])
 for phase in(0,1,2,3,4,255):
  for mode in(0,1,2,3,254,255):
   for payload in(0,1,2,255):add('command-mode-phase-payload-guards',[unit()],phase=phase,mode=mode,steps=[(b(10),payload)])
 for discriminator in(0,1,2,3,0xffffffffffffffff):add('game-discriminant-gate',[unit()],discriminant=discriminator)
 for now in(b(10),b(11)-1,b(11),b(11)+1,0x7fc00001,0x7f800000,0xff800000):add('exact-end-and-NaN-now',[unit()],steps=[(now,1),(now,0)])
 for byte in range(8):add('packed-guid-byte-positions',[unit(1<<(byte*8)),unit(0)],sequence=0xffffffff)
 # f32 addition rounds16777216+1 back to16777216: no movement atnow.
 add('f32-end-rounding',[unit(start=b(16777216),duration=b(1))],steps=[(b(16777216),1),(b(16777216),0)])
 rng=random.Random(0x3551426200)
 for j in range(48):
  records=[unit(rng.getrandbits(64),marker=rng.choice((0,0,0,1)),start=b(rng.choice((8,9,10,11))),duration=b(rng.choice((0,.01,.2,1,2,10))))for _ in range(j%17)]
  add('seeded-vector-order-and-count',records,sequence=rng.getrandbits(32))
 return json.loads(json.dumps(rows))


def negatives():
 rows=[]
 for name,call in(('missing-both',lambda:moving_sequence_delta((),0)),('missing-aux',lambda:moving_sequence_delta((),0,claims=())),('missing-claims',lambda:moving_sequence_delta((),0,auxiliary_motions=())),('nonempty-aux',lambda:moving_sequence_delta((),0,auxiliary_motions=(1,),claims=())),('nonempty-claims',lambda:moving_sequence_delta((),0,auxiliary_motions=(),claims=(1,))),('incomplete424',lambda:moving_sequence_delta(('00',),0,auxiliary_motions=(),claims=())),('clock-over-u32',lambda:moving_sequence_delta((),1<<32,auxiliary_motions=(),claims=()))):
  try:call()
  except(UnresolvedMovementPause135,ValueError,TypeError)as e:rows.append(dict(case=name,rejected=True,reason=str(e)))
  else:raise AssertionError(name)
 return rows


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args();before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_SHA
 identities=bodies_guard();rejected=negatives();cases=corpus(args.phase=='pilot');out,manifest=build(['command']);snap=out/'source-snapshot';snap.mkdir()
 for name,h in before.items():
  p=snap/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 fixture=out/'movement-pause135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
 fixed={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])};assert sha(RUNTIME)==RUNTIME_SHA
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_movement_pause135_oracle.mjs'),str(out),str(fixture)];start=time.monotonic();results=out/'movement-pause135-results.jsonl';stderr=out/'movement-pause135-stderr.log'
 with results.open('w')as stdout,stderr.open('w')as err:
  child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned movement pause deadline')
 if code:raise RuntimeError(f'Original movement pause failed:{out}')
 actual=[json.loads(x)for x in results.read_text().splitlines()];assert [x['id']for x in actual]==list(range(len(cases)));failures=[]
 for c,a in zip(cases,actual):
  if c['expected']!=a['projection']:failures.append(dict(case=c['id'],expected=c['expected'],actual=a['projection']))
 after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and fixed=={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
 (out/'movement-pause135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n');(out/'movement-pause135-rejections.json').write_text(json.dumps(rejected,indent=2)+'\n')
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),stages=sum(len(c['steps'])for c in cases),groups=dict(Counter(c['group']for c in cases)),mismatch_cases=len(failures),source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),body_guards=identities,rejected_cases=len(rejected),artifacts={p.name:sha(p)for p in(fixture,results,stderr,out/'movement-pause135-mismatches.json',out/'movement-pause135-rejections.json',out/'movement-pause135-runtime.json')},expected_before_original=True,production_freeze_before_import=True,runtime=json.loads((out/'movement-pause135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),limitations=['Explicit empty112B auxiliary motion and88B claim sources only.','Full424B NPC bytes and all221 packet GUID/sequence/stopflag compared; complete packet bytes retained but terrain positions/duration serialization not independently restored.','Flat absent terrain only; bodypredicate/sequence unaffected by height queries, nonflat packet geometry remains unknown.','1371 tag7 changes1↔3; direct35514/25472 onchoice transitions proven same unchangedcallee but root integration separate.'])
 (out/'movement-pause135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),stages=receipt['stages'],mismatch_cases=len(failures),first_failures=failures[:1]),indent=2))
 if failures:raise SystemExit(1)

if __name__=='__main__':main()
