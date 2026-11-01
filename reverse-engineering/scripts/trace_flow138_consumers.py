#!/usr/bin/env python3
"""Bounded RO135→138 consumer-entry mapping; not behavioral acceptance."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,re,sqlite3
ROOT=Path(__file__).resolve().parents[1]
VERSIONS={
 '135':dict(version='0.135.1',build='90898d5e3',source='originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',sha256='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2',profile='evidence/wasm0135-profile-20261101T031028.877964Z'),
 '138':dict(version='0.138.0',build='382771e6c',source='originals/official-release-20261101T201508.341687Z/latest-wenilla_bg.wasm',sha256='c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b',profile='evidence/wasm0138-profile-20261101T202038.814151Z')}
PAIRS={'update_units':(921,919),'spawn_tick':(947,946),'collect_pickups':(2862,2862),'select_ability':(1072,1072)}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def lines(text):return [re.sub(r'\(;.*?;\)','',x).strip()for x in text.splitlines()if re.sub(r'\(;.*?;\)','',x).strip()]
def skeleton(ls):
 result=[]
 for x in ls:
  x=re.sub(r'\(type \d+\)','(type #)',x);x=re.sub(r'^call \d+$','call #',x);x=re.sub(r'^i(?:32|64)\.const -?\d+$','iconst #',x);x=re.sub(r'offset=(\d{6,})','offset=#static',x);result.append(x)
 return result

def main():
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('flow138-consumers-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();dbs={};sources={};read_bytes=0
 for key,s in VERSIONS.items():
  source=ROOT/s['source'];assert sha(source)==s['sha256'];sources[key]={**s,'bytes':source.stat().st_size,'source_checked_now':True}
  p=ROOT/s['profile'];db=sqlite3.connect((p/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');dbs[key]=db;sources[key]['profile_manifest_sha256']=sha(p/'manifest.json')
 def get(key,idx):
  nonlocal read_bytes
  s=VERSIONS[key];p=ROOT/s['profile'];row=dict(dbs[key].execute('select * from functions where idx=?',(idx,)).fetchone());size=row['wat_end']-row['wat_start'];assert 0<size<600000
  with(p/('official-'+s['version']+'-full.wat')).open('rb')as f:f.seek(row['wat_start']);wat=f.read(size)
  assert len(wat)==size;read_bytes+=size
  with(ROOT/s['source']).open('rb')as f:f.seek(row['body_start']);body=f.read(row['body_bytes'])
  assert len(body)==row['body_bytes'];name=f'{key}-{idx}.wat';(out/name).write_bytes(wat)
  ls=lines(wat.decode());header=ls[0];signature=re.sub(r'^\(func\s*\(type \d+\)\s*','',header)
  return dict(index=idx,**row,header=header,signature=signature,body_sha256=hashlib.sha256(body).hexdigest(),wat_bytes=size,wat_sha256=hashlib.sha256(wat).hexdigest(),artifact=name,direct_calls=[dict(x)for x in dbs[key].execute('select callee,wat_line,wat_offset from calls where caller=? order by wat_offset',(idx,))]),ls
 entries={}
 for role,(old,new)in PAIRS.items():
  a,al=get('135',old);b,bl=get('138',new);sk_a,sk_b=skeleton(al),skeleton(bl)
  zipped=[]
  if len(al)==len(bl):
   for i,(x,y)in enumerate(zip(al,bl)):
    if x!=y:zipped.append(dict(instruction_ordinal=i,old=x,new=y,category='call_index'if x.startswith('call ')and y.startswith('call ')else'static_address_or_scalar_literal'if x.startswith(('i32.const','i64.const'))and y.startswith(('i32.const','i64.const'))else'other'))
  small_literals=[]
  for item in zipped:
   if item['category']=='static_address_or_scalar_literal':
    x=int(item['old'].rsplit(' ',1)[1]);y=int(item['new'].rsplit(' ',1)[1])
    if abs(x)<65536 or abs(y)<65536:small_literals.append(item)
  callmap=defaultdict(set)
  #Ordinal pairing is recorded only for same exact normalized instruction shape.
  if sk_a==sk_b:
   for x,y in zip(a['direct_calls'],b['direct_calls']):callmap[x['callee']].add(y['callee'])
  entries[role]=dict(old=a,new=b,signature_equal=a['signature']==b['signature'],raw_body_equal=a['body_sha256']==b['body_sha256'],instruction_lines_old=len(al),instruction_lines_new=len(bl),normalized_instruction_skeleton_equal=sk_a==sk_b,normalization='Drop comments/type-id,replace direct call indices/integer literal values/static mem offsets>=100000; not semantic equivalence.',zipped_instruction_differences=zipped,ordinal_call_candidate_map={str(k):sorted(v)for k,v in callmap.items()},ordinal_map_is_semantic_proof=False,small_integer_literal_changes=small_literals,required_new_runtime_acceptance=True)
  if role=='update_units':
   entries[role]['unit_stride_constants']={'old424_count':sum(x=='i32.const 424'for x in al),'new432_count':sum(x=='i32.const 432'for x in bl)}
   entries[role]['major_Game_memops']=[dict(x)for x in dbs['138'].execute('select operation,field_offset,count(*) as occurrences from memops where function_idx=? and field_offset in(1336,1416,1420,1424,1440,1536,1568,1572,1708,1712,1788,1792,2348,2352,2412,2587) group by operation,field_offset order by field_offset',(new,))]
 for db in dbs.values():db.close()
 save(out/'mapping.json',dict(status='bounded_static_candidates_guarded_not_runtime_acceptance',versions=sources,entries=entries,wat_read_bytes=read_bytes,full_WAT_read=False,producer_sha256=sha(Path(__file__)),original_executions=0,model_executions=0,Windows_executions=0,full880_frames=0,limitations=['These are guarded static entry candidates, not whole-function behavioral equivalence.','Normalized skeleton hides literal/address/callee changes; all actual changed instructions are retained where line counts match.','AI919 body grows and is not normalized-equal; new behavior and full Unit432 writer/consumer layout need fresh recovery.','Spawn/selection static table relocation requires new data extraction; same control shape does not prove table data equality.','135 original differential counts do not transfer to138.']))
 print(json.dumps(dict(directory=str(out),mapping_sha256=sha(out/'mapping.json'),wat_read_bytes=read_bytes,roles={k:dict(old=v['old']['index'],new=v['new']['index'],signature=v['new']['signature'],skeleton=v['normalized_instruction_skeleton_equal'],body_equal=v['raw_body_equal'])for k,v in entries.items()},original_executions=0)))
if __name__=='__main__':main()
