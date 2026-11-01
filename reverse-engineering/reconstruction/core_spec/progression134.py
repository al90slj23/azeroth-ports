"""Official0.134.0 arithmetic projection recovered from complete function4630.

Source SHA256: 2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52.
New instruction evidence: reports/2026-11-01-progression0134-chain.json.
This projects only G+1520 level, G+1524 XP and G+2368 pending. Original1513
stat rebuilding, keyed-state writes, messages, healing10847/accounting1453,
and actual choice generation2159 are excluded. Eligibility reports the actual
terminal guard without executing or simulating2159.
"""
from dataclasses import dataclass

from .binary32 import MASK, SIGN, add, from_u32, mul

MAX_LEVEL = 120


def _u32(value):
    if type(value) is not int or not 0 <= value <= MASK:
        raise ValueError('Expected an unsigned 32-bit integer')
    return value


def round_85718_bits(bits):
    """New68B helper: add signed0x3effffff, then clear fractional bits.

    The original0.134 body is byte-identical to historical85387. Preserve
    signed zero and infinities; shared binary32 canonicalizes NaN payloads.
    """
    _u32(bits)
    shifted = add(bits, (bits & SIGN) | 0x3effffff)
    exponent = (shifted >> 23) & 255
    if exponent > 149:
        return shifted
    mask = SIGN if exponent < 127 else (-0x800000 >> (exponent - 127)) & MASK
    return shifted & mask


def trunc_sat_u32(bits):
    """WASM i32.trunc_sat_f32_u, exposed as an unsigned integer."""
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
    """Current4630 order: R85718((n*4+5)+(n*f32(.35))*n).

    n=u32_to_f32(level-(level!=0)); every operation uses binary32 RNE.
    No input-level clamp is applied; levels0 and1 both yield threshold5.
    """
    _u32(level)
    n = from_u32(level - (level != 0))
    linear = add(mul(n, 0x40800000), 0x40a00000)
    quadratic = mul(mul(n, 0x3eb33333), n)
    return round_85718_bits(add(linear, quadratic))


def xp_threshold(level):
    return trunc_sat_u32(xp_threshold_bits(level))


@dataclass(frozen=True)
class ProgressionState:
    """u32 arithmetic fields G+1520/G+1524/G+2368 of official0.134.0."""
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
    """Project XP wrapping and currentlevel<=119 loop, without side effects.

    Phase is not an entry guard. Level120 or higher is retained unchanged;
    held XP still wraps on addition. A zero increment can spend held XP.
    Pending wraps, and a callback is not simulated between iterations.
    """
    if not isinstance(state, ProgressionState):
        raise TypeError('Expected an official0.134 ProgressionState')
    _u32(amount)
    level, xp, pending = state.level, (state.xp + amount) & MASK, state.pending_upgrades
    spent = []
    while level < MAX_LEVEL:
        threshold = xp_threshold(level)
        if xp < threshold:
            break
        level = (level + 1) & MASK
        xp = (xp - threshold) & MASK
        pending = (pending + 1) & MASK
        spent.append(threshold)
    return ProgressionResult(ProgressionState(level, xp, pending), len(spent), tuple(spent))


def card_choice_eligible(pending_upgrades, phase2579, flags2568, gate2564, flags2565):
    """Current4630 terminal guard for2159(G,0,1), with no candidate creation.

    byte2564 is compared exactly to1. Bytes2568/2565 use bit0 only, so a
    noncanonical byte2 must not be treated as a general boolean true.
    """
    _u32(pending_upgrades)
    for value in (phase2579, flags2568, gate2564, flags2565):
        if type(value) is not int or not 0 <= value <= 255:
            raise ValueError('Expected an unsigned byte')
    return (pending_upgrades != 0 and phase2579 == 1 and not (flags2568 & 1)
            and (gate2564 != 1 or bool(flags2565 & 1)))
