#!/usr/bin/env python3
"""Retain exact current-core functions and transport-table facts for co-op research.

Uses a previously validated complete-WAT index read-only. This is a local static
extraction aid, not target execution, traffic capture, or stock REA semantics.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct

from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
KEY_FUNCTIONS = (880, 933, 1031, 1341, 1474, 1623, 3696, 6565, 8283, 9476,
                 12107, 15808, 21363, 22098, 24264, 30563, 36331, 39032,
                 40002, 45020, 47321, 47521, 50551, 53577, 57446, 58042,
                 59035, 86273, 86274, 86275, 86276, 94709, 28392, 83846,
                 92093, 95632, 171798)


def module_data(data):
    def uint(p, signed=False):
        value = shift = 0
        while p < len(data) and shift <= 35:
            byte = data[p]; p += 1
            value |= (byte & 127) << shift; shift += 7
            if byte < 128:
                if signed and byte & 64:
                    value -= 1 << shift
                return value, p
        raise ValueError('Invalid LEB')
    sections = {}; p = 8
    while p < len(data):
        kind = data[p]; size, begin = uint(p + 1)
        sections[kind] = (begin, begin + size); p = begin + size
    count, p = uint(sections[11][0]); segments = []
    for index in range(count):
        flags, p = uint(p)
        if flags != 0 or data[p] != 65:
            raise ValueError('Unexpected exact-target data profile')
        address, p = uint(p + 1, True)
        if data[p] != 11:
            raise ValueError('Unexpected data offset expression')
        size, p = uint(p + 1)
        segments.append({'index': index, 'address': address, 'file_start': p,
                         'file_end': p + size, 'size': size})
        p += size
    if p != sections[11][1]:
        raise ValueError('Data section boundary differs')
    count, p = uint(sections[9][0])
    if count != 1:
        raise ValueError('Unexpected exact-target element profile')
    flags, p = uint(p)
    if flags != 0 or data[p] != 65:
        raise ValueError('Unexpected exact-target table profile')
    base, p = uint(p + 1, True)
    if data[p] != 11:
        raise ValueError('Unexpected table offset expression')
    count, p = uint(p + 1); elements = []
    for _ in range(count):
        value, p = uint(p); elements.append(value)
    if p != sections[9][1]:
        raise ValueError('Element section boundary differs')
    return segments, base, elements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(source) != ORIGINAL_SHA:
        raise SystemExit('Original current core identity differs')
    binary = source.read_bytes(); ranges = body_ranges(binary)
    database = args.index.resolve(strict=True)
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as con:
        meta = {key: json.loads(value) for key, value in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index provenance/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('coop-sync-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []
        with wat.open('rb') as stream:
            for index in KEY_FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?', (index,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[index]:
                    raise ValueError('Index body bounds differ from the original')
                stream.seek(row[0]); decoded = stream.read(row[1] - row[0])
                headers = re.findall(rb'^  \(func \(;(\d+);\)', decoded, re.M)
                if headers != [str(index).encode()]:
                    raise ValueError('Expected one complete indexed function')
                (run / f'function-{index}.wat').write_bytes(decoded)
                functions.append({'function_index': index, 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': row[5], 'body_sha256': hashlib.sha256(binary[row[3]:row[4]]).hexdigest(),
                                  'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(decoded), 'wat_sha256': hashlib.sha256(decoded).hexdigest()})
        segments, base, elements = module_data(binary)
        def memory(address, length):
            hits = [segment for segment in segments if segment['address'] <= address
                    and address + length <= segment['address'] + segment['size']]
            if len(hits) != 1:
                raise ValueError('Memory span does not map uniquely')
            segment = hits[0]; offset = segment['file_start'] + address - segment['address']
            return offset, binary[offset:offset + length]
        vtables = []
        for label, address, methods in (
                ('browser_socket', 1665524, {12: 47521, 16: 39032}),
                ('host_listener', 1739928, {12: 47322}),
                ('guest_stream', 1739956, {12: 53577, 16: 53929}),
                ('accepted_peer_stream', 1778064, {12: 30563, 16: 29450})):
            entries = []
            for offset, expected in methods.items():
                file_offset, raw = memory(address + offset, 4)
                slot = struct.unpack('<I', raw)[0]
                actual = elements[slot - base]
                if actual != expected:
                    raise ValueError('Known trait/table function binding differs')
                entries.append({'vtable_field_offset': offset, 'file_offset': file_offset,
                                'table_slot': slot, 'function_index': actual, 'raw_hex': raw.hex()})
            vtables.append({'descriptive_label': label, 'memory_address': address, 'methods': entries})
        report = {'version': '0.126.0', 'build': '3e72472a', 'original_sha256': ORIGINAL_SHA,
                  'complete_wat_sha256': WAT_SHA, 'analysis_method': 'exact byte extraction and local read-only instruction index navigation',
                  'functions': functions, 'selected_transport_vtables': vtables,
                  'target_executed': False, 'official_network_used': False,
                  'limitations': ['Function roles and protocol meaning require the companion manually reviewed report.',
                                  'Static function/trait binding does not establish runtime reachability, delivery or timing.',
                                  'The report does not reconstruct the remote relay server implementation.']}
        (run / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if sha(source) != ORIGINAL_SHA or sha(wat) != WAT_SHA:
        raise SystemExit('Original or complete WAT changed while extracting')
    print(json.dumps({'run_directory': str(run), 'complete_functions': len(functions),
                      'verified_vtables': len(vtables), 'target_executed': False, 'network_used': False}))


if __name__ == '__main__':
    main()
