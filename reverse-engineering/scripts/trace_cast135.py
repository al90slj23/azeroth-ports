#!/usr/bin/env python3
"""Static135 common cast, target and queued-hit evidence; never executes WASM."""
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re,sqlite3,struct
from pathlib import Path
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source
from build_upgrade134_oracle import sha
from trace_ecs_forward import structural_targets
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT=PROFILE/'official-0.135.1-full.wat';DB=PROFILE/'index.sqlite'
WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
DB_SHA='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
FUNCTIONS=(916,922,914,8295,1754,27562,8685,20038,36021,47198,38012,22287,2244)


def speed_selector(lines,spell):
 """Read the literal speed branch using lexical block destinations, not a game call."""
 frames=[];at={};starts={}
 for n,line in enumerate(lines):
  if line.startswith(('block ','if ','loop ')):
   frame={'start':n};frames.append(frame);starts[n]=frame
  elif line in ('end','end)') and frames:frames.pop()['end']=n
  elif line.startswith('else') and frames:frames[-1]['else']=n
  at[n]=tuple(frames)
 start=next(n for n,l in enumerate(lines) if l=='f32.const 0x1.8p+4 (;=24;)')
 origin=next(n for n in range(start,len(lines)-1) if lines[n:n+2]==['local.get 0','f32.load offset=1416'])
 outer=starts[start+2]['end']
 stack=[];locals_={1:spell};pc=start;branches=[]
 for _ in range(500):
  if pc>=outer:return None,branches
  if pc==origin:return locals_[15],branches
  parts=lines[pc].split();op=parts[0]
  if op=='f32.const':stack.append(float.fromhex(parts[1]))
  elif op=='i32.const':stack.append(int(parts[1])&0xffffffff)
  elif op=='local.get':stack.append(locals_[int(parts[1])])
  elif op=='local.set':locals_[int(parts[1])]=stack.pop()
  elif op in ('i32.le_s','i32.gt_s','i32.eq','i32.ne','i32.sub','i32.and'):
   b,a=stack.pop(),stack.pop()
   if op=='i32.sub':value=(a-b)&0xffffffff
   elif op=='i32.and':value=a&b
   elif op=='i32.eq':value=int(a==b)
   elif op=='i32.ne':value=int(a!=b)
   else:
    a=a if a<2**31 else a-2**32;b=b if b<2**31 else b-2**32
    value=int(a<=b if op=='i32.le_s' else a>b)
   stack.append(value)
  elif op=='if':
   if not stack.pop():pc=starts[pc].get('else',starts[pc]['end']);continue
  elif op in ('br','br_if','br_table'):
   if op=='br_if' and not stack.pop():pc+=1;continue
   if op=='br_table':
    depths=[int(x) for x in re.findall(r'(\d+) \(;@\d+;\)',lines[pc])]
    selector=stack.pop();depth=depths[min(selector,len(depths)-1)]
   else:depth=int(parts[1])
   target=at[pc][-1-depth];branches.append({'branch_line':pc+1,'target_end_line':target['end']+1})
   pc=target['end']+1;continue
  elif op not in ('block','end'):raise ValueError((pc+1,lines[pc]))
  pc+=1
 raise ValueError('Static selector watchdog')


