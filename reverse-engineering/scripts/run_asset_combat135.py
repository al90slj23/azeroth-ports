#!/usr/bin/env python3
"""Independent451 assets -> world -> absent-companion opening -> combat tail.

The manifest supplies raw asset names/files/hashes, never a preparsed world or
an original memory image. This runner performs model self-checks only: zero
oracle cases, zero original program executions and zero full880 frames.
"""
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = Path('/Volumes/RuiRui4TB').resolve()

# Resolve the complete static closure before importing gameplay/resource code.
from production_closure135 import production_sources135

PRODUCTION_ENTRIES = (
    'core_spec.headless135', 'core_spec.opening_handoff135',
    'core_spec.profile_companions135', 'core_spec.special2376_notify135',
    'core_spec.spawn_position135_data', 'resource_spec.entry_resources135',
    'resource_spec.terrain135', 'resource_spec.world_placements135',
    'resource_spec.world_cache135',
)
HOST_SOURCES = ('scripts/run_asset_combat135.py', 'scripts/run_asset_world135.py',
                'scripts/production_closure135.py')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def external_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to(EXTERNAL):
        raise ValueError('Research inputs and outputs must stay on the4T volume')
    return path


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def source_files():
    return tuple(sorted(set(HOST_SOURCES + production_sources135(ROOT, *PRODUCTION_ENTRIES))))


def freeze_sources(output, files):
    before = {}
    for name in files:
        data = (ROOT / name).read_bytes()
        before[name] = hashlib.sha256(data).hexdigest()
        target = output / 'source-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if before != {name: sha(ROOT / name) for name in files}:
        raise RuntimeError('Production source changed while freezing; no model run started')
    write_json(output / 'source-before.json', before)
    return before


