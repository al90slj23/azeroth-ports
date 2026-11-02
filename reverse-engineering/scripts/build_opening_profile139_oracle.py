#!/usr/bin/env python3
"""Private unchanged2945/18062 current139 components;no snapshot required."""
from incoming139_tools import original,private_exports,SOURCE_SHA,sha,save
from trace_opening_aux139 import trace
def build(out):
    raw,identity,_=original();static=out/'static';static.mkdir();proof=trace(static)
    added=[('research139_companion2945',0,2945),('research139_start18062',0,18062),('research139_opening_profile_stack0',3,0)]
    assert proof['functions'][2945]['signature']==('7f7f','')and proof['functions'][18062]['signature']==('7f7f7f7f7f','')
    module=private_exports(raw,identity,added);name='opening-profile139-original-exports.wasm';(out/name).write_bytes(module)
    manifest=dict(version='0.139.0',actual_build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),only_changed_section=7,original_imports=identity['imports'],added_exports=added,roles={'companion_selection':proof['functions'][2945],'start_banner':proof['functions'][18062]},static_trace_sha256=sha(static/'trace.json'),stack_initial=1048576,allocator=93344,implicit_start=False,original_executed_by_builder=False)
    save(out/'manifest.json',manifest);return manifest,proof