def main():
 assert sha(SOURCE)==SOURCE_SHA and sha(WAT)==WAT_SHA and sha(DB)==DB_SHA
 binary=SOURCE.read_bytes();types,imports,decls,bodies,segments=parse_source(binary)
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('cast0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 texts={};records=[];con=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
 with WAT.open('rb') as stream:
  for index in FUNCTIONS:
   ws,we,bs,be=con.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone()
   assert bodies[index]==(bs,be);stream.seek(ws);raw=stream.read(we-ws)
   assert raw.startswith(f'  (func (;{index};) '.encode());(out/f'function-{index}.wat').write_bytes(raw)
   texts[index]=[line.strip() for line in raw.decode().splitlines()]
   signature=types[decls[index-len(imports)]]
   records.append(dict(index=index,body_start=bs,body_end=be,body_sha256=hashlib.sha256(binary[bs:be]).hexdigest(),
    wat_sha256=hashlib.sha256(raw).hexdigest(),parameters_hex=signature[0].hex(),results_hex=signature[1].hex()))
 guards=[]
 def guard(index,sequence,label):
  lines=texts[index];hits=[n+1 for n in range(len(lines)-len(sequence)+1) if lines[n:n+len(sequence)]==sequence]
  assert hits,(index,label);guards.append(dict(function=index,label=label,lines=hits,instructions=sequence))
 guard(922,['local.get 25','local.get 8','f32.load offset=48','local.tee 29','f32.const 0x1.666666p+0 (;=1.4;)','f32.mul'],'base damage ordered1.4')
 guard(922,['local.get 9','i32.const 2','i32.shl','f32.load offset=1595788'],'execution-kind coefficient table')
 guard(922,['local.get 8','i32.load8_u offset=84','local.tee 6','i32.const 2','i32.sub'],'dispatch source is execution-kind84 minus2')
 guard(922,['local.get 24','f32.const -0x1.18p+6 (;=-70;)','f32.add','f32.const 0x1.4p+3 (;=10;)','f32.div','call 35877'],'ordered radius soft compression')
 guard(916,['local.get 7','f32.load','local.get 1','f32.sub','f32.store'],'per-active countdown subtract')
 guard(916,['local.get 3','i32.const 48','i32.add','local.get 0','local.get 7','i32.load','local.tee 8','call 22287'],'active resolves actual owned record before922')
 guard(916,['i32.const 8','i32.add','i32.const 1050253722','i32.store'],'failed-cast retry0.3')
 guard(22287,['local.get 1','i32.load offset=1660','local.set 6'],'owned80B vector pointer')
 guard(22287,['i32.load offset=1664','local.tee 5'],'owned80B vector count')
 guard(27562,['local.get 1','i32.load offset=1788','local.tee 2'],'current424B unit vector')
 guard(27562,['local.get 1','i32.load offset=1792','i32.const 424','i32.mul'],'unit count and stride')
 guard(20038,['local.get 4','i32.load','br_if 0 (;@3;)'],'marker0 target eligibility')
 guard(20038,['local.tee 21','local.get 13','f32.load','f32.le','i32.eqz','br_if 0 (;@3;)'],'ordered squared-radius test')
 guard(8685,['f32.const 0x1.2p+5 (;=36;)','f32.le'],'6-unit nearby group')
 guard(8295,['i32.const 8','i32.shr_u','f32.convert_i32_u','f32.const 0x1p-24 (;=5.96046e-08;)','f32.mul','f32.gt'],'strict critical chance vs high24 draw')
 guard(8295,['local.get 18','local.get 6','local.get 0','f32.load offset=2352','f32.add','f32.add'],'due=travel+(delay+now)')
 guard(8295,['local.get 8','local.get 4','i64.store offset=64'],'queued target GUID')
 guard(8295,['local.get 8','local.get 5','f32.store offset=100'],'queued chosen damage')
 guard(1754,['local.get 4','i32.const 92','i32.add','f32.load','local.set 35'],'dequeue due field92')
 guard(1754,['local.get 35','local.get 36','f32.le','i32.eqz'],'due <=now retains NaN')
 memory=bytearray(max(s['address']+s['length'] for s in segments if s['address'] is not None))
 for s in segments:
  if s['address'] is not None:memory[s['address']:s['address']+s['length']]=binary[s['file_offset']:s['file_offset']+s['length']]
 coeff=list(struct.unpack_from('<7I',memory,1595788))
 catalogue=[]
 for j in range(114):
  p=5467428+j*88;w=struct.unpack_from('<22I',memory,p);identifier=bytes(memory[w[3]:w[3]+w[4]]).decode()
  catalogue.append(dict(id=identifier,pointer=p,kind=memory[p+84],effect=w[0],spell=w[11]))
 dispatch=next(n+1 for n,l in enumerate(texts[922]) if l.startswith('br_table '))
 branches={}
 for kind in range(12):
  branches[kind]=structural_targets(texts[922],{dispatch:(kind-2)&0xffffffff})[dispatch]
 speeds=[]
 for spell in sorted({x['spell'] for x in catalogue}):
  speed,trace=speed_selector(texts[8295],spell);speeds.append(dict(spell_id=spell,speed=speed,instant_if_none=speed is None,branches=trace))
 result=dict(version='0.135.1',build='0898d5e3',original_wasm_sha256=SOURCE_SHA,profile_wat_sha256=WAT_SHA,
  functions=records,guards=guards,dispatch_kind_minus2=branches,definition_count=114,
  execution_kind_counts=dict(Counter(x['kind'] for x in catalogue)),effect_tag_counts=dict(Counter(x['effect'] for x in catalogue)),
  supported_damage_only_ids=[x['id'] for x in catalogue if x['kind'] in (0,2) and x['effect']==0],
  coefficient_table=dict(address=1595788,raw_words=coeff),projectile_speed_selector=speeds,
  sources={n:sha(ROOT/n) for n in ('scripts/trace_cast135.py','scripts/trace_ecs_forward.py','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py')},
  target_executed=False,limitations=['All dispatcher branches are located; only kind0/2 effect0 numeric production behavior implemented.',
   'Static speed-selector traversal is a data extraction aid, not an independent runtime acceptance.',
   'Projectile priority special states, other effects/procs/death/packet rendering remain separately pending.'])
 assert sha(SOURCE)==SOURCE_SHA and sha(WAT)==WAT_SHA
 (out/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'directory':str(out),'functions':len(records),'guards':len(guards),'supported_ids':len(result['supported_damage_only_ids']),'target_executed':False}))

if __name__=='__main__':main()
