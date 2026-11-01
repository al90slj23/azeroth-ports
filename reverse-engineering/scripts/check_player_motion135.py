#!/usr/bin/env python3
"""Expected-first full2328 differential; real worldRc, legal snapshot only."""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode=True
from build_player_motion135_oracle import build_motion135
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA
from build_upgrade134_oracle import sha
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure

FILES=tuple(dict.fromkeys(('scripts/check_player_motion135.py','scripts/build_player_motion135_oracle.py',
    'scripts/run_player_motion135_oracle.mjs','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py',
    'scripts/production_closure135.py','scripts/source_closure137.py')+
    production_sources135(ROOT,'core_spec.player_motion135','resource_spec.world_query135')))
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.player_motion135 import (MotionMap135, MotionWorld135, MotionUnknownRead135,
    apply_player_motion135, decode_motion135)
from resource_spec.world_query135 import decode_world_snapshot

SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
G,WORLD=14554176,26204808
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def corpus(snapshot,world,pilot):
    baseline=bytes(snapshot[G:G+8192]);cx,cy=MotionMap135.fixed_zone(0).center_xy_bits
    map_=MotionMap135.fixed_zone(0);rows=[]
    def add(group,x,y,z,patch=(),face=0):
        raw=bytearray(baseline)
        for o,v in patch:struct.pack_into('<I',raw,o,v)
        result=apply_player_motion135(bytes(raw),(x,y,z),face,world,map_)
        assert result.complete2328 and not result.begin_run_required
        rows.append(dict(id=len(rows),group=group,input=dict(id=len(rows),xyz_bits=(x,y,z),facing_bits=face,patch_words=patch),
            expected=dict(return_value=int(result.unchanged_input_xyz),game_before_hex=bytes(raw).hex(),game_after_hex=result.game_bytes.hex(),
                packets=result.packets,branch=result.branch),diagnostic=dict(writes=result.writes)))
    z=world.queries.height(cx,cy).value_bits
    add('same-real-position',cx,cy,z,face=0x3fc00000)
    add('real-small-xy',f.add(cx,f.from_float(1)),cy,z,patch=((2352,f.from_float(1)),))
    if pilot:return json.loads(json.dumps(rows))
    for dx,dy in ((-2,0),(0,2),(3,4),(-8,-6),(10,20),(50,0),(0,-60)):
        x,y=f.add(cx,f.from_float(dx)),f.add(cy,f.from_float(dy));h=world.queries.height(x,y);assert h.found
        for dz in (0,.5,20):add('real-terrain-accepted',x,y,f.add(h.value_bits,f.from_float(dz)),
            patch=((2352,f.from_float(3.25)),(440,1),(444,f.from_float(999.125)),(2496,1)),face=0x40c90fdb)
    for dx,dy in ((0,0),(100,0),(0,100)):
        x,y=f.add(cx,f.from_float(dx)),f.add(cy,f.from_float(dy));h=world.queries.height(x,y);assert h.found
        threshold=f.add(h.value_bits,f.from_float(-15))
        add('z-threshold-inclusive',x,y,threshold)
        lower=f.from_float(f.to_float(threshold)-.001)
        add('z-below-threshold-correction',x,y,lower,patch=((1644,0xffffffff),))
    for distance in (3,3.001,4):
        for now in (2.999,3):
            x,y=f.add(cx,f.from_float(distance)),cy;h=world.queries.height(x,y);assert h.found
            add('pending-distance-time-boundaries',x,y,h.value_bits,patch=((416,1),(420,cx),(424,cy),(436,0),(2352,f.from_float(now))))
    for dx,dy in ((131,0),(0,140),(-120,-100)):
        x,y=f.add(cx,f.from_float(dx)),f.add(cy,f.from_float(dy));h=world.queries.height(x,y)
        if not h.found:continue
        add('outside-circle-real-terrain',x,y,h.value_bits,patch=((2352,f.from_float(10)),),face=0x3f800000)
    return json.loads(json.dumps(rows))


def canonical_selfcheck(rows,world):
    """Static-consumer read view check, separately labelled from originaldiff."""
    map_=MotionMap135.fixed_zone(0);preserved=0;cases=0
    for c in rows:
        physical=bytes.fromhex(c['expected']['game_before_hex']);word=lambda o:struct.unpack_from('<I',physical,o)[0]
        spans=[(416,4),(440,4),(464,4),(2352,4),(1416,8),(2587,1)]
        if word(416):spans.extend(((420,8),(436,4)))
        if word(440)&1:spans.append((444,4))
        if c['expected']['packets']:spans.extend(((1336,8),(1644,4),(1880,4),(1888,4)))
        cells=[None]*len(physical)
        for p,n in spans:cells[p:p+n]=physical[p:p+n]
        result=apply_player_motion135(tuple(cells),tuple(c['input']['xyz_bits']),c['input']['facing_bits'],world,map_)
        expected=bytes.fromhex(c['expected']['game_after_hex'])
        for j,v in enumerate(result.game_bytes):
            if v is not None:assert v==expected[j],(c['id'],j,v,expected[j])
            else:assert cells[j]is None;preserved+=1
        assert result.packets==tuple(tuple(x)for x in c['expected']['packets'])
        assert int(result.unchanged_input_xyz)==c['expected']['return_value'];cases+=1
    first=rows[0];raw=bytes.fromhex(first['expected']['game_before_hex']);cells=list(raw);cells[464:468]=[None]*4
    try:apply_player_motion135(tuple(cells),tuple(first['input']['xyz_bits']),first['input']['facing_bits'],world,map_)
    except MotionUnknownRead135 as error:assert error.offset==464 and error.size==4
    else:raise AssertionError('Unknown diagnostic flag was silently filled')
    assert decode_motion135(238,struct.pack('<6I',1,123,0,0,0,0)) is not None
    assert decode_motion135(199,struct.pack('<6I',1,123,0,0,0,0)) is None
    assert decode_motion135(238,struct.pack('<6I',1,123,0x7f800000,0,0,0)) is None
    return dict(kind='model-selfcheck-not-original-differential',cases=cases,unknown_bytes_preserved=preserved,
        unknown_read464_raises=True,canonical24_local_decode_checks=3,constructor_unknown_payload_not_filled=True)


