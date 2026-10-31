#!/usr/bin/env python3
"""Extract two identified Lua source chunks without executing the target.

This auxiliary extractor supports the REA investigation; it is not a stock REA
Lua analyzer. Original source bytes stay in ignored local evidence directories.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_BYTES = 90116970
ORIGINAL_SHA256 = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'
CHUNKS = [
    {
        'name': 'AZSApi', 'start': 77755796, 'end': 77774732,
        'sha256': '34cbd3f976e6207783b365e881fcce580b6cd1f6fe886660418bcbbd6d61bb54',
        'named_functions': 39, 'following': b'HUD_CVARS_LUA',
        'source_kind': 'embedded addon API source template with HUD_CVARS_LUA placeholder',
    },
    {
        'name': 'AZSCharacterStats', 'start': 81306394, 'end': 81314978,
        'sha256': '5ae575eb7b036b413f2eb7a33c93dec1af8488b532fde3acd19b2bcccf1f151e',
        'named_functions': 11, 'following': b'Worn gear: ',
        'source_kind': 'embedded character-pane source reading host-reported statistics',
    },
]
EXPECTED_PREFIXES = [
    'AZSRUN', 'AZSZONE', 'AZSBOSSES', 'AZSUNITS', 'AZSDEBUFFS', 'AZSTGT',
    'AZSSPELLS', 'AZSTIMERS', 'AZSBUFFS', 'AZSPETS', 'AZSTOTEMS', 'AZSMETER',
    'AZSHEAL', 'AZSBOSSDMG', 'AZSREVIVE', 'AZSPARTY', 'AZSCHESTS', 'AZSLAIRS',
    'AZSTAKEN', 'AZSEND', 'AZSBANNER', 'AZS',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inspect_source(wasm):
    if len(wasm) != ORIGINAL_BYTES or sha(wasm) != ORIGINAL_SHA256:
        raise ValueError('Original WASM identity differs; add a reviewed version baseline first')
    chunks = []
    for expected in CHUNKS:
        data = wasm[expected['start']:expected['end']]
        if sha(data) != expected['sha256']:
            raise ValueError('Embedded source boundary/hash changed: ' + expected['name'])
        following = wasm[expected['end']:expected['end'] + len(expected['following'])]
        if following != expected['following']:
            raise ValueError('Following literal changed: ' + expected['name'])
        text = data.decode('utf-8', errors='strict')
        functions = [
            {'name': m.group(1), 'parameters': m.group(2),
             'line': text.count('\n', 0, m.start()) + 1,
             'wasm_file_offset': expected['start'] + len(text[:m.start()].encode())}
            for m in re.finditer(r'(?m)^function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)', text)
        ]
        if len(functions) != expected['named_functions']:
            raise ValueError('Unexpected lexical function index: ' + expected['name'])
        chunks.append({'name': expected['name'], 'source_kind': expected['source_kind'],
                       'file_start': expected['start'], 'file_end_exclusive': expected['end'],
                       'bytes': len(data), 'sha256': sha(data),
                       'named_function_count': len(functions), 'functions': functions,
                       'anonymous_function_count': len(re.findall(r'\bfunction\s*\(', text)),
                       'source': data})
    api = chunks[0]['source'].decode()
    dispatcher = api[api.index('function AZS_ApiOnEvent()'):api.index('AZSApiFrame = CreateFrame')]
    matches = list(re.finditer(r'(?:if|elseif) \( arg1 == "([A-Z]+)" \) then', dispatcher))
    prefixes = []
    for i, match in enumerate(matches):
        stop = matches[i + 1].start() if i + 1 < len(matches) else len(dispatcher)
        body = dispatcher[match.end():stop]
        assignment = re.search(r'\b(AZS_[A-Z][A-Z0-9_]*) = (AZS_[A-Za-z0-9_]+)\(arg2(?:, \{ ([^}]*) \})?\)', body)
        prefixes.append({'prefix': match.group(1),
                         'cache': assignment.group(1) if assignment else None,
                         'parser': assignment.group(2) if assignment else 'AZS_OnBanner',
                         'ordered_fields': re.findall(r'"([A-Za-z0-9_]+)"', assignment.group(3) or '') if assignment else []})
    if [item['prefix'] for item in prefixes] != EXPECTED_PREFIXES:
        raise ValueError('Unexpected message-prefix index')
    # Exact pointer/length constants support the addon template's selected span.
    if wasm[20720030:20720039] != bytes.fromhex('41dcadeb0041f89301'):
        raise ValueError('Embedded API pointer/length anchor changed')
    return chunks, prefixes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wasm', type=Path,
                        default=ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm')
    parser.add_argument('--compile', action='store_true', help='Optional LuaJIT -b syntax check; never execute the chunk')
    parser.add_argument('--luajit', type=Path, help='Existing LuaJIT executable for --compile')
    args = parser.parse_args()
    if args.luajit and not args.compile:
        parser.error('--luajit requires --compile')
    compiler = str(args.luajit) if args.luajit else shutil.which('luajit')
    if args.compile and not compiler:
        parser.error('--compile requires an existing LuaJIT; supply --luajit')
    source = args.wasm.resolve(strict=True)
    chunks, messages = inspect_source(source.read_bytes())
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ-embedded-lua')
    run.mkdir(parents=True, exist_ok=False)
    for chunk in chunks:
        data = chunk.pop('source')
        file = run / (chunk['name'] + '.original.lua')
        file.write_bytes(data)
        chunk['compile_check'] = {'performed': False, 'target_executed': False}
        if args.compile:
            bytecode = run / (chunk['name'] + '.compile-check.luac')
            subprocess.run([compiler, '-b', str(file), str(bytecode)], check=True)
            chunk['compile_check'] = {'performed': True, 'operation': 'LuaJIT -b compile only',
                                      'exit_code': 0, 'bytecode_sha256': sha(bytecode.read_bytes()),
                                      'target_executed': False}
    report = {
        'game_version': '0.126.0', 'game_build': '3e72472a',
        'original_wasm_bytes': ORIGINAL_BYTES, 'original_wasm_sha256': ORIGINAL_SHA256,
        'analysis_method': 'local exact-byte extraction and lexical indexing; auxiliary to REA, not stock REA Lua semantic analysis',
        'chunks': chunks, 'message_prefix_count': len(messages), 'messages': messages,
        'api_template_boundary_support': {
            'data_segment': 3488, 'memory_start': 1758940, 'memory_end_exclusive': 1777876,
            'code_body_index': 3323, 'pointer_length_file_offset': 20720030,
            'pointer_length_bytes': '41dcadeb0041f89301',
            'qualification': 'matching byte sequence in a declared code body; not independently instruction-decoded here',
        },
        'cvar_actions': {'AZS_OpenStoredLevels': 'spendLevels=1',
                        'AZS_SetStoringLevels': 'storeLevels=1/0',
                        'AZS_SetHudShown': 'selected/all HUD variables from the host-expanded map'},
        'other_ui_actions': ['sorted frame-name CSV for UI stacking', 'banner handler registration and bounded history'],
        'limitations': [
            'The addon API is a source template containing the unexpanded HUD_CVARS_LUA placeholder.',
            'Lexical function/message indexing is not a complete Lua semantic or control/data-flow proof.',
            'Source-template extraction does not recover Rust combat implementation or actual damage rules.',
            'Optional LuaJIT compilation checks syntax only; host globals and runtime behavior stay unverified.',
            'No target code, message injection, game-value patch or user-save mutation is performed.',
        ],
    }
    with source.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != ORIGINAL_SHA256:
            raise SystemExit('Original WASM changed while extracting')
    (run / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'run_directory': str(run), 'chunks': len(chunks),
                      'named_functions': sum(c['named_function_count'] for c in chunks),
                      'message_prefixes': len(messages), 'original_preserved': True,
                      'target_executed': False}))


if __name__ == '__main__':
    main()
