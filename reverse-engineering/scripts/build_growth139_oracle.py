#!/usr/bin/env python3
"""Bounded static139 first-level constructors/gain/choice export module."""
import ast
import struct
from incoming139_tools import ROOT, SOURCE, SOURCE_SHA, original, private_exports, function_proof, static_reader, sha, save


def build(out):
    raw, identity, ranges = original()
    static = out / 'static'
    static.mkdir()
    ids = {1600, 1542, 83304, 4677, 2181, 1093, 1501, 30022, 27572, 27167, 28657,
           11033, 28155, 86979, 34853, 35988, 26364, 25613, 4603, 1173}
    functions, texts = function_proof(raw, identity, ranges, ids, static)
    assert functions[1600]['signature'] == ('7f7f7f', '')
    assert functions[4677]['signature'] == functions[1093]['signature'] == ('7f7f', '')
    assert functions[83304]['signature'] == ('', '')
    assert 'i32.const 0\n      i32.const 1\n      call 2181' in texts[4677]
    assert 'i32.const 2\n        i32.store8 offset=2587' in texts[2181]
    read = static_reader(raw, identity)
    path = ROOT / 'reconstruction/core_spec/candidates139_data.py'
    declarations = {node.targets[0].id: ast.literal_eval(node.value) for node in ast.parse(path.read_text()).body if isinstance(node, ast.Assign)}
    cls = read(5877920, 108)
    kit = []
    ptr, count = struct.unpack_from('<II', cls, 32)
    for p, n in struct.iter_unpack('<II', read(ptr, count * 8)):
        kit.append(read(p, n).decode())
    assert tuple(kit) == declarations['WARRIOR_KIT139']
    for name, (p, rawhex, kinds) in declarations['DEFINITIONS139'].items():
        record = read(p, 88)
        a, n = struct.unpack_from('<II', record, 12)
        k, z = struct.unpack_from('<II', record, 36)
        assert record.hex() == rawhex and read(a, n).decode() == name and tuple(read(k, z)) == kinds
    assert tuple(struct.unpack('<5I', read(5912332, 20))) == declarations['TIER_COOLDOWN139']
    assert tuple(struct.unpack('<5I', read(5912384, 20))) == declarations['TIER_DAMAGE139']
    added = [('research139_growth_ctor', 0, 1600), ('research139_growth_locale', 0, 83304),
             ('research139_growth_gain', 0, 4677), ('research139_growth_select', 0, 1093), ('research139_growth_stack', 3, 0)]
    module = private_exports(raw, identity, added)
    name = 'growth139-original-exports.wasm'
    (out / name).write_bytes(module)
    result = dict(version='0.139.0', build='f79c5e2b4', source_sha256=SOURCE_SHA,
                  module_file=name, module_sha256=sha(out / name), original_imports=identity['imports'], added_exports=added,
                  functions=functions, static_reads=read.proof, declarations139=declarations,
                  only_export_section_changed=True, builder_original_executions=0,
                  limitations=['Explicit empty researchP376 andborrowedflatV128;not naturalApp/worldRc.',
                               'Phase1 is an explicitcomponentinput;real2181 phase2 and1093 remainunaltered.'])
    save(out / 'manifest.json', result)
    return result
