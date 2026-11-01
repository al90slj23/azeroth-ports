#!/usr/bin/env python3
"""Pin/extract new1063 and shield/revival consumers, without executing WASM."""
from datetime import datetime, timezone
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY = ROOT / 'scripts/extract_catalogue134.py'
DEPENDENCY_SHA = '4e465095731c6abc9775ce8445fdd6b96c11982300ec33be1c1b4bda0b8b709a'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


if sha(DEPENDENCY) != DEPENDENCY_SHA:
    raise ValueError('Static reader dependency differs')
from extract_catalogue134 import (parse_binary, reconstruct, require, digest, save,
                                  strict_json, SOURCE, SOURCE_SHA, WAT, WAT_SHA, DB, DB_SHA)

MODEL = ROOT / 'reconstruction/core_spec/incoming134.py'
FLOAT = ROOT / 'reconstruction/core_spec/binary32.py'
FUNCTIONS = (1063, 922, 38322, 58020, 27959, 1453, 1202, 984, 5620)
PINNED = {
    1063: ('e6ea2aaca5f6d402fe5969f637e1b2cad398f2e2b3250b18c4fd0950d3ac59bf',
           'c916ae5af9d5cd3d9e9acb4645cc63816052157377a120bbc5d94a13693a7808'),
    922: ('c20ff5249a260e150399cd272dbc7f1868dd5537c86020484f662cbc8be37182',
          'defb9acf71e59f353359d89fe2eb7a65f30fa7c95fe3f621a4d37abdae09b07a')}

# Reviewed ranges are bound to the pinned complete1063/922 hashes. Every range
# retains exact instructions, complete-file line numbers and a separate hash.
REGIONS = [
    (1063, 'entry phase/protection and fixed0.8 ordered mode scaling', 8, 51),
    (1063, 'active raw buff12 early return', 52, 101),
    (1063, 'ARM1392', 102, 113),
    (1063, 'five live units within squared64; ordered interpolation', 114, 616),
    (1063, 'first eligible raw54 within squared49 and unsigned byte percentage', 617, 781),
    (1063, 'positive shield gate, minNum absorption and barrier decrement', 784, 837),
    (1063, '1344/1348 source consumption and spill', 838, 902),
    (1063, 'reserve768,27959/1453 and reserve clamp', 903, 992),
    (1063, 'shield/source exhaustion, stable buff compaction and1202', 993, 1415),
    (1063, 'residual damage and740/744 accumulation or reset; shield-break984', 1416, 1513),
    (1063, 'source GUID/definition registry before HP write', 1515, 1776),
    (1063, 'last-hit time, actual HP subtraction and uncapped incoming f64 total', 1777, 1793),
    (1063, 'per-source ordered-key f64 statistics tree', 1794, 3110),
    (1063, 'source labels, argument metadata and48B rolling history', 3111, 3628),
    (1063, 'active raw buff13 and raw item22 retaliation through914', 3629, 3991),
    (1063, 'two984 incoming event records before final HP reread', 3992, 4060),
    (1063, '2570 minimum-one including NaN guard', 4061, 4082),
    (1063, 'lethal raw effect12 cast922 and rollback on failure', 4083, 4180),
    (1063, 'successful922 cooldown floor, packets and skip remaining revival chain', 4210, 4418),
    (1063, 'first raw31 lookup, cooldown748 and restore fraction', 4181, 4210),
    (1063, 'raw31 cooldown gate and restore stores', 4437, 4460),
    (1063, 'raw31 nonpositive parameter12 event branch', 4461, 4623),
    (1063, 'raw31 positive parameter12 active raw12 buff1856', 4624, 4778),
    (1063, 'remaining-life1628 or final5620', 4779, 4802),
    (1063, 'life packets and replace spell1020 by raw12 two-second buff', 4803, 5110),
    (1063, 'life-revival radius12 strict collection and200*damage attacks914', 5111, 5617),
    (1063, 'final HP wire22 and maxHP wire28 into2468 field map', 5618, 5888),
    (922, 'barrier candidate arithmetic before replacement', 5311, 5331),
    (922, 'raw7 candidate multiplier and matching spell buff rejects cast', 4396, 4448),
    (922, 'spell11426 barrier/last-source removal, positive remainder', 5332, 5375),
    (922, 'zero base, maxHP capacity and ordered candidate clamp', 5376, 5408),
    (922, 'barrier1536 and total1532 stores', 5409, 5416),
    (922, 'last shield source1344 and remaining1348 write', 5439, 5447),
]


