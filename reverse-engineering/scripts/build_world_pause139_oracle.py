#!/usr/bin/env python3
"""Current13926364/35988/25613, intact full module with private exports."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,function_proof,save,sha


def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir()
    ids={2945,1600,1108,925,26364,35988,25613,2181,29912,23333,46692,27650,
         55846,108362,66546,73034,15962,46462}
    functions,texts=function_proof(raw,identity,ranges,ids,static)
    assert functions[26364]['signature']==('7f7f','')
    assert functions[35988]['signature']==functions[25613]['signature']==('7f','')
    assert functions[73034]['signature']==('7f7f','')
    for n in(35988,25613):
        assert 'call 26364'in texts[n] and 'call 29912'in texts[n] and 'call 23333'in texts[n]
        assert 'i32.store offset=2412'in texts[n]
    assert 'call 46692'in texts[35988] and 'call 27650'in texts[25613]
    assert 'i32.const 432'in texts[26364]and'i32.const 112'in texts[26364]and'i32.const 88'in texts[26364]
    assert 'f32.store offset=32'in texts[26364]and'i64.store offset=20 align=4'in texts[26364]
    added=[('research139_pause_account',0,2945),('research139_pause_ctor',0,1600),
           ('research139_pause_opening',0,1108),('research139_pause_AI',0,925),
           ('research139_pause_gather',0,26364),('research139_pause_stop',0,35988),
           ('research139_pause_resume',0,25613),('research139_pause_free',0,73034),
           ('research139_pause_stack',3,0)]
    name='world-pause139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,added))
    result=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,
                module_file=name,module_sha256=sha(out/name),functions=functions,
                original_imports=identity['imports'],added_exports=added,only_export_section_changed=True,
                builder_original_executions=0,full_main884_frames=0)
    save(out/'manifest.json',result);return result
