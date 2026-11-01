"""Bounded WDBC container reader; column game semantics are deliberately unknown."""
from dataclasses import dataclass
import struct


@dataclass(frozen=True)
class DBC:
    rows: int
    fields: int
    record_bytes: int
    strings_bytes: int
    records: bytes
    strings: bytes

    @classmethod
    def parse(cls, data: bytes):
        if len(data) < 20 or data[:4] != b'WDBC':
            raise ValueError('Only WDBC containers are supported')
        rows, fields, record_bytes, strings_bytes = struct.unpack_from('<4I', data, 4)
        # WDBC also admits packed byte fields; CharBaseInfo has2B records and
        # CharStartOutfit has41 declared fields in152B. Widths need a schema.
        if not 0 < fields <= 4096 or not 0 < record_bytes <= 16384 or rows > 10_000_000:
            raise ValueError('Unexpected WDBC row layout')
        end = 20 + rows * record_bytes
        if end + strings_bytes != len(data) or not strings_bytes or data[end] != 0:
            raise ValueError('WDBC exact size or initial empty string differs')
        return cls(rows, fields, record_bytes, strings_bytes, data[20:end], data[end:])

    def raw_record(self, index: int) -> bytes:
        if not 0 <= index < self.rows:
            raise IndexError(index)
        start = index * self.record_bytes
        return self.records[start:start + self.record_bytes]

    def word(self, row: int, column: int) -> int:
        if self.record_bytes != self.fields * 4:
            raise ValueError('Packed WDBC fields require an explicit schema')
        if not 0 <= column < self.fields:
            raise IndexError(column)
        return struct.unpack_from('<I', self.raw_record(row), column * 4)[0]

    def string(self, offset: int) -> bytes:
        if not 0 <= offset < len(self.strings):
            raise IndexError(offset)
        end = self.strings.find(b'\0', offset)
        if end < 0:
            raise ValueError('String lacks terminator')
        return self.strings[offset:end]
