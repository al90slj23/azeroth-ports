#!/usr/bin/env python3
"""Fresh full921 world AI components; no snapshots or original-output inputs."""
from collections import Counter
from dataclasses import asdict
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA
from build_distance_map135_oracle import build_distance_map135
from build_upgrade134_oracle import sha
from ai_world135_inputs import (load_asset_world135, asset_world_description135,
    controlled_world135, ASSET_WORLD, HASHES)
from core_spec import binary32 as f
from core_spec.ai135 import AiFrame135
from core_spec.ai_world135 import update_world_ordinary_units135
from core_spec.distance_map135 import update_distance_map135
from core_spec.incoming135 import input_from_dict
from core_spec.record_cells135 import cells135, u32, u64, put_u32, put_u64, encode_row

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
BASE = ROOT / 'evidence/full0135-oracle-20261101T044817.224194Z/ai135-fixtures.jsonl'
FIELDS = ('armor_1392_bits', 'armor_cap_1572_bits', 'nearby_reduction_1444_bits', 'hp_1528_bits',
    'shield_1532_bits', 'barrier_1536_bits', 'shield_source_1344', 'shield_source_remaining_1348_bits',
    'reserve_768_bits', 'absorbed_740_bits', 'maximum_shield_744_bits', 'last_hit_1648_bits')


def map_projection(path):
    return None if path is None else dict(sha256=hashlib.sha256(struct.pack('<' + str(len(path.values_u16)) + 'H', *path.values_u16)).hexdigest(),
        field24=path.field24, start_index=path.start_index, length=len(path.values_u16))


