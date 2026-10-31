#!/usr/bin/env python3
"""Partial offline codecs reconstructed from 0.126.0 WASM instructions.

No sockets, target execution or game writes. Unsupported tags are rejected,
not guessed. Field labels describe wire shapes and are not recovered Rust names.
Limits below are local research admission limits, not original server limits.
"""
import argparse
import json
from pathlib import Path
import struct

MAX_BYTES = 4 * 1024 * 1024
MAX_RECORDS = 65536


class Reader:
    def __init__(self, data):
        if len(data) > MAX_BYTES:
            raise ValueError('Local research frame budget exceeded')
        self.data = data
        self.offset = 0

    def take(self, count):
        if count < 0 or count > len(self.data) - self.offset:
            raise ValueError('Truncated field')
        start = self.offset
        self.offset += count
        return self.data[start:self.offset]

    def number(self, fmt):
        return struct.unpack('<' + fmt, self.take(struct.calcsize('<' + fmt)))[0]

    def blob(self):
        return self.take(self.number('I')).hex()

    def records(self, fmt):
        count = self.number('I')
        if count > MAX_RECORDS:
            raise ValueError('Local research record budget exceeded')
        size = struct.calcsize('<' + fmt)
        return [list(struct.unpack('<' + fmt, self.take(size))) for _ in range(count)]

    def finish(self):
        if self.offset != len(self.data):
            raise ValueError('Trailing bytes outside this reconstructed variant')


def number(fmt, value):
    return struct.pack('<' + fmt, value)


def blob(hex_value):
    data = bytes.fromhex(hex_value)
    if len(data) > MAX_BYTES:
        raise ValueError('Local research blob budget exceeded')
    return number('I', len(data)) + data


def records(fmt, values):
    if len(values) > MAX_RECORDS:
        raise ValueError('Local research record budget exceeded')
    return number('I', len(values)) + b''.join(struct.pack('<' + fmt, *item) for item in values)


def decode_relay(data):
    """Subset of serializer3696: tags1,2,5,6,7,8,9,10, field order exact."""
    r = Reader(data)
    tag = r.number('B')
    result = {'tag': tag}
    if tag == 1:
        result.update(word=r.number('I'), blob0=r.blob(), blob1=r.blob(), flag=r.number('B'))
    elif tag in (2, 8, 9):
        pass
    elif tag == 5:
        result.update(blob0=r.blob(), blob1=r.blob())
    elif tag == 6:
        result.update(peer_word=r.number('I'), payload=r.blob())
    elif tag == 7:
        result['word'] = r.number('I')
    elif tag == 10:
        result.update(wide_word=r.number('Q'), payload=r.blob())
    else:
        raise ValueError('Relay tag not reconstructed in this offline subset')
    r.finish()
    return result


def encode_relay(item):
    tag = item['tag']
    out = number('B', tag)
    if tag == 1:
        out += number('I', item['word']) + blob(item['blob0']) + blob(item['blob1']) + number('B', item['flag'])
    elif tag in (2, 8, 9):
        pass
    elif tag == 5:
        out += blob(item['blob0']) + blob(item['blob1'])
    elif tag == 6:
        out += number('I', item['peer_word']) + blob(item['payload'])
    elif tag == 7:
        out += number('I', item['word'])
    elif tag == 10:
        out += number('Q', item['wide_word']) + blob(item['payload'])
    else:
        raise ValueError('Relay tag not reconstructed in this offline subset')
    Reader(out)
    return out


def decode_application(data):
    """Selected serializer1474 shapes; values do not imply HP/damage semantics."""
    r = Reader(data)
    tag = r.number('B')
    result = {'tag': tag}
    if tag == 1:
        result.update(word=r.number('I'), blob0=r.blob(), blob1=r.blob())
    elif tag == 2:
        result.update(byte0=r.number('B'), byte1=r.number('B'))
    elif tag in (3, 5, 9, 10, 19):
        result['payload'] = r.blob()
    elif tag in (6, 16, 18):
        pass
    elif tag == 7:
        result.update(half_word=r.number('H'), payload=r.blob())
    elif tag == 12:
        result['records'] = r.records('IfB')
    elif tag == 13:
        result['records'] = r.records('IIf')
    elif tag == 20:
        result['scalar32'] = r.number('f')
        result['words'] = [x[0] for x in r.records('I')]
    elif tag in (21, 23, 24):
        result['word'] = r.number('I')
    elif tag == 22:
        result.update(wide_word=r.number('Q'), blob0=r.blob(), flag=r.number('B'), blob1=r.blob())
    elif tag == 25:
        result['blob0'] = r.blob()
        count = r.number('I')
        if count > MAX_RECORDS:
            raise ValueError('Local research record budget exceeded')
        result['blobs'] = [r.blob() for _ in range(count)]
    else:
        raise ValueError('Application tag not reconstructed in this offline subset')
    r.finish()
    return result


def encode_application(item):
    tag = item['tag']
    out = number('B', tag)
    if tag == 1:
        out += number('I', item['word']) + blob(item['blob0']) + blob(item['blob1'])
    elif tag == 2:
        out += number('B', item['byte0']) + number('B', item['byte1'])
    elif tag in (3, 5, 9, 10, 19):
        out += blob(item['payload'])
    elif tag in (6, 16, 18):
        pass
    elif tag == 7:
        out += number('H', item['half_word']) + blob(item['payload'])
    elif tag == 12:
        out += records('IfB', item['records'])
    elif tag == 13:
        out += records('IIf', item['records'])
    elif tag == 20:
        out += number('f', item['scalar32']) + records('I', [[x] for x in item['words']])
    elif tag in (21, 23, 24):
        out += number('I', item['word'])
    elif tag == 22:
        out += number('Q', item['wide_word']) + blob(item['blob0']) + number('B', item['flag']) + blob(item['blob1'])
    elif tag == 25:
        if len(item['blobs']) > MAX_RECORDS:
            raise ValueError('Local research record budget exceeded')
        out += blob(item['blob0']) + number('I', len(item['blobs'])) + b''.join(blob(x) for x in item['blobs'])
    else:
        raise ValueError('Application tag not reconstructed in this offline subset')
    Reader(out)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('layer', choices=('relay', 'application'))
    parser.add_argument('input', type=Path, help='Local binary frame; never read from a network')
    args = parser.parse_args()
    if args.input.stat().st_size > MAX_BYTES:
        parser.error('Local frame exceeds research budget')
    decoder = decode_relay if args.layer == 'relay' else decode_application
    print(json.dumps(decoder(args.input.read_bytes()), ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
