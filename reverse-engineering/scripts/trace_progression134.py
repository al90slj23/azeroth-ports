#!/usr/bin/env python3
"""Retain complete official0.134.0 pickup -> XP -> selection evidence statically.

The original WASM is parsed as bytes only. No module is instantiated, no host
is contacted, and fixture notes below are proposals for later runtime work.
"""
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
MANIFEST_SHA = '952e2cd4c1fdb0bbf62cf44d6cf4f265ae15120a1572facaad23b43ff4fc51b9'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


if sha(DEPENDENCY) != DEPENDENCY_SHA:
    raise ValueError('Pinned static reader dependency differs')
from extract_catalogue134 import (Reader, parse_binary, reconstruct, require, digest,
                                  save, strict_json, SOURCE, SOURCE_SHA, PROFILE,
                                  WAT, WAT_SHA, DB, DB_SHA)

ROLES = {2862: 'collected pickup dispatch', 4630: 'XP add and level-up loop',
         85718: 'f32 round helper', 2159: 'choice generation entry and phase transition',
         1513: 'derived-stat rebuild', 10847: 'heal and downstream accounting',
         1453: 'heal accounting/message side effects', 27959: 'cause descriptor resolver',
         3735: 'keyed state insertion helper', 65323: '16B message-vector reserve helper',
         91940: 'exported allocator wrapper', 106890: 'internal allocation'}


def signatures(binary, indices, import_count):
    top, sections = Reader(binary, 8), {}
    while top.pos < top.end:
        kind, size = top.byte(), top.leb()
        begin = top.pos
        top.raw(size)
        if kind:
            sections[kind] = (begin, top.pos)
    type_reader = Reader(binary, *sections[1])
    types = []
    for _ in range(type_reader.leb()):
        require(type_reader.byte() == 0x60, 'Unsupported WASM type')
        types.append((type_reader.raw(type_reader.leb()), type_reader.raw(type_reader.leb())))
    type_reader.finished()
    declarations = Reader(binary, *sections[3])
    tids = [declarations.leb() for _ in range(declarations.leb())]
    declarations.finished()
    values = {0x7f: 'i32', 0x7e: 'i64', 0x7d: 'f32', 0x7c: 'f64', 0x6f: 'externref'}
    return {idx: {'type_index': tids[idx - import_count],
                  'parameters': [values[x] for x in types[tids[idx - import_count]][0]],
                  'results': [values[x] for x in types[tids[idx - import_count]][1]]}
            for idx in indices}


def resolve_table_arm(lines, number, selector):
    """Resolve one annotated br_table arm against actual nested block ends."""
    frames, result = [], None
    for n, line in enumerate(lines, 1):
        if line.startswith(('block ', 'loop ', 'if ')):
            frames.append({'start_function_line': n, 'header': line})
        elif line in ('end', 'end)') and frames:
            frames.pop()['end_function_line'] = n
        if n == number:
            require(line.startswith('br_table '), 'Reviewed branch is not br_table')
            depths = [int(x) for x in re.findall(r'(\d+) \(;@\d+;\)', line)]
            require(bool(depths), 'Missing annotated branch depths')
            slot = min(selector, len(depths) - 1)
            require(depths[slot] < len(frames), 'Branch targets function frame')
            result = {'branch_function_line': n, 'instruction': line, 'selector_u32': selector,
                      'table_slot': slot, 'depth': depths[slot], 'target': frames[-1-depths[slot]]}
    require(result is not None and 'end_function_line' in result['target'], 'Unmatched branch target')
    return result


