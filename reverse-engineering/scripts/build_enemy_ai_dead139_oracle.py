#!/usr/bin/env python3
"""Current complete925/40215 and genuine cold2123 death-prefix exports."""
from build_player_autocast139_oracle import build as build_autocast
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,function_proof,sha,save


def build(out):
    manifest=build_autocast(out);raw,identity,ranges=original()
    ids={40215,81682,30179,29237,50441,11425,11499,13833,15962,20060,23333,70932,52557,59230,29912,5719}
    proof,texts=function_proof(raw,identity,ranges,ids,out/'static');manifest['functions'].update(proof)
    assert 'i32.const 432\n          memory.copy'in texts[40215]
    assert 'i32.store offset=8'in texts[40215]and'call 73034'in texts[40215]
    manifest['module_file']='enemy-ai-dead139-original-exports.wasm'
    (out/'player-autocast139-original-exports.wasm').rename(out/manifest['module_file'])
    manifest['module_sha256']=sha(out/manifest['module_file'])
    manifest['dead_producer']='Fresh actual2945/1600/1108/4677/1093,initial925,6full2123; optional actual922,never dead marker edits'
    manifest['scope']='Actualcomplete925 retained913 marker1 and stable432byte40215 removal with full physicalVec capacity/staleTail; bounded default owners'
    save(out/'manifest.json',manifest);return manifest
