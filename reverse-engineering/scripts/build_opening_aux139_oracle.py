#!/usr/bin/env python3
"""Unchanged139 actor/rune/full1108 private export surface;no target runs."""
import re
from incoming139_tools import original,private_exports,SOURCE_SHA,function_proof,sha,save
from trace_opening_aux139 import trace
def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir();proof=trace(static);extra=out/'static-extra';extra.mkdir();functions,texts=function_proof(raw,identity,ranges,{24602,11425,11499,50441},extra)
    actor=(static/'1886.wat').read_text();keys=list(map(int,re.findall(r'i32.const (\d+)\n\s+i32.store offset=72',actor)));assert keys==[2,3,4,8,9,12,13,14,15,16,17,18,20,21]
    additions=[('research139_open_actor1886',0,1886),('research139_open_pickup1446',0,1446),('research139_open_random13563',0,13563),('research139_open_initial1600',0,1600),('research139_open_companion2945',0,2945),('research139_open_begin1108',0,1108),('research139_open_stack0',3,0)]
    assert proof['functions'][1886]['signature']==('7f7f7f7f7f','7e')
    name='opening-aux139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,additions));manifest=dict(version='0.139.0',actual_build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),only_changed_section=7,original_imports=identity['imports'],added_exports=additions,functions=proof['functions'],extra_static_functions=functions,actor1886_keys=keys,source_trace_sha256=sha(static/'trace.json'),allocator_index=93344,stack_initial=1048576,implicit_start=False,original_executed_by_builder=False)
    save(out/'manifest.json',manifest);return manifest,proof
