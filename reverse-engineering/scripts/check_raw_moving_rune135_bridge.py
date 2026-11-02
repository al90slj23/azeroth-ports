#!/usr/bin/env python3
"""Bind raw451 moving460 model terminal state to a scoped differential.

This reads two independently generated model results. It does not read or run
an original EXE/WASM/memory image, and proves neither a new original case nor
per-stage raw-asset differential agreement. Caller scratch values stay unknown.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import sys

sys.dont_write_bytecode = True
EXTERNAL = Path('/Volumes/RuiRui4TB').resolve()


def external(path):
    path = Path(path).resolve()
    if not path.is_relative_to(EXTERNAL):
        raise ValueError('All bridge inputs and outputs must remain on4T')
    return path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def owner(rows, count):
    digest = hashlib.sha256()
    for row in rows:
        digest.update(json.dumps(row, separators=(',', ':')).encode() + b'\n')
    return dict(count=count, capacity=len(rows), backing_sha256=digest.hexdigest(),
        unknown_backing_cells=sum(row.count(None) for row in rows))


def creates(packets):
    result = []
    for opcode, payload in packets:
        if opcode != 169:
            continue
        raw = bytes.fromhex(payload)
        if len(raw) < 7 or raw[:5] != b'\1\0\0\0\0' or raw[5] not in (2, 3):
            continue
        mask, cursor, guid = raw[6], 7, 0
        for i in range(8):
            if mask >> i & 1:
                if cursor >= len(raw):
                    raise ValueError('Truncated create GUID')
                guid |= raw[cursor] << (8 * i)
                cursor += 1
        result.append(dict(guid=str(guid), payload169_hex=payload))
    return result


def npc_aura(packets):
    import struct
    result = []
    for opcode, payload in packets:
        if opcode != 169:
            continue
        raw = bytes.fromhex(payload)
        if len(raw) < 8 or raw[:6] != b'\1\0\0\0\0\0':
            continue
        mask, cursor, guid = raw[6], 7, 0
        for i in range(8):
            if mask >> i & 1:
                if cursor >= len(raw):
                    raise ValueError('Truncated values GUID')
                guid |= raw[cursor] << (8 * i)
                cursor += 1
        if guid >> 48 != 0xf130:
            continue
        if cursor >= len(raw):
            raise ValueError('Missing values mask count')
        words = raw[cursor]
        cursor += 1
        if words != 4:
            continue
        if cursor + 16 > len(raw):
            raise ValueError('Truncated values mask')
        masks = struct.unpack_from('<4I', raw, cursor)
        cursor += 16
        keys = [32 * j + bit for j, word in enumerate(masks)
            for bit in range(32) if word >> bit & 1]
        if len(raw) != cursor + 4 * len(keys):
            raise ValueError('Values payload length differs')
        slots = [key - 79 for key in keys if 79 <= key <= 94]
        if len(slots) == 1 and set(keys) == {79 + slots[0],
                99 + (slots[0] >> 3), 121 + (slots[0] >> 2)}:
            result.append(dict(guid=str(guid), slot=slots[0], payload169_hex=payload))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-directory', required=True, type=Path)
    parser.add_argument('--comparison', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    model, comparison, output = map(external,
        (args.model_directory, args.comparison, args.output))
    if output.exists():
        raise ValueError('Existing evidence may not be overwritten')
    receipt, oracle = load(model / 'receipt.json'), load(comparison)
    if (receipt['kind'] != 'independent_raw_asset_to_world_opening_combat_modelselfcheck'
            or (receipt['model_version'], receipt['model_actual_build']) != ('0.135.1', '90898d5e3')
            or (oracle['version'], oracle['actual_build']) != ('0.135.1', '90898d5e3')
            or oracle['differences'] != 0 or not oracle['completed_requested_budget']
            or oracle.get('physical_player_sources') is not True):
        raise ValueError('Matching complete physical135 model and scoped differential required')
    if sha(comparison) != '521db52b9d97637212460083a7ea88b9038d63871536d6635edc21645e0bd622':
        raise ValueError('Fixed moving460 differential identity required')
    files = dict(receipt_json=sha(model / 'receipt.json'), comparison_json=sha(comparison))
    for name, key in (('inputs.json', 'inputs_sha256'), ('stages.jsonl', 'stages_sha256'),
            ('final-state.json', 'final_state_sha256'),
            ('opaque-pickup-amount-origins.json', 'opaque_pickup_amount_origins_sha256')):
        if sha(model / name) != receipt[key]:
            raise ValueError('Raw model artifact identity differs: ' + name)
        files[name] = sha(model / name)
    files['final-summary.json'] = sha(model / 'final-summary.json')
    expectations = comparison.parent / 'stage-expectations.jsonl.gz'
    if sha(expectations) != oracle['expectations_sha256']:
        raise ValueError('Frozen expectation stream hash differs')
    count, logical_bytes, terminal = 0, 0, None
    with gzip.open(expectations, 'rb') as stream:
        for raw in stream:
            count += 1
            logical_bytes += len(raw)
            if len(raw) > 2 * 1024 * 1024 or logical_bytes > 1024 ** 3:
                raise ValueError('Expectation stream budget')
            terminal = json.loads(raw)
    if count != oracle['compared_stages'] + 1 or logical_bytes != oracle['expected_uncompressed_bytes']:
        raise ValueError('Incomplete frozen model expectation stream')
    if (terminal['record_kind'] != 'stage' or terminal['kind'] != 'terminal'
            or terminal['stage_index'] != oracle['compared_stages'] - 1):
        raise ValueError('Last expectation is not the declared final terminal stage')
    files['stage-expectations.jsonl.gz'] = sha(expectations)
    expected = terminal['expected']
    state, summary, inputs = (load(model / n) for n in
        ('final-state.json', 'final-summary.json', 'inputs.json'))
    content = {k: v for k, v in summary.items() if k != 'summary_sha256'}
    if hashlib.sha256(json.dumps(content, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != summary['summary_sha256']:
        raise ValueError('Summary content hash differs')
    last = None
    with (model / 'stages.jsonl').open('rb') as stream:
        for raw in stream:
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError('Summary record budget')
            last = json.loads(raw)
    if last['summary'] != summary:
        raise ValueError('Final summary is not the recorded model terminal')
    p = expected['projection']
    own = state['independent_opening_owner']
    player = state['player_source_owner']
    checks = {}
    direct = tuple(k for k in p if k in state)
    for key in direct:
        checks['terminal.' + key] = state[key] == p[key]
    owner_rows = {
        'units': (own['unit_backing_cells'], len(state['records']), 'units424'),
        'areas': (own['area_backing_cells'], len(state['area_records']), 'areas88'),
        'pickups': (own['pickup_backing_cells'], own['pickup_active_count'], 'pickups56'),
        'windows': (own['window_backing_cells'], own['window_count'], 'windows8'),
        'boundaries': (own['boundary_backing_cells'], own['boundary_count'], 'boundaries8'),
        'live32': (player['live_backing_cells'], player['live_count'], 'live32'),
        'aura48': (player['aura_backing_cells'], player['aura_capacity'], 'aura48'),
    }
    for name, (rows, n, label) in owner_rows.items():
        vector = expected['vectors'][name]
        checks['full_owner.' + name] = (vector['capacity'] == len(rows)
            and vector['count'] == n and vector['storage'] == rows
            and owner(rows, n) == summary['owners'][label])
    #Special/claims inactive backing is serialized in summary hashes but only
    #active rows in the generic tail projection. Bind the complete expected
    #backing to those full-capacity known/None-aware summary fingerprints.
    for name, label in (('special', 'special40'), ('companions', 'companions88')):
        vector = expected['vectors'][name]
        checks['full_owner.' + name] = owner(vector['storage'], vector['count']) == summary['owners'][label]
    checks['guardian_cooldowns'] = own['guardian_cooldowns'] == p['guardian_cooldowns']
    checks['special_serialized_fields'] = all(own[key] == p['special'][target] for key, target in (
        ('special_selected392', 'selected392'), ('special_target396', 'target396'),
        ('special_announced2565', 'announced2565'), ('special_clock2392_bits', 'announcement_time2392_bits')))
    checks['special_navigation_input'] = inputs['navigation_enabled'] is False and p['special']['navigation2564'] == 0
    if p['distance_map'] is None:
        checks['distance_map_serialized_projection'] = summary['distance_map'] is None
    else:
        checks['distance_map_serialized_projection'] = summary['distance_map'] == dict(
            start_index=p['distance_map']['start_index'], reachable=p['distance_map']['field24'],
            values_sha256=p['distance_map']['values_sha256'])
    checks['distance_map_clock'] = own['distance_map_updated_at_bits'] == p['distance_map_updated_at_bits']
    packets = own['produced_packets']
    actor = creates(packets)
    checks['all_declared_actor169'] = actor == p['explicit_actor_creates169']
    checks['resource_actor169'] = [x for x in actor if int(x['guid']) >> 48 == 0xf110
        and (int(x['guid']) >> 24) & 0xffffff in (9006, 9007, 9008)] == p['resource_create_packets169']
    checks['all_banner150'] = [payload for opcode, payload in packets if opcode == 150] == p['banner150_packets']
    checks['all_player226'] = [payload for opcode, payload in packets if opcode == 226] == p['player_speed226_packets']
    checks['npc_aura169'] = npc_aura(packets) == p['npc_aura_updates169']
    checks['rune_notifications'] = player['rune_notifications'] == p['rune_notifications']
    checks['player_aura_flag'] = player['aura_initialized2569'] == p['aura_initialized2569']
    checks['App_notification_context'] = (inputs['physical_player_sources'] is True
        and inputs['explicit_App_notification_counter'] == 1
        and player['notification_next_id14340336'] == p['notification_next_id14340336'])
    observed_origins = summary['physical_player_sources']['auxiliary_origins']
    checks['written_unknown_auxiliary_origins'] = [dict(slot=i, source=value)
        for i, value in enumerate(observed_origins) if value is not None] == expected['unresolved_live_auxiliary_origins']
    checks['opaque_pickup_origins'] = load(model / 'opaque-pickup-amount-origins.json') == expected['opaque_pickup_amount_origins']
    checks['effect_controls'] = all(state['effect_state'][key] == value for key, value in p['effect'].items())
    checks['tail_controls'] = all(state['tail_state'][key] == p['tail_flags'][key]
        for key in ('field400', 'flag2568', 'gate2579'))
    for name, count_value in (('effects120', len(state['effect_state']['effects120']['records_hex'])),
            ('delayed56', len(state['effect_state']['delayed56']['records_hex'])),
            ('hits112', len(state['queued'])),
            ('active84', len(state['tail_state']['active84']['records_hex'])),
            ('timed12', state['timed916_count'])):
        checks['vector_count.' + name] = count_value == expected['vectors'][name]['count']
    checks['frame_selection_budget'] = (receipt['independent_frames'], receipt['independent_selections'],
        receipt['boundary']['kind']) == (460, 4, 'frame_budget')
    checks['oracle_frame_selection_identity'] = (receipt['independent_frames'], receipt['independent_selections']) == (
        oracle['independent_frames'], oracle['independent_selections'])
    fixture = load(comparison.parent / 'fixtures.json')
    motion_rows=[]
    with (model / 'stages.jsonl').open()as stream:
        for line in stream:
            row=json.loads(line)
            if row['kind']=='motion':motion_rows.append(row)
    requested_motion=[row for row in fixture['actions']if row['kind']=='motion']
    checks['all44_controlled_motion_inputs']=(len(motion_rows)==44 and [dict(kind='motion',opcode=row['opcode'],payload24_hex=row['payload24_hex'])for row in motion_rows]==requested_motion)
    checks['route_events']=(inputs['motion_route']==receipt['motion_route']==oracle['motion_route']=='first-rune' and receipt['motion_route_events']==fixture['motion_route_events'])
    motion_cells=load(model/'final-motion-owner.json');files['final-motion-owner.json']=sha(model/'final-motion-owner.json')
    motion_words=(416,420,424,428,432,436,440,444,448,452,456,460,464,1428,1744,1748,1752,1756,1760,1764,1768,1772,1776,1780,2496,2500)
    known=p['motion_scalar_words'];valid_bytes={j for o in motion_words for j in range(o,o+4)}
    checks['canonical_motion_owner_mask']=(len(motion_cells)==2592 and all(v is None for j,v in enumerate(motion_cells)if j not in valid_bytes) and all((motion_cells[o:o+4]==[None]*4 if str(o)not in known else None not in motion_cells[o:o+4] and int.from_bytes(bytes(motion_cells[o:o+4]),'little')==known[str(o)])for o in motion_words))
    checks['motion_summary']={k:v for k,v in summary['motion_words'].items()if v is not None}==known
    checks['rune_consumed_and_notification_continued']=(player['notification_next_id14340336']==2 and len(player['rune_notifications'])==1 and len(p['rune_notifications'])==1)
    checks['opening_input_identity'] = all(str(inputs['opening'][key]) == fixture['input'][key]
        if key in ('app_lcg_seed_u64', 'object_id_u64') else inputs['opening'][key] == fixture['input'][key]
        for key in ('class_byte', 'race_byte', 'region_index', 'app_lcg_seed_u64', 'object_id_u64'))
    declared = {row['chain']: row for row in inputs['asset_inputs']}
    loaded = receipt['loaded_assets_sha256_after']
    checks['raw451_inputs'] = (receipt['declared_asset_files'], receipt['loaded_asset_files'],
        receipt['decoded_asset_bytes']) == (453, 451, 67281330)
    checks['loaded_asset_input_binding'] = (len(declared) == 453 and len(loaded) == 451
        and all(declared[name]['sha256'] == digest for name, digest in loaded.items())
        and sum(declared[name]['bytes'] for name in loaded) == 67281330
        and set(declared) - set(loaded) == {
            'dbfilesclient\\spell.dbc', 'dbfilesclient\\spellicon.dbc'})
    checks['all_assets_stable'] = receipt['assets_unchanged'] is True
    checks['model_sources_stable'] = (receipt['production_source_unchanged'] is True
        and receipt['source_sha256_before'] == receipt['source_sha256_after']
        and not receipt['escaped_runtime_sources'])
    shared = {n: h for n, h in oracle['source_sha256_before'].items() if n.startswith('reconstruction/')}
    checks['shared_production_sources'] = bool(shared) and all(
        receipt['source_sha256_before'].get(n) == receipt['source_sha256_after'].get(n) == h for n, h in shared.items())
    for name, digest in receipt['source_sha256_before'].items():
        if sha(model / 'source-snapshot' / name) != digest:
            raise ValueError('Model frozen source differs: ' + name)
    for name, digest in shared.items():
        if sha(comparison.parent / 'source-snapshot' / name) != digest:
            raise ValueError('Differential frozen production source differs: ' + name)
    checks['no_original_or_preparsed_inputs'] = all(receipt[k] is False for k in (
        'original_program_executed', 'original_memory_read', 'original_wasm_executed', 'preparsed_world_input_read'))
    world_hashes = {Path(name).name: digest for name, digest in oracle['world_input']['artifacts'].items()}
    for artifact in receipt['world_artifacts'].values():
        path = external(model / artifact['file'])
        checks['world.' + artifact['file']] = sha(path) == artifact['sha256'] == world_hashes.get(artifact['file'])
    result = dict(kind='raw451_moving460_terminal_model_composition_bridge',
        all_passed=all(checks.values()), checks=checks, check_count=len(checks),
        model_directory=str(model), comparison=str(comparison),
        expected_records=count, expected_logical_bytes=logical_bytes,
        expected_terminal_stage_index=terminal['stage_index'],
        expected_terminal_action_index=terminal['action_index'],
        shared_production_files=len(shared), artifact_sha256=files,
        model_source_files=len(receipt['source_sha256_before']),
        declared_manifest_asset_files=453, loaded_raw_asset_files=451, raw_asset_bytes=67281330,
        declared_but_unloaded_assets=sorted(set(declared) - set(loaded)),
        full_owner_known_and_None_backing_compared=True,
        unresolved_written_scratch_values_predicted=False,
        stage_comparison=False, direct_terminal_projection_keys=list(direct),
        not_direct_terminal_projection_keys=[k for k in p if k not in direct],
        driver_sha256=sha(Path(__file__)),
        new_original_cases=0, original_executions=0, full880_frames=0,
        native_windows_execution=False, playable_replacement=False,
        limitations=['Terminal comparison between two independent model runs; no new original execution or per-stage raw-asset differential.',
            'The explicitly listed serialized projection, complete owners and output subsets are compared; absent serializer fields are not invented.',
            'App notification context1 is an explicit input; caller scratch values remain typed unknown sources.'])
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(output=str(output), checks=len(checks), all_passed=result['all_passed'])))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
