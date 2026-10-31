"""IEEE binary32 operations for readable, reproducible rule specifications.

Finite arithmetic is evaluated as an exact rational, then rounded to nearest,
ties to even. It does not silently use binary64 intermediate arithmetic.
NaNs are canonicalized; callers must not assume NaN payload preservation.
"""
from fractions import Fraction
import math
import struct

SIGN = 0x80000000
INF = 0x7f800000
NAN = 0x7fc00000
MASK = 0xffffffff


def is_nan(bits):
    return bits & INF == INF and bits & 0x7fffff != 0


def is_inf(bits):
    return bits & 0x7fffffff == INF


def is_zero(bits):
    return bits & 0x7fffffff == 0


def to_float(bits):
    return struct.unpack('<f', struct.pack('<I', bits & MASK))[0]


def from_float(value):
    try:
        return struct.unpack('<I', struct.pack('<f', value))[0]
    except OverflowError:
        return INF | (SIGN if math.copysign(1, value) < 0 else 0)


def _fraction(bits):
    exponent = (bits >> 23) & 255
    fraction = bits & 0x7fffff
    if exponent == 255:
        raise ValueError('Nonfinite value has no rational representation')
    significand = fraction if exponent == 0 else (1 << 23) | fraction
    power = -149 if exponent == 0 else exponent - 150
    value = (Fraction(significand << power) if power >= 0
             else Fraction(significand, 1 << -power))
    return -value if bits & SIGN else value


def _rounded_scaled(numerator, denominator, power):
    if power >= 0:
        numerator <<= power
    else:
        denominator <<= -power
    quotient, remainder = divmod(numerator, denominator)
    twice = remainder * 2
    if twice > denominator or (twice == denominator and quotient & 1):
        quotient += 1
    return quotient


def _encode(value, zero_sign=0):
    if value == 0:
        return zero_sign & SIGN
    sign = SIGN if value < 0 else 0
    numerator = abs(value.numerator)
    denominator = value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if ((exponent >= 0 and numerator < denominator << exponent)
            or (exponent < 0 and numerator << -exponent < denominator)):
        exponent -= 1
    if exponent > 127:
        return sign | INF
    if exponent < -126:
        significand = _rounded_scaled(numerator, denominator, 149)
        return sign | significand  # Includes a rounded transition to minimum normal.
    significand = _rounded_scaled(numerator, denominator, 23 - exponent)
    if significand == 1 << 24:
        significand >>= 1
        exponent += 1
    if exponent > 127:
        return sign | INF
    return sign | (exponent + 127) << 23 | (significand - (1 << 23))


def from_u32(value):
    return _encode(Fraction(value & MASK))


def add(a, b):
    if is_nan(a) or is_nan(b):
        return NAN
    if is_inf(a) or is_inf(b):
        if is_inf(a) and is_inf(b) and (a ^ b) & SIGN:
            return NAN
        return a if is_inf(a) else b
    if is_zero(a) and is_zero(b):
        return (a & b) & SIGN
    return _encode(_fraction(a) + _fraction(b))


def sub(a, b):
    return add(a, b ^ SIGN)


def mul(a, b):
    sign = (a ^ b) & SIGN
    if is_nan(a) or is_nan(b) or (is_inf(a) and is_zero(b)) or (is_inf(b) and is_zero(a)):
        return NAN
    if is_inf(a) or is_inf(b):
        return sign | INF
    if is_zero(a) or is_zero(b):
        return sign
    return _encode(_fraction(a) * _fraction(b))


def div(a, b):
    sign = (a ^ b) & SIGN
    if is_nan(a) or is_nan(b) or (is_inf(a) and is_inf(b)) or (is_zero(a) and is_zero(b)):
        return NAN
    if is_inf(a) or is_zero(b):
        return sign | INF
    if is_zero(a) or is_inf(b):
        return sign
    return _encode(_fraction(a) / _fraction(b))


def positive_or_zero(bits):
    return bits if to_float(bits) > 0 else 0
