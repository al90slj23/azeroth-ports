#!/usr/bin/env python3
"""Pure local WDT->ADT terrain composition replay; never execute original code."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]
FILES=('scripts/check_terrain135_local.py','reconstruction/resource_spec/__init__.py',
 'reconstruction/resource_spec/terrain135.py','reconstruction/resource_spec/entry_resources135.py',
 'reconstruction/resource_spec/mpq.py','reconstruction/resource_spec/dbc.py',
 'reconstruction/core_spec/__init__.py','reconstruction/core_spec/binary32.py','reconstruction/core_spec/upgrade_values.py')
def sha(p):
 with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
BEFORE={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from resource_spec.terrain135 import load_terrain_tiles,sample_terrain
from resource_spec.mpq import Archive


def main():
 inventory_path=ROOT/'evidence/entry-resources135-local-inventory-20261101T072438.139967Z/inventory.json'
 inventory=json.loads(inventory_path.read_text());by_name={r['chain_name']:r for r in inventory['resources']}
 base=ROOT/'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'
 archives={};reads=[]
 def provider(name):
  name=name.decode();row=by_name[name]
  if row['archive']not in archives:archives[row['archive']]=Archive(base/row['archive'])
  data=archives[row['archive']].read(name);h=hashlib.sha256(data).hexdigest()
  assert h==row['sha256']and len(data)==row['bytes']
  reads.append(dict(name=name,bytes=len(data),sha256=h));return data
 rows=[]
 for zone in inventory['regions']:
  xy=tuple(zone['center_xyz_bits'][:2]);loaded=load_terrain_tiles(zone['map_id'],xy,provider)
  assert [n.decode()for n,t in loaded]==zone['adt_order']
  sample=sample_terrain(tuple(t for n,t in loaded),*xy)
  rows.append(dict(zone=zone['zone'],map_id=zone['map_id'],center_xy_bits=xy,
   adt_order=[n.decode()for n,t in loaded],terrain_chunk_count=sum(len(t.chunks)for n,t in loaded),terrain_only_center_sample=asdict(sample)))
 assert BEFORE=={n:sha(ROOT/n)for n in FILES}
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('terrain135-local-replay-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 for n in FILES:
  target=out/'source-snapshot'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes())
 result=dict(version='0.135.1',build='0898d5e3',status='passed independent local composition,not original differential',
  source_sha256_before=BEFORE,source_sha256_after={n:sha(ROOT/n)for n in FILES},inventory_sha256=sha(inventory_path),
  zones=rows,asset_reads=reads,unique_assets=len({x['name']for x in reads}),
  original_executed=False,network_used=False,user_saves_accessed=False,original_VFS_or_cache_forged=False,
  limitations=['Terrain-only center samples exclude M2/WMO,cachedraster,collision,navigation andzone-specific world construction.',
   'This independent executable composition adds no original cases to107 fullADT differential receipt.'])
 (out/'replay.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(directory=str(out),zones=len(rows),asset_reads=len(reads),unique_assets=result['unique_assets'],original_executed=False)))


if __name__=='__main__':main()
