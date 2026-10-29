#!/usr/bin/env python3
"""Strict official 0.126.0 Android-only native Reroll button layout patch.

Original input and game rules remain unchanged. The patch returns a new packaging copy and
an instruction audit; it never edits the official snapshot. The CLI can write
a separate output and report. Runtime acceptance is recorded under evidence/.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ORIGINAL_SHA256 = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'
FUNCTION_START, FUNCTION_END = 11911582, 11966851
FUNCTION_SHA256 = '07945312985c39fa158ee4bd529ea145b8e6bbfd92717dddc425b6b66e58b5a1'

def signed_leb(n):
    out = bytearray()
    while True:
        byte = n & 127
        n >>= 7
        done = (n == 0 and byte & 64 == 0) or (n == -1 and byte & 64 != 0)
        out.append(byte if done else byte | 128)
        if done:
            return bytes(out)

def float_bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]

def val_px(value):
    return (float_bits(value) << 32) | 1

# Per-instruction anchors, not a search-and-replace over float values.
# Node fields are written only in the RerollButton creation bundle, then its
# descendant text/badge bundles. No run state/counter/cost/roll tables change.
# f32 nextDown(2): identical rendered border thickness to 2px, while keeping
# signed-LEB length equal at the packed-Val 1px/2px sign boundary.
BORDER_TWO = struct.unpack('<f', struct.pack('<I', 0x3fffffff))[0]
VAL_PATCHES = [
    (11962831, 8, 16, 'button column gap'),
    (11962864, 6, 12, 'button radius side 4'),
    (11962881, 6, 12, 'button radius side 3'),
    (11962898, 6, 12, 'button radius side 2'),
    (11962915, 6, 12, 'button radius side 1'),
    (11962932, 1, BORDER_TWO, 'button border side 4'),
    (11962948, 1, BORDER_TWO, 'button border side 3'),
    (11962964, 1, BORDER_TWO, 'button border side 2'),
    (11962980, 1, BORDER_TWO, 'button border side 1'),
    (11962996, 8, 16, 'button vertical padding 2'),
    (11963013, 8, 16, 'button vertical padding 1'),
    (11963030, 16, 32, 'button horizontal padding 2'),
    (11963047, 16, 32, 'button horizontal padding 1'),
    (11965816, 3, 6, 'R badge radius side 4'),
    (11965833, 3, 6, 'R badge radius side 3'),
    (11965850, 3, 6, 'R badge radius side 2'),
    (11965867, 3, 6, 'R badge radius side 1'),
    (11965884, 1, BORDER_TWO, 'R badge border side 4'),
    (11965900, 1, BORDER_TWO, 'R badge border side 3'),
    (11965916, 1, BORDER_TWO, 'R badge border side 2'),
    (11965932, 1, BORDER_TWO, 'R badge border side 1'),
    (11965964, 5, 10, 'R badge horizontal padding 2'),
    (11965981, 5, 10, 'R badge horizontal padding 1'),
]
FONT_PATCHES = [
    (11963818, 17, 34, 'Reroll main label'),
    (11964558, 17, 34, 'Reroll count label'),
    (11964998, 14, 28, 'gold denomination'),
    (11965426, 17, 34, 'paid reroll amount'),
    (11966624, 11, 22, 'R key badge label'),
]

def patch(data):
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('Official WASM revision changed; review mobile Reroll patch')
    if hashlib.sha256(data[FUNCTION_START:FUNCTION_END]).hexdigest() != FUNCTION_SHA256:
        raise ValueError('Reroll creation function changed')
    if data[77412646:77412652] != b'Reroll':
        raise ValueError('Original Reroll string anchor changed')
    output = bytearray(data)
    edits = []
    for opcode, entries, encode in [(0x42, VAL_PATCHES, val_px), (0x41, FONT_PATCHES, float_bits)]:
        for offset, before, after, label in entries:
            if not FUNCTION_START <= offset < FUNCTION_END:
                raise ValueError('Patch escaped the Reroll creation function')
            old = bytes([opcode]) + signed_leb(encode(before))
            new = bytes([opcode]) + signed_leb(encode(after))
            if len(old) != len(new) or data[offset:offset+len(old)] != old:
                raise ValueError(f'Layout instruction drift: {label} at {offset}')
            output[offset:offset+len(old)] = new
            edits.append({'offset':offset,'field':label,'before':before,'after':after,
                          'old_bytes':old.hex(),'new_bytes':new.hex(),
                          'context_before':data[offset-8:offset+len(old)+8].hex()})
    for offset, (before, after) in enumerate(zip(data, output)):
        if before != after and not any(e['offset'] <= offset < e['offset']+len(bytes.fromhex(e['old_bytes'])) for e in edits):
            raise AssertionError('Unexpected change outside exact layout constants')
    return bytes(output), edits

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise SystemExit('Never overwrite official source')
    data = args.source.read_bytes()
    output, edits = patch(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    report = {'original_sha256':ORIGINAL_SHA256,'candidate_sha256':hashlib.sha256(output).hexdigest(),
              'original_unmodified':hashlib.sha256(args.source.read_bytes()).hexdigest()==ORIGINAL_SHA256,
              'same_binary_length':len(data)==len(output),'code_function_index':1800,
              'code_body_index':922,'original_function_sha256':FUNCTION_SHA256,
              'edits':edits,'rules_changed':False,'runtime_acceptance':'pending'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='edits'}))
