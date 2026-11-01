#!/usr/bin/env python3
"""Compare independent kind0 metadata against complete official0.135.1 2159.

Original2159 and every reached callee remain unchanged. The synthetic mode1
fixture omits world effects through the real guard. All878 host imports throw.
Only allocated-candidate metadata/RNG/phase/kind/counter are accepted here.
"""
import argparse
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, ROLES, build
from build_upgrade134_oracle import sha

SOURCE_FILES = ('scripts/check_candidates135_full_spec.py', 'scripts/run_candidates135_full_oracle.mjs',
    'scripts/build_full135_oracle.py', 'scripts/build_upgrade134_oracle.py', 'scripts/full135_host.mjs',
    'scripts/extract_catalogue135.py', 'reconstruction/core_spec/candidates135.py',
    'reconstruction/core_spec/ability_state.py', 'reconstruction/core_spec/upgrade_values.py',
    'reconstruction/core_spec/rng.py', 'reconstruction/core_spec/binary32.py', 'scripts/extract_catalogue134.py')


def source_hashes():
    return {name: sha(ROOT / name) for name in SOURCE_FILES}


IMPORT_SOURCE_HASHES = source_hashes()
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.candidates135 import (CLASS_BYTE, CLASS_KITS, DEFINITIONS, Effect, Summon,
    Owned, generate_kind0_metadata)
from core_spec.ability_state import AbilityRecord
from core_spec.binary32 import from_float

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_VERSION = 'v22.23.4'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
RUNTIME_FLAGS = ('--max-old-space-size=512', '--wasm-max-mem-pages=512')
SEED = 0xa2e02159
SEEDS = ((1, 2, 3, 4), (0, 0, 0, 0), (0, 0, 0, 0xffffffff),
         (0xffffffff, 1, 2345, 0x7fffffff), (123456789, 362436069, 521288629, 88675123))
CLASSES = (1, 2, 3, 4, 5, 7, 8, 9, 11)


def owned(ability_id, **changes):
    record = replace(AbilityRecord(DEFINITIONS[ability_id].pointer), **changes)
    return {'ability_id': ability_id, 'record_hex': record.to_bytes().hex()}


def state(**changes):
    value = {'rng_words': list(SEEDS[0]), 'class_byte': 1, 'owned': [], 'level': 1,
        'luck_bits': 0, 'cooldown_bits': 0x3f800000, 'flag275': 0, 'flag2573': 1,
        'blocked_ids': [], 'banished_keys': [], 'effects': [], 'summons': [],
        'phase': 1, 'generation_counter': 0, 'third_arg': 1}
    value.update(changes)
    return value


def pilot_cases():
    yield {'group': 'pilot-three', 'input': state(flag2573=1)}
    yield {'group': 'pilot-four', 'input': state(flag275=1, flag2573=0)}