def corpus(world, full):
    base = json.loads(BASE.read_text().splitlines()[0])
    npc = base['input']['records'][0]; assert u32(npc, 284) == 5415572
    opening = json.loads((ASSET_WORLD / 'opening.json').read_text())
    player = tuple(opening['player_xyz']); rows = []

    def add(group, offsets, *, description=None, steps=1, in_flight=False, angles=None, player_override=None):
        geometry = world if description is None else controlled_world135(description)
        xyz = player if player_override is None else tuple(player_override)
        incoming_raw = dict(base['input']['incoming']); incoming_raw['mode_2574'] = 0
        incoming = input_from_dict(incoming_raw); records = []
        for index, (dx, dy, dz) in enumerate(offsets):
            raw = cells135(npc)
            xx, yy = f.add(xyz[0], f.from_float(dx)), f.add(xyz[1], f.from_float(dy))
            h = geometry.height(xx, yy); zz = f.add(h.value_bits if h.found else xyz[2], f.from_float(dz))
            for off in (316, 328):
                for j, word in enumerate((xx, yy, zz)): put_u32(raw, off + j * 4, word)
            put_u32(raw, 340, 0); put_u32(raw, 344, f.from_float(1) if in_flight else 0)
            put_u32(raw, 348, 0); put_u32(raw, 352, f.from_float(.2)); put_u32(raw, 400, 0)
            put_u32(raw, 396, f.from_float(0 if angles is None else angles[index % len(angles)]))
            put_u64(raw, 112, (u64(npc, 112) + index) & 0xffffffffffffffff)
            records.append(encode_row(raw))
        initial = tuple(records); expected, trace, routing = [], [], []
        path, updated, sequence, packets = None, 0, 123, 0
        for step in range(steps):
            now, dt = f.from_float(.1 + step * .1), f.from_float(.1)
            refreshed = update_distance_map135(geometry.nav, xyz[:2], now, previous=path, updated_at_bits=updated)
            path, updated = refreshed.distance_map, refreshed.updated_at_bits
            result = update_world_ordinary_units135(AiFrame135(tuple(records), now, dt, xyz, incoming,
                other_incoming_sources_absent=True), geometry, distance_map=path)
            records, incoming = result.records, result.incoming
            movements = []
            for movement in result.movement_geometry:
                sequence = (sequence + 1) & f.MASK
                value = asdict(movement); value['target_id'] = str(value['target_id']); value['sequence'] = sequence
                movements.append(value)
            packets += len(result.attacks) + len(result.movements)
            output = dict(records=list(records), **{key:getattr(incoming, key) for key in FIELDS})
            output.update(incoming_total_992_bits=struct.pack('>d', incoming.incoming_total_992).hex(), sequence=sequence,
                packet_count=packets, rng_words=[1, 2, 3, 4], distance_map=map_projection(path),
                distance_map_updated_at_bits=updated, movement_geometry=movements)
            expected.append(output); trace.append(dict(now_bits=now, dt_bits=dt, player_xyz_bits=xyz)); routing.extend(result.routing)
        rows.append(dict(id=len(rows), group=group, world=asset_world_description135() if description is None else description,
            records=list(initial), incoming=incoming_raw, max_hp_bits=f.from_float(10000), sequence=123,
            distance_map_updated_at_bits=0, steps=trace, expected=expected, diagnostic_routing=routing))

    add('pilot-real-parsed-world-chase', [(15, 0, 0)])
    add('pilot-real-parsed-world-multiple', [(-20, 10, 5), (25, -10, -4)], angles=(1, 3))
    def controlled(byte=1, primary=None):
        width = 16; nav = bytearray(width * width)
        for y in range(width - 2): nav[y * width + 7] = byte
        return dict(kind='controlled_query_world', nav=dict(hex=bytes(nav).hex(), origin_xy_bits=[0, 0], width=width),
            primary=primary, fallback_height_bits=f.from_float(68), flat_height_bits=f.from_float(23) if primary is None else None)
    add('pilot-controlled-flow-height-separation', [(10, 0, 50)], description=controlled(), player_override=(f.from_float(2), f.from_float(5), f.from_float(99)))
    if not full:
        return json.loads(json.dumps(rows))
    for dx, dy in ((-60, 0), (-45, 35), (-30, -30), (0, 40), (20, 20), (35, -35), (55, 10), (0, -60)):
        add('real-parsed-world-nonflat-and-obstacles', [(dx, dy, 7)], angles=(2.5,))
    add('real-parsed-world-ten-frames', [(15, 0, 1), (-15, 5, -2), (0, 20, 4)], steps=10, angles=(0, 1, 3))
    add('real-parsed-world-contact-stop', [(1, 0, 0)], in_flight=True, steps=3)
    for byte in (0, 1, 2, 7, 255):
        add('controlled-nav-bit0-and-flow', [(10, 0, 50)], description=controlled(byte),
            player_override=(f.from_float(2), f.from_float(5), f.from_float(99)))
    add('controlled-flow-continuous', [(10, 0, 50)], description=controlled(), steps=15,
        player_override=(f.from_float(2), f.from_float(5), f.from_float(99)))
    primary = dict(width=9, origin_xy_bits=[0, 0], values_bits=[0x7fc00000] * 81)
    primary['values_bits'][4 * 9 + 4] = f.from_float(77)
    desc = controlled(0, primary); desc['nav'] = None
    add('controlled-packet-nearest-z-only', [(7, 1, 20)], description=desc,
        player_override=(f.from_float(1), f.from_float(1), f.from_float(99)))
    return json.loads(json.dumps(rows))


