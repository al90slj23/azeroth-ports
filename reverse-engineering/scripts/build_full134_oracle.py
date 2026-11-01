#!/usr/bin/env python3
"""Add approved research exports to the fixed official0.134.0 full module.

All source instructions and nonexport sections remain byte-identical. This
builder never executes WASM. A runner must deny every host import, call no
application start, use synthetic original-allocator memory, and state coverage.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from build_upgrade134_oracle import Reader, parse_source, unsigned, sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/latest-wenilla_bg.wasm'
SOURCE_SHA = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
SOURCE_BYTES = 90953762
VALIDATOR_SHA = 'a17b421f1cca2c0bba48c6ab3a510f9510db44e505cffd5a48c64bb1f0b5659c'
# Mappings are separately recovered from current0.134.0 instructions/callers.
ROLES = {'select_ability': (1073, b'\x7f\x7f', b''),
         'recalculate_stats': (1513, b'\x7f', b''),
         'finish_selection': (4600, b'\x7f\x7f', b''),
         'resolve_owned_ability': (22287, b'\x7f\x7f\x7f', b''),
         'auto_cast': (916, b'\x7f\x7d', b''),
         'cast': (922, b'\x7f\x7f', b'\x7f'),
         'damage': (914, b'\x7f\x7e\x7d\x7f\x7f\x7f\x7f', b''),
         'gain_experience': (4630, b'\x7f\x7f', b''),
         'incoming_damage': (1063, b'\x7f\x7d\x7e\x7f\x7f\x7f', b''),
         'spawn_pickup': (1417, b'\x7f\x7f\x7f\x7f', b''),
         'collect_pickups': (2862, b'\x7f', b''),
         'attract_all_xp': (21779, b'\x7f', b''),
         'generate_choices': (2159, b'\x7f\x7f\x7f', b''),
         'upgrade_value': (25368, b'\x7f\x7f\x7f', b'\x7d')}


def section_list(binary):
    if binary[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Bad WASM header')
    reader = Reader(binary, 8); result = []
    while reader.pos < reader.end:
        first = reader.pos; kind, size = reader.byte(), reader.uint(); start = reader.pos
        reader.raw(size)
        result.append((kind, first, start, reader.pos))
    return result


def export_entries(binary, section):
    reader = Reader(binary, section[2], section[3]); count = reader.uint(); first = reader.pos
    entries = [(reader.name(), reader.byte(), reader.uint()) for _ in range(count)]
    reader.finished()
    return entries, first


def build(roles):
    roles = sorted(set(roles))
    if not roles or any(x not in ROLES for x in roles):
        raise ValueError('Select a current-version approved role')
    binary = SOURCE.read_bytes()
    if len(binary) != SOURCE_BYTES or hashlib.sha256(binary).hexdigest() != SOURCE_SHA:
        raise ValueError('Official0.134.0 identity differs')
    types, imports, declarations, bodies, _ = parse_source(binary)
    sections = section_list(binary)
    if any(kind == 8 for kind, *_ in sections):
        raise ValueError('Implicit source start is forbidden')
    ex = [x for x in sections if x[0] == 7]
    if len(ex) != 1:
        raise ValueError('Expected one export section')
    exports, first_entry = export_entries(binary, ex[0])
    malloc = [x for x in exports if x[0] == '__wbindgen_malloc' and x[1] == 0]
    if len(malloc) != 1 or malloc[0][2] != 91940:
        raise ValueError('New original allocator export identity differs')
    if types[declarations[malloc[0][2] - len(imports)]] != (b'\x7f\x7f', b'\x7f'):
        raise ValueError('New allocator signature differs')
    boot = {idx for name, kind, idx in exports if kind == 0 and name in ('start', '__wbindgen_start')}
    details = []; added = b''
    for role in roles:
        index, params, results = ROLES[role]
        if index in boot or types[declarations[index - len(imports)]] != (params, results):
            raise ValueError('Approved role signature or startup guard differs')
        start, end = bodies[index]; name = ('research134_' + role).encode()
        added += unsigned(len(name)) + name + b'\x00' + unsigned(index)
        details.append({'role': role, 'index': index, 'export': name.decode(),
                        'type_index': declarations[index - len(imports)],
                        'parameters_hex': params.hex(), 'results_hex': results.hex(),
                        'body_start': start, 'body_end': end, 'body_bytes': end - start,
                        'body_sha256': hashlib.sha256(binary[start:end]).hexdigest()})
    kind, start, begin, end = ex[0]
    payload = unsigned(len(exports) + len(roles)) + binary[first_entry:end] + added
    changed = binary[:start] + b'\x07' + unsigned(len(payload)) + payload + binary[end:]
    new_sections = section_list(changed)
    if [x[0] for x in sections] != [x[0] for x in new_sections]:
        raise ValueError('Section profile changed')
    unchanged = []
    for a, b in zip(sections, new_sections):
        if a[0] != 7:
            if binary[a[1]:a[3]] != changed[b[1]:b[3]]:
                raise ValueError('Original nonexport bytes changed')
            unchanged.append({'section': a[0], 'original_sha256': hashlib.sha256(binary[a[1]:a[3]]).hexdigest()})
    new_exports, _ = export_entries(changed, next(x for x in new_sections if x[0] == 7))
    if new_exports[:len(exports)] != exports or len(new_exports) != len(exports) + len(details):
        raise ValueError('Original export prefix changed')
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('full0134-oracle-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    path = out / 'research134-exports.wasm'; path.write_bytes(changed)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    if sha(validator) != VALIDATOR_SHA:
        raise ValueError('Pinned WABT validator differs')
    with (out / 'validation.stdout.txt').open('wb') as stdout, (out / 'validation.stderr.txt').open('wb') as stderr:
        subprocess.run([str(validator), '--enable-all', str(path)], stdout=stdout, stderr=stderr, check=True, timeout=45)
    if sha(SOURCE) != SOURCE_SHA or sha(path) != hashlib.sha256(changed).hexdigest():
        raise ValueError('Source/output changed')
    manifest = {'version': '0.134.0', 'build': '983346a7', 'original_wasm_sha256': SOURCE_SHA,
                'original_bytes': SOURCE_BYTES, 'module_file': path.name, 'module_sha256': sha(path),
                'module_bytes': len(changed), 'only_changed_section': 7, 'source_implicit_start': False,
                'original_export_count': len(exports), 'original_exports': exports,
                'original_allocator_export': {'name': '__wbindgen_malloc', 'index': 91940, 'signature': '(i32,i32)->i32'},
                'roles': details, 'denied_function_import_count': len(imports),
                'unchanged_original_sections': unchanged, 'target_executed_by_builder': False,
                'source_sha256': {'scripts/build_full134_oracle.py': sha(Path(__file__)),
                                  'scripts/build_upgrade134_oracle.py': sha(ROOT / 'scripts/build_upgrade134_oracle.py')},
                'validator_sha256': VALIDATOR_SHA}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    return out, manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roles', nargs='+', choices=sorted(ROLES), required=True)
    args = parser.parse_args()
    out, manifest = build(args.roles)
    print(json.dumps({'evidence_directory': str(out), 'roles': args.roles,
                      'module_sha256': manifest['module_sha256'], 'target_executed': False}))
