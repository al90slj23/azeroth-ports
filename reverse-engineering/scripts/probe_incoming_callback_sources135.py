#!/usr/bin/env python3
"""Observe independent typed sources beforeAI; never prove omitted producers.

Uses the frozen first-rune model probe without changing its source or feeding
any observation back. Source changes include cooldown/live backing changes.
No original runtime, captured Game or post-target oracle result is read.
"""
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'reconstruction')]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normalize(value):
    if isinstance(value,bytes):return dict(bytes_hex=value.hex())
    if isinstance(value,dict):return{key:normalize(item)for key,item in value.items()}
    if isinstance(value,(tuple,list)):return[normalize(item)for item in value]
    return value


def main():
    import core_spec.headless135 as headless
    import probe_run_summary135 as probe
    from production_closure135 import production_sources135
    files=set(production_sources135(ROOT,'core_spec.headless135',
        'core_spec.opening_handoff135','core_spec.run_summary135',
        'core_spec.incoming_history135','core_spec.incoming_source135'))
    files.update(('scripts/probe_incoming_callback_sources135.py',
        'scripts/probe_run_summary135.py','scripts/check_opening_combat135.py',
        'scripts/motion_route135.py'))
    before={name:sha(ROOT/name)for name in sorted(files)}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('incoming-callback-sources135-model-observer-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    old=headless._ai_phase
    observations=[]
    def observe(state,delta):
        level=state.collection.level
        shape=normalize(dict(sources=asdict(level.sources),
            owned=[dict(ability_id=normalize(row.ability_id),record80_hex=row.record.to_bytes().hex())
                   for row in level.choice_inputs.owned],
            racial80_hex=state.racial.to_bytes().hex(),
            player_sources=None if state.player_sources is None else dict(
                live_capacity=state.player_sources.live.capacity,
                live_count=state.player_sources.live.count,
                live_storage=state.player_sources.live.storage,
                live_auxiliary_origins=state.player_sources.live_auxiliary_origins),
            state_live_records=state.live_records,
            unspecified_live_words=state.unspecified_live_words,
            state_incoming_modifiers=[asdict(row)for row in state.incoming.modifiers]))
        raw=json.dumps(shape,sort_keys=True,separators=(',',':')).encode()
        observations.append(dict(frame=state.frames,stats=asdict(level.stats),
            progression=asdict(level.progression),
            phase2587=level.phase2587,flags2576=level.flags2576,
            gate2572=level.gate2572,flags2573=level.flags2573,
            heal_gate387=level.heal_gate387,
            source_shape_sha256=hashlib.sha256(raw).hexdigest(),shape=shape,
            unowned={'original_G2056_36B_vector':None,'original_G2028_8B_item_vector':None},
            observation_limit='headless._ai_phase currently supplies modifiers=() andincoming_item_effects=(); these are not independently recovered producers'))
        return old(state,delta)
    headless._ai_phase=observe
    try:probe.main()
    finally:headless._ai_phase=old
    assert all(sha(ROOT/name)==value for name,value in before.items())
    assert len(observations)==921 and observations[-1]['frame']==921, 'Incomplete pre-AI observation retained as failed attempt'
    report=dict(kind='pure_model_typed_source_observation_not_original_differential',
        original_calls=0,observations=observations,source_sha256=before,source_unchanged=True,
        input=dict(class_byte=1,race_byte=1,region_index=0,app_lcg_seed_u64=0,object_id_u64=42),
        limits=['No data is fed back into the model','Model empty tuples are not evidence of original source-vector initialization/absence',
                'G2056/G2028 full physical owners are absent from HeadlessState; explicit null is unknown, not an empty vector',
                'Any new callbacks predicate must recover actual producer provenance independently'])
    path=out/'sources.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(source_observer_directory=str(out),source_observer_sha256=sha(path),
        frames=len(observations),last_frame=observations[-1]['frame'],original_calls=0)))


if __name__=='__main__':main()
