#!/usr/bin/env python3
"""Local/static world-cache contract checks, explicitly zero original cases.

Full real-asset historical comparison belongs to the parent world-bundle CLI.
This command does not read a snapshot or instantiate an original module.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from source_closure135 import core_sources

FILES=('scripts/check_world_cache135.py','scripts/source_closure135.py',
 'reconstruction/resource_spec/__init__.py')+tuple('reconstruction/resource_spec/'+name+'.py'for name in(
 'world_cache135','terrain135','world_query135','world_raster135','wmo_geometry135','entry_resources135','dbc'))+core_sources(ROOT,'binary32.py','binary32_sqrt.py','ai_trig135.py')
def sha(path):
    with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    before={p:sha(ROOT/p)for p in FILES}
    from core_spec import binary32 as f
    from resource_spec.terrain135 import TerrainChunk135,tile_from_chunks
    from resource_spec.world_cache135 import(CacheGrid135,cache_grid135,ground_grid135,
        merge_secondary135,seal_unreachable_nav135,CacheBoundsTrap135)
    b=f.from_float;checks=[]
    actual=cache_grid135((b(-9396),b(-633)),b(120))
    assert tuple(map(f.to_float,actual.origin_xy_bits))==(-9536.,-773.)and actual.nav_width==280 and actual.secondary_width==560
    checks.append('zone120+20/origin/nav280/secondary560')
    fractional=cache_grid135((0,0),b(120.125));assert(fractional.nav_width,fractional.secondary_width)==(281,561)
    checks.append('secondary ceil before integer doubling,not2*ceil')
    grid=CacheGrid135((b(4),b(4)),(0,0),8,16)
    def terrain(size):
        vertices=tuple((b(x),b(y),0)for x,y in((size,size),(0,size),(size,0),(0,0)))
        return(tile_from_chunks((TerrainChunk135(vertices,indices=(0,1,2,1,3,2)),)),)
    tiles=terrain(8);assert ground_grid135(tiles,grid)==(0,)*64;checks.append('ground1mcellcentres/terrain0')
    pairs=[(0,b(.1)),(1,b(.1)+1),(2,b(3)),(3,b(3)+1),(2,b(2)),(4,0x7fc01234),(5,0x7f800000),(2,b(3)),(6,b(1)),(6,b(2))]
    stats={};r=merge_secondary135(tiles,grid,pairs,stats=stats)
    assert r.values_bits[:7]==(0x7fc00000,b(.1)+1,b(3),0x7fc00000,0x7fc00000,0x7fc00000,b(2))
    assert sum(not f.is_nan(x)for x in r.values_bits)==3
    checks.extend(('strict lower+.1/exactupper+3','NaN/Inf rejection','ordered duplicate max'))
    assert merge_secondary135(tiles,grid,[(0,b(.1))])is None;checks.append('all-rejected secondary absent')
    assert merge_secondary135(tiles,grid,[(256,b(1))])is None;checks.append('terrainmiss precedes candidatebounds')
    try:merge_secondary135(terrain(16),grid,[(256,b(1))])
    except CacheBoundsTrap135:pass
    else:raise AssertionError('Accepted invalid candidate must trap')
    checks.append('eligible candidatebounds trap')
    assert seal_unreachable_nav135(bytes(64),grid)==bytes(64);checks.append('free perimeter/centre remain free')
    assert seal_unreachable_nav135(bytes([1])*64,grid)==bytes([1])*64;checks.append('allblocked remains blocked')
    nav=bytearray(64)
    for x,y in((1,0),(0,1),(2,1),(1,2)):nav[y*8+x]=1
    assert seal_unreachable_nav135(bytes(nav),grid)[9]==1;checks.append('diagonal contact doesnot connect four-neighbour room')
    nav=bytearray(64)
    for x,y in((4,3),(3,4),(5,4),(4,5)):nav[y*8+x]=1
    assert seal_unreachable_nav135(bytes(nav),grid)[36]==0;checks.append('closedfreecentre retained')
    nav[2*8+2]=2;assert seal_unreachable_nav135(bytes(nav),grid)[18]==3;checks.append('final OR preserves rawbyte semantics')
    assert before=={p:sha(ROOT/p)for p in FILES}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-cache0135-local-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    for p,h in before.items():dst=out/'source-snapshot'/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/p).read_bytes());assert sha(dst)==h
    result=dict(status='passed_local_static_contracts',checks=checks,count=len(checks),source_sha256=before,
        controlled_merge_input_pairs=pairs,controlled_merge_stats=stats,
        original_executed=False,new_original_cases=0,snapshots_read=False,
        full_original_or_historical_world_comparison=False,
        limitation='Controlled local contracts from static6730 rules;not original differential or fullassetworld acceptance')
    target=out/'check.json';target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),sha256=sha(target),checks=len(checks),original_executed=False,snapshots_read=False)))


if __name__=='__main__':main()
