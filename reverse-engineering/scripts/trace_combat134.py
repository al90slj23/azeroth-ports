#!/usr/bin/env python3
"""Retain reviewed official0.134.0 damage/T/death guards; never execute WASM."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY = ROOT / 'scripts/extract_catalogue134.py'
DEPENDENCY_SHA = '4e465095731c6abc9775ce8445fdd6b96c11982300ec33be1c1b4bda0b8b709a'
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
if sha(DEPENDENCY) != DEPENDENCY_SHA:
    raise ValueError('Pinned static binary-reader dependency differs')
from extract_catalogue134 import (Reader, parse_binary, reconstruct, require, digest, save,
                                  strict_json, SOURCE, SOURCE_SHA, PROFILE, WAT, WAT_SHA, DB, DB_SHA)

OLD_WAT = ROOT / 'evidence/damage-core-20261031T214725.681383Z/function-933.wat'
OLD_WAT_SHA = 'e3f34bbb48729849c3d8feb3aed7ee9710e0550ec0e0e78dc45e636335221d26'
MODEL = ROOT / 'reconstruction/core_spec/combat.py'
MODEL_SHA = '1bff4413144ac703fbac172b559034c81376f1c8e70fc768cb28184be890dd5c'
FUNCTIONS = (914, 922, 968, 1063)


def signatures(binary, import_count):
    top, sections = Reader(binary, 8), {}
    while top.pos < top.end:
        kind, length = top.byte(), top.leb()
        start = top.pos
        top.raw(length)
        if kind:
            sections[kind] = (start, top.pos)
    typ = Reader(binary, *sections[1])
    types = []
    for _ in range(typ.leb()):
        require(typ.byte() == 0x60, 'Unexpected non-function type')
        types.append((typ.raw(typ.leb()), typ.raw(typ.leb())))
    typ.finished()
    fun = Reader(binary, *sections[3])
    declarations = [fun.leb() for _ in range(fun.leb())]
    fun.finished()
    return {i: {'type_index': declarations[i - import_count],
                'parameters_hex': types[declarations[i - import_count]][0].hex(),
                'results_hex': types[declarations[i - import_count]][1].hex()} for i in FUNCTIONS}


def main():
    started = time.monotonic()
    source_hash = sha(Path(__file__))
    inputs = {SOURCE: SOURCE_SHA, WAT: WAT_SHA, DB: DB_SHA, DEPENDENCY: DEPENDENCY_SHA,
              OLD_WAT: OLD_WAT_SHA, MODEL: MODEL_SHA}
    require(all(sha(path) == expected for path, expected in inputs.items()), 'Pinned source/tool/baseline identity differs')
    binary = SOURCE.read_bytes()
    require(digest(binary) == SOURCE_SHA, 'Source readback differs')
    profile = parse_binary(binary)
    require(profile['function_imports'] == 878 and profile['defined_functions'] == 175316, 'New source function profile differs')
    sigs = signatures(binary, profile['function_imports'])
    require(sigs[914] == {'type_index': 267, 'parameters_hex': '7f7e7d7f7f7f7f', 'results_hex': ''}, 'New914 signature differs')
    require(sigs[922] == {'type_index': 6, 'parameters_hex': '7f7f', 'results_hex': '7f'}, 'New922 signature differs')
    require(sigs[1063] == {'type_index': 273, 'parameters_hex': '7f7d7e7f7f7f', 'results_hex': ''}, 'New incoming signature differs')
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('combat0134-chain-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    connection = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    functions, normalized, raw_functions = [], {}, {}
    try:
        meta = {key: strict_json(value) for key, value in connection.execute('SELECT key,value FROM meta')}
        require(meta['original_sha256'] == SOURCE_SHA and meta['wat_sha256'] == WAT_SHA
                and meta['terminal_parentheses_supported'] is True, 'Full index provenance differs')
        with WAT.open('rb') as stream:
            for index in FUNCTIONS:
                row = connection.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?', (index,)).fetchone()
                require(row is not None and tuple(row[3:5]) == profile['bodies'][index]
                        and row[5] == row[4] - row[3], 'Binary/index function range differs')
                stream.seek(row[0])
                wat = stream.read(row[1] - row[0])
                require(re.findall(rb'^  \(func \(;(\d+);\)', wat, re.M) == [str(index).encode()], 'Not one complete new function')
                body = binary[row[3]:row[4]]
                (run / f'function-{index}.wat').write_bytes(wat)
                (run / f'function-{index}.body.bin').write_bytes(body)
                raw_functions[index] = wat
                normalized[index] = '\n'.join(x.strip() for x in wat.decode().splitlines())
                functions.append({'function_index': index, **sigs[index], 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': len(body), 'body_sha256': digest(body), 'wat_start': row[0],
                                  'wat_end': row[1], 'wat_line': row[2], 'wat_bytes': len(wat), 'wat_sha256': digest(wat),
                                  'direct_callers': [x[0] for x in connection.execute('SELECT DISTINCT caller FROM calls WHERE callee=? ORDER BY caller', (index,))]})
    finally:
        connection.close()
    guards = []
    def guard(index, label, sequence):
        needle = '\n'.join(sequence)
        positions = [m.start() for m in re.finditer(re.escape(needle), normalized[index])]
        require(positions, 'Reviewed new instruction guard differs: ' + label)
        start_line = next(x['wat_line'] for x in functions if x['function_index'] == index)
        lines = [normalized[index][:p].count('\n') + 1 for p in positions]
        guards.append({'function_index': index, 'label': label, 'function_lines': lines,
                       'complete_wat_lines': [start_line + p - 1 for p in lines], 'instructions': sequence})
    def g(index, label, text):
        guard(index, label, text.split('|'))
    g(914, 'active phase gate', 'local.get 0|i32.load8_u offset=2579|i32.const 1|i32.ne|br_if 0 (;@2;)')
    g(914, 'unit vector count and424B stride', 'local.get 0|i32.load offset=1784|local.tee 29|i32.const 424|i32.mul|local.set 10')
    g(914, 'unit vector pointer', 'local.get 0|i32.load offset=1780|local.tee 11|local.set 7')
    g(914, 'entry time', 'local.get 0|f32.load offset=2344|local.set 37')
    g(914, 'full64-bit GUID lookup', 'local.get 7|i64.load offset=112|local.set 48|local.get 7|i32.const 424|i32.add|local.set 7|local.get 1|local.get 48|i64.ne')
    g(914, 'M control380', 'local.get 9|local.get 11|i32.add|local.tee 15|i32.const 44|i32.sub|f32.load|local.get 37|f32.gt')
    g(914, 'M control124', 'local.get 15|i32.const 300|i32.sub|f32.load|local.get 37|f32.gt')
    g(914, 'M control388', 'local.get 15|i32.const 36|i32.sub|f32.load|local.get 37|f32.gt')
    g(914, 'M item count and pointer', 'local.get 0|i32.load offset=2024|local.tee 7|i32.eqz|br_if 0 (;@5;)|local.get 0|i32.load offset=2020|local.set 14')
    for tag in (18, 19, 20, 21, 28):
        g(914, 'M raw item tag' + str(tag), f'i32.load8_u|i32.const {tag}|i32.eq|select')
    g(914, 'M elite244/flag416', 'local.get 15|i32.const 180|i32.sub|i32.load|i32.const -1|i32.eq|if  ;; label = @5|local.get 15|i32.const 8|i32.sub|i32.load8_u|i32.const 1|i32.ne')
    g(914, 'M shield1532 gate', 'local.get 0|f32.load offset=1532|f32.const 0x0p+0 (;=0;)|f32.gt')
    g(914, 'M final raw additive368', 'local.get 15|i32.const 56|i32.sub|f32.load|f32.add')
    g(914, 'T starts positive zero and skips zero spell/count', 'f32.const 0x0p+0 (;=0;)|local.set 35|block  ;; label = @3|local.get 3|i32.eqz|br_if 0 (;@3;)|local.get 0|i32.load offset=2048|local.tee 10|i32.eqz|br_if 0 (;@3;)')
    g(914, 'T record pointer/end36B', 'local.get 0|i32.load offset=2044|local.tee 12|local.get 10|i32.const 36|i32.mul|i32.add|local.set 10')
    g(914, 'T unitHP288 and gate356 address', 'local.get 11|i32.const 136|i32.sub|local.set 13')
    g(914, 'T tag50/51 unsigned selector', 'i32.const 4|local.get 12|i32.load|local.tee 7|i32.const 12|i32.sub|local.get 7|i32.const 11|i32.le_u|select|i32.const 38|i32.sub|br_table 0 (;@10;) 1 (;@9;) 5 (;@5;)')
    g(914, 'T tag50 raw unit356 gate', 'local.get 13|i32.const 68|i32.add|local.set 14')
    g(914, 'T tag50 strict greater-than gate', 'local.get 14|f32.load|local.get 37|f32.gt|i32.eqz|br_if 4 (;@5;)')
    g(914, 'T tag51 HP/maxHP*threshold strict gate', 'local.get 13|f32.load|local.get 13|i32.const 4|i32.add|f32.load|local.get 12|f32.load offset=12|f32.mul|f32.lt|i32.eqz|br_if 3 (;@5;)')
    g(914, 'T ID pointer/length and114-table negative cursor', 'local.get 12|i32.load offset=4|local.set 15|local.get 8|local.get 12|i32.load offset=8|local.tee 7|i32.store offset=996|local.get 8|local.get 15|i32.store offset=992|i32.const -10032|local.set 9')
    g(914, 'T ID exact string comparison', 'local.get 9|i32.const 5473516|i32.add|i32.load|local.get 15|local.get 7|call 82065|i32.eqz')
    g(914, 'T tag50 spell match and contribution12', 'local.get 9|i32.const 5473548|i32.add|i32.load|local.get 3|i32.ne|br_if 2 (;@5;)|i32.const 12|br 1 (;@6;)')
    g(914, 'T tag51 spell match and contribution16', 'local.get 9|i32.const 5473548|i32.add|i32.load|local.get 3|i32.ne|br_if 1 (;@5;)|i32.const 16')
    g(914, 'T ordered f32 sum and36B next record', 'local.get 12|i32.add|f32.load|f32.add|local.set 35|end|local.get 12|i32.const 36|i32.add|local.tee 12|local.get 10|i32.ne|br_if 0 (;@4;)')
    g(914, 'T missing ID exits to panic path', 'local.get 9|i32.const 88|i32.add|local.tee 9|br_if 0 (;@10;)|end|br 8 (;@1;)')
    g(914, 'T missing ID final panic call', 'i32.const 1059653|local.get 8|i32.const 528|i32.add|i32.const 5459844|call 90674|unreachable)')
    g(914, 'amount times additive M+T before P', 'local.get 2|local.get 34|local.get 35|f32.add|f32.mul|i32.const 0|local.set 9')
    g(914, 'P eligibility elite244 or kind64', 'local.tee 7|i32.const 180|i32.sub|i32.load|i32.const -1|i32.eq|if  ;; label = @5|local.get 7|i32.const 360|i32.sub|i32.load|i32.const -1|i32.eq')
    g(914, 'P412 strict gate1.5', 'f32.const 0x1.8p+0 (;=1.5;)|local.set 35|local.get 7|i32.const 12|i32.sub|f32.load|local.get 37|f32.gt')
    g(914, 'P408 strict gate0.25', 'f32.const 0x1p-2 (;=0.25;)|local.set 35|local.get 7|i32.const 16|i32.sub|f32.load|local.get 37|f32.gt')
    g(914, 'special cap category bitmask unchanged', 'i32.const 1|local.get 7|i32.shl|i32.const 3340|i32.and|br_if 2 (;@2;)')
    g(914, 'special cap maxHP292/5', 'local.get 13|i32.const 132|i32.sub|f32.load|f32.const 0x1.4p+2 (;=5;)|f32.div')
    g(914, 'final GUID and marker guard', 'local.tee 20|i32.const 112|i32.add|i64.load|i64.eq|if  ;; label = @5|local.get 20|i32.load|i32.const 1|i32.ne')
    g(914, 'HP288 address and old HP', 'local.get 20|i32.const 288|i32.add|local.tee 7|local.get 7|f32.load|local.tee 36')
    g(914, 'NaN to1 minimum1 actual subtraction', 'f32.const 0x1p+0 (;=1;)|local.get 35|local.get 35|local.get 35|f32.ne|select|local.tee 34|f32.const 0x1p+0 (;=1;)|local.get 34|f32.const 0x1p+0 (;=1;)|f32.gt|select|local.tee 35|f32.sub|f32.store')
    g(914, 'accounted total f64+984 with capped oldHP', 'local.get 0|local.get 0|f64.load offset=984|local.get 35|local.get 37|f32.min|f64.promote_f32|local.tee 52|f64.add|f64.store offset=984')
    g(914, 'death HP<=0 gate', 'local.get 43|f32.const 0x0p+0 (;=0;)|f32.le|i32.eqz|if  ;; label = @4|i32.const -1|local.set 14|br 1 (;@3;)')
    g(914, 'death target base', 'local.get 9|local.get 10|i32.add|local.tee 10|i32.const 424|i32.sub|local.set 11')
    g(914, 'death duration344 zero and marker0 one', 'local.get 7|i32.const 0|i32.store|local.get 11|i32.const 1|i32.store')
    g(914, 'death movement time340, afflicted240 and death time4', 'local.get 10|i32.const 84|i32.sub|local.get 42|f32.store|local.get 10|i32.const 184|i32.sub|i32.const 0|i32.store|local.get 10|i32.const 420|i32.sub|local.get 42|f32.store')
    g(914, 'definition pointer284 after death', 'local.get 10|i32.const 140|i32.sub|i32.load|local.set 20')
    g(968, 'new default static unit definition selected', 'i32.const 5414404|local.set 5|i32.const 5411616|local.set 3|i32.const 5452060|local.set 10')
    g(922, 'cast base selected formula stats', 'local.get 0|f32.load offset=1364|local.set 25|local.get 0|f32.load offset=1360|local.set 26')
    g(922, 'cast category table address', 'local.get 9|i32.const 2|i32.shl|f32.load offset=1595772')
    g(922, 'cast fresh critical and call914', 'local.get 8|i32.load offset=44|local.get 8|i32.load8_u offset=85|local.get 1|i32.const 0|call 914')
    g(922, 'separate spell11426 barrier branch', 'local.get 6|i32.const 11426|i32.eq|if  ;; label = @20')
    g(922, 'separate barrier-specific1536 write and total shield1532', 'f32.store offset=1536|local.get 0|local.get 28|local.get 27|f32.add|f32.store offset=1532')
    g(1063, 'incoming separate ARM1392 reduction', 'local.get 1|f32.const 0x1p+0 (;=1;)|local.get 0|f32.load offset=1392|f32.sub|f32.mul|local.set 33')
    g(1063, 'incoming separate HP1528 subtraction', 'local.get 0|local.get 0|f32.load offset=1528|local.get 33|f32.sub|f32.store offset=1528')
    g(1063, 'incoming separate total f64+992', 'f64.load offset=992|local.get 33|f64.promote_f32')
    require('offset=1536' not in normalized[914] and 'i32.const 11426\n' not in normalized[914], 'Barrier-specific code unexpectedly appears in914')
    old = '\n'.join(x.strip() for x in OLD_WAT.read_text().splitlines())
    require('local.get 2\nlocal.get 31\nf32.mul' in old, 'Historical immediate amount*M baseline differs')
    memory = reconstruct(binary, profile)
    definition_address = 5411616
    definition = bytes(memory[definition_address:definition_address + 72])
    pointer, length = struct.unpack_from('<II', definition, 16)
    require((pointer, length) == (5411448, 13) and bytes(memory[pointer:pointer + length]) == b'Kobold Vermin', 'New fixture definition bytes differ')
    (run / 'fixture-unit-definition-5411616.bin').write_bytes(definition)
    scale = bytes(memory[1595772:1595772 + 28])
    require(struct.unpack('<7f', scale) == (.5, .5, 1, 1, 1, 1, .5), 'New cast scale table differs')
    (run / 'cast-category-scale.bin').write_bytes(scale)
    t_lines = raw_functions[914].splitlines(keepends=True)[899:1119]
    (run / 'damage914-complete-T-region.wat-fragment').write_bytes(b''.join(t_lines))
    state_fields = {'phase_u8': 2579, 'units_pointer': 1780, 'units_count': 1784, 'now_f32': 2344,
                    'shield_f32': 1532, 'items_pointer': 2020, 'items_count': 2024, 'item_stride': 8,
                    'T_pointer': 2044, 'T_count': 2048, 'T_stride': 36, 'accounted_f64': 984,
                    'rng_u32_offsets': [1712, 1716, 1720, 1724],
                    'packet_queue_capacity': 1872, 'packet_queue_pointer': 1876, 'packet_queue_count': 1880,
                    'player_max_hp_stat_f32': 1360, 'player_damage_stat_f32': 1364,
                    'player_crit_probability_f32': 1372, 'player_crit_multiplier_f32': 1376,
                    'player_current_hp_f32': 1528}
    unit_fields = {'stride': 424, 'marker_u32': 0, 'dead_marker_value': 1, 'death_time_f32': 4,
                   'linked_guid_u64': 32, 'kind40_i32': 40, 'kind64_i32': 64, 'guid_u64': 112,
                   'control124_f32': 124, 'additive144_f32': 144, 'additive_until148_f32': 148,
                   'additive152_f32': 152, 'additive_until156_f32': 156, 'additive160_f32': 160,
                   'additive_until164_f32': 164, 'afflicted240_u32': 240, 'elite244_i32': 244,
                   'definition_pointer': 284, 'hp_f32': 288, 'max_hp_f32': 292,
                   'movement_time_f32': 340, 'movement_duration_f32': 344, 'T50_gate356_f32': 356,
                   'additive368_f32': 368, 'control380_f32': 380, 'control388_f32': 388,
                   'phase408_f32': 408, 'phase412_f32': 412, 'elite416_u8': 416}
    t_spec = {'record_pointer_offset': 2044, 'record_count_offset': 2048, 'record_stride': 36,
              'record_fields': {'raw_tag_u32': 0, 'ability_id_pointer_u32': 4, 'ability_id_length_u32': 8,
                                'tag50_contribution_f32_or_tag51_threshold_f32': 12, 'tag51_contribution_f32': 16,
                                'remaining_bytes20_to35': 'not used by this T consumer'},
              'entry': 'T=+0; if spell==0, count==0, or target GUID absent, skip T records. This occurs before final marker==1 rejection.',
              'dispatch': 'selector=wrapping_sub_u32(select(4,wrapping_sub_u32(tag,12),tag<=u11),38); only raw tags50/51 have contributing branches.',
              'tag50': {'gate': 'unit.f32(356)>entry_now', 'contribution_offset': 12},
              'tag51': {'gate': 'unit.f32(288)<f32.mul(unit.f32(292),record.f32(12))', 'contribution_offset': 16},
              'common_filter_order': ['Evaluate tag-specific strict float gate; NaN gate result is false.',
                                      'Only after gate success, resolve the exact pointer/length ID bytes in the new114-entry ability table, stride88, base5463472.',
                                      'Missing ID branches to the original panic90674/unreachable path before any HP write; it is not a skipped record.',
                                      'If ID exists, compare its u32 spell_id at definition+44 with argument3; mismatch skips the record.',
                                      'If spell matches, T=f32.add(T,record contribution), in forward record order. No clamp/deduplication observed.'],
              'lookup': {'count': 114, 'stride': 88, 'base': 5463472, 'id_pointer_offset': 12,
                         'id_length_offset': 16, 'spell_id_offset': 44, 'string_compare_function': 82065,
                         'cursor_initial': -10032, 'length_constant': 5473520, 'pointer_constant': 5473516,
                         'spell_constant': 5473548, 'not_found_panic': 90674},
              'arithmetic': 'after=f32.mul(f32.mul(amount,f32.add(M,T)),P); all additions/multiplications round per original f32 order.',
              'nonfinite': 'Nonfinite contributions are summed as f32, without early sanitization. After P and possible special cap, final NaN-to1/minimum1 logic applies.',
              'names': 'Raw50/51 only; no skill/talent names inferred.'}
    ordinary_fixture = {'qualification': 'Statically recovered controlled-state recipe; this script does not execute or prove full return. Root performs original full914 acceptance separately.',
                        'G_allocation_bytes': 5000, 'unit_allocation_bytes': 424, 'zero_initialize_both': True,
                        'G_writes': {'1780': 'unit pointer', '1784': 1, '2579_u8': 1, '2344_f32': 10,
                                     '2024': 0, '2048': 0, '1712..1724_u32': [1, 2, 3, 4]},
                        'unit_writes': {'112_u64': 1, '288_f32': 100, '292_f32': 100,
                                        '40_i32': -1, '64_i32': -1, '244_i32': -1, '284': definition_address},
                        'call': 'damage914(G,1n,10.0,133,2,0,0); death variant amount150.0; these are invented local inputs.',
                        'definition': {'memory_address': definition_address, 'bytes': 72, 'raw_hex': definition.hex(),
                                       'sha256': digest(definition), 'name_pointer': pointer, 'name_length': length,
                                       'name': 'Kobold Vermin', 'pointer_selection_function': 968},
                        'safety_boundary': 'Allocation/host denial/no-start/deadline belongs to the separate root full-function harness. No runtime acceptance is claimed here.'}
    limitations = ['Static complete-function guards and raw bytes do not validate every proc, RNG continuation, death XP/loot or subsequent packet consumer.',
                   'Ordinary unique-GUID projection may reuse old arithmetic ideas after the new offsets/T extension are implemented; unchanged old combat.py is not a general0.134 model.',
                   'Initial directory entries and fixture names do not establish gameplay reachability.',
                   'Incoming1063 and IceBarrier-specific922 branches are separate from damage914; no incoming runtime comparison is performed.',
                   'No original module/function execution, network, saves, installed-game mutation, commit or push occurs.']
    require(all(sha(path) == expected for path, expected in inputs.items()) and sha(Path(__file__)) == source_hash, 'Inputs changed during static trace')
    for record in functions:
        i = record['function_index']
        require(sha(run / f'function-{i}.wat') == record['wat_sha256'] and sha(run / f'function-{i}.body.bin') == record['body_sha256'], 'Function artifact readback differs')
    require((run / 'fixture-unit-definition-5411616.bin').read_bytes() == definition
            and (run / 'cast-category-scale.bin').read_bytes() == scale, 'Static data artifact readback differs')
    report = {'date': '2026-11-01', 'version': '0.134.0', 'build': '983346a7', 'original_wasm_sha256': SOURCE_SHA,
              'complete_wat_sha256': WAT_SHA, 'index_sha256': DB_SHA, 'script_sha256': source_hash,
              'binary_reader_dependency_sha256': DEPENDENCY_SHA, 'old_navigation_wat_sha256': OLD_WAT_SHA,
              'unchanged_old_model_sha256': MODEL_SHA, 'complete_functions': functions, 'instruction_guards': guards,
              'G_fields': state_fields, 'unit_fields': unit_fields, 'T': t_spec, 'ordinary_fixture': ordinary_fixture,
              'M': {'order': ['1', 'sum(tag18) if U380>now or U124>now or U388>now',
                              'sum(tag19) if U244!=-1 or byte416==1', 'sum(tag20) if U288<f32.mul(U292,f32(.3))',
                              'sum(tag21) if U240!=0', 'U144 if now<U148',
                              'U152 if now<U156 else U160 if U164>now else0', 'sum(tag28) if G1532>0', 'U368'],
                     'item_sum': 'matching raw tag byte0; value f32+4; stride8; accumulator starts-0, f32.add in input order; terms add to the same M.'},
              'P': {'eligibility': 'U244!=-1 or U64!=-1', 'priority': ['U412>now =>1.5', 'else U408>now =>.25',
                         'else any unit marker0==0/kind40==2/linkedGUID32==target =>.25', 'else1']},
              'special_cap': {'condition': 'U40==3 and U32_u64==0', 'rule': 'nonzero spell resolves category; category<=11 and bitmask3340 rejects; otherwise minNum-like(amount,U292/5); zero cap result returns.',
                              'status': 'reviewed structure/constants remain, with new unit stride and lookup function30315'},
              'HP_and_death': {'damage': 'NaN amount becomes1, then minimum1; U288=oldHP-damage without zero clamp',
                               'accounting': 'G984_f64 += promote_f32(min(nonnegative_nonNaN(oldHP),damage))',
                               'death_gate': 'newHP<=0; NaN does not pass',
                               'core_writes': {'U0_u32': 1, 'U344_f32': 0, 'U240_u32': 0, 'U4_f32': 'now', 'U340_f32': 'now'},
                               'other_writes': 'position interpolation/freeze, packet field22, per-spell statistics, counters and extended effects remain in the full body; not all independently reconstructed.'},
              'cast_base': {'formula': 'G1364 * (definition48*1.4*ability12*ability52*categoryScale + (definition48>0 ? G1360*ability72 :0))',
                            'category_scale': {'memory_address': 1595772, 'raw_hex': scale.hex(), 'sha256': digest(scale), 'values': [.5, .5, 1, 1, 1, 1, .5]},
                            'critical': 'one ordered U24 RNG draw at1712/1716/1720/1724; strict G1372>U; critical amount multipliesG1376; selected922 path, not universal all-ability damage'},
              'incoming_separate': {'function': 1063, 'signature': sigs[1063], 'ARM_f32': 1392, 'player_HP_f32': 1528,
                                    'total_shield_f32': 1532, 'barrier_component_f32': 1536, 'incoming_accounted_f64': 992,
                                    'boundary': '922 spell11426 branch separately updates1536/1532;1063 subtracts absorption from1532 and1536.914 has no1536/11426 instructions. Do not apply a player barrier cap as an enemy914 cap.',
                                    'target_executed': False, 'cap_semantics_fully_reconstructed': False},
              'new_vs_old': ['unit stride416->424; GUID112/HP288/maxHP292/marker0 retained by new guards.',
                             'G phase2299->2579, unitptr/count1596/1600->1780/1784, now2064->2344, shield1348->1532, total824->984, items1012/1016->2020/2024.',
                             'Target controls376/384->380/388, additive364->368, phase404/408->408/412, elite byte412->416.',
                             'New T36B records2044/2048 add spell-matched raw50/51 contributions before P; old immediate amount*M has no corresponding T scan.',
                             'HP floor/subtraction/accounting and core death fields preserve their reviewed operations; complete side-effect equivalence is not claimed.'],
              'source_and_artifact_readback_verified': True, 'target_executed': False, 'runtime_cases': 0,
              'network_used': False, 'user_saves_accessed': False, 'installed_game_modified': False,
              'run_directory': str(run), 'elapsed_seconds': round(time.monotonic() - started, 3), 'limitations': limitations,
              'artifacts': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(run.iterdir()) if p.is_file()}}
    save(run / 'manifest.json', report)
    final = {**report, 'local_manifest_sha256': sha(run / 'manifest.json')}
    save(ROOT / 'reports/2026-11-01-combat0134-chain.json', final)
    md = f'''# Official0.134.0 damage, target layout and new T term

Latest damage914 is type267 `(i32 G,i64 GUID,f32 amount,i32 spell,i32 school,i32 crit,i32 extra)->void`.
The current target record is **424B**, not the historical416B. Full new914/922/968/1063 functions and
{len(guards)} instruction guards are retained; no WASM executes in this extractor.

| Field | New byte offset |
| --- | ---: |
| G phase byte (required1) | 2579 |
| G units pointer/count | 1780 / 1784 |
| G time / shield | 2344 / 1532 |
| G item pointer/count/stride | 2020 / 2024 / 8 |
| G new T pointer/count/stride | 2044 / 2048 / 36 |
| G accounted outgoing damage f64 | 984 |
| G RNG words | 1712 / 1716 / 1720 / 1724 |
| Unit GUID / HP / maxHP / marker | 112 / 288 / 292 / 0 |
| Unit controls | 124 / 380 / 388 |
| Unit extra additive / phase gates / elite byte | 368 / 408,412 / 416 |

T starts at positive zero. Zero spell ID, empty T list or absent target skips the scan.
Records are processed in forward36B order. Raw u32 tags50/51 are the only contributing cases:

| Raw tag | Gate before ID lookup | Contribution |
| --- | --- | --- |
| 50 | `U.f32(356)>entry_now` | record f32+12 |
| 51 | `U.f32(288)<f32.mul(U.f32(292),record.f32(12))` | record f32+16 |

After the gate succeeds, record+4/+8 identify an exact byte string in the current114-entry ability table.
The resolved definition's spell ID+44 must equal the914 spell argument. A mismatch skips the record.
**A missing ID after a successful gate takes the original panic90674/unreachable path before HP writes.**
Unknown tags and failed gates do not resolve IDs. NaN comparisons fail these strict gates; nonfinite
contributions are summed without an early clamp. Every contribution uses ordered `T=f32.add(T,value)`.
The operation is **`f32.mul(f32.mul(amount,f32.add(M,T)),P)`**. It is not an amount-independent bonus.
T scanning precedes the final dead-marker rejection. The JSON gives the exact unsigned selector,
all record fields, lookup constants, panic branch and complete original guards; names are not guessed.

M retains the reviewed item/debuff addition order with the new offsets. P still chooses1.5 for
U412>now, else.25 forU408>now or a live linked kind2 unit. The special kind3/link0 cap remains maxHP/5
with category bitmask3340. After these stages, NaN becomes1 and damage is at least1; HP is stored
without a zero clamp. G984 receives capped accounted damage. HP<=0 writes marker1, duration344=0,
afflicted240=0 and both death4/movement340 times. Position, statistics, packets and further death effects
remain in the full original body; their complete equivalence is not claimed.

For a controlled ordinary fixture, use a zeroed5000B G and424B unit; set the recovered pointers/counts,
phase1, time10, GUID1, HP/maxHP100, unit kind40/kind64/elite244=-1 and unit definition pointer+284=**5411616**.
This is a real new72B static definition selected by complete function968, with name`Kobold Vermin`;
raw bytes/hash are retained. Use zero item/T counts and a nonzero RNG seed. The recipe is static evidence;
the separate full914 harness must establish successful non-death/death returns and side effects.

Player incoming is separately function1063 (type273), with ARM1392, currentHP1528, shield1532,
barrier component1536 and incoming f64 total992. Cast922's spell11426 branch and incoming1063
touch the barrier component; complete914 contains no1536 or11426 references. This trace does not execute
incoming1063 or claim its entire cap behavior. An IceBarrier player path is not an enemy914 cap.

The old `combat.py` remains unchanged and does not implement the new T term/layout. Only selected
arithmetic/projection ideas may be reused after new mapping and new runtime comparison.

Official source SHA256`{SOURCE_SHA}`. Ignored evidence:`{run.relative_to(ROOT)}`.
Manifest SHA256`{final['local_manifest_sha256']}`. Reproduce:
`python3 reverse-engineering/scripts/trace_combat134.py`. Strict JSON, source identities and raw artifact
readback checks pass. No game/module execution, networking, saves, installed-game write, commit or push.
'''
    target = ROOT / 'reports/2026-11-01-combat0134-chain.md'
    target.write_text(md)
    require(target.read_text() == md, 'Markdown readback differs')
    print(json.dumps({'run_directory': str(run), 'version': '0.134.0', 'complete_functions': len(functions),
                      'guards': len(guards), 'unit_stride': 424, 'T_tags': [50, 51], 'target_executed': False}, allow_nan=False))


if __name__ == '__main__':
    main()
