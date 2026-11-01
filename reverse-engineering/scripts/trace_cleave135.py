#!/usr/bin/env python3
"""Index-seek cleave135 static evidence; never executes the target program."""
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import struct

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source
from trace_ecs_forward import structural_targets

PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
FUNCTIONS = (922, 1076, 8685, 27562, 43468, 914, 2244)


def main():
    binary = SOURCE.read_bytes()
    assert hashlib.sha256(binary).hexdigest() == SOURCE_SHA
    types, imports, declarations, bodies, segments = parse_source(binary)
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('cleave0135-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    functions, texts = [], {}
    with sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro', uri=True) as con:
        with (PROFILE / 'official-0.135.1-full.wat').open('rb') as wat:
            for index in FUNCTIONS:
                ws, we, bs, be = con.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?', (index,)).fetchone()
                assert bodies[index] == (bs, be)
                wat.seek(ws)
                raw = wat.read(we - ws)
                assert raw.startswith(f'  (func (;{index};) '.encode())
                (out / f'{index}.wat').write_bytes(raw)
                texts[index] = [line.strip() for line in raw.decode().splitlines()]
                signature = types[declarations[index - len(imports)]]
                functions.append(dict(index=index, wat_start=ws, wat_end=we,
                    body_sha256=hashlib.sha256(binary[bs:be]).hexdigest(),
                    wat_sha256=hashlib.sha256(raw).hexdigest(),
                    parameters_hex=signature[0].hex(), results_hex=signature[1].hex()))
    memory = bytearray(max(s['address'] + s['length'] for s in segments if s['address'] is not None))
    for s in segments:
        if s['address'] is not None:
            memory[s['address']:s['address'] + s['length']] = binary[s['file_offset']:s['file_offset'] + s['length']]
    pointer = 5467428
    raw = bytes(memory[pointer:pointer + 88])
    words = struct.unpack('<22I', raw)
    assert bytes(memory[words[3]:words[3] + words[4]]) == b'cleave'
    assert (words[0], words[11], raw[84]) == (0, 845, 5)
    dispatch = next(n + 1 for n, line in enumerate(texts[922]) if line.startswith('br_table '))
    effect = next(n + 1 for n, line in enumerate(texts[2244]) if line.startswith('br_table '))
    branch = structural_targets(texts[922], {dispatch: 3})[dispatch]
    no_effect = structural_targets(texts[2244], {effect: 0xffffffff})[effect]
    assert branch['target']['end_function_line'] == 9168
    assert no_effect['target']['end_function_line'] == 1542
    result = dict(version='0.135.1', build='0898d5e3', original_wasm_sha256=SOURCE_SHA,
        target_executed=False, full_wat_read=False, index_seek_only=True,
        functions=functions, cleave_definition=dict(pointer=pointer, words=list(words), hex=raw.hex(),
            ability_id='cleave', spell_id=845, execution_kind=5, effect_tag=0,
            damage=47, cooldown=1.5, range=7, count=3),
        coefficient_table_words=list(struct.unpack_from('<7I', memory, 1595788)),
        execution_branch=branch, effect0_return_branch=no_effect,
        static_rules=[
            '922 exec5/7 branch begins at function line9169; exec7-only sorting and low-health doubling do not apply to cleave.',
            '922 uses8685 priority query at definition+56; count additions wrap u32, clamp minimum1, then available count.',
            'Each selected GUID calls43468 then914 immediately, then2244; no8295 projectile queue.',
            '43468 identifier lengths9/11 gate special bonus sources; cleave length6 skips them but still advances RNG once.',
            '2244 effect0 subtracts1, selects default, and returns after restoring its stack.',
            '1076 owns countdown, class melee prelude and embedded G1256 racial80; this fixture supplies effect0 in that slot and calls unchanged922.'],
        source_file='scripts/trace_cleave135.py',
        source_sha256=hashlib.sha256((ROOT / 'scripts/trace_cleave135.py').read_bytes()).hexdigest())
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), functions=len(functions), target_executed=False)))


if __name__ == '__main__':
    main()
