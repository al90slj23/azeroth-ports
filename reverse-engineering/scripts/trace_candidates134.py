#!/usr/bin/env python3
"""Freeze new0134 candidate generation bodies and contiguous static guards.

Uses the pinned full-WAT producer through SQLite mode=ro, seeks whole functions,
reconstructs only initial data memory, and never instantiates or runs a target.
"""
from datetime import datetime, timezone
import hashlib
import difflib
import json
from pathlib import Path
import sqlite3
import struct
import time

from extract_catalogue134 import parse_binary, reconstruct

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/latest-wenilla_bg.wasm'
SOURCE_SHA = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
PROFILE = ROOT / 'evidence/wasm0134-profile-20261101T001728.222975Z'
WAT_SHA = '6014dab110e40ae279a6450ae15dcc0d84727c31e2da71f18f2cab1f21ec8422'
DB_SHA = 'f131b4454ac1a8754f5b0417e4192efbaada6478df737e09490154c71fd340f9'
PROFILE_TOOL_SHA = 'ecbdc939fe1cad8b240a6d5f6645a96b54fe69b87b69ee54ab39290d14969cf9'
ROLES = {2159: 'candidate generation entry and weighted sampling',
         1480: 'candidate80B construction and upgrade-kind shuffle',
         32652: 'xoshiro128++ ordered f32 range sampler',
         29736: 'collect available upgrade kinds', 27375: 'upgrade eligibility iterator',
         25368: 'numeric upgrade value', 49338: 'special cooldown floor helper',
         1708: 'kind1/2 generator, unresolved', 34493: 'destroy candidate vector',
         75441: 'string clone', 32245: 'rank key formatting',
         35513: 'world notification side effects, unresolved',
         1203: 'selection notification rendering, unresolved',
         6310: 'selection text notification, unresolved'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def save(path, value):
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    path.write_text(text)
    require(json.loads(path.read_text()) == value, 'JSON readback differs')


def main():
    started = time.monotonic()
    require(SOURCE.stat().st_size == 90953762 and sha(SOURCE) == SOURCE_SHA, 'Official source differs')
    require(sha(ROOT / 'scripts/wasm134_profile.py') == PROFILE_TOOL_SHA, 'Profile producer changed')
    manifest = json.loads((PROFILE / 'manifest.json').read_text())
    require(manifest['target_version'] == '0.134.0' and manifest['embedded_build'] == '983346a7', 'Profile target differs')
    wat, db = Path(manifest['wat_path']), Path(manifest['database_path'])
    require(sha(wat) == WAT_SHA and sha(db) == DB_SHA, 'Frozen full profile differs')
    binary = SOURCE.read_bytes()
    image = reconstruct(binary, parse_binary(binary))
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('candidates0134-chain-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    connection = sqlite3.connect('file:' + str(db) + '?mode=ro', uri=True)
    meta = {k: json.loads(v) for k, v in connection.execute('SELECT key,value FROM meta')}
    require(meta['original_sha256'] == SOURCE_SHA, 'Index source differs')
    functions, texts = {}, {}
    with wat.open('rb') as stream:
        for index, role in ROLES.items():
            a, b, line, ba, bb, size = connection.execute(
                'SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?', (index,)).fetchone()
            stream.seek(a)
            text = stream.read(b - a)
            require(text.startswith(f'  (func (;{index};)'.encode()) and bb - ba == size, 'Incomplete function range')
            body = binary[ba:bb]
            (out / f'function-{index}.wat').write_bytes(text)
            (out / f'function-{index}.body.bin').write_bytes(body)
            functions[index] = {'index': index, 'role': role, 'wat_start': a, 'wat_end': b,
                'wat_start_line': line, 'wat_bytes': len(text), 'wat_sha256': hashlib.sha256(text).hexdigest(),
                'body_start': ba, 'body_end': bb, 'body_bytes': size,
                'body_sha256': hashlib.sha256(body).hexdigest()}
            texts[index] = text.decode().splitlines()
    guards = []

    def guard(index, label, sequence, before=4, after=10, occurrence=0):
        lines = texts[index]
        normalized = [s.strip() for s in lines]
        matches = [i for i in range(len(lines) - len(sequence) + 1)
                   if normalized[i:i + len(sequence)] == sequence]
        require(len(matches) > occurrence, f'Missing candidate guard {index}: {label}')
        n = matches[occurrence]
        a, b = max(0, n - before), min(len(lines), n + len(sequence) + after)
        guards.append({'function': index, 'label': label, 'match_count': len(matches),
            'function_line_start': a + 1, 'function_line_end': b,
            'full_wat_line_start': functions[index]['wat_start_line'] + a,
            'instructions': lines[a:b]})

    guard(2159, 'kind low8 and kind1/2 dispatch', ['local.get 1','i32.const 255','i32.and','i32.const 1','i32.sub'], after=10)
    guard(2159, 'owned count six excludes all new candidates', ['local.get 16','i32.const 6','i32.lt_u','br_if 3 (;@6;)'], after=9)
    guard(2159, 'class byte and lookup table', ['local.get 8','i32.const 2','i32.sub','i32.const 255','i32.and'], after=18)
    guard(2159, 'new weight1.6 below3 otherwise0.9', ['f32.const 0x1.99999ap+0 (;=1.6;)','f32.const 0x1.ccccccp-1 (;=0.9;)'], after=10)
    guard(2159, 'new candidate owned id exclusion', ['local.get 3','i32.load','local.get 12','local.get 11','call 82065'], before=10, after=12)
    guard(2159, 'demonic effect list and summon filtering', ['i32.load offset=2024'], before=30, after=250)
    guard(2159, 'explicit blocked borrowed-id vector', ['i32.load offset=2084'], before=2, after=38)
    guard(2159, 'banished string vector for new IDs', ['i32.load offset=2096'], before=2, after=42)
    guard(2159, 'new weighted20B pool record', ['i32.const -2147483648','i32.store offset=4','local.get 4','local.get 23','f32.store'], before=16, after=12)
    guard(2159, 'tier4 eligibility probe before upgrade pooling', ['i32.const 4','i32.store offset=132'], after=69)
    guard(2159, 'rank key formatting and upgrade-ban comparison', ['i32.const 1056420'], before=12, after=64)
    guard(2159, 'upgrade weight1.3 record', ['i64.const 5362837094','i64.store align=4'], before=22, after=16)
    guard(2159, 'requested candidate count3/4 flags', ['i32.load8_u offset=275'], before=2, after=52)
    guard(2159, 'pool f32 sum and range sample', ['call 32652'], before=28, after=59, occurrence=0)
    guard(2159, 'remove selected pool element preserving order', ['local.get 4','local.get 4','i32.const 20','i32.add','local.get 3','memory.copy'], before=25, after=12)
    guard(2159, 'tier luck level and weights', ['f32.load offset=1404'], before=6, after=127)
    guard(2159, 'tier escalation until eligible', ['i32.store offset=108'], before=12, after=110, occurrence=0)
    guard(2159, 'empty pool gold25 fallback', ['i64.const 109521666052'], before=8, after=30)
    guard(2159, 'replace candidate vector', ['i32.const 1896','i32.add'], before=3, after=30)
    guard(2159, 'kind counter phase ui effects', ['i32.store8 offset=2577'], before=3, after=30)
    guard(1480, 'existing candidate selected-owned index guard', ['i32.load offset=12','local.tee 17'], after=17)
    guard(1480, 'kind vector collection and random shuffle setup', ['call 29736'], before=65, after=160)
    guard(1480, 'tier4 takes2 otherwise1 kinds', ['i32.const 2','i32.const 1','local.get 3','i32.const 3','i32.gt_u','select'], before=3, after=15)
    guard(1480, 'existing candidate tail fields60..76', ['i32.store offset=68','local.get 0','local.get 4','i64.load offset=456 align=4','i64.store offset=60 align=4'], before=5, after=16)
    guard(1480, 'new candidate canonical tag and ID/tier tail', ['i32.const -2147483648','i32.store offset=60'], before=12, after=8)
    guard(32652, 'range validation and ordered width', ['local.get 1','local.get 2','f32.lt'], after=26)
    guard(32652, 'xoshiro recurrence and high23-bit f32 construction', ['loop  ;; label = @5'], after=82)
    guard(32652, 'RNG final state writes', ['i32.store offset=12','local.get 0','local.get 3','i32.store'], before=2, after=12)
    guard(29736, 'collect all eligible kind bytes to255', ['call 27375'], before=6, after=22)
    guard(27375, 'eligibility definition execution dispatch', ['i32.load8_u offset=84'], before=8, after=208)
    guard(27375, 'kind2 disallows tier0 and helper minimum0.005', ['call 25368','f32.const 0x1.47ae14p-8 (;=0.005;)','f32.ge'], before=13, after=9)
    for index, label, a, b in [
            (27375, 'complete execution11 structure', 43, 97),
            (27375, 'complete non11 structural switch', 105, 247),
            (27375, 'complete execution9 interval saturation', 255, 396),
            (27375, 'complete execution11 special cooldown branches', 398, 625),
            (49338, 'complete six-ID cooldown floor', 1, 109)]:
        require(0 < a <= b <= len(texts[index]), 'Full branch evidence range differs')
        guards.append({'function':index,'label':label,'function_line_start':a,'function_line_end':b,
            'full_wat_line_start':functions[index]['wat_start_line'] + a - 1,
            'instructions':texts[index][a-1:b]})
    old_helper = ROOT / 'evidence/wasm-focused-20261031T225829.291348Z/function-25242.wat'
    old_sha = '6f2b604d5905ff04dd9a1c99d58be8cdce67b7279afbecd4a677de45a46d5ba5'
    require(sha(old_helper) == old_sha, 'Historical complete helper evidence differs')
    old_lines = old_helper.read_text().splitlines()
    expected = list(old_lines)
    replacements = {'25242':'25368','(type 92)':'(type 94)',
        '5308472':'5410584','5308508':'5410620','5308544':'5410656',
        '5308580':'5410692','5308616':'5410728','5308492':'5410604',
        '5308528':'5410640','5308564':'5410676','5308600':'5410712',
        '5308636':'5410748','call 80330':'call 80662'}
    for old, new in replacements.items():
        expected = [line.replace(old,new) for line in expected]
    require(expected == texts[25368], 'New upgrade helper differs beyond header/data/panic relocation')
    helper_diff = list(difflib.unified_diff(old_lines,texts[25368],fromfile='old25242',tofile='new25368',lineterm=''))
    (out / 'upgrade-helper-relocation.diff').write_text('\n'.join(helper_diff)+'\n')
    edges = []
    for caller, callee in [(2159,1480),(2159,29736),(2159,32652),(2159,1708),
                           (1480,29736),(1480,25368),(29736,27375),(27375,25368),(27375,49338)]:
        sites = [{'full_wat_line': line, 'wat_offset': a, 'instruction': op}
                 for a, line, op in connection.execute('SELECT wat_offset,wat_line,instruction FROM calls WHERE caller=? AND callee=?', (caller, callee))]
        require(sites, f'Missing direct edge{caller}->{callee}')
        edges.append({'caller': caller, 'callee': callee, 'sites': sites})
    connection.close()
    class_pointers = list(struct.unpack_from('<10I', image, 1595872))
    require(class_pointers == [5458740,5458828,5458916,5459004,5458652,5459092,5459180,5459268,5458652,5459356], 'Class pointer switch differs')
    tables = [list(struct.unpack_from('<5I', image, a)) for a in [5410584,5410620,5410656,5410692,5410728]]
    import sys
    sys.path.insert(0, str(ROOT / 'reconstruction'))
    from core_spec.upgrade_values import TABLES
    require(tables == [list(x) for x in TABLES], 'New numeric helper tables differ')
    from core_spec.candidates134 import DEFINITIONS, CLASS_KITS, CLASS_BYTE
    def static_string(address):
        pointer, length = struct.unpack_from('<II',image,address)
        return bytes(image[pointer:pointer+length]).decode('ascii')
    require(len(DEFINITIONS) == 114 and len(CLASS_KITS) == 9, 'Model declaration count differs')
    for index in range(114):
        address = 5463472 + index * 88
        ability_id = static_string(address+12)
        definition = DEFINITIONS[ability_id]
        words = struct.unpack_from('<22I',image,address)
        kp, kn = words[9:11]
        require((definition.pointer,definition.kinds,definition.execution,definition.damage_bits,
                 definition.radius_bits,definition.count,definition.effect_tag,definition.cooldown_bits,definition.duration_bits) ==
                (address,tuple(image[kp:kp+kn]),image[address+84],words[12],words[15],words[16],words[0],words[13],words[17]),
                'Model definition differs from official initial image')
    for index in range(9):
        address = 5458652 + index * 88
        class_id = static_string(address+16)
        pointer, count = struct.unpack_from('<II',image,address+32)
        require(CLASS_KITS[class_id] == tuple(static_string(pointer+i*8) for i in range(count)), 'Model class kit differs')
    require(CLASS_BYTE == {2:'paladin',3:'hunter',4:'rogue',5:'priest',7:'shaman',8:'mage',9:'warlock',11:'druid'}, 'Model class switch differs')
    static = {'class_switch_table_address' :1595872,'class_pointer_words_u32':class_pointers,
        'rank_template_address':1056420,'rank_template_prefix_hex':bytes(image[1056420:1056428]).hex(),
        'rank_key_semantics':'rank:'+ '{ability_id}',
        'special_id':'demonic_empowerment', 'new_max_owned_exclusive':6,
        'upgrade_tables_addresses':[5410584,5410620,5410656,5410692,5410728],
        'upgrade_tables_raw_u32':tables,'old_helper_complete_wat_sha256':old_sha,
        'new_helper_complete_wat_sha256':functions[25368]['wat_sha256'],
        'helper_only_header_table_panic_relocations_verified':True}
    save(out / 'guards.json', guards)
    save(out / 'static-data.json', static)
    result = {'target_version':'0.134.0','build':'983346a7','status':'static kind0 metadata model; UI payload pending; no runtime acceptance',
        'source_sha256':SOURCE_SHA,'source_bytes':len(binary),'wat_sha256':WAT_SHA,'database_sha256':DB_SHA,
        'profile_manifest_sha256':sha(PROFILE / 'manifest.json'),'profile_tool_sha256':PROFILE_TOOL_SHA,
        'trace_tool_sha256':sha(Path(__file__)),'independent_model_sha256':sha(ROOT / 'reconstruction/core_spec/candidates134.py'),
        'evidence_directory':str(out),'database_read_only':True,'full_functions':list(functions.values()),
        'direct_edges':edges,'guards':guards,'static_data':static,
        'rng':{'state_G_offset':1712,'words':4,'algorithm':'xoshiro128++','range_function':32652,
            'shuffle_function':1480,'shuffle_accept':'product.low32<=u32((n<<clz32(n))-1)',
            'order':'all weighted pool samples; then per selected item tier sample; then that upgrade item kind shuffle'},
        'fields':{'class':360,'flag_enable4':275,'flag_default3_bit0':2573,'luck_f32':1404,'level':1520,
            'owned_ptr':1656,'owned_count':1660,'blocked_ptr':2080,'blocked_count':2084,
            'banished_strings_ptr':2092,'banished_strings_count':2096,'effects_ptr':2020,'effects_count':2024,
            'summons_ptr':2044,'summons_count':2048,'candidate_cap':1896,'candidate_ptr':1900,'candidate_count':1904,
            'choice_history_cap':1944,'choice_history_ptr':1948,'choice_history_count':1952,
            'generation_counter':2392,'selection_kind':2577,'phase':2579},
        'model_supported':'kind0 metadata, all114 definition eligibility, demonic predicate from explicit effects/summons, exact draw ordering/f32/tier/shuffle, gold25 fallback',
        'unknown':['Allocated80B display payload+0..59 and allocator identity','kind1/2 generator1708','world side effects35513 and notifications1203/6310','seed initialization and external reroll action semantics'],
        'target_executed':False,'runtime_oracle_cases':0,'network_used':False,'save_accessed':False,
        'elapsed_seconds':round(time.monotonic()-started,3)}
    require(sha(SOURCE) == SOURCE_SHA and sha(ROOT / 'scripts/wasm134_profile.py') == PROFILE_TOOL_SHA, 'Inputs changed')
    save(out / 'manifest.json', result)
    save(ROOT / 'reports/2026-11-01-candidates0134-chain.json', result)
    md = f'''# 官方0.134.0候选生成与随机链

冻结原件 **0.134.0 / 983346a7**，SHA256 `{SOURCE_SHA}`。SQLite以`mode=ro`连接，只按完整func range seek WAT；全部14个函数WAT/body、SHA、连续guards和绝对行号在`{out.relative_to(ROOT)}`。没有执行WASM/EXE/APK、联网、存档读写或应用写入。运行差分case数为0，本报告不能称为原件运行验收。

## kind0候选池

2159按kind低8位派发；1/2调用1708(G,0/0.25)，其余default走普通能力池。本独立模型只接受kind0，其他明确pending。owned80B向量来自G+1656/1660。owned数量>=6完全跳过新技能；数量<6按职业kit原顺序访问，排除已有ID、blocked借用ID向量2080/2084、banished字符串向量2092/2096。新技能weight为owned<3时f32(1.6)，否则f32(0.9)。职业byte360的2/3/4/5/7/8/9/11分别为paladin/hunter/rogue/priest/shaman/mage/warlock/druid；其他byte回退warrior。该映射来自实际1595872指针表，不是职业列表顺序猜测。

`demonic_empowerment`还有先于blocked列表的过滤：从effects2020/2024的8B项按顺序累加kind-byte32的f32值。sum>0时，summon2044/2048的36B项tag42要求pointer4指向对象的u8+41>4；sum不>0则要求>0。tag46/47总合格；tag45仅sum不>0合格。没有合格项就排除此新技能。独立模型使用显式Effect/Summon快照，默认空列表表示明确空的相关向量。

已有技能按owned原顺序，先用tier4收集可升级kind（29736→27375→25368），空列表不入池。再以`rank:{{ability_id}}`排除banished字符串，合格项weight f32(1.3)。这不是每kind一个独立pool项；每个owned能力最多一个项。blocked借用ID只过滤新技能，不直接过滤已有升级。

## 抽样与tier

flag275为0固定请求3卡；flag275非零时，flag2573的bit0为1请求3卡、为0请求4卡。此处两个select的栈顺序已用首轮pilot失败保留证据修正。每轮从剩余20B pool项按顺序累加f32权重，用32652抽[0,sum)，依次减权重取首个命中；命中项以memory.copy移除并保留其他项顺序。最多抽请求数或pool长度，因此同次普通池不会重复同一项。先抽完所有pool项，再按被抽出的顺序分别生成tier；不能交错pool抽样与tier随机。

令`x=f32(f32(G.f32[1404]+1)+min(f32(f32_u32(G.u32[1520])*.01),.3))`。tier权重是`[60,25*x,10*x²,4*x³,x⁴]`，全部按原指令次序f32舍入；x²先算、x⁴由x²*x²、4*x³由(x*x²)*4。tier单次range随机先减60，再减后续weight；越界舍入尾值回退tier0。新技能保留此tier。已有技能若此tier没有可升级kind，则按tier递增探测，最高4；pool先前已证明tier4至少有一项。

29736保留定义upgrade-byte列表顺序且不耗随机。1480对完整合格kind列表做Fisher–Yates洗牌，长度n..2；每次raw RNG乘n，`low32<=u32((n<<clz32(n))-1)`才接受，拒绝也推进RNG，index为乘积high32。tier0..3保留洗牌后1项，tier4保留最多2项。每张升级卡的洗牌在下一张tier roll之前完成。

32652 RNG位于G+1712的4×u32，是xoshiro128++：output=rotl(s0+s3,7)+s0，然后四word按完整body更新；高23位构造[1,2)的f32再减1，ordered f32缩放到range。四word全零是退化固定点，本模型不擅自补seed；seed初始化仍unknown。

## 过滤、fallback与刷新边界

非execution9/11的27375结构过滤：kind0要求definition.damage48>0；kind1允许；kind2要求definition.count64非零并满足execution bitset/radius条件且tier非0；kind3要求execution∈{{2,3,4,8}}或execution10且radius60>0；kind4要求execution∈{{3,6,10}}。每个kind都需25368>=f32(.005)。execution9/11的27375分支也已完整恢复：e9有effect-tag结构过滤及kind1/4的duration/有效cooldown饱和度；e11有redemption的76字段概率阈值、faerie_fire禁止cooldown以及六ID冷却floor。模型按原指令f32次序计算，derived cooldown显式取G1368。divine_shield的duration截到6、冷却floor=10-duration，hellfire floor=.5，其他默认.25。49338的bloodrage/seal_fate/soul_fire/lightwell/polymorph/hunters_mark下限分别8/2/3/6/3/2，其余0。新版25368与旧完整helper268行逐条比较，只允许16行header、五表和panic重定位；其余完全相同。五张新版表原始u32与独立upgrade_values.py逐项一致，diff也保存为证据。

空pool无随机draw，构造gold25的输入tag0x80000004、tier0作为唯一fallback候选。普通新/已有/gold三种候选不会进入G+1944的特殊历史记录追加dispatch，因此该历史不影响已规格域。再次调用2159从当前RNG重抽；2392只在末尾加1，不能把这个counter或历史向量误当作去重seed。实际reroll操作如何修改banish/flags/queues仍未在此独立实现。

候选80B中+60分派，+64/+68在新技能为ID ptr/len、已有为kind Vec ptr/len，+72为已有owned index，+76为tier。1480会另外生成+0..59显示payload；独立模型返回selection所需metadata并显式`ui_payload_pending=True`，不宣称已生成完整UI80B。2159替换1896/1900/1904后写kind2577、counter2392；第三参非零才置phase2579=2，mode2574=0时还执行35513世界副作用，随后1203/6310通知。这些副作用明确pending。

## Controlled2159入口

研究fixture先用kind0、第三参1、mode2574=1跳过世界副作用，2558=0使6310早退。设置class360=1为warrior、G1712四个非零u32，level1520=1、luck1404=0；owned1660=0，effects2024/summons2048/blocked2084/banished2096/history1952/candidate1904/notification1892均0，各空Vec的capacity0、ptr为合适对齐dangling指针。flag2573=1、flag275=0期望3卡；flag2573=0且flag275=1才请求4卡。生成顺序、候选ID/tier、RNG四word可与独立`generate_kind0_metadata`差分；展示文本、分配器地址不属于该函数返回的已实现域。

重现：`python3 reverse-engineering/scripts/trace_candidates134.py`。只新增trace、报告与core_spec/candidates134.py；没有改model/builder/host/docs，没有commit/push。
'''
    (ROOT / 'reports/2026-11-01-candidates0134-chain.md').write_text(md)
    print(json.dumps({'evidence':str(out),'functions':len(functions),'guards':len(guards),'elapsed_seconds':result['elapsed_seconds']}))


if __name__ == '__main__':
    main()
