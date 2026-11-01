#!/usr/bin/env python3
"""Freeze current0.134.0 new-record helpers and guard their operation order."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import struct

from build_full134_oracle import ROOT, SOURCE, SOURCE_SHA
from build_upgrade134_oracle import sha
from extract_catalogue134 import parse_binary, reconstruct

PROFILE = ROOT / 'evidence/wasm0134-profile-20261101T001728.222975Z'
FUNCTIONS = (1073, 26967, 26591, 85718)


def static_snapshot(out=None):
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Official0.134.0 identity differs')
    manifest = json.loads((PROFILE / 'manifest.json').read_text())
    if manifest['original_sha256'] != SOURCE_SHA or manifest['target_version'] != '0.134.0':
        raise ValueError('Frozen current profile differs')
    wat, db = Path(manifest['wat_path']), Path(manifest['database_path'])
    if sha(wat) != manifest['wat_sha256'] or sha(db) != manifest['database_sha256']:
        raise ValueError('Frozen WAT/database identity differs')
    if out is None:
        out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('new-ability0134-static-%Y%m%dT%H%M%S.%fZ')
        out.mkdir(parents=True, exist_ok=False)
    binary = SOURCE.read_bytes()
    profile = parse_binary(binary)
    memory = reconstruct(binary, profile)
    con = sqlite3.connect('file:' + str(db) + '?mode=ro', uri=True)
    functions, texts = {}, {}
    with wat.open('rb') as stream:
        for idx in FUNCTIONS:
            a, b, line, ba, bb = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end FROM functions WHERE idx=?', (idx,)).fetchone()
            stream.seek(a); text = stream.read(b - a)
            if not text.startswith(f'  (func (;{idx};)'.encode()) or (ba, bb) != profile['bodies'][idx]:
                raise ValueError('Full current helper range differs')
            (out / f'function-{idx}.wat').write_bytes(text)
            (out / f'function-{idx}.body.bin').write_bytes(binary[ba:bb])
            texts[idx] = text.decode().splitlines()
            functions[str(idx)] = {'wat_start_line': line, 'wat_start': a, 'wat_end': b,
                'wat_sha256': hashlib.sha256(text).hexdigest(), 'body_start': ba, 'body_end': bb,
                'body_sha256': hashlib.sha256(binary[ba:bb]).hexdigest()}
    con.close()
    guards = []
    def guard(idx, label, seq):
        lines = [x.strip() for x in texts[idx]]
        sites = [i for i in range(len(lines) - len(seq) + 1) if lines[i:i+len(seq)] == seq]
        if not sites:
            raise ValueError(f'Current helper order guard missing: {idx} {label}')
        guards.append({'function': idx, 'label': label, 'sites': sites,
            'absolute_wat_lines': [functions[str(idx)]['wat_start_line'] + i for i in sites], 'instructions': seq})
    guard(1073, 'new helper receives explicit G+2016 snapshot before tier helper', [
        'i32.const 252', 'i32.add', 'local.get 0', 'i32.const 2016', 'i32.add', 'local.get 4', 'call 26967',
        'local.get 3', 'i32.const 104', 'i32.add', 'local.tee 4', 'local.get 3', 'i32.const 200', 'i32.add',
        'local.tee 2', 'local.get 10', 'call 26591'])
    guard(1073, 'new record starts cooldown0.5 and damage1', ['local.get 3',
        'i64.const 4575657222465388544', 'i64.store offset=208 align=4'])
    guard(26967, '20B modifier stride and count', ['i32.load offset=16', 'local.tee 13', 'local.get 11', 'i32.const 20', 'i32.mul', 'i32.add'])
    guard(26967, 'filter tag dispatch', ['i32.load8_u', 'i32.const 1', 'i32.sub', 'br_table 2 (;@7;) 0 (;@9;) 3 (;@6;) 1 (;@8;) 5 (;@4;) 5 (;@4;) 6 (;@3;)'])
    guard(26967, 'numeric kind dispatch', ['i32.load8_u offset=12', 'i32.const 1', 'i32.sub', 'br_table 1 (;@9;) 2 (;@8;) 3 (;@7;) 4 (;@6;) 5 (;@5;) 6 (;@4;) 0 (;@10;)'])
    for slot, local in ((0,10),(12,9),(16,8),(20,7),(24,6)):
        store = 'f32.store' + (f' offset={slot}' if slot else '')
        guard(26967, f'ordered additive output{slot}', ['local.get 0', f'local.get {local}', 'local.get 3', 'f32.add', f'local.tee {local}', store])
    for local,label in ((5,'cooldown reduction'),(4,'targets before round')):
        guard(26967, f'ordered {label} accumulation', [f'local.get {local}', 'local.get 3', 'f32.add', f'local.set {local}'])
    guard(26967, 'round helper before saturating target conversion', ['local.get 0', 'local.get 4', 'call 85718', 'i32.trunc_sat_f32_u', 'i32.store offset=8'])
    guard(26967, 'cooldown subtract then NaN select then max0.4', ['f32.const 0x1.99999ap-2 (;=0.4;)', 'f32.const 0x1p+0 (;=1;)', 'local.get 5', 'f32.sub', 'local.tee 3', 'local.get 3', 'local.get 3', 'f32.ne', 'select', 'local.tee 3', 'f32.const 0x1.99999ap-2 (;=0.4;)', 'local.get 3', 'f32.const 0x1.99999ap-2 (;=0.4;)', 'f32.gt', 'select', 'f32.store offset=4)'])
    guard(26591, 'tier0 copy without table read', ['local.get 2', 'i32.eqz', 'if  ;; label = @2', 'local.get 0', 'local.get 1', 'i32.const 80', 'memory.copy'])
    guard(26591, 'execution classification', ['i32.load8_u offset=84', 'i32.const 9', 'i32.sub', 'br_table 1 (;@11;) 3 (;@9;) 0 (;@12;) 3 (;@9;)'])
    guard(26591, 'effect-tag mask', ['i32.const 1', 'local.get 4', 'i32.shl', 'i32.const 8384', 'i32.and'])
    guard(26591, 'tier cooldown order', ['f32.load offset=16', 'f32.const 0x1p+0 (;=1;)', 'local.get 4', 'i32.const 2', 'i32.shl', 'f32.load offset=5879624', 'local.tee 8', 'f32.sub', 'f32.mul', 'f32.store offset=16'])
    guard(26591, 'tier damage order', ['f32.load offset=12', 'local.get 4', 'i32.const 2', 'i32.shl', 'f32.load offset=5879676', 'local.tee 8', 'f32.const 0x1p+0 (;=1;)', 'f32.add', 'f32.mul', 'f32.store offset=12'])
    guard(85718, 'binary32 bias before integer mask', ['local.get 0', 'f32.const 0x1.fffffep-2 (;=0.5;)', 'local.get 0', 'f32.copysign', 'f32.add', 'local.tee 0', 'i32.reinterpret_f32'])
    definitions = []
    for i in range(114):
        pointer = 5463472 + i*88
        raw = memory[pointer:pointer+88]
        idptr, idlen = struct.unpack_from('<II', raw, 12)
        kindptr, kindlen = struct.unpack_from('<II', raw, 36)
        definitions.append({'pointer': pointer, 'ability_id': bytes(memory[idptr:idptr+idlen]).decode('ascii'),
            'execution_kind': raw[84], 'school': raw[85], 'effect_tag': struct.unpack_from('<I',raw)[0],
            'base_damage_bits': struct.unpack_from('<I',raw,48)[0], 'kinds': list(memory[kindptr:kindptr+kindlen]),
            'raw88_hex': bytes(raw).hex()})
    tables = {'cooldown_address': 5879624, 'cooldown_bits': list(struct.unpack_from('<5I',memory,5879624)),
        'damage_address': 5879676, 'damage_bits': list(struct.unpack_from('<5I',memory,5879676))}
    result = {'version': '0.134.0', 'build': '983346a7', 'source_sha256': SOURCE_SHA,
        'profile_manifest_sha256': sha(PROFILE/'manifest.json'), 'wat_sha256': manifest['wat_sha256'],
        'database_sha256': manifest['database_sha256'], 'database_read_only': True,
        'full_functions': functions, 'guards': guards, 'definitions': definitions, 'tables': tables,
        'evidence_directory': str(out), 'target_executed': False}
    (out/'static-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Official source changed during static trace')
    return result


if __name__ == '__main__':
    result = static_snapshot()
    print(json.dumps({'directory':result['evidence_directory'], 'definitions':len(result['definitions']),
        'tables':result['tables'], 'guards':len(result['guards'])}))
