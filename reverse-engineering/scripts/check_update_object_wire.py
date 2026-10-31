#!/usr/bin/env python3
"""Literal local fixtures for the reconstructed opcode169 values subset.

Bytes below are hand-transcribed from observed field order, not encoder output,
not game traffic and not target execution. There is intentionally no encoder.
"""
import json
from update_object_wire import (decode_values_payload, decode_application_frame,
                                decode_plain_server_frame)

# Expected (guid, field-index/value pairs), with literal little-endian masks.
PAYLOADS = [
    ('010000000000ff0807060504030201010000400025000000',
     [('0102030405060708', {22: 37})]),
    ('010000000000012a01000040007b000000',
     [('000000000000002a', {22: 123})]),
    ('010000000000810102010000c0000a00000014000000',
     [('0200000000000001', {22: 10, 23: 20})]),
    ('01000000000001070200004000000080005800000063000000',
     [('0000000000000007', {22: 88, 55: 99})]),
    ('020000000000012a01000040006400000000012b010000400000000000',
     [('000000000000002a', {22: 100}), ('000000000000002b', {22: 0})]),
    ('010000000000000100004000ffffffff',
     [('0000000000000000', {22: 4294967295})]),
    ('0000000000', []),
    ('0100000000000000', [('0000000000000000', {})]),
]
APPLICATION = '07a90011000000010000000000012a01000040007b000000'
PLAIN_SERVER = '0013a900010000000000012a01000040007b000000'


def values(decoded):
    return [(x['guid_hex'], {f['index']: f['raw_u32'] for f in x['fields']})
            for x in decoded['updates']]


def main():
    passed = rejected = 0
    fixtures = [(decode_values_payload, literal, expected)
                for literal, expected in PAYLOADS]
    fixtures += [(decode_application_frame, APPLICATION, PAYLOADS[1][1]),
                 (decode_plain_server_frame, PLAIN_SERVER, PAYLOADS[1][1])]
    for decode, literal, expected in fixtures:
        raw = bytes.fromhex(literal)
        actual = decode(raw)
        assert values(actual) == expected, literal
        assert actual['block_count'] == len(expected)
        for update in actual['updates']:
            by_index = {x['index']: x['raw_u32'] for x in update['fields']}
            if 22 in by_index:
                assert update['field22_health_u32'] == by_index[22]
        passed += 1
        for size in range(len(raw)):
            try:
                decode(raw[:size])
            except ValueError:
                rejected += 1
            else:
                raise AssertionError(('accepted incomplete literal', literal, size))
        try:
            decode(raw + b'\0')
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('accepted trailing byte')
    invalid = [
        (decode_values_payload, '0100000001000000'),  # hasTransport not covered
        (decode_values_payload, '010000000001'),       # kind1 not covered
        (decode_values_payload, '010000000002'),       # kind2 create/movement not covered
        (decode_values_payload, '010000000003'),
        (decode_values_payload, '010000000004'),
        (decode_values_payload, '010000000005'),
        (decode_values_payload, 'ffffffff00'),          # local block budget
        (decode_values_payload, '010000000000000100004000'),  # missing field22 value
        (decode_application_frame, '06'),
        (decode_application_frame, '07500200000000'),   # other opcode
        (decode_plain_server_frame, '0012a900010000000000012a01000040007b000000'),
        (decode_plain_server_frame, '0001a900'),
    ]
    for decode, literal in invalid:
        try:
            decode(bytes.fromhex(literal))
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(('accepted unsupported input', literal))
    print(json.dumps({'literal_golden_frames_passed': passed,
                      'malformed_or_unsupported_inputs_rejected': rejected,
                      'encoder_used': False, 'original_game_executed': False,
                      'network_used': False,
                      'qualification': 'Handmade local fixtures validate only the reconstructed subset.'}))


if __name__ == '__main__':
    main()
