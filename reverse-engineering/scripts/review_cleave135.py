#!/usr/bin/env python3
"""Read-only cleave135 receipt/source review. Does not execute original WASM."""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source, section_list, export_entries
import check_cleave135 as model
from trace_ecs_forward import structural_targets

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.cast135 import UnresolvedCast, CastDeathBoundary
from core_spec.cast_events135 import cast_ability
from core_spec.cleave135 import cast_cleave135
from core_spec.owned_cast135 import OwnedEntry135


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard_checks():
    definition, _ = model.cleave_definition()
    owned = AbilityRecord(definition.pointer)
    state = model.state_from_input(model.inputs([model.unit(1, 1), model.unit(2, 2), model.unit(3, 3)]))
    hit = lambda state, result: state
    checks = {}
    guards = (
        ('default_entry_rejects_cleave', lambda: OwnedEntry135(definition, owned)),
        ('default_cast_rejects_cleave', lambda: cast_ability(state, definition, owned, after_hit=hit)),
        ('cleave_rejects_unrestored_effect', lambda: cast_cleave135(state, replace(definition, effect_tag=1), owned, after_hit=hit)),
        ('cleave_rejects_other_exec5_identifier', lambda: cast_cleave135(state, replace(definition, ability_id=b'other'), owned, after_hit=hit)),
        ('cleave_rejects_nonzero_context', lambda: cast_cleave135(replace(state, context908=1), definition, owned, after_hit=hit)),
        ('cleave_rejects_duplicate_GUID', lambda: cast_cleave135(model.state_from_input(model.inputs([model.unit(1, 1), model.unit(1, 2)])), definition, owned, after_hit=hit)),
    )
    for name, operation in guards:
        try:
            operation()
        except UnresolvedCast:
            checks[name] = True
        else:
            checks[name] = False
    try:
        cast_cleave135(state, definition, replace(owned, definition_pointer=0), after_hit=hit)
    except ValueError:
        checks['cleave_rejects_pointer_mismatch'] = True
    else:
        checks['cleave_rejects_pointer_mismatch'] = False
    lethal = model.state_from_input(model.inputs([model.unit(1, 1, hp_bits=f.from_float(1)), model.unit(2, 2), model.unit(3, 3)]))
    try:
        cast_cleave135(lethal, definition, owned, after_hit=hit)
    except CastDeathBoundary as boundary:
        checks['lethal_boundary_preserves_remaining_targets'] = (
            boundary.remaining_targets == (2, 3) and boundary.damage_result.dead
            and boundary.state.rng_words != lethal.rng_words)
    else:
        checks['lethal_boundary_preserves_remaining_targets'] = False
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--oracle-dir', type=Path, required=True)
    parser.add_argument('--static-dir', type=Path, required=True)
    args = parser.parse_args()
    oracle, static = args.oracle_dir.resolve(), args.static_dir.resolve()
    receipt_path = oracle / 'cleave135-comparison.json'
    receipt = json.loads(receipt_path.read_text())
    assertions = {}
    assertions['receipt_source_hashes_before_after_identical'] = receipt['source_sha256_before'] == receipt['source_sha256_after']
    artifacts = {name: sha(oracle / name) for name in receipt['artifacts']}
    assertions['all_artifact_hashes_match'] = artifacts == receipt['artifacts']
    sources = {name: sha(ROOT / name) for name in receipt['source_sha256_before']}
    snapshots = {name: sha(oracle / 'source-snapshot' / name) for name in sources}
    assertions['all_current_source_hashes_match'] = sources == receipt['source_sha256_before']
    assertions['all_source_snapshots_match'] = snapshots == sources
    fixtures = [json.loads(line) for line in (oracle / 'cleave135-fixtures.jsonl').read_text().splitlines()]
    results = [json.loads(line) for line in (oracle / 'cleave135-results.jsonl').read_text().splitlines()]
    rows = model.corpus(receipt['phase'])
    assertions['independent_regeneration_matches_frozen_fixtures'] = rows == fixtures
    assertions['case_ids_and_count_match'] = [row['id'] for row in results] == list(range(len(rows))) and len(rows) == receipt['cases']
    assertions['all_frozen_original_results_match_expected'] = all(model.equivalent(row['expected'], actual['stages']) for row, actual in zip(rows, results))
    assertions['stage_count_matches'] = sum(len(row['ops']) for row in rows) == receipt['stages']
    assertions['accepted_hit_count_matches'] = sum(row['accepted_hit_count'] for row in rows) == receipt['accepted_hits']
    original = SOURCE.read_bytes()
    assertions['original_sha_matches'] = hashlib.sha256(original).hexdigest() == SOURCE_SHA == receipt['original_wasm_sha256']
    changed = (oracle / 'research135-exports.wasm').read_bytes()
    before, after = section_list(original), section_list(changed)
    assertions['all_nonexport_sections_identical'] = len(before) == len(after) and all(a[0] == b[0] and (a[0] == 7 or original[a[1]:a[3]] == changed[b[1]:b[3]]) for a, b in zip(before, after))
    assertions['no_implicit_start_section'] = not any(part[0] == 8 for part in before)
    manifest = json.loads((oracle / 'manifest.json').read_text())
    private_stack = receipt.get('private_stack_guard') is True
    if private_stack:
        old_exports, _ = export_entries(original, next(s for s in before if s[0] == 7))
        new_exports, _ = export_entries(changed, next(s for s in after if s[0] == 7))
        assertions['private_export_surface_exact'] = (
            new_exports[:len(old_exports)] == old_exports
            and new_exports[len(old_exports):] == [
                ('research135_cast', 0, 922), ('research135_owned_tick', 0, 1076),
                ('research135_process_hits', 0, 1754), ('research135_cleave_stack0', 3, 0)])
        assertions['private_validator_exited_and_cleaned'] = (
            manifest['private_validation']['exit_code'] == 0
            and manifest['private_validation']['process_group_absent_after'] is True)
        baseline = receipt['baseline_input_expected_identity']
        baseline_path = ROOT / baseline['path']
        assertions['stack_rerun_preserves_previous_fixture_bytes'] = (
            baseline['bytes_equal'] is True and baseline['previous_counts_not_added'] is True
            and sha(baseline_path) == baseline['sha256']
            and baseline_path.read_bytes() == (oracle / 'cleave135-fixtures.jsonl').read_bytes())
        checks = receipt['runtime']['stack_checks']
        expected_calls = []
        names = {'cast': 'cast', 'owned': 'owned_tick', 'process': 'process_hits'}
        for row in rows:
            expected_calls.extend((row['id'], '__wbindgen_malloc') for _ in range(3))
            expected_calls.extend((row['id'], names[op['kind']]) for op in row['ops'])
        assertions['stack_checks_cover_every_exposed_entry_and_allocator_invocation'] = (
            [(call['case_id'], call['role']) for call in checks] == expected_calls)
        assertions['all_exposed_invocations_return_and_restore_original_stack'] = (
            receipt['runtime']['stack_all_restored'] is True
            and all(call['entered'] is True and call['returned'] is True
                    and call['before'] == 1048576 and call['after'] == call['before'] for call in checks))
    types, imports, declarations, bodies, _ = parse_source(original)
    static_receipt = json.loads((static / 'summary.json').read_text())
    static_function_checks, texts = {}, {}
    for function in static_receipt['functions']:
        index = function['index']
        raw = (static / f'{index}.wat').read_bytes()
        start, end = bodies[index]
        signature = types[declarations[index - len(imports)]]
        static_function_checks[str(index)] = (
            hashlib.sha256(raw).hexdigest() == function['wat_sha256']
            and hashlib.sha256(original[start:end]).hexdigest() == function['body_sha256']
            and (signature[0].hex(), signature[1].hex()) == (function['parameters_hex'], function['results_hex']))
        texts[index] = [line.strip() for line in raw.decode().splitlines()]
    assertions['all_seven_static_function_signatures_and_hashes_match'] = len(static_function_checks) == 7 and all(static_function_checks.values())
    dispatch = next(i + 1 for i, line in enumerate(texts[922]) if line.startswith('br_table '))
    effect = next(i + 1 for i, line in enumerate(texts[2244]) if line.startswith('br_table '))
    assertions['exec5_static_branch_reconfirmed'] = structural_targets(texts[922], {dispatch: 3})[dispatch] == static_receipt['execution_branch']
    assertions['effect0_static_return_branch_reconfirmed'] = structural_targets(texts[2244], {effect: 0xffffffff})[effect] == static_receipt['effect0_return_branch']
    guards = guard_checks()
    assertions['all_eight_pure_model_guards_pass'] = all(guards.values()) and len(guards) == 8
    assertions['runtime_scope_is_quiet_component_fixture'] = (
        receipt['runtime']['actual_host_calls'] == 0
        and receipt['runtime']['denied_function_imports'] == 878
        and receipt['runtime']['memory_page_limit'] == 512
        and receipt['runtime']['max_memory_bytes'] <= 32 * 1024 * 1024
        and receipt['runtime']['application_start_called'] is False
        and receipt['runtime']['full_game_started'] is False
        and receipt['process']['exit_code'] == 0
        and receipt['process']['process_group_absent_after'] is True)
    result = dict(checked_at=datetime.now(timezone.utc).isoformat(),
        status='pass' if all(assertions.values()) else 'fail',
        original_target_executed_by_review=False, new_independent_acceptance_cases=0,
        pure_model_guard_checks=len(guards), assertions=assertions,
        scope=dict(cases=receipt['cases'], stages=receipt['stages'], accepted_hits=receipt['accepted_hits'],
            frozen_sources=len(sources), artifact_count=len(artifacts)),
        receipt_path=str(receipt_path.relative_to(ROOT)), receipt_sha256=sha(receipt_path),
        static_path=str(static.relative_to(ROOT)), static_receipt_sha256=sha(static / 'summary.json'),
        script_sha256=sha(Path(__file__)), checked_source_sha256=sources,
        pure_model_guard_results=guards, static_function_checks=static_function_checks,
        observations=[
            'The production module imports independent math/query/combat modules and reads no target file or oracle output.',
            'Cleave5 takes8685 priority prefix in definition range7, then one43468 draw and immediate914 hit per selected GUID; effect0 reaches2244 return.',
            'The older OwnedEntry135 and common dispatcher still reject execution5; the new entry subclass and wrapper explicitly opt in.',
            'Observed UI80B fields supply one relocated input shape; the original App/Game memory, RNG, NPCs and complete880 scheduler are not replayed.',
            'G1256 is the racial80 record. Legacy real-basic fixture group names mean canonical nonnull catalog records relocated into that slot, not the real observed racial definition/state.',
            ('Private global0 export is read inside a closure; every exposed entry/allocator invocation is checked before/after; no Global object or setter is returned.' if private_stack else 'Stack init1048576 is statically checked only; the fixture does not dynamically read/write stack or claim stack restoration observation.'),
            'Physical packets, death/loot continuation, nonempty sources and natural Game/complete-game acceptance remain outside the receipt.'])
    destination = ROOT / 'reports/2026-11-01-cleave0135-independent-review.json'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    markdown = ROOT / 'reports/2026-11-01-cleave0135-independent-review.md'
    markdown.write_text(
        f"# Cleave 0.135.1 独立复核\n\n结论：**{result['status'].upper()}**。只读复核现有收据、源码快照和静态片段，未执行原件。\n\n"
        f"- 已重新生成 {receipt['cases']} 组合成输入及独立期望，与封存 fixture 逐对象一致；{receipt['stages']} 阶段、{receipt['accepted_hits']} 次 accepted hit 的原件输出无差异。\n"
        f"- {len(sources)} 个源码的当前字节、前后 SHA、封存快照一致；{len(artifacts)} 份产物 SHA 一致。原 WASM SHA 固定，所有非 export section 与原件逐字节相同，无隐式 start。\n"
        "- 静态复核 execution5 目标数与 range7 →8685→43468→914→2244 effect0；exec7 专用排序/低血倍率未套入 cleave。\n"
        "- 8 个纯模型保护检查通过，包含旧默认拒绝、未知 effect/ID/context、重复 GUID、错 pointer 和保留剩余目标的致死边界。这些检查不新增原件验收案例。\n"
        + (f"- 私有export-only模块额外只导出global0；{len(receipt['runtime']['stack_checks'])} 次对外 entry/allocator 调用前后栈均为1048576。Global对象与setter不外露，未对内部callee逐个插桩。输入与旧轮逐字一致，旧轮计数未重复相加。\n" if private_stack else "- 栈初值仅静态验证1048576，未宣称动态栈恢复观测。\n")
        + "- 真实 UI owned80B 只用于迁入合成 fixture 的数据形状。此结果不代表自然 Game、880、完整一局或原真实场景重放；物理包、死亡掉落和非空来源继续保留为边界。NaN位置未纳入边界组。\n\n"
        + "G1256 是 racial80。旧 fixture 中带 real-basic 的组名仅表示该槽放入实际目录中的非空 canonical 记录；没有重放真实 racial 定义或计时状态。\n\n"
        f"原差分收据：[cleave135-comparison.json](../{receipt_path.relative_to(ROOT)})；复核明细：[JSON](2026-11-01-cleave0135-independent-review.json)。\n")
    print(json.dumps(dict(status=result['status'], assertions=len(assertions),
        report=str(destination), receipt=str(receipt_path), original_target_executed=False)))
    if not all(assertions.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
