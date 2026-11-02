#!/usr/bin/env python3
"""Static-only current139 realThunder slow ->925 private export surface."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,function_proof,static_reader,sha,save


def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir()
    ids={2945,1600,1108,4677,2181,1093,4603,922,913,2189,10490,27754,925,81682,30179,29237,50441,11425,11499,1076,13833,27650,15962,20060,23333,70932,52557,59230,29912,5719,1173,1542}
    functions,texts=function_proof(raw,identity,ranges,ids,static);read=static_reader(raw,identity)
    assert all(x in texts[81682]for x in['f32.load offset=300','f32.load offset=120','f32.load offset=124','f32.gt','f32.mul'])
    assert 'call 81682'in texts[925]and'call 1076'in texts[925]and'call 2189'in texts[922]
    added=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),('research139_gw_select',0,1093),('research139_gw_stack',3,0),('research139_status_cast922',0,922),('research139_status_tick925',0,925)]
    filename='enemy-ai-status139-original-exports.wasm';(out/filename).write_bytes(private_exports(raw,identity,added))
    manifest=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=filename,module_sha256=sha(out/filename),original_imports=identity['imports'],added_exports=added,functions=functions,only_export_section_changed=True,original_executions=0,thunder88_hex=read(5882916,88).hex(),static_reads=read.proof,scope='Realfull1108/XP5/firstnewThunder922slow then full925; no NPC/source/live/CD edits; direct component schedule')
    save(out/'manifest.json',manifest);return manifest
