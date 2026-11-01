"""Bounded classic MPQ v0 reader, independent of StormLib and the game.

Implemented domain: one header at offset0, classic hash/block tables, raw,
zlib or bzip2 sectors/single units, and classic file/table encryption. Unknown
compression, patch files and sector-checksum files are explicit unsupported
inputs. This is an archive reader, not a model/texture/animation renderer.
"""
from dataclasses import dataclass
from pathlib import Path
import bz2
import struct
import zlib

U32 = 0xffffffff
EXISTS = 0x80000000
IMPLODE = 0x100
COMPRESS = 0x200
ENCRYPTED = 0x10000
FIX_KEY = 0x20000
PATCH_FILE = 0x100000
SINGLE_UNIT = 0x1000000
DELETE_MARKER = 0x2000000
SECTOR_CRC = 0x4000000


class UnsupportedMPQ(ValueError):
    pass


def _crypt_table():
    table = [0] * 1280
    seed = 0x100001
    for low in range(256):
        for high in range(5):
            seed = (seed * 125 + 3) % 0x2aaaab
            first = (seed & 0xffff) << 16
            seed = (seed * 125 + 3) % 0x2aaaab
            table[low + high * 256] = first | (seed & 0xffff)
    return tuple(table)


CRYPT_TABLE = _crypt_table()


def normalized_name(name: str) -> bytes:
    """StormLib archive-name case folding, preserving path separators.

    Filename lookup uses HashStringSlash, unlike HashString's slash-to-backslash
    behavior. Any application-level path aliases must be resolved separately.
    """
    raw = name.encode('latin1')
    return bytes(c - 32 if 97 <= c <= 122 else c for c in raw)


def hash_name(name: str, kind: int) -> int:
    if kind not in range(4):
        raise ValueError('Unknown classic MPQ hash kind')
    first, second = 0x7fed7fed, 0xeeeeeeee
    for byte in normalized_name(name):
        first = (CRYPT_TABLE[kind * 256 + byte] ^ ((first + second) & U32)) & U32
        second = (byte + first + second + (second << 5) + 3) & U32
    return first


def decrypt_words(data: bytes, key: int) -> bytes:
    """Decrypt complete little-endian words; trailing bytes remain unchanged."""
    result = bytearray(data)
    seed = 0xeeeeeeee
    for offset in range(0, len(data) - 3, 4):
        seed = (seed + CRYPT_TABLE[1024 + (key & 255)]) & U32
        value = struct.unpack_from('<I', data, offset)[0] ^ ((key + seed) & U32)
        struct.pack_into('<I', result, offset, value)
        key = ((((~key & U32) << 21) + 0x11111111) | (key >> 11)) & U32
        seed = (value + seed + (seed << 5) + 3) & U32
    return bytes(result)


@dataclass(frozen=True)
class Block:
    offset: int
    compressed_size: int
    size: int
    flags: int


@dataclass(frozen=True)
class HashEntry:
    slot: int
    name_a: int
    name_b: int
    locale: int
    platform: int
    reserved: int
    block: int


def _inflate(data: bytes, expected: int) -> bytes:
    if len(data) == expected:
        return data
    if not data:
        raise ValueError('Empty compressed sector')
    method, payload = data[0], data[1:]
    if method == 2:
        inflater = zlib.decompressobj()
        result = inflater.decompress(payload, expected + 1)
        if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
            raise ValueError('Zlib stream is incomplete, trailing or oversized')
    elif method == 16:
        inflater = bz2.BZ2Decompressor()
        result = inflater.decompress(payload, max_length=expected + 1)
        if not inflater.eof or inflater.unused_data:
            raise ValueError('Bzip2 stream is incomplete, trailing or oversized')
    else:
        raise UnsupportedMPQ(f'Compression mask0x{method:02x}')
    if len(result) != expected:
        raise ValueError('Decompressed sector size differs')
    return result


