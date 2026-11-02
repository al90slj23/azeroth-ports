#!/usr/bin/env python3
"""Full current1391446/1886 plus intact geometry; private exports only."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,function_proof,static_reader,save,sha

def build(out):
 raw,identity,ranges=original();static=out/'static';static.mkdir();functions,texts=function_proof(raw,identity,ranges,{1446,1886,10804,24602,52397,51773,66558,29912,23333,11425,11499,50441},static);read=static_reader(raw,identity)
 assert functions[1446]['signature']==('7f7f7f7f','')
 assert 'i32.const 45'in texts[1446]and'i64.const -1067352960675086336'in texts[1446]
 speeds=read(1593032,24)
 added=[('research139_drop1446',0,1446),('research139_drop_stack0',3,0)];module=private_exports(raw,identity,added);name='death-pickups139-original-exports.wasm';(out/name).write_bytes(module)
 m=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),functions=functions,original_imports=identity['imports'],added_exports=added,only_changed_section=7,implicit_start=False,original_full_callees_preserved=True,XP_speeds_hex=speeds.hex(),static_reads=read.proof,validation='FreshNodecompile_beforeoriginalfunction')
 save(out/'manifest.json',m);return m
