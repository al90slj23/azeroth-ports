#!/usr/bin/env python3
"""Compare the model with byte-identical CONTIGUOUS ORIGINAL1065 FRAGMENTS.

The executed1065 fragments are its initialization stores and existing-ability
upgrade loop, not the complete1065. The loop calls the unchanged original25242
body. Wrapper setup is synthetic; original gameplay/entrypoints are absent.
"""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tarfile

from build_upgrade_oracle import (ROOT, PANIC, TARGET, BODY_SHA, TABLES,
                                  unsigned, signed, section, export)
from wasm_index import ORIGINAL_SHA, body_ranges, sha

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.ability_state import (AbilityDefinition, AbilityRecord, UpgradeCard,
    NewAbilityCard, SelectionState, UnresolvedAbilityEffect, accept_upgrade_selection,
    accept_new_ability_selection,
    apply_upgrade_card, initialize_ability, neutral_additional_bytes,
    selection_completion_control)

WAT = ROOT / 'evidence/abilities-20261031T224245.735794Z/function-1065.wat'
F1065_SHA = 'f37ff412a377544132ceefbcad008468a369b64b5f5b78a6749bb87cdbb3cf27'


def uint(data, p):
    value = shift = 0
    while True:
        byte = data[p]; p += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, p
        shift += 7


def code_bodies(binary):
    p = 8
    while p < len(binary):
        kind = binary[p]; length, begin = uint(binary, p + 1); end = begin + length
        if kind == 10:
            count, p = uint(binary, begin); bodies = []
            for _ in range(count):
                length, p = uint(binary, p)
                bodies.append(binary[p:p + length]); p += length
            assert p == end
            return bodies
        p = end
    raise ValueError('Missing code section')


def local_end(body):
    groups, p = uint(body, 0)
    for _ in range(groups):
        _, p = uint(body, p); p += 1
    return p


