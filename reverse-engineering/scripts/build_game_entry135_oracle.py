#!/usr/bin/env python3
"""Append one stack-global observer export to fixed135; never run the module.

The original mutable global remains mutable. Research code must only read its
exported value; this builder neither writes it nor changes any memory limit.
The later browser host owns its separate runtime budget and lifecycle policy.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

sys.dont_write_bytecode = True
from build_full135_oracle import (
    ROOT, SOURCE, SOURCE_SHA, SOURCE_BYTES, VALIDATOR_SHA,
    section_list, export_entries,
)
from build_upgrade134_oracle import unsigned, sha

STACK_EXPORT = 'research_game_entry135_stack'
GLOBAL_SECTION_HEX = '017f01418080c0000b'
FILES = ('scripts/build_game_entry135_oracle.py',
         'scripts/build_full135_oracle.py',
         'scripts/build_upgrade134_oracle.py')


def build_game_entry135(out):
    """Return a manifest for a private, export-only module written inside out.

    out must be on the4T volume. Existing artifacts are never overwritten.
    Caller may share the directory with its own config/source snapshots.
    """
    out = Path(out).resolve()
    if not out.is_relative_to(Path('/Volumes/RuiRui4TB').resolve()):
        raise ValueError('Research artifacts must remain on the4T volume')
    out.mkdir(parents=True, exist_ok=True)
    module_path = out / 'game-entry135-observer.wasm'
    manifest_path = out / 'game-entry135-module.json'
    stdout_path = out / 'game-entry135-validation.stdout'
    stderr_path = out / 'game-entry135-validation.stderr'
    paths = (module_path, manifest_path, stdout_path, stderr_path)
    if any(path.exists() for path in paths):
        raise FileExistsError('Private game-entry artifacts already exist')
    before = {name: sha(ROOT/name) for name in FILES}
    original = SOURCE.read_bytes()
    assert len(original) == SOURCE_BYTES
    assert hashlib.sha256(original).hexdigest() == SOURCE_SHA
    old_sections = section_list(original)
    assert 8 not in [row[0] for row in old_sections]
    globals_section = next(row for row in old_sections if row[0] == 6)
    assert original[globals_section[2]:globals_section[3]].hex() == GLOBAL_SECTION_HEX
    exports_section = next(row for row in old_sections if row[0] == 7)
    prior_exports, records_start = export_entries(original, exports_section)
    assert len(prior_exports) == 36
    assert not any(name == STACK_EXPORT for name, _, _ in prior_exports)
    assert ('__wbindgen_malloc', 0, 91941) in prior_exports
    name = STACK_EXPORT.encode('ascii')
    addition = unsigned(len(name)) + name + b'\x03' + unsigned(0)
    payload = (unsigned(len(prior_exports)+1)
               + original[records_start:exports_section[3]] + addition)
    changed = (original[:exports_section[1]] + b'\x07'
               + unsigned(len(payload)) + payload
               + original[exports_section[3]:])
    new_sections = section_list(changed)
    assert [s[0] for s in new_sections] == [s[0] for s in old_sections]
    unchanged = []
    for old, new in zip(old_sections, new_sections):
        if old[0] == 7:
            continue
        original_bytes = original[old[1]:old[3]]
        assert original_bytes == changed[new[1]:new[3]]
        unchanged.append({'section': old[0], 'bytes': len(original_bytes),
                          'sha256': hashlib.sha256(original_bytes).hexdigest()})
    exported, _ = export_entries(changed, next(s for s in new_sections if s[0] == 7))
    assert exported == prior_exports + [(STACK_EXPORT, 3, 0)]
    assert [x for x in exported if x[1] == 0] == [x for x in prior_exports if x[1] == 0]
    with module_path.open('xb') as stream:
        stream.write(changed)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    assert sha(validator) == VALIDATOR_SHA
    command = [str(validator), '--enable-all', str(module_path)]
    result = subprocess.run(command, capture_output=True, timeout=45)
    with stdout_path.open('xb') as stream:
        stream.write(result.stdout)
    with stderr_path.open('xb') as stream:
        stream.write(result.stderr)
    if result.returncode != 0:
        raise RuntimeError('Private module validation failed; artifacts retained')
    after = {name: sha(ROOT/name) for name in FILES}
    assert before == after and sha(SOURCE) == SOURCE_SHA
    manifest = {
        'version': '0.135.1', 'build': '0898d5e3',
        'kind': 'private_original_game_entry_stack_observer_export_only',
        'original_path': str(SOURCE), 'original_wasm_sha256': SOURCE_SHA,
        'original_bytes': SOURCE_BYTES,
        'module_file': module_path.name, 'module_path': str(module_path),
        'module_bytes': len(changed), 'module_sha256': sha(module_path),
        'manifest_file': manifest_path.name, 'manifest_path': str(manifest_path),
        'only_changed_section': 7, 'source_implicit_start': False,
        'original_export_count': len(prior_exports),
        'original_exports': prior_exports,
        'observer_export': {'name': STACK_EXPORT, 'kind': 'global', 'index': 0,
                            'value_type': 'i32', 'initial_value': 1048576,
                            'original_mutable': True,
                            'research_access': 'read only; mutability itself is unchanged',
                            'original_global_section_hex': GLOBAL_SECTION_HEX},
        'unchanged_nonexport_sections': unchanged,
        'all_original_function_bodies_unchanged': True,
        'function_exports_added': 0, 'function_roles_added': 0,
        'shared_approved_function_roles_unchanged': 52,
        'original_tables_and_segments_unchanged': True,
        'original_memory_section_unchanged': True,
        'runtime_memory_limit_set_by_builder': False,
        'runtime_host_policy': 'Separate caller-owned browser policy; no host or runtime is instantiated here.',
        'validator': {'path': str(validator), 'sha256': VALIDATOR_SHA,
                      'command': command, 'exit_code': result.returncode,
                      'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)},
        'source_files': len(before), 'source_sha256_before': before,
        'source_sha256_after': after,
        'original_program_instantiated': False,
        'original_functions_or_appstart_called': False,
        'global_memory_or_Once_written': False,
        'network_used': False, 'user_saves_accessed': False,
    }
    with manifest_path.open('x') as stream:
        stream.write(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    directory = args.output or ROOT/'evidence'/datetime.now(timezone.utc).strftime(
        'game-entry0135-module-%Y%m%dT%H%M%S.%fZ')
    manifest = build_game_entry135(directory)
    print(json.dumps({'directory': str(Path(directory).resolve()),
                      'module_sha256': manifest['module_sha256'],
                      'manifest': manifest['manifest_path'],
                      'manifest_sha256': sha(Path(manifest['manifest_path'])),
                      'observer_export': STACK_EXPORT,
                      'original_executed': False}, indent=2))


if __name__ == '__main__':
    main()
