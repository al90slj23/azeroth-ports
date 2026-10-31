#!/usr/bin/env python3
"""Emit static C for one exact WAT body in an explicitly synthetic module.

The original body is retained except for function names/direct-call indices.
Direct callees become signature-preserving named imports. Original memory,
global and table declarations are copied, but data/element segments, other
function bodies and the original start/export surface are deliberately absent.
Neither the original game nor the generated module/C is ever executed.

This is a local reading aid, not recovered Rust or a runnable original module.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
ARCHIVE_SHA = '3f654779b436c628db3ca4323c51538815f5fbc887a6d5f3bb1c18d36281e240'
DIRECT_CALL = re.compile(r'^(\s*)(call|return_call) (\d+)(\)*\s*)$', re.MULTILINE)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(path):
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def uint(data, offset):
    value = shift = 0
    while offset < len(data) and shift <= 28:
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
        shift += 7
    raise ValueError('Invalid u32 LEB')


def binary_info(data, target):
    """Read exact original signature indices/body range without decoding code."""
    if data[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Unsupported WASM header')
    sections = {}
    offset = 8
    while offset < len(data):
        section_id = data[offset]
        size, begin = uint(data, offset + 1)
        offset = begin + size
        if offset > len(data):
            raise ValueError('Section outside original file')
        if section_id:
            if section_id in sections:
                raise ValueError('Duplicate non-custom section')
            sections[section_id] = (begin, offset)
    count, offset = uint(data, sections[2][0])
    function_types = []
    for _ in range(count):
        for _ in range(2):
            length, offset = uint(data, offset)
            offset += length
        if data[offset] != 0:
            raise ValueError('Exact target profile expects function-only imports')
        type_index, offset = uint(data, offset + 1)
        function_types.append(type_index)
    imported = len(function_types)
    count, offset = uint(data, sections[3][0])
    for _ in range(count):
        type_index, offset = uint(data, offset)
        function_types.append(type_index)
    if not imported <= target < len(function_types):
        raise ValueError('Select one defined original function')
    body_count, offset = uint(data, sections[10][0])
    if body_count != count:
        raise ValueError('Function/code section count differs')
    body_range = None
    for function_index in range(imported, len(function_types)):
        length, begin = uint(data, offset)
        offset = begin + length
        if function_index == target:
            body_range = (begin, offset)
    if offset != sections[10][1]:
        raise ValueError('Original code section boundary differs')
    return function_types, body_range


def declarations(wat, first_function, last_function):
    """Use the verified canonical WABT layout; never read huge data/elem lines."""
    types = []
    resources = []
    with wat.open('rb') as stream:
        prefix = stream.read(first_function).decode()
        for line in prefix.splitlines():
            if line.startswith('  (type '):
                match = re.fullmatch(r'  \(type \(;(\d+);\) (\(func.*\))\)', line)
                if not match or int(match[1]) != len(types):
                    raise ValueError('Unsupported/non-contiguous canonical type declaration')
                types.append({'index': int(match[1]), 'signature': match[2], 'wat': line})
        stream.seek(last_function)
        while True:
            line = stream.readline(16384)
            if not line:
                break
            if re.match(rb'^  \((table|memory|global) ', line):
                if not line.endswith(b'\n'):
                    raise ValueError('Resource declaration exceeds supported single line')
                resources.append(line.decode().rstrip('\n'))
            else:
                # Exact full WABT output puts declarations before export/elem/data.
                if not resources:
                    raise ValueError('Expected original resource declarations after functions')
                break
    if not types or not resources:
        raise ValueError('Missing original declarations')
    return types, resources


def invoke(arguments, output, label):
    started = time.monotonic()
    with (output / f'{label}.stdout.txt').open('wb') as out, \
            (output / f'{label}.stderr.txt').open('wb') as err:
        result = subprocess.run([str(x) for x in arguments], stdout=out, stderr=err,
                                timeout=120, check=False)
    if result.returncode:
        raise SystemExit(f'{label} failed ({result.returncode}); inspect {output}')
    return {'arguments': [str(x) for x in arguments], 'exit_code': result.returncode,
            'elapsed_seconds': round(time.monotonic() - started, 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True,
                        help='Existing verified full-WAT index.sqlite (opened read-only)')
    parser.add_argument('--function', type=int, required=True,
                        help='Original defined function index, e.g. 1065 or 933')
    parser.add_argument('--max-wat-bytes', type=int, default=2 * 1024 * 1024,
                        help='Local output scope guard; default 2 MiB for the selected body')
    args = parser.parse_args()
    script = Path(__file__).resolve()
    script_sha = sha(script)
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    database = args.index.resolve()
    input_identities = {path: identity(path) for path in (source, database, script)}
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA:
        raise SystemExit('Original 0.126.0 module identity changed')
    function_types, (body_start, body_end) = binary_info(data, args.function)
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        meta = {key: json.loads(value) for key, value in connection.execute('SELECT * FROM meta')}
        row = connection.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end '
                                 'FROM functions WHERE idx=?', (args.function,)).fetchone()
        first, last = connection.execute('SELECT min(wat_start),max(wat_end) FROM functions').fetchone()
        indexed_calls = connection.execute('SELECT callee,wat_offset,wat_line FROM calls '
                                           'WHERE caller=? ORDER BY wat_offset',
                                           (args.function,)).fetchall()
    if meta['original_sha256'] != ORIGINAL_SHA or not row:
        raise SystemExit('Index original identity/function differs')
    if meta.get('wat_sha256') != WAT_SHA:
        raise SystemExit('Index WAT hash differs from fixed full-WAT identity')
    if meta.get('terminal_parentheses_supported') is not True:
        raise SystemExit('Index must explicitly support terminal-parenthesis calls')
    if meta.get('direct_call_kinds') != ['call', 'return_call']:
        raise SystemExit('Index direct-call coverage must include exactly call/return_call')
    start, end, first_line, indexed_start, indexed_end = row
    if (body_start, body_end) != (indexed_start, indexed_end):
        raise SystemExit('Index original code-body range differs')
    if end - start > args.max_wat_bytes or args.max_wat_bytes <= 0:
        raise SystemExit('Selected WAT exceeds explicit local output scope guard')
    wat = Path(meta['wat_path'])
    input_identities[wat] = identity(wat)
    if sha(wat) != WAT_SHA:
        raise SystemExit('Full WAT identity differs from fixed full-WAT identity')
    with wat.open('rb') as stream:
        stream.seek(start)
        original = stream.read(end - start).decode()
    types, resources = declarations(wat, first, last)
    header = re.match(r'  \(func \(;(\d+);\) \(type (\d+)\)', original)
    if (not header or int(header[1]) != args.function
            or int(header[2]) != function_types[args.function]):
        raise SystemExit('Selected WAT function header/signature differs')
    # Segments are intentionally absent, so instructions that require them must
    # fail closed rather than receive invented data, elements or function refs.
    if re.search(r'^\s*(?:memory\.init|data\.drop|table\.init|elem\.drop|ref\.func)\b',
                 original, re.MULTILINE):
        raise SystemExit('Body needs data/element/ref.func handling; not supported by this emitter')
    direct = list(DIRECT_CALL.finditer(original))
    if [int(match[3]) for match in direct] != [row[0] for row in indexed_calls]:
        raise SystemExit('Body direct calls differ from full-WAT index')
    callees = sorted({int(match[3]) for match in direct})
    remap = [{'original_index': index, 'synthetic_index': synthetic,
              'wat_name': f'$original_f{index}', 'import_module': 'original_function',
              'import_name': f'f{index}', 'original_type_index': function_types[index],
              'signature': types[function_types[index]]['signature']}
             for synthetic, index in enumerate(callees)]
    rewritten = DIRECT_CALL.sub(lambda match: f'{match[1]}{match[2]} $original_f{match[3]}{match[4]}',
                                original)
    rewritten = re.sub(r'^  \(func \(;\d+;\)', f'  (func $target_f{args.function}', rewritten, count=1)
    # Verify the only body edits are the documented names/direct-call remapping.
    restored = re.sub(r'^  \(func \$target_f\d+', f'  (func (;{args.function};)', rewritten, count=1)
    restored = re.sub(r'\b(call|return_call) \$original_f(\d+)', r'\1 \2', restored)
    if restored != original:
        raise SystemExit('Synthetic body does not round-trip to exact original WAT')
    indirect = [{'original_wat_line': first_line + original.count('\n', 0, match.start()),
                 'instruction': match[0].strip(), 'resolution': 'unknown; original table init omitted'}
                for match in re.finditer(r'^\s*(?:call_indirect|return_call_indirect|call_ref|return_call_ref)\b[^\n]*',
                                         original, re.MULTILINE)]
    tools = ROOT / '.toolchain/rea-wasm-profile'
    archive = tools / 'wabt-1.0.42-macos-arm64.tar.gz'
    if sha(archive) != ARCHIVE_SHA:
        raise SystemExit('Official WABT archive identity differs')
    binary = tools / 'wabt/wabt-1.0.42/bin'
    tool_identities = {}
    with tarfile.open(archive, 'r:gz') as package:
        for name in ('wat2wasm', 'wasm-validate', 'wasm2c'):
            executable = binary / name
            member = package.extractfile(f'wabt-1.0.42/bin/{name}')
            executable_sha = sha(executable)
            if member is None or hashlib.sha256(member.read()).hexdigest() != executable_sha:
                raise SystemExit('WABT executable differs from verified official archive')
            version = subprocess.check_output([str(executable), '--version'], text=True).strip()
            if version != '1.0.42':
                raise SystemExit('Unsupported WABT tool version')
            tool_identities[name] = {'version': version, 'sha256': executable_sha,
                                     'matches_verified_archive': True}
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('readable-ir-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    (output / f'original-f{args.function}.wat').write_text(original)
    imports = [f'  (import "{item["import_module"]}" "{item["import_name"]}" '
               f'(func {item["wat_name"]} (type {item["original_type_index"]})))'
               for item in remap]
    module = ('(module\n' + '\n'.join(item['wat'] for item in types) + '\n'
              + '\n'.join(imports + resources) + '\n' + rewritten
              + f'  (export "target_f{args.function}" (func $target_f{args.function}))\n)\n')
    micro = output / f'synthetic-f{args.function}.wat'
    micro.write_text(module)
    wasm = micro.with_suffix('.wasm')
    c_file = micro.with_suffix('.c')
    # Use the common default feature set: --enable-all makes wat2wasm emit
    # compact imports and makes wasm2c reject unsupported enabled features.
    # Bodies requiring additional features fail explicitly at this stage.
    invocations = [invoke([binary / 'wat2wasm', micro, '-o', wasm], output, 'assemble'),
                   invoke([binary / 'wasm-validate', wasm], output, 'validate'),
                   invoke([binary / 'wasm2c', '-n', f'synthetic_f{args.function}',
                           wasm, '-o', c_file], output, 'emit-c')]
    c_text = c_file.read_text()
    c_entries = [{'symbol': match[1], 'line': c_text.count('\n', 0, match.start()) + 1}
                 for match in re.finditer(
                     rf'^[^;\n]*\b(w2c_\w*target_f{args.function}(?:_\d+)?)\([^;\n]*\) \{{$',
                     c_text, re.MULTILINE)]
    if not c_entries:
        raise SystemExit('WABT output lacks a named target C definition')
    (output / 'README.txt').write_text(
        f'STATIC READING AID: original function {args.function} in a synthetic module.\n'
        'This is WABT stack-to-C translation, not original Rust source or a runnable original game.\n'
        'Original data segments, element/table initialization and all other function bodies are absent.\n'
        'Direct callees are named imports with original signatures and no implementations.\n'
        'Indirect calls, if present, retain type/table operands but their targets remain unknown.\n'
        'Do not execute or use this synthetic output as a behavior oracle.\n'
        'manifest.json records input hashes, exact ranges, call-index remapping and tool receipts.\n'
        f'C entry points in {c_file.name}:\n'
        + ''.join(f'  line {entry["line"]}: {entry["symbol"]}\n' for entry in c_entries))
    if (sha(source) != ORIGINAL_SHA or sha(script) != script_sha
            or any(identity(path) != before for path, before in input_identities.items())):
        raise SystemExit('Original or indexed input changed during static emission')
    manifest = {
        'method': 'WABT C translation of one synthetic micro-module; not original-module decompilation',
        'producer_script': {'path': str(script), 'sha256': script_sha},
        'original_module': {'path': str(source), 'bytes': source.stat().st_size, 'sha256': ORIGINAL_SHA},
        'index': {'path': str(database), 'sha256': sha(database)},
        'full_wat': {'path': str(wat), 'sha256': WAT_SHA},
        'index_coverage': {'terminal_parentheses_supported': meta['terminal_parentheses_supported'],
                           'direct_call_kinds': meta['direct_call_kinds']},
        'selected_function': {'original_index': args.function, 'synthetic_index': len(callees),
                              'original_type_index': function_types[args.function],
                              'original_body_range': [body_start, body_end],
                              'original_body_sha256': hashlib.sha256(data[body_start:body_end]).hexdigest(),
                              'original_wat_range': [start, end], 'original_wat_first_line': first_line,
                              'original_wat_sha256': hashlib.sha256(original.encode()).hexdigest(),
                              'exact_wat_round_trip_verified': True},
        'direct_call_sites': len(direct), 'direct_callee_remap': remap,
        'c_entry_points': c_entries,
        'indirect_calls': indirect, 'copied_type_count': len(types),
        'copied_resource_declarations': resources,
        'omissions': ['all other function bodies', 'original imports/export/start surface',
                      'all original data segments', 'all original element/table initialization'],
        'interpretation_limits': ['C is stack-to-C translation, not original Rust source',
                                  'named direct imports have original signatures but no implementations',
                                  'copied resource declarations do not restore original runtime state',
                                  'indirect targets remain unknown; original vtable/table evidence must be consulted',
                                  'synthetic output must not be used as a behavior oracle'],
        'wabt_archive_sha256': ARCHIVE_SHA, 'wabt_tools': tool_identities, 'invocations': invocations,
        'target_executed': False, 'synthetic_module_executed': False, 'generated_c_compiled_or_executed': False,
        'artifacts': {path.name: {'bytes': path.stat().st_size, 'sha256': sha(path)}
                      for path in sorted(output.iterdir()) if path.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'output_directory': str(output), 'original_function': args.function,
                      'producer_script_sha256': script_sha,
                      'direct_call_sites': len(direct), 'named_callee_imports': len(callees),
                      'indirect_call_sites': len(indirect), 'c_bytes': c_file.stat().st_size,
                      'c_entry_points': c_entries,
                      'exact_wat_round_trip_verified': True, 'target_executed': False}))


if __name__ == '__main__':
    main()