def full_cases():
    yield from pilot_cases()
    for class_byte in range(256):
        yield {'group': 'all-class-byte-switch', 'input': state(class_byte=class_byte,
            rng_words=list(SEEDS[class_byte % len(SEEDS)]), flag2573=class_byte & 1)}
    for class_byte in CLASSES:
        for level in (0, 1, 2, 29, 30, 31, 120, 0xffffffff):
            for luck in (-.99, 0, 3):
                yield {'group': 'class-level-luck', 'input': state(class_byte=class_byte,
                    level=level, luck_bits=from_float(luck), rng_words=list(SEEDS[level % len(SEEDS)]))}
        for words in SEEDS:
            for luck in (-.99, 0, 3, 100):
                for level in (0, 30):
                    yield {'group': 'rng-pool-tier-endpoints', 'input': state(class_byte=class_byte,
                        rng_words=list(words), level=level, luck_bits=from_float(luck))}
        for flag275 in (0, 1, 2, 128, 255):
            for flag2573 in (0, 1, 2, 128, 255):
                yield {'group': 'card-count-flags', 'input': state(class_byte=class_byte,
                    flag275=flag275, flag2573=flag2573)}
        kit = CLASS_KITS[CLASS_BYTE.get(class_byte, 'warrior')]
        for count in range(7):
            for words in SEEDS[:3]:
                yield {'group': 'owned-count-new-weight-and-six-cap', 'input': state(class_byte=class_byte,
                    owned=[owned(name) for name in kit[:count]], rng_words=list(words))}
        for remaining in range(5):
            yield {'group': 'blocked-new-pool-size-and-empty-fallback', 'input': state(class_byte=class_byte,
                blocked_ids=list(kit[:len(kit)-remaining]))}
            yield {'group': 'banished-new-pool-size-and-empty-fallback', 'input': state(class_byte=class_byte,
                banished_keys=list(kit[:len(kit)-remaining]))}
    all_warrior = list(CLASS_KITS['warrior'])
    record_variants = [
        ('neutral', {}),
        ('damage-count-u32max', {'counts': (0xffffffff, 0, 0, 0, 0)}),
        ('cooldown-below-point2', {'cooldown_bits': 0x3e4ccccc}),
        ('cooldown-point2', {'cooldown_bits': 0x3e4ccccd}),
        ('cooldown-above-point2', {'cooldown_bits': 0x3e4cccce}),
        ('targets-eleven', {'extra_targets': 11}),
        ('targets-twelve', {'extra_targets': 12}),
        ('area-below-five', {'area_bits': 0x409fffff}),
        ('area-five', {'area_bits': 0x40a00000}),
        ('duration-below-six', {'duration_bits': 0x40bfffff}),
        ('duration-six', {'duration_bits': 0x40c00000}),
        ('all-numeric-caps', {'counts': (0xffffffff,) * 5, 'cooldown_bits': 0x3e4ccccd,
            'extra_targets': 12, 'area_bits': 0x40a00000, 'duration_bits': 0x40c00000})]
    for number, ability_id in enumerate(DEFINITIONS):
        for variant_index, (label, changes) in enumerate(record_variants):
            yield {'group': 'all114-owned-' + label, 'input': state(owned=[owned(ability_id, **changes)],
                blocked_ids=all_warrior, rng_words=list(SEEDS[(number + variant_index) % len(SEEDS)]),
                luck_bits=from_float(0 if variant_index & 1 else 100))}
        yield {'group': 'all114-rank-ban', 'input': state(owned=[owned(ability_id)], blocked_ids=all_warrior,
            banished_keys=['rank:' + ability_id, 'unrelated_id'])}
    for ability_id in ('hellfire', 'divine_shield', 'demonic_empowerment', 'redemption', 'faerie_fire',
                       'bloodrage', 'seal_fate', 'soul_fire', 'lightwell', 'polymorph', 'hunters_mark'):
        for cooldown in (.01, .1, .25, .5, 1, 5):
            for duration in (1, 5, 6):
                yield {'group': 'special9-11-interval-saturation', 'input': state(
                    owned=[owned(ability_id, duration_bits=from_float(duration),
                        additional_duration_bits=from_float(1.4), additional_cooldown_bits=from_float(.8))],
                    blocked_ids=all_warrior, cooldown_bits=from_float(cooldown), luck_bits=from_float(100))}
        for factor in (.19799998, .198, .19800002, .98999995, .99, .99000007, 1, 2):
            yield {'group': 'special9-11-record76-probability', 'input': state(
                owned=[owned(ability_id, field76_bits=from_float(factor))],
                blocked_ids=all_warrior, cooldown_bits=from_float(.1))}
    warlock_blocked = [name for name in CLASS_KITS['warlock'] if name != 'demonic_empowerment']
    effect_sets = ([], [{'kind': 32, 'value_bits': 0}],
        [{'kind': 32, 'value_bits': from_float(1)}], [{'kind': 32, 'value_bits': from_float(-1)}],
        [{'kind': 32, 'value_bits': 0x7fc00001}],
        [{'kind': 32, 'value_bits': from_float(1)}, {'kind': 32, 'value_bits': from_float(-1)}],
        [{'kind': 31, 'value_bits': from_float(1)}])
    for effects in effect_sets:
        for tag in (0, 12, 41, 42, 43, 44, 45, 46, 47, 48):
            for value in (0, 1, 4, 5):
                yield {'group': 'demonic-effect-summon-predicate', 'input': state(class_byte=9,
                    blocked_ids=warlock_blocked, effects=effects, summons=[{'tag': tag, 'state41': value}])}
    multi_kind = [name for name, definition in DEFINITIONS.items() if len(definition.kinds) >= 3]
    rng = random.Random(SEED)
    for ability_id in multi_kind[:25]:
        for _ in range(8):
            yield {'group': 'kind-shuffle-rejection-and-tier4-two', 'input': state(owned=[owned(ability_id)],
                blocked_ids=all_warrior, rng_words=[rng.getrandbits(32) for _ in range(4)],
                luck_bits=from_float(100))}
    for counter in (0, 1, 0xfffffffe, 0xffffffff):
        for third_arg in (0, 1):
            for phase in (0, 1, 2, 3, 255):
                yield {'group': 'phase-counter-wrap-and-third-argument', 'input': state(
                    generation_counter=counter, third_arg=third_arg, phase=phase)}
    for _ in range(500):
        class_byte = rng.choice(CLASSES)
        kit = CLASS_KITS[CLASS_BYTE.get(class_byte, 'warrior')]
        identifiers = rng.sample(list(DEFINITIONS), rng.randrange(7))
        yield {'group': 'seeded-mixed-weighted-exclusions', 'input': state(class_byte=class_byte,
            rng_words=[rng.getrandbits(32) for _ in range(4)], level=rng.randrange(121),
            luck_bits=from_float(rng.choice((-.5, 0, .1, 1, 3, 100))),
            cooldown_bits=from_float(rng.choice((.05, .25, 1, 2))),
            flag275=rng.randrange(2), flag2573=rng.randrange(2),
            owned=[owned(name, counts=(rng.randrange(100), 0, 0, 0, 0),
                extra_targets=rng.randrange(14), cooldown_bits=from_float(rng.choice((.2, .3, .6, 1))),
                area_bits=from_float(rng.choice((1, 3, 5))), duration_bits=from_float(rng.choice((1, 3, 6))))
                for name in identifiers],
            blocked_ids=rng.sample(list(kit), rng.randrange(len(kit)+1)),
            banished_keys=['rank:' + name for name in rng.sample(identifiers, rng.randrange(len(identifiers)+1))])}


