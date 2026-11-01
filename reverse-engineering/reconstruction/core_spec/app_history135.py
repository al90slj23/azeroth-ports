"""Fixed135 empty history storage and explicitly sourced App hash-state inputs.

53845 writes20 empty12B byte-vector headers. The four32B maps at App3992
are a separate4253 inline constructor. Address-derived entropy is an explicit
input here, never invented by injecting the original Once/global state.
"""
from dataclasses import dataclass
import struct

MASK64 = (1 << 64) - 1
EMPTY_RAW_TABLE_WORDS135 = (5222416, 0, 0, 0)  # Original static5222424[16].


def _u64(value):
    if type(value) is not int or not 0 <= value <= MASK64:
        raise ValueError('Explicit u64 state word required')
    return value


def empty_history135():
    """Complete53845 bytes:20(capacity0,dangling-byte-pointer1,length0)."""
    return struct.pack('<3I', 0, 1, 0) * 20


@dataclass(frozen=True)
class AddressEntropy135:
    """Original81334 output, dependent on actual stack/allocation addresses."""
    stack_address: int
    allocation_address: int

    def __post_init__(self):
        for value in (self.stack_address, self.allocation_address):
            if type(value) is not int or not 0 < value <= 0xffffffff:
                raise ValueError('Actual nonzero wasm32 address input required')


def entropy81334(stack_before, one_byte_allocation_pointer):
    """Caller-supplied real allocator result; no independent allocator claim."""
    if type(stack_before) is not int or not 16 <= stack_before <= 0xffffffff:
        raise ValueError('Valid original stack boundary required')
    return AddressEntropy135(stack_before - 1, one_byte_allocation_pointer)


def entropy60416(stack_before, one_byte_allocation_pointer):
    if type(stack_before) is not int or stack_before < 32:
        raise ValueError('Original60416 needs its own16B stack frame')
    return entropy81334(stack_before - 16, one_byte_allocation_pointer)


@dataclass(frozen=True)
class RandomState135:
    first: int
    second: int

    def __post_init__(self):
        _u64(self.first); _u64(self.second)


@dataclass(frozen=True)
class EmptyAppHashMaps135:
    """Four physical32B headers plus post-construction thread-local seed state."""
    bytes128: bytes
    keys: tuple
    next_state: RandomState135


def app_hash_maps135(state, *, empty_table_words=EMPTY_RAW_TABLE_WORDS135):
    """4253 App3992..4119; requires a genuinely initialized typed seed state.

    Each map uses successive wrapping first words and the same second word.
    The physical empty-table pointer belongs to this fixedWASM; callers using
    another allocator/layout must supply their independently valid header.
    App4120..4147 are different fields and are deliberately excluded.
    """
    if not isinstance(state, RandomState135):
        raise TypeError('Explicit initialized RandomState135 input required')
    if len(empty_table_words) != 4 or any(type(x) is not int or not 0 <= x <= 0xffffffff for x in empty_table_words):
        raise ValueError('Four actual raw-table header words required')
    keys = tuple(((state.first + index) & MASK64, state.second) for index in range(4))
    records = b''.join(struct.pack('<4I2Q', *empty_table_words, *key) for key in keys)
    return EmptyAppHashMaps135(records, keys, RandomState135((state.first+4) & MASK64, state.second))
