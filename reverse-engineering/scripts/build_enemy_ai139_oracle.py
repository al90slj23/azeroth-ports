#!/usr/bin/env python3
"""Export-only current139 AI925 on real full1108 owners."""
from incoming139_tools import original,private_exports,function_proof,sha,save,SOURCE_SHA
from trace_enemy_ai139 import trace
def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir();proof=trace(static)
    setup,_=function_proof(raw,identity,ranges,{2945,1600,1108},static)
    added=[('research139_ai_companion',0,2945),('research139_ai_initial',0,1600),('research139_ai_opening',0,1108),('research139_ai_tick',0,925),('research139_ai_stack',3,0)]
    name='enemy-ai139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,added))
    manifest=dict(source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),original_imports=identity['imports'],added_exports=added,functions=proof['functions'],setup_functions=setup,only_export_section_changed=True,original_executions=0)
    save(out/'manifest.json',manifest);return manifest
