"""Independent ordinary-death reward arithmetic for official 0.134.0.

Source SHA256: 2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52.
Evidence: reports/2026-11-01-death-xp0134-chain.json, complete 914 WAT
SHA256 40c5bd3b5cfc0f2ef7c0822b1a710b4119fbe130a1046ebb368332402873723b,
function-relative lines 7664..7955 (source selection starts at 6819).

This starts at the ordinary reward boundary after a death has already been
accepted. Input RNG is the state *at that boundary*, not necessarily 914 entry.
It projects 914's direct draws and ordered 1417 requests; it does not spawn
pickups, call original code or claim to complete 914. In particular 1417 kinds
1/2 call 1820, which consumes RNG outside this arithmetic projection.
Every result names pending effects, even when no pickup request is produced.
All *_bits values are binary32 bit patterns; NaN payloads are canonicalized.
"""
from dataclasses import dataclass
import struct

from . import binary32 as f
from .progression134 import trunc_sat_u32
from .rng import next_u32_words

SOURCE_SHA256 = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
FUNCTION_914_BODY_SHA256 = '5beb09c77e81990305a5f71d961fed8fa25d979259c8bd9bcb9a1c51ef659e2f'
FUNCTION_914_WAT_SHA256 = '40c5bd3b5cfc0f2ef7c0822b1a710b4119fbe130a1046ebb368332402873723b'

XP_SCALE_BITS = 0x3fd33333       # f32.const 0x1.a66666p+0
CURRENCY_CHANCE_BITS = 0x3e28f5c3  # f32.const 0x1.51eb86p-3
UNIT24_SCALE_BITS = 0x33800000   # 2**-24
BOUNDED3_ACCEPT_MAX = 0xbfffffff # i32.const -1073741825, unsigned comparison
ONE_BITS = 0x3f800000
ZERO_BITS = 0


def _u32(value):
    if type(value) is not int or not 0 <= value <= f.MASK:
        raise ValueError('Expected an unsigned 32-bit integer')
    return value


def _rng_state(state):
    state = tuple(state)
    if len(state) != 4:
        raise ValueError('RNG state must contain exactly four uint32 words')
    for word in state:
        _u32(word)
    return state


class UnsupportedDeathRoute(ValueError):
    """The supplied source does not reach the reviewed ordinary reward arm."""


class DrawLimitExceeded(RuntimeError):
    """Independent watchdog, not an original game guard or RNG failure."""


@dataclass(frozen=True)
class RewardSource:
    """Raw 424B Unit fields read before 914's source-selection block.

    U244!=-1 loads U256; a *nonzero payload*, rather than the tag alone,
    chooses the boss arm. If that payload is zero, U64!=-1 chooses the special
    arm. Only after both does U284!=0 reach the ordinary definition arm.
    U40 and U416 are not ordinary reward rejection gates in this block.
    """
    tag244: int
    payload256: int
    tag64: int
    definition284: int

    def __post_init__(self):
        for value in (self.tag244, self.payload256, self.tag64, self.definition284):
            _u32(value)

    def require_ordinary(self):
        if self.tag244 != f.MASK and self.payload256 != 0:
            raise UnsupportedDeathRoute('U244/U256 boss reward arm is pending')
        if self.tag64 != f.MASK:
            raise UnsupportedDeathRoute('U64 special reward arm is pending')
        if self.definition284 == 0:
            raise UnsupportedDeathRoute('U284 is null; no ordinary definition arm')


@dataclass(frozen=True)
class OrdinaryDefinition:
    """Fields +56/+60/+68 of the 72B definition referenced by Unit+284."""
    base_xp: int
    scalar60_bits: int = ZERO_BITS
    flag68: int = 0

    def __post_init__(self):
        _u32(self.base_xp)
        _u32(self.scalar60_bits)
        if type(self.flag68) is not int or not 0 <= self.flag68 <= 255:
            raise ValueError('Definition+68 must be an unsigned byte')

    @classmethod
    def from_bytes(cls, data):
        """Decode a supplied 72B record without reading original files/memory."""
        if not isinstance(data, bytes) or len(data) != 72:
            raise ValueError('Expected exactly 72 definition bytes')
        return cls(struct.unpack_from('<I', data, 56)[0],
                   struct.unpack_from('<I', data, 60)[0], data[68])


