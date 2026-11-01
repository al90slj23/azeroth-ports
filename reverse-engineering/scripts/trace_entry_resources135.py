#!/usr/bin/env python3
"""Static entry/resource evidence only; never instantiate WASM or access hosts."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, re, sqlite3
from extract_catalogue134 import parse_binary

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT_SHA = '15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
INDEX_SHA = 'b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
DEFAULT = (1089,4546,95986,23171,50449,96127,67826,19179,122098,1744,13516,
           5112,5893,20468,27849,41301,48393,75619,90403,95999,96128,102275)


def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--functions', nargs='+', type=int, default=DEFAULT)
    args = p.parse_args(); indices = tuple(dict.fromkeys(args.functions))
    assert len(indices) <= 80 and all(878 <= i < 176195 for i in indices)
    assert sha(SOURCE) == SOURCE_SHA and sha(PROFILE / 'index.sqlite') == INDEX_SHA
    assert sha(PROFILE / 'official-0.135.1-full.wat') == WAT_SHA
    files = (Path(__file__), ROOT / 'scripts/extract_catalogue134.py')
    before = {str(x.relative_to(ROOT)): sha(x) for x in files}
    raw = SOURCE.read_bytes(); profile = parse_binary(raw)
    assert profile['function_imports'] == 878 and profile['defined_functions'] == 175317
    memory = bytearray(max(s['memory_start'] + s['file_end'] - s['file_start'] for s in profile['segments']))
    for s in profile['segments']:
        memory[s['memory_start']:s['memory_start'] + s['file_end'] - s['file_start']] = raw[s['file_start']:s['file_end']]
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('entry-resources0135-static-%Y%m%dT%H%M%S.%fZ'); out.mkdir()
    con = sqlite3.connect(f'file:{PROFILE / "index.sqlite"}?mode=ro', uri=True); con.row_factory = sqlite3.Row
    functions = []
    with (PROFILE / 'official-0.135.1-full.wat').open('rb') as f:
        for index in indices:
            row = dict(con.execute('select * from functions where idx=?', (index,)).fetchone())
            f.seek(row['wat_start']); wat = f.read(row['wat_end'] - row['wat_start']); text = wat.decode()
            assert text.splitlines()[0].startswith(f'  (func (;{index};)')
            (out / f'{index}.wat').write_bytes(wat)
            strings = []
            for m in re.finditer(r'i32.const (\d+)', text):
                pointer = int(m.group(1))
                if not 1000000 <= pointer < len(memory): continue
                tail = bytes(memory[pointer:pointer + 256]); end = 0
                while end < len(tail) and 32 <= tail[end] < 127: end += 1
                if end >= 4:
                    value = tail[:end].decode('ascii')
                    if (pointer, value) not in [(s['address'], s['ascii_prefix']) for s in strings]:
                        strings.append(dict(address=pointer, ascii_prefix=value, function_line=text[:m.start()].count('\n') + 1))
            functions.append(dict(row, body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),
                wat_sha256=hashlib.sha256(wat).hexdigest(), header=text.splitlines()[0],
                direct_callees=[dict(x) for x in con.execute('select callee,count(*) as sites from calls where caller=? group by callee', (index,))],
                referenced_ascii_prefixes=strings))
    assert before == {str(x.relative_to(ROOT)): sha(x) for x in files}
    result = dict(version='0.135.1', build='0898d5e3', original_sha256=SOURCE_SHA,
        wat_sha256=WAT_SHA, index_sha256=INDEX_SHA, functions=functions, sources=before,
        target_executed=False, host_or_cache_forged=False, downloads=False, user_saves_accessed=False,
        scope='Static exact bodies and data references only; prefixes are not inferred full path or runtime reachability proof.')
    (out / 'trace.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), functions=len(functions), target_executed=False)))


if __name__ == '__main__': main()