def expected(input_value):
    args = {key: value for key, value in input_value.items()
            if key not in ('phase', 'generation_counter', 'third_arg', 'owned', 'effects', 'summons')}
    args['owned'] = tuple(Owned(item['ability_id'], AbilityRecord.from_bytes(bytes.fromhex(item['record_hex'])))
                          for item in input_value['owned'])
    args['effects'] = tuple(Effect(**item) for item in input_value['effects'])
    args['summons'] = tuple(Summon(**item) for item in input_value['summons'])
    result = generate_kind0_metadata(**args)
    candidates = [dict(asdict(card), kinds=list(card.kinds)) for card in result.candidates]
    return {'candidates': candidates, 'rng_words': list(result.rng_words),
        'phase2587': 2 if input_value['third_arg'] else input_value['phase'],
        'selection_kind2585': 0, 'generation_counter2400': (input_value['generation_counter'] + 1) & 0xffffffff,
        'candidate_count1912': len(candidates)}, result.rng_draws


def materialize(phase):
    cases = list(pilot_cases() if phase == 'pilot' else full_cases())
    for index, case in enumerate(cases):
        case['id'] = index
        case['expected'], case['expected_rng_draws'] = expected(case['input'])
    return cases


def run_fixed_oracle(directory, casefile, resultfile, stderr):
    if sha(RUNTIME) != RUNTIME_SHA:
        raise ValueError('Pinned project Node identity differs')
    version = subprocess.check_output([str(RUNTIME), '--version'], text=True, timeout=10).strip()
    if version != RUNTIME_VERSION:
        raise ValueError('Pinned project Node version differs')
    command = [str(RUNTIME), *RUNTIME_FLAGS, str(ROOT / 'scripts/run_candidates135_full_oracle.mjs'),
               str(directory), str(casefile)]
    started = time.monotonic()
    with resultfile.open('w') as out, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            raise RuntimeError('Owned original2159 subprocess exceeded60s and was stopped')
    if sha(RUNTIME) != RUNTIME_SHA:
        raise ValueError('Pinned Node changed during comparison')
    return {'command': command, 'runtime_sha256': RUNTIME_SHA, 'runtime_version': version,
        'exit_code': code, 'subprocess_deadline_seconds': 60,
        'elapsed_seconds': round(time.monotonic() - started, 3)}


def coverage(cases):
    cards = [card for case in cases for card in case['expected']['candidates']]
    return {'groups': dict(Counter(case['group'] for case in cases)),
        'input_owned_definition_count': len({item['ability_id'] for case in cases for item in case['input']['owned']}),
        'input_class_bytes': sorted({case['input']['class_byte'] for case in cases}),
        'predicted_card_variants': dict(Counter(card['variant'] for card in cards)),
        'predicted_tiers': dict(Counter(str(card['tier']) for card in cards)),
        'predicted_upgrade_kinds': dict(Counter(str(k) for card in cards for k in card['kinds'])),
        'predicted_empty_pool_fallbacks': sum(case['expected']['candidates'][0]['variant'] == 'gold' for case in cases),
        'predicted_rng_draws_total': sum(case['expected_rng_draws'] for case in cases)}


