#!/usr/bin/env python3
"""Stream a complete WABT decode into focused, explicitly local REA Evidence.

This does not change REA's stock WASM admission guard. It inspects the exact
original module and records selected complete functions with binary/WAT ranges.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'
WABT_ARCHIVE_SHA = '3f654779b436c628db3ca4323c51538815f5fbc887a6d5f3bb1c18d36281e240'
SELECTED = {905, 1065, 4201, 12692, 15920, 25238, 25242, 81718}
PRESENCE_ADDRESS = 1486550


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def command(argv, stdout, stderr, timeout=120):
    started = time.monotonic()
    with stdout.open('wb') as out, stderr.open('wb') as err:
        p = subprocess.Popen([str(x) for x in argv], stdout=out, stderr=err,
                             start_new_session=True)
        try:
            code = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            raise SystemExit('Owned WABT command exceeded deadline and was stopped')
    if code:
        raise SystemExit(f'WABT exited {code}; inspect {stderr}')
    return {'arguments': [str(x) for x in argv], 'exit_code': code,
            'elapsed_seconds': round(time.monotonic() - started, 3)}


def binary_functions(data, requested=None):
    requested = SELECTED if requested is None else set(requested)
    def uint(p):
        value = shift = 0
        while p < len(data) and shift <= 28:
            byte = data[p]; p += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, p
            shift += 7
        raise ValueError('Invalid u32 LEB')
    assert data[:8] == b'\0asm\1\0\0\0'
    p = 8
    sections = {}
    while p < len(data):
        kind = data[p]; size, begin = uint(p + 1)
        end = begin + size
        assert end <= len(data)
        sections[kind] = (begin, end)
        p = end
    count, p = uint(sections[2][0])
    imported = 0
    for _ in range(count):
        for _ in range(2):
            length, p = uint(p); p += length
        kind = data[p]; p += 1
        # Exact target profile: all 878 imports are functions.
        assert kind == 0
        _, p = uint(p); imported += 1
    count, p = uint(sections[10][0])
    selected = {}
    for local_index in range(count):
        leb = p; length, begin = uint(p); p = begin + length
        index = local_index + imported
        if index in requested:
            selected[index] = {'function_index': index, 'code_body_index': local_index,
                               'size_leb_offset': leb, 'body_start': begin, 'body_end': p,
                               'body_bytes': length,
                               'body_sha256': hashlib.sha256(data[begin:p]).hexdigest()}
    assert p == sections[10][1]
    if set(selected) != requested:
        raise ValueError('Requested indices must identify existing local functions')
    return imported, count, selected


def extract(wat, output, selected, call_targets=(630, 25238, 25242)):
    head = re.compile(rb'^  \(func \(;(\d+);\)')
    current = None
    written = None
    calls = []
    url_references = []
    lua_references = []
    offset = 0
    wat_line = 0
    target_calls = set(call_targets)
    direct_call = re.compile(rb'^(call|return_call) (\d+)\)*$')
    with wat.open('rb') as stream:
        for line in stream:
            wat_line += 1
            if line.startswith(b'  (') or line == b')\n':
                match = head.match(line)
                if match is None and line.startswith(b'  (func '):
                    raise ValueError('Unexpected WABT function header')
                if written is not None:
                    written.close(); written = None
                if current in selected:
                    selected[current]['wat_end'] = offset
                current = int(match[1]) if match else None
                if current in selected:
                    selected[current]['wat_start'] = offset
                    selected[current]['wat_start_line'] = wat_line
                    written = (output / f'function-{current}.wat').open('wb')
            if written is not None:
                written.write(line)
            stripped = line.strip()
            if current is not None and stripped.startswith((b'call ', b'return_call ')):
                call = direct_call.fullmatch(stripped)
                if call is not None and int(call[2]) in target_calls:
                    calls.append({'caller': current, 'callee': int(call[2]), 'instruction': call[1].decode(),
                              'wat_offset': offset, 'wat_line': wat_line})
            instruction = stripped.rstrip(b')')
            if current is not None and instruction == f'i32.const {PRESENCE_ADDRESS}'.encode():
                url_references.append({'function_index': current, 'wat_offset': offset,
                                       'wat_line': wat_line})
            if current is not None and instruction == b'i32.const 1758940':
                lua_references.append({'function_index': current, 'wat_offset': offset,
                                       'wat_line': wat_line, 'linear_memory_address': 1758940})
            offset += len(line)
    if written is not None:
        written.close()
    for index, item in selected.items():
        path = output / f'function-{index}.wat'
        assert item['wat_end'] - item['wat_start'] == path.stat().st_size
        item['wat_bytes'] = path.stat().st_size
        item['wat_sha256'] = sha(path)
        item['wat_file'] = path.name
    return calls, url_references, lua_references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-preflight', type=Path,
                        help='Reuse an existing recorded WABT preflight with matching provenance')
    parser.add_argument('--functions', type=int, nargs='+', default=sorted(SELECTED),
                        help='Complete local function indices to retain; defaults to the original eight')
    parser.add_argument('--call-targets', type=int, nargs='+', default=[630, 25238, 25242],
                        help='Direct call/return_call targets to index, including final-line calls')
    args = parser.parse_args()
    wasm = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(wasm) != ORIGINAL_SHA:
        raise SystemExit('Original 0.126.0 core identity changed')
    if any(i < 0 for i in args.functions + args.call_targets):
        parser.error('Function indices must be nonnegative')
    imported, defined, selected = binary_functions(wasm.read_bytes(), args.functions)
    tools = ROOT / '.toolchain/rea-wasm-profile'
    archive = tools / 'wabt-1.0.42-macos-arm64.tar.gz'
    if sha(archive) != WABT_ARCHIVE_SHA:
        raise SystemExit('WABT archive identity changed')
    binary = tools / 'wabt/wabt-1.0.42/bin'
    identities = {}
    for name in ('wasm-validate', 'wasm-objdump', 'wasm2wat'):
        path = binary / name
        version = subprocess.check_output([str(path), '--version'], text=True).strip()
        if version != '1.0.42':
            raise SystemExit('Unsupported WABT tool version')
        identities[name] = {'version': version, 'sha256': sha(path)}
    output = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('wasm-focused-%Y%m%dT%H%M%S.%fZ')
    output.mkdir(parents=True, exist_ok=False)
    invocations = []
    if args.reuse_preflight:
        provenance = json.loads((args.reuse_preflight / 'producer-provenance.json').read_text())
        wat = args.reuse_preflight / 'original-full.wat'
        if (provenance['original_sha256'] != ORIGINAL_SHA or
                provenance['wabt_tools'] != identities or provenance['wat_sha256'] != sha(wat)):
            raise SystemExit('Existing producer run identity does not match')
        invocations = provenance['invocations']
    else:
        invocations.append(command([binary / 'wasm-validate', '--enable-all', '--ignore-custom-section-errors', wasm],
                                   output / 'validate.stdout.txt', output / 'validate.stderr.txt'))
        invocations.append(command([binary / 'wasm-objdump', '-h', wasm],
                                   output / 'headers.txt', output / 'headers.stderr.txt'))
        wat = output / 'original-full.wat'
        invocations.append(command([binary / 'wasm2wat', '--enable-all', '--ignore-custom-section-errors', wasm, '-o', wat],
                                   output / 'decode.stdout.txt', output / 'decode.stderr.txt'))
        provenance = {'original_sha256': ORIGINAL_SHA, 'wabt_tools': identities,
                      'wat_sha256': sha(wat), 'wat_bytes': wat.stat().st_size,
                      'invocations': invocations}
        (output / 'producer-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    calls, url_references, lua_references = extract(wat, output, selected, args.call_targets)
    result = {'profile': 'local-focused-extension; not stock REA inspect_wasm_artifact',
              'original_module': {'path': str(wasm), 'bytes': wasm.stat().st_size, 'sha256': ORIGINAL_SHA},
              'wabt_archive_sha256': WABT_ARCHIVE_SHA, 'wabt_tools': identities,
              'full_module_validated': True, 'full_wat': {'path': str(wat), 'bytes': wat.stat().st_size,
                                                         'sha256': provenance['wat_sha256']},
              'function_imports': imported, 'defined_functions': defined,
              'selected_complete_functions': list(selected.values()), 'direct_call_sites': calls,
              'indexed_direct_call_kinds': ['call', 'return_call'],
              'indexed_call_targets': sorted(set(args.call_targets)),
              'presence_url_memory_address': PRESENCE_ADDRESS, 'presence_url_references': url_references,
              'lua_api_source_references': lua_references,
              'invocations': invocations, 'target_executed': False,
              'max_child_rss_bytes_on_macos': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}
    facts = output / 'focused-facts.json'; facts.write_text(json.dumps(result, indent=2) + '\n')
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    subprocess.run([str(runtime), str(ROOT / 'scripts/wasm_seal.mjs'), str(facts)], check=True)
    if sha(wasm) != ORIGINAL_SHA:
        raise SystemExit('Original core changed during analysis')
    print(json.dumps({'output_directory': str(output), 'complete_function_count': len(selected),
                      'original_preserved': True, 'target_executed': False}))


if __name__ == '__main__':
    main()
