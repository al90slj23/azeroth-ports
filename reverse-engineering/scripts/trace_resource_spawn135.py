#!/usr/bin/env python3
"""Bounded indexed resource947/1417 provenance, zero execution."""
from pathlib import Path
import hashlib
import json
import sqlite3
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
from build_full135_oracle import SOURCE, SOURCE_SHA, parse_source


def trace_resource_spawn135(out):
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    _, _, _, bodies, _ = parse_source(raw)
    profile = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
    db = sqlite3.connect((profile / 'index.sqlite').as_uri() + '?mode=ro', uri=True)
    functions = []
    with (profile / 'official-0.135.1-full.wat').open('rb') as stream:
        for index in (947, 1417, 13516, 1821, 29631, 23181, 26970, 50798, 65337):
            a, b, line, start, end = db.execute(
                'select wat_start,wat_end,wat_line,body_start,body_end from functions where idx=?', (index,)).fetchone()
            assert b - a < 524288 and bodies[index] == (start, end)
            stream.seek(a); text = stream.read(b - a)
            (out / f'resource-{index}.wat').write_bytes(text)
            functions.append(dict(index=index, wat_start=a, wat_end=b, wat_line=line,
                wat_sha256=hashlib.sha256(text).hexdigest(), body_start=start, body_end=end,
                body_sha256=hashlib.sha256(raw[start:end]).hexdigest(), direct_callees=[row[0] for row in
                    db.execute('select distinct callee from calls where caller=? order by callee', (index,))]))
    db.close()
    result = dict(version='0.135.1', actual_build='90898d5e3', original_sha256=SOURCE_SHA,
        functions=functions, original_executed=False, index_seek_only=True, full_wat_read=False,
        rules=['947 due G2352>=G2444 writes G2444=now+45 before active pickup56 kind3..5 combined cap2; marker ignored.',
            'Inlined xoshiro128++ multiply3 rejects (lowProduct&0xc0000000)==0xc0000000; accepted highProduct selects kind3/4/5.',
            '1417 amount argument is post-selection local2/state0, before13516 advances shared RNG.',
            '13516 samples actual world at radius15..40, then1417 clamp radius-2 and final world height.',
            '1417 kinds3/4/5: visual9006/9007/9008, display5931/5995/5991, scale1, actor kind21=5 flags9=0.',
            '1821 uses shared counter, xoshiro yaw, GUID F110|entry<<24|counter; exact169 via26970/50798.',
            'Append56 writes0,8..55 only; +4 and prior backing retained; aux Vec(cap0,ptr8,len0).'],
        pending=['1417 other kinds and kind6 auxiliary objects.',
            '1417 primary-present nearest-miss low-address fallback.',
            'Resource kind3..5 collection and gameplay effects.',
            '947 G2424/G2440/G2448/Boss due consumers are not this component.',
            'Explicit40 single947 is not natural40-second full880 acceptance.'])
    (out / 'resource-spawn135-static.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    from datetime import datetime, timezone
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('resource-spawn0135-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(); trace_resource_spawn135(out)
    print(json.dumps(dict(directory=str(out), original_executed=False)))
