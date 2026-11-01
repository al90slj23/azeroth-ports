#!/usr/bin/env python3
"""Owned original-UI entry observation; separate from independent game models."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import os
import plistlib
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA
from build_upgrade134_oracle import sha
from build_game_entry135_oracle import build_game_entry135
from probe_full_app135 import APPEND, verify_owned_terminal

FILES = (
    'scripts/probe_game_entry135.py', 'scripts/run_game_entry135.mjs',
    'scripts/browser_game_entry135.mjs', 'scripts/build_game_entry135_oracle.py',
    'scripts/probe_full_app135.py', 'scripts/probe_entry_world135.py',
    'scripts/build_full135_oracle.py', 'scripts/build_upgrade134_oracle.py',
    'scripts/trace_coop.py', 'scripts/wasm_index.py',
    'reconstruction/resource_spec/__init__.py',
    'reconstruction/resource_spec/mpq.py',
)
TEMPLATE = ROOT/'evidence/full-app0135-probe-20261101T122659.584362Z/config.json'
VERSION_CHECK = ROOT/'evidence/official-version-check-20261101T132611.332454Z/receipt.json'
EXE_SHA = '71e5f1767279db4bd428d1cd9c5d50d37759b72295386a69f9e3f6e70bc59249'


def prepare(before):
    if not ROOT.resolve().is_relative_to(Path('/Volumes/RuiRui4TB').resolve()):
        raise ValueError('Research volume is unavailable')
    prior = json.loads(TEMPLATE.read_text())
    version = json.loads(VERSION_CHECK.read_text())
    assert version['status'] == 200
    assert version['manifest']['version'] == '0.135.1'
    assert version['manifest']['sha256'] == EXE_SHA
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime(
        'game-entry0135-probe-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    (out/'tmp').mkdir()
    manifest = build_game_entry135(out)
    glue = ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js'
    assert sha(glue) == prior['official_glue_sha256']
    bridge = out/'bridge.mjs'
    bridge.write_bytes(glue.read_bytes()+APPEND.encode())
    chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    browser_version = plistlib.loads(Path('/Applications/Google Chrome.app/Contents/Info.plist').read_bytes())['CFBundleShortVersionString']
    node = ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    assert sha(node) == '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    package = Path(prior['playwright_path'])/'package.json'
    config = {k: prior[k] for k in (
        'archives', 'name_index_path', 'name_index_sha256', 'playwright_path',
        'asset_index_path', 'asset_index_sha256', 'aux_path', 'aux_sha256',
        'font_path', 'font_sha256', 'font_bytes', 'font_origin_url')}
    config.update(
        directory=str(out), original_path=str(SOURCE), original_sha256=SOURCE_SHA,
        module_path=manifest['module_path'], module_sha256=manifest['module_sha256'],
        module_manifest_sha256=sha(Path(manifest['manifest_path'])),
        glue_path=str(bridge), glue_sha256=sha(bridge),
        glue_prefix_bytes=glue.stat().st_size, official_glue_sha256=sha(glue),
        observer_script_path=str(ROOT/'scripts/browser_game_entry135.mjs'),
        observer_script_sha256=before['scripts/browser_game_entry135.mjs'],
        python_path=sys.executable, python_sha256=sha(Path(sys.executable)),
        python_version=sys.version, asset_worker_script=str(ROOT/'scripts/probe_entry_world135.py'),
        chrome_path=str(chrome), chrome_sha256=sha(chrome), browser_version=browser_version,
        node_path=str(node), node_sha256=sha(node),
        playwright_version=json.loads(package.read_text())['version'],
        playwright_package_sha256=sha(package), browser_profile='metal',
        browser_extra_args=['--use-angle=metal', '--enable-unsafe-webgpu'],
        expected_adapter_architecture='metal-3', browser_heap_mib=768,
        memory_page_cap=32768, memory_cap_bytes=2*1024*1024*1024,
        asset_file_budget=8192, asset_decoded_byte_budget=512*1024*1024,
        capture_chunk_bytes=1024*1024, callback_budget=2400,
        running_return_budget=8, observation_seconds=90,
        checkpoint_byte_budget=128*1024, command_observation_budget=100,
        command_rows_per_observation=64, host_detail_budget=20000,
        inner_deadline_seconds=240, outer_deadline_seconds=270,
        official_version_check_path=str(VERSION_CHECK), official_version_check_sha256=sha(VERSION_CHECK),
        template_config_path=str(TEMPLATE), template_config_sha256=sha(TEMPLATE),
        source_sha256=before,
        scope='Separate natural original UI entry in fresh isolated origin. Real mouse/keyboard only, no App/Game/world/profile/Once/command injection. Original code/table/memory/data unchanged; only global0 observer export appended and read. All878 browser imports delegate real official bindings; no Playwright request routing. Physical Apple Metal backend; no performance acceptance. Own2GiB WASM/512MiB decoded-assets/8192-file policy distinct from prior research hosts; frozen-copy allocation is additional, not an RSS bound. Full-memory bytes are one coherent copy, not a full JS/externref/VM checkpoint. Independent model cases/frames remain0.')
    for key in ('aux', 'font'):
        assert sha(Path(config[key+'_path'])) == config[key+'_sha256']
    config_path = out/'config.json'
    config_path.write_text(json.dumps(config, indent=2)+'\n')
    (out/'official-version-check.json').write_bytes(VERSION_CHECK.read_bytes())
    for name, digest in before.items():
        target = out/'source-snapshot'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes())
        assert sha(target) == digest
    return out, config_path, config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--directory', type=Path)
    args = parser.parse_args()
    before = {name: sha(ROOT/name) for name in FILES}
    assert sha(SOURCE) == SOURCE_SHA
    if args.directory:
        out = args.directory.resolve()
        assert out.parent == ROOT/'evidence' and out.name.startswith('game-entry0135-probe-')
        config_path = out/'config.json'
        config = json.loads(config_path.read_text())
        assert config['source_sha256'] == before and config['directory'] == str(out)
        assert not (out/'owned-process.json').exists(), 'Prepared experiment runs only once'
    else:
        out, config_path, config = prepare(before)
    if args.prepare_only:
        print(json.dumps({'directory': str(out), 'prepared_only': True, 'source_files': len(before),
                          'config_sha256': sha(config_path), 'module_sha256': config['module_sha256'], 'original_executed': False}))
        return
    frozen = {config_path: sha(config_path)}
    for path, digest in (
        (out/'game-entry135-module.json', config['module_manifest_sha256']),
        (Path(config['template_config_path']), config['template_config_sha256']),
    ):
        assert sha(path) == digest
        frozen[path] = digest
    for path_key, hash_key in (
        ('module_path', 'module_sha256'), ('glue_path', 'glue_sha256'),
        ('original_path', 'original_sha256'), ('observer_script_path', 'observer_script_sha256'),
        ('node_path', 'node_sha256'), ('chrome_path', 'chrome_sha256'),
        ('python_path', 'python_sha256'), ('official_version_check_path', 'official_version_check_sha256'),
    ):
        path = Path(config[path_key])
        assert sha(path) == config[hash_key]
        frozen[path] = config[hash_key]
    package = Path(config['playwright_path'])/'package.json'
    assert sha(package) == config['playwright_package_sha256']
    frozen[package] = config['playwright_package_sha256']
    command = [config['node_path'], '--max-old-space-size=512',
               str(ROOT/'scripts/run_game_entry135.mjs'), str(config_path)]
    began = time.monotonic()
    runtime = None
    launcher_error = None
    journal_errors = []

    def read_journal(name):
        path = out/name
        if not path.exists():
            return None
        try:
            value = json.loads(path.read_text())
            if not isinstance(value, dict):
                raise ValueError('Journal must be an object')
            return value
        except (OSError, ValueError) as exc:
            journal_errors.append({'file': name, 'error': str(exc)})
            return None

    def interrupted(sig, frame):
        raise KeyboardInterrupt('Owned launcher interrupted by signal '+str(sig))

    prior_sigterm = signal.signal(signal.SIGTERM, interrupted)
    with (out/'stdout.log').open('wb') as stdout, (out/'stderr.log').open('wb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True,
                                 env=dict(os.environ, TMPDIR=str(out/'tmp')))
        try:
            (out/'owned-process.json').write_text(json.dumps({
                'pid': child.pid, 'pgid': child.pid, 'command': command,
                'outer_deadline_seconds': config['outer_deadline_seconds']}, indent=2)+'\n')
            child.wait(timeout=config['outer_deadline_seconds'])
        except (subprocess.TimeoutExpired, KeyboardInterrupt, OSError) as exc:
            launcher_error = str(exc)
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
            runtime = read_journal('runtime.json')
            ledger = read_journal('owned-hosts.json')
            cleanup_identity = {'events': (runtime or {}).get('events', [])+(ledger or {}).get('events', [])}
            terminal = verify_owned_terminal(child, cleanup_identity)
            signal.signal(signal.SIGTERM, prior_sigterm)
    after = {name: sha(ROOT/name) for name in FILES}
    identity = before == after and all(sha(p) == digest for p, digest in frozen.items())
    status = (runtime or {}).get('status', 'runtime_receipt_missing')
    if launcher_error:
        status = 'owned_launcher_boundary'
    if not identity:
        status = 'source_or_input_identity_boundary'
    if not terminal['all_owned_terminal']:
        status = 'cleanup_boundary'
    receipt = {
        'version': '0.135.1', 'build': '0898d5e3',
        'kind': 'controlled_original_natural_UI_to_Game_observation_not_independent_model',
        'status': status, 'original_sha256': SOURCE_SHA,
        'module_sha256': config['module_sha256'], 'config_sha256': sha(config_path),
        'source_sha256_before': before, 'source_sha256_after': after,
        'source_and_input_identities_unchanged': identity,
        'process': {'pid': child.pid, 'pgid': child.pid, 'exit_code': child.returncode,
                    'seconds': time.monotonic()-began, 'terminal': terminal},
        'launcher_error': launcher_error, 'journal_errors': journal_errors,
        'runtime': runtime, 'new_independent_cases': 0, 'new_independent_mainloop_frames': 0,
        'native_Windows_execution_validated': False, 'user_profile_used': False,
        'installed_apps_or_saves_modified': False, 'complete_game': False,
    }
    (out/'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'directory': str(out), 'status': status, 'exit_code': child.returncode,
                      'all_owned_terminal': terminal['all_owned_terminal'],
                      'source_and_input_identities_unchanged': identity,
                      'error': (runtime or {}).get('error')}))


if __name__ == '__main__':
    main()
