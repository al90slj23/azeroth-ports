#!/usr/bin/env python3
"""Bounded indexed event947/1560/31520 provenance, zero execution."""
from pathlib import Path
import hashlib
import json
import sqlite3
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
from build_full135_oracle import SOURCE, SOURCE_SHA, parse_source


def trace_event_wave135(out):
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    _, _, _, bodies, _ = parse_source(raw)
    profile = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
    db = sqlite3.connect((profile / 'index.sqlite').as_uri() + '?mode=ro', uri=True)
    functions = []
    with (profile / 'official-0.135.1-full.wat').open('rb') as stream:
        for index in (947,1560,6730,1089,5736,8751,31520,19964,17979,20272,80447):
            a, b, line, start, end = db.execute(
                'select wat_start,wat_end,wat_line,body_start,body_end from functions where idx=?', (index,)).fetchone()
            assert b - a < 1048576 and bodies[index] == (start, end)
            stream.seek(a); text = stream.read(b - a)
            (out / f'event-{index}.wat').write_bytes(text)
            functions.append(dict(index=index, wat_start=a, wat_end=b, wat_line=line,
                wat_sha256=hashlib.sha256(text).hexdigest(), body_start=start, body_end=end,
                body_sha256=hashlib.sha256(raw[start:end]).hexdigest(), direct_callees=[row[0] for row in
                    db.execute('select distinct callee from calls where caller=? order by callee', (index,))]))
    db.close()
    result = dict(version='0.135.1', actual_build='90898d5e3', original_sha256=SOURCE_SHA,
        functions=functions, original_executed=False, index_seek_only=True, full_wat_read=False,
        rules=['G2424 event0swarm/event1stampede/event2wall/event3pack, distinct from following Boss2456/2460.', '1560 explicitly writes scratch2674=255; Game scratch88 copy means G2586=255.', 'G2424 deadline now+max(35,60−1.5*minute); eligible-empty still advances.', '31520 refuses any nonzero inbounds nav; inline swarm/wall pathNone rejects onlynav1.', 'stampede writes unit16/20/24/28/348 by returnedGUID owner; consumers remain separate.'], pending=['Mode1/party ownership', 'Whole601-frame original composition not validated by component947'])
    (out / 'event-wave135-static.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    from datetime import datetime, timezone
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('event-wave0135-static-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(); trace_event_wave135(out)
    print(json.dumps(dict(directory=str(out), original_executed=False)))
