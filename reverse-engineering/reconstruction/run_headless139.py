#!/usr/bin/env python3
"""Run fixed139 raw resources -> independent world -> natural combat slice.

This is a headless research executable, not a rendered or complete game.
Only the verified first-choice Thunder path is admitted. Unsupported cards and
later systems produce an explicit boundary with the last committed state.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import ast
import hashlib
import json
import os
import struct
import sys
import time
sys.dont_write_bytecode = True

from resource_spec.asset_bundle139 import AssetBundle139, digest
from resource_spec.world139 import build_world139
from core_spec import binary32 as f
from core_spec.natural_spawn139 import prepare_natural_spawn139, advance_natural_spawn139, choose_natural_spawn_card139
from core_spec.frame_clock139 import FrameClock139, sample_frame_clock139, bits64, advance_game_clock139
from core_spec.growth139 import projection139 as growth_projection
from core_spec.world_pause139 import update_world_pause139
from core_spec.death139 import word139, guid139

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def source_closure():
    """Hash local Python modules, including imports nested in functions."""
    pending = [Path(__file__).resolve()]
    found = {}
    def local(parts):
        p = ROOT.joinpath(*parts)
        return p.with_suffix('.py') if p.with_suffix('.py').is_file() else p / '__init__.py'
    while pending:
        path = pending.pop()
        if path in found or not path.is_file():
            continue
        found[path] = digest(path)
        parts = list(path.relative_to(ROOT).with_suffix('').parts)
        package = parts[:-1]
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                names = [a.name.split('.') for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = package[:len(package)-node.level+1] if node.level else []
                if node.module:
                    base += node.module.split('.')
                names = [base] + [base + [a.name] for a in node.names if a.name != '*']
            else:
                continue
            for name in names:
                if not name or name[0] not in ('core_spec', 'resource_spec'):
                    continue
                for length in range(1, len(name)+1):
                    candidate = local(name[:length])
                    if candidate.is_file():
                        pending.append(candidate)
    return found


def state_projection(composition):
    state = composition.run
    actor = state.actor
    growth = actor.player.growth
    damage = actor.damage
    return dict(growth=growth_projection(growth), player_xyz=list(actor.player.player_xyz),
        live=dict(count=actor.player.live.count, storage=[list(r) for r in actor.player.live.storage]),
        aura=dict(count=actor.player.aura_state.count, storage=[list(r) for r in actor.player.aura_state.storage]),
        physical_NPC_count=state.units.count, physical_NPC_storage=[list(r) for r in state.units.storage],
        pickups_count=damage.pickups.count, pickups_storage=[list(r) for r in damage.pickups.storage],
        accounted_total_bits=str(damage.accounted_total_bits), killcost2420_bits=damage.killcost2420_bits,
        counter2408=damage.counter2408, movement_sequence2412=damage.movement_sequence2412,
        kills1084=damage.kills1084, gold1456=state.gold1456, earned1100=state.earned1100,
        ledger=dict(event_counter960=str(actor.ledger.event_counter960), accepted_count1016=str(actor.ledger.accepted_count1016), reason_totals64={key:str(value) for key,value in actor.ledger.reason_totals64}))


def world_digests(world):
    terrain = bytearray(struct.pack('<I', len(world.tiles)))
    for tile in world.tiles:
        terrain.extend(struct.pack('<5I', *tile.bounds_bits, len(tile.chunks)))
        for chunk in tile.chunks:
            terrain.extend(struct.pack('<HI', chunk.holes, len(chunk.vertices)))
            for vertex in chunk.vertices:
                terrain.extend(struct.pack('<3I', *vertex))
    blobs = dict(terrain=bytes(terrain), navigation=world.nav.values,
                 secondary=b''.join(struct.pack('<I', value) for value in world.secondary.values_bits))
    return {name:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for name,raw in blobs.items()}


def main():
    started_utc = datetime.now(timezone.utc).isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-map', required=True, type=Path)
    parser.add_argument('--acquisition-receipt', required=True, type=Path)
    parser.add_argument('--asset-root', type=Path, default=REPO)
    parser.add_argument('--seeds', type=int, nargs='+', default=[0])
    parser.add_argument('--steps', type=int, default=110)
    parser.add_argument('--choice', choices=['first', 'pause'], default='first')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if not 1 <= args.steps <= 6000 or not 1 <= len(args.seeds) <= 16 or any(not 0 <= seed <= 127 for seed in args.seeds):
        parser.error('Use 1..6000 steps and 1..16 seeds in 0..127')
    out = args.output.resolve()
    if not out.is_relative_to(Path('/Volumes/RuiRui4TB')):
        parser.error('Output must be on the 4T volume')
    out.mkdir(parents=True, exist_ok=False)
    sources = source_closure()
    assets = AssetBundle139(args.asset_map, args.acquisition_receipt, args.asset_root)
    before = {str(p.relative_to(ROOT)):h for p,h in sources.items()}
    for path, value in sources.items():
        p = out / 'source-snapshot' / path.relative_to(ROOT)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(path.read_bytes())
        if digest(p) != value:
            raise ValueError('Source changed while freezing')
    opened, forbidden = [], []
    allowed = set(sources) | {v[0] for v in assets.assets.values()} | {assets.manifest, assets.acquisition}
    def audit(event, values):
        if event != 'open' or not isinstance(values[0], (str, bytes, os.PathLike)):
            return
        p = Path(os.fsdecode(values[0])).resolve()
        mode, flags = values[1:3]
        reading = isinstance(mode, str) and 'r' in mode or mode is None and isinstance(flags, int) and flags & 3 == os.O_RDONLY
        if not reading:
            return
        if p.suffix.lower() in ('.wasm', '.wat', '.memory', '.exe'):
            forbidden.append(str(p))
            raise RuntimeError('Original program/memory denied in independent executable')
        if p.is_relative_to(REPO):
            admitted = p in allowed or p.is_relative_to(out)
            opened.append(dict(path=str(p), admitted=admitted))
            if not admitted:
                forbidden.append(str(p))
                raise RuntimeError('Read outside declared raw inputs/source: ' + str(p))
    sys.addaudithook(audit)
    started = time.monotonic()
    def progress(value):
        with (out / 'world-progress.jsonl').open('a') as stream:
            stream.write(json.dumps(value)+'\n')
    built = build_world139(assets, progress=progress)
    world = built.world
    cases = []
    with (out / 'states.jsonl').open('w') as stream:
        for seed in args.seeds:
            state = prepare_natural_spawn139(seed, world)
            clock = FrameClock139(1, bits64(0.0))
            selections, steps, error = [], 0, None
            boundary = 'requested_step_budget'
            stream.write(json.dumps(dict(seed=seed, step=-1, stage='opening', state=state_projection(state)))+'\n')
            for step in range(args.steps):
                try:
                    sample = sample_frame_clock139(clock, bits64((step+1)*.125))
                    now = advance_game_clock139(state.run.actor.player.growth.now_bits, sample.dt_bits, phase2587=1)
                    result = advance_natural_spawn139(state, now, sample.dt_bits, world, pause_world=update_world_pause139)
                except NotImplementedError as exc:
                    boundary, error = 'unrestored_next_component_branch', dict(type=type(exc).__name__, reason=str(exc), attempted_step=step)
                    break
                state, clock, steps = result.state, sample.state, step+1
                stream.write(json.dumps(dict(seed=seed, step=step, stage='components', state=state_projection(state)))+'\n')
                if state.run.actor.player.growth.phase2587 == 2:
                    cards = state.run.actor.player.growth.candidates
                    selection = dict(step=step, offered=[dict(variant=c.variant,ability_id=c.ability_id,tier=c.tier,kinds=list(c.kinds)) for c in cards], chosen_index=None)
                    selections.append(selection)
                    if args.choice == 'pause':
                        boundary = 'real_offered_choice_paused'
                        break
                    first = cards[0]
                    if first.variant != 'new' or first.ability_id != 'thunder_clap':
                        boundary = 'unrestored_real_first_card'
                        break
                    try:
                        selected, choice = choose_natural_spawn_card139(state, 0, world, resume_world=update_world_pause139)
                    except NotImplementedError as exc:
                        boundary, error = 'unrestored_selection_continuation', dict(type=type(exc).__name__,reason=str(exc),attempted_step=step)
                        break
                    if not choice.accepted:
                        raise ValueError('Actual offered first card was unexpectedly rejected')
                    state = selected
                    selection.update(chosen_index=0,raw_XP=choice.raw_XP_sum,scaled_XP=choice.scaled_XP_award)
                    stream.write(json.dumps(dict(seed=seed, step=step, stage='choice', state=state_projection(state)))+'\n')
            growth = state.run.actor.player.growth
            cases.append(dict(seed=seed, steps=steps, simulation_seconds=f.to_float(growth.now_bits), boundary=boundary, error=error,
                level=growth.level, xp=growth.xp, hp=f.to_float(growth.current_hp_bits), kills=state.run.actor.damage.kills1084,
                NPCs=state.run.units.count, live_NPCs=sum(word139(row,0)==0 for row in state.run.units.active),
                selections=selections, final_state=state_projection(state)))
    assets.verify_unchanged()
    after = {str(p.relative_to(ROOT)):digest(p) for p in sources}
    if before != after or forbidden:
        raise ValueError('Independent execution input/source boundary failed')
    receipt = dict(kind='independent_raw_assets_world_natural_combat139_headless_run', version='0.139.0', actual_build='f79c5e2b4',
        started_at_utc=started_utc, finished_at_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started,
        source_sha256_before=before, source_sha256_after=after, source_files=len(before),
        asset_map_sha256=assets.manifest_sha256, acquisition_receipt_sha256=assets.acquisition_sha256,
        loaded_assets=len(assets.loaded), raw_asset_bytes=assets.loaded_bytes, asset_requests=assets.requests,
        raw_assets_unchanged=True, world_artifacts=world_digests(world), cases=cases,
        states_sha256=digest(out/'states.jsonl'), original_program_executed=False, original_memory_read=False,
        pre_parsed_world_read=False, original_calls=0, full_main884_frames=0, complete_games=0,
        scope='Independentrawresources/Elwynnworld/defaultopening/2123→925→2890→952andfirstThunderchoiceonly;clock/UIpolicyexplicit. NoApp/render/audio/save/network/full14/full884/Windows/gameacceptance.',
        known_packet_stream_incomplete=True, early_stop_is_not_complete_game=True,
        read_audit_layer='Python open audit, not OS-wide syscall audit')
    (out/'read-audit.json').write_text(json.dumps(dict(opened=opened,forbidden=forbidden),indent=2)+'\n')
    (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),receipt_sha256=digest(out/'receipt.json'),loaded_assets=len(assets.loaded),raw_asset_bytes=assets.loaded_bytes,
        cases=[{k:v for k,v in c.items() if k!='final_state'} for c in cases],original_calls=0,complete_games=0),ensure_ascii=False),flush=True)

if __name__ == '__main__':
    main()
