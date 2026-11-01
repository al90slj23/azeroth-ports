#!/usr/bin/env python3
"""Independent135 distance-map generation, then complete921 zero-unit oracle."""
from dataclasses import asdict
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import struct
import subprocess
import sys
import time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA
from build_distance_map135_oracle import build_distance_map135
from build_upgrade134_oracle import sha
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.distance_map135 import (ProducedDistanceMap135, produce_distance_map135,
    update_distance_map135)
from resource_spec.world_query135 import NavGrid135

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
CAPTURE = ROOT / 'evidence/game-entry0135-probe-20261101T135403.797895Z/original_game.memory'


def corpus(full):
    rows = []
    def add(group, nav, ops, previous=None, updated=0):
        state, last, expected = previous, updated, []
        for xy, now in ops:
            result = update_distance_map135(nav, tuple(xy), now, previous=state, updated_at_bits=last)
            state, last = result.distance_map, result.updated_at_bits
            expected.append(dict(distance_map=asdict(state) if state else None,
                updated_at_bits=last, world_refcount=1, map_refcounts=[1, 1] if state else None,
                unit_count=0, packet_count=0))
        rows.append(dict(id=len(rows), group=group,
            nav=None if nav is None else dict(hex=nav.values.hex(), origin_xy_bits=list(nav.origin_xy_bits), width=nav.width),
            previous=asdict(previous) if previous else None, updated_at_bits=updated,
            ops=[dict(player_xy_bits=list(xy), now_bits=now) for xy, now in ops], expected=expected))

    def xy(x, y):
        return (f.from_float(x), f.from_float(y))
    nav = NavGrid135(bytes(25), (0, 0), 5)
    add('pilot-open-eight-way', nav, [(xy(2.5, 2.5), f.from_float(.026))])
    blocked = bytearray(25); blocked[13] = 1; blocked[17] = 2
    add('pilot-corner-blocked-nonzero', NavGrid135(bytes(blocked), (0, 0), 5), [(xy(2, 2), f.from_float(1))])
    add('pilot-refresh-gates-and-outside-clear', nav,
        [(xy(2, 2), 0), (xy(2.9, 2.9), f.from_float(100)),
         (xy(3, 2), f.from_float(.1)), (xy(3, 2), f.from_float(.2)),
         (xy(-1, 2), f.from_float(.3)), (xy(-1, 2), f.from_float(.4))])
    old = produce_distance_map135(nav, xy(2, 2))
    add('pilot-absent-nav-retains-map-clock', None, [(xy(3, 3), f.from_float(100))], old, f.from_float(7))
    if not full:
        return rows
    for width in (1, 2, 3, 4, 7, 20, 21):
        for x, y in ((0, 0), (width - .001, width - .001), (-.001, 0), (width, 0)):
            add('dimensions-origins-and-player-bounds', NavGrid135(bytes(width * width), xy(-20, 10), width),
                [(xy(x - 20, y + 10), f.from_float(10))])
    for mask in range(16):
        b = bytearray(9)
        for j, index in enumerate((1, 3, 5, 7)):
            b[index] = 2 if mask & (1 << j) else 0
        add('all-four-corner-constraints', NavGrid135(bytes(b), (0, 0), 3), [(xy(1, 1), 0)])
    for value in (1, 2, 7, 255):
        b = bytearray([value] * 25)
        add('blocked-seed-still-zero', NavGrid135(bytes(b), (0, 0), 5), [(xy(2, 2), 0)])
    rng = random.Random(0x1352368)
    for k in range(120):
        width = (3, 5, 8, 13, 24)[k % 5]
        b = bytes((rng.choice((1, 2, 7, 255)) if rng.random() < (k % 5) * .12 else 0) for _ in range(width * width))
        x, y = rng.randrange(width), rng.randrange(width)
        add('random-maze-eight-way-counts', NavGrid135(b, xy(-3, -5), width),
            [(xy(x - 3 + .125, y - 5 + .875), f.from_float(k))])
    for word in (0x3e4ccccc, 0x3e4ccccd, 0x3e4cccce, f.INF, 0x7fc00001):
        add('refresh-exact-binary32-point2', nav, [(xy(3, 2), word)], old, 0)
    for initial in (None, old):
        add('absent-nav-no-update', None, [(xy(-100, -100), f.from_float(100))], initial, f.from_float(7))
    # Short backing with width1 is never read: seed initialization does not
    # require an obstacle byte, and all eight neighbors are outside the grid.
    add('unread-empty-backing-width1', NavGrid135(b'', (0, 0), 1), [(xy(0, 0), 0)])
    return rows


