"""Ordered binary32 radius soft compression and original helper35684 model.

Only arithmetic and bit rules are reimplemented here; no original WASM is
loaded. The helper is a log1p-family approximation, not a call to math.log1p.
The outer function models the recovered callsite in original934; that entire
function and its surrounding ability state have not been executed/rebuilt.
NaN payloads are preserved only on an unmodified return path, as in the body.
"""
from . import binary32 as f

SEVENTY = 0x428c0000
TEN = 0x41200000


def _input(bits):
    if not isinstance(bits, int) or not 0 <= bits <= 0xffffffff:
        raise ValueError('Expected a uint32 binary32 bit pattern')
    return bits


def log1p_helper_bits(input_bits):
    """Independent instruction-order model of original (f32)->f32 function35684."""
    x = _input(input_bits)
    ix = x
    signed = ix if ix < 0x80000000 else ix - 0x100000000
    k = 0
    c = 0
    if signed <= 0x3ed413cf:
        if ix > 0xbf7fffff:
            if x == 0xbf800000:
                return 0xff800000
            return f.div(f.sub(x, x), 0)
        if ((ix << 1) & 0xffffffff) < 0x67000000:
            # Original subnormals additionally store/load x*x at a scratch
            # address. WASM exposes no FP exception flags; returned bits are x.
            return x
        reduce = ix > 0xbe95f619
    else:
        if ix > 0x7f7fffff:
            return x
        reduce = True
    if reduce:
        u = f.add(x, 0x3f800000)
        iu = (u + 0x004afb0d) & 0xffffffff
        k = (iu >> 23) - 127
        if iu < 0x4c000000:
            if iu > 0x407fffff:
                numerator = f.add(f.sub(x, u), 0x3f800000)
            else:
                numerator = f.sub(x, f.add(u, 0xbf800000))
            c = f.div(numerator, u)
        x = f.add((iu & 0x007fffff) + 0x3f3504f3, 0xbf800000)
    # k is an exactly representable small signed integer; this is the original
    # f32.convert_i32_s, not a binary64 intermediate arithmetic calculation.
    kf = f.from_float(k)
    s = f.div(x, f.add(x, 0x40000000))
    h = f.mul(x, f.mul(x, 0x3f000000))
    z = f.mul(s, s)
    w = f.mul(z, z)
    t1 = f.mul(z, f.add(f.mul(w, 0x3e91e9ee), 0x3f2aaaaa))
    t2 = f.mul(w, f.add(f.mul(w, 0x3e789e26), 0x3eccce13))
    series = f.add(t1, t2)
    correction = f.add(c, f.mul(kf, 0x3717f7d1))
    correction = f.add(correction, f.mul(s, f.add(h, series)))
    correction = f.sub(correction, h)
    return f.add(f.mul(kf, 0x3f317180), f.add(x, correction))


def radius_bits(radius_input_bits):
    """Recovered934 callsite: for not(r<=70), 70+10*helper((r-70)/10).

    Each operation rounds to binary32 in original order. The unordered NaN
    comparison takes the compression branch; replacing the guard with r>70
    would change that behavior. This is a callsite specification, not all934.
    """
    r = _input(radius_input_bits)
    if f.to_float(r) <= 70:
        return r
    scaled = f.div(f.add(r, 0xc28c0000), TEN)
    compressed = log1p_helper_bits(scaled)
    return f.add(f.mul(compressed, TEN), SEVENTY)
