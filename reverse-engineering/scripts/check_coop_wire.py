#!/usr/bin/env python3
"""Offline literal golden frames derived from decoded serializer field order.

These are invented local fixtures, not traffic captures or runtime validation.
Independent literal bytes detect byte order, lengths, ordering and width errors.
"""
import json
import struct
from coop_wire import decode_relay, encode_relay, decode_application, encode_application

RELAY = [
    ('010300000007000000302e3132362e300000000001', {'tag': 1, 'word': 3, 'blob0': '302e3132362e30', 'blob1': '', 'flag': 1}),
    ('02', {'tag': 2}),
    ('05030000006162630100000078', {'tag': 5, 'blob0': '616263', 'blob1': '78'}),
    ('062a00000004000000000102ff', {'tag': 6, 'peer_word': 42, 'payload': '000102ff'}),
    ('0778563412', {'tag': 7, 'word': 305419896}),
    ('08', {'tag': 8}),
    ('09', {'tag': 9}),
    ('0a080706050403020102000000aabb', {'tag': 10, 'wide_word': 72623859790382856, 'payload': 'aabb'}),
]
APPLICATION = [
    ('010800000007000000302e3132362e3006000000414243313233', {'tag': 1, 'word': 8, 'blob0': '302e3132362e30', 'blob1': '414243313233'}),
    ('02fe7f', {'tag': 2, 'byte0': 254, 'byte1': 127}),
    ('03020000007b7d', {'tag': 3, 'payload': '7b7d'}),
    ('05020000006869', {'tag': 5, 'payload': '6869'}),
    ('06', {'tag': 6}),
    ('07341203000000000102', {'tag': 7, 'half_word': 4660, 'payload': '000102'}),
    ('09020000007b7d', {'tag': 9, 'payload': '7b7d'}),
    ('0a020000007b7d', {'tag': 10, 'payload': '7b7d'}),
    ('0c020000002a0000000000c03f03090000000000803eff', {'tag': 12, 'records': [[42, 1.5, 3], [9, 0.25, 255]]}),
    ('0d01000000010000006300000000004841', {'tag': 13, 'records': [[1, 99, 12.5]]}),
    ('10', {'tag': 16}),
    ('12', {'tag': 18}),
    ('13020000007b7d', {'tag': 19, 'payload': '7b7d'}),
    ('140000003f02000000010000002a000000', {'tag': 20, 'scalar32': 0.5, 'words': [1, 42]}),
    ('15e8030000', {'tag': 21, 'word': 1000}),
    ('1608070605040302010200000048690102000000aabb', {'tag': 22, 'wide_word': 72623859790382856, 'blob0': '4869', 'flag': 1, 'blob1': 'aabb'}),
    ('1705000000', {'tag': 23, 'word': 5}),
    ('1806000000', {'tag': 24, 'word': 6}),
    ('1903000000666f6f020000000100000061020000006263', {'tag': 25, 'blob0': '666f6f', 'blobs': ['61', '6263']}),
]


def main():
    checked = rejected = 0
    for decode, encode, fixtures in ((decode_relay, encode_relay, RELAY),
                                     (decode_application, encode_application, APPLICATION)):
        for literal, expected in fixtures:
            raw = bytes.fromhex(literal)
            assert decode(raw) == expected, literal
            assert encode(expected) == raw, literal
            checked += 1
            # Every proper prefix is invalid for these single-frame exact variants.
            for size in range(len(raw)):
                try:
                    decode(raw[:size])
                except (ValueError, struct.error):
                    rejected += 1
                else:
                    raise AssertionError(('accepted truncated fixture', literal, size))
            try:
                decode(raw + b'\0')
            except ValueError:
                rejected += 1
            else:
                raise AssertionError('accepted trailing byte')
    for decode, invalid in ((decode_relay, '03'), (decode_application, '04'),
                             (decode_application, '0cffffffff'),
                             (decode_application, '1900000000ffffffff'),
                             (decode_relay, '0601000000ffffffff')):
        try:
            decode(bytes.fromhex(invalid))
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('accepted unsupported/unbounded/truncated input')
    print(json.dumps({'literal_golden_frames_passed': checked,
                      'malformed_or_unsupported_inputs_rejected': rejected,
                      'original_game_executed': False, 'network_used': False,
                      'qualification': 'local fixtures validate the transcription; no live compatibility claim'}))


if __name__ == '__main__':
    main()
