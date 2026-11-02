#!/usr/bin/env python3
"""True1395719→two922 including full913 and every deathcallee intact."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,function_proof,static_reader,save,sha

def build(out):
 raw,identity,ranges=original();static=out/'static';static.mkdir();functions,texts=function_proof(raw,identity,ranges,{1600,5719,8740,13563,922,913,8673,44070,10490,1446,1886,58587,36367,994,18421,1466,46692,46462},static);read=static_reader(raw,identity)
 assert functions[922]['signature']==('7f7f','7f')and functions[913]['signature']==('7f7e7d7f7f7f7f','')
 definition=dict(pointer=5882740,ability_id='cleave',raw88_hex=read(5882740,88).hex());npc=read(5830904,72)
 added=[('research139_spawn5719',0,5719),('research139_npc_cast922',0,922),('research139_spawn_stack0',3,0)];module=private_exports(raw,identity,added);name='death139-original-exports.wasm';(out/name).write_bytes(module)
 m=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),functions=functions,definition=definition,ordinary72_hex=npc.hex(),original_imports=identity['imports'],added_exports=added,only_changed_section=7,implicit_start=False,original_full_callees_preserved=True,original_executed=False,validation='FreshboundedNodecompileofexactexportonlymodule')
 save(out/'manifest.json',m);return m
