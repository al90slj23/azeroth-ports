"""Independent135 sin11428/cos11503 through their medium-angle reduction.

Uses the original ordered binary64 arithmetic and split pi/2 constants, then
rounds the existing independent polynomial kernels to binary32. It does not
use host libm sin/cos or reduce with a rounded binary32 tau. Payne-Hanek1814
for finite angles beyond421657408 remains an explicit unresolved boundary.
"""
from . import binary32 as f
from .spawn_geometry135 import (sin_bits as small_sin, cos_bits as small_cos,
    _sin_kernel, _cos_kernel, TAU)

MEDIUM_MAX_BITS = 1305022426
REDUCTION_START_BITS = 1088565718
H = float.fromhex


def _reduced(bits):
    x = f.to_float(bits)
    n = ((x * H('0x1.45f306dc9c883p-1')) + H('0x1.8p52')) + H('-0x1.8p52')
    y = (x + n * H('-0x1.921fb5p0')) + n * H('-0x1.110b4611a6263p-26')
    return int(n) & 3, y


def sin_bits(bits):
    if type(bits) is not int or not 0 <= bits <= f.MASK:
        raise ValueError('Explicit binary32 word required')
    absolute = bits & ~f.SIGN
    if absolute >= f.INF:
        return f.NAN
    if absolute <= 0x40c90fdb:
        return small_sin(bits)
    if absolute < REDUCTION_START_BITS:
        return _sin_kernel(abs(f.to_float(bits)) - TAU) ^ (bits & f.SIGN)
    if absolute > MEDIUM_MAX_BITS:
        raise ValueError('Finite Payne-Hanek1814 reduction remains unresolved')
    quadrant, y = _reduced(bits)
    return (_sin_kernel(y), _cos_kernel(y), _sin_kernel(y) ^ f.SIGN,
            _cos_kernel(y) ^ f.SIGN)[quadrant]


def cos_bits(bits):
    if type(bits) is not int or not 0 <= bits <= f.MASK:
        raise ValueError('Explicit binary32 word required')
    absolute = bits & ~f.SIGN
    if absolute >= f.INF:
        return f.NAN
    if absolute <= 0x40c90fdb:
        return small_cos(bits)
    if absolute < REDUCTION_START_BITS:
        return _cos_kernel(abs(f.to_float(bits)) - TAU)
    if absolute > MEDIUM_MAX_BITS:
        raise ValueError('Finite Payne-Hanek1814 reduction remains unresolved')
    quadrant, y = _reduced(bits)
    return (_cos_kernel(y), _sin_kernel(y) ^ f.SIGN, _cos_kernel(y) ^ f.SIGN,
            _sin_kernel(y))[quadrant]
