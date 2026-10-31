"""Independent binary32 models of the two recovered enemy HP-growth curves.

Inputs and outputs are unsigned IEEE-754 binary32 bit patterns. Each add/mul
rounds once to nearest, ties to even, matching the original instruction order.
No original executable, tables, imports, graphics, clocks or saves are loaded.
These are only the growth factors: full enemy HP also includes base stats,
difficulty, zone late scaling, endless and multiplayer multipliers.
"""
from .binary32 import add, mul

ONE = 0x3f800000
LINEAR = 0x3dcccccd          # f32(0.1), original 0x1.99999ap-4
QUADRATIC = 0x3d1374bc       # f32(0.036), original 0x1.26e978p-5
ELITE_CUBIC = 0x3bc2a455     # f32(0.00594), original 0x1.8548aap-8
NORMAL_CUBIC = 0x3be6afcd    # f32(0.00704), original 0x1.cd5f9ap-8


def _growth(time_minutes_bits, zone_scaling_bits, cubic):
    for value in (time_minutes_bits, zone_scaling_bits):
        if not isinstance(value, int) or not 0 <= value <= 0xffffffff:
            raise ValueError('Expected a uint32 binary32 bit pattern')
    t, z = time_minutes_bits, zone_scaling_bits
    # Deliberately do not rewrite as pow(), Horner form or double arithmetic:
    # regrouping multiplications changes rounding for some valid finite inputs.
    first = add(mul(t, LINEAR), ONE)
    second = mul(t, mul(t, QUADRATIC))
    third = mul(t, mul(t, mul(t, cubic)))
    return mul(z, add(add(first, second), third))


def elite_growth_bits(time_minutes_bits, zone_scaling_bits):
    """Original function95640: z*(1+.1*t+.036*t²+.00594*t³), ordered f32."""
    return _growth(time_minutes_bits, zone_scaling_bits, ELITE_CUBIC)


def normal_growth_bits(time_minutes_bits, zone_scaling_bits):
    """Original function95641: z*(1+.1*t+.036*t²+.00704*t³), ordered f32."""
    return _growth(time_minutes_bits, zone_scaling_bits, NORMAL_CUBIC)
