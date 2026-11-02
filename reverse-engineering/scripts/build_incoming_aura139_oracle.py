#!/usr/bin/env python3
"""Export-only actual1391600/83304/1173/1076 bounded consumer component."""
from incoming139_tools import original,private_exports,save,sha,SOURCE_SHA
from trace_incoming_aura139 import trace
def build(out):
    raw,identity,_=original();static=out/'static';static.mkdir();proof=trace(static)
    additions=[('research139_incoming1076',0,1076),('research139_locale83304',0,83304),('research139_aura1173',0,1173),('research139_initial1600',0,1600),('research139_incoming_stack',3,0)]
    module=private_exports(raw,identity,additions);name='incoming-aura139-original-exports.wasm';(out/name).write_bytes(module)
    manifest=dict(original_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),added_exports=additions,only_changed_section=7,original_imports=identity['imports'],functions=proof['functions'],static_trace_sha256=sha(static/'trace.json'),denied_imports=882,original_executed_by_builder=False)
    save(out/'manifest.json',manifest);return manifest,proof
