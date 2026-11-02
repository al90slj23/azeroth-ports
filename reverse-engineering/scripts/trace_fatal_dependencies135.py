#!/usr/bin/env python3
"""Bounded static source proof for921 incoming order and run-summary owners."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
ORIGINAL_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    before = digest(Path(__file__))
    assert digest(ORIGINAL) == ORIGINAL_SHA
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('fatal-dependencies135-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    con = sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    windows = {
        921: [('entry_phase_and_queue_headers', 1, 131), ('incoming_queue', 7410, 7510),
              ('planned_outgoing_drain', 8415, 8465), ('planned_cast_drain', 9215, 9300),
              ('mechanic_rechecks_phase', 9452, 9498)],
        1073: [('phase_guard', 1, 21), ('ordinary_registry_skip', 1330, 1380),
               ('hp_and_taken', 1588, 1620), ('ring_append', 3277, 3450),
               ('post_history_callbacks_and_hp_reread', 3803, 3905), ('fatal_lives0', 4588, 4612)],
        5620: [('mode0_stop_and_defeat', 1, 82)],
        17119: [('auxiliary_and_claim_stop_tail', 339, 362)],
        1560: [('source_zero_words', 622, 650), ('empty_ring_header', 988, 1000),
               ('counter_unaligned_copy', 1038, 1073), ('final_copy', 2738, 2761)],
        914: [('dead_unit_classification', 5482, 5550), ('kills_and_elites', 5728, 5753),
              ('boss_counter', 6892, 6910), ('guardian_counter', 7284, 7303)],
        20660: [('entry_guard', 1, 64), ('chest_counter', 250, 305)],
        28796: [('earned_gold', 74, 145)],
        910: [('entry_guard', 1, 64), ('branch_specific_phase_guard', 1203, 1238)],
    }
    functions = {}
    with (PROFILE / 'official-0.135.1-full.wat').open('rb') as wat, ORIGINAL.open('rb') as wasm:
        for index, selected in windows.items():
            row = dict(con.execute('select * from functions where idx=?', (index,)).fetchone())
            wat.seek(row['wat_start'])
            text = wat.read(row['wat_end'] - row['wat_start'])
            lines = text.decode().splitlines()
            assert lines[0].startswith(f'  (func (;{index};)')
            wasm.seek(row['body_start'])
            body = wasm.read(row['body_end'] - row['body_start'])
            (out / f'{index}.wat').write_bytes(text)
            calls = [dict(callee=r['callee'], relative_line=r['wat_line']-row['wat_line']+1)
                     for r in con.execute('select * from calls where caller=? order by wat_offset', (index,))
                     if r['callee'] in (1073, 914, 1453, 910, 984, 5620, 17119, 17217, 16340, 1938)]
            accesses = [dict(operation=r['operation'], offset=r['field_offset'], relative_line=r['wat_line']-row['wat_line']+1)
                        for r in con.execute('select * from memops where function_idx=? order by wat_offset', (index,))
                        if r['field_offset'] in (1084, 1088, 1092, 1096, 1100, 1104, 2587, 968, 972, 976, 980)]
            functions[str(index)] = dict(**row, body_sha256=hashlib.sha256(body).hexdigest(),
                wat_sha256=hashlib.sha256(text).hexdigest(), lines=len(lines), relevant_calls=calls,
                direct_field_accesses=accesses,
                windows={label: [dict(line=j+1, instruction=lines[j].strip())
                                 for j in range(a-1, min(b, len(lines)))] for label,a,b in selected})
    proof = dict(version='0.135.1', original_wasm_sha256=ORIGINAL_SHA,
        script_sha256=before, original_calls=0, full_profile_scan=False, sqlite_mode='ro', functions=functions,
        rules={
            '921_order': 'Unit planning and movement-message production precede the scratch124/128/132 incoming16 queue. Every queued entry calls1073 in order. Fatal does not break that loop. Later914/1453/910 queues still drain; their own phase/source guards apply.',
            '5620_order': 'Phase2587=4 is written before mode0 calls17119 then1938 defeat.17119 itself ends bycalling17217 and16340, soNPC thenauxiliary thenclaim stop allprecede the defeatnotification.5620 direct17217/16340 belowitsmode0branch belong to nonzero mode.',
            'history': '1073 writesHP1440 andf64taken992, resolves history source and appendsG968/972/976/980 ring48 before retaliation984 and finalHP reread. Initial header cap0 ptr4 head0 count0 is explicitly produced by1560 scratch1056/1064.',
            'counter_initialization': 'G1084..1104 at scratch1172..1195 are copied unaligned from scratch2807..2830; zero stores2795..2838 precede these copies. No running value is inferred from records.',
            'ordinary_event': '914 accepted new death incrementsG1084; rawU416 lowbit incrementsG1088. Headless cast_events.apply_hit invokes on_death for every applied+dead result before continuing the next hit.',
            '910_after_fatal': 'No universal phase guard at910 entry: index/count andunit marker guard precede the dispatch. The one2587 readisinside a specificcastbranch, not an unconditional return.Queuedguardian casts afterfatal therefore requiretheir actualbranch, not a blanketno-op.',
            'other_counters': '914 has later nonordinary branches incrementingG1096 boss andG1092 guardian. G1104 increments in20660. These continuations are not represented by the ordinary counter adapter.',
            'existing_owners': 'G1432 is current progression.level; G1100 is cumulative collected gold CurrencyState.earned (13528796), not currently availablegold.'},
        boundaries=['No full921 differential or naturalfatal acceptance in this static proof',
                    'No claim1073 callbacks complete; keyed/source stats/rawbuff13/item22/984 remain separate inputs and continuations',
                    'No restored boss/guardian/chest wholeproducer implied by finding its counter increment',
                    'No hero text inferred from the absence of an EmptyOpeningInput field'])
    path = out / 'proof.json'
    path.write_text(json.dumps(proof, indent=2) + '\n')
    assert digest(Path(__file__)) == before
    print(json.dumps(dict(directory=str(out), proof_sha256=digest(path), original_calls=0)))


if __name__ == '__main__':
    main()
