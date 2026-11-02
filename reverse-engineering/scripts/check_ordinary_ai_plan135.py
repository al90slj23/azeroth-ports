#!/usr/bin/env python3
"""Structural plan-boundary selfcheck; not an original differential.

The separate unchanged check_demo_ai135 full corpus supplies the original
regression. These checks address the new scheduling interface: no incoming
execution in planning, no dropped attacks, late Aura order and retention of
the caller's explicitly supplied post-callback/stop backing.
"""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'reconstruction')]

from check_demo_ai135 import corpus, declaration, FIELDS
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from ai_world135_inputs import controlled_world135
from core_spec import binary32 as f
from core_spec.ai135 import AiFrame135
import core_spec.ai_world135 as ai_world
from core_spec.incoming135 import input_from_dict
from core_spec.record_cells135 import cells135, u32, u64, put_u32, put_u64, encode_row


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    scripts = ('check_ordinary_ai_plan135.py', 'check_demo_ai135.py',
        'build_demo_ai135_oracle.py', 'run_demo_ai135_oracle.mjs',
        'demo_ai135_host.mjs', 'ai_world135_packing.mjs',
        'build_distance_map135_oracle.py', 'build_full135_oracle.py',
        'build_upgrade134_oracle.py', 'production_closure135.py',
        'source_closure137.py', 'ai_world135_inputs.py')
    files = tuple('scripts/'+name for name in scripts) + production_sources135(
        ROOT, 'core_spec.ai_world135', 'core_spec.ai_motion135')
    edges = verify_local_source_closure(files)
    before = {name: sha(ROOT/name) for name in files}
    rows, _, _ = corpus(False)
    case = rows[2]  # Existing expired-contact/lateAura controlled input.
    base = cells135(case['records'][0])
    second = base.copy()
    put_u64(second,112,(u64(base,112)+1)&((1<<64)-1))
    records = (encode_row(base), encode_row(second))
    incoming = replace(input_from_dict(case['incoming']),hp_1528_bits=f.from_float(.125))
    frame = AiFrame135(records, f.from_float(10), f.from_float(.1),
        (0,0,0), incoming, other_incoming_sources_absent=True,
        known_demo_statuses=tuple(declaration(cells135(row)) for row in records))
    world = controlled_world135(case['world'])
    old_prefix = ai_world.resolve_incoming_prefix
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError('Planning must not execute incoming prefix')
    ai_world.resolve_incoming_prefix = forbidden
    try:
        plan = ai_world.plan_world_ordinary_units135(frame,world)
    finally:
        ai_world.resolve_incoming_prefix = old_prefix
    assert not calls
    assert frame.records == records and frame.incoming == incoming
    assert len(plan.attacks) == 2
    assert tuple(guid for guid,_ in plan.attacks) == tuple(u64(row,112) for row in records)
    assert all(getattr(plan.incoming,key)==getattr(incoming,key) for key in FIELDS)
    assert plan.incoming.incoming_total_992 == incoming.incoming_total_992
    assert plan.incoming.now_bits == frame.now_bits
    assert (plan.incoming.player_x_1504_bits,plan.incoming.player_y_1508_bits) == frame.player_xyz_bits[:2]
    assert len(plan.incoming.units) == 2
    assert len(plan.demo_expirations) == 2
    assert all(1160 in declaration(cells135(row)).aura_slots168 for row in plan.records)
    assert all(u32(row,360)==0 for row in plan.records)
    try:
        ai_world.drain_world_ordinary_plan135(plan)
    except ValueError as error:
        assert str(error) == 'Incoming callback/death boundary: before_unresolved_death'
    else:
        raise AssertionError('Default scalar adapter silently completed fatal incoming')
    # Explicit controlled post-stop-like bytes are inputs for this structural
    # check only: no real stop/terrain behavior or fatal callback is claimed.
    stopped = []
    for index,row in enumerate(plan.records):
        raw = cells135(row)
        for offset in (316,328):
            for axis in range(3):
                put_u32(raw,offset+axis*4,f.from_float(30+index*3+axis))
        put_u32(raw,340,frame.now_bits)
        put_u32(raw,344,0)
        stopped.append(encode_row(raw))
    stopped = tuple(stopped)
    post = replace(plan.incoming,phase_2579=4,hp_1528_bits=0)
    finished = ai_world.finish_world_ordinary_plan135(plan,post,records=stopped)
    assert finished.incoming is post
    assert finished.attacks == plan.attacks and finished.movements == plan.movements
    assert finished.movement_geometry == plan.movement_geometry
    for supplied,result in zip(stopped,finished.records):
        supplied,result = cells135(supplied),cells135(result)
        assert supplied[316:348] == result[316:348]
        assert all(a==b for index,(a,b) in enumerate(zip(supplied,result)) if not 168<=index<232)
        assert 1160 not in declaration(result).aura_slots168
    refusals = []
    for name,backing in (('changed_count',stopped[:1]),('changed_GUID_order',tuple(reversed(stopped)))):
        try:
            ai_world.finish_world_ordinary_plan135(plan,post,records=backing)
        except ValueError:
            refusals.append(name)
        else:
            raise AssertionError('Unrestored post-callback vector change accepted')
    after = {name:sha(ROOT/name) for name in files}
    assert before == after
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('ordinary-ai-plan135-selfcheck-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    for name,value in before.items():
        path=out/'source-snapshot'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((ROOT/name).read_bytes())
        assert sha(path)==value
    report = dict(kind='model_structural_selfcheck_not_original_differential',
        original_calls=0, source_sha256_before=before,source_sha256_after=after,
        local_source_import_edges=edges,
        checks=['planning makes zero incoming calls and does not mutate input',
                'two ordered contact attacks survive planning with unchanged HP/shield/totals',
                'input clock/playerXY and planned unit motions are retained',
                'early360 expiry is separate from late Aura removal',
                'default scalar drain retains fatal boundary',
                'explicit changed backing positions survive late Aura finish',
                'count/GUID-order changes reject instead of overwriting callback state'],
        refusals=refusals,
        boundaries=['Controlled post-stop-like bytes are supplied as structural inputs; no terrain/stop/fatal execution is claimed',
                    'No guardian ordering/full921/fatal whole-chain acceptance',
                    'Original compatibility requires the separate unchanged demo-AI regression'])
    path=out/'selfcheck.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),source_files=len(files),edges=len(edges),
        selfcheck_sha256=sha(path),original_calls=0)))


if __name__ == '__main__':
    main()
