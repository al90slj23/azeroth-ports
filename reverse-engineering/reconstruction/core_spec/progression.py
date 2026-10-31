"""Independent arithmetic projection of the recovered XP/level-up instructions.

This does not implement all of original3231: attribute/heal recalculation1573,
messages, notifications and card generation2098 are excluded. Their effects on
game state are not simulated. The guard only reports whether2098 is eligible.
All f32 arithmetic has the original order and per-operation binary32 rounding.
"""
from dataclasses import dataclass

from .binary32 import MASK, SIGN, add, from_u32, mul


def _u32(value):
    if type(value) is not int or not 0 <= value <= MASK:
        raise ValueError('Expected an unsigned 32-bit integer')
    return value


def round_85387_bits(bits):
    """Original85387, including signed zero; NaN payloads canonicalized.

    Add copysign(0x3effffff,x), then clear fractional significand bits when
    the biased exponent is <=149. This is not a host-language round().
    """
    _u32(bits)
    shifted = add(bits, (bits & SIGN) | 0x3effffff)
    exponent = (shifted >> 23) & 255
    if exponent > 149:
        return shifted
    mask = SIGN if exponent < 127 else (-0x800000 >> (exponent - 127)) & MASK
    return shifted & mask


def trunc_sat_u32(bits):
    """WASM i32.trunc_sat_f32_u, returning the unsigned bit interpretation."""
    _u32(bits)
    exponent = (bits >> 23) & 255
    fraction = bits & 0x7fffff
    if bits & SIGN or (exponent == 255 and fraction) or exponent < 127:
        return 0
    if exponent >= 159:
        return MASK
    significand = (1 << 23) | fraction
    power = exponent - 150
    return significand << power if power >= 0 else significand >> -power


def xp_threshold_bits(level):
    """Rounded f32 threshold for a u32 level, before saturating conversion.

    n=f32(level-(level!=0)); R85387((n*4+5)+(n*.35)*n).
    Level0 and level1 both use n=0. The input is not clamped to99.
    """
    _u32(level)
    n = from_u32(level - (level != 0))
    linear = add(mul(n, 0x40800000), 0x40a00000)
    quadratic = mul(mul(n, 0x3eb33333), n)
    return round_85387_bits(add(linear, quadratic))


def xp_threshold(level):
    return trunc_sat_u32(xp_threshold_bits(level))


@dataclass(frozen=True)
class ProgressionState:
    """Arithmetic fields G+1336/G+1340/G+2088, interpreted as u32."""
    level: int
    xp: int
    pending_upgrades: int

    def __post_init__(self):
        for value in (self.level, self.xp, self.pending_upgrades):
            _u32(value)


@dataclass(frozen=True)
class ProgressionResult:
    state: ProgressionState
    levels_gained: int
    thresholds_spent: tuple


def apply_xp(state, amount):
    """Apply the XP arithmetic only, with u32 wrap and the <=98 loop guard.

    Existing level>=99 is retained (not coerced to99); no further XP is spent.
    Calling with amount0 can still spend XP already held. Pending2088 wraps.
    The projection deliberately does not invoke callbacks between iterations.
    """
    if not isinstance(state, ProgressionState):
        raise TypeError('Expected ProgressionState')
    _u32(amount)
    level, xp, pending = state.level, (state.xp + amount) & MASK, state.pending_upgrades
    spent = []
    while level <= 98:
        threshold = xp_threshold(level)
        if xp < threshold:
            break
        level += 1
        xp = (xp - threshold) & MASK
        pending = (pending + 1) & MASK
        spent.append(threshold)
    return ProgressionResult(ProgressionState(level, xp, pending), len(spent), tuple(spent))


def card_choice_eligible(pending_upgrades, phase2299, flags2288, gate2284, flags2285):
    """Original3231's final guard for2098(G,0,1), without2098 side effects.

    The gate2284 comparison is exactly ==1, while2288/2285 use bit0 only.
    These four fields are bytes; noncanonical byte2 is not treated as true1.
    """
    _u32(pending_upgrades)
    for value in (phase2299, flags2288, gate2284, flags2285):
        if type(value) is not int or not 0 <= value <= 255:
            raise ValueError('Expected an unsigned byte')
    return (pending_upgrades != 0 and phase2299 == 1 and not (flags2288 & 1)
            and (gate2284 != 1 or bool(flags2285 & 1)))
