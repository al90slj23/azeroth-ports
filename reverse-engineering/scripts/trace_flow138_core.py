#!/usr/bin/env python3
"""Bounded, source-bound135→138 flow guard discovery; no target execution.

Function indices below are explicit candidates anchored to1512 callers and
subsequently checked with full signatures/body ranges/raw WAT differences.
Normalization is diagnostic only and never transfers behavior acceptance.
"""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import difflib,hashlib,json,re,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from map_core135_to136 import load,normalize
from wasm138_profile import binary_identity
from wasm135_profile import binary_identity as identity135
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 '135':(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm','c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2',175317,ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z','official-0.135.1-full.wat'),
 '138':(ROOT/'originals/official-release-20261101T201508.341687Z/latest-wenilla_bg.wasm','c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b',175576,ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z','official-0.138.0-full.wat')}
PAIRS=(('constructor',1560,1571),('cached_world_construct',6730,6760),('opening',1089,1087),('stats',1512,1512),('player_tick',2088,2086),('owned_tick',1076,1232),('cast',922,916),('auto_cast',916,917),('player_aura',1202,1155))

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def connect(p):
 c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('pragma query_only=on');return c

def main():
 began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('flow135-to138-core-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 source_names=('scripts/trace_flow138_core.py','scripts/map_core135_to136.py','scripts/wasm135_profile.py','scripts/wasm_index.py','scripts/wasm138_profile.py','scripts/wasm136_profile.py','scripts/wasm134_profile.py')
 frozen={n:sha(ROOT/n)for n in source_names}
 for n in source_names:
  p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
 models={};connections={};streams={};identities={};readbytes=0;records={};texts={}
 for v,(binary,h,count,profile,wat)in SOURCES.items():
  models[v]=load(binary,h,count);connections[v]=connect(profile/'index.sqlite');streams[v]=(profile/wat).open('rb')
  m=json.loads((profile/'manifest.json').read_text());assert m['original_sha256']==h
  identities[v]=dict(source=str(binary.relative_to(ROOT)),source_sha256=h,source_bytes=len(models[v]['raw']),profile_manifest=str((profile/'manifest.json').relative_to(ROOT)),profile_manifest_sha256=sha(profile/'manifest.json'),full_WAT_read=False,profile_hashes_reused_from_producer=True)
 def fun(v,i):
  nonlocal readbytes
  if(v,i)in records:return records[v,i],texts[v,i]
  c=connections[v];row=dict(c.execute('select *from functions where idx=?',(i,)).fetchone());assert(row['body_start'],row['body_end'],row['body_bytes'])==models[v]['ranges'][i]
  n=row['wat_end']-row['wat_start'];assert n<=700000 and readbytes+n<=6000000
  stream=streams[v];stream.seek(row['wat_start']);wat=stream.read(n);readbytes+=n;t=wat.decode();assert t.startswith(f'  (func (;{i};) ')
  p=out/f'{v}-{i}.wat';p.write_bytes(wat);sig=models[v]['signatures'][i]
  calls=[dict(x)for x in c.execute('select callee,wat_offset,wat_line,instruction from calls where caller=?',(i,))]
  record=dict(index=i,signature=dict(params_hex=sig[0].hex(),results_hex=sig[1].hex()),**row,body_sha256=models[v]['hashes'][i],WAT_sha256=sha(p),direct_calls=calls)
  records[v,i]=record;texts[v,i]=t;return record,t
 rows=[]
 for role,a,b in PAIRS:
  old,at=fun('135',a);new,bt=fun('138',b);sig=old['signature']==new['signature'];assert sig,role
  normalized={mode:(normalize(at,models['135'],mode),normalize(bt,models['138'],mode))for mode in(False,True)}
  al=normalized[True][0].splitlines();bl=normalized[True][1].splitlines();ops_a=[x.split()[0]for x in al];ops_b=[x.split()[0]for x in bl]
  sm=difflib.SequenceMatcher(None,al,bl,autojunk=True);opcodes=sm.get_opcodes();different=[dict(operation=op,old_range=[i,j],new_range=[k,l],old=al[i:min(j,i+12)],new=bl[k:min(l,k+12)])for op,i,j,k,l in opcodes if op!='equal']
  rawdiff='\n'.join(difflib.unified_diff(at.splitlines(),bt.splitlines(),fromfile=f'135/{a}',tofile=f'138/{b}',n=2))+'\n';dp=out/(role+'.diff');dp.write_text(rawdiff)
  ca=[x['callee']for x in old['direct_calls']];cb=[x['callee']for x in new['direct_calls']]
  rows.append(dict(role=role,old=old,new=new,signature_equal=sig,exact_body_equal=old['body_sha256']==new['body_sha256'],calls_normalized_equal=normalized[False][0]==normalized[False][1],calls_static_address_normalized_equal=al==bl,opcode_sequence_equal=ops_a==ops_b,normalized_line_similarity=sm.ratio(),normalized_changes=different,raw_diff_sha256=sha(dp),ordered_direct_call_correspondence=[dict(old=x,new=y)for x,y in zip(ca,cb)]if len(ca)==len(cb)else None,static_only=True,runtime_acceptance_transferred=False))
 #1512's two scalar class loads are at+72/+76; race source is counted8B at+16/+20.
 static=[]
 for v in('135','138'):
  ident,_=(identity135 if v=='135'else binary_identity)(models[v]['raw']);segments=ident['data_segments']
  def read(address,n):
   matches=[x for x in segments if x['address']is not None and x['address']<=address and address+n<=x['address']+x['bytes']]
   assert len(matches)==1,(v,address,n);x=matches[0];off=x['file_offset']+address-x['address'];return models[v]['raw'][off:off+n]
  classdefault,classtable,racedefault,racetable=(5462608,1595888,5459304,1595728)if v=='135'else(1673176,1597616,1669892,1597456)
  classes=[]
  for key in range(1,12):
   p=struct.unpack('<I',read(classtable+4*(key-2),4))[0]if key>=2 else classdefault
   classes.append(dict(class_byte=key,pointer=p,HP72_bits=struct.unpack('<I',read(p+72,4))[0],armor76_bits=struct.unpack('<I',read(p+76,4))[0]))
  races=[]
  for key in range(1,9):
   p=struct.unpack('<I',read(racetable+4*(key-2),4))[0]if key>=2 else racedefault
   ptr,count=struct.unpack('<II',read(p+16,8));assert count<=16
   races.append(dict(race_byte=key,pointer=p,modifiers_pointer=ptr,count=count,modifier8_hex=read(ptr,count*8).hex()if count else''))
  static.append(dict(version=v,classes=classes,races=races))
 class_equal=all((a['class_byte'],a['HP72_bits'],a['armor76_bits'])==(b['class_byte'],b['HP72_bits'],b['armor76_bits'])for a,b in zip(static[0]['classes'],static[1]['classes']))
 race_equal=all((a['race_byte'],a['count'],a['modifier8_hex'])==(b['race_byte'],b['count'],b['modifier8_hex'])for a,b in zip(static[0]['races'],static[1]['races']))
 proof=dict(class_scalar_data_equal=class_equal,race_modifier_data_equal=race_equal,versions=static,scope='Static1512 referenced numeric class/race sources only, not all constructor data or gameplay equivalence')
 save(out/'stats-static-data.json',proof)
 native=ROOT/'originals/official-release-20261101T201508.341687Z/windows-0.138.0/AzerothSurvivors.exe';assert sha(native)=='eb5fd1c1b96e6180fcf5f3d685d90a61471af28d22e5f060c02b7b7663fbf79e'
 exe=native.read_bytes();native_rows=[]
 for row in static[1]['classes']:
  pattern=struct.pack('<II',row['HP72_bits'],row['armor76_bits']);found=[];pos=0
  while True:
   pos=exe.find(pattern,pos)
   if pos<0:break
   found.append(pos);pos+=1
   if len(found)>16:break
  native_rows.append(dict(class_byte=row['class_byte'],scalar8_hex=pattern.hex(),file_matches=found,search_stopped_after17=len(found)>16))
 save(out/'native-class-scalar-correspondence.json',dict(exe_sha256=sha(native),classes=native_rows,target_executed=False,scope='Scalar8 byte search only; native layout/function/ABI and gameplay not established'))
 for c in connections.values():c.close()
 for s in streams.values():s.close()
 assert all(sha(ROOT/n)==h for n,h in frozen.items())
 result=dict(kind='bounded_flow135_to138_core_static_guard_discovery',version='0.138.0',actual_build='382771e6c',identities=identities,entries=rows,stats_static_data=proof,stats_data_sha256=sha(out/'stats-static-data.json'),native_scalar_sha256=sha(out/'native-class-scalar-correspondence.json'),source_sha256=frozen,WAT_read_bytes=readbytes,full_WAT_read=False,original_executions=0,independent_model_cases=0,old_acceptance_transferred=False,elapsed_seconds=time.monotonic()-began,limitations=['Normalized matches are migration guards/candidates, not semantic equivalence.','Calls/static address changes still requirecallee/data provenance checks.','Constructor/cachedworld/owned/cast have real instruction changes; do not execute135fixtures through old indices.','No nativeWindows gameplay ABI/runtime is proved by scalar byte correspondence.'])
 save(out/'mapping.json',result);print(json.dumps(dict(directory=str(out),mapping_sha256=sha(out/'mapping.json'),WAT_read_bytes=readbytes,roles=len(rows),stats_class_equal=class_equal,stats_race_equal=race_equal,original_executions=0)))
if __name__=='__main__':main()
