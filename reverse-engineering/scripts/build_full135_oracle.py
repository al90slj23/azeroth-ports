#!/usr/bin/env python3
"""Export approved internal functions from fixed official0.135.1 without body changes.

No target execution by this builder. Every runtime must deny all878 host imports,
call no application entry and use explicitly scoped synthetic fixtures. Source
identity, each approved body, signatures and every non-export section are checked.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from build_upgrade134_oracle import Reader, unsigned, sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
SOURCE_BYTES = 90959080
VALIDATOR_SHA = 'a17b421f1cca2c0bba48c6ab3a510f9510db44e505cffd5a48c64bb1f0b5659c'
# Candidate discovery by structural correspondence is separately recorded in the
# migration trace. These fixed bindings are independently signature/body-guarded.
ROLES = {'select_ability': (1072, b'\x7f\x7f', b''),
 'recalculate_stats': (1512, b'\x7f', b''),
 'finish_selection': (4600, b'\x7f\x7f', b''),
 'resolve_owned_ability': (22287, b'\x7f\x7f\x7f', b''),
 'auto_cast': (916, b'\x7f}', b''),
 'cast': (922, b'\x7f\x7f', b'\x7f'),
 'damage': (914, b'\x7f~}\x7f\x7f\x7f\x7f', b''),
 'gain_experience': (4630, b'\x7f\x7f', b''),
 'incoming_damage': (1073, b'\x7f}~\x7f\x7f\x7f', b''),
 'spawn_pickup': (1417, b'\x7f\x7f\x7f\x7f', b''),
 'collect_pickups': (2862, b'\x7f', b''),
 'attract_all_xp': (21779, b'\x7f', b''),
 'generate_choices': (2159, b'\x7f\x7f\x7f', b''),
 'upgrade_value': (25368, b'\x7f\x7f\x7f', b'}'),
 'tick': (880, b'\x7f|', b''),
 'command': (1371, b'\x7f\x7f', b''),
 'effective_armor': (27375, b'\x7f', b'}'),
 'spawn_tick': (947, b'\x7f}', b''),
 'special_tick': (2376, b'\x7f', b''),
 'choose_spawn': (20272, b'\x7f\x7f\x7f}', b'\x7f'),
 'spawn_normal': (5736, b'\x7f\x7f\x7f\x7f', b''),
 'spawn_boss': (2785, b'\x7f\x7f}', b''),
 'spawn_position': (8751, b'\x7f\x7f}}}', b''),
 'spawn_decay': (26361, b'}', b'}'),
 'process_hits': (1754, b'\x7f', b''),
 'query_targets': (27562, b'\x7f\x7f\x7f}\x7f\x7f', b''),
 'queue_hit': (8295, b'\x7f\x7f\x7f\x7f~}}\x7f', b''),
 'atan2_heading': (42475, b'}}', b'}'),
 'atan_heading': (34787, b'}', b'}'),
 'update_units': (921, b'\x7f}', b''),
 'owned_tick': (1076, b'\x7f}', b''),
 'player_tick': (2088, b'\x7f}', b''),
 'proc_event': (984, b'\x7f\x7f\x7f', b''),
 'proc_gate': (8157, b'\x7f\x7f\x7f', b'\x7f'),
 'sin_angle': (11428, b'}', b'}'),
 'cos_angle': (11503, b'}', b'}'),
 'initial_game': (1560, b'\x7f\x7f\x7f', b''),
 'begin_run': (1089, b'\x7f', b''),
 'move_player': (2328, b'\x7f\x7f}', b'\x7f'),
 'area_tick': (3757, b'\x7f', b'')}

APPROVED_BODY_SHA = {'select_ability': '2a2be6157b509b2ac741f5d1dacf803f2fdf273da9512916ef750b9817ee5b01',
 'recalculate_stats': '31ff40340e52cb6b24453d114b676fb519187a30c1c091418208eda59c89e748',
 'finish_selection': '55b714430f81a1440d38cdeede434a677b8e4cbcce331cbe8266104281329acd',
 'resolve_owned_ability': '2809d38e9e5b3bf6ac302e790d591c19447804b1e9ae1345a9403233468306fb',
 'auto_cast': 'a358136ba7f5f35bc5a33968b35624d5a788f6fabcbc017c01e2a3652caa4bdf',
 'cast': '32cdc4ec4ee9b320ae2052560c2a3f4682979df5638e57c3e7140ffc8b047d80',
 'damage': '13da39eca94557de0048ad65b63eb398d8774d08b7985b398d1ccc34a04519fc',
 'gain_experience': '828722a8f200878b4bdcf5ac59df4d95f1021df6ca42044a6419c216a405fd21',
 'incoming_damage': 'ae8055c998f7dad212a404de8cee67a5375c9f4f94750f1e69fd5119f4f9e076',
 'spawn_pickup': '4bb47348a0b2b2e4564b4862512de1e7164cc1f4636921e0d00abcea1f861342',
 'collect_pickups': '5c99fc846ee151902af4a39bd6e9fc14b9ed7fd96ecb49fd538606bfba16de3a',
 'attract_all_xp': '08a1fc041396675a27f577af12436433a72256c79958008fd129ddf59b7a17b6',
 'generate_choices': '413d98654b02253f255eb0cf54bcdc06309fb7aea5c9079fb73a20a9b6a98bcc',
 'upgrade_value': 'bd939e6a7a535282fef1ac6d6e476183a8666298880371c24aba497b580ec68e',
 'tick': 'c3a0484b1e630dda325e24b14a9003bc19ffc9720c24a9dd24393b7845e1ed58',
 'command': 'fe613365e0c9b6520201f744a7c4c187e07e3d6010b074e65ef57179bef660cd',
 'effective_armor': 'e45b81dd82d055b9baff0a5bcbdf7461568882656922c250b8a6a6c9cd2f3d2a',
 'spawn_tick': '8eafc61592944f9083c7542177928d582672300323e367fd0c7b343d777c1c76',
 'special_tick': '6b985b23a141a82085f021e7bedf0247ea2a61a99bda05cf820e38a369be29ff',
 'choose_spawn': 'a84d3dcb7bd37b23115b15898284e140817d80b8631c086c78bc3b08fc100aad',
 'spawn_normal': '59e98d191a6da662992a9e4e261f02d012ad34adb8744b98a4011a9d26f7b671',
 'spawn_boss': '2b8d07e32cdde3d22724bb7f1992812be8cc165d22c5092cff2f64eed2ef0a76',
 'spawn_position': '94147d4d71b3186ec42fa1b9012884441fb874563c5995527d04d35ab926e4d8',
 'spawn_decay': '867e5b613a355ed43c0395805ec4b11200177d5a29c6c13ac3365165cdb1b46f',
 'process_hits': '7a214558b394295d2bf84bee2db34163c5596ceb1c00c38ce4336eaef1dd9b89',
 'query_targets': 'bfbeab0a322ceecda316c34b4cf6097c8dbce7a90b211946996b9fe24ac57344',
 'queue_hit': 'fe1c2b62706ac3f5f9b9edee25336d356fbad815272d58d84dd789b0d6557a7d',
 'atan2_heading': '5e81fe1b4ddc5f97b4ad5acca32430cbeac843302398a0f9afe88d4556a99fb5',
 'atan_heading': '01ed1cbceddf892890336caa312038ca20b55e0c0f84521218c998c095e8b345',
 'update_units': '5c2c1cdc75e805e7d4e7ed51f5dddde34eda6331617c9ea8ee2a26da90329a37',
 'owned_tick': '3dbb7ab4e94cbe5fdacce3f544419951c84bc056a969703835f83586d5076777',
 'player_tick': 'a20643b34a3be2898101856d84102ba9e7964b6846b0345510306fd500ffa77a',
 'proc_event': 'f9e1b5fb843e275626d1cef0d554014e304a24c1e6fbe1e2b0ed21dcdb48b5fe',
 'proc_gate': 'eb826c0e86dceff28ec3d14bc7afb4ffca376411a8e2c1a4c921cce8ebb37c51',
 'sin_angle': '67188c5a196f2538d8d29d0de23b30935d4adcdefd6cc563d393888b03e2aeeb',
 'cos_angle': 'e6b1b35466a69bf778e1a26a23296457144510ca9c825e00eccd22e48a012d99',
 'initial_game': '064fd2a7ae947b934f9a398c75aaf17923188e8fad36ddf60849f69f960837fe',
 'begin_run': '08ba0c62e0fa4009e7faa31de75154a9c0a98a1f0349d72ec7cd1874229772cb',
 'move_player': '8e456fb160c30e4c4275670d2f4c1d9a6691e4be791905364ea5ff34b008b84b',
 'area_tick': 'e976ee48b3f0ad4117bfa98c81538fa88bf4607c4a9ca15c1a5a040c1c4477f5'}

def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_source(data):
    require(data[:8] == b'\0asm\1\0\0\0', 'Wrong source WASM header')
    top, sections = Reader(data, 8), {}
    while top.pos < top.end:
        kind, size = top.byte(), top.uint()
        begin = top.pos
        top.raw(size)
        if kind:
            require(kind not in sections, 'Duplicate non-custom source section')
            sections[kind] = (begin, top.pos)
    def reader(kind):
        return Reader(data, *sections[kind])
    t, types = reader(1), []
    for _ in range(t.uint()):
        require(t.byte() == 0x60, 'Unsupported non-function type')
        params = t.raw(t.uint())
        results = t.raw(t.uint())
        types.append((params, results))
    t.finished()
    imp, imports = reader(2), []
    for _ in range(imp.uint()):
        module, name, kind = imp.name(), imp.name(), imp.byte()
        require(kind == 0, 'Pinned source expects only function imports')
        imports.append((module, name, imp.uint()))
    imp.finished()
    fun = reader(3)
    declarations = [fun.uint() for _ in range(fun.uint())]
    fun.finished()
    require(len(imports) == 878 and len(declarations) == 175317, 'Source function counts differ')
    require(all(x < len(types) for x in declarations), 'Source function type outside section')
    code, bodies = reader(10), {}
    require(code.uint() == len(declarations), 'Function/code counts differ')
    for index in range(len(imports), len(imports) + len(declarations)):
        length = code.uint()
        begin = code.pos
        code.raw(length)
        bodies[index] = (begin, code.pos)
    code.finished()
    dat, segments = reader(11), []
    for index in range(dat.uint()):
        flags = dat.uint()
        require(flags in (0, 1, 2), 'Unknown data segment flags')
        memory, address = None, None
        if flags != 1:
            memory = 0 if flags == 0 else dat.uint()
            require(dat.byte() == 0x41, 'Data offset is not i32.const')
            address = dat.sint() & 0xffffffff
            require(dat.byte() == 0x0b and memory == 0, 'Unsupported active data expression')
        length = dat.uint()
        begin = dat.pos
        dat.raw(length)
        segments.append({'index': index, 'memory': memory, 'address': address,
                         'file_offset': begin, 'length': length})
    dat.finished()
    return types, imports, declarations, bodies, segments



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
        raise ValueError('Official0.135.1 identity differs')
    types, imports, declarations, bodies, _ = parse_source(binary)
    sections = section_list(binary)
    if any(kind == 8 for kind, *_ in sections):
        raise ValueError('Implicit source start is forbidden')
    ex = [x for x in sections if x[0] == 7]
    if len(ex) != 1:
        raise ValueError('Expected one export section')
    exports, first_entry = export_entries(binary, ex[0])
    malloc = [x for x in exports if x[0] == '__wbindgen_malloc' and x[1] == 0]
    if len(malloc) != 1 or malloc[0][2] != 91941:
        raise ValueError('New original allocator export identity differs')
    if types[declarations[malloc[0][2] - len(imports)]] != (b'\x7f\x7f', b'\x7f'):
        raise ValueError('New allocator signature differs')
    boot = {idx for name, kind, idx in exports if kind == 0 and name in ('start', '__wbindgen_start')}
    details = []; added = b''
    for role in roles:
        index, params, results = ROLES[role]
        if index in boot or types[declarations[index - len(imports)]] != (params, results):
            raise ValueError('Approved role signature or startup guard differs')
        start, end = bodies[index]
        if hashlib.sha256(binary[start:end]).hexdigest() != APPROVED_BODY_SHA[role]:
            raise ValueError('Approved role body differs')
        name = ('research135_' + role).encode()
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
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('full0135-oracle-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    path = out / 'research135-exports.wasm'; path.write_bytes(changed)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    if sha(validator) != VALIDATOR_SHA:
        raise ValueError('Pinned WABT validator differs')
    with (out / 'validation.stdout.txt').open('wb') as stdout, (out / 'validation.stderr.txt').open('wb') as stderr:
        subprocess.run([str(validator), '--enable-all', str(path)], stdout=stdout, stderr=stderr, check=True, timeout=45)
    if sha(SOURCE) != SOURCE_SHA or sha(path) != hashlib.sha256(changed).hexdigest():
        raise ValueError('Source/output changed')
    manifest = {'version': '0.135.1', 'build': '0898d5e3', 'original_wasm_sha256': SOURCE_SHA,
                'original_bytes': SOURCE_BYTES, 'module_file': path.name, 'module_sha256': sha(path),
                'module_bytes': len(changed), 'only_changed_section': 7, 'source_implicit_start': False,
                'original_export_count': len(exports), 'original_exports': exports,
                'original_allocator_export': {'name': '__wbindgen_malloc', 'index': 91941, 'signature': '(i32,i32)->i32'},
                'roles': details, 'denied_function_import_count': len(imports),
                'unchanged_original_sections': unchanged, 'target_executed_by_builder': False,
                'source_sha256': {'scripts/build_full135_oracle.py': sha(Path(__file__)),
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