class Archive:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.bytes = self.path.stat().st_size
        header = self._read(0, 32)
        (magic, header_size, archive_size, version, sector_shift,
         self.hash_offset, self.block_offset, hash_count, block_count) = struct.unpack('<4sIIHHIIII', header)
        if magic != b'MPQ\x1a' or version != 0 or header_size != 32:
            raise UnsupportedMPQ('Only classic v0 header at offset0 is supported')
        if archive_size != self.bytes or sector_shift > 12:
            raise ValueError('MPQ archive size or sector exponent differs')
        if not hash_count or hash_count & (hash_count - 1) or hash_count > 1 << 20:
            raise ValueError('Hash table is not a bounded power of two')
        if not 0 < block_count <= 1 << 20:
            raise ValueError('Block table exceeds budget')
        self.sector_size = 512 << sector_shift
        hashes = decrypt_words(self._read(self.hash_offset, hash_count * 16), hash_name('(hash table)', 3))
        blocks = decrypt_words(self._read(self.block_offset, block_count * 16), hash_name('(block table)', 3))
        self.hashes = tuple(HashEntry(i, *struct.unpack_from('<IIHBBI', hashes, i * 16)) for i in range(hash_count))
        self.blocks = tuple(Block(*struct.unpack_from('<4I', blocks, i * 16)) for i in range(block_count))
        self.hash_table_bytes, self.block_table_bytes = hashes, blocks
        for entry in self.hashes:
            if entry.block not in (U32, U32 - 1) and entry.block >= block_count:
                raise ValueError('Hash entry refers outside block table')
        for block in self.blocks:
            if block.flags & EXISTS and not block.flags & DELETE_MARKER:
                if block.offset < header_size or block.offset + block.compressed_size > self.bytes:
                    raise ValueError('File block lies outside archive')

    def _read(self, offset: int, size: int) -> bytes:
        if not 0 <= offset <= offset + size <= self.bytes:
            raise ValueError('Read outside archive')
        with self.path.open('rb') as stream:
            stream.seek(offset)
            result = stream.read(size)
        if len(result) != size:
            raise ValueError('Short archive read')
        return result

    def lookup_all(self, name: str) -> tuple[HashEntry, ...]:
        start = hash_name(name, 0) & (len(self.hashes) - 1)
        wanted = hash_name(name, 1), hash_name(name, 2)
        found = []
        for step in range(len(self.hashes)):
            entry = self.hashes[(start + step) & (len(self.hashes) - 1)]
            if entry.block == U32:
                break
            if entry.block != U32 - 1 and (entry.name_a, entry.name_b) == wanted:
                found.append(entry)
        return tuple(found)

    def lookup(self, name: str, locale: int = 0) -> HashEntry:
        entries = self.lookup_all(name)
        candidates = [e for e in entries if e.locale == locale and e.platform == 0]
        if not candidates and locale:
            candidates = [e for e in entries if e.locale == 0 and e.platform == 0]
        if len(candidates) != 1:
            if not entries:
                raise FileNotFoundError(name)
            raise UnsupportedMPQ('Ambiguous or unsupported locale/platform')
        return candidates[0]

    def read(self, name: str, *, max_bytes: int = 32 * 1024 * 1024, locale: int = 0) -> bytes:
        entry = self.lookup(name, locale)
        block = self.blocks[entry.block]
        if not block.flags & EXISTS or block.flags & DELETE_MARKER:
            raise FileNotFoundError(name)
        known_flags = EXISTS | IMPLODE | COMPRESS | ENCRYPTED | FIX_KEY | PATCH_FILE | SINGLE_UNIT | DELETE_MARKER | SECTOR_CRC
        if block.flags & ~known_flags or block.flags & (IMPLODE | PATCH_FILE | SECTOR_CRC):
            raise UnsupportedMPQ(f'Unsupported file flags0x{block.flags:08x}')
        if block.size > max_bytes or block.compressed_size > max_bytes + 1024 * 1024:
            raise ValueError('File exceeds caller budget')
        raw = self._read(block.offset, block.compressed_size)
        if block.size == 0 and not raw:
            return b''
        key = hash_name(name.replace('/', '\\').rsplit('\\', 1)[-1], 3)
        if block.flags & FIX_KEY:
            key = ((key + block.offset) ^ block.size) & U32
        encrypted, compressed = bool(block.flags & ENCRYPTED), bool(block.flags & COMPRESS)
        if block.flags & SINGLE_UNIT:
            if encrypted:
                raw = decrypt_words(raw, key)
            result = _inflate(raw, block.size) if compressed else raw
        elif compressed:
            sectors = (block.size + self.sector_size - 1) // self.sector_size
            offset_bytes = (sectors + 1) * 4
            table = raw[:offset_bytes]
            if len(table) != offset_bytes:
                raise ValueError('Truncated sector offset table')
            if encrypted:
                table = decrypt_words(table, (key - 1) & U32)
            offsets = struct.unpack(f'<{sectors + 1}I', table)
            if offsets[0] != offset_bytes or offsets[-1] != len(raw) or any(a > b for a, b in zip(offsets, offsets[1:])):
                raise ValueError('Sector offsets differ from bounded classic layout')
            result = bytearray()
            for i, (start, end) in enumerate(zip(offsets, offsets[1:])):
                sector = raw[start:end]
                if encrypted:
                    sector = decrypt_words(sector, (key + i) & U32)
                expected = min(self.sector_size, block.size - len(result))
                result.extend(_inflate(sector, expected))
            result = bytes(result)
        else:
            result = bytearray()
            for i, start in enumerate(range(0, len(raw), self.sector_size)):
                sector = raw[start:start + self.sector_size]
                result.extend(decrypt_words(sector, (key + i) & U32) if encrypted else sector)
            result = bytes(result)
        if len(result) != block.size:
            raise ValueError('Decoded file length differs')
        return result

    def listfile(self) -> tuple[str, ...]:
        data = self.read('(listfile)', max_bytes=8 * 1024 * 1024)
        return tuple(line.decode('latin1') for line in data.replace(b'\r', b'').split(b'\n') if line)
