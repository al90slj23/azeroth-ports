#!/usr/bin/env python3
"""Pure snapshot replay and independent byte/queue review; no WASM execution."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, hashlib, struct
from review_gameplay_phase135 import ROOT, ORIGINAL, ORIGINAL_SHA, sha, strict, norm, sections, bodies, core_closure, load_checker

BATCH = ROOT / 'evidence/full0135-oracle-20261101T071906.163112Z'
HELPER_TRACE = ROOT / 'evidence/effect-system135-delayed-static-20261101T071931.505004Z/trace.json'


def fp(word): return struct.unpack('<f', struct.pack('<I', word))[0]
def u(raw, off): return struct.unpack_from('<I', raw, off)[0]
def guid(raw, off=112): return struct.unpack_from('<Q', raw, off)[0]


def equal(want, actual, counts, path='root'):
    counts['strict_nodes'] += 1
    assert type(want) == type(actual), (path, type(want), type(actual))
    if isinstance(want, dict):
        assert want.keys() == actual.keys(), path
        for k in want: equal(want[k], actual[k], counts, path + '.' + k)
    elif isinstance(want, list):
        assert len(want) == len(actual), path
        for j, (a, b) in enumerate(zip(want, actual)): equal(a, b, counts, path + f'[{j}]')
    else: assert want == actual, (path, want, actual)


def independent_queue(before, projected, now, counts):
    rows = list(before.delayed_records); backing = list(before.delayed_storage)
    units = [bytearray.fromhex(x) for x in before.units]; index = 0; trap = False
    while index < len(rows):
        raw = bytes.fromhex(rows[index]); target_guid = guid(raw, 0)
        due = not fp(u(raw, 8)) > fp(now)
        if due and before.mode2582:
            owner = next((u(x, 280) for x in units if guid(x) == target_guid), 0)
            due = owner == before.local_peer2528
        if not due: index += 1; continue
        if index + 1 < len(rows): counts['nontrivial56_compactions'] += 1
        for j in range(index, len(rows) - 1): backing[j] = backing[j+1]
        rows.pop(index); counts['due_records_popped'] += 1
        tag = raw[49]
        if tag == 255: trap = True; counts['raw255_after_pop_traps'] += 1; break
        outer = next((j for j, x in enumerate(units) if guid(x) == target_guid and not u(x, 0) & 1), None)
        if outer is None: counts['missing_or_lowbit_target_pops'] += 1; continue
        assert tag in (35, 36, 37)
        counts['matched_tag' + str(tag)] += 1
        if tag == 37:
            own = next((j for j, x in enumerate(units) if guid(x) == target_guid and u(x, 0) != 1), None)
            if own is not None:
                spell = u(raw, 12); slot = next((j for j in range(16) if u(units[own], 168+4*j) == spell), None)
                if slot is not None:
                    if own != outer: counts['aura_independent_target_differs_from_outer'] += 1
                    if spell == 0: counts['aura_zero_spell_callbacks'] += 1
                    struct.pack_into('<I', units[own], 168+4*slot, 0); counts['first_slot_aura_callbacks'] += 1
    assert projected['entry_trap'] == trap
    assert projected['delayed_records'] == rows and projected['delayed_storage'] == backing
    full = b''.join(bytes.fromhex(x) for x in backing)
    assert hashlib.sha256(full).hexdigest() == projected['delayed_storage_sha256']
    for a, b in zip(units, projected['units']): assert a[168:232] == bytes.fromhex(b)[168:232]
    counts['full56_backing_bytes_checked'] += len(full)
    counts['full424_unit_bytes_compared'] += len(units)*424
    counts['independent_aura_bytes_checked'] += len(units)*64


def main():
    receipt_path = BATCH / 'effect-system135-comparison.json'; receipt = json.loads(receipt_path.read_text())
    frozen = receipt['source_sha256_before']; assert frozen == receipt['source_sha256_after']; snap = BATCH / 'source-snapshot'
    for n, h in frozen.items(): assert sha(snap / n) == h
    closure = core_closure(snap, ('effect_system135.py','spawn135_data.py')); assert set(closure) <= frozen.keys()
    drift = {n: dict(frozen=h,current=sha(ROOT/n)) for n,h in frozen.items() if sha(ROOT/n) != h}
    for name, h in receipt['artifacts'].items(): assert sha(BATCH/name) == h
    assert sha(BATCH/'manifest.json') == receipt['manifest_sha256']
    raw = ORIGINAL.read_bytes(); assert hashlib.sha256(raw).hexdigest() == ORIGINAL_SHA
    sec = sections(raw); code = bodies(raw, sec); module = (BATCH/'research135-exports.wasm').read_bytes()
    assert hashlib.sha256(module).hexdigest() == receipt['module_sha256']
    assert [(k,x) for k,x,_,_ in sec if k != 7] == [(k,x) for k,x,_,_ in sections(module) if k != 7]
    manifest = json.loads((BATCH/'manifest.json').read_text()); assert manifest['denied_function_import_count'] == 878
    assert len(manifest['roles']) == 1 and manifest['roles'][0]['index'] == 915
    role = manifest['roles'][0]; a,b = code[915-878]
    assert (a,b) == (role['body_start'],role['body_end']) and hashlib.sha256(raw[a:b]).hexdigest() == role['body_sha256']
    helper_trace = json.loads(HELPER_TRACE.read_text())
    helper_identity = []
    for helper in helper_trace['functions']:
        index = helper['index']; a,b = code[index-878]
        assert (a,b) == (helper['body_start'],helper['body_end'])
        assert hashlib.sha256(raw[a:b]).hexdigest() == helper['body_sha256']
        wat = HELPER_TRACE.parent/f'{index}.wat'
        assert sha(wat) == helper['wat_sha256']
        assert wat.read_text().splitlines()[0].strip() == helper['signature']
        helper_identity.append(dict(index=index,body_sha256=helper['body_sha256'],wat_sha256=helper['wat_sha256']))
    del raw,module
    author = load_checker(snap,'check_effect_system135.py','review_effect_system135_frozen_checker')
    cases = json.loads((BATCH/'effect-system135-fixtures.json').read_text()); regenerated = author.corpus(False)
    assert strict(cases,regenerated)
    guards = norm(author.guards()); assert strict(guards,json.loads((BATCH/'effect-system135-guards.json').read_text()))
    outputs = [json.loads(x) for x in (BATCH/'effect-system135-results.jsonl').read_text().splitlines()]
    assert [x['id'] for x in outputs] == list(range(500))
    counts = Counter(); kinds = Counter(); packet_bytes = 0; source_id_above_2pow53 = 0
    for case,out in zip(cases,outputs):
        equal(case['expected'],out['stages'],counts,f'case{case["id"]}')
        state = author.from_input(case['input']); source_id_above_2pow53 += state.source_id > 1<<53
        cumulative_codes = []; replay = []
        assert len(out['stages']) == len(out['physical_message_payloads'])
        for op,observed,physical in zip(case['ops'],out['stages'],out['physical_message_payloads']):
            state = author.replace(state,now_bits=op['now_bits'],**op.get('changes',{}))
            independent_queue(state,observed,op['now_bits'],counts)
            result = author.step_effect_system(state,op['dt_bits']); state = result.state
            assert result.status in ('delayed_prefix_projection','trap_invalid255_after_pop')
            cumulative_codes.extend(e[1] for e in result.events)
            prediction = dict(author.projection(state,cumulative_codes),entry_trap=result.status=='trap_invalid255_after_pop')
            equal(norm(prediction),observed,Counter(),f'actioncase{case["id"]}')
            assert len(physical) == len(cumulative_codes) and [p['opcode'] for p in physical] == cumulative_codes
            for p in physical:
                assert type(p['opcode']) is int and 0<=p['opcode']<=65535
                assert len(p['payload_hex'])%2==0; packet_bytes += len(bytes.fromhex(p['payload_hex']))
            assert observed['effect120_count'] == 0
            assert observed['rng_words'] == list(state.rng_words) and observed['spawn_counter2408'] == state.spawn_counter2408
            replay.append(norm(prediction)); counts['stages'] += 1
            if observed['entry_trap']: break
        assert strict(replay,case['expected'])
        kinds['actual_expected_trap_cases' if replay[-1]['entry_trap'] else 'normal_return_cases'] += 1
    assert (len(cases),counts['stages'],kinds['actual_expected_trap_cases'],kinds['normal_return_cases']) == (500,2121,117,383)
    assert frozen == {n:sha(snap/n) for n in frozen}
    assert receipt['runtime']['host_calls'] == 0 and receipt['runtime']['denied_imports'] == 878
    assert not receipt['runtime']['application_start_called'] and not receipt['runtime']['network_used'] and not receipt['runtime']['user_saves_accessed']
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('effect-system0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    reviewer_deps = (Path(__file__),ROOT/'scripts/review_gameplay_phase135.py')
    reviewer_sources = {str(p.relative_to(ROOT)):sha(p) for p in reviewer_deps}
    for p in reviewer_deps:
        dest=out/'reviewer-source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    review = dict(version='0.135.1',build='0898d5e3',reviewed_receipt=str(receipt_path.relative_to(ROOT)),reviewed_receipt_sha256=sha(receipt_path),
        original_sha256=ORIGINAL_SHA,status='passed within explicit empty120/special35,36,37 and raw255 trap domain',
        source_files=len(frozen),core_init_import_closure=closure,current_source_drift=drift,cases=500,stages=2121,case_outcomes=dict(kinds),
        strict_comparison=dict(counts),model_fixture_regeneration_equal=True,independent_action_replay_equal=True,original_results_strict_equal=True,
        regenerated_original_guard_cases=guards,all_nonexport_sections_identical=True,original915_role=role,
        static_helper_trace=str(HELPER_TRACE.relative_to(ROOT)),static_helper_trace_sha256=sha(HELPER_TRACE),
        independently_checked_helper_identities=helper_identity,reviewer_source_sha256=reviewer_sources,
        comparison_masks=[],nan_relaxation=False,source_ID_inputs_above_2pow53=source_id_above_2pow53,
        physical_payload_bytes_observed_in_cumulative_sidecars=packet_bytes,physical_wire_encoding_independently_restored=False,
        original_executed_by_reviewer=False,author_sources_modified_by_reviewer=False,reviewer_script_sha256=sha(Path(__file__)),
        limitations=receipt['limitations']+['Onlyopcode order checked for physical packets; neither payload geometry nor actorGUID wire encoding is independently proved.',
            'SourceID fixture strings are lossless input data; output message GUIDs are not decoded by this review.',
            'Expectedraw255trapcases are117separate post-pop originalunreachable outcomes, not117normal gameplayreturns.',
            'Fixture source/flatworld/empty120domain isexplicit; thiscomponent doesnotestablish real910/120producers orfull915/880 gameplay.'])
    (out/'review.json').write_text(json.dumps(review,indent=2)+'\n')
    wrapper=dict(review,evidence_directory=str(out.relative_to(ROOT)),review_sha256=sha(out/'review.json'))
    (ROOT/'reports/2026-11-01-effect-system0135-independent-review.json').write_text(json.dumps(wrapper,indent=2)+'\n')
    (ROOT/'reports/2026-11-01-effect-system0135-independent-review.md').write_text(
        '# 0.135.1 delayed56/915组件独立只读复核\n\n'
        '**500组、2121阶段通过**：383正常返回、117预期raw255在pop后真实unreachable。两类分开，未把trap计为正常玩法。冻结模型重生fixture及逐action重放严格匹配保留原件输出；5项未知域guard重放通过。\n\n'
        f'{len(frozen)}源快照及包含package init的完整闭包通过；原件全部非export节逐字节一致，915body/导出身份通过。当前漂移见JSON（若为共享导出扩展，只说明原批仍绑定其冻结源码）。\n\n'
        '另逐一核对915、4543及8个callee的原件body与WAT身份。独立字节算法复核due/owner筛选、稳定56B压缩与完整尾槽、raw255先pop后trap、outer marker低位与4543独立marker!=1查找，以及16槽aura首次匹配归零。完整56B backing与424B单位记录全部严格，无字段mask或NaN分类放宽。clock/due的NaN payload按原始字词保留。\n\n'
        '非空120B效果在进入前拒绝并原样保留；ordinary910只返回真实pop后的pending边界。特殊35/36仅有限平地且geometry来源显式缺席。RNG/counter保持、player XYZ/action词、消息opcode顺序均对照；原物理payload只保留侧录，未独立恢复wire、消息GUID或几何编码。真实producer、120/910、完整915/880及完整游戏仍未验收。\n\n'
        '没有重跑原件或修改作者源码。证据：`'+str((out/'review.json').relative_to(ROOT))+'`。\n')
    print(json.dumps(dict(directory=str(out),cases=500,stages=2121,outcomes=dict(kinds),counts=dict(counts),current_source_drift=list(drift))))


if __name__=='__main__':main()