def build_fragment_oracle(output):
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    assert sha(source) == ORIGINAL_SHA
    binary = source.read_bytes(); ranges = body_ranges(binary)
    original1065 = binary[ranges[1065][0]:ranges[1065][1]]
    original25242 = binary[ranges[TARGET][0]:ranges[TARGET][1]]
    assert hashlib.sha256(original1065).hexdigest() == F1065_SHA
    assert hashlib.sha256(original25242).hexdigest() == BODY_SHA
    lines = WAT.read_text().splitlines()
    assert lines[835].strip().startswith('loop') and lines[947].strip() == 'end'
    assert lines[456].strip() == 'local.get 3' and lines[494].strip() == 'i32.store offset=192'
    locals_text = lines[1]
    compiler = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wat2wasm'
    provenance = json.loads((ROOT / '.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    archives = list((ROOT / '.toolchain').rglob('wabt-1.0.42-macos-arm64.tar.gz'))
    if not archives:
        archives = [p for p in (ROOT / '.toolchain').rglob('*.tar.gz')
                    if sha(p) == provenance['archive_sha256']]
    assert len(archives) == 1 and sha(archives[0]) == provenance['archive_sha256']
    with tarfile.open(archives[0]) as archive:
        members = [m for m in archive.getmembers() if m.name.endswith('/bin/wat2wasm')]
        assert len(members) == 1 and archive.extractfile(members[0]).read() == compiler.read_bytes()

    def compile_function(name, instructions):
        path = output / (name + '.wat')
        path.write_text('(module (import "stub" "upgrade" (func (param i32 i32 i32) (result f32))) '
                        '(memory 82 82) (func (param i32 i32)\n' + locals_text + '\n'
                        + instructions + '\n))\n')
        compiled = path.with_suffix('.wasm')
        subprocess.run([str(compiler), str(path), '-o', str(compiled)], check=True, timeout=30)
        body = code_bodies(compiled.read_bytes())[0]
        return body[:local_end(body)], body[local_end(body):-1]

    decl, loop = compile_function('loop-fragment', '\n'.join(lines[835:948]).replace('call 25242', 'call 0'))
    assert loop.count(b'\x10\x00') == 1
    loop = loop.replace(b'\x10\x00', b'\x10' + unsigned(25242))
    _, initialization = compile_function('initialization-fragment', '\n'.join(lines[456:495]))
    assert original1065.count(loop) == 1 and original1065.count(initialization) == 1
    _, setup_loop = compile_function('loop-wrapper-setup', '''
        local.get 1 i32.load local.set 4
        local.get 1 i32.load offset=4 local.set 5
        local.get 1 i32.load offset=8 local.set 11
        local.get 4 local.set 2
        local.get 0 i32.const 32 i32.add local.set 10
        local.get 0 local.set 1
    ''')
    _, setup_init = compile_function('initialization-wrapper-setup', '''
        local.get 0 i32.const 192 i32.sub local.set 3
        local.get 1 i32.const 1719492 i32.sub local.set 1
    ''')
    # Preserve all function indices used by25242. There are no host imports.
    count = PANIC + 3
    types = b'\x03\x60\x03\x7f\x7f\x7f\x01\x7d\x60\x03\x7f\x7f\x7f\x00\x60\x02\x7f\x7f\x00'
    declarations = bytearray(b'\x01' * count)
    declarations[TARGET] = 0; declarations[-2:] = b'\x02\x02'
    stub = b'\x03\x00\x00\x0b'
    body_loop = decl + setup_loop + loop + b'\x0b'
    body_init = decl + setup_init + initialization + b'\x0b'
    code = (unsigned(count) + stub * TARGET + unsigned(len(original25242)) + original25242
            + stub * (PANIC - TARGET) + unsigned(len(body_loop)) + body_loop
            + unsigned(len(body_init)) + body_init)
    data = bytearray(unsigned(len(TABLES)))
    for address, offset in TABLES:
        data += b'\x00\x41' + signed(address) + b'\x0b\x14' + binary[offset:offset + 20]
    module = (b'\0asm\1\0\0\0' + section(1, types)
              + section(3, unsigned(count) + declarations)
              + section(5, b'\x01\x01' + unsigned(82) + unsigned(82))
              + section(7, b'\x03' + export('apply', 0, PANIC + 1)
                        + export('initialize', 0, PANIC + 2) + export('memory', 2, 0))
              + section(10, code) + section(11, data))
    path = output / 'isolated-ability-fragments.wasm'; path.write_bytes(module)
    validator = compiler.with_name('wasm-validate')
    assert sha(validator) == provenance['tools']['wasm-validate']['sha256']
    subprocess.run([str(validator), str(path)], check=True, timeout=30)
    parsed = code_bodies(module)
    assert len(parsed) == count and parsed[TARGET] == original25242
    assert parsed[PANIC + 1] == body_loop and parsed[PANIC + 2] == body_init
    assert all(body == b'\x00\x00\x0b' for i, body in enumerate(parsed)
               if i not in (TARGET, PANIC + 1, PANIC + 2))
    fragments = []
    for name, fragment, start_line, end_line in (
            ('existing_ability_upgrade_loop', loop, 836, 948),
            ('new_ability_initialization_stores', initialization, 457, 495)):
        begin = ranges[1065][0] + original1065.index(fragment)
        fragments.append({'name': name, 'wat_lines': [start_line, end_line],
                          'original_file_start': begin, 'original_file_end': begin + len(fragment),
                          'bytes': len(fragment), 'sha256': hashlib.sha256(fragment).hexdigest(),
                          'byte_identical_contiguous_fragment': True})
    assert sha(source) == ORIGINAL_SHA
    return path, {'original_wasm_sha256': ORIGINAL_SHA, 'original1065_body_sha256': F1065_SHA,
                  'original25242_body_sha256': BODY_SHA, 'fragments': fragments,
                  'module_sha256': sha(path), 'imports': [], 'start': None,
                  'full1065_executed': False, 'full_game_started': False}


def corpus():
    cases = []
    def add(group, record, kinds, tier, kind=0, name=b'fireball'):
        cases.append({'id': len(cases), 'group': group, 'record_hex': record.to_bytes().hex(),
                      'kinds': list(kinds), 'tier': tier, 'definition_kind': kind,
                      'definition_id_hex': name.hex()})
    base = AbilityRecord(12288)
    for tier in range(5):
        for length in (1, 2, 3):
            for kinds in itertools.product(range(5), repeat=length):
                add('ordered_kind_sequences', base, kinds, tier)
    for level in (0, 1, 2, 3, 16777215, 16777216, 0xfffffffe, 0xffffffff):
        for kind in range(5):
            add('level_and_counter_wrap', replace(base, level=level, counts=(0xffffffff,) * 5),
                (kind, kind), 4)
    for name in (b'seal_fate', b'soul_fire', b'lightwell', b'faerie_fire', b'fireball'):
        for extra in (0, 1, 2, 11, 12, 0xffffffff):
            add('target_caps', replace(base, extra_targets=extra), (2, 2, 2), 4, 11, name)
    rng = random.Random(0x1065A80)
    for _ in range(1500):
        words = [rng.getrandbits(32) for _ in range(20)]
        words[0] = 12288
        # Cover signed zero/subnormal/large finite fields without claiming NaN payload identity.
        for i in (2, 3, 4, 6, 7, 13, 14, 16, 17, 18, 19):
            if words[i] & 0x7f800000 == 0x7f800000:
                words[i] &= 0xff7fffff
        add('seeded_finite_record_words', AbilityRecord.from_bytes(struct.pack('<20I', *words)),
            tuple(rng.randrange(5) for _ in range(rng.randrange(1, 16))), rng.randrange(5),
            rng.choice((0, 11, 255)), rng.choice((b'fireball', b'seal_fate')))
    return cases


def static_boundary_checks():
    definition = AbilityDefinition(12288, b'fireball', 0)
    record = AbilityRecord(12288)
    card = UpgradeCard(0, (0, 1), 2)
    state = SelectionState((record,), (card,))
    result = accept_upgrade_selection(state, 0, {12288: definition})
    assert result.accepted and result.state.owned[0].level == 3
    assert result.state.phase2299 == 2 and len(result.pending_effects) == 3
    assert not accept_upgrade_selection(replace(state, phase2299=1), 0, {}).accepted
    assert not accept_upgrade_selection(state, -1, {}).accepted
    assert not accept_upgrade_selection(replace(state, selection_kind2297=255), 0, {}).accepted
    assert apply_upgrade_card(record, UpgradeCard(0, (), 999), definition) == record
    assert initialize_ability(definition, additional=neutral_additional_bytes()) == record
    new_state = SelectionState((), (NewAbilityCard(b'fireball', 0),))
    acquired = accept_new_ability_selection(new_state, 0, {b'fireball': definition},
                                           additional=neutral_additional_bytes())
    assert acquired.state.owned == (record,) and len(acquired.pending_effects) == 4
    for kwargs in ({}, {'tier': 1, 'additional': neutral_additional_bytes()}):
        try:
            initialize_ability(definition, **kwargs)
        except UnresolvedAbilityEffect:
            pass
        else:
            raise AssertionError('Missing original helper must be explicit')
    for p0, p1, p2 in itertools.product(range(3), repeat=3):
        for entry in (0, 1, 2, 3):
            result = selection_completion_control(entry_kind=entry, pending2088=p0,
                pending2092=p1, pending2096=p2, loot_collection_complete=True)
            counts = [p0, p1, p2]; slot = entry if entry < 3 else 0
            counts[slot] = max(0, counts[slot] - 1)
            expected = 1 if counts[1] else 2 if counts[2] else 0 if counts[0] else None
            assert result.next_selection_kind == expected
    raw = bytearray(80); struct.pack_into('<5I', raw, 60, 0, 9000, 2, 7, 4)
    assert UpgradeCard.from_candidate_bytes(raw, lambda p, n: b'\x03\x00') == UpgradeCard(7, (3, 0), 4)
    struct.pack_into('<I', raw, 60, 0x80000001)
    assert UpgradeCard.from_candidate_bytes(raw, lambda p, n: b'\x03\x00') == UpgradeCard(7, (3, 0), 4)
    return {'model_boundary_checks': 'passed', 'completion_queue_cases': 108,
            'qualification': 'Boundary assertions are model checks and static-source recovery, not original4595 execution.'}


def main():
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('ability-state-oracle-%Y%m%dT%H%M%S.%fZ')
    output.mkdir()
    module, manifest = build_fragment_oracle(output)
    cases = corpus(); case_file = output / 'cases.jsonl'
    case_file.write_text(''.join(json.dumps(c, separators=(',', ':')) + '\n' for c in cases))
    expected = []
    for case in cases:
        record = AbilityRecord.from_bytes(bytes.fromhex(case['record_hex']))
        definition = AbilityDefinition(12288, bytes.fromhex(case['definition_id_hex']), case['definition_kind'])
        result = apply_upgrade_card(record, UpgradeCard(0, tuple(case['kinds']), case['tier']), definition)
        # WASM arithmetic NaN payloads are unspecified; compare NaN classes for
        # arithmetic fields, while preserving all other original record bytes.
        expected.append({'id': case['id'], 'record_hex': result.to_bytes().hex()})
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    actual_file = output / 'original-fragment-results.jsonl'
    with actual_file.open('w') as out:
        subprocess.run([str(runtime), str(ROOT / 'scripts/run_ability_state_oracle.mjs'),
                        str(module), str(case_file)], stdout=out, check=True, timeout=45)
    actual = [json.loads(line) for line in actual_file.read_text().splitlines()]
    assert len(actual) == len(expected) + 1
    initialization = actual.pop()
    assert initialization == {'initialization_hex': AbilityRecord(12288).to_bytes().hex()}
    mismatches = []
    nan_equivalent_words = 0
    for case, exp, got in zip(cases, expected, actual):
        assert got['id'] == exp['id']
        left = struct.unpack('<20I', bytes.fromhex(exp['record_hex']))
        right = struct.unpack('<20I', bytes.fromhex(got['record_hex']))
        differences = []
        for offset, (a, b) in enumerate(zip(left, right)):
            is_nan = lambda x: x & 0x7f800000 == 0x7f800000 and x & 0x7fffff != 0
            if a != b and offset in (3, 4, 6, 7) and is_nan(a) and is_nan(b):
                nan_equivalent_words += 1
            elif a != b:
                differences.append(offset * 4)
        if differences:
            mismatches.append({'input': case, 'model': exp, 'original_fragment': got, 'offsets': differences})
    (output / 'model-results.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in expected))
    (output / 'mismatches.json').write_text(json.dumps(mismatches, indent=2) + '\n')
    summary = {**manifest, 'case_count': len(cases), 'initialization_cases': 1,
               'mismatch_count': len(mismatches), 'nan_equivalent_words': nan_equivalent_words,
               'groups': {g: sum(c['group'] == g for c in cases) for g in sorted({c['group'] for c in cases})},
               'boundary_validation': static_boundary_checks(), 'network_used': False,
               'user_saves_accessed': False, 'oracle_qualification': 'Original1065 fragments, NOT full1065.',
               'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (
                   Path(__file__), ROOT / 'scripts/run_ability_state_oracle.mjs',
                   ROOT / 'reconstruction/core_spec/ability_state.py')}}
    (output / 'differential-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'run_directory': str(output), **summary}))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
