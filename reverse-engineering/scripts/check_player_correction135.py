#!/usr/bin/env python3
"""Expected-first full968 opcode199 acknowledgement on a partialApp input.

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

FILES=tuple(dict.fromkeys(tuple('scripts/'+x for x in ('check_player_correction135.py','build_player_dispatch135_oracle.py',
    'build_player_motion135_oracle.py','run_player_correction135_oracle.mjs','build_full135_oracle.py',
    'build_upgrade134_oracle.py','production_closure135.py','source_closure137.py'))+
    production_sources135(ROOT,'core_spec.player_correction135','resource_spec.world_query135')))
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.player_correction135 import (encode_player_correction_ack135,decode_player_correction_ack135,
    consume_player_correction_ack135,UnknownPlayerCorrection135)
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
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_player_correction135_oracle.mjs'),str(out),str(config),phase]
    start=time.monotonic()
    with(out/f'{phase}-results.jsonl').open('w')as stdout,(out/f'{phase}-stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
    receipt=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,
        deadline_seconds=60,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True))
    (out/f'{phase}-terminal.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def corpus(context,pilot):
    base=bytes.fromhex(context['game2592_hex']);own=struct.unpack_from('<Q',base,1336)[0]
    xyz=tuple(struct.unpack_from('<I',base,o)[0]for o in(1416,1420,1424));rows=[];preserved=0
    def add(tag,pending,ack,guid,group):
        nonlocal preserved
        patch=((416,tag),(420,xyz[0]),(424,xyz[1]),(428,xyz[2]),(432,pending),(436,0));raw=bytearray(base)
        for o,v in patch:struct.pack_into('<I',raw,o,v)
        payload=encode_player_correction_ack135(guid,ack);decoded=decode_player_correction_ack135(payload)
        assert decoded.guid==guid and decoded.sequence==ack
        result=consume_player_correction_ack135(bytes(raw),payload)
        app_before=bytearray.fromhex(context['app5168_hex']);app_before[16:16+2592]=raw
        app_after=bytearray(app_before);app_after[16:16+2592]=result.game_bytes
        cells=[None]*2592;cells[416:420]=struct.pack('<I',tag)
        if tag==1:cells[432:436]=struct.pack('<I',pending)
        partial=consume_player_correction_ack135(tuple(cells),payload)
        for j,v in enumerate(partial.game_bytes):
            if v is None:assert cells[j]is None;preserved+=1
            else:assert v==result.game_bytes[j]
        assert partial.cleared==result.cleared
        rows.append(dict(id=len(rows),group=group,input=dict(id=len(rows),opcode=199,payload_hex=payload.hex(),patch_words=patch),
            expected=dict(game_before_hex=bytes(raw).hex(),game_after_hex=result.game_bytes.hex(),app_before_hex=app_before.hex(),app_after_hex=app_after.hex(),packets=[]),
            diagnostic=dict(tag=tag,pending_sequence=pending,ack_sequence=ack,ack_guid=str(guid),player_guid=str(own),cleared=result.cleared,writes=result.writes)))
    add(1,17,16,own,'ack-older-retains');add(1,17,17,own,'ack-equal-clears')
    if not pilot:
        guids=(0,own,0x0102030405060708)
        for tag in(0,1,2):
            for pending in(0,1,17,0x7fffffff,0x80000000,0xffffffff):
                for ack in sorted({0,max(0,pending-1),pending,min(0xffffffff,pending+1),0xffffffff}):
                    add(tag,pending,ack,guids[len(rows)%len(guids)],'tag-sequence-unsigned-matrix')
        for guid in(0,1,0x100,0x10000,0x1000000,0x100000000,0x10000000000,0x1000000000000,0x100000000000000,0x8000000000000000,0xffffffffffffffff):
            add(1,17,17,guid,'packedGUID-ignored-local')
    payload=encode_player_correction_ack135(0,0)
    try:consume_player_correction_ack135(tuple([None]*2592),payload)
    except UnknownPlayerCorrection135:pass
    else:raise AssertionError('Unknown G416 silently accepted')
    for payload in(b'',b'\xff',b'\x00',b'\x00'+bytes(8)):
        try:decode_player_correction_ack135(payload)
        except UnknownPlayerCorrection135:pass
        else:raise AssertionError('Noncanonical ACK accepted')
    return json.loads(json.dumps(rows)),dict(kind='model-selfcheck-not-original-differential',cases=len(rows),unknown_bytes_preserved=preserved,
        tag0or2_does_not_consume_unknown432=True,unknown416_rejected=True,noncanonical_payloads_refused=4)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    edges=verify_local_source_closure(FILES);before={n:sha(ROOT/n)for n in FILES}
    assert not any('headless'in n for n in FILES) and sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
    snapshot=SNAPSHOT.read_bytes();world=decode_world_snapshot(snapshot,WORLD);del snapshot
    ranges=[];seen=set()
    for _,p,n in world.source_ranges:
        if(p,n)not in seen:seen.add((p,n));ranges.append((p,n))
    out,manifest=build_dispatch135()
    for name,value in before.items():
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==value
    setup_config=out/'setup-config.json';base_config=dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,app_pointer=APP,world_pointer=WORLD,world_ranges=ranges)
    setup_config.write_text(json.dumps(base_config)+'\n');setup_terminal=execute(out,setup_config,'setup')
    if setup_terminal['exit_code']or not(out/'setup-context.json').exists():
        print(json.dumps(dict(directory=str(out),status='setup-observation-failed',terminal=setup_terminal)));raise SystemExit(1)
    context=json.loads((out/'setup-context.json').read_text());assert context['G']==APP+16 and context['completeApp_producer']is False and context['original_host_calls']==0
    rows,canonical=corpus(context,args.phase=='pilot')
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
        groups=dict(Counter(x['group']for x in rows)),target_opcode=199,canonical_cells=canonical,original_wasm_sha256=SOURCE_SHA,snapshot_sha256=SNAPSHOT_SHA,
        source_sha256_before=before,source_sha256_after=before,complete_static_local_import_edges=edges,closure_verified_before_expectations=True,
        setup_context_kind=context['kind'],setup_context_sha256=sha(out/'setup-context.json'),target_expected_before_original=True,
        setup_observation_used_as_explicit_prestate=True,independent_constructor_validation=False,input_contains_expected=False,
        setup_process=setup_terminal,target_process=terminal,setup_runtime=json.loads((out/'setup-runtime.json').read_text()),
        runtime=json.loads((out/'cases-runtime.json').read_text())if(out/'cases-runtime.json').exists()else None,
        artifacts={p.name:sha(p)for p in(fixture,inputs,config,setup_config,out/'setup-context.json',out/'cases-results.jsonl',out/'cases-stderr.log',out/'setup-terminal.json',out/'cases-terminal.json',out/'manifest.json')},
        limitations=['Genuine full968 opcode199 default ownerRoute0/peer0 exactpackedGUID+u32 only.',
            'TypedpartialApp setup with real6730/1089,notnatural4253/1371 orindependentconstructor acceptance.',
            'All2592Game/all5168App bytes,preservedqueueprefix,noappendedpackets,andworldrecord/ranges compared.',
            'Mode0 full17726 no-op;ownerRoute1/mode1/truncatedACK/915 continuation remainseparate.',
            'GUIDdecodedbutnotcomparedbylocalscalarsegment,notaclaimaboutallnetworkauthentication.',
            'No freshGameboot,externrefVMrestoration,multiplayerplayability orcompletegameacceptance.'])
    target=out/'correction-comparison.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(target),cases=len(rows),actual_cases=len(actual),differences=len(differences),first_differences=differences[:4],terminal=terminal)))
    if terminal['exit_code']or len(actual)!=len(rows)or differences or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)


if __name__=='__main__':main()
