#!/usr/bin/env python3
"""Trace official 0.134.0 selection/owned-ability consumers without execution.

Every function is extracted from the frozen 0.134 profile, checked against the
official binary and retained completely. Historical indices are role labels,
not arithmetic index translations or claims of whole-function equivalence.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import time

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'evidence/wasm0134-profile-20261101T001728.222975Z'
SOURCE = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/latest-wenilla_bg.wasm'
SOURCE_SHA = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
PROFILE_TOOL_SHA = 'ecbdc939fe1cad8b240a6d5f6645a96b54fe69b87b69ee54ab39290d14969cf9'
ROLES = {1073: 'selection accept/apply', 25368: 'upgrade numeric helper',
         1513: 'derived-stat rebuild', 4600: 'selection completion',
         22287: 'owned effective record resolver', 916: 'active ability tick',
         922: 'ability cast executor', 914: 'damage/HP/death path',
         2159: 'next-choice generation entry', 26967: 'record modifier helper',
         26591: 'new-record tier adjustment', 91940: '__wbindgen_malloc wrapper',
         106890: 'internal allocation', 135228: '__wbindgen_free wrapper',
         71888: 'internal deallocation', 95051: '__wbindgen_realloc wrapper'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def module_exports(data):
    def uint(p):
        value = shift = 0
        while p < len(data) and shift <= 28:
            byte = data[p]; p += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, p
            shift += 7
        raise ValueError('Invalid u32 LEB')
    def name(p):
        size, p = uint(p)
        return data[p:p + size].decode(), p + size
    require(data[:8] == b'\0asm\1\0\0\0', 'Wrong WASM header')
    sections = {}; p = 8
    while p < len(data):
        kind = data[p]; size, begin = uint(p + 1)
        require(begin + size <= len(data), 'Invalid WASM section boundary')
        if kind:
            require(kind not in sections, 'Duplicate non-custom section')
            sections[kind] = (begin, begin + size)
        p = begin + size
    types = []; count, p = uint(sections[1][0])
    for _ in range(count):
        require(data[p] == 0x60, 'Unsupported type form'); p += 1
        n, p = uint(p); params = data[p:p + n]; p += n
        n, p = uint(p); results = data[p:p + n]; p += n
        types.append((params, results))
    require(p == sections[1][1], 'Type boundary differs')
    count, p = uint(sections[2][0]); imports = []
    for _ in range(count):
        _, p = name(p); _, p = name(p)
        require(data[p] == 0, 'Profile expects only function imports')
        tid, p = uint(p + 1); imports.append(tid)
    require(p == sections[2][1] and len(imports) == 878, 'Import boundary/count differs')
    count, p = uint(sections[3][0]); declarations = []
    for _ in range(count):
        tid, p = uint(p); declarations.append(tid)
    require(p == sections[3][1] and len(declarations) == 175316, 'Function boundary/count differs')
    count, p = uint(sections[7][0]); exports = []
    values = {0x7f: 'i32', 0x7e: 'i64', 0x7d: 'f32', 0x7c: 'f64', 0x6f: 'externref'}
    for _ in range(count):
        label, p = name(p); kind = data[p]; idx, p = uint(p + 1)
        item = {'name': label, 'kind': kind, 'index': idx}
        if kind == 0:
            tid = imports[idx] if idx < len(imports) else declarations[idx - len(imports)]
            params, results = types[tid]
            item.update({'type_index': tid, 'parameters': [values.get(v, hex(v)) for v in params],
                         'results': [values.get(v, hex(v)) for v in results]})
        exports.append(item)
    require(p == sections[7][1], 'Export boundary differs')
    return exports, 8 in sections


def main():
    started = time.monotonic(); deadline = started + 120
    require(sha(SOURCE) == SOURCE_SHA and SOURCE.stat().st_size == 90953762, 'Official source identity differs')
    require(sha(ROOT / 'scripts/wasm134_profile.py') == PROFILE_TOOL_SHA, 'Frozen profile tool changed')
    manifest = json.loads((PROFILE / 'manifest.json').read_text())
    require(manifest['target_version'] == '0.134.0' and manifest['original_sha256'] == SOURCE_SHA, 'Wrong profile')
    wat = Path(manifest['wat_path']); database = Path(manifest['database_path'])
    require(sha(wat) == manifest['wat_sha256'] and sha(database) == manifest['database_sha256'], 'Profile artifact differs')
    binary = SOURCE.read_bytes(); exports, has_start = module_exports(binary)
    malloc = next(x for x in exports if x['name'] == '__wbindgen_malloc')
    require(malloc == {'name': '__wbindgen_malloc', 'kind': 0, 'index': 91940, 'type_index': 6,
                       'parameters': ['i32', 'i32'], 'results': ['i32']}, 'New allocator export differs')
    con = sqlite3.connect('file:' + str(database) + '?mode=ro', uri=True)
    meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
    require(meta['target_version'] == '0.134.0' and meta['original_sha256'] == SOURCE_SHA, 'Database target differs')
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('selection0134-chain-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    functions = {}; texts = {}; lines = {}
    with wat.open('rb') as stream:
        for idx, role in ROLES.items():
            require(time.monotonic() < deadline, 'Owned trace deadline exceeded')
            row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?', (idx,)).fetchone()
            a, b, line, ba, bb, count = row
            stream.seek(a); text = stream.read(b - a)
            require(text.startswith(f'  (func (;{idx};)'.encode()) and bb - ba == count, 'Complete function range differs')
            (out / f'function-{idx}.wat').write_bytes(text)
            body = binary[ba:bb]
            (out / f'function-{idx}.body.bin').write_bytes(body)
            functions[idx] = {'function_idx': idx, 'descriptive_role': role,
                              'signature_wat': text.splitlines()[0].decode(),
                              'wat_start': a, 'wat_end': b, 'wat_start_line': line,
                              'wat_bytes': len(text), 'wat_sha256': hashlib.sha256(text).hexdigest(),
                              'body_start': ba, 'body_end': bb, 'body_bytes': count,
                              'body_sha256': hashlib.sha256(body).hexdigest()}
            texts[idx] = text.decode(); lines[idx] = texts[idx].splitlines()
    guards = []
    def evidence(idx, label, sequence=None, anchor=None, before=5, after=12):
        normalized = [x.strip() for x in lines[idx]]
        if sequence:
            matches = [n for n in range(len(normalized) - len(sequence) + 1)
                       if normalized[n:n + len(sequence)] == sequence]
        else:
            matches = [n for n, text in enumerate(normalized) if anchor in text]
        require(bool(matches), f'Missing new-source guard: {idx} {label}')
        n = matches[0]; start = max(0, n - before); end = min(len(normalized), n + (len(sequence) if sequence else 1) + after)
        guards.append({'function_idx': idx, 'label': label, 'matching_sites': len(matches),
                       'function_line_start': start + 1, 'function_line_end': end,
                       'full_wat_line_start': functions[idx]['wat_start_line'] + start,
                       'instructions': lines[idx][start:end]})
    evidence(1073, 'phase guard', ['local.get 0', 'i32.load8_u offset=2579', 'i32.const 2', 'i32.ne', 'br_if 0 (;@2;)'])
    evidence(1073, 'candidate index and selection-kind guards', anchor='i32.load offset=1904', before=2, after=12)
    evidence(1073, 'candidate80B and niche selector', anchor='i32.load offset=1900', after=21)
    evidence(1073, 'existing candidate kind-vector/index', anchor='i32.load offset=72', before=10, after=22)
    evidence(1073, 'candidate tier76', anchor='i32.load offset=76', before=3, after=6)
    evidence(1073, 'definition lookup stride88 span10032', anchor='i32.const 10032', before=30, after=7)
    evidence(1073, 'new record initialization', anchor='i32.store offset=248', before=3, after=45)
    evidence(1073, 'new owned append cap/ptr/count and80B', anchor='i32.load offset=1652', before=4, after=29)
    evidence(1073, 'existing owned-index bound', ['local.get 0', 'i32.load offset=1660', 'local.get 9', 'i32.le_u'], after=16)
    evidence(1073, 'per-kind apply and counter/shared growth', anchor='call 25368', before=23, after=112)
    evidence(1073, 'shared postprocessing then rebuild/completion', ['local.get 0', 'call 1513', 'local.get 0', 'local.get 21', 'call 4600'], before=12, after=4)
    evidence(1513, 'new stat output1360', anchor='f32.store offset=1360', before=18, after=24)
    evidence(1513, 'current HP output1528', anchor='f32.store offset=1528', before=15, after=8)
    evidence(4600, 'entry queue decrement2368/2372/2376', anchor='i32.load offset=2368', before=12, after=32)
    evidence(4600, 'clear candidate count1904', anchor='i32.store offset=1904', before=5, after=24)
    evidence(4600, 'loot-processing before queue decision', anchor='call 4630', before=13, after=37)
    evidence(4600, 'queue priority and suppression; clear kind2577', anchor='i32.load offset=2372', before=3, after=37)
    # First2372 is the decrement; retain the later decision explicitly as well.
    evidence(4600, 'suppression flags2564/2565', anchor='i32.load8_u offset=2564', before=24, after=22)
    evidence(4600, 'resume phase2579', anchor='i32.store8 offset=2579', before=3, after=12)
    evidence(4600, 'generate next choice2159', anchor='call 2159', before=4, after=3)
    evidence(22287, 'owned record vector1656/1660 and80B stride', anchor='i32.load offset=1656', before=1, after=45)
    evidence(22287, 'complete existing record copy', anchor='i64.store offset=32 align=4', before=6, after=65)
    evidence(916, 'active84B records648/652 and countdown decrement', anchor='i32.load offset=652', before=1, after=76)
    evidence(916, 'resolve effective80B record', anchor='call 22287', before=10, after=16)
    evidence(916, 'execute cast922', anchor='call 922', before=13, after=14)
    evidence(922, 'cast calls actual hit914', anchor='call 914', before=22, after=4)
    evidence(914, 'actual unit HP pointer288 and subtract/store', anchor='i32.const 288', before=2, after=29)
    evidence(91940, 'exported malloc wrapper calls internal106890', anchor='call 106890', before=16, after=7)
    evidence(135228, 'exported free wrapper calls internal71888', anchor='call 71888', before=5, after=2)
    required_edges = [(1073,25368),(1073,1513),(1073,4600),(4600,2159),
                      (916,22287),(916,922),(922,914),(91940,106890),(135228,71888)]
    edges = []
    for caller, callee in required_edges:
        sites = [{'wat_offset': a, 'wat_line': line, 'instruction': kind}
                 for a, line, kind in con.execute('SELECT wat_offset,wat_line,instruction FROM calls WHERE caller=? AND callee=?', (caller, callee))]
        require(bool(sites), 'Missing actual direct edge')
        edges.append({'caller': caller, 'callee': callee, 'sites': sites})
    stores = [{'operation': op, 'field_offset': offset, 'wat_line': line}
              for op, offset, line in con.execute("SELECT operation,field_offset,wat_line FROM memops WHERE function_idx=1513 AND operation LIKE '%store%' AND field_offset BETWEEN 1360 AND 1444 ORDER BY wat_line")]
    con.close()
    save(out / 'guards.json', guards)
    input_pin = {'source_sha256': SOURCE_SHA, 'profile_manifest_sha256': sha(PROFILE / 'manifest.json'),
                 'wat_sha256': manifest['wat_sha256'], 'database_sha256': manifest['database_sha256'],
                 'profile_tool_sha256': PROFILE_TOOL_SHA, 'trace_tool_sha256': sha(Path(__file__))}
    require(sha(SOURCE) == SOURCE_SHA and sha(ROOT / 'scripts/wasm134_profile.py') == PROFILE_TOOL_SHA, 'Input/tool changed')
    result = {'target_version': '0.134.0', 'build': '983346a7', 'status': 'static trace complete',
              'input_identity': input_pin, 'database_read_only': True, 'evidence_directory': str(out),
              'full_functions': list(functions.values()), 'direct_edges': edges, 'guards': guards,
              'exports': exports, 'original_has_implicit_start_section': has_start,
              'exported_allocator': malloc,
              'verified_role_correspondence_from_historical': {'1065':1073,'1573':1513,'4595':4600,'22136':22287,'917':916,'934':922,'933':914},
              'state_offsets_0134': {'phase':2579,'selection_kind':2577,'mode':2574,
                  'candidate_capacity':1896,'candidate_pointer':1900,'candidate_count':1904,
                  'owned_capacity':1652,'owned_pointer':1656,'owned_count':1660,
                  'queue_default':2368,'queue_kind1':2372,'queue_kind2':2376,
                  'queue_default_flag':2573,'selection_suppression_mode':2564,'selection_suppression_flag':2565,
                  'active_pointer':648,'active_count':652,'max_hp':1360,'damage':1364,'cooldown':1368,
                  'critical_chance':1372,'critical_multiplier':1376,'area':1400,'current_hp':1528},
              'candidate_layout_0134': {'stride_bytes':80,'niche_or_capacity':60,'payload_pointer':64,
                  'payload_length':68,'owned_index':72,'tier':76,
                  'canonical_new_ability_tag_u32':2147483648,'existing_special_tag_u32':2147483649,
                  'new_id_vs_existing_kind_payload': 'determined by full niche dispatch; +0..59 are presentation payload, not owned record prefix'},
              'owned_layout_0134': {'stride_bytes':80,'definition_pointer':0,'level':4,'countdown':8,
                  'damage':12,'cooldown':16,'targets':20,'area':24,'duration':28,'kind_counters':[32,36,40,44,48]},
              'ability_definition_lookup': {'base':5463472,'record_stride':88,'lookup_span_bytes':10032,'count':114,
                  'id_pointer_offset':12,'id_length_offset':16},
              'stat_output_stores': stores,
              'target_executed':False,'runtime_oracle_cases':0,'network_used':False,'app_or_save_writes':False,
              'elapsed_seconds':round(time.monotonic()-started,3),
              'limitations':['Static live owned-vector read/write and consumer chain only; no selection runtime acceptance in this report.',
                 'Role correspondence does not imply complete function equivalence across versions.',
                 'Shared talent/equipment/notification branches remain original code and are not independently reconstructed.',
                 'Next-choice generation2159 is identified as the actual continuation, not fully specified here.',
                 'No historical state offsets, runtime counters or helper acceptance numbers are reused as new-version validation.']}
    save(out / 'manifest.json', result)
    save(ROOT / 'reports/2026-11-01-selection0134-chain.json', result)
    md = f'''# 官方0.134.0选卡至实际拥有记录消费链

本轮为新版 **0.134.0 / 983346a7** 原件的静态分析，SHA-256 `{SOURCE_SHA}`。复用冻结新版完整WAT/SQLite，只读数据库；没有执行原件、运行差分样例、联网或读写存档。所有完整函数、二进制body、关键连续指令与绝对WAT行号保留在 `{out.relative_to(ROOT)}`。

## 新版真实函数链

| 角色 | 新版函数 | 历史编号仅供检索 |
| --- | ---: | ---: |
| 接受并应用选择 |1073|1065|
| 每kind数值helper |25368|25242|
| 属性重算 |1513|1573|
| 收尾与下一选择 |4600|4595|
| 按ID解析真实owned记录 |22287|22136|
| active能力tick |916|917|
| 实际施法executor |922|934|
| 实际伤害/HP路径 |914|933|

这些编号来自新版真实direct-call edge和完整函数读写指令，不是按统一偏移换算。1073尾部明确依次`1513(G)`、`4600(G,entry_kind)`；916先从22287得到有效80B能力记录，再交给922，922实际调用914；914存在指向单位`+288`的f32减法和store。JSON列出每个完整body/WAT范围、字节数、SHA和全部该链调用位置。

## 关键布局已变化

| 新版G字段 | Offset |
| --- | ---: |
| phase / selection kind / mode |2579 /2577 /2574|
| candidate cap / ptr / count |1896 /1900 /1904|
| owned cap / ptr / count |1652 /1656 /1660|
| default /kind1 /kind2 pending queues |2368 /2372 /2376|
| active ptr / count |648 /652|
| maxHP /damage /cooldown /area /currentHP |1360 /1364 /1368 /1400 /1528|

1073真实入口要求`G.u8(2579)==2`、`choice_index<G.u32(1904)`、`G.u8(2577)!=255`。历史2299/2297、1716/1720、1468/1472不能放进新版fixture。

候选仍为80B；`+60`仍是niche/capacity复用槽，dispatch将非负值和`0x80000001`导入已有能力路径，canonical新能力tag为`0x80000000`。已有分支`+64/+68`为kind-byte向量ptr/len、`+72`为owned index、`+76`为tier；新能力分支`+64/+68`为ID ptr/len。完整分派还存在其他候选变体，不能把它简化成“只有两个tag”，也不能把展示payload`+0..59`当owned记录前缀。

新能力ID lookup明确每次推进88字节，终止span10032，因此本版表为 **114×88B**、base`5463472`。成功后构造80B记录、调用26967/26591，按`G+1652`capacity检查后向`G+1656 + count*80`完整复制，更新`G+1660`。

已有能力先检查owned index边界；非空kind序列从真实owned指针取记录。每kind先把record.level4加1，调用25368，再分别写12/16/20/24/28；更新32+4*kind的计数，最后对damage12应用有序f32共享增长。非空/空kind、越界owned index及内存释放分支均在完整1073保留，不宣称只靠这些静态片段已完成整次选择验收。

## 后处理、phase与消费者

1073保留共享天赋/通知/装备等分支后调用1513；1513实际写新版stats1360..1444及currentHP1528。4600对入口类别的2368/2372/2376队列饱和减1，清候选count1904并销毁80B内容，经过loot/XP路径（含call4630）之后才判断2372→2376→2368。默认队列还受2564/2565抑制。无下一项时清2577为255、置phase2579为1并进入恢复/通知路径；有下一项则真正调用`2159(G,next_kind,0)`。2159候选生成内部规则、所有共享副作用仍需独立研究。

22287从同一owned ptr1656/count1660按definition ID寻找记录，80B步进并复制完整有效记录；找不到时有独立默认构造及跨owned damage汇总路径，不能把它当作无条件直接拷贝。916使用84B active记录（ptr648/count652），先减countdown8，达到施法条件后调用22287→922，并读取新版cooldown1368。由此证明选择写入的向量被实际能力消费者读取。

## full134研究oracle的分配器入口

原export节已独立解析：`__wbindgen_malloc` = **91940**, type6 **(i32 size,i32 align)->i32**；`__wbindgen_realloc`=95051/type16 `(i32,i32,i32,i32)->i32`；`__wbindgen_free`=135228/type1 `(i32,i32,i32)->()`。91940内部call106890，135228内部call71888；内部函数编号不能冒称现有同名导出。原件没有隐式start节；`__wbindgen_start`仍是显式应用启动导出，研究oracle不应调用。

此报告只给新版真实函数与字段静态入口，不给整核心/整卡片流程运行验收。原件和冻结profile身份前后复查一致；模型、旧脚本、README、targets均未修改。
'''
    (ROOT / 'reports/2026-11-01-selection0134-chain.md').write_text(md)
    print(json.dumps({'evidence_directory':str(out),'functions':len(functions),'guards':len(guards),
                      'malloc':malloc,'target_executed':False,'runtime_oracle_cases':0}))


if __name__ == '__main__':
    main()
