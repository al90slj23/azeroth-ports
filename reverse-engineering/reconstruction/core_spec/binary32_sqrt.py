"""Correctly rounded binary32 square root, using exact rational comparisons.

Independent of host libm. NaNs/negative nonzero inputs canonicalize to quietNaN;
signed zero is preserved. Ordered finite positive float bits allow bisection,
then comparison with the exact square of the midpoint chooses ties-to-even.
"""
from . import binary32 as f


def sqrt_bits(bits):
    if type(bits) is not int or not 0 <= bits <= f.MASK:
        raise ValueError('Expected uint32 float bits')
    if f.is_nan(bits):
        return 0x7fc00000
    if f.is_zero(bits):
        return bits
    if bits & 0x80000000:
        return 0x7fc00000
    if f.is_inf(bits):
        return bits
    value=f._fraction(bits)
    low,high=0,0x7f7fffff
    while low+1<high:
        middle=(low+high)//2
        candidate=f._fraction(middle)
        if candidate*candidate<=value:
            low=middle
        else:
            high=middle
    lower=f._fraction(low)
    if lower*lower==value:
        return low
    midpoint=(lower+f._fraction(high))/2
    boundary=midpoint*midpoint
    if value<boundary:
        return low
    if value>boundary:
        return high
    return low if low%2==0 else high
