#!/usr/bin/env python3
"""Pure real-asset placement plan and historical read-set order comparison.

This executes no original code and is not a new original6730 differential.
The asset manifest is an explicit local input, never a WASM memory snapshot.
"""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
from source_closure135 import core_sources
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from resource_spec.world_placements135 import load_world_placements,select_collision_instances,first_chain_requests
from resource_spec.entry_resources135 import canonical_chain_name
from resource_spec.wmo_geometry135 import parse_wmo_collision,WmoRoot135,root_group_paths

INVENTORY=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
INVENTORY_SHA='cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'
FILES=('scripts/plan_world_placements135.py','scripts/source_closure135.py',
 'reconstruction/resource_spec/__init__.py','reconstruction/resource_spec/world_placements135.py',
 'reconstruction/resource_spec/wmo_geometry135.py','reconstruction/resource_spec/entry_resources135.py',
 'reconstruction/resource_spec/dbc.py')+core_sources(ROOT,'binary32.py')

def sha(p):
    with Path(p).open('rb')as h:return hashlib.file_digest(h,'sha256').hexdigest()

def json_instance(instance):
    value=asdict(instance);value['name_utf8_hex']=value.pop('name_utf8').hex()
    value['source_file_hex']=value.pop('source_file').hex();value['chain']=instance.chain.decode('utf8')
    return value

def main():
    assert sha(INVENTORY)==INVENTORY_SHA
    before={p:sha(ROOT/p)for p in FILES}
    inventory=json.loads(INVENTORY.read_text());assets={r['chain'].encode():r for r in inventory['requests']if r['status']==200}
    requests=[];loaded={}
    def provider(name):
        chain=canonical_chain_name(name);row=assets[chain]
        data=Path(row['file']).read_bytes();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']
        loaded[chain]=row;requests.append(chain);return data
    center=tuple(map(f.from_float,(-9396,-633)));extent=f.from_float(140)
    tiles=load_world_placements(0,center,provider)
    selections={phase:select_collision_instances(tiles,center,extent,phase=phase)for phase in('nav_m2','nav_wmo','secondary_wmo')}
    m2_requests=first_chain_requests(selections['nav_m2'])
    root_requests=first_chain_requests(selections['nav_wmo']+selections['secondary_wmo'])
    historical_m2=tuple(n for n in assets if n.endswith(b'.m2'))
    historical_roots=tuple(n for n in assets if n.endswith(b'.wmo')and isinstance(parse_wmo_collision(provider(n)),WmoRoot135))
    historical_wmo=tuple(n for n in assets if n.endswith(b'.wmo'))
    planned_wmo=[]
    for name in root_requests:
        root=parse_wmo_collision(provider(name));assert isinstance(root,WmoRoot135)
        planned_wmo.append(name)
        planned_wmo.extend(n.encode()for n in root_group_paths(name.decode(),root))
    assert len(tiles)==9 and len(m2_requests)==31 and len(root_requests)==23
    assert m2_requests==historical_m2 and root_requests==historical_roots and tuple(planned_wmo)==historical_wmo
    after={p:sha(ROOT/p)for p in FILES};assert before==after
    assert all(sha(row['file'])==row['sha256']for row in loaded.values())
    output=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-placements0135-plan-%Y%m%dT%H%M%S.%fZ');output.mkdir()
    plan=dict(kind='independent_local_asset_plan_historical_read_set_comparison',version='0.135.1',build='0898d5e3',
        inventory=str(INVENTORY.relative_to(ROOT)),inventory_sha256=INVENTORY_SHA,
        center_xy_bits=center,extent_bits=extent,adt_requests=[n.decode()for n,_ in tiles],
        placement_counts=dict(m2=sum(len(t.m2)for _,t in tiles),wmo=sum(len(t.wmo)for _,t in tiles)),
        selections={phase:[json_instance(p)for p in rows]for phase,rows in selections.items()},
        counts={phase:dict(instances=len(rows),unique_chains=len(first_chain_requests(rows)))for phase,rows in selections.items()},
        first_m2_requests=[n.decode()for n in m2_requests],first_wmo_root_requests=[n.decode()for n in root_requests],
        first_wmo_all_requests=[n.decode()for n in planned_wmo],
        historical_comparison=dict(m2_first31_order_equal=True,wmo_root_first23_order_equal=True,wmo_root_group_first410_order_equal=True),
        actual_inputs={n.decode():dict(bytes=r['bytes'],sha256=r['sha256'],file=r['file'])for n,r in loaded.items()},
        production_inputs_contain_memory_snapshot=False,new_original_calls=0,new_original6730_cases=0,
        full_world_producer=False,selection_original_differential=False,
        source_sha256_before=before,source_sha256_after=after,source_count=len(before))
    for name,h in before.items():
        path=output/'source-snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes());assert sha(path)==h
    path=output/'plan.json';path.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(directory=str(output),sha256=sha(path),placement_counts=plan['placement_counts'],counts=plan['counts'],new_original_calls=0)))

if __name__=='__main__':main()