@dataclass(frozen=True)
class Rng24Result:
    output_u32: int
    bits: int
    state: tuple
    draws: int = 1


def next_rng24(state):
    """914 direct RNG: u32 output>>8, convert to f32, then multiply 2**-24.

    This differs from rng.uniform_range_bits' 23-bit mantissa construction.
    The four-word wrapping recurrence is shared only after checking the new
    inlined 914 instructions at 7684..7740 and 7760..7813. All-zero is a valid
    raw state and remains a fixed point; no seeding/entropy is inferred.
    """
    output, state = next_u32_words(_rng_state(state))
    bits = f.mul(f.from_u32(output >> 8), UNIT24_SCALE_BITS)
    return Rng24Result(output, bits, state)


@dataclass(frozen=True)
class BoundedThreeResult:
    value: int
    state: tuple
    draws: int
    outputs_u32: tuple
    product_u64: int


def bounded_three(state, *, max_draws=100000):
    """914 L7834..7894: multiply full u32 by 3, reject low32>0xbfffffff.

    On acceptance return high32 in 0..2. Equality at 0xbfffffff is accepted.
    This is the exact reviewed rejection rule, not low32<threshold 1 and not
    a float/modulo sampler. Every rejected output advances the recurrence.
    max_draws is an independent watchdog; the original loop has no limit.
    """
    current = _rng_state(state)
    if type(max_draws) is not int or max_draws < 1:
        raise ValueError('max_draws must be a positive integer')
    outputs = []
    for draws in range(1, max_draws + 1):
        output, current = next_u32_words(current)
        outputs.append(output)
        product = output * 3
        if (product & f.MASK) <= BOUNDED3_ACCEPT_MAX:
            return BoundedThreeResult(product >> 32, current, draws,
                                      tuple(outputs), product)
    raise DrawLimitExceeded('Independent bounded-three draw watchdog exceeded')


def _trunc_positive_f32(bits):
    # q comes from uint32*positive 1.65 and is always finite/nonnegative.
    # At exponent>=150 every finite binary32 value is already integral.
    exponent = (bits >> 23) & 255
    if exponent >= 150:
        return bits
    if exponent < 127:
        return bits & f.SIGN
    return bits & (~((1 << (150 - exponent)) - 1) & f.MASK)


@dataclass(frozen=True)
class XpRewardResult:
    amount: int
    state: tuple
    draws: int
    scaled_bits: int | None
    fraction_bits: int | None
    rounding_draw: Rng24Result | None


def project_ordinary_xp(definition, state):
    """Definition68=0 consumes one draw even for baseXP 0 or integral q.

    q=f32(f32.u32(base)*f32(1.65)); result wraps after saturated truncation
    plus the strict comparison f32(q-trunc_f32(q))>rng24. A nonzero *byte*
    flag returns the base amount with no XP-rounding draw.
    """
    if not isinstance(definition, OrdinaryDefinition):
        raise TypeError('Expected an OrdinaryDefinition')
    current = _rng_state(state)
    if definition.flag68 != 0:
        return XpRewardResult(definition.base_xp, current, 0, None, None, None)
    scaled = f.mul(f.from_u32(definition.base_xp), XP_SCALE_BITS)
    fraction = f.sub(scaled, _trunc_positive_f32(scaled))
    draw = next_rng24(current)
    amount = (trunc_sat_u32(scaled)
              + int(f.to_float(fraction) > f.to_float(draw.bits))) & f.MASK
    return XpRewardResult(amount, draw.state, 1, scaled, fraction, draw)


@dataclass(frozen=True)
class CurrencyRewardResult:
    amount: int
    chance_bits: int
    chance_passed: bool
    chance_draw: Rng24Result
    bounded: BoundedThreeResult | None
    direct_rng_state: tuple
    direct_draws: int


