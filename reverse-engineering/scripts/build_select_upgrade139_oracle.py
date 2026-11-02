#!/usr/bin/env python3
"""Current139 actualfirstcleaveupgrade exports/fullbody/table binding."""
import ast,struct
from build_growth_world139_oracle import build as base_build
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,function_proof,static_reader,save,sha


def build(out):
    result=base_build(out);raw,identity,ranges=original();extra=out/'upgrade-static';extra.mkdir()
    functions,texts=function_proof(raw,identity,ranges,{25511},extra)
    assert functions[25511]['signature']==('7f7f7f','7d')
    declarations={node.targets[0].id:ast.literal_eval(node.value)for node in ast.parse((ROOT/'reconstruction/core_spec/select_upgrade139.py').read_text()).body if isinstance(node,ast.Assign)}
    read=static_reader(raw,identity)
    tables=tuple(tuple(struct.unpack('<5I',read(p,20)))for p in declarations['UPGRADE_TABLE_POINTERS139'])
    assert tables==declarations['UPGRADE_TABLES139']
    old=out/result['module_file'];name='select-upgrade139-original-exports.wasm';(out/name).write_bytes(old.read_bytes());result['module_file']=name;result['module_sha256']=sha(out/name)
    result['extra_upgrade_functions']=functions;result['upgrade_table_pointers']=declarations['UPGRADE_TABLE_POINTERS139'];result['upgrade_tables139']=tables;result['upgrade_static_reads']=read.proof
    save(out/'manifest.json',result);return result
