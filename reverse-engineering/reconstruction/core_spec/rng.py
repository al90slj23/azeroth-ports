"""Independent four-word RNG and ordered-binary32 range sampler from 32475.

State is four unsigned words in linear-memory order. No original WASM, runtime,
entropy source, seed initialization or application state is used by this model.
The all-zero state is accepted as raw input (it is a degenerate fixed point).
"""
from dataclasses import dataclass

from .binary32 import MASK, add, sub, mul, to_float


class RngRangeError(ValueError):
    """Original32475 takes its panic path before writing any RNG state."""


@dataclass(frozen=True)
class RangeResult:
    bits: int
    state: tuple
    draws: int


def _words(state):
    state = tuple(state)
    if len(state) != 4 or any(not isinstance(x, int) or not 0 <= x <= MASK for x in state):
        raise ValueError('State must contain exactly four uint32 words')
    return state


def _rotl(value, count):
    value &= MASK
    return ((value << count) | (value >> (32 - count))) & MASK


def next_u32_words(state):
    """Return (xoshiro128++ output, next_state), using wrapping uint32 math.

    This is the integer recurrence inlined in32475, not a separately executed
    original leaf function and not the global/entropy initializer95651.
    """
    a, b, c, d = _words(state)
    output = (_rotl((a + d) & MASK, 7) + a) & MASK
    return output, (a ^ b ^ d, b ^ a ^ c,
                    (a ^ c ^ (b << 9)) & MASK, _rotl(b ^ d, 11))


def uniform_range_bits(state, low_bits, high_bits, *, max_draws=100000):
    """Model32475, returning result bits, all four new words and draw count.

    Inputs are binary32 bit patterns. Accepted intervals satisfy low<high and
    have a finite binary32 width. The candidate is computed with the original
    per-operation rounding and rejected when it rounds to the upper endpoint.
    The guard is an independent model watchdog, not original game behavior.
    """
    current = _words(state)
    if not all(isinstance(x, int) and 0 <= x <= MASK for x in (low_bits, high_bits)):
        raise ValueError('Bounds must be uint32 binary32 bit patterns')
    if not to_float(low_bits) < to_float(high_bits):
        raise RngRangeError('low is not strictly less than high; original panic121709')
    width = sub(high_bits, low_bits)
    if (width & 0x7fffffff) > 0x7f7fffff:
        raise RngRangeError('binary32 interval width is not finite; original panic121709')
    for draws in range(1, max_draws + 1):
        value, current = next_u32_words(current)
        unit = add((value >> 9) | 0x3f800000, 0xbf800000)
        candidate = add(low_bits, mul(unit, width))
        if to_float(high_bits) > to_float(candidate):
            return RangeResult(candidate, current, draws)
    raise RuntimeError('Independent model draw watchdog exceeded')