def main():
    started = time.monotonic()
    pins = {SOURCE: SOURCE_SHA, WAT: WAT_SHA, DB: DB_SHA, DEPENDENCY: DEPENDENCY_SHA,
            PROFILE / 'manifest.json': MANIFEST_SHA}
    require(all(sha(p) == h for p, h in pins.items()), 'Frozen input identity differs')
    manifest = strict_json((PROFILE / 'manifest.json').read_text())
    require(manifest['target_version'] == '0.134.0' and manifest['embedded_build'] == '983346a7'
            and manifest['original_sha256'] == SOURCE_SHA, 'Wrong source version/build')
    binary = SOURCE.read_bytes()
    require(digest(binary) == SOURCE_SHA, 'Source readback differs')
    binary_profile = parse_binary(binary)
    require(binary_profile['function_imports'] == 878 and binary_profile['defined_functions'] == 175316,
            'New module function counts differ')
    sigs = signatures(binary, ROLES, binary_profile['function_imports'])
    require(sigs[4630] == {'type_index': 0, 'parameters': ['i32', 'i32'], 'results': []}, 'XP signature differs')
    require(sigs[2159] == {'type_index': 1, 'parameters': ['i32', 'i32', 'i32'], 'results': []}, 'Choice signature differs')
    require(sigs[85718] == {'type_index': 55, 'parameters': ['f32'], 'results': ['f32']}, 'Round signature differs')
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('progression0134-chain-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    connection = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    functions, lines, bodies = {}, {}, {}
    guards, edges = [], []
    try:
        meta = {k: strict_json(v) for k, v in connection.execute('SELECT key,value FROM meta')}
        require(meta['original_sha256'] == SOURCE_SHA and meta['wat_sha256'] == WAT_SHA
                and meta['terminal_parentheses_supported'] is True, 'Read-only database provenance differs')
        with WAT.open('rb') as stream:
            for index, role in ROLES.items():
                row = connection.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?', (index,)).fetchone()
                require(row is not None and tuple(row[3:5]) == binary_profile['bodies'][index]
                        and row[5] == row[4] - row[3], 'Binary/index function boundaries differ')
                stream.seek(row[0]); wat = stream.read(row[1] - row[0])
                require(re.findall(rb'^  \(func \(;(\d+);\)', wat, re.M) == [str(index).encode()], 'Not one complete function')
                body = binary[row[3]:row[4]]
                (out / f'function-{index}.wat').write_bytes(wat)
                (out / f'function-{index}.body.bin').write_bytes(body)
                lines[index] = [x.strip() for x in wat.decode().splitlines()]
                bodies[index] = body
                functions[index] = {'function_index': index, 'descriptive_role': role, **sigs[index],
                    'signature_wat': wat.splitlines()[0].decode(), 'wat_start': row[0], 'wat_end': row[1],
                    'wat_line': row[2], 'wat_bytes': len(wat), 'wat_sha256': digest(wat),
                    'body_start': row[3], 'body_end': row[4], 'body_bytes': row[5], 'body_sha256': digest(body),
                    'direct_callers': [x[0] for x in connection.execute('SELECT DISTINCT caller FROM calls WHERE callee=? ORDER BY caller', (index,))]}

        def guard(index, label, text):
            sequence = text.split('|')
            positions = [n for n in range(len(lines[index]) - len(sequence) + 1)
                         if lines[index][n:n + len(sequence)] == sequence]
            require(bool(positions), 'Reviewed new-source guard differs: ' + label)
            guards.append({'function_index': index, 'label': label, 'function_lines': [n+1 for n in positions],
                           'full_wat_lines': [functions[index]['wat_line']+n for n in positions],
                           'instructions': sequence})

        guard(2862, '56B pickup vector and count', 'local.get 0|i32.load offset=1868|local.tee 1|i32.eqz|br_if 0 (;@1;)|local.get 1|i32.const 56|i32.mul|local.set 9|local.get 0|i32.load offset=1864|local.set 1')
        guard(2862, 'selected56B pickup reads actual kind8', 'local.get 0|i32.load offset=1864|local.get 1|i32.const 56|i32.mul|i32.add|local.tee 4|i32.load offset=8|local.tee 3')
        guard(2862, 'selected pickup kind8 and amount12 before removal', 'local.get 4|i32.load offset=12|local.set 4|local.get 0|local.get 1|call 31731|local.get 3|i32.const 1|i32.sub|br_table 3 (;@15;) 1 (;@17;) 4 (;@14;) 4 (;@14;) 4 (;@14;) 5 (;@13;) 2 (;@16;)')
        guard(2862, 'kind0 branch starts multiplier1 and mode guard', 'end|f32.const 0x1p+0 (;=1;)|local.set 22|local.get 0|i32.load8_u offset=2574|i32.eqz|br_if 10 (;@5;)')
        guard(2862, 'ordered pickup XP round NaN and minimum1 before4630', 'local.get 0|f32.const 0x1p+0 (;=1;)|local.get 22|local.get 0|f32.load offset=1388|local.get 4|f32.convert_i32_u|f32.mul|f32.mul|call 85718|local.tee 22|local.get 22|local.get 22|f32.ne|select|local.tee 22|f32.const 0x1p+0 (;=1;)|local.get 22|f32.const 0x1p+0 (;=1;)|f32.gt|select|i32.trunc_sat_f32_u|call 4630')
        guard(4630, 'wrapping XP addition1524 before every phase check', 'local.get 0|local.get 0|i32.load offset=1524|local.get 1|i32.add|local.tee 4|i32.store offset=1524')
        guard(4630, 'exact threshold f32 evaluation order', 'local.get 0|i32.load offset=1520|local.tee 1|local.get 1|i32.const 0|i32.ne|i32.sub|f32.convert_i32_u|local.tee 14|f32.const 0x1p+2 (;=4;)|f32.mul|f32.const 0x1.4p+2 (;=5;)|f32.add|local.get 14|f32.const 0x1.666666p-2 (;=0.35;)|f32.mul|local.get 14|f32.mul|f32.add|call 85718')
        guard(4630, 'new119 current-level ceiling and unsigned XP comparison', 'local.get 1|i32.const 119|i32.le_u|if  ;; label = @5|local.get 4|local.get 14|i32.trunc_sat_f32_u|local.tee 3|i32.ge_u|br_if 1 (;@4;)')
        guard(4630, 'level XP and default pending writes', 'local.get 0|local.get 1|i32.const 1|i32.add|local.tee 6|i32.store offset=1520|local.get 0|local.get 4|local.get 3|i32.sub|i32.store offset=1524|local.get 0|local.get 0|i32.load offset=2368|i32.const 1|i32.add|i32.store offset=2368')
        guard(4630, 'key34 level state insertion', 'local.get 2|i32.const 34|i32.store offset=56')
        guard(4630, 'key716 XP state insertion', 'local.get 2|i32.const 716|i32.store offset=56')
        guard(4630, 'key717 threshold state insertion', 'local.get 2|i32.const 717|i32.store offset=56')
        guard(4630, 'snapshot stats and original1513 rebuild each level', 'local.get 0|i32.load offset=1428|local.set 5|local.get 0|f32.load offset=1396|local.set 14|local.get 0|f32.load offset=1360|local.set 15|local.get 0|f32.load offset=1364|local.set 16|local.get 0|call 1513')
        guard(4630, 'message reserve then append16B', 'local.get 0|i32.load offset=1880|local.tee 1|local.get 0|i32.load offset=1872|i32.eq|if  ;; label = @4|local.get 10|call 65323|end|local.get 0|i32.load offset=1876|local.get 1|i32.const 4|i32.shl|i32.add')
        guard(4630, 'level_up cause descriptor and resolver', 'local.get 2|i32.const 0|i32.store offset=120|local.get 2|i32.const 1588144|i32.store offset=124|local.get 2|i32.const 40|i32.add|local.get 0|local.get 2|i32.const 120|i32.add|local.tee 1|call 27959')
        guard(4630, 'heal20percent post-rebuild max HP and reload XP loop', 'local.get 0|local.get 14|f32.const 0x1.99999ap-3 (;=0.2;)|f32.mul|local.get 3|local.get 2|i32.const 136|i32.add|local.get 1|call 10847|local.get 0|i32.load offset=1524|local.set 4|br 1 (;@2;)')
        guard(4630, 'complete choice-entry guard and actual2159 arguments', 'block  ;; label = @1|local.get 0|i32.load offset=2368|i32.eqz|br_if 0 (;@1;)|local.get 0|i32.load8_u offset=2579|i32.const 1|i32.ne|br_if 0 (;@1;)|local.get 0|i32.load8_u offset=2568|i32.const 1|i32.and|br_if 0 (;@1;)|local.get 0|i32.load8_u offset=2564|i32.const 1|i32.eq|if  ;; label = @2|local.get 0|i32.load8_u offset=2565|i32.const 1|i32.and|i32.eqz|br_if 1 (;@1;)|end|local.get 0|i32.const 0|i32.const 1|call 2159')
        guard(2159, 'selection kind low byte dispatch', 'local.get 1|i32.const 255|i32.and|i32.const 1|i32.sub|br_table 1 (;@9;) 2 (;@8;) 0 (;@10;)')
        guard(2159, 'kind and generation count then optional phase2', 'local.get 0|local.get 1|i32.store8 offset=2577|local.get 0|local.get 0|i32.load offset=2392|i32.const 1|i32.add|i32.store offset=2392|local.get 2|i32.eqz|br_if 1 (;@1;)|local.get 0|i32.const 2|i32.store8 offset=2579')
        guard(1513, 'character selectors360 and361', 'local.get 0|i32.load8_u offset=360|i32.const 2|i32.sub|i32.const 255|i32.and')
        guard(1513, 'race selector361', 'local.get 0|i32.load8_u offset=361|i32.const 2|i32.sub')
        guard(1513, 'new level enters stat rebuild', 'local.get 0|i32.load offset=1520|f32.convert_i32_u|f32.const -0x1p+0 (;=-1;)|f32.add')
        guard(1513, 'rebuilt maxHP field1360', 'local.get 0|local.get 49|local.get 41|f32.const 0x1.2p+3 (;=9;)|f32.mul|f32.add|local.tee 28|local.get 42|f32.add|local.get 26|f32.mul|local.tee 21|f32.store offset=1360')
        guard(1513, 'player GUID1336 in derived message', 'local.get 5|i32.const 12|i32.add|local.get 0|i64.load offset=1336|local.get 3|local.get 23|call 48065')
        guard(10847, 'heal consumes player maxHP1360 and currentHP1528', 'local.get 0|local.get 0|f32.load offset=1360|local.tee 5|local.get 0|f32.load offset=1528|local.tee 7|local.get 1')
        guard(10847, 'heal writes currentHP then calls1453 with actual delta', 'f32.store offset=1528|local.get 0|local.get 1|local.get 7|f32.sub|local.tee 1|local.get 2|local.get 3|local.get 4|call 1453')
        guard(1453, 'positive heal gate then player GUID1336', 'local.get 1|f32.const 0x0p+0 (;=0;)|f32.le|i32.eqz|if  ;; label = @25|local.get 3|i32.load|local.set 18|local.get 5|local.get 0|i64.load offset=1336')
        guard(91940, 'exported allocator wraps actual internal allocation', 'local.get 0|local.get 1|call 106890')
        for caller, callee in ((2862,4630),(2862,85718),(4630,85718),(4630,1513),(4630,27959),
                               (4630,10847),(10847,1453),(4630,3735),(4630,65323),(4630,2159),(91940,106890)):
            sites = [{'wat_offset': a, 'wat_line': b, 'instruction': k} for a,b,k in connection.execute(
                'SELECT wat_offset,wat_line,instruction FROM calls WHERE caller=? AND callee=? ORDER BY wat_line', (caller,callee))]
            require(bool(sites), 'Missing reviewed actual call edge')
            edges.append({'caller': caller, 'callee': callee, 'sites': sites})
    finally:
        connection.close()
    require(digest(bodies[85718]) == '3f9127d30eefb0c9bad49101460ed45df1f6069e63c42d87e351ffbb67151c36',
            'New round body no longer matches reviewed68B historical helper')
    pickup_branch = resolve_table_arm(lines[2862], 1065, 0xffffffff)
    require(pickup_branch['target']['end_function_line'] == 1099, 'Kind0 no longer enters reviewed XP block')
    memory = reconstruct(binary, binary_profile)
    cause_address, cause_size = 1588144, 44
    cause = bytes(memory[cause_address:cause_address+cause_size])
    expected = ('level_up', 'system', 'known', 'Level Up', 'Spell_Holy_HolyBolt')
    cause_strings = []
    for n, expected_text in enumerate(expected):
        pointer, length = struct.unpack_from('<II', cause, n*8)
        raw = bytes(memory[pointer:pointer+length])
        require(raw.decode() == expected_text, 'Static level-up cause descriptor differs')
        cause_strings.append({'descriptor_offset': n*8, 'pointer': pointer, 'length': length, 'text': expected_text})
    (out / 'level-up-cause-1588144.bin').write_bytes(cause)
    input_identity = {'source_sha256': SOURCE_SHA, 'profile_manifest_sha256': MANIFEST_SHA,
        'wat_sha256': WAT_SHA, 'database_sha256': DB_SHA, 'static_reader_sha256': DEPENDENCY_SHA,
        'trace_tool_sha256': sha(Path(__file__))}
    fields = {'character_selector_u8':360,'race_selector_u8':361,'heal_modifier_gate_u8':387,
        'player_guid_u64':1336,'max_hp_f32':1360,'damage_f32':1364,'xp_multiplier_f32':1388,
        'regen_f32':1396,'stat1428_u32':1428,'player_x_f32':1504,'player_y_f32':1508,
        'level_u32':1520,'xp_u32':1524,'current_hp_f32':1528,
        'owned_capacity':1652,'owned_pointer':1656,'owned_count':1660,
        'pickup_pointer':1864,'pickup_count':1868,'pickup_stride_bytes':56,
        'message_capacity':1872,'message_pointer':1876,'message_count':1880,'message_stride_bytes':16,
        'candidate_capacity':1896,'candidate_pointer':1900,'candidate_count':1904,
        'item_pointer':2020,'item_count':2024,'modifier_pointer':2044,'modifier_count':2048,
        'now_f32':2344,'pending_default_u32':2368,'pending_kind1_u32':2372,'pending_kind2_u32':2376,
        'choice_generation_counter_u32':2392,'keyed_state_tree_root':2468,'keyed_state_tree_depth':2472,
        'choice_gate_mode_u8':2564,'choice_gate_flag_u8':2565,'choice_inhibit_bit0_u8':2568,
        'mode_u8':2574,'selection_kind_u8':2577,'phase_u8':2579}
    require(all(sha(p) == h for p,h in pins.items()), 'Pinned input changed during trace')
    result = {'target_version':'0.134.0','build':'983346a7','status':'static trace complete',
        'input_identity':input_identity,'evidence_directory':str(out),'database_read_only':True,
        'complete_functions':list(functions.values()),'direct_edges':edges,'instruction_guards':guards,
        'pickup_kind0_branch':pickup_branch,'state_offsets_0134':fields,
        'pickup_record_fields':{'kind_u32':8,'base_amount_u32':12,'stride_bytes':56},
        'xp_semantics':{'arguments':['G state pointer','amount u32 bit pattern'],
            'entry_phase_guard':False,'add':'XP=wrap_u32(XP+amount)',
            'threshold':'n=f32.u32(level-(level!=0)); trunc_sat_u32(round85718((n*4+5)+(n*f32(0.35))*n))',
            'loop':'while level<=u119 and XP>=u threshold: level+=1; XP-=threshold; pending2368=wrap_u32(pending2368+1); execute original side effects; reload XP',
            'natural_level_ceiling':120,'input_level_above_ceiling':'retained; no clamping',
            'zero_amount':'still consumes sufficient held XP',
            'choice_guard':'pending2368!=0 && phase2579==1 && !(byte2568&1) && (byte2564!=1 || (byte2565&1))',
            'choice_call':{'function':2159,'arguments':['G',0,1]},
            'per_level_keyed_state_writes':[34],'post_loop_keyed_state_writes':[716,717],
            'round_body_matches_old85387':True},
        'choice_parameters':{'function':2159,'arguments':['G state pointer','selection kind low8 bits','nonzero enables phase2 transition'],
            'qualification':'Full candidate-generation function retained statically; actual candidate construction never executed.'},
        'level_up_cause':{'address':cause_address,'bytes':cause_size,'sha256':digest(cause),'strings':cause_strings},
        'historical_role_correspondence_only':{'3231':4630,'2098':2159,'2852':2862,'1573':1513,'85387':85718},
        'fixture_proposal':{'status':'not executed or accepted', 'entry_function':4630,'phase':3,
            'entry_parameters':['G', 'u32 XP amount'],
            'reusable_approach':'Original allocator plus synthetic zeroed auxiliary state, explicit current fields, no application start, host imports fail closed.',
            'proposed_allocation_bytes':8192,'character_and_race_bytes':[360,361],'proposed_selectors':[1,1],
            'proposed_player_guid':{'offset':1336,'type':'u64','value':1},
            'compared_fields':['u32 G+1520 level','u32 G+1524 XP','u32 G+2368 pending','u8 G+2579 phase'],
            'auxiliary_containers_to_initialize':['owned1652/1656/1660','message1872/1876/1880','items2020/2024','modifiers2044/2048','keyed tree2468/2472'],
            'real_guard_skipped_function':2159,
            'still_reached_on_levelup':[1513,27959,10847,1453,3735],
            'must_change_from_old_fixture':['old3231 entry ->4630','old allocator106495 ->new exported91940 or its verified internal106890','old level1336/XP1340/pending2088 ->1520/1524/2368','old phase2299 ->2579','old playerGUID1152 ->1336','old99 ceiling ->120; extend cap/boundary corpus'],
            'acceptance_needed':'A later controlled full-original fixture must measure imports, memory cap, reached functions and output readback; static analysis is not runtime acceptance.'},
        'target_executed':False,'runtime_oracle_cases':0,'network_used':False,'app_or_save_writes':False,
        'elapsed_seconds':round(time.monotonic()-started,3),
        'limitations':['No original0.134 function or runtime fixture was executed.',
            'No candidate generation, random candidate content, UI flow, save state, or APK behavior was accepted.',
            'Character/race selectors, player GUID and container offsets are established from new instructions; zeroed-state fixture suitability remains untested.',
            'Intermediate message/heal/stat/keyed-state effects are retained as original code, not independently reconstructed.',
            'Historical role correspondence does not establish whole-function equivalence; old model caps at99 and must be revised for120.',
            'Pickup mode-dependent multiplier and collection geometry remain original branches; only their static route and final XP rounding are traced here.']}
    save(out/'guards.json',guards)
    save(out/'manifest.json',result)
    save(ROOT/'reports/2026-11-01-progression0134-chain.json',result)
    rows = '\n'.join(f"| {i} | `{f['signature_wat'].strip()}` | {f['body_bytes']} | `{f['body_sha256']}` |" for i,f in functions.items())
    md = f'''# 官方0.134.0：拾取XP、等级/pending与选卡入口

本报告固定 **0.134.0 / 983346a7**，原件SHA-256 `{SOURCE_SHA}`。使用新版完整WAT/SQLite，数据库只读；全程仅解析字节，没有实例化WASM、调用游戏入口、联网、读取存档或修改APK。完整函数WAT/body与连续指令guard保存在 `{out.relative_to(ROOT)}`。运行时样例数为 **0**。

## 已恢复的真实链

`2862(G) → 4630(G, amount) → 每级1513(G) → 27959解析level_up原因 → 10847治疗 → 1453副作用 → 末尾真实守卫 → 2159(G,0,1)`。

历史3231职责由新版**4630**承担；历史2098职责由新版**2159**承担。这是新原件调用、字段和连续指令所建立的角色对应，不是编号算术平移，也不声称整函数等价。新版round **85718(f32)→f32** 的68B body哈希与历史85387相同。

2862按G+1864/1868遍历56B拾取记录，从record+8读kind、+12读amount，先保存amount再调用31731移除拾取。`kind-1`的无符号br_table默认臂使kind0进入函数行1099之后的XP分支，脚本实际解析嵌套block终点核对。普通mode0令局部倍数为1；随后按原顺序计算 `round85718((G.f32(1388)*f32.u32(base_amount))*modeMultiplier)`，NaN选择1、再取至少1、最后trunc_sat_u32，传入4630。mode的多人调整和完整拾取几何没有做独立数值规格。

4630签名是 `(param i32 i32)`，参数0为G，参数1为XP增量的u32位解释，返回void。**入口没有phase限制**，先写 `G.u32(1524)=wrap_u32(oldXP+amount)`。循环读取 `G.u32(1520)`，阈值保持每步f32原顺序：

```text
n = u32_to_f32(level - (level != 0))
threshold = trunc_sat_u32(R85718((n*4+5)+(n*f32(0.35))*n))
while level <=u 119 and XP >=u threshold:
    level = wrap_u32(level+1)
    XP = wrap_u32(XP-threshold)
    pending2368 = wrap_u32(pending2368+1)
    原属性重算、keyed state、消息和治疗等副作用
    重新读取XP
```

**新版自然升级上限为120，旧版是99。** 已大于上限的输入不会夹回120；amount0仍可消费已有XP，XP和pending加法仍绕回。旧模型的阈值公式与helper算法可以作为迁移起点，但`level<=98`、99级边界和旧运行时数字不能作为新版验收。

每级先写level1520、XP1524、pending2368，再更新key34并调用1513。重算前快照maxHP1360、damage1364、regen1396和计数1428，随后生成16B消息到G+1872/1876/1880。之后从静态descriptor1588144解析 `level_up / system / known / Level Up / Spell_Holy_HolyBolt`，以重算后maxHP的20%请求10847治疗；10847更新currentHP1528，再以实际治疗差值调用1453。循环外仍更新key716(XP)和717(新阈值)。这些副作用仅追踪并保留原body，未独立重建。

末尾调用2159的完整守卫：

```text
pending2368 != 0
&& phase2579 == 1
&& !(byte2568 & 1)
&& (byte2564 != 1 || (byte2565 & 1))
→ 2159(G, 0, 1)
```

2564要求精确等于1；2568/2565只看bit0，非规范字节2不能统一当true。2159参数1按低8位分发选择种类，参数2非零时在生成后的路径写phase2579=2；同时写selection_kind2577与增加counter2392。本报告保存2159完整body和守卫，**没有实际生成候选，也没有验收候选内容**。

## 阶段3受控fixture的静态迁移边界

可复用原分配器分配合成G、清空辅助容器、禁止host imports、直接调用XP核心的方式。新版应从已验证导出91940分配，或采用后续harness允许的internal106890；建议沿用现有新版fixture的8192B分配额度。class/race读取仍在byte360/361；player GUID已是u64 **G+1336**；level/XP/pending改为1520/1524/2368，phase改为byte2579。消息Vec是1872/1876/1880，owned是1652/1656/1660，items是2020/2024，modifiers是2044/2048，keyed-state树是2468/2472。

把phase2579设为3，只会通过4630末尾真实守卫阻断2159；XP循环、1513、消息、keyed state、10847/1453仍然执行。后续比较字段可以限定为level1520、XP1524、pending2368和phase2579，但这不能声称覆盖其他副作用。需要把120级停止、119级阈值前/等于/后、120级及更高输入、加法/pending绕回、多级升级、零增量纳入新版语料。selectors=1/1、GUID=1及空辅助状态只是待运行提案，本轮未验证可执行性或host调用数。

## 完整提取函数及身份

| 函数 | 新版WAT签名 | body字节 | body SHA-256 |
| ---: | --- | ---: | --- |
{rows}

原件SHA-256 `{SOURCE_SHA}`；profile manifest `{MANIFEST_SHA}`；完整WAT `{WAT_SHA}`；SQLite `{DB_SHA}`。JSON还包含每个函数的二进制与WAT起止偏移、完整WAT行号、所有guard命中位置和直接调用位置。

复现：`python3 reverse-engineering/scripts/trace_progression134.py`。该命令只做静态解析与忽略目录证据写入，不运行原WASM。输出的JSON和本报告仅说明静态恢复范围；实际候选生成、UI、存档、APK和新版full original fixture均未验收。
'''
    (ROOT/'reports/2026-11-01-progression0134-chain.md').write_text(md)
    print(json.dumps({'evidence_directory':str(out),'complete_functions':len(functions),
                      'guards':len(guards),'xp_function':4630,'natural_level_ceiling':120,
                      'target_executed':False,'runtime_oracle_cases':0}))


if __name__ == '__main__':
    main()
