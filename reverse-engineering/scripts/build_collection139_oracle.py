#!/usr/bin/env python3
"""Current139sameGameNPC/death→full2890, exports only."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,function_proof,static_reader,save,sha

def build(out):
 raw,identity,ranges=original();static=out/'static';static.mkdir();functions,texts=function_proof(raw,identity,ranges,{1600,5719,8740,922,913,1446,1886,2890,32070,27650,29338,4677,86979,88159,15962,46462},static);read=static_reader(raw,identity)
 assert functions[2890]['signature']==('7f','')and functions[4677]['signature']==('7f7f','')
 definition=dict(pointer=5882740,ability_id='cleave',raw88_hex=read(5882740,88).hex());added=[('research139_spawn5719',0,5719),('research139_npc_cast922',0,922),('research139_collect2890',0,2890),('research139_spawn_stack0',3,0)];module=private_exports(raw,identity,added);name='collection139-original-exports.wasm';(out/name).write_bytes(module)
 manifest=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),functions=functions,definition=definition,original_imports=identity['imports'],added_exports=added,only_changed_section=7,implicit_start=False,original_full_callees_preserved=True,original_executed=False,validation='FreshboundedNodecompileoftheexportonlymodule')
 save(out/'manifest.json',manifest);return manifest
