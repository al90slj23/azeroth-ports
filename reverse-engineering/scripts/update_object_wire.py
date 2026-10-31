#!/usr/bin/env python3
"""Decode the observed opcode169 values-update subset entirely offline.

Reconstructed from current0.126.0 functions933/15808/6565/50551. Only values
blocks(kind0), packedGUIDs, update masks and u32 field words are covered.
Create/movement/transport/compressed variants are deliberately unsupported.
This does not execute the original game, contact a server or replay packets.
The admission budgets here belong to this local research tool.
"""
import argparse
import json
from pathlib import Path
import struct

OPCODE = 169
MAX_BYTES = 4 * 1024 * 1024
MAX_BLOCKS = 4096
ORIGINAL_SHA256 = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'


class Reader:
    def __init__(self, data):
        if len(data) > MAX_BYTES:
            raise ValueError('Local research byte budget exceeded')
        self.data = data
        self.offset = 0

    def take(self, size):
        if size < 0 or size > len(self.data) - self.offset:
            raise ValueError('Truncated values-update frame')
        start = self.offset
        self.offset += size
        return self.data[start:self.offset]

    def number(self, fmt):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def finish(self):
        if self.offset != len(self.data):
            raise ValueError('Trailing bytes outside the reconstructed subset')


def decode_values_payload(data):
    """Payload built by50551, with kind0 blocks emitted by933."""
    r = Reader(data)
    count = r.number('<I')
    if count > MAX_BLOCKS:
        raise ValueError('Local research block budget exceeded')
    if r.number('<B') != 0:
        raise ValueError('Transport-bearing updates are outside this subset')
    updates = []
    for _ in range(count):
        block_start = r.offset
        if r.number('<B') != 0:
            raise ValueError('Only observed kind0 values blocks are covered')
        guid_start = r.offset
        guid_mask = r.number('<B')
        guid = 0
        for byte_index in range(8):
            if guid_mask & (1 << byte_index):
                guid |= r.number('<B') << (8 * byte_index)
        packed_guid = data[guid_start:r.offset].hex()
        word_count = r.number('<B')
        masks = [r.number('<I') for _ in range(word_count)]
        if sum(x.bit_count() for x in masks) > (len(data) - r.offset) // 4:
            raise ValueError('Update mask requires missing u32 field values')
        fields = []
        for word_index, mask in enumerate(masks):
            for bit in range(32):
                if mask & (1 << bit):
                    fields.append({'index': word_index * 32 + bit,
                                   'raw_u32': r.number('<I')})
        record = {'kind': 0, 'guid_hex': f'{guid:016x}',
                  'packed_guid_hex': packed_guid, 'mask_word_count': word_count,
                  'mask_words_hex': [f'{x:08x}' for x in masks], 'fields': fields,
                  'payload_start': block_start, 'payload_end_exclusive': r.offset}
        hp = [x['raw_u32'] for x in fields if x['index'] == 22]
        if hp:
            record['field22_health_u32'] = hp[0]
        updates.append(record)
    r.finish()
    return {'opcode': OPCODE, 'block_count': count, 'has_transport': False,
            'updates': updates, 'payload_bytes': len(data)}


def decode_application_frame(data):
    """Explicit application-layer wiretag7: u16opcode + length-prefixed payload."""
    r = Reader(data)
    if r.number('<B') != 7:
        raise ValueError('Only application wiretag7 is covered')
    if r.number('<H') != OPCODE:
        raise ValueError('Only opcode169 values updates are covered')
    payload = r.take(r.number('<I'))
    r.finish()
    return decode_values_payload(payload)


def decode_plain_server_frame(data):
    """Explicit unencrypted22098 header: u16BE(payloadLen+2),u16LEopcode."""
    r = Reader(data)
    length = r.number('>H')
    if length < 2:
        raise ValueError('Server header length must include the two opcode bytes')
    if r.number('<H') != OPCODE:
        raise ValueError('Only plain opcode169 values updates are covered')
    payload = r.take(length - 2)
    r.finish()
    return decode_values_payload(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='A local byte fixture; no network input')
    parser.add_argument('--layer', choices=('payload', 'application', 'plain-server'),
                        default='payload')
    args = parser.parse_args()
    if args.input.stat().st_size > MAX_BYTES:
        parser.error('Input exceeds the local research byte budget')
    decoder = {'payload': decode_values_payload, 'application': decode_application_frame,
               'plain-server': decode_plain_server_frame}[args.layer]
    try:
        result = decoder(args.input.read_bytes())
    except ValueError as error:
        parser.error(str(error))
    result.update({'layer': args.layer, 'original_game_executed': False,
                   'game_version': '0.126.0', 'original_wasm_sha256': ORIGINAL_SHA256,
                   'qualification': 'Partial offline transcription; input is not assumed to be a traffic capture.'})
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
