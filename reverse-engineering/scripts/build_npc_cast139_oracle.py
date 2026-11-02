#!/usr/bin/env python3
"""Private current1395719/922 same-Game exports; no target execution."""
from incoming139_tools import (ROOT,SOURCE,SOURCE_SHA,original,private_exports,
    function_proof,static_reader,save,sha)


def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir()
    functions,_=function_proof(raw,identity,ranges,
        {1600,5719,8740,13563,922,913,8673,44070,10490},static)
    assert functions[5719]['signature']==('7f7f7f7f','')
    assert functions[922]['signature']==('7f7f','7f')
    read=static_reader(raw,identity);definition=dict(pointer=5882740,
        ability_id='cleave',raw88_hex=read(5882740,88).hex())
    added=[('research139_spawn5719',0,5719),('research139_npc_cast922',0,922),
        ('research139_spawn_stack0',3,0)]
    module=private_exports(raw,identity,added);name='npc-cast139-original-exports.wasm'
    (out/name).write_bytes(module)
    manifest=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,
        module_file=name,module_sha256=sha(out/name),functions=functions,
        definition=definition,original_imports=identity['imports'],
        added_exports=added,only_changed_section=7,implicit_start=False,
        original_full_callees_preserved=True,original_executed=False,
        validation='Fresh bounded Node WebAssembly.compile of exact export-only module')
    save(out/'manifest.json',manifest);return manifest
