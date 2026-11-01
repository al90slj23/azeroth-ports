#!/usr/bin/env python3
"""Private cleave fixture: three approved functions plus global0 inspection.

Only the export section changes. The shared52-role builder is used unchanged,
then one global export is appended. The runtime facade never exposes a setter.
This builder runs only the pinned static validator, never the original program.
"""
import hashlib
import json
import os
import signal
import subprocess
import time

from build_full135_oracle import (ROOT, SOURCE, SOURCE_SHA, VALIDATOR_SHA, build,
    section_list, export_entries)
from build_upgrade134_oracle import unsigned, sha

STACK_EXPORT = 'research135_cleave_stack0'


def build_cleave135_stack():
    out, function_manifest = build(['cast', 'owned_tick', 'process_hits'])
    path = out / function_manifest['module_file']
    function_only = path.read_bytes()
    sections = section_list(function_only)
    section = next(s for s in sections if s[0] == 7)
    exports, first = export_entries(function_only, section)
    assert STACK_EXPORT not in {name for name, _, _ in exports}
    name = STACK_EXPORT.encode()
    added = unsigned(len(name)) + name + b'\x03' + unsigned(0)
    payload = unsigned(len(exports) + 1) + function_only[first:section[3]] + added
    changed = function_only[:section[1]] + b'\x07' + unsigned(len(payload)) + payload + function_only[section[3]:]
    original = SOURCE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == SOURCE_SHA
    original_sections, changed_sections = section_list(original), section_list(changed)
    assert [s[0] for s in original_sections] == [s[0] for s in changed_sections]
    assert not any(s[0] == 8 for s in original_sections)
    unchanged = []
    for before, after in zip(original_sections, changed_sections):
        if before[0] != 7:
            raw = original[before[1]:before[3]]
            assert raw == changed[after[1]:after[3]]
            unchanged.append(dict(section=before[0], sha256=hashlib.sha256(raw).hexdigest()))
    original_exports, _ = export_entries(original, next(s for s in original_sections if s[0] == 7))
    new_exports, _ = export_entries(changed, next(s for s in changed_sections if s[0] == 7))
    assert new_exports[:-1] == exports
    assert new_exports[-1] == (STACK_EXPORT, 3, 0)
    assert new_exports[:len(original_exports)] == original_exports
    assert [(r['role'], r['index']) for r in function_manifest['roles']] == [('cast', 922), ('owned_tick', 1076), ('process_hits', 1754)]
    (out / 'function-only-manifest.json').write_text(json.dumps(function_manifest, indent=2) + '\n')
    path.write_bytes(changed)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    assert sha(validator) == VALIDATOR_SHA
    command = [str(validator), '--enable-all', str(path)]
    started = time.monotonic()
    with (out / 'stack-validation.stdout.txt').open('wb') as stdout, (out / 'stack-validation.stderr.txt').open('wb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            code = child.wait(timeout=45)
        finally:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
    try:
        os.killpg(child.pid, 0)
    except ProcessLookupError:
        group_absent = True
    else:
        group_absent = False
    assert code == 0 and group_absent
    assert sha(SOURCE) == SOURCE_SHA and sha(path) == hashlib.sha256(changed).hexdigest()
    manifest = dict(function_manifest)
    manifest.update(module_sha256=sha(path), module_bytes=len(changed),
        private_stack_export=dict(name=STACK_EXPORT, kind=3, index=0,
            initial_i32=1048576, harness_access='read-only getter; global object remains private'),
        function_only_module_sha256=function_manifest['module_sha256'],
        exact_added_exports=new_exports[len(original_exports):],
        unchanged_original_sections_private=unchanged,
        private_builder_source_sha256=sha(ROOT / 'scripts/build_cleave135_oracle.py'),
        private_validation=dict(command=command, pid=child.pid, pgid=child.pid,
            exit_code=code, deadline_seconds=45, process_group_absent_after=group_absent,
            seconds=round(time.monotonic() - started, 3)), target_executed_by_private_builder=False)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return out, manifest


if __name__ == '__main__':
    directory, manifest = build_cleave135_stack()
    print(json.dumps(dict(directory=str(directory), module_sha256=manifest['module_sha256'])))
