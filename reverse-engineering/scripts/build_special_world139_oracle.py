#!/usr/bin/env python3
"""Export-only current2372 with unchanged full constructor/opening helpers."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,save,sha
from trace_special_world139 import trace


def build(out):
    static=out/'static';static.mkdir();proof=trace(static);raw,identity,ranges=original()
    additions=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_stack',3,0),('research139_special2372',0,2372)]
    name='special-world139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,additions))
    manifest=dict(source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),original_imports=identity['imports'],added_exports=additions,functions=proof['functions'],special_trace=proof,only_export_section_changed=True,original_executions_by_builder=0)
    save(out/'manifest.json',manifest);return manifest