def reaching_definitions(lines, local_index, before_line):
    """Conservative static structured CFG; no instruction is executed.

    Both arms of conditions and all br_table targets are retained. Calls fall
    through because they cannot write the caller's locals. Unique reaching
    definitions thus do not depend on choosing an observed game path.
    """
    lines = [line.strip() for line in lines]
    stack, blocks, active, ends, elses = [], {}, {}, {}, {}
    for n, line in enumerate(lines):
        active[n] = tuple(stack)
        op = line.split(' ')[0].rstrip(')')
        if op in ('block', 'loop', 'if'):
            blocks[n] = op
            stack.append(n)
        elif op == 'else':
            elses[stack[-1]] = n
        elif op == 'end':
            ends[stack.pop()] = n
    require(not stack, 'CFG unclosed structured control')
    edges = {}
    for n, line in enumerate(lines):
        op = line.split(' ')[0].rstrip(')')
        destinations = [n + 1] if n + 1 < len(lines) else []
        if op == 'if':
            destinations = [n + 1, elses.get(n, ends[n]) + 1]
        elif op == 'else':
            destinations = [ends[active[n][-1]] + 1]
        elif op in ('br', 'br_if', 'br_table'):
            depths = ([int(line.split()[1])] if op != 'br_table'
                      else [int(x) for x in re.findall(r'(\d+) \(;@', line)])
            targets = [active[n][-1 - depth] for depth in depths]
            destinations = [target + 1 if blocks[target] == 'loop' else ends[target] + 1
                            for target in targets]
            if op == 'br_if':
                destinations.append(n + 1)
        elif op in ('return', 'unreachable'):
            destinations = []
        edges[n] = destinations
    incoming = defaultdict(set)
    incoming[0] = {0}
    queue, queued = deque([0]), {0}
    pattern = re.compile(r'local\.(?:set|tee) ' + str(local_index))
    while queue:
        n = queue.popleft()
        queued.remove(n)
        output = {n + 1} if pattern.fullmatch(lines[n]) else incoming[n]
        for destination in edges[n]:
            old_length = len(incoming[destination])
            incoming[destination] |= output
            if len(incoming[destination]) != old_length and destination not in queued:
                queue.append(destination)
                queued.add(destination)
    return sorted(incoming[before_line - 1])


