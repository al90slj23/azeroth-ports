#!/usr/bin/env python3
"""Expected-first full38553 scheduled32 consumer; no natural producer claim."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import argparse, json, math, os, signal, struct, subprocess, sys, time
sys.dont_write_bytecode = True
from incoming139_tools import ROOT, SOURCE, SOURCE_SHA, save, sha
from build_frame_deadline139_oracle import build
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.frame_systems139 import ScheduledSpellVector139, PendingFrameSystem139, tick_scheduled_spells139

NODE = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def closure():
    names = set(production_sources135(ROOT, 'core_spec.frame_systems139')) | {
        'scripts/' + name for name in (
            'check_frame_deadline139.py', 'build_frame_deadline139_oracle.py',
            'run_frame_deadline139_oracle.mjs', 'production_closure135.py', 'source_closure137.py')}
    while True:
        try:
            return sorted(names), verify_local_source_closure(sorted(names))
        except AssertionError as error:
            pair = error.args[0]
            assert isinstance(pair, tuple) and len(pair) == 2 and pair[1] not in names
            names.add(pair[1])


def row(guid=0, due=0, spell=0, xyz=(0, 0, 0), opaque=0xa5a55a5a):
    return struct.pack('<Q6I', guid, due, spell, *xyz, opaque).hex()


def corpus(full):
    cases, labels = [], []

    def add(label, records, updates, phase=1, count=None):
        cases.append(dict(id=len(cases), count=len(records) if count is None else count,
                          phase=phase, storage32_hex=records, updates=updates))
        labels.append(label)

    zero, one = f.from_float(0), f.from_float(1)
    add('empty-capacity-zero', [], [zero, one])
    add('inclusive-equal-guid0', [row(due=one, spell=123, xyz=(f.SIGN, f.NAN, f.INF))], [one, one])
    add('future-then-equal-full-guid', [row(0x0102030405060708, one, 0xffffffff,
                                           (0x7f800001, 0xff800000, 0x80000001))], [zero, one])
    add('unsorted-stable-physical-moves', [row(j + 1, due, j + 100, (j, j + 1, j + 2), j + 300)
                                         for j, due in enumerate((f.from_float(2), zero, one, f.NAN))],
        [one, f.from_float(2), f.INF])
    add('all-ready-vector-reserve', [row(j + 1, zero, j + 200) for j in range(9)], [zero], phase=0)
    add('spare-physical-storage-not-active', [row(j, zero, j) for j in range(4)], [one], count=0, phase=5)
    if full:
        for n in (1, 3, 4, 5, 8, 9, 16, 17, 33):
            add('all-ready-capacity-boundary-' + str(n),
                [row(0x0102030405060708 if j % 2 else j, zero, 0x10203040 + j,
                     (0x80000000 + j, 0x7fc00000 + j, j), 0x12340000 + j) for j in range(n)],
                [zero, one])
        for phase in (0, 1, 5):
            for guid in (0, 1, 0x100, 0x8000000000000000, 0x0102030405060708, 0xffffffffffffffff):
                add('phase-and-packed-guid', [row(guid, one, 592, (zero, f.SIGN, f.INF))], [one], phase=phase)
        special = (0xff800000, 0x80000000, 0, 1, 0x3f7fffff, one, 0x3f800001,
                   0x7f7fffff, f.INF, f.NAN, 0x7f800001, 0xffc00123)
        for due in special:
            add('raw-due-special-' + format(due, '08x'), [row(0x1000000000000001, due, 0x7fffffff)],
                [0xff800000, zero, one, f.INF, f.NAN])
        for now in special:
            add('raw-now-special-' + format(now, '08x'),
                [row(j + 1, due, 1000 + j, (due, now, f.SIGN)) for j, due in enumerate(special)], [now])
        add('repeated-clock-duplicate-guid-and-spares',
            [row(55, due, 71 + j, (j, f.SIGN, f.NAN), 0x55550000 + j)
             for j, due in enumerate((one, zero, f.from_float(.5), one, f.NAN, zero, zero, zero))],
            [zero, f.from_float(.5), one, f.from_float(2), one], count=5)
    assert 0 < len(cases) <= 128
    return cases, labels


def expected(case):
    vector = ScheduledSpellVector139(tuple(tuple(bytes.fromhex(s)) for s in case['storage32_hex']), case['count'])
    packets, cap, stages = [], 0, []
    for now in case['updates']:
        result = tick_scheduled_spells139(vector, now)
        vector = result.vector
        for opcode, capacity, payload in result.packets:
            if len(packets) == cap:
                cap = max(4, cap * 2)
            packets.append(dict(opcode=opcode, capacity=capacity, payload_hex=payload))
        stages.append(dict(count=vector.count, capacity=len(vector.storage),
                           storage=[bytes(r).hex() for r in vector.storage],
                           packet_capacity=cap, packet_count=len(packets), packets=list(packets),
                           removed_indices=list(result.removed_indices)))
    return stages


def model_only_checks():
    # Unconsumed opaque cells can remain Unknown and still move verbatim.
    a = tuple(bytes.fromhex(row(1, f.from_float(2), 2)))
    b = tuple(bytes.fromhex(row(3, 0, 4)))[:28] + (None,) * 4
    result = tick_scheduled_spells139(ScheduledSpellVector139((b, a), 2), 0)
    assert result.vector.storage == (a, a) and result.vector.count == 1
    opaque = tuple(bytes.fromhex(row(1, f.from_float(2), 2)))[:28] + (None,) * 4
    result = tick_scheduled_spells139(ScheduledSpellVector139((b, opaque), 2), 0)
    assert result.vector.storage == (opaque, opaque)
    # Future rows do not consume Unknown GUID/spell/XYZ cells.
    future = (None,) * 8 + tuple(struct.pack('<I', f.from_float(2))) + (None,) * 20
    result = tick_scheduled_spells139(ScheduledSpellVector139((future,), 1), 0)
    assert result.vector.count == 1 and not result.packets
    rejected = 0
    for value, now in ((future, f.from_float(2)), ((None,) * 32, 0)):
        try:
            tick_scheduled_spells139(ScheduledSpellVector139((value,), 1), now)
        except PendingFrameSystem139:
            rejected += 1
    assert rejected == 2
    return dict(layer='pure_model_selfcheck', unknown_rejections=rejected,
                opaque_move_checks=2, future_unknown_unconsumed=1, original_calls=0)


def missing(pid, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=('pilot', 'full'), default='pilot')
    args = ap.parse_args()
    files, edges = closure()
    sources = {n: sha(ROOT / n) for n in files}
    assert sha(SOURCE) == SOURCE_SHA and sha(NODE) == NODE_SHA
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('frame-deadline139-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    manifest = build(out)  # Current original bodies bound before model expectations.
    opened, forbidden = [], []
    model_phase = True

    def audit(event, arguments):
        if model_phase and event == 'open' and isinstance(arguments[0], (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(arguments[0])).resolve()
            opened.append(str(p))
            if p.suffix.lower() in ('.wasm', '.wat', '.memory', '.exe') or '/originals/' in str(p):
                forbidden.append(str(p))
                raise RuntimeError('Original denied during expectation')

    sys.addaudithook(audit)
    try:
        cases, labels = corpus(args.phase == 'full')
        rows = [dict(id=c['id'], stages=expected(c)) for c in cases]
        checks = model_only_checks()
    finally:
        model_phase = False
    assert not forbidden and sources == {n: sha(ROOT / n) for n in files}
    for n, value in sources.items():
        q = out / 'source-snapshot' / n
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes((ROOT / n).read_bytes())
        assert sha(q) == value
    save(out / 'inputs.json', cases)
    save(out / 'case-labels.json', labels)
    save(out / 'expected.json', rows)
    save(out / 'expectation-read-audit.json', dict(opened=opened, forbidden=forbidden, layer='Python open audit'))
    save(out / 'model-only-checks.json', checks)
    save(out / 'config.json', dict(input_file=str(out / 'inputs.json'), input_sha256=sha(out / 'inputs.json')))
    frozen = {n: sha(out / n) for n in ('inputs.json', 'case-labels.json', 'expected.json', 'manifest.json',
                                       'config.json', manifest['module_file'], 'expectation-read-audit.json',
                                       'model-only-checks.json')}
    save(out / 'prepared.json', dict(sources=sources, source_import_edges=edges, frozen=frozen,
                                    expected_before_original_execution=True, original_input_contains_expected=False,
                                    natural_queue_producer=False))
    cmd = [str(NODE), '--max-old-space-size=512', '--wasm-max-mem-pages=512',
           str(ROOT / 'scripts/run_frame_deadline139_oracle.mjs'), str(out), str(out / 'config.json')]
    start = time.monotonic()
    with (out / 'actual.jsonl').open('w') as stdout, (out / 'stderr.log').open('w') as stderr:
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, start_new_session=True)
        save(out / 'owned-start.json', dict(pid=p.pid, pgid=p.pid, command=cmd, deadline_seconds=60))
        try:
            code = p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            code = p.returncode
    terminal = dict(pid=p.pid, pgid=p.pid, exit_code=code, seconds=time.monotonic() - start,
                    pid_missing=missing(p.pid), pgid_missing=missing(p.pid, True))
    save(out / 'owned-terminal.json', terminal)
    actual = [json.loads(s) for s in (out / 'actual.jsonl').read_text().splitlines()]
    differences, counts = [], Counter()

    def eq(cid, field, want, got):
        counts['assertions'] += 1
        if want != got:
            counts['differences'] += 1
            if len(differences) < 100:
                differences.append(dict(case=cid, field=field, expected=want, actual=got))

    def u(raw, at):
        return struct.unpack_from('<I', raw, at)[0]

    for c, want, got in zip(cases, rows, actual):
        cid = c['id']
        eq(cid, 'id', cid, got['id'])
        eq(cid, 'stage-count', len(want['stages']), len(got['stages']))
        before = got['before']
        for field in ('count', 'capacity', 'storage'):
            eq(cid, 'before.' + field, {'count': c['count'], 'capacity': len(c['storage32_hex']),
                                       'storage': c['storage32_hex']}[field], before[field])
        eq(cid, 'before.packet-count', 0, before['packet_count'])
        eq(cid, 'before.packets', [], before['packets'])
        previous = bytes.fromhex(before['raw_game2592_hex'])
        for i, (w, a) in enumerate(zip(want['stages'], got['stages'])):
            prefix = 'step' + str(i) + '.'
            for field in ('count', 'capacity', 'storage', 'packet_capacity', 'packet_count', 'packets'):
                eq(cid, prefix + field, w[field], a[field])
            input_game = bytes.fromhex(a['input_game2592_hex'])
            anticipated_input = bytearray(previous)
            struct.pack_into('<I', anticipated_input, 2352, c['updates'][i])
            eq(cid, prefix + 'clock-only-driver-patch', bytes(anticipated_input).hex(), input_game.hex())
            output = bytes.fromhex(a['raw_game2592_hex'])
            anticipated = bytearray(input_game)
            struct.pack_into('<I', anticipated, 1840, w['count'])
            struct.pack_into('<I', anticipated, 1880, w['packet_capacity'])
            struct.pack_into('<I', anticipated, 1888, w['packet_count'])
            if u(input_game, 1880) != w['packet_capacity']:
                # Allocator addresses are observed only; all other bytes are predicted.
                anticipated[1884:1888] = output[1884:1888]
                counts['observed_new_packet_pointer_words'] += 1
                eq(cid, prefix + 'new-packet-pointer-nonzero', True, u(output, 1884) > 0)
            eq(cid, prefix + 'whole-Game-conservation', bytes(anticipated).hex(), output.hex())
            eq(cid, prefix + 'queue-count-word', w['count'], u(output, 1840))
            eq(cid, prefix + 'queue-capacity-word', len(c['storage32_hex']), u(output, 1832))
            eq(cid, prefix + 'queue-pointer-stable', u(previous, 1836), u(output, 1836))
            eq(cid, prefix + 'packet-count-word', w['packet_count'], u(output, 1888))
            counts['target38553_calls'] += 1
            counts['removed_rows'] += len(w['removed_indices'])
            counts['physical_storage_bytes_compared'] += len(c['storage32_hex']) * 32
            counts['game_bytes_compared'] += 2592
            previous = output
        for name in ('profile', 'query'):
            eq(cid, name + '-unchanged', got[name + '_before_hex'], got[name + '_after_hex'])
        eq(cid, 'stack-after', 1048576, got['stack_after'])
    for n, value in sources.items():
        assert sha(ROOT / n) == value
    for n, value in frozen.items():
        assert sha(out / n) == value
    runtime = json.loads((out / 'runtime.json').read_text()) if (out / 'runtime.json').exists() else None
    if runtime:
        eq('runtime', '38553-count', sum(len(c['updates']) for c in cases), runtime['full38553_calls'])
        eq('runtime', '1600-setup', len(cases), runtime['setup1600_calls'])
        eq('runtime', 'fresh-instances', len(cases), runtime['fresh_instances'])
        eq('runtime', 'host-import-calls', 0, runtime['actual_host_calls'])
        eq('runtime', 'snapshot-restores', 0, runtime['snapshot_restores'])
        for j, r in enumerate(runtime['returns']):
            eq('runtime', 'return' + str(j), (1048576, 1048576, True),
               (r['before'], r['after'], r['returned']))
    save(out / 'differences.json', differences)
    artifacts = {n: sha(out / n) for n in ('actual.jsonl', 'runtime.json', 'stderr.log', 'prepared.json',
                                         'owned-start.json', 'owned-terminal.json', 'differences.json') if (out / n).exists()}
    comparison = dict(version='0.139.0', build='f79c5e2b4', phase=args.phase,
                      kind='full-original-function-scheduled32-consumer', cases=len(cases), completed_cases=len(actual),
                      target_entry_calls=sum(len(c['updates']) for c in cases),
                      setup1600_calls=len(cases), differences=counts['differences'], counts=dict(counts),
                      sources_before=sources, sources_after=sources, source_import_edges=edges,
                      frozen=frozen, artifacts=artifacts, runtime=runtime, process=terminal,
                      original_function_bodies_unchanged=True, natural_queue_producer=False,
                      full_mainloop_frames=0, native_windows_execution=False, complete_games=0,
                      limits=['Explicit complete32B scheduled queue carriers; natural producer not restored.',
                              'Original1600 borrowed flat query/profile0 setup, not a completeApp/opening.',
                              'Packet Vec allocation pointers observed; all other2592B predicted relative to actual input.',
                              'RawXYZ including NaN payloads copied as bits; due/now NaN prevents removal.',
                              'Unknown consumption rejected in separate pure model checks, not original target cases.',
                              'Pilot and failed runs preserved and excluded from any later formal acceptance.'])
    save(out / 'comparison.json', comparison)
    print(json.dumps(dict(directory=str(out), comparison_sha256=sha(out / 'comparison.json'),
                          cases=len(cases), completed=len(actual), differences=counts['differences'],
                          counts=dict(counts), first=differences[:3], process=terminal)), flush=True)
    if code or len(actual) != len(cases) or not runtime or counts['differences']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