def project_ordinary_currency(flag68, state, *, max_draws=100000):
    """Always draw probability; pass iff rng24<(flag68?1:f32(.165)).

    Failure consumes no bounded draw. Ordinary success gives bounded3+2;
    flagged success gives 15 with no bounded draw. Every possible 24-bit
    sample is <1, so any nonzero flag always passes this particular guard.
    The returned state stops before 1417(kind1)'s additional 1820 RNG.
    """
    if type(flag68) is not int or not 0 <= flag68 <= 255:
        raise ValueError('Definition+68 must be an unsigned byte')
    draw = next_rng24(state)
    chance = ONE_BITS if flag68 else CURRENCY_CHANCE_BITS
    passed = f.to_float(draw.bits) < f.to_float(chance)
    bounded = None
    amount = 0
    current = draw.state
    draws = 1
    if passed:
        amount = 15
        if flag68 == 0:
            bounded = bounded_three(current, max_draws=max_draws)
            amount = bounded.value + 2
            current = bounded.state
            draws += bounded.draws
    return CurrencyRewardResult(amount, chance, passed, draw, bounded, current, draws)


@dataclass(frozen=True)
class PickupRequest:
    """An ordered 1417 invocation, never an allocated 56B pickup record.

    Offset bits apply to the accepted death position with separate f32 adds.
    Kind2's height requires 60414(world+8,x+2,y-1) and remains pending.
    Even known death height can subsequently change in 1417 geometry logic.
    """
    kind: int
    amount: int
    offset_x_bits: int = ZERO_BITS
    offset_y_bits: int = ZERO_BITS
    height_source: str = 'death_position'


@dataclass(frozen=True)
class DeathRewardProjection:
    source: RewardSource
    xp: XpRewardResult
    currency: CurrencyRewardResult
    accumulator2412_bits: int
    requests: tuple
    direct_rng_state: tuple
    direct_draws: int
    pending: tuple
    status: str = 'pending_consumers'
    stage: str = '914_L7664_L7955_direct_reward_projection'


def project_ordinary_rewards(definition, state, *, source, accumulator_bits=ZERO_BITS,
                             max_draws=100000):
    """Project only the accepted-death ordinary source arm, in original order.

    Guards are raw source fields, not guessed boss/pet/elite names. A death
    caller must separately establish phase 1, target existence, lethal damage
    and entry at this boundary. Pre-boundary state changes are not replayed.
    The three possible requests are XP(kind0),currency(kind1),flagged(kind2).
    G2412 accumulates definition60 only for flag68=0, with binary32 addition.
    The returned direct_rng_state excludes 1417/1820 and all other callbacks;
    it must not be written as the final RNG after a complete 914 execution.
    """
    if not isinstance(source, RewardSource):
        raise TypeError('Expected raw RewardSource guards')
    source.require_ordinary()
    if not isinstance(definition, OrdinaryDefinition):
        raise TypeError('Expected an OrdinaryDefinition')
    _u32(accumulator_bits)
    if definition.flag68 == 0:
        accumulator_bits = f.add(definition.scalar60_bits, accumulator_bits)
    xp = project_ordinary_xp(definition, state)
    currency = project_ordinary_currency(definition.flag68, xp.state,
                                          max_draws=max_draws)
    requests = []
    pending = [
        '914 pre-boundary damage/death guards, unit freeze, statistics, messages, '
        'item/modifier callbacks and healing are not replayed; supplied RNG is boundary state',
        '914 post-boundary20664, owned/item death events and possible recursive914 remain pending',
    ]
    if xp.amount != 0:
        requests.append(PickupRequest(0, xp.amount))
        pending.append('1417 kind0 geometry,45-idle merge/allocation, GUID/messages and pickup mutation')
    if currency.chance_passed:
        requests.append(PickupRequest(1, currency.amount, 0x3f4ccccd, 0x3f4ccccd))
        pending.append('1417 kind1 geometry/entity/pickup effects and1820 RNG; final914 RNG unknown')
    if definition.flag68 != 0:
        requests.append(PickupRequest(2, 15, 0x40000000, 0xbf800000,
                                      'pending60414_world_height'))
        pending.append('60414 height and1417 kind2 entity/item effects including1820 RNG')
    return DeathRewardProjection(source, xp, currency, accumulator_bits,
                                 tuple(requests), currency.direct_rng_state,
                                 xp.draws + currency.direct_draws, tuple(pending))