def unknown_opening_check(world):
    opening = json.loads((ASSET_WORLD / 'opening.json').read_text())
    base = json.loads(BASE.read_text().splitlines()[0]); incoming = input_from_dict(base['input']['incoming'])
    records = tuple(tuple(row) for row in opening['units']['storage'][:opening['units']['count']])
    xyz = tuple(opening['player_xyz']); now = f.from_float(.026)
    path = update_distance_map135(world.nav, xyz[:2], now).distance_map
    result = update_world_ordinary_units135(AiFrame135(records, now, now, xyz, incoming,
        other_incoming_sources_absent=True), world, distance_map=path)
    for before, after in zip(records, result.records):
        assert all(after[index] is None for index, value in enumerate(before) if value is None)
    return dict(kind='pure-model independent-opening None preservation, not original differential',
        rows=len(records), unknown_input_bytes=sum(value is None for row in records for value in row),
        unknown_bytes_preserved=True, records=result.records, movements=len(result.movements), original_calls=0)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot'); args = parser.parse_args()
    files = sorted({str(Path(m.__file__).resolve().relative_to(ROOT)) for m in tuple(sys.modules.values())
        if getattr(m, '__file__', None) and str(Path(m.__file__).resolve()).startswith(str(ROOT) + '/')}
        | {'scripts/check_ai_world135.py', 'scripts/run_ai_world135_oracle.mjs', 'scripts/ai_world135_packing.mjs', 'scripts/distance_map135_host.mjs', 'scripts/full135_host.mjs'})
    before = {name:sha(ROOT / name) for name in files}; world = load_asset_world135(); rows = corpus(world, args.phase == 'full')
    unknown = unknown_opening_check(world)
    out, manifest = build_distance_map135()
    for name in files:
        target = out / 'source-snapshot' / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes()); assert sha(target) == before[name]
    fixture = out / 'ai-world135-fixtures.json'; fixture.write_text(json.dumps(rows, separators=(',', ':'), allow_nan=False) + '\n')
    unknown_path = out / 'ai-world135-none-opening.json'; unknown_path.write_text(json.dumps(unknown, indent=2) + '\n')
    frozen = {p.name:sha(p) for p in (fixture, unknown_path, out / 'manifest.json', out / manifest['module_file'])}
    assert sha(RUNTIME) == RUNTIME_SHA and sha(SOURCE) == SOURCE_SHA
    command = [str(RUNTIME), '--max-old-space-size=512', '--wasm-max-mem-pages=512', str(ROOT / 'scripts/run_ai_world135_oracle.mjs'), str(out), str(fixture)]
    result, stderr = out / 'ai-world135-results.jsonl', out / 'ai-world135-stderr.log'; started = time.monotonic()
    with result.open('w') as stdout, stderr.open('w') as err:
        child = subprocess.Popen(command, stdout=stdout, stderr=err, start_new_session=True)
        try: code = child.wait(timeout=60)
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
    failures = [dict(id=c['id'], group=c['group'], expected=c['expected'], actual=a['stages']) for c, a in zip(rows, actual) if c['expected'] != a['stages']]
    mismatch = out / 'ai-world135-mismatches.json'; mismatch.write_text(json.dumps(failures, indent=2) + '\n')
    after = {name:sha(ROOT / name) for name in files}; assert before == after
    assert frozen == {p.name:sha(p) for p in (fixture, unknown_path, out / 'manifest.json', out / manifest['module_file'])}
    runtime = json.loads((out / 'ai-world135-runtime.json').read_text()); assert runtime['stack_all_restored']
    receipt = dict(version='0.135.1', build='0898d5e3', phase=args.phase, original_wasm_sha256=SOURCE_SHA,
        cases=len(rows), stages=sum(len(c['steps']) for c in rows), mismatch_cases=len(failures), source_sha256_before=before, source_sha256_after=after,
        independent_expected_before_original=True, original_snapshot_loaded=False,
        independent_world_input=dict(directory=str(ASSET_WORLD.relative_to(ROOT)), hashes=HASHES,
            context='already independently parsed451-asset world; not a new resource-production run'),
        groups=dict(Counter(c['group'] for c in rows)), routing=dict(Counter(branch for c in rows for _, branch in c['diagnostic_routing'])),
        none_opening_pure_model=dict(rows=unknown['rows'], unknown_input_bytes=unknown['unknown_input_bytes'], preserved=True, original_calls=0),
        runtime=runtime, process=dict(command=command, pid=child.pid, pgid=child.pid, exit_code=code,
            deadline_seconds=60, seconds=round(time.monotonic() - started, 3), process_group_absent_after=absent),
        artifacts={p.name:sha(p) for p in (fixture, unknown_path, result, stderr, mismatch, out / 'manifest.json', out / manifest['module_file'], out / 'ai-world135-runtime.json')},
        limitations=['Controlled fully known NPC row fixtures on independently parsed Elwynn world inputs, not natural Game/880.',
            'Independent opening None rows are pure-model only; never materialized into original input.',
            'Ordinary melee/local/finite/nonfatal source restrictions inherited; ranged/Boss/status/proc producers remain explicit unknown.',
            'Movement221 XYZ/duration/sequence projections compared; full hit/registry/aura packet semantics remain pending.',
            'Fixed0.135.1 only, no0.136 or complete-game acceptance.'])
    (out / 'ai-world135-comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), cases=len(rows), stages=receipt['stages'], mismatches=len(failures), routing=receipt['routing'], seconds=receipt['process']['seconds'])))
    if failures: raise SystemExit(1)


if __name__ == '__main__': main()
