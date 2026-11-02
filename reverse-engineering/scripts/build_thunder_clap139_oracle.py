#!/usr/bin/env python3
"""Bind complete current139922 area2 and real fullopening/selection prefix."""
from incoming139_tools import (ROOT, SOURCE, SOURCE_SHA, original, private_exports,
                               function_proof, static_reader, sha, save)


def build(out):
    raw, identity, ranges = original()
    static = out/'static'
    static.mkdir()
    ids = {2945,1600,1108,4677,2181,1093,4603,922,913,2189,1775,3755,
           10490,27754,20123,36364,83299,994,4593,1542,1173}
    functions, texts = function_proof(raw, identity, ranges, ids, static)
    read = static_reader(raw, identity)
    thunder = read(5882916, 88)
    assert thunder[84] == 2 and int.from_bytes(thunder[:4], 'little') == 1
    assert read(1601276, 4) == bytes.fromhex('0000003f')
    assert 'call 2189' in texts[922] and 'call 1775' not in texts[922] and 'call 3755' not in texts[922]
    assert 'i32.load offset=1852' in texts[1775] and 'i32.load offset=1804' in texts[3755]
    additions = [('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),
        ('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),
        ('research139_gw_select',0,1093),('research139_gw_stack',3,0),
        ('research139_tc_cast922',0,922),('research139_tc_hits1775',0,1775),
        ('research139_tc_areas3755',0,3755)]
    filename = 'thunder-clap139-original-exports.wasm'
    (out/filename).write_bytes(private_exports(raw, identity, additions))
    manifest = dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,
        module_file=filename,module_sha256=sha(out/filename),original_imports=identity['imports'],
        added_exports=additions,functions=functions,only_export_section_changed=True,
        implicit_start=False,builder_original_executions=0,thunder_clap88_hex=thunder.hex(),
        cleave88_hex=read(5882740,88).hex(),coefficient1601276_hex=read(1601276,28).hex(),
        static_reads=read.proof,scope='Current922exec2/effect1 synchronous913 then2189; real2owned/live fullopening; controlledplayerplacement; empty1775/3755 checks not nonempty producer recovery')
    save(out/'manifest.json',manifest)
    return manifest