def check(phase, directory=None, prepare_only=False):
    frozen_sources = source_hashes()
    if frozen_sources != IMPORT_SOURCE_HASHES or sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Frozen sources differ before fixture generation')
    cases = materialize(phase)
    if len(cases) > 6000:
        raise ValueError('Corpus exceeds runner budget')
    if prepare_only:
        output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('candidates0135-prepared-%Y%m%dT%H%M%S.%fZ')
        output.mkdir(parents=True, exist_ok=False)
        manifest = None
    else:
        if ROLES.get('generate_choices') != (2159, b'\x7f\x7f\x7f', b''):
            raise ValueError('Root-approved generate_choices2159 role is not ready')
        if directory is None:
            output, manifest = build(['generate_choices'])
        else:
            output = Path(directory).resolve()
            manifest = json.loads((output / 'manifest.json').read_text())
    casefile = output / 'candidates135-fixtures.jsonl'
    expectedfile = output / 'candidates135-expected.jsonl'
    if casefile.exists() or expectedfile.exists():
        raise ValueError('Refusing to overwrite prior comparison evidence')
    snapshot = output / 'source-snapshot'
    for name, wanted in frozen_sources.items():
        raw = (ROOT / name).read_bytes()
        target = snapshot / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        if sha(target) != wanted:
            raise ValueError('Frozen source snapshot differs before execution')
    (snapshot / 'manifest.json').write_text(json.dumps(frozen_sources, indent=2)+'\n')
    casefile.write_text(''.join(json.dumps(case, separators=(',', ':'), allow_nan=False) + '\n' for case in cases))
    expectedfile.write_text(''.join(json.dumps({'id':case['id'], **case['expected']}, separators=(',', ':'), allow_nan=False) + '\n' for case in cases))
    if [json.loads(line) for line in casefile.read_text().splitlines()] != cases:
        raise ValueError('Persisted fixtures differ')
    artifacts = {'fixtures': sha(casefile), 'expected': sha(expectedfile)}
    if prepare_only:
        receipt = {'version':'0.135.1','build':'0898d5e3','phase':phase,'cases':len(cases),
            'target_executed':False,'source_sha256':frozen_sources,'artifact_sha256':artifacts,
            'coverage':coverage(cases),'original_wasm_sha256':SOURCE_SHA}
        (output / 'prepared.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
        if source_hashes() != frozen_sources or sha(SOURCE) != SOURCE_SHA:
            raise ValueError('Source changed during preparation')
        return receipt, output
    manifestfile = output / 'manifest.json'
    modulefile = output / manifest['module_file']
    manifest_sha, module_sha = sha(manifestfile), sha(modulefile)
    if manifest['version'] != '0.135.1' or manifest['build'] != '0898d5e3' or module_sha != manifest['module_sha256']:
        raise ValueError('Approved module identity differs')
    resultfile, stderr = output / 'candidates135-original-results.jsonl', output / 'candidates135-stderr.log'
    process = run_fixed_oracle(output, casefile, resultfile, stderr)
    artifacts.update({'results':sha(resultfile),'stderr':sha(stderr)})
    rows = [json.loads(line) for line in resultfile.read_text().splitlines()]
    expected_ids = list(range(len(cases)))
    received_ids = [row.get('id') for row in rows]
    complete = received_ids == expected_ids and len(set(received_ids)) == len(expected_ids)
    failures = []
    for row in rows:
        if type(row.get('id')) is not int or not 0 <= row['id'] < len(cases):
            raise ValueError('Original result ID outside corpus')
        case = cases[row['id']]
        actual = {key: row[key] for key in case['expected']}
        if actual != case['expected']:
            failures.append({'id':case['id'],'group':case['group'],'input':case['input'],
                'expected':case['expected'],'actual':actual})
        if row['host_calls']:
            raise ValueError('Host calls occurred')
    mismatchfile = output / 'candidates135-mismatches.json'
    mismatchfile.write_text(json.dumps(failures, indent=2, allow_nan=False)+'\n')
    artifacts['mismatches'] = sha(mismatchfile)
    runtimefile = output / 'candidates135-runtime.json'
    runtime = json.loads(runtimefile.read_text()) if runtimefile.exists() else None
    if runtimefile.exists():
        artifacts['runtime'] = sha(runtimefile)
    receipt = {'version':'0.135.1','build':'0898d5e3','phase':phase,'status':
        'passed scoped metadata comparison' if process['exit_code']==0 and complete and not failures else 'failed; preserve evidence',
        'original_wasm_sha256':SOURCE_SHA,'original_full_function':2159,'original_full_function_executed':bool(rows),
        'original_internal_callees_unchanged':True,'only_changed_source_section':7,'dependency_shims':[],
        'cases':len(cases),'result_rows':len(rows),'complete_unique_ordered_ids':complete,
        'mismatch_cases':len(failures),'fields_compared':['candidate_count1912','candidate variant/id/tier/owned_index/kinds/gold',
            'RNG1720 four u32','phase2587','selection_kind2585','generation_counter2400'],
        'coverage':coverage(cases),'process':process,'runtime':runtime,
        'source_sha256':frozen_sources,'module_sha256':module_sha,'module_manifest_sha256':manifest_sha,
        'artifact_sha256':artifacts,'evidence_directory':str(output),
        'limitations':['Only ordinary kind0 candidate selection metadata is compared; allocated UI strings/payload+0..59 are not independently reconstructed.',
            'mode2582=1 skips world35513 through original guard; flag2566=0 skips6310 text path.',
            'Original1480 display formatting/talent/tier callees and1203 notification generation may run but are not independently accepted.',
            'Synthetic allocated state uses explicit snapshots, original static definitions, existing RNG words and empty unrelated auxiliaries.',
            'No seed initialization, actual reroll action, XP→selection integration, kinds1/2, new-ability application, UI or full game acceptance.',
            'Finite deterministic corpus does not prove every float/input/RNG state.']}
    if source_hashes()!=frozen_sources or sha(SOURCE)!=SOURCE_SHA or sha(manifestfile)!=manifest_sha or sha(modulefile)!=module_sha:
        raise ValueError('Frozen sources/module changed during comparison')
    if sha(casefile)!=artifacts['fixtures'] or sha(expectedfile)!=artifacts['expected'] or sha(resultfile)!=artifacts['results']:
        raise ValueError('Persisted fixture/expected/result changed during comparison')
    (output / 'candidates135-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    (ROOT / 'reports/2026-11-01-candidates0135-spec.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    md = f'''# 官方0.135.1 kind0候选metadata完整函数差分

目标 **0.135.1 / 0898d5e3**，原件SHA256 `{SOURCE_SHA}`。本次phase `{phase}`：{len(cases)}个预先落盘fixture，原件输出{len(rows)}行，metadata mismatch {len(failures)}，有序唯一ID覆盖 `{complete}`，状态 `{receipt['status']}`。

实际执行原完整2159及其全部可达原callee，只有export节增加批准role；没有替换内部函数、shim、app start。固定Node22.23.4、32MiB WASM上限、heap512MiB、owned进程60秒上限、原91941 allocator；全部878 host imports拒绝，实际host调用见receipt。

比较候选数量、new/upgrade/gold变体、ID、tier、owned index、kind-byte序列、gold；另比较最终四word RNG、phase2587、kind2577、counter2392。每例fresh分配8192B G，32例换instance；mode2582=1使原guard跳过世界35513，2558=0跳过6310。完整fixture、预生成独立期望、原结果、stderr、mismatches与前后source hash在`{output.relative_to(ROOT)}`。

输入覆盖与候选实际出现统计以JSON为准；full corpus加入所有114种owned定义、全部职业byte、level/luck、3/4卡flags、owned6上限、权重/随机边界、caps、execution9/11特殊interval、blocked/banished、demonic effect/summon、tier4多kind和shuffle拒绝抽样。pilot仅用于最初两例确认真实80B tail解码，不能称为完整候选接受。

**独立实现边界**：只接受kind0 metadata/RNG/三个控制字段。80B展示payload+0..59、世界/通知表现、种子初始化、实际reroll动作、kind1/2、XP→选择组合、new能力应用、UI与完整游戏均未因此完成。原1480/1203等显示/天赋函数虽然保持原件并可能执行，其语义没有被此metadata差分独立验收。
'''
    (ROOT / 'reports/2026-11-01-candidates0135-spec.md').write_text(md)
    return receipt, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('pilot','full'), default='pilot')
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--prepare-only', action='store_true', help='Write independent fixtures/expected only; no WASM execution')
    args = parser.parse_args()
    receipt, output = check(args.phase, args.directory, args.prepare_only)
    print(json.dumps({'evidence':str(output),'phase':args.phase,'cases':receipt['cases'],
        'target_executed':not args.prepare_only,'mismatch_cases':receipt.get('mismatch_cases'),
        'status':receipt.get('status','prepared only')}))
    if not args.prepare_only and receipt['status']!='passed scoped metadata comparison':
        raise SystemExit('Original2159 comparison failed; retain evidence and report before any model changes')


if __name__ == '__main__':
    main()
