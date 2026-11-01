#!/usr/bin/env python3
"""Independent frozen-snapshot/real-bytes reviews; never instantiate original WASM."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
import argparse,ast,collections,hashlib,importlib.util,json,sqlite3,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
ORIGINAL_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(x).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def norm(x):return json.loads(json.dumps(x,allow_nan=False))
def strict(a,b):
 if type(a)is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys()and all(strict(a[k],b[k])for k in a)
 if isinstance(a,list):return len(a)==len(b)and all(strict(x,y)for x,y in zip(a,b))
 return a==b
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');assert strict(load(p),norm(x))
def uint(raw,p):
 value=shift=0
 while True:
  b=raw[p];p+=1;value|=(b&127)<<shift
  if b<128:return value,p
  shift+=7;assert shift<64
def sections(raw):
 assert raw[:8]==b'\0asm\1\0\0\0';p=8;rows=[]
 while p<len(raw):
  start=p;kind=raw[p];n,p=uint(raw,p+1);rows.append((kind,raw[start:p+n],p,p+n));p+=n
 assert p==len(raw);return rows
def exports(raw,section):
 n,p=uint(raw,section[2]);rows=[]
 for _ in range(n):
  size,p=uint(raw,p);name=raw[p:p+size].decode();p+=size;kind=raw[p];idx,p=uint(raw,p+1);rows.append((name,kind,idx))
 assert p==section[3];return rows
def identity(batch,roles):
 original=ORIGINAL.read_bytes();assert digest(original)==ORIGINAL_SHA;ss=sections(original);module=(batch/'research135-exports.wasm').read_bytes();mm=sections(module);manifest=load(batch/'manifest.json')
 assert [(k,x)for k,x,*_ in ss if k!=7]==[(k,x)for k,x,*_ in mm if k!=7]and not any(k==8 for k,*_ in ss)
 assert manifest['original_wasm_sha256']==ORIGINAL_SHA and manifest['module_sha256']==digest(module)and manifest['denied_function_import_count']==878
 n,p=uint(original,next(s for s in ss if s[0]==1)[2]);types=[]
 for _ in range(n):
  assert original[p]==0x60;p+=1;a,p=uint(original,p);params=original[p:p+a].hex();p+=a;b,p=uint(original,p);results=original[p:p+b].hex();p+=b;types.append((params,results))
 n,p=uint(original,next(s for s in ss if s[0]==3)[2]);decl=[]
 for _ in range(n):t,p=uint(original,p);decl.append(t)
 n,p=uint(original,next(s for s in ss if s[0]==10)[2]);bodies=[]
 for _ in range(n):size,p=uint(original,p);bodies.append((p,p+size));p+=size
 assert {r['role']:r['index']for r in manifest['roles']}==roles
 for r in manifest['roles']:
  idx=r['index'];a,b=bodies[idx-878];assert(a,b)==(r['body_start'],r['body_end']);assert digest(original[a:b])==r['body_sha256'];assert types[decl[idx-878]]==(r['parameters_hex'],r['results_hex'])
 old=exports(original,next(s for s in ss if s[0]==7));new=exports(module,next(s for s in mm if s[0]==7));assert new[:len(old)]==old and new[len(old):]==[(r['export'],0,r['index'])for r in manifest['roles']]
 return manifest
def closure(snapshot,entries):
 todo=['reconstruction/core_spec/__init__.py',*entries];seen=set()
 while todo:
  name=todo.pop()
  if name in seen:continue
  seen.add(name);path=snapshot/name;assert path.is_file(),name
  if name.startswith('reconstruction/'):
   init=str(Path(name).parent/'__init__.py')
   if init!=name:todo.append(init)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom):
    if node.level:
     assert node.level==1
     parts=[node.module]if node.module else[x.name for x in node.names];todo.extend(str(Path(name).parent/(x.replace('.','/')+'.py'))for x in parts)
    elif node.module in('core_spec','resource_spec'):todo.extend('reconstruction/'+node.module+'/'+x.name+'.py'for x in node.names)
    elif node.module and node.module.startswith(('core_spec.','resource_spec.')):todo.append('reconstruction/'+node.module.replace('.','/')+'.py')
   if isinstance(node,ast.Call)and isinstance(node.func,ast.Name):assert node.func.id!='__import__'
 return sorted(seen)
def frozen(batch,receipt):
 hashes=receipt['source_sha256_before'];assert hashes==receipt['source_sha256_after'];snap=batch/'source-snapshot';drift={}
 assert sha(batch/'manifest.json')==receipt['manifest_sha256']and sha(batch/'research135-exports.wasm')==receipt['module_sha256']
 for n,h in hashes.items():
  assert sha(snap/n)==h
  current=sha(ROOT/n)
  if current!=h:drift[n]=dict(frozen=h,current=current)
 for n,h in receipt['artifacts'].items():assert sha(batch/n)==h,n
 for n,h in receipt.get('frozen_artifacts_sha256',{}).items():assert sha(batch/n)==h,n
 return snap,drift
def checker(snapshot,name):
 for key in list(sys.modules):
  if key.startswith(('core_spec','resource_spec'))or key in('build_full135_oracle','build_upgrade134_oracle','source_closure135'):del sys.modules[key]
 sys.path.insert(0,str(snapshot/'scripts'));sys.path.insert(0,str(snapshot/'reconstruction'));spec=importlib.util.spec_from_file_location('independent_frozen_'+name,snapshot/'scripts'/name);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def terrain(out):
 batch=ROOT/'evidence/full0135-oracle-20261101T080051.480589Z';receipt_path=batch/'terrain135-comparison.json';receipt=load(receipt_path);assert sha(receipt_path)=='45a2501da4ceef05fa66992bf45df30f5aaa2c4502e0dc9e22c94a12b8ca5be7'
 snap,drift=frozen(batch,receipt);manifest=identity(batch,dict(adt_parse=1446,chunk_height=5795,tile_height=46295,terrain_height=18670,world_height=29631));prod=closure(snap,['reconstruction/resource_spec/terrain135.py','reconstruction/resource_spec/mpq.py']);assert set(prod)<=receipt['source_sha256_before'].keys()and len(receipt['source_sha256_before'])==14
 author=checker(snap,'check_terrain135.py');fixtures=load(batch/'terrain135-fixtures.json');observed=[json.loads(x)for x in(batch/'terrain135-results.jsonl').read_text().splitlines()];assert [x['id']for x in observed]==list(range(107))
 inventory=load(ROOT/'evidence/entry-resources135-local-inventory-20261101T072438.139967Z/inventory.json');assert sha(ROOT/'evidence/entry-resources135-local-inventory-20261101T072438.139967Z/inventory.json')==receipt['inventory_sha256'];adts={x['chain_name']:x for x in inventory['resources']if x['chain_name'].endswith('.adt')};assert {c['chain_name']for c in fixtures}==adts.keys()
 totals=collections.Counter();actual_assets={}
 for c,a in zip(fixtures,observed):
  payload=(batch/'actual-assets'/f'{c["id"]}.adt').read_bytes();row=adts[c['chain_name']];assert len(payload)==c['asset_bytes']==row['bytes']and digest(payload)==c['asset_sha256']==row['sha256'];actual_assets[c['chain_name']]=payload
  expected,bounds,samples,flat,matrix=author.expected(payload,with_matrix=c['id']==0)
  assert strict(norm(expected),c['expected']);assert strict(norm(bounds),c['bounds_bits']);assert strict([{k:v for k,v in norm(s).items()if k!='expected'}for s in samples],c['samples']);assert flat==c['flat_height_bits'];assert strict([{k:v for k,v in norm(q).items()if k!='expected'}for q in matrix],c['consumer_matrix'])
  assert strict(c['expected'],{k:a[k]for k in('producer','samples','consumer_matrix')})
  chunks=author.parse_adt_height(payload);raw_vertices=b''.join(struct.pack('<3I',*v)for ch in chunks for v in ch.vertices);vp=batch/f'terrain135-original-{c["id"]}-vertices.bin';rp=batch/f'terrain135-original-{c["id"]}-records264.bin';records=rp.read_bytes()
  assert raw_vertices==vp.read_bytes()and digest(raw_vertices)==a['raw_vertices_sha256'];assert len(records)==len(chunks)*264 and digest(records)==a['raw_records264_sha256']
  for j,ch in enumerate(chunks):assert struct.unpack_from('<H',records,j*264+260)[0]==ch.holes and struct.unpack_from('<I',records,j*264+8)[0]==145
  totals.update(assets=1,asset_bytes=len(payload),chunks=len(chunks),vertices=sum(len(ch.vertices)for ch in chunks),vertex_bytes=len(raw_vertices),raw264_bytes=len(records),nonzero_holes=sum(ch.holes!=0 for ch in chunks),samples=len(samples),matrix=len(matrix),sample_found=sum(s['expected']['terrain']['found']for s in samples),sample_notfound=sum(not s['expected']['terrain']['found']for s in samples))
  if c['id']%25==0:print(json.dumps(dict(review='terrain',verified=c['id']+1)),flush=True)
 assert dict(totals)==dict(assets=107,asset_bytes=153802039,chunks=27392,vertices=3971840,vertex_bytes=47662080,raw264_bytes=7231488,nonzero_holes=213,samples=3650,matrix=56,sample_found=3586,sample_notfound=64)
 assert receipt['runtime']['calls']==107+3650*5+56==18413 and receipt['comparison_masks']==[]and receipt['nan_relaxation']is False
 # Independent local WDT->ADT replay from its own9source frozen snapshot.
 local_path=ROOT/'evidence/terrain135-local-replay-20261101T080701.038206Z/replay.json';local=load(local_path);ls=local_path.parent/'source-snapshot';assert local['source_sha256_before']==local['source_sha256_after']and len(local['source_sha256_before'])==9
 for n,h in local['source_sha256_before'].items():assert sha(ls/n)==h
 lc=closure(ls,['reconstruction/resource_spec/terrain135.py','reconstruction/resource_spec/mpq.py']);assert set(lc)<=local['source_sha256_before'].keys()
 local_author=checker(ls,'check_terrain135_local.py');byname={r['chain_name']:r for r in inventory['resources']};archives={};reads=[];zones=[]
 def provider(name):
  key=name.decode();r=byname[key]
  if key in actual_assets:payload=actual_assets[key]
  else:
   if r['archive']not in archives:archives[r['archive']]=local_author.Archive(ROOT/'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'/r['archive'])
   payload=archives[r['archive']].read(key)
  assert len(payload)==r['bytes']and digest(payload)==r['sha256'];reads.append(dict(name=key,bytes=len(payload),sha256=digest(payload)));return payload
 for z in inventory['regions']:
  xy=tuple(z['center_xyz_bits'][:2]);loaded=local_author.load_terrain_tiles(z['map_id'],xy,provider);assert[n.decode()for n,t in loaded]==z['adt_order'];sample=local_author.sample_terrain(tuple(t for n,t in loaded),*xy)
  zones.append(dict(zone=z['zone'],map_id=z['map_id'],center_xy_bits=list(xy),adt_order=[n.decode()for n,t in loaded],terrain_chunk_count=sum(len(t.chunks)for n,t in loaded),terrain_only_center_sample=asdict(sample)))
 assert strict(norm(zones),local['zones'])and strict(reads,local['asset_reads'])and len(reads)==120 and len({x['name']for x in reads})==114
 return dict(kind='terrain',receipt_sha256=sha(receipt_path),receipt=str(receipt_path.relative_to(ROOT)),sources=len(receipt['source_sha256_before']),production_closure=prod,current_source_drift=drift,roles=manifest['roles'],totals=dict(totals),local_replay=dict(path=str(local_path.relative_to(ROOT)),sha256=sha(local_path),sources=9,zone_count=12,read_count=120,unique_assets=114,original_cases_added=0),limitations=receipt['limitations']+['Real264B records are fully retained andchecked forvertexcount/holes,not semantically reproducedbeyonddeclared145XYZ projection.','Pure local replay center heights do not include M2/WMO floors,world cache producers orfull1089.'])


def geometry(out):
 batch=ROOT/'evidence/full0135-oracle-20261101T080844.947484Z';receipt_path=batch/'effect-geometry135-comparison.json';receipt=load(receipt_path);assert sha(receipt_path)=='94cbbfaf8d629037ac4739b334e1b6eda6642f4485467218d29a4d66508177b8'
 snap,drift=frozen(batch,receipt);manifest=identity(batch,dict(effect_tick=915,npc_action=910,spawn_boss=2785));prod=closure(snap,['reconstruction/core_spec/effect_geometry135.py','reconstruction/core_spec/spawn_boss135.py']);assert set(prod)<=receipt['source_sha256_before'].keys()and len(receipt['source_sha256_before'])==28
 author=checker(snap,'check_effect_geometry135.py');fixtures=load(batch/'effect-geometry135-fixtures.json');regenerated=author.corpus(False);assert strict(fixtures,regenerated);assert strict(author.guards(),load(batch/'effect-geometry135-guards.json'));actual=[json.loads(x)for x in(batch/'effect-geometry135-results.jsonl').read_text().splitlines()];assert[x['id']for x in actual]==list(range(390));failures,strict_bytes,unspecified=author.compare(fixtures,actual);assert not failures and strict_bytes==receipt['strict120_storage_bytes']and unspecified==receipt['unspecified_scratch_bytes']
 totals=collections.Counter();opcodes=collections.Counter();events=collections.Counter();denies=collections.Counter();initial_opcodes=collections.Counter();normal=prefix=0
 for c,row in zip(fixtures,actual):
  assert len(c['expected'])==len(row['stages'])==len(row['physical'])
  packet_cursor=json_cursor=0;previous=[];previous_json=[]
  for si,(e,a,p,masks)in enumerate(zip(c['expected'],row['stages'],row['physical'],c['unspecified_storage_bytes'])):
   assert len(e['storage'])==len(a['storage'])==len(masks)==64
   assert len(a['units'])==1 and len(bytes.fromhex(a['units'][0]))==424 and bytes.fromhex(a['units'][0])[248:252]==bytes(4)
   assert type(p['unit248_pointer'])is int and p['unit248_pointer']>0
   whole=bytes.fromhex(p['full_storage_hex']);assert whole==b''.join(bytes.fromhex(x)for x in a['storage'])and len(whole)==7680
   for ei,(x,y,mask)in enumerate(zip(e['storage'],a['storage'],masks)):
    assert mask in([],[20,21,22,23]);xb=bytes.fromhex(x);yb=bytes.fromhex(y);assert len(xb)==len(yb)==120
    for j,(u,v)in enumerate(zip(xb,yb)):
     if j in mask:totals['scratch_observation_bytes']+=1;totals['nonzero_scratch_bytes']+=int(v!=0)
     else:assert u==v;totals['strict_storage_bytes']+=1
   assert p['packets'][:packet_cursor]==previous and p['effect_json'][:json_cursor]==previous_json
   newly=[]if si==0 else p['packets'][packet_cursor:]
   if si==0:initial_opcodes.update(pkt['opcode']for pkt in p['packets']);totals['initial_boss_JSON_prefixes']+=len(p['effect_json'])
   assert[pkt['opcode']for pkt in newly]==a['new_packet_opcodes'];opcodes.update(pkt['opcode']for pkt in newly)
   for pkt in p['packets']:assert type(pkt['opcode'])is int and type(pkt['payload_hex'])is str;bytes.fromhex(pkt['payload_hex'])
   json_events=[]
   for raw in([]if si==0 else p['effect_json'][json_cursor:]):
    value=json.loads(raw);typ=value['type'];events[typ]+=1
    if typ=='hz':json_events.append({k:value[k]for k in('type','id','kind','shape')})
    elif typ=='hzend':json_events.append({k:value[k]for k in('type','id')})
    else:assert typ=='hzt';json_events.append(dict(type=typ))
   assert strict(json_events,a['new_effect_json_events'])
   packet_cursor=len(p['packets']);json_cursor=len(p['effect_json']);previous=p['packets'];previous_json=p['effect_json'];totals['stages']+=1;totals['unit_bytes_compared']+=424
  pending=c['expected'][-1]['entry_status']=='pending_original_spell_database'
  if pending:
   prefix+=1;assert row['stages'][-1]['entry_status']=='pending_original_spell_database'and c['ops'][-1]['expected_status']=='pending_original_spell_database';assert len(row['physical'][-1]['denied_host_calls'])==1;denies.update(row['physical'][-1]['denied_host_calls'])
   assert all('denied_host_calls'not in p for p in row['physical'][:-1]);totals['hp_changed_prefixes']+=int(c['expected'][0]['hp_1528_bits']!=c['expected'][-1]['hp_1528_bits'])
  else:normal+=1;assert all('denied_host_calls'not in p for p in row['physical'])
 assert(normal,prefix)==(277,113)and totals['stages']==2883 and totals['strict_storage_bytes']==22128144 and totals['scratch_observation_bytes']==13296 and totals['nonzero_scratch_bytes']==3324
 assert dict(opcodes)=={221:522,305:522,306:477}and dict(events)=={'hz':498,'hzt':1224,'hzend':477}
 assert dict(denies)=={'./wenilla_bg.js.__wbg_static_accessor_SELF_4c59f6c7ea29a144':113}and totals['hp_changed_prefixes']==98
 assert receipt['runtime']['producer_calls']==522 and receipt['runtime']['tick_calls']==1971 and receipt['runtime']['expected_host_boundaries']==113 and receipt['runtime']['successful_host_calls']==0
 return dict(kind='effect-geometry',receipt_sha256=sha(receipt_path),receipt=str(receipt_path.relative_to(ROOT)),sources=len(receipt['source_sha256_before']),production_closure=prod,current_source_drift=drift,roles=manifest['roles'],cases=390,normal_completed_cases=normal,expected_host_denial_prefix_cases=prefix,totals=dict(totals),packet_delta_opcodes=dict(opcodes),initial_boss_packet_prefixes=dict(initial_opcodes),effect_json_events=dict(events),denied_host_calls=dict(denies),guards=len(author.guards()),fixture_regeneration='strict exact all390 fromfrozenproduction',limitations=receipt['limitations']+['113 denied prefixes and98HPchanges are not complete/resumable915 entries.','Complete wirebytes/JSON strings are sidecars;only exactopcodes andtype/id/kind/shape/order plus gameplayrecordgeometry compared.','Initial2785 banner/packetprefix is preserved byteforbyte acrosslaterstages;its wirecodec/JSON is not a newindependentgeometry assertion.'])


def main():
 parser=argparse.ArgumentParser();parser.add_argument('kind',choices=('terrain','geometry'));args=parser.parse_args();name='terrain0135'if args.kind=='terrain'else'effect-geometry0135';out=ROOT/'evidence'/datetime.now(timezone.utc).strftime(name+'-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();(out/'reviewer-source.py').write_bytes(Path(__file__).read_bytes())
 result=(terrain if args.kind=='terrain'else geometry)(out);result.update(status='passed_scoped_independent_read_only_review',reviewer_sha256=sha(Path(__file__)),original_runtime_reexecuted=False,author_sources_modified=False);save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),kind=args.kind)),flush=True)
if __name__=='__main__':main()
