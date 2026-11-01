#!/usr/bin/env python3
"""Bind independent motion flags/facing to fixed135 constructor instructions."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sqlite3,struct,sys
sys.dont_write_bytecode=True
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source
from build_upgrade134_oracle import source_memory,sha
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.initial_state135_data import ZONE_ENTRIES
from core_spec.headless_motion135 import ZERO_WORDS135,HeadlessMotionOwner135


def main():
    binary=SOURCE.read_bytes();assert hashlib.sha256(binary).hexdigest()==SOURCE_SHA
    _,_,_,bodies,segments=parse_source(binary)
    profile=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
    with sqlite3.connect((profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        lo,hi=db.execute('select wat_start,wat_end from functions where idx=1560').fetchone()
    with(profile/'official-0.135.1-full.wat').open('rb')as stream:
        stream.seek(lo);wat=stream.read(hi-lo)
    lines=wat.decode().splitlines();ops=[x.strip().split(' (;')[0]for x in lines]
    def find(sequence):
        matches=[i for i in range(len(ops)-len(sequence)+1)if ops[i:i+len(sequence)]==sequence]
        assert len(matches)==1,(sequence,matches)
        i=matches[0];return dict(line_start=i+1,line_end=i+len(sequence),text='\n'.join(lines[i:i+len(sequence)]))
    stores=[]
    for offset in (416,440,448,456,464,1744,1764):
        stores.append(dict(game_offset=offset,width=4,value=0,frame_offset=offset+88,
            proof=find(['local.get 3','i32.const 0',f'i32.store offset={offset+88}'])))
    stores.append(dict(game_offsets=[2496,2500],width=8,value=0,frame_offset=2584,
        proof=find(['local.get 3','i64.const 0','i64.store offset=2584'])))
    assert set(ZERO_WORDS135)=={416,440,448,456,464,1744,1764,2496,2500}
    heading_load=find(['local.get 8','f32.load offset=116','local.set 33'])
    heading_store=find(['local.get 3','local.get 33','f32.store offset=1516'])
    zones=[]
    for i,zone in enumerate(ZONE_ENTRIES):
        raw,at,segment=source_memory(binary,segments,5456016+152*i+116,4)
        value=struct.unpack('<I',raw)[0];assert value==zone[3]
        owner=HeadlessMotionOwner135.from_empty_constructor(i)
        assert owner.cells[444:448]==(None,)*4 and owner.cells[452:456]==(None,)*4
        zones.append(dict(index=i,heading_bits=value,address=5456016+152*i+116,file_offset=at,data_segment=segment))
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('headless-motion-owner135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    (out/'1560.wat').write_bytes(wat)
    begin,end=bodies[1560]
    result=dict(kind='static_constructor_motion_owner_proof_not_runtime_differential',version='0.135.1',actual_build='90898d5e3',
        original_wasm_sha256=SOURCE_SHA,constructor_body_sha256=hashlib.sha256(binary[begin:end]).hexdigest(),
        constructor_wat_sha256=hashlib.sha256(wat).hexdigest(),game_frame_offset=88,
        zero_stores=stores,heading_load=heading_load,heading_store=heading_store,static_zones=zones,
        unknown_payloads_not_filled=[420,424,428,432,436,444,452,460,1748,1752,1756,1760,1768,1772,1776,1780],
        production_sha256=sha(ROOT/'reconstruction/core_spec/headless_motion135.py'),trace_sha256=sha(Path(__file__)),
        original_calls=0,snapshot_reads=False,limitations=['Successful empty-profile constructor domain; other writers and naturalApp input production remain separate.'])
    p=out/'proof.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),proof_sha256=sha(p),original_executed=False)))


if __name__=='__main__':main()
