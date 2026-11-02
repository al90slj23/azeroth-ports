#!/usr/bin/env python3
"""1391542 full-body/race table/7source static recovery;0 original execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,sqlite3
import map_engine139_incremental as base
ROOT=base.ROOT
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
MAPPING=ROOT/'evidence/engine139-refined-static-20261102T013743.612949Z/mapping.json'
MAP_SHA='7b41961bce7f45e74a8d2a24305cf84d0d64f2f2d739c723b1e445af208c40f0'

def main():
 assert base.sha(MAPPING)==MAP_SHA;role=next(x for x in json.loads(MAPPING.read_text())['entries']if x['role']=='stats');old=base.catalog(base.OLD,base.OLD_SHA,base.identity138);new=base.catalog(base.SOURCE,base.SOURCE_SHA,base.identity139)
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('stats139-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();memory=bytearray(new['static_bounds'][1])
 for s in new['identity']['data_segments']:
  if s['address']is not None:memory[s['address']:s['address']+s['bytes']]=new['raw'][s['file_offset']:s['file_offset']+s['bytes']]
 def u(p):return int.from_bytes(memory[p:p+4],'little')
 classes={};races={};declarations=[]
 for cls in(1,2,3,4,5,7,8,9,11):
  p=u(1601376+4*(cls-2))if cls>=2 else 5877920;classes[cls]=(u(p+72),u(p+76));declarations.append(dict(domain='class',selector=cls,pointer=p,hp_bits=u(p+72),armor_bits=u(p+76),scalar8_hex=memory[p+72:p+80].hex()))
 for race in range(1,9):
  p=u(1601216+4*(race-2))if race>=2 else 5874636;ptr,count=u(p+16),u(p+20);assert 1<=count<=8;mods=[(memory[ptr+8*i],u(ptr+8*i+4))for i in range(count)];races[race]=mods;declarations.append(dict(domain='race',selector=race,pointer=p,modifier_pointer=ptr,modifier_count=count,raw_modifiers8_hex=memory[ptr:ptr+8*count].hex(),modifiers=mods))
 with sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
  db.row_factory=sqlite3.Row;callees=[dict(x)for x in db.execute('select callee,count(*) sites from calls where caller=1542 group by callee')];functions=[];texts={}
  for idx in[1542]+[x['callee']for x in callees]:
   x=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());assert(x['body_start'],x['body_end'],x['body_bytes'])==new['ranges'][idx];n=x['wat_end']-x['wat_start'];assert n<500000;stream.seek(x['wat_start']);t=stream.read(n);assert t.startswith(f'  (func (;{idx};)'.encode());(out/f'{idx}.wat').write_bytes(t);texts[idx]=t.decode();functions.append(dict(index=idx,params_hex=new['sig'][idx][0],results_hex=new['sig'][idx][1],body_sha256=new['hashes'][idx],wat_sha256=hashlib.sha256(t).hexdigest(),**x))
 assert new['sig'][1542]==('7f','')and new['hashes'][1542]==role['new']['body_sha256'];assert hashlib.sha256(texts[1542].encode()).hexdigest()==role['new']['wat_sha256']
 a=base.normalized((MAPPING.parent/'138-stats-1512.wat').read_text(),old,True);b=base.normalized(texts[1542],new,True);transforms=[]
 def rewrite(label,before,after,count):
  nonlocal a
  sites=[j for j in range(len(a)-len(before)+1)if a[j:j+len(before)]==before];assert len(sites)==count,(label,sites)
  for j in reversed(sites):a[j:j+len(before)]=after
  transforms.append(dict(label=label,sites=sites,before=before,after=after))
 assert a[1].endswith(' i64)')and b[1]==a[1][:-5]+')';a[1]=b[1]
 a=[re.sub(r'^(local\.(?:get|set|tee)) ([45])$',lambda m:m[1]+' '+str(9-int(m[2])),x)for x in a]
 rewrite('passive count local2→1',['i32.load offset=1700','local.tee 2','i32.eqz'],['i32.load offset=1700','local.tee 1','i32.eqz'],1)
 rewrite('passive count local1 consumed',['end','local.get 2','i32.const 3','i32.shl','local.set 2'],['end','local.get 1','i32.const 3','i32.shl','local.set 2'],1)
 rewrite('live spell temporary local2→5',['i32.load offset=20','local.tee 2','i32.const 23451','i32.ne','if  ;; label = @4','local.get 2','i32.const 23505'],['i32.load offset=20','local.tee 5','i32.const 23451','i32.ne','if  ;; label = @4','local.get 5','i32.const 23505'],1)
 for local,count in[(6,2),(0,1)]:rewrite('empty BTree pointer branch direct '+str(local),[f'local.get {local}','i32.eqz','if  ;; label = @5','local.get 2','i64.extend_i32_u','i64.const 32','i64.shl','local.set 52','br 3 (;@2;)','end'],[f'local.get {local}','i32.eqz','br_if 2 (;@2;)'],count)
 rewrite('BTree packed u64 low0/highlocal2→two u32 writes',['local.get 4','local.get 52','i64.store offset=20 align=4'],['local.get 4','local.get 2','i32.store offset=24','local.get 4','i32.const 0','i32.store offset=20'],3)
 assert a==b,'Unhandled139 full-function structural/arithmetic delta'
 lines=[x.strip()for x in texts[1542].splitlines()];guards=[]
 def guard(label,sequence):
  sites=[j+1 for j in range(len(lines)-len(sequence)+1)if lines[j:j+len(sequence)]==sequence];assert sites,label;guards.append(dict(label=label,sites=sites,instructions=sequence))
 for label,seq in [('classdefault',['i32.const 5877920','local.set 3']),('classtable',['i32.load offset=1601376','local.set 3']),('racedefault',['i32.const 5874636','local.set 9']),('racetable',['i32.load offset=1601216','local.set 9']),('racecount',['local.get 9','i32.load offset=20']),('raceptr',['local.get 9','i32.load offset=16']),('frame32',['global.get 0','i32.const 32','i32.sub','local.tee 4','global.set 0'])]:guard(label,seq)
 headers=dict(passives=[1692,1696,1700,8],adjustments=[1668,1672,1676,16],items=[2024,2028,2032,8],owned=[168,172,176,8],timed_definitions=[2048,2052,2056,36],timed_records=[592,596,600,12],live=[1704,1708,1712,32])
 for name,(cap,ptr,count,stride)in headers.items():
  assert f'i32.load offset={ptr}'in lines and f'i32.load offset={count}'in lines,(name,ptr,count)
 result=dict(version='0.139.0',build='f79c5e2b4',source_sha256=base.SOURCE_SHA,old_source_sha256=base.OLD_SHA,entry_map_sha256=MAP_SHA,script_sha256=base.sha(Path(__file__)),classes=classes,races=races,declarations=declarations,functions=functions,direct_callees=callees,full_normalized_body_after_explicit_codegen_rewrites_equal=True,transforms=transforms,guards=guards,seven_source_headers=headers,
 output_fields=dict(derived=list(range(1536,1625,4)),currentHP=1440,auxiliary=[1444,1448,1348,764],speed=1648,speed_sequence=1644,movement_queue=[1880,1884,1888],BTree=[2476,2480],BTree_keys=[22,28,1109]),original_executions=0,old_acceptance_transferred=False,
 limitations=['Call indices and active-static-envelope addresses are normalized only for the explicit body comparison;actualcallee execution needsfresh139differential','Transform6packedBTree header is static byte equivalence onlittleendian;no whole BTree physical layout claim','Seven sources are explicit supplied snapshots;their natural producers remain outofscope'])
 base.save(out/'trace.json',result);print(json.dumps(dict(directory=str(out),sha256=base.sha(out/'trace.json'),classes=classes,races=races,callees=callees)),flush=True)
if __name__=='__main__':main()
