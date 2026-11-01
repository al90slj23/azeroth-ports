#!/usr/bin/env python3
"""Bounded original-WAT/data identity for independent final world caches.

Reads exact indexed function ranges and original static data; never executes
the original or reads a snapshot. This is static evidence, not new cases.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3,struct,sys
sys.dont_write_bytecode=True
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source
from build_upgrade134_oracle import sha,source_memory

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'


def main():
    source=SOURCE.read_bytes();assert hashlib.sha256(source).hexdigest()==SOURCE_SHA
    _,_,_,bodies,segments=parse_source(source)
    raw,offset,segment=source_memory(source,segments,5456016+96,28)
    assert struct.unpack('<7I',raw)==(0,12,3323121664,3290316800,1116209152,1070386381,1123024896)
    assert sha(PROFILE/'index.sqlite')=='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-cache0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);functions=[];texts={}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        for index in(6730,15374,9328,12375,18572,18670,84193):
            lo,hi=con.execute('SELECT wat_start,wat_end FROM functions WHERE idx=?',(index,)).fetchone()
            wat.seek(lo);text=wat.read(hi-lo);texts[index]=text;path=out/f'{index}.wat';path.write_bytes(text)
            start,end=bodies[index]
            functions.append(dict(index=index,body_sha256=hashlib.sha256(source[start:end]).hexdigest(),wat_sha256=sha(path),wat_start=lo,wat_end=hi))
    con.close()
    assert b'f32.const 0x1.99999ap-4'in texts[6730]and b'f32.const 0x1.8p+1'in texts[6730]
    assert b'call 15374'in texts[6730]and b'i32.const 1\n                                    i32.xor\n                                    i32.or'in texts[6730]
    result=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,functions=functions,
        static_zone0=dict(address=5456016,fields_address=5456112,fields96to123_hex=raw.hex(),file_offset=offset,data_segment=segment,
            map_id=0,center_xy_bits=[3323121664,3290316800],fallback_z_bits=1116209152,heading_bits=1070386381,radius_bits=1123024896),
        instruction_ranges=dict(grid_extent_radius_plus20=[473,493],fallback_zone112_via_app3704=[3426,3429],
            nav_ground_no_primary=[6616,6689],nav_center_seed=[8249,8305],free_boundary_iterator=[8330,8785],
            bfs_four_neighbors=[9014,9063],nav_final_unvisited_or1=[9374,9403],secondary_nan_init=[10088,10133],
            secondary_terrain_filter_max_merge=[10204,10295],secondary_absent_if_no_update=[10312,10327]),
        rc_layout=dict(nav=[32,36,40,44,48,52],primary=[56,72,76,80,84,88],secondary=[92,96,100,104,108,112],fallback=116,flat_flag=120),
        domain='Successfulnonflat/no-primary pipeline;fullindependent ownership/menu/render not claimed',
        new_original_calls=0,snapshots_read=False,original_executed=False,
        production_source_sha256=sha(ROOT/'reconstruction/resource_spec/world_cache135.py'),reviewer_source_sha256=sha(Path(__file__)))
    target=out/'trace.json';target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),trace_sha256=sha(target),original_executed=False,snapshots_read=False)))


if __name__=='__main__':main()
