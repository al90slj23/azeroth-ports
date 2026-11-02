#!/usr/bin/env python3
"""Export-only unchanged current925/916/38553 with freshopening source."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,save,sha
from trace_guardian_charge139 import trace


def build(out):
    static=out/'static';static.mkdir();proof=trace(static);raw,identity,ranges=original()
    exports=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_stack',3,0),('research139_special2372',0,2372),('research139_guardian925',0,925),('research139_guardian916',0,916),('research139_scheduled38553',0,38553)]
    name='guardian-charge139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,exports))
    result=dict(source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),original_imports=identity['imports'],added_exports=exports,functions=proof['functions'],guardian_trace=proof,only_export_section_changed=True,original_executions_by_builder=0)
    save(out/'manifest.json',result);return result
