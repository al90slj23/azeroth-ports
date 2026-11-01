#!/usr/bin/env python3
"""Extract fixed declaration bytes; never execute the original game."""
import hashlib, struct
from pathlib import Path
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source


def main():
    binary = SOURCE.read_bytes(); assert hashlib.sha256(binary).hexdigest() == SOURCE_SHA
    segments = parse_source(binary)[4]
    memory = bytearray(max(s['address'] + s['length'] for s in segments if s['address'] is not None))
    for s in segments:
        if s['address'] is not None:
            memory[s['address']:s['address'] + s['length']] = binary[s['file_offset']:s['file_offset'] + s['length']]
    rows = []
    for index in range(114):
        pointer = 5467428 + index * 88; raw = bytes(memory[pointer:pointer + 88]); w = struct.unpack('<22I', raw)
        name = bytes(memory[w[3]:w[3] + w[4]]).decode('ascii'); rows.append((pointer, name, raw.hex()))
    assert len({r[1] for r in rows}) == 114
    out = ROOT / 'reconstruction/core_spec/cast_catalogue135_data.py'
    out.write_text('"""Fixed135 declaration bytes, not recovered executable behavior; no runtime IO."""\n'
        + 'SOURCE_SHA256 = ' + repr(SOURCE_SHA) + '\nRAW_DEFINITIONS = ' + repr(tuple(rows)) + '\n')
    print(f'Extracted114 fixed88B declarations into {out}')


if __name__ == '__main__': main()