def state_summary(state):
    """Known/unknown-aware digests plus gameplay scalars, not oracle evidence."""
    from core_spec import binary32 as f
    from core_spec.record_cells135 import cells135, u32
    level, tail = state.collection.level, state.tail

    def owner(rows, stride, count):
        digest = hashlib.sha256()
        unknown = 0
        for row in rows:
            cells = cells135(row, stride)
            unknown += cells.count(None)
            # JSON null distinguishes unwritten cells from concrete zero bytes.
            digest.update(json.dumps(cells, separators=(',', ':')).encode())
            digest.update(b'\n')
        return dict(count=count, capacity=len(rows), backing_sha256=digest.hexdigest(),
                    unknown_backing_cells=unknown)

    path = state.distance_map
    result = dict(frames=state.frames, selections=state.selections,
        now_bits=level.stats.now_bits, seconds=f.to_float(level.stats.now_bits),
        phase2587=level.phase2587, progression=asdict(level.progression),
        current_hp_bits=level.stats.current_hp_bits,
        rng_words=list(level.rng_words), spawn_counter=state.collection.death.spawn_counter,
        message_sequence=state.collection.death.message_sequence,
        kill_cost_bits=state.collection.death.kill_cost_bits, budget_bits=state.budget_bits,
        gold=state.collection.currency.gold, earned=state.collection.currency.earned,
        outgoing_total_hex=struct.pack('>d', state.outgoing_total).hex(),
        incoming_total_hex=struct.pack('>d', state.incoming.incoming_total_992).hex(),
        alive_units=sum(u32(row, 0, 'asset-combat summary marker') == 0 for row in state.records),
        produced_packet_count=len(state.produced_packets),
        owned=[entry.ability_id for entry in level.choice_inputs.owned],
        owners={
            'units424': owner(state.unit_storage, 424, len(state.records)),
            'areas88': owner(state.area_storage, 88, len(state.areas)),
            'pickups56': owner(state.pickup_storage56, 56, state.pickup_active_count),
            'companions88': owner(tail.claims88_storage, 88, tail.claims88_count),
            'special40': owner(tail.special40_storage, 40, tail.special40_count),
            'windows8': owner(state.window_storage8, 8, state.window_count),
            'boundaries8': owner(state.boundary_storage8, 8, state.boundary_count)},
        distance_map=None if path is None else dict(start_index=path.start_index,
            reachable=path.field24, values_sha256=hashlib.sha256(
                b''.join(struct.pack('<H', value) for value in path.values_u16)).hexdigest()),
        distance_map_updated_at_bits=state.distance_map_updated_at_bits)
    result['summary_sha256'] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--frames', type=int, default=120)
    parser.add_argument('--class-byte', type=int, default=1)
    parser.add_argument('--race-byte', type=int, default=1)
    parser.add_argument('--app-seed', '--seed', type=lambda value: int(value, 0), default=0)
    parser.add_argument('--object-id', type=lambda value: int(value, 0), default=42)
    parser.add_argument('--navigation', action='store_true',
                        help='Enable special-target announcements; default is disabled.')
    args = parser.parse_args()
    if not 1 <= args.frames <= 1000:
        parser.error('frames must be1..1000')
    if not 0 <= args.app_seed < 1 << 64 or not 0 <= args.object_id < 1 << 64:
        parser.error('app-seed and object-id must be uint64')
    manifest = external_path(args.asset_manifest)
    output = external_path(args.output or ROOT / 'evidence' / datetime.now(timezone.utc).strftime(
        'asset-combat0135-modelselfcheck-%Y%m%dT%H%M%S.%fZ'))
    output.mkdir(parents=True, exist_ok=False)
    files = source_files()
    before = freeze_sources(output, files)

    # Import only after the full static production source set has been frozen.
    from run_asset_world135 import ManifestAssets135, build_asset_world135, write_world_outputs
    from core_spec import binary32 as f
    from core_spec.headless135 import from_opening_handoff, step_frame, select, projection
    from core_spec.opening135 import EmptyOpeningInput135
    from core_spec.opening_handoff135 import initialize_absent_companion_handoff, projection as opening_projection
    from core_spec.profile_companions135 import EmptyCompanionProfile135
    from core_spec.special2376_notify135 import SpecialLocale2376_135, ELWYNN_ENGLISH_NAMES

    began = time.monotonic()
    provider = None
    state = None
    inputs = None
    world_artifacts = None
    world_stats = None
    boundary = dict(kind='frame_budget', phase='combat', requested_frames=args.frames)
    execution_phase = 'asset_manifest'
    stage_count = 0
    action_count = 0
    failure = False
    with (output / 'stages.jsonl').open('w', buffering=1) as stages, \
            (output / 'progress.jsonl').open('w', buffering=1) as progress_log:
        def progress(*values, **fields):
            progress_log.write(json.dumps(dict(elapsed_seconds=time.monotonic() - began,
                phase=execution_phase, values=values, **fields), default=str) + '\n')

        def emit(kind, snapshot, **fields):
            nonlocal stage_count
            stages.write(json.dumps(dict(stage_index=stage_count, kind=kind,
                **fields, summary=state_summary(snapshot)), ensure_ascii=False) + '\n')
            stage_count += 1

        try:
            provider = ManifestAssets135(manifest)
            manifest_bytes = provider.path.read_bytes()
            if hashlib.sha256(manifest_bytes).hexdigest() != provider.manifest_sha256:
                raise ValueError('Asset manifest changed while initializing its provider')
            (output / 'asset-manifest.input.json').write_bytes(manifest_bytes)
            opening_input = EmptyOpeningInput135(args.class_byte, args.race_byte, 0,
                                                args.app_seed, args.object_id)
            asset_inputs = [dict(chain=name.decode('utf8'), file=str(path), bytes=size, sha256=digest)
                for name, (path, size, digest) in sorted(provider.assets.items())]
            inputs = dict(opening=asdict(opening_input), account_flags=[], companion_tags=[255, 255],
                navigation_enabled=args.navigation, locale='explicit_static_Elwynn_English_names',
                dt_bits=f.from_float(.1), requested_frames=args.frames,
                selection_policy='first_upgrade_else_index0',
                asset_manifest=str(provider.path), asset_manifest_sha256=provider.manifest_sha256,
                asset_inputs=asset_inputs,
                world_input='raw_assets_only_no_preparsed_world_or_original_memory')
            write_json(output / 'inputs.json', inputs)
            execution_phase = 'asset_world'
            built, tiles, selected = build_asset_world135(provider, progress=progress)
            world_artifacts = write_world_outputs(built, output)
            world_stats = dict(stats=built.stats, terrain_tiles=len(tiles),
                instances={phase: len(rows) for phase, rows in selected.items()})
            execution_phase = 'opening'
            handoff = initialize_absent_companion_handoff(opening_input, built.world,
                companion_profile=EmptyCompanionProfile135(()),
                title_utf8=b'Elwynn Forest', subtitle_utf8=b'')
            write_json(output / 'opening.json', opening_projection(handoff))
            state = from_opening_handoff(handoff, navigation_enabled=args.navigation,
                special_locale=SpecialLocale2376_135(ELWYNN_ENGLISH_NAMES))
            emit('opening', state, action_index=None)
            for frame in range(args.frames):
                execution_phase = 'frame'
                candidate, snapshots, status = step_frame(state, f.from_float(.1))
                if status != 'ordered_frame_projection':
                    boundary = dict(kind=status, phase=execution_phase, attempted_frame=frame,
                                    completed_frames=state.frames)
                    break
                state = candidate
                for kind, snapshot in snapshots:
                    emit(kind, snapshot, action_index=action_count)
                action_count += 1
                choices_this_frame = 0
                while state.collection.level.phase2587 == 2:
                    execution_phase = 'select'
                    if choices_this_frame >= 64:
                        boundary = dict(kind='selection_budget', phase=execution_phase,
                            completed_frames=state.frames, per_frame_choice_budget=64)
                        break
                    cards = state.collection.level.candidates
                    index = next((i for i, card in enumerate(cards) if card.variant == 'upgrade'), 0)
                    state, status = select(state, index)
                    emit('select', state, action_index=action_count, chosen_index=index, status=status)
                    action_count += 1
                    choices_this_frame += 1
                    if status not in ('running', 'choice_regenerated'):
                        boundary = dict(kind=status, phase=execution_phase,
                                        completed_frames=state.frames)
                        break
                if boundary['kind'] != 'frame_budget':
                    break
        except Exception as error:
            failure = not (isinstance(error, NotImplementedError) or
                execution_phase in ('frame', 'select') and isinstance(error, ValueError))
            boundary = dict(kind='model_boundary' if not failure else 'runner_error',
                phase=execution_phase, exception=type(error).__name__, reason=str(error),
                completed_frames=0 if state is None else state.frames,
                partial_failed_frame_available=False,
                stack=[dict(file=str(Path(row.filename).resolve()), line=row.lineno, function=row.name)
                       for row in traceback.extract_tb(error.__traceback__)])
            progress('stopped', boundary=boundary)

    if state is not None:
        write_json(output / 'final-state.json', projection(state))
        write_json(output / 'final-summary.json', state_summary(state))
    after = {name: sha(ROOT / name) for name in files}
    runtime_local_sources = set()
    for module in tuple(sys.modules.values()):
        value = getattr(module, '__file__', None)
        if value:
            path = Path(value).resolve()
            if path.is_relative_to(ROOT) and path.suffix == '.py':
                runtime_local_sources.add(str(path.relative_to(ROOT)))
    escaped_sources = sorted(runtime_local_sources - set(files))
    source_unchanged = before == after and not escaped_sources and source_files() == files
    assets_after = {}
    assets_unchanged = True
    if provider is not None:
        assets_unchanged = sha(provider.path) == provider.manifest_sha256
        for name in sorted(provider.loaded):
            path, size, digest = provider.assets[name]
            actual = sha(path)
            assets_after[name.decode('utf8')] = actual
            assets_unchanged = assets_unchanged and actual == digest and path.stat().st_size == size
    receipt = dict(kind='independent_raw_asset_to_world_opening_combat_modelselfcheck',
        model_version='0.135.1', model_actual_build='90898d5e3',
        mode='modelselfcheck', oracle_cases=0, new_original_differential_cases=0,
        full880_frames=0, original_program_executed=False, original_memory_read=False,
        original_wasm_executed=False, preparsed_world_input_read=False,
        inputs_sha256=sha(output / 'inputs.json') if inputs is not None else None,
        stages_sha256=sha(output / 'stages.jsonl'),
        final_state_sha256=sha(output / 'final-state.json') if state is not None else None,
        asset_manifest=str(manifest), asset_manifest_sha256=sha(manifest),
        declared_asset_files=0 if provider is None else len(provider.assets),
        loaded_asset_files=0 if provider is None else len(provider.loaded),
        decoded_asset_bytes=0 if provider is None else provider.decoded_bytes,
        asset_requests=[] if provider is None else provider.requests,
        loaded_assets_sha256_after=assets_after, assets_unchanged=assets_unchanged,
        world_artifacts=world_artifacts, world=world_stats,
        independent_frames=0 if state is None else state.frames,
        independent_selections=0 if state is None else state.selections,
        stage_summaries=stage_count, actions=action_count, boundary=boundary,
        source_sha256_before=before, source_sha256_after=after,
        escaped_runtime_sources=escaped_sources, production_source_unchanged=source_unchanged,
        elapsed_seconds=time.monotonic() - began,
        limitations=['Model self-check only; no original-side comparison was performed.',
            'External f32 clock scheduler and controlled ordered tail; full880/front/party/transport remain incomplete.',
            'Summaries cover opening and returned stages; an exception inside a frame exposes no partial frame state.',
            'None cells remain explicitly unknown; zero oracle cases cannot establish agreement with the original.',
            'Independent physical owners and produced outputs are scoped projections, not a playable replacement.'],
        whole_game_complete=False, playable_replacement=False)
    write_json(output / 'receipt.json', receipt)
    print(json.dumps(dict(directory=str(output), mode='modelselfcheck', oracle_cases=0,
        full880_frames=0, frames=receipt['independent_frames'], selections=receipt['independent_selections'],
        stages=stage_count, boundary=boundary, source_unchanged=source_unchanged,
        assets_unchanged=assets_unchanged), ensure_ascii=False))
    if failure or not source_unchanged or not assets_unchanged:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