def observed_nav_replay(out):
    """Seek only explicit source ranges; observed nav is input, map is expected."""
    G = 22624720 + 16
    ranges = []
    with CAPTURE.open('rb') as stream:
        def take(offset, size, label):
            stream.seek(offset); raw = stream.read(size)
            assert len(raw) == size
            ranges.append(dict(label=label, offset=offset, bytes=size, sha256=hashlib.sha256(raw).hexdigest()))
            return raw
        world = struct.unpack('<I', take(G + 2348, 4, 'world_rc'))[0]
        pmap, updated = struct.unpack('<2I', take(G + 2368, 8, 'distance_map_and_clock'))
        player = struct.unpack('<2I', take(G + 1416, 8, 'player_xy'))
        cap, pointer, length, ox, oy, width = struct.unpack('<6I', take(world + 32, 24, 'nav_header'))
        assert cap == length == width * width == 78400
        nav = NavGrid135(take(pointer, length, 'nav_input_bytes'), (ox, oy), width)
        strong, weak, mapcap, values, n, seed, reached = struct.unpack('<7I', take(pmap, 28, 'observed_map_header'))
        expected = struct.unpack('<' + str(n) + 'H', take(values, n * 2, 'observed_map_values'))
    produced = produce_distance_map135(nav, player)
    assert produced.start_index == seed and produced.field24 == reached and produced.values_u16 == expected
    proof = dict(kind='observed_nav_input_to_independent_map_output_not_world_or_Game_production',
        snapshot_path=str(CAPTURE.relative_to(ROOT)), snapshot_bytes=CAPTURE.stat().st_size,
        all_reads_explicit_seeks=True, total_source_bytes=sum(r['bytes'] for r in ranges), ranges=ranges,
        world_rc=world, old_map_rc=pmap, updated_at_bits=updated, player_xy_bits=list(player),
        width=width, cells=n, start_index=seed, field24=reached,
        max_cost=max(x for x in produced.values_u16 if x != 65535), full_map_u16_equal=True,
        source_map_not_used_as_production_input=True)
    (out / 'observed-nav-model-replay.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot'); args = parser.parse_args()
    files = sorted({str(Path(m.__file__).resolve().relative_to(ROOT)) for m in tuple(sys.modules.values())
        if getattr(m, '__file__', None) and str(Path(m.__file__).resolve()).startswith(str(ROOT) + '/')}
        | {'scripts/check_distance_map135.py', 'scripts/run_distance_map135_oracle.mjs', 'scripts/distance_map135_host.mjs', 'scripts/full135_host.mjs'})
    before = {name: sha(ROOT / name) for name in files}
    rows = corpus(args.phase == 'full')
    out, manifest = build_distance_map135()
    for name in files:
        target = out / 'source-snapshot' / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes()); assert sha(target) == before[name]
    observed = observed_nav_replay(out) if args.phase == 'full' else None
    fixture = out / 'distance-map135-fixtures.jsonl'
    fixture.write_text(''.join(json.dumps(c, allow_nan=False, separators=(',', ':')) + '\n' for c in rows))
    assert json.loads(json.dumps(rows)) == [json.loads(line) for line in fixture.read_text().splitlines()]
    frozen = {p.name: sha(p) for p in (fixture, out / 'manifest.json', out / manifest['module_file'])}
    assert sha(SOURCE) == SOURCE_SHA and sha(RUNTIME) == RUNTIME_SHA
    assert subprocess.check_output([str(RUNTIME), '--version'], text=True, timeout=5).strip() == 'v22.23.4'
    command = [str(RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512', str(ROOT / 'scripts/run_distance_map135_oracle.mjs'), str(out), str(fixture)]
    result, stderr = out / 'distance-map135-results.jsonl', out / 'distance-map135-stderr.log'; started = time.monotonic()
    with result.open('w') as stdout, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stdout, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=60)
        finally:
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            child.wait()
    try: os.killpg(child.pid, 0)
    except ProcessLookupError: absent = True
    else: absent = False
    assert code == 0 and absent, out
    actual = [json.loads(line) for line in result.read_text().splitlines()]
    assert [a['id'] for a in actual] == list(range(len(rows)))
    failures = [dict(id=c['id'], group=c['group'], expected=c['expected'], actual=a['stages']) for c, a in zip(rows, actual) if json.loads(json.dumps(c['expected'])) != a['stages']]
    mismatch = out / 'distance-map135-mismatches.json'; mismatch.write_text(json.dumps(failures, indent=2) + '\n')
    after = {name: sha(ROOT / name) for name in files}; assert before == after
    assert frozen == {p.name: sha(p) for p in (fixture, out / 'manifest.json', out / manifest['module_file'])}
    runtime = json.loads((out / 'distance-map135-runtime.json').read_text()); assert runtime['stack_all_restored'] is True
    receipt = dict(version='0.135.1', build='0898d5e3', phase=args.phase, original_wasm_sha256=SOURCE_SHA,
        cases=len(rows), stages=sum(len(c['ops']) for c in rows), mismatch_cases=len(failures),
        source_sha256_before=before, source_sha256_after=after, independent_expected_before_original=True,
        runtime=runtime, process=dict(command=command, pid=child.pid, pgid=child.pid, exit_code=code,
            deadline_seconds=60, seconds=round(time.monotonic() - started, 3), process_group_absent_after=absent),
        artifacts={p.name: sha(p) for p in (fixture, result, stderr, mismatch, out / 'manifest.json', out / manifest['module_file'], out / 'distance-map135-runtime.json')},
        observed_nav_model_replay=observed,
        limitations=['Pure explicit nav input producer; observed-nav replay does not prove independent world/bootstrap/Game production.',
            'Complete original921 component runs have zero unit vectors and no AI/combat/packet continuation.',
            'Finite player XY and at most1048576 grid cells; u16 sentinel-collision paths remain explicit unresolved.',
            'Fixed0.135.1 only; no0.136 acceptance or full880/complete game claim.'])
    (out / 'distance-map135-comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), cases=len(rows), stages=receipt['stages'], mismatches=len(failures), seconds=receipt['process']['seconds'])))
    if failures: raise SystemExit(1)


if __name__ == '__main__': main()
