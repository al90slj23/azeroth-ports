#!/usr/bin/env python3
"""Retain current-core zone/enemy tables and the spawn/death/XP path statically.

No target execution. Names not independently established remain offsets/raw
fields; the companion report states the extent of manual interpretation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import struct

from trace_coop import module_data
from trace_ecs_forward import structural_targets
from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
FUNCTIONS = (38110, 95640, 95641, 5684, 2768, 948, 20145, 933, 1411, 2852, 3231, 85387, 13409)
ZONE_IDS = ('elwynn', 'duskwood', 'wsg', 'ungoro', 'ab', 'feralas', 'arena', 'sm', 'av', 'brm', 'aq', 'naxx')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(source) != ORIGINAL_SHA:
        raise SystemExit('Original current core identity differs')
    binary = source.read_bytes(); ranges = body_ranges(binary)
    segments, _, _ = module_data(binary)
    linear = bytearray(max(s['address'] + s['size'] for s in segments))
    for s in segments:
        linear[s['address']:s['address'] + s['size']] = binary[s['file_start']:s['file_end']]

    def span(address, length):
        stop = address + length
        if address < 0 or length < 0 or stop > len(linear):
            raise ValueError('Static span outside initialized data profile')
        fragments = []
        for s in segments:
            lo, hi = max(address, s['address']), min(stop, s['address'] + s['size'])
            if lo < hi:
                fragments.append({'memory_start': lo, 'bytes': hi - lo,
                                  'file_start': s['file_start'] + lo - s['address']})
        raw = bytes(linear[address:stop])
        return raw, {'memory_start': address, 'bytes': length,
                     'sha256': hashlib.sha256(raw).hexdigest(), 'file_fragments': fragments}

    def text(pointer, length):
        if not 0 <= length <= 512:
            raise ValueError('Unexpected source string length')
        return span(pointer, length)[0].decode('utf-8', errors='strict')

    zones = []
    for index, expected_id in enumerate(ZONE_IDS):
        address = 1708124 + index * 152
        raw, identity = span(address, 152)
        words = struct.unpack('<38I', raw)
        floats = struct.unpack('<38f', raw)
        if text(words[2], words[3]) != expected_id:
            raise ValueError('Zone table/id correspondence differs')
        if words[17] != (16 if index == 11 else 12) or words[19] != 5:
            raise ValueError('Known per-zone definition counts differ')
        normals = []
        for j in range(words[17]):
            data, info = span(words[16] + 72 * j, 72)
            u, f = struct.unpack('<18I', data), struct.unpack('<18f', data)
            normals.append({'index': j, 'source': info, 'name': text(u[4], u[5]),
                            'creature_entry': u[6], 'display_id': u[7],
                            'spawn_scale_f32': f[8], 'classification_u32_raw': u[9],
                            'base_hp_f32': f[10], 'base_attack_f32': f[11],
                            'field48_f32': f[12], 'field52_f32': f[13],
                            'base_xp_pickup_units_u32': u[14],
                            'selection_weight_denominator_f32': f[15],
                            'unlock_minute_f32': (f[16] if math.isfinite(f[16]) else
                                                  '+Infinity' if f[16] > 0 else
                                                  '-Infinity' if f[16] < 0 else 'NaN'),
                            'unlock_minute_bits_hex': f'{u[16]:08x}',
                            'elite_flag_u8': data[68],
                            'behavior_prefix_hex': data[:16].hex(), 'raw72_hex': data.hex()})
        bosses = []
        for j in range(words[19]):
            data, info = span(words[18] + 72 * j, 72)
            u, f = struct.unpack('<18I', data), struct.unpack('<18f', data)
            bosses.append({'index': j, 'source': info, 'name': text(u[0], u[1]),
                           'announcement': text(u[4], u[5]), 'creature_entry': u[8],
                           'display_id': u[9], 'spawn_scale_f32': f[10],
                           'classification_u32_raw': u[11], 'at_minute_f32': f[12],
                           'base_hp_f32': f[13], 'base_attack_f32': f[14],
                           'field60_f32': f[15], 'final_flag_u8': data[68],
                           'auxiliary_ptr_count_u32': [u[2], u[3], u[6], u[7]], 'raw72_hex': data.hex()})
        zones.append({'index': index, 'id': expected_id, 'name': text(words[4], words[5]),
                      'chapter': text(words[6], words[7]), 'source': identity,
                      'base_scaling_f32': floats[34], 'late_hp_scaling_f32': floats[35],
                      'normal_and_elite_definitions': normals, 'boss_schedule': bosses,
                      'remaining_zone_words_u32': list(words)})
    difficulty = []
    for index in range(1, 6):
        raw, identity = span(1568892 + index * 32, 8)
        hp, attack = struct.unpack('<2f', raw)
        difficulty.append({'difficulty_byte': index, 'hp_factor_f32': hp,
                           'attack_factor_f32': attack, 'source': identity,
                           'raw8_hex': raw.hex()})

    with sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Full WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('world-progression-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []; normalized = {}
        with wat.open('rb') as stream:
            for idx in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[idx]:
                    raise ValueError('Original code-body/index bounds differ')
                stream.seek(row[0]); raw = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', raw, re.M) != [str(idx).encode()]:
                    raise ValueError('Expected one complete selected function')
                (run / f'function-{idx}.wat').write_bytes(raw)
                normalized[idx] = [x.strip() for x in raw.decode().splitlines()]
                functions.append({'function_index': idx, 'wat_start': row[0], 'wat_end': row[1],
                                  'wat_line': row[2], 'wat_bytes': len(raw), 'wat_sha256': hashlib.sha256(raw).hexdigest(),
                                  'body_start': row[3], 'body_end': row[4], 'body_bytes': row[5],
                                  'body_sha256': hashlib.sha256(binary[row[3]:row[4]]).hexdigest()})
        guards = []
        def require(idx, pattern, label):
            needle = '\n'.join(pattern); text = '\n'.join(normalized[idx])
            if needle not in text:
                raise ValueError('Reviewed instruction sequence differs: ' + label)
            guards.append({'function_index': idx, 'label': label,
                           'function_line': text[:text.index(needle)].count('\n') + 1,
                           'instructions': pattern})
        require(5684, ['i32.const 50', 'end', 'local.get 5', 'i32.gt_u'], 'normal spawn population cap')
        require(5684, ['local.get 2', 'local.get 13', 'f32.store offset=292',
                       'local.get 2', 'local.get 13', 'f32.store offset=288'], 'spawn HP max/current share exact scaled value')
        require(5684, ['local.get 2', 'local.get 20', 'local.get 17', 'f32.mul',
                       'local.get 14', 'f32.mul', 'f32.store offset=296'], 'spawn attack field')
        require(933, ['local.get 17', 'i32.load offset=56', 'end', 'local.tee 7'], 'death base XP count fallback')
        require(933, ['local.get 0', 'i32.const 0', 'local.get 7', 'local.get 8',
                      'i32.const 208', 'i32.add', 'call 1411'], 'death spawns kind0 pickups')
        require(2852, ['i32.trunc_sat_f32_u', 'call 3231'], 'collected kind0 amount reaches XP apply')
        require(3231, ['local.get 0', 'local.get 0', 'i32.load offset=1340',
                       'local.get 1', 'i32.add', 'local.tee 4', 'i32.store offset=1340'], 'XP addition')
        require(3231, ['local.get 3', 'i32.const 98', 'i32.le_u'], 'level99 ceiling')
        require(3231, ['local.get 0', 'local.get 3', 'i32.const 1', 'i32.add',
                       'local.tee 10', 'i32.store offset=1336', 'local.get 0',
                       'local.get 4', 'local.get 1', 'i32.sub', 'i32.store offset=1340'], 'levelup consumes XP threshold')
        require(3231, ['local.get 0', 'i32.const 0', 'i32.const 1', 'call 2098'], 'levelup may enter card-choice path')
        require(948, ['local.get 0', 'local.get 0', 'f32.load offset=2064',
                      'f32.const 0x1.2cp+8 (;=300;)', 'f32.add', 'f32.store offset=2172'], 'endless boss reschedule300')
        require(948, ['local.get 0', 'local.get 2', 'i32.const 1', 'i32.add',
                      'i32.store offset=2168', 'local.get 0', 'local.get 3',
                      'f32.const 0x1p+0 (;=1;)', 'call 2768'], 'scheduled boss spawn')
        require(948, ['local.get 5', 'i32.const -64', 'i32.sub', 'f32.load',
                      'local.get 6', 'f32.load', 'f32.le', 'br_if 1 (;@8;)'], 'normal candidate unlock-minute eligibility')
        require(948, ['local.get 5', 'i32.const 68', 'i32.add', 'i32.load8_u',
                      'i32.eqz', 'if  ;; label = @9'], 'normal candidate excludes elites')
        require(948, ['local.get 0', 'local.get 0', 'f32.load offset=2128',
                      'local.get 1', 'local.get 22', 'local.get 24', 'f32.mul',
                      'f32.mul', 'f32.add', 'f32.store offset=2128'], 'budget accumulates dt times adjusted spawn rate')
        require(948, ['local.get 0', 'local.get 1', 'local.get 23', 'f32.sub',
                      'local.tee 1', 'f32.store offset=2128'], 'successful spawn debits definition cost')
        require(948, ['local.get 5', 'i32.const 7', 'i32.lt_u',
                      'local.get 5', 'i32.const 1', 'i32.add', 'local.set 5',
                      'br_if 1 (;@5;)'], 'budget loop allows at most eight successes per tick')
        require(2768, ['local.get 3', 'local.get 1', 'i32.store offset=256'], 'boss unit retains boss definition pointer')
        require(5684, ['local.get 2', 'i32.const -1', 'i32.store offset=244'], 'normal unit carries non-boss index sentinel')
        require(20145, ['local.get 2', 'br_if 1 (;@2;)', 'i32.const 0', 'i32.const 0',
                        'i32.const 1570940', 'call 80330', 'unreachable', 'end',
                        'local.get 9', 'local.set 1'], 'nonempty exhausted selection skips candidate pointer reassignment')
        require(5684, ['local.get 3', 'i32.load8_u offset=68', 'local.tee 6', 'select'], 'definition68 selects normal versus elite scalar')
        require(5684, ['local.get 6', 'if (result f32)  ;; label = @3', 'local.get 22',
                       'local.get 23', 'call 95640', 'else', 'local.get 22',
                       'local.get 23', 'call 95641', 'end'], 'definition68 true selects95640 false95641')
        require(5684, ['local.get 3', 'i32.load8_u offset=68', 'local.set 9'], 'definition68 retained in local9 for unit flag')
        require(5684, ['local.get 2', 'local.get 9', 'i32.store8 offset=412'], 'same definition68 flag reaches unit412')
        require(933, ['local.get 14', 'i32.const 172', 'i32.sub', 'i32.load',
                      'i32.const -1', 'i32.eq', 'if  ;; label = @4', 'local.get 14',
                      'i32.const 4', 'i32.sub', 'i32.load8_u', 'i32.const 1',
                      'i32.ne', 'br_if 1 (;@3;)', 'end'], 'tag19 VsElites gate is unit244 nonminus1 or unit412 exactly1')
        target = structural_targets(normalized[2852], {1065: 0xffffffff})[1065]
        if target['target']['end_function_line'] != 1099:
            raise ValueError('Kind0 pickup dispatch branch differs')
        selection_targets = structural_targets(normalized[20145], {378: 1, 403: 1})
        if [selection_targets[n]['target']['end_function_line'] for n in (378, 403)] != [409, 416]:
            raise ValueError('Weighted selection hit/fallback block ends differ')
        result = {'version': '0.126.0', 'build': '3e72472a', 'original_sha256': ORIGINAL_SHA,
                  'complete_wat_sha256': WAT_SHA, 'complete_functions': functions,
                  'catalogue': zones, 'difficulty_enemy_factors': difficulty, 'counts': {'zones': len(zones),
                   'normal_and_elite_definitions': sum(len(z['normal_and_elite_definitions']) for z in zones),
                   'boss_schedule_definitions': sum(len(z['boss_schedule']) for z in zones)},
                  'instruction_guards': guards, 'kind0_pickup_dispatch': target,
                  'weighted_selection_hit_and_fallback': list(selection_targets.values()),
                  'target_executed': False, 'network_used': False,
                  'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
                                    (Path(__file__), ROOT / 'scripts/wasm_index.py',
                                     ROOT / 'scripts/trace_coop.py', ROOT / 'scripts/trace_ecs_forward.py')},
                  'limitations': ['Catalogue values and function bytes are extracted; field roles follow the companion manual report.',
                                  'Normal/elite and boss72-byte record layouts differ and must not be interchanged.',
                                  'Full AI, geometry, every wave style and every reward/loot branch are not recovered here.']}
        (run / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    if sha(source) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise SystemExit('An original changed while extracting')
    print(json.dumps({'run_directory': str(run), **result['counts'], 'complete_functions': len(functions),
                      'instruction_guards_passed': len(guards), 'structural_branches_passed': 3,
                      'target_executed': False, 'network_used': False}))


if __name__ == '__main__':
    main()
