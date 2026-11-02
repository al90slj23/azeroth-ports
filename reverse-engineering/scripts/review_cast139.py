#!/usr/bin/env python3
"""Different-author stdlib-only139 cleave review; never imports author code."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
from datetime import datetime,timezone
import argparse,ast,hashlib,json,os,re,sqlite3,struct,sys
ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/cast139-oracle-20261102T043654.185463Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMPARISON_SHA='77fa62cb19d90f17ec91773593dd21bb97e7311f0f2f1052ebe5fec88321c9be'
HANDOFF_SHA='13b138db90dc80c05c2fa5cb2d98f6d0d9dff569969f1f3fbc447105498390b6'
M=(1<<32)-1;ONE=0x3f800000

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def u(b,o=0):return struct.unpack_from('<I',b,o)[0]
def q(b,o=0):return struct.unpack_from('<Q',b,o)[0]
def bits64(v):return struct.unpack('<Q',struct.pack('<d',v))[0]
def f64(v):return struct.unpack('<d',struct.pack('<Q',v))[0]
@lru_cache(maxsize=65536)
def rational(b):
 assert 0<=b<=M and (b&0x7fffffff)<0x7f800000
 mant=b&0x7fffff;e=(b>>23)&255
 n=mant if e==0 else mant|0x800000;power=-149 if e==0 else e-150
 v=Fraction(n<<power,1)if power>=0 else Fraction(n,1<<-power)
 return -v if b>>31 else v

def even_div(n,d):
 v,r=divmod(n,d);return v+int(2*r>d or 2*r==d and v&1)
@lru_cache(maxsize=65536)
def rounded(v,negative_zero=False):
 if not v:return 0x80000000 if negative_zero else 0
 sign=0x80000000 if v<0 else 0;n,d=abs(v).numerator,abs(v).denominator;e=n.bit_length()-d.bit_length()
 if e>=0:
  if n<d<<e:e-=1
 elif n<<-e<d:e-=1
 if e < -126:return sign|even_div(n<<149,d)
 shift=23-e;sig=even_div(n<<shift,d)if shift>=0 else even_div(n,d<<-shift)
 if sig==1<<24:e+=1;sig>>=1
 assert -126<=e<=127
 return sign|((e+127)<<23)|(sig&0x7fffff)
def add(a,b):return rounded(rational(a)+rational(b),bool(a>>31 and b>>31))
def sub(a,b):return add(a,b^0x80000000)
def mul(a,b):return rounded(rational(a)*rational(b),bool((a^b)>>31))
def div(a,b):assert rational(b);return rounded(rational(a)/rational(b),bool((a^b)>>31))
def le(a,b):return rational(a)<=rational(b)
def ro(a,n):return((a<<n)|(a>>(32-n)))&M
def nextword(words):
 a,b,c,d=words;out=(ro((a+d)&M,7)+a)&M;t=(b<<9)&M
 c^=a;d^=b;b^=c;a^=d;c^=t;d=ro(d,11)
 return out,(a&M,b&M,c&M,d&M)
def totalkey(b):return (~b)&M if b>>31 else b|0x80000000

def xy(row,now):
 duration=u(row,344)
 if rational(duration)<=0:return(u(row,328),u(row,332))
 t=div(sub(now,u(row,340)),duration)
 if rational(t)<0:t=0
 if rational(t)>1:t=ONE
 return tuple(add(u(row,a),mul(sub(u(row,b),u(row,a)),t))for a,b in((316,328),(320,332)))
def distance(a,b):
 dx,dy=sub(a[0],b[0]),sub(a[1],b[1]);return add(mul(dx,dx),mul(dy,dy))
def select(records,s,radius):
 square=mul(radius,radius);now=s['now_bits'];px=s['player_xyz'][:2]
 candidates=[(i,xy(row,now))for i,row in enumerate(records)if u(row)==0 and le(distance(xy(row,now),px),square)]
 # Insertion implementation is independent of author Python list.sort.
 def ordered(values,key):
  ans=[]
  for v in values:
   k=key(v);i=len(ans)
   while i and key(ans[i-1])>k:i-=1
   ans.insert(i,v)
  return ans
 candidates=ordered(candidates,lambda v:totalkey(distance(v[1],px)))
 def priority(v):
  row=records[v[0]];return 3 if rational(now)<rational(u(row,380))else 2-row[424]
 buckets=[[],[],[],[]]
 for v in candidates:buckets[priority(v)].append(v)
 if buckets[2]:
  anchor=buckets[2][0][1];near=[];far=[]
  for v in buckets[2]:(near if rational(distance(v[1],anchor))<=36 else far).append(v)
  buckets[2]=ordered(near,lambda v:totalkey(u(records[v[0]],288)))+far
 return [v[0]for bucket in buckets for v in bucket]
def packguid(value):
 raw=value.to_bytes(8,'little');return bytes([sum((1<<i)for i,v in enumerate(raw)if v)])+bytes(v for v in raw if v)
def launch(source,spell,targets):
 return (packguid(source)+packguid(source)+struct.pack('<IH',spell,256)+bytes([len(targets)])+b''.join(t.to_bytes(8,'little')for t in targets)+bytes([0,2,0])+packguid(targets[0])).hex()
def decode306(hx):
 raw=bytes.fromhex(hx);p=0
 def packed():
  nonlocal p
  mask=raw[p];p+=1;out=0
  for i in range(8):
   if mask>>i&1:out|=raw[p]<<(8*i);p+=1
  return out
 source=packed();same=packed();spell,flags=struct.unpack_from('<IH',raw,p);p+=6;n=raw[p];p+=1
 targets=list(struct.unpack_from('<'+'Q'*n,raw,p));p+=n*8;miss=raw[p];targetmask=struct.unpack_from('<H',raw,p+1)[0];p+=3;first=packed()
 assert p==len(raw)and same==source and flags==256 and miss==0 and targetmask==2 and first==targets[0]
 return dict(source=source,spell=spell,targets=targets,bytes=len(raw))
def step(s,records,words,total,sets,owned,definition):
 # Exact input-derived model, with fractional binary32 rounding after every op.
 spell=u(definition,44);count=u(definition,64)
 if count:count=max(1,(count+u(owned,20)+u(owned,60)+s['extra_targets'])&M)
 else:count=1
 selected=select(records,s,u(definition,56))[:count];ids=[q(records[i],112)for i in selected]
 for j in range(3):
  if j==2 and s['suppress_primary_attempt']:continue
  if spell not in sets[j]:sets[j].append(spell)
 weighted=mul(mul(mul(mul(u(definition,48),0x3fb33333),u(owned,12)),u(owned,52)),ONE)
 hp_part=mul(s['max_hp_bits'],u(owned,72))if rational(u(definition,48))>0 else 0
 base=mul(s['damage_multiplier_bits'],add(weighted,hp_part));hits=[]
 for index in selected:
  value,words=nextword(words);random01=mul(rounded(Fraction(value>>8)),0x33800000)
  critical=rational(add(0,s['critical_chance_bits']))>rational(random01)
  amount=mul(base,s['critical_multiplier_bits'])if critical else base;row=records[index]
  if s['phase2587']==1:
   assert u(row,40)==u(row,64)==u(row,244)==M and row[424]in(0,1)
   now=s['now_bits'];coefficient=ONE
   if rational(now)<rational(u(row,148)):coefficient=add(coefficient,u(row,144))
   term=u(row,152)if rational(now)<rational(u(row,156))else(u(row,160)if rational(now)<rational(u(row,164))else 0)
   coefficient=add(add(add(coefficient,term),u(row,368)),0)
   school=0x3dcccccd if definition[85]&254==2 and rational(now)<rational(u(row,372))else 0
   damage=mul(mul(amount,add(coefficient,school)),ONE)
   if rational(damage)<=1:damage=ONE
   old=u(row,288);new=sub(old,damage);assert rational(new)>0
   account=min(max(rational(old),0),rational(damage));total=bits64(f64(total)+float(account));struct.pack_into('<I',row,288,new)
  hits.append(dict(guid=str(q(row,112)),critical=critical,amount_bits=amount))
 packet=[]if not ids else [[306,launch(int(s['source_id']),spell,ids)]]
 answer=dict(success=int(bool(ids)),units432_hex=[bytes(row).hex()for row in records],rng_words=list(words),accounted_total_bits=str(total),spell_sets=[list(a)for a in sets],owned80_hex=owned.hex(),launch306_packets=packet)
 return answer,words,total,dict(selected_ids=[str(v)for v in ids],base_damage_bits=base,hits=hits)

class Reader:
 def __init__(self,b,p=0,end=None):self.b=b;self.p=p;self.end=len(b)if end is None else end
 def byte(self):assert self.p<self.end;v=self.b[self.p];self.p+=1;return v
 def uint(self):
  value=shift=0
  while True:
   x=self.byte();value|=(x&127)<<shift
   if x<128:return value
   shift+=7;assert shift<70
 def sint(self):
  value=shift=0
  while True:
   x=self.byte();value|=(x&127)<<shift;shift+=7
   if x<128:return value-(1<<shift)if x&64 else value
 def take(self,n):assert self.p+n<=self.end;v=self.b[self.p:self.p+n];self.p+=n;return v
 def string(self):return self.take(self.uint()).decode()
def image(raw):
 assert raw[:8]==b'\0asm\1\0\0\0';r=Reader(raw,8);sections=[]
 while r.p<r.end:
  start=r.p;kind=r.byte();n=r.uint();p=r.p;r.take(n);sections.append(dict(kind=kind,start=start,payload=p,end=r.p))
 by={x['kind']:x for x in sections if x['kind']};assert 8 not in by
 r=Reader(raw,by[1]['payload'],by[1]['end']);types=[]
 for _ in range(r.uint()):assert r.byte()==96;types.append((r.take(r.uint()).hex(),r.take(r.uint()).hex()))
 r=Reader(raw,by[2]['payload'],by[2]['end']);imports=[]
 for _ in range(r.uint()):
  module,name,kind=r.string(),r.string(),r.byte();assert kind==0;imports.append(dict(module=module,name=name,type_index=r.uint()))
 r=Reader(raw,by[3]['payload'],by[3]['end']);decl=[r.uint()for _ in range(r.uint())]
 r=Reader(raw,by[7]['payload'],by[7]['end']);exports=[]
 for _ in range(r.uint()):exports.append((r.string(),r.byte(),r.uint()))
 r=Reader(raw,by[10]['payload'],by[10]['end']);n=r.uint();assert n==len(decl);bodies={}
 for i in range(n):
  size=r.uint();start=r.p;r.take(size);bodies[len(imports)+i]=(start,r.p)
 r=Reader(raw,by[11]['payload'],by[11]['end']);data=[]
 for _ in range(r.uint()):
  flag=r.uint();assert flag in(0,1,2)
  if flag==2:assert r.uint()==0
  addr=None
  if flag!=1:assert r.byte()==0x41;addr=r.sint();assert r.byte()==0xb
  n=r.uint();pos=r.p;r.take(n);data.append((addr,pos,n))
 return dict(sections=sections,types=types,imports=imports,decl=decl,exports=exports,bodies=bodies,data=data)
def readstatic(raw,meta,address,n):
 # WASM active-data loader: unmentioned module-initial memory bytes are zero;
 # this is static initializer decoding,not filling callerrecord unknowns.
 result=bytearray(n);overlaps=0
 for base,pos,size in meta['data']:
  if base is None:continue
  low=max(address,base);high=min(address+n,base+size)
  if low<high:result[low-address:high-address]=raw[pos+low-base:pos+high-base];overlaps+=1
 assert overlaps
 return bytes(result)
def static_review(out,batch,m):
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;meta=image(raw);private=(batch/m['module_file']).read_bytes();assert hashlib.sha256(private).hexdigest()==m['module_sha256'];changed=image(private)
 assert meta['imports']==m['original_imports']and len(meta['imports'])==882
 assert changed['exports']==meta['exports']+[('research139_cast922',0,922),('research139_cast_stack0',3,0)]
 assert len(meta['sections'])==len(changed['sections'])
 for a,b in zip(meta['sections'],changed['sections']):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
 profile=json.loads((PROFILE/'manifest.json').read_text());assert profile['original_sha256']==SOURCE_SHA and profile['target_version']=='0.139.0'and profile['function_imports']==882 and profile['defined_functions']==177101 and profile['full_module_validated']
 trace=json.loads((batch/'static/trace.json').read_text());assert sha(batch/'static/trace.json')==m['static_trace_sha256'];functions={};texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as wat:
  for key,proof in trace['functions'].items():
   i=int(key);row=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(i,)).fetchone();assert row
   start,end=meta['bodies'][i];assert(start,end)==tuple(row[2:]);assert hashlib.sha256(raw[start:end]).hexdigest()==proof['body_sha256'];assert start==proof['body_start']and end==proof['body_end']
   wat.seek(row[0]);block=wat.read(row[1]-row[0]);assert block==(batch/'static'/f'{i}.wat').read_bytes();assert hashlib.sha256(block).hexdigest()==proof['WAT_sha256'];text=block.decode();texts[i]=text
   actual_calls=[int(v)for v in re.findall(r'^\s*call (\d+)\s*$',text,re.M)];assert actual_calls==[x[0]for x in trace['direct_calls'][key]]
   signature=meta['types'][meta['decl'][i-882]];assert list(signature)==proof['signature'];functions[key]=dict(body_sha256=proof['body_sha256'],wat_sha256=proof['WAT_sha256'],signature=signature,direct_call_sites=len(actual_calls))
 assert set(functions)==set(map(str,(922,913,8673,27754,36518,20123,48064,5797,5406,38554,44070,2189,10490,15962,93344)))
 definition=readstatic(raw,meta,m['definition']['pointer'],88);assert definition.hex()==m['definition']['raw88_hex']and definition[84:86]==bytes([5,0]);assert u(definition)==0 and u(definition,44)==845
 assert readstatic(raw,meta,u(definition,12),u(definition,16))==b'cleave';coeff=struct.unpack('<7I',readstatic(raw,meta,1601276,28));assert coeff[3]==ONE
 assert dict((name,index)for name,kind,index in meta['exports']if kind==0)['__wbindgen_malloc']==93344
 t=lambda i:'\n'.join(x.strip()for x in texts[i].splitlines())
 assert 'offset=2587'not in texts[922]and 'i32.load8_u offset=2587\ni32.const 1\ni32.ne'in t(913)
 assert 'i32.const 52\ni32.sub\nf32.load'in t(8673)and 'i32.const 8\ni32.sub\ni32.load8_u'in t(8673)
 assert 'f32.const 0x1.2p+5 (;=36;)\nf32.le'in t(8673)
 assert 'i32.const 8\ni32.const 0\ncall 27754'in t(8673)
 assert 'f32.mul\nf32.add\nlocal.tee 21'in t(20123)and 'i32.const 432'in texts[20123]
 assert 'i32.const 306\ni32.store16 offset=44'in t(10490)and t(10490).count('call 15962')>=3
 assert 'i32.const 256'in texts[10490]and 'i32.const 2'in texts[10490]
 result=dict(profile_manifest_sha256=sha(PROFILE/'manifest.json'),bounded_WAT_slices_rebound=True,whole_profile_not_rehashed_in_review=True,source_sha256=SOURCE_SHA,original_bytes=len(raw),private_module_sha256=m['module_sha256'],only_section7_changed=True,all_nonexport_bytes_equal=True,all_callees_and_data_preserved=True,implicit_start=False,imports882_exact=True,functions=functions,definition=dict(pointer=m['definition']['pointer'],raw88_hex=definition.hex()),coefficients=list(coeff),rule_anchors=dict(priority380_from_end432_minus52=True,classification424_from_end432_minus8=True,ordinary_near_squared36_inclusive=True,exclude_slice_is_pointer8_count0=True,phaseguard_in913_not922=True,execution5_coefficient_index3=True,effect0_descriptor_from_original12bytes=definition[:12].hex()),large_sort_scope='Actual20/21/32/63 orderedpacketfixtures checked; no arbitrarylargeN stability theorem')
 save(out/'static-binding.json',result);return definition,result

def local_import_edges(files):
 # Read AST only. Resolve local files without executing any module/import hook.
 found=set();allowed=set(files)
 def resolve(path):
  for candidate in(path.with_suffix('.py'),path/'__init__.py'):
   if candidate.is_file():return candidate
 def admit(caller,target):
  if target is None:return
  name=str(target.relative_to(ROOT));assert name in allowed,(caller,name);found.add((caller,name))
  package=target.parent/'__init__.py'
  if package.is_file():
   name=str(package.relative_to(ROOT));assert name in allowed;found.add((caller,name))
 def absolute(name):
  for base in(ROOT/'scripts',ROOT/'reconstruction'):
   p=resolve(base.joinpath(*name.split('.')))
   if p is not None:return p
 for name in files:
  file=ROOT/name
  if file.suffix!='.py':
   assert file.suffix=='.mjs'and all(v.startswith('node:')for v in re.findall(r"from\s*['\"]([^'\"]+)['\"]",file.read_text()));continue
  tree=ast.parse(file.read_text())
  for node in ast.walk(tree):
   if isinstance(node,ast.Import):
    for alias in node.names:admit(name,absolute(alias.name))
   elif isinstance(node,ast.ImportFrom):
    if node.level:
     parent=file.parent
     for _ in range(node.level-1):parent=parent.parent
     target=resolve(parent.joinpath(*node.module.split('.')))if node.module else resolve(parent)
    else:target=absolute(node.module)if node.module else None
    admit(name,target)
    if target is not None and target.name=='__init__.py':
     for alias in node.names:admit(name,resolve(target.parent/alias.name))
 return sorted(map(list,found))

def known_game_initial(s,before,unit_pointer):
 assert len(before)==2592
 checks={1784:len(s['units432_hex']),1788:unit_pointer,1792:len(s['units432_hex']),2352:s['now_bits'],1536:s['max_hp_bits'],1540:s['damage_multiplier_bits'],1548:s['critical_chance_bits'],1552:s['critical_multiplier_bits'],1592:s['extra_targets'],1440:s['max_hp_bits'],1544:ONE,1580:ONE,552:int(s['suppress_primary_attempt'])}
 for j,v in enumerate(s['rng_words']):checks[1720+4*j]=v
 for j,v in enumerate(s['player_xyz']):checks[1416+4*j]=v
 for o,v in checks.items():assert u(before,o)==v
 assert q(before,984)==int(s['accounted_total_bits'])and q(before,1336)==int(s['source_id'])and before[2587]==s['phase2587']and before[360:362]==bytes([1,1])and before[908]==0
 for o in(176,1816,1828,1840,1852,1864,1876,1888,1972,2032,2044,2056):assert u(before,o)==0
 for o in(2028,2052,600,648,1660,1884,1896,1812,1824,1836,1848,1860,1872,1908,1920,1968,2112,2124):assert u(before,o)==8
 return len(checks)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out');args=ap.parse_args();out=Path(args.out)if args.out else ROOT/'evidence'/datetime.now(timezone.utc).strftime('cast139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir(parents=True,exist_ok=False)
 assert sha(BATCH/'comparison.json')==COMPARISON_SHA and sha(BATCH/'task-handoff.json')==HANDOFF_SHA
 comp=json.loads((BATCH/'comparison.json').read_text());handoff=json.loads((BATCH/'task-handoff.json').read_text());assert comp['source_before']==comp['source_after']==handoff['source_closure']
 source_before={p:sha(ROOT/p)for p in comp['source_before']};assert source_before==comp['source_before'];assert all(sha(ROOT/p)==h for p,h in handoff['files'].items())
 for p,h in source_before.items():assert sha(BATCH/'source-snapshot'/p)==h
 assert local_import_edges(source_before)==comp['source_import_edges']
 assert len(source_before)==15 and len(comp['source_import_edges'])==24
 prepared=json.loads((BATCH/'prepared.json').read_text());assert prepared['expected_before_original']and not prepared['inputs_contain_expected']
 for n,h in prepared['frozen'].items():assert sha(BATCH/n)==h
 for file,key in(('inputs.json','inputs_sha256'),('expected.json','expected_sha256'),('stdout.jsonl','actual_sha256'),('manifest.json','manifest_sha256')):assert sha(BATCH/file)==comp[key]
 m=json.loads((BATCH/'manifest.json').read_text());definition,static=static_review(out,BATCH,m)
 inputs=json.loads((BATCH/'inputs.json').read_text());stored=json.loads((BATCH/'expected.json').read_text());actual=[json.loads(x)for x in(BATCH/'stdout.jsonl').read_text().splitlines()];obs=[json.loads(x)for x in(BATCH/'observations.jsonl').read_text().splitlines()]
 assert len(inputs)==len(stored)==len(actual)==110 and sum(c['repeats']for c in inputs)==184 and len(obs)==184
 differences=[];reference=[];diagnostics=[];counts=dict(cases=110,calls=0,full432_bytes=0,owned80_bytes=0,launch306_messages=0,launch306_bytes=0,ordered_targetIDs=0,selected_hits=0,phase0_cast_calls=0,rawGame_knowninitial_words=0);oi=0
 def compare(kind,case,stage,field,e,a):
  if e!=a:differences.append(dict(kind=kind,case=case,stage=stage,field=field,expected=e,actual=a))
 for c,e,a in zip(inputs,stored,actual):
  assert c['id']==e['id']==a['id'];s=c['state'];records=[bytearray.fromhex(h)for h in s['units432_hex']];owned=bytes.fromhex(c['owned80_hex']);assert len(owned)==80 and u(owned)==m['definition']['pointer'];words=tuple(s['rng_words']);total=int(s['accounted_total_bits']);sets=[list(v)for v in s['spell_sets']];answers=[];diagnostics_one=[];cursor=0
  assert all(len(row)==432 and u(row,40)==u(row,64)==u(row,244)==M and row[424]in(0,1)for row in records)
  assert len(set(q(row,112)for row in records))==len(records)and s['phase2587']in(0,1)
  assert len(e['answers'])==len(a['answers'])==c['repeats']
  for stage in range(c['repeats']):
   independent,words,total,diag=step(s,records,words,total,sets,owned,definition);answers.append(independent);diagnostics_one.append(diag);counts['calls']+=1;counts['selected_hits']+=len(diag['selected_ids']);counts['phase0_cast_calls']+=s['phase2587']==0
   for key in independent:
    compare('stored_expected',c['id'],stage,key,independent[key],e['answers'][stage].get(key));compare('original_actual',c['id'],stage,key,independent[key],a['answers'][stage].get(key))
   counts['full432_bytes']+=432*len(records);counts['owned80_bytes']+=80
   observation=obs[oi];oi+=1;assert observation['id']==c['id']and observation['stage']==stage and observation['owned80_hex']==owned.hex();before=bytes.fromhex(observation['game_before2592_hex']);after=bytes.fromhex(observation['game_after2592_hex']);assert len(after)==2592;counts['rawGame_knowninitial_words']+=known_game_initial(s,before,observation['unit_pointer'])
   assert q(after,984)==total and q(after,1336)==int(s['source_id'])and [u(after,1720+j*4)for j in range(4)]==list(words)and after[2587]==s['phase2587']
   for countoff,values in zip((672,684,732),sets):assert u(after,countoff)==len(values)
   assert u(after,1792)==len(records)and u(after,1788)==observation['unit_pointer']
   packets=observation['packets'];assert len(packets)==u(after,1888);new306=[v for v in packets[cursor:]if v[0]==306];cursor=len(packets);compare('observation_packet_envelope',c['id'],stage,'launch306_packets',independent['launch306_packets'],new306)
   for _,hx in new306:
    decoded=decode306(hx);assert decoded['source']==int(s['source_id'])and decoded['spell']==845 and decoded['targets']==[int(v)for v in diag['selected_ids']];counts['launch306_messages']+=1;counts['launch306_bytes']+=decoded['bytes'];counts['ordered_targetIDs']+=len(decoded['targets'])
  reference.append(dict(id=c['id'],answers=answers));diagnostics.append(dict(id=c['id'],stages=diagnostics_one))
 runtime=json.loads((BATCH/'runtime.json').read_text());terminal=json.loads((BATCH/'owned-terminal.json').read_text());assert runtime['full922_calls']==184 and runtime['fresh_instances']==110 and runtime['snapshot_restores']==runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['memory_cap_bytes']==33554432 and runtime['peak_memory_bytes']<=33554432
 stack=runtime['stack_checks'];assert len(stack)==547 and all(v['before']==v['after']==1048576 and v['returned']for v in stack);assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']
 assert counts['full432_bytes']==1002672 and counts['owned80_bytes']==14720 and counts['launch306_messages']==157 and counts['launch306_bytes']==9858
 history=[]
 for name,h,cases,calls,diffs in [('cast139-oracle-20261102T043143.182996Z','bb13bd6d745c189746d56044b717b46db13491df65b254924033d589e27a6869',4,5,0),('cast139-oracle-20261102T043212.947622Z','45b9fdde4f316f8b525013b424a79606ec454d6505e490934cd08cffc7073887',102,176,36),('cast139-oracle-20261102T043320.590395Z','32d95eb9d5d3ad44b28d3f0cdd87d97744793fc1c46671bae4ea021af2b2089b',103,177,0),('cast139-oracle-20261102T043523.100176Z','12d4e8d21fd17c6d49be46d83f25ce537e64cee488984ae01f307c5d1776c248',110,184,0)]:
  p=ROOT/'evidence'/name;assert sha(p/'comparison.json')==h;old=json.loads((p/'comparison.json').read_text());assert(old['cases'],old['target_calls'],old['differences'])==(cases,calls,diffs);history.append(dict(directory=name,comparison_sha256=h,cases=cases,calls=calls,differences=diffs,counted_in_this_review=False))
 assert source_before=={p:sha(ROOT/p)for p in source_before}and all(sha(ROOT/p)==h for p,h in handoff['files'].items())
 save(out/'independent-reference.json',reference);save(out/'independent-diagnostics.json',diagnostics);save(out/'differences.json',differences)
 report=dict(status='accepted_with_explicit_scoped_limits'if not differences else'notaccepted_differences',reviewer='stats138_review',author='root',version='0.139.0',build='f79c5e2b4',review_script_sha256=sha(__file__),comparison_sha256=COMPARISON_SHA,handoff_sha256=HANDOFF_SHA,counters=counts,differences=len(differences),sources=source_before,source_count=15,production_source_count=6,declared_edges_checked=24,source_snapshots_and_current_match=True,author_models_builders_checkers_executed=0,new_original_executions=0,new_original_cases=0,numeric_reference='Stdlib Fraction exact RNE binary32 operations, independent insertion targetordering, xoshiro128++, f64 cumulative total; input only',static_binding_sha256=sha(out/'static-binding.json'),independent_reference_sha256=sha(out/'independent-reference.json'),diagnostics_sha256=sha(out/'independent-diagnostics.json'),actual_stdout_sha256=sha(BATCH/'stdout.jsonl'),observations_sha256=sha(BATCH/'observations.jsonl'),runtime_host0_is_runner_observation=True,stack547_assertions_are_runner_observations=True,history=history,unknowns=['fullGamephysicalcontainerandpacketallocationsemantics','damage592andHP169packetsemantics','arbitrarylargeNsortstability','nonemptyproc/item/modifiercallbacks','otherabilities/effects','death','naturalAppscheduler/world','fullgame','nativeWindows'],none_padding_input_note='All432B are explicit caller fixture inputs; this does not fill naturalNPC129Nonepadding',author_source_files_untouched=True)
 save(out/'review.json',report);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=report['status'],counts=counts,differences=len(differences))))
 if differences:raise SystemExit(1)
if __name__=='__main__':main()
