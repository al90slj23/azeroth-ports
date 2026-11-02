#!/usr/bin/env python3
"""Bind current139 victory terminal49961/17209/1965 over canonical world."""
from incoming139_tools import (ROOT, SOURCE, SOURCE_SHA, original, private_exports,
                               function_proof, static_reader, sha, save)


def build(out):
    raw, identity, ranges = original()
    static = out/'static'
    static.mkdir()
    ids = {2945,1600,1108,925,49961,17209,17319,16380,46692,1965,53225,29912,23333,
           55851,11741,45182,20060,28993,38882,32605,66545,66546}
    functions, texts = function_proof(raw, identity, ranges, ids, static)
    read = static_reader(raw, identity)
    assert 'i32.const 432' in texts[17209] and 'call 17319' in texts[17209] and 'call 16380' in texts[17209]
    assert 'call 17209' in texts[49961] and 'call 55851' in texts[49961] and 'call 1965' in texts[49961]
    assert read(1588650,7)==b'victory'
    for offset in(2795,2803,2811,2819,2827):assert f'i64.const 0\n                  i64.store offset={offset} align=1' in texts[1600]
    for offset in(1169,1177,1185,1193):assert f'i64.store offset={offset} align=1' in texts[1600]
    cls=read(5877920,108);race=read(5874636,32);zone=read(5871348,152)
    def string_at(row,offset):
        ptr=int.from_bytes(row[offset:offset+4],'little');count=int.from_bytes(row[offset+4:offset+8],'little')
        return read(ptr,count).decode('utf8')
    labels=dict(class_id=string_at(cls,16),class_label=string_at(cls,24),race_label=string_at(race,0),zone_label=string_at(zone,16))
    assert labels==dict(class_id='warrior',class_label='Warrior',race_label='Human',zone_label='Elwynn Forest')
    additions = [('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),
        ('research139_gw_opening',0,1108),('research139_gw_stack',3,0),
        ('research139_auto_ai925',0,925),('research139_terminal49961',0,49961)]
    filename = 'terminal139-original-exports.wasm'
    (out/filename).write_bytes(private_exports(raw, identity, additions))
    manifest = dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,
        module_file=filename,module_sha256=sha(out/filename),original_imports=identity['imports'],
        added_exports=additions,functions=functions,only_export_section_changed=True,
        implicit_start=False,builder_original_executions=0,current_labels=labels,
        class108_hex=cls.hex(),race32_hex=race.hex(),zone152_hex=zone.hex(),static_reads=read.proof,
        scope='Actualfull1108->full925movingproducer->controlled400->full49961;canonicalterrain;notnaturalBossvictory')
    save(out/'manifest.json',manifest)
    return manifest
