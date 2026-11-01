"""Typed, unconsumed address words in947 kind2 pickup records.

The producer stores an address derived from its physical pickup owner in+12.
An independent core must not invent that original allocation address. Keep its
origin and all four unknown bytes until a verifier binds the original owner or
an independent allocator supplies its own address. This is not reward currency.
"""
from dataclasses import dataclass, fields

from .pickups134 import PickupRecord, _u
from .record_cells135 import cells135, u32, u64
from .opening_handoff135 import pickup_semantics135, _word


@dataclass(frozen=True)
class PickupAmountAddress135:
    guid: int
    owner_field_offset: int
    byte_addend: int
    producer: str = '947.G2448'

    def __post_init__(self):
        _u(self.guid, 64)
        _u(self.byte_addend)
        if self.owner_field_offset != 1872 or self.producer != '947.G2448':
            raise ValueError('Only the proven G2448 pickup-owner address producer is admitted')

    def resolve(self, owner_pointer):
        """Evaluate an explicit owner input; never obtain it from original IO."""
        _u(owner_pointer)
        return (owner_pointer + self.byte_addend) & 0xffffffff


@dataclass(frozen=True)
class OpaqueKind2Pickup135(PickupRecord):
    amount: int | None = None
    amount_origin: PickupAmountAddress135 | None = None

    def __post_init__(self):
        if self.kind != 2 or self.amount is not None:
            raise ValueError('Opaque address amounts are admitted only for kind2')
        if not isinstance(self.amount_origin, PickupAmountAddress135) or self.amount_origin.guid != self.guid:
            raise ValueError('The amount origin must belong to this exact pickup GUID')
        for field in fields(PickupRecord):
            value = getattr(self, field.name)
            if field.name == 'amount' or field.name == 'arrival_bits' and value is None:
                continue
            _u(value, 64 if field.name == 'guid' else 32)

    def resolved_record(self, owner_pointer):
        values = {field.name: getattr(self, field.name) for field in fields(PickupRecord)}
        values['amount'] = self.amount_origin.resolve(owner_pointer)
        return PickupRecord(**values)


def pickup_semantics_with_origins135(row, origins=()):
    """Retain legacy known amounts; admit only a GUID-bound opaque kind2+12.

    Unknown +12 without the specific producer declaration is still a hard
    boundary. Arrival+4 follows the existing marker-dependent read rule.
    """
    row = tuple(cells135(row, 56))
    kind = u32(row, 8, 'Pickup kind')
    if kind != 2 or all(byte is not None for byte in row[12:16]):
        return pickup_semantics135(row)
    if row[12:16] != (None,) * 4:
        raise ValueError('The declared opaque address must own exactly all four bytes at+12')
    guid = u64(row, 16, 'Pickup GUID')
    if any(not isinstance(origin, PickupAmountAddress135) for origin in origins):
        raise TypeError('Typed pickup address origins required')
    matches = tuple(origin for origin in origins if origin.guid == guid)
    if len(matches) != 1:
        raise ValueError('Exactly one explicit amount origin is required for an opaque pickup')
    marker = u32(row, 0, 'Pickup marker')
    arrival = _word(row, 4, optional=marker == 0)
    return OpaqueKind2Pickup135(marker, arrival, kind, None, guid,
        *(_word(row, offset) for offset in range(24, 56, 4)), amount_origin=matches[0])
