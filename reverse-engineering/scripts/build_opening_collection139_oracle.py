#!/usr/bin/env python3
"""Current139 full1108→922→2890 private exports; original bodies intact."""
from incoming139_tools import original,private_exports,function_proof,static_reader,save,sha
from build_opening_aux139_oracle import build as build_opening
from trace_opening139 import trace_opening139


def build(out):
    manifest,_=build_opening(out);trace_opening139(out/'whole-opening-static')
    raw,identity,ranges=original();folder=out/'chain-static';folder.mkdir()
    proof,_=function_proof(raw,identity,ranges,{922,913,2890,4677,32070,27650,29338,88159,86979,15962,46462,1093,28657,26364,25613},folder)
    added=list(manifest['added_exports'])+[
        ('research139_chain_cast922',0,922),('research139_chain_collect2890',0,2890),
        ('research139_chain_select1093',0,1093)]
    name='opening-collection139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,added))
    read=static_reader(raw,identity);definition=read(5882740,88)
    assert proof[922]['signature']==('7f7f','7f') and proof[2890]['signature']==('7f','')
    manifest.update(module_file=name,module_sha256=sha(out/name),added_exports=added,
        chain_functions=proof,definition=dict(pointer=5882740,ability_id='cleave',raw88_hex=definition.hex()),
        whole_opening_trace_sha256=sha(out/'whole-opening-static/trace.json'),
        original_full_callees_preserved=True,source_counter_contract='Zero initial accounting/kills/gold and sequence1 are explicit checked component inputs,not fullGameproducerproof')
    save(out/'manifest.json',manifest);return manifest
