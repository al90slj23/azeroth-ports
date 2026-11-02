#!/usr/bin/env python3
"""Bind current139 consecutive2123→925 components with genuine corpse lifecycle."""
from incoming139_tools import (ROOT, SOURCE, SOURCE_SHA, original, private_exports,
                               function_proof, static_reader, sha, save)


def build(out):
    raw, identity, ranges = original()
    static = out/'static'
    static.mkdir()
    ids = {884,40215,9541,8673,13833,46690,23328,925,2945,1600,1108,4677,2181,1093,4603,922,913,2189,1775,3755,
           10490,27754,20123,36364,83299,994,4593,1542,1173,
           2123,1238,1076,1466,28155,18421,11033,2077,19598,36520,26202,30861,8569}
    functions, texts = function_proof(raw, identity, ranges, ids, static)
    read = static_reader(raw, identity)
    assert functions[1076]['signature']==('7f7d7e7f7f7f','')
    assert 'local.get 57\n          i32.const 1\n          i32.const 0\n          local.get 2\n          call 1076'in texts[925]
    assert 'local.get 4\n            i32.eqz\n            br_if 0'in texts[1076]and 'call 4562'in texts[1076]
    thunder = read(5882916, 88)
    assert thunder[84] == 2 and int.from_bytes(thunder[:4], 'little') == 1
    assert read(1601276, 4) == bytes.fromhex('0000003f')
    assert texts[925].index('call 40215')<texts[925].index('i32.const 170')<texts[925].index('i32.const 221')<texts[925].index('call 13833')<texts[925].index('call 1076')
    assert 'call 9541' in texts[913] and 'i32.const 330' in texts[913]
    assert read(1596339,5)==b'melee' and read(1592776,5)==b'Melee'
    assert 'call 2189' in texts[922] and 'call 1775' not in texts[922] and 'call 3755' not in texts[922]
    assert 'i32.load offset=1852' in texts[1775] and 'i32.load offset=1804' in texts[3755]
    additions = [('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),
        ('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),
        ('research139_gw_select',0,1093),('research139_gw_stack',3,0),
        ('research139_tc_cast922',0,922),('research139_tc_hits1775',0,1775),
        ('research139_tc_areas3755',0,3755),('research139_heal_update2123',0,2123),
        ('research139_heal_incoming1076',0,1076),('research139_heal_direct913',0,913),('research139_auto_tick1238',0,1238),('research139_auto_ai925',0,925)]
    filename = 'player-enemy139-v2-original-exports.wasm'
    (out/filename).write_bytes(private_exports(raw, identity, additions))
    manifest = dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,
        module_file=filename,module_sha256=sha(out/filename),original_imports=identity['imports'],
        added_exports=additions,functions=functions,only_export_section_changed=True,
        implicit_start=False,builder_original_executions=0,incoming_source_schema=dict(actual925_native_contact_flag=1,category=0,param5='prior330queueindex;sourceprovenunreadincategory0;notmodeledasfixturezero',direct1076controlled_calls=0),thunder_clap88_hex=thunder.hex(),
        cleave88_hex=read(5882740,88).hex(),coefficient1601276_hex=read(1601276,28).hex(),
        outgoing_identity_prefix1056242_hex=read(1056242,16).hex(),outgoing_rank_prefix1052715_hex=read(1052715,8).hex(),class108_hex=read(5877920,108).hex(),regen44_hex=read(1592624,44).hex(),leech44_hex=read(1591852,44).hex(),static_reads=read.proof,basic_fallback44_hex=read(1596344,44).hex(),basic_packet_flag1_static=True,scope='Actualfullopening/newThunder->external884-compatibleclock->full2123->full925 perstep;notfull884;noincominghurtfixture')
    save(out/'manifest.json',manifest)
    return manifest
