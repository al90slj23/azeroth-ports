#!/usr/bin/env python3
"""Only add current1391600/38553/stack exports; retain all original bodies."""
from incoming139_tools import original,private_exports,function_proof,sha,save,SOURCE_SHA


def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir()
    proof,texts=function_proof(raw,identity,ranges,{1600,38553,10490,15962,66546},static)
    assert proof[38553]['signature']==('7f','')
    assert 'i32.load offset=1840'in texts[38553]and'f32.le'in texts[38553]and'memory.copy'in texts[38553]
    assert 'i32.const 8\n            i32.const 0'in texts[38553]and'call 10490'in texts[38553]
    added=[('research139_deadline_ctor',0,1600),('research139_deadline_tick',0,38553),('research139_deadline_stack',3,0)]
    name='frame-deadline139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,added))
    result=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),original_imports=identity['imports'],added_exports=added,functions=proof,only_export_section_changed=True,original_executions=0)
    save(out/'manifest.json',result)
    return result
