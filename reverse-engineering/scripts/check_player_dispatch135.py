#!/usr/bin/env python3
"""Expected-first full968 default localroute on a typed partialApp input.

The separate full6730/1089 setup observation supplies an explicit component
prestate. It is never counted as an independent constructor or natural App.
"""
from collections import Counter
from pathlib import Path
import argparse
import json
import os
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode=True
from build_player_dispatch135_oracle import build_dispatch135
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA
from build_upgrade134_oracle import sha
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure

FILES=tuple(dict.fromkeys(tuple('scripts/'+x for x in ('check_player_dispatch135.py','build_player_dispatch135_oracle.py',
    'build_player_motion135_oracle.py','run_player_dispatch135_oracle.mjs','build_full135_oracle.py',
    'build_upgrade134_oracle.py','production_closure135.py','source_closure137.py'))+
    production_sources135(ROOT,'core_spec.player_motion135','resource_spec.world_query135')))
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.player_motion135 import MotionMap135,MotionWorld135,consume_motion_payload135
from resource_spec.world_query135 import decode_world_snapshot

SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
APP,WORLD=14549000,26204808
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def execute(out,config,phase):
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_player_dispatch135_oracle.mjs'),str(out),str(config),phase]
    start=time.monotonic()
    with(out/f'{phase}-results.jsonl').open('w')as stdout,(out/f'{phase}-stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
    receipt=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,
        deadline_seconds=60,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True))
    (out/f'{phase}-terminal.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def corpus(context,world,pilot):
    base=bytes.fromhex(context['game2592_hex']);map_=MotionMap135.fixed_zone(0);cx,cy=map_.center_xy_bits;rows=[]
    def add(group,xyz,*,flags=0,ms=0,face=0,opcode=238,patch=()):
        payload=struct.pack('<6I',flags,ms,*xyz,face);raw=bytearray(base)
        for o,v in patch:struct.pack_into('<I',raw,o,v)
        result=consume_motion_payload135(bytes(raw),opcode,payload,world,map_)
        before=bytes(raw)
        after=before if result is None else result.game_bytes
        app_before=bytearray.fromhex(context['app5168_hex']);app_before[16:16+2592]=before
        app_after=bytearray(app_before);app_after[16:16+2592]=after
        rows.append(dict(id=len(rows),group=group,input=dict(id=len(rows),opcode=opcode,payload24_hex=payload.hex(),patch_words=patch),
            expected=dict(game_before_hex=before.hex(),game_after_hex=after.hex(),app_before_hex=app_before.hex(),app_after_hex=app_after.hex(),
                packets=[]if result is None else result.packets),diagnostic=dict(rejected_nonfinite=result is None,
                scalar_writes=[]if result is None else result.writes,complete2328=True if result is None else result.complete2328)))
    h=world.queries.height(cx,cy);assert h.found
    add('local238-same-real-position',(cx,cy,h.value_bits),ms=123,flags=1,face=0x3fc00000)
    add('local181-real-move',(f.add(cx,f.from_float(1)),cy,h.value_bits),ms=1000,flags=1,opcode=181,patch=((2352,f.from_float(1)),))
    if pilot:return json.loads(json.dumps(rows))
    for opcode in (182,183,185,193,198,200,201,203,218,219,238):
        x,y=f.add(cx,f.from_float(3)),f.add(cy,f.from_float(4));hh=world.queries.height(x,y);assert hh.found
        add('opcode-family-finite',(x,y,hh.value_bits),opcode=opcode,ms=0xffffffff,flags=0x1001,face=0x40c90fdb,patch=((2352,f.from_float(3)),))
    for dx,dy in ((0,0),(100,0),(0,100),(131,0),(-120,-100)):
        x,y=f.add(cx,f.from_float(dx)),f.add(cy,f.from_float(dy));hh=world.queries.height(x,y);assert hh.found
        add('full968-real-correction',(x,y,f.add(hh.value_bits,f.from_float(-16))),flags=1,ms=2500,face=0x3f800000,
            patch=((2352,f.from_float(2.5)),(1644,0xffffffff)))
    for distance,now in ((3,2.999),(3.001,2.999),(4,3)):
        x=f.add(cx,f.from_float(distance));hh=world.queries.height(x,cy);assert hh.found
        add('full968-pending-correction',(x,cy,hh.value_bits),ms=999999,flags=9,
            patch=((416,1),(420,cx),(424,cy),(436,0),(2352,f.from_float(now))))
    for field in range(4):
        for word in (0x7f800000,0xff800000,0x7fc00000):
            xyz=[cx,cy,h.value_bits];face=0
            if field==3:face=word
            else:xyz[field]=word
            add('nonfinite-before-mutation',tuple(xyz),flags=0xffffffff,ms=0xffffffff,face=face)
    return json.loads(json.dumps(rows))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    edges=verify_local_source_closure(FILES);before={n:sha(ROOT/n)for n in FILES}
    assert not any('headless'in n for n in FILES) and sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
    snapshot=SNAPSHOT.read_bytes();world=MotionWorld135(decode_world_snapshot(snapshot,WORLD),None);del snapshot
    ranges=[];seen=set()
    for _,p,n in world.queries.source_ranges:
        if(p,n)not in seen:seen.add((p,n));ranges.append((p,n))
    out,manifest=build_dispatch135()
    for name,value in before.items():
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==value
    setup_config=out/'setup-config.json';base_config=dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,app_pointer=APP,world_pointer=WORLD,world_ranges=ranges)
    setup_config.write_text(json.dumps(base_config)+'\n');setup_terminal=execute(out,setup_config,'setup')
    if setup_terminal['exit_code']or not(out/'setup-context.json').exists():
        print(json.dumps(dict(directory=str(out),status='setup-observation-failed',terminal=setup_terminal)));raise SystemExit(1)
    context=json.loads((out/'setup-context.json').read_text());assert context['G']==APP+16 and context['completeApp_producer']is False and context['original_host_calls']==0
    rows=corpus(context,world,args.phase=='pilot')
    fixture=out/'fixtures.json';fixture.write_text(json.dumps(rows,separators=(',',':'))+'\n')
    inputs=out/'inputs.json';inputs.write_text(json.dumps([x['input']for x in rows],separators=(',',':'))+'\n')
    config=out/'cases-config.json';config.write_text(json.dumps(dict(base_config,input_path=str(inputs),input_sha256=sha(inputs),context_sha256=sha(out/'setup-context.json')))+'\n')
    frozen={p.name:sha(p)for p in(fixture,inputs,config,setup_config,out/'setup-context.json',out/'manifest.json',out/manifest['module_file'])}
    assert before=={n:sha(ROOT/n)for n in FILES}
    terminal=execute(out,config,'cases');actual=[json.loads(x)for x in(out/'cases-results.jsonl').read_text().splitlines()];differences=[]
    for c,a in zip(rows,actual):
        assert c['id']==a['id']
        for key in c['expected']:
            if c['expected'][key]!=a[key]:
                row=dict(id=c['id'],group=c['group'],field=key)
                if key.endswith('hex'):
                    x,y=bytes.fromhex(c['expected'][key]),bytes.fromhex(a[key]);row['byte_differences']=[[j,p,q]for j,(p,q)in enumerate(zip(x,y))if p!=q]
                else:row.update(expected=c['expected'][key],actual=a[key])
                differences.append(row)
    assert before=={n:sha(ROOT/n)for n in FILES}
    assert frozen=={p.name:sha(p)for p in(fixture,inputs,config,setup_config,out/'setup-context.json',out/'manifest.json',out/manifest['module_file'])}
    report=dict(version='0.135.1',build='90898d5e3',phase=args.phase,cases=len(rows),actual_cases=len(actual),differences=len(differences),difference_rows=differences,
        groups=dict(Counter(x['group']for x in rows)),original_wasm_sha256=SOURCE_SHA,snapshot_sha256=SNAPSHOT_SHA,
        source_sha256_before=before,source_sha256_after=before,complete_static_local_import_edges=edges,closure_verified_before_expectations=True,
        setup_context_kind=context['kind'],setup_context_sha256=sha(out/'setup-context.json'),target_expected_before_original=True,
        setup_observation_used_as_explicit_prestate=True,independent_constructor_validation=False,input_contains_expected=False,
        setup_process=setup_terminal,target_process=terminal,setup_runtime=json.loads((out/'setup-runtime.json').read_text()),
        runtime=json.loads((out/'cases-runtime.json').read_text())if(out/'cases-runtime.json').exists()else None,
        artifacts={p.name:sha(p)for p in(fixture,inputs,config,setup_config,out/'setup-context.json',out/'cases-results.jsonl',out/'cases-stderr.log',out/'setup-terminal.json',out/'cases-terminal.json',out/'manifest.json')},
        limitations=['Genuine full968 default ownerRoute0/peer0 with canonical24 only;setup App is typedpartial component,not natural App4253/1371.',
            'Real6730/1089 setup snapshotprestate is input,not independent constructor differential;full968 expected is frozen first.',
            'All2592Game/all5168App bytes andcomplete appendedpacketopcode+payload compared;prefix andworldranges preserved.',
            'Mode2582=0 makes full17726 no-op;ownerRoute1/mode1/networkbroadcast/199ACK/phase0 andUIinput producer remainseparate.',
            'No freshGame boot,externrefVM restoration,multiplayerplayability or completegame acceptance.'])
    target=out/'dispatch-comparison.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(target),cases=len(rows),actual_cases=len(actual),differences=len(differences),first_differences=differences[:4],terminal=terminal)))
    if terminal['exit_code']or len(actual)!=len(rows)or differences or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)


if __name__=='__main__':main()
