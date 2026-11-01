#!/usr/bin/env python3
"""Add a small explicit research-export surface to the fixed original module.

Only section7 is changed. No original instructions, tables, globals, memory or
data are rewritten. This builder does not execute WASM. Consumers must reject
all host calls and never invoke either original application start export.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from wasm_index import ORIGINAL_SHA, sha

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {1065, 1573, 3231, 933, 934, 917, 25242, 32475, 85387, 106495, 71577}


def u32(data, position):
    value = shift = 0
    while position < len(data) and shift <= 28:
        byte = data[position]; position += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, position
        shift += 7
    raise ValueError('Invalid bounded u32 LEB')


def encode(value):
    result = bytearray()
    while True:
        byte = value & 127; value >>= 7
        result.append(byte | (128 if value else 0))
        if not value:
            return bytes(result)


def sections(data):
    if data[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Unexpected original WASM header')
    result = []; p = 8
    while p < len(data):
        kind = data[p]; size, start = u32(data, p + 1); stop = start + size
        if stop > len(data):
            raise ValueError('Section outside original')
        result.append((kind, p, start, stop)); p = stop
    if p != len(data):
        raise ValueError('Final section boundary differs')
    return result


def build(functions):
    functions = sorted(set(functions))
    if not functions or any(x not in ALLOWED for x in functions):
        raise ValueError('Select an explicitly allowed internal research function')
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    data = original.read_bytes()
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA:
        raise ValueError('Fixed original identity differs')
    original_sections = sections(data)
    if any(kind == 8 for kind, *_ in original_sections):
        raise ValueError('Original has an implicit WASM start; instantiation is not admitted')
    imports = []; all_exports = []; replacement = None
    for kind, first, start, stop in original_sections:
        if kind == 2:
            count, p = u32(data, start)
            for index in range(count):
                names = []
                for _ in range(2):
                    length, p = u32(data, p); names.append(data[p:p + length].decode()); p += length
                if data[p] != 0:
                    raise ValueError('Only function imports accepted by denied-host harness')
                type_index, p = u32(data, p + 1)
                imports.append({'index': index, 'module': names[0], 'name': names[1], 'type_index': type_index})
            if p != stop:
                raise ValueError('Import section boundary differs')
        if kind == 7:
            count, p = u32(data, start); original_entries_start = p
            for _ in range(count):
                length, p = u32(data, p); name = data[p:p + length].decode(); p += length
                export_kind = data[p]; idx, p = u32(data, p + 1)
                all_exports.append({'name': name, 'kind': export_kind, 'index': idx})
            if p != stop or any(x['name'].startswith('research_') for x in all_exports):
                raise ValueError('Original export profile differs')
            added = b''
            for function in functions:
                name = f'research_f{function}'.encode()
                added += encode(len(name)) + name + b'\x00' + encode(function)
            payload = encode(count + len(functions)) + data[original_entries_start:stop] + added
            replacement = data[:first] + b'\x07' + encode(len(payload)) + payload + data[stop:]
    if replacement is None or not imports:
        raise ValueError('Expected original imports and exports')
    replaced_sections = sections(replacement)
    if [x[0] for x in replaced_sections] != [x[0] for x in original_sections]:
        raise ValueError('Added/removed a section')
    identities = []
    for old, new in zip(original_sections, replaced_sections):
        kind, first, start, stop = old
        if kind != 7 and data[first:stop] != replacement[new[1]:new[3]]:
            raise ValueError('Nonexport original section changed')
        identities.append({'section': kind, 'original_payload_sha256': hashlib.sha256(data[start:stop]).hexdigest(),
                           'original_bytes': stop - start, 'unchanged': kind != 7})
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('full-function-oracle-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    output = run / 'research-exports.wasm'; output.write_bytes(replacement)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    provenance = json.loads((ROOT / '.toolchain/rea-wasm-profile/installed-provenance.json').read_text())
    if sha(validator) != provenance['tools']['wasm-validate']['sha256']:
        raise ValueError('Fixed WABT validator identity differs')
    subprocess.run([str(validator), '--enable-all', str(output)], check=True, timeout=45)
    if sha(original) != ORIGINAL_SHA or sha(output) != hashlib.sha256(replacement).hexdigest():
        raise ValueError('Original/output identity changed')
    manifest = {'original_wasm_sha256': ORIGINAL_SHA, 'original_bytes': len(data),
                'module_sha256': sha(output), 'module_bytes': len(replacement), 'module_file': output.name,
                'research_functions': functions, 'original_export_count': len(all_exports),
                'original_exports': all_exports, 'denied_function_imports': imports,
                'wasm_implicit_start_present': False, 'application_start_must_not_be_called': True,
                'only_changed_section': 7, 'section_identities': identities,
                'builder_sha256': sha(Path(__file__)), 'validator_sha256': sha(validator),
                'builder_executed_target': False,
                'scope': 'Original full-module research copy with added exports, not a pure-function micro-module. No host calls permitted by its runner.'}
    (run / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    return run, manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--functions', type=int, nargs='+', required=True)
    args = parser.parse_args()
    run, manifest = build(args.functions)
    print(json.dumps({'evidence_directory': str(run), 'module_sha256': manifest['module_sha256'],
                      'research_functions': manifest['research_functions'], 'target_executed': False}))