def model_checks():
    sys.path.insert(0, str(ROOT / 'reconstruction'))
    from core_spec import incoming134 as m
    from core_spec import binary32 as f
    from dataclasses import replace
    b = f.from_float
    checks = []

    def check(label, condition):
        require(condition, 'Independent model assertion failed: ' + label)
        checks.append(label)

    ordinary = m.IncomingState(hp_1528_bits=b(100), now_bits=b(10))
    check('phase guard unchanged', m.resolve_incoming_prefix(replace(ordinary, phase_2579=4), b(10)).state == replace(ordinary, phase_2579=4))
    check('protection bit0 guard', m.reduce_incoming_bits(replace(ordinary, protection_2568=3), b(10)).reason == 'protection_guard')
    check('non-bit0 does not guard', m.reduce_incoming_bits(replace(ordinary, protection_2568=2), b(10)).reason == 'reduced')
    check('ordinary core HP90 total10', (m.resolve_incoming_prefix(ordinary, b(10)).state.hp_1528_bits, m.resolve_incoming_prefix(ordinary, b(10)).state.incoming_total_992) == (b(90), 10.0))
    check('no minimum-one in prefix', m.resolve_incoming_prefix(ordinary, b(0)).amount_bits == b(0))
    check('negative damage heals scalar HP', m.resolve_incoming_prefix(ordinary, b(-10)).state.hp_1528_bits == b(110))
    check('mode first wave fixed0.8', m.reduce_incoming_bits(replace(ordinary, mode_2574=1), b(10)).amount_bits == b(8))
    check('mode lookup exact matches and unknown default0', [m.classify_38322(x) for x in (b'elwynn', b'duskwood', b'wsg', b'ungoro', b'ab', b'feralas', b'arena', b'sm', b'av', b'brm', b'aq', b'naxx', b'')] == list(range(12)) + [0])
    active = m.BuffRecord(12, expires24_bits=b(11))
    expired = m.BuffRecord(12, expires24_bits=b(10))
    check('strict raw12 expiry', m.reduce_incoming_bits(replace(ordinary, buffs=(active,)), b(10)).reason == 'active_raw_buff12_guard' and m.reduce_incoming_bits(replace(ordinary, buffs=(expired,)), b(10)).reason == 'reduced')
    unit = m.UnitPosition(end_x_bits=b(8))
    nearby = replace(ordinary, nearby_reduction_1444_bits=b(.5))
    check('four near units do not reduce', m.reduce_incoming_bits(replace(nearby, units=(unit,) * 4), b(10)).amount_bits == b(10))
    check('fifth at squared64 reduces', m.reduce_incoming_bits(replace(nearby, units=(unit,) * 5), b(10)).amount_bits == b(5))
    check('dead units excluded', m.reduce_incoming_bits(replace(nearby, units=(unit,) * 4 + (replace(unit, marker=1),)), b(10)).amount_bits == b(10))
    r54 = m.ModifierRecord(54, 1, 50)
    check('raw54 inclusive squared49', m.reduce_incoming_bits(replace(ordinary, units=(m.UnitPosition(end_x_bits=b(7)),), modifiers=(r54,)), b(10)).amount_bits == b(5))
    check('first eligible54 only', m.reduce_incoming_bits(replace(ordinary, units=(m.UnitPosition(),), modifiers=(r54, m.ModifierRecord(54, 1, 90))), b(10)).amount_bits == b(5))
    shielded = replace(ordinary, shield_1532_bits=b(50), barrier_1536_bits=b(30))
    result = m.resolve_incoming_prefix(shielded, b(10))
    check('partial shield consumes barrier by full absorb', (result.state.shield_1532_bits, result.state.barrier_1536_bits, result.state.hp_1528_bits) == (b(40), b(20), b(100)))
    check('negative absorption increases shields', m.resolve_incoming_prefix(shielded, b(-10)).state.shield_1532_bits == b(60))
    check('barrier zero clamp', m.resolve_incoming_prefix(replace(shielded, barrier_1536_bits=b(5)), b(10)).state.barrier_1536_bits == b(0))
    check('shield depletion pending1202', m.resolve_incoming_prefix(shielded, b(60)).stage == 'before1202')
    check('reserve spill pending1453', m.resolve_incoming_prefix(replace(shielded, reserve_768_bits=b(2)), b(10)).stage == 'before27959_and1453')
    check('matched source registry explicitly pending', m.resolve_incoming_prefix(ordinary, b(10), source_guid=1).stage == 'before_source_registry_L1515')
    cast = m.replace_barrier_candidate_bits(b(80), b(30), 11426, b(30), b(100), b(150))
    check('barrier alone capped100; total150 allowed', (cast.barrier_bits, cast.shield_bits) == (b(100), b(150)))
    cast = m.replace_barrier_candidate_bits(b(80), b(30), 17, b(20), b(100), b(90))
    check('replace other source after removing old barrier', (cast.other_shield_bits, cast.barrier_bits, cast.shield_bits) == (b(30), b(90), b(120)))
    check('negative candidate zero', m.replace_barrier_candidate_bits(0, 0, 0, 0, b(100), b(-5)).barrier_bits == 0)
    check('NaN candidate propagates', f.is_nan(m.replace_barrier_candidate_bits(0, 0, 0, 0, b(100), f.NAN).barrier_bits))
    return checks


