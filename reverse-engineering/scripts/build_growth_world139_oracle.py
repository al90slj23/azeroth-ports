#!/usr/bin/env python3
"""Current139 fullopening then inactive-world growth: export-only module."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,function_proof,sha,save


def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir()
    ids={1600,2945,1108,5719,1446,1886,8740,13563,1795,10099,1542,4677,2181,1093,
         1501,30022,27572,27167,28657,11033,28155,86979,34853,35988,26364,25613,4603,1173}
    functions,texts=function_proof(raw,identity,ranges,ids,static)
    assert functions[4677]['signature']==functions[1093]['signature']==('7f7f','')
    assert functions[26364]['signature']==('7f7f','')and functions[25613]['signature']==('7f','')
    for needle in('i32.load offset=1788','i32.load offset=1792','i32.const 344','i32.load offset=660','i32.load offset=2116'):
        assert needle in texts[26364],needle
    assert 'call 26364'in texts[35988]and'call 26364'in texts[25613]
    assert 'i32.const 0\n      i32.const 1\n      call 2181'in texts[4677]
    added=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),
           ('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),
           ('research139_gw_select',0,1093),('research139_gw_stack',3,0)]
    name='growth-world139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,added))
    result=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=name,
        module_sha256=sha(out/name),original_imports=identity['imports'],added_exports=added,
        functions=functions,only_export_section_changed=True,implicit_start=False,builder_original_executions=0)
    save(out/'manifest.json',result);return result
