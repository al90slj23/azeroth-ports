#!/usr/bin/env python3
"""Current139 complete922 private export-only fixture and static bindings."""
import sqlite3, struct
from incoming139_tools import (ROOT, SOURCE_SHA, PROFILE, original,
    private_exports, function_proof, static_reader, save, sha)


def build(out):
    raw, identity, ranges = original()
    static = out/'static'
    static.mkdir()
    functions, texts = function_proof(raw, identity, ranges,
        {922, 913, 8673, 27754, 36518, 20123, 48064, 5797, 5406,
         38554, 44070, 2189, 10490, 15962, 93344}, static)
    assert functions[922]['signature'] == ('7f7f', '7f')
    assert functions[44070]['signature'] == ('7f7f7f', '7f')
    assert functions[922]['body_bytes'] == 25214
    assert 'i32.const 432' in texts[20123] and 'i32.const 8\n              i32.sub\n              i32.load8_u' in texts[8673]
    normalized = '\n'.join(line.strip() for line in texts[8673].splitlines())
    assert 'i32.const 52\ni32.sub\nf32.load' in normalized
    assert 'i32.const 306\ni32.store16 offset=44' in '\n'.join(line.strip() for line in texts[10490].splitlines())
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro', uri=True) as db:
        calls = {str(i): list(db.execute('select callee,wat_line from calls where caller=?', (i,))) for i in functions}
    read = static_reader(raw, identity)
    declarations = []
    for index in range(114):
        p = 5882740+index*88
        ptr, n = struct.unpack('<2I', read(p+12, 8))
        if n == 6 and read(ptr, n) == b'cleave':
            declarations.append(dict(pointer=p, ability_id='cleave', raw88_hex=read(p, 88).hex()))
    assert len(declarations) == 1
    definition = declarations[0]
    decl = bytes.fromhex(definition['raw88_hex'])
    assert decl[84] == 5 and struct.unpack_from('<II', decl, 44)[0] == 845 and struct.unpack_from('<I', decl)[0] == 0
    coefficients = struct.unpack('<7I', read(1601276, 28))
    assert coefficients[3] == 0x3f800000
    proof = dict(version='0.139.0', build='f79c5e2b4', original_sha256=SOURCE_SHA,
        functions=functions, direct_calls=calls, definition=definition,
        execution_coefficients=coefficients, static_reads=read.proof,
        scoped_rules=dict(normal_kind40=-1, normal_header64=-1,
            boss_header244=-1, classification_byte=424,
            priority_until=380, damage_school_bonus_until=372,
            interpolation_from=[316, 320], interpolation_to=[328, 332],
            movement_start=340, duration=344, ordinary_near_squared=36,
            radius_squared_inclusive=True, critical_uses_strict_greater=True,
            spell_sets=[[664, 668, 672], [676, 680, 684], [724, 728, 732]],
            first_set_skip='G552 !=0 or G908&1', effect0_2189='no Game/target mutation',
            launch306='packed source twice,spellU32,flagsU16=256,countU8,ordered rawGUID64s,missU8=0,targetmaskU16=2,packedfirst'),
        original_executions=0, old_acceptance_transferred=False,
        limits=['Static binding does not itself prove current runtime behavior.'])
    save(static/'trace.json', proof)
    additions = [('research139_cast922', 0, 922), ('research139_cast_stack0', 3, 0)]
    module = private_exports(raw, identity, additions)
    path = out/'cast139-original-exports.wasm'
    path.write_bytes(module)
    manifest = dict(version='0.139.0', build='f79c5e2b4', original_sha256=SOURCE_SHA,
        module_file=path.name, module_sha256=sha(path), definition=definition,
        entry=functions[922], static_trace_sha256=sha(static/'trace.json'),
        original_imports=identity['imports'], original_exports=identity['exports'],
        added_exports=additions, only_changed_section=7, implicit_start=False,
        denied_imports=882, allocator_index=93344, stack_initial=1048576,
        original_executed_by_builder=False,
        validation='Fresh Node WebAssembly.compile validates exact export-only module before instantiation')
    save(out/'manifest.json', manifest)
    return manifest, proof
