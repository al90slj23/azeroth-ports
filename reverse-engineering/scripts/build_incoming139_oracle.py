#!/usr/bin/env python3
"""Private export-only current1391076,real locale83304 and stack surface."""
from incoming139_tools import ROOT,SOURCE_SHA,original,private_exports,save,sha
from trace_incoming139 import trace
def build(out):
    raw,identity,ranges=original();static_dir=out/'static';static_dir.mkdir();proof=trace(static_dir)
    additions=[('research139_incoming1076',0,1076),('research139_locale83304',0,83304),('research139_incoming_stack',3,0)]
    module=private_exports(raw,identity,additions);path=out/'incoming139-original-exports.wasm';path.write_bytes(module)
    manifest=dict(version='0.139.0',actual_build='f79c5e2b4',original_sha256=SOURCE_SHA,module_file=path.name,module_sha256=sha(path),entry=proof['functions'][1076],static_trace_sha256=sha(static_dir/'trace.json'),original_exports=identity['exports'],added_exports=additions,original_imports=identity['imports'],denied_imports=882,implicit_start=False,only_changed_section=7,allocator_index=93344,stack_initial=1048576,original_executed_by_builder=False)
    save(out/'manifest.json',manifest);return manifest,proof
