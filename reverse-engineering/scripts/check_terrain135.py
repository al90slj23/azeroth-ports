#!/usr/bin/env python3
"""Expected-first genuine local ADT producer/height differential, no VFS stubs."""
from pathlib import Path
from dataclasses import asdict,replace
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from source_closure135 import core_sources

FILES=('scripts/check_terrain135.py','scripts/run_terrain135_oracle.mjs','scripts/source_closure135.py',
 'scripts/build_full135_oracle.py','scripts/full135_host.mjs','scripts/build_upgrade134_oracle.py',
 'reconstruction/resource_spec/__init__.py','reconstruction/resource_spec/terrain135.py',
 'reconstruction/resource_spec/entry_resources135.py','reconstruction/resource_spec/dbc.py','reconstruction/resource_spec/mpq.py')+core_sources(ROOT,'binary32.py')
def sha(p):
 with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
IMPORT_HASH={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from resource_spec.mpq import Archive
from resource_spec.terrain135 import parse_adt_height,sample_chunk,sample_tile,sample_terrain,sample_world,tile_from_chunks,HeightRaster135,TILE,CHUNK

RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
INVENTORY=ROOT/'evidence/entry-resources135-local-inventory-20261101T072438.139967Z/inventory.json'
DATA=ROOT/'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'

def producer(chunk):
 raw=b''.join(struct.pack('<3I',*v)for v in chunk.vertices)
 return dict(vertex_count=len(chunk.vertices),vertices_sha256=hashlib.sha256(raw).hexdigest(),holes=chunk.holes)

def strict_equal(a,b):
 if type(a)is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys()and all(strict_equal(a[k],b[k])for k in a)
 if isinstance(a,list):return len(a)==len(b)and all(strict_equal(x,y)for x,y in zip(a,b))
 return a==b

def consumer_matrix(chunks,tiles):
 rows=[];v=chunks[0].vertices[0];b=f.from_float
 def add(kind,x,y,**kwargs):
  args=dict(kwargs)
  if kind=='holes':value=sample_chunk(replace(chunks[0],holes=args['holes']),x,y)
  else:
   for key in('primary','secondary'):
    if key in args:args[key]=HeightRaster135(tuple(args[key]['values_bits']),tuple(args[key]['origin_xy_bits']),args[key]['width'])
   value=sample_world(tiles,x,y,**args)
  rows.append(dict(kind=kind,x_bits=x,y_bits=y,**kwargs,expected=asdict(value)))
 for bit in range(16):
  row=(bit>>2)*2;col=(bit&3)*2;x=f.sub(v[0],f.mul(b((row+.25)/8),CHUNK));y=f.sub(v[1],f.mul(b((col+.25)/8),CHUNK))
  for holes in(0,1<<bit):add('holes',x,y,holes=holes)
 x=f.sub(v[0],b(.25));y=f.sub(v[1],b(.25));origin=(f.sub(x,b(.25)),f.sub(y,b(.25)))
 for word in(b(-1000000),b(1000000),0x7fc12345,0x7f800000,0xff800000,0,0x80000000):
  for key in('primary','secondary'):
   raster=dict(values_bits=[word]*4,origin_xy_bits=origin,width=2)
   add('raster',x,y,**{key:raster})
 for dx,dy in((-.001,0),(0,-.001),(.9999,0),(1,0),(0,1)):
  px=f.add(origin[0],b(dx));py=f.add(origin[1],b(dy))
  for key in('primary','secondary'):
   add('raster',px,py,**{key:dict(values_bits=[b(1000000),0x7fc12345,b(-1000000),b(123)],origin_xy_bits=origin,width=2)})
 return rows

def expected(data,*,with_matrix=False):
 chunks=parse_adt_height(data);tiles=(tile_from_chunks(chunks),);bounds=tiles[0].bounds_bits;samples=[];flat=f.from_float(-77.25)
 # Different sides of the four-triangle fan, grid edges, outside and exact corners.
 fractions=((0,0),(.03,.09),(.09,.03),(.09,.09),(.03,.03),(.5,.5),(.999,.999),(1,1),(-.0001,.5),(1.0001,.5))
 selected=tuple(dict.fromkeys((0,len(chunks)//2,len(chunks)-1,*next(((i,)for i,c in enumerate(chunks)if c.holes),()))))
 for ci in selected:
  origin=chunks[ci].vertices[0]
  for a,b in fractions:
   #5795 local unit is1/16th of a tile.
   step=f.div(TILE,f.from_float(16))
   x=f.sub(origin[0],f.mul(f.from_float(a),step));y=f.sub(origin[1],f.mul(f.from_float(b),step))
   samples.append(dict(chunk_index=ci,x_bits=x,y_bits=y,expected=dict(chunk=asdict(sample_chunk(chunks[ci],x,y)),tile=asdict(sample_tile(chunks,x,y)),
    terrain=asdict(sample_terrain(tiles,x,y)),world=asdict(sample_world(tiles,x,y)),flat=asdict(sample_world(tiles,x,y,flat_height_bits=flat)))))
 matrix=consumer_matrix(chunks,tiles)if with_matrix else[]
 return dict(producer=[producer(c)for c in chunks],samples=[s['expected']for s in samples],consumer_matrix=[r['expected']for r in matrix]),bounds,samples,flat,matrix

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=('pilot','current','full'),default='pilot');args=p.parse_args()
 before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_HASH
 resources=[x for x in json.loads(INVENTORY.read_text())['resources']if x['chain_name'].endswith('.adt')]
 if args.phase!='full':resources=[x for x in resources if x['bytes']<=1048576]
 if args.phase=='pilot':
  folders=('Kalimdor','PVPZone01','Stratholme Raid');resources=[min((x for x in resources if x['chain_name'].split('\\')[2]==name),key=lambda x:x['bytes'])for name in folders]
 out,manifest=build(['adt_parse','chunk_height','tile_height','terrain_height','world_height']);snap=out/'source-snapshot';snap.mkdir();assets=out/'actual-assets';assets.mkdir()
 for n,h in before.items():
  target=snap/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
 archive={};cases=[]
 for row in resources:
  archive.setdefault(row['archive'],None)
  if archive[row['archive']]is None:archive[row['archive']]=Archive(DATA/row['archive'])
  data=archive[row['archive']].read(row['chain_name']);assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']
  ident=len(cases);path=assets/f'{ident}.adt';path.write_bytes(data);e,bounds,samples,flat,matrix=expected(data,with_matrix=ident==0)
  cases.append(dict(id=ident,chain_name=row['chain_name'],archive=row['archive'],asset_path=str(path),asset_bytes=len(data),asset_sha256=row['sha256'],
   bounds_bits=bounds,flat_height_bits=flat,samples=[{k:v for k,v in s.items()if k!='expected'}for s in samples],consumer_matrix=[{k:v for k,v in s.items()if k!='expected'}for s in matrix],expected=e))
 fixture=out/'terrain135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==json.loads(json.dumps(cases))
 cases=json.loads(fixture.read_text())
 frozen_paths=[fixture,out/'manifest.json',out/manifest['module_file'],*assets.iterdir()]
 frozen_artifacts={str(p.relative_to(out)):sha(p)for p in frozen_paths}
 assert before=={n:sha(ROOT/n)for n in FILES};result=out/'terrain135-results.jsonl';stderr=out/'terrain135-stderr.log';assert sha(RUNTIME)==RUNTIME_SHA
 command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_terrain135_oracle.mjs'),str(out),str(fixture)];start=time.monotonic()
 with result.open('w')as stream,stderr.open('w')as err:
  child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
 after={n:sha(ROOT/n)for n in FILES};assert before==after
 assert frozen_artifacts=={str(p.relative_to(out)):sha(p)for p in frozen_paths}
 rows=[json.loads(x)for x in result.read_text().splitlines()];failures=[]
 if [r['id']for r in rows]!=list(range(len(cases))):failures.append(dict(error='Actual result case identity/count differs'))
 for c,r in zip(cases,rows):
  actual={k:r[k]for k in('producer','samples','consumer_matrix')}
  if not strict_equal(c['expected'],actual):failures.append(dict(id=c['id'],chain_name=c['chain_name'],expected=c['expected'],actual=actual))
 mismatch=out/'terrain135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
 artifacts=[fixture,result,stderr,mismatch]+list(out.glob('terrain135-original-*'))+list(out.glob('terrain135-failure-*'))+list(assets.iterdir())
 runtime=out/'terrain135-runtime.json'
 if runtime.exists():artifacts.append(runtime)
 receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,status='passed'if code==0 and len(rows)==len(cases)and not failures else'failed_preserved',
  cases=len(cases),completed_cases=len(rows),chunks=sum(len(c['expected']['producer'])for c in cases),samples=sum(len(c['samples'])for c in cases),
  mismatch_cases=len(failures),source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],
  manifest_sha256=sha(out/'manifest.json'),frozen_artifacts_sha256=frozen_artifacts,artifacts={str(p.relative_to(out)):sha(p)for p in artifacts},runtime=json.loads(runtime.read_text())if runtime.exists()else None,
  process=dict(command=command,pid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),expected_before_original=True,source_snapshots=True,
  inventory_sha256=sha(INVENTORY),strict_types_shapes_values=True,comparison_masks=[],nan_relaxation=False,
  controlled_consumer_matrix_cases=sum(len(c['consumer_matrix'])for c in cases),
  input_assets=[dict(chain_name=c['chain_name'],archive=c['archive'],bytes=c['asset_bytes'],sha256=c['asset_sha256'])for c in cases],
  limitations=['Only vertex145 XYZ+holes producer projection compared;complete264B geometry fields preserved as raw original sidecar,not independently reproduced.',
   'World height inputs use explicit one-tile bounding box and absent raster caches;not the complete6730 world producer.',
   'Current local base MPQ assets are not proof of complete latest135 assets. No SELF/VFS/Once/cache forged.'])
 (out/'terrain135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),status=receipt['status'],cases=len(cases),completed=len(rows),mismatches=len(failures),exit_code=code)))
 if receipt['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