def absent(identifier,group=False):
    try:(os.killpg if group else os.kill)(identifier,0)
    except ProcessLookupError:return True
    return False


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    import_edges=verify_local_source_closure(FILES)
    before={n:sha(ROOT/n)for n in FILES};assert sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
    snapshot=SNAPSHOT.read_bytes();queries=decode_world_snapshot(snapshot,WORLD)
    # Real Elwynn primary tag is absent; no auxiliary backing is invented.
    assert queries.primary is None
    world=MotionWorld135(queries,None);rows=corpus(snapshot,world,args.phase=='pilot')
    canonical=canonical_selfcheck(rows,world)
    del snapshot
    out,manifest=build_motion135()
    fixture=out/'fixtures.json';fixture.write_text(json.dumps(rows,separators=(',',':'))+'\n')
    inputs=out/'inputs.json';inputs.write_text(json.dumps([c['input']for c in rows],separators=(',',':'))+'\n')
    ranges=[];seen=set()
    for _,p,n in queries.source_ranges:
        if (p,n) not in seen:seen.add((p,n));ranges.append((p,n))
    config=out/'config.json';config.write_text(json.dumps(dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,
        game_pointer=G,world_pointer=WORLD,input_path=str(inputs),input_sha256=sha(inputs),world_ranges=ranges))+'\n')
    for name,value in before.items():
        path=out/'source-snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes());assert sha(path)==value
    frozen={p.name:sha(p)for p in(fixture,inputs,config,out/'manifest.json',out/manifest['module_file'])}
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_player_motion135_oracle.mjs'),str(out),str(config)]
    results=out/'results.jsonl';stderr=out/'stderr.log';start=time.monotonic()
    with results.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60,
        pid_missing=absent(child.pid),pgid_missing=absent(child.pid,True),no_detached_child=True)
    (out/'terminal.json').write_text(json.dumps(terminal,indent=2)+'\n')
    actual=[json.loads(line)for line in results.read_text().splitlines()];differences=[]
    for expected,actual_row in zip(rows,actual):
        assert expected['id']==actual_row['id']
        for key in ('return_value','game_before_hex','game_after_hex','packets'):
            if expected['expected'][key]!=actual_row[key]:
                entry=dict(id=expected['id'],group=expected['group'],field=key)
                if key.endswith('hex'):
                    a,b=bytes.fromhex(expected['expected'][key]),bytes.fromhex(actual_row[key]);entry['byte_differences']=[[i,x,y]for i,(x,y)in enumerate(zip(a,b))if x!=y]
                else:entry.update(expected=expected['expected'][key],actual=actual_row[key])
                differences.append(entry)
        assert actual_row['queue_before']['pointer']==actual_row['queue_after']['pointer'] and actual_row['queue_before']['capacity']==actual_row['queue_after']['capacity']
        assert actual_row['queue_after']['count']-actual_row['queue_before']['count']==len(actual_row['packets'])
    assert before=={n:sha(ROOT/n)for n in FILES},'Frozen source changed'
    assert frozen=={p.name:sha(p)for p in(fixture,inputs,config,out/'manifest.json',out/manifest['module_file'])},'Frozen artifact changed'
    report=dict(version='0.135.1',build='90898d5e3',phase=args.phase,cases=len(rows),actual_cases=len(actual),differences=len(differences),
        groups=dict(Counter(c['group']for c in rows)),difference_rows=differences,expected_first=True,input_contains_expected=False,
        source_sha256_before=before,source_sha256_after=before,source_closure_no_headless=True,original_wasm_sha256=SOURCE_SHA,
        complete_static_local_import_edges=import_edges,closure_verified_before_expectations=True,
        canonical_cells=canonical,
        snapshot_sha256=SNAPSHOT_SHA,world_pointer=WORLD,game_pointer=G,comparison='all8192Game bytes,return value,complete appendedpacketopcode+payload,existingqueueprefix,worldrecord/ranges invariance',
        process=terminal,runtime=json.loads((out/'runtime.json').read_text()) if (out/'runtime.json').exists()else None,
        artifacts={p.name:sha(p)for p in(fixture,inputs,config,results,stderr,out/'terminal.json',out/'manifest.json')},
        limitations=['Direct2328 only;968 decoder/17726/broadcast remain separate.',
            'Phase1 actual afterbegin snapshot,not freshGame,independentworldproducer orfullinputloop.',
            'Elwynn policy148=0/circle/realterrain;policy1aux/navtimers/polygons/ringrescue need next differentiated corpus.',
            'Existing packet queue capacity sufficient;heap addresses/backing ofnewpayload notindependently reconstructed.',
            'Rawkeyboard/joystickmotionproducer andphase0 actual1089 continuation remainunknown.'])
    target=out/'comparison.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(target),cases=len(rows),actual_cases=len(actual),differences=len(differences),first_differences=differences[:5],terminal=terminal)))
    if code or len(actual)!=len(rows)or differences or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)


if __name__=='__main__':main()