def main():
    inputs = {SOURCE: SOURCE_SHA, WAT: WAT_SHA, DB: DB_SHA, DEPENDENCY: DEPENDENCY_SHA}
    require(all(sha(path) == expected for path, expected in inputs.items()), 'Pinned input identity differs')
    binary = SOURCE.read_bytes()
    profile = parse_binary(binary)
    require(digest(binary) == SOURCE_SHA, 'Source readback differs')
    require(profile['function_imports'] == 878 and profile['defined_functions'] == 175316, 'Function profile differs')
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('incoming0134-chain-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    con = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    con.execute('PRAGMA query_only=ON')
    functions, texts = [], {}
    try:
        metadata = {k: strict_json(v) for k, v in con.execute('SELECT key,value FROM meta')}
        require(metadata['original_sha256'] == SOURCE_SHA and metadata['wat_sha256'] == WAT_SHA, 'Index provenance differs')
        with WAT.open('rb') as stream:
            for index in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end FROM functions WHERE idx=?', (index,)).fetchone()
                require(row is not None and tuple(row[3:5]) == profile['bodies'][index], 'Function bounds differ')
                stream.seek(row[0])
                wat = stream.read(row[1] - row[0])
                body = binary[row[3]:row[4]]
                require(re.findall(rb'^  \(func \(;(\d+);\)', wat, re.M) == [str(index).encode()], 'Expected one complete function')
                if index in PINNED:
                    require((digest(body), digest(wat)) == PINNED[index], 'Reviewed complete function differs')
                texts[index] = wat.decode().splitlines()
                (run / f'function-{index}.wat').write_bytes(wat)
                (run / f'function-{index}.body.bin').write_bytes(body)
                functions.append({'function_index': index, 'body_start': row[3], 'body_end': row[4],
                                  'body_sha256': digest(body), 'wat_start': row[0], 'wat_end': row[1],
                                  'wat_line': row[2], 'wat_sha256': digest(wat), 'wat_lines': len(texts[index]),
                                  'direct_callees': [x[0] for x in con.execute('SELECT DISTINCT callee FROM calls WHERE caller=? ORDER BY callee', (index,))]})
    finally:
        con.close()
    require(texts[1063][0].strip() == '(func (;1063;) (type 273) (param i32 f32 i64 i32 i32 i32)', '1063 signature differs')
    reaching = {str(index): reaching_definitions(texts[922], index, 5311)
                for index in (25, 26, 27, 28)}
    require(reaching == {'25': [4414], '26': [663], '27': [684], '28': [688]},
            'Barrier candidate/cap reaching definitions differ')
    guards = []
    for index, label, first, last in REGIONS:
        lines = texts[index][first - 1:last]
        require(len(lines) == last - first + 1, 'Reviewed region exceeds function')
        raw = ('\n'.join(lines) + '\n').encode()
        full_line = next(x['wat_line'] for x in functions if x['function_index'] == index)
        guards.append({'function_index': index, 'label': label, 'function_first_line': first,
                       'function_last_line': last, 'complete_first_line': full_line + first - 1,
                       'complete_last_line': full_line + last - 1, 'region_sha256': digest(raw),
                       'instructions': [line.strip() for line in lines]})
    memory = reconstruct(binary, profile)
    strings = []
    for address, length in ((5410764, 8), (5410772, 13), (1587444, 4), (1587448, 10),
                            (1587458, 10), (1587468, 9), (1587477, 9), (1584471, 5),
                            (1590468, 19), (1590487, 16)):
        data = bytes(memory[address:address + length])
        strings.append({'address': address, 'length': length, 'hex': data.hex(),
                        'utf8': data.decode('utf-8', errors='strict')})
    calls = [{'function_line': n + 1, 'callee': int(match.group(1))}
             for n, line in enumerate(texts[1063])
             if (match := re.search(r'\bcall (\d+)', line))]
    require(not any(re.search(r'offset=171[26]|offset=172[04]', x) for x in texts[1063]), 'Unexpected direct RNG state access')
    checks = model_checks()
    result = {'date': '2026-11-01', 'version': '0.134.0', 'build': '983346a7',
              'source_sha256': SOURCE_SHA, 'complete_wat_sha256': WAT_SHA, 'index_sha256': DB_SHA,
              'script_sha256': sha(Path(__file__)), 'reader_sha256': DEPENDENCY_SHA,
              'model_sha256': sha(MODEL), 'binary32_sha256': sha(FLOAT),
              'signature': {'type_index': 273, 'parameters': ['i32 G', 'f32 amount', 'i64 sourceGUID', 'i32 raw3', 'i32 raw4', 'i32 raw5'], 'result': 'void'},
              'complete_functions': functions, 'reviewed_original_regions': guards,
              'barrier_static_CFG_reaching_definitions': {
                  'function': 922, 'before_function_line': 5311,
                  'all_condition_arms_retained': True, 'all_br_table_targets_retained': True,
                  'WASM_executed': False, 'definitions_by_local': reaching,
                  'interpretation': {'25': 'f32.mul(owned.f32(76),definition.f32(4))',
                                     '26': 'G.f32(1360)', '27': 'owned.f32(12)', '28': 'owned.f32(52)'},
                  'candidate_order': 'a=f32.mul(f32.sqrt(f32.mul(owned12,owned52)),1.4); b=f32.mul(G1360,f32.mul(owned76,definition4)); candidate=f32.mul(f32.mul(a,b),f32.add(G1424,1))'},
              'direct_calls_1063': calls, 'direct_rng_access_1063': False,
              'raw_static_strings': strings,
              'scalar_model': {'independent': True, 'dependencies': ['Python standard library', 'core_spec.binary32'],
                               'original_called': False, 'full1063_implemented': False,
                               'assertions_passed': checks, 'runtime_oracle_cases': 0,
                               'NaN_policy': 'NaN category only, no payload/sign equivalence'},
              'controlled_fixture': {
                  'qualification': 'Static recipe only; full original module has not been executed by this trace.',
                  'allocation': 'Use real original allocator for a zeroed5000B G and any extra vectors; never choose raw heap addresses.',
                  'G_writes': {'2579_u8': 1, '2344_f32': 10, '1360_f32': 100, '1528_f32': 100,
                               '1712..1724_u32': [1, 2, 3, 4]},
                  'call': '1063(G,10.0,0n,0,0,0)',
                  'baseline_zero_fields': [2568, 2570, 2574, 1784, 1708, 2048, 2024, 1392, 1444, 1532, 1536, 1344, 1348, 768, 1628],
                  'first_cases': ['nonlethal no shield10/0/-10/NaN/Infinity',
                                  'partial shield total50/barrier30 amount10; source1344=0 and reserve768=0',
                                  'shield exhaustion amount50/60, separately inspect1202 and preHP state',
                                  'source1344=11426, source_remaining1348=5/10/20, partial total50/barrier30',
                                  'five vs four marker0 units at squared64 boundary; tag54 squared49 boundary',
                                  '2570 minimum-one protection with huge amount, NaN and negative amount',
                                  'lethal fixtures only after valid ability pointer1256 is established'],
                  'depletion_buffs': {'capacity': 1700, 'pointer': 1704, 'count': 1708, 'stride': 32, 'tag_u32': 8, 'value12_f32': 12, 'spell_u32': 20, 'expiry24_f32': 24},
                  'conditional_modifiers': {'capacity': 2040, 'pointer': 2044, 'count': 2048, 'stride': 36, 'tag_u32': 0, 'enabled_u8': 4, 'percent_u8': 5},
                  'units': {'pointer': 1780, 'count': 1784, 'stride': 424, 'marker_u32': 0, 'GUID_u64': 112, 'kind244_i32': 244, 'definition_ptr': 256,
                            'start_xyz_f32': [316, 320, 324], 'end_xyz_f32': [328, 332, 336], 'movement_time': 340, 'movement_duration': 344},
                  'observe': ['HP1528', 'shield1532', 'barrier1536', 'source1344/1348', 'reserve768', '740/744', 'total992_f64', 'last_hit1648', 'phase2579', 'lives1628', 'RNG1712..1724', 'buff1700/1704/1708', 'packet1872/1876/1880', 'history968/972/976/980', 'fieldmap2468/2472'],
                  'death_warning': 'G1256 is dereferenced on lethal entry before fallback lives; zero pointer is not a valid no-ability sentinel. Extract/allocate a real valid record first.'},
              'unknowns': [
                  'Full1202 stat/field-map effects and27959/1453 reserve-spill effect must be independently rebuilt before final HP can be claimed on those paths.',
                  'Complete984 event dispatch can invoke914/922 and other consumers; its transitive state/RNG effects remain pending.',
                  'Full source-definition registry and statistics/history containers are retained as original guards, not independently implemented.',
                  'Effect12 ability casting, cooldown, packet/buff details and raw31/lives revival side effects are statically mapped but remain pending in the scalar model.',
                  '922 candidate sqrt/multipliers are statically recovered with conservative CFG reaching-def proof but not implemented in the scalar model; the cast remainder remains pending. Only already-computed barrier replacement is implemented.',
                  'Raw numeric tags and parameters3/4/5 are not assigned guessed gameplay names.',
                  'No direct RNG word access in1063 does not imply RNG stability:914/922/984 and final5620 callees can consume RNG or mutate queues.',
                  'No original WASM function, slice, game start, host import, network, save or APK is executed/modified by this script.'],
              'validation_level': 'static complete-source identities + original regions + independent Python boundary assertions; zero original runtime cases',
              'run_directory': str(run.relative_to(ROOT)), 'target_executed': False}
    save(run / 'manifest.json', result)
    require(all(sha(path) == expected for path, expected in inputs.items()), 'Input identity changed during extraction')
    save(ROOT / 'reports/2026-11-01-incoming0134-chain.json', result)
    print(json.dumps({'run_directory': result['run_directory'], 'manifest_sha256': sha(run / 'manifest.json'),
                      'model_sha256': result['model_sha256'], 'reviewed_regions': len(guards),
                      'python_assertions': len(checks), 'target_executed': False}, indent=2))


if __name__ == '__main__':
    main()
