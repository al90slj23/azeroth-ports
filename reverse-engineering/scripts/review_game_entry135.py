#!/usr/bin/env python3
"""Independently read terminal natural-entry evidence; never instantiate WASM."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import ast
import hashlib
import json
import math
import mmap
import os
import re
import sqlite3
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
INDEX_SHA = 'b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
PROFILE = ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
EXPECTED_FILES = {
    'scripts/probe_game_entry135.py', 'scripts/run_game_entry135.mjs',
    'scripts/browser_game_entry135.mjs', 'scripts/build_game_entry135_oracle.py',
    'scripts/probe_full_app135.py', 'scripts/probe_entry_world135.py',
    'scripts/build_full135_oracle.py', 'scripts/build_upgrade134_oracle.py',
    'scripts/trace_coop.py', 'scripts/wasm_index.py',
    'reconstruction/resource_spec/__init__.py', 'reconstruction/resource_spec/mpq.py',
}


def sha(file):
    with Path(file).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(file):
    return json.loads(Path(file).read_text())


def digest_slice(data, start, end):
    digest = hashlib.sha256()
    for at in range(start, end, 1024*1024):
        digest.update(data[at:min(end, at+1024*1024)])
    return digest.hexdigest()


def ule(data, at):
    result = shift = 0
    while True:
        value = data[at]
        at += 1
        result |= (value & 127) << shift
        if value < 128:
            return result, at
        shift += 7
        assert shift <= 35, 'LEB bound'


def sections(data):
    assert data[:8] == b'\0asm\1\0\0\0'
    result, at = [], 8
    while at < len(data):
        start, identifier = at, data[at]
        size, body = ule(data, at+1)
        at = body+size
        assert at <= len(data)
        result.append((identifier, start, body, at))
    assert at == len(data)
    return result


def exports(data, section):
    count, at = ule(data, section[2])
    result = []
    for _ in range(count):
        size, at = ule(data, at)
        name = data[at:at+size].decode()
        at += size
        kind = data[at]
        index, at = ule(data, at+1)
        result.append((name, kind, index))
    assert at == section[3]
    return result


def imports(data, section):
    count, at = ule(data, section[2])
    result = []
    for _ in range(count):
        size, at = ule(data, at)
        module = data[at:at+size].decode(); at += size
        size, at = ule(data, at)
        name = data[at:at+size].decode(); at += size
        kind = data[at]; at += 1
        assert kind == 0, 'This fixed original has878 function imports'
        type_index, at = ule(data, at)
        result.append(dict(module=module, name=name, kind=kind, type_index=type_index))
    assert at == section[3]
    return result


def f64word(value):
    return struct.unpack('<Q', struct.pack('<d', value))[0]


def present(header):
    return header['game_tag_u64'] == '0'


def running(header):
    if not present(header):
        return False
    game = header['game']
    return (game['phase'] if game['mode'] == 0 else game['global_phase']) == 1


def missing(pid, group=False):
    try:
        (os.killpg if group else os.kill)(int(pid), 0)
    except ProcessLookupError:
        return True
    return False


def closure(config, batch):
    expected = config['source_sha256']
    assert set(expected) == EXPECTED_FILES
    for name, value in expected.items():
        assert sha(ROOT/name) == sha(batch/'source-snapshot'/name) == value
        if name.endswith('.py'):
            ast.parse((ROOT/name).read_text())
    pending = [ROOT/'scripts/probe_game_entry135.py', ROOT/'scripts/probe_entry_world135.py',
               ROOT/'reconstruction/resource_spec/mpq.py', ROOT/'reconstruction/resource_spec/__init__.py']
    found = set()
    while pending:
        file = pending.pop()
        name = str(file.relative_to(ROOT))
        if name in found:
            continue
        found.add(name)
        for node in ast.walk(ast.parse(file.read_text())):
            names = [v.name for v in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) and node.module else []
            for module in names:
                candidate = ROOT/'scripts'/(module.split('.')[0]+'.py')
                if candidate.is_file():
                    pending.append(candidate)
    assert found | {'scripts/run_game_entry135.mjs', 'scripts/browser_game_entry135.mjs'} == EXPECTED_FILES
    return dict(files=len(expected), independently_walked_local_python_imports=sorted(found), sha256=expected)


def static_evidence(original, destination):
    index = PROFILE/'index.sqlite'
    assert sha(index) == INDEX_SHA
    db = sqlite3.connect(index.resolve().as_uri()+'?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    result = []
    with (PROFILE/'official-0.135.1-full.wat').open('rb') as stream:
        for idx in (176107, 4253, 122123, 104471, 83825, 174119, 880, 6730, 24129, 2328, 1089, 45626):
            row = dict(db.execute('select * from functions where idx=?', (idx,)).fetchone())
            stream.seek(row['wat_start'])
            data = stream.read(row['wat_end']-row['wat_start'])
            lines = [v.strip() for v in data.decode().splitlines()]
            needles = {
                176107: ['call 4253'], 4253: ['i32.const 5305816', 'call 517'],
                122123: ['call 867'], 104471: ['call_indirect (type 3)'],
                83825: ['call 880', 'i32.load8_u offset=8'], 174119: ['call 681'],
                880: ['call 6730', 'call 24129', 'call 1089', 'i32.store8 offset=2575'],
                6730: ['i32.const 3376'], 24129: [],
                2328: ['f32.const 0x1.47ae14p-5 (;=0.04;)', 'call 1089'],
                1089: ['i32.store8 offset=2587'], 45626: [],
            }[idx]
            windows = []
            for needle in needles:
                # Original optimized entry trampolines may use return_call.
                pattern = re.compile(re.escape(needle)+r'(?![0-9])')
                hits = [i for i, line in enumerate(lines) if pattern.search(line)]
                assert hits, (idx, needle)
                for at in hits[:8]:
                    a, b = max(0, at-14), min(len(lines), at+15)
                    windows.append(dict(needle=needle, function_local_line=at+1,
                                        source_lines=[dict(line=i+1, text=lines[i]) for i in range(a, b)]))
            item = dict(index=idx, sqlite_row=row, wat_sha256=hashlib.sha256(data).hexdigest(),
                        original_body_sha256=digest_slice(original, row['body_start'], row['body_end']), windows=windows)
            result.append(item)
    db.close()
    target = destination/'static-original-windows.json'
    target.write_text(json.dumps(dict(index_sha256=INDEX_SHA, functions=result), indent=2)+'\n')
    return dict(file=str(target), sha256=sha(target), functions=len(result),
                method='SQLite mode=ro exact byte-range seek; no full WAT scan or original execution')


def audit(batch, receipt_sha, destination):
    receipt_path = batch/'receipt.json'
    assert sha(receipt_path) == receipt_sha
    receipt, config, runtime = load(receipt_path), load(batch/'config.json'), load(batch/'runtime.json')
    assert receipt['version'] == '0.135.1' and receipt['build'] == '0898d5e3'
    assert receipt['runtime'] == runtime and sha(batch/'config.json') == receipt['config_sha256']
    assert receipt['source_sha256_before'] == receipt['source_sha256_after'] == config['source_sha256']
    assert receipt['source_and_input_identities_unchanged'] is True
    assert receipt['launcher_error'] is None and receipt['journal_errors'] == []
    assert receipt['process']['exit_code'] == 0
    assert receipt['status'] == runtime['status'] == 'observed_natural_Game_running_complete880_returns'
    result = runtime['result']
    assert result['status'] == receipt['status'] and result['error'] is None and runtime.get('error') is None
    assert result['observerBoundaries'] == []
    metadata_path = batch/'observation-before-upload.json'
    metadata_raw = metadata_path.read_bytes(); metadata = json.loads(metadata_raw)
    metadata_receipt = result['pre_upload_observation_receipt']
    assert metadata_receipt == runtime['pre_upload_observation_receipt']
    assert len(metadata_raw) == metadata_receipt['bytes'] <= 16*1024**2 and sha(metadata_path) == metadata_receipt['sha256']
    assert metadata_receipt['persisted_before_bulk_memory_upload'] is True
    assert metadata['version'] == '0.135.1' and metadata['build'] == '0898d5e3'
    assert metadata['original_sha256'] == config['original_sha256'] and metadata['module_sha256'] == config['module_sha256']
    assert metadata['bulk_memory_capture_complete'] is False
    for key in ('frames', 'commands', 'checkpoints', 'contexts', 'confirmed_complete880_returns', 'running_complete880_returns',
                'clock_advances', 'capture_stack_observed', 'post_freeze_RAF_cancellation', 'error', 'stopped'):
        assert metadata[key] == result[key], ('pre-upload/final immutable observation mismatch', key)
    raf = result['post_freeze_RAF_cancellation']
    assert raf['after_synchronous_memory_copy'] is True and raf['original_import'] == 507
    assert raf['observed_handles_cancelled'] > 0 and raf['original_frames_before_copy_unchanged'] is True
    assert raf['shutdown_or_Rc_destructor_equivalence_claimed'] is False
    source = closure(config, batch)
    tools = {}
    for key in ('original', 'module', 'node', 'chrome', 'python', 'aux', 'font', 'name_index', 'asset_index', 'observer_script'):
        file, expected = Path(config[key+'_path']), config[key+'_sha256']
        assert sha(file) == expected, (key, file)
        tools[key] = dict(path=str(file), sha256=expected, bytes=file.stat().st_size)
    package = Path(config['playwright_path'])/'package.json'
    assert sha(package) == config['playwright_package_sha256']
    assert load(package)['version'] == config['playwright_version']
    tools['playwright_package_metadata'] = dict(path=str(package), sha256=sha(package), version=config['playwright_version'])
    assert config['original_sha256'] == ORIGINAL_SHA == receipt['original_sha256']
    for file, expected in ((batch/'game-entry135-module.json', config['module_manifest_sha256']),
                           (Path(config['official_version_check_path']), config['official_version_check_sha256']),
                           (Path(config['template_config_path']), config['template_config_sha256'])):
        assert sha(file) == expected
    version = load(config['official_version_check_path'])
    assert version['status'] == 200 and version['manifest']['version'] == '0.135.1'
    assert version['manifest']['sha256'] == '71e5f1767279db4bd428d1cd9c5d50d37759b72295386a69f9e3f6e70bc59249'
    assert (batch/'official-version-check.json').read_bytes() == Path(config['official_version_check_path']).read_bytes()
    glue = Path(config['glue_path']).read_bytes()
    assert hash_bytes(glue[:config['glue_prefix_bytes']]) == config['official_glue_sha256']
    append = glue[config['glue_prefix_bytes']:].decode()
    assert 'Reflect.apply(fn,this,args)' in append and 'return __wbg_finalize_init(instance,module)' in append
    manifest = load(batch/'game-entry135-module.json')
    assert manifest['module_sha256'] == config['module_sha256'] == receipt['module_sha256']
    assert manifest['original_program_instantiated'] is False and manifest['function_exports_added'] == 0
    assert sha(manifest['validator']['path']) == manifest['validator']['sha256']
    assert manifest['validator']['exit_code'] == 0
    for name in ('stdout', 'stderr'):
        assert sha(batch/('game-entry135-validation.'+name)) == manifest['validator'][name+'_sha256']
    with Path(config['original_path']).open('rb') as first, Path(config['module_path']).open('rb') as second:
        with mmap.mmap(first.fileno(), 0, access=mmap.ACCESS_READ) as original, mmap.mmap(second.fileno(), 0, access=mmap.ACCESS_READ) as module:
            old, new = sections(original), sections(module)
            assert [r[0] for r in old] == [r[0] for r in new] and not any(r[0] == 8 for r in old)
            unchanged = []
            for a, b in zip(old, new):
                if a[0] != 7:
                    assert a[3]-a[1] == b[3]-b[1]
                    digest = digest_slice(original, a[1], a[3])
                    assert digest == digest_slice(module, b[1], b[3])
                    unchanged.append(dict(section=a[0], bytes=a[3]-a[1], sha256=digest))
            original_exports = exports(original, next(v for v in old if v[0] == 7))
            modified_exports = exports(module, next(v for v in new if v[0] == 7))
            assert len(original_exports) == 36 and modified_exports == original_exports+[('research_game_entry135_stack', 3, 0)]
            global_section = next(v for v in old if v[0] == 6)
            assert original[global_section[2]:global_section[3]].hex() == '017f01418080c0000b'
            bindings = imports(original, next(v for v in old if v[0] == 2))
            assert len(bindings) == 878 and bindings[507]['name'].startswith('__wbg_requestAnimationFrame_')
            assert bindings[517]['name'].startswith('__wbg_setInterval_') and bindings[681]['name'].startswith('__wbg_now_')
            assert bindings[867]['name'] == '__wbindgen_cast_0000000000000010'
            static = static_evidence(original, destination)
    browser_source = (ROOT/'scripts/browser_game_entry135.mjs').read_text()
    host_source = (ROOT/'scripts/run_game_entry135.mjs').read_text()
    assert not re.search(r'\b(?:context|page)\s*\.\s*route\s*\(', host_source)
    for text in ("connect-src 'self'", 'MAP * ~NOTFOUND', 'disable_non_proxied_udp', 'serviceWorkers:', 'proxyRejected', 'fs.rename'):
        assert text in host_source
    assert 'new Uint8Array(buffer).slice()' in browser_source and 'header(x.App,frozen.buffer)' in browser_source
    assert not re.search(r'research_game_entry135_stack\s*\.\s*value\s*=', browser_source)
    assert 'Reflect.apply(original,this,values)' in browser_source
    copy_to_cancel = browser_source[browser_source.index('frozenStack=stack();'):browser_source.index('postFreezeRAFCancellation={')]
    assert 'new Uint8Array(buffer).slice()' in copy_to_cancel and 'for(const handle of originalRAFHandles)cancelAnimationFrame(handle)' in copy_to_cancel
    assert 'await' not in copy_to_cancel
    assert "phase==='after'&&id===507&&typeof returned==='number')originalRAFHandles.add(returned)" in browser_source
    assert result['adapterInfo'] == {'vendor': 'apple', 'architecture': 'metal-3'}
    assert config['memory_page_cap'] == 32768 and config['memory_cap_bytes'] == 2*1024**3
    assert config['asset_file_budget'] == 8192 and config['asset_decoded_byte_budget'] == 512*1024**2
    assert config['browser_heap_mib'] == 768 and config['capture_chunk_bytes'] == 1024**2
    assert result['wasm_memory_written_by_research'] is False and result['global_value_written_by_research'] is False
    assert result['original_function_bodies_changed'] is False and result['synthetic_App_Game_profile_world_or_command_injected'] is False
    assert result['independent_model_cases'] == result['new_independent_mainloop_frames'] == receipt['new_independent_cases'] == receipt['new_independent_mainloop_frames'] == 0
    assert receipt['complete_game'] is False and result['complete_game'] is False
    assert result['user_profile_used'] is False
    assert "if(Object.keys(localStorage).length||Object.keys(sessionStorage).length||(await indexedDB.databases()).length)throw Error('Origin is not fresh')" in browser_source
    contexts, timers, frames = result['contexts'], result['timers'], result['frames']
    assert len(contexts) == len(timers) == 1
    context, timer = contexts[0], timers[0]
    App, Rc = context['App'], context['Rc']
    assert App == Rc+16 and context['vtable'] == 5305816
    assert struct.unpack_from('<I', bytes.fromhex(context['closure_env12_hex']), 8)[0] == Rc
    assert timer['interval_ms'] == 25 and timer['errors'] == []
    assert struct.unpack_from('<Q', bytes.fromhex(context['app5168_hex_at_cast']), 16)[0] == 2
    confirmed, active, previous_clock, advances = [], [], None, 0
    for index, frame in enumerate(frames):
        assert frame['index'] == index and frame['App'] == App
        before, after = frame['before'], frame.get('after')
        complete = bool(after and frame.get('returned') and before['borrow'] == after['borrow'] == 0 and
                        before['stack_observed'] is not None and before['stack_observed'] == after['stack_observed'])
        assert frame.get('confirmed_complete880_return', False) == complete
        assert not frame.get('error') and not frame.get('observer_error')
        for value in (before, after):
            assert value['strong'] > 0 and value['game_present'] == present(value) and value['running'] == running(value)
        if complete:
            confirmed.append(index)
            assert any(f64word(now/1000) == f64word(after['app_previous_seconds']) for now in frame['original_now_values_ms'])
        if complete and running(after):
            active.append(index)
            clock = struct.unpack('<f', struct.pack('<I', after['game']['clock_bits']))[0]
            assert math.isfinite(clock) and clock == after['game']['clock']
            if previous_clock is not None and clock > previous_clock:
                advances += 1
            previous_clock = clock
    assert len(confirmed) == result['confirmed_complete880_returns']
    assert len(active) == result['running_complete880_returns'] >= config['running_return_budget'] == 8
    assert advances == result['clock_advances'] > 0 and result['stopped'] == 'running_callback_budget_reached'
    assert timer['returns'] == sum(bool(v.get('returned')) for v in frames)
    command_tags = Counter()
    for index, command in enumerate(result['commands']):
        frame = frames[command['frame']]
        assert frame['commands']['index'] == index and frame['commands']['len'] == command['len']
        assert command['app_before_header'] == frame['before'] and command['App'] == App
        assert command['len'] <= command['cap'] and command['transport'] == frame['before']['transport_pointer']
        assert command['all_rows_captured'] == (len(command['entries']) == command['len'])
        for row in command['entries']:
            raw = bytes.fromhex(row['raw232_hex'])
            assert len(raw) == 232 and struct.unpack_from('<I', raw)[0] == row['raw_tag']
            command_tags[row['raw_tag']] += 1
    assert not runtime['errors'] and not runtime['network_boundary'] and not runtime['passive_requests']
    renderer_errors = [v for v in runtime['logs'] if v['type'] == 'error' and re.search(r'panicked|createBuffer failed|device lost', v['text'], re.I)]
    assert not renderer_errors
    proxy_rejections = [v for v in runtime['blocked'] if v['kind'].startswith('owned_proxy_rejected_')]
    for row in proxy_rejections:
        assert row['forwarded'] is False and row['provenance'] == 'browser_process_unattributed'
    assert len(proxy_rejections) == len(runtime['blocked'])
    input_events = runtime['trusted_input_events']
    assert input_events and all(v['isTrusted'] is True for v in input_events)
    assert any(v['type'] == 'click' and v['x'] == 475 and v['y'] == 490 for v in input_events)
    assert any(v['type'] == 'keydown' and v['code'] == 'KeyW' for v in input_events)
    assert any(v['type'] == 'keyup' and v['code'] == 'KeyW' for v in input_events)
    assert all(v.get('code') != 'Enter' for v in input_events)
    assert any(v['action'] == 'keyboard_hold' and v['requested_duration_ms'] == 1500 for v in runtime['inputs'])
    quiet = next(v for v in runtime['events'] if v['label'] == 'scene_asset_quiet_observation')
    waiting = next(v for v in runtime['events'] if v['label'] == 'waiting_for_scene_asset_quiet')
    assert quiet['quiet'] is True and quiet['assets_in_flight'] == 0 and quiet['quiet_ms'] >= 3000
    assert quiet['elapsed_ms']-waiting['elapsed_ms'] >= 10000
    capture_file = batch/'original_game.memory'
    capture = result['capture']
    assert capture['complete'] and capture_file.stat().st_size == capture['bytes'] <= config['memory_cap_bytes']
    assert sha(capture_file) == capture['sha256'] == runtime['capture']['sha256']
    assert runtime['capture']['bytes'] == runtime['capture']['total'] == capture['bytes']
    assert metadata['snapshot_total_bytes'] == capture['bytes']
    assert result['capture_synchronously_copied_unshared_memory'] and result['final_header_from_same_frozen_copy']
    world = {}
    with capture_file.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as memory:
        def u(at):
            assert 0 <= at <= len(memory)-4
            return struct.unpack_from('<I', memory, at)[0]
        def q(at):
            assert 0 <= at <= len(memory)-8
            return struct.unpack_from('<Q', memory, at)[0]
        def vector(at, stride):
            cap, ptr, count = u(at), u(at+4), u(at+8)
            assert count <= cap and 0 <= ptr <= len(memory) and ptr+cap*stride <= len(memory)
            return dict(capacity=cap, pointer=ptr, count=count, stride=stride,
                        active_sha256=digest_slice(memory, ptr, ptr+count*stride))
        assert q(App+16) == 0 and u(context['env']+8) == Rc and u(App-16) > 0 and memory[App-8] == 0
        final = context['final']; G = App+16
        assert final['App'] == App and final['memory_bytes'] == len(memory) and final['game_tag_u64'] == '0'
        assert u(App+3376) == final['profile_tag'] != 2
        assert u(App+5116) == final['world_cache'] and u(G+2348) == final['game']['world_rc'] > 0
        assert u(G+2352) == final['game']['clock_bits'] and memory[G+2582] == final['game']['mode']
        assert memory[G+2587] == final['game']['phase'] and memory[G+2588] == final['game']['global_phase'] and running(final)
        assert final['stack_observed'] == result['capture_stack_observed'] == frames[-1]['after']['stack_observed']
        assert q(App) == 1 and f64word(struct.unpack_from('<d', memory, App+8)[0]) == f64word(final['app_previous_seconds'])
        profile = dict(tag=u(App+3376), raw376_sha256=digest_slice(memory, App+3376, App+3752))
        entities = {name: vector(G+offset, stride) for name, offset, stride in (
            ('units424', 1784, 424), ('areas88', 1796, 88), ('pickups56', 1868, 56),
            ('packets16', 1880, 16), ('candidates80', 1904, 80), ('companions88', 2108, 88))}
        W = u(G+2348)
        assert W+124 <= len(memory) and u(W) > 0
        world = dict(pointer=W, raw124_hex=memory[W:W+124].hex(), tiles=vector(W+8, 36))
        for name, offset, stride, width_at in (('nav', 32, 1, 52), ('secondary', 92, 4, 112)):
            if u(W+offset) == 0xffffffff:
                world[name] = dict(present=False)
            else:
                value = vector(W+offset, stride); width = u(W+width_at)
                assert value['count'] == width*width
                world[name] = dict(present=True, width=width, **value)
        T = u(App+4768); C = u(T+16)
        assert T+24 <= len(memory) and C+76 <= len(memory) and u(C) > 0
        transport = dict(holder=T, holder24_hex=memory[T:T+24].hex(), cell=C, cell76_hex=memory[C:C+76].hex(), commands232=vector(C+28, 232),
                         historical_commands_not_negated_by_empty_final_queue=True)
    requests = runtime['requests']
    bad = [v for v in requests if v.get('status') != 200]
    assert all(v['path'] == '/favicon.ico' and v.get('status') == 404 for v in bad)
    metadata_posts = [v for v in requests if v['method'] == 'POST' and v['path'] == '/capture/observation.json']
    assert len(metadata_posts) == 1 and metadata_posts[0]['status'] == 200 and metadata_posts[0]['bytes'] == len(metadata_raw)
    posts = [v for v in requests if v['method'] == 'POST' and v['path'] == '/capture/original_game.memory']
    assert len(metadata_posts)+len(posts) == sum(v['method'] == 'POST' for v in requests)
    assert all(v['path'] == '/capture/original_game.memory' and v['status'] == 200 for v in posts)
    assert requests.index(metadata_posts[0]) < requests.index(posts[0])
    whole, tail = divmod(capture['bytes'], config['capture_chunk_bytes'])
    assert [v['bytes'] for v in posts] == [config['capture_chunk_bytes']]*whole+([tail] if tail else [])
    checked_assets = {}
    for row in requests:
        asset = row.get('asset')
        if asset is None:
            continue
        assert row['status'] == asset['status'] == 200 and asset['index_sha256'] == config['asset_index_sha256']
        file = Path(asset['file'])
        assert file.resolve().is_relative_to(batch/'actual-assets') and file.stat().st_size == asset['bytes']
        if str(file) not in checked_assets:
            assert sha(file) == asset['sha256']; checked_assets[str(file)] = asset['bytes']
    inventory = load(batch/'actual-assets-inventory.json')
    assert all(v['status'] == 200 for v in inventory['requests'])
    assert inventory['decoded_bytes'] <= config['asset_decoded_byte_budget'] and len(inventory['requests']) <= config['asset_file_budget']
    ledger, owned = load(batch/'owned-hosts.json'), load(batch/'owned-process.json')
    starts = [v for v in runtime['events'] if v['label'] in ('worker_started', 'browser_started')]
    assert ledger == {'events': starts} and len(starts) == 2
    assert owned['pid'] == owned['pgid'] == runtime['pid'] == receipt['process']['pid']
    assert receipt['process']['terminal']['all_owned_terminal'] is True
    terminal_now = dict(pids={}, groups={})
    for pid, value in receipt['process']['terminal']['owned_pids'].items():
        assert value is True; terminal_now['pids'][pid] = missing(pid); assert terminal_now['pids'][pid]
    for group, value in receipt['process']['terminal']['owned_pgids'].items():
        assert value is True; terminal_now['groups'][group] = missing(group, True); assert terminal_now['groups'][group]
    browser_start = next(v for v in starts if v['label'] == 'browser_started')
    profile_args = [v for v in browser_start['spawnargs'] if v.startswith('--user-data-dir=')]
    assert len(profile_args) == 1 and Path(profile_args[0].split('=', 1)[1]).is_relative_to(batch/'tmp')
    assert Path(config['directory']).resolve() == batch and batch.is_relative_to(Path('/Volumes/RuiRui4TB'))
    shots = {}
    for name in ('menu-ready.png', 'scene-before-movement.png', 'after-move.png', 'original-game.png'):
        file = batch/name; raw = file.read_bytes()
        assert raw[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', raw, 16) == (960, 540)
        shots[name] = dict(sha256=sha(file), bytes=len(raw))
    return dict(status='passed_scoped_original_observation_review', receipt=str(receipt_path), receipt_sha256=receipt_sha,
                config_sha256=sha(batch/'config.json'), source_closure=source, tools_and_resource_identities=tools,
                module=dict(only_export_changed=True, original_exports=36, appended_global0_export=modified_exports[-1], unchanged_sections=unchanged,
                    selected_actual_imports={i: bindings[i] for i in (507, 517, 681, 867)}),
                static_original_evidence=static, confirmed_complete880_returns=len(confirmed), running_complete880_returns=len(active),
                running_frame_indices=active, clock_advances=advances, final_clock=previous_clock, profile=profile,
                world=world, entities=entities, transport=transport, raw_command_tag_counts=dict(command_tags),
                input_actions=runtime['inputs'], trusted_input_events=input_events,
                isolated_storage=dict(empty_origin_checked_before_original_initialization=True,
                    final_local_storage_keys=result['local_storage_keys'], final_session_storage_keys=result['session_storage_keys'],
                    final_indexeddb_databases=result['indexeddb_databases'], original_may_write_its_new_isolated_profile=True),
                asset_quiet=quiet, capture=dict(bytes=capture['bytes'], sha256=capture['sha256'], stack=result['capture_stack_observed'],
                    live_memory_bytes_after_upload=result['memory_bytes'], coherent_copy_not_full_VM_snapshot=True),
                pre_upload_observation=dict(path=str(metadata_path), receipt=metadata_receipt, all_immutable_frame_command_header_fields_equal_final=True,
                    metadata_itself_did_not_claim_bulk_completion=True),
                post_freeze_RAF_cancellation=dict(receipt=raf, only_actual_import507_handles_source_verified=True,
                    individual_handle_identity_list_persisted=False, per_handle_runtime_validation_claimed=False,
                    static_order_copy_then_cancel_without_await=True, lifecycle_stop_not_additional_game_behavior=True),
                http=dict(count=len(requests), statuses=dict(Counter(v['status'] for v in requests)), nonasset404=bad,
                    memory_chunks=len(posts), unique_asset_files_hashed=len(checked_assets), unique_asset_bytes_hashed=sum(checked_assets.values())),
                network=dict(passive_nonloopback=[], unattributed_proxy_rejections=proxy_rejections, csp_violations=result['security_policy_violations'],
                    no_claim_that_blocked_presence_is_working_multiplayer=True), screenshots=shots,
                owned_terminal_rechecked=terminal_now, original_functions_executed_by_review=0, new_original_cases=0,
                independent_model_cases=0, independent_mainloop_frames=0, complete_game=False,
                limitations=[
                    'This is an original-program observation, not an independent complete880 implementation or gameplay differential test.',
                    'Only global0 export visibility changes; the original mutable global remains mutable and is read by research.',
                    'Raw232 commands are actual pre-poll bytes; nested payload pointers remain opaque, and temporal UI correlation is not a fully restored producer.',
                    'The coherent snapshot excludes JS objects, externrefs, browser/GPU state, and mutable globals except separately observed stack metadata.',
                    'Twelve project sources, listed binaries/resources, and package metadata are bound; all node_modules, Python stdlib, and OS implementation bytes are not frozen.',
                    'WASM2GiB, decoded assets512MiB, JS heap768MiB and a separate frozen copy are separate budgets, not a process RSS bound.',
                    'Proxy rejects are browser-process-unattributed; CSP presence intent is retained without claiming successful external connectivity.',
                    'Post-copy RAF cancellation has a count and verified source origin/order; individual cancelled handle IDs were not persisted or individually revalidated.',
                    'Eight running returns and clock advancement do not validate a complete run, performance, Windows execution, save recovery, or multiplayer.',
                ])


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--receipt-sha256', required=True)
    args = parser.parse_args()
    batch = args.directory.resolve()
    assert batch.parent == ROOT/'evidence' and batch.name.startswith('game-entry0135-probe-')
    assert (batch/'receipt.json').is_file(), 'A terminal receipt is required; live runs are not reviewed'
    own = Path(__file__); own_sha = sha(own)
    destination = ROOT/'evidence'/datetime.now(timezone.utc).strftime('game-entry0135-independent-review-%Y%m%dT%H%M%S.%fZ')
    destination.mkdir()
    result = audit(batch, args.receipt_sha256, destination)
    assert sha(own) == own_sha
    result.update(reviewer_script=str(own), reviewer_script_sha256=own_sha,
                  reviewed_version='0.135.1', reviewed_build='0898d5e3', independent_review=True)
    target = destination/'review.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'], review=str(target), sha256=sha(target),
                         running_returns=result['running_complete880_returns'], clock_advances=result['clock_advances'],
                         new_original_cases=0, independent_mainloop_frames=0)))


if __name__ == '__main__':
    main()
