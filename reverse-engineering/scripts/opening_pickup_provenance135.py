"""Read-only original-side binding of unconsumed947 kind2 address words.

Nothing observed here is supplied to the independent production model. A new
word must satisfy its exact pre-supply owner expression, then retain the same
bytes at every later compared stage. Unresolved simultaneous producer paths
are refused rather than granted a general unknown-value mask.
"""
import struct


def _float(word):
    return struct.unpack('<f', struct.pack('<I', word))[0]


class PickupAddressVerifier135:
    def __init__(self):
        self.previous = None
        self.bindings = {}
        self.births = []
        self.observations = 0

    def observe(self, raw, expected):
        declarations = expected.get('opaque_pickup_amount_origins', [])
        vector = raw['vectors']['pickups']
        rows = [bytes.fromhex(row) for row in vector['storage'][:vector['count']]]
        actual = {struct.unpack_from('<Q', row, 16)[0]: row for row in rows}
        if len(actual) != len(rows):
            raise ValueError('Pickup address proof requires unique active GUIDs')
        declared = {item['guid']: item for item in declarations}
        if len(declared) != len(declarations):
            raise ValueError('Duplicate pickup address declaration')
        indices = set()
        for index, words in enumerate(expected['projection']['pickup_words']):
            guid = words[4] | words[5] << 32
            if words[3] is not None:
                if guid in declared:
                    raise ValueError('A concrete pickup amount cannot acquire an opaque declaration')
                continue
            if words[2] != 2 or guid not in declared:
                raise ValueError('Only declared kind2 address words may be opaque')
            origin = declared.pop(guid)
            if set(origin) != {'guid', 'owner_field_offset', 'byte_addend', 'producer'}:
                raise ValueError('Unexpected pickup address origin shape')
            if origin['owner_field_offset'] != 1872 or origin['producer'] != '947.G2448':
                raise ValueError('Unrestored pickup address producer')
            row = actual[guid]
            if struct.unpack_from('<I', row, 8)[0] != 2:
                raise ValueError('Original opaque pickup is not kind2')
            amount = struct.unpack_from('<I', row, 12)[0]
            if guid not in self.bindings:
                previous = self.previous
                if (raw['record_kind'] != 'stage' or raw.get('kind') != 'spawn'
                        or previous is None or previous['kind'] != 'claims'):
                    raise ValueError('Opaque amount must first appear at its real spawn stage')
                now = raw['projection']['now_bits']
                if not _float(now) < _float(previous['next_resource2444_bits']):
                    raise ValueError('Simultaneous resource/supply address provenance is not yet verified')
                count = previous['count']
                if count == 0:
                    raise ValueError('Mode0 empty-owner local2 source remains unresolved')
                addend = 8 + 56 * count if count < 4 or count % 4 else 176 + 224 * (count // 4)
                if origin['byte_addend'] != addend:
                    raise ValueError('Independent supply address expression differs from original loop')
                predicted = (previous['pointer'] + addend) & 0xffffffff
                if amount != predicted:
                    raise ValueError('Original kind2 amount differs from its pre-supply owner expression')
                self.bindings[guid] = amount
                self.births.append(dict(guid=str(guid), frame=raw['frame'], stage_index=raw['stage_index'],
                    owner_pointer=previous['pointer'], owner_count=count, byte_addend=addend,
                    original_amount=amount, independent_model_received_original_pointer=False))
            elif self.bindings[guid] != amount:
                raise ValueError('Original bound pickup address bytes changed after production')
            indices.add(index)
            self.observations += 1
        if declared:
            raise ValueError('Opaque address declaration has no active semantic owner')
        self.previous = dict(kind=raw.get('kind', raw['record_kind']), pointer=vector['pointer'],
            count=vector['count'], next_resource2444_bits=raw['projection']['next_resource2444_bits'])
        return indices

    def report(self):
        return dict(births=self.births, bound_words=len(self.bindings), observations=self.observations,
            all_birth_formulas_and_retained_bytes_verified=True,
            original_values_used_as_model_inputs=False,
            unsupported_domains=['simultaneousG2444_resource_andG2448_supply', 'mode0_empty_owner'])
