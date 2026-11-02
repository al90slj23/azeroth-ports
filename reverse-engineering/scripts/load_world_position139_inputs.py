"""Decode independent139 canonical producer artifacts, never originalmemory."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from resource_spec.terrain135 import TerrainChunk135,TerrainTile135,HeightRaster135
from resource_spec.world_query135 import WorldQueries135,NavGrid135

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load_world139_canonical(directory,receipt_sha256):
 directory=Path(directory);receipt=directory/'receipt.json';assert sha(receipt)==receipt_sha256;d=json.loads(receipt.read_text())
 assert d['version']=='0.139.0'and d['actual_build']=='f79c5e2b4'and d['kind']=='independent139_raw_assets_to_canonical_world'
 assert d['original_memory_read']is False and d['original_program_executed']is False and d['preparsed_world_input_read']is False
 assert d['source_sha256_before']==d['source_sha256_after']and d['assets_unchanged']is True
 rows=d['world_artifacts'];raws={}
 for name in('terrain','navigation','secondary'):
  row=rows[name];p=directory/row['file'];assert p.parent==directory and p.suffix.lower()not in('.memory','.wasm','.wat','.exe');assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];raws[name]=p.read_bytes()
 raw=raws['terrain'];pos=0
 def take(fmt):
  nonlocal pos
  n=struct.calcsize(fmt);assert pos+n<=len(raw);v=struct.unpack_from(fmt,raw,pos);pos+=n;return v
 count,=take('<I');assert count<=512;tiles=[]
 for _ in range(count):
  x0,y0,x1,y1,n=take('<5I');assert n<=1024;chunks=[]
  for _ in range(n):
   holes,vertices=take('<HI');assert vertices==145
   chunks.append(TerrainChunk135(tuple(take('<3I')for _ in range(vertices)),holes))
  tiles.append(TerrainTile135(tuple(chunks),(x0,y0,x1,y1)))
 assert pos==len(raw)
 nav=rows['navigation'];assert len(raws['navigation'])==nav['width']**2
 secondary=rows['secondary'];assert len(raws['secondary'])==secondary['width']**2*4
 scalars=d['query_scalars'];assert scalars['primary_present']is False and scalars['flat_present']is False
 world=WorldQueries135(tuple(tiles),None,HeightRaster135(tuple(x[0]for x in struct.iter_unpack('<I',raws['secondary'])),tuple(secondary['origin_xy_bits']),secondary['width']),
  NavGrid135(raws['navigation'],tuple(nav['origin_xy_bits']),nav['width']),scalars['fallback_height_bits'])
 return world,dict(receipt=str(receipt),receipt_sha256=receipt_sha256,world_artifacts=rows,query_scalars=scalars,source='Independent139rawassetproducer; generic135-named algorithms reusedwithoutoldacceptance',original_memory_input=False)
