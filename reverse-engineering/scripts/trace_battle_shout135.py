#!/usr/bin/env python3
"""Read-only indexed Battle Shout922/1076/2088 provenance; zero execution."""
from pathlib import Path
import hashlib
import json
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
from build_full135_oracle import SOURCE, SOURCE_SHA, parse_source


def trace_battle_shout135(out):
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    _, _, _, bodies, segments = parse_source(raw)
    pointer, size = 5467956, 88
    definition = bytearray(size)
    for segment in segments:
        if segment['address'] is None:
            continue
        start = max(pointer, segment['address'])
        end = min(pointer + size, segment['address'] + segment['length'])
        if start < end:
            offset = segment['file_offset'] + start - segment['address']
            definition[start - pointer:end - pointer] = raw[offset:offset + end - start]
    profile = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
    database = sqlite3.connect((profile / 'index.sqlite').as_uri() + '?mode=ro', uri=True)
    functions = []
    with (profile / 'official-0.135.1-full.wat').open('rb') as stream:
        for index in (922, 1076, 2088, 1512, 1202, 27562, 29983, 44446):
            a, b, line, start, end = database.execute(
                'select wat_start,wat_end,wat_line,body_start,body_end from functions where idx=?', (index,)).fetchone()
            assert b - a < 524288 and bodies[index] == (start, end)
            stream.seek(a)
            text = stream.read(b - a)
            (out / f'battle-{index}.wat').write_bytes(text)
            functions.append(dict(index=index, wat_start=a, wat_end=b, wat_line=line,
                wat_sha256=hashlib.sha256(text).hexdigest(), body_start=start, body_end=end,
                body_sha256=hashlib.sha256(raw[start:end]).hexdigest(), direct_callees=[row[0] for row in
                    database.execute('select distinct callee from calls where caller=? order by callee', (index,))]))
    database.close()
    result = dict(version='0.135.1', actual_build='90898d5e3', original_sha256=SOURCE_SHA,
        definition_pointer=pointer, definition88_hex=definition.hex(), definition88_sha256=hashlib.sha256(definition).hexdigest(),
        functions=functions, original_executed=False, index_seek_only=True, full_wat_read=False,
        rules=['922 execution9/effect8 enters the real generic self-buff branch; spell6673/school0.',
            'Append attempts before target30 eligibility; busy488 or context908 bit0 gates only ledger3.',
            'Strength=owned76*definition4; duration=maxNumeric(.1,((definition68*1.4)*owned28)*owned68).',
            'Stable-remove only same6673 ownerGUID0 rows; append32B kind8, actual1512 then actual1202.',
            '1076 owns initial countdown, pre-call infinity, retry.2 and successCD=max(.25,(((16*1.4)*owned16)*owned56)*G1544).',
            '2088 expiry precedes1512/1202, shield clamp/regen and1076; expiry does not itself recast.'],
        unknown_words=['New effect8 live+16 is unwritten scratch; only that new word is explicitly unspecified.',
            'Existing declared unknown live words retain per-record masks through stable removal/remapping.'],
        pending=['Nonempty external stat/item/talent/proc source continuation.',
            '1202 physical aura/object keys and encoded packets are not numeric effect8 completion.'])
    (out / 'battle-shout135-static.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    from datetime import datetime, timezone
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('battle-shout0135-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    trace_battle_shout135(out)
    print(json.dumps(dict(directory=str(out), original_executed=False)))
